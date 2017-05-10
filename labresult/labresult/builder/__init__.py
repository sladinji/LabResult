import warnings
import traceback
from pkg_resources import iter_entry_points

import labresult
from labresult.lib import Singleton
from labresult.model import Patient, HealthWorker, Document, User, Labo
from labresult.model import PatientAccess, HealthWorkerAccess, GroupAccess
from labresult.builder.validator import Validator
from labresult.builder.publisher import Publisher
from labresult.lib.model import dblog

class BuilderException(Exception):
    pass

class Builder(metaclass=Singleton):
    parsers={}
    """
    Dictionnary keys = parser name, values = parser object
    """

    def __init__(self, parser=None, validator=Validator, publisher=Publisher):
        """
        TODO : remove this dirty progi import
        :param parser: document parser
        :param validator: objects validator
        """
        for plugin in iter_entry_points(group='labresult.plugin.parser', name=None):
            parser = plugin.load()()
            self.parsers[parser.name] = parser
        self.validator = validator()
        self.publisher = publisher()

    def _save_objs(self, objs, doc):
        """
        Merge objs in db and add them to doc.
        :param objs: list of :class:`labresult.model.*` (obj must have an
        attribute called 'externam_id'.
        :param doc: :class:`labresult.model.Document`
        """
        for obj in objs:
            role = obj.role
            obj = obj.merge()
            if isinstance(obj, Patient) :
                doc.patient = PatientAccess(user=obj)
            elif isinstance(obj, HealthWorker):
                doc.healthworkers.append(HealthWorkerAccess(user=obj, role=role))
                # check if hw is member of group and share with it
                for grp in [ gm.user for gm in obj.groups if gm.share]:
                    doc.groups.append(GroupAccess(user=grp))
            elif isinstance(obj, Labo):
                doc.labo = obj
            else :
                raise BuilderException(
                    "Type d'objet inconnu {0}".format(
                    obj.__class__)
                    )

    def _parse(self, doc):
        """
        Try to extract data from document with specified parser or try with available parsers.
        """
        parsers = {doc.parser_name: self.parsers[doc.parser_name]} if doc.parser_name else self.parsers
        objs = None
        for parser_name, parser in parsers.items():
            try :
                objs = parser.parse(doc)
                doc.parser_name = parser_name
            except Exception as ex :
                labresult.app.logger.warning(traceback.format_exc())
            if objs :
                break
        if not objs :
            raise BuilderException("Unable to extract objs from doc")
        return objs



    def build(self, doc):
        """
        Parse and validate a document. Then, document is saved in db, with
        status OK if integration was OK or with status ERROR there was a
        problem. Problems are reported in doc.log and doc.traceback.

        :param doc: :class:`model.Document`
        """
        try :
            with warnings.catch_warnings(record=True) as ws:
                # Cause all warnings to always be triggered.
                warnings.simplefilter("always")
                objs = self._parse(doc)
                self.validator.validate_users(*objs)
                self._save_objs(objs, doc)
                self.validator.validate_document(doc)
                self.publisher.publish_document(doc)
                doc.status = Document.OK
                doc.warnings = '\n'.join([str(w.message) for w in ws])
                self._handle_version(doc)
                doc.save()
        except Exception as err:
            dblog(doc, err)
        return doc

    def _handle_version(self, doc):
        """
        Remove read access on older version and set version number to current
        one.
        """
        if doc.version != 0 :
            return
        doc.save()
        last_version = Document.objects( numdos = doc.numdos,
                doc_type = doc.doc_type,
                id__ne = doc.id ).update( set__current_version = False)
        doc.version = last_version + 1
