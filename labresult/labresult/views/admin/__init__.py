from flask_admin.form import rules
from flask.ext.babelex import gettext
from jinja2 import Markup
from wtforms.fields import PasswordField

from labresult.api.board import Board
from labresult.lib.auth import password_check, no_duplicate_login
from labresult.lib.views import AuthView, frmt_group_name, format_user, format_members, frmt_doc_type
from labresult.model import Document, HealthWorker
from labresult.model import Patient

labo_markup = Markup('<span class="itemic flaticon-microscope23"></span> Laboratoire')
file_markup = Markup('<span class="itemic flaticon-text20"></span> Fichiers')
id_markup = Markup('<span class="flaticon-personal19"></span> Identité')
con_markup = Markup('<span class="flaticon-password17"></span> Accès')
adr_markup = Markup('<span class="flaticon-house109"></span> Adresse')
ct_markup = Markup('<span class="flaticon-phone43"></span> Contacts')
grp_markup = Markup('<span class="flaticon-multiple25"></span> Groupes')
opt_markup = Markup('<span class="itemic flaticon-adjust3"></span> Option')
opts_markup = Markup('<span class="itemic flaticon-adjust3"></span> Options')
act_markup = Markup('<span class="itemic flaticon-adjust3"></span> Activation')
dif_markup = Markup('<span class="itemic flaticon-programming"></span> Règle de diffusion')
print_markup = Markup('<span class="itemic flaticon-printer53"></span> Imprimante')
auth_markup = Markup('<span class="itemic flaticon-adjust3"></span> Autorisations')


# Customized admin views
class UserView(AuthView):
    allowed_users = ['User.Administrator']
    column_filters = ('name', 'mobile', 'fixe', 'email', 'external_id', 'account_activated')
    column_searchable_list = ('name', 'mobile', 'fixe', 'email', 'external_id')
    column_list = ('name',  'mobile', 'fixe', 'email', 'account_activated')
    form_excluded_columns = ('password')
    form_extra_fields = {
        'password_holder': PasswordField('Mot de passe', [password_check]), 'confirm': PasswordField('Confirmation')
    }
    form_args = dict(
        login={'validators': [no_duplicate_login]}, birthdate=dict(format='%d/%m/%Y')
        # changes how the input is parsed by strptime (12 hour time)
    )
    form_widget_args = dict(birthdate={'data-date-format': u'dd/mm/yyyy',
                                       # changes how the DateTimeField displays the time
                                       }
                            )

    column_labels = dict(
        name=gettext("Nom"),
        account_activated=gettext("Compte activé"),
        groups=gettext("Groupes"),
        comment=gettext("Commentaire"),
        members=gettext("Membres"),
    )

    def on_model_change(self, form, model, is_created):
        if form.password_holder.data:
            model.set_pass(form.password_holder.data)


class PatientView(UserView):
    list_template = "admin/patient_list.html"
    form_create_rules = [
        rules.FieldSet(('name', 'external_id', 'birthdate', 'secu'), id_markup),
        rules.FieldSet(('login', 'password_holder', 'confirm', 'account_activated'), con_markup),
        rules.FieldSet(('address1', 'address2', 'address3'), adr_markup),
        rules.FieldSet(('mobile', 'fixe', 'email'), ct_markup),
        ]

    form_edit_rules = form_create_rules

    def on_model_delete(self, model):
        Document.objects(patient__user=model).delete()
        Patient.objects(tutor=model).update(set__tutor=None)


class HealthWorkerView(UserView):
    list_template = "admin/ps_list.html"
    column_list = ('name',  'mobile', 'fixe', 'email', 'groups', 'account_activated')

    column_formatters = {'groups': frmt_group_name}

    form_create_rules = [
        rules.FieldSet(('name', 'external_id', 'mobile', 'fixe', 'email'), id_markup),
        rules.FieldSet(('login', 'password_holder', 'confirm', 'account_activated'), con_markup),
        rules.FieldSet(('address1', 'address2', 'address3'), adr_markup),
        rules.FieldSet(('groups',), grp_markup),
        ]

    form_edit_rules = form_create_rules

    def on_model_delete(self, model):
        """Delete hw reference in documents"""
        Document.objects(healthworkers__match={'user': model.id}).update(pull__healthworkers__user=model)


class GroupView(UserView):
    list_template = "admin/group_list.html"
    column_list = ('name', 'comment', 'members', 'account_activated')

    form_create_rules = [
        rules.FieldSet(('name', "comment"), id_markup),
        rules.FieldSet(('login', 'password_holder', 'confirm', 'account_activated'), con_markup),
        rules.FieldSet(('mobile', 'fixe', 'email'), ct_markup),
        rules.FieldSet(('address1', 'address2', 'address3'), adr_markup),
        ]
    form_widget_args = {'name': {'style': {'color': 'red'}}}
    form_edit_rules = form_create_rules
    create_template = 'rule_create.html'
    edit_template = 'rule_edit.html'
    column_formatters = {'members': format_members}

    def on_model_delete(self, model):
        """Delete  group reference in hw and documents"""
        for cls in Document, HealthWorker:
                cls.objects(groups__match={'user': model.id}).update(pull__groups__user=model)


class DocumentPatientView(AuthView):
    allowed_users = ['User.Patient']
    action_disallowed_list = ['delete']
    can_create = False
    can_edit = False
    can_delete = True
    column_list = ('doc_type', 'date_dossier', 'numdos')
    column_labels = dict(doc_type='Type de document', date_dossier='Date', numdos='Numéro de dossier')
    list_template = "admin/doc_patient_list.html"
    column_formatters = {'doc_type': frmt_doc_type}

    def get_query(self):
        return Board()._get_qry()

    def get_count_query(self):
        return self.get_query().count()


class DocumentHealthWorkerView(DocumentPatientView):
    allowed_users = ['User.HealthWorker']
    column_list = ('patient_name', 'date_dossier', 'doc_type', 'numdos')
    column_searchable_list = ('numdos', 'patient_name')
    list_template = "admin/doc_hw_list.html"
    column_formatters = {'doc_type': frmt_doc_type}


class DocumentGroupView(DocumentHealthWorkerView):
    allowed_users = ['User.Group']
    list_template = "admin/group_list.html"


class UserLogView(AuthView):
    list_template = "admin/log_list.html"
    column_default_sort = ('date', True)
    column_list = ('date', 'user', 'ip', 'url', 'args', 'platform', 'uas')
    column_labels = dict(
        use=gettext('Utilisateur'),
        platform=gettext('Système'),
        uas=gettext('Détails système'),
        ip='IP',
        url='URL',
        args="Arguments",
    )
    column_filters = ('date',  'user_name', 'ip', 'url', 'platform', 'uas')
    allowed_users = ['User.Administrator']
    column_searchable_list = ('user_name', 'url')
    can_create = False
    can_edit = False
    can_delete = False
    column_formatters = {'user': format_user, 'date': lambda v, c, m, p: m.date.strftime("%d-%m-%y %H:%M:%S")}
