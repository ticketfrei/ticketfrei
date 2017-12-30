#!/usr/bin/env python3

import pytoml as toml
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
    with open('ticketfrei.cfg') as configfile:
        config = toml.load(configfile)

    trigger = Trigger(config)

    logpath = os.path.join("logs", str(datetime.datetime.now()))

    mbot = RetootBot(config, trigger, logpath=logpath)
    tbot = RetweetBot(trigger, config, logpath=logpath)

    try:
        statuses = []
        while True:
            statuses = mbot.retoot(statuses)
            statuses = tbot.flow(statuses)
            time.sleep(60)
    except KeyboardInterrupt:
        print("Good bye. Remember to restart the bot!")
    except:
        tbot.log(traceback.extract_tb(sys.exc_info()[2]))
        tbot.shutdown()
