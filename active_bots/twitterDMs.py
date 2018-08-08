#!/usr/bin/env python3

import logging
import tweepy
import re
import requests
import report
from bot import Bot


logger = logging.getLogger(__name__)


class TwitterBot(Bot):
    def get_api(self, user):
        keys = user.get_api_keys()
        auth = tweepy.OAuthHandler(consumer_key=keys[0],
                                   consumer_secret=keys[1])
        auth.set_access_token(keys[2],  # access_token_key
                              keys[3])  # access_token_secret
        return tweepy.API(auth)

    def crawl(self, user):
        """
        crawls all Tweets which mention the bot from the twitter rest API.

        :return: reports: (list of report.Report objects)
        """
        reports = []
        try:
            api = self.get_api(user)
        except IndexError:
            return reports  # no twitter account for this user.
        last_dm = user.get_seen_dm()
        try:
            if last_dm == None:
                mentions = api.direct_messages()
            else:
                mentions = api.mentions_timeline(since_id=last_dm[0])
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
        except tweepy.TweepError:
            logger.error("Twitter API Error: General Error", exc_info=True)
        return []

    def post(self, user, report):
        pass
