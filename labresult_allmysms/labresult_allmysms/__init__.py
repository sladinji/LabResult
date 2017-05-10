import urllib
import xml.etree.ElementTree as ET
from labresult.lib.sms import SmsBase

login = 'labresult'
apikey = 'ca5293b37f6f5d8'
retours = {
    "100" : "Le message a été envoyé",
    "101" : "Le message a été programmé pour un envoyénvoi différé",
    "102" : "Problème de connexion – Aucun compte ne correspond aux clientcode",
    "103" : "Crédit SMS épuisé. Veuillez re-créditer votre compte sur",
    "104" : "Crédit insuffisant pour traiter cet envoi. A utiliser: XX Crédits,",
    "105" : "Flux XML Vide",
    "106" : "        Flux XML invalide ou incomplet après la balise",
    "107" : "Flux XML invalide   ou incomplet après la balise",
    "108" : "Le code CLIENT donné dans le flux XMLML est incorrect, il doit"
    "correspondre au clientcode en majuscule",
    "109" : "    Flux XML invalide ou incomplet après la balise",
    "110" : "Message non défini (vide) dans le   flux XML",
    "111" : "Le message dépasse 640 caractères",
    "112" : "Flux XML invalidee ou incomplet après la balise",
    "113" : "Certains numéros de téléphone suront invalides ou non pris en"
    " charge",
    "114" : "Aucun numéro de téléphone videalide dans le flux.",
    "115" : "Flux XML invalide ou date mal formatée entre les balises et",
    "117" : "Balise – Lien trop long, dépasse les 80 caractèrestères",
    "118" : "Le compte maître spécifié n’existe pas"
}

class AllsmsException(Exception):
    pass

class Allmysms(SmsBase):

    def _send_sms(self, user, message):
        smsData = '<DATA><MESSAGE><![CDATA[{message}]]></MESSAGE><TPOA>LabResult</TPOA><SMS><MOBILEPHONE>{mobile}</MOBILEPHONE></SMS></DATA>'
        smsData = smsData.format(message=message, mobile=user.mobile)
        urlbase = 'https://api.allmysms.com/http/9.0/sendSms/?'
        urlparam = urllib.parse.urlencode([('login',login),('apiKey',
            apikey),('smsData',smsData)])
        response = ET.parse(urllib.request.urlopen(urlbase+urlparam)).getroot()
        ret = response.findtext('status')
        if ret != "100":
            raise AllsmsException(retours.get(ret, "Error code {}".format(ret)))


def get_sms_plugin():
    return Allmysms()

