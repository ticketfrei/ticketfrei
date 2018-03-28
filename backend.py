#!/usr/bin/env python3
from bot import Bot
import active_bots
from config import config
from db import db
import logging
import sendmail
import time


if __name__ == '__main__':
    logpath = config['logging']['logpath']
    logger = logging.getLogger()
    fh = logging.FileHandler(logpath)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    bots = []
    for ActiveBot in active_bots.__dict__.values():
        if isinstance(ActiveBot, type) and issubclass(ActiveBot, Bot):
            bots.append(ActiveBot())

    try:
        while True:
            for user in db.active_users:
                for bot in bots:
                    reports = bot.crawl(user)
                    for status in reports:
                        if not user.is_appropriate(status):
                            continue
                        for bot in bots:
                            bot.post(user, status)
            time.sleep(60)  # twitter rate limit >.<
    except:
        logger.error('Shutdown', exc_info=True)
        mailer = sendmail.Mailer(config)
        try:
            mailer.send('', config['web']['contact'],
                        'Ticketfrei Crash Report',
                        attachment=config['logging']['logpath'])
        except:
            logger.error('Mail sending failed', exc_info=True)
