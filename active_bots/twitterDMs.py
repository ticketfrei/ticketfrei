#!/usr/bin/env python3

import logging
import tweepy
import re
import requests
import report
from time import time
from bot import Bot


logger = logging.getLogger(__name__)


class TwitterDMListener(Bot):

    def get_api(self, user):
        keys = user.get_twitter_credentials()
        auth = tweepy.OAuthHandler(consumer_key=keys[0],
                                   consumer_secret=keys[1])
        auth.set_access_token(keys[2],  # access_token_key
                              keys[3])  # access_token_secret
        return tweepy.API(auth, wait_on_rate_limit=True)

    def crawl(self, user):
        """
        crawls all Tweets which mention the bot from the twitter rest API.

        :return: reports: (list of report.Report objects)
        """
        reports = []
        try:
            if user.get_last_twitter_request() + 60 > time():
                return reports
        except TypeError:
            user.set_last_twitter_request(time())
        try:
            api = self.get_api(user)
        except TypeError:
            return reports  # no twitter account for this user.
        last_dm = user.get_seen_dm()
        try:
            if last_dm is None:
                mentions = api.list_direct_messages()
                logger.error("list_direct_messages() returns:\n" + type(mentions) + "\n" + str(mentions) + "\n")
                logger.error("its first object is a " + type(mentions[0]) + ":\n" + str(mentions) + "\n")
            else:
                mentions = api.list_direct_messages()
                logger.error("list_direct_messages() returns:\n" + type(mentions) + "\n" + str(mentions) + "\n")
                logger.error("its first object is a " + type(mentions[0]) + ":\n" + str(mentions) + "\n")
            user.set_last_twitter_request(time())
            for status in mentions:
                text = re.sub(
                       "(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9-_]+)",
                       "", status.text)
                reports.append(report.Report(status.author.screen_name,
                                             "twitterDM",
                                             text,
                                             status.id,
                                             status.created_at))
            user.save_seen_dm(last_dm)
            return reports
        except tweepy.RateLimitError:
            logger.error("Twitter API Error: Rate Limit Exceeded",
                         exc_info=True)
            # :todo implement rate limiting
        except requests.exceptions.ConnectionError:
            logger.error("Twitter API Error: Bad Connection", exc_info=True)
        except tweepy.TweepError as terror:
            # Waiting for https://github.com/tweepy/tweepy/pull/1109 to get
            # merged, so direct messages work again
            if terror.api_code == 34:
                return reports
            logger.error("Twitter API Error: General Error", exc_info=True)
        return reports

    def post(self, user, report):
        pass
