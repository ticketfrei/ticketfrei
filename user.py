from bottle import response
from mastodon import Mastodon


class User(object):
    def __init__(self, db, uid):
        # set cookie
        response.set_cookie('uid', uid, secret=db.secret, path='/')
        self.db = db
        self.uid = uid

    def get_masto_credentials(self):
        self.db.cur.execute("SELECT access_token, instance_id FROM mastodon_accounts WHERE user_id = ? AND active = 1;",
                            (self.uid, ))
        row = self.db.cur.fetchone()
        self.db.cur.execute("SELECT instance, client_id, client_secret FROM mastodon_instances WHERE id = ?;",
                            (row[1], ))
        instance = self.db.cur.fetchone()
        return instance[1], instance[2], row[0], instance[0]

    def get_seen_toot(self):
        self.db.cur.execute("SELECT toot_id FROM seen_toots WHERE user_id = ?;",
                            (self.uid, ))
        return self.db.cur.fetchone()[0]

    def save_seen_toot(self, toot_id):
        self.db.cur.execute("UPDATE seen_toots SET toot_id = ? WHERE user_id = ?;",
                            (toot_id, self.uid))

    def get_seen_tweet(self):
        self.db.cur.execute("SELECT tweet_id FROM seen_tweets WHERE user_id = ?;",
                            (self.uid, ))
        return self.db.cur.fetchone()[0]

    def save_seen_tweet(self, tweet_id):
        self.db.cur.execute("UPDATE seen_tweets SET tweet_id = ? WHERE user_id = ?;",
                            (tweet_id, self.uid))

    def get_mail(self):
        self.db.cur.execute("SELECT email FROM mail WHERE user_id = ?;", (self.uid, ))

    def get_seen_mail(self):
        self.db.cur.execute("SELECT mail_date FROM seen_mails WHERE user_id = ?;", (self.uid, ))
        return self.db.cur.fetchone()[0]

    def save_seen_mail(self, mail_date):
        self.db.cur.execute("UPDATE seen_mail SET mail_date = ? WHERE user_id = ?;",
                            (mail_date, self.uid))

    def get_trigger_words(self, table):
        self.db.cur.execute("SELECT words FROM ? WHERE user_id = ?;", (table, self.uid,))
        return self.db.cur.fetchone()[0]

    def state(self):
        return dict(foo='bar')

    def save_request_token(self, token):
        self.db.cur.execute("INSERT INTO twitter_request_tokens(user_id, request_token) VALUES(?, ?);",
                            (self.uid, token))
        self.db.conn.commit()

    def get_request_token(self):
        self.db.cur.execute("SELECT request_token FROM twitter_request_tokens WHERE user_id = ?;", (id,))
        request_token = self.db.cur.fetchone()[0]
        self.db.cur.execute("DELETE FROM twitter_request_tokens WHERE user_id = ?;", (id,))
        self.db.conn.commit()
        return request_token

    def save_twitter_token(self, access_token, access_token_secret):
        self.db.cur.execute(
            "INSERT INTO twitter_accounts(user_id, access_token_key, access_token_secret) VALUES(?, ?, ?);",
            (id, access_token, access_token_secret))
        self.db.conn.commit()

    def get_twitter_token(self):
        self.db.cur.execute("SELECT access_token, access_token_secret FROM twitter_accouts WHERE user_id = ?;",
                            (self.uid, ))
        return self.db.cur.fetchall()

    def get_mastodon_app_keys(self, instance):
        self.db.cur.execute("SELECT client_id, client_secret FROM mastodon_instances WHERE instance = ?;", (instance, ))
        try:
            row = self.db.cur.fetchone()
            client_id = row[0]
            client_secret = row[1]
            return client_id, client_secret
        except TypeError:
            app_name = "ticketfrei" + str(self.db.secret)[0:4]
            client_id, client_secret = Mastodon.create_app(app_name, api_base_url=instance)
            self.db.cur.execute("INSERT INTO mastodon_instances(instance, client_id, client_secret) VALUES(?, ?, ?);",
                                (instance, client_id, client_secret))
            self.db.conn.commit()
            return client_id, client_secret

    def save_masto_token(self, access_token, instance):
        self.db.cur.execute("SELECT id FROM mastodon_instances WHERE instance = ?;", (instance, ))
        instance_id = self.db.cur.fetchone()[0]
        self.db.cur.execute("INSERT INTO mastodon_accounts(user_id, access_token, instance_id, active) "
                            "VALUES(?, ?, ?, ?);", (self.uid, access_token, instance_id, 1))
        self.db.conn.commit()
