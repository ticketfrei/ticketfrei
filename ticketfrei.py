#!/usr/bin/env python3

import pytoml as toml
import logger
import time
import traceback
import os
import sys
import datetime

from retootbot import RetootBot
from retweetbot import RetweetBot
from trigger import Trigger


if __name__ == '__main__':
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    trigger = Trigger(config)

    logpath = os.path.join("logs", str(datetime.datetime.now()))
    logger = logger.Logger(logpath)

    mbot = RetootBot(config, trigger, logger)
    tbot = RetweetBot(trigger, config, logger)

    try:
        statuses = []
        while True:
            statuses = mbot.retoot(statuses)
            statuses = tbot.flow(statuses)
            time.sleep(60)
    except KeyboardInterrupt:
        print("Good bye. Remember to restart the bot!")
    except:
        exc = sys.exc_info()  # returns tuple [Exception type, Exception object, Traceback object]
        tb = traceback.extract_tb(exc[2])  # returns StackSummary object
        tb = "\n".join(tb.format())  # string of the actual traceback
        message = ("Traceback (most recent call last):\n",
                   tb,
                   exc[0].__name__)  # the type of the Exception
        message = "".join(message)  # concatenate to full traceback message
        tbot.logger.log(message)
        tbot.shutdown(message)
