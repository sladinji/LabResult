import traceback
from functools import wraps
from datetime import datetime

from flask import jsonify, request
from flask.ext import login
from flask.ext.babelex import gettext
from flask.ext.restful import abort
from mongoengine import Q
from mongoengine.errors import ValidationError, DoesNotExist
from wtforms.validators import ValidationError as WTFValError

import labresult
from labresult.lib.model import get_option
from labresult.model import Document, HealthWorker, Group, User, FailedLogin



class RestrictedArea:
    """
    Base class for view and API right management.
    """

    allowed_users = []
    """
    User type allowed (User.Patient, User.Administrator...).
    """

    def user_is_authorized(self):
        user = login.current_user
        if not hasattr(user, '_cls') or not user.is_authenticated:
            return False

        cls = user._cls
        cls = "User.Administrator" if "Administrator" in cls else cls
        if cls not in self.allowed_users :
            return False
        if cls == "User.Administrator" :
            return user.get_right(self.model._class_name).read
        return True

class UserPermissionError(Exception):
    pass

class InvalidRequestException(Exception):
    pass

def _check_group_doc(doc) :
    """
    Check if logged group has access to doc
    """
    if not doc.current_version:
        return False
    group_access = [ x for x in doc.groups
            if x.user.id == login.current_user.id and x.read ]
    if group_access:
        return True

def _check_hw_doc(doc) :
    """
    Check if logged user has access to doc as healthworker
    """
    user_access = [x for x in doc.healthworkers
            if  x.user.id == login.current_user.id and x.read ]
    groups = [x.user for x in login.current_user.groups]
    group_access = [x for x in doc.groups if x.user in groups and x.read]

    if doc.current_version and (group_access or user_access):
        return True

def _check_grp_user(user):
    """
    Check if a group has something to do with given user
    """
    grp = Group.objects.get(id=login.current_user.id)
    #check if grp only check info on himself
    if user == grp :
        return True
    qry = Q( groups__user = grp, patient__user = user)
    return Document.objects(qry).only('id').first()

def _check_hw_user(user):
    """
    Check if healthworker has something to do with given user
    """
    hw = HealthWorker.objects.get(id=login.current_user.id)
    #check if hw only check info on himself
    if user == hw :
        return True
    #check if hw has a direct association or via a group
    qry = Q( healthworkers__user = hw, patient__user = user)
    if hw.groups:
        groups_id = [ x.user.id for x in hw.groups ]
        qry = qry | Q( groups__match = {
            'user': { '$in' : groups_id},
            })
    return Document.objects(qry).only('id').first()

def _check_pat_doc(doc):
    return doc.patient.user.id == login.current_user.id \
            and doc.patient.read and doc.current_version

def permission_on_doc(doc):
    check = {
            'User.Administrator' : lambda x : True,
            'User.Administrator.AdminGeneric' : lambda x : True,
            'User.Administrator.Biologist' : lambda x : True,
            'User.Patient' : _check_pat_doc,
            'User.HealthWorker' : _check_hw_doc,
            'User.Group' : _check_group_doc,
            }[login.current_user._cls]

    if not check(doc) :
        raise UserPermissionError()

def permission_on_user(user):
    check = {
            'User.Administrator': lambda x : True,
            'User.Administrator.AdminGeneric': lambda x : True,
            'User.Administrator.Biologist': lambda x : True,
            'User.Patient': lambda user : user.id == login.current_user.id,
            'User.HealthWorker' : _check_hw_user,
            'User.Group' : _check_grp_user,
            }[login.current_user._cls]
    if not check(user):
        raise UserPermissionError()

def auth_exception_manager(fn):
    """
    Decorator for handling excetpion in get/put/post method of restfull ressource.
    """
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            ret = fn(*args, **kwargs)
        except UserPermissionError as e :
            labresult.app.logger.info(e)
            ret = { 'success' : False, 'error': 'Access denied to'
                ' requested ressource'}
        except ValidationError as e:
            labresult.app.logger.info(e)
            ret = { 'success' : False, 'error': 'Invalid ID'}
        except DoesNotExist as e:
            labresult.app.logger.info(e)
            ret = { 'success' : False, 'error': 'Ressource not found'}
        except InvalidRequestException as e:
            labresult.app.logger.info(e)
            ret = { 'success' : False, 'error': str(e)}
        except Exception as e:
            labresult.app.logger.error(traceback.format_exc())
            ret = { 'success' : False, 'error': 'Unknow'}
        finally :
            if ret['success']:
                return jsonify(ret)
            else :
                return abort( 401, **ret)
    return wrapped

def password_check(form, field):
    if not field.data:
        return
    min = get_option('password_min_lenth', 8,
    gettext('Nombre de caractères minimum pour un mot de passe'))
    if len(field.data) < min:
        msg = gettext('Le mot de passe doit faire plus de %s caractères')
        raise WTFValError(msg.format(min))
    if form.confirm.data != field.data :
        raise WTFValError(gettext('La confirmation du mot de passe ne'
        ' correspond pas'))

def no_duplicate_login(form, field, except_current=False):
    if field.data == '':
        field.data = None
    if not field.data:
        return
    already = User.objects(login=field.data)
    if except_current :
        already = User.objects(login=field.data, id__ne=login.current_user.id)
    if hasattr(form, '_obj') and form._obj :
        already = User.objects(login=field.data, id__ne=form._obj.id)
    if already:
        raise WTFValError(gettext("Le login existe déjà"))
def is_black_listed():
    try :
        attempt = FailedLogin.objects(ip = request.remote_addr).get()
        max_fail =get_option("max_login_attempt", 20, gettext(
            "Nombre maximal d'échec de connexion avant blocage."
            ))
        return attempt.total >= max_fail
    except labresult.model.db.DoesNotExist:
        return False

def black_list(login):
    """
    Call on a login failure. Return True if ip is now black listed or False if
    other attempts are allowed.
    """
    try :
        attempt = FailedLogin.objects(ip = request.remote_addr).get()
        max_fail =get_option("max_login_attempt", 20, gettext(
            "Nombre maximal d'échec de connexion avant blocage."
            ))
        attempt.total += 1
        attempt.login = login
        attempt.last = datetime.utcnow()
        attempt.save()
        if attempt.total >= max_fail :
            return True
        else :
            return False
    except labresult.model.db.DoesNotExist:
        FailedLogin(ip = request.remote_addr, total =1, login=login).save()
        return False



