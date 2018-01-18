#!/usr/bin/env python3

import tweepy
import re
import requests
import pytoml as toml
import trigger
from time import sleep
import report
import logging
import sendmail

logger = logging.getLogger(__name__)


class RetweetBot(object):
    """
    This bot retweets all tweets which
    1) mention him,
    2) contain at least one of the triggerwords provided.

    api: The api object, generated with your oAuth keys, responsible for
        communication with twitter rest API
    last_mention: the ID of the last tweet which mentioned you
    """

    def __init__(self, config, history_path="last_mention"):
        """
        Initializes the bot and loads all the necessary data.

        :param config: (dictionary) config.toml as a dictionary of dictionaries
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
        self.waitcounter = 0

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

    def save_last(self):
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

    def crawl(self):
        """
        crawls all Tweets which mention the bot from the twitter rest API.

        :return: reports: (list of report.Report objects)
        """
        reports = []
        try:
            if not self.waiting():
                if self.last_mention == 0:
                    mentions = self.api.mentions_timeline()
                else:
                    mentions = self.api.mentions_timeline(since_id=self.last_mention)
                for status in mentions:
                    text = re.sub("(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9-_]+)", "", status.text)
                    reports.append(report.Report(status.author.screen_name,
                                                 "twitter",
                                                 text,
                                                 status.id,
                                                 status.created_at))
                self.save_last()
                return reports
        except tweepy.RateLimitError:
            logger.error("Twitter API Error: Rate Limit Exceeded", exc_info=True)
            self.waitcounter += 60*15 + 1
        except requests.exceptions.ConnectionError:
            logger.error("Twitter API Error: Bad Connection", exc_info=True)
            self.waitcounter += 10
        except tweepy.TweepError:
            logger.error("Twitter API Error: General Error", exc_info=True)
        return []

    def repost(self, status):
        """
        Retweets a given tweet.

        :param status: (report.Report object)
        :return: toot: string of the tweet, to toot on mastodon.
        """
        while 1:
            try:
                self.api.retweet(status.id)
                logger.info("Retweeted: " + status.format())
                if status.id > self.last_mention:
                    self.last_mention = status.id
                self.save_last()
                return status.format()
            except requests.exceptions.ConnectionError:
                logger.error("Twitter API Error: Bad Connection", exc_info=True)
                sleep(10)
            # maybe one day we get rid of this error:
            except tweepy.TweepError:
                logger.error("Twitter Error", exc_info=True)
                if status.id > self.last_mention:
                    self.last_mention = status.id
                self.save_last()
                return None

    def post(self, status):
        """
        Tweet a post.

        :param status: (report.Report object)
        """
        text = status.format()
        if len(text) > 280:
            text = status.text[:280 - 4] + u' ...'
        while 1:
            try:
                self.api.update_status(status=text)
                return
            except requests.exceptions.ConnectionError:
                logger.error("Twitter API Error: Bad Connection", exc_info=True)
                sleep(10)

    def flow(self, trigger, to_tweet=()):
        """ The flow of crawling mentions and retweeting them.

        :param to_tweet: list of strings to tweet
        :return list of retweeted tweets, to toot on mastodon
        """

        # Tweet the reports from other sources
        for post in to_tweet:
            self.post(post)

        # Store all mentions in a list of Status Objects
        mentions = self.crawl()

        # initialise list of strings for other bots
        all_tweets = []

        for status in mentions:
            # Is the Text of the Tweet in the triggerlist?
            if trigger.is_ok(status.text):
                # Retweet status
                toot = self.repost(status)
                if toot:
                    all_tweets.append(toot)

        # Return Retweets for posting on other bots
        return all_tweets


if __name__ == "__main__":
    # get the config dict of dicts
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    # set log file
    fh = logging.FileHandler(config['logging']['logpath'])
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    # initialise trigger
    trigger = trigger.Trigger(config)

    # initialise twitter bot
    bot = RetweetBot(config)

    try:
        while True:
            # :todo separate into small functions
            bot.flow(trigger)
            sleep(60)
    except KeyboardInterrupt:
        print("Good bye. Remember to restart the bot!")
    except:
        logger.error('Shutdown', exc_info=True)
        bot.save_last()
        try:
            mailer = sendmail.Mailer(config)
            mailer.send('', config['mail']['contact'],
                        'Ticketfrei Crash Report',
                        attachment=config['logging']['logpath'])
        except:
            logger.error('Mail sending failed', exc_info=True)
