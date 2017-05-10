import traceback
from functools import partial
import datetime

from flask import url_for, request, redirect, flash
from flask.ext.admin.contrib.mongoengine import ModelView, helpers
from jinja2 import Markup, escape
from flask.ext import login
from flask.ext.admin import BaseView
from mongoengine.fields import GridFSProxy

import labresult
from labresult.lib.auth import RestrictedArea
from flask.ext.admin.contrib.mongoengine.typefmt import DEFAULT_FORMATTERS

from flask.ext.babelex import gettext

def date_formatter(view, value):
    if not value :
        return ""
    else :
        return datetime.datetime.strftime(value,'%d/%m/%Y')

def bool_formatter(view, value):
    """
        Return check icon if value is `True` or empty string otherwise.

        :param value:
            Value to check
    """
    glyph = 'ok-circle' if value else 'minus-sign'
    color = 'txtvertF' if value else 'txtredF'

    return Markup('<span class="glyphicon glyphicon-%s icon-%s %s"></span>' % (glyph, glyph, color))

def grid_formatter(view, value):
    if not value.grid_id:
        return ''

    args = helpers.make_gridfs_args(value)

    return Markup(
        ('<a href="%(url)s" target="_blank">' +
            '<i class="icon-file"></i>%(name)s' +
         '</a> %(size)dk (%(content_type)s)') %
        {
            'url': view.get_url('.api_file_view', **args),
            'name': escape(value.name) if hasattr(value,'name') else
            gettext("fichier"),
            'size': value.length // 1024 if hasattr(value, 'length') else 0,
            'content_type': escape(value.content_type) if hasattr(value,
                'content_type') else '',
        })



MY_DEFAULT_FORMATTERS = dict(DEFAULT_FORMATTERS)
MY_DEFAULT_FORMATTERS.update({
            datetime.datetime : date_formatter,
	    bool: bool_formatter,
            GridFSProxy: grid_formatter,
                })
class LoginRedirect:
    """
    Class with a conviniant method to redirect user to login page when they're
    not authenticaded.
    """
    def inaccessible_callback(self, name, **kwargs):
        flash(gettext("Vous devez vous identifier pour accéder à la ressource"
                " demandée"), "error")
        return redirect(url_for("admin.index"), 307)


class LoggedinView(LoginRedirect, BaseView):

    def is_accessible(self):
        return login.current_user.is_authenticated

class AuthView(LoginRedirect, ModelView, RestrictedArea):
    """
    Base class to centralize authentication.
    """
    list_template="admin/model/list_custo.html"
    column_type_formatters = MY_DEFAULT_FORMATTERS

    @property
    def can_edit(self):
        return login.current_user.get_right(self.model._class_name).update

    @property
    def can_delete(self):
        return login.current_user.get_right(self.model._class_name).delete

    @property
    def can_create(self):
        return login.current_user.get_right(self.model._class_name).create

    def is_accessible(self):
        return self.user_is_authorized()

    def inaccessible_callback(self, name, **kwargs):
        if not login.current_user.is_authenticated:
            flash(gettext("Vous devez vous identifier pour accéder à la ressource"
                " demandée."), "error")
        else:
            flash(gettext("Vous n'avez pas les droits nécessaires pour accéder à"
               " la page demandée."), "error")
        return redirect(url_for("admin.index"), 307)

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True):
        """
        Add '*' in front of search term to turn query case insensitive by
        default.
        """
        if search :
            search = '*' + search
        return super(AuthView, self).get_list(page, sort_column, sort_desc,
                search, filters, execute)

def frmt_numdos(v,c,m,n):
    """
    Callback function for BaseModelView column_formatters technique.
    Create a link to edit user and set a return url.
    :param v: current administrative view
    :param c: instance of jinja2.runtime.Context
    :param m: model instance
    :param n: property name
    """
    return m.numdos + "(v%s)" % m.version if m.numdos else ""

def frmt_doc_type(v,c,m,n):
    """
    Callback function for BaseModelView column_formatters technique.
    Create a link to edit user and set a return url.
    :param v: current administrative view
    :param c: instance of jinja2.runtime.Context
    :param m: model instance
    :param n: property name
    """
    mapping = {}
    if "User.Administrator" in login.current_user._cls :
        mapping = dict(
            CR_DOCTOR = 'Compte rendu médecin',
            CR_PATIENT = 'Compte rendu patient',
            CR_CORRES = 'Compte rendu correspondant',
            )
        if m.signed :
            icon = ' <span class="itemic {}" title="{}"></span>'.format(
                    'flaticon-verified9',
                    gettext("Document signé numériquement")
                    )
            mapping = { k : Markup(v + icon) for k, v in mapping.items()}
    else :
        mapping = dict(
            CR_DOCTOR = "Compte rendu d'analyse",
            CR_PATIENT = "Compte rendu d'analyse",
            CR_CORRES = "Compte rendu d'analyse",
            )
    return mapping.get(m.doc_type, m.doc_type)

def format_members(v,c,m,n):
    """
    Callback function for BaseModelView column_formatters technique.
    Create a link to edit user and set a return url.
    :param v: current administrative view
    :param c: instance of jinja2.runtime.Context
    :param m: model instance
    :param n: property name
    """
    str = "<a href='{}'>{}</a><br>"
    return_url = request.url or url_for('group.index_view')
    linklist = []
    for mb in m.members :
        try :
            linklist.append(  str.format(
                url_for(mb.__class__.__name__.lower()+".edit_view",
                    url=return_url,
                    id= mb.id,
                    ),
                mb.name
                )
            )
        except:
            labresult.app.logger.warning(traceback.format_exc())

    return Markup(" ".join(linklist))

def _user_name_to_link(user):
    link = "<a href='{}'>{}</a>".format(
        url_for(user.__class__.__name__.lower()+".edit_view",
            id= user.id,
            url = request.url,
            ),
        user.name if user.name else user.login
        )
    return link

def format_user(v,c,m,n):
    """
    Display a link to edit user
    """
    return Markup(_user_name_to_link(m.user))

def format_name(users,v,c,m,n):
    """
    Callback function for BaseModelView column_formatters technique.
    Create a link to edit user and set a return url.
    :param users: str, 'patient', 'healthworkers'
    :param v: current administrative view
    :param c: instance of jinja2.runtime.Context
    :param m: model instance
    :param n: property name
    """
    linklist = []
    accesslist = None
    if hasattr(m, users) :
        accesslist = getattr(m,users)
        if not isinstance(accesslist, list):
            accesslist = [accesslist]
    if accesslist:
        for access in accesslist :
            if not access :
                continue
            try :
                linklist.append(_user_name_to_link(access.user))
            except:
                labresult.app.logger.warning(traceback.format_exc())

    return Markup(" ".join(linklist))


def frmt_acl(v,c,m,n):
    """
    :param v: current administrative view
    :param c: instance of jinja2.runtime.Context
    :param m: model instance
    :param n: property name
    """
    html = """<table class="table">
      <thead>
        <tr>
          <th>Ressource</th>
          <th>Création</th>
          <th>Lecture</th>
          <th>Édition</th>
          <th>Suppression</th>
        </tr>
      </thead>
      <tbody>
     """
    def boolrender(bool_):
        if bool_ :
            return '<span class="glyphicon glyphicon-ok-circle icon-ok-circle txtvertF"></span>'
        else :
            return '<span class="glyphicon glyphicon-minus-sign icon-minus-sign txtredF"></span>'

    for ac in m.acl :
        html += "<tr><th>%s</th> : <td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (ac.view.menu_name,
                boolrender(ac.create),
                boolrender(ac.read),
                boolrender(ac.update),
                boolrender(ac.delete),
                )
    html += "</tbody></table>"
    return Markup(html)

frmt_pat_name = partial(format_name,'patient')
frmt_healthworker_name = partial(format_name, 'healthworkers')
frmt_group_name = partial(format_name, 'groups')
