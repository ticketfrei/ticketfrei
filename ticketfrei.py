#!/usr/bin/env python3

import pytoml as toml
import mastodon
import os
import pickle
import re
import time


class RetootBot(object):
    def __init__(self, config):
        self.config = config
        self.register()
        self.login()

        # load state
        try:
            with open('seen_toots.pickle', 'rb') as f:
                self.seen_toots = pickle.load(f)
        except IOError:
            self.seen_toots = set()

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

    def retoot(self, toots=[]):
        # toot external provided messages
        for toot in toots:
            self.m.toot(toot)

        # boost mentions
        retoots = []
        for notification in self.m.notifications():
            if (notification['type'] == 'mention'
                    and notification['status']['id'] not in self.seen_toots):
                print('Boosting toot %d from %s: %s' % (
                    notification['status']['id'],
                    notification['status']['account']['acct'],
                    notification['status']['content']))
                self.m.status_reblog(notification['status']['id'])
                retoots.append(re.sub('<[^>]*>', '',
                                      notification['status']['content']))
                self.seen_toots.add(notification['status']['id'])

        # save state
        with open('seen_toots.pickle.part', 'xb') as f:
            pickle.dump(self.seen_toots, f)
        os.rename('seen_toots.pickle.part', 'seen_toots.pickle')

        # return mentions for mirroring
        return retoots


if __name__ == '__main__':
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('ticketfrei.cfg') as configfile:
        bot = RetootBot(toml.load(configfile))

    while True:
        bot.retoot()
        time.sleep(1)
