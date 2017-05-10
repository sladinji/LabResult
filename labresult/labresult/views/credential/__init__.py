import traceback
from datetime import timedelta, datetime

from flask import url_for, request, flash, redirect
from flask.ext import login
from flask.ext.admin import expose, BaseView
from flask.ext.babelex import gettext
from wtforms import Form, TextField

import labresult
from labresult.lib.model import get_option
from labresult.model import User


class CredentialForm(Form):
    code= TextField(gettext('Code'))

class CredentialView(BaseView):

    def is_visible(self):
        return False

    @expose('/', methods=('GET', 'POST'))
    def index(self):
        form = CredentialForm(request.form)
        ttl = get_option("credential_code.ttl",
                20,
        gettext("Durée de validité en minutes d'un code"
        " d'authentification."))
        if request.method == 'POST' and form.validate() and form.code.data :
            try:
                user = User.objects(credential_code =
                        form.code.data.strip()).get()
                delta = datetime.now() - user.credential_code_date
                if delta < timedelta(minutes = ttl) :
                    login.login_user(user)
                    return redirect(url_for('account.index'))
                else:
                    flash(gettext("Le code saisi n'est plus valide, vous"
                        " devez recommencer la procédure."), "error")
                    return redirect("/")
            except labresult.model.db.DoesNotExist:
                labresult.app.logger.warning("Invalid credential code")
                flash(gettext("Le code saisi n'est pas valide"), 'error')
            except :
                labresult.app.logger.error(traceback.format_exc())
                flash(gettext("Le système à rencontrer un problème, veuillez"
                    " recommencer la procédure."), 'error')
                return redirect("/")
        return self.render("credential/form.html", form=form, ttl=ttl)

