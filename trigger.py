#!/usr/bin/env python
import os
import pytoml as toml


class Trigger(object):
    """
    This class provides a filter to test a string against.
    """
    def __init__(self, config):
        self.config = config

        try:
            self.goodlistpath = config['trigger']['goodlist_path']
        except KeyError:
            self.goodlistpath = 'goodlists'
        self.goodlist = self.get_lists(self.goodlistpath)

        try:
            self.blacklistpath = config['trigger']['blacklist_path']
        except KeyError:
            self.blacklistpath = 'blacklists'
        self.blacklist = self.get_lists(self.blacklistpath)

    def get_lists(self, path):
        """
        pass a folder with text files in it. each line in the files becomes a
        filter word.

        :param path: path to folder whose files shall be added to the set
        :return: set of trigger words.
        """
        trigger_words = set()
        for filename in os.listdir(path):
            with open(os.path.join(path, filename), "r+") as listfile:
                for word in listfile:
                    word = word.strip()
                    if word:
                        trigger_words.add(word)
        return trigger_words

    def is_ok(self, message):
        """
        checks if a string contains no bad words and at least 1 good word.

        :param message: A given string. Tweet or Toot, cleaned from html.
        :return: If the string passes the test
        """
        ret = False
        for word in message.lower().split():
            if word in self.goodlist:
                ret = True
            if word in self.blacklist:
                return False
        return ret


if __name__ == "__main__":
    with open("ticketfrei.cfg", "r") as configfile:
        config = toml.load(configfile)

    print("testing the trigger")
    trigger = Trigger(config)

    print("Printing words which trigger the bot:")
    for i in trigger.goodlist:
        print(i)
    print()

    print("Printing words which block a bot:")
    for i in trigger.blacklist:
        print(i)
