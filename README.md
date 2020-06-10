# Ticketfrei social bot

Ticketfrei is a mastodon/twitter/mail bot to dodge ticket controllers in public
transport systems.

## Mission

Public transportation is meant to provide an easy and time-saving way to move
within a region while being affordable for everybody. Unfortunately, this is
not yet the case. Ticketfrei's approach is to **enable people to reclaim public
transportation.**

On short term we want to do this by helping users to avoid controllers and
fines - on long term by **pressuring public transportation companies to offer
their services free of charge**, financed by the public.

Because with Ticketfrei you're able to use trains and subways for free anyway.
Take part and create a new understanding of what public transportation could
look like!

## How It Works

The functionality is simple: It retweets every tweet where it is mentioned.

This leads to a community which evolves around it. If you see ticket
controllers, tweet their location and mention the bot. The bot then retweets
your tweet and others can read the info and think twice whether they want to
buy a ticket or not. If enough people, a critical mass, participate for the bot
to become reliable, you have positive self-reinforcing dynamics.

Today, you can use a Twitter, Mastodon, Telegram, and Mail with the account.
They will communicate with each other; if someone warns others via Mail,
Telegram, Twitter and Mastodon users will also see the message. And vice versa.

In version 2, this repository contains a web application. On this website,
people can register an own bot for their city - the website manages multiple
bots for multiple citys. This way, you do not have to host it yourself.

In the promotion folder, you'll find some promotion material you can use to
build up such a community in your city. Unfortunately it is in german - but
it's editable, feel free to translate it!

Website (our flagship instance): https://ticketfrei.links-tech.org

More information: https://wiki.links-tech.org/IT/Ticketfrei

## Do you want Ticketfrei in your city?

Just go to https://ticketfrei.links-tech.org or another website where this software is
running.

* Register on the ticketfrei site
* Optionally: register bots:
  * Register a Twitter account
  * Register a Mastodon account
  * Register a Telegram bot
* Configure account
* The hard part: do the promotion! You need a community.

### Maintaining

There is one security hole: People could start mentioning the bot with useless
information, turning it into a spammer. That's why it has to be maintained. If
someone spams the bot, mute them and undo the retweet. That way, it won't
retweet their future tweets and the useless retweet is deleted if someone tries
to check if something was retweeted in the last hour or something.

To this date, we have never heard of this happening though.

### Blocklisting

You also need to edit the goodlist and the blocklist. You can do this on the
website, in the settings of your bot.

Just add the words to the goodlist, which you want to require. A report is only
spread if it contains at least one of them. If you want to RT everything, just
add a ```*```.

There is also a blocklist, which you can use to automatically sort out
malicious messages. Be careful though, our filter can't read the intention with
which a word was used. Maybe you wanted it there.

## Do you want to offer a Ticketfrei website to others?

If you want to offer this website to others, feel free to do so. If you have questions, just open 
a GitHub issue or write to tech@lists.links-tech.org, we are happy to help and share best practices.

We wrote these installation notes, so you can set up the website easily:

### Install from the git repository

This guide assumes you are on a Debian 9 Server:

```shell
sudo apt install python3 virtualenv uwsgi uwsgi-plugin-python3 nginx git exim4
cd /srv
sudo git clone https://github.com/b3yond/ticketfrei
cd ticketfrei
```

Install the necessary packages, create and activate virtualenv:

```shell
virtualenv -p python3 .
. bin/activate
```

Install the dependencies:

```shell
pip install tweepy pytoml Mastodon.py bottle pyjwt pylibscrypt Markdown twx gitpython
```

Configure the bot:

```shell
cp config.toml.example config.toml
vim config.toml
```

This configuration is only for the admin. Moderators can log into
twitter/mastodon/mail and configure their personal bot on the settings page.

Set up LetsEncrypt:

```shell
sudo apt-get install python-certbot-nginx -t stretch-backports
sudo certbot --authenticator webroot --installer nginx --agree-tos --redirect --hsts 
```

Configure exim4 for using mbox files.

```
sudo dpkg-reconfigure exim4-config
# Choose the following values:
# internet site; mail is sent and received directly using SMTP
# your domain name
# 
# your domain name
# 
# 
# No
# mbox format in /var/mail/
# No
```

Deploy ticketfrei with uwsgi:

```shell
echo "Enter your domain name into the following prompt:" && read DOMAIN

# configure nginx
sudo sed -r "s/example.org/$DOMAIN/g" deployment/example.org.conf > /etc/nginx/sites-enabled/$DOMAIN.conf

# create folder for database
sudo mkdir /var/ticketfrei
sudo chown www-data:www-data -R /var/ticketfrei

# create folder for socket
sudo mkdir /var/run/ticketfrei
sudo chown -R www-data:www-data /var/run/ticketfrei
sudo -s
echo "mkdir /var/run/ticketfrei" >> /etc/rc.local
echo "chown -R www-data:www-data /var/run/ticketfrei" >> /etc/rc.local
echo "service ticketfrei-web restart" >> /etc/rc.local
exit

# change /etc/aliases permissions to be able to receive reports per mail
sudo chown root:www-data /etc/aliases
sudo chmod 664 /etc/aliases

# create folder for logs
sudo mkdir /var/log/ticketfrei
sudo chown www-data:www-data -R /var/log/ticketfrei

# start up nginx
sudo service nginx restart

# create and start the frontend systemd service
sudo cp deployment/ticketfrei-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start ticketfrei-web.service

# create and start the backend systemd service
sudo cp deployment/ticketfrei-backend.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl start ticketfrei-backend.service
```

### Backup

For automated backups, you need to backup these files:

* `/var/ticketfrei/db.sqlite`
* `/srv/ticketfrei/config.toml`
* `/etc/aliases`

You can find an example how to do this with borgbackup in the deployment
folder. Adjust it to your needs.

### Logs

There are several logfiles which you can look at:

```
# for the uwsgi deployment:
less /var/log/ticketfrei/uwsgi.log

# for the backend:
less /var/log/ticketfrei/backend.log

# for the systemd service:
less /var/log/syslog

# for the nginx web server:
less /var/log/nginx/example.org_error.log

# for the mail server
less /var/log/exim4/mainlog
```

### Development Install

If you want to install it locally to develop on it, note that twitter and mail
will probably not work. You should test them on a server instead.

```shell
sudo apt install python3 virtualenv uwsgi uwsgi-plugin-python3 nginx git
sudo git clone https://github.com/b3yond/ticketfrei
cd ticketfrei
git checkout multi-deployment
```

Install the necessary packages, create and activate virtualenv:

```shell
virtualenv -p python3 .
. bin/activate
```

Install the dependencies:

```shell
pip install tweepy pytoml Mastodon.py bottle pyjwt pylibscrypt Markdown twx
```

Configure the bot:

```shell
cp config.toml.example config.toml
vim config.toml
```

This configuration is only for the admin. Users can log into
twitter/mastodon/mail and configure their personal bot on the settings page.

```shell
# create folder for socket & database
sudo mkdir /var/ticketfrei
sudo chown $USER:$USER -R /var/ticketfrei

# create folder for logs
sudo mkdir /var/log/ticketfrei
sudo chown $USER:$USER -R /var/log/ticketfrei

# start Ticketfrei
./frontend.py & ./backend.py &
```

# Project History

## Version 1

- more of less hacked together during a mate-fueled weekend
- backend-only, twitter & mastodon
- just a script, which crawled & retweeted tweets, if they match a whitelist & blocklist
- whitelist & blocklist were just 2 files

## Version 2

Reasons for the rewrite:
- user management: Users should be able to run a Ticketfrei bot in their city
  - without needing a server, without needing command line skills
- more networks; not only Twitter & Mastodon, also Email & Telegram

2 processes: backend & frontend.  
The two Processes talk via a database.
The two Processes have separate log files.
Both processes take some config values from config.toml.

### Backend

The Backend takes care of crawling & spreading the reports.

backend.py:
- main loop which does the crawling & posting. 
- loops through all cities in the database
  - per city it tries all of the networks/bots:
    - per network/bot it runs the crawl()-function to ask the social network for new reports
    - then it checks whether the report is appropriate
    - if yes, it posts the report via all networks/bots, which belong to the city.

config.py: imports config values
- Imports values from config.toml
- If there is no config file it tries to use environment variables,
- Apart from that it uses the default values.

bot.py: bot parent Class
- just the absolute minimum what a bot needs to be able to do: crawl + post
- is never instantiated, only inherited from

report.py: report Class
- defines how reports are supposed to look like

active_bots/mailbot.py as an example for how a network/bot works
- crawl():
  - mails arrive at an mbox file through exim4
  - the bot checks whether they are new
  - the bot generates a report object from the mail and returns it to the backend.py-loop
- post():
  - asks the database for the list of mails which want to receive reports for this city
  - sends the report.text to those mail addresses


### Frontend

the architecture of the frontend is loosely oriented off [Model View
Controller](https://blog.codinghorror.com/understanding-model-view-controller/).

user.py (Model)
- high-level interface to talk to the database
- database calls; almost all values in the database are specific to a city/user
- user.py is also a Class for frontend web authentication
- user.py keeps the user-id, through which the frontend tracks authentication

db.py (Model)
- DB-Layout; creates the database if it doesn't exist yet.
- holds some database calls which are not city-specific.

frontend.py (Controller): bottle web application
- handles POST/GET requests
- talks to the database through user.py
- everyone can look at the pages, and register
- but only authenticated users can login and change settings

session.py: User Authentication
- takes care of session cookies and "403 unauthenticated" error messages

sendmail.py: helper script to send mails
- sends all mails the frontend, backend, and bots need to send

static/
- css, images, javascript for the login form etc.

template/ (view)
- base for the HTML generation, uses the bottle-template-framework
- wrapper.tpl is the base template for every other template


### active_bots: how to implement a new network

If you want to write a new bot, e.g. a Wire-Bot, you have to take these steps:

- look for a python-library which can talk to Wire
- the city/users have to provide authentication details; this needs a form in
  the settings
  - depending on the network either a password, a token, or an implementation
    of the OAuth login flow
- the backend needs to crawl messages from the network, & post reports to the
  network

Files you need to change:

1. active_bots/wire.py - crawl & post functions
2. settings.tpl - form to authenticate to the network & possible network specific settings.
3. frontend.py - routes for the forms you added to settings.tpl
4. db.py - database layout, to store the account credentials/tokens, and to save which message you have last seen
5. user.py - database calls to get or set values

