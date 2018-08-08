#!/usr/bin/env python3

import logging
import sendmail
import datetime
import email
import report
from bot import Bot


logger = logging.getLogger(__name__)


class Mailbot(Bot):

    # returns a list of Report objects
    def crawl(self, user):
        reports = []
        mails = []  # todo: look if new reports are in mailbox
        for msg in mails:
            if msg.date > user.get_seen_mail():
                reports.append(make_report(msg, user))
        return reports

    # post/boost Report object
    def post(self, user, report):
        recipients = user.get_mailinglist()
        for rec in recipients:
            rec = rec[0]
            unsubscribe_link = ""  # todo: generate unsubscribe link
            body = report.text + unsubscribe_link
            if report.author != rec:
                try:
                    sendmail.sendmail(rec, "Ticketfrei " + user.get_city() +
                                  " Report", body=body)
                except Exception:
                    logger.error("Sending Mail failed.", exc_info=True)


def make_report(msg, user):
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
    user.save_seen_mail(date)
    return post
