#!/usr/bin/env python3

import logging
import pytoml as toml
import time
import sendmail

from retootbot import RetootBot
from retweetbot import RetweetBot
from trigger import Trigger


if __name__ == '__main__':
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    logger = logging.getLogger()
    fh = logging.FileHandler(config['logging']['logpath'])
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    trigger = Trigger(config)
    mbot = RetootBot(config, trigger)
    tbot = RetweetBot(trigger, config)

    try:
        statuses = []
        while True:
            statuses = mbot.retoot(statuses)
            statuses = tbot.flow(statuses)
            time.sleep(60)
    except KeyboardInterrupt:
        print("Good bye. Remember to restart the bot!")
    except:
        logger.error('Shutdown', exc_info=True)
        tbot.save_last_mention()
        try:
            mailer = sendmail.Mailer(config)
            mailer.send('', config['mail']['contact'],
                        'Ticketfrei Crash Report',
                        attachment=config['logging']['logpath'])
        except:
            logger.error('Mail sending failed', exc_info=True)
