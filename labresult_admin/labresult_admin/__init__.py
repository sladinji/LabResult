from io import BytesIO

import lxml.etree as ET
from flask_babelex import gettext
from flask_admin.actions import action
from flask_admin.babel import lazy_gettext
from flask_admin.form import rules
from flask import url_for, redirect, flash, request
from flask_admin import expose
from flask_admin.helpers import get_redirect_target
from wtforms.fields import PasswordField, FileField, TextField
from wtforms.widgets import TextArea
from flask import send_file
import pdfquery

import labresult
from labresult.builder.validator import Validator
from labresult.views.admin import UserView, id_markup, con_markup, labo_markup, opts_markup, print_markup
from labresult.views.admin import auth_markup, dif_markup, act_markup, file_markup, opt_markup
from labresult.lib.views import frmt_acl, format_user
from labresult.lib.views import AuthView, frmt_pat_name, frmt_healthworker_name, frmt_numdos, frmt_doc_type
from labresult.api.board import Board
from labresult.builder.tasks import integrate
from labresult.model import Option, FileOption, Document, FailedLogin
from labresult.printing import printdoc
from labresult.lib.model import set_option, get_option
import labresult.views.admin as admin
from labresult.lib.model import get_readable_name


class AdminView(UserView):
    list_template = "admin/admin_list.html"
    column_list = ('name',  'role', 'fixe', 'email', 'account_activated')
    form_create_rules = [
        rules.FieldSet(('name', 'mobile', 'fixe', 'email'), id_markup),
        rules.FieldSet(('login', 'password_holder', 'confirm',
                        'account_activated'), con_markup),
        rules.FieldSet(('role', 'special_acl', "labos"), auth_markup),
        ]

    form_edit_rules = form_create_rules
    form_args = {'labos': {'allow_blank': True}}

    def on_model_change(self, form, model, is_created):
        """
        Empty labos list when no labo id is posted (looks like a flask admin
        bug)
        """
        super(AdminView, self).on_model_change(form, model, is_created)
        if 'labos' not in request.form:
            model.labos = []


class BiologistView(AdminView):
    list_template = "admin/biolo_list.html"
    form_create_rules = [
        rules.FieldSet(('name', 'mobile', 'fixe', 'email'), id_markup),
        rules.FieldSet(('login', 'password_holder', 'confirm',
                        'account_activated'), con_markup),
        rules.FieldSet(('special_acl', "labos"), auth_markup),
        ]
    form_edit_rules = form_create_rules


class RoleView(AuthView):
    list_template = "admin/role_list.html"
    allowed_users = ['User.Administrator']
    form_create_rules = [
        rules.FieldSet(('name', 'acl'), id_markup),
    ]
    form_edit_rules = form_create_rules
    column_list = ('name', 'acl')
    column_formatters = {'acl': frmt_acl}


class DocumentView(AuthView):

    allowed_users = ['User.Administrator']
    list_template = "admin/doc_admin_list.html"
    # True means descending = True
    column_default_sort = ('capture_date', True)
    column_list = ('doc_type', 'date_dossier', 'numdos', 'patient',
                   'healthworkers_name')
    column_labels = dict(data=gettext("Fichiers"), doc_type=gettext("Type"),
                         healthworkers_name=gettext("Professionnels"),
                         patient_name=gettext("Patient"), numdos=gettext("Dossier"), origin=gettext("Provenance"),
                         status=gettext("Statut"), signed=gettext("Document signé"),)

    column_filters = ['numdos', 'patient_name', 'healthworkers_name', 'status', 'origin', 'signed']

    column_searchable_list = ('numdos', 'patient_name', 'healthworkers_name')

    form_columns = ('version', 'current_version', 'labo', 'patient', 'biologist', 'signed', 'healthworkers', 'groups',
                    'log', 'doc_type', 'numdos', 'traceback', 'data', 'pdf')

    column_formatters = {
            'patient': frmt_pat_name,
            'healthworkers_name': frmt_healthworker_name,
            'numdos': frmt_numdos,
            'doc_type': frmt_doc_type,
            }

    def get_query(self):
        return Board()._get_qry()

    def get_count_query(self):
        return self.get_query().count()

    def after_model_change(self, form, model, is_created):
        if is_created:
            # build doc, not used for now (creation is done via restful api)
            #integrate.delay(doc_id=model.id)
            pass
        else:
            # reset healthworkers_name, corres_name...
            Validator.doc_validator.denormalize(model)

    @expose('/pdf2xml/<string:id>')
    def pdf2xml(self, id):
        """
        Return XML representation of a PDF (helpful to configure PDF extraction)
        """
        doc = Document.objects(id=id).get()
        pdf = pdfquery.PDFQuery(doc.pdf)
        pdf.load(0)
        xml = BytesIO(ET.tostring(pdf.get_tree(0)))
        return send_file(xml, mimetype="text/xml",
                         attachment_filename=get_readable_name(doc) + ".xml",
                         as_attachment=True,
                         cache_timeout=10000, add_etags=False)

    @expose('/reset_doc/<string:id>')
    def reset_doc(self, id):
        return_url = get_redirect_target() or url_for('.index_view')
        doc_id = integrate.delay(doc_id=id).get()
        doc = Document.objects(id=doc_id).get()
        if doc.log:
            msg = gettext(doc.log).lower()
            prefix = gettext("Problème avec le document : ")
            flash("%s %s" % (prefix, msg), 'error')
        else:
            flash(gettext('Document repassé : %s').format(doc))
        return redirect(return_url)

    @action('reset',
            lazy_gettext('Repasser'),
            lazy_gettext('Êtes vous sur de vouloir repasser les documents sélectionnés ?'))
    def action_reset(self, ids):
        try:
            for pk in ids:
                integrate.delay(doc_id=pk)
            flash("Documents correctement envoyés en ré-intégration")
        except Exception as ex:
            msg = gettext("Erreur lors de la réintégration des documents (%s)")
            flash(msg.format(str(ex)), 'error')

    @expose("/print_doc/<string:id>")
    def print_doc(self, id):
        return_url = get_redirect_target() or url_for('.index_view')
        try:
            doc = Document.objects.get(id=id)
            printdoc(doc)
            job = doc.print_jobs[-1]
            msg = gettext("Impression OK ( id du job : %s )")
            flash(msg.format(job.cups_job_id))
        except Exception as ex:
            flash(gettext("Erreur lors de l'impression du document (%s)").format(str(ex)), 'error')
        return redirect(return_url)

    @action('print',
            lazy_gettext('Imprimer'),
            lazy_gettext('Êtes vous sur de vouloir imprimer les documents sélectionnés ?'))
    def action_print(self, ids):
        try:
            for pk in ids:
                doc = Document.objects.get(id=pk)
                printdoc(doc)
            flash(gettext("Impression demandée pour les document sélectionnés."))
        except Exception as ex:
            msg = gettext(
                    "Erreur lors de la demande d'impression des documents (%s)"
                    )
            flash(msg.format(str(ex)), 'error')


class LaboView(AuthView):
    list_template = "admin/labo_list.html"
    allowed_users = ['User.Administrator']
    column_searchable_list = ('external_id',  'name', 'address')
    column_filters = ('external_id', 'name', 'address')
    form_create_rules = [
        rules.FieldSet(('name', 'external_id', 'address'), labo_markup),
        rules.FieldSet(('printers', 'underlays', 'is_default'), opts_markup),
        ]
    form_edit_rules = form_create_rules
    column_labels = dict(
        name=gettext("Nom"),
        external_id=gettext("Identifiant externe"),
        address=gettext("Adresse"),
        is_default=gettext("Labo par défaut"),
        printers=gettext("Imprimantes"),
        underlays=gettext("Entêtes"),
    )
    form_args = {'printers': {'allow_blank': True},
                 'underlays': {'allow_blank': True},
                 }


class PrinterView(AuthView):
    allowed_users = ['User.Administrator']
    column_searchable_list = ('name',  'cups_host')
    form_create_rules = [
        rules.FieldSet(('name', 'cups_host', 'cups_port'), print_markup),
        rules.FieldSet(('is_default', 'activated', 'options'), opts_markup),
        ]
    form_edit_rules = form_create_rules
    list_template = "admin/printer_list.html"


class PublicationView(AuthView):
    list_template = "admin/pub_list.html"
    allowed_users = ["User.Administrator"]
    column_searchable_list = ('comment',  'user', 'rule', 'msg_error')
    column_filters = ('comment', 'user', 'rule', 'activated')
    column_list = ('user', 'comment', 'msg_error', 'activated')
    form_create_rules = [
        rules.FieldSet(('user', 'rule', 'msg_error'), dif_markup),
        rules.FieldSet(('activated', 'comment'), act_markup),
        ]
    column_labels = dict(
        user=gettext("Utilisateur"),
        comment=gettext("Commentaire"),
        msg_error=gettext("Message"),
        activated=gettext("Activé"),
    )
    form_edit_rules = form_create_rules

    def after_model_change(self, form, model, is_created):
        """
        restart celery in order to refresh rules
        """
        labresult.celery.control.broadcast('pool_restart')


class UnderlayView(AuthView):
    allowed_users = ['User.Administrator']
    form_create_rules = [
        rules.FieldSet(('name', 'comment', 'all_pages'), opts_markup),
        rules.FieldSet(('recto', 'verso', 'doc_types',), file_markup),
        ]
    form_edit_rules = form_create_rules
    list_template = "admin/header_list.html"


class PolymorphField(TextField):
    """
    Option value can be file or string, this field return the appropriate
    widget according to requested option.
    """
    @property
    def widget(self):
        m = Option.objects(id=request.args['id']).get()
        if isinstance(m, FileOption):
            return FileField.widget
        else:
            return TextArea() if m.visible else PasswordField.widget


class OptionView(AuthView):
    list_template = "admin/option_list.html"
    allowed_users = ['User.Administrator']
    form_create_rules = [
        rules.FieldSet(('key', 'value', 'description'), opt_markup),
        ]

    column_list = ('key', 'value', 'description')
    form_columns = ('key', 'value', 'description')
    form_edit_rules = form_create_rules
    column_filters = ('key',  'description')
    column_searchable_list = ('key', 'description')
    # form_overrides = dict(value=PolymorphField)
    # bug in v 1.3.0
    column_formatters = {'value': lambda v, c, m, p: m.value if m.visible else "*" * len(m.value)}
    can_create = True

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            set_option(model.key, model.value, model.description)
        except Exception as ex:
            flash(gettext('%(error)s', error=str(ex)),
                  'error')
            return False
        return True

    def update_model(self, form, model):
        try:
            form.populate_obj(model)
            set_option(model.key, model.value, model.description, model.visible)
        except Exception as ex:
            if 'duplicate key' in str(ex):
                flash(gettext(
                    "L'option est de type %(type)s. La valeur que vous avez "
                    "saisie est incorrecte pour ce type."
                    "Si vous souhaitez changer de type d'option, vous devez d'abord la supprimer.",
                    type=model.__class__.__name__),
                    'error')
            else:
                flash(gettext('%(error)s', error=str(ex)), 'error')
            return False
        return True


class IPUnblockView(AuthView):
    allowed_users = ['User.Administrator']
    can_edit = False
    can_create = False
    list_template = "admin/ip_lock_list.html"

    @property
    def query(self):
        max_fail = get_option("max_login_attempt", 20, gettext(
            "Nombre maximal d'échec de connexion avant blocage."
            ))
        return FailedLogin.objects(total__gt=max_fail)

    def get_query(self):
        return self.query

    def get_count_query(self):
        return self.query.count()


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


def load_views(reg_view, create_aview, user_menu, param_menu):
    admin.AdminView = AdminView
    admin.BiologistView = BiologistView
    admin.RoleView = RoleView
    admin.DocumentView = DocumentView
    admin.LaboView = LaboView
    admin.PrinterView = PrinterView
    admin.PublicationView = PublicationView
    admin.UnderlayView = UnderlayView
    admin.PolymorphField = PolymorphField
    admin.OptionView = OptionView
    admin.IPUnblockView = IPUnblockView
    admin.UserLogView = UserLogView

    reg_view(create_aview('Document', gettext('Documents'), 'drawer4', 'DocumentView'))
    reg_view(create_aview('AdminGeneric',
                          gettext('Personnel du laboratoire'), 'microscope23', 'AdminView', category=user_menu)
             )
    reg_view(create_aview('Biologist',
                          gettext('Biologistes'), 'scientist', category=user_menu)
             )
    reg_view(create_aview('AdminRole', gettext('Rôles'), 'edit1', 'RoleView', category=user_menu))
    reg_view(create_aview('Labo', gettext('Laboratoires'), 'microscope23', category=param_menu))
    reg_view(create_aview('Underlay', gettext('Entêtes'), 'text20', category=param_menu))
    reg_view(create_aview('Printer', gettext('Imprimantes'), 'printer53', category=param_menu))
    reg_view(create_aview('Option', gettext('Options'),  'adjust3', category=param_menu))
    reg_view(create_aview('PublicationRule',
                          gettext('Règles de diffusion'), 'programming', 'PublicationView',
                          category=param_menu)
             )
    reg_view(create_aview('FailedLogin',
                          gettext('IP bloquées'), 'firewall13', 'IPUnblockView',
                          category=param_menu)
             )
    reg_view(create_aview('UserLog', gettext('Journaux'), 'text20', category=param_menu))
