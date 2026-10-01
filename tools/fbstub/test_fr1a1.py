#!/usr/bin/env python3
"""0.4.5_29 (FR1a1) tests: the Ferma Algidone! run shell -- FA.run (G=null), FA.score/FA.lives aliases, girone -> level (g-1) mod 3,
the two girone hooks at the floor-win and «Avanti» moments, lives refill (not in Hardcore), soft respawn, end through runPayout and
«Partita finita», the dev button, and activeRun() (golden against BASE_REF, default aa6fe6c = 0.4.5_28, for the maze).
Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_fr1a1.py"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

BASE_REF = os.environ.get("BASE_REF", "aa6fe6c")
OLD_PORT = 8795
OLD_DIR = tempfile.mkdtemp(prefix="mgs_old_")
open(os.path.join(OLD_DIR, "index.html"), "wb").write(subprocess.run(["git", "show", BASE_REF + ":index.html"], cwd=ROOT, capture_output=True, check=True).stdout)
NEW_BASE, OLD_BASE = BASE, "http://127.0.0.1:%d/" % OLD_PORT

FREEZE = "(()=>{window.__raf=window.__raf||window.requestAnimationFrame;window.requestAnimationFrame=()=>0;if(FA)cancelAnimationFrame(FA.raf);0})()"
UNF = "if(window.__raf)window.requestAnimationFrame=window.__raf;"
UNFREEZE = "(()=>{" + UNF + "0})()"
QUIET = "(()=>{faIntroEnd();Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;0})()"
# the real win sequence of the current floor (climb on floors 1-2, collapse on floor 3) up to its panel
WIN = """(()=>{faIntroEnd();Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;
  if(FA.level<2)faWin();else faFinalWin();let i=0;while(FA.state!=='win'&&i<1000){faStep(1/60);i++}return FA.state})()"""
DIE_AND_WAIT = "(()=>{faDie('prova',true);const eat=FA.alg.state,stockDying=FA.stock;let i=0;while(FA.state==='dying'&&i<200){faStep(1/60);i++}return{eat,stockDying,state:FA.state}})()"
SNAP = "(()=>JSON.stringify({p:S.p,ach:S.ach,quick:S.quick}))()"


def start_ferma_run(p, tile="new"):
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}G=null;S.quick=null;persist();go('menu')})()"); p.wait_for_timeout(300)
    p.click("[data-tile=%s]" % tile); p.wait_for_timeout(300); p.click("[data-rg=ferma]")
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def click_panel(p, act):
    p.click("#fapanel [data-fa=%s]" % act); p.wait_for_timeout(150)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=False)
    settle(p, 600)

    # ---------------- a) the chooser starts a Ferma run; Algidone still skips the chooser
    start_ferma_run(p)
    r = p.evaluate("({G,game:FA.run.game,char:FA.run.char,lives:FA.run.lives,girone:FA.run.girone,level:FA.level,own:Object.keys(FA).filter(k=>k==='score'||k==='lives'),"
                   "alias:(()=>{const s0=FA.run.score;FA.score+=7;const d=FA.run.score-s0;FA.score-=7;return d})(),test:FA.test,screen,"
                   "h3:document.querySelector('#fapanel h3').textContent,wv:(document.querySelector('#fawv')||{}).textContent})")
    check("a) «Nuovo gioco» → «Ferma Algidone!»: G === null, run game ferma / char roccia / 3 lives / girone 1, level 1",
          r["G"] is None and (r["game"], r["char"], r["lives"], r["girone"], r["level"]) == ("ferma", "roccia", 3, 1, 0), r)
    check("a) FA.score/FA.lives are aliases of FA.run (never own props)", r["own"] == [] and r["alias"] == 7, r)
    check("a) intro card «Girone 1 · <piano>» and the HUD shows the girone", r["h3"].startswith("Girone 1 · ") and r["wv"] == "Girone 1", r)
    p.evaluate("(()=>{" + UNF + "FA.dead=true;FA=null;S.p.char='algidone';S.quick=null;go('menu')})()"); p.wait_for_timeout(300)
    p.click("[data-tile=new]"); p.wait_for_timeout(600)
    r = p.evaluate("({chooser:!!document.querySelector('[data-rg]'),screen,game:G&&G.game})")
    check("a) Algidone still skips the chooser and starts the maze", not r["chooser"] and r["screen"] == "game" and r["game"] == "maze", r)
    p.evaluate("(()=>{cancelAnimationFrame(raf);G=null;S.p.char='roccia';persist();go('menu')})()"); p.wait_for_timeout(300)
    check("no console errors (a)", not errs, errs)

    # ---------------- b) gironi 1..7 load levels 1,2,3,1,2,3,1
    start_ferma_run(p)
    lv = [p.evaluate("FA.level")]
    for _ in range(6):
        p.evaluate(WIN); click_panel(p, "next"); lv.append(p.evaluate("FA.level"))
    girone = p.evaluate("FA.run.girone")
    check("b) gironi 1..7 play levels 1,2,3,1,2,3,1 (the loop continues after the floor-3 collapse)", [x + 1 for x in lv] == [1, 2, 3, 1, 2, 3, 1] and girone == 7, (lv, girone))
    check("no console errors (b)", not errs, errs)

    # ---------------- c) floor win: credit at the win moment, girone +1 only after «Avanti»; quitting between keeps the credit
    start_ferma_run(p)
    r = p.evaluate("""(()=>{S.ach={prog:{},done:{}};const g0=S.p.ch.roccia.gir;faIntroEnd();FA.alg.wait=1e9;faWin();
      return{g0,g1:S.p.ch.roccia.gir,girone:FA.run.girone,prog:S.ach.prog}})()""")
    check("c) at the win moment: career gironi +1, girone still 1, the «stage» achievement counted girone 1",
          r["g1"] == r["g0"] + 1 and r["girone"] == 1 and 1 in r["prog"].values(), r)
    p.evaluate("(()=>{let i=0;while(FA.state!=='win'&&i<1000){faStep(1/60);i++}})()")
    btns = p.evaluate("[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa)")
    check("c) floor-1 win panel in a run: «Avanti» + «Salva ed esci» (FR1c) + «Esci»", btns == ["next", "savewin", "exit"], btns)
    g_mid = p.evaluate("[FA.run.girone,S.p.ch.roccia.gir]")
    click_panel(p, "next")
    g_after = p.evaluate("[FA.run.girone,S.p.ch.roccia.gir]")
    check("c) «Avanti»: girone +1, no second career credit", g_after == [g_mid[0] + 1, g_mid[1]], (g_mid, g_after))
    # floor 3's panel shows «Avanti» too
    p.evaluate(WIN); click_panel(p, "next"); p.evaluate(WIN)
    btns = p.evaluate("[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa)")
    check("c) floor-3 (collapse) panel in a run: «Avanti» + «Salva ed esci» (FR1c) + «Esci», no «Rigioca»", btns == ["next", "savewin", "exit"] and p.evaluate("FA.level") == 2, btns)
    # quitting between the two moments
    start_ferma_run(p)
    r = p.evaluate("(()=>{const g0=S.p.ch.roccia.gir,s0=S.p.sordi;FA.score=1500;faIntroEnd();FA.alg.wait=1e9;faWin();let i=0;while(FA.state!=='win'&&i<1000){faStep(1/60);i++}return{g0,s0}})()")
    click_panel(p, "exit"); p.wait_for_timeout(300)
    q = p.evaluate("({gir:S.p.ch.roccia.gir,sordi:S.p.sordi,screen,FA,G})")
    check("c) «Esci» between the win and «Avanti»: the girone credit stays, the run ends quietly with its payout (menu)",
          q["gir"] == r["g0"] + 1 and q["sordi"] > r["s0"] and q["screen"] == "menu" and q["FA"] is None and q["G"] is None, (r, q))
    check("no console errors (c)", not errs, errs)

    # ---------------- d) lives refilled at each advance; Hardcore not refilled
    start_ferma_run(p)
    p.evaluate("FA.lives=1"); p.evaluate(WIN); click_panel(p, "next")
    check("d) normal run: lives 1 → 3 at the advance", p.evaluate("FA.lives") == 3 and p.evaluate("FA.run.lives") == 3, p.evaluate("FA.lives"))
    start_ferma_run(p, tile="hard")
    r = p.evaluate("({hard:FA.run.hard,lives:FA.lives})")
    p.evaluate("FA.lives=1"); p.evaluate(WIN); click_panel(p, "next")
    check("d) Hardcore run (3 lives, hard): not refilled at the advance (stays 1)", r == {"hard": True, "lives": 3} and p.evaluate("FA.lives") == 1, (r, p.evaluate("FA.lives")))
    check("no console errors (d)", not errs, errs)

    # ---------------- e) death in a run: soft respawn (floor 3, a bolt already picked)
    start_ferma_run(p)
    p.evaluate(WIN); click_panel(p, "next"); p.evaluate(WIN); click_panel(p, "next")  # girone 3 = floor 3 (bolts)
    p.evaluate(QUIET)
    before = p.evaluate("""(()=>{const b=FA.bolts[0];b.st='gone';FA.gaps[b.g].push(b.x);FA.score=777;FA.items.push({id:999,type:'sausage',x:100,y:100,vx:0,vy:0});
      window.__belt=FA.belt;window.__bolts=FA.bolts;
      return{bolts:JSON.stringify(FA.bolts),gaps:JSON.stringify(FA.gaps),belt:true,stock:FA.stock,score:FA.score,lives:FA.lives,items:FA.items.length}})()""")
    d = p.evaluate(DIE_AND_WAIT)
    after = p.evaluate("({bolts:JSON.stringify(FA.bolts),gaps:JSON.stringify(FA.gaps),belt:FA.belt===window.__belt&&FA.bolts===window.__bolts,stock:FA.stock,score:FA.score,lives:FA.lives,items:FA.items.length,inv:FA.inv,st:FA.state,x:FA.p.x,sx:FA.lv.start.x,wait:FA.alg.wait})")
    check("e) death: lives −1, items cleared, back at the level start, ~2 s invulnerability, throw grace",
          after["lives"] == before["lives"] - 1 and after["items"] == 0 and after["x"] == after["sx"] and 1.9 < after["inv"] <= 2 and after["st"] == "play" and after["wait"] == 2.5, (before["lives"], after))
    check("e) death: picked bolts/holes, belts and score unchanged", (after["bolts"], after["gaps"], after["belt"], after["score"]) == (before["bolts"], before["gaps"], before["belt"], before["score"]), after)
    check("e) death: no forced eat, no stock loss (only the normal drain while dying)", d["eat"] != "eat" and before["stock"] - after["stock"] < 1.5, (d, before["stock"], after["stock"]))
    # control: as of FR1b2, practice ALSO switched to soft respawn (no stock/bite loss on death) -- superseded, see CLAUDE.md FR1b2
    p.evaluate("(()=>{" + UNF + "FA.dead=true;FA=null;go('menu')})()"); p.wait_for_timeout(300)
    p.evaluate("startFerma({test:true})"); p.wait_for_function("FA&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE); p.evaluate(QUIET)
    s0 = p.evaluate("FA.stock"); d = p.evaluate(DIE_AND_WAIT)
    check("e) control — practice now soft-respawns too (FR1b2): no bite, stock unchanged", d["eat"] != "eat" and abs(s0 - p.evaluate("FA.stock")) < 1.5 and p.evaluate("FA.run") is None, (s0, d))
    check("no console errors (e)", not errs, errs)

    # ---------------- f) 0 lives → «Partita finita» with the same numbers as a maze runPayout; «Ancora!»; pause «Esci»
    base = p.evaluate("(()=>{" + UNF + "FA.dead=true;FA=null;S.quick=null;S.ach={prog:{},done:{}};return JSON.stringify({p:S.p,ach:S.ach})})()")
    start_ferma_run(p)
    p.evaluate("(()=>{S.ach=JSON.parse(%s).ach;A_t=0;FA.run.girone=3;FA.lives=1;FA.score=2000;0})()" % json.dumps(base)); p.evaluate(QUIET)
    p.evaluate(DIE_AND_WAIT)
    over = p.evaluate("({st:FA.state,btns:[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa)})")
    check("f) 0 lives → today's lost panel with «Continua»", over == {"st": "over", "btns": ["exit"]}, over)
    click_panel(p, "exit"); p.wait_for_timeout(300)
    fv = p.evaluate("({screen,opt:[...document.querySelectorAll('.opt b')].map(b=>b.textContent),gir:(document.querySelector('.disp')||{}).textContent,sordi:S.p.sordi,exp:S.p.ch.roccia.exp,lvl:S.p.ch.roccia.lvl,FA,G})")
    p.evaluate("(()=>{const s=JSON.parse(%s);S.p=s.p;S.ach=s.ach;A_t=0;cancelAnimationFrame(raf);startGame(false,{});cancelAnimationFrame(raf);G.stage=3;G.score=2000;finishRun();0})()" % json.dumps(base))
    p.wait_for_timeout(300)
    mv = p.evaluate("({screen,opt:[...document.querySelectorAll('.opt b')].map(b=>b.textContent),gir:(document.querySelector('.disp')||{}).textContent,sordi:S.p.sordi,exp:S.p.ch.roccia.exp,lvl:S.p.ch.roccia.lvl})")
    check("f) «Partita finita» after a Ferma run: FA/G null, screen over, Girone 3", fv["screen"] == "over" and fv["FA"] is None and fv["G"] is None and fv["gir"] == "Girone 3", fv)
    check("f) same numbers as a maze runPayout at the same score/girone/difficulty (screen + sordi/XP/level)",
          (fv["opt"], fv["sordi"], fv["exp"], fv["lvl"]) == (mv["opt"], mv["sordi"], mv["exp"], mv["lvl"]), {"ferma": fv["opt"], "maze": mv["opt"]})
    # «Ancora!» after a Ferma run → a new Ferma run
    p.evaluate("(()=>{S.p=JSON.parse(%s).p;0})()" % json.dumps(base))
    start_ferma_run(p); p.evaluate("(()=>{FA.lives=1;0})()"); p.evaluate(QUIET); p.evaluate(DIE_AND_WAIT); click_panel(p, "exit"); p.wait_for_timeout(300)
    p.evaluate(UNFREEZE); p.click("#ag")
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    r = p.evaluate("({G,game:FA.run.game,girone:FA.run.girone,lives:FA.lives})")
    check("f) «Ancora!» after a Ferma run starts a new Ferma run", r == {"G": None, "game": "ferma", "girone": 1, "lives": 3}, r)
    # pause «Esci» = quiet end with payout
    p.evaluate(FREEZE); p.evaluate("(()=>{faIntroEnd();FA.score=1500;0})()")
    s0 = p.evaluate("S.p.sordi")
    p.click("#fap"); p.wait_for_timeout(150); click_panel(p, "exit"); p.wait_for_timeout(300)
    r = p.evaluate("({screen,sordi:S.p.sordi,FA,G,toast:(document.querySelector('#toasts')||{}).textContent||''})")
    check("f) pause «Esci» in a run: quiet end (menu + «Partita abbandonata» toast) with payout, FA null", r["screen"] == "menu" and r["sordi"] > s0 and r["FA"] is None and "abbandonata" in r["toast"], (s0, r))
    check("no console errors (f)", not errs, errs)
    ctx.close()

    # ---------------- g) dev run from girone 5 via the new button: level 2, no progress, no S.quick
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=True)
    settle(p, 600)
    p.evaluate("S.quick={keep:1};persist();go('menu')"); p.wait_for_timeout(300)
    before = p.evaluate(SNAP)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(#jgFa)').open"):
        p.click("details.acc:has(#jgFa) > summary"); p.wait_for_timeout(250)
    p.fill("#jgN", "5"); p.click("#jgFa")
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE)
    r = p.evaluate("({dev:FA.run.dev,girone:FA.run.girone,level:FA.level,G,test:FA.test})")
    check("g) «Partita Ferma dal girone N» (5): dev run, girone 5, level 2 (Macelleria), G null", r == {"dev": True, "girone": 5, "level": 1, "G": None, "test": True}, r)
    p.evaluate(WIN); click_panel(p, "next"); p.evaluate(QUIET); p.evaluate("FA.lives=1"); p.evaluate(DIE_AND_WAIT); click_panel(p, "exit"); p.wait_for_timeout(300)
    after = p.evaluate(SNAP)
    check("g) dev run: win + advance + game over write no progress (S.p, achievements) and leave S.quick untouched", after == before and p.evaluate("screen") == "over", (json.loads(before)["quick"], json.loads(after)["quick"]))
    check("no console errors (g)", not errs, errs)
    ctx.close()

    # ---------------- h) activeRun(): maze results identical to the previous build (golden)
    import functools, http.server, threading
    class OH(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    osrv = http.server.ThreadingHTTPServer(("127.0.0.1", OLD_PORT), functools.partial(OH, directory=OLD_DIR))
    threading.Thread(target=osrv.serve_forever, daemon=True).start()
    PROBE = """(()=>{const out=[],key=()=>Object.keys(DIFF).find(k=>DIFF[k]===dfc());
      const blocked=()=>{const p0=JSON.stringify(S.ach.prog);ach('run',{ch:'roccia',d:'hard'});const b=JSON.stringify(S.ach.prog)===p0;return b};
      for(const dev of [false,true])for(const diff of ['easy','medium','hard'])for(const ch of ['roccia','algidone']){
        cancelAnimationFrame(raf);startGame(false,{});cancelAnimationFrame(raf);G.dev=dev;G.diff=diff;G.char=ch;S.ach={prog:{},done:{}};
        out.push({dev,diff,ch,dfc:key(),gcar:gcar(),curD:curD(),blocked:blocked()})}
      cancelAnimationFrame(raf);G=null;S.ach={prog:{},done:{}};out.push({g:null,dfc:key(),gcar:gcar(),curD:curD(),blocked:blocked()});
      G={dev:true,diff:'easy',char:'algidone'};S.ach={prog:{},done:{}};out.push({g:'plain',dfc:key(),gcar:gcar(),curD:curD(),blocked:blocked()});G=null;
      return JSON.stringify(out)})()"""
    res = {}
    for label, base_url in (("old", OLD_BASE), ("new", NEW_BASE)):
        BASE = base_url
        ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=False)
        settle(p, 600)
        res[label] = (p.evaluate(PROBE), list(errs))
        ctx.close()
    BASE = NEW_BASE
    check("h) maze run (dev × diff × char), G=null and a plain G: dfc/gcar/curD/ach blocking identical to %s" % BASE_REF,
          res["old"][0] == res["new"][0], {"old": res["old"][0][:200], "new": res["new"][0][:200]})
    check("h) sanity: the probe saw a dev run blocked and a normal run not", '"dev":true,"diff":"easy","ch":"roccia","dfc":"easy","gcar":"roccia","curD":"easy","blocked":true' in res["new"][0]
          and '"dev":false,"diff":"easy","ch":"roccia","dfc":"easy","gcar":"roccia","curD":"easy","blocked":false' in res["new"][0], res["new"][0][:300])
    check("no console errors (h, both builds)", not res["old"][1] and not res["new"][1], (res["old"][1], res["new"][1]))
    b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
