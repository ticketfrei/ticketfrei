#!/usr/bin/env python3
from config import config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from getpass import getuser
import smtplib
from socket import getfqdn


logger = logging.getLogger(__name__)


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
    sendmail(config['mail']['contact'], "Test Mail",
             body="This is a test mail.")
