% rebase('template/wrapper.tpl')

<%
import markdown as md

html = md.markdown(mail_md)
%>

{{!html}}

<form action="/city/mail/submit/{{!city}}" method="post">
    <input type="text" name="mailaddress" placeholder="E-Mail address" id="mailaddress">
    <input name='confirm' value='Subscribe to E-Mail notifications' type='submit'/>
</form>
<br>
<p style="text-align: center;"><a href="/city/{{!city}}">Back to Ticketfrei {{!city}} overview</a></p>
