import pytoml as toml
import os

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(ROOT_DIR, 'template', '')
STATIC_DIR = os.path.join(ROOT_DIR, 'static', '')

def load_env():
    """
    load environment variables from the environment. If empty, use default
    values from config.toml.example.

    :return: config dictionary of dictionaries.
    """
    with open(os.path.join(ROOT_DIR, 'config.toml.example')) as defaultconf:
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

    try:
        if os.environ['LOG_FRONTEND'] != "":
            configdict['log']['log_frontend'] = os.environ['LOG_FRONTEND']
    except KeyError:
        pass

    try:
        if os.environ['LOG_BACKEND'] != "":
            configdict['log']['log_backend'] = os.environ['LOG_BACKEND']
    except KeyError:
        pass

    return configdict


# read config in TOML format (https://github.com/toml-lang/toml#toml)
try:
    with open(os.path.join(ROOT_DIR, 'config.toml')) as configfile:
        config = toml.load(configfile)
except FileNotFoundError:
    config = load_env()

if __name__ == "__main__":
    for category in config:
        for key in config[category]:
            print(key + "=" + str(config[category][key]))
