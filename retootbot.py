#!/usr/bin/env python3

import pytoml as toml
import mastodon
import os
import pickle
import re
import time
import trigger
import logging
import sendmail
import report

logger = logging.getLogger(__name__)


class RetootBot(object):
    def __init__(self, config):
        self.config = config
        self.client_id = self.register()
        self.m = self.login()

        # load state
        try:
            with open('seen_toots.pickle', 'rb') as f:
                self.seen_toots = pickle.load(f)
        except IOError:
            self.seen_toots = set()

    def register(self):
        client_id = os.path.join(
            'appkeys',
            self.config['mapp']['name'] +
            '@' + self.config['muser']['server']
        )

        if not os.path.isfile(client_id):
            mastodon.Mastodon.create_app(
                self.config['mapp']['name'],
                api_base_url=self.config['muser']['server'],
                to_file=client_id
            )
        return client_id

    def login(self):
        m = mastodon.Mastodon(
            client_id=self.client_id,
            api_base_url=self.config['muser']['server']
        )
        m.log_in(
            self.config['muser']['email'],
            self.config['muser']['password']
        )
        return m

    def save_last(self):
        """ save the last seen toot """
        try:
            with os.fdopen(os.open('seen_toots.pickle.part', os.O_WRONLY | os.O_EXCL | os.O_CREAT), 'wb') as f:
                pickle.dump(self.seen_toots, f)
        except FileExistsError:
            with os.fdopen(os.open('seen_toots.pickle.part', os.O_WRONLY), 'wb') as f:
                pickle.dump(self.seen_toots, f)

    def crawl(self):
        """
        Crawl mentions from Mastodon.

        :return: list of statuses
        """
        all = self.m.notifications()
        mentions = []
        for status in all:
            if (status['type'] == 'mention' and status['status']['id'] not in self.seen_toots):
                # save state
                self.seen_toots.add(status['status']['id'])
                self.save_last()
                os.rename('seen_toots.pickle.part', 'seen_toots.pickle')
                # add mention to mentions
                mentions.append(report.Report(status['account']['acct'],
                                              "mastodon",
                                              re.sub(r'<[^>]*>', '', status['status']['content']),
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


if __name__ == '__main__':
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    fh = logging.FileHandler(config['logging']['logpath'])
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    trigger = trigger.Trigger(config)
    bot = RetootBot(config)

    try:
        while True:
            bot.flow(trigger)
            time.sleep(1)
    except KeyboardInterrupt:
            print("Good bye. Remember to restart the bot!")
    except:
        logger.error('Shutdown', exc_info=True)
        try:
            mailer = sendmail.Mailer(config)
            mailer.send('', config['mail']['contact'],
                        'Ticketfrei Crash Report',
                        attachment=config['logging']['logpath'])
        except:
            logger.error('Mail sending failed', exc_info=True)
