import datetime
import testlib
from labresult.builder.publisher import Publisher
from labresult.model import *

class TestPublisher(testlib.TestBase):

    def add_basic_rule(self):
        rule = PublicationRule(user="patient",
                comment="Document non autorisé",
                rule="doc.doc_type in ['CR_PATIENT']",
                activated=True)
        rule.save()
        rule = PublicationRule(user="doctor",
                comment="Document non autorisé",
                rule="doc.doc_type in ['CR_DOCTOR']",
                activated=True)
        rule.save()

    def setUp(self):
        super(TestPublisher, self).setUp()
        self.publisher = Publisher()

    def get_doc(self):
        doc = Document()
        doc.doc_type = "CR_PATIENT"
        pat = Patient(name = "patname",
                firstname = "patfirstname",
                birthdate=datetime.date(1980, 5, 13),
                )
        doc.patient= PatientAccess(user=pat)
        hw = HealthWorker(name = "Dr Dutest")
        doc.healthworkers.append(HealthWorkerAccess(user=hw, role='doctor'))
        return doc

    def test_no_rule(self):
        doc = self.get_doc()
        self.publisher.publish_document(doc)
        self.assertFalse(doc.patient.read)
        self.assertEquals("No rules for patient" ,doc.patient.comment)
        self.assertFalse(doc.healthworkers[0].read)
        self.assertEquals("No rules for doctor" ,doc.healthworkers[0].comment)
        doc.doc_type = 'CR_DOCTOR'

    def test_doctype(self):
        self.add_basic_rule()
        doc = self.get_doc()
        self.publisher.publish_document(doc)
        self.assertTrue(doc.patient.read)
        self.assertFalse(doc.healthworkers[0].read)
        doc.doc_type = 'CR_DOCTOR'
        self.publisher.publish_document(doc)
        self.assertFalse(doc.patient.read)
        self.assertEqual(None, doc.tutor)
        self.assertTrue(doc.healthworkers[0].read)

    def test_tutor(self):
        self.add_basic_rule()
        doc = self.get_doc()
        doc.patient.user.tutor = Patient(name="tutor")
        self.publisher.publish_document(doc)
        self.assertFalse(doc.patient.read)
        self.assertTrue(doc.tutor.read)

    def test_group(self):
        self.add_basic_rule()
        doc = self.get_doc()
        doc.doc_type = 'CR_DOCTOR'
        group = Group(name = "group test")
        doc.groups.append(GroupAccess(user=group))
        hw = doc.healthworkers[0].user
        hw.groups.append(GroupMember(user= group))
        self.publisher.publish_document(doc)
        self.assertTrue(doc.groups[0].read)
        self.assertTrue(doc.groups[0].user == group)

