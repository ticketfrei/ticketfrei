#!/usr/bin/env python3

import logging
import sendmail
import datetime
import mailbox
import email
import report
from bot import Bot
from config import config
from db import db

logger = logging.getLogger(__name__)


class Mailbot(Bot):

    # returns a list of Report objects
    def crawl(self, user):
        reports = []
        mails = mailbox.mbox('/var/mail/test')  # todo: adjust to actual mailbox
        for msg in mails:
            if get_date_from_header(msg['Date']) > user.get_seen_mail():
                reports.append(make_report(msg, user))
        return reports

    # post/boost Report object
    def post(self, user, report):
        recipients = user.get_mailinglist()
        print(recipients)  # debug
        for rec in recipients:
            rec = rec[0]
            unsubscribe_text = "\n_______\nYou don't want to receive those messages? Unsubscribe with this link: "
            body = report.text + unsubscribe_text + config['web']['host'] + "/city/mail/unsubscribe/" \
                   + db.mail_subscription_token(rec, user.get_city())
            print(body)  # debug
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
    date = get_date_from_header(msg['Date'])

    author = msg['From']  # get mail author from email header
    # :todo take only the part in between the < >

    text = msg.get_payload()
    post = report.Report(author, "mail", text, None, date)
    user.save_seen_mail(date)
    return post


def get_date_from_header(header):
    """
    :param header: msg['Date']
    :return: float: total seconds
    """
    date_tuple = email.utils.parsedate_tz(header)
    date_tuple = datetime.datetime.fromtimestamp(
        email.utils.mktime_tz(date_tuple)
    )
    return (date_tuple - datetime.datetime(1970, 1, 1)).total_seconds()
