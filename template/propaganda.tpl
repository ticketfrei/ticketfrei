% rebase('template/wrapper.tpl')
% if defined('info'):
<div class="ui-widget">
    <div class="ui-state-highlight ui-corner-all" style="padding: 0.7em;">
        <p><span class="ui-icon ui-icon-info" style="float: left; margin-right: .3em;"></span>{{!info}}</p>
    </div>
</div>
<br>
% end
% include('template/login-plain.tpl')
<h1>Features</h1>
<p>
    Don't pay for public transport. Instead, warn each other
    from ticket controllers! With Ticketfrei, you can turn
    your city into a paradise for fare dodgers.
</p>
<p>
    Ticketfrei is a Twitter, Mastodon, and E-Mail bot. Users
    can help each other by tweeting, tooting, or mailing,
    when and where they spot a ticket controller.
</p>
<p>
    Ticketfrei automatically retweets, boosts, and remails
    those controller reports, so others can see them. If there
    are ticket controllers around, they can still buy a ticket
    - but if the coast is clear, they can save the money.
</p>
<h2>How to get Ticketfrei to my city?</h2>
<p>
    We try to make it as easy as possible to spread Ticketfrei
    to other citys. There are four basic steps:
</p>
<ul>
    <li>Create a Twitter and/or a Mastodon account.</li>
    <li>Register on this website to create a bot for your city.</li>
    <li>Log in with the social media accounts you want to
    use for Ticketfrei.</li>
    <li>Promote the service! Ticketfrei only works if there is
    a community for it. Fortunately, we prepared some material
    you can use:
    <a href="https://github.com/b3yond/ticketfrei/tree/master/promotion" target="_blank">https://github.com/b3yond/ticketfrei/tree/master/promotion</a></li>
</ul>
% include('template/register-plain.tpl')
<h2>Our Mission</h2>
<p>
    Public transportation is meant to provide an easy and
    time-saving way to move within a region while being
    affordable for everybody. Unfortunately, this is not the
    case. Ticketfrei's approach is to enable people to
    reclaim public transportation.
</p>
<p>
    On short term we want to do this by helping users to avoid
    controllers and fines - on long term by pressuring public
    transportation companies to offer their services free of
    charge, financed by the public.
</p>
<p>
    Because with Ticketfrei you're able to use trains and
    subways for free anyway. Take part and create a new
    understanding of what public transportation should look
    like!
</p>



