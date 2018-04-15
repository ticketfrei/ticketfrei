#!/usr/bin/env python3
from bot import Bot
import active_bots
from config import config
from db import db
import logging
from sendmail import sendmail
import time


def shutdown():
    try:
        sendmail(config['web']['contact'], 'Ticketfrei Shutdown')
    except Exception:
        logger.error('Could not inform admin.', exc_info=True)
    exit(1)


if __name__ == '__main__':
    logger = logging.getLogger()
    fh = logging.FileHandler('/var/log/ticketfrei/backend.log')
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
                        for bot2 in bots:
                            bot2.post(user, status)
            time.sleep(60)  # twitter rate limit >.<
    except Exception:
        logger.error('Shutdown.', exc_info=True)
        shutdown()
