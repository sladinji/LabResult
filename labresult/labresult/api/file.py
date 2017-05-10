from io import BytesIO
from zipfile import ZipFile
import labresult
from labresult.lib.api import PrivateResource
from flask.ext.restful import reqparse, abort
from flask import send_file
from labresult.builder.tasks import get_doc
from labresult.converter import get_img, get_pdf
from mimetypes import types_map
from labresult.lib.model import get_readable_name
from labresult.lib.auth import permission_on_doc, UserPermissionError
from labresult.model import Document

class File(PrivateResource):

    model = Document

    allowed_users = ['User.Administrator', 'User.Patient', 'User.HealthWorker',
            'User.Group']
    parser = reqparse.RequestParser()
    parser.add_argument('format', type=str, help="raw, pdf, png")
    parser.add_argument('numdos', type=str)
    parser.add_argument('doc_type', type=str)
    parser.add_argument("as_attachment", type=bool)
    parser.add_argument("gridfs_id", type=str, help="gridfs id")
    parser.add_argument("id", type=str, help="document id")
    parser.add_argument("ids", type=str, action='append', help="document id")
    parser.add_argument("thumbnail", type=bool)
    parser.add_argument("page_num", type=int, default=1)
    parser.add_argument("format", type=str, default="png",
            help="pdf, png or svg")

    def _get_fp(self, doc, frmt, page_num, thumbnail):
        fp = None
        if frmt == 'pdf' :
            if hasattr(doc.pdf, '_id') :
                fp = doc.pdf
            else :
                pdf_data = get_pdf(doc)
                fp = BytesIO(pdf_data)

        elif frmt in ('png', 'jpg') :
            if not doc.pdf_nb_pages :
                get_pdf(doc)
            if page_num in range(1,doc.pdf_nb_pages+1):
                img_data = get_img(doc, page_num, thumbnail, frmt)
                fp = BytesIO(img_data)
        elif frmt == 'raw' :
            fp = doc.data

        return fp


    def _get_name_and_mime(self, doc, frmt, thumbnail, page_num ):
        ext = "." + frmt
        mimetype = types_map.get(ext, 'application/' + frmt)
        if frmt in ('png', 'jpg'):
            suffix = '_small.%s' % frmt  if thumbnail else '.%s' % frmt
            name = "%s_%s%s" % (doc.id,page_num, suffix)
        else :
            name = get_readable_name(doc) + ext
        return name, mimetype

    def get(self):
        try :
            args = self.parser.parse_args()
            frmt = args['format'].lower()
            thumb = args['thumbnail']
            if args['ids'] :
                return self._send_thumbnails(args['ids'])
            doc = get_doc(**args)
            permission_on_doc(doc)
            as_attachment = args.get("as_attachment", False)
            name, mimetype = self._get_name_and_mime(doc, frmt,  thumb,
                    args['page_num'])
            timeout = 86400 if thumb else 0
            fp = self._get_fp(doc, frmt, args['page_num'], thumb)
            if not fp :
                return { 'success' : False, 'error': 'Invalid file format'}, 404
            else:
                return send_file(fp, mimetype=mimetype,
                    attachment_filename=name, as_attachment=as_attachment,
                    cache_timeout=timeout, add_etags=False)
        except UserPermissionError as e :
            labresult.app.logger.warning(e)
            return { 'success' : False, 'error': 'Access denied to requested document'}, 401
        except Exception as e :
            labresult.app.logger.error(e)
            return { 'success' : False, 'error': 'Invalid request'}, 401

    def _send_thumbnails(self, ids):
        if len(ids) > 25:
            return { 'success' : False, 'error': 'Multiple file can'
            ' only be png thumbnail and less than 26 items'}, 401
        buf = BytesIO()
        with ZipFile(buf, 'w') as zip:
            for id in ids:
                doc = get_doc(id=id)
                permission_on_doc(doc)
                fp = self._get_fp(doc, 'png', 1, True)
                if not fp :
                    return abort(404, status = 404,
                            error="Document not found."
                            )
                else:
                    zip.writestr(id, fp.read())
        buf.seek(0)
        return send_file(buf, mimetype='application/zip',
            attachment_filename='thumbs.zip', as_attachment=False,
            cache_timeout=86400)


