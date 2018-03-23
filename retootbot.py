#!/usr/bin/env python3

import mastodon
import os
import pickle
import re
import time
import trigger
import sendmail
import report
import backend

class RetootBot(object):
    def __init__(self, config):
        self.config = config
        self.logger = backend.get_logger(config)
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
            os.unlink('seen_toots.pickle.part')
            with os.fdopen(os.open('seen_toots.pickle.part', os.O_WRONLY | os.O_EXCL | os.O_CREAT), 'wb') as f:
                pickle.dump(self.seen_toots, f)
        os.rename('seen_toots.pickle.part', 'seen_toots.pickle')

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
            if (status['type'] == 'mention' and status['status']['id'] not in self.seen_toots):
                # save state
                self.seen_toots.add(status['status']['id'])
                self.save_last()
                # add mention to mentions
                text = re.sub(r'<[^>]*>', '', status['status']['content'])
                text = re.sub("(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9-_]+)", "", text)
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
