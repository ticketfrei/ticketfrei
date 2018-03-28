#!/usr/bin/env python3

from config import config
import logging
import sendmail
import ssl
import datetime
import email
import imaplib
import report
from user import User
from bot import Bot


logger = logging.getLogger(__name__)


class Mailbot(Bot):
    """
    Bot which sends Mails if mentioned via twitter/mastodon, and tells
    other bots that it received mails.
    """

    def __init__(self, uid):
        """
        Creates a Bot who listens to mails and forwards them to other
        bots.

        """
        try:
            self.mailinglist = self.user.get_mailinglist()
        except TypeError:
            self.mailinglist = None

        self.mailbox = imaplib.IMAP4_SSL(config["mail"]["imapserver"])
        context = ssl.create_default_context()
        try:
            self.mailbox.starttls(ssl_context=context)
        except:
            logger.error('StartTLS failed', exc_info=True)
        try:
            self.mailbox.login(config["mail"]["user"],
                               config["mail"]["passphrase"])
        except imaplib.IMAP4.error:
            logger.error("Login to mail server failed", exc_info=True)
            try:
                mailer = sendmail.Mailer()
                mailer.send('', config['web']['contact'],
                            'Ticketfrei Crash Report',
                            attachment=config['logging']['logpath'])
            except:
                logger.error('Mail sending failed', exc_info=True)

    def repost(self, status):
        """
        E-Mails don't have to be reposted - they already reached everyone on the mailing list.
        The function still needs to be here because backend.py assumes it, and take the
        report object they want to give us.

        :param status: (report.Report object)
        """
        pass

    def crawl(self, user):
        """
        crawl for new mails.
        :return: msgs: (list of report.Report objects)
        """
        mailinglist = user.get_mailinglist()
        try:
            rv, data = self.mailbox.select("Inbox")
        except imaplib.IMAP4.abort:
            logger.error("Crawling Mail failed", exc_info=True)
            rv = False
        msgs = []
        if rv == 'OK':
            rv, data = self.mailbox.search(None, "ALL")
            if rv != 'OK':
                return msgs

            for num in data[0].split():
                rv, data = self.mailbox.fetch(num, '(RFC822)')
                if rv != 'OK':
                    logger.error("Couldn't fetch mail %s %s" % (rv, str(data)))
                    return msgs
                msg = email.message_from_bytes(data[0][1])

                if not self.user.get_mailinglist() in msg['From']:
                    # get a comparable date out of the email
                    date_tuple = email.utils.parsedate_tz(msg['Date'])
                    date_tuple = datetime.datetime.fromtimestamp(
                            email.utils.mktime_tz(date_tuple)
                        )
                    date = int((date_tuple -
                                datetime.datetime(1970, 1, 1)).total_seconds())
                    if date > self.user.get_seen_mail():
                        self.last_mail = date
                        self.save_last()
                        msgs.append(self.make_report(msg))
        return msgs

    def save_last(self):
        """ Saves the last retweeted tweet in the db. """
        self.user.save_seen_mail(self.last_mail)

    def post(self, status):
        """
        sends reports by other sources to a mailing list.

        :param status: (report.Report object)
        """
        mailer = sendmail.Mailer()
        mailer.send(status.format(), self.mailinglist,
                    "Warnung: Kontrolleure gesehen")

    def make_report(self, msg):
        """
        generates a report out of a mail

        :param msg: email.parser.Message object
        :return: post: report.Report object
        """
        # get a comparable date out of the email
        date_tuple = email.utils.parsedate_tz(msg['Date'])
        date_tuple = datetime.datetime.fromtimestamp(
                email.utils.mktime_tz(date_tuple)
            )
        date = (date_tuple - datetime.datetime(1970, 1, 1)).total_seconds()

        author = msg.get("From")  # get mail author from email header
        # :todo take only the part before the @

        text = msg.get_payload()
        post = report.Report(author, "mail", text, None, date)
        self.last_mail = date
        self.save_last()
        return post

    def flow(self, trigger, statuses):
        """
        to be iterated. uses trigger to separate the sheep from the goats

        :param statuses: (list of report.Report objects)
        :return: statuses: (list of report.Report objects)
        """
        for status in statuses:
            self.post(status)

        msgs = self.crawl()

        statuses = []
        for msg in msgs:
            if trigger.is_ok(msg.get_payload()):
                statuses.append(msg)
        return statuses
