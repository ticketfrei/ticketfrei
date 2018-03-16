function enableButton() {
    var enablebutton = '<form action="/enable" method="POST"> <button type="submit">Enable</button> </form> ';
    var disablebutton = '<form action="/disable" method="POST"> <button style="background-color: red;" type="submit">Disable</button> </form> ';
    var enabled = getCookie('enabled');
    if (enabled == "True") {
        return disablebutton;
    } else {
        return enablebutton;
    }
}

function getCookie(cname) {
    var name = cname + '=';
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

document.getElementById("enablebutton").innerHTML = enableButton();

// document.getElementById("goodlist").innerHTML = getCookie("goodlist");

alert(getCookie("goodlist"))
alert(getCookie("blacklist"))

// document.getElementById("blacklist").innerHTML = getCookie("blacklist");