from flask.ext import login

from labresult.model import Document as Doc, User
from labresult.lib.api import FilterableListResource as FLR
from labresult.lib.auth import permission_on_doc, UserPermissionError
from labresult.lib.auth import auth_exception_manager
from flask.ext.restful import reqparse
from werkzeug.datastructures import FileStorage


class Doc2Sign(FLR):
    allowed_users = ["User.Administrator"]
    model = Doc

    parser = reqparse.RequestParser()
    parser.add_argument('pdf', type=FileStorage, location='files')
    parser.add_argument('id', type=str)
    parser.add_argument('error', type=str)

    def _get_qry(self, args):
        user = User.objects.get(id=login.current_user.id)
        qry = Doc.objects.filter(biologist=user, signed__ne=True,
                                 signature_tries__lte=3)
        qry = qry.order_by("date_dossier", "capture_date")
        return qry

    def _get_limit_per_page(self):
        return 1000

    @auth_exception_manager
    def post(self):
        """
        Update PDF (should be signed PDF)
        """
        args = self.parser.parse_args()

        doc = Doc.objects.get(id=args.id)
        if doc.biologist.id != login.current_user.id:
            raise UserPermissionError()
        if args.error:
            doc.signature_tries += 1
            doc.signature_error = args.error
            doc.save()
        else:
            doc.pdf = args.pdf.read()
            doc.signed = True
            doc.save()
        return dict(success=True)

    def check_permission(self, item):
        return permission_on_doc(item)
