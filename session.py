from bottle import redirect, request, abort, response
from db import db
from functools import wraps
from inspect import Signature
from user import User


class SessionPlugin(object):
    name = 'SessionPlugin'
    keyword = 'user'
    api = 2

    def __init__(self, loginpage):
        self.loginpage = loginpage

    def apply(self, callback, route):
        if self.keyword in Signature.from_callable(route.callback).parameters:
            @wraps(callback)
            def wrapper(*args, **kwargs):
                uid = request.get_cookie('uid', secret=db.get_secret())
                if uid is None:
                    return redirect(self.loginpage)
                kwargs[self.keyword] = User(uid)
                csrf = None  # initialize variable
                if request.method == 'POST':
                    csrf = request.form.get('csrf')
                elif request.method == 'GET':
                    csrf = request.args.get('csrf')
                if csrf != request.get_cookie('csrf'):
                        abort(400)
                return callback(*args, **kwargs)

            return wrapper
        else:
            return callback
