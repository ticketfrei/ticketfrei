% rebase('template/wrapper.tpl')
<a href="/logout/"><button>Logout</button></a>

<div id="enablebutton" style="float: right; padding: 2em;">asdf</div>

<a class='button' style="padding: 1.5em;" href="/login/twitter">
    <picture>
        <source type='image/webp' sizes='20px' srcset="/static-cb/1517673283/twitter-20.webp 20w,/static-cb/1517673283/twitter-40.webp 40w,/static-cb/1517673283/twitter-80.webp 80w,"/>
        <source type='image/png' sizes='20px' srcset="/static-cb/1517673283/twitter-20.png 20w,/static-cb/1517673283/twitter-40.png 40w,/static-cb/1517673283/twitter-80.png 80w,"/>
        <img src="https://patriciaannbridewell.files.wordpress.com/2014/04/official-twitter-logo-tile.png" alt="" />
    </picture>
    Log in with Twitter
</a>

<section style="padding: 1.5em;">
    <h2>Log in with Mastodon</h2>
    <p>
        <form action="/login/mastodon" method='post'>
            <label for="email">E-Mail of your Mastodon-Account</label>
            <input type="text" placeholder="Enter Email" name="email" id="email" required>

            <label for="pass">Mastodon Password</label>
            <input type="password" placeholder="Enter Password" name="pass" id="pass" required>

            <label>Mastodon instance:
                <input type='text' name='instance_url' list='instances' placeholder='social.example.net'/>
            </label>
            <datalist id='instances'>
                <option value=''>
                <option value='anticapitalist.party'>
                <option value='awoo.space'>
                <option value='cybre.space'>
                <option value='mastodon.social'>
                <option value='glitch.social'>
                <option value='botsin.space'>
                <option value='witches.town'>
                <option value='social.wxcafe.net'>
                <option value='monsterpit.net'>
                <option value='mastodon.xyz'>
                <option value='a.weirder.earth'>
                <option value='chitter.xyz'>
                <option value='sins.center'>
                <option value='dev.glitch.social'>
                <option value='computerfairi.es'>
                <option value='niu.moe'>
                <option value='icosahedron.website'>
                <option value='hostux.social'>
                <option value='hyenas.space'>
                <option value='instance.business'>
                <option value='mastodon.sdf.org'>
                <option value='pawoo.net'>
                <option value='pouet.it'>
                <option value='scalie.business'>
                <option value='sleeping.town'>
                <option value='social.koyu.space'>
                <option value='sunshinegardens.org'>
                <option value='vcity.network'>
                <option value='octodon.social'>
                <option value='soc.ialis.me'>
            </datalist>
            <input name='confirm' value='Log in' type='submit'/>
        </form>
    </p>
</section>

<div style="float: left; padding: 1.5em;">
    <h2>Edit your city page</h2>
    <p>
        With your bot, we generated you a page, which you can use for promotion: <a href="city/$city"
        target="_blank">Ticketfrei $city</a> You can change what your users will read there, and adjust it to your
        needs. <b>You should definitely adjust the Social Media profile links.</b> This is just the default text we
        suggest:
    </p>
    <form action="/settings/goodlist" method="post">
        <textarea id="markdown" rows="20" cols="70" name="goodlist" wrap="physical">$markdown</textarea>
        <input name='confirm' value='Save' type='submit'/>
    </form>
</div>

<div style="float: left; padding: 1.5em;">
    <h2>Edit your trigger patterns</h2>
    <p>
        These words have to be contained in a report.
        If none of these expressions is in the report, it will be ignored by the bot.
        You can use the defaults, or enter some expressions specific to your city and language.
    </p>
    <form action="/settings/goodlist" method="post">
        <!-- find a way to display current good list. js which reads from a cookie? template? -->
        <textarea id="goodlist" rows="8" cols="70" name="goodlist" wrap="physical">$triggerwords</textarea>
        <input name='confirm' value='Submit' type='submit'/>
    </form>
</div>

<div style="float:right; padding: 1.5em;">
    <h2>Edit the blacklist</h2>
    <p>
        These words are not allowed in reports.
        If you encounter spam, you can add more here - the bot will ignore reports which use such words.
        <!-- There are words which you can't exclude from the blacklist, e.g. certain racist, sexist, or antisemitic slurs. (to be implemented) -->
    </p>
    <form action="/settings/blacklist" method="post">
        <!-- find a way to display current blacklist. js which reads from a cookie? template? -->
        <textarea id="blacklist" rows="8" cols="70" name="blacklist" wrap="physical">$badwords</textarea>
        <input name='confirm' value='Submit' type='submit'/>
    </form>
</div>


