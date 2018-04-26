#!/usr/bin/env python3
import bottle
from bottle import get, post, redirect, request, response, view
from config import config
from db import db
import logging
import tweepy
from sendmail import sendmail
from session import SessionPlugin
from mastodon import Mastodon


def url(route):
    return '%s://%s/%s' % (
            request.urlparts.scheme,
            request.urlparts.netloc,
            route)


@get('/')
@view('template/propaganda.tpl')
def propaganda():
    pass


@post('/register')
@view('template/register.tpl')
def register_post():
    try:
        email = request.forms['email']
        password = request.forms['pass']
        password_repeat = request.forms['pass-repeat']
    except KeyError:
        return dict(error='Please, fill the form.')
    if password != password_repeat:
        return dict(error='Passwords do not match.')
    if db.by_email(email):
        return dict(error='Email address already in use.')
    # send confirmation mail
    try:
        sendmail(
                email,
                "Confirm your account",
                "Complete your registration here: %s" % (
                        url('confirm/%s' % db.user_token(email, password))
                    )
            )
        return dict(info='Confirmation mail sent.')
    except Exception:
        logger.error("Could not send confirmation mail to " + email, exc_info=True)
        return dict(error='Could not send confirmation mail.')


@get('/confirm/<token>')
@view('template/propaganda.tpl')
def confirm(token):
    # create db-entry
    if db.confirm(token):
        # :todo show info "Account creation successful."
        redirect('/settings')
    return dict(error='Email confirmation failed.')


@post('/login')
@view('template/login.tpl')
def login_post():
    # check login
    try:
        if db.by_email(request.forms['email']) \
             .check_password(request.forms['pass']):
            redirect('/settings')
    except KeyError:
        return dict(error='Please, fill the form.')
    except AttributeError:
        pass
    return dict(error='Authentication failed.')


@get('/city/<city>')
@view('/template/user-facing.tpl')
def city_page(city):
    # :todo how can we transfer the city name to the wrapper template?
    pass


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


@get('/guides/<filename:path>')
def guides(filename):
    return bottle.static_file(filename, root='guides')


@get('/logout/')
def logout():
    # clear auth cookie
    response.set_cookie('uid', '', expires=0, path="/")
    # :todo show info "Logout successful."
    redirect('/')


@get('/login/twitter')
def login_twitter(user):
    """
    Starts the twitter OAuth authentication process.
    :return: redirect to twitter.
    """
    consumer_key = config["twitter"]["consumer_key"]
    consumer_secret = config["twitter"]["consumer_secret"]
    callback_url = url("login/twitter/callback")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        logger.error('Twitter OAuth Error: Failed to get request token.',
                     exc_info=True)
        return dict(error="Failed to get request token.")
    user.save_request_token(auth.request_token)
    redirect(redirect_url)


@get('/login/twitter/callback')
def twitter_callback(user):
    """
    Gets the callback
    :return:
    """
    # twitter passes the verifier/oauth token secret in a GET request.
    verifier = request.query['oauth_verifier']
    consumer_key = config["twitter"]["consumer_key"]
    consumer_secret = config["twitter"]["consumer_secret"]
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    request_token = user.get_request_token()
    auth.request_token = request_token
    auth.get_access_token(verifier)
    user.save_twitter_token(auth.access_token, auth.access_token_secret)
    redirect("/settings")


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
    except Exception:
        logger.error('Login to Mastodon failed.', exc_info=True)
        return dict(error='Login to Mastodon failed.')


logger = logging.getLogger()
fh = logging.FileHandler('/var/log/ticketfrei/error.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

application = bottle.default_app()
bottle.install(SessionPlugin('/'))

if __name__ == '__main__':
    # testing only
    bottle.run(host='localhost', port=8080)
else:
    application.catchall = False
