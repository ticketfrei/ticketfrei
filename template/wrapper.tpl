<head>
    <title>Ticketfrei - {{get('title', 'A bot against control society!')}}</title>
    <meta name='og:title' content='Ticketfrei'/>
    <meta name='og:description' content='A bot against control society! Nobody should have to pay for public transport. Find out where ticket controllers are!'/>
    <meta name='og:image' content="https://ticketfrei.links-tech.org/static/img/ticketfrei-og-image.png"/>
    <meta name='og:image:alt' content='Ticketfrei'/>
    <meta name='og:type' content='website' />
    <link rel='stylesheet' href='/static/css/style.css'>
    <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
    <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
    <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
</head>
<body>
    <div id="content">
        <img src="/static/img/ticketfrei_logo.png" alt="Ticketfrei" id="logo">
        % if defined('error'):
        <div class="ui-widget">
            <div class="ui-state-error ui-corner-all" style="padding: 0.7em;">
                <p><span class="ui-icon ui-icon-alert" style="float: left; margin-right: .3em;"></span>{{error}}</p>
            </div>
        </div>
        % end
        {{!base}}
        <p>Contribute on <a href="https://github.com/b3yond/ticketfrei">GitHub!</a></p>
    </div>
</body>
