import re
import warnings
from datetime import datetime
from labresult.model import User

class UserValidator:
    """
    Do some checks on integrated user.
    """
    def validate(self, user):
        """
        Actually check birthdate and complete name if name is splitted over
        prefix, lastname and firstname.
        :param user: :class:`labresult.model.User`
        """
        lnames = [ user.civility, user.firstname, user.lastname ]
        lnames = [ x.strip() for x in lnames if x and x.strip()]
        if len(lnames) >= 2 :
            user.name = ' '.join(lnames)
        if user.birthdate and isinstance(user.birthdate, str) :
            try :
                clean_date = re.sub(r"[^\d]", "", user.birthdate)
                user.birthdate = datetime.strptime(clean_date, "%d%m%Y")
            except:
                warnings.warn("Invalid birthdate {0}".format(user.birthdate))
                user.birthdate = None

class DocumentValidatorException(Exception):
        pass

class DocumentValidator:
    """
    Do some checks on integrated document to put in error document with partial
    or invalid data.
    """

    def _check_integrity(self, doc) :
        """
        Check document on :

         * patient presence for CR*
         * external_id for patient
         * date_dos for CR
         * doctor presence for CR_DOCTOR
         * sampler presence for CR_SAMPLER
         * numdos presence

        :param doc: :class:`model.Document`
        """
        if doc.doc_type.startswith('CR'):
            checks = [
            (not doc.patient , "* No patient with this CR"),
            (doc.patient and not doc.patient.user.external_id ,
                "* No external_id for patient"),
            (not doc.date_dossier , "* No date for this CR"),
            (doc.doc_type == 'CR_DOCTOR' and not doc.healthworkers ,
                '* No doctor for CR_DOCTOR'),
            (doc.doc_type == 'CR_CORRES' and not doc.healthworkers,
                '* No corres for CR_CORRES'),
            (doc.doc_type == 'CR_SAMPLER' and not doc.healthworkers,
                '* No sampler for CR_SAMPLER'),
            ]
            errors = [ msg for nok, msg in checks if nok ]
            if errors :
                msg_err = "\n".join(errors)
                warnings.warn(msg_err)

        if not doc.numdos :
            warnings.warn("* No numdos for this document")

    def denormalize(self, doc):
        """
        Fill doc.patient_name, doc.doctor_name (etc...) for query
        optimization when searching document by user's name.
        :param doc: :class:`model.Document`
        """
        doc.patient_name = doc.patient.user.name
        doc.healthworkers_name= ' '.join([ x.user.name for x in filter(lambda
            x:x.user.name, doc.healthworkers)]).strip()

    def _compile(self, doc):
        """
        Set data into correct type.
        :param doc: :class:`model.Document`
        """
        if doc.date_dossier :
            try :
                doc.date_dossier = datetime.strptime(re.sub(r"[^\d]", "",
                    doc.date_dossier), "%d%m%y")
            except Exception as e:
                try :
                    doc.date_dossier = datetime.strptime(re.sub(r"[^\d]", "",
                                                                doc.date_dossier)[:8], "%d%m%Y")
                except Exception as e:
                    doc.date_dossier = None
                    warnings.warn("Invalid datedos ({0})".format(e))


    def _set_underlay(self, doc):
        """
        Look for a suitable underlay and keep a reference on it
        """
        if not doc.labo:
            return
        for underlay in doc.labo.underlays :
            for doc_type in underlay.doc_types:
                if doc_type == doc.doc_type:
                    doc.underlay = underlay

    def validate(self, doc):
        """
        Do some transformations and checks on doc.
        :param doc: :class:`model.Document`
        """
        self._compile(doc)
        self._check_integrity(doc)
        self._set_underlay(doc)
        self.denormalize(doc)

class Validator:
    """
    Composit of various validator (document, user for now).
    """

    doc_validator = DocumentValidator()
    user_validator = UserValidator()

    def validate_document(self, doc):
        """
        :param doc: :class:`model.Document`
        """
        self.doc_validator.validate(doc)

    def validate_users(self, *users):
        for user in users:
            if hasattr(user, 'model_class') and issubclass(user.model_class,
                    User) or\
            isinstance(user, User) :
                self.user_validator.validate(user)


