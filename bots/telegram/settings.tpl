
<%
# todo: hide this part, if there is already a telegram bot connected.
%>
<div>
    <h2>Connect with Telegram</h2>
    <p>
        If you have a Telegram account, you can register a bot there. Just
        write to @botfather. There are detailed instructions on
        <a href="https://botsfortelegram.com/project/the-bot-father/" target="_blank">
        Bots for Telegram</a>.
    </p>
    <p>
        The botfather will give you an API key - with the API key, Ticketfrei
        can use the Telegram bot. Enter it here:
    </p>
    <form action="/settings/telegram" method="post">
        <input type="text" name="apikey" placeholder="Telegram bot API key" id="apikey">
        <input name='csrf' value='{{csrf}}' type='hidden' />
        <input name='confirm' value='Login with Telegram' type='submit'/>
    </form>
</div>

