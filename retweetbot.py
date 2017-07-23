#!/usr/bin/env python

import twitter
import os
import datetime
import requests
import pytoml as toml
import trigger
from time import sleep
import traceback


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
        """
        self.config = config
        keys = self.get_api_keys()
        self.api = twitter.Api(consumer_key=keys[0],
                               consumer_secret=keys[1],
                               access_token_key=keys[2],
                               access_token_secret=keys[3])
        self.historypath = historypath
        try:
            self.user_id = self.config['tapp']['shutdown_contact_userid']
            self.screen_name = \
                self.config['tapp']['shutdown_contact_screen_name']
        except KeyError:
            self.no_shutdown_contact = True
        self.last_mention = self.get_history(self.historypath)
        self.trigger = trigger
        if logpath:
            self.logpath = logpath
        else:
            self.logpath = os.path.join("logs", str(datetime.datetime.now()))
        print "Path of logfile: " + self.logpath

    def get_api_keys(self):
        """
        How to get these keys is described in doc/twitter_api.md

        After you received keys, store them in your ticketfrei.cfg like this:
        [tapp]
        consumer_key = "..."
        consumer_secret = "..."

        [tuser]
        access_token_key = "..."
        access_token_secret = "..."

        :return: keys: list of these 4 strings.
        """
        keys = []
        keys.append(self.config['tapp']['consumer_key'])
        keys.append(self.config['tapp']['consumer_secret'])
        keys.append(self.config['tuser']['access_token_key'])
        keys.append(self.config['tuser']['access_token_secret'])
        return keys

    def log(self, message, tb=False):
        """
        Writing an error message to a logfile in logs/ and prints it.

        :param message(string): Log message to be displayed
        :param tb: String of the Traceback
        """
        time = str(datetime.datetime.now())
        if tb:
            message = message + " The traceback is located at " + os.path.join("logs" + time)
            with open(os.path.join("logs", time), 'w+') as f:
                f.write(tb)
        line = "[" + time + "] "+ message + "\n"
        with open(self.logpath, 'a') as f:
            f.write(line)
        print line,

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

    def format_mastodon(self, status):
        """
        Bridge your Retweets to mastodon.
        :todo vmann: add all the mastodon API magic.

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
        while 1:
            try:
                mentions = self.api.GetMentions(since_id=self.last_mention)
                return mentions
            except twitter.TwitterError:
                self.log("Twitter API Error: Rate Limit Exceeded.")
                sleep(120)
            except requests.exceptions.ConnectionError:
                self.log("Twitter API Error: Bad Connection.")
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
                self.log("Retweeted: " + self.format_mastodon(status))
                if status.id > self.last_mention:
                    self.last_mention = status.id
                return self.format_mastodon(status)
            # maybe one day we get rid of this error. If not, try to uncomment
            # these lines.
            except twitter.error.TwitterError:
                self.log("Twitter API Error: You probably already retweeted this tweet: " + status.text)
                if status.id > self.last_mention:
                    self.last_mention = status.id
                return None
            except requests.exceptions.ConnectionError:
                self.log("Twitter API Error: Bad Connection.")
                sleep(10)

    def tweet(self, post):
        """
        Tweet a post.

        :param post: String with the text to tweet.
        """
        if len(post) > 140:
            post = post[:140 - 4] + u' ...'
        while 1:
            try:
                self.api.PostUpdate(status=post)
                return
            except requests.exceptions.ConnectionError:
                self.log("Twitter API Error: Bad Connection.")
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

    def shutdown(self):
        """ If something breaks, it shuts down the bot and messages the owner.
        """
        logmessage = "Shit went wrong, closing down."
        if self.screen_name:
            logmessage = logmessage + " Sending message to " + self.screen_name
        self.log(logmessage)
        if self.no_shutdown_contact:
            return
        self.save_last_mention()
        try:
            self.api.PostDirectMessage("Help! I broke down. restart me pls :$",
                                   self.user_id, self.screen_name)
        except:
            traceback.print_exc()
            print


if __name__ == "__main__":
    # create an Api object
    with open('ticketfrei.cfg') as configfile:
        config = toml.load(configfile)

    trigger = trigger.Trigger(config)

    bot = RetweetBot(trigger, config)
    try:
        while True:
            bot.flow()
            sleep(10)
    except:
        traceback.print_exc()
        print
        bot.shutdown()
