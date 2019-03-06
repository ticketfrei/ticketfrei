% rebase('wrapper.tpl')
<a href="/logout/"><button>Logout</button></a>

% if enabled:
    <div id="enablebutton" style="float: right; padding: 2em;">Disable</div>
% else:
    <div id="enablebutton" style="float: right; padding: 2em;" color="red">Enable</div>
% end

<%
# import all the settings templates from bots/*/settings.tpl
from config import BOT_DIR
import os
bots = os.listdir(BOT_DIR)

for bot in bots:
    include(os.path.join(BOT_DIR, bot, 'settings.tpl'), csrf=csrf, city=city)
end
%>

<div>
    <h2>Edit your city page</h2>
    <p>
        With your bot, we generated you a page, which you can use for promotion:
        <a href="/city/{{city}}" target="_blank">Ticketfrei {{city}}</a> You
        can change what your users will read there, and adjust it to your
        needs.
    </p>
    <p>
        <b>You should definitely adjust the Social Media, E-Mail, and Telegram
        profile links.</b>
        Also consider adding this link to the text: <a href="/city/mail/{{city}}"
        target="_blank">Link to the mail subscription page</a>. Your readers
        can use this to subscribe to mail notifications.
    </p>
    <p>
        So this is the default text we suggest:
    </p>
    <form action="/settings/markdown" method="post">
        <textarea id="markdown" rows="20" cols="70" name="markdown" wrap="physical">{{markdown}}</textarea>
        <input name='csrf' value='{{csrf}}' type='hidden' />
        <input name='confirm' value='Save' type='submit'/>
    </form>
</div>

<div>
    <h2>Edit your trigger patterns</h2>
    <p>
        These words have to be contained in a report. If none of these
        expressions is in the report, it will be ignored by the bot. You can
        use the defaults, or enter some expressions specific to your city and
        language.
    </p>
    <form action="/settings/goodlist" method="post">
        <textarea id="goodlist" rows="8" cols="70" name="goodlist" wrap="physical">{{triggerwords}}</textarea>
        <input name='csrf' value='{{csrf}}' type='hidden' />
        <input name='confirm' value='Submit' type='submit'/>
    </form>
</div>

<div>
    <h2>Edit the blocklist</h2>
    <p>
        These words are not allowed in reports. If you encounter spam, you can
        add more here - the bot will ignore reports which use such words.
        There are words which you can't exclude from the blocklist, e.g.
        certain racist, sexist, or antisemitic slurs.
    </p>
    <form action="/settings/blocklist" method="post">
        <textarea id="blocklist" rows="8" cols="70" name="blocklist" wrap="physical">{{badwords}}</textarea>
        <input name='csrf' value='{{csrf}}' type='hidden' />
        <input name='confirm' value='Submit' type='submit'/>
    </form>
</div>


