#!/usr/bin/env python3

import smtplib
from email.mime.text import MIMEText

from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid

USERNAME = 'demo-labresult@labresult.fr'
PASSWORD = 'pacman9732'

recipient = "jualmarcha@free.fr"
# Create the base text message.
msg = EmailMessage()
msg['Subject'] = "Connexion démo LabResult "
msg['From'] = Address("", "demo-labresult@labresult.fr")
msg['To'] = (Address("", recipient),)
msg.set_content("""\
Bonjour,

Pour accéder au site de démonstration LabResult, vous pouvez utiliser les identifiants suivant:

 patient :
  identifiant  : patient
  mot de passe : password

 médecin :
   identifiant  : docteur
   mot de passe : password

 biologiste :
  identifiant  : biologiste
  mot de passe : password

LabResult

Tel. : 07 82 42 32 12
""")

# Add the html version.  This converts the message into a multipart/alternative
# container, with the original text message as the first part and the new html
# message as the second part.
logo_cid = make_msgid()
msg.add_alternative("""\
<html>
  <head></head>
  <body>
    <p>Bonjour,</p>

<p>Pour accéder au site de démonstration LabResult, vous pouvez utiliser les identifiants suivant:</p>
<ul>
 <li> patient :
  <ul>
  <li> identifiant  : patient</li>
  <li> mot de passe : password</li>
  </ul>
 </li>
<br>
 <li> médecin :
  <ul>
  <li> identifiant  : docteur</li>
  <li> mot de passe : password</li>
  </ul>
 </li>
<br>
 <li> biologiste :
  <ul>
  <li> identifiant  : biologiste</li>
  <li> mot de passe : password</li>
  </ul>
 </li>
</ul>

LabResult<br>
Tel : 07 82 42 32 12
<br>
    <img src="cid:{logo_cid}" \>
  </body>
</html>
""".format(logo_cid=logo_cid[1:-1]), subtype='html')
# note that we needed to peel the <> off the msgid for use in the html.

# Now add the related image to the html part.
with open("logo.png", 'rb') as img:
    msg.get_payload()[1].add_related(img.read(), 'logo', 'png',
                                     cid=logo_cid)

# Make a local copy of what we are going to send.
with open('outgoing.msg', 'wb') as f:
    f.write(bytes(msg))

msg2 = MIMEText("Envoi des identifians de démo à %s" % recipient)
msg2['Subject'] = "Connexion démo LabResult "
msg2['From'] = "demo-labresult@labresult.fr"
msg2['To'] = "julien.almarcha@gmail.com"
# Send the message via local SMTP server.
with smtplib.SMTP_SSL('mail.gandi.net') as s:
    s.login(USERNAME, PASSWORD)
    s.send_message(msg)
    s.send_message(msg2)
