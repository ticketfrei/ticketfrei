% rebase('template/wrapper.tpl')

<%
import markdown as md

html = md.markdown(markdown)
%>

% if info is not None:
<div class="ui-widget">
    <div class="ui-state-highlight ui-corner-all" style="padding: 0.7em;">
        <p><span class="ui-icon ui-icon-info" style="float: left; margin-right: .3em;"></span>{{!info}}</p>
    </div>
</div>
% end

{{!html}}
