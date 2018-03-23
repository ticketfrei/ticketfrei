#!/usr/bin/env python3

import mastodon
import re
# import time
# import trigger
# import sendmail
import report
from user import User


class RetootBot(object):
    def __init__(self, config, logger, uid, db):
        self.config = config
        self.logger = logger
        self.user = User(db, uid)
        client_id, client_secret, access_token, instance_url = self.user.get_masto_credentials()
        self.m = mastodon.Mastodon(client_id=client_id, client_secret=client_secret,
                                   access_token=access_token, api_base_url=instance_url)

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
            all = self.m.notifications()
        except:  # mastodon.Mastodon.MastodonAPIError is unfortunately not in __init__.py
            self.logger.error("Unknown Mastodon API Error.", exc_info=True)
            return mentions
        for status in all:
            if status['type'] == 'mention' and status['status']['id'] > self.seen_toots:
                # save state
                self.seen_toots = status['status']['id']
                self.save_last()
                # add mention to mentions
                text = re.sub(r'<[^>]*>', '', status['status']['content'])
                text = re.sub("(?<=^|(?<=[^a-zA-Z0-9-_.]))@([A-Za-z]+[A-Za-z0-9-_]+)", "", text)
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
        self.logger.info('Boosting toot from %s' % (
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

"""
if __name__ == '__main__':
    config = backend.get_config()

    trigger = trigger.Trigger(config)
    bot = RetootBot(config)

    try:
        while True:
            bot.flow(trigger)
            time.sleep(1)
    except KeyboardInterrupt:
            print("Good bye. Remember to restart the bot!")
    except:
        bot.logger.error('Shutdown', exc_info=True)
        try:
            mailer = sendmail.Mailer(config)
            mailer.send('', config['mail']['contact'],
                        'Ticketfrei Crash Report',
                        attachment=config['logging']['logpath'])
        except:
            bot.logger.error('Mail sending failed', exc_info=True)
"""