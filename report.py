#!/usr/bin/env python3


class Report(object):
    """
    A ticketfrei report object.

    Toots, Tweets, and E-Mails can be formed into ticketfrei reports.

    """

    def __init__(self, author, source, text, id, timestamp):
        """
        Constructor of a ticketfrei report

        :param author: username of the author
        :param source: mastodon, twitter, or email bot object
        :param text: the text of the report
        :param id: id in the network
        :param timestamp: time of the report
        """
        self.author = author
        self.source = source
        self.text = text
        self.timestamp = timestamp
        self.id = id
