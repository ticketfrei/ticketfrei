#!/usr/bin/env python
import re
from user import User


class Trigger(object):
    """
    This class provides a filter to test a string against.
    """
    def __init__(self, config, uid, db):
        self.config = config
        self.db = db
        self.user = User(db, uid)

        # load goodlists
        self.goodlist = []
        raw = self.user.get_trigger_words("trigger_good")
        print(raw)
        print(type(raw))
        for pattern in raw:
            pattern = pattern.strip()
            if pattern:
                self.goodlist.append(re.compile(pattern, re.IGNORECASE))

        # load blacklists
        self.blacklist = set()
        raw = self.user.get_trigger_words("trigger_bad")
        for word in raw:
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

"""
if __name__ == "__main__":
    import prepare
    config = prepare.get_config()

    print("testing the trigger")
    trigger = Trigger(config)

    print("Printing words which trigger the bot:")
    for i in trigger.goodlist:
        print(i)
    print()

    print("Printing words which block a bot:")
    for i in trigger.blacklist:
        print(i)
"""