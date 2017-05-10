from flask.ext import login
from flask.ext.restful import reqparse
from mongoengine import Q

from labresult.lib.api import StandardPermissionsCheck,FilterableListResource
from labresult.lib.auth import permission_on_user
from labresult.lib.auth import auth_exception_manager
from labresult.model import  User, Patient, HealthWorker, Administrator

class UserInfo(StandardPermissionsCheck):
    """
    Return info about a requested User. Check if logged user has something to
    do with requested user.
    """
    model = User
    allowed_users = ["User.Patient", "User.HealthWorker", "User.Administrator",
            'User.Group']
    parser = reqparse.RequestParser()
    parser.add_argument("ids", type=str, action='append')
    userattr = [
            'name', 'birthdate', 'mobile', 'fixe','email', 'address1',
            'address2', 'address3', 'login', 'id'
            ]
    """
    Attribute accessible in read mode, in write mode password can be added.
    """
    parser.add_argument("password", type=str)
    for attr in userattr:
        parser.add_argument(attr, type="str")


    def _pack_item(self, id):
        """
        Return user matching id in a dictionnary ready for jsonify.
        """
        user = User.objects.get(id=id)
        self.check_permission(user)
        userdic = { k: str(getattr(user, k)) if getattr(user,k) else None for k in self.userattr }
        userdic.update( user_type = login.current_user._cls)
        return userdic

    @auth_exception_manager
    def get(self):
        """
        Override default behavior by sending logged user class if not id
        provided.
        """
        args = self.parser.parse_args()
        ids = args['ids']
        ret = dict(success=True)
        if ids :
            ret.update(items=self._pack_items(ids))
        else:
            ret.update(items=self._pack_items([str(login.current_user.id),]))
        return ret

    def check_permission(self, item):
        return permission_on_user(item)

    def post(self):
        args = self.parser.parse_args()
        if args['password']:
            login.current_user.set_password(args.pop('password'))
        for k, v in args.items():
            login.current_user.setattr(k, v)
            login.current_user.save()




class UserList(FilterableListResource):
    allowed_users = ["User.Administrator", "User.HealthWorker"]
    parser = reqparse.RequestParser()
    parser.add_argument("page_num", type=int, default=1)
    parser.add_argument("filter", type=str)
    parser.add_argument("cls", type=str)
    model = User

    def _get_qry(self, args):
        """
        Return json for board api.
        """
        qry1 = Q()
        class_ = User
        if args['filter']:
            qry1 = Q(name__icontains=args['filter'])
        cls = args['cls']
        if cls:
            class_ = {'User.Patient': Patient,
                    'User.HealthWorker': HealthWorker,
                    'User.Administrator': Administrator,
                    }[cls]
        qry = class_.objects.filter(qry1)
        return qry
