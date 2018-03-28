from config import config
from bottle import response
from db import db
import jwt
from mastodon import Mastodon
from pylibscrypt import scrypt_mcf, scrypt_mcf_check


class User(object):
    def __init__(self, uid):
        # set cookie
        response.set_cookie('uid', uid, secret=db.secret, path='/')
        self.uid = uid

    def check_password(self, password):
        db.execute("SELECT passhash FROM user WHERE id=?;", (self.uid, ))
        passhash, = db.cur.fetchone()
        return scrypt_mcf_check(passhash.encode('ascii'),
                                password.encode('utf-8'))

    def password(self, password):
        passhash = scrypt_mcf(password.encode('utf-8')).decode('ascii')
        db.execute("UPDATE user SET passhash=? WHERE id=?;",
                   (passhash, self.uid))
        db.commit()
    password = property(None, password)  # setter only, can't read back

    @property
    def enabled(self):
        db.execute("SELECT enabled FROM user WHERE user_id=?;", (self.uid, ))
        return bool(db.cur.fetchone()[0])

    @enabled.setter
    def enabled(self, enabled):
        db.execute("UPDATE user SET enabled=? WHERE id=?",
                   (1 if enabled else 0, self.uid))
        db.commit()

    @property
    def emails(self):
        db.execute("SELECT email FROM email WHERE user_id=?;", (self.uid, ))
        return (*db.cur.fetchall(), )

    def delete_email(self, email):
        db.execute("SELECT COUNT(*) FROM email WHERE user_id=?", (self.uid, ))
        if db.cur.fetchone()[0] == 1:
            return False  # don't allow to delete last email
        db.execute("DELETE FROM email WHERE user_id=? AND email=?;",
                   (self.uid, email))
        db.commit()
        return True

    def email_token(self, email):
        return jwt.encode({
                'email': email,
                'uid': self.uid
            }, db.secret).decode('ascii')

    def is_appropriate(self, report):
        db.execute("SELECT pattern FROM triggerpatterns WHERE user_id=?;",
                   (self.uid, ))
        for pattern, in db.cur.fetchall():
            if pattern.search(report.text) is not None:
                break
        else:
            # no pattern matched
            return False
        db.execute("SELECT word FROM badwords WHERE user_id=?;",
                   (self.uid, ))
        badwords = [word.lower() for word, in db.cur.fetchall()]
        for word in report.text.lower().split():
            if word in badwords:
                return False
        return True

    def get_masto_credentials(self):
        db.execute("SELECT access_token, instance_id FROM mastodon_accounts WHERE user_id = ? AND active = 1;",
                   (self.uid, ))
        row = db.cur.fetchone()
        db.execute("SELECT instance, client_id, client_secret FROM mastodon_instances WHERE id = ?;",
                   (row[1], ))
        instance = db.cur.fetchone()
        return instance[1], instance[2], row[0], instance[0]

    def get_twitter_credentials(self):
        keys = [config['twitter']['consumer_key'],
                config['twitter']['consumer_secret']]
        row = self.get_twitter_token()
        keys.append(row[0])
        keys.append(row[1])
        return keys

    def get_seen_toot(self):
        db.execute("SELECT toot_id FROM seen_toots WHERE user_id = ?;",
                   (self.uid, ))
        return db.cur.fetchone()[0]

    def save_seen_toot(self, toot_id):
        db.execute("UPDATE seen_toots SET toot_id = ? WHERE user_id = ?;",
                   (toot_id, self.uid))

    def get_seen_tweet(self):
        db.execute("SELECT tweet_id FROM seen_tweets WHERE user_id = ?;",
                   (self.uid, ))
        return db.cur.fetchone()[0]

    def save_seen_tweet(self, tweet_id):
        db.execute("UPDATE seen_tweets SET tweet_id = ? WHERE user_id = ?;",
                   (tweet_id, self.uid))

    def get_mail(self):
        db.execute("SELECT email FROM mail WHERE user_id = ?;", (self.uid, ))

    def get_seen_mail(self):
        db.execute("SELECT mail_date FROM seen_mails WHERE user_id = ?;", (self.uid, ))
        return db.cur.fetchone()[0]

    def save_seen_mail(self, mail_date):
        db.execute("UPDATE seen_mail SET mail_date = ? WHERE user_id = ?;",
                   (mail_date, self.uid))

    def get_trigger_words(self, table):
        db.execute("SELECT words FROM ? WHERE user_id = ?;", (table, self.uid,))
        return db.cur.fetchone()[0]

    def state(self):
        return dict(foo='bar')

    def save_request_token(self, token):
        db.execute("INSERT INTO twitter_request_tokens(user_id, request_token) VALUES(?, ?);",
                   (self.uid, token))
        db.commit()

    def get_request_token(self):
        db.execute("SELECT request_token FROM twitter_request_tokens WHERE user_id = ?;", (id,))
        request_token = db.cur.fetchone()[0]
        db.execute("DELETE FROM twitter_request_tokens WHERE user_id = ?;", (id,))
        db.commit()
        return request_token

    def save_twitter_token(self, access_token, access_token_secret):
        db.execute(
            "INSERT INTO twitter_accounts(user_id, access_token_key, access_token_secret) VALUES(?, ?, ?);",
            (id, access_token, access_token_secret))
        db.commit()

    def get_twitter_token(self):
        db.execute("SELECT access_token, access_token_secret FROM twitter_accouts WHERE user_id = ?;",
                   (self.uid, ))
        return db.cur.fetchall()

    def get_mastodon_app_keys(self, instance):
        db.execute("SELECT client_id, client_secret FROM mastodon_instances WHERE instance = ?;", (instance, ))
        try:
            row = db.cur.fetchone()
            client_id = row[0]
            client_secret = row[1]
            return client_id, client_secret
        except TypeError:
            app_name = "ticketfrei" + str(db.secret)[0:4]
            client_id, client_secret = Mastodon.create_app(app_name, api_base_url=instance)
            db.execute("INSERT INTO mastodon_instances(instance, client_id, client_secret) VALUES(?, ?, ?);",
                       (instance, client_id, client_secret))
            db.commit()
            return client_id, client_secret

    def save_masto_token(self, access_token, instance):
        db.execute("SELECT id FROM mastodon_instances WHERE instance = ?;", (instance, ))
        instance_id = db.cur.fetchone()[0]
        db.execute("INSERT INTO mastodon_accounts(user_id, access_token, instance_id, active) "
                   "VALUES(?, ?, ?, ?);", (self.uid, access_token, instance_id, 1))
        db.commit()
