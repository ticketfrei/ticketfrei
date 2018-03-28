#!/usr/bin/env python3

from bot import Bot
import logging
from mastodon import Mastodon
import re
from report import Report


logger = logging.getLogger(__name__)


class MastodonBot(Bot):
    def crawl(self, user):
        """
        Crawl mentions from Mastodon.

        :return: list of statuses
        """
        mentions = []
        m = Mastodon(*user.get_masto_credentials())
        try:
            notifications = m.notifications()
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
                mentions.append(Report(status['account']['acct'],
                                       self,
                                       text,
                                       status['status']['id'],
                                       status['status']['created_at']))
        return mentions

    def post(self, user, report):
        m = Mastodon(*user.get_masto_credentials())
        if report.source == self:
            m.status_reblog(report.id)
        else:
            m.toot(report.text)
