import testlib
from labresult.builder import tasks
from labresult.model import Document

class TestBuilder(testlib.TestBase):

    def add_a_doc(self):
        doc_id = tasks.integrate(data = self.get_data("progi.pcl"))
        return doc_id

    def test_get_doc(self):
        doc_id = self.add_a_doc()
        doc = Document.objects(id=doc_id).get()
        doc2 = tasks.get_doc(id = doc_id)
        self.assertEquals(doc, doc2)
        doc2 = tasks.get_doc(numdos = doc.numdos, doc_type = doc.doc_type)
        self.assertEquals(doc, doc2)

    def test_get_gridfs_data_from_id(self):
        doc_id = self.add_a_doc()
        data1 = tasks.get_gridfs_data(doc_id)
        doc = Document.objects(id=doc_id).get()
        data2 = tasks.get_gridfs_data_from_id(doc.data._id)
        self.assertEquals(data1, data2)

    def test_version(self):
        for w in range(10):
            self.add_a_doc()

        self.assertEquals( 10, Document.objects( current_version = True
            ).first().version)

    def add_a_pdf(self):
        doc_id = tasks.integrate(pdf= self.get_data("biowin.pdf"))
        return doc_id

    def test_integrate_pdf(self):
        doc_id = self.add_a_pdf()
        doc = Document.objects(id=doc_id).get()

