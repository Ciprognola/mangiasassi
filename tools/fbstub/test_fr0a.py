#!/usr/bin/env python3
"""0.4.5_27 (FR0a) tests: the run layer -- G.run + the RUN_PROTO accessor aliases (G.stage/G.score/... read and write G.run),
mkMazeG as the one builder of a fresh maze G (startGame + devJump), quicksave/resume carrying run, old-shaped quicksaves migrated.
Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_fr0a.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only
from gp import pick_maze

RUN_KEYS = sorted(["girone", "score", "girPts", "girBonusTxt", "lives", "hard", "game", "char", "diff", "dev"])

# force a real girone clear: one pellet at the player's own cell, one update() tick (-> "clear"), then let the clear timer run out (-> next girone)
CLEAR_AND_ADVANCE = """(()=>{
  cancelAnimationFrame(raf);G.state='play';G.t=0;
  G.grid=G.grid.map(row=>row.map(ch=>ch==='.'?' ':ch));
  G.grid[G.pl.ty][G.pl.tx]='.';G.pl.prog=0;G.pl.dir=null;G.pl.next=null;
  update(1/60);const mid=G.state;G.t=0;update(1/60);cancelAnimationFrame(raf);
  return {mid,stage:G.stage,girone:G.run.girone};
})()"""

RUN_INFO = """(()=>({hasRun:!!G.run,proto:Object.getPrototypeOf(G)===RUN_PROTO,stage:G.stage,girone:G.run&&G.run.girone,
  keys:Object.keys(G.run||{}).sort(),own:Object.keys(G).filter(k=>k in RUN_ALIAS),
  json:(()=>{const j=JSON.parse(JSON.stringify(G));return{run:'run' in j,aliased:Object.keys(j).filter(k=>k in RUN_ALIAS)}})()}))()"""

with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    # ---------------- a) a new run through the real «Nuovo gioco» click
    p.evaluate("(()=>{cancelAnimationFrame(raf);G=null;S.quick=null;persist();go('menu')})()"); p.wait_for_timeout(300)
    p.click("[data-tile=new]"); p.wait_for_timeout(200); pick_maze(p)
    p.wait_for_function("G&&G.run&&(G.state==='ready'||G.state==='play')", timeout=5000); p.wait_for_timeout(200)
    r = p.evaluate(RUN_INFO)
    check("a) «Nuovo gioco»: G.run exists, G is built on RUN_PROTO", r["hasRun"] and r["proto"], r)
    check("a) G.stage === G.run.girone (girone 1)", r["stage"] == r["girone"] == 1, r)
    r = p.evaluate(CLEAR_AND_ADVANCE)
    check("a) after a forced girone clear both G.stage and G.run.girone are +1", r["mid"] == "clear" and r["stage"] == r["girone"] == 2, r)
    check("no console errors (a)", not errs, errs)

    # ---------------- b) writes go through the alias; aliases are never own properties
    r = p.evaluate("(()=>{const s0=G.run.score;G.score+=50;return{d:G.run.score-s0,same:G.score===G.run.score}})()")
    check("b) G.score += 50 changes G.run.score by 50", r["d"] == 50 and r["same"], r)
    r = p.evaluate("(()=>{const l0=G.run.lives;G.lives--;const d=l0-G.run.lives;G.lives++;return{d}})()")
    check("b) G.lives-- writes G.run.lives", r["d"] == 1, r)
    r = p.evaluate(RUN_INFO)
    check("b) Object.keys(G) has no aliased name", r["own"] == [], r)
    check("b) JSON of G has run and none of the aliased names", r["json"]["run"] and r["json"]["aliased"] == [], r)
    check("no console errors (b)", not errs, errs)

    # ---------------- c) startGame and devJump produce runs with the same key set
    k1 = p.evaluate("(()=>{cancelAnimationFrame(raf);startGame(false,{});cancelAnimationFrame(raf);return Object.keys(G.run).sort()})()")
    k2 = p.evaluate("(()=>{cancelAnimationFrame(raf);devJump(3);cancelAnimationFrame(raf);return Object.keys(G.run).sort()})()")
    check("c) startGame and devJump runs have the same key set (the 10 run fields)", k1 == k2 == RUN_KEYS, {"startGame": k1, "devJump": k2})
    r = p.evaluate("({dev:G.run.dev,girone:G.run.girone,score:G.run.score,lives:G.run.lives,hard:G.run.hard,game:G.run.game})")
    check("c) devJump(3)'s run keeps today's values (girone 3, score 1500, lives 3, not hard, dev)",
          r == {"dev": True, "girone": 3, "score": 1500, "lives": 3, "hard": False, "game": "maze"}, r)
    r = p.evaluate("(()=>{cancelAnimationFrame(raf);startGame(false,{hard:true});cancelAnimationFrame(raf);return{lives:G.lives,hard:G.hard,dev:G.dev,diff:G.diff===(S.opts.diff||'medium'),char:G.char===(S.p.char||'roccia'),girPts:G.girPts}})()")
    check("c) startGame Hardcore keeps today's defaults (4 lives, hard, not dev, diff/char from options, girPts 0)",
          r == {"lives": 4, "hard": True, "dev": False, "diff": True, "char": True, "girPts": 0}, r)
    check("no console errors (c)", not errs, errs)

    # ---------------- d) quicksave -> resume round trip
    p.evaluate("(()=>{cancelAnimationFrame(raf);startGame(false,{});cancelAnimationFrame(raf);G.score=1234;G.girPts=77;G.state='play'})()")
    before = p.evaluate("(()=>{quicksave();return{run:JSON.stringify(G.run),mapi:G.mapi,grid:JSON.stringify(G.grid),"
                        "q:{run:'run' in S.quick,aliased:Object.keys(S.quick).filter(k=>k in RUN_ALIAS)}}})()")
    check("d) the quicksave carries run and none of the aliased names", before["q"]["run"] and before["q"]["aliased"] == [], before["q"])
    p.evaluate("(()=>{cancelAnimationFrame(raf);G=null;go('menu')})()"); p.wait_for_timeout(300)
    p.click("[data-tile=cur]"); p.wait_for_function("G&&(G.state==='ready'||G.state==='play')", timeout=5000); p.wait_for_timeout(200)
    after = p.evaluate("({run:JSON.stringify(G.run),mapi:G.mapi,grid:JSON.stringify(G.grid),proto:Object.getPrototypeOf(G)===RUN_PROTO,own:Object.keys(G).filter(k=>k in RUN_ALIAS)})")
    check("d) resume: run identical", after["run"] == before["run"], {"before": before["run"], "after": after["run"]})
    check("d) resume: map and grid identical", after["mapi"] == before["mapi"] and after["grid"] == before["grid"])
    check("d) resume: G back on RUN_PROTO, no own aliased props", after["proto"] and after["own"] == [], after)
    check("no console errors (d)", not errs, errs)

    # ---------------- e) an old-shaped quicksave (no run, no girPts) resumes with the same values
    p.evaluate("""(()=>{
      cancelAnimationFrame(raf);setDims(0);const g=freshGrid(0),st=MET.ghosts,ch=[.52,.38,.24,.41],tn=['#e5484d','#3ec7e0','#ff9a3c','#ff7ac6'];
      const en=st.map((s,i)=>({tx:s[0],ty:s[1],dir:null,prog:0,wait:0,chase:ch[i],tint:tn[i],mode:'n',gt:0,stage:1}));
      S.quick={game:'maze',stage:4,score:2600,lives:2,hard:true,grid:g,parts:[],diff:'hard',char:'roccia',mapi:0,plane:0,rock:0,
        pl:{tx:MET.start[0],ty:MET.start[1],dir:null,next:null,prog:0,lastH:1},en,power:0,pu:null,since:0,open:8,chain:0,still:false,
        state:'ready',t:1.6,invuln:0,anim:0,st:null,fx:[],shake:0,burn:0,inW:false,cam:null,lastMi:{S:0,M:null,L:null}};
      persist();G=null;go('menu');
    })()"""); p.wait_for_timeout(300)
    p.click("[data-tile=cur]"); p.wait_for_function("G&&(G.state==='ready'||G.state==='play')", timeout=5000); p.wait_for_timeout(200)
    r = p.evaluate("({girone:G.run.girone,stage:G.stage,score:G.run.score,lives:G.run.lives,hard:G.run.hard,game:G.run.game,diff:G.run.diff,girPts:G.run.girPts,"
                   "own:Object.getOwnPropertyNames(G).filter(k=>k in RUN_ALIAS),keys:Object.keys(G.run).sort()})")
    check("e) old quicksave: girone/score/lives/hard/game/diff carried into the run",
          (r["girone"], r["stage"], r["score"], r["lives"], r["hard"], r["game"], r["diff"]) == (4, 4, 2600, 2, True, "maze", "hard"), r)
    check("e) old quicksave: girPts 0, no own stage/score/... props left, full run key set", r["girPts"] == 0 and r["own"] == [] and r["keys"] == RUN_KEYS, r)
    check("no console errors (e)", not errs, errs)

    # ---------------- f) professor-win start (girone 3, seeded score)
    r = p.evaluate("(()=>{cancelAnimationFrame(raf);G=null;go('menu');startGame(false,{stage:3,score:5000});cancelAnimationFrame(raf);return{girone:G.run.girone,score:G.run.score,girPts:G.run.girPts,stage:G.stage}})()")
    check("f) professor-win start: run.girone 3, run.score = reward, girPts 0", r == {"girone": 3, "score": 5000, "girPts": 0, "stage": 3}, r)
    check("no console errors (f)", not errs, errs)

    # ---------------- g) dev jump to girone 8: dev run, nothing written to S.quick or progress
    SNAP = "JSON.stringify({q:S.quick,ls:(store.get('mgs_v1')||{}).quick||null,gir:S.p.ch[S.p.char||'roccia'].gir,g5:S.p.g5,sec:S.p.sec,best:S.p.best,sordi:S.p.sordi})"
    p.evaluate("(()=>{cancelAnimationFrame(raf);G=null;S.quick=null;persist();go('menu')})()"); p.wait_for_timeout(200)
    s0 = p.evaluate(SNAP)
    r = p.evaluate("(()=>{devJump(8);cancelAnimationFrame(raf);return{dev:G.run.dev,girone:G.run.girone}})()")
    check("g) devJump(8): run.dev true, girone 8", r == {"dev": True, "girone": 8}, r)
    r = p.evaluate(CLEAR_AND_ADVANCE)
    check("g) dev run clears girone 8 -> 9 through the aliases", r["stage"] == r["girone"] == 9, r)
    check("g) nothing written to S.quick or progress (gir, g5, sec, best, sordi, stored quicksave)", p.evaluate(SNAP) == s0, {"before": s0, "after": p.evaluate(SNAP)})
    check("no console errors (g)", not errs, errs)
    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
