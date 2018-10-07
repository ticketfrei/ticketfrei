import pytoml as toml

# read config in TOML format (https://github.com/toml-lang/toml#toml)
with open('config.toml') as configfile:
    config = toml.load(configfile)
