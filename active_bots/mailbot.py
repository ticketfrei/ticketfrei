#!/usr/bin/env python3

from config import config
import logging
import sendmail
import ssl
import datetime
import email
import imaplib
import report
from bot import Bot


logger = logging.getLogger(__name__)


class Mailbot(Bot):
    """
    Bot which sends Mails if mentioned via twitter/mastodon, and tells
    other bots that it received mails.
    """

    def login(self, user):
        # change to use mailbox of local system
        mailinglist = user.get_mailinglist()
        mailbox = imaplib.IMAP4_SSL(mailinglist)
        context = ssl.create_default_context()
        try:
            mailbox.starttls(ssl_context=context)
        except:
            logger.error('StartTLS failed', exc_info=True)
        try:
            mailbox.login(config["mail"]["user"],
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

    def crawl(self, user):
        """
        crawl for new mails.
        :return: msgs: (list of report.Report objects)
        """
        mailbox = self.login(user)
        try:
            rv, data = mailbox.select("Inbox")
        except imaplib.IMAP4.abort:
            logger.error("Crawling Mail failed", exc_info=True)
            rv = False
        msgs = []
        if rv == 'OK':
            rv, data = mailbox.search(None, "ALL")
            if rv != 'OK':
                return msgs

            for num in data[0].split():
                rv, data = mailbox.fetch(num, '(RFC822)')
                if rv != 'OK':
                    logger.error("Couldn't fetch mail %s %s" % (rv, str(data)))
                    return msgs
                msg = email.message_from_bytes(data[0][1])

                # check if email was sent by the bot itself. Different solution?
                if not user.get_mailinglist() in msg['From']:
                    # get a comparable date out of the email
                    date_tuple = email.utils.parsedate_tz(msg['Date'])
                    date_tuple = datetime.datetime.fromtimestamp(
                            email.utils.mktime_tz(date_tuple)
                        )
                    date = int((date_tuple -
                                datetime.datetime(1970, 1, 1)).total_seconds())
                    if date > user.get_seen_mail():
                        msgs.append(self.make_report(msg))
        return msgs

    def post(self, user, report):
        """
        sends reports by other sources to a mailing list.

        :param report: (report.Report object)
        """
        mailinglist = self.login(user)
        if report.source is not self:
            mailer = sendmail.Mailer()
            mailer.send(report.text, mailinglist,
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
        return post
