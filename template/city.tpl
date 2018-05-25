% rebase('template/wrapper.tpl')

<%
import markdown2 as md

html = md.markdown(markdown)
%>

{{html}}
