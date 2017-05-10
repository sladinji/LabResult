import os
import smtplib
import traceback
import uuid
from email.headerregistry import Address
from email.message import EmailMessage
from email.mime.image     import MIMEImage
from email.mime.text import MIMEText

import labresult
from labresult_demo import mail_tmplt_txt, mail_tmplt_html
from labresult.lib.model import get_option


def send(recipient):
    """
    Send demo credentials to recipient
    """
    # Create the base text message.
    msg = EmailMessage()
    msg['Subject'] = "Connexion démo LabResult "
    msg['From'] = Address("", "demo-labresult@labresult.fr")
    msg['To'] = (Address("", recipient),)
    msg.set_content(mail_tmplt_txt.content)

    logo_cid = str(uuid.uuid4())
    msg.add_alternative(mail_tmplt_html.content.format(logo_cid=logo_cid),
            'html', 'utf-8')
    # Now add the related image to the html part.
    logo = os.path.join(os.path.dirname(__file__), "data", "logo.png")
    with open(logo, 'rb') as img:
        msg_image = MIMEImage(img.read(), name=os.path.basename(logo),
                _subtype="image/png" )
        msg.attach(msg_image)
        msg_image.add_header('Content-ID', '<{}>'.format(logo_cid))

    msg2 = MIMEText("Envoi des identifians de démo à %s" % recipient)
    msg2['Subject'] = "Connexion démo LabResult "
    msg2['From'] = "demo-labresult@labresult.fr"
    msg2['To'] = "julien.almarcha@gmail.com"
    # Send the message via local SMTP server.
    ret = False
    try :
        smtp_server = get_option('smtp_server', 'mail.gandi.net')
        with smtplib.SMTP_SSL(smtp_server) as s:
            USERNAME = get_option('smtp_login', 'demo-labresult@labresult.fr')
            PASSWORD = get_option('smtp_password','pacman9732')
            s.login(USERNAME, PASSWORD)
            s.send_message(msg)
            s.send_message(msg2)
            ret = True
    except Exception :
        labresult.app.logger.error(traceback.format_exc())
    finally:
        return ret
