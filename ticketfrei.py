#!/usr/bin/env python3

import logging
import pytoml as toml
import time
import sendmail

from retootbot import RetootBot
from retweetbot import RetweetBot
from mailbot import Mailbot
from trigger import Trigger

if __name__ == '__main__':
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('config.toml') as configfile:
        config = toml.load(configfile)

    # set log file
    logger = logging.getLogger()
    fh = logging.FileHandler(config['logging']['logpath'])
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    trigger = Trigger(config)

    bots = [RetootBot(config), RetweetBot(config), Mailbot(config)]

    try:
        statuses = []
        while True:
            for bot in bots:
                reports = bot.crawl()
                for status in reports:
                    if not trigger.is_ok(status.text):
                        continue
                    for bot2 in bots:
                        if bot == bot2:
                            bot2.repost(status)
                        else:
                            bot2.post(status)
            time.sleep(60)  # twitter rate limit >.<
    except KeyboardInterrupt:
        print("Good bye. Remember to restart the bot!")
    except:
        logger.error('Shutdown', exc_info=True)
        for bot in bots:
            bot.save_last()
        try:
            mailer = sendmail.Mailer(config)
            mailer.send('', config['mail']['contact'],
                        'Ticketfrei Crash Report',
                        attachment=config['logging']['logpath'])
        except:
            logger.error('Mail sending failed', exc_info=True)
