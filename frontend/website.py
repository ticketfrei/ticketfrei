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
        self.db = "../ticketfrei.sqlite"
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
    db.cur.execute("SELECT pass_hashed FROM user WHERE email=?;", (uname, )), psw
    pass_hashed = db.cur.fetchone()
    print(pass_hashed)
    if pylibscrypt.scrypt_mcf_check(pass_hashed, psw):
        # :todo Generate Session Cookie and give to user
        return bottle.static_file("../static/bot.html", root="../static")
    else:
        return "Wrong Credentials."


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

    # needs to be encoded somehow
    psw = psw.encode("utf-8")
    psw = pylibscrypt.scrypt_mcf(psw)
    psw = base64.encodebytes(psw)
    psw = psw.decode("ascii")
    payload = {"email": email, "psw_hashed": psw}  # hash password
    encoded_jwt = jwt.encode(payload, secret)
    confirmlink = "ticketfrei.links-tech.org/confirm?" + str(encoded_jwt)
    print(type(confirmlink))
    m = sendmail.Mailer(config)
    m.send("Complete your registration here: " + confirmlink, email, "[Ticketfrei] Confirm your account")
    return "We sent you an E-Mail. Please click on the confirmation link."


# How can I parse the arguments from the URI?
# https://ticketfrei.links-tech.org/confirm?user=asdf&pass=sup3rs3cur3
@app.route('/confirm', method="GET")
def confirmaccount():
    """
    Confirm the account creation and create a database entry.
    :return: Redirection to bot.html
    """
    encoded_jwt = bottle.request.forms.get('encoded_jwt')
    dict = jwt.decode(encoded_jwt, secret)
    uname = dict["email"]
    pass_hashed = dict["psw_hashed"]
    print(uname, pass_hashed)
    db.cur.execute("INSERT INTO user(email, pass_hashed, enabled) VALUES(?, ?, ?);", (uname, pass_hashed, True))
    db.conn.commit()
    return bottle.static_file("../static/bot.html", root='../static')


@app.route('/static/<filename:path>')
def static(filename):
    """
    Serve static files
    """
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
