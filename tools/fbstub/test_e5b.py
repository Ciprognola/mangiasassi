#!/usr/bin/env python3
"""0.4.5_25 (E5b) tests: Super Panino wall-breaking (fills the direction-choice half of the merged host's
movement, CLAUDE.md §10.3 -- "breaks walls in its path via the shared smashable() helper; protected
cells never"). Only the merged host is affected: normal ghosts, aerei, grease, and the merge/split/eat
rules built in E5a (0.4.5_24) are unchanged.

Uses the dev girone jump + the "Stadio" (E1a) override on Algidone, plus PANINO.startIntro directly to
reach 'merged' deterministically with the host at a chosen tile (same pattern as test_e5a.py, which also
never validates range/eligibility through PANINO.startIntro -- that is check()'s own job, exercised in
test_e5a.py already), and "Forza Super Panino" (#jgPan) through a real click for one check.
Run: python tools/fbstub/test_e5b.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("srv = serve()")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness incl. dev_click


def setup_algidone(stage=3, girone=1, mi=0):
    return """(()=>{
      S.p.char='algidone';E1_STAGE_OV=%d;
      cancelAnimationFrame(raf);devJump(%d,%d);
      G.state='play';G.invuln=0;G.power=0;G.st=null;G.pl.dir=null;G.pl.prog=0;
      GREASE.clear();MPROJ.clear();PANINO.clear();
      const findRowRun=(y,len)=>{for(let x0=1;x0+len<W-1;x0++){let ok=true;
        for(let i=0;i<=len;i++){const x=x0+i;if(wall(x,y)||inHouse(x,y)){ok=false;break}}
        if(ok)return x0}return null};
      const findWallBetween=()=>{for(let y=0;y<H;y++){if(isTun(y))continue;
        for(let x=2;x<W-2;x++){if(wall(x,y)&&smashable(x,y)&&!wall(x-2,y)&&!wall(x+2,y)&&!inHouse(x-2,y)&&!inHouse(x+2,y))return{y,xa:x-2,xb:x+2,xw:x}}}
        return null};
      let openRow=null;
      for(let y=0;y<H;y++){if(isTun(y))continue;const x0=findRowRun(y,4);if(x0!=null){openRow={y,x0};break}}
      window.__geo={openRow,house:{x:MET.house[0],y:MET.house[1]},nEn:G.en.length,wallCase:findWallBetween()};
      return window.__geo;
    })()""" % (stage, girone, mi)


def merge_at(x, y):
    """host (G.en[0]) placed at (x,y), stage 3, fully active; partner (G.en[1]) merged right away via
    PANINO.startIntro (bypasses check()'s own range/eligibility gates -- those are test_e5a.py's job) --
    G.t forced to 0 so the very next update() tick finishes the intro and seeds the real 12s life.
    G.invuln is forced sky-high because several tests let a chasing host actually reach the player over
    many simulated seconds -- without this, 3 real deaths null out G via finishRun() mid-loop."""
    return """
      G.invuln=99999;
      const e0=G.en[0],e1=G.en[1];
      e0.tx=%d;e0.ty=%d;e0.dir=1;e0.prog=0;e0.stage=3;e0.mode='n';e0.wait=0;e0.merged=false;e0.pan=null;
      e1.tx=%d;e1.ty=%d;e1.dir=1;e1.prog=0;e1.stage=3;e1.mode='n';e1.wait=0;e1.merged=false;e1.pan=null;
      if(e0.ab)e0.ab.panino={cd:0};if(e1.ab)e1.ab.panino={cd:0};
      G.anim=10;G.state='play';
      PANINO.startIntro(e0,e1);G.t=0;update(1/60);
      const host=e0;host.pan.t=1e9; // stay merged for the whole test window unless a test overrides it
    """ % (x, y, x, y)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    geo = p.evaluate(setup_algidone(3))
    check("found test geometry (open row + a smashable wall between two open cells)", geo["wallCase"] is not None, geo)
    wy, xa, xb, xw = geo["wallCase"]["y"], geo["wallCase"]["xa"], geo["wallCase"]["xb"], geo["wallCase"]["xw"]

    # ---------------- breaks a smashable wall in its path and reaches the far side; cell becomes floor
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;G.invuln=99999; // far side, so chase pulls the host through the wall
      const wallWasWall=wall(%d,%d);
      let reachedFarSide=false;
      for(let i=0;i<600;i++){update(0.05);if(host.tx>=%d)reachedFarSide=true} // up to 30s; "reached" = crossed onto the far side at some point, not necessarily still sitting there at tick 600
      return {wallWasWall,cellNow:G.grid[%d][%d],reachedFarSide,breaks:host.pan.breaks};
    })()""" % (merge_at(xa, wy), xb, wy, xw, wy, xb, wy, xw))
    check("the wall cell was really a wall before the test", r["wallWasWall"], r)
    check("the smashed cell becomes floor (not a pellet)", r["cellNow"] == " ", r)
    check("the merged host breaks through and reaches the far side of the wall", r["reachedFarSide"], r)
    check("at least one wall was broken to get there", r["breaks"] >= 1, r)
    check("no console errors (breakthrough)", not errs, errs)

    # ---------------- budget: never more than breakMax walls broken in one merge; host never clips a wall (S/M/L sweep)
    for cls, girone, mi in [("S", 1, 0), ("M", 4, 5), ("L", 6, 8)]:
        geoC = p.evaluate(setup_algidone(3, girone=girone, mi=mi))
        yC, x0C = geoC["openRow"]["y"], geoC["openRow"]["x0"]
        r = p.evaluate("""(()=>{
          %s
          // snapshot every protected wall cell before the run
          const before=[];
          for(let yy=0;yy<H;yy++)for(let xx=0;xx<W;xx++)if(protectedCell(xx,yy)&&wall(xx,yy))before.push(xx+','+yy);
          let clipped=false;
          for(let i=0;i<600;i++){ // 30s
            update(0.05);
            if(wall(host.tx,host.ty))clipped=true;
          }
          const stillWall=before.filter(k=>{const[xx,yy]=k.split(',').map(Number);return wall(xx,yy)});
          return {protectedCount:before.length,stillProtectedWalls:stillWall.length,breaks:host.pan.breaks,clipped};
        })()""" % merge_at(x0C, yC))
        check(f"({cls}) every protected cell that was a wall is still a wall after 30 merged seconds",
              r["stillProtectedWalls"] == r["protectedCount"] and r["protectedCount"] > 0, r)
        check(f"({cls}) breakMax (8) respected over the whole 30s run", r["breaks"] <= 8, r)
        check(f"({cls}) the merged host is never on a wall tile (no clipping)", not r["clipped"], r)
    check("no console errors (S/M/L protected-cell + budget + clipping sweep)", not errs, errs)

    # ---------------- breakPause: host holds still right after a break, then moves on
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;G.invuln=99999; // contact must never end the run mid-stress-test
      let brokeAt=-1,posAfterBreak=null,stillHeld=true,movedAfterPause=false;
      const pauseTicks=Math.round(PANINO_CFG.breakPause/(1/60));
      for(let i=0;i<300;i++){
        update(1/60);
        if(brokeAt<0&&G.grid[%d][%d]===' '){brokeAt=i;posAfterBreak={tx:host.tx,ty:host.ty}}
        if(brokeAt>=0&&i>brokeAt&&i<brokeAt+pauseTicks-1){
          if(host.tx!==posAfterBreak.tx||host.ty!==posAfterBreak.ty)stillHeld=false;
        }
        if(brokeAt>=0&&i>=brokeAt+pauseTicks+3&&(host.tx!==posAfterBreak.tx||host.ty!==posAfterBreak.ty))movedAfterPause=true;
      }
      return {broke:brokeAt>=0,stillHeld,movedAfterPause};
    })()""" % (merge_at(xa, wy), xb, wy, wy, xw))
    check("a break happened", r["broke"], r)
    check("the host's position is unchanged for breakPause right after a break", r["stillHeld"], r)
    check("the host moves on again once breakPause has elapsed", r["movedAfterPause"], r)
    check("no console errors (breakPause)", not errs, errs)

    # ---------------- scared Super Panino breaks nothing
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      activatePower(); // host turns scared
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;G.invuln=99999; // contact must never end the run mid-stress-test
      for(let i=0;i<200;i++)update(0.05); // 10s, safely inside the 15s power-up window
      return {wallStillWall:wall(%d,%d),breaks:host.pan.breaks,scared:host.mode==='s'};
    })()""" % (merge_at(xa, wy), xb, wy, xw, wy))
    check("host really turned scared", r["scared"], r)
    check("a scared Super Panino never breaks a wall", r["wallStillWall"] and r["breaks"] == 0, r)
    check("no console errors (scared)", not errs, errs)

    # ---------------- normal (non-merged) ghosts never break walls
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      const e0=G.en[0];
      e0.tx=%d;e0.ty=%d;e0.dir=1;e0.prog=0;e0.stage=3;e0.mode='n';e0.wait=0;e0.merged=false;e0.pan=null;
      if(e0.ab)e0.ab.panino={cd:0};G.anim=10;
      for(let i=1;i<G.en.length;i++)G.en[i].stage=1; // the OTHER ghosts must not naturally pair up with each other mid-test and break something unrelated
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;G.invuln=99999; // contact must never end the run mid-stress-test
      for(let i=0;i<300;i++)update(0.05); // 15s, never merged
      return wall(%d,%d);
    })()""" % (xa, wy, xb, wy, xw, wy))
    check("a lone (never-merged) stage-3 attrezzo never breaks a wall", r, r)

    # ---------------- after a split, neither ghost breaks walls any more
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      const partner=G.en[host.pan.partner];
      host.pan.t=0.001;update(1/60); // force the split
      const stillPan=!!host.pan||!!partner.merged;
      host.tx=%d;host.ty=%d;host.dir=1;host.prog=0;host.mode='n';
      partner.tx=%d;partner.ty=%d;partner.dir=1;partner.prog=0;partner.mode='n';
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;G.invuln=99999; // contact must never end the run mid-stress-test
      for(let i=0;i<300;i++)update(0.05); // 15s post-split
      return {stillPan,wallStillWall:wall(%d,%d)};
    })()""" % (merge_at(xa, wy), xa, wy, xa, wy, xb, wy, xw, wy))
    check("split really cleared the merge (neither ghost still has pan/merged)", not r["stillPan"], r)
    check("after the split neither ghost breaks walls", r["wallStillWall"], r)
    check("no console errors (non-merged/post-split)", not errs, errs)

    # ---------------- broken cells stay floor after the split, until the next girone start restores the map
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;G.invuln=99999; // contact must never end the run mid-stress-test
      for(let i=0;i<600;i++)update(0.05); // up to 30s to break through
      const brokenAfterBreak=G.grid[%d][%d]===' ';
      host.pan.t=0.001;update(1/60); // split
      const stillFloorAfterSplit=G.grid[%d][%d]===' ';
      cancelAnimationFrame(raf);devJump(1,0); // next girone start -> fresh map
      const wallRestored=wall(%d,%d);
      return {brokenAfterBreak,stillFloorAfterSplit,wallRestored};
    })()""" % (merge_at(xa, wy), xb, wy, wy, xw, wy, xw, xw, wy))
    check("the wall broke during the merge", r["brokenAfterBreak"], r)
    check("the broken cell stays floor right after the split", r["stillFloorAfterSplit"], r)
    check("the next girone start restores a fresh map (wall present again)", r["wallRestored"], r)
    check("no console errors (persistence/restore)", not errs, errs)

    # ---------------- pellets on a broken cell follow the same rule as a player smash (never a pellet, always floor)
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;G.invuln=99999; // contact must never end the run mid-stress-test
      for(let i=0;i<600;i++)update(0.05); // up to 30s to break through
      return G.grid[%d][%d];
    })()""" % (merge_at(xa, wy), xb, wy, wy, xw))
    check("a broken cell is plain floor (' '), the same rule smash() already applies to the player -- never a pellet",
          r == " ", r)
    check("no console errors (pellet rule)", not errs, errs)

    # ---------------- dev button through a real click: forced merge can then break a wall
    geo2 = p.evaluate(setup_algidone(3))
    wc2 = geo2["wallCase"]
    p.evaluate("""(()=>{
      const e0=G.en[0],e1=G.en[1];
      e0.tx=%d;e0.ty=%d;e0.dir=1;e0.prog=0;e0.stage=3;e0.mode='n';e0.wait=0;e0.merged=false;e0.pan=null;
      e1.tx=%d;e1.ty=%d;e1.dir=1;e1.prog=0;e1.stage=3;e1.mode='n';e1.wait=0;e1.merged=false;e1.pan=null;
      G.anim=0;G.state='play';
      cancelAnimationFrame(raf); // devJump's own buildGameDOM() left a real-time rAF loop running; dev_click's real waits below must not let it drive the merge on its own
      go('menu');
    })()""" % (wc2["xa"], wc2["y"], wc2["xa"] + 1, wc2["y"]))
    dev_click(p, "#jgPan")
    r = p.evaluate("""(()=>{
      cancelAnimationFrame(raf);
      const host=G.en[0];if(!host.pan)return{merged:false};
      G.t=0;update(1/60); // the click landed mid-intro (G.state='panintro'); finish it deterministically, same trick merge_at() uses, before seeding a long life below
      host.pan.t=1e9;
      screen='game';buildGameDOM();cancelAnimationFrame(raf); // back on the game screen so update()'s own DOM writes (#sc, ...) have somewhere to land, but drive update() manually below, not via the real rAF loop buildGameDOM() just started
      G.pl.tx=%d;G.pl.ty=%d;G.pl.dir=null;G.pl.prog=0;G.invuln=99999; // contact must never end the run mid-stress-test
      for(let i=0;i<600;i++)update(0.05); // up to 30s to break through
      return {merged:true,broke:host.pan.breaks>0};
    })()""" % (wc2["xb"], wc2["y"]))
    check("«Forza Super Panino» (real click) merges, and the resulting host can then break a wall",
          r["merged"] and r["broke"], r)
    check("no console errors (dev button)", not errs, errs)

    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
