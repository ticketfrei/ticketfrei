#!/usr/bin/env python

__author__ = "b3yond"

import twitter
import requests
from time import sleep

"""
How to get these keys is described in doc/twitter_api.md

After you received keys, store them in ../../api_keys, one at a line.
"""
with open("../appkeys/ticketfrei@twitter.com", "r") as file:
    keys = file.readlines()
    for status in keys:
        print status,


# create an Api object
api = twitter.Api(consumer_key = keys[0].strip(),
                  consumer_secret = keys[1].strip(),
                  access_token_key = keys[2].strip(),
                  access_token_secret = keys[3].strip())


# This counter is needed to keep track which was the last tweet you retweeted
# ACTUALLY it keeps track of the last mention, whether you retweeted it or not.
with open("../last_rt", "r+") as file:
    last_rt = file.read()


# Words which have to be included into the tweets for the tweet to get retweeted
with open("../triggerwords", "r") as file:
    triggers = [s.strip() for s in file.readlines()]

try:
    while 1:
        sleep(1)

        # Store all mentions in a list of Status Objects
        done = False
        while not done:
            try:
                mentions = api.GetMentions(since_id=last_rt)
                done = True
            except requests.exceptions.ConnectionError:
                print("[ERROR] Bad Connection.")
                sleep(10)

        print mentions  # debug
        for status in mentions:

            # Is the Text of the Tweet in the triggerlist?
            should_retweet = False
            for triggerword in triggers:
                if status.text.lower().find(triggerword):
                    should_retweet = True
                    break

            # Retweet status
            if should_retweet:
                done = False
                while not done:
                    try:
                        api.PostRetweet(status.id)
                        done = True

                    # This is an Error we need to get rid of. Why are tweets RTed twice?
#                    except twitter.error.TwitterError:
#                        print("[ERROR] probably you already retweeted this tweet.")
#                        done = True
                    except requests.exceptions.ConnectionError:
                        print("[ERROR] Bad Connection.")
                        sleep(10)

            # save the id so it doesn't get crawled again
            last_rt = status.id
            print last_rt

except:
    print "[ERROR] Shit went wrong, closing down."
    with open("../last_rt", "w") as file:
        file.write(str(last_rt))
    api.PostDirectMessage("Help! I broke down. restart me pls :$", "801098086005243904", "links_tech")