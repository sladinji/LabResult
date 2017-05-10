from labresult.lib.api import PrivateResource
from flask.ext.restful import reqparse
from flask import jsonify, url_for
from labresult.model import Labo as Lab
from flask.ext.restful import fields, marshal_with

class PrinterField(fields.Raw):

    def output(self, key, obj):
        printer = obj[key]
        return dict(name=printer.name, uri=url_for('printer', id=printer.id))


labo_fields = {
    'external_id':   fields.String,
    'name':    fields.String,
    'address': fields.String,
    'is_default': fields.Boolean,
    'printers': fields.List(PrinterField),
}

class Labo(PrivateResource):

    model = Lab

    allowed_users = ['User.Administrator']
    parser = reqparse.RequestParser()
    parser.add_argument("name", type=str)
    parser.add_argument("address", type=str)
    parser.add_argument("printers", type=str)
    parser.add_argument("is_default", type=bool)


    @marshal_with(labo_fields)
    def get(self, id):
        labo = Lab.objects.get(id=id)
        return labo

    @marshal_with(labo_fields)
    def put(self, id):
        args = self.parser.parse_args()
        lab = Lab.objects.get(id=id)
        for k in args:
            if args[k]:
                setattr(lab, k, args[k])
        lab.save()
        return lab

class Labos(PrivateResource):

    allowed_users = ['User.Administrator']
    model = Lab

    def get(self):
        labos = []
        for lab in Lab.objects :
            printers = []
            for printer in lab.printers :
                printers.append({'name': printer.name, 'id ':
                    str(printer.id)})
            labos.append({'name' : lab.name, "id" : lab.external_id,
                "printers": printers})
        return jsonify({'success' : True, 'labos':labos})
