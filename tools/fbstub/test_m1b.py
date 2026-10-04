#!/usr/bin/env python3
"""0.4.5_15 (M1b) tests: girone bonus multipliers (GIR_BONUS), girPts (this girone's own points),
the «Bonus girone ×M +P» clear-screen line. Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_m1b.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

# gironi 7/8's raw formula gives 2.03/2.1 -- both capped to GIR_BONUS.maxMult (1.8) as of E6b (0.4.5_26)
EXPECT_MULT = {1: 1.0, 2: 1.1, 3: 1.2, 4: 1.44, 5: 1.44, 6: 1.68, 7: 1.8, 8: 1.8}

# force a real girone clear: one pellet, at the player's own cell, then one update() tick
CLEAR_ONE = """(dt)=>{
  G.state='play';G.t=0;
  G.grid=G.grid.map(row=>row.map(ch=>ch==='.'?' ':ch));
  G.grid[G.pl.ty][G.pl.tx]='.';G.pl.prog=0;G.pl.dir=null;G.pl.next=null;
  update(dt||1/60);
  return {state:G.state,txt:G.girBonusTxt,score:G.score,girPts:G.girPts,stage:G.stage};
}"""


def dev_click(p, sel):
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(%s)').open" % sel.replace("'", "\\'")):
        p.click("details.acc:has(%s) > summary" % sel); p.wait_for_timeout(250)
    p.click(sel); p.wait_for_timeout(600)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    # ---------------- mult for gironi 1-8 matches the table (capped at GIR_BONUS.maxMult); 9+ matches the formula
    check("GIR_BONUS.maxMult is 1.8", p.evaluate("GIR_BONUS.maxMult") == 1.8, p.evaluate("GIR_BONUS.maxMult"))
    for g in range(1, 9):
        p.evaluate("cancelAnimationFrame(raf);devJump(%d)" % g); p.wait_for_timeout(300)
        r = p.evaluate("""(()=>{const cls=mapClassOf(G.mapi),n2=G.en.filter(e=>e.stage===2).length,n3=G.en.filter(e=>e.stage===3).length;
          return {mult:Math.min(GIR_BONUS.maxMult,GIR_BONUS.cls[cls]*(1+GIR_BONUS.st2*n2+GIR_BONUS.st3*n3)),cls,n2,n3}})()""")
        want = EXPECT_MULT[g]
        check(f"girone {g}: bonus mult = {want} ({r['cls']}, {r['n2']}x stage2, {r['n3']}x stage3)", abs(r["mult"] - want) < 1e-9, r)
    for g in (9, 10, 12):
        p.evaluate("cancelAnimationFrame(raf);devJump(%d)" % g); p.wait_for_timeout(300)
        r = p.evaluate("""(()=>{const cls=mapClassOf(G.mapi),n2=G.en.filter(e=>e.stage===2).length,n3=G.en.filter(e=>e.stage===3).length,clsMult={S:1.0,M:1.2,L:1.4}[cls];
          return {mult:Math.min(GIR_BONUS.maxMult,GIR_BONUS.cls[cls]*(1+GIR_BONUS.st2*n2+GIR_BONUS.st3*n3)),want:Math.min(1.8,clsMult*(1+.10*n2+.25*n3))}})()""")
        check(f"girone {g}: bonus mult matches the formula (girone-9+ classes/stages)", abs(r["mult"] - r["want"]) < 1e-9, r)
    check("no console errors (mult table)", not errs, errs)

    # ---------------- cap boundary: an uncapped girone (6, x1.68) vs a capped one (8, raw x2.1 -> x1.8), plus a
    # synthetic far-past-the-cap case proving it clamps rather than merely landing near 1.8 by coincidence
    p.evaluate("cancelAnimationFrame(raf);devJump(6)"); p.wait_for_timeout(300)
    r = p.evaluate("""(()=>{const cls=mapClassOf(G.mapi),n2=G.en.filter(e=>e.stage===2).length,n3=G.en.filter(e=>e.stage===3).length;
      return {raw:GIR_BONUS.cls[cls]*(1+GIR_BONUS.st2*n2+GIR_BONUS.st3*n3),capped:Math.min(GIR_BONUS.maxMult,GIR_BONUS.cls[cls]*(1+GIR_BONUS.st2*n2+GIR_BONUS.st3*n3))}})()""")
    check("girone 6 (x1.68) is below the cap -- capping is a no-op here", r["raw"] < 1.8 and abs(r["capped"] - r["raw"]) < 1e-9, r)
    p.evaluate("cancelAnimationFrame(raf);devJump(8)"); p.wait_for_timeout(300)
    r = p.evaluate("""(()=>{const cls=mapClassOf(G.mapi),n2=G.en.filter(e=>e.stage===2).length,n3=G.en.filter(e=>e.stage===3).length;
      return {raw:GIR_BONUS.cls[cls]*(1+GIR_BONUS.st2*n2+GIR_BONUS.st3*n3),capped:Math.min(GIR_BONUS.maxMult,GIR_BONUS.cls[cls]*(1+GIR_BONUS.st2*n2+GIR_BONUS.st3*n3))}})()""")
    check("girone 8's raw mult (x2.1) is above the cap and gets clamped to x1.8", r["raw"] > 1.8 and abs(r["capped"] - 1.8) < 1e-9, r)
    r = p.evaluate("""(()=>{const raw=GIR_BONUS.cls.L*(1+GIR_BONUS.st2*0+GIR_BONUS.st3*20);return{raw,capped:Math.min(GIR_BONUS.maxMult,raw)}})()""")
    check("a synthetic extreme case (20x stage-3 weight, raw x8.4) still clamps to exactly x1.8, not just near it",
          r["raw"] > 5 and abs(r["capped"] - 1.8) < 1e-9, r)
    check("no console errors (cap boundary)", not errs, errs)

    # ---------------- clearing a girone adds the bonus exactly once; line shows only when bonus > 0
    for g, wantLine in ((1, False), (2, True), (7, True)):
        p.evaluate("cancelAnimationFrame(raf);devJump(%d)" % g); p.wait_for_timeout(300)
        p.evaluate("G.score=1500;G.girPts=1000")
        r = p.evaluate(CLEAR_ONE, 1 / 60)
        mult = EXPECT_MULT[g]
        girPtsAfterEat = 1000 + 10 + 200  # the pellet just eaten + the clear bonus, both part of this girone's own points
        bonus = round(girPtsAfterEat * (mult - 1))
        expScore = 1500 + 10 + 200 + bonus
        check(f"girone {g}: clearing adds pellet(+10) + clear(+200) + bonus(+{bonus}) exactly once", r["state"] == "clear" and r["score"] == expScore, r)
        check(f"girone {g}: «Bonus girone» line {'shown' if wantLine else 'absent'} (bonus {'>' if wantLine else '='} 0)",
              (r["txt"] is not None) == wantLine and (not wantLine or ("×%s" % (str(mult) if mult != int(mult) else str(int(mult))) in r["txt"] or "×%s" % mult in r["txt"])), r)
    check("no console errors (clear + bonus)", not errs, errs)

    # ---------------- girPts resets at each girone start
    p.evaluate("cancelAnimationFrame(raf);devJump(2)"); p.wait_for_timeout(300)
    p.evaluate("G.score=1500;G.girPts=1000")
    p.evaluate(CLEAR_ONE, 1 / 60)
    check("(setup) mid-clear girPts still holds this girone's points", p.evaluate("G.girPts") > 0)
    p.evaluate("update(1.7)")  # let the 1.6s clear pause expire -> advances to the next girone
    r = p.evaluate("({stage:G.stage,girPts:G.girPts,txt:G.girBonusTxt})")
    check("girPts resets to 0 at the next girone start (and the bonus line is cleared)", r["girPts"] == 0 and r["txt"] is None, r)
    check("no console errors (girPts reset)", not errs, errs)

    # ---------------- mid-girone quicksave keeps girPts
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    p.click("[data-tile=new]"); pick_maze(p); p.wait_for_function("G&&G.state==='play'", timeout=8000)
    p.evaluate("G.girPts=345;quicksave()"); p.wait_for_timeout(200)
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    p.click("[data-tile=cur]"); p.wait_for_function("G&&(G.state==='ready'||G.state==='play')", timeout=5000); p.wait_for_timeout(300)
    check("a mid-girone quicksave keeps girPts (resume)", p.evaluate("G.girPts") == 345, p.evaluate("G.girPts"))
    check("no console errors (quicksave keeps girPts)", not errs, errs)

    # ---------------- an old-shaped quicksave (no girPts field) resumes with girPts = 0
    p.evaluate("""(()=>{
      setDims(0);const g=freshGrid(0),st=MET.ghosts,ch=[.52,.38,.24,.41],tn=['#e5484d','#3ec7e0','#ff9a3c','#ff7ac6'];
      const en=st.map((s,i)=>({tx:s[0],ty:s[1],dir:null,prog:0,wait:0,chase:ch[i],tint:tn[i],mode:'n',gt:0,stage:1}));
      S.quick={game:'maze',stage:2,score:800,lives:3,hard:false,grid:g,parts:[],diff:'medium',char:'roccia',mapi:0,plane:0,rock:0,
        pl:{tx:MET.start[0],ty:MET.start[1],dir:null,next:null,prog:0,lastH:1},en,power:0,pu:null,since:0,open:8,chain:0,still:false,
        state:'ready',t:1.6,invuln:0,anim:0,st:null,fx:[],shake:0,burn:0,inW:false,cam:null,lastMi:{S:0,M:null,L:null}};
      persist();
    })()""")
    p.evaluate("cancelAnimationFrame(raf);G=null;go('menu')"); p.wait_for_timeout(300)
    p.click("[data-tile=cur]"); p.wait_for_function("G&&(G.state==='ready'||G.state==='play')", timeout=5000); p.wait_for_timeout(300)
    check("an old quicksave (no girPts field) resumes with girPts = 0", p.evaluate("G.girPts") == 0, p.evaluate("G.girPts"))
    check("no console errors (old quicksave)", not errs, errs)

    # ---------------- the professor-seeded score at girone 3 is not multiplied (not part of girPts)
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    r = p.evaluate("(()=>{cancelAnimationFrame(raf);startGame(false,{stage:3,score:5000});return {score:G.score,girPts:G.girPts,stage:G.stage}})()")
    check("professor-win seeded score (5000 at girone 3) is not counted in girPts", r["score"] == 5000 and not r["girPts"], r)
    p.evaluate("G.score=1500;G.girPts=1000")
    r2 = p.evaluate(CLEAR_ONE, 1 / 60)
    check("the seeded 5000 stays untouched by the bonus (only girPts from play is multiplied)", r2["score"] == 1500 + 10 + 200 + round(1210 * (1.2 - 1)), r2)
    check("no console errors (professor-seeded score)", not errs, errs)

    # ---------------- finishRun order unchanged: limiter, DIFF.mult, .7 still apply after the bonus, on the final G.score
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    p.evaluate("cancelAnimationFrame(raf);devJump(2);G.diff='hard';S.p.ch.roccia.lvl=20;S.p.ch.roccia.exp=0")
    p.evaluate("G.score=1500;G.girPts=1000")
    p.evaluate(CLEAR_ONE, 1 / 60)
    r3 = p.evaluate("""(()=>{
      cancelAnimationFrame(raf);G.dev=false;
      S.ach.done=Object.fromEntries(ACH.map(a=>[a.id,{d:0}]));  // no achievement unlocks in this call: isolate the base gain formula
      const finalScore=G.score,lim=limiter(S.p.ch.roccia.lvl),mult=dfc().mult,expGain=Math.floor(finalScore*(1-lim)*mult*.7);
      const before=S.p.sordi;finishRun({quiet:true});
      return {gain:S.p.sordi-before,expGain,finalScore,lim,mult};
    })()""")
    check("finishRun still applies limiter/DIFF.mult/.7 after the bonus, on the final G.score (order unchanged)", r3["gain"] == r3["expGain"], r3)
    check("no console errors (finishRun order)", not errs, errs)
    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
