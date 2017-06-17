#!/usr/bin/env python

import twitter
import requests
import trigger
from time import sleep


class RetweetBot(object):
    """
    This bot retweets all tweets which
    1) mention him,
    2) contain at least one of the triggerwords provided.

    api: The api object, generated with your oAuth keys, responsible for communication with twitter rest API
    triggers: a list of words, one of them has to be in a tweet for it to be retweeted
    last_mention: the ID of the last tweet which mentioned you
    """

    def __init__(self, trigger=trigger.Trigger(),
                 keypath="appkeys/ticketfrei@twitter.com",
                 historypath="last_mention",
                 triggerpath="goodlist",
                 user_id="801098086005243904",
                 screen_name="links_tech"):
        """
        Initializes the bot and loads all the necessary data.

        :param keypath: Path to the file with API keys
        :param historypath: Path to the file with ID of the last retweeted Tweet
        :param triggerpath: Path to the file of the triggerwords
        """
        keys = self.get_api_keys(keypath)
        self.api = twitter.Api(consumer_key=keys[0],
                               consumer_secret=keys[1],
                               access_token_key=keys[2],
                               access_token_secret=keys[3])
        self.historypath = historypath
        self.triggerpath = triggerpath
        self.user_id = user_id
        self.screen_name = screen_name
        self.last_mention = bot.get_history(self.historypath)
        self.triggers = bot.get_trigger(self.triggerpath)
        self.trigger = trigger

    def get_api_keys(self, path):
        """
        How to get these keys is described in doc/twitter_api.md

        After you received keys, store them in ../appkeys/appname@service.tld, one at a line:
        consumer_key
        consumer_secret
        access_token_key
        access_token_secret

        :return: keys: list of these 4 strings.
        """
        keys = []
        try:
            with open(path, "r") as f:
                keys = [s.strip() for s in f.readlines()]
        except IOError:
            print "[ERROR] You didn't specify Twitter API oAuth keys. Look into the documentation."
            exit(-1)
        return keys

    def get_history(self, path):
        """ This counter is needed to keep track of your mentions, so you don't double RT them

        :param path: string: contains path to the file where the ID of the last_mention is stored.
        :return: last_mention: ID of the last tweet which mentioned the bot
        """
        with open(path, "r+") as f:
            last_mention = f.read()
        return last_mention

    def get_trigger(self, path):
        """ Words which have to be included into the tweets for the tweet to get retweeted """
        with open(path, "r") as f:
            triggers = [s.strip() for s in f.readlines()]
        return triggers

    def format_mastodon(self, status):
        """
        Bridge your Retweets to mastodon.
        :todo vmann: add all the mastodon API magic.

        :param status: Object of a tweet.
        :return: toot: text tooted on mastodon, e.g. "_b3yond: There are uniformed controllers in the U2 at Opernhaus."
        """
        toot = status.user.name + ": " + status.text
        return toot

    def crawl_mentions(self):
        """
        crawls all Tweets which mention the bot from the twitter rest API.

        :return: list of Status objects
        """
        while 1:
            try:
                mentions = self.api.GetMentions(since_id=self.last_mention)
                return mentions
            except requests.exceptions.ConnectionError:
                print("[ERROR] Bad Connection.")
                sleep(10)

    def retweet(self, status):
        """
        Retweets a given tweet.

        :param status: A tweet object.
        :return: toot: string of the tweet, to toot on mastodon.
        """
        while 1:
            try:
                self.api.PostRetweet(status.id)
                return self.format_mastodon(status)
            # Hopefully we got rid of this error. If not, try to uncomment these lines.
            # except twitter.error.TwitterError:
            #    print("[ERROR] probably you already retweeted this tweet.")
            #    done = True
            except requests.exceptions.ConnectionError:
                print("[ERROR] Bad Connection.")
                sleep(10)

    def tweet(self, post):
        """
        Tweet a post.

        :param post: String with the text to tweet.
        """
        while 1:
            try:
                self.api.PostUpdate(status=post)
                return
            except requests.exceptions.ConnectionError:
                print("[ERROR] Bad Connection.")
                sleep(10)

    def flow(self, to_tweet=()):
        """ The flow of crawling mentions and retweeting them.

        :param to_tweet: list of strings to tweet
        :return list of retweeted tweets, to toot on mastodon
        """

        # Tweet the toots the Retootbot gives to us
        for post in to_tweet:
            self.tweet(post)

        # Store all mentions in a list of Status Objects
        mentions = self.crawl_mentions()
        mastodon = []

        for status in mentions:
            # Is the Text of the Tweet in the triggerlist?
            if self.trigger.check_string(status.text):
                # Retweet status
                mastodon.append(self.retweet(status))

            # save the id so it doesn't get crawled again
            self.last_mention = status.id
            print self.last_mention
        # Return Retweets for tooting on mastodon
        return mastodon

    def shutdown(self):
        """ If something breaks, it shuts down the bot and messages the owner. """
        print "[ERROR] Shit went wrong, closing down."
        with open(self.historypath, "w") as f:
            f.write(str(self.last_mention))
        self.api.PostDirectMessage("Help! I broke down. restart me pls :$", self.user_id, self.screen_name)


if __name__ == "main":
    # create an Api object
    bot = RetweetBot()
    try:
        while True:
            bot.flow()
    except:
        bot.shutdown()
