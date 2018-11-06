import pytoml as toml
import os

def load_env():
    """
    load environment variables from the environment. If empty, use default
    values from config.toml.example.

    :return: config dictionary of dictionaries.
    """
    with open('config.toml.example') as defaultconf:
        config = toml.load(configfile)

    try:
        config['twitter']['consumer_key'] = os.environ['CONSUMER_KEY']
    except KeyError:
        pass

    try:
        config['twitter']['consumer_secret'] = os.environ['CONSUMER_SECRET']
    except KeyError:
        pass

    try:
        config['web']['host'] = os.environ['HOST']
    except KeyError:
        pass

    try:
        config['web']['port'] = os.environ['PORT']
    except KeyError:
        pass

    try:
        config['web']['contact'] = os.environ['CONTACT']
    except KeyError:
        pass

    try:
        config['mail']['mbox_user'] = os.environ['MBOX_USER']
    except KeyError:
        pass

    try:
        config['database']['db_path'] = os.environ['DB_PATH']
    except KeyError:
        pass

    return config


# read config in TOML format (https://github.com/toml-lang/toml#toml)
try:
    with open('config.toml') as configfile:
        config = toml.load(configfile)
except FileNotFoundError:
    config = load_env()
