import bottle
from bottle import get, post, redirect, request, response, view
from config import config
from db import db
import logging
import tweepy
import sendmail
from session import SessionPlugin
import smtplib
from mastodon import Mastodon


logger = logging.getLogger(__name__)


@get('/')
@view('template/propaganda.tpl')
def propaganda():
    pass


@post('/register')
@view('template/register.tpl')
def register_post():
    email = request.forms.get('email', '')
    password = request.forms.get('pass', '')
    password_repeat = request.forms.get('pass-repeat', '')
    if password != password_repeat:
        return dict(error='Passwords do not match.')
    if db.by_email(email):
        return dict(error='Email address already in use.')
    # send confirmation mail
    confirm_link = request.url + "/../confirm/" + db.user_token(email, password)
    send_confirmation_mail(confirm_link, email)
    return dict(info='Confirmation mail sent.')


def send_confirmation_mail(confirm_link, email):
    m = sendmail.Mailer()
    try:
        m.send("Complete your registration here: " + confirm_link, email,
               "[Ticketfrei] Confirm your account")
    except smtplib.SMTPRecipientsRefused:
        return "Please enter a valid E-Mail address."


@get('/confirm/<token>')
@view('template/propaganda.tpl')
def confirm(token):
    # create db-entry
    if db.confirm(token):
        # :todo show info "Account creation successful."
        return redirect('/settings')
    return dict(error='Email confirmation failed.')


@post('/login')
@view('template/login.tpl')
def login_post():
    # check login
    if db.by_email(request.forms.get('email', '')) \
         .check_password(request.forms.get('pass', '')):
        return redirect('/settings')
    return dict(error='Authentication failed.')


@get('/settings')
@view('template/settings.tpl')
def settings(user):
    return user.state()


@get('/api/state')
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


@get('/login/twitter')
def login_twitter(user):
    """
    Starts the twitter OAuth authentication process.
    :return: redirect to twitter.
    """
    consumer_key = config["tapp"]["consumer_key"]
    consumer_secret = config["tapp"]["consumer_secret"]
    callback_url = request.get_header('host') + "/login/twitter/callback"
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        logger.error('Twitter OAuth Error: Failed to get request token.',
                     exc_info=True)
        return dict(error="Failed to get request token.")
    user.save_request_token(auth.request_token)
    return bottle.redirect(redirect_url)


@get('/login/twitter/callback')
def twitter_callback(user):
    """
    Gets the callback
    :return:
    """
    # twitter passes the verifier/oauth token secret in a GET request.
    verifier = request.query('oauth_verifier')
    consumer_key = config["twitter"]["consumer_key"]
    consumer_secret = config["twitter"]["consumer_secret"]
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    request_token = user.get_request_token
    auth.request_token = {"oauth_token": request_token,
                          "oauth_token_secret": verifier}
    auth.get_access_token(verifier)
    user.save_twitter_token(auth.access_token, auth.access_token_secret)
    return bottle.redirect("/settings")


@post('/login/mastodon')
def login_mastodon(user):
    """
    Starts the mastodon OAuth authentication process.
    :return: redirect to twitter.
    """
    # get app tokens
    instance_url = request.forms.get('instance_url')
    masto_email = request.forms.get('email')
    print(masto_email)
    masto_pass = request.forms.get('pass')
    print(masto_pass)
    client_id, client_secret = user.get_mastodon_app_keys(instance_url)
    m = Mastodon(client_id=client_id, client_secret=client_secret,
                 api_base_url=instance_url)
    try:
        access_token = m.log_in(masto_email, masto_pass)
        user.save_masto_token(access_token, instance_url)
        return dict(
                info='Thanks for supporting decentralized social networks!'
            )
    except:
        logger.error('Login to Mastodon failed.', exc_info=True)
        return dict(error='Login to Mastodon failed.')


application = bottle.default_app()
bottle.install(SessionPlugin('/'))

if __name__ == '__main__':
    # testing only
    bottle.run(host='localhost', port=8080)
