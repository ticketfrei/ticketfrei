from config import config
import jwt
import logging
from os import urandom, system
from pylibscrypt import scrypt_mcf
import sqlite3


logger = logging.getLogger(__name__)


class DB(object):
    def __init__(self, dbfile):
        self.conn = sqlite3.connect(dbfile)
        self.cur = self.conn.cursor()
        self.create()
        self.secret = self.get_secret()

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
                patterns    TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS badwords (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                words       TEXT,
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
                toot_id            INTEGER,
                FOREIGN KEY(user_id) REFERENCES user(id),
                FOREIGN KEY(mastodon_accounts_id)
                    REFERENCES mastodon_accounts(id)
            );
            CREATE TABLE IF NOT EXISTS seen_telegrams (
                id                 INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id            INTEGER,
                tg_id              INTEGER,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS twitter_request_tokens (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                request_token   TEXT,
                request_token_secret TEXT,
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
            CREATE TABLE IF NOT EXISTS twitter_last_request (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                date        INTEGER,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS telegram_accounts (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                apikey      TEXT,
                active      INTEGER,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS seen_tweets (
                id         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id            INTEGER,
                twitter_accounts_id INTEGER,
                tweet_id    TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id)
                FOREIGN KEY(twitter_accounts_id)
                    REFERENCES twitter_accounts(id)
            );
            CREATE TABLE IF NOT EXISTS seen_dms (
                id         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id            INTEGER,
                twitter_accounts_id INTEGER,
                message_id    TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id)
                FOREIGN KEY(twitter_accounts_id)
                    REFERENCES twitter_accounts(id)
            );
            CREATE TABLE IF NOT EXISTS telegram_accounts (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                api_token   TEXT,
                active      INTEGER,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS telegram_subscribers (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                subscriber_id   INTEGER,
                FOREIGN KEY(user_id) REFERENCES user(id),
                UNIQUE(user_id, subscriber_id) ON CONFLICT IGNORE
            );
            CREATE TABLE IF NOT EXISTS mailinglist (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                email       TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS seen_mail (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                mail_date   REAL,
                FOREIGN KEY(user_id) REFERENCES user(id)
            );
            CREATE TABLE IF NOT EXISTS cities (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                user_id     INTEGER,
                city        TEXT,
                markdown    TEXT,
                mail_md     TEXT,
                masto_link  TEXT,
                twit_link   TEXT,
                FOREIGN KEY(user_id) REFERENCES user(id),
                UNIQUE(user_id, city) ON CONFLICT IGNORE
            );
            CREATE TABLE IF NOT EXISTS secret (
                id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                secret      BLOB
            );
        ''')

    def get_secret(self):
        """
        At __init__(), the db needs a secret. It tries to fetch it from the db,
        and if it fails, it generates a new one.

        :return:
        """
        # select only the newest secret. should be only one row anyway.
        self.execute("SELECT secret FROM secret ORDER BY id DESC LIMIT 1")
        try:
            return self.cur.fetchone()[0]
        except TypeError:
            new_secret = urandom(32)
            self.execute("INSERT INTO secret (secret) VALUES (?);",
                         (new_secret, ))
            self.commit()
            return new_secret

    def user_token(self, email, password):
        """
        This function is called by the register confirmation process. It wants
        to write an email to the email table and a passhash to the user table.

        :param email: a string with an E-Mail address.
        :param password: a string with a passhash.
        :return:
        """
        return jwt.encode({
            'email': email,
            'passhash': scrypt_mcf(
                password.encode('utf-8')
            ).decode('ascii')
        }, self.secret).decode('ascii')

    def mail_subscription_token(self, email, city):
        """
        This function is called by the mail subscription process. It wants
        to write an email to the mailinglist table.

        :param email: string
        :param city: string
        :return: a token with an encoded json dict { email: x, city: y }
        """
        token = jwt.encode({
            'email': email,
            'city': city
        }, self.secret).decode('ascii')
        return token

    def confirm_subscription(self, token):
        json = jwt.decode(token, self.secret)
        return json['email'], json['city']

    def confirm(self, token, city):
        from user import User
        try:
            json = jwt.decode(token, self.secret)
        except jwt.DecodeError:
            return None  # invalid token
        if 'passhash' in json.keys():
            # create user
            self.execute("INSERT INTO user (passhash) VALUES(?);",
                         (json['passhash'], ))
            uid = self.cur.lastrowid
            default_triggerpatterns = """kontroll?e
konti
db
vgn
vag
zivil
sicherheit
uniform
station
bus
bahn
tram
linie
nuernberg
nürnberg
s\d
u\d\d?"""
            self.execute("""INSERT INTO triggerpatterns (user_id, patterns)
                                VALUES(?, ?); """, (uid, default_triggerpatterns))
            self.execute("INSERT INTO badwords (user_id, words) VALUES(?, ?);",
                         (uid, "bastard"))
        else:
            uid = json['uid']
        with open("/etc/aliases", "a+") as f:
            f.write(city + ": " + config["mail"]["mbox_user"])
        self.execute("INSERT INTO email (user_id, email) VALUES(?, ?);",
                     (uid, json['email']))
        self.execute("""INSERT INTO telegram_accounts (user_id, apikey,
                        active) VALUES(?, ?, ?);""", (uid, "", 1))
        self.execute(
            "INSERT INTO seen_telegrams (user_id, tg_id) VALUES (?,?);", (uid, 0))
        self.execute(
            "INSERT INTO seen_mail (user_id, mail_date) VALUES (?,?);", (uid, 0))
        self.commit()
        user = User(uid)
        user.set_city(city)
        return user

    def by_email(self, email):
        from user import User
        self.execute("SELECT user_id FROM email WHERE email=?;", (email, ))
        try:
            uid, = self.cur.fetchone()
        except TypeError:
            return None
        return User(uid)

    def by_city(self, city):
        from user import User
        self.execute("SELECT user_id FROM cities WHERE city=?", (city, ))
        try:
            uid, = self.cur.fetchone()
        except TypeError:
            return None
        return User(uid)

    def user_facing_properties(self, city):
        self.execute("""SELECT city, markdown, mail_md, masto_link, twit_link
                            FROM cities
                            WHERE city=?;""", (city, ))
        try:
            city, markdown, mail_md, masto_link, twit_link = self.cur.fetchone()
            return dict(city=city,
                        markdown=markdown,
                        mail_md=mail_md,
                        masto_link=masto_link,
                        twit_link=twit_link,
                        mailinglist=city + "@" + config["web"]["host"])
        except TypeError:
            return None

    @property
    def active_users(self):
        from user import User
        self.execute("SELECT id FROM user WHERE enabled=1;")
        return [User(uid) for uid, in self.cur.fetchall()]


db = DB(config['database']['db_path'])
