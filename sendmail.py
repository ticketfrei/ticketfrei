#!/usr/bin/env python3

import smtplib
import pytoml as toml
from email.mime.text import MIMEText


class Mailer(object):
    """
    Maintains the connection to the mailserver and sends text to users.
    """

    def __init__(self, config):
        """

        :param config: The config file generated from config.toml
        """
        # This generates the From address by stripping the part until the first
        # period from the mail server address and won't work always.
        self.fromaddr = config["mail"]["user"] + "@" + \
                        config["mail"]["mailserver"].partition(".")[2]

        # starts a client session with the SMTP server
        self.s = smtplib.SMTP(config["mail"]["mailserver"])
        self.s.starttls()
        self.s.login(config["mail"]["user"], config["mail"]["passphrase"])

    def send(self, text, recipient, subject):
        """

        :param text: (string) the content of the mail
        :param recipient: (string) the recipient of the mail
        :param subject: (string) the subject of the mail
        :return: string for logging purposes, contains recipient & subject
        """
        msg = MIMEText(text)

        msg["From"] = self.fromaddr
        msg["To"] = recipient
        msg["Subject"] = subject

        self.s.send_message(msg)

        return "Sent mail to " + recipient + ": " + subject

# For testing:
if __name__ == '__main__':
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('config.toml') as configfile:
        config = toml.load(configfile)

        m = Mailer(config)
        print(m.send("This is a test mail.", m.fromaddr, "Test"))
