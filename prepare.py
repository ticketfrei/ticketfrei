import logging
import pytoml as toml

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


