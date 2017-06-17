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
    for i in keys:
        print i,


# create an Api object
api = twitter.Api(consumer_key = keys[0].strip(),
                  consumer_secret = keys[1].strip(),
                  access_token_key = keys[2].strip(),
                  access_token_secret = keys[3].strip())


# This counter is needed to keep track which was the last tweet you retweeted
with open("../last_rt", "r+") as file:
    last_rt = file.read()


# Words which have to be included into the tweets for the tweet to get retweeted
with open("../triggerwords", "r") as file:
    triggers = file.readlines()

try:
    while 1:
        sleep(1)

        # Store all mentions in a list of Status Objects
        try:
            mentions = api.GetMentions(since_id=last_rt)
        except requests.exceptions.ConnectionError:
            done = False
            while done == False:
                try:
                    mentions = api.GetMentions(since_id=last_rt)
                    done = True
                except:
                    sleep(10)

        print mentions
        for i in mentions:
            print i.user.name, i.user.id, i.text  # debug

            # Is the Text of the Tweet in the triggerlist?
            for j in triggers:
                if i.text.lower().find(j):

                    # Retweet status
                    try:
                        api.PostRetweet(i.id)

                    # This is an Error we need to get rid of. Why are tweets RTed twice?
                    except twitter.error.TwitterError:
                        print("[ERROR] probably you already retweeted this tweet.")
                    except requests.exceptions.ConnectionError:
                        done = False
                        while done == False:
                            try:
                                api.PostRetweet(i.id)
                                done = True
                            except:
                                sleep(10)

                    # save the id so it doesn't get crawled again
                    last_rt = i.id
                    break
except:
    api.PostDirectMessage("Help! I broke down. restart me pls :$", "801098086005243904", "links_tech")
    with open("../last_rt", "w") as file:
        file.write(last_rt)