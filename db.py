from config import config
import jwt
import logging
from os import urandom
from pylibscrypt import scrypt_mcf
import sqlite3
from user import User


logger = logging.getLogger(__name__)


class DB(object):
    def __init__(self, dbfile):
        self.conn = sqlite3.connect(dbfile)
        self.cur = self.conn.cursor()
        self.create()
        self.secret = urandom(32)

    def execute(self, *args, **kwargs):
        return self.cur.execute(*args, **kwargs)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def create(self):
        # init db
        self.cur.executescript('''
            CREATE TABLE IF NOT EXISTS user (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                passhash    TEXT,
                enabled     INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS email (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                email       TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS triggerpatterns (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                pattern     TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS badwords (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                word        TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS mastodon_instances (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                instance    TEXT,
                client_id   TEXT,
                client_secret   TEXT
            );
            CREATE TABLE IF NOT EXISTS mastodon_accounts (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                access_token    TEXT,
                instance_id INTEGER,
                active      INTEGER,
                FOREIGN KEY(user_id) REFERENCES user(id),
                FOREIGN KEY(instance_id) REFERENCES mastodon_instances(id)
            );
            CREATE TABLE IF NOT EXISTS seen_toots (
                id         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id            INTEGER,
                mastodon_accounts_id    INTEGER,
                toot_id            TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id),
                FOREIGN KEY(mastodon_accounts_id)
                    REFERENCES mastodon_accounts(id)
            );
            CREATE TABLE IF NOT EXISTS twitter_request_tokens (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                request_token   TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS twitter_accounts (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                client_id   TEXT,
                client_secret   TEXT,
                active      INTEGER,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS seen_tweets (
                id         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id            INTEGER,
                twitter_accounts_id INTEGER,
                tweet_id    TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS mailinglist (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                email       TEXT,
                active      INTEGER,
                FOREIGN KEY(user_id) REFERENCES user(id)
                FOREIGN KEY(twitter_accounts_id)
                    REFERENCES twitter_accounts(id)
            );
        ''')

    def user_token(self, email, password):
        return jwt.encode({
                'email': email,
                'passhash': scrypt_mcf(
                        password.encode('utf-8')
                    ).decode('ascii')
            }, self.secret).decode('ascii')

    def confirm(self, token):
        try:
            json = jwt.decode(token, self.secret)
        except jwt.DecodeError:
            return None  # invalid token
        if 'passhash' in json.keys():
            # create user
            self.execute("INSERT INTO user (passhash) VALUES(?, ?);",
                         (json['passhash'], ))
            uid = self.cur.lastrowid
        else:
            uid = json['uid']
        self.execute("INSERT INTO email (user_id, email) VALUES(?, ?);",
                     (uid, json['email']))
        self.commit()
        return User(uid)

    def by_email(self, email):
        self.execute("SELECT user_id FROM email WHERE email=?;", (email, ))
        try:
            uid, = self.cur.fetchone()
        except TypeError:
            return None
        return User(uid)

    @property
    def active_users(self):
        self.execute("SELECT id FROM user WHERE enabled=1;")
        return [User(uid) for uid, in self.cur.fetchall()]


db = DB(config['database']['db_path'])
