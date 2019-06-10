from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import create_engine
from sqlalchemy.schema import Table, Column, ForeignKey, UniqueConstraint
from sqlalchemy.types import Integer, String, DateTime, BLOB, REAL
#from sqlalchemy.orm import relationship, backref

# Get Base class where table objects inherit from
Base = declarative_base()
engine = create_engine("sqlite:///:memory:")


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    passhash = Column(String)
    enabled = Column(Integer, default=1)

    def __repr__(self):
        return '<User(id=%s, passhash=%s, enabled=%s)>' % (
            self.id, self.passhash, self.enabled)


class Email(Base):
    __tablename__ = 'email'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    email = Column(String)

    # necessary? https://docs.sqlalchemy.org/en/13/orm/tutorial.html#building-a-relationship
    # user = relationship(User, back_populates='email')

# necessary?
# User.email = relationship('email', order_by=Email.id, back_populates='user')

class TriggerPatterns(Base):
    __tablename__ = 'triggerpatterns'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    patterns = Column(String)

class BadWords(Base):
    __tablename__ = 'badwords'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    words = Column(String)

class MastodonInstances(Base):
    __tablename__ = 'mastodon_instances'
    id = Column(Integer, primary_key=True)
    instance = Column(String)
    client_id = Column(String)
    client_secret = Column(String)

class MastodonAccounts(Base):
    __tablename__ = 'mastodon_accounts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    access_token = Column(String)
    instance_id = Column(Integer, ForeignKey('mastodon_instances.id'))
    active = Column(Integer)  # could be default=1

class SeenToots(Base):
    __tablename__ = 'seen_toots'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    toot_uri = Column(String)

class SeenTelegrams(Base):
    __tablename__ = 'seen_telegrams'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    tg_id = Column(Integer)

class TwitterRequestTokens(Base):
    __tablename__ = 'twitter_request_tokens'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    request_token = Column(String)
    request_token_secret = Column(String)

class TwitterAccounts(Base):
    __tablename__ = 'twitter_accounts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    client_id = Column(String)
    client_secret = Column(String)
    active = Column(Integer)  # could be default=1

class TelegramAccounts(Base):
    __tablename__ = 'telegram_accounts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    apikey = Column(String)
    active = Column(Integer)  # could be default=1

class SeenTweets(Base):
    __tablename__ = 'seen_tweets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    tweet_id = Column(String)

class SeenDMs(Base):
    __tablename__ = 'seen_dms'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    twitter_accounts = Column(Integer, ForeignKey('twitter_accounts.id'))
    message_id = Column(String)

class TelegramSubscribers(Base):
    __tablename__ = 'telegram_subscribers'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    subscriber_id = Column(Integer)

    # how to get this to work?
    # https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#on-conflict-support-for-constraints
    # UniqueConstraint('id', 'subscriber_id', sqlite_on_conflict='IGNORE')

class Mailinglist(Base):
    __tablename__ = 'mailinglist'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    email = Column(String)

    # It would be good to have a Unique on conflict ignore here, just as in
    # telegram_subscribers.

class SeenMail(Base):
    __tablename__ = 'seen_mail'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    mail_date = Column(REAL) # could be Datetime, too

class TwitterLastRequest(Base):
    __tablename__ = 'twitter_last_request'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    date = Column(Integer)

class Cities(Base):
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    city = Column(String)
    markdown = Column(String)
    mail_md = Column(String)
    masto_link = Column(String)
    twit_link = Column(String)

    # how to get this to work?
    # https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#on-conflict-support-for-constraints
    # UniqueConstraint('id', 'city', sqlite_on_conflict='IGNORE')

class Secret(Base):
    __tablename__ = 'secret'
    id = Column(Integer, primary_key=True)
    secret = Column(BLOB)

Base.metadata.create_all(engine)

