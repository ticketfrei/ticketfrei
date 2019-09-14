#!/usr/bin/env python3

from bot import Bot
import logging
import mastodon
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
            m = mastodon.Mastodon(*user.get_masto_credentials())
        except TypeError:
            # No Mastodon Credentials in database.
            return mentions
        try:
            notifications = m.notifications()
        except mastodon.MastodonInternalServerError:
            try:
                logger.error("Mastodon Error: 500. Server: " + m.instance()['urls']['streaming_api'])
            except mastodon.MastodonServerError:
                logger.error("Mastodon Server Error 500, can't get instance.")
            return mentions
        except mastodon.MastodonBadGatewayError:
            try:
                logger.error("Mastodon Error: 502. Server: " + m.instance()['urls']['streaming_api'])
            except mastodon.MastodonServerError:
                logger.error("Mastodon Server Error 502, can't get instance.")
            return mentions
        except mastodon.MastodonServiceUnavailableError:
            try:
                logger.error("Mastodon Error: 503. Server: " + m.instance()['urls']['streaming_api'])
            except mastodon.MastodonServerError:
                logger.error("Mastodon Server Error 503, can't get instance.")
            return mentions
        except mastodon.MastodonGatewayTimeoutError:
            try:
                logger.error("Mastodon Error: 504. Server: " + m.instance()['urls']['streaming_api'])
            except mastodon.MastodonServerError:
                logger.error("Mastodon Server Error 504, can't get instance.")
            return mentions
        except mastodon.MastodonServerError:
            try:
                logger.error("Unknown Mastodon Server Error. Server: " + m.instance()['urls']['streaming_api'], exc_info=True)
            except mastodon.MastodonServerError:
                logger.error("Unknown Mastodon Server Error.", exc_info=True)
            return mentions
        for status in notifications:
            if (status['type'] == 'mention' and
                    not user.toot_is_seen(status['status']['uri'])):
                # save state
                user.toot_witness(status['status']['uri'])
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
            m = mastodon.Mastodon(*user.get_masto_credentials())
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
