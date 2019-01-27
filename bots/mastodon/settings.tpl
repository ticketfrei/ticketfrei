
<section>
    <h2>Log in with Mastodon</h2>
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
            <input name='csrf' value='{{csrf}}' type='hidden' />
            <input name='confirm' value='Log in' type='submit'/>
        </form>
</section>

