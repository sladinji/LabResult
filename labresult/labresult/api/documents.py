from flask import url_for
from flask.ext.restful import reqparse
from werkzeug.datastructures import FileStorage

from labresult.converter import get_pdf
from labresult.lib.api import StandardPermissionsCheck
from labresult.lib.model import get_readable_name
from labresult.model import Document as Doc
from labresult.lib.auth import permission_on_doc


class Document(StandardPermissionsCheck):
    """
    Restfull ressource for labresult.model.Document object.
    """
    model = Doc
    allowed_users = ['User.Administrator', 'User.Patient', 'User.HealthWorker',
            'User.Group']

    parser = reqparse.RequestParser()
    #TODO put only required attribute
    attrs = [ k for k in Doc.__dict__
            if not callable(Doc.__dict__[k])
            # remove private attributes
            and not k.startswith('_')
            # remove constant like, NEW, ERROR...
            and k.lower() == k
            ]
    for att in attrs :
        parser.add_argument(att, type=str)
    parser.add_argument('ids', type=str, action='append')
    parser.add_argument('pdf', type=FileStorage, location='files')
    parser.add_argument('id', type=str)
    """Only used for put method"""

    def _get_limit_per_page(self):
        return 1000

    def _pack_item(self, id):
        """
        Do a response for a doc
        """
        doc = Doc.objects.get(id=id)
        self.check_permission(doc)
        if doc.status == Doc.OK :
            if not doc.pdf_nb_pages :
                get_pdf(doc)
            images_url = [ url_for('file', id=doc.id, format='png', page_num=n) for n
                    in range(1, doc.pdf_nb_pages + 1)
                    ] if doc.pdf_nb_pages else []
            jsdoc = {
                'id' : str(doc.id),
                'traceback' : doc.traceback, 'log' : doc.log,
                'raw_url':url_for('file', id=doc.id, format='raw',
                    as_attachment=True),
                'images_url':images_url,
                'pdf_nb_pages':doc.pdf_nb_pages,
                'doc_type' : doc.doc_type,
                'numdos' : doc.numdos,
                'patient_name' : doc.patient_name,
                'patient_id': str(doc.patient.user.id),
                'pdf_url' : url_for('file', id=doc.id, format='pdf'),
                'name' : get_readable_name(doc),
                'date_dossier' :
                doc.date_dossier.strftime('%d/%m/%Y'),
            }
        else :
            jsdoc = {
            'id' : str(doc.id),
            'traceback' : doc.traceback,
            'log' : doc.log,
            'raw_url':url_for('file', id=doc.id, format='raw',as_attachment=True),
            }

        return jsdoc

    def check_permission(self, item):
        return permission_on_doc(item)
