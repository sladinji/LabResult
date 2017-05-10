import os
from flask import request, flash
from flask.ext.admin import expose
from jinja2 import Markup
from labresult.lib.admin import NotAuthenticatedMenuLink, AuthenticatedMenuLink
from labresult.views.login import LoginView
from labresult.lib.model import get_option
from wtforms import form, validators
from wtforms.fields.html5 import EmailField
from labresult_demo import mail
import jinja2


class DemoForm(form.Form):
    email = EmailField('Email address', [validators.DataRequired(),
            validators.Email()])


class DemoLoginView(LoginView):
    login_template = 'demologin/form.html'
    credential_form = DemoForm

    @expose('/democredentials', methods=('POST',))
    def send_demo_credentials(self):
        """
        Send demo credential
        """
        cform = DemoForm(request.form)
        if cform.validate():
            if mail.send(cform.email.data) :
                flash("Un email vient d'être envoyé à l'adresse indiquée")
            else :
                flash("Un problème est survenu lors de l'envoi du message"
                " Veuillez réessayer à nouveau.", "error")

        return self.render(self.login_template, form=self.form_class(),
                cform=cform)

def get_plugin_view(app):
    tpath = os.path.join(os.path.dirname(__file__), 'templates')
    my_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
            jinja2.FileSystemLoader(tpath),
            ])
    app.jinja_loader = my_loader
    return DemoLoginView

def get_demo_menu_html(label, icon, is_submenu=False):
    if is_submenu :
        menu = Markup('<span class="itemic flaticon-{}"></span> {}'.format(icon,
        label))
    else:
        menu = Markup('<span class="hidden-sm hidden-xs glyphicon glyphicon-{}"></span> {}'.format(icon,
        label))
    return menu

def get_plugin_menu(app):
    #set google messaging api value
    get_option("GCM_API_KEY", "AIzaSyDu6UcM87szA-3SLUpFA629m_j0wxgXGGs", "Clé pour API GCM",
            visible=False)
    #change menu
    fadmin = app.extensions.get('admin')[0]
    fadmin.pre_links = []
    menu = [( "Accueil", "home", "http://labresult.fr"),
            ("Démo", "star", "/"),
            ("Entreprise", "cloud-upload", "http://labresult.fr/entreprise/"),
            ("Contact", "envelope", "http://labresult.fr/contact/"),
            ]
    for name, icon, link in menu :
        fadmin.pre_links.append(
            NotAuthenticatedMenuLink(name=get_demo_menu_html(name, icon),
                url=link
                )
            )

    fadmin.pre_links.append(
            AuthenticatedMenuLink(name=get_demo_menu_html("Acceuil", "home"),
                url="/"
                )
            )

