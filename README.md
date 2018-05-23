# Ticketfrei micro messaging bot

Version: 1.0

<!-- This mastodon/twitter bot has one purpose - breaking the law. -->

The functionality is simple: It retweets every tweet where it is
mentioned.

This leads to a community which evolves around it. If you see ticket
controllers, tweet their location and mention the bot. The bot
then retweets your tweet and others can read the info and think twice
whether they want to buy a ticket or not. If enough people, a critical mass,
participate for the bot to become reliable, you have positive
self-reinforcing dynamics.

In the promotion folder, you'll find some promotion material you
can use to build up such a community in your city. It is in german
though =/
Feel free to translate it!

website: https://wiki.links-tech.org/IT/Ticketfrei

## install

Setting up a ticketfrei bot for your city is quite easy. Here are the
few steps:

First, you need to install python3 and virtualenv with your favorite
package manager.

Create and activate virtualenv:

```shell
sudo apt install python3 virtualenv
virtualenv -p python3 .
. bin/activate
```

Install the dependencies:
```shell
pip install tweepy pytoml requests Mastodon.py
```

Configure the bot:
```shell
cp config.toml.example config.toml
vim config.toml
```

You can use a Twitter, Mastodon, and Mail with the account. They
will communicate with each other: If someone warns others via Mail,
Twitter and Mastodon users will also see the message and vice versa.

You have to configure all of the accounts via config.toml. It should
be fairly intuitive to enter the right values.

## maintaining

There is one security hole: People could start mentioning the bot
with useless information, turning it into a spammer. That's why it
has to be maintained. If someone spams the bot, mute them and undo
the retweet. That way, it won't retweet their future tweets and the useless
retweet is deleted if someone tries to check if something was
retweeted in the last hour or something.

To this date, we have never heard of this happening though.

### blacklisting

You also need to edit the goodlist and blacklist. They are in the
"goodlists" and "blacklists" folders. All text files in those
directories will be used, so you should delete our templates. But
feel free to use them as an orientation.

Just add the words to the goodlist, which you want to require. A
report is only spread if it contains at least one of them. If you
want to RT everything, just add a ```*```.

There is also a blacklist, which you can use to automatically sort
out malicious messages. Be careful though, our filter can't read the
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

