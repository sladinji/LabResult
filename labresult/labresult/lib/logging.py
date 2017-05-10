import smtplib
from logging.handlers import SMTPHandler
from email.mime.text import MIMEText
from email.utils import formatdate

class SMTPHandler_unicode(SMTPHandler):
    def emit(self, record):
        try:
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT # 25
            smtp = smtplib.SMTP(self.mailhost, port, timeout = 30)
            msg = self.format(record)
            # Au moment de la création de l'objet par MIMEText, si msg est
            # de type unicode,
            # il sera encodé selon _charset, sinon il sera laissé tel quel
            message = MIMEText(msg, _charset = "utf-8")
            # On ajoute les headers nécessaires. S'il sont de type unicode,
            # ils seront encodés selon _charset
            message.add_header("Subject", self.getSubject(record))
            message.add_header("From", self.fromaddr)
            message.add_header("To", ",".join(self.toaddrs))
            message.add_header("Date", formatdate())
            if self.username:
                if self.secure is not None:
                    smtp.ehlo()
                    smtp.starttls(*self.secure)
                    smtp.ehlo()
                    smtp.login(self.username, self.password)
                    # Envoi du message proprement encodé
                    smtp.sendmail(self.fromaddr, self.toaddrs,
                            message.as_string())
                    smtp.quit()
        except:
            self.handleError(record)
