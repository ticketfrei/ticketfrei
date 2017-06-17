#!/usr/bin/env python
__encoding__ = "utf-8"


class Trigger(object):
    """
    This class provides a filter to test a string against.
    """
    def __init__(self, config, goodlistpath="goodlist", blacklistpath="blacklist"):
        self.config = config

        self.goodlistpath = goodlistpath
        with open(goodlistpath, "r+") as f:
            self.goodlist = [s.strip() for s in f.readlines()]
        for word in config["goodlist"]:
            self.goodlist.append(word)
        self.goodlist = self.strings_ok(self.goodlist)

        self.blacklistpath = blacklistpath
        with open(blacklistpath, "r+") as f:
            self.blacklist = [s.strip() for s in f.readlines()]
        for word in config["blacklist"]:
            self.blacklist.append(word)
        self.blacklist = self.strings_ok(self.blacklist)

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

    def update_list(self, word, whichlist):
        """

        :param word: a string of a word which should be appended to one of the lists
        :param boolean whichlist: 0 : goodlist, 1 : badlist.
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
    pass
