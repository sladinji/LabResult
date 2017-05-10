from flask.ext.restful import Resource, reqparse
from flask import jsonify
from werkzeug.datastructures import FileStorage
from labresult.builder.tasks import integrate


class MissingDataException(Exception):
    pass

class PCL(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('data', type=FileStorage, location='files')
    parser.add_argument('pdf', type=FileStorage, location='files')
    """usefull for test"""
    parser.add_argument('pdf_nb_pages', type=int)
    parser.add_argument('origin', type=str, help="Can be printer name")
    parser.add_argument('numdos', type=str)
    parser.add_argument('parser_name', type=str)
    parser.add_argument('doc_type', type=str)
    parser.add_argument("as_attachment", type=bool)
    parser.add_argument("id", type=str, help="gridfs id")

    def post(self):
        args = self.parser.parse_args()
        no_file = True
        if args["data"] :
            args["data"] = args["data"].read()
            no_file = False
        if args["pdf"] :
            args["pdf"] = args["pdf"].read()
            no_file = False
        if no_file:
            return {"success":False, 'error':"Missing data Exception, no file provided"}, 422
        task = integrate.delay(**args)
        return {"success": True, "message": "Integration task %s" % task}
