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
        try:
            m = Mastodon(*user.get_masto_credentials())
        except TypeError:
            # logger.error("No Mastodon Credentials in database.", exc_info=True)
            return mentions
        try:
            notifications = m.notifications()
        except Exception:
            logger.error("Unknown Mastodon API Error.", exc_info=True)
            return mentions
        for status in notifications:
            if user.get_seen_toot() is None:
                user.init_seen_toot(m.instance()['uri'])
            if (status['type'] == 'mention' and
                    status['status']['id'] > user.get_seen_toot()):
                # save state
                user.save_seen_toot(status['status']['id'])
                # add mention to mentions
                text = re.sub(r'<[^>]*>', '', status['status']['content'])
                text = re.sub(
                        "(?<=^|(?<=[^a-zA-Z0-9-_.]))@([A-Za-z]+[A-Za-z0-9-_]+)",
                        "", text)
                if status['status']['visibility'] == 'public':
                    mentions.append(Report(status['account']['acct'],
                                           self,
                                           text,
                                           status['status']['id'],
                                           status['status']['created_at']))
                else:
                    mentions.append(Report(status['account']['acct'],
                                           'mastodonPrivate',
                                           text,
                                           status['status']['id'],
                                           status['status']['created_at']))
        return mentions

    def post(self, user, report):
        try:
            m = Mastodon(*user.get_masto_credentials())
        except TypeError:
            return  # no mastodon account for this user.
        if report.source == self:
            try:
                m.status_reblog(report.id)
            except Exception:
                logger.error('Error boosting: ' + report.id, exc_info=True)
        else:
            text = report.text
            if len(text) > 500:
                text = text[:500 - 4] + u' ...'
            try:
                m.toot(text)
            except Exception:
                logger.error('Error tooting: ' + user.get_city() + ': ' +
                             report.id, exc_info=True)
