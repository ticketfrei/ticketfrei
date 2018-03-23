#!/usr/bin/env python3

import logging
import pytoml as toml
import time
import sendmail

from retootbot import RetootBot
from retweetbot import RetweetBot
from mailbot import Mailbot
from trigger import Trigger

def get_logger(config):
    logpath = config['logging']['logpath']
    logger = logging.getLogger()
    fh = logging.FileHandler(logpath)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    return logger

def get_config():
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('config.toml') as configfile:
        config = toml.load(configfile)
    return config

def run():
    config = get_config()
    logger = get_logger(config)

    # set trigger
    trigger = Trigger(config)

    # initialize bots
    bots = []
    if config["muser"]["enabled"] != "false":
        bots.append(RetootBot(config))
    if config["tuser"]["enabled"] != "false":
        bots.append(RetweetBot(config))
    if config["mail"]["enabled"] != "false":
        bots.append(Mailbot(config))

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
        mailer = sendmail.Mailer(config)
        try:
            mailer.send('', config['mail']['contact'],
                        'Ticketfrei Crash Report',
                        attachment=config['logging']['logpath'])
        except:
            logger.error('Mail sending failed', exc_info=True)


if __name__ == '__main__':
    run()