import pytoml as toml
import os


def load_env():
    """
    load environment variables from the environment. If empty, use default
    values from config.toml.example.

    :return: config dictionary of dictionaries.
    """
    with open('config.toml.example') as defaultconf:
        configdict = toml.load(defaultconf)

    try:
        if os.environ['CONSUMER_KEY'] != "":
            configdict['twitter']['consumer_key'] = os.environ['CONSUMER_KEY']
    except KeyError:
        pass

    try:
        if os.environ['CONSUMER_SECRET'] != "":
            configdict['twitter']['consumer_secret'] = os.environ['CONSUMER_SECRET']
    except KeyError:
        pass

    try:
        if os.environ['HOST'] != "":
            configdict['web']['host'] = os.environ['HOST']
    except KeyError:
        pass

    try:
        if os.environ['PORT'] != "":
            configdict['web']['port'] = os.environ['PORT']
    except KeyError:
        pass

    try:
        if os.environ['CONTACT'] != "":
            configdict['web']['contact'] = os.environ['CONTACT']
    except KeyError:
        pass

    try:
        if os.environ['MBOX_USER'] != "":
            configdict['mail']['mbox_user'] = os.environ['MBOX_USER']
    except KeyError:
        pass

    try:
        if os.environ['DB_PATH'] != "":
            configdict['database']['db_path'] = os.environ['DB_PATH']
    except KeyError:
        pass

    return configdict


# read config in TOML format (https://github.com/toml-lang/toml#toml)
try:
    with open('config.toml') as configfile:
        config = toml.load(configfile)
except FileNotFoundError:
    config = load_env()

if __name__ == "__main__":
    for category in config:
        for key in config[category]:
            print(key + "=" + str(config[category][key]))
