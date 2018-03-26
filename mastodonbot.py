#!/usr/bin/env python3

import logging
import mastodon
import re
import report
from user import User


logger = logging.getLogger(__name__)


class MastodonBot(object):
    def __init__(self, uid, db):
        self.user = User(db, uid)
        client_id, client_secret, access_token, instance_url = \
            self.user.get_masto_credentials()
        self.m = mastodon.Mastodon(
                client_id=client_id,
                client_secret=client_secret,
                access_token=access_token,
                api_base_url=instance_url
            )

        # load state
        try:
            self.seen_toots = self.user.get_seen_toot()
        except TypeError:
            self.seen_toots = 0

    def save_last(self):
        self.user.save_seen_toot(self.seen_toots)

    def crawl(self):
        """
        Crawl mentions from Mastodon.

        :return: list of statuses
        """
        mentions = []
        try:
            notifications = self.m.notifications()
        except:  # mastodon.Mastodon.MastodonAPIError is unfortunately not in __init__.py
            logger.error("Unknown Mastodon API Error.", exc_info=True)
            return mentions
        for status in notifications:
            if (status['type'] == 'mention' and
                    status['status']['id'] > self.seen_toots):
                # save state
                self.seen_toots = status['status']['id']
                self.save_last()
                # add mention to mentions
                text = re.sub(r'<[^>]*>', '', status['status']['content'])
                text = re.sub(
                        "(?<=^|(?<=[^a-zA-Z0-9-_.]))@([A-Za-z]+[A-Za-z0-9-_]+)",
                        "", text)
                mentions.append(report.Report(status['account']['acct'],
                                              "mastodon",
                                              text,
                                              status['status']['id'],
                                              status['status']['created_at']))
        return mentions

    def repost(self, mention):
        """
        Retoots a mention.

        :param mention: (report.Report object)
        """
        logger.info('Boosting toot from %s' % (
            mention.format()))
        self.m.status_reblog(mention.id)

    def post(self, report):
        """
        Toots a report from other sources.

        :param report: (report.Report object)
        """
        toot = report.format()
        self.m.toot(toot)

    def flow(self, trigger, reports=()):
        # toot external provided messages
        for report in reports:
            self.post(report)

        # boost mentions
        retoots = []
        for mention in self.crawl():
            if not trigger.is_ok(mention.text):
                continue
            self.repost(mention)
            retoots.append(mention)

        # return mentions for mirroring
        return retoots
