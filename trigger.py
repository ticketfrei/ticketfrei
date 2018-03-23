#!/usr/bin/env python
import os
import re

class Trigger(object):
    """
    This class provides a filter to test a string against.
    """
    def __init__(self, config):
        self.config = config

        try:
            goodlistpath = config['trigger']['goodlist_path']
        except KeyError:
            goodlistpath = 'goodlists'

        # load goodlists
        self.goodlist = []
        for filename in os.listdir(goodlistpath):
            with open(os.path.join(goodlistpath, filename), "r+") as listfile:
                for pattern in listfile:
                    pattern = pattern.strip()
                    if pattern:
                        self.goodlist.append(re.compile(pattern, re.IGNORECASE))

        try:
            blacklistpath = config['trigger']['blacklist_path']
        except KeyError:
            blacklistpath = 'blacklists'

        # load blacklists
        self.blacklist = set()
        for filename in os.listdir(blacklistpath):
            with open(os.path.join(blacklistpath, filename), "r+") as listfile:
                for word in listfile:
                    word = word.strip()
                    if word:
                        self.blacklist.add(word)

    def is_ok(self, message):
        """
        checks if a string contains no bad words and at least 1 good word.

        :param message: A given string. Tweet or Toot, cleaned from html.
        :return: If the string passes the test
        """
        for pattern in self.goodlist:
            if pattern.search(message) is not None:
                break
        else:
            # no pattern matched
            return False
        for word in message.lower().split():
            if word in self.blacklist:
                return False
        return True


if __name__ == "__main__":
    import backend
    config = backend.get_config()

    print("testing the trigger")
    trigger = Trigger(config)

    print("Printing words which trigger the bot:")
    for i in trigger.goodlist:
        print(i)
    print()

    print("Printing words which block a bot:")
    for i in trigger.blacklist:
        print(i)
