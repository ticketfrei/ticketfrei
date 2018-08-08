% rebase('template/wrapper.tpl')

<%
import markdown as md

html = md.markdown(markdown)
%>

<form action="/city/mail/submit/{{!city}}" method="post">
    <input type="text" name="mailaddress" placeholder="E-Mail address" id="mailaddress">
    <input name='confirm' value='Subscribe to E-Mail notifications' type='submit'/>
</form>


{{!html}}
