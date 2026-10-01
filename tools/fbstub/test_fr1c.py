#!/usr/bin/env python3
"""0.4.5_34 (FR1c) tests: music exclusivity (the shared loop player stops every other music track the instant
one starts, even an async load that resolves late), the maze-only secret toast queued until the player is back
on the main menu during a Ferma run, the win panel's «Salva ed esci» (saves exactly the state «Avanti» would
start the next girone with), and the Ferma run's per-difficulty progression (FA_RUN.diff, continuous e). Practice,
the maze encounter and the maze itself are golden-compared against BASE_REF (default 5ac1377 = 0.4.5_33).
Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_fr1c.py"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

BASE_REF = os.environ.get("BASE_REF", "5ac1377")
OLD_PORT = 8799
OLD_DIR = tempfile.mkdtemp(prefix="mgs_old_")
open(os.path.join(OLD_DIR, "index.html"), "wb").write(subprocess.run(["git", "show", BASE_REF + ":index.html"], cwd=ROOT, capture_output=True, check=True).stdout)
NEW_BASE, OLD_BASE = BASE, "http://127.0.0.1:%d/" % OLD_PORT
import functools, http.server, threading
class OH(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
osrv = http.server.ThreadingHTTPServer(("127.0.0.1", OLD_PORT), functools.partial(OH, directory=OLD_DIR))
threading.Thread(target=osrv.serve_forever, daemon=True).start()

SEED ="""(a=>{window.__s=a;Math.random=()=>{let t=(window.__s=window.__s+0x6D2B79F5|0);t=Math.imul(t^t>>>15,1|t);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}})(%d)"""
FREEZE = "(()=>{window.__raf=window.__raf||window.requestAnimationFrame;window.requestAnimationFrame=()=>0;if(FA)cancelAnimationFrame(FA.raf);if(typeof raf!=='undefined')cancelAnimationFrame(raf);0})()"
UNF = "if(window.__raf)window.requestAnimationFrame=window.__raf;"
QUIET = "(()=>{faIntroEnd();Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;0})()"
STEP = "(n=>{for(let i=0;i<n;i++)faStep(1/60)})"


def to_menu(p):
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}if(typeof raf!=='undefined')cancelAnimationFrame(raf);G=null;S.quick=null;persist();go('menu')})()")
    p.wait_for_timeout(300)


def start_run(p):
    to_menu(p)
    p.click("[data-tile=new]"); p.wait_for_timeout(300); p.click("[data-rg=ferma]")
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_dev_run(p, girone=1):
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}G=null;S.quick=null;go('menu');startFermaRun({girone:%d,dev:true});0})()" % girone)
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_practice(p):
    to_menu(p)
    p.evaluate("startFerma({test:true})")
    p.wait_for_function("FA&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_enc(p, n=2):
    to_menu(p)
    p.evaluate("startFerma({test:true,encounter:%d})" % n)
    p.wait_for_function("FA&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def win_floor(p):
    p.evaluate(QUIET)
    p.evaluate("Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;if(FA.level<2)faWin();else faFinalWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)")
    p.evaluate(STEP + "(90)")


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=True)
    settle(p, 600)

    # ================= a) music exclusivity
    to_menu(p)
    p.evaluate("S.opts.music=true;persist();syncMusic()")
    p.wait_for_function("bgm && !bgm.paused", timeout=5000)
    # the real bug scenario: the menu track's own reload is artificially slow (released, then re-decoding)
    # while a Ferma run starts from "Nuovo gioco" -- music.fa must win, the stale bgm start must be dropped
    r = p.evaluate("""(async()=>{
      const origFetch=window.fetch;
      window.fetch=(...a)=>new Promise(res=>setTimeout(()=>res(origFetch(...a)),400));
      bgm.release();const p0=bgm.play(); // bgm's reload is now slow and in flight
      window.fetch=origFetch; // music.fa itself decodes at normal speed
      await startFermaRun({girone:1,dev:true});
      await p0; // let the stale bgm start resolve (it must have been dropped already)
      await new Promise(r=>setTimeout(r,50));
      return {bgmPaused:bgm.paused,musicFaPaused:musicFa.paused,musicFaExists:!!musicFa}
    })()""")
    check("a) run from «Nuovo gioco», bgm's own reload delayed: exactly music.fa ends up playing, the stale menu-track start is dropped",
          r["musicFaExists"] and not r["musicFaPaused"] and r["bgmPaused"], r)
    p.evaluate(FREEZE)
    to_menu(p)
    p.wait_for_function("bgm && !bgm.paused", timeout=5000)
    r2 = p.evaluate("({bgmPlaying:!bgm.paused,musicFaPaused:!musicFa||musicFa.paused})")
    check("a) back on the menu: only the menu track plays", r2["bgmPlaying"] and r2["musicFaPaused"], r2)
    # practice and the encounter: same exclusivity, no delay needed to demonstrate it (the sync stop-others covers both)
    start_practice(p)
    p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
    check("a) practice: music.fa plays, bgm paused", p.evaluate("!musicFa.paused && (!bgm || bgm.paused)"))
    to_menu(p); p.wait_for_function("bgm && !bgm.paused", timeout=5000)
    check("a) back on the menu after practice: only the menu track plays", p.evaluate("!bgm.paused && (!musicFa || musicFa.paused)"))
    start_enc(p, 2)
    p.wait_for_function("musicFa && !musicFa.paused", timeout=5000)
    check("a) encounter: music.fa plays, bgm paused", p.evaluate("!musicFa.paused && (!bgm || bgm.paused)"))
    to_menu(p); p.wait_for_function("bgm && !bgm.paused", timeout=5000)
    check("a) back on the menu after the encounter: only the menu track plays", p.evaluate("!bgm.paused && (!musicFa || musicFa.paused)"))
    # a direct, deterministic unit check of the race on two fresh tracks (no bgm/musicFa involved)
    r3 = p.evaluate("""(async()=>{
      const url="data:audio/mpeg;base64,"+FA_MUSIC_B64;
      const origFetch=window.fetch;
      let delay=true;
      window.fetch=(...a)=>delay?new Promise(res=>setTimeout(()=>res(origFetch(...a)),300)):origFetch(...a);
      const A=loopTrack(url,{vol:.1}),B=loopTrack(url,{vol:.1});
      const pa=A.play(); delay=false; const pb=B.play();
      await pa; await pb; await new Promise(r=>setTimeout(r,30));
      const out={aPaused:A.paused,bPaused:B.paused};
      A.release();B.release();window.fetch=origFetch;
      return out
    })()""")
    check("a) unit: a track whose async start resolves late is dropped once another track has started", r3["aPaused"] and not r3["bPaused"], r3)
    check("no console errors (a)", not errs, errs)

    # ================= b) secret toast queued during a Ferma run, shown once back on the menu
    TOAST_NOW = "document.querySelector('.toast')?document.querySelector('.toast').textContent:null"
    SECRET_MSG = "Segreto sbloccato in Mangiaroccia: Segreto sbloccato: Trasformati! (al posto di Pausa)"
    base_p = p.evaluate("(()=>{S.ach={prog:{},done:{}};const s=JSON.parse(JSON.stringify(S.p));s.sec=false;return JSON.stringify(s)})()")
    p.evaluate("(p0)=>{S.p=JSON.parse(p0);persist()}", base_p)
    start_dev_run(p, 6)  # girone 6, floor 3 (fabbrica): winning it and clicking Avanti reaches girone 7
    p.evaluate("FA.run.dev=false;0")  # a real (non-dev) run, discarded after this check
    win_floor(p)
    check("b) girone 7 not yet reached: S.p.sec still false", p.evaluate("S.p.sec") is False, p.evaluate("S.p.sec"))
    p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd();0")  # onGironeAdvance runs here: girone -> 7
    tnow = p.evaluate(TOAST_NOW)
    check("b) girone 7 reached (Avanti clicked): S.p.sec set, no toast shown yet (still in a Ferma run)",
          p.evaluate("S.p.sec") is True and p.evaluate("FA.run.girone") == 7 and tnow is None, (p.evaluate("S.p.sec"), p.evaluate("FA.run.girone"), tnow))
    p.evaluate(STEP + "(30)")
    check("b) still no toast while the run continues", p.evaluate(TOAST_NOW) is None, p.evaluate(TOAST_NOW))
    p.evaluate("FA.run.dev=true;0")  # back to dev so exiting doesn't touch real progress further
    p.evaluate("faPause(true)"); p.click("#fapanel [data-fa=exit]")
    p.wait_for_function("(%s)==='%s'" % (TOAST_NOW, SECRET_MSG), timeout=8000)  # an earlier "Partita abbandonata" toast may show first and run its own course
    check("b) back on the menu: the queued toast shows, prefixed for Mangiaroccia", True)
    p.wait_for_timeout(5500)  # let the secret toast (long message, capped at 5s) finish its own course
    to_menu(p); p.wait_for_timeout(700)
    ttoast2 = p.evaluate(TOAST_NOW)
    check("b) not shown again on a later menu visit", ttoast2 is None, ttoast2)
    check("no console errors (b)", not errs, errs)
    # maze run reaching girone 7: unchanged behaviour (golden against BASE_REF)
    mres = {}
    for label, base_url in (("old", OLD_BASE), ("new", NEW_BASE)):
        BASE = base_url
        ctxm, pm, errsm = page(b, site="stable", local=save(sordi=4200, r=14, a=8), toggle=False, dev=True)
        settle(pm, 500)
        pm.evaluate("S.p.sec=false;persist();cancelAnimationFrame(raf);G=null;devJump(6,0);cancelAnimationFrame(raf);G.dev=false;0")
        pm.evaluate("G.state='clear';G.t=0;onGironeAdvance(G.run);0")
        pm.wait_for_timeout(700)
        mres[label] = {"sec": pm.evaluate("S.p.sec"), "toast": pm.evaluate("document.querySelector('.toast')?document.querySelector('.toast').textContent:null"), "errs": list(errsm)}
        ctxm.close()
    BASE = NEW_BASE
    check("b) a maze run reaching girone 7 behaves as at " + BASE_REF + " (toast shown right away, not queued)", mres["old"] == mres["new"], mres)
    check("b) sanity: the maze toast actually appears (not None)", mres["new"]["sec"] is True and mres["new"]["toast"] is not None, mres["new"])
    check("no console errors (b, maze old)", not mres["old"]["errs"], mres["old"]["errs"])
    check("no console errors (b, maze new)", not mres["new"]["errs"], mres["new"]["errs"])

    # ================= c) win panel "Salva ed esci" == the state "Avanti" would start the next girone with
    p.evaluate(SEED % 777)  # same seed before each branch's own floor load, so the bar's own random N jitter matches (fair comparison)
    start_dev_run(p, 4)
    p.evaluate("FA.run.dev=false;S.ach={prog:{},done:{}};0")
    p.evaluate("FA.score=1000;FA.run.girPts=500;0")
    snap = p.evaluate("JSON.stringify(FA.run)")
    baseGir = p.evaluate("(S.p.ch.roccia||{}).gir")  # gir BEFORE either branch's own win, the real common baseline
    win_floor(p)
    btns = p.evaluate("[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa)")
    check("c) win panel buttons in order: Avanti / Salva ed esci / Esci", btns == ["next", "savewin", "exit"], btns)
    # branch A: click "Avanti", record the run state at the start of the next girone
    p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd();0")
    wantRun = p.evaluate("JSON.stringify(FA.run)")
    wantGir = p.evaluate("(S.p.ch.roccia||{}).gir")
    to_menu(p)
    # branch B: from the identical pre-win state, click "Salva ed esci" instead
    p.evaluate("(()=>{S.p.ch.roccia.gir=%d;0})()" % baseGir)  # undo branch A's one win_floor() career-gironi increment, back to the real common baseline
    p.evaluate(SEED % 777)  # identical seed: branch B's own fresh floor load gets the same random bar jitter branch A got
    start_dev_run(p, 4)
    p.evaluate("(s)=>{FA.run=JSON.parse(s);FA.run.dev=false;FA.score=FA.run.score;0}", snap)
    win_floor(p)
    p.click("#fapanel [data-fa=savewin]"); p.wait_for_timeout(300)
    r = p.evaluate("({screen,quick:S.quick,gir:(S.p.ch.roccia||{}).gir,toast:document.querySelector('.toast')?document.querySelector('.toast').textContent:null})")
    check("c) «Salva ed esci»: back on the menu with a «Partita salvata» toast", r["screen"] == "menu" and r["toast"] == "Partita salvata", r)
    check("c) S.quick's run equals exactly the state «Avanti» starts the next girone with", r["quick"] == {"game": "ferma", "run": json.loads(wantRun)}, {"got": r["quick"], "want": json.loads(wantRun)})
    check("c) onGironeAdvance ran once (career gironi match «Avanti»'s own, not double-counted)", r["gir"] == wantGir, (r["gir"], wantGir, baseGir))
    p.click("[data-tile=cur]"); p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    r2 = p.evaluate("({girone:FA.run.girone,level:FA.level})")
    check("c) «Gioco corrente» resumes at that next girone", r2["girone"] == json.loads(wantRun)["girone"] and r2["level"] == (json.loads(wantRun)["girone"] - 1) % 3, r2)
    check("no console errors (c, floors 1-2)", not errs, errs)
    # dev run: no "savewin" button; floor 3 panel included
    start_dev_run(p, 3)
    p.evaluate(QUIET); p.evaluate("Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;faFinalWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)")
    btnsDev = p.evaluate("[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa)")
    check("c) dev run, floor 3: no «Salva ed esci» button", "savewin" not in btnsDev, btnsDev)
    start_dev_run(p, 3)
    p.evaluate("FA.run.dev=false;0")
    p.evaluate(QUIET); p.evaluate("Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;faFinalWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)")
    btnsReal3 = p.evaluate("[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa)")
    check("c) real run, floor 3: Avanti / Salva ed esci / Esci too", btnsReal3 == ["next", "savewin", "exit"], btnsReal3)
    check("no console errors (c, floor 3)", not errs, errs)

    # ================= d) per-difficulty progression table, gironi 1-12
    table = {}
    for d in ("easy", "medium", "hard"):
        table[d] = []
        for g in range(1, 13):
            start_dev_run(p, g)
            p.evaluate("FA.run.diff='%s';faBarInit();0" % d)  # the bar was computed at floor-load time with the default diff; recompute it now that diff changed
            # recompute cfg/bar/layout as faLoadFloor would for this girone+diff, without a full floor reload
            r = p.evaluate("""(()=>{
              const k=faLoopThrowK(),ik=faLoopItemK(),e=faLoopE();
              const base=FA_LEVELS[2].items,B=FA_RUN.bar;
              const n0=Math.max(B.Nmin,Math.round(B.N1-B.dN*e)); // pre-jitter N (FA.bar.N itself carries a +-nRand random jitter, not monotonic by design)
              return {e:+e.toFixed(4),throwMin:+(base.throwMin*k).toFixed(4),throwMax:+(base.throwMax*k).toFixed(4),itemK:+ik.toFixed(4),
                      barL:FA.bar.L,barN:FA.bar.N,barN0:n0,layout:Math.min(2,Math.floor(e))}
            })()""")
            table[d].append(dict(g=g, **r))
    print("FR1c difficulty table:")
    for d in ("easy", "medium", "hard"):
        print(" ", d, "g\te\tthrowMin\tthrowMax\titemK\tbarL\tbarN\tlayout")
        for row in table[d]:
            print("   ", row["g"], row["e"], row["throwMin"], row["throwMax"], row["itemK"], row["barL"], row["barN"], row["layout"])
    ok = True
    for d in ("easy", "medium", "hard"):
        for i in range(1, len(table[d])):
            ra, rb = table[d][i - 1], table[d][i]
            if not (rb["throwMin"] <= ra["throwMin"] + 1e-9 and rb["itemK"] >= ra["itemK"] - 1e-9 and rb["barL"] <= ra["barL"] and rb["barN0"] <= ra["barN0"]):
                ok = False
    check("d) within each difficulty, every girone is at least as hard as the previous one (never easier)", ok, table)
    strictly = any(table["hard"][i]["throwMin"] < table["hard"][0]["throwMin"] for i in range(1, 12))
    check("d) strictly harder somewhere before the caps (hard, throw wait)", strictly, [r["throwMin"] for r in table["hard"]])
    crossOk = all(table["medium"][g]["throwMin"] <= table["easy"][g]["throwMin"] and table["medium"][g]["itemK"] >= table["easy"][g]["itemK"] and
                  table["hard"][g]["throwMin"] <= table["medium"][g]["throwMin"] and table["hard"][g]["itemK"] >= table["medium"][g]["itemK"] for g in range(12))
    check("d) at every girone, a harder difficulty is at least as hard as an easier one", crossOk, table)
    firstL2 = {d: next(r["g"] for r in table[d] if r["layout"] >= 1) for d in table}
    firstL3 = {d: next((r["g"] for r in table[d] if r["layout"] >= 2), None) for d in table}
    check("d) L2 arrives earlier (or as early) on hard than on easy", firstL2["hard"] < firstL2["easy"], firstL2)
    check("d) L3 arrives earlier (or as early) on hard than on easy", firstL3["hard"] < firstL3["easy"], firstL3)
    check("no console errors (d)", not errs, errs)
    # FA_MAX_ITEMS sanity at the hardest settings reached in this table: never the binding constraint
    start_dev_run(p, 12); p.evaluate("FA.run.diff='hard';faLoadFloor(2,3,0);0")
    p.evaluate(QUIET)
    maxItems = p.evaluate("(()=>{let m=0;for(let i=0;i<60*30;i++){faStep(1/60);m=Math.max(m,FA.items.length)}return m})()")
    check("d) FA_MAX_ITEMS (14) sanity: peak concurrent items at hard/girone 12 stays well under the cap", maxItems < 14, maxItems)
    check("no console errors (d, FA_MAX_ITEMS)", not errs, errs)

    ctx.close()

    # ================= e) practice, encounter and the maze: golden against the previous build
    SCEN = """(async kind=>{
      __SEED__;window.requestAnimationFrame=()=>0;const out={};
      await (kind==='enc'?startFerma({test:true,encounter:2}):startFerma({test:true}));cancelAnimationFrame(FA.raf);
      faIntroEnd();FA.inv=1e9;const eats=[];let prev=FA.alg.state;
      for(let i=0;i<60*90;i++){faStep(1/60);if(FA.alg.state==='eat'&&prev!=='eat')eats.push(i);prev=FA.alg.state;if(FA.state==='over')break}
      out.eats=eats;out.state=FA.state;out.throws=FA.throws;out.items=FA.items.length;out.score=FA.score;out.bar={L:FA.bar.L,N:FA.bar.N};
      return JSON.stringify(out)})""".replace("__SEED__", SEED % 8080)
    res = {}
    for label, base_url in (("old", OLD_BASE), ("new", NEW_BASE)):
        BASE = base_url
        ctxe, pe, errse = page(b, site="stable", local=save(), toggle=False, dev=False)
        settle(pe, 500)
        res[label] = {}
        for kind in ("practice", "enc"):
            pe.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null};go('menu')})()"); pe.wait_for_timeout(200)
            res[label][kind] = pe.evaluate("(%s)('%s')" % (SCEN, kind))
        res[label]["errs"] = list(errse)
        ctxe.close()
    BASE = NEW_BASE
    for kind in ("practice", "enc"):
        check("e) %s identical to %s (bar, bites, throws, items, score)" % (kind, BASE_REF), res["old"][kind] == res["new"][kind], {"old": res["old"][kind][:200], "new": res["new"][kind][:200]})
    check("no console errors (e, practice/encounter)", not res["old"]["errs"] and not res["new"]["errs"], (res["old"]["errs"], res["new"]["errs"]))
    # maze quicksave/resume golden, same pattern as test_fr1b2.py section j
    mres2 = {}
    for label, base_url in (("old", OLD_BASE), ("new", NEW_BASE)):
        BASE = base_url
        ctxm2, pm2, errsm2 = page(b, site="stable", local=save(), toggle=False, dev=False)
        settle(pm2, 400)
        pm2.evaluate("(()=>{cancelAnimationFrame(raf);S.quick=null;G=null;devJump(1,0);cancelAnimationFrame(raf);G.dev=false;G.score=1234;G.girPts=77;G.state='play';quicksave()})()")
        before_m = pm2.evaluate("JSON.stringify(S.quick)")
        pm2.evaluate("(()=>{cancelAnimationFrame(raf);G=null;go('menu')})()"); pm2.wait_for_timeout(300)
        pm2.click("[data-tile=cur]"); pm2.wait_for_function("G&&(G.state==='ready'||G.state==='play')", timeout=5000); pm2.wait_for_timeout(200)
        after_m = pm2.evaluate("JSON.stringify({run:G.run,mapi:G.mapi,grid:G.grid})")
        mres2[label] = (before_m, after_m, list(errsm2))
        ctxm2.close()
    BASE = NEW_BASE
    check("e) maze quicksave identical to " + BASE_REF, mres2["old"][0] == mres2["new"][0], {"old": mres2["old"][0][:150], "new": mres2["new"][0][:150]})
    check("e) maze resume identical to " + BASE_REF, mres2["old"][1] == mres2["new"][1], {"old": mres2["old"][1][:150], "new": mres2["new"][1][:150]})
    check("no console errors (e, maze old)", not mres2["old"][2], mres2["old"][2])
    check("no console errors (e, maze new)", not mres2["new"][2], mres2["new"][2])
    b.close()

print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
