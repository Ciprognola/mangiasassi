#!/usr/bin/env python3
"""0.4.5_30 (FR1a2) tests: the Ferma buttons clear of the bug icon (HUD fits, every panel button is the topmost element at its centre at
390x844 and 360x740) and the eat-driven time bar of the Ferma RUN (FA_RUN.bar: L/N per loop, bites on schedule only, clock pauses,
bite = 1/N, floor bonus = uneaten bites x 100, last-bite ending, dev readout/button). Practice and the maze encounter are golden-compared
against BASE_REF (default 94359d0 = 0.4.5_29). Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_fr1a2.py
Section h) (practice/the maze encounter's old stock mechanic) was superseded by FR1b2 (0.4.5_33, both switched to the
eat-driven bar) and now checks the new behaviour directly rather than diffing against BASE_REF; OLD_BASE/OLD_PORT/OLD_DIR
are unused leftovers from that golden comparison, kept rather than touching the file more than this chunk needs."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

BASE_REF = os.environ.get("BASE_REF", "94359d0")
OLD_PORT = 8796
OLD_DIR = tempfile.mkdtemp(prefix="mgs_old_")
open(os.path.join(OLD_DIR, "index.html"), "wb").write(subprocess.run(["git", "show", BASE_REF + ":index.html"], cwd=ROOT, capture_output=True, check=True).stdout)
NEW_BASE, OLD_BASE = BASE, "http://127.0.0.1:%d/" % OLD_PORT

SEED = """(a=>{window.__s=a;Math.random=()=>{let t=(window.__s=window.__s+0x6D2B79F5|0);t=Math.imul(t^t>>>15,1|t);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}})(%d)"""
FREEZE = "(()=>{window.__raf=window.__raf||window.requestAnimationFrame;window.requestAnimationFrame=()=>0;if(FA)cancelAnimationFrame(FA.raf);0})()"
UNF = "if(window.__raf)window.requestAnimationFrame=window.__raf;"
QUIET = "(()=>{faIntroEnd();Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;0})()"
STEP = "(n=>{for(let i=0;i<n;i++)faStep(1/60)})"
TAP = """(()=>{const out=[];
  for(const b of document.querySelectorAll('#fapanel [data-fa],#fap')){const r=b.getBoundingClientRect(),cx=r.left+r.width/2,cy=r.top+r.height/2,el=document.elementFromPoint(cx,cy);
    out.push({txt:b.textContent.trim(),hit:(el===b||b.contains(el)),inView:r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight,top:el&&(el.id||el.className||el.tagName)})}
  const h=document.querySelector('#fahud'),bug=document.querySelector('#bugb'),ps=document.querySelector('#fap'),bl=bug&&bug.getBoundingClientRect(),pl=ps.getBoundingClientRect();
  return{btns:out,hudFits:h.scrollWidth<=h.clientWidth,bugShown:!!bug,noOverlap:!bl||bl.right<=pl.left||bl.left>=pl.right}})()"""


def fresh(b, w, h, dev=True):
    VIEW.update({"width": w, "height": h})
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=dev)
    settle(p, 600)
    return ctx, p, errs


def start_run(p, tile="new"):
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}G=null;S.quick=null;persist();go('menu')})()"); p.wait_for_timeout(300)
    p.click("[data-tile=%s]" % tile); p.wait_for_timeout(300); p.click("[data-rg=ferma]")
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_dev_run(p, girone=1):
    p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}G=null;S.quick=null;go('menu');startFermaRun({girone:%d,dev:true});0})()" % girone)
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)

    # ================= a) «Esci» / every Ferma button reachable, at both phone sizes (dev session: the bug icon is shown)
    for (w, h) in ((390, 844), (360, 740)):
        ctx, p, errs = fresh(b, w, h)
        seen = {}
        def tap(label):
            r = p.evaluate(TAP); seen[label] = r
            bad = [x for x in r["btns"] if not (x["hit"] and x["inView"])]
            check("a) %dx%d %s: every button is the topmost element at its centre (%s)" % (w, h, label, ", ".join(x["txt"] for x in r["btns"])), not bad and r["btns"], bad)
        start_run(p)
        r = p.evaluate(TAP)
        check("a) %dx%d run HUD fits the screen, bug icon shown and not overlapping the pause button, pause button reachable" % (w, h),
              r["hudFits"] and r["bugShown"] and r["noOverlap"] and r["btns"][0]["hit"] and r["btns"][0]["inView"], r)
        p.evaluate("faIntroEnd();faPause(true)"); tap("run pause (dev: +Ultimo morso)")
        p.evaluate("faPause(false);Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;faWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)"); tap("run win floor 1")
        p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd()")
        p.evaluate("Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;faWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)"); p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd()")
        p.evaluate("Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;faFinalWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)"); tap("run win floor 3")
        p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd();FA.state='play';FA.lives=1;faDie('x',true);for(let i=0;i<200&&FA.state==='dying';i++)faStep(1/60)"); tap("run lost (0 lives)")
        start_run(p); p.evaluate(QUIET)
        p.evaluate("FA.bar.left=1;FA.bar.pending=true;for(let i=0;i<400&&FA.state!=='over';i++)faStep(1/60)"); tap("run last-bite popup")
        check("a) %dx%d last-bite popup title/button" % (w, h), p.evaluate("document.querySelector('#fapanel h3').textContent") == "Algidone ha finito tutto!", None)
        # practice + encounter (same buttons as before; must also be clear of the icon)
        p.evaluate("(()=>{" + UNF + "FA.dead=true;FA=null;go('menu')})()"); p.wait_for_timeout(300)
        p.evaluate("startFerma({test:true})"); p.wait_for_function("FA&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE)
        p.evaluate("faIntroEnd();faPause(true)"); tap("practice pause")
        p.evaluate("faPause(false);FA.alg.wait=1e9;Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});faWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)"); tap("practice win")
        p.evaluate("FA.state='play';FA.lives=1;faDie('x',true);for(let i=0;i<200&&FA.state==='dying';i++)faStep(1/60)"); tap("practice over")
        p.evaluate("(()=>{" + UNF + "FA.dead=true;FA=null;go('menu')})()"); p.wait_for_timeout(300)
        p.evaluate("startFerma({test:true,encounter:2})"); p.wait_for_function("FA&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE)
        p.evaluate("faIntroEnd();faPause(true)"); tap("encounter pause")
        p.evaluate("faPause(false);FA.alg.wait=1e9;Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});faWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)"); tap("encounter win")
        check("a) %dx%d practice/encounter HUD fits too" % (w, h), p.evaluate(TAP)["hudFits"])
        check("no console errors (a %dx%d)" % (w, h), not errs, errs)
        ctx.close()

    VIEW.update({"width": 390, "height": 844})
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=True)
    settle(p, 600)

    # ================= b) L / N per loop, seeded
    p.evaluate(SEED % 1234)
    res = {}
    for g in (1, 4, 7, 10):
        start_dev_run(p, g); res[g] = p.evaluate("({L:FA.bar.L,N:FA.bar.N,left:FA.bar.left,shown:FA.bar.shown,stock:FA.stock,full:FA.lv.stock,girone:FA.run.girone})")
    want = {1: (120, 12), 4: (105, 10), 7: (90, 8), 10: (75, 6)}
    check("b) gironi 1/4/7/10: L = 120/105/90/75 and N within 12±1 / 10±1 / 8±1 / 6±1, bar full",
          all(res[g]["L"] == want[g][0] and abs(res[g]["N"] - want[g][1]) <= 1 and res[g]["left"] == res[g]["N"] and res[g]["stock"] == res[g]["full"] for g in want), res)
    ns = set()
    for i in range(40):
        start_dev_run(p, 4); ns.add(p.evaluate("FA.bar.N"))
    check("b) N is random in [−1,+1] around the loop value (girone 4: 9, 10 and 11 all show up, nothing else)", ns == {9, 10, 11}, sorted(ns))
    check("no console errors (b)", not errs, errs)

    # ================= c) bites only on schedule, over a whole level
    p.evaluate(SEED % 777); start_dev_run(p, 1)
    r = p.evaluate("""(()=>{faIntroEnd();FA.inv=1e9;const B=FA.bar,log=[],eats=[];let prevA=FA.alg.state,rnd=0;
      const fb=faBite;window.faBite=function(){log.push({clock:B.clock,due:B.due,pending:B.pending});fb()};
      for(let i=0;i<60*60;i++){faStep(1/60);if(FA.alg.state==='eat'&&prevA!=='eat')eats.push(B.clock);prevA=FA.alg.state;if(FA.lb)break}
      window.faBite=fb;return{log,eats,L:B.L,N:B.N,left:B.left,clock:B.clock,throws:FA.throws}})()""")
    gaps = [r["log"][0]["due"]] + [r["log"][i]["due"] - r["log"][i - 1]["due"] for i in range(1, len(r["log"]))]
    # `due` is logged BEFORE faBite advances it: log[k].due = scheduled time of bite k
    per = r["L"] / r["N"]
    check("c) 60 s of play with throws active: Algidone ate exactly as many times as bites were scheduled (no random eat)", len(r["eats"]) == len(r["log"]) and r["N"] - r["left"] == len(r["log"]) and r["throws"] > 5, (len(r["eats"]), len(r["log"]), r["throws"]))
    check("c) every scheduled interval is within (L/N)·(1±0.15)", all(per * .85 - 1e-6 <= g_ <= per * 1.15 + 1e-6 for g_ in gaps), (per, [round(x, 2) for x in gaps]))
    check("c) each bite happens at/after its due time, and no later than the wait for a throw in progress", all(0 <= e - l["due"] < 2.5 for e, l in zip(r["eats"], r["log"])), [(round(e, 2), round(l["due"], 2)) for e, l in zip(r["eats"], r["log"])])
    # a whole level on a fresh run: the last due ≈ L
    p.evaluate(SEED % 99); start_dev_run(p, 1)
    r3 = p.evaluate("""(()=>{faIntroEnd();FA.inv=1e9;const B=FA.bar,fb=faBite,dues=[];window.faBite=function(){dues.push(B.due);fb()};
      for(let i=0;i<60*200&&!FA.lb;i++)faStep(1/60);window.faBite=fb;return{dues,L:B.L,N:B.N,lb:!!FA.lb,clock:B.clock}})()""")
    check("c) a whole level: N bites, the last one due at ≈ L (within ±15%), the level ends with the last bite", r3["lb"] and len(r3["dues"]) == r3["N"] and .85 * r3["L"] <= r3["dues"][-1] <= 1.15 * r3["L"] + 1e-6, (r3["N"], r3["L"], r3["dues"][-1]))
    check("no console errors (c)", not errs, errs)

    # ================= d) the clock: paused in intro / pause / death animation / win; running during the respawn invulnerability
    start_dev_run(p, 1)
    clk = lambda: p.evaluate("FA.bar.clock")
    c0 = clk(); p.evaluate("for(let i=0;i<30;i++){FA.introT=9;faStep(1/60)}")
    check("d) clock paused during the intro card", clk() == c0 and p.evaluate("FA.state") == "intro", (c0, clk()))
    p.evaluate(QUIET); p.evaluate("FA.inv=0;" + STEP + "(60)"); c1 = clk()
    check("d) clock runs while playing", c1 > c0 + .9, (c0, c1))
    p.evaluate("faPause(true)"); p.evaluate(STEP + "(60)")
    check("d) clock paused during the pause menu", clk() == c1, (c1, clk())); p.evaluate("faPause(false)")
    p.evaluate("faDie('x',true)"); p.evaluate(STEP + "(20)")
    check("d) clock paused during the death animation", p.evaluate("FA.state") == "dying" and clk() == c1, (c1, clk(), p.evaluate("FA.state")))
    p.evaluate("for(let i=0;i<200&&FA.state==='dying';i++)faStep(1/60)")
    p.evaluate("FA.alg.wait=1e9;" + STEP + "(60)"); c2 = clk()
    check("d) clock runs again during the 2 s respawn invulnerability", p.evaluate("FA.inv") > 0 and c2 > c1 + .9, (c1, c2, p.evaluate("FA.inv")))
    p.evaluate("FA.inv=0;faWin()"); c3 = clk(); p.evaluate("for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60);" + STEP + "(120)")
    check("d) clock paused through the win sequence and its panel", p.evaluate("FA.state") == "win" and clk() == c3, (c3, clk()))
    check("no console errors (d)", not errs, errs)

    # ================= e) a death costs no bite and no bar; a bite removes exactly 1/N
    start_dev_run(p, 4); p.evaluate(QUIET); p.evaluate("FA.inv=0")
    b0 = p.evaluate("({left:FA.bar.left,N:FA.bar.N,shown:FA.bar.shown,stock:FA.stock,due:FA.bar.due})")
    p.evaluate("faDie('x',true)"); d = p.evaluate("(()=>{const eat=FA.alg.state;for(let i=0;i<200&&FA.state==='dying';i++)faStep(1/60);return{eat,state:FA.state,left:FA.bar.left,shown:FA.bar.shown,stock:FA.stock,alg:FA.alg.state}})()")
    check("e) death in a run: no bite, bar untouched, Algidone not eating", d["eat"] != "eat" and d["alg"] != "eat" and d["left"] == b0["left"] and d["shown"] == b0["shown"] and d["stock"] == b0["stock"], (b0, d))
    e = p.evaluate("""(()=>{const B=FA.bar,l0=B.left,N=B.N;B.pending=true;FA.alg.state='idle';FA.alg.wait=0;FA.inv=1e9;faStep(1/60);const l1=B.left,st=FA.alg.state;
      for(let i=0;i<120;i++)faStep(1/60);return{l0,l1,st,N,shown:B.shown,want:(l0-1)/N,stock:FA.stock,full:FA.lv.stock}})()""")
    check("e) a bite removes exactly 1/N of the bar (left −1, bar → (left)/N with a smooth drain, stock scaled)", e["l1"] == e["l0"] - 1 and e["st"] == "eat" and abs(e["shown"] - e["want"]) < 1e-9 and abs(e["stock"] - e["full"] * e["want"]) < 1e-6, e)
    mid = p.evaluate("""(()=>{const B=FA.bar;B.pending=true;FA.alg.state='idle';FA.alg.wait=0;const s0=B.shown;faStep(1/60);faStep(1/60);faStep(1/60);return{s0,s1:B.shown,tgt:B.left/B.N}})()""")
    check("e) the drain is smooth (the bar is between the old and the new value a few frames after the bite)", mid["tgt"] < mid["s1"] < mid["s0"], mid)
    # a bite that falls due mid-throw waits for the throw to finish
    w = p.evaluate("""(()=>{FA.alg.state='throw';FA.alg.t=0;FA.alg.released=false;FA.alg.pick=null;const B=FA.bar,l0=B.left;B.pending=true;let inThrow=0;
      for(let i=0;i<200&&FA.alg.state==='throw';i++){faStep(1/60);if(B.left!==l0)inThrow++}return{inThrow,after:FA.alg.state,eatNext:(()=>{faStep(1/60);return FA.alg.state+':'+B.left+'/'+l0})()}})()""")
    check("e) a bite due mid-throw waits for the throw animation, then Algidone eats", w["inThrow"] == 0 and w["after"] == "idle" and w["eatNext"].startswith("eat:"), w)
    check("no console errors (e)", not errs, errs)

    # ================= f) floor win: bonus = uneaten bites × 100, bar frozen
    start_dev_run(p, 1); p.evaluate(QUIET)
    f = p.evaluate("""(()=>{const B=FA.bar;B.left=7;B.N=12;B.shown=7/12+.05;FA.score=500;faWin();const at=B.shown,stock=FA.stock,clock=B.clock;
      for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60);for(let i=0;i<120;i++)faStep(1/60);
      return{bonus:FA.cnt.bonus,base:FA.cnt.base,at,want:7/12,frozen:B.shown===at&&FA.stock===stock&&B.clock===clock,score:FA.score,txt:document.querySelector('#fabonus')&&document.querySelector('#fabonus').textContent}})()""")
    check("f) floor win: bonus = 7 uneaten bites × 100 = 700 (count-up reaches it), bar frozen at its real value", f["bonus"] == 700 and f["score"] == 1200 and abs(f["at"] - f["want"]) < 1e-9 and f["frozen"], f)
    start_dev_run(p, 3); p.evaluate(QUIET)  # floor 3 collapse uses the same bonus
    f = p.evaluate("""(()=>{FA.bar.left=FA.bar.N;faFinalWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60);return{bonus:FA.cnt.bonus,N:FA.bar.N}})()""")
    check("f) floor-3 collapse: bonus = N × 100 (all bites uneaten)", f["bonus"] == f["N"] * 100, f)
    check("no console errors (f)", not errs, errs)

    # ================= g) «Ultimo morso»: slow motion → fade → popup → «Continua» → «Partita finita» (runPayout numbers)
    base = p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null}G=null;S.quick=null;S.ach={prog:{},done:{}};A_t=0;return JSON.stringify({p:S.p,ach:S.ach})})()")
    start_run(p); p.evaluate(QUIET)
    p.evaluate("(()=>{S.ach=JSON.parse(%s).ach;A_t=0;FA.run.girone=3;FA.score=2000;FA.inv=1e9;0})()" % json.dumps(base))
    p.evaluate("faPause(true)")
    btns = p.evaluate("[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.textContent.trim())")
    check("g) dev session: the pause menu has «Salva ed esci» (FR1b1) and «Ultimo morso» between «Riprendi» and «Esci»", btns == ["Riprendi", "Salva ed esci", "Ultimo morso", "Esci"], btns)
    p.click("#fapanel [data-fa=lastbite]"); p.evaluate(FREEZE)
    r = p.evaluate("(()=>{faHud();return{left:FA.bar.left,gap:+(FA.bar.due-FA.bar.clock).toFixed(3),paused:FA.paused,dev:document.querySelector('#fadev').textContent}})()")
    check("g) «Ultimo morso»: one bite left, next bite due in 1 s, game resumed; the dev readout shows «morsi 1/N · prossimo 1.0s»",
          r["left"] == 1 and r["gap"] == 1 and not r["paused"] and r["dev"].startswith("morsi 1/") and r["dev"].endswith("prossimo 1.0s"), r)
    p.evaluate(STEP + "(61)")  # the bite is due and Algidone eats at once (his idle wait is ignored)
    lb = p.evaluate("({lb:!!FA.lb,alg:FA.alg.state,left:FA.bar.left})")
    check("g) the last bite starts the ending (Algidone eating, bar at 0 bites)", lb["lb"] and lb["alg"] == "eat" and lb["left"] == 0, lb)
    sm = p.evaluate("(()=>{const a0=FA.alg.t,t0=FA.t;faStep(1/60);return{da:FA.alg.t-a0,dt:1/60}})()")
    check("g) slow motion: everything advances at ×0.3 (the eat animation moves 0.3 of a frame)", abs(sm["da"] - sm["dt"] * .3) < 1e-9, sm)
    p.evaluate("for(let i=0;i<60&&true;i++)faStep(1/60)")  # ≈ 1.03 s real so far
    g1 = p.evaluate("({a:FA.lb.a,state:FA.state,panel:document.querySelector('#fapanel').classList.contains('on')})")
    check("g) still in slow motion before lastSlowDur (1.5 s): not faded, no popup", g1["a"] == 0 and g1["state"] == "play" and not g1["panel"], g1)
    p.evaluate("for(let i=0;i<60;i++)faStep(1/60)")  # ≈ 2.03 s → 0.5 s into the fade
    g2 = p.evaluate("({a:+FA.lb.a.toFixed(2),state:FA.state,panel:document.querySelector('#fapanel').classList.contains('on')})")
    check("g) fade to black after 1.5 s (alpha ≈ 0.5 half a second in), popup not yet", .4 < g2["a"] < .6 and g2["state"] == "play" and not g2["panel"], g2)
    p.evaluate("faDie('x',true)"); check("g) no death during the last-bite ending", p.evaluate("FA.state") == "play")
    p.evaluate("for(let i=0;i<70;i++)faStep(1/60)")
    g3 = p.evaluate("({state:FA.state,a:FA.lb.a,h3:document.querySelector('#fapanel h3').textContent,btns:[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.textContent.trim())})")
    check("g) popup «Algidone ha finito tutto!» with one button «Continua»", g3["state"] == "over" and g3["a"] == 1 and g3["h3"] == "Algidone ha finito tutto!" and g3["btns"] == ["Continua"], g3)
    p.click("#fapanel [data-fa=exit]"); p.wait_for_timeout(300)
    fv = p.evaluate("({screen,opt:[...document.querySelectorAll('.opt b')].map(b=>b.textContent),gir:(document.querySelector('.disp')||{}).textContent,sordi:S.p.sordi,exp:S.p.ch.roccia.exp,lvl:S.p.ch.roccia.lvl,FA,G})")
    p.evaluate("(()=>{const s=JSON.parse(%s);S.p=s.p;S.ach=s.ach;A_t=0;cancelAnimationFrame(raf);startGame(false,{});cancelAnimationFrame(raf);G.stage=3;G.score=2000;finishRun();0})()" % json.dumps(base))
    p.wait_for_timeout(300)
    mv = p.evaluate("({opt:[...document.querySelectorAll('.opt b')].map(b=>b.textContent),sordi:S.p.sordi,exp:S.p.ch.roccia.exp,lvl:S.p.ch.roccia.lvl})")
    check("g) «Continua» → «Partita finita» (Girone 3) with the same numbers as a maze runPayout", fv["screen"] == "over" and fv["FA"] is None and fv["G"] is None and fv["gir"] == "Girone 3" and (fv["opt"], fv["sordi"], fv["exp"], fv["lvl"]) == (mv["opt"], mv["sordi"], mv["exp"], mv["lvl"]), (fv["opt"], mv["opt"]))
    # player (non-dev) session: no dev readout / button
    ctx2, p2, errs2 = fresh(b, 390, 844, dev=False)
    start_run(p2); p2.evaluate("faIntroEnd();faHud();faPause(true)")
    r = p2.evaluate("({btns:[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.textContent.trim()),dev:!!document.querySelector('#fadev'),wv:(document.querySelector('#fawv')||{}).textContent})")
    check("g) player session: «Salva ed esci» (FR1b1) but no «Ultimo morso», no dev readout; the girone label is there", r == {"btns": ["Riprendi", "Salva ed esci", "Esci"], "dev": False, "wv": "Girone 1"}, r)
    check("no console errors (g)", not errs and not errs2, (errs, errs2))
    ctx2.close(); ctx.close()

    # ================= h) practice and the maze encounter: SUPERSEDED by FR1b2 (0.4.5_33) — both switched to the
    # eat-driven bar (own tables FA_PRAC.bar/FA_ENC.bar), so the golden comparison against the pre-FR1b2 build this
    # section used to run (continuous drain, 22% random eat, death −10 s stock, floor(stock)×10 bonus) no longer
    # holds by design; see CLAUDE.md FR1b2 and tools/fbstub/test_fr1b2.py for the new behaviour's own coverage.
    # This section now only checks the NEW invariant directly, on the current build.
    SCEN = """(async kind=>{
      __SEED__;window.requestAnimationFrame=()=>0;const out={};
      await (kind==='enc'?startFerma({test:true,encounter:2}):startFerma({test:true}));cancelAnimationFrame(FA.raf);
      faIntroEnd();FA.inv=1e9;const eats=[];let prev=FA.alg.state,sig=[];
      for(let i=0;i<60*90;i++){faStep(1/60);if(FA.alg.state==='eat'&&prev!=='eat')eats.push(i);prev=FA.alg.state;if(i%600===0)sig.push(+FA.stock.toFixed(3));if(FA.state==='over')break}
      out.eats=eats;out.sig=sig;out.state=FA.state;out.stock=+FA.stock.toFixed(3);out.throws=FA.throws;out.items=FA.items.length;out.score=FA.score;out.hasBar=!!FA.bar;out.hasRun=!!FA.run;
      FA.state==='over'&&(FA.state='play');const s0=FA.stock;FA.inv=0;faDie('x',true);out.deathEat=FA.alg.state;out.deathStock=FA.stock;for(let i=0;i<200&&FA.state==='dying';i++)faStep(1/60);out.afterDeath=[FA.state,+FA.stock.toFixed(3),FA.lives];out.deathStockDelta=+(s0-FA.stock).toFixed(3);
      FA.state==='over'&&(FA.state='play');FA.bar.left=7;FA.bar.N=12;FA.bar.shown=7/12;FA.alg.wait=1e9;faWin();for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60);out.bonus=FA.cnt.bonus;
      return JSON.stringify(out)})""".replace("__SEED__", SEED % 4242)
    res = {}
    ctx, p, errs = fresh(b, 390, 844, dev=False)
    for kind in ("practice", "enc"):
        p.evaluate("(()=>{" + UNF + "if(FA){FA.dead=true;FA=null};go('menu')})()"); p.wait_for_timeout(200)
        res[kind] = json.loads(p.evaluate("(%s)('%s')" % (SCEN, kind)))
    res["errs"] = list(errs)
    ctx.close()
    for kind in ("practice", "enc"):
        n = res[kind]
        check("h) %s (FR1b2): scheduled bites only (no random 22%% eat — several eats over 90s, spaced out, not clustered), bar/no run object" % kind,
              len(n["eats"]) >= 2 and n["hasBar"] and not n["hasRun"], n)
        check("h) %s (FR1b2): stock (now the bar) drains only via bites, not continuously" % kind, n["sig"][0] > n["sig"][-1], n)
        check("h) %s (FR1b2): a death costs no bite and no stock, only a life" % kind,
              n["deathEat"] != "eat" and n["deathStockDelta"] < 1.5 and n["afterDeath"][2] == 2, n)
        check("h) %s (FR1b2): floor bonus = 7 uneaten bites × 100 = 700 (not floor(stock)×10)" % kind, n["bonus"] == 700, n)
    check("no console errors (h)", not res["errs"], res["errs"])
    b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
