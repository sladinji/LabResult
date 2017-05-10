import traceback

from flask.ext.babelex import gettext

import labresult
from labresult.lib.message import log_message
from labresult.lib.model import get_option


class SmsBase:
    """
    Base class for sms plugins.
    """

    def send_credential(self, user):
        gname = get_option("gname", "LabResult")
        ttl = get_option("credential_code.ttl", 20)
        model = get_option("sms.template.credential",
            gettext("Votre code de vérification est:\n\n{code}\n\nIl est"
            " valable {validity} minutes. {gname} vous remercie.")
            )
        content = model.format(code = user.credential_code, validity = ttl, gname = gname)
        try :
            self._send_sms(user, content)
            log_message(user, "credential", "sms", self.__class__.__name__,
                    content)
            return True
        except :
            error = traceback.format_exc()
            labresult.app.logger.error(error)
            return False

    def send_notif_dispo(self, user):
       pass

    def _send_sms(self, user, message):
        raise Exception("MUST BE IMPLEMENTED IN SUBCLASS")

def send_sms_credential(user):
    for plugin in labresult.app.sms_plugins :
        if plugin.send_credential(user):
            return True
