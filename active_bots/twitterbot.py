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
            api = self.get_api(user)
        except Exception:
            #logger.error("Error Authenticating Twitter", exc_info=True)
            return reports
        last_mention = user.get_seen_tweet()
        try:
            if last_mention == 0:
                mentions = api.mentions_timeline()
            else:
                mentions = api.mentions_timeline(since_id=last_mention)
            for status in mentions:
                text = re.sub(
                        "(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9-_]+)",
                        "", status.text)
                reports.append(report.Report(status.author.screen_name,
                                             self,
                                             text,
                                             status.id,
                                             status.created_at))
            user.save_seen_tweet(last_mention)
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
        api = self.get_api(user)
        try:
            if report.source == self:
                api.retweet(report.id)
            else:
                text = report.text
                if len(text) > 280:
                    text = text[:280 - 4] + u' ...'
                api.update_status(status=text)
        except requests.exceptions.ConnectionError:
            logger.error("Twitter API Error: Bad Connection",
                         exc_info=True)
            # :todo implement rate limiting
