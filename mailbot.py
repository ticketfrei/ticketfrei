#!/usr/bin/env python3

import sendmail
import ssl
import time
import trigger
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

    def __init__(self, config, trigger, logger, history_path="last_mail"):
        """
        Creates a Bot who listens to mails and forwards them to other
        bots.

        :param config: (dictionary) config.toml as a dictionary of dictionaries
        """
        self.config = config
        self.trigger = trigger
        self.logger = logger

        self.history_path = history_path
        self.last_mail = self.get_history(self.history_path)

        try:
            self.mailinglist = self.config["mail"]["list"]
        except KeyError:
            self.mailinglist = None

        self.mailbox = imaplib.IMAP4_SSL(self.config["mail"]["imapserver"])
        context = ssl.create_default_context()
        try:
            self.mailbox.starttls(ssl_context=context)
        except:
            logmsg = logger.generate_tb(sys.exc_info())
            logger.log(logmsg)
        try:
            self.mailbox.login(self.config["mail"]["user"], self.config["mail"]["passphrase"])
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
        msgs = []
        if rv == 'OK':
            rv, data = self.mailbox.search(None, "ALL")
            if rv != 'OK':
                return msgs

            for num in data[0].split():
                rv, data = self.mailbox.fetch(num, '(RFC822)')
                if rv != 'OK':
                    logmsg = "Didn't receive mail. Error: " + rv + str(data)
                    self.logger.log(logmsg)
                    return msgs
                msg = email.message_from_bytes(data[0][1])

                # get a comparable date out of the email
                date_tuple = email.utils.parsedate_tz(msg['Date'])
                date_tuple = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                date = (date_tuple - datetime.datetime(1970, 1, 1)).total_seconds()
                if date > self.get_history(self.history_path):
                    self.last_mail = date
                    self.save_last_mail()
                    msgs.append(msg)
        return msgs

    def get_history(self, path):
        """ This counter is needed to keep track of your mails, so you
        don't double parse them

        :param path: string: contains path to the file where the ID of the
            last_mail is stored.
        :return: last_mail: ID of the last mail the bot parsed
        """
        try:
            with open(path, "r+") as f:
                last_mail = f.read()
        except IOError:
            with open(path, "w+") as f:
                last_mail = "0"
                f.write(last_mail)
        return float(last_mail)

    def save_last_mail(self):
        """ Saves the last retweeted tweet in last_mention. """
        with open(self.history_path, "w") as f:
            f.write(str(self.last_mail))

    def send_report(self, statuses):
        """
        sends reports by twitter & mastodon to a mailing list.

        :param statuses: (list) of status strings
        """
        for status in statuses:
            mailer = sendmail.Mailer(self.config)
            mailer.send(status, self.mailinglist, "Warnung: Kontrolleure gesehen")

    def to_social(self, msg):
        """
        sends a report from the mailing list to social
        :param msg: email.parser.Message object
        :return: post: (string) of author + text
        """
        # get a comparable date out of the email
        date_tuple = email.utils.parsedate_tz(msg['Date'])
        date_tuple = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        date = (date_tuple-datetime.datetime(1970,1,1)).total_seconds()

        author = msg.get("From")  # get mail author from email header
        # :todo take only the part before the @

        text = msg.get_payload()
        post = author + ": " + text
        self.last_mail = date
        self.save_last_mail()
        return post

    def flow(self, statuses):
        """
        to be iterated

        :param statuses: (list) of statuses to send to mailinglist
        :return: list of statuses to post in mastodon & twitter
        """
        self.send_report(statuses)

        msgs = self.listen()

        statuses = []
        for msg in msgs:
            if self.trigger.is_ok(msg.get_payload()):
                statuses.append(self.to_social(msg))
        return statuses


if __name__ == "__main__":
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    logger = logger.Logger(config)
    trigger = trigger.Trigger(config)

    m = Mailbot(config, trigger, logger)
    statuses = []
    try:
        while 1:
            print("Received Reports: " + str(m.flow(statuses)))
            time.sleep(1)
    except KeyboardInterrupt:
        print("Good bye. Remember to restart the bot!")
    except:
        exc = sys.exc_info()  # returns tuple [Exception type, Exception object, Traceback object]
        message = logger.generate_tb(exc)
        m.logger.log(message)
        m.save_last_mail()
        m.logger.shutdown(message)
