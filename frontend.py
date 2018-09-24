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
        city = request.forms['city']
    except KeyError:
        return dict(error='Please, fill the form.')
    if password != password_repeat:
        return dict(error='Passwords do not match.')
    if db.by_email(email):
        return dict(error='Email address already in use.')
    # send confirmation mail
    try:
        link = url('confirm/' + city + '/%s' % db.user_token(email, password))
        print(link)  # only for local testing
        logger.error('confirmation link to ' + email + ": " + link)
        sendmail(
                email,
                "Confirm your account",
                "Complete your registration here: %s" % (link)
            )
        return dict(info='Confirmation mail sent.')
    except Exception:
        logger.error("Could not send confirmation mail to " + email, exc_info=True)
        return dict(error='Could not send confirmation mail.')


@get('/confirm/<city>/<token>')
@view('template/propaganda.tpl')
def confirm(city, token):
    # create db-entry
    if db.confirm(token, city):
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
def city_page(city, info=None):
    citydict = db.user_facing_properties(city)
    if citydict is not None:
        citydict['info'] = info
        return bottle.template('template/city.tpl', **citydict)
    return bottle.template('template/propaganda.tpl',
                           **dict(info='There is no Ticketfrei bot in your city'
                                       ' yet. Create one yourself!'))


@get('/city/mail/<city>')
@view('template/mail.tpl')
def display_mail_page(city):
    user = db.by_city(city)
    return user.state()


@post('/city/mail/submit/<city>')
def subscribe_mail(city):
    email = request.forms['mailaddress']
    token = db.mail_subscription_token(email, city)
    confirm_link = url('city/mail/confirm/' + token)
    print(confirm_link)  # only for local testing
    # send mail with code to email
    sendmail(email, "Subscribe to Ticketfrei " + city + " Mail Notifications",
             body="To subscribe to the mail notifications for Ticketfrei " +
                  city + ", click on this link: " + confirm_link)
    return city_page(city, info="Thanks! You will receive a confirmation mail.")


@get('/city/mail/confirm/<token>')
def confirm_subscribe(token):
    email, city = db.confirm_subscription(token)
    user = db.by_city(city)
    user.add_subscriber(email)
    return city_page(city, info="Thanks for subscribing to mail notifications!")


@get('/city/mail/unsubscribe/<token>')
def unsubscribe(token):
    email, city = db.confirm_subscription(token)
    user = db.by_city(city)
    user.remove_subscriber(email)
    return city_page(city, info="You successfully unsubscribed " + email +
                     " from the mail notifications.")


@get('/settings')
@view('template/settings.tpl')
def settings(user):
    return user.state()


@post('/settings/markdown')
@view('template/settings.tpl')
def update_markdown(user):
    user.set_markdown(request.forms['markdown'])
    return user.state()


@post('/settings/mail_md')
@view('template/settings.tpl')
def update_mail_md(user):
    user.set_mail_md(request.forms['mail_md'])
    return user.state()


@post('/settings/goodlist')
@view('template/settings.tpl')
def update_trigger_patterns(user):
    user.set_trigger_words(request.forms['goodlist'])
    return user.state()


@post('/settings/blocklist')
@view('template/settings.tpl')
def update_badwords(user):
    user.set_badwords(request.forms['blocklist'])
    return user.state()


@post('/settings/telegram')
def register_telegram(user):
    apikey = request.forms['apikey']
    user.update_telegram_key(apikey)
    return city_page(user.get_city(), info="Thanks for registering Telegram!")


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
    masto_pass = request.forms.get('pass')
    client_id, client_secret = user.get_mastodon_app_keys(instance_url)
    m = Mastodon(client_id=client_id, client_secret=client_secret,
                 api_base_url=instance_url)
    try:
        access_token = m.log_in(masto_email, masto_pass)
        user.save_masto_token(access_token, instance_url)

        # Trying to set the seen_toot to 0, thereby initializing it.
        # It should work now, but has default values. Not sure if I need them.
        user.init_seen_toot(instance_url)

        return city_page(user.get_city(), info='Thanks for supporting decentralized social networks!')
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
    bottle.run(host=config["web"]["host"], port=config["web"]["port"])
else:
    application.catchall = False
