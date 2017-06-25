#!/usr/bin/env python
__encoding__ = "utf-8"

import os
import pytoml as toml

class Trigger(object):
    """
    This class provides a filter to test a string against.
    """
    def __init__(self, config):
        self.config = config


        self.goodlistpath = config['trigger']['goodlist_path']
        self.goodlist = self.get_lists(self.goodlistpath)
        self.goodlist = self.strings_ok(self.goodlist)

        self.blacklistpath = config['trigger']['blacklist_path']
        self.blacklist = self.get_lists(self.blacklistpath)
        self.blacklist = self.strings_ok(self.blacklist)

    def get_lists(self, path):
        """
        pass a folder with text files in it. each line in the files becomes a filter word.

        :param path: path to folder whose files shall be added to the set
        :return: set of trigger words.
        """
        trigger_words = set()
        for filename in os.listdir(path):
            with open(path + filename, "r+") as f:
                [trigger_words.add(s.strip()) for s in f.readlines()]
        return trigger_words

    def strings_ok(self, filterlist):
        """
        Checks if an empty line is in a list and removes it.
        :param filterlist: a good- or blacklist.
        :return: filterlist: a corrected list.
        """
        for word in filterlist:
            if word == "\n":
                del word
        return filterlist

    def check_string(self, string):
        """
        checks if a string contains no bad words and at least 1 good word.

        :param string: A given string. Tweet or Toot, cleaned from html.
        :return: If the string passes the test
        """
        string = unicode.decode(string)
        for triggerword in self.goodlist:
            if string.lower().find(triggerword) != -1:
                for triggerword in self.blacklist:
                    if string.lower().find(triggerword) != -1:
                        return False
                return True
        return False

    def add_to_list(self, word, whichlist):
        """

        :param word: a string of a word which should be appended to one of the lists
        :param boolean whichlist: 0 : goodlist, 1 : blacklist.
        """
        if whichlist:
            path = self.goodlistpath
        else:
            path = self.blacklistpath
        with open(path, "w") as f:
            old = f.readlines()
            old.append(word)
            f.writelines(old)

if __name__ == "__main__":
    with open("ticketfrei.cfg", "r") as configfile:
        config = toml.load(configfile)

    print "testing the trigger"
    trigger = Trigger(config)

    print "Printing words which trigger the bot:"
    for i in trigger.goodlist:
        print i
    print

    print "Printing words which block a bot:"
    for i in trigger.blacklist:
        print i
    print


