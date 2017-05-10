from io import StringIO
import re

import pdfquery

from labresult.model import Patient, Labo
from labresult.lib.model import get_option
from labresult.lib.model import DbDict


class PDFParser():
    name="pdfparser"

    def fix_coord(self, tag, default_value):
        """
        Coordinate are saved in option like displayed in XML, but we need to adapt it to used it with pdf.extract
        """
        option = get_option("pdf.extract." + tag, default_value)
        return tag, option.replace(' bbox="[', ':in_bbox("').replace(']"', '")')

    def parse(self, doc):
        """
        Parse PDF according to box coordinates
        :param doc: labresult.model.Document
        :rtype: Document, Patient, Labo
        """
        mapping = [
            ('patient.name', 'LTTextBoxHorizontal bbox="[342.0, 673.17, 517.896, 686.5]"'),
            ('patient.external_id', 'LTTextBoxHorizontal bbox="[342.0, 673.17, 517.896, 686.5]"'),
            ('patient.address1', 'LTTextBoxHorizontal bbox="[342.0, 625.77, 449.76, 662.55]"'),
            ("patient.birthdate", 'LTTextBoxHorizontal bbox="[359.64, 591.54, 409.36, 603.1]"'),
            ("sexe", 'LTTextBoxHorizontal bbox="[436.32, 590.49, 468.17, 603.63]"'),
            ("doc.numdos", 'LTTextBoxHorizontal bbox="[23.64, 613.446, 162.588, 627.726]"'),
            ("doc.date_dossier", 'LTTextLineHorizontal bbox="[23.64, 590.49, 201.76, 603.63]"'),
            ("date_edit", 'LTTextLineHorizontal bbox="[23.64, 578.61, 152.49, 591.75]"'),
            ("labo.name", 'LTTextLineHorizontal bbox="[200.52, 779.994, 372.978, 814.652]"'),
            ("labo.external_id", 'LTTextLineHorizontal bbox="[200.52, 779.994, 372.978, 814.652]"'),
        ]
        mapping = [self.fix_coord(tag, default) for tag, default in mapping]

        pdf = pdfquery.PDFQuery(doc.pdf)
        pdf.load(0)
        extraction = pdf.extract([('with_formatter', 'text')] + mapping)

        doc.doc_type = 'CR_PATIENT'
        for k, v in {k: v for k, v in extraction.items() if 'doc.' in k}.items():
            setattr(doc, k.replace('doc.', ''), v)

        patient = DbDict(Patient)
        for k, v in {k: v for k, v in extraction.items() if 'patient.' in k}.items():
            setattr(patient, k.replace('patient.', ''), v)

        labo = DbDict(Labo)
        for k, v in {k: v for k, v in extraction.items() if 'labo.' in k}.items():
            setattr(labo, k.replace('labo.', ''), v)

        self.clean(doc, patient, labo)

        return patient, labo

    def clean(self, doc, patient, labo):
        doc.numdos = doc.numdos.replace("Dossier n° :", "").replace("*","").strip()
        patient.name = re.sub(r'\d{12}','',patient.name[:-12]).strip()
        match_ext_id = re.search(r'\d{12}', patient.external_id)
        if match_ext_id :
            patient.external_id = match_ext_id.group(0)
        else :
            patient.external_id = None

    def get_xml(self, doc):
        """
        Return XML with boxes coordinates (helpfull to set coordinates)
        :param doc: labresult.model.Document
        :rtype: xml data
        """
        pdf = pdfquery.PDFQuery(doc.pdf)
        pdf.load(0)
        xml = StringIO()
        pdf.tree.write(xml, pretty_print=True, encoding="utf-8")
        return xml.read()


def get_parser_plugin():
    return PDFParser()
