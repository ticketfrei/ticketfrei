#!/usr/bin/env python3
from config import config
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import logging
from getpass import getuser
import smtplib
from socket import getfqdn
import ssl


logger = logging.getLogger(__name__)


class Mailer(object):
    """
    Maintains the connection to the mailserver and sends text to users.
    """

    def __init__(self):
        """
        Creates an SMTP client to send a mail. Is called only once
        when you actually want to send a mail. After you sent the
        mail, the SMTP client is shut down again.

        """
        # This generates the From address by stripping the part until the first
        # period from the mail server address and won't work always.
        self.fromaddr = config["mail"]["user"] + "@" + config["mail"]["mailserver"].partition(".")[2]

        # starts a client session with the SMTP server
        self.s = smtplib.SMTP(config["mail"]["mailserver"])
        try:
            context = ssl.create_default_context()
            self.s.starttls(context=context)
        except BaseException:  # TODO: Amend specific exception
            logger.error('StartTLS failed.', exc_info=True)
        self.s.login(config["mail"]["user"], config["mail"]["passphrase"])

    def send(self, text, recipient, subject, attachment=None):
        """

        :param text: (string) the content of the mail
        :param recipient: (string) the recipient of the mail
        :param subject: (string) the subject of the mail
        :param attachment: (string) the path to the logfile
        :return: string for logging purposes, contains recipient & subject
        """
        msg = MIMEMultipart()
        msg.attach(MIMEText(text))

        msg["From"] = self.fromaddr
        msg["To"] = recipient
        msg["Subject"] = subject

        # attach logfile
        if attachment:
            with open(attachment, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name="logfile"
                )
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="logfile"'
            msg.attach(part)

        self.s.send_message(msg)
        self.s.close()

        return "Sent mail to " + recipient + ": " + subject


def sendmail(to, subject, city=None, body=''):
    msg = MIMEMultipart()
    if city:
        msg['From'] = 'Ticketfrei <%s@%s>' % (city, getfqdn())
    else:
        msg['From'] = 'Ticketfrei <%s@%s>' % (getuser(), getfqdn())
    msg['To'] = to
    msg['Subject'] = '[Ticketfrei] %s' % (subject, )
    msg.attach(MIMEText(body))

    with smtplib.SMTP('localhost') as smtp:
        smtp.send_message(msg)


# For testing:
if __name__ == '__main__':
    m = Mailer()
    print(m.send("This is a test mail.", m.fromaddr, "Test"))
