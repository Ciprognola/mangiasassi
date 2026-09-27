#!/usr/bin/env python3
"""0.4.5_22 (E3) tests: aerei shooting (fills ABIL.shoot, CLAUDE.md §10.3). Uomo roccia's stage-3
enemies only -- stage-2 aerei and all attrezzi are unaffected. Reuses E1b's losRC/MPROJ verbatim.

CONFLICT NOTE (also in CHANGELOG.md/CLAUDE.md §10.9): the brief's own SHOOT_CFG fallback specified a
1.5x-player-speed projectile and a 7s cooldown, but CLAUDE.md §10.3 (the actual spec source, which the
brief says wins on any number) specifies a flat 7 tiles/s and a 4s cooldown -- the build and these tests
follow §10.3, not the fallback block, per the brief's own instruction to do so and report the conflict.

Uses the dev girone jump + the "Stadio" (E1a) override (stage 3) to force stage 3 deterministically.
Reuses the harness of test_f2b.py, same pattern as test_e1a.py/test_e1b.py/test_e2.py.
Run: python tools/fbstub/test_e3.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

SETUP_ROCCIA3 = """(()=>{
  S.p.char='roccia';E1_STAGE_OV=3;
  cancelAnimationFrame(raf);devJump(1,0);
  G.state='play';G.invuln=99999;G.power=0;G.st=null;G.pl.dir=null;G.pl.prog=0;
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

def arm(e_setup, x0, y, px, py):
    """Places ghost 0 at (x0,y) stage 3, player at (px,py); shoot cd=0, sprint neutralised (idle, cd huge) so
    it never fires independently and interferes with a shoot-focused check."""
    return """(()=>{
      const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=null;e.prog=0;e.stage=3;e.mode='n';e.wait=0;
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;
      e.ab.sprint.phase='idle';e.ab.sprint.cd=1e9;e.lastSprintEnd=-1e9;e.lastShotEnd=-1e9;
      e.ab.shoot.cd=0;
      %s
    })()""" % (x0, y, px, py, e_setup)

with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    geo = p.evaluate(SETUP_ROCCIA3)
    check("found test geometry (open row + wall-between case)", geo["openRow"] and geo["wallCase"], geo)
    y, x0 = geo["openRow"]["y"], geo["openRow"]["x0"]

    # ---------------- start cooldown is within 0..cdStartMax
    cds = p.evaluate("""(()=>{
      const out=[];
      for(let i=0;i<10;i++){cancelAnimationFrame(raf);devJump(1,0);out.push(G.en[0].ab.shoot.cd)}
      return out;
    })()""")
    check("start cooldown always within [0, cdStartMax]", all(0 <= v <= p.evaluate("SHOOT_CFG.cdStartMax") for v in cds), cds)
    check("start cooldown is randomised, not a constant", len(set(round(v, 4) for v in cds)) > 1, cds)

    # ---------------- aims only with LOS within range; not beyond range, through a wall, or diagonally
    p.evaluate(SETUP_ROCCIA3)
    r = p.evaluate(arm("update(1/60);return e.ab.shoot.phase;", x0, y, x0 + 3, y))
    check("aims when in LOS within range (dist 3 <= range 8)", r == "aim", r)

    p.evaluate(SETUP_ROCCIA3)
    r = p.evaluate(arm(
        "G.pl.tx=Math.min(W-2,SHOOT_CFG.range+e.tx+3);update(1/60);return {phase:e.ab.shoot.phase,dist:Math.abs(G.pl.tx-e.tx)};",
        x0, y, x0, y))
    check("does not aim beyond range", r["phase"] == "idle" and r["dist"] > p.evaluate("SHOOT_CFG.range"), r)

    wy, xa, xb = geo["wallCase"]["y"], geo["wallCase"]["xa"], geo["wallCase"]["xb"]
    r = p.evaluate(arm("update(1/60);return e.ab.shoot.phase;", xa, wy, xb, wy))
    check("does not aim through a wall", r == "idle", r)

    r = p.evaluate(arm("update(1/60);return e.ab.shoot.phase;", x0, y, x0 + 2, y + 2))
    check("does not aim diagonally", r == "idle", r)
    check("no console errors (aim trigger conditions)", not errs, errs)

    # ---------------- aim ~0.5s with zero movement, then exactly one projectile fired in the aimed direction
    p.evaluate(SETUP_ROCCIA3)
    r = p.evaluate(arm("""
      MPROJ.clear();
      update(1/60); // idle -> aim
      const phaseAfterTrigger=e.ab.shoot.phase,dir=e.ab.shoot.dir;
      let moved=false,cdAfterAim=null;const stx=e.tx,sty=e.ty,sprog=e.prog;
      for(let i=0;i<15;i++){ // stop the instant it fires, so cd is read before idle's own countdown starts eating it
        update(0.05);if(e.tx!==stx||e.ty!==sty||e.prog!==sprog)moved=true;
        if(e.ab.shoot.phase==="idle"){cdAfterAim=e.ab.shoot.cd;break}
      }
      return {phaseAfterTrigger,dir,phaseAfterAim:e.ab.shoot.phase,moved,cdAfterAim,proj:MPROJ.list.slice()};
    """, x0, y, x0 + 3, y))
    check("phase becomes 'aim' on trigger", r["phaseAfterTrigger"] == "aim", r)
    check("no movement during the ~0.5s aim", not r["moved"], r)
    check("phase back to 'idle' after aim, cd = SHOOT_CFG.cd (4s per §10.3, not the brief's 7s fallback)",
          r["phaseAfterAim"] == "idle" and abs(r["cdAfterAim"] - p.evaluate("SHOOT_CFG.cd")) < 1e-6, r)
    check("exactly one projectile fired, in the aimed (LOS) direction", len(r["proj"]) == 1 and r["proj"][0]["dir"] == r["dir"], r)
    check("projectile speed is the flat SHOOT_CFG.projSpeed (7 tiles/s per §10.3, not the brief's 1.5x-player-speed fallback)",
          len(r["proj"]) == 1 and abs(r["proj"][0]["speed"] - p.evaluate("SHOOT_CFG.projSpeed")) < 1e-9, r)
    check("no console errors (aim/fire timeline)", not errs, errs)

    # ---------------- cooldown ~4s (§10.3) with no second shot
    r = p.evaluate("""(()=>{
      const e=G.en[0];let refired=false;
      for(let i=0;i<70;i++){update(0.05);if(e.ab.shoot.phase!=="idle"){refired=true;break}} // ~3.5s, still short of the ~4s cd
      return {refired,cd:e.ab.shoot.cd};
    })()""")
    check("no second shot while the ~4s cooldown is still running", not r["refired"], r)
    check("no console errors (cooldown)", not errs, errs)

    # ---------------- never aims while sprint is in wind/run
    for phase in ("wind", "run"):
        p.evaluate(SETUP_ROCCIA3)
        r = p.evaluate(arm("e.ab.sprint.phase='%s';update(1/60);return e.ab.shoot.phase;" % phase, x0, y, x0 + 3, y))
        check(f"never aims while sprint is '{phase}'", r == "idle", r)
    check("no console errors (sprint-gates-shoot)", not errs, errs)

    # ---------------- the 1.5s gap, enforced both ways (sprint<->shot)
    # time is skipped directly (rather than looping many real update() ticks) so the ghost's own ordinary
    # movement/chase never has a chance to wander it away from the LOS-aligned test position in between
    p.evaluate(SETUP_ROCCIA3)
    r = p.evaluate(arm("""
      e.lastSprintEnd=G.anim; // sprint "just" ended
      update(1/60);
      const tooSoon=e.ab.shoot.phase;
      e.ab.shoot.cd=0;e.lastSprintEnd-=(SHOOT_CFG.gapAfterSprint+0.5); // fast-forward past the 1.5s gap
      update(1/60);
      const afterGap=e.ab.shoot.phase;
      return {tooSoon,afterGap};
    """, x0, y, x0 + 3, y))
    check("shoot does not trigger right after a sprint ends (gap not elapsed)", r["tooSoon"] == "idle", r)
    check("shoot triggers once the 1.5s gap has elapsed since the sprint ended", r["afterGap"] == "aim", r)

    p.evaluate(SETUP_ROCCIA3)
    r = p.evaluate(arm("""
      e.lastShotEnd=G.anim; // a shot "just" fired
      e.ab.sprint.cd=0;
      update(1/60);
      const tooSoon=e.ab.sprint.phase;
      e.ab.sprint.cd=0;e.lastShotEnd-=(SHOOT_CFG.gapAfterSprint+0.5); // fast-forward past the 1.5s gap
      update(1/60);
      const afterGap=e.ab.sprint.phase;
      return {tooSoon,afterGap};
    """, x0, y, x0 + 3, y))
    check("sprint does not trigger right after a shot (gap not elapsed)", r["tooSoon"] == "idle", r)
    check("sprint triggers once the 1.5s gap has elapsed since the shot", r["afterGap"] == "wind", r)
    check("no console errors (1.5s gap both ways)", not errs, errs)

    # ---------------- no aim while scared, eaten, in the house or waiting
    for setup, label in [
        ("e.mode='s';", "scared"),
        ("e.mode='g';", "eaten"),
        ("e.wait=1;", "waiting"),
        ("e.tx=MET.house[0];e.ty=MET.house[1];", "in the house"),
    ]:
        p.evaluate(SETUP_ROCCIA3)
        r = p.evaluate(arm(setup + "update(1/60);return e.ab.shoot.phase;", x0, y, x0 + 3, y))
        check(f"no aim trigger while {label}", r == "idle", r)
    check("no console errors (gating)", not errs, errs)

    # ---------------- a power-up during aim cancels it, no projectile
    p.evaluate(SETUP_ROCCIA3)
    r = p.evaluate(arm("""
      MPROJ.clear();
      e.ab.shoot={phase:'aim',t:0.3,cd:0,dir:1};
      activatePower();
      return {phase:e.ab.shoot.phase,cd:e.ab.shoot.cd,proj:MPROJ.list.length};
    """, x0, y, x0 + 3, y))
    check("a power-up during 'aim' cancels the shot (idle, full cd, no projectile)",
          r["phase"] == "idle" and abs(r["cd"] - p.evaluate("SHOOT_CFG.cd")) < 1e-6 and r["proj"] == 0, r)
    check("no console errors (power-up cancel)", not errs, errs)

    # ---------------- a real shot: hit costs a life normally, ignored while powered up
    p.evaluate(SETUP_ROCCIA3)
    r = p.evaluate(arm("""
      MPROJ.clear();G.invuln=0; // SETUP_ROCCIA3 sets a large invuln for the other checks' safety; a real hit needs it off
      update(1/60); // idle -> aim
      for(let i=0;i<12;i++)update(0.05); // fires
      for(let i=0;i<20&&MPROJ.list.length;i++)update(0.05); // let it travel to the player
      return {state:G.state,left:MPROJ.list.length};
    """, x0, y, x0 + 3, y))
    check("a real shot that reaches a normal player costs a life via the shared MPROJ hit path",
          r["state"] == "dying" and r["left"] == 0, r)

    p.evaluate(SETUP_ROCCIA3)
    r = p.evaluate(arm("""
      MPROJ.clear();G.power=8;
      update(1/60);
      for(let i=0;i<12;i++)update(0.05);
      for(let i=0;i<20&&MPROJ.list.length;i++)update(0.05);
      return {state:G.state,left:MPROJ.list.length};
    """, x0, y, x0 + 3, y))
    check("a real shot while powered up does nothing and the projectile is still removed", r["state"] == "play" and r["left"] == 0, r)
    check("no console errors (real shot hit resolution)", not errs, errs)

    # ---------------- stage-2 aerei and all attrezzi never shoot
    r = p.evaluate("""(()=>{
      S.p.char='roccia';E1_STAGE_OV=2;
      cancelAnimationFrame(raf);devJump(1,0);
      const e=G.en[0];
      return {abils:E1AbilsFor(e),hasShoot:!!(e.ab&&e.ab.shoot)};
    })()""")
    check("stage-2 aerei never get 'shoot'", "shoot" not in r["abils"] and not r["hasShoot"], r)

    r = p.evaluate("""(()=>{
      S.p.char='algidone';E1_STAGE_OV=3;
      cancelAnimationFrame(raf);devJump(1,0);
      const e=G.en[0];
      return {family:E1Family(),abils:E1AbilsFor(e),hasShoot:!!(e.ab&&e.ab.shoot)};
    })()""")
    check("Algidone's family is 'attrezzi', not 'aerei'", r["family"] == "attrezzi", r)
    check("Algidone's stage-3 abilities never include 'shoot'", "shoot" not in r["abils"] and not r["hasShoot"], r)
    check("no console errors (stage-2/Algidone unaffected)", not errs, errs)

    # ---------------- reset on death and at girone start
    p.evaluate(SETUP_ROCCIA3)
    r = p.evaluate("""(()=>{
      const e=G.en[0];e.ab.shoot={phase:'aim',t:0.2,cd:0,dir:1};
      G.state='dying';G.t=0.001;update(0.02); // forced death -> resetActors(true) -> fresh E1InitGhost
      return G.en[0].ab.shoot;
    })()""")
    check("a forced death respawn resets every ghost's shoot to idle with a fresh randomised cd",
          r["phase"] == "idle" and 0 <= r["cd"] <= p.evaluate("SHOOT_CFG.cdStartMax"), r)

    r = p.evaluate("""(()=>{
      const e=G.en[0];e.ab.shoot={phase:'aim',t:0.2,cd:0,dir:1};
      cancelAnimationFrame(raf);devJump(1,0); // girone start -> resetActors -> fresh E1InitGhost
      return G.en[0].ab.shoot;
    })()""")
    check("girone start resets every ghost's shoot to idle with a fresh randomised cd",
          r["phase"] == "idle" and 0 <= r["cd"] <= p.evaluate("SHOOT_CFG.cdStartMax"), r)
    check("no console errors (reset points)", not errs, errs)

    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
