#!/usr/bin/env python3

import tweepy
import sys
import requests
import pytoml as toml
import trigger
from time import sleep
import traceback
import log


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

    def __init__(self, trigger, config, historypath="last_mention", logpath=None):
        """
        Initializes the bot and loads all the necessary data.

        :param historypath: Path to the file with ID of the last retweeted
            Tweet
        :param logpath: Path to the file where the log is stored
        """
        self.config = config

        # initialize API access
        keys = self.get_api_keys()
        auth = tweepy.OAuthHandler(consumer_key=keys[0],
                                   consumer_secret=keys[1])
        auth.set_access_token(keys[2],  # access_token_key
                              keys[3])  # access_token_secret
        self.api = tweepy.API(auth)

        # intialize shutdown contact
        try:
            self.no_shutdown_contact = False
            self.screen_name = \
                self.config['tapp']['shutdown_contact_screen_name']
        except KeyError:
            self.no_shutdown_contact = True

        self.historypath = historypath
        self.last_mention = self.get_history(self.historypath)
        self.trigger = trigger
        self.waitcounter = 0
        
        self.log = log.log.log(logpath)


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
        with open(self.historypath, "w") as f:
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
            self.log.log("Twitter API Error: Rate Limit Exceeded.")
            self.waitcounter += 60*15 + 1
        except requests.exceptions.ConnectionError:
            self.log.log("Twitter API Error: Bad Connection.")
            self.waitcounter += 10
        return None

    def retweet(self, status):
        """
        Retweets a given tweet.

        :param status: A tweet object.
        :return: toot: string of the tweet, to toot on mastodon.
        """
        while 1:
            try:
                self.api.retweet(status.id)
                self.log.log("Retweeted: " + self.format_mastodon(status))
                if status.id > self.last_mention:
                    self.last_mention = status.id
                return self.format_mastodon(status)
            # maybe one day we get rid of this error. If not, try to uncomment
            # these lines.
            except requests.exceptions.ConnectionError:
                self.log.log("Twitter API Error: Bad Connection.")
                sleep(10)
            except tweepy.TweepError as error:
                self.log.log("Twitter Error " + error.api_code + ": " + error.reason + error.response)
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
                self.log.log("Twitter API Error: Bad Connection.")
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

        if mentions is not None:
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

    def shutdown(self):
        """ If something breaks, it shuts down the bot and messages the owner.
        """
        logmessage = "Shit went wrong, closing down."
        if self.screen_name:
            logmessage = logmessage + " Sending message to " + self.screen_name
        self.log.log(logmessage)
        if self.no_shutdown_contact:
            return
        self.save_last_mention()
        try:
            self.api.send_direct_message(self.screen_name, "Help! I broke down. restart me pls :$")
        except:
            # traceback.print_exc()
            self.log.log(traceback.extract_tb(sys.exc_info()[2]))
            print()


if __name__ == "__main__":
    # create an Api object
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    trigger = trigger.Trigger(config)

    bot = RetweetBot(trigger, config)
    try:
        while True:
            bot.flow()
            sleep(60)
    except KeyboardInterrupt:
        print("Good bye! Remember to restart the bot.")
    except:
        bot.log.log(traceback.extract_tb(sys.exc_info()[2]))
        print()
        bot.shutdown()