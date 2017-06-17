#!/usr/bin/env python

import twitter
import requests
from time import sleep


class Retweetbot(object):
    """
    :todo description

    api: The api object, generated with your oAuth keys, responsible for communication with twitter rest API
    triggers: a list of words, one of them has to be in a tweet for it to be retweeted
    last_mention: the ID of the last tweet which mentioned you
    """

    def __init__(self, keypath="appkeys/ticketfrei@twitter.com",
                 historypath="last_mention",
                 triggerpath="triggerwords",
                 user_id="801098086005243904",
                 screen_name="links_tech"):
        """
        Initializes the bot and loads all the necessary data.

        :param keypath: Path to the file with API keys
        :param historypath: Path to the file with ID of the last retweeted Tweet
        :param triggerpath: Path to the file of the triggerwords
        """
        keys = self.get_api_keys(keypath)
        self.api = twitter.Api(consumer_key=keys[0].strip(),
                               consumer_secret=keys[1].strip(),
                               access_token_key=keys[2].strip(),
                               access_token_secret=keys[3].strip())
        self.historypath = historypath
        self.triggerpath = triggerpath
        self.user_id = user_id
        self.screen_name = screen_name
        self.last_mention = bot.get_history(self.historypath)
        self.triggers = bot.get_trigger(self.triggerpath)

    def get_api_keys(self, path):
        """
        How to get these keys is described in doc/twitter_api.md

        After you received keys, store them in ../appkeys/appname@service.tld, one at a line:
        consumer_key
        consumer_secret
        access_token_key
        access_token_secret
        """
        with open(path, "r") as f:
            keys = f.readlines()
        return keys

    def get_history(self, path):
        """ This counter is needed to keep track of your mentions, so you don't double RT them """
        with open(path, "r+") as f:
            last_mention = f.read()
        return last_mention

    def get_trigger(self, path):
        """ Words which have to be included into the tweets for the tweet to get retweeted """
        with open(path, "r") as f:
            triggers = [s.strip() for s in f.readlines()]
        return triggers

    def bridge_mastodon(self, status):
        """
        Bridge your Retweets to mastodon.
        :todo vmann: add all the mastodon API magic.

        :param status: Object of a tweet.
        :return: toot: text tooted on mastodon, e.g. "_b3yond: There are uniformed controllers in the U2 at Opernhaus."
        """
        toot = status.user.name + ": " + status.text
        return toot

    def crawl_mentions(self):
        done = False
        mentions = []
        while not done:
            try:
                mentions = self.api.GetMentions(since_id=self.last_mention)
                done = True
            except requests.exceptions.ConnectionError:
                print("[ERROR] Bad Connection.")
                sleep(10)
        return mentions

    def trigger_rt(self, status):
        for triggerword in self.triggers:
            if status.text.lower().find(triggerword):
                return True
        return False

    def retweet(self, status):
        done = False
        while not done:
            try:
                self.api.PostRetweet(status.id)
                self.bridge_mastodon(status)
                done = True

            # Hopefully we got rid of this error. If not, try to uncomment these lines.
            # except twitter.error.TwitterError:
            #    print("[ERROR] probably you already retweeted this tweet.")
            #    done = True
            except requests.exceptions.ConnectionError:
                print("[ERROR] Bad Connection.")
                sleep(10)

    def flow(self):
        """ The flow of crawling mentions and retweeting them."""

        # Store all mentions in a list of Status Objects
        mentions = self.crawl_mentions()

        for status in mentions:
            # Is the Text of the Tweet in the triggerlist?
            should_retweet = self.trigger_rt(status)

            # Retweet status
            if should_retweet:
                self.retweet(status)

            # save the id so it doesn't get crawled again
            self.last_mention = status.id
            print self.last_mention

    def shutdown(self):
        print "[ERROR] Shit went wrong, closing down."
        with open(self.historypath, "w") as f:
            f.write(str(self.last_mention))
        self.api.PostDirectMessage("Help! I broke down. restart me pls :$", self.user_id, self.screen_name)


if __name__ == "main":
    # create an Api object
    bot = Retweetbot()
    try:
        bot.flow()
    except:
        bot.shutdown()
