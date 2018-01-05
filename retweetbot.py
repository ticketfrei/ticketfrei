#!/usr/bin/env python3

import tweepy
import sys
import requests
import pytoml as toml
import trigger
from time import sleep
import logger


class RetweetBot(object):
    """
    This bot retweets all tweets which
    1) mention him,
    2) contain at least one of the triggerwords provided.

    api: The api object, generated with your oAuth keys, responsible for
        communication with twitter rest API
    triggers: a list of words, one of them has to be in a tweet for it to be
        retweeted
    last_mention: the ID of the last tweet which mentioned you
    """

    def __init__(self, trigger, config, logger, history_path="last_mention"):
        """
        Initializes the bot and loads all the necessary data.

        :param trigger: object of the trigger
        :param config: (dictionary) config.toml as a dictionary of dictionaries
        :param logger: object of the logger
        :param history_path: Path to the file with ID of the last retweeted
            Tweet
        """
        self.config = config

        # initialize API access
        keys = self.get_api_keys()
        auth = tweepy.OAuthHandler(consumer_key=keys[0],
                                   consumer_secret=keys[1])
        auth.set_access_token(keys[2],  # access_token_key
                              keys[3])  # access_token_secret
        self.api = tweepy.API(auth)

        self.history_path = history_path
        self.last_mention = self.get_history(self.history_path)
        self.trigger = trigger
        self.waitcounter = 0

        self.logger = logger

    def get_api_keys(self):
        """
        How to get these keys is described in doc/twitter_api.md

        After you received keys, store them in your config.toml like this:
        [tapp]
        consumer_key = "..."
        consumer_secret = "..."

        [tuser]
        access_token_key = "..."
        access_token_secret = "..."

        :return: keys: list of these 4 strings.
        """
        keys = [self.config['tapp']['consumer_key'], self.config['tapp']['consumer_secret'],
                self.config['tuser']['access_token_key'], self.config['tuser']['access_token_secret']]
        return keys

    def get_history(self, path):
        """ This counter is needed to keep track of your mentions, so you
        don't double RT them

        :param path: string: contains path to the file where the ID of the
            last_mention is stored.
        :return: last_mention: ID of the last tweet which mentioned the bot
        """
        try:
            with open(path, "r+") as f:
                last_mention = f.read()
        except IOError:
            with open(path, "w+") as f:
                last_mention = "0"
                f.write(last_mention)
        return int(last_mention)

    def save_last_mention(self):
        """ Saves the last retweeted tweet in last_mention. """
        with open(self.history_path, "w") as f:
            f.write(str(self.last_mention))

    def waiting(self):
        """
        If the counter is not 0, you should be waiting instead.

        :return: self.waitcounter(int): if 0, do smth.
        """
        if self.waitcounter > 0:
            sleep(1)
            self.waitcounter -= 1
        return self.waitcounter

    def format_mastodon(self, status):
        """
        Bridge your Retweets to mastodon.

        :rtype: string
        :param status: Object of a tweet.
        :return: toot: text tooted on mastodon, e.g. "_b3yond: There are
            uniformed controllers in the U2 at Opernhaus."
        """
        toot = status.user.name + ": " + status.text
        return toot

    def crawl_mentions(self):
        """
        crawls all Tweets which mention the bot from the twitter rest API.

        :return: list of Status objects
        """
        try:
            if not self.waiting():
                if self.last_mention == 0:
                    mentions = self.api.mentions_timeline()
                else:
                    mentions = self.api.mentions_timeline(since_id=self.last_mention)
                return mentions
        except tweepy.RateLimitError:
            logmsg = "Twitter API Error: Rate Limit Exceeded."
            logmsg = logmsg + self.logger.generate_tb(sys.exc_info())
            self.logger.log(logmsg)
            self.waitcounter += 60*15 + 1
        except requests.exceptions.ConnectionError:
            logmsg = "Twitter API Error: Bad Connection."
            logmsg = logmsg + self.logger.generate_tb(sys.exc_info())
            self.logger.log(logmsg)
            self.waitcounter += 10
        return []

    def retweet(self, status):
        """
        Retweets a given tweet.

        :param status: A tweet object.
        :return: toot: string of the tweet, to toot on mastodon.
        """
        while 1:
            try:
                self.api.retweet(status.id)
                self.logger.log("Retweeted: " + self.format_mastodon(status))
                if status.id > self.last_mention:
                    self.last_mention = status.id
                return self.format_mastodon(status)
            except requests.exceptions.ConnectionError:
                logmsg = "Twitter API Error: Bad Connection."
                logmsg = logmsg + self.logger.generate_tb(sys.exc_info())
                self.logger.log(logmsg)
                sleep(10)
            # maybe one day we get rid of this error:
            except tweepy.TweepError:
                logmsg = "Twitter Error."
                logmsg = logmsg + self.logger.generate_tb(sys.exc_info())
                self.logger.log(logmsg)
                # self.log.log("Twitter API Error: You probably already retweeted this tweet: " + status.text)
                if status.id > self.last_mention:
                    self.last_mention = status.id
                return None

    def tweet(self, post):
        """
        Tweet a post.

        :param post: String with the text to tweet.
        """
        if len(post) > 280:
            post = post[:280 - 4] + u' ...'
        while 1:
            try:
                self.api.update_status(status=post)
                return
            except requests.exceptions.ConnectionError:
                logmsg = "Twitter API Error: Bad Connection."
                logmsg = logmsg + self.logger.generate_tb(sys.exc_info())
                self.logger.log(logmsg)
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
            if self.trigger.is_ok(status.text):
                # Retweet status
                toot = self.retweet(status)
                if toot:
                    mastodon.append(toot)

            # save the id so it doesn't get crawled again
            if status.id > self.last_mention:
                self.last_mention = status.id
            self.save_last_mention()
        # Return Retweets for tooting on mastodon
        return mastodon


if __name__ == "__main__":
    # create an Api object
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    trigger = trigger.Trigger(config)
    logger = logger.Logger(config)

    bot = RetweetBot(trigger, config, logger)
    try:
        while True:
            bot.flow()
            sleep(60)
    except KeyboardInterrupt:
        print("Good bye. Remember to restart the bot!")
    except:
        exc = sys.exc_info()  # returns tuple [Exception type, Exception object, Traceback object]
        message = logger.generate_tb(exc)
        bot.logger.log(message)
        bot.save_last_mention()
        bot.logger.shutdown(message)
