from datetime import datetime, timedelta
import re
from random import randint

from flask import request, redirect, url_for, flash
from flask.ext import login
from flask.ext.admin import AdminIndexView, expose
from flask.ext.babelex import gettext
from wtforms import form, fields, validators

import labresult
from labresult.lib.email import send_email_credential
from labresult.lib.sms import send_sms_credential
from labresult.model import User, UserLog
from labresult.lib.model import get_option
from labresult.lib.auth import black_list, is_black_listed


# Initialize flask-login
def init_login(app):
    login_manager = login.LoginManager()
    login_manager.setup_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(id=user_id).first()

# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    login = fields.TextField()
    password = fields.PasswordField()

    def validate_login(self, field):
        user = self.get_user()
        if not user.match_pass(self.password.data):
            labresult.app.logger.warning("Password does not match")
            raise validators.ValidationError('Invalid password')

        if not user.is_active():
            labresult.app.logger.warning("Account desactivated")
            raise validators.ValidationError('Account deactivated')
        log = UserLog(
                 ip = request.environ.get("REMOTE_ADDR"),
                 user = user,
                 user_name = user.name,
                 url = 'login',
                 method = request.method,
                 browser = request.user_agent.browser,
                 version = request.user_agent.version,
                 platform = request.user_agent.platform,
                 uas = request.user_agent.string,
                 )
        log.save()

    def get_user(self):
        try:
            return User.objects(login=self.login.data.strip()).get()
        except Exception:
            labresult.app.logger.warning("%s does not match any user to log in."
                    % self.login.data)
            raise validators.ValidationError('Invalid user')

class CredentialForm(form.Form):
    channel = fields.TextField()
    user = None
    contact_by = None

    def _flash_info(self):
        flash(gettext("Les données saisies n'ont pas permis de vous"
            " identifier. Votre résultat n'est peut être pas"
            " encore disponible, ou votre saisie"
            " est incorrecte."), "error")

    def validate_channel(self, field):
        if not self.channel.data :
            raise validators.ValidationError(gettext(
                "Veuillez remplir la case ci-dessus"))
        if '@' in self.channel.data:
            email = self.channel.data.strip()
            try :
                self.user = User.objects(email=email).get()
                self.contact_by = 'email'
            except:
                self._flash_info()
                raise validators.ValidationError(gettext(
                    "L'email saisi ne permet pas de vous identifier."))
        else :
            mobile = re.sub(r"[^\d]","", self.channel.data)
            if not mobile :
                raise validators.ValidationError(gettext(
                    "Vous devez saisir une adresse email ou un numéro de"
                    " mobile valide")
                    )
            try :
                self.user = User.objects(mobile=mobile).get()
                self.contact_by = 'mobile'
            except:
                self._flash_info()
                raise validators.ValidationError(gettext(
                    "Le numéro saisi ne permet pas de vous identifier."))


class LoginView(AdminIndexView):

    welcome_pat = 'login/welcomepatient.html'
    welcome_hw = 'login/welcomehw.html'
    welcome_group = 'login/welcomegroup.html'
    welcome_admin= 'login/welcomeadmin.html'
    login_template = 'login/form.html'
    form_class = LoginForm
    credential_form = CredentialForm

    def is_visible(self):
        return False

    def _flash_bl(self):
        flash(gettext("Votre accès est bloqué suite à un trop"
                    " grand nombre d'échec, veuillez ré-essayer"
                    " ultérieurement."),
                    "error"
                    )
    @expose('/', methods=('GET', 'POST'))
    def index(self):
        form = self.form_class(request.form)
        status_code = 200

        if is_black_listed():
            self._flash_bl()
            status_code = 401

        form = self.form_class(request.form)

        if request.method == 'POST' and not is_black_listed():
            if form.validate():
                user = form.get_user()
                login.login_user(user)
                flash("Vous êtes maintenant connecté.")
            else :
                status_code = 401
                if black_list(form.login.data):
                    self._flash_bl()
                else:
                    flash("Nom d'utilisateur ou mot de passe invalide, impossible de vous identifier.", "error")


        if login.current_user.is_authenticated :
            if login.current_user._cls == 'User.Patient':
                return self.render(self.welcome_pat), status_code
            elif login.current_user._cls == 'User.HealthWorker':
                return self.render(self.welcome_hw), status_code
            elif login.current_user._cls == 'User.Group':
                return self.render(self.welcome_group), status_code
            elif 'User.Administrator' in login.current_user._cls:
                return self.render(self.welcome_admin), status_code

        return self.render(self.login_template, form=form,
                cform=self.credential_form()), status_code


    @expose('/logout', methods=('GET', 'POST'))
    def logout(self):
        if login.current_user.is_authenticated :
            login.logout_user()
            flash(gettext("Vous êtes maintenant déconnecté."))
        return redirect(url_for('index'))

    def _generate_credential(self,user):
        if user.credential_code :
            credential_age = datetime.now() - user.credential_code_date
            ttl = timedelta(minutes=get_option('credential_code.ttl', 20))

            if credential_age < ttl:
                return

        code = ''.join(["%s" % randint(0, 9) for num in range(0, 5)])
        user.credential_code = code
        user.credential_code_date = datetime.now()
        user.save()

    @expose('/credential', methods=('GET', 'POST'))
    def credential_view(self):
        cform = self.credential_form(request.form)
        if request.method == 'POST' and cform.validate():
            user = cform.user
            self._generate_credential(user)
            if cform.contact_by == 'mobile' and send_sms_credential(user) :
                    flash(gettext("Un code vient de vous être envoyé par SMS."))
                    return redirect(url_for('credential.index'))

            elif cform.contact_by == 'email' and send_email_credential(user):
                    flash(gettext("Un code vient de vous être envoyé par email."))
                    return redirect(url_for('credential.index'))
        return self.render(self.login_template, form=LoginForm(), cform=cform), 403
