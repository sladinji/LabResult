from labresult.lib.api import PrivateResource
from flask.ext.restful import reqparse, abort
from labresult.builder.tasks import get_doc
from labresult.printing import printdoc, PrintingException
from labresult.model import Document


class Printing(PrivateResource):

    allowed_users = ['User.Administrator']
    model = Document
    parser = reqparse.RequestParser()
    parser.add_argument("id", type=str, required=True)

    def get(self):
        try :
            args = self.parser.parse_args()
            doc = get_doc(**args)
            printdoc(doc)
            job= doc.print_jobs[-1]
            joblink = "http://%s:%s/jobs/?WHICH_JOBS=completed&QUERY=%s" %(
                    job.printer.cups_host, job.printer.cups_port, job.cups_job_id)
            return joblink, 200
        except PrintingException as e:
            return abort( 400, message=str(e))
        except Exception as e:
            return abort(400, message=str(e))

