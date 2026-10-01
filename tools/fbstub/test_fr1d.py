#!/usr/bin/env python3
"""0.4.5_35 (FR1d) tests: the floor-3 bolt layout sequence per difficulty (FA_RUN.diff[id].bolts, indexed by the
real discrete loop rather than the continuous e, since floor 3 only comes up every 3rd girone) and Algidone's
anger (an upward ladder climb starts a throw-wait outburst; the girder just below him makes him permanently
angry and slightly slower; own tuning table per mode, §10.0). Practice, the maze encounter and the maze itself
are golden-compared against BASE_REF (default cfae3b9 = 0.4.5_34). Reuses the harness of test_f2b.py.
Run: python tools/fbstub/test_fr1d.py"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

BASE_REF = os.environ.get("BASE_REF", "cfae3b9")
OLD_PORT = 8800
OLD_DIR = tempfile.mkdtemp(prefix="mgs_old_")
open(os.path.join(OLD_DIR, "index.html"), "wb").write(subprocess.run(["git", "show", BASE_REF + ":index.html"], cwd=ROOT, capture_output=True, check=True).stdout)
NEW_BASE, OLD_BASE = BASE, "http://127.0.0.1:%d/" % OLD_PORT
import functools, http.server, threading
class OH(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
osrv = http.server.ThreadingHTTPServer(("127.0.0.1", OLD_PORT), functools.partial(OH, directory=OLD_DIR))
threading.Thread(target=osrv.serve_forever, daemon=True).start()

SEED = """(a=>{window.__s=a;Math.random=()=>{let t=(window.__s=window.__s+0x6D2B79F5|0);t=Math.imul(t^t>>>15,1|t);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}})(%d)"""
FREEZE = "(()=>{window.__raf=window.__raf||window.requestAnimationFrame;window.requestAnimationFrame=()=>0;if(FA)cancelAnimationFrame(FA.raf);if(typeof raf!=='undefined')cancelAnimationFrame(raf);0})()"
UNF = "if(window.__raf)window.requestAnimationFrame=window.__raf;"
QUIET = "(()=>{faIntroEnd();Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;0})()"
STEP = "(n=>{for(let i=0;i<n;i++)faStep(1/60)})"
# positions the player at a ladder's bottom/top and walks the climb to completion through the real game code
CLIMB = """(dir)=>{
  const l=FA.lv.ladders[0]; // x:210, gBot:0, gTop:1 on every floor -- not broken, same arrangement everywhere
  const fromGi=dir==='u'?l.gBot:l.gTop, toGi=dir==='u'?l.gTop:l.gBot;
  FA.p.gi=fromGi;FA.p.x=l.x;FA.p.onGround=true;FA.p.climbing=null;FA.p.airY=null;FA.p.vy=0;FA.p.y=faGirderY(FA.lv.girders[fromGi],l.x);
  FA_TOUCH.u=0;FA_TOUCH.d=0;FA_TOUCH[dir]=1;
  for(let i=0;i<10&&FA.p.climbing===null;i++)faStep(1/600); // enter the ladder
  for(let i=0;i<4000&&FA.p.climbing!==null;i++)faStep(1/600); // climb to completion (fine steps: climb speed is slow, avoid overshoot)
  FA_TOUCH[dir]=0;
  return {gi:FA.p.gi,reached:FA.p.gi===toGi,climbing:!!FA.p.climbing};
}"""
FIXED_WAIT = "Object.assign(FA.cfg,{throwMin:1,throwMax:1});FA.dm.pause=1;0"  # deterministic faThrowWait(): base always 1


def to_menu(p):
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}if(typeof raf!=='undefined')cancelAnimationFrame(raf);G=null;S.quick=null;persist();go('menu')})()")
    p.wait_for_timeout(300)


def start_dev_run(p, girone=1, diff=None):
    extra = (",diff:'%s'" % diff) if diff else ""
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}G=null;S.quick=null;go('menu');startFermaRun({girone:%d,dev:true%s});0})()" % (girone, extra))
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_practice(p):
    to_menu(p)
    p.evaluate("startFerma({test:true})")
    p.wait_for_function("FA&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_practice_floor3(p):
    to_menu(p)
    p.evaluate("startFerma({test:true,level:2})")
    p.wait_for_function("FA&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_enc(p, n=2, level=None):
    to_menu(p)
    extra = (",level:%d" % level) if level is not None else ""
    p.evaluate("startFerma({test:true,encounter:%d%s})" % (n, extra))
    p.wait_for_function("FA&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=True)
    settle(p, 600)

    # ================= Part A: floor-3 layout sequence per difficulty
    a_data = p.evaluate("({L1:FA_BOLTS[0],L2:FA_BOLTS[1],L3:FA_BOLTS[2]})")
    GIRONI_A = [3, 6, 9, 12, 15]
    WANT_A = {"easy": [0, 0, 1, 2, 2], "medium": [0, 1, 2, 2, 2], "hard": [1, 2, 2, 2, 2]}
    for d, want in WANT_A.items():
        for g, li in zip(GIRONI_A, want):
            start_dev_run(p, g, diff=d)
            bolts = p.evaluate("({level:FA.level,bolts:FA.bolts.map(b=>({g:b.g,x:b.x}))})")
            check("a) %s girone %d: floor index %d, bolt layout L%d" % (d, g, bolts["level"], li + 1),
                  bolts["level"] == 2 and bolts["bolts"] == a_data[["L1", "L2", "L3"][li]], bolts)
    start_practice_floor3(p)
    check("a) practice floor 3: always L1", p.evaluate("FA.bolts.map(b=>({g:b.g,x:b.x}))") == a_data["L1"])
    start_enc(p, 2, level=2)
    check("a) encounter floor 3: always L1", p.evaluate("FA.bolts.map(b=>({g:b.g,x:b.x}))") == a_data["L1"])
    check("no console errors (A)", not errs, errs)

    # ================= b) upward climb starts the outburst; downward doesn't; a 2nd climb mid-burst restarts it
    start_dev_run(p, 1); p.evaluate(QUIET); p.evaluate(FIXED_WAIT)
    up1 = p.evaluate(CLIMB, "u")
    check("b) upward climb reaches the top girder", up1["reached"] and not up1["climbing"], up1)
    r1 = p.evaluate("({outT:FA.ang.outT,pose:faAlgFrame().key})")
    check("b) upward climb starts the outburst and the angry pose", 3.0 < r1["outT"] <= 3.5 and r1["pose"].startswith("alg_angry"), r1)
    w1 = p.evaluate("faThrowWait()")
    check("b) throw wait during the outburst is base x outK (1 x .5 = .5)", abs(w1 - 0.5) < 1e-9, w1)
    p.evaluate(STEP + "(1*60)")  # 1s in: still within the 3.5s outburst
    mid = p.evaluate("({outT:FA.ang.outT,w:faThrowWait()})")
    check("b) 1s in: still angry, wait still scaled", mid["outT"] > 2.0 and abs(mid["w"] - 0.5) < 1e-9, mid)
    # a second upward climb mid-burst restarts outDur
    p.evaluate("FA.ang.outT=1.2;0")
    up2 = p.evaluate(CLIMB, "u")
    r2 = p.evaluate("FA.ang.outT")
    check("b) a second climb mid-burst restarts outDur (back near 3.5, not continuing from 1.2)", 3.0 < r2 <= 3.5, r2)
    p.evaluate(STEP + "(" + str(int(3.6 * 60)) + ")")
    after = p.evaluate("({outT:FA.ang.outT,w:faThrowWait()})")
    check("b) after outDur elapses: back to the base wait, no outburst", after["outT"] == 0 and abs(after["w"] - 1) < 1e-9, after)
    # downward climb never triggers
    p.evaluate("FA.ang.outT=0;0")
    down1 = p.evaluate(CLIMB, "d")
    check("b) downward climb reaches the bottom girder, no outburst", down1["reached"] and p.evaluate("FA.ang.outT") == 0, (down1, p.evaluate("FA.ang.outT")))
    check("no console errors (b)", not errs, errs)

    # ================= c) a long already-running wait is re-drawn at the outburst rate the moment it starts
    start_dev_run(p, 1); p.evaluate(QUIET); p.evaluate(FIXED_WAIT)
    p.evaluate("FA.alg.state='idle';FA.alg.wait=100;FA.ang.outT=0;0")
    p.evaluate(CLIMB, "u")  # triggers the outburst via the real climb path
    p.evaluate(STEP + "(1)")  # one tick for faAlgStep to see the fresh outburst
    waitNow = p.evaluate("FA.alg.wait")
    check("c) a 100s wait gets redrawn to <= the outburst max (1 x .5 = .5) the moment the burst starts", waitNow <= 0.5 + 1e-9, waitNow)
    check("no console errors (c)", not errs, errs)

    # ================= d) last girder: topK, constant angry pose, ends on leaving
    start_dev_run(p, 1); p.evaluate(QUIET); p.evaluate(FIXED_WAIT)
    lastGi = p.evaluate("FA.lv.girders.length-2")
    p.evaluate("(gi)=>{FA.p.gi=gi;FA.p.onGround=true;FA.p.climbing=null;0}", lastGi)
    p.evaluate(STEP + "(1)")
    r = p.evaluate("({onLast:FA.ang.onLast,w:faThrowWait(),pose1:faAlgFrame().key})")
    p.evaluate(STEP + "(20)")
    r2d = p.evaluate("faAlgFrame().key")
    check("d) on the last girder: onLast true, wait x topK (1 x .65 = .65), angry pose", r["onLast"] and abs(r["w"] - 0.65) < 1e-9 and r["pose1"].startswith("alg_angry") and r2d.startswith("alg_angry"), (r, r2d))
    p.evaluate("FA.p.gi=0;0"); p.evaluate(STEP + "(1)")
    check("d) leaving the last girder ends it", p.evaluate("FA.ang.onLast") is False, p.evaluate("FA.ang.onLast"))
    check("no console errors (d)", not errs, errs)

    # ================= e) bar under 25%: still eats on schedule, low-stock beep still fires
    start_dev_run(p, 1); p.evaluate(QUIET)
    p.evaluate("window.__snd=[];window.__orig=playSnd;playSnd=(s,c)=>{window.__snd.push(s);return window.__orig(s,c)}")
    r = p.evaluate("""(()=>{FA.bar.left=1;FA.bar.N=12;FA.bar.shown=1/12;FA.bar.pending=true;FA.alg.state='idle';FA.alg.wait=0;FA.inv=1e9;
      faStep(1/60);const bitState=FA.alg.state;for(let i=0;i<180;i++)faStep(1/60);
      return {bitState,lowSnd:window.__snd.includes('low'),stockPct:FA.stock/FA.lv.stock}})()""")
    p.evaluate("playSnd=window.__orig;0")
    check("e) bar under 25%: the scheduled bite still happens (Algidone eats), low-stock beep still fires", r["bitState"] == "eat" and r["lowSnd"] and r["stockPct"] < 0.25, r)
    check("no console errors (e)", not errs, errs)

    # ================= f) death clears both anger states
    start_dev_run(p, 1); p.evaluate(QUIET)
    p.evaluate("FA.ang.outT=2.5;FA.ang.onLast=true;FA.inv=0;0")
    p.evaluate("faDie('x',true)")
    p.evaluate("for(let i=0;i<200&&FA.state==='dying';i++)faStep(1/60)")
    r = p.evaluate("({outT:FA.ang.outT,onLast:FA.ang.onLast,state:FA.state})")
    check("f) death/respawn clears the outburst and the last-girder state", r == {"outT": 0, "onLast": False, "state": "play"}, r)
    check("no console errors (f)", not errs, errs)

    # ================= g) FA_PRAC.anger / FA_RUN.anger / FA_ENC.anger are independent objects
    r0 = p.evaluate("({run:FA_RUN.anger.outK,prac:FA_PRAC.anger.outK,enc:FA_ENC.anger.outK})")
    p.evaluate("FA_PRAC.anger.outK=0.1;0")
    r1g = p.evaluate("({run:FA_RUN.anger.outK,prac:FA_PRAC.anger.outK,enc:FA_ENC.anger.outK})")
    check("g) mutating FA_PRAC.anger leaves FA_RUN.anger/FA_ENC.anger unchanged", r1g["run"] == r0["run"] and r1g["enc"] == r0["enc"] and r1g["prac"] == 0.1, (r0, r1g))
    p.evaluate("FA_PRAC.anger.outK=%r;FA_RUN.anger.outK=0.2;0" % r0["prac"])
    r2g = p.evaluate("({run:FA_RUN.anger.outK,prac:FA_PRAC.anger.outK,enc:FA_ENC.anger.outK})")
    check("g) ...and the other way round", r2g["prac"] == r0["prac"] and r2g["enc"] == r0["enc"] and r2g["run"] == 0.2, (r0, r2g))
    p.evaluate("FA_RUN.anger.outK=%r;0" % r0["run"])
    check("no console errors (g)", not errs, errs)
    ctx.close()

    # ================= h) no climb, off the last girder: throw waits match BASE_REF; the maze untouched
    SCEN_RUN = """(async()=>{
      __SEED__;window.requestAnimationFrame=()=>0;const out={};
      if(FA){FA.dead=true;FA=null}G=null;S.quick=null;go('menu');
      await startFermaRun({girone:1,dev:true});cancelAnimationFrame(FA.raf);
      faIntroEnd();FA.inv=1e9;const waits=[];let prevWait=FA.alg.wait;
      for(let i=0;i<60*120;i++){faStep(1/60);if(FA.alg.wait!==prevWait&&FA.alg.state==='idle'){waits.push(+FA.alg.wait.toFixed(4));prevWait=FA.alg.wait}}
      out.waits=waits;out.layout=FA.bolts.map(b=>({g:b.g,x:b.x}));
      return JSON.stringify(out)})""".replace("__SEED__", SEED % 2468)
    res = {}
    for label, base_url in (("old", OLD_BASE), ("new", NEW_BASE)):
        BASE = base_url
        ctxh, ph, errsh = page(b, site="stable", local=save(), toggle=False, dev=True)
        settle(ph, 400)
        res[label] = {"data": json.loads(ph.evaluate(SCEN_RUN)), "errs": list(errsh)}
        ctxh.close()
    BASE = NEW_BASE
    check("h) throw waits (no climb, off the last girder), same seed, identical to " + BASE_REF, res["old"]["data"] == res["new"]["data"], {"old": str(res["old"]["data"])[:200], "new": str(res["new"]["data"])[:200]})
    check("no console errors (h, old build)", not res["old"]["errs"], res["old"]["errs"])
    check("no console errors (h, new build)", not res["new"]["errs"], res["new"]["errs"])
    mres = {}
    for label, base_url in (("old", OLD_BASE), ("new", NEW_BASE)):
        BASE = base_url
        ctxm, pm, errsm = page(b, site="stable", local=save(), toggle=False, dev=False)
        settle(pm, 400)
        pm.evaluate("(()=>{cancelAnimationFrame(raf);S.quick=null;G=null;devJump(1,0);cancelAnimationFrame(raf);G.dev=false;G.score=1234;G.girPts=77;G.state='play';quicksave()})()")
        before_m = pm.evaluate("JSON.stringify(S.quick)")
        pm.evaluate("(()=>{cancelAnimationFrame(raf);G=null;go('menu')})()"); pm.wait_for_timeout(300)
        pm.click("[data-tile=cur]"); pm.wait_for_function("G&&(G.state==='ready'||G.state==='play')", timeout=5000); pm.wait_for_timeout(200)
        after_m = pm.evaluate("JSON.stringify({run:G.run,mapi:G.mapi,grid:G.grid})")
        mres[label] = (before_m, after_m, list(errsm))
        ctxm.close()
    BASE = NEW_BASE
    check("h) maze quicksave identical to " + BASE_REF, mres["old"][0] == mres["new"][0], {"old": mres["old"][0][:150], "new": mres["new"][0][:150]})
    check("h) maze resume identical to " + BASE_REF, mres["old"][1] == mres["new"][1], {"old": mres["old"][1][:150], "new": mres["new"][1][:150]})
    check("no console errors (h, maze old)", not mres["old"][2], mres["old"][2])
    check("no console errors (h, maze new)", not mres["new"][2], mres["new"][2])
    b.close()

print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
