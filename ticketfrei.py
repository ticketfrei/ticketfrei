#!/usr/bin/env python3

import pytoml as toml
import logger
import time
import sys

from retootbot import RetootBot
from retweetbot import RetweetBot
from trigger import Trigger


if __name__ == '__main__':
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    trigger = Trigger(config)

    logger = logger.Logger(config)

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
        message = logger.generate_tb(exc)
        tbot.logger.log(message)
        tbot.save_last_mention()
        tbot.logger.shutdown(message)
