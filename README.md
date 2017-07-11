# Ticketfrei micro messaging bot

<!-- This mastodon/twitter bot has one purpose - breaking the law. -->

The functionality is simple: it retweets every tweet where it is mentioned.

This leads to a community which evolves around it; if you see ticket controllers, you tweet their location and mention the bot. The bot then retweets your tweet and others can read the info and think twice if they want to buy a ticket. If enough people, a critical mass, participate for the bot to become reliable, you have positive self-reinforcing dynamics.

There is one security hole: people could start mentioning the bot with useless information, turning it into a spammer. That's why it has to be maintained; if someone spams the bot, mute them and undo the retweet. So it won't retweet their future tweets and the useless retweet is deleted if someone tries to check if something was retweeted in the last hour or something.


# Install

Install python3 with your favourite package manager.
Create and activate virtualenv
```shell
$ virtualenv -p python3 .
$ . bin/activate
```
Install dependencies
```shell
$ pip3 install Mastodon.py pytoml
$ pip install python-twitter pytoml requests
```
Configure
```shell
$ cp ticketfrei.cfg.example ticketfrei.cfg
$ vim ticketfrei.cfg
```
Edit the account credentials, so your bot can use your accounts.

Also add the words to the goodlist, which you want to require. A tweet is only retweeted, if it contains at least one of them. If you want to RT everything, just add your account name.

There is also a blacklist, which you can use to automatically sort out malicious tweets. Be careful though, our filter can't read the intention with which a word was used. Maybe you wanted it there.

Note that atm the good- & blacklist are still outside of ticketfrei.cfg, in separate files. we will repare this soon.

## ideas

* You can only use the twitter API if you have confirmed a phone number and sacrificed a penguin in a blood ritual. So we should build it in a way that it uses the twitter web GUI. It's difficult, but maybe it works. We had another twitter bot that worked similarly, years ago: https://github.com/b3yond/twitter-bot
* Make it for mastodon instead of twitter. Mastodon has an open API, that's way more fun. Also mastodon may profit from the network effects though it may be hard to reach the critical mass if you can only use mastodon users. 
* Bridge to mastodon, so people can use both platforms. Easier to reach the critical mass. But could be hard to do without the twitter API.
* Build a tool that deletes wrong toots/tweets on both platforms, would work nicely with a web UI.
* write the muted people to the db, to easily undo the mutes if necessary.

## to do
Desktop/pycharm-community-2017.1.4/bin/pycharm.sh
- [x] Twitter: Crawl mentions
- [x] Mastodon: Crawl mentions
- [ ] Write toots/tweets to database/log
- [x] Twitter: retweet people
- [x] Mastodon: boost people
<!--
- [ ] Mastodon: toot who has been retweeted on twitter
- [ ] Twitter: tweet who has been boosted on mastodon
-->
- [x] Twitter: access the API
- [ ] Web UI that lets you easily delete toots/tweets per db id and mute the tweet author
- [x] Write Bots as Classes to be easier implemented
- [x] Create extra Class for the filter
- [ ] Put as much as possible into ticketfrei.cfg
- [ ] Make both bots run on their own *and* next to each other
  - [ ] implement trigger class in retootbot
  - [ ] read config in retweetbot
- [ ] put shutdown contact in ticketfrei.cfg
