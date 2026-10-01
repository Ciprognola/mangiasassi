#!/usr/bin/env python3
"""0.4.5_37 (FR2a) tests: run-agnostic El Gamblador/interlude entry+exit (RUN_HOLD/RUN_BACK), dev "Forza El Gamblador".
Golden checks a)-c): the same scripted scenario runs on the PREVIOUS build (git show BASE_REF:index.html, default
3ab6d8d = 0.4.5_36) and on the working tree, and every observation must be identical. Reuses the harness of test_f2b.py
(golden-comparison plumbing borrowed from test_fr0b.py). Run: python tools/fbstub/test_fr2a.py   [BASE_REF=<commit>]"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

BASE_REF = os.environ.get("BASE_REF", "3ab6d8d")
OLD_PORT = 8795
OLD_DIR = tempfile.mkdtemp(prefix="mgs_old_fr2a_")
old_html = subprocess.run(["git", "show", BASE_REF + ":index.html"], cwd=ROOT, capture_output=True, check=True).stdout
open(os.path.join(OLD_DIR, "index.html"), "wb").write(old_html)
OLD_BASE = "http://127.0.0.1:%d/" % OLD_PORT
NEW_BASE = BASE

NEWRUN = "(()=>{cancelAnimationFrame(raf);G=null;S.quick=null;startGame(false,%s);cancelAnimationFrame(raf);return 1})()"  # NOTE: unlike test_fr0b/test_s1's own NEWRUN, this one leaves bjAfterClear real -- this file tests it directly
PELLET = """(()=>{cancelAnimationFrame(raf);G.state='play';G.t=0;G.invuln=99;
  G.grid=G.grid.map(row=>row.map(ch=>ch==='.'?' ':ch));
  G.grid[G.pl.ty][G.pl.tx]='.';G.pl.prog=0;G.pl.dir=null;G.pl.next=null;
  update(1/60);cancelAnimationFrame(raf);return G.state})()"""
TIMER = "(()=>{cancelAnimationFrame(raf);G.t=0;update(1/60);cancelAnimationFrame(raf);return G.state})()"

BJ_AUTO = """(items=>{const ids=items.map(i=>i.id);if(ids.includes('presentation'))return true;if(ids.includes('stand'))return 'stand';if(ids.includes('leave'))return 'leave';return ids[0]})"""
def shoe_js(pc, dc):  # pop order: player1, dealer up, player2, dealer hole
    c = lambda r: "{r:%d,s:0}" % r
    return "(()=>{const s=[];for(let i=0;i<30;i++)s.push({r:2,s:1});s.push(%s,%s,%s,%s);return s})()" % (c(dc[1]), c(pc[1]), c(dc[0]), c(pc[0]))


def scenario(b, base, label):
    """returns {observation: value}; a)-c) must be identical on the previous build and on the new one"""
    global BASE
    BASE = base
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p, 600)
    out = {}
    # ---- a) girone-5 advance -> El Gamblador (mandatory), a real hand through the auto hook, bjExit restores the maze
    p.evaluate(NEWRUN % "{}")
    p.evaluate("S.ach={prog:{},done:{}};S.p.g5=false;S.p.sec=false;S.p.gam.visits=0;G.stage=4;G.score=1000;S.p.fa.enc=5;window.bjNewShoe=()=>%s;0" % shoe_js((10, 10), (10, 7)))
    # bjAfterClear's own mandatory-girone-5 branch calls startGamblador({run:true,...}) with no `auto` -- wrap it
    # (global-scope lookup: a classic-script top-level function IS the window property, so this really replaces
    # what bjAfterClear's unqualified call resolves to) so the real hand still auto-plays
    p.evaluate("(()=>{const orig=startGamblador;window.startGamblador=o=>{o=o||{};o.auto=%s;return orig(o)}})()" % BJ_AUTO)
    out["a_pellet_state"] = p.evaluate(PELLET)
    out["a_timer_state"] = p.evaluate(TIMER)
    p.wait_for_function("typeof B!=='undefined'&&B&&B.run", timeout=15000)
    out["a_price"] = p.evaluate("B.price")
    out["a_start_score"] = p.evaluate("bjScore()")
    if label == "new":
        out["a_host_is_run"] = p.evaluate("B.host===G.run")
    p.wait_for_function("screen==='game'", timeout=90000)
    out["a_final_screen"] = p.evaluate("screen")
    out["a_final_state"] = p.evaluate("G.state")
    out["a_final_score"] = p.evaluate("G.score")
    out["a_final_stage"] = p.evaluate("G.stage")
    out["a_visits"] = p.evaluate("S.p.gam.visits")
    # ---- b) miniInterlude at girone 10, no encounter: title + Avanti restore
    p.evaluate(NEWRUN % "{}")
    p.evaluate("S.ach={prog:{},done:{}};S.p.fa.enc=5;Math.random=()=>0.99;G.stage=9;G.score=500;0")
    out["b_pellet_state"] = p.evaluate(PELLET)
    out["b_timer_state"] = p.evaluate(TIMER)
    out["b_title"] = p.evaluate("(document.querySelector('#modal h3')||{}).textContent||''")
    out["b_mid_state"] = p.evaluate("G.state")
    p.evaluate("document.querySelector('#mgo').click()")
    p.wait_for_timeout(200)
    out["b_after_state"] = p.evaluate("G.state")
    out["b_after_screen"] = p.evaluate("screen")
    out["b_stage"] = p.evaluate("G.stage")
    # ---- c) random (non-mandatory) Ferma invite beats a non-firing El Gamblador roll; faResume path (Non ora) unchanged
    # (the 0.4.5_36 BASE_REF uses a 2-ply decision at girone>5: El Gamblador's own 15% roll, then Ferma's 15% roll --
    # a deterministic sequence [miss, hit] exercises faInvite's non-forced shape, which the girone-8-mandatory case can't:
    # once forced, faInvite never renders "Non ora" at all. The sequence is wired to bjAfterClear's own call, not
    # Math.random globally -- pickMap/resetActors run earlier in the same "clear" tick and consume rolls of their own)
    p.evaluate(NEWRUN % "{}")
    p.evaluate("""S.ach={prog:{},done:{}};S.p.fa.enc=3;G.stage=5;G.score=500;
      (()=>{const orig=bjAfterClear;window.bjAfterClear=run=>{const seq=[0.99,0.01];let n=0;Math.random=()=>n<seq.length?seq[n++]:0.5;return orig(run)}})();0""")
    out["c_pellet_state"] = p.evaluate(PELLET)
    out["c_timer_state"] = p.evaluate(TIMER)
    out["c_stage_after"] = p.evaluate("G.stage")
    out["c_invite_shown"] = p.evaluate("typeof faInvShow!=='undefined'&&faInvShow")
    out["c_modal_has_fermalo"] = p.evaluate("!!document.querySelector('#fai-yes')")
    out["c_modal_has_nonora"] = p.evaluate("!!document.querySelector('#fai-no')")
    p.evaluate("document.querySelector('#fai-no').click()")
    p.wait_for_timeout(200)
    out["c_after_state"] = p.evaluate("G.state")
    out["c_after_screen"] = p.evaluate("screen")
    out["errs"] = errs
    ctx.close()
    return out


with sync_playwright() as pw:
    srv = serve()
    import functools, http.server, threading
    class OH(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    osrv = http.server.ThreadingHTTPServer(("127.0.0.1", OLD_PORT), functools.partial(OH, directory=OLD_DIR))
    threading.Thread(target=osrv.serve_forever, daemon=True).start()
    b = launch_browser(pw)
    old = scenario(b, OLD_BASE, "old")
    new = scenario(b, NEW_BASE, "new")
    BASE = NEW_BASE

    groups = [
        ("a) girone-5 advance -> El Gamblador starts and plays out identically (price, start score, final score/stage, visits)",
         ["a_pellet_state", "a_timer_state", "a_price", "a_start_score", "a_final_screen", "a_final_state", "a_final_score", "a_final_stage", "a_visits"]),
        ("b) miniInterlude at girone 10 (no encounter): title + Avanti restore identical", ["b_pellet_state", "b_timer_state", "b_title", "b_mid_state", "b_after_state", "b_after_screen", "b_stage"]),
        ("c) a non-forced Ferma invite beats a missed El Gamblador roll; faResume (Non ora) restore identical", ["c_pellet_state", "c_timer_state", "c_stage_after", "c_invite_shown", "c_modal_has_fermalo", "c_modal_has_nonora", "c_after_state", "c_after_screen"]),
    ]
    for name, keys in groups:
        diff = {k: (old.get(k), new.get(k)) for k in keys if old.get(k) != new.get(k)}
        check(name, not diff, {k: str(v)[:160] for k, v in diff.items()} if diff else {k: str(old.get(k))[:60] for k in keys[:3]})
    check("a) new build: B.host === G.run", new.get("a_host_is_run") is True, new.get("a_host_is_run"))
    check("a) sanity: El Gamblador actually played (score moved from the buy-in start)", new["a_final_score"] != new["a_start_score"], (new["a_start_score"], new["a_final_score"]))
    check("b) sanity: the interlude card showed girone 10", "10" in new["b_title"], new["b_title"])
    check("c) sanity: the non-forced invite really showed with both buttons (faInvShow true, #fai-yes and #fai-no present)", new["c_invite_shown"] is True and new["c_modal_has_fermalo"] and new["c_modal_has_nonora"], (new["c_invite_shown"], new["c_modal_has_fermalo"], new["c_modal_has_nonora"]))
    check("no console errors (old build)", not old["errs"], old["errs"])
    check("no console errors (new build)", not new["errs"], new["errs"])

    # ---------------- d) startGamblador({run:true, host:<hand-built run>}) with G=null does not throw
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p, 600)
    r = p.evaluate("""(()=>{
      cancelAnimationFrame(raf);G=null;
      const hostRun=mkRun({girone:5,score:5000,game:'maze',dev:true});
      try{startGamblador({run:true,host:hostRun});return {threw:false}}
      catch(e){return {threw:true,msg:String(e)}}
    })()""")
    check("d) startGamblador({run:true,host}) with G=null does not throw", r["threw"] is False, r)
    p.wait_for_function("typeof B!=='undefined'&&B&&B.host&&B.host.girone===5", timeout=15000)
    check("d) B.host is the explicit hand-built run (girone 5), not G.run", p.evaluate("B.host.girone"), 5)
    check("no console errors (d)", not errs, errs)
    ctx.close()

    # ---------------- e) dev "Forza El Gamblador": fires outside normal odds, consumed once, never touches S.p.gam; gate-fail -> toast, no table
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p, 600)
    p.evaluate(NEWRUN % "{dev:true}")
    p.evaluate("window.bjNewShoe=()=>%s" % shoe_js((10, 10), (10, 7)))
    p.evaluate("(()=>{const orig=startGamblador;window.startGamblador=o=>{o=o||{};o.auto=%s;return orig(o)}})()" % BJ_AUTO)
    e1 = p.evaluate("""(()=>{
      cancelAnimationFrame(raf);
      S.p.fa.enc=5;S.p.gam.visits=0;G.stage=3;G.score=99999;G.dev=true;Math.random=()=>0.99;
      GAM_FORCE.on=true;
      bjAfterClear(G.run);
      return {gamForceAfter:GAM_FORCE.on};
    })()""")
    p.wait_for_function("typeof B!=='undefined'&&B&&B.run", timeout=15000)
    e1["bHostDev"] = p.evaluate("B.host.dev")
    e1["bHostGirone"] = p.evaluate("B.host.girone")
    e1["visitsAfterStart"] = p.evaluate("S.p.gam.visits")
    p.wait_for_function("screen==='game'", timeout=90000)
    e1["visitsAfterPlay"] = p.evaluate("S.p.gam.visits")
    check("e) Forza El Gamblador fires at girone 3 (outside the 5/15% odds) in a dev run", e1["gamForceAfter"] is False and e1["bHostGirone"] == 3 and e1["bHostDev"] is True, e1)
    check("e) S.p.gam.visits never touched by a dev-run El Gamblador table (start or finished)", e1["visitsAfterStart"] == 0 and e1["visitsAfterPlay"] == 0, e1)

    p.evaluate(NEWRUN % "{dev:true}")
    e2 = p.evaluate("""(()=>{
      cancelAnimationFrame(raf);
      S.p.fa.enc=5;S.p.gam.visits=0;G.stage=3;G.score=0;G.dev=true;Math.random=()=>0.99;
      window.__toasted=null;const o=toast;window.toast=m=>{window.__toasted=m;o(m)};
      GAM_FORCE.on=true;
      bjAfterClear(G.run);
      return {gamForceAfter:GAM_FORCE.on,toasted:window.__toasted,screen,Bexists:typeof B!=='undefined'&&!!B};
    })()""")
    check("e) Forza El Gamblador still respects bjPrice>=50: gate fails (score 0) -> toast, flag consumed, no table", e2["gamForceAfter"] is False and e2["toasted"] == "El Gamblador: punti insufficienti" and e2["Bexists"] is False and e2["screen"] == "game", e2)
    check("no console errors (e)", not errs, errs)
    ctx.close()

    # ---------------- f) RUN_BACK/RUN_HOLD have exactly the "maze" key
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p, 600)
    r = p.evaluate("({hold:Object.keys(RUN_HOLD),back:Object.keys(RUN_BACK)})")
    check("f) RUN_HOLD has exactly the \"maze\" + \"ferma\" keys (\"ferma\" added by FR2b, 0.4.5_38)", r["hold"] == ["maze", "ferma"], r)
    check("f) RUN_BACK has exactly the \"maze\" + \"ferma\" keys (\"ferma\" added by FR2b, 0.4.5_38)", r["back"] == ["maze", "ferma"], r)
    check("no console errors (f)", not errs, errs)
    ctx.close()

print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
