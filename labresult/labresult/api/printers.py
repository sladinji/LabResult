from labresult.lib.api import PrivateResource
from flask.ext.restful import reqparse
from labresult.model import Printer as Printer_
from flask.ext.restful import fields, marshal_with

class PrinterOptionField(fields.Raw):
    def output(self, key, obj):
        option = obj[key]
        return dict( document_type = option.document_type,
                options = option.options
                )

printer_fields = {
    'is_default' : fields.Boolean,
    'name': fields.String,
    'cups_host' : fields.String,
    'cups_port' : fields.Integer,
    'activated' : fields.Boolean,
    'options' : fields.List(PrinterOptionField),
}

class Printer(PrivateResource):

    model = Printer_

    allowed_users = ['User.Administrator']
    parser = reqparse.RequestParser()
    parser.add_argument("name", type=str)
    parser.add_argument("cups_host", type=str)
    parser.add_argument("cups_port", type=str)
    parser.add_argument("is_default", type=bool)
    parser.add_argument("activated", type=bool)


    @marshal_with(printer_fields)
    def get(self, id):
        return Printer_.objects.get(id=id)

    @marshal_with(printer_fields)
    def put(self, id):
        args = self.parser.parse_args()
        printer = Printer_.objects.get(id=id)
        for k in args:
            if args[k]:
                setattr(printer, k, args[k])
        printer.save()
        return printer

