#!/usr/bin/env python3

import bottle
import sqlite3

class Datagetter(object):
    def __init__(self):
        self.db = "../../../ticketfrei.sqlite"
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
    if psw == db.cur.execute("SELECT pass FROM user WHERE email=?;", (uname, )):
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
    uname = bottle.request.forms.get('email')
    psw = bottle.request.forms.get('psw')
    pswrepeat = bottle.request.forms.get('psw-repeat')
    if pswrepeat != psw:
        return "ERROR: Passwords don't match. Try again."

    # :todo send confirmation Mail with encoded email+passphrase to email
    return "We Sent you an E-Mail. Please click on the confirmation link."

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
    global db
    db = Datagetter()
    bottle.run(app=StripPathMiddleware(app), host='0.0.0.0', port=8080)