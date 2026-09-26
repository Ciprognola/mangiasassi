#!/usr/bin/env python3
"""F6a headless tests (Firebase stub, no real Firestore): bug report button. Run: python tools/fbstub/test_f6.py"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "screens"))
import capture as C, fbstub
from playwright.sync_api import sync_playwright

RES = []
DEVC = {"role": "master", "acct": "master", "fb": True, "devOn": True}


def check(name, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name, extra)


def page(b, dev=True, vp=None, **kw):
    ctx = b.new_context(viewport=vp or C.VIEW, has_touch=True)
    if dev:
        ctx.add_init_script("if(!sessionStorage.getItem('__seeded')){sessionStorage.setItem('__seeded','1');localStorage.setItem('mgs_dev',%s)}" % json.dumps(json.dumps(DEVC)))
        kw.setdefault("session", "master")
    fbstub.install(ctx, **kw)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    return ctx, p, errs


def menu(p):
    p.goto(C.BASE + "index.html"); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(900)


def dev_click(p, sel):
    p.click("[data-tile=opt]"); p.wait_for_timeout(250); p.click("[data-otab=dev]"); p.wait_for_timeout(250)
    p.click(f"details.acc:has({sel}) > summary"); p.wait_for_timeout(250); p.click(sel); p.wait_for_timeout(500)


def has_bug(p):
    return p.evaluate("!!document.querySelector('#bugb')")


def hit_ok(p):  # tap area >= 44 px (the ::after extends the button by 4 px per side)
    return p.evaluate("(()=>{const r=document.querySelector('#bugb').getBoundingClientRect();return Math.min(r.width,r.height)+8})()") >= 44


def launch_browser(pw):
    """Some sandboxes preinstall a Chromium revision older than this pip playwright expects; fall
    back to whatever chrome-linux/chrome is actually on disk before giving up (see test_f4a.py)."""
    try:
        return pw.chromium.launch()
    except Exception:
        import glob, os
        base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
        cands = glob.glob(os.path.join(base, "chromium-*", "chrome-linux", "chrome")) if base else []
        if cands:
            return pw.chromium.launch(executable_path=cands[0])
        raise


srv = C.serve()
with sync_playwright() as pw:
    b = launch_browser(pw)
    # 1 hidden logged out
    ctx, p, errs = page(b, dev=False); menu(p)
    ids = []
    for s in ("menu", "opt", "wish", "ach", "road"):
        p.evaluate(f"go('{s}')"); p.wait_for_timeout(300); ids.append(has_bug(p))
    check("icon hidden when logged out (menu/opt/wish/ach/road)", not any(ids), ids)
    ctx.close()
    # 2 visible as dev, screenId, popup basics
    ctx, p, errs = page(b); menu(p)
    seen = {}
    for s in ("menu", "opt", "wish", "ach", "road"):
        p.evaluate(f"go('{s}')"); p.wait_for_timeout(300); seen[s] = (has_bug(p), p.evaluate("screenId()"))
    check("icon visible as dev on menu/opt/wish/ach/road", all(v[0] for v in seen.values()), seen)
    check("screenId on 5 screens", [seen[k][1] for k in ("menu", "opt", "wish", "ach", "road")] == ["menu-home-roccia", "opt-generali", "wish-enemies-roccia", "ach-gen", "road-top-current"], seen)
    p.evaluate("go('menu')"); p.wait_for_timeout(300); check("tap area >= 44 px", hit_ok(p))
    before = p.evaluate("localStorage.getItem('mgs_v1_dev')||localStorage.getItem('mgs_v1')")
    p.click("#bugb"); p.wait_for_timeout(300)
    check("popup opens", p.evaluate("!!document.querySelector('#bgt')") and "Hai un insetto?" in p.evaluate("document.querySelector('#modal').innerText"))
    check("Invia disabled when empty", p.evaluate("document.querySelector('#bgk').disabled"))
    p.fill("#bgt", "   "); check("Invia disabled with only spaces", p.evaluate("document.querySelector('#bgk').disabled"))
    p.fill("#bgt", "x" * 1200); check("1000 char cap + counter", p.evaluate("document.querySelector('#bgt').value.length") == 1000 and p.evaluate("document.querySelector('#bgc').innerText") == "1000/1000")
    p.fill("#bgt", "ciao"); p.press("#bgt", "Enter"); p.type("#bgt", "mondo"); check("Enter is a new line", p.evaluate("document.querySelector('#bgt').value") == "ciao\nmondo")
    p.keyboard.press("Escape"); p.wait_for_timeout(200); check("Esc = Indietro", not p.evaluate("!!document.querySelector('#bgt')"))
    p.click("#bugb"); p.wait_for_timeout(200); p.fill("#bgt", "  il menu ha un problema  "); p.click("#bgk"); p.wait_for_timeout(600)
    bugs = p.evaluate("window.__fbs.bugs||[]")
    check("send ok writes exactly the allowed field set", len(bugs) == 1 and sorted(bugs[0]) == sorted(["uid", "text", "screen", "version", "char", "ts", "ua", "meta"]), list(bugs[0]) if bugs else None)
    if bugs:
        d = bugs[0]
        check("field values", d["uid"] == "uid_master" and d["text"] == "il menu ha un problema" and d["screen"] == "menu-home-roccia" and d["version"] == p.evaluate("VERSION") and d["char"] == "roccia" and d["ts"] == {"__ts": True} and 0 < len(d["ua"]) <= 300, d)
        check("meta", set(d["meta"]) == {"acct", "site", "girone", "diff", "viewport"} and d["meta"]["site"] == "stable" and d["meta"]["viewport"] == "390x844" and d["meta"]["acct"] == "master", d["meta"])
    check("popup closed + success toast", not p.evaluate("!!document.querySelector('#bgt')") and "inviata" in p.evaluate("document.body.innerText"))
    after = p.evaluate("localStorage.getItem('mgs_v1_dev')||localStorage.getItem('mgs_v1')")
    check("save untouched by opening/sending", before == after)
    check("no console errors (menu flow)", not errs, errs)
    # 3 maze freeze
    p.click("[data-tile=new]"); p.wait_for_timeout(3600)
    check("icon in maze HUD, tap area", has_bug(p) and hit_ok(p) and p.evaluate("screenId()").startswith("maze-"), p.evaluate("screenId()"))
    snap = "JSON.stringify(G,(k,v)=>k==='grid'||k==='parts'||k==='last'?undefined:v)"
    a = p.evaluate(snap); p.wait_for_timeout(600); check("control: maze state changes while running", a != p.evaluate(snap))
    p.click("#bugb"); p.wait_for_timeout(200); a = p.evaluate(snap); st = p.evaluate("G.state"); p.wait_for_timeout(2000)
    check("maze frozen while popup open (no pause menu)", p.evaluate("G.state") == "pause" and a == p.evaluate(snap) and not p.evaluate("!!document.querySelector('#r')"), st)
    p.keyboard.press("ArrowLeft"); p.wait_for_timeout(300); check("keys don't reach the frozen maze", a == p.evaluate(snap))
    p.click("#bgx"); p.wait_for_timeout(700); check("Indietro resumes the maze", p.evaluate("G.state") == "play" and a != p.evaluate(snap))
    p.evaluate("G.st={on:true,t:8,tp:0,cd:0}"); check("screenId maze ability", p.evaluate("screenId()") == "maze-acciaio-roccia"); p.evaluate("G.st.on=false")
    p.evaluate("G.lives=1;G.state='dying';G.t=0"); p.wait_for_timeout(900); check("screenId over + icon on the over screen", p.evaluate("screenId()") == "maze-over" and has_bug(p))
    ctx.close()
    # 4 Ferma freeze
    ctx, p, errs = page(b); menu(p); dev_click(p, "#mgfa"); p.wait_for_timeout(3500)
    check("icon in Ferma HUD, tap area", has_bug(p) and hit_ok(p) and p.evaluate("screenId()") == "fa-floor1-play", p.evaluate("screenId()"))
    p.click("#bugb"); p.wait_for_timeout(200); t0, s0 = p.evaluate("[FA.t,FA.stock]"); p.wait_for_timeout(2000)
    check("Ferma frozen incl. stock, no pause panel", p.evaluate("FA.paused") and p.evaluate("[FA.t,FA.stock]") == [t0, s0] and not p.evaluate("!!document.querySelector('#fapanel.on')"))
    p.keyboard.press("Escape"); p.wait_for_timeout(300); check("Esc closes only the popup (Ferma stays paused until Indietro)", not p.evaluate("!!document.querySelector('#bgt')") and not p.evaluate("FA.paused"))
    p.click("#bugb"); p.wait_for_timeout(200); p.click("#bgx"); p.wait_for_timeout(700)
    check("Indietro resumes Ferma", not p.evaluate("FA.paused") and p.evaluate("FA.t") > t0)
    check("no console errors (Ferma)", not errs, errs)
    ctx.close()
    # 5 El Gamblador freeze
    ctx, p, errs = page(b); menu(p); dev_click(p, "#mggam"); p.wait_for_selector("#bp-yes"); p.wait_for_timeout(300)
    check("icon in El Gamblador HUD, screenId invite", has_bug(p) and p.evaluate("screenId()") == "bj-invite")
    p.click("#bp-yes"); p.wait_for_timeout(1500); p.click("#bugb"); p.wait_for_timeout(200)
    check("Gamblador frozen (bjPauseT set), no pause menu", p.evaluate("bjPauseT>0") and not p.evaluate("!!document.querySelector('#r')"))
    p.click("#bgx"); p.wait_for_timeout(300); check("Indietro resumes El Gamblador", p.evaluate("bjPauseT===0"))
    check("no console errors (Gamblador)", not errs, errs); ctx.close()
    # 6 professor battle freeze
    ctx, p, errs = page(b); menu(p); dev_click(p, "#mgrob")
    t0 = time.time()
    while time.time() - t0 < 40 and p.evaluate("!(PR&&PR.pb&&PR.pb.ask)"):
        if p.evaluate("!!(PR&&PR.pb&&PR.pb.w&&PR.pb.w.hold==null)"): p.keyboard.press("Enter")
        time.sleep(0.3)
    check("battle command menu reached, icon present", p.evaluate("!!(PR&&PR.pb&&PR.pb.ask)") and has_bug(p) and p.evaluate("screenId()") == "pb-command", p.evaluate("screenId()"))
    p.click("[data-bm='fight']"); p.wait_for_timeout(300); p.click("[data-bv='0']"); p.wait_for_timeout(500)  # a turn starts: sleeps and tweens are running
    n0 = p.evaluate("performance.now()"); p.click("#bugb"); p.wait_for_timeout(200); n1 = p.evaluate("performance.now()"); p.wait_for_timeout(1500); n2 = p.evaluate("performance.now()")
    check("professor: time frozen while popup open", n2 == n1, (n1, n2))
    sl = p.evaluate("PR.sp.size"); hp = p.evaluate("JSON.stringify(PR.pb.d)"); p.wait_for_timeout(1500)
    check("professor: battle state unchanged while frozen", hp == p.evaluate("JSON.stringify(PR.pb.d)"))
    p.click("#bgx"); p.wait_for_timeout(1500); n3 = p.evaluate("performance.now()")
    check("professor: resumes and keeps going", n3 > n2 and p.evaluate("!!PR") and not p.evaluate("PR.dead"))
    check("no console errors (battle)", not errs, errs); ctx.close()
    # 7 offline queue + permission
    ctx, p, errs = page(b); menu(p)
    ctx.set_offline(True); p.wait_for_timeout(200); p.click("#bugb"); p.fill("#bgt", "senza rete"); p.click("#bgk"); p.wait_for_timeout(600)
    q = p.evaluate("JSON.parse(localStorage.getItem('mgs_bugq')||'[]')")
    check("offline: queued with original time in meta.qts", len(q) == 1 and q[0]["text"] == "senza rete" and "qts" in q[0]["meta"] and q[0]["screen"] == "menu-home-roccia", q and q[0]["meta"])
    check("offline toast", "verrà inviata" in p.evaluate("document.body.innerText"))
    check("offline: nothing sent", not p.evaluate("(window.__fbs.bugs||[]).length"))
    ctx.set_offline(False); p.wait_for_timeout(1500)
    check("'online' flushes the queue", p.evaluate("(window.__fbs.bugs||[]).length") == 1 and p.evaluate("JSON.parse(localStorage.getItem('mgs_bugq')||'[]').length") == 0)
    p.evaluate("(()=>{for(let i=0;i<25;i++)bugQueue({text:'q'+i,screen:'menu-home-roccia',version:'x',char:'roccia',ua:'u',meta:{}})})()")
    check("queue capped at 20 (oldest dropped)", p.evaluate("bugQ().length") == 20 and p.evaluate("bugQ()[0].text") == "q5")
    ctx.close()
    ctx, p, errs = page(b, denyBugs=True); menu(p)
    p.click("#bugb"); p.fill("#bgt", "non autorizzato"); p.click("#bgk"); p.wait_for_timeout(600)
    check("permission error: toast, kept in queue, flush stops", "Invio non riuscito" in p.evaluate("document.body.innerText") and p.evaluate("bugQ().length") == 1 and p.evaluate("BUG_NOFLUSH"))
    ctx.close()
    # 8 more screenIds
    ctx, p, errs = page(b); menu(p); dev_click(p, "#mgfa2"); p.wait_for_timeout(500)
    ids = [p.evaluate("screenId()")]; p.wait_for_timeout(3500); ids.append(p.evaluate("screenId()")); p.evaluate("faOver()"); p.wait_for_timeout(300); ids.append(p.evaluate("screenId()"))
    check("screenId Ferma floor 2 (intro, play, game over)", ids == ["fa-intro-floor2", "fa-floor2-play", "fa-game-over"], ids)
    ctx.close()
    # 9 layout at 360x640: icon does not overlap the HUD neighbours
    for vp in ({"width": 360, "height": 640}, {"width": 390, "height": 844}):
        ctx, p, errs = page(b, vp=vp); menu(p)
        ov = []
        def overlap(sel_a, sel_b):
            return p.evaluate("(()=>{const a=document.querySelector('%s'),b=document.querySelector('%s');if(!a||!b)return null;const x=a.getBoundingClientRect(),y=b.getBoundingClientRect();return !(x.right<=y.left||x.left>=y.right||x.bottom<=y.top||x.top>=y.bottom)})()" % (sel_a, sel_b))
        ov.append(("menu bug/devt", overlap("#bugb", "#devt"))); ov.append(("menu bug/title", overlap("#bugb", ".brand h1")))
        p.click("[data-tile=new]"); p.wait_for_timeout(1500)
        ov.append(("maze bug/pause", overlap("#bugb", "#ps"))); ov.append(("maze bug/wv", overlap("#bugb", "#wv"))); ov.append(("maze bug/lives", overlap("#bugb", "#lv")))
        check(f"no overlaps at {vp['width']}x{vp['height']}", not any(v for _, v in ov), ov)
        p.screenshot(path=os.path.join(os.path.expanduser("~"), f"f6_maze_{vp['width']}.png"))
        ctx.close()
    # 10 splash / sad / bye screens (0.4_5)
    for vp in ({"width": 360, "height": 640}, {"width": 390, "height": 844}):
        ctx, p, errs = page(b, vp=vp); p.goto(C.BASE + "index.html"); p.wait_for_selector("#rsi"); p.wait_for_timeout(500)
        check(f"splash: icon visible, tap area, screenId ({vp['width']}x{vp['height']})", has_bug(p) and hit_ok(p) and p.evaluate("screenId()") == "splash-question")
        p.click("#bugb"); p.wait_for_timeout(300)
        check("splash: popup opens over the question", p.evaluate("!!document.querySelector('#bgt')"))
        p.click("#bgx"); p.wait_for_timeout(400)
        check("splash: Indietro brings the question back", p.evaluate("!!document.querySelector('#rsi')") and has_bug(p))
        p.screenshot(path=os.path.join(os.path.expanduser("~"), f"f6_splash_{vp['width']}.png"))
        p.evaluate("go('sad')"); p.wait_for_timeout(300)
        check("sad: icon visible + screenId", has_bug(p) and p.evaluate("screenId()") == "sad-countdown")
        p.click("#bugb"); p.wait_for_timeout(200); n = p.evaluate("sadN"); p.wait_for_timeout(2500)
        check("sad: countdown frozen while the popup is open, popup still there", p.evaluate("sadN") == n and p.evaluate("screen") == "sad" and p.evaluate("!!document.querySelector('#bgt')"), n)
        p.screenshot(path=os.path.join(os.path.expanduser("~"), f"f6_sad_{vp['width']}.png"))
        p.click("#bgx"); p.wait_for_timeout(3600); check("sad: resumes and ends on the splash", p.evaluate("screen") == "splash")
        p.evaluate("go('bye')"); p.wait_for_timeout(300)
        check("bye: icon visible + screenId", has_bug(p) and p.evaluate("screenId()") == "bye-goodbye")
        p.screenshot(path=os.path.join(os.path.expanduser("~"), f"f6_bye_{vp['width']}.png"))
        check("no console errors (splash/sad/bye)", not errs, errs); ctx.close()
    ctx, p, errs = page(b, dev=False); p.goto(C.BASE + "index.html"); p.wait_for_selector("#rsi"); p.wait_for_timeout(400)
    ok1 = not has_bug(p); p.evaluate("go('bye')"); p.wait_for_timeout(200); ok2 = not has_bug(p); p.evaluate("go('sad')"); p.wait_for_timeout(200)
    check("splash/bye/sad: no icon when logged out", ok1 and ok2 and not has_bug(p)); ctx.close()
    b.close()
srv.shutdown()
print(sum(RES), "/", len(RES), "passed"); sys.exit(0 if all(RES) else 1)
