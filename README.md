# Ticketfrei social bot

Version: 1.0

Ticketfrei is a mastodon/twitter/mail bot to dodge ticket controllers
in public transport systems.

The functionality is simple: it retweets every tweet where it is
mentioned.

This leads to a community which evolves around it; if you see ticket
controllers, you tweet their location and mention the bot. The bot
then retweets your tweet and others can read the info and think twice
if they want to buy a ticket. If enough people, a critical mass,
participate for the bot to become reliable, you have positive
self-reinforcing dynamics.

In the promotion folder, you will find some promotion material you
can use to build up such a community in your city. It is in german
though =/

Website: https://wiki.links-tech.org/IT/Ticketfrei

## Install

Setting up a ticketfrei bot for your city is quite easy. Here are the
few steps:

First you need to install python3 and virtualenv with your favourite
package manager.

Create and activate virtualenv:

```shell
sudo apt install python3 virtualenv uwsgi uwsgi-plugin-python nginx
virtualenv -p python3 .
. bin/activate
```

Install the dependencies:
```shell
pip install tweepy pytoml requests Mastodon.py bottle pyjwt 
```

Configure the bot:
```shell
cp config.toml.example config.toml
vim config.toml
```

You can use a Twitter, a Mastodon, and Mail with the account. They
will communicate with each other; if someone warns others via Mail,
Twitter and Mastodon users will also see the message. And vice versa.

You have to configure all of the accounts via config.toml; it should
be fairly intuitive to enter the right values.

## Maintaining

There is one security hole: people could start mentioning the bot
with useless information, turning it into a spammer. That's why it
has to be maintained; if someone spams the bot, mute them and undo
the retweet. So it won't retweet their future tweets and the useless
retweet is deleted if someone tries to check if something was
retweeted in the last hour or something.

To this date, we have never heard of this happening though.

### blacklisting

You also need to edit the goodlist and the blacklist. They are in the
"goodlists" and "blacklists" folders. All text files in those
directories will be used, so you should delete our templates; but
feel free to use them as an orientation.

Just add the words to the goodlist, which you want to require. A
report is only spread, if it contains at least one of them. If you
want to RT everything, just add a ```*```.

There is also a blacklist, which you can use to automatically sort
out malicious tweets. Be careful though, our filter can't read the
intention with which a word was used. Maybe you wanted it there.

### screen

To keep the bots running when you are logged out of the shell, you
can use screen:

```shell
sudo apt-get install screen 
echo "if [ -z "$STY" ]; then screen -RR; fi" >> ~/.bash_login
screen
python3 ticketfrei.py
```

To log out of the screen session, press "ctrl+a", and then "d".

### Manually creating the database

Unfortunately, if you want to help developing, you have to create the
database manually for now.

At the moment, we use a SQLITE3 database. If you are in the repo
directory, just open it with ```sqlitebrowser ticketfrei.sqlite```.
Then execute following SQL to create the tables:

```sql
CREATE TABLE `user` (
    `id`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    `email` TEXT,
    `pass_hashed`   TEXT,
    `enabled`   INTEGER
)
```
