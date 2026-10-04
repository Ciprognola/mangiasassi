#!/usr/bin/env python3
"""0.4.5_23 (E4) tests: attrezzi grease (fills ABIL.grease, CLAUDE.md §10.3). Algidone's stage 2/3
enemies only -- Uomo roccia's aerei and stage-1 attrezzi are unaffected.

CONFLICT NOTE (also in CHANGELOG.md/CLAUDE.md §10.9): the brief's own GREASE_CFG fallback specified
dropEvery:1.5s, maxPerGhost:4, life:5s, but CLAUDE.md §10.3 (the actual spec source, which the brief
says wins on any number) specifies every 8s, max 3 per ghost, fades out after 10s -- the build and these
tests follow §10.3, not the fallback block. slowMult (x0.6) matches both, no conflict there.

Uses the dev girone jump + the "Stadio" (E1a) override on Algidone to force stage 2/3 deterministically.
Reuses the harness of test_f2b.py, same pattern as test_e1a.py/test_e1b.py/test_e2.py/test_e3.py.
Run: python tools/fbstub/test_e4.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

def setup_algidone(stage):
    return """(()=>{
      S.p.char='algidone';E1_STAGE_OV=%d;
      cancelAnimationFrame(raf);devJump(1,0);
      G.state='play';G.invuln=99999;G.power=0;G.st=null;G.pl.dir=null;G.pl.prog=0;
      GREASE.clear();
      const findRowRun=(y,len)=>{for(let x0=1;x0+len<W-1;x0++){let ok=true;
        for(let i=0;i<=len;i++){const x=x0+i;if(wall(x,y)||inHouse(x,y)){ok=false;break}}
        if(ok)return x0}return null};
      let openRow=null;
      for(let y=0;y<H;y++){if(isTun(y))continue;const x0=findRowRun(y,4);if(x0!=null){openRow={y,x0};break}}
      window.__geo={openRow,house:{x:MET.house[0],y:MET.house[1]}};
      return window.__geo;
    })()""" % stage

with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    geo = p.evaluate(setup_algidone(2))
    check("found test geometry (open row + house rectangle)", geo["openRow"] is not None, geo)
    y, x0 = geo["openRow"]["y"], geo["openRow"]["x0"]
    hx, hy = geo["house"]["x"], geo["house"]["y"]

    # ---------------- drop timing: exactly one puddle after dropEvery, none before
    p.evaluate(setup_algidone(2))
    r = p.evaluate("""(()=>{
      const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=1;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
      e.ab.grease.t=0.02; // small remainder to the next due drop (between 1 and 2 ticks of 1/60s), regardless of the full dropEvery value
      update(1/60); // one tick (~0.01667s) is not yet enough to cross 0.02
      const before=GREASE.list.length;
      update(1/60); // a second tick pushes the cumulative dt past 0.02, crossing the due-time boundary; the ghost barely moves in these two 1/60s frames
      return {before,after:GREASE.list.length,puddle:GREASE.list[0],gTile:{x:e.tx,y:e.ty}};
    })()""" % (x0, y))
    check("no puddle before dropEvery elapses", r["before"] == 0, r)
    check("exactly one puddle right when dropEvery elapses, at the ghost's (then-current) tile",
          r["after"] == 1 and r["puddle"]["x"] == r["gTile"]["x"] and r["puddle"]["y"] == r["gTile"]["y"], r)
    check("no console errors (drop timing)", not errs, errs)

    # ---------------- no duplicate on a tile already holding one
    r = p.evaluate("""(()=>{
      GREASE.clear();
      GREASE.add(3,3,'other');
      const before=GREASE.list.length;
      GREASE.add(3,3,'other2');
      return {before,after:GREASE.list.length};
    })()""")
    check("no duplicate puddle on an already-occupied tile", r["before"] == 1 and r["after"] == 1, r)

    # ---------------- never inside the house
    r = p.evaluate("""(()=>{
      GREASE.clear();
      GREASE.add(%d,%d,'x');
      return GREASE.list.length;
    })()""" % (hx, hy))
    check("never drops a puddle inside the house", r == 0, r)
    check("no console errors (dedup/house)", not errs, errs)

    # ---------------- maxPerGhost respected, oldest removed first
    r = p.evaluate("""(()=>{
      GREASE.clear();
      const owner={};
      GREASE.add(1,1,owner);
      GREASE.list[0].t=1; // make this the oldest (least time remaining)
      GREASE.add(2,1,owner);
      GREASE.add(3,1,owner);
      const beforeCount=GREASE.list.length;
      GREASE.add(4,1,owner); // 4th for this owner -> exceeds maxPerGhost (3), oldest (1,1) must go
      return {beforeCount,afterCount:GREASE.list.length,has11:!!GREASE.at({x:1,y:1}),has4:!!GREASE.at({x:4,y:1})};
    })()""")
    check("maxPerGhost respected (still 3 for this owner after a 4th add)", r["beforeCount"] == 3 and r["afterCount"] == 3, r)
    check("the oldest puddle (least time left) was removed, the newest kept", not r["has11"] and r["has4"], r)
    check("no console errors (maxPerGhost)", not errs, errs)

    # ---------------- lifetime + removal
    r = p.evaluate("""(()=>{
      GREASE.clear();GREASE.add(5,5,'z');
      const life=GREASE_CFG.life;
      let stillThereJustBefore;
      for(let i=0;i<Math.floor(life/0.1)-1;i++)GREASE.update(0.1);
      stillThereJustBefore=GREASE.list.length===1;
      GREASE.update(1); // push well past life
      return {stillThereJustBefore,afterLife:GREASE.list.length};
    })()""")
    check("a puddle is still there just before its lifetime ends", r["stillThereJustBefore"], r)
    check("a puddle is removed once its lifetime elapses", r["afterLife"] == 0, r)
    check("no console errors (lifetime)", not errs, errs)

    # ---------------- player speed effect on/off a puddle; ghosts unaffected
    p.evaluate(setup_algidone(2))
    r = p.evaluate("""(()=>{
      GREASE.clear();
      const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=1;e.prog=0;e.stage=1;e.mode='n';e.wait=0; // stage 1: this ghost must not itself be slowed by anything of its own
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;
      update(1/60);
      const offSpeed=G.pl.speed;
      GREASE.add(%d,%d,'x');
      update(1/60);
      const onSpeed=G.pl.speed;
      return {offSpeed,onSpeed,ratio:onSpeed/offSpeed};
    })()""" % (x0, y, x0 + 3, y, x0 + 3, y))
    check("player speed unaffected off a puddle, then x0.6 while standing on one",
          abs(r["ratio"] - 0.6) < 1e-6, r)

    r = p.evaluate("""(()=>{
      const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=1;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
      GREASE.clear();GREASE.add(%d,%d,'x'); // a puddle right on the ghost's own tile
      update(1/60);
      return e.speed;
    })()""" % (x0, y, x0, y))
    baseline = p.evaluate("Math.min(5.7,4.3+G.stage*.18)*dfc().spd")
    check("ghosts standing on a puddle are never slowed by it", abs(r - baseline) < 0.05, {"e_speed": r, "baseline": baseline})
    check("no console errors (player/ghost speed)", not errs, errs)

    # ---------------- no drops while scared, eaten, in the house or waiting
    for setup, label in [
        ("e.mode='s';", "scared"),
        ("e.mode='g';", "eaten"),
        ("e.wait=1;", "waiting"),
        ("e.tx=MET.house[0];e.ty=MET.house[1];", "in the house"),
    ]:
        p.evaluate(setup_algidone(2))
        r = p.evaluate("""(()=>{
          GREASE.clear();
          const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=1;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
          e.ab.grease.t=0;
          %s
          update(1/60);
          return GREASE.list.length;
        })()""" % (x0, y, setup))
        check(f"no puddle drop while {label}", r == 0, r)
    check("no console errors (gating)", not errs, errs)

    # ---------------- clear on death and at girone start; nothing in the quicksave
    p.evaluate(setup_algidone(2))
    r = p.evaluate("""(()=>{
      const e=G.en[0];e.tx=%d;e.ty=%d;e.dir=1;e.prog=0;e.stage=2;e.mode='n';e.wait=0;
      GREASE.clear();GREASE.add(%d,%d,e);
      const before=GREASE.list.length;
      G.state='dying';G.t=0.001;update(0.02); // forced death -> resetActors(true) -> GREASE.clear()
      return {before,afterDeath:GREASE.list.length};
    })()""" % (x0, y, x0, y))
    check("GREASE.clear() runs on a forced death respawn", r["before"] == 1 and r["afterDeath"] == 0, r)

    r = p.evaluate("""(()=>{
      GREASE.add(%d,%d,'x');
      const before=GREASE.list.length;
      cancelAnimationFrame(raf);devJump(1,0); // girone start -> resetActors -> GREASE.clear()
      return {before,afterStart:GREASE.list.length};
    })()""" % (x0, y))
    check("GREASE.clear() runs on girone start", r["before"] == 1 and r["afterStart"] == 0, r)

    r = p.evaluate("""(()=>{
      GREASE.add(1,1,'x');
      quicksave();
      const j=JSON.stringify(S.quick);
      return {hasKey:'GREASE' in S.quick,inJson:j.includes('GREASE')};
    })()""")
    check("GREASE is never part of the quicksave", not r["hasKey"] and not r["inJson"], r)
    p.evaluate("GREASE.clear()")
    check("no console errors (clear points/quicksave)", not errs, errs)

    # ---------------- Uomo roccia (aerei) never drops grease; stage-1 attrezzi never drop
    r = p.evaluate("""(()=>{
      S.p.char='roccia';E1_STAGE_OV=2;
      cancelAnimationFrame(raf);devJump(1,0);
      const e=G.en[0];
      return {family:E1Family(),abils:E1AbilsFor(e),hasGrease:!!(e.ab&&e.ab.grease)};
    })()""")
    check("Uomo roccia's family is 'aerei', not 'attrezzi'", r["family"] == "aerei", r)
    check("Uomo roccia's ghosts never get a 'grease' entry", "grease" not in r["abils"] and not r["hasGrease"], r)

    r = p.evaluate("""(()=>{
      S.p.char='algidone';E1_STAGE_OV=1;
      cancelAnimationFrame(raf);devJump(1,0);
      const e=G.en[0];
      return {abils:E1AbilsFor(e),hasGrease:!!(e.ab&&e.ab.grease)};
    })()""")
    check("stage-1 attrezzi never get a 'grease' entry", "grease" not in r["abils"] and not r["hasGrease"], r)
    check("no console errors (aerei/stage-1 unaffected)", not errs, errs)

    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
