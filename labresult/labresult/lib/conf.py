from datetime import timedelta
from pkg_resources import iter_entry_points

from flask import redirect, url_for, session, flash, request
from flask.ext import admin, login
from flask.ext.babelex import gettext
from flask.ext.restful import Api

import labresult.api.file as apifile
from labresult.api import labos, pcl, documents, printers, user, board
from labresult.api import doc2sign
from labresult.api.printing import Printing
from labresult.lib.admin import AuthenticatedMenuLink, NotAuthenticatedMenuLink, create_aview, get_menu_html, configure_logging
from labresult.lib.model import get_option
from labresult.model import UserLog, User, View
from labresult.views.account import AccountView
from labresult.views.login import LoginView
from labresult.views.credential import CredentialView
from labresult.lib.admin import render_user_button, render_user_button_css_class, render_ariane_user

def do_post_config(app):
    """
    Apply paramters that are in DB. Because of dependancies on labresult.app
    for logging, DB configuration can't be done in create_app.
    """

    #session timeout management
    @app.before_request
    def make_session_permanent():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(
                minutes=get_option('session_timeout', 120,
                gettext("Durée en minutes d'inactivité avant déconnexion automatique."))
)
    #user tracking in DB
    @app.before_request
    def log_user_action():
        if "static" in request.url or not login.current_user.is_authenticated:
            return
        args = "{ "
        for k,v in request.args.lists() :
            args += "%s = %s, " % (k, v)
        args += "}"
        log = UserLog(
                ip = request.environ.get("REMOTE_ADDR"),
                user = User.objects( id = login.current_user.id).first(),
                user_name = login.current_user.name,
                url = request.path,
                method = request.method,
                args = args,
                browser = request.user_agent.browser,
                version = request.user_agent.version,
                platform = request.user_agent.platform,
                uas = request.user_agent.string,
                )
        log.save()

    configure_logging(app)

    #Menu icons
    app.jinja_env.filters['render_menu_item'] = render_user_button
    app.jinja_env.filters['render_ariane_user'] = render_ariane_user
    app.jinja_env.filters['render_menu_item_css_class'] = render_user_button_css_class
    ident_menu = get_menu_html( gettext('Mon compte'), 'password17',
            is_submenu=True)
    acceuil_menu = get_menu_html( gettext('Accueil'),'house109')
    user_menu = get_menu_html(gettext('Utilisateurs'),'personal19')
    param_menu = get_menu_html(gettext('Paramètres'),'two185')
    # Flask Admin views
    login_view_plugin = None
    #look for login plugin
    for plugin in iter_entry_points(group='labresult.plugin.login', name=None):
            plugin_init = plugin.load()
            login_view_plugin = plugin_init(app)
    if not login_view_plugin :
        login_view_plugin = LoginView
    #look for sms plugin
    app.sms_plugins = []
    for plugin in iter_entry_points(group='labresult.plugin.sms', name=None):
            app.sms_plugins.append(plugin.load()())
    if not login_view_plugin :
        login_view_plugin = LoginView

    lview = login_view_plugin(url="/lab", name=gettext("Accueil"))
    fadmin = admin.Admin(app, 'LabResult', "/", base_template="admin/base_custo.html", template_mode='bootstrap3',
            index_view=lview)

    fadmin.add_view(CredentialView(name='Authentification', endpoint='credential'))

    def reg_view(view):
        """
        Record view in DB to manage ACL.
        """
        if not view:
            return
        View.objects(name=view.__class__.__name__).update_one(
                    upsert=True,
                    set__name=view.__class__.__name__,
                    set__url="/" + view.endpoint + '/' if view.endpoint else '',
                    set__menu_name=view.name if view.name else '',
                    set__model=view.model._class_name if hasattr(view, 'model') else '',
                    )
        fadmin.add_view(view)

    #look for admin plugin
    for plugin in iter_entry_points(group='labresult.plugin.admin', name=None):
            plugin_init = plugin.load()
            plugin_init(reg_view, create_aview, user_menu, param_menu)

    reg_view(create_aview('Document', gettext('Résultats'), 'drawer4', 'DocumentPatientView',
    endpoint='mesdocuments'))
    reg_view(create_aview('Document', gettext('Résultats'), 'drawer4', 'DocumentHealthWorkerView',
    endpoint='mesdossiers'))
    reg_view(create_aview('Document', gettext('Résultats'), 'drawer4', 'DocumentGroupView',
    endpoint='nosdossiers'))
    reg_view(create_aview('Patient', gettext('Patients'), 'user58', category=user_menu))
    reg_view(create_aview('HealthWorker',gettext('Professionnels de santé'), 'medical14',
        category=user_menu)
    )
    reg_view(create_aview('Group', gettext('Groupes'), 'multiple25', category=user_menu))
    current_user_menu = get_menu_html("UserName",'user58')
    reg_view(AccountView(endpoint="account", name=ident_menu, category =
        current_user_menu))


    # Restful api
    api = Api(app)
    api.add_resource(pcl.PCL, '/api/v1.0/pcl')
    api.add_resource(apifile.File, '/api/v1.0/file')
    api.add_resource(Printing, '/api/v1.0/printing')
    api.add_resource(labos.Labo, '/api/v1.0/labos/<string:id>')
    api.add_resource(printers.Printer, '/api/v1.0/printers/<string:id>')
    api.add_resource(labos.Labos, '/api/v1.0/labos')
    api.add_resource(documents.Document, '/api/v1.0/documents/')
    api.add_resource(board.Board, '/api/v1.0/board')
    api.add_resource(doc2sign.Doc2Sign, '/api/v1.0/doc2sign')
    api.add_resource(user.UserInfo, '/api/v1.0/user')
    api.add_resource(user.UserList, '/api/v1.0/userlist')

    fadmin.pre_links = []
    fadmin.pre_links.append(AuthenticatedMenuLink(name=acceuil_menu, url='/'))
    #Add login link
    deco_menu = get_menu_html(gettext('Déconnexion'),'logout20',
            is_submenu=True)
    con_menu = get_menu_html('Accueil','house109')
    fadmin.add_link(AuthenticatedMenuLink(name=deco_menu,
    endpoint="admin.logout",category=current_user_menu)
)
    fadmin.pre_links.append(NotAuthenticatedMenuLink(name=con_menu,
    endpoint="admin.index"))

    @app.route('/')
    def index():
        return redirect(url_for("admin.index"))

    from labresult.views.error import ErrorView

    #Error handling

    errv = ErrorView()
    errv.admin = fadmin

    @app.errorhandler(404)
    def page_not_found(e):
        flash(gettext("La page demandée n'existe pas."), 'error')
        return errv.render("error.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        flash(gettext("Le serveur a rencontré une erreur."), 'error')
        return errv.render("error.html"), 500

    #menu plugin
    for plugin in iter_entry_points(group='labresult.plugin.menu', name=None):
            plugin_init = plugin.load()
            plugin_init(app)
    print(app.url_map)
    return app
