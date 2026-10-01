#!/usr/bin/env python3
"""0.4.5_38 (FR2b) tests: encounters between Ferma-run gironi. faGapRoll (rolled once after onGironeAdvance, stored as
run.gap), faPlayGap (Ferma torn down, El Gamblador with host = the live run, or the interlude card), RUN_BACK.ferma
(the next level from the live run), «Salva ed esci» on the win panel + «Gioco corrente» playing the owed gap once,
old quicksaves without gap, no Ferma-in-Ferma, dev rules (GAM_FORCE only, x5 interlude, start score 1500).
Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_fr2b.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

FREEZE = "(()=>{window.__raf=window.__raf||window.requestAnimationFrame;window.requestAnimationFrame=()=>0;if(FA)cancelAnimationFrame(FA.raf);if(typeof raf!=='undefined')cancelAnimationFrame(raf);0})()"
UNF = "(()=>{if(window.__raf)window.requestAnimationFrame=window.__raf;0})()"
QUIET = "(()=>{faIntroEnd();Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;0})()"
BJ_AUTO = """(items=>{const ids=items.map(i=>i.id);if(ids.includes('presentation'))return true;if(ids.includes('stand'))return 'stand';if(ids.includes('leave'))return 'leave';return ids[0]})"""
SHOE = "(()=>{const s=[];for(let i=0;i<30;i++)s.push({r:2,s:1});s.push({r:7,s:0},{r:10,s:0},{r:10,s:0},{r:10,s:0});return s})()"
# spies: startGamblador auto-plays (and is counted), faInvite counted, the last table score captured at bjExit
SPIES = """(()=>{if(window.__spied)return 0;window.__spied=1;window.__gamb=0;window.__inv=0;window.__bjEnd=null;
  window.bjNewShoe=()=>%s;
  const sg=startGamblador;window.startGamblador=o=>{o=o||{};window.__gamb++;o.auto=%s;return sg(o)};
  const fi=faInvite;window.faInvite=o=>{window.__inv++;return fi(o)};
  const be=bjExit;window.bjExit=()=>{if(B&&!B.dead)window.__bjEnd=bjScore();return be()};
  const gr=faGapRoll;window.__rolls=[];window.faGapRoll=r=>{const v=gr(r);window.__rolls.push(v);return v};0})()""" % (SHOE, BJ_AUTO)


def to_menu(p, keep_quick=False):
    p.evaluate(UNF)
    p.evaluate("(()=>{if(FA){FA.dead=true;cancelAnimationFrame(FA.raf);FA=null}if(typeof B!=='undefined'&&B&&!B.dead){B.dead=true;B=null}cancelAnimationFrame(raf);G=null;%sgo('menu');0})()" % ("" if keep_quick else "S.quick=null;persist();"))
    p.wait_for_timeout(300)
    m = p.evaluate("(document.querySelector('#modal .ov')||{}).textContent||''")
    if m:
        print("   (closing menu popup: %s)" % m[:80])
        p.evaluate("closeModal();0")


def start_run(p, girone, score):
    to_menu(p)
    p.click("[data-tile=new]"); p.wait_for_timeout(300); p.click("[data-rg=ferma]")
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)
    # jump the live run to the wanted girone (on its own level), then win it
    p.evaluate("(()=>{FA.run.girone=%d;faLoadFloor((FA.run.girone-1)%%3,FA.lives,%d);0})()" % (girone, score))


def start_dev_run(p, girone):
    to_menu(p)
    p.evaluate("startFermaRun({girone:%d,dev:true});0" % girone)
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def win_floor(p, score=None):
    p.evaluate(QUIET)
    p.evaluate("Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;if(FA.level<2)faWin();else faFinalWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)")
    p.evaluate("for(let i=0;i<90;i++)faStep(1/60)")
    if score is not None:  # force the girone's final score (count-up included)
        p.evaluate("FA.cnt.base=%d;FA.cnt.bonus=0;FA.cnt.shown=0;FA.score=%d;0" % (score, score))


def click_next(p):
    p.evaluate("window.__run=FA.run;window.__rolls=[];0")
    p.evaluate(UNF)
    p.click("#fapanel [data-fa=next]")


def wait_level(p, girone):
    p.wait_for_function("screen==='fa'&&FA&&FA.run&&FA.run.girone===%d&&FA.state==='intro'" % girone, timeout=90000)
    p.wait_for_timeout(300)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=True)
    settle(p, 600)
    p.evaluate("S.opts.music=true;persist();0")
    p.evaluate(SPIES)

    # ================= a) real run, girone 4 -> 5 with score over the gate: El Gamblador, then girone 5's level from the live run
    p.evaluate("S.p.gam.visits=0;S.p.fa.enc=0;FA_FORCE.on=true;persist();0")
    start_run(p, 4, 0)
    p.evaluate("FA.lives=1;0")  # lost two lives in girone 4: the advance must refill them
    win_floor(p, 5000)
    p.evaluate("window.__gamb=0;window.__inv=0;0")
    click_next(p)
    p.wait_for_function("typeof B!=='undefined'&&B&&B.run", timeout=15000)
    a = p.evaluate("({rolls:window.__rolls.slice(),gap:window.__run.gap,FA:FA,musicPaused:!musicFa||musicFa.paused,hostIsRun:B.host===window.__run,price:B.price,visits:S.p.gam.visits,activeIsHost:activeRun()===B.host,screen})")
    check("a) gap rolled exactly once, \"gamb\"", a["rolls"] == ["gamb"], a["rolls"])
    check("a) gap consumed (run.gap null) before the table", a["gap"] is None, a["gap"])
    check("a) Ferma torn down (FA null, music.fa paused, screen bj)", a["FA"] is None and a["musicPaused"] and a["screen"] == "bj", a)
    check("a) B.host === the live Ferma run", a["hostIsRun"] is True, a)
    check("a) real run: S.p.gam.visits++ as in the maze", a["visits"] == 1, a["visits"])
    check("a) activeRun() during the table = the host run", a["activeIsHost"] is True, a)
    wait_level(p, 5)
    a2 = p.evaluate("({same:FA.run===window.__run,level:FA.level,score:FA.run.score,end:window.__bjEnd,lives:FA.run.lives,ref:FA_RUN.lives,gap:FA.run.gap,inv:window.__inv,force:FA_FORCE.on,quick:FA.quick&&FA.quick.run.score})")
    check("a) back in Ferma from the LIVE run object, girone 5 at level (5-1)%3 = 1", a2["same"] is True and a2["level"] == 1, a2)
    check("a) score = the table's result", a2["score"] == a2["end"] and a2["end"] is not None, a2)
    check("a) lives = the refill value (1 -> 3)", a2["lives"] == a2["ref"] == 3, a2)
    check("a) girone-start snapshot taken from the post-table run", a2["quick"] == a2["score"], a2)
    check("a) no Ferma invite, FA_FORCE left set", a2["inv"] == 0 and a2["force"] is True, a2)
    p.wait_for_function("musicFa&&!musicFa.paused", timeout=8000)
    check("a) music.fa playing again", p.evaluate("!musicFa.paused") is True, "")
    p.evaluate(FREEZE)

    # ================= b) under the gate: no table
    start_run(p, 4, 0)
    win_floor(p, 20)
    p.evaluate("window.__gamb=0;0")
    click_next(p)
    p.wait_for_timeout(500)
    bb = p.evaluate("({rolls:window.__rolls.slice(),gamb:window.__gamb,title:(document.querySelector('#modal h3')||{}).textContent||''})")
    check("b) girone 5 under the gate: no El Gamblador; the x5 card instead (gap \"inter\")", bb["gamb"] == 0 and bb["rolls"] == ["inter"] and "5" in bb["title"], bb)
    p.click("#mgo"); wait_level(p, 5)
    check("b) «Avanti» on the card loads girone 5's level", p.evaluate("FA.level") == 1, p.evaluate("FA.level"))
    p.evaluate(FREEZE)
    start_run(p, 6, 0)
    win_floor(p, 20)
    p.evaluate("window.__gamb=0;window.__mr=Math.random;Math.random=()=>0.01;0")
    click_next(p)
    p.evaluate("Math.random=window.__mr;0")
    wait_level(p, 7)
    bb2 = p.evaluate("({rolls:window.__rolls.slice(),gamb:window.__gamb,modal:!!document.querySelector('#modal .ov')})")
    check("b) girone 7, 15% hit but under the gate: no table, no card, level loads directly", bb2["rolls"] == [None] and bb2["gamb"] == 0 and not bb2["modal"], bb2)
    p.evaluate(FREEZE)

    # ================= c) girone 10, no table -> interlude naming Ferma Algidone!
    start_run(p, 9, 0)
    win_floor(p, 5000)
    p.evaluate("window.__gamb=0;window.__mr=Math.random;Math.random=()=>0.99;0")
    click_next(p)
    p.evaluate("Math.random=window.__mr;0")
    p.wait_for_selector("#mgo", timeout=5000)
    c = p.evaluate("({rolls:window.__rolls.slice(),title:document.querySelector('#modal h3').textContent,txt:document.querySelector('#modal p').textContent,FA:FA,gamb:window.__gamb})")
    check("c) girone 10: gap \"inter\", no table, Ferma torn down", c["rolls"] == ["inter"] and c["gamb"] == 0 and c["FA"] is None, c)
    check("c) card titled «Girone 10» and names «Ferma Algidone!»", c["title"] == "Girone 10" and "Ferma Algidone!" in c["txt"], c)
    p.click("#mgo"); wait_level(p, 10)
    check("c) «Avanti» loads girone 10 at level (10-1)%3 = 0", p.evaluate("FA.level===0&&FA.run===window.__run") is True, "")
    p.evaluate(FREEZE)

    # ================= d) 15%: just below / just above
    d = p.evaluate("""(()=>{const mr=Math.random,o={};
      Math.random=()=>0.1499;o.below=faGapRoll(mkRun({girone:7,score:5000,game:'ferma'}));
      Math.random=()=>0.1501;o.above=faGapRoll(mkRun({girone:7,score:5000,game:'ferma'}));
      Math.random=mr;o.odds=GAM_ODDS;return o})()""")
    check("d) GAM_ODDS = .15; just below -> table, just above -> none", d == {"below": "gamb", "above": None, "odds": 0.15}, d)

    # ================= e) sweep 5-20: never a Ferma invite, FA_FORCE untouched
    e = p.evaluate("""(()=>{const mr=Math.random,out=[];S.p.fa.enc=0;FA_FORCE.on=true;window.__inv=0;
      for(const v of [0.01,0.5,0.99]){Math.random=()=>v;for(let g=5;g<=20;g++)out.push(faGapRoll(mkRun({girone:g,score:5000,game:'ferma'})))}
      Math.random=mr;return {inv:window.__inv,force:FA_FORCE.on,kinds:[...new Set(out.map(String))].sort()}})()""")
    check("e) gironi 5-20 (enc 0, FA_FORCE on): faInvite never called, FA_FORCE still set", e["inv"] == 0 and e["force"] is True, e)
    check("e) only \"gamb\"/\"inter\"/null ever rolled", set(e["kinds"]) <= {"gamb", "inter", "null"}, e["kinds"])
    p.evaluate("FA_FORCE.on=false;0")

    # ================= f) win «Salva ed esci» on the girone-5 advance; «Gioco corrente» plays the owed table once
    start_run(p, 4, 0)
    p.evaluate("FA.lives=1;0")
    win_floor(p, 5000)
    p.evaluate("window.__gamb=0;0")
    p.evaluate(UNF)
    p.click("#fapanel [data-fa=savewin]"); p.wait_for_timeout(600)
    p.evaluate("closeModal();0")  # the menu's own "Nuovo personaggio" unlock card (girone 5 reached)
    f = p.evaluate("({lives:S.quick&&S.quick.run.lives,gap:S.quick&&S.quick.run.gap,gir:S.quick&&S.quick.run.girone,saved:JSON.parse(localStorage.getItem('mgs_v1')).quick.run.gap,screen,gamb:window.__gamb})")
    check("f) win «Salva ed esci»: S.quick.run.gap \"gamb\" (saved unplayed, persisted), menu, no table yet", f["gap"] == "gamb" and f["saved"] == "gamb" and f["lives"] == 3 and f["gir"] == 5 and f["screen"] == "menu" and f["gamb"] == 0, f)
    p.click("[data-tile=cur]")
    p.wait_for_function("typeof B!=='undefined'&&B&&B.run", timeout=15000)
    f2 = p.evaluate("({gamb:window.__gamb,qgap:S.quick.run.gap,stored:JSON.parse(localStorage.getItem('mgs_v1')).quick.run.gap,host:B.host.girone})")
    check("f) «Gioco corrente»: El Gamblador first; the gap is cleared in S.quick (persisted) as it starts", f2["gamb"] == 1 and f2["qgap"] is None and f2["stored"] is None and f2["host"] == 5, f2)
    wait_level(p, 5)
    check("f) after the table: girone 5's level", p.evaluate("FA.level===1&&FA.run.gap===null") is True, "")
    p.evaluate(FREEZE)
    to_menu(p, keep_quick=True)
    p.evaluate("window.__gamb=0;0")
    p.click("[data-tile=cur]"); wait_level(p, 5)
    check("f) a second «Gioco corrente» does not replay the table", p.evaluate("window.__gamb") == 0, p.evaluate("window.__gamb"))
    p.evaluate(FREEZE)

    # ================= g) old Ferma quicksave without gap
    to_menu(p)
    p.evaluate("(()=>{const r=mkRun({girone:4,score:300,game:'ferma',char:'roccia',lives:3});S.quick={game:'ferma',run:r};persist();window.__gamb=0;go('menu');0})()")
    p.wait_for_timeout(300); p.evaluate("closeModal();0")
    p.click("[data-tile=cur]"); wait_level(p, 4)
    g = p.evaluate("({level:FA.level,score:FA.run.score,gap:FA.run.gap,gamb:window.__gamb})")
    check("g) old quicksave (no gap): resumes as before, gap null, no table", g == {"level": 0, "score": 300, "gap": None, "gamb": 0}, g)
    p.evaluate(FREEZE)

    # ================= h) dev (inferred from D5 / task 1: the brief's own h) was cut off)
    p.evaluate("S.p.gam.visits=0;S.p.gam.seen=false;persist();0")
    start_dev_run(p, 1)
    check("h) dev Ferma run starts at 1500", p.evaluate("FA.run.score") == 1500, p.evaluate("FA.run.score"))
    to_menu(p)
    p.evaluate("startFermaRun({girone:1});0"); p.wait_for_function("FA&&FA.run", timeout=15000); p.evaluate(FREEZE)
    check("h) a real Ferma run still starts at 0", p.evaluate("FA.run.score") == 0, p.evaluate("FA.run.score"))
    # no own rolls: girone 4 -> 5 with Math.random 0 -> no table, the x5 card (mirrors the maze dev branch)
    start_dev_run(p, 4)
    win_floor(p, 5000)
    p.evaluate("window.__gamb=0;window.__mr=Math.random;Math.random=()=>0;FA_FORCE.on=true;0")
    click_next(p)
    p.evaluate("Math.random=window.__mr;0")
    p.wait_for_selector("#mgo", timeout=5000)
    h1 = p.evaluate("({rolls:window.__rolls.slice(),gamb:window.__gamb,force:FA_FORCE.on})")
    check("h) dev: no own El Gamblador roll at girone 5, x5 card shown, FA_FORCE unconsumed", h1["rolls"] == ["inter"] and h1["gamb"] == 0 and h1["force"] is True, h1)
    p.click("#mgo"); wait_level(p, 5); p.evaluate(FREEZE)
    p.evaluate("FA_FORCE.on=false;0")
    # GAM_FORCE: fires once at girone 3, never touches S.p.gam, blocks achievements through the host
    start_dev_run(p, 2)
    win_floor(p, 5000)
    p.evaluate("window.__gamb=0;GAM_FORCE.on=true;0")
    click_next(p)
    p.wait_for_function("typeof B!=='undefined'&&B&&B.run", timeout=15000)
    h2 = p.evaluate("({rolls:window.__rolls.slice(),force:GAM_FORCE.on,dev:B.host.dev,visits:S.p.gam.visits,seen:S.p.gam.seen,active:activeRun()===B.host})")
    check("h) dev: «Forza El Gamblador» fires at girone 3, consumed", h2["rolls"] == ["gamb"] and h2["force"] is False and h2["dev"] is True, h2)
    check("h) dev: S.p.gam untouched, activeRun() = the dev host (ach blocked)", h2["visits"] == 0 and h2["seen"] is False and h2["active"] is True, h2)
    wait_level(p, 3)
    check("h) dev: after the table, girone 3's level; S.p.gam.visits still 0", p.evaluate("FA.level===2&&S.p.gam.visits===0") is True, "")
    p.evaluate(FREEZE)
    start_dev_run(p, 2)
    win_floor(p, 10)
    p.evaluate("window.__gamb=0;GAM_FORCE.on=true;window.__t=null;const o=toast;window.toast=m=>{window.__t=m;o(m)};0")
    click_next(p)
    wait_level(p, 3)
    h3 = p.evaluate("({rolls:window.__rolls.slice(),gamb:window.__gamb,force:GAM_FORCE.on,t:window.__t})")
    check("h) dev: GAM_FORCE under the gate -> toast, consumed, no table, level loads", h3["rolls"] == [None] and h3["gamb"] == 0 and h3["force"] is False and h3["t"] == "El Gamblador: punti insufficienti", h3)
    p.evaluate(FREEZE)

    # ================= RUN tables
    k = p.evaluate("({hold:Object.keys(RUN_HOLD),back:Object.keys(RUN_BACK)})")
    check("RUN_HOLD/RUN_BACK: \"maze\" + \"ferma\"", k["hold"] == ["maze", "ferma"] and k["back"] == ["maze", "ferma"], k)
    check("no console errors", not errs, errs)
    ctx.close()

print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
