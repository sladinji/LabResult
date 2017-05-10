from flask.ext.admin import expose
from flask.ext import login
from flask import request, flash, redirect
from wtforms import Form, TextField, PasswordField, validators
from functools import partial

from labresult.lib.auth import password_check, no_duplicate_login
from labresult.lib.model import get_option
from labresult.lib.views import LoggedinView
from flask.ext.babelex import gettext

class AccountForm(Form):
    check_login = partial(no_duplicate_login, except_current=True)
    login = TextField(gettext('Login'), [check_login],)
    password = PasswordField(gettext('Mot de passe'), [
        validators.Required(),
        password_check,
    ])
    confirm = PasswordField(gettext('Confirmation'))

class AccountView(LoggedinView):

    @expose('/', methods=('GET', 'POST'))
    def index(self):
        form = AccountForm(request.form)
        if request.method == 'POST' and form.validate():
            if form.login.data :
                login.current_user.login = form.login.data
            login.current_user.set_pass(form.password.data)
            login.current_user.save()
            flash(gettext('Vos identifiants ont été mis à jour'))
            return redirect('/')
        form.login.data = login.current_user.login
        return self.render("account/form.html", form=form, min_car= get_option('password_min_lenth', 8))

