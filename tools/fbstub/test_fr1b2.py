#!/usr/bin/env python3
"""0.4.5_33 (FR1b2) tests: the Ferma floor-3 bolt layouts per loop (FA_BOLTS, faBoltCheck pure validator, R1-R5) and the
eat-driven time bar extended to practice and encounter (own tables FA_PRAC.bar/FA_ENC.bar, scheduled bites only, soft
respawn, last-bite ending with mode-aware buttons, floor bonus = uneaten bites x 100, dev «Ultimo morso» everywhere).
The Ferma run's own bar/bolt behaviour and the maze are golden-compared against BASE_REF (default cf3a1d4 = 0.4.5_32).
Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_fr1b2.py"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

BASE_REF = os.environ.get("BASE_REF", "cf3a1d4")
OLD_PORT = 8798
OLD_DIR = tempfile.mkdtemp(prefix="mgs_old_")
open(os.path.join(OLD_DIR, "index.html"), "wb").write(subprocess.run(["git", "show", BASE_REF + ":index.html"], cwd=ROOT, capture_output=True, check=True).stdout)
NEW_BASE, OLD_BASE = BASE, "http://127.0.0.1:%d/" % OLD_PORT

SEED = """(a=>{window.__s=a;Math.random=()=>{let t=(window.__s=window.__s+0x6D2B79F5|0);t=Math.imul(t^t>>>15,1|t);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}})(%d)"""
FREEZE = "(()=>{window.__raf=window.__raf||window.requestAnimationFrame;window.requestAnimationFrame=()=>0;if(FA)cancelAnimationFrame(FA.raf);if(typeof raf!=='undefined')cancelAnimationFrame(raf);0})()"
UNF = "if(window.__raf)window.requestAnimationFrame=window.__raf;"
QUIET = "(()=>{faIntroEnd();Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;0})()"
STEP = "(n=>{for(let i=0;i<n;i++)faStep(1/60)})"


def start_dev_run(p, girone=1):
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}G=null;S.quick=null;go('menu');startFermaRun({girone:%d,dev:true});0})()" % girone)
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_practice(p):
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}go('menu')})()"); p.wait_for_timeout(200)
    p.evaluate("startFerma({test:true})"); p.wait_for_function("FA&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE)


def start_practice_floor3(p):
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}go('menu')})()"); p.wait_for_timeout(200)
    p.evaluate("startFerma({test:true,level:2})"); p.wait_for_function("FA&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE)


def start_encounter_in_maze(p, n=2, score=5000):
    """a REAL (non-dev) encounter hosted by a real (non-dev) maze run, exactly faInvite's own accept path"""
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}cancelAnimationFrame(raf);G=null;S.quick=null;go('menu')})()"); p.wait_for_timeout(200)
    p.evaluate("(()=>{cancelAnimationFrame(raf);startGame(false,{});cancelAnimationFrame(raf);G.score=%d;window.__hostRun=G.run;0})()" % score)
    p.evaluate("startFerma({run:true,encounter:%d})" % n)
    p.wait_for_function("FA&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=True)
    settle(p, 600)

    # ================= Part A: bolt layouts + validator
    a_data = p.evaluate("""(()=>({
      L1:FA_BOLTS[0],L2:FA_BOLTS[1],L3:FA_BOLTS[2],
      sameRef:FA_BOLTS[0]===FA_LEVELS[2].bolts,
      r1:faBoltCheck(FA_BOLTS[0]),r2:faBoltCheck(FA_BOLTS[1]),r3:faBoltCheck(FA_BOLTS[2]),
      span:FA_JUMP_SPAN}))()""")
    # a) FA_BOLTS[0] golden against BASE_REF's FA_LEVELS[2].bolts
    import functools, http.server, threading
    class OH(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    osrv = http.server.ThreadingHTTPServer(("127.0.0.1", OLD_PORT), functools.partial(OH, directory=OLD_DIR))
    threading.Thread(target=osrv.serve_forever, daemon=True).start()
    BASE = OLD_BASE
    ctxo, po, errso = page(b, site="stable", local=save(), toggle=False, dev=False)
    settle(po, 400)
    old_bolts = po.evaluate("FA_LEVELS[2].bolts")
    ctxo.close()
    BASE = NEW_BASE
    check("a) FA_BOLTS[0] equals " + BASE_REF + "'s FA_LEVELS[2].bolts (byte-for-byte)", a_data["L1"] == old_bolts, (a_data["L1"], old_bolts))
    check("a) FA_BOLTS[0] is the SAME object as FA_LEVELS[2].bolts (no duplication)", a_data["sameRef"])

    # b) faBoltCheck passes on L1/L2/L3; counts 8/8/10
    check("b) L1: 8 bolts, faBoltCheck ok", len(a_data["L1"]) == 8 and a_data["r1"]["ok"], a_data["r1"])
    check("b) L2: 8 bolts, faBoltCheck ok", len(a_data["L2"]) == 8 and a_data["r2"]["ok"], a_data["r2"])
    check("b) L3: 10 bolts, faBoltCheck ok", len(a_data["L3"]) == 10 and a_data["r3"]["ok"], a_data["r3"])
    check("b) FA_JUMP_SPAN is a sane fraction of the real jump's max horizontal reach (26 px hole comfortably jumpable)", a_data["span"] >= 26 and a_data["span"] < 100, a_data["span"])

    # c) faBoltCheck fails on 4 hand-made bad layouts
    bad = p.evaluate("""(()=>({
      ladder:faBoltCheck([{g:1,x:205}]),
      overlap:faBoltCheck([{g:2,x:150},{g:2,x:155}]),
      respawn:faBoltCheck([{g:0,x:40}]),
      deadend:faBoltCheck(FA_BOLTS[0].concat([{g:0,x:300}]))
    }))()""")
    check("c) hole on a ladder: rejected", not bad["ladder"]["ok"] and any("scala" in e for e in bad["ladder"]["errs"]), bad["ladder"])
    check("c) overlapping holes: rejected", not bad["overlap"]["ok"] and any("sovrapposti" in e for e in bad["overlap"]["errs"]), bad["overlap"])
    check("c) hole at respawn (inside safeXEnd on the start girder): rejected", not bad["respawn"]["ok"] and any("partenza" in e for e in bad["respawn"]["errs"]), bad["respawn"])
    check("c) dead end (a bolt placed beyond the ground-floor grill wall, R1-compliant but genuinely unreachable): rejected",
          not bad["deadend"]["ok"] and any("vicolo cieco" in e for e in bad["deadend"]["errs"]), bad["deadend"])

    # d) stats: L2/L3 mean ladder distance and route both exceed L1's
    stats = p.evaluate("({l1:faBoltCheck(FA_BOLTS[0]).stats,l2:faBoltCheck(FA_BOLTS[1]).stats,l3:faBoltCheck(FA_BOLTS[2]).stats})")
    print("FR1b2 bolt stats:", json.dumps(stats, indent=2))
    check("d) L2 mean ladder distance > L1's", stats["l2"]["meanLadderDist"] > stats["l1"]["meanLadderDist"], (stats["l2"]["meanLadderDist"], stats["l1"]["meanLadderDist"]))
    check("d) L3 mean ladder distance > L1's", stats["l3"]["meanLadderDist"] > stats["l1"]["meanLadderDist"], (stats["l3"]["meanLadderDist"], stats["l1"]["meanLadderDist"]))
    check("d) L2 shortest route > L1's", stats["l2"]["route"] > stats["l1"]["route"], (stats["l2"]["route"], stats["l1"]["route"]))
    check("d) L3 shortest route > L1's", stats["l3"]["route"] > stats["l1"]["route"], (stats["l3"]["route"], stats["l1"]["route"]))
    check("no console errors (A, bolt validator)", not errs, errs)

    # e) run at gironi 3/6/9/12 on floor 3; practice/encounter always L1
    # SUPERSEDED TWICE since this check was written: FR1c first moved layout selection to floor(e) (continuous,
    # e=(girone-1)/3*rate); FR1d (0.4.5_35) replaced that with an explicit per-difficulty sequence indexed by the
    # real discrete loop (FA_RUN.diff[id].bolts, since floor 3 only recurs every 3rd girone, floor(e) could skip a
    # whole tier on faster difficulties -- see CLAUDE.md FR1d). On "easy" (bolts:[0,0,1,2]) gironi 3/6/9/12 ->
    # loop 0/1/2/3 -> L1/L1/L2/L3 (not L1/L2/L3/L3 as this check's name still says; kept as the clearest difficulty
    # to exercise all three layouts, see test_fr1d.py for the full per-difficulty table).
    want = {3: 0, 6: 0, 9: 1, 12: 2}
    for g, li in want.items():
        p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}G=null;S.quick=null;go('menu');startFermaRun({girone:%d,dev:true,diff:'easy'});0})()" % g)
        p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE)
        bolts = p.evaluate("({level:FA.level,bolts:FA.bolts.map(b=>({g:b.g,x:b.x}))})")
        check("e) run girone %d (easy): floor index %d, bolt layout L%d" % (g, bolts["level"], li + 1),
              bolts["level"] == 2 and bolts["bolts"] == a_data[["L1", "L2", "L3"][li]], bolts)
    start_practice_floor3(p)
    pbolts = p.evaluate("FA.bolts.map(b=>({g:b.g,x:b.x}))")
    check("e) practice floor 3: always L1", pbolts == a_data["L1"], pbolts)
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}go('menu')})()"); p.wait_for_timeout(200)
    p.evaluate("startFerma({test:true,level:2,encounter:2})")
    p.wait_for_function("FA&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE)
    ebolts = p.evaluate("FA.bolts.map(b=>({g:b.g,x:b.x}))")
    check("e) encounter floor 3: always L1", ebolts == a_data["L1"], ebolts)
    check("no console errors (e)", not errs, errs)

    # ================= Part B: eat-driven bar in practice and encounter
    # f) no bite before due; bar drops 1/N per bite; death leaves bar/schedule unchanged, costs one life
    start_practice(p); p.evaluate(QUIET)
    b0 = p.evaluate("({left:FA.bar.left,N:FA.bar.N,due:FA.bar.due,clock:FA.bar.clock,lives:FA.lives})")
    p.evaluate(STEP + "(5)")  # well before the first due time (L/N ~ 10s at girone-1-equivalent values)
    early = p.evaluate("({left:FA.bar.left,pending:FA.bar.pending})")
    check("f) no bite before the first due time", early["left"] == b0["left"] and not early["pending"], (b0, early))
    e = p.evaluate("""(()=>{const B=FA.bar,l0=B.left,N=B.N;B.pending=true;FA.alg.state='idle';FA.alg.wait=0;FA.inv=1e9;faStep(1/60);
      return{l1:B.left,st:FA.alg.state,want:(l0-1)/N}})()""")
    check("f) practice: a bite removes exactly 1/N of the bar", e["l1"] == b0["left"] - 1 and e["st"] == "eat", e)
    p.evaluate("FA.alg.state='idle';FA.alg.wait=1e9")  # clear the "eat" state left over from the bite just above, isolate the death's own effect
    d0 = p.evaluate("({left:FA.bar.left,N:FA.bar.N,due:FA.bar.due,clock:FA.bar.clock,lives:FA.lives})")
    p.evaluate("FA.inv=0;faDie('x',true)")
    d1 = p.evaluate("(()=>{const eat=FA.alg.state;for(let i=0;i<200&&FA.state==='dying';i++)faStep(1/60);return{eat,state:FA.state,left:FA.bar.left,due:FA.bar.due,clock:FA.bar.clock,lives:FA.lives}})()")
    check("f) practice death: no bite, bar/clock/due unchanged, one life lost, Algidone not eating",
          d1["eat"] != "eat" and d1["left"] == d0["left"] and d1["due"] == d0["due"] and d1["clock"] == d0["clock"] and d1["lives"] == d0["lives"] - 1, (d0, d1))
    check("no console errors (f)", not errs, errs)

    # g) practice empty bar -> ending -> lost panel Riprova/Esci; Riprova restarts
    start_practice(p); p.evaluate(QUIET); p.evaluate("FA.inv=1e9")
    p.evaluate("FA.bar.left=1;FA.bar.pending=true;for(let i=0;i<400&&FA.state!=='over';i++)faStep(1/60)")
    g1 = p.evaluate("({state:FA.state,h3:document.querySelector('#fapanel h3').textContent,btns:[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>({a:b.dataset.fa,t:b.textContent.trim()}))})")
    check("g) practice empty bar: «Algidone ha finito tutto!» with Riprova/Esci", g1["state"] == "over" and g1["h3"] == "Algidone ha finito tutto!" and [x["a"] for x in g1["btns"]] == ["retry", "exit"], g1)
    p.click("#fapanel [data-fa=retry]")
    g2 = p.evaluate("({level:FA.level,lives:FA.lives,score:FA.score,state:FA.state})")
    check("g) Riprova restarts from floor 1, lives 3, score 0", g2 == {"level": 0, "lives": 3, "score": 0, "state": "intro"}, g2)
    check("no console errors (g)", not errs, errs)

    # h) encounter empty bar -> back to the maze, host score unchanged, no reward
    start_encounter_in_maze(p, n=2, score=5000)
    p.evaluate(QUIET); p.evaluate("FA.inv=1e9")
    before = p.evaluate("window.__hostRun.score")
    p.evaluate("FA.bar.left=1;FA.bar.pending=true;for(let i=0;i<400&&FA.state!=='over';i++)faStep(1/60)")
    h1 = p.evaluate("({state:FA.state,btns:[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa),paid:FA.paid})")
    check("h) encounter empty bar: «Continua» only, not paid", h1["state"] == "over" and h1["btns"] == ["exit"] and not h1["paid"], h1)
    p.click("#fapanel [data-fa=exit]"); p.wait_for_timeout(300)
    h2 = p.evaluate("({screen,hostScore:window.__hostRun.score,FA})")
    check("h) back to the maze, host score unchanged, no reward", h2["screen"] == "game" and h2["hostScore"] == before and h2["FA"] is None, (h2["screen"], h2["hostScore"], before))
    check("no console errors (h)", not errs, errs)

    # i) encounter win: floor bonus = uneaten x 100, paid through faEncPay
    start_encounter_in_maze(p, n=1, score=5000)  # 1-floor encounter: this floor's win is the last
    p.evaluate(QUIET)
    before_i = p.evaluate("window.__hostRun.score")
    i1 = p.evaluate("""(()=>{FA.bar.left=6;FA.bar.N=12;FA.bar.shown=6/12;FA.score=400;faWin();
      for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60);for(let i=0;i<120;i++)faStep(1/60);
      return{bonus:FA.cnt.bonus,base:FA.cnt.base,paid:FA.paid,hostScore:window.__hostRun.score}})()""")
    check("i) encounter win: bonus = 6 uneaten bites x 100 = 600, paid to the host run",
          i1["bonus"] == 600 and i1["base"] == 400 and i1["paid"] and i1["hostScore"] == before_i + 400 + 600, (i1, before_i))
    check("no console errors (i)", not errs, errs)

    # j) the run's bar values/behaviour and bolt layout are unchanged vs BASE_REF; the maze is untouched
    SCEN_RUN = """(async()=>{
      __SEED__;window.requestAnimationFrame=()=>0;const out={};
      if(FA){FA.dead=true;FA=null}G=null;S.quick=null;go('menu');
      await startFermaRun({girone:1,dev:true});cancelAnimationFrame(FA.raf);
      faIntroEnd();FA.inv=1e9;const dues=[];const fb=faBite;window.faBite=function(){dues.push(FA.bar.due);fb()};
      for(let i=0;i<60*200&&!FA.lb;i++)faStep(1/60);window.faBite=fb;
      out.L=FA.bar.L;out.N=FA.bar.N;out.dues=dues;out.lastSlow=FA_RUN.bar.lastSlow;
      return JSON.stringify(out)})""".replace("__SEED__", SEED % 5151)
    res = {}
    for label, base_url in (("old", OLD_BASE), ("new", NEW_BASE)):
        BASE = base_url
        ctxj, pj, errsj = page(b, site="stable", local=save(), toggle=False, dev=True)
        settle(pj, 400)
        res[label] = {"data": json.loads(pj.evaluate(SCEN_RUN)), "errs": list(errsj)}
        ctxj.close()
    BASE = NEW_BASE
    check("j) the run's bar (L/N/scheduled due times/lastSlow), same seed, identical to " + BASE_REF, res["old"]["data"] == res["new"]["data"], {"old": str(res["old"]["data"])[:200], "new": str(res["new"]["data"])[:200]})
    check("no console errors (j, old build)", not res["old"]["errs"], res["old"]["errs"])
    check("no console errors (j, new build)", not res["new"]["errs"], res["new"]["errs"])
    # maze untouched: quicksave/resume golden, same pattern as test_fr1b1.py section d
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
    check("j) maze quicksave identical to " + BASE_REF, mres["old"][0] == mres["new"][0], {"old": mres["old"][0][:150], "new": mres["new"][0][:150]})
    check("j) maze resume identical to " + BASE_REF, mres["old"][1] == mres["new"][1], {"old": mres["old"][1][:150], "new": mres["new"][1][:150]})
    check("no console errors (j, maze old)", not mres["old"][2], mres["old"][2])
    check("no console errors (j, maze new)", not mres["new"][2], mres["new"][2])

    # k) «Ultimo morso» in practice/encounter pause menus, dev mode only
    start_practice(p); p.evaluate("faPause(true)")
    kbtns = p.evaluate("[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa)")
    check("k) practice pause (dev): has «Ultimo morso»", "lastbite" in kbtns, kbtns)
    p.evaluate("faPause(false)")
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}go('menu')})()"); p.wait_for_timeout(200)
    p.evaluate("startFerma({test:true,encounter:2})"); p.wait_for_function("FA&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE)
    p.evaluate("faPause(true)")
    kbtns2 = p.evaluate("[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa)")
    check("k) encounter pause (dev): has «Ultimo morso»", "lastbite" in kbtns2, kbtns2)
    check("no console errors (k, dev)", not errs, errs)
    ctx.close()

    ctx2, p2, errs2 = page(b, site="stable", local=save(), toggle=False, dev=False)
    settle(p2, 600)
    start_practice(p2); p2.evaluate("faPause(true)")
    kbtns3 = p2.evaluate("[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa)")
    check("k) practice pause (player, no dev): no «Ultimo morso»", "lastbite" not in kbtns3, kbtns3)
    check("no console errors (k, player)", not errs2, errs2)
    ctx2.close(); b.close()

print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
