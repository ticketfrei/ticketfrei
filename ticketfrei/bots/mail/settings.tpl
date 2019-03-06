
<div>
    <h2>Edit your mail subscription page</h2>
    <p>
        There is also a page where users can subscribe to mail notifications:
        <a href="/city/mail/{{city}}" target="_blank">Ticketfrei {{city}}</a>.
        You can change what your users will read there, and adjust it to your
        needs.
    </p>
    <p>
        So this is the default text we suggest:
    </p>
    <form action="/settings/mail_md" method="post">
        <textarea id="mail_md" rows="20" cols="70" name="mail_md" wrap="physical">{{mail_md}}</textarea>
        <input name='csrf' value='{{csrf}}' type='hidden' />
        <input name='confirm' value='Save' type='submit'/>
    </form>
</div>

