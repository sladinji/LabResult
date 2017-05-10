import warnings
import datetime
import testlib
from labresult import builder
from labresult.model import *
from labresult.lib.model import *
from labresult.builder.validator import DocumentValidator
from labresult.lib.model import set_option

class TestParse(testlib.TestBase):

    def test_extract( self ):
        b = builder.Builder()
        p = b.parsers['pclparser']
        doc = self.get_doc("progi.pcl")
        objs = p.parse(doc)
        self.assertEquals(len(objs), 4)
        self.assertEquals( doc.date_dossier, '14/01/14')
        self.assertEquals( doc.doc_type, 'CR_PATIENT')
        self.assertEquals( doc.numdos, '4LI0114012')
        self.assertEquals( doc.tags, 'P        V')
        pat = objs[0]
        self.assertEquals( pat.address1, '3 RUE DU BALLON')
        self.assertEquals( pat.address2, '68700 CERNAY')
        self.assertEquals( pat.birthdate, '22/07/1933')
        self.assertEquals( pat.civility, 'Mr')
        self.assertEquals( pat.external_id, '0632968',)
        self.assertEquals( pat.firstname, 'LOUIS')
        self.assertEquals( pat.lastname, 'SCHERRER')
        self.assertEquals( pat.secu, '133076833401062')
        self.assertEquals( pat.fixe, '0389399067')
        doctor = objs[1]
        self.assertEquals( doctor.external_id, 'HTWIL2')
        self.assertEquals( doctor.name, 'DR J MARIE WILHELM')
        samp = objs[2]
        self.assertEquals( samp.external_id, 'MASO')
        self.assertEquals( samp.name, 'MAZURE Sophie')

        labo = objs[3]
        self.assertEquals( labo.external_id, '46')

    def test_pdfparser(self):
        b = builder.Builder()
        p = b.parsers['pdfparser']
        doc = self.get_doc("biowin.pdf")
        objs = p.parse(doc)
        self.assertEquals(len(objs), 2)
        self.assertEquals( doc.date_dossier, 'Date Prélèvement: 01/03/2016 à 14:50')
        self.assertEquals( doc.doc_type, 'CR_PATIENT')

    def test_pdfintegration(self):
        b = builder.Builder()
        doc = self.get_doc("biowin.pdf")
        b.build(doc)
        doc.save()

    def test_build(self):
        b = builder.Builder()
        doc = self.get_doc("progi.pcl")
        b.build(doc)

    def test_birth_date(self):
        b = builder.Builder()
        doc = self.get_doc("birthdate.pcl")
        b.build(doc)

    def test_invalide_date(self):
        b = builder.Builder()
        doc = self.get_doc("invdate.pcl")
        b.build(doc)

    def test_UTF8(self):
        b = builder.Builder()
        doc = self.get_doc("utf8.pcl")
        b.build(doc)

    def test_document_integrity(self):
        dv = DocumentValidator()
        doc = Document(doc_type = 'CR_PATIENT')
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            dv._check_integrity(doc)
            msg = '\n'.join([str(w.message) for w in ws])
            self.assertEquals(
                "* No patient with this CR\n"
                "* No date for this CR\n"
                "* No numdos for this document",msg )

    def test_denormalize(self):
        dv = DocumentValidator()
        doc = Document()
        doc.patient = PatientAccess(user=Patient(name="jean paul"))
        doc.healthworkers.append(HealthWorkerAccess(
            user = HealthWorker(name="Dr Dre"), role = "doctor")
            )
        doc.healthworkers.append(HealthWorkerAccess(
            user = HealthWorker(name="Dr Jeckyl"), role = "doctor")
            )
        doc.healthworkers.append(HealthWorkerAccess(
            user = HealthWorker(name="Jean Preleve"), role = "sampler" )
            )
        doc.healthworkers.append(HealthWorkerAccess(
            user = HealthWorker(name="Mireille Linf"), role = "sampler")
            )
        dv.denormalize(doc)
        self.assertEquals("jean paul", doc.patient_name)
        self.assertEquals("Dr Dre Dr Jeckyl Jean Preleve Mireille Linf", doc.healthworkers_name)

    def test_doc_compile(self):
        dv = DocumentValidator()
        doc = Document(date_dossier = '13-05-14')
        dv._compile(doc)
        self.assertEquals(datetime.datetime(2014,5,13), doc.date_dossier)

    def test_invalid_user(self):
        class NimpUser(User):
            pass
        class NimpParser():
            def parse(self, doc):
                d = DbDict(NimpUser)
                d.external_id = '1234'
                return [d]
        b = builder.Builder()
        getitback = b.parsers['pclparser']
        b.parsers['pclparser'] = NimpParser()
        doc = self.get_doc("progi.pcl")
        doc.save()
        b.build(doc)
        doc.reload()
        self.assertEquals("Type d'objet inconnu <class "
        "'testparse.TestParse.test_invalid_user.<locals>.NimpUser'>", doc.log)
        b.parsers['pclparser'] = getitback

    def test_no_numdos(self):
        b = builder.Builder()
        doc = self.get_doc("progi.pcl")
        doc2 = Document(data =
                bytes(doc.data.read().decode('ascii').replace("numdos",""),
                "ascii")
                )
        b.build(doc2)
        self.assertTrue("No numdos for this document" in doc2.warnings)
        self.assertEquals(doc2.status , Document.OK)

    def test_notag( self ):
        """
        Test exception raise when no tag present.
        """
        b = builder.Builder()
        p = b.parsers['pclparser']
        doc = self.get_doc("progi.pcl")
        #remove marker
        doc2 = Document(data =
                bytes(doc.data.read().decode('ascii').replace("&a350C",""),
                "ascii")
                )
        self.assertRaises(Exception, p.parse, doc2)
        #remove tag
        doc2 = Document(data = bytes("&a350C Type =","utf8"))
        self.assertRaises(Exception, p.parse, doc2)

    def test_fixtag( self ):
        """
        Set wrong marker and parser automaticly fix it
        """
        set_option("pclparser.marker", "&a444C")
        b = builder.Builder()
        p = b.parsers['pclparser']
        doc = self.get_doc("progi.pcl")
        p.parse(doc)
        self.assertEquals("&a350C", p.marker)
