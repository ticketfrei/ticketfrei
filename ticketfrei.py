import pytoml as toml
import time

from retootbot import RetootBot
from retweetbot import RetweetBot


if __name__ == '__main__':
    # read config in TOML format (https://github.com/toml-lang/toml#toml)
    with open('ticketfrei.cfg') as configfile:
        config = toml.load(configfile)

    mbot = RetootBot(config)
    tbot = RetweetBot()

    try:
        statuses = []
        while True:
            statuses = mbot.retoot(statuses)
            statuses = tbot.flow(statuses)  # XXX not implemented in RetweetBot
            time.sleep(1)
    except:
        tbot.shutdown()
