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
        db.execute("SELECT enabled FROM user WHERE id=?;", (self.uid, ))
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
        patterns = db.cur.fetchone()
        for pattern in patterns.splitlines():
            if pattern.search(report.text) is not None:
                break
        else:
            # no pattern matched
            return False
        default_badwords = """
bastard
bitch
whore
hitler
slut
hure
jude
schwuchtel
fag
faggot
nigger
neger
schlitz           
        """
        db.execute("SELECT word FROM badwords WHERE user_id=?;",
                   (self.uid, ))
        badwords = db.cur.fetchone()
        for word in report.text.lower().splitlines():
            if word in badwords:
                return False
        for word in default_badwords.splitlines():
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

    def get_seen_dm(self):
        db.execute("SELECT message_id FROM seen_dms WHERE user_id = ?;",
                   (self.uid, ))
        return db.cur.fetchone()

    def save_seen_dm(self, tweet_id):
        db.execute("UPDATE seen_dms SET message_id = ? WHERE user_id = ?;",
                   (tweet_id, self.uid))

    def get_mailinglist(self):
        db.execute("SELECT email FROM mailinglist WHERE user_id = ? AND active = 1;", (self.uid, ))
        return db.cur.fetchone()[0]

    def get_seen_mail(self):
        db.execute("SELECT mail_date FROM seen_mails WHERE user_id = ?;", (self.uid, ))
        return db.cur.fetchone()[0]

    def save_seen_mail(self, mail_date):
        db.execute("UPDATE seen_mail SET mail_date = ? WHERE user_id = ?;",
                   (mail_date, self.uid))

    def set_trigger_words(self, patterns):
        db.execute("UPDATE triggerpatterns SET patterns = ? WHERE user_id = ?;",
                   (patterns, self.uid))

    def get_trigger_words(self):
        db.execute("SELECT patterns FROM triggerpatterns WHERE user_id = ?;",
                   (self.uid,))
        return db.cur.fetchone()[0]

    def set_badwords(self, words):
        db.execute("UPDATE badwords SET words = ? WHERE user_id = ?;",
                   (words, self.uid))

    def get_badwords(self):
        db.execute("SELECT words FROM badwords WHERE user_id = ?;",
                   (self.uid,))
        return db.cur.fetchone()[0]

    def state(self):
        # necessary:
        # - city
        # - markdown
        # - goodlist
        # - blacklist
        # - logged in with twitter?
        # - logged in with mastodon?
        # - enabled?
        citydict = db.user_facing_properties(self.get_city())
        return dict(city=citydict['city'],
                    markdown=citydict['markdown'],
                    triggerwords=self.get_trigger_words(),
                    badwords=self.get_badwords(),
                    enabled=self.enabled)

    def save_request_token(self, token):
        db.execute("INSERT INTO twitter_request_tokens(user_id, request_token, request_token_secret) VALUES(?, ?, ?);",
                   (self.uid, token["oauth_token"], token["oauth_token_secret"]))
        db.commit()

    def get_request_token(self):
        db.execute("SELECT request_token, request_token_secret FROM twitter_request_tokens WHERE user_id = ?;", (self.uid,))
        request_token = db.cur.fetchone()
        db.execute("DELETE FROM twitter_request_tokens WHERE user_id = ?;", (self.uid,))
        db.commit()
        return {"oauth_token" : request_token[0],
                "oauth_token_secret" : request_token[1]}

    def save_twitter_token(self, access_token, access_token_secret):
        db.execute(
            "INSERT INTO twitter_accounts(user_id, client_id, client_secret) VALUES(?, ?, ?);",
            (self.uid, access_token, access_token_secret))
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

    def get_city(self):
        db.execute("SELECT city FROM cities WHERE user_id == ?;", (self.uid, ))
        return db.cur.fetchone()[0]

    def set_city(self, city):
        masto_link = "example.mastodon.social/@" + city # get masto_link
        twit_link = "example.twitter.com/" + city # get twit_link
        mailinglist = city + "@" + config['web']['host']
        markdown = """
# Wie funktioniert Ticketfrei?

Willst du mithelfen, Ticketkontrolleure zu überwachen?
Willst du einen Fahrscheinfreien ÖPNV erkämpfen?

## Ist es gerade sicher, schwarz zu fahren?

Schau einfach auf das Profil unseres Bots: """ + twit_link + """

Hat jemand vor kurzem etwas über Kontrolleur*innen gepostet?
* Wenn ja, dann kauf dir vllt lieber ein Ticket. In Nürnberg 
 haben wir die Erfahrung gemacht, dass Kontis normalerweile 
 ungefähr ne Woche aktiv sind, ein paar Stunden am Tag. Wenn es 
 also in den letzten Stunden einen Bericht gab, pass lieber 
 auf.
* Wenn nicht, ist es wahrscheinlich kein Problem :)

Wir können natürlich nicht garantieren, dass es sicher ist, 
also pass trotzdem auf, wer auf dem Bahnsteig steht.
Aber je mehr Leute mitmachen, desto eher kannst du dir sicher 
sein, dass wir sie finden, bevor sie uns finden.

Also, wenn du weniger Glück hast, und der erste bist, der einen 
Kontrolleur sieht:

## Was mache ich, wenn ich Kontis sehe?

Ganz einfach, du schreibst es den anderen. Das geht entweder

<!-- * mit Mastodon: """ + masto_link + """ -->
<!-- * über Twitter: """ + twit_link + """ -->
* Oder per Mail an """ + mailinglist + """, wenn ihr kein
  Social Media benutzen wollt.

Schreibe einfach einen Toot oder einen Tweet, der den Bot 
mentioned, und gib an
* Wo du die Kontis gesehen hast
* Welche Linie sie benutzen und in welche Richtung sie fahren.

Zum Beispiel so:

[[https://github.com/b3yond/ticketfrei/blob/master/guides/tooting_screenshot.png|Screenshot of writing a toot]]

[[https://github.com/b3yond/ticketfrei/blob/master/guides/toot_screenshot.png|A toot ready to be boosted]]

Der Bot wird die Nachricht dann weiterverbreiten, auch zu den 
anderen Netzwerken.
Dann können andere Leute das lesen und sicher vor Kontis sein.

Danke, dass du mithilfst, öffentlichen Verkehr für alle 
sicherzustellen!

## Kann ich darauf vertrauen, was random stranger from the 
Internet mir da erzählen?

Aber natürlich! Wir haben Katzenbilder!

[[https://lorempixel.com/550/300/cats|Katzenbilder...]]

Glaubt besser nicht, wenn jemand postet, dass die Luft da und 
da gerade rein ist.
Das ist vielleicht sogar gut gemeint - aber klar könnte die 
VAG sich hinsetzen und einfach lauter Falschmeldungen posten.

Aber Falschmeldungen darüber, dass gerade Kontis i-wo unterwegs 
sind?
Das macht keinen Sinn. 
Im schlimmsten Fall kauft jmd mal eine Fahrkarte mehr - aber 
kann sonst immer schwarz fahren.

Also ja - es macht Sinn, uns zu vertrauen, wenn wir sagen, wo 
gerade Kontis sind.

## Was ist Mastodon und warum sollte ich es benutzen?

Mastodon ist ein dezentrales soziales Netzwerk - so wie 
Twitter, nur ohne Monopol und Zentralismus.
Ihr könnt Kurznachrichten (Toots) über alles mögliche 
schreiben, und euch mit anderen austauschen.

Mastodon ist Open Source, Privatsphäre-freundlich und relativ 
sicher vor Zensur.

Um Mastodon zu benutzen, besucht diese Seite: 
https://joinmastodon.org/
        """
        db.execute("""INSERT INTO cities(user_id, city, markdown, masto_link, 
                        twit_link) VALUES(?,?,?,?,?)""",
                   (self.uid, city, markdown, masto_link, twit_link))
        db.commit()
