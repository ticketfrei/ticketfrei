#!/usr/bin/env python3

import pytoml as toml
import mastodon
import pickle
import os
import time

# read config in TOML format (https://github.com/toml-lang/toml#toml)
with open('ticketfrei.cfg') as configfile:
    config = toml.load(configfile)

client_id = os.path.join(
        'appkeys',
        config['app']['name'] + '@' + config['user']['server']
    )

if not os.path.isfile(client_id):
    mastodon.Mastodon.create_app(
            config['app']['name'],
            api_base_url=config['user']['server'],
            to_file=client_id
        )

m = mastodon.Mastodon(
        client_id=client_id,
        api_base_url=config['user']['server']
    )
m.log_in(config['user']['email'], config['user']['password'])

try:
    with open('seen_toots.pickle', 'rb') as f:
        seen_toots = pickle.load(f)
except IOError:
    seen_toots = set()

while True:
    for notification in m.notifications():
        if (notification['type'] == 'mention'
                and notification['status']['id'] not in seen_toots):
            print('Boosting toot %d from %s: %s' % (
                notification['status']['id'],
                notification['status']['account']['acct'],
                notification['status']['content']))
            seen_toots.add(notification['status']['id'])
            m.status_reblog(notification['status']['id'])
    with open('seen_toots.pickle.part', 'wb') as f:
        pickle.dump(seen_toots, f)
    os.rename('seen_toots.pickle.part', 'seen_toots.pickle')
    time.sleep(1)
