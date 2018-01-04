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
        tb = traceback.extract_tb(sys.exc_info()[2])
        tbot.logger.log(tb)
        tbot.shutdown(tb)
