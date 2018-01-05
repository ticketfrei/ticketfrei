#!/usr/bin/env python3

import sendmail
import datetime
import email
import logger
import pytoml as toml
import imaplib
import sys

class Mailbot(object):
    """
    Bot which sends Mails if mentioned via twitter/mastodon, and tells
    other bots that it received mails.
    """

    def __init__(self, config, logger):
        """
        Creates a Bot who listens to mails and forwards them to other
        bots.

        :param config: (dictionary) config.toml as a dictionary of dictionaries
        """
        self.config = config
        self.logger = logger

        try:
            self.mailinglist = self.config["mail"]["list"]
        except KeyError:
            self.mailinglist = None

        self.mailbox = imaplib.IMAP4_SSL(self.config["mail"]["imapserver"])
        # context = ssl.create_default_context()
        # print(self.mailbox.starttls(ssl_context=context))  # print is a debug
        try:
            rv, data = self.mailbox.login(self.config["mail"]["user"],
                                     self.config["mail"]["passphrase"])
        except imaplib.IMAP4.error:
            logmsg = "Login to mail server failed."
            logmsg = logmsg + logger.generate_tb(sys.exc_info())
            logger.log(logmsg)
            logger.shutdown(logmsg)

    def listen(self):
        """
        listen for mails which contain goodwords but no badwords.
        :return:
        """
        rv, data = self.mailbox.select("Inbox")
        if rv == 'OK':
            rv, data = self.mailbox.search(None, "ALL")
            print(data)
            rv, data = self.mailbox.search(None, "ALL")
            if rv != 'OK':
                print("No messages found!")
                return

            for num in data[0].split():
                rv, data = self.mailbox.fetch(num, '(RFC822)')
                if rv != 'OK':
                    print("ERROR getting message", num)
                    return
                msg = email.message_from_bytes(data[0][1])
                hdr = email.header.make_header(email.header.decode_header(msg['Subject']))
                subject = str(hdr)
                print('Message %s: %s' % (num, subject))
                print('Raw Date:', msg['Date'])
                # Now convert to local date-time
                date_tuple = email.utils.parsedate_tz(msg['Date'])
                if date_tuple:
                    local_date = datetime.datetime.fromtimestamp(
                        email.utils.mktime_tz(date_tuple))
                    print ("Local Date:", local_date.strftime("%a, %d %b %Y %H:%M:%S"))
                #print(msg.as_string())
                author = msg.get("From")  # get mail author from email header
                text = msg.get_payload()
                print(author)
                print(text)
        # :todo check if they match trigger
        # :todo return a nice list of warning messages

    def send_warning(self, statuses):
        """
        sends warnings by twitter & mastodon to a mailing list.
        """
        for status in statuses:
            mailer = sendmail.Mailer(self.config)
            mailer.send(status, self.mailinglist, "Warnung: Kontrolleure gesehen")

if __name__ == "__main__":
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    logger = logger.Logger(config)

    m = Mailbot(config, logger)
    m.listen()

