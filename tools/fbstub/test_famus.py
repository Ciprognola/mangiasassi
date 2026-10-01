#!/usr/bin/env python3
"""0.4.5_31 (FA-MUS) tests: the Ferma Algidone! soundtrack (music.fa, own loopTrack instance `musicFa`), the
generic `rate` getter/setter added to the shared loop player, and the bite sound (sound.fa.bite). Reads the
loopTrack instances directly (top-level `let`/`const` bindings are reachable from page.evaluate, exactly like
`G`/`FA`/`S` in every other test here) rather than spying on Web Audio internals. Reuses the harness of
test_f2b.py. Run: python tools/fbstub/test_famus.py"""
import json, os, struct, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

FREEZE = "(()=>{window.__raf=window.__raf||window.requestAnimationFrame;window.requestAnimationFrame=()=>0;if(FA)cancelAnimationFrame(FA.raf);0})()"
UNF = "if(window.__raf)window.requestAnimationFrame=window.__raf;"


def start_run(p, tile="new", music=True):
    p.evaluate("(()=>{" + UNF + "S.opts.music=%s;if(FA){FA.dead=true;FA=null}G=null;S.quick=null;persist();go('menu')})()" % ("true" if music else "false")); p.wait_for_timeout(300)
    p.click("[data-tile=%s]" % tile); p.wait_for_timeout(300); p.click("[data-rg=ferma]")
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_practice(p, music=True):
    p.evaluate("(()=>{" + UNF + "S.opts.music=%s;if(FA){FA.dead=true;FA=null}go('menu')})()" % ("true" if music else "false")); p.wait_for_timeout(300)
    p.evaluate("startFerma({test:true})")
    p.wait_for_function("FA&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_enc(p, n=2, music=True):
    p.evaluate("(()=>{" + UNF + "S.opts.music=%s;if(FA){FA.dead=true;FA=null}go('menu')})()" % ("true" if music else "false")); p.wait_for_timeout(300)
    p.evaluate("startFerma({test:true,encounter:%d})" % n)
    p.wait_for_function("FA&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_real_enc(p, n=1):
    """a REAL (non-test) encounter, with an active maze G: faExit's 'back to maze' branch needs FA.enc.run and G"""
    p.evaluate("(()=>{" + UNF + "S.opts.music=true;if(FA){FA.dead=true;FA=null}G=null;S.quick=null;persist();go('menu')})()"); p.wait_for_timeout(300)
    p.evaluate("(()=>{cancelAnimationFrame(raf);startGame(false,{});cancelAnimationFrame(raf);startFerma({run:true,encounter:%d,dev:false})})()" % n)
    p.wait_for_function("FA&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


MUSIC_STATE = "({has:!!musicFa,paused:musicFa&&musicFa.paused,rate:musicFa&&musicFa.rate,vol:musicFa&&musicFa.volume})"
QUIET = "(()=>{faIntroEnd();Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;0})()"
STEP = "(n=>{for(let i=0;i<n;i++)faStep(1/60)})"


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=True)
    settle(p, 600)

    # ---------------- a) music.fa starts in all three modes; continues across a floor change and a death
    for label, starter in (("practice", start_practice), ("encounter", lambda pp: start_enc(pp, 2)), ("run", start_run)):
        starter(p)
        p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
        r = p.evaluate(MUSIC_STATE)
        check("a) %s: music.fa started (musicFa exists and is playing)" % label, r["has"] and not r["paused"], r)
    start_run(p)
    p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
    ref0 = p.evaluate("musicFa===musicFa")  # sanity, identity comparison below uses a stored handle
    p.evaluate("window.__mf0=musicFa")
    p.evaluate(QUIET); p.evaluate("FA.alg.wait=1e9;Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});faWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)")
    r = p.evaluate("({same:musicFa===window.__mf0,playing:musicFa&&!musicFa.paused})")
    check("a) same music.fa instance still playing through the win sequence", r["same"] and r["playing"], r)
    p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd();0")
    r = p.evaluate("({same:musicFa===window.__mf0,playing:musicFa&&!musicFa.paused,girone:FA.run.girone})")
    check("a) music.fa continues across a floor change (girone advanced, same instance, still playing)", r["same"] and r["playing"] and r["girone"] == 2, r)
    p.evaluate("FA.inv=0;faDie('x',true)"); p.evaluate("for(let i=0;i<200&&FA.state==='dying';i++)faStep(1/60)")
    r = p.evaluate("({same:musicFa===window.__mf0,playing:musicFa&&!musicFa.paused,state:FA.state})")
    check("a) music.fa continues through a death and respawn", r["same"] and r["playing"] and r["state"] == "play", r)
    check("no console errors (a)", not errs, errs)

    # ---------------- b) paused on pause, resumed on unpause
    start_practice(p)
    p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
    p.evaluate("faIntroEnd();faPause(true)")
    check("b) paused with the game", p.evaluate("musicFa.paused") is True)
    p.evaluate("faPause(false)")
    p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
    check("b) resumed with the game", p.evaluate("!musicFa.paused"))
    check("no console errors (b)", not errs, errs)

    # ---------------- c) exit to maze -> no music; exit to menu -> menu track
    start_real_enc(p, 1)
    p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
    p.evaluate("faIntroEnd();faExit()"); p.wait_for_timeout(300)
    r = p.evaluate("({screen,musicFaPaused:musicFa&&musicFa.paused,bgmPaused:bgm&&bgm.paused})")
    check("c) exit to the maze (real encounter, faIntroEnd -> Continua): music.fa silenced, maze has no music", r["screen"] == "game" and r["musicFaPaused"] is True and r["bgmPaused"] is True, r)
    p.evaluate("cancelAnimationFrame(raf);G=null;go('menu')"); p.wait_for_timeout(300)
    start_practice(p)
    p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
    p.evaluate("faIntroEnd();faExit()"); p.wait_for_timeout(1200)
    r = p.evaluate("({screen,musicFaPaused:musicFa&&musicFa.paused,bgmPaused:bgm&&bgm.paused})")
    check("c) exit to the menu (practice Esci): music.fa silenced, the menu track plays", r["screen"] == "menu" and r["musicFaPaused"] is True and r["bgmPaused"] is False, r)
    check("no console errors (c)", not errs, errs)

    # ---------------- d) last-bite ending: rate -> lastSlow, volume fades to 0, stopped at the popup
    start_run(p); p.evaluate(QUIET); p.evaluate("FA.inv=1e9")
    p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
    v0 = p.evaluate("musicFa.volume")
    p.evaluate("FA.alg.state='idle';FA.alg.t=0;FA.bar.left=1;FA.bar.pending=true")
    p.evaluate(STEP + "(2)")  # idle -> the bite is consumed at once (FA.lb set)
    check("d) last bite started (FA.lb set)", p.evaluate("!!FA.lb"))
    check("d) rate set to FA_RUN.bar.lastSlow during the slow motion", p.evaluate("musicFa.rate") == p.evaluate("FA_RUN.bar.lastSlow"), (p.evaluate("musicFa.rate"), p.evaluate("FA_RUN.bar.lastSlow")))
    p.evaluate(STEP + "(108)")  # lastSlowDur 1.5s (90 frames) + part of the 1s fade (~18/60 frames): still mid-fade
    mid = p.evaluate("(v0)=>({a:FA.lb.a,vol:musicFa?musicFa.volume:null,v0})", v0)
    check("d) volume fading towards 0 during the fade to black (proportional to 1 - FA.lb.a)", 0 < mid["a"] < 1 and abs(mid["vol"] - v0 * (1 - mid["a"])) < 1e-6, mid)
    p.evaluate(STEP + "(50)")  # finishes the fade (total ~160 frames from the bite) -> faLastBiteEnd -> popup
    r = p.evaluate("({state:FA.state,paused:musicFa&&musicFa.paused,h3:document.querySelector('#fapanel h3').textContent})")
    check("d) music.fa stopped exactly when the popup shows", r["state"] == "over" and r["paused"] is True and r["h3"] == "Algidone ha finito tutto!", r)
    check("no console errors (d)", not errs, errs)

    # ---------------- e) music option off -> nothing plays
    start_run(p, music=False); p.wait_for_timeout(400)
    r = p.evaluate("({has:!!musicFa,paused:musicFa&&musicFa.paused})")
    check("e) music option off: music.fa never plays", r["has"] and r["paused"] is True, r)
    check("no console errors (e)", not errs, errs)
    ctx.close()

    # ---------------- f) dev upload overrides music.fa, reset restores the built-in, export target listed
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=True)
    settle(p, 600)
    def wav(ms, rate=8000):  # minimal valid WAV, named .mp3 below (the upload handler only checks name/type; Chromium decodes by content)
        n = int(rate * ms / 1000); data = bytes([128]) * n
        return (b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate, 1, 8) + b"data" + struct.pack("<I", n) + data)
    mp3 = wav(300)
    tmp = tempfile.mkdtemp(prefix="mgs_famus_")
    mp3path = os.path.join(tmp, "custom.mp3")
    open(mp3path, "wb").write(mp3)
    p.evaluate("(()=>{cancelAnimationFrame(raf);G=null;go('menu')})()"); p.wait_for_timeout(300)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(#fmf)').open"):
        p.click("details.acc:has(#fmf) > summary"); p.wait_for_timeout(250)
    check("f) upload/reset UI present, open to every dev (no master gate)", p.evaluate("!!document.querySelector('#fmf')&&!!document.querySelector('#fmr')"))
    p.set_input_files("#fmf", mp3path); p.wait_for_timeout(500)
    r = p.evaluate("(async()=>({musicFaNull:musicFa===null,idb:!!(await IDB.get('musicFa'))}))()")
    check("f) upload: musicFa reset to null (forces a rebuild), the file is stored in IDB", r["musicFaNull"] and r["idb"], r)
    p.evaluate("window.__seenUrl=null;const orig=loopTrack;loopTrack=(url,opts)=>{if(!window.__seenUrl)window.__seenUrl=url;return orig(url,opts)}")
    start_practice(p)
    p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
    check("f) upload took effect: loopTrack was built from a blob: URL (the uploaded file), not the embedded data: URL", p.evaluate("window.__seenUrl.startsWith('blob:')"), p.evaluate("window.__seenUrl"))
    items = p.evaluate("(async()=>(await expAudioItems()).map(i=>i.target))()")
    check("f) export target music.fa listed once an override exists", "music.fa" in items, items)
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}go('menu')})()"); p.wait_for_timeout(300)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(#fmr)').open"):
        p.click("details.acc:has(#fmr) > summary"); p.wait_for_timeout(250)
    p.click("#fmr"); p.wait_for_timeout(300)
    r = p.evaluate("(async()=>({musicFaNull:musicFa===null,idb:!!(await IDB.get('musicFa'))}))()")
    check("f) reset: musicFa null again, IDB entry gone", r["musicFaNull"] and not r["idb"], r)
    p.evaluate("window.__seenUrl=null")
    start_practice(p)
    p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
    check("f) after reset: loopTrack built from the embedded data: URL again (built-in track)", p.evaluate("window.__seenUrl.startsWith('data:audio/mpeg;base64,')"), p.evaluate("(window.__seenUrl||'').slice(0,40)"))
    check("no console errors (f)", not errs, errs)

    # ---------------- g) sound.fa.bite: a scheduled bite (run) and an eat (practice)
    p.evaluate("window.__snd=[];window.__orig_playSnd=playSnd;playSnd=(slot,ch)=>{window.__snd.push([slot,ch]);return window.__orig_playSnd(slot,ch)}")
    start_run(p); p.evaluate(QUIET); p.evaluate("FA.inv=1e9;window.__snd=[]")
    p.evaluate("FA.bar.left=3;FA.bar.pending=true"); p.evaluate(STEP + "(65)")
    check("g) scheduled bite (run) plays sound.fa.bite", p.evaluate("window.__snd.some(([s,c])=>s==='bite'&&c==='fa')"), p.evaluate("window.__snd"))
    start_practice(p); p.evaluate(QUIET); p.evaluate("window.__snd=[];FA.inv=1e9")
    p.evaluate("FA.bar.left=3;FA.bar.pending=true")  # FR1b2: practice has no random eat any more, only scheduled bites (same as a run)
    p.evaluate("FA.alg.state='idle';FA.alg.wait=0"); p.evaluate(STEP + "(3)")
    check("g) a scheduled bite (practice, FR1b2) plays sound.fa.bite", p.evaluate("window.__snd.some(([s,c])=>s==='bite'&&c==='fa')") and p.evaluate("FA.alg.state") == "eat", p.evaluate("window.__snd"))
    p.evaluate("playSnd=window.__orig_playSnd")
    check("no console errors (g)", not errs, errs)

    # ---------------- h) the other tracks: unchanged start/stop, rate defaults to 1
    # (calling each track's own init/play directly rather than the full screen flow, which the existing
    # suites already cover end to end -- here only the shared loopTrack `rate` addition is in scope)
    p.evaluate("(()=>{" + UNF + "S.opts.music=true;if(FA){FA.dead=true;FA=null}go('menu')})()"); p.wait_for_timeout(600)
    r = p.evaluate("({playing:bgm&&!bgm.paused,rate:bgm&&bgm.rate})")
    check("h) menu track: still plays on the menu, rate defaults to 1", r["playing"] and r["rate"] == 1, r)
    r = p.evaluate("(async()=>{await gamMusicInit();gamMusic(true);await new Promise(res=>setTimeout(res,300));return{playing:bgmGam&&!bgmGam.paused,rate:bgmGam&&bgmGam.rate}})()")
    check("h) El Gamblador track: still starts (gamMusicInit/gamMusic), rate defaults to 1", r["playing"] and r["rate"] == 1, r)
    r = p.evaluate("(async()=>{await prMusic('intro',{});return{slot:PRM.slot,playing:PRM.a&&!PRM.a.paused,rate:PRM.a&&PRM.a.rate}})()")
    check("h) professor track: still starts (prMusic), rate defaults to 1", r["playing"] and r["rate"] == 1, r)
    check("no console errors (h)", not errs, errs)
    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
