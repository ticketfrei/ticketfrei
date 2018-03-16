#!/usr/bin/env python3

import os
import base64
import bottle
import sqlite3
import sendmail
import pytoml as toml
import jwt
import pylibscrypt
import smtplib
# from bottle_auth import AuthPlugin


class Datagetter(object):
    def __init__(self):
        self.db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ticketfrei.sqlite")
        self.conn = self.create_connection(self.db)
        self.cur = self.conn.cursor()

    def create_connection(self, db_file):
        """ create a database connection to the SQLite database
            specified by the db_file
        :param db_file: database file
        :return: Connection object or None
        """
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except sqlite3.Error as e:
            print(e)
        return None


app = application = bottle.Bottle()


@app.route('/login', method="POST")
def login():
    """
    Login to the ticketfrei account with credentials from the user table.

    :return: bot.py Session Cookie
    """
    email = bottle.request.forms.get('uname')
    psw = bottle.request.forms.get('psw')
    psw = psw.encode("utf-8")
    db.cur.execute("SELECT pass_hashed FROM user WHERE email=?;", (email, ))
    try:
        pass_hashed = db.cur.fetchone()[0]
    except TypeError:
        return "Wrong Credentials."  # no user with this email
    if pylibscrypt.scrypt_mcf_check(pass_hashed, psw):
        bottle.response.set_cookie("account", email, secret)
        return bottle.redirect("/settings")
    else:
        return "Wrong Credentials."  # passphrase is wrong


@app.route('/register', method="POST")
def register():
    """
    Login to the ticketfrei account with credentials from the user table.

    :return: bot.py Session Cookie
    """
    email = bottle.request.forms.get('email')
    psw = bottle.request.forms.get('psw')
    pswrepeat = bottle.request.forms.get('psw-repeat')
    if pswrepeat != psw:
        return "ERROR: Passwords don't match. Try again."

    # check if email is already in use
    db.cur.execute("SELECT id FROM user WHERE email=?;", (email,))
    if db.cur.fetchone() is not None:
        return "E-Mail is already in use."  # account already exists

    # hash and format for being encoded in the confirmation mail
    psw = psw.encode("utf-8")
    pass_hashed = pylibscrypt.scrypt_mcf(psw)  # hash password
    pass_hashed = base64.encodebytes(pass_hashed)
    pass_hashed = pass_hashed.decode("ascii")
    payload = {"email": email, "pass_hashed": pass_hashed}

    # create confirm_link
    encoded_jwt = jwt.encode(payload, secret).decode('utf-8')
    confirm_link = "http://" + bottle.request.get_header('host') + "/confirm/" + str(encoded_jwt)  # :todo http -> https

    # send the mail
    m = sendmail.Mailer(config)
    try:
        m.send("Complete your registration here: " + confirm_link, email, "[Ticketfrei] Confirm your account")
    except smtplib.SMTPRecipientsRefused:
        return "Please enter a valid E-Mail address."
    return "We sent you an E-Mail. Please click on the confirmation link."


@app.route('/confirm/<encoded_jwt>', method="GET")
def confirm_account(encoded_jwt):
    """
    Confirm the account creation and create a database entry.
    :return: Redirection to bot.html
    """
    # get values from URL
    payload = jwt.decode(encoded_jwt, secret)
    email = payload["email"]
    pass_hashed = base64.b64decode(payload["pass_hashed"])

    # create db entry
    db.cur.execute("INSERT INTO user(email, pass_hashed, enabled) VALUES(?, ?, ?);", (email, pass_hashed, 1))
    # insert default good- & blacklist into db
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "goodlists", "nbg_goodlist"),
              "r") as f:
        default_goodlist = f.read()
    db.cur.execute("INSERT INTO trigger_good(user_id, words) VALUES(?, ?);", (get_user_id(email), default_goodlist))
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blacklists", "nbg_blacklist"),
              "r") as f:
        default_blacklist = f.read()
    print(default_goodlist)  # debug
    print(default_blacklist)  # debug
    db.cur.execute("INSERT INTO trigger_bad(user_id, words) VALUES(?, ?);", (get_user_id(email), default_blacklist))
    db.conn.commit()
    bottle.response.set_cookie("account", email, secret, path="/")
    return bottle.redirect("/settings")


@app.route('/settings')
def manage_bot():
    """
    Restricted area. Deliver the bot settings page.
    Deliver user settings with Cookies.
    :return: If it returns something, it just refreshes the page.
    """
    email = bottle.request.get_cookie("account", secret=secret)
    print(email)  # debug
    if email is not None:
        user_id = get_user_id(email)
        # get Enable Status from db
        db.cur.execute("SELECT enabled FROM user WHERE email = ?;", (email,))
        enabled = db.cur.fetchone()[0]
        # Set Enable Status with a Cookie
        resp = bottle.static_file("../static/bot.html", root='../static')
        if enabled:
            resp.set_cookie("enabled", "True")
        else:
            resp.set_cookie("enabled", "False")

        # Get goodlist from db
        db.cur.execute("SELECT words FROM trigger_good WHERE user_id=?;", (user_id,))
        words = db.cur.fetchone()[0]
        # Deliver goodlist with a Cookie
        print("setting goodlist cookies?")
        resp.set_cookie("goodlist", words, path="/settings")
        print(words)  # debug

        # Get blacklist from db
        db.cur.execute("SELECT words FROM trigger_bad WHERE user_id=?;", (user_id,))
        words = db.cur.fetchone()[0]
        # Deliver badlist with a Cookie
        print("setting blacklist cookies?")
        resp.set_cookie("blacklist", words, path="/settings")
        print(words)  # debug

        return resp
    else:
        bottle.abort(401, "Wrong username or passphrase. Try again!")


def get_user_id(email):
    # get user_id from email
    db.cur.execute("SELECT id FROM user WHERE email = ?", (email, ))
    return db.cur.fetchone()[0]


@app.route('/settings/goodlist', method="POST")
def update_goodlist():
    """
    Writes the goodlist textarea on /settings to the database.
    This function expects a multi-line string, transmitted over the textarea form.
    :return: redirect to settings page
    """
    # get new goodlist
    words = bottle.request.forms.get("goodlist")
    user_id = get_user_id(bottle.request.get_cookie("account", secret=secret))
    # write new goodlist to db
    db.cur.execute("UPDATE trigger_good SET words = ? WHERE user_id = ?;", (words, user_id, ))
    db.conn.commit()
    return bottle.redirect("/settings")


@app.route('/settings/blacklist', method="POST")
def update_blacklist():
    """
    Writes the blacklist textarea on /settings to the database.
    This function expects a multi-line string, transmitted over the textarea form.
    :return: redirect to settings page
    """
    # get new blacklist
    words = bottle.request.forms.get("blacklist")
    # get user_id
    user_id = get_user_id(bottle.request.get_cookie("account", secret=secret))
    # write new goodlist to db
    db.cur.execute("UPDATE trigger_bad SET words = ? WHERE user_id = ?;", (words, user_id, ))
    db.conn.commit()
    return bottle.redirect("/settings")


@app.route('/enable', method="POST")
def enable():
    """
    Enable the bot. Called by the Enable button in bot.html
    :return: redirect to settings page
    """
    email = bottle.request.get_cookie("account", secret=secret)
    db.cur.execute("UPDATE user SET enabled = 1 WHERE email=?;", (email,))
    db.conn.commit()
    bottle.response.set_cookie("enabled", "True")
    return bottle.redirect("/settings")


@app.route('/disable', method="POST")
def disable():
    """
    Disable the bot. Called by the Disable button in bot.html
    :return: redirect to settings page
    """
    email = bottle.request.get_cookie("account", secret=secret)
    db.cur.execute("UPDATE user SET enabled = 0 WHERE email=?;", (email,))
    db.conn.commit()
    bottle.response.set_cookie("enabled", "False")
    return bottle.redirect("/settings")


@app.route('/login/twitter', method="POST")
def login_twitter():
    """
    Starts the twitter OAuth authentication process.
    :return: redirect to twitter.
    """
    # twitter.redirect("no environ", "no cookie monster")
    return "logging in with twitter is not implemented yet."


@app.route('/login/twitter/callback', method="POST")
def twitter_callback():
    """
    Gets the callback
    :return:
    """
    return "logging in with twitter is not implemented yet."


@app.route('/login/mastodon', method="POST")
def login_mastodon():
    """
    Starts the mastodon OAuth authentication process.
    :return: redirect to twitter.
    """
    # instance_url = bottle.request.forms.get('instance_url')
    return "logging in with mastodon is not implemented yet."


@app.route('/static/<filename:path>')
def static(filename):
    """
    Serve static files
    """
    if filename == "bot.html":
        bottle.abort(401, "Sorry, access denied.")
    return bottle.static_file(filename, root='../static')


@app.route('/')
def show_index():
    """
    The front "index" page
    :return: /static/index.html
    """
    return bottle.static_file("../static/index.html", root='../static')


class StripPathMiddleware(object):
    """
    Get that slash out of the request
    """
    def __init__(self, a):
        self.a = a

    def __call__(self, e, h):
        e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
        return self.a(e, h)


if __name__ == "__main__":
    global config
    with open('../config.toml') as configfile:
        config = toml.load(configfile)

    global db
    global secret
    global twitter

    secret = os.urandom(32)
    db = Datagetter()
    host = '0.0.0.0'

    # from bottle_auth.social import twitter as twitterplugin
    # callback_url = host + '/login/twitter/callback'
    # twitter = twitterplugin.Twitter(config['tapp']['consumer_key'], config['tapp']['consumer_secret'], callback_url)
    # bottle.install(AuthPlugin(twitter))

    try:
        bottle.run(app=StripPathMiddleware(app), host=host, port=8080)
    finally:
        db.conn.close()
