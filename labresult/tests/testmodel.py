
import testlib
from labresult.model import *
import datetime

class TestParse(testlib.TestBase):

    def test_lastresult( self ):
        pat = Patient(name = 'jean')
        pat.save()
        doc = Document(
                doc_type = 'CR_DOCTOR',
                patient = PatientAccess(user=pat, read=False)
                )
        doc.save()
        self.assertEqual('', pat.last_result())
        doc2 = Document(
                doc_type = 'CR_PATIENT',
                patient = PatientAccess(user=pat, read=True),
                date_dossier = datetime.datetime.now(),
                )
        doc2.save()
        doc3 = Document(
                doc_type = 'CR_PATIENT',
                patient = PatientAccess(user=pat, read=True),
                date_dossier = datetime.datetime.now(),
                status = Document.OK,
                current_version = True
                )
        doc3.save()
        self.assertEqual(str(doc3.id), pat.last_result())
