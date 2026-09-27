#!/usr/bin/env python3
"""0.4.5_20 (E2) tests: aerei sprint (fills ABIL.sprint, CLAUDE.md §10.3). Uomo roccia's enemies
only -- Algidone's attrezzi are unaffected. Uses the dev girone jump + the "Stadio" (E1a) override
to force stage 2 deterministically. Reuses the harness of test_f2b.py, same pattern as
test_e1a.py/test_e1b.py.
Run: python tools/fbstub/test_e2.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

SETUP_ROCCIA = """(()=>{
  S.p.char='roccia';E1_STAGE_OV=2;
  cancelAnimationFrame(raf);devJump(1,0);
  G.state='play';G.invuln=99999;G.pl.dir=null;G.pl.prog=0;
  const findRowRun=(y,len)=>{for(let x0=1;x0+len<W-1;x0++){let ok=true;
    for(let i=0;i<=len;i++){const x=x0+i;if(wall(x,y)||inHouse(x,y)){ok=false;break}}
    if(ok)return x0}return null};
  const findWallBetween=()=>{for(let y=0;y<H;y++){if(isTun(y))continue;
    for(let x=2;x<W-2;x++){if(wall(x,y)&&!wall(x-2,y)&&!wall(x+2,y)&&!inHouse(x-2,y)&&!inHouse(x+2,y))return{y,xa:x-2,xb:x+2}}}
    return null};
  let openRow=null;
  for(let y=0;y<H;y++){if(isTun(y))continue;const x0=findRowRun(y,4);if(x0!=null){openRow={y,x0};break}}
  window.__geo={openRow,wallCase:findWallBetween()};
  return window.__geo;
})()"""

with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    geo = p.evaluate(SETUP_ROCCIA)
    check("found test geometry (open row + wall-between case)", geo["openRow"] and geo["wallCase"], geo)
    y, x0 = geo["openRow"]["y"], geo["openRow"]["x0"]

    # ---------------- start cooldown is within 0..3s (SPRINT_CFG.cdStartMax), sampled across fresh spawns
    cds = p.evaluate("""(()=>{
      const out=[];
      for(let i=0;i<10;i++){cancelAnimationFrame(raf);devJump(1,0);out.push(G.en[0].ab.sprint.cd)}
      return out;
    })()""")
    check("start cooldown always within [0, cdStartMax]", all(0 <= v <= p.evaluate("SPRINT_CFG.cdStartMax") for v in cds), cds)
    check("start cooldown is randomised, not a constant", len(set(round(v, 4) for v in cds)) > 1, cds)

    # ---------------- triggers only with LOS within range; not beyond range; not through a wall
    p.evaluate(SETUP_ROCCIA)
    r = p.evaluate("""(()=>{
      const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=null;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;
      e.ab.sprint.cd=0;
      update(1/60);
      return e.ab.sprint.phase;
    })()""" % (x0, y, x0 + 3, y))
    check("triggers wind-up when in LOS within range (dist 3 <= range 6)", r == "wind", r)

    p.evaluate(SETUP_ROCCIA)
    r = p.evaluate("""(()=>{
      const range=SPRINT_CFG.range,e=G.en[0];e.tx=%d;e.ty=%d;e.dir=null;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
      G.pl.tx=Math.min(W-2,%d+range+3);G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;
      e.ab.sprint.cd=0;
      update(1/60);
      return {phase:e.ab.sprint.phase,dist:Math.abs(G.pl.tx-e.tx)};
    })()""" % (x0, y, x0, y))
    check("does not trigger beyond range", r["phase"] == "idle" and r["dist"] > p.evaluate("SPRINT_CFG.range"), r)

    wy, xa, xb = geo["wallCase"]["y"], geo["wallCase"]["xa"], geo["wallCase"]["xb"]
    r = p.evaluate("""(()=>{
      const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=null;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;
      e.ab.sprint.cd=0;
      update(1/60);
      return e.ab.sprint.phase;
    })()""" % (xa, wy, xb, wy))
    check("does not trigger through a wall", r == "idle", r)
    check("no console errors (trigger conditions)", not errs, errs)

    # ---------------- wind ~0.6s with zero movement; run ~1.5s at ~x1.8 speed; then cooldown, no re-trigger
    p.evaluate(SETUP_ROCCIA)
    r = p.evaluate("""(()=>{
      const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=null;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;
      // baseline normal speed for this stage/diff, measured directly from the same shared formula
      const es=Math.min(5.7,4.3+G.stage*.18)*dfc().spd;
      e.ab.sprint.cd=0;
      update(1/60); // idle -> wind
      const phaseAfterTrigger=e.ab.sprint.phase;
      let movedDuringWind=false;const startTx=e.tx,startTy=e.ty,startProg=e.prog;
      for(let i=0;i<13;i++){update(0.05);if(e.tx!==startTx||e.ty!==startTy||e.prog!==startProg)movedDuringWind=true} // 0.65s: safely past the ~0.6s wind-up (float-drift margin)
      const phaseAfterWind=e.ab.sprint.phase;
      let maxSpeed=0,cdAfterRun=null;
      for(let i=0;i<40;i++){ // stop the instant it goes back to idle, so cd is read before idle's own countdown starts eating it
        update(0.05);if(e.speed>maxSpeed)maxSpeed=e.speed;
        if(e.ab.sprint.phase==="idle"){cdAfterRun=e.ab.sprint.cd;break}
      }
      const phaseAfterRun=e.ab.sprint.phase;
      return {phaseAfterTrigger,movedDuringWind,phaseAfterWind,speedRatio:maxSpeed/es,phaseAfterRun,cdAfterRun};
    })()""" % (x0, y, x0 + 3, y))
    check("phase becomes 'wind' on trigger", r["phaseAfterTrigger"] == "wind", r)
    check("no movement during the ~0.6s wind-up", not r["movedDuringWind"], r)
    check("phase becomes 'run' after ~0.6s", r["phaseAfterWind"] == "run", r)
    check("speed during run is ~x1.8 the normal speed", abs(r["speedRatio"] - 1.8) < 0.05, r)
    check("phase back to 'idle' after ~1.5s of run, cd = SPRINT_CFG.cd", r["phaseAfterRun"] == "idle" and abs(r["cdAfterRun"] - p.evaluate("SPRINT_CFG.cd")) < 1e-6, r)

    r = p.evaluate("""(()=>{
      const e=G.en[0];let retrig=false;
      for(let i=0;i<110;i++){update(0.05);if(e.ab.sprint.phase!=="idle"){retrig=true;break}} // ~5.5s, still short of the ~6s cd
      return {retrig,cd:e.ab.sprint.cd};
    })()""")
    check("no re-trigger while the ~6s cooldown is still running", not r["retrig"], r)
    check("no console errors (timing)", not errs, errs)

    # ---------------- no sprint while scared, eaten, in the house or waiting
    for setup, label in [
        ("e.mode='s'", "scared"),
        ("e.mode='g'", "eaten"),
        ("e.wait=1", "waiting"),
        ("e.tx=MET.house[0];e.ty=MET.house[1]", "in the house"),
    ]:
        p.evaluate(SETUP_ROCCIA)
        r = p.evaluate("""(()=>{
          const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=null;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
          G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;
          e.ab.sprint.cd=0;
          %s;
          update(1/60);
          return e.ab.sprint.phase;
        })()""" % (x0, y, x0 + 3, y, setup))
        check(f"no sprint trigger while {label}", r == "idle", r)
    check("no console errors (gating)", not errs, errs)

    # ---------------- a power-up during wind/run cancels it (E1CancelGhost via activatePower)
    for phase in ("wind", "run"):
        p.evaluate(SETUP_ROCCIA)
        r = p.evaluate("""(()=>{
          const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=null;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
          const savedChase=e.chase;
          e.ab.sprint={phase:'%s',t:1,cd:0,chaseSave:e.chase};e.chase=1;
          activatePower();
          return {phase:e.ab.sprint.phase,cd:e.ab.sprint.cd,chase:e.chase,savedChase};
        })()""" % (x0, y, phase))
        check(f"a power-up during '{phase}' cancels the sprint (idle, full cd, chase restored)",
              r["phase"] == "idle" and abs(r["cd"] - p.evaluate("SPRINT_CFG.cd")) < 1e-6 and r["chase"] == r["savedChase"], r)
    check("no console errors (power-up cancel)", not errs, errs)

    # ---------------- 20s simulated chase: a sprinting ghost never overlaps a wall or leaves a legal position
    p.evaluate(SETUP_ROCCIA)
    r = p.evaluate("""(()=>{
      const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=null;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
      G.pl.tx=%d;G.pl.ty=%d;
      e.ab.sprint={phase:'run',t:1e9,cd:1e9,chaseSave:e.chase};e.chase=1; // force-locked in 'run', always chasing, for the whole simulated chase
      let bad=[];
      for(let i=0;i<400;i++){ // 400 x 0.05s = 20s
        update(0.05);
        if(wall(e.tx,e.ty)||e.prog<0||e.prog>=1||e.tx<0||e.tx>=W||e.ty<0||e.ty>=H)bad.push({tx:e.tx,ty:e.ty,prog:e.prog});
      }
      return {bad:bad.slice(0,5),badCount:bad.length};
    })()""" % (x0, y, x0 + 3, y))
    check("a sprinting ghost never overlaps a wall or an illegal position over a 20s simulated chase", r["badCount"] == 0, r)
    check("no console errors (20s chase safety)", not errs, errs)

    # ---------------- Algidone (attrezzi) ghosts never sprint
    r = p.evaluate("""(()=>{
      S.p.char='algidone';E1_STAGE_OV=2;
      cancelAnimationFrame(raf);devJump(1,0);
      const e=G.en[0];
      return {family:E1Family(),abils:E1AbilsFor(e),hasSprint:!!(e.ab&&e.ab.sprint)};
    })()""")
    check("Algidone's family is 'attrezzi', not 'aerei'", r["family"] == "attrezzi", r)
    check("Algidone's stage-2 abilities never include 'sprint'", "sprint" not in r["abils"], r)
    check("Algidone ghosts never even get a g.ab.sprint object", not r["hasSprint"], r)
    check("no console errors (Algidone unaffected)", not errs, errs)

    # ---------------- reset on death and at girone start
    p.evaluate(SETUP_ROCCIA)
    r = p.evaluate("""(()=>{
      const e=G.en[0];e.ab.sprint={phase:'run',t:1,cd:0,chaseSave:e.chase};e.chase=1;
      G.state='dying';G.t=0.001;update(0.02); // forced death -> resetActors(true) -> fresh E1InitGhost
      return G.en[0].ab.sprint;
    })()""")
    check("a forced death respawn resets every ghost's sprint to idle with a fresh randomised cd",
          r["phase"] == "idle" and 0 <= r["cd"] <= p.evaluate("SPRINT_CFG.cdStartMax"), r)

    r = p.evaluate("""(()=>{
      const e=G.en[0];e.ab.sprint={phase:'wind',t:1,cd:0,chaseSave:e.chase};e.chase=1;
      cancelAnimationFrame(raf);devJump(1,0); // girone start -> resetActors -> fresh E1InitGhost
      return G.en[0].ab.sprint;
    })()""")
    check("girone start resets every ghost's sprint to idle with a fresh randomised cd",
          r["phase"] == "idle" and 0 <= r["cd"] <= p.evaluate("SPRINT_CFG.cdStartMax"), r)
    check("no console errors (reset points)", not errs, errs)

    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
