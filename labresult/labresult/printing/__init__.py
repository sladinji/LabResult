from tempfile import NamedTemporaryFile
import subprocess

from labresult.model import PrintJob
from labresult.converter import get_pdf
from labresult.lib.model import get_readable_name
from flask.ext.babelex import gettext

class PrintingException(Exception):
    pass

def find_printer(doc):
    """
    Return suited printer for given doc or raise PrintingException if not
    possible.
    """
    if not doc.labo :
        raise PrintingException(
        gettext("Pas de labo associé au document")
        )
    prt = (
        doc.labo.get_printer_by_doc_type( doc.doc_type ) or
        doc.labo.get_default_printer()
    )
    if not prt :
        raise PrintingException(
                gettext(
                "Pas d'imprimante pour ce type de document ou pas d'imprimante par"
                " défaut définie pour ce laboratoire. Configurez le laboratoire"
                " ou les imprimantes correctement pour pouvoir imprimer.")
                )
    return prt

def printdoc( doc, prt=None ):
    """Print a document. if prt is None, printer is found with document's laboratory and laboratory's printers

    :param doc: document to print
    :type doc: sismodel.Document
    """
    if not prt :
       prt = find_printer(doc)
    with NamedTemporaryFile() as tmpf :
        tmpf.write(get_pdf(doc))
        out = subprocess.check_output("/usr/bin/lp -d %s -h %s:%s -t "
                "%s %s " % (prt.name, prt.cups_host, prt.cups_port,
                    get_readable_name(doc), tmpf.name), shell=True)
        out = out.decode("utf8")
        # get job-id in lp output
        job_id = [ x for x in out.split() if  x.startswith("%s-" % prt.name) ][0].split('-')[-1]
        job = PrintJob(
            cups_job_id = job_id,
            printer = prt,
        )
        doc.print_jobs.append(job)
        doc.save()
