#!/usr/bin/env python


class Trigger(object):
    """
    This class provides a filter to test a string against.
    """
    def __init__(self, goodlistpath="goodlist", badlistpath="badlist"):
        self.goodlistpath = goodlistpath
        with open(goodlistpath, "r+") as f:
            self.goodlist = [s.strip() for s in f.readlines()]

        self.badlistpath = badlistpath
        with open(badlistpath, "r+") as f:
            self.badlist = [s.strip() for s in f.readlines()]

    def check_string(self, string):
        """
        checks if a string contains no bad words and at least 1 good word.

        :param string: A given string. Tweet or Toot, cleaned from html.
        :return: If the string passes the test
        """
        for triggerword in self.goodlist:
            if string.lower().find(triggerword):
                for triggerword in self.badlist:
                    if string.lower().find(triggerword):
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
            path = self.badlistpath
        with open(path, "w") as f:
            old = f.readlines()
            old.append(word)
            f.writelines(old)

if __name__ == "main":
    pass
