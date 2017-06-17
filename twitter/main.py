#!/usr/bin/env python
__author__ = "b3yond"

import twitter
from time import sleep

"""
How to get these keys is described in doc/twitter_api.md

After you received keys, store them in ../../api_keys, one at a line.
"""
with open("../../api_keys", "r") as file:
    keys = file.readlines()
    for i in keys:
        print i,


# create an Api object
api = twitter.Api(consumer_key = keys[0].strip(),
                  consumer_secret = keys[1].strip(),
                  access_token_key = keys[2].strip(),
                  access_token_secret = keys[3].strip())


# This counter is needed to keep track which was the last tweet you retweeted
last_rt = ""


# Words which have to be included into the tweets for the tweet to get retweeted
with open("../triggerwords.txt", "r") as file:
    triggers = file.readlines()


while 1:
    sleep(1)

    # Store all mentions in a list of Status Objects
    mentions = api.GetMentions(since_id=last_rt)
    print mentions
    for i in mentions:
        print i.user.name, i.user.id, i.text  # debug

        # Is the Text of the Tweet in the triggerlist?
        for j in triggers:
            if i.text.lower().find(j):

                # Retweet status, save the id so it doesn't get crawled again
                try:
                    feedback = api.PostRetweet(i.id)
                    print feedback
                except twitter.error.TwitterError:
                    print("[ERROR] probably you already retweeted this tweet.")
                last_rt = i.id
                break