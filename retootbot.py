#!/usr/bin/env python3

import pytoml as toml
import mastodon
import os
import pickle
import re
import time
import trigger
import logger


class RetootBot(object):
    def __init__(self, config, filter, logger):
        self.config = config
        self.filter = filter
        self.register()
        self.login()

        # load state
        try:
            with open('seen_toots.pickle', 'rb') as f:
                self.seen_toots = pickle.load(f)
        except IOError:
            self.seen_toots = set()

        self.logger = logger

    def register(self):
        self.client_id = os.path.join(
            'appkeys',
            self.config['mapp']['name'] +
            '@' + self.config['muser']['server']
        )

        if not os.path.isfile(self.client_id):
            mastodon.Mastodon.create_app(
                self.config['mapp']['name'],
                api_base_url=self.config['muser']['server'],
                to_file=self.client_id
            )

    def login(self):
        self.m = mastodon.Mastodon(
            client_id=self.client_id,
            api_base_url=self.config['muser']['server']
        )
        self.m.log_in(
            self.config['muser']['email'],
            self.config['muser']['password']
        )

    def retoot(self, toots=()):
        # toot external provided messages
        for toot in toots:
            self.m.toot(toot)

        # boost mentions
        retoots = []
        for notification in self.m.notifications():
            if (notification['type'] == 'mention'
                    and notification['status']['id'] not in self.seen_toots):
                self.seen_toots.add(notification['status']['id'])
                text_content = re.sub(r'<[^>]*>', '',
                                      notification['status']['content'])
                if not self.filter.is_ok(text_content):
                    continue
                self.logger.log('Boosting toot from %s: %s' % (
                    # notification['status']['id'],
                    notification['status']['account']['acct'],
                    notification['status']['content']))
                self.m.status_reblog(notification['status']['id'])
                retoots.append('%s: %s' % (
                    notification['status']['account']['acct'],
                    re.sub(r'@\S*', '', text_content)))
        # If the Mastodon instance returns interesting Errors, add them here:

        # save state
        with os.fdopen(os.open('seen_toots.pickle.part', os.O_WRONLY | os.O_EXCL | os.O_CREAT), 'wb') as f:
            pickle.dump(self.seen_toots, f)
        os.rename('seen_toots.pickle.part', 'seen_toots.pickle')

        # return mentions for mirroring
        return retoots


if __name__ == '__main__':
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    filter = trigger.Trigger(config)
    logger = logger.Logger()

    bot = RetootBot(config, filter, logger)

    while True:
        bot.retoot()
        time.sleep(1)
