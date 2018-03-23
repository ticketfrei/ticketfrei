#!/usr/bin/env python3

import sendmail
import ssl
import time
import trigger
import datetime
import email
import ticketfrei
import imaplib
import report


class Mailbot(object):
    """
    Bot which sends Mails if mentioned via twitter/mastodon, and tells
    other bots that it received mails.
    """

    def __init__(self, config, history_path="last_mail"):
        """
        Creates a Bot who listens to mails and forwards them to other
        bots.

        :param config: (dictionary) config.toml as a dictionary of dictionaries
        """
        self.config = config
        self.logger = ticketfrei.get_logger(config)

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
            self.logger.error('StartTLS failed', exc_info=True)
        try:
            self.mailbox.login(self.config["mail"]["user"], self.config["mail"]["passphrase"])
        except imaplib.IMAP4.error:
            self.logger.error("Login to mail server failed", exc_info=True)
            try:
                mailer = sendmail.Mailer(config)
                mailer.send('', config['mail']['contact'],
                            'Ticketfrei Crash Report',
                            attachment=config['logging']['logpath'])
            except:
                self.logger.error('Mail sending failed', exc_info=True)

    def repost(self, status):
        """
        E-Mails don't have to be reposted - they already reached everyone on the mailing list.
        The function still needs to be here because ticketfrei.py assumes it, and take the
        report object they want to give us.

        :param status: (report.Report object)
        """
        pass

    def crawl(self):
        """
        crawl for new mails.
        :return: msgs: (list of report.Report objects)
        """
        try:
            rv, data = self.mailbox.select("Inbox")
        except imaplib.IMAP4.abort:
            self.logger.error("Crawling Mail failed", exc_info=True)
            rv = False
        msgs = []
        if rv == 'OK':
            rv, data = self.mailbox.search(None, "ALL")
            if rv != 'OK':
                return msgs

            for num in data[0].split():
                rv, data = self.mailbox.fetch(num, '(RFC822)')
                if rv != 'OK':
                    self.logger.error("Couldn't fetch mail %s %s" % (rv, str(data)))
                    return msgs
                msg = email.message_from_bytes(data[0][1])

                if not self.config['mail']['user'] + "@" + \
                        self.config["mail"]["mailserver"].partition(".")[2] in msg['From']:
                    # get a comparable date out of the email
                    date_tuple = email.utils.parsedate_tz(msg['Date'])
                    date_tuple = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                    date = (date_tuple - datetime.datetime(1970, 1, 1)).total_seconds()
                    if date > self.get_history(self.history_path):
                        self.last_mail = date
                        self.save_last()
                        msgs.append(self.make_report(msg))
        return msgs

    def get_history(self, path):
        """
        This counter is needed to keep track of your mails, so you
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

    def save_last(self):
        """ Saves the last retweeted tweet in last_mention. """
        with open(self.history_path, "w") as f:
            f.write(str(self.last_mail))

    def post(self, status):
        """
        sends reports by other sources to a mailing list.

        :param status: (report.Report object)
        """
        mailer = sendmail.Mailer(self.config)
        mailer.send(status.format(), self.mailinglist, "Warnung: Kontrolleure gesehen")

    def make_report(self, msg):
        """
        generates a report out of a mail

        :param msg: email.parser.Message object
        :return: post: report.Report object
        """
        # get a comparable date out of the email
        date_tuple = email.utils.parsedate_tz(msg['Date'])
        date_tuple = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        date = (date_tuple-datetime.datetime(1970,1,1)).total_seconds()

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


if __name__ == "__main__":
    config = ticketfrei.get_config()

    # initialise trigger
    trigger = trigger.Trigger(config)

    # initialise mail bot
    m = Mailbot(config)

    statuses = []
    try:
        while 1:
            print("Received Reports: " + str(m.flow(trigger, statuses)))
            time.sleep(1)
    except KeyboardInterrupt:
        print("Good bye. Remember to restart the bot!")
    except:
        m.logger.error('Shutdown', exc_info=True)
        m.save_last()
        try:
            mailer = sendmail.Mailer(config)
            mailer.send('', config['mail']['contact'],
                        'Ticketfrei Crash Report',
                        attachment=config['logging']['logpath'])
        except:
            m.logger.error('Mail sending failed', exc_info=True)
