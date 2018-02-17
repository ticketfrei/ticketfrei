#!/usr/bin/env python3

import os
import base64
import bottle
import sqlite3
import sendmail
import pytoml as toml
import jwt
import pylibscrypt


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
    uname = bottle.request.forms.get('uname')
    psw = bottle.request.forms.get('psw')
    psw = psw.encode("utf-8")
    db.cur.execute("SELECT pass_hashed FROM user WHERE email=?;", (uname, ))
    try:
        pass_hashed = db.cur.fetchone()[0]
    except TypeError:
        return "Wrong Credentials."  # no user with this email
    if pylibscrypt.scrypt_mcf_check(pass_hashed, psw):
        bottle.response.set_cookie("account", uname, secret)
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

    # create confirmlink
    encoded_jwt = jwt.encode(payload, secret).decode('utf-8')
    host = bottle.request.get_header('host')
    confirmlink = "http://" + host + "/confirm/" + str(encoded_jwt)  # to be changed to https

    # send the mail
    m = sendmail.Mailer(config)
    m.send("Complete your registration here: " + confirmlink, email, "[Ticketfrei] Confirm your account")
    return "We sent you an E-Mail. Please click on the confirmation link."


@app.route('/confirm/<encoded_jwt>', method="GET")
def confirmaccount(encoded_jwt):
    """
    Confirm the account creation and create a database entry.
    :return: Redirection to bot.html
    """
    # get values from URL
    dict = jwt.decode(encoded_jwt, secret)
    uname = dict["email"]
    pass_hashed = base64.b64decode(dict["pass_hashed"])
    print(uname, pass_hashed)

    # create db entry
    db.cur.execute("INSERT INTO user(email, pass_hashed, enabled) VALUES(?, ?, ?);", (uname, pass_hashed, True))
    db.conn.commit()
    bottle.response.set_cookie("account", uname, secret)
    return bottle.redirect("/settings")


@app.route('/settings')
def manage_bot():
    """
    Restricted area. Deliver the bot settings page.
    :return:
    """
    uname = bottle.request.get_cookie("account", secret=secret)
    if uname is not None:
        return bottle.static_file("../static/bot.html", root='../static')
    else:
        bottle.abort(401, "Sorry, access denied.")


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
    secret = os.urandom(32)
    db = Datagetter()
    try:
        bottle.run(app=StripPathMiddleware(app), host='0.0.0.0', port=8080)
    finally:
        db.conn.close()
