"""
DB model.
"""


import datetime
from flask.ext.mongoengine import MongoEngine
from flask.ext.babelex import gettext
from jinja2 import Markup
db = MongoEngine()


class Underlay(db.Document):
    """
    PDF underlay
    """
    name = db.StringField()
    doc_types = db.ListField(db.StringField(), help_text=gettext("Types de"
    " documents sur lesquels l'entête sera appliquée.")
    )
    recto = db.FileField()
    verso = db.FileField()
    all_pages = db.BooleanField(default=False)
    comment = db.StringField()

    def __str__(self):
        if self.name :
            return self.name
        else :
            return "Sans nom"

class PrinterOption(db.EmbeddedDocument):
    """
    A printer option is associated with a document type. This allow to define
    on which tray a document type has to be printed on a printer.
    """
    document_type = db.StringField(verbose_name = gettext("Type de document"))
    """document type associated with option"""
    options = db.DictField(verbose_name = gettext("Options"))
    """lp option to pass when running command"""


class Printer( db.Document):
    is_default = db.BooleanField(default=False,
            verbose_name = gettext("Imprimante par défaut"))
    """ tells if this printer is the default one"""
    name = db.StringField(verbose_name = gettext("Nom"), required = True)
    """ the cups name """

    cups_host = db.StringField( default='localhost', required = True,
            verbose_name = gettext("Adresse serveur d'impression"))
    """Cups host of the printer"""

    cups_port = db.IntField( required=True, default=631,
            verbose_name = gettext("Port"))
    """Cups port of the printer"""

    activated = db.BooleanField(default=False, verbose_name =
            gettext("Activée"))
    """Activation status"""

    options = db.ListField(db.EmbeddedDocumentField(PrinterOption),
            verbose_name = gettext("Options"))

    @property
    def document_types(self):
        return [ o.document_type for o in self.options ]

    def __unicode__(self):
        return self.name or "Imprimante sans nom"


class Labo( db.Document ):
    # Columns
    external_id = db.StringField(
            verbose_name = gettext("ID externe")
            )
    """ Labo unique sglid """
    name = db.StringField(verbose_name = gettext("Nom"))
    """ Labo's name """
    address = db.StringField(verbose_name = gettext("Adresse"))
    """ The labo address """
    is_default = db.BooleanField(
            default = False,
            verbose_name = gettext("Labo par défaut"))
    """ If this is the default labo of the group """
    printers = db.ListField(db.ReferenceField('Printer',
        reverse_delete_rule=db.PULL),
        verbose_name = gettext("Imprimantes"),
        )
    underlays = db.ListField(db.ReferenceField('Underlay',
        reverse_delete_rule=db.NULLIFY),
        verbose_name = gettext("Entêtes"),
        )

    def __unicode__(self):
        return self.name if self.name else "Labo sans nom"

    def get_default_printer(self):
        """this function is able to give the default printer for a labo or None if no printer is default """
        defaults = [ p for p in self.printers if p.activated and p.is_default]
        if defaults:
            return defaults[0]

    def get_printer_by_doc_type(self, doctype):
        """this function is able to retrieve a printer with a doctype """
        defaults = [ p for p in self.printers if p.activated and
                p.document_types and doctype in p.document_types ]
        if defaults:
            return defaults[0]
        return None

channel_choices = ("email", "sms")

class Message(db.EmbeddedDocument):
    """
    Message sent to a user used to keep history in User object
    """
    title = db.StringField(verbose_name = gettext("Titre"))
    content = db.StringField(verbose_name = gettext("Contenu du message"))
    date = db.DateTimeField(default=datetime.datetime.now)
    destination = db.StringField(verbose_name = gettext("Adresse email ou"
    " n° de téléphone"))
    channel = db.StringField(max_length=5, choices = channel_choices)

class LogMessage(db.Document):
    """
    Message log, used for stats
    """
    date = db.DateTimeField(default=datetime.datetime.now)
    user = db.ReferenceField("User")
    title = db.StringField()
    channel = db.StringField(max_length=5, choices = channel_choices)
    provider = db.StringField(verbose_name = gettext("SMS provider or smtp"
    " server"))

# Define mongoengine documents
class User(db.Document):
    external_id = db.StringField(max_length=256, verbose_name =
    gettext("ID externe"))
    account_activated = db.BooleanField(default=False,
            help_text = gettext(
            "Connexion impossible si le compte n'est pas activé"),
            verbose_name = gettext("Compte activé"),
            )
    name = db.StringField(max_length=256, verbose_name = gettext("Nom"))
    firstname = db.StringField(max_length=256, verbose_name = gettext("Prénom"))
    lastname = db.StringField(max_length=256,
            verbose_name = gettext("Nom de famille"))
    civility = db.StringField(max_length=16, verbose_name = gettext("Civilité"))
    birthdate = db.DateTimeField(verbose_name = gettext("Naissance"))
    mobile = db.StringField(max_length=32, verbose_name = gettext("Mobile"))
    fixe = db.StringField(max_length=32, verbose_name = gettext("Fixe"))
    email = db.EmailField(max_length=120, verbose_name = gettext("Courriel"))
    address1= db.StringField(max_length=256, verbose_name = gettext("Adresse"))
    address2= db.StringField(max_length=256, verbose_name = "")
    address3= db.StringField(max_length=256, verbose_name = "")
    password = db.StringField(max_length=256,
        verbose_name = gettext("Mot de passe"))
    login = db.StringField(max_length=80, verbose_name = gettext("Login"))
    credential_code = db.StringField(max_length=12, verbose_name =
            gettext("Code d'authentification"))
    credential_code_date = db.DateTimeField(default=None)
    messages = db.ListField(db.EmbeddedDocumentField(Message))

    meta = {
        'allow_inheritance' : True,
        'indexes':[
                {'fields': ['-login'], 'unique': True, 'sparse': True, 'types': False},
                ],
    }

    def __init__(self, **kwargs):
        """
        Hash pass if present in kwargs.
        """
        if "pass2hash" in kwargs:
            pass2hash = kwargs.pop('pass2hash')
            super().__init__(**kwargs)
            self.set_pass(pass2hash)
        else :
            super().__init__(**kwargs)


    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return self.account_activated

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __unicode__(self):
        return self.name if self.name else "?"

    def set_pass(self, pwd):
        """
        Hash password
        """
        from labresult.lib.crypto import hashpass
        self.password = hashpass(pwd)

    def match_pass(self, pwd):
        from labresult.lib.crypto import hashpass
        return hashpass(pwd) == self.password


class UserLog(db.Document):
    date = db.DateTimeField(default=datetime.datetime.now)
    ip = db.StringField()
    user = db.ReferenceField(User)
    user_name = db.StringField()
    url = db.StringField()
    method = db.StringField()
    args = db.StringField()
    browser = db.StringField()
    version = db.StringField()
    platform = db.StringField()
    uas = db.StringField()

class Patient(User):
    secu = db.StringField(max_length=15,
            verbose_name = gettext("N° sécu"))
    tutor = db.ReferenceField(User, reverse_delete_rule=db.NULLIFY,
            verbose_name = gettext("Tuteur"))

    def last_result(self):
        """
        Return the id of last result.
        """
        from labresult.api.board import Board
        self._cls = "User.Patient"
        qry = Board()._get_qry(user=self)
        doc = qry.first()
        if doc :
            return str(doc.id)
        else :
            return ''

class Group(User):
    comment = db.StringField(verbose_name = gettext("Commentaire"))
    """Comment for describing group"""

    @property
    def members(self):
        return HealthWorker.objects(groups__user = self)

class GroupMember(db.EmbeddedDocument):
    user = db.ReferenceField(Group, verbose_name = gettext("Groupe"))
    share = db.BooleanField(default=True, verbose_name = gettext("Partage"))

    def __str__(self):
        return self.group.name

class HealthWorker(User):
    groups = db.ListField(db.EmbeddedDocumentField(GroupMember),
            help_text = gettext(
            "L'utilisateur peut accéder aux documents des groupes auxquels il"
            " appartient, et partage ses documents avec le groupe si l'option"
            ' "partage" est activée.'),
            verbose_name = gettext("Groupes"),
            )

class View(db.Document):
    """
    Web site view
    """
    name = db.StringField(verbose_name = gettext("Nom"))
    url = db.StringField()
    menu_name = db.StringField()
    model = db.StringField()

    def __str__(self):
        name = None
        if self.menu_name :
            name = Markup(self.menu_name)
        return name if name else "{0} ({1})".format(self.name, self.url)

class Right(db.EmbeddedDocument):
    """
    Right for admin role on website view
    """
    view = db.ReferenceField(View, verbose_name = gettext("Vue"))
    create = db.BooleanField( verbose_name = gettext("Création"))
    read = db.BooleanField( verbose_name = gettext("Lecture"))
    update = db.BooleanField( verbose_name = gettext("Edition"))
    delete = db.BooleanField( verbose_name = gettext("Suppression"))


class AdminRole(db.Document):
    """
    Biologist, secretary, etc...
    """
    name = db.StringField(verbose_name = gettext("Nom"))
    acl = db.ListField(db.EmbeddedDocumentField(Right),
            verbose_name = "Droits",
            help_text = "Droits d'accès pour le role, peuvent être ajuster au"
            " niveau de chaque utilisateur.")

    def __str__(self):
        return self.name

class Administrator(User):
    role = db.ReferenceField(AdminRole)
    special_acl = db.ListField(db.EmbeddedDocumentField(Right),
            help_text = gettext("Droits particuliers à l'utilisateur, priment"
                " sur les droits définis au niveau du role."),
            verbose_name = gettext("Droits"))
    labos = db.ListField(db.ReferenceField("Labo"),
            help_text = gettext("Liste des laboratoires accessibles à"
                " l'utilisateur (laisser la liste vide pour garder tous les"
                " laboratoires accessibles)"),
            verbose_name = gettext("Laboratoires"))

    def get_right(self, model):
        for right in self.special_acl :
            if right.view.model == model :
                return right
        if not self.role :
            #no role mean super admin
            return Right(create=True, read=True, update=True, delete=True)
        for right in self.role.acl :
            if right.view.model == model :
                return right
        return Right()

class AdminGeneric(Administrator):
    """
    Subclass Administrator to be distinct of Biologist.
    """
    pass

class Biologist(Administrator):
    """
    Biologist is the only user type which can be associated with a document as
    biologist.
    """
    pass

class Img(db.Document):
    """
    Image of document.
    """
    format_ = db.StringField(max_length=3, verbose_name = gettext("Format"))
    data = db.FileField(verbose_name = gettext("Fichier"))
    thumbnail = db.FileField(verbose_name = gettext("Miniature"))
    page_num = db.IntField(verbose_name = gettext("Numéro de page"))

class PrintJob( db.EmbeddedDocument ):
    """
    EmbeddedDocument for document.
    """
    UNKNOW         = 0
    JOB_ABORTED    = 1
    JOB_COMPLETED  = 2
    JOB_PENDING    = 3
    JOB_STOPPED    = 4
    JOB_CANCELED   = 5
    JOB_HELD       = 6
    JOB_PROCESSING = 7

    cups_jobs_state_labels = {
        UNKNOW : str('unknow'),
        JOB_ABORTED: str('aborted'),
        JOB_COMPLETED: str('completed'),
        JOB_PENDING: str('pending'),
        JOB_STOPPED: str('stopped'),
        JOB_CANCELED: str('canceled'),
        JOB_HELD: str('held'),
        JOB_PROCESSING: str('processing'),
    }


    cups_job_id = db.IntField(verbose_name = gettext("ID travail d'impression"))
    job_date = db.DateTimeField(default=datetime.datetime.now,
            verbose_name = gettext("Date d'impression"))
    printer = db.ReferenceField('Printer', verbose_name = gettext("Imprimante"))
    job_status = db.IntField(default=0, verbose_name = gettext("Statut"))

    def __unicode__(self) :
        try :
            return self.cups_jobs_state_labels[self.job_status]
        except :
            return self.cups_jobs_state_labels[0]

class Log(db.EmbeddedDocument):
    """
    Date an IP address for tracking.
    """
    date = db.DateTimeField()
    ip = db.StringField()

class Access(db.EmbeddedDocument):
    """
    Access composed of User and right, and define if a user can access a
    document.
    """
    user = db.ReferenceField(User, verbose_name = gettext("Utilisateur"))
    """User concerned"""
    read = db.BooleanField(default=False, verbose_name = gettext("Accessible"))
    """is document readable by user ?"""
    pub_date = db.DateTimeField(default=None, verbose_name =
            gettext("Disponible depuis"))
    """when document was available"""
    comment = db.StringField(verbose_name = gettext("Raison de non diffusion"))
    """why document is not accessible or whatever"""
    #TODO : fill logs
    logs = db.ListField(db.EmbeddedDocumentField(Log), verbose_name =
    gettext("Journaux"))
    """Access done by user (Date - IP), or whatever"""

    meta = {
        'allow_inheritance' : True,
        }

class PatientAccess(Access):
    user = db.ReferenceField(Patient, verbose_name = gettext("Patient"))

class TutorAccess(Access):
    user = db.ReferenceField(Patient, verbose_name = gettext("Tuteur"))

class HealthWorkerAccess(Access):
    user = db.ReferenceField(HealthWorker, verbose_name = gettext(
    "Professionel de santé"))
    role = db.StringField(verbose_name = gettext("Rôle"))
    """doctor, corres ..."""

class GroupAccess(Access):
    user = db.ReferenceField(Group, verbose_name = gettext("Groupe"))

class Document(db.Document):
    #document constant status
    NEW = 0
    OK = 1
    ERROR = -1

    data = db.FileField(verbose_name = gettext("Fichier"))
    """Raw data"""
    parser_name = db.StringField(max_length=32, verbose_name = gettext("Parser"))
    """Parser name"""
    doc_type = db.StringField(max_length=256, verbose_name = gettext("Type de"
    " document"))
    """Type of document (CR patient, Ordonnance...)"""
    text = db.StringField(verbose_name = gettext("Texte"))
    """Text extracted from document"""
    capture_date = db.DateTimeField(default=datetime.datetime.now, verbose_name
            = gettext("Date de capture"))
    date_dossier = db.DateTimeField(default=None)
    """Date when document was recorded in the system"""
    numdos = db.StringField(max_length=128, verbose_name = gettext("Numéro de"
    " dossier"))
    """Folder number"""
    patient = db.EmbeddedDocumentField(PatientAccess, required=False,
            verbose_name = gettext("Patient"))
    """Patient associated with this document"""
    biologist = db.ReferenceField(Biologist, reverse_delete_rule=db.NULLIFY)
    """Biologist associated with this document"""
    healthworkers = db.ListField(db.EmbeddedDocumentField(HealthWorkerAccess),
            verbose_name = gettext("Professionnels de santé"))
    """Health workers associated with the document"""
    groups = db.ListField(db.EmbeddedDocumentField(GroupAccess), verbose_name =
            gettext("Groupes"))
    """Group associated with document"""
    tutor = db.EmbeddedDocumentField(TutorAccess, required=False, verbose_name
            = gettext("Tuteur"))
    """Tutor's access"""
    tags = db.StringField(max_length=256, verbose_name = gettext("Mots clés"))
    """Tags assiciated with documents"""
    patient_name = db.StringField(max_length=256, verbose_name = gettext("Nom"
    " patient"))
    """Patient name"""
    healthworkers_name = db.StringField(max_length=512, verbose_name =
            gettext("Noms professionels de santé"))
    """Names of health workers separated by spaces"""
    log = db.StringField(verbose_name = gettext("Journaux"))
    """Error log"""
    warnings = db.StringField(verbose_name = gettext("Avertissements"))
    """Warnings log"""
    traceback = db.StringField(verbose_name = gettext("Erreur de traitement"))
    """HTML traceback when error occured during integration"""
    status = db.IntField(default=0, verbose_name = gettext("Statut"))
    """NEW, OK, ERROR..."""
    origin = db.StringField(max_length=64, verbose_name = gettext("Origine"))
    """Where the document come from (printer...)"""
    pdf = db.FileField(verbose_name = gettext("PDF"))
    """Document in PDF format"""
    signed = db.BooleanField(verbose_name = gettext("Signé"), default=False)
    """Is PDF signed"""
    signature_tries = db.IntField(
        verbose_name = gettext("Nombre de tentatives de signature"),
        default = 0)
    """How many signature fails"""
    signature_error = db.StringField(
            verbose_name=gettext("Erreur lors de lasignature du fichier"))
    """Signature error label"""
    pdf_nb_pages = db.IntField(verbose_name = gettext("Nombres de pages"))
    """Number of pages in the PDF document"""
    imgs = db.ListField(db.ReferenceField(Img, reverse_delete_rule=db.PULL))
    """PNG images of the document"""
    print_jobs = db.ListField(db.EmbeddedDocumentField(PrintJob), verbose_name
            = gettext("Travaux d'impression"))
    """Printing jobs"""
    labo = db.ReferenceField(Labo, reverse_delete_rule = db.NULLIFY,
            verbose_name = gettext("Laboratoire"))
    """Labo producer"""
    version = db.IntField(default=0, verbose_name = gettext("Version"))
    """version number"""
    current_version = db.BooleanField(default=True, verbose_name =
    gettext("Version courante"))
    """Is the current_version the last one"""
    underlay = db.ReferenceField('Underlay',
        reverse_delete_rule=db.NULLIFY, verbose_name = gettext("Entête"))

    meta = {
        'allow_inheritance' : False,
        'indexes':[
                '-numdos',
                '-capture_date',
                ],
    }
    # Required for administrative interface
    def __unicode__(self):
        return "{0.doc_type} : {0.numdos}".format(self) if self.numdos else "?"

class Option(db.Document):
    key = db.StringField()
    value = db.StringField()
    description = db.StringField()
    visible = db.BooleanField(default=True)
    """If False, option will not be visible through IHM"""

    meta = { 'allow_inheritance' : True,
        'indexes':[
                {'fields': ['-key'], 'unique': True, 'sparse': True, 'types': False},
                ],
        }

class IntOption(Option):
    value = db.IntField()

class StringOption(Option):
    value = db.StringField()

class ListOption(Option):
    value = db.ListField()

class FileOption(Option):
    value = db.FileField()

class PublicationRuleException(Exception):
    pass

class PublicationRule(db.Document):
    """
    Class discribing publication rules. If PublicationRule.apply return False,
    this means that document won't be publish, and True means this rule allow
    publication.
    """
    comment = db.StringField(verbose_name = gettext("Commentaire"))
    msg_error = db.StringField( verbose_name = gettext("Message"),
            help_text = gettext("Ce message apparaitra dans les journaux"
            " pour expliquer pourquoi le document n'est pas accessible")
            )
    """Comment put in log when rule returns false"""
    user = db.StringField(verbose_name = gettext("Utilisateur"))
    """User type, can be "patient" or "doctor" or "corres" or "preleveur" """
    rule = db.StringField(verbose_name = gettext("Règle"))
    """Rule to apply"""
    activated = db.BooleanField(help_text=gettext("Une règle de diffusion"
    " sert à définir les droits d'accès à un document. Elle ne s'applique que"
    " lorsqu'elle est activée. Si la règle retourne vrai, le document est"
    " accessible."),
    verbose_name = gettext("Activée"),
    )

    def _check_rule(self):
        blacklist = ["__", "import", "delete", "rm", "exec"]
        for word in blacklist :
            if word in self.rule :
                raise PublicationRuleException( "Rule can't contain %s" % word)

    def apply(self, doc):
        self._check_rule()
        return eval(self.rule)

    def __str__(self):
        try :
            return '<Rule %s : %s>' % (self.user, self.comment)
        except:
            return "<Rule invalid>"

class FailedLogin(db.Document):
    last = db.DateTimeField(default=datetime.datetime.utcnow)
    total = db.IntField()
    ip = db.StringField()
    login = db.StringField()
    meta = {
        'indexes': [
            {'fields': ['last'], 'expireAfterSeconds': 3600}
        ]
    }
