
import testlib
from labresult.model import *
from labresult.printing import printdoc, PrintingException
from nose.tools import assert_raises

class TestPrint(testlib.TestBase):

    def test_printdoc(self):
        printer = Printer(name='PDF', activated=True)
        printer.options.append(PrinterOption(document_type='CR'))
        printer.save()
        labo = Labo(name="labtest")
        labo.printers.append(printer)
        labo.save()
        doc = Document(doc_type = "CR")
        assert_raises(PrintingException, printdoc,doc)
        pdf_data = self.get_data('2pages.pdf')
        doc = Document(doc_type = "CR", labo=labo, pdf=pdf_data)
        printdoc(doc)
        self.assertEquals(1, len(doc.print_jobs))
        self.assertEquals("unknow", str(doc.print_jobs[0]))
