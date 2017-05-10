from labresult.model import Document, Patient, HealthWorker, Labo
from labresult.lib.model import DbDict
from labresult.converter.pcl import fix_fr_accent
from labresult.lib.model import get_option
import re
import sys

type_mapping = {
    'P': 'CR_PATIENT',
    'M': 'CR_DOCTOR',
    'C': 'CR_CORRES'
}

doc_mapping = {
    'Type': "doc_type",
    "datedos": "date_dossier",
    "numdos": "numdos",
    'suf': 'tags',
}

patient_mapping = {
    'npat': 'external_id',
    'ad1': 'address1',
    'ad2': 'address2',
    'ddn': 'birthdate',
    'nSS': 'secu',
    'pfx': 'civility',
    'pnom': 'lastname',
    'prn': 'firstname',
    'tel': 'fixe',
}

doctor_mapping = {
    'cmed': 'external_id',
    'nommed': 'name',
}

sampler_mapping = {
    'cprl': 'external_id',
    'nprl': 'name',
}

mappings = [
    (Document, doc_mapping, None),
    (Patient, patient_mapping, None),
    (HealthWorker, doctor_mapping, 'doctor'),
    (HealthWorker, sampler_mapping, 'sampler'),
]


class ParserException(Exception):
    pass


class Parser():
    name = "pclparser"

    def __init__(self):
        """
        :param marker: marker before tags, if marker = None, try to find
        it (should be something like "&a200C" or "&a350C").
        :param dbload: true means db object will be load from db according to
        their external_id, false means no interaction with db, usefull for
        tests.
        """
        self.marker = get_option("pclparser.marker", "&a350C")

    def guess_marker(self, data):
        """
        try to guess wich marker is used for tags
        :param data: str, pcl data
        """
        try:
            self.marker = re.search(r"(&a\d\d\dC)\s*Type\s*=", data).group(1)
        except:
            tb = sys.exc_info()[2]
            raise ParserException("Aucun marqueur trouvé").with_traceback(tb)

    def get_tags(self, data):
        """
        :param data: string to parse
        :rtype: dict of tags
        """
        tags = ''
        if not self.marker:
            self.guess_marker(data)
        for match in re.findall(self.marker + "(.*)", data):
                tags += match
        if not tags:
            self.guess_marker(data)
            for match in re.findall(self.marker + "(.*)", data):
                    tags += match

        kv = [x.split("=") for x in tags.split(";")]
        kv = [x for x in kv if len(x) == 2 and x[1].strip()]
        if not kv:
            raise ParserException("Aucun tag trouvé.")
        return {key.strip(): value.strip() for key, value in kv}

    def get_objs(self, doc, doc_tags):
        """
        Update doc and return a list of :class:`labresult.model.DbDict`
        :param doc: :class:`labresult.model.Document`
        :param doc_tags: dict of tags present in doc
        :rtype: list of tuple
        """
        ret = []
        for class_, mapping, role in mappings:
            known_keys = [k for k in doc_tags.keys() if k in mapping.keys()]
            if not known_keys:
                continue
            dic = doc if class_ is Document else DbDict(class_, role)
            for key in known_keys:
                value = fix_fr_accent(doc_tags[key])
                setattr(dic, mapping[key], value)
            if class_ is not Document:
                ret.append(dic)
        return ret

    def parse(self, doc):
        """
        Update doc and retrun a list of DbDict
        :param doc: model.Document
        :rtype: list of :class:`labresult.model.DbDict`
        """
        data = doc.data.read().decode('cp437')
        tags = self.get_tags(data)
        objs = self.get_objs(doc, tags)
        match = re.match(r'(?P<type>\w)(?P<labo>\d+)(?P<subtype>\w*)##',
                         doc.doc_type)
        if match:
            mgd = match.groupdict()
            labo = DbDict(Labo)
            labo.external_id = mgd['labo']
            objs.append(labo)
            default = "PJ_%s" % mgd["subtype"]
            doc.doc_type = type_mapping.get(mgd["type"], default)
        return objs


def get_parser_plugin():
    return Parser()
