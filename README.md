# Ticketfrei social bot

Version: 2.0beta

Ticketfrei is a mastodon/twitter/mail bot to dodge ticket controllers in public
transport systems.

The functionality is simple: it retweets every tweet where it is mentioned.

This leads to a community which evolves around it; if you see ticket
controllers, you tweet their location and mention the bot. The bot then
retweets your tweet and others can read the info and think twice if they want
to buy a ticket. If enough people, a critical mass, participate for the bot to
become reliable, you have positive self-reinforcing dynamics.

Today, you can use a Twitter, a Mastodon, and Mail with the account. They will
communicate with each other; if someone warns others via Mail, Twitter and
Mastodon users will also see the message. And vice versa.

In version 2, this bot has received a frontend website. On this website, people
can register an own bot for their city - the website manages multiple bots for
multiple citys. This way, you do not have to host it yourself.

In the promotion folder, you will find some (german) promotion material you can
use to build up such a community in your city.

Website: ticketfrei.links-tech.org

More information: https://wiki.links-tech.org/IT/Ticketfrei

## Do you want Ticketfrei in your city?

Just got to ticketfrei.links-tech.org or another website where this software is
running.

* Register a twitter account
* Register a Mastodon account
* Register on the ticketfrei site
* Configure account
* The hard part: do the promotion! You need a community.

### Maintaining

There is one security hole: people could start mentioning the bot with useless
information, turning it into a spammer. That's why it has to be maintained; if
someone spams the bot, mute them and undo the retweet. So it won't retweet
their future tweets and the useless retweet is deleted if someone tries to
check if something was retweeted in the last hour or something.

To this date, we have never heard of this happening though.

### blacklisting

You also need to edit the goodlist and the blacklist. You can do this on the
website, in the settings of your bot.

Just add the words to the goodlist, which you want to require. A report is only
spread, if it contains at least one of them. If you want to RT everything, just
add a ```*```.

There is also a blacklist, which you can use to automatically sort out
malicious tweets. Be careful though, our filter can't read the intention with
which a word was used. Maybe you wanted it there.

## Do you want to offer a Ticketfrei website to others?

If you want to offer this website to others, feel free to do so. If you have questions, just open 
a GitHub issue or write to tech@lists.links-tech.org, we are happy to help and share best practices.

We wrote these installation notes, so you can set up the website easily:

### Install

To Do:

```shell
sudo apt install python3 virtualenv uwsgi uwsgi-plugin-python nginx 
```

* set up nginx
* set up LetsEncrypt https://certbot.eff.org/
* set up mariadb
* set up uwsgi

Install the necessary packages, create and activate virtualenv:

```shell
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

This configuration is only for the admin. Users can log into
twitter/mastodon/mail and configure their personal bot on the settings page.

