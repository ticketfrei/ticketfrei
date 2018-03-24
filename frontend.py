import bottle
from bottle import get, post, redirect, request, response, view
from db import DBPlugin
import tweepy
import sendmail
import smtplib
from mastodon import Mastodon
import prepare


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
    send_confirmation_mail(db.config, confirm_link, email)
    return dict(info='Confirmation mail sent.')


def send_confirmation_mail(config, confirm_link, email):
    m = sendmail.Mailer(config)
    try:
        m.send("Complete your registration here: " + confirm_link, email, "[Ticketfrei] Confirm your account")
    except smtplib.SMTPRecipientsRefused:
        return "Please enter a valid E-Mail address."


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


@get('/login/twitter', user='user')
def login_twitter(user):
    """
    Starts the twitter OAuth authentication process.
    :return: redirect to twitter.
    """
    consumer_key = user.db.config["tapp"]["consumer_key"]
    consumer_secret = user.db.config["tapp"]["consumer_secret"]
    callback_url = bottle.request.get_header('host') + "/login/twitter/callback"
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        user.db.logger.error('Twitter OAuth Error: Failed to get request token.', exc_info=True)
        return dict(error="Failed to get request token.")
    user.save_request_token(auth.request_token)
    return bottle.redirect(redirect_url)


@get('/login/twitter/callback', user="user")
def twitter_callback(user):
    """
    Gets the callback
    :return:
    """
    # twitter passes the verifier/oauth token secret in a GET request.
    verifier = bottle.request.query('oauth_verifier')
    consumer_key = user.db.config["tapp"]["consumer_key"]
    consumer_secret = user.db.config["tapp"]["consumer_secret"]
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    request_token = user.get_request_token
    auth.request_token = {"oauth_token": request_token,
                          "oauth_token_secret": verifier}
    auth.get_access_token(verifier)
    user.save_twitter_token(auth.access_token, auth.access_token_secret)
    return bottle.redirect("/settings")


@post('/login/mastodon', user="user")
def login_mastodon(user):
    """
    Starts the mastodon OAuth authentication process.
    :return: redirect to twitter.
    """
    # get app tokens
    instance_url = bottle.request.forms.get('instance_url')
    masto_email = bottle.request.forms.get('email')
    print(masto_email)
    masto_pass = bottle.request.forms.get('pass')
    print(masto_pass)
    client_id, client_secret = user.get_mastodon_app_keys(instance_url)
    m = Mastodon(client_id=client_id, client_secret=client_secret, api_base_url=instance_url)
    try:
        access_token = m.log_in(masto_email, masto_pass)
        user.save_masto_token(access_token, instance_url)
        return dict(info='Thanks for supporting decentralized social networks!')
    except:
        user.db.logger.error('Login to Mastodon failed.', exc_info=True)
        return dict(error='Login to Mastodon failed.')


if __name__ == '__main__':
    # testing only
    bottle.install(DBPlugin(':memory:', '/'))
    bottle.run(host='localhost', port=8080)
else:
    config = prepare.get_config()
    bottle.install(DBPlugin(config['database']['db_path'], '/'))
    application = bottle.default_app()
