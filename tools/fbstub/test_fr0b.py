#!/usr/bin/env python3
"""0.4.5_28 (FR0b) tests: the two girone hooks (onGironeClear = last pellet, onGironeAdvance = end of the 1.6 s timer), runPayout,
host runs (FA.enc.host, B.host). Golden checks: the same scripted scenario runs on the PREVIOUS build (git show BASE_REF:index.html,
default ecc547d = 0.4.5_27) and on the working tree, and every observation must be identical. Reuses the harness of test_f2b.py.
Run: python tools/fbstub/test_fr0b.py   [BASE_REF=<commit> to compare against another build]"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

BASE_REF = os.environ.get("BASE_REF", "ecc547d")
OLD_PORT = 8794
OLD_DIR = tempfile.mkdtemp(prefix="mgs_old_")
old_html = subprocess.run(["git", "show", BASE_REF + ":index.html"], cwd=ROOT, capture_output=True, check=True).stdout
open(os.path.join(OLD_DIR, "index.html"), "wb").write(old_html)
OLD_BASE = "http://127.0.0.1:%d/" % OLD_PORT
NEW_BASE = BASE

SNAP = "(()=>JSON.stringify({p:S.p,ach:S.ach,quick:S.quick===null}))()"

# one pellet, at the player's own cell, then one update() tick -> the pellet moment; then the timer tick -> the advance moment
PELLET = """(()=>{cancelAnimationFrame(raf);G.state='play';G.t=0;G.invuln=99;
  G.grid=G.grid.map(row=>row.map(ch=>ch==='.'?' ':ch));
  G.grid[G.pl.ty][G.pl.tx]='.';G.pl.prog=0;G.pl.dir=null;G.pl.next=null;
  update(1/60);cancelAnimationFrame(raf);return G.state})()"""
TIMER = "(()=>{cancelAnimationFrame(raf);G.t=0;update(1/60);cancelAnimationFrame(raf);return G.state})()"
NEWRUN = "(()=>{cancelAnimationFrame(raf);G=null;S.quick=null;window.bjAfterClear=function(){};startGame(false,%s);cancelAnimationFrame(raf);return 1})()"
FIN_VIEW = """(()=>({screen,opt:[...document.querySelectorAll('.opt b')].map(b=>b.textContent),girone:(document.querySelector('.disp')||{}).textContent,
  hasAg:!!document.querySelector('#ag'),hasMn:!!document.querySelector('#mn')}))()"""

BJ_AUTO = """(items=>{const ids=items.map(i=>i.id);if(ids.includes('presentation'))return true;if(ids.includes('stand'))return 'stand';if(ids.includes('leave'))return 'leave';return ids[0]})"""
def shoe_js(pc, dc):  # pop order: player1, dealer up, player2, dealer hole
    c = lambda r: "{r:%d,s:0}" % r
    return "(()=>{const s=[];for(let i=0;i<30;i++)s.push({r:2,s:1});s.push(%s,%s,%s,%s);return s})()" % (c(dc[1]), c(pc[1]), c(dc[0]), c(pc[0]))


def scenario(b, base, label):
    """returns {observation: value}; everything here must be identical on the previous build and on the new one"""
    global BASE
    BASE = base
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=False)
    settle(p, 600)
    out = {}
    # ---- a) real girone clear, non-dev run, both moments (g5/sec off so their unlocks fire too; 4->5 then 6->7)
    p.evaluate(NEWRUN % "{}"); p.evaluate("S.p.g5=false;S.p.sec=false;S.ach={prog:{},done:{}};G.stage=4;G.score=1000;0")
    out["a0"] = p.evaluate(SNAP)
    out["a1_state"] = p.evaluate(PELLET); out["a1_stage"] = p.evaluate("G.stage"); out["a1"] = p.evaluate(SNAP)
    out["a2_state"] = p.evaluate(TIMER); out["a2_stage"] = p.evaluate("G.stage"); out["a2"] = p.evaluate(SNAP)
    p.evaluate("G.stage=6;0")
    out["a3_state"] = p.evaluate(PELLET); out["a3_stage"] = p.evaluate("G.stage"); out["a3"] = p.evaluate(SNAP)
    out["a4_state"] = p.evaluate(TIMER); out["a4_stage"] = p.evaluate("G.stage"); out["a4"] = p.evaluate(SNAP)
    out["a4_lives"] = p.evaluate("G.lives")
    # ---- b) quitting (quiet finishRun) inside the 1.6 s clear window
    p.evaluate(NEWRUN % "{}"); p.evaluate("S.ach={prog:{},done:{}};G.stage=4;G.score=1000;0")
    p.evaluate(PELLET); out["b_before"] = p.evaluate(SNAP)
    p.evaluate("finishRun({quiet:true})"); p.wait_for_timeout(300)
    out["b_after"] = p.evaluate(SNAP); out["b_screen"] = p.evaluate("screen")
    # ---- c) finishRun at a fixed girone/score: quiet, then normal (Hardcore run, «Ancora!» keeps hard + game)
    p.evaluate(NEWRUN % "{}"); p.evaluate("S.ach={prog:{},done:{}};G.stage=6;G.score=3000;0")
    p.evaluate("finishRun({quiet:true})"); p.wait_for_timeout(300)
    out["c_quiet"] = p.evaluate(SNAP); out["c_quiet_screen"] = p.evaluate("screen")
    p.evaluate(NEWRUN % "{hard:true}"); p.evaluate("S.ach={prog:{},done:{}};G.stage=6;G.score=3000;S.quick={x:1};0")
    p.evaluate("finishRun()"); p.wait_for_timeout(300)
    out["c_norm"] = p.evaluate(SNAP); out["c_norm_view"] = p.evaluate(FIN_VIEW)
    p.evaluate("document.querySelector('#ag').click()"); p.wait_for_timeout(300)
    out["c_again"] = p.evaluate("({hard:G.hard,lives:G.lives,game:G.game,stage:G.stage,score:G.score})")
    # ---- h) a devJump run clearing a girone writes no progress
    p.evaluate("(()=>{cancelAnimationFrame(raf);G=null;window.bjAfterClear=function(){};devJump(6);cancelAnimationFrame(raf);S.p.g5=false;S.p.sec=false;0})()")
    out["h0"] = p.evaluate(SNAP)
    p.evaluate(PELLET); out["h1"] = p.evaluate(SNAP); p.evaluate(TIMER); out["h2"] = p.evaluate(SNAP); out["h_stage"] = p.evaluate("G.stage")
    # ---- d) Ferma encounter win: host score after the pay-out
    p.evaluate(NEWRUN % "{}"); p.evaluate("S.ach={prog:{},done:{}};G.stage=5;G.score=1000;S.p.fa.enc=0;0")
    p.evaluate("(()=>{G.state='mini';faInvite({forced:true,dev:false,n:1,mult5:false});0})()")
    p.wait_for_selector("#fai-yes", timeout=5000); p.click("#fai-yes")
    p.wait_for_function("FA&&FA.enc&&FA.state", timeout=15000)
    p.evaluate("cancelAnimationFrame(FA.raf)")
    out["d_before"] = p.evaluate("G.score")
    p.evaluate("FA.cnt={base:300,bonus:50};FA.level=0;FA.paid=false;faEncPay()")
    out["d_after"] = p.evaluate("G.score"); out["d_paid"] = p.evaluate("FA.paid")
    out["d_host"] = p.evaluate("typeof FA.enc.host==='object'&&FA.enc.host===G.run") if label == "new" else None
    p.evaluate("FA.paid=false;FA.enc.dev=true;faEncPay();FA.enc.dev=false")  # a dev encounter pays nothing
    out["d_dev_after"] = p.evaluate("G.score")
    # ---- e) El Gamblador, real hands through the auto hook: a win, then a loss (fixed shoes)
    for name, pc, dc in (("win", (10, 10), (10, 7)), ("loss", (10, 6), (10, 9))):
        p.evaluate(NEWRUN % "{}"); p.evaluate("S.ach={prog:{},done:{}};G.stage=5;G.score=1000;S.p.gam.visits=0;window.bjNewShoe=()=>%s;0" % shoe_js(pc, dc))
        p.evaluate("(()=>{G.state='mini';startGamblador({run:true,auto:%s});0})()" % BJ_AUTO)
        p.wait_for_function("typeof B!=='undefined'&&B&&B.run", timeout=15000)
        out["e_%s_price" % name] = p.evaluate("B.price")
        out["e_%s_start" % name] = p.evaluate("bjScore()")
        if label == "new":
            out["e_host"] = p.evaluate("B.host===G.run")
        p.wait_for_function("screen==='game'", timeout=90000)
        out["e_%s_score" % name] = p.evaluate("G.score"); out["e_%s_visits" % name] = p.evaluate("S.p.gam.visits")
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

    # ---------------- golden comparison, observation by observation
    groups = [("a) girone clear, pellet moment: state, G.stage and S.p/S.ach diff identical", ["a0", "a1_state", "a1_stage", "a1"]),
              ("a) girone clear, timer moment: state, G.stage (+1) and S.p/S.ach diff identical", ["a2_state", "a2_stage", "a2"]),
              ("a) girone 6->7 (sec unlock) at both moments, lives refill identical", ["a3_state", "a3_stage", "a3", "a4_state", "a4_stage", "a4", "a4_lives"]),
              ("b) quitting inside the 1.6 s clear window: identical gironi credit / sordi / XP / achievements", ["b_before", "b_after", "b_screen"]),
              ("c) finishRun quiet: identical sordi/XP/achievements/S.quick", ["c_quiet", "c_quiet_screen"]),
              ("c) finishRun normal (Hardcore): identical result screen, sordi/XP/achievements/S.quick; «Ancora!» restarts the same way", ["c_norm", "c_norm_view", "c_again"]),
              ("h) devJump run clearing a girone: identical (nothing written)", ["h0", "h1", "h2", "h_stage"]),
              ("d) Ferma encounter win: identical host score after the pay-out (and a dev encounter pays nothing)", ["d_before", "d_after", "d_paid", "d_dev_after"]),
              ("e) El Gamblador win: identical buy-in, start score, final score, visits", ["e_win_price", "e_win_start", "e_win_score", "e_win_visits"]),
              ("e) El Gamblador loss: identical buy-in, start score, final score, visits", ["e_loss_price", "e_loss_start", "e_loss_score", "e_loss_visits"])]
    for name, keys in groups:
        diff = {k: (old.get(k), new.get(k)) for k in keys if old.get(k) != new.get(k)}
        check(name, not diff, {k: str(v)[:160] for k, v in diff.items()} if diff else {k: str(old.get(k))[:60] for k in keys[:3]})
    # the scenarios really did something (guards against a golden comparison of two no-ops)
    a0, a1, a2 = (json.loads(new[k]) for k in ("a0", "a1", "a2"))
    check("sanity: the pellet moment credits one girone (gir +1) and the timer moment does not", a1["p"]["ch"]["roccia"]["gir"] == a0["p"]["ch"]["roccia"]["gir"] + 1 == a2["p"]["ch"]["roccia"]["gir"], (a0["p"]["ch"]["roccia"]["gir"], a1["p"]["ch"]["roccia"]["gir"], a2["p"]["ch"]["roccia"]["gir"]))
    check("sanity: G.stage moves only at the timer moment (4 -> 4 -> 5), g5 unlocks then", (new["a1_stage"], new["a2_stage"]) == (4, 5) and a1["p"]["g5"] is False and a2["p"]["g5"] is True, (new["a1_stage"], new["a2_stage"], a2["p"]["g5"]))
    check("sanity: the «stage» achievement counted the OLD girone at the pellet moment (progress 4)", 4 in json.loads(new["a1"])["ach"]["prog"].values(), json.loads(new["a1"])["ach"]["prog"])
    check("sanity: a sec unlock happened at girone 7 and the maze kept its lives refill", json.loads(new["a4"])["p"]["sec"] is True and new["a4_lives"] == 3, (json.loads(new["a4"])["p"].get("sec"), new["a4_lives"]))
    check("sanity: Ferma pay-out added 350 to the host score", new["d_after"] - new["d_before"] == 350 and new["d_dev_after"] == new["d_after"], (new["d_before"], new["d_after"]))
    check("d) new build: FA.enc.host === G.run", new["d_host"] is True, new["d_host"])
    check("sanity: El Gamblador hands moved the score (win up, loss down) and the table ended back in the maze",
          new["e_win_score"] > new["e_win_start"] and new["e_loss_score"] < new["e_loss_start"], (new["e_win_start"], new["e_win_score"], new["e_loss_start"], new["e_loss_score"]))
    check("e) new build: B.host === G.run", new.get("e_host") is True, new.get("e_host"))
    check("no console errors (old build)", not old["errs"], old["errs"])
    check("no console errors (new build)", not new["errs"], new["errs"])

    # ---------------- f) hooks with no maze G at all: plain non-dev run object
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=False)
    settle(p, 600)
    p.evaluate("(()=>{cancelAnimationFrame(raf);G=null;S.ach={prog:{},done:{}};S.p.g5=false;S.p.sec=false;go('menu');0})()"); p.wait_for_timeout(300)
    r = p.evaluate("""(()=>{
      const run=mkRun({girone:4,score:500}),gir=()=>S.p.ch.roccia.gir,g0=gir(),out={g0};
      onGironeClear(run);out.g1=gir();out.girone1=run.girone;onGironeClear(run);out.g2=gir();
      onGironeAdvance(run);out.girone2=run.girone;out.g5a=S.p.g5;onGironeAdvance(run);out.girone3=run.girone;
      out.g=G;out.prog=JSON.stringify(S.ach.prog);return out})()""")
    check("f) G=null, non-dev run: career gironi +1 per onGironeClear call (twice -> +2), run.girone untouched by it",
          r["g1"] == r["g0"] + 1 and r["g2"] == r["g0"] + 2 and r["girone1"] == 4 and r["g"] is None, r)
    check("f) G=null: onGironeAdvance girone +1 per call (twice -> +2), g5 unlocks at 5", r["girone2"] == 5 and r["girone3"] == 6 and r["g5a"] is True, r)
    check("f) the «stage» achievement counted with the run's girone (n = 4)", 4 in json.loads(r["prog"]).values(), r["prog"])
    check("no console errors (f)", not errs, errs)
    # ---------------- g) a dev run object: no career gironi, no achievement, no g5/sec
    before = p.evaluate(SNAP)
    r = p.evaluate("""(()=>{const run=mkRun({girone:6,score:500,dev:true});onGironeClear(run);onGironeClear(run);onGironeAdvance(run);onGironeAdvance(run);return{girone:run.girone,G:G}})()""")
    after = p.evaluate(SNAP)
    check("g) G=null, dev run: onGironeClear x2 + onGironeAdvance x2 write no career gironi, no achievement, no g5/sec", before == after and r["G"] is None, r)
    check("g) the dev run's own girone still advances (+1 per advance call)", r["girone"] == 8, r)
    check("no console errors (g)", not errs, errs)
    # ---------------- runPayout on a plain run with no maze G: pays like finishRun would (sordi/XP), clears the quicksave
    r = p.evaluate("""(()=>{S.quick={x:1};const s0=S.p.sordi,run=mkRun({girone:6,score:3000}),o=runPayout(run);return{gain:o.gain,paid:S.p.sordi-s0,quick:S.quick,stage:o.stage,G:G}})()""")
    check("runPayout(run) with G=null: sordi credited >= gain (achievement rewards may add to it), S.quick cleared, stage = run.girone", r["gain"] > 0 and r["paid"] >= r["gain"] and r["quick"] is None and r["stage"] == 6, r)
    check("no console errors (runPayout)", not errs, errs)
    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
