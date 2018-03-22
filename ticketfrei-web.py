import bottle
from bottle import get, post, redirect, request, response, view
from db import DBPlugin


@get('/')
@view('template/propaganda.tpl')
def propaganda():
    pass

@post('/register', db='db')
@view('template/register.tpl')
def register_post(db):
    email = request.forms.get('email', '')
    password = request.forms.get('pass', '')
    password_repeat = request.forms.get('pass-repeat', '')
    if password != password_repeat:
        return dict(error='Passwords do not match.')
    if db.by_email(email):
        return dict(error='Email address already in use.')
    # send confirmation mail
    confirm_link = request.url + "/../confirm/" + db.token(email, password)
    db.send_confirmation_mail(confirm_link, email)
    return dict(info='Confirmation mail sent.')


@get('/confirm/<token>', db='db')
@view('template/propaganda.tpl')
def confirm(db, token):
    # create db-entry
    if db.register(token):
        # :todo show info "Account creation successful."
        return redirect('/settings')
    return dict(error='Account creation failed.')


@post('/login', db='db')
@view('template/login.tpl')
def login_post(db):
    # check login
    if db.authenticate(request.forms.get('email', ''),
                       request.forms.get('pass', '')):
        return redirect('/settings')
    return dict(error='Authentication failed.')


@get('/settings', user='user')
@view('template/settings.tpl')
def settings(user):
    return user.state()


@get('/api/state', user='user')
def api_enable(user):
    return user.state()


@get('/static/<filename:path>')
def static(filename):
    return bottle.static_file(filename, root='static')

@get('/logout/')
def logout():
    # clear auth cookie
    response.set_cookie('uid', '', expires=0, path="/")
    # :todo show info "Logout successful."
    return redirect('/')


bottle.install(DBPlugin('/'))
bottle.run(host='localhost', port=8080)
