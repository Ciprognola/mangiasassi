#!/usr/bin/env python3
"""0.4.5_19 (E1b) tests: line-of-sight helper (losRC) and the maze projectile module (MPROJ),
the two helpers E2 (sprint) and E3 (shoot) will build on. No gameplay change in this build --
nothing calls them yet, the ABIL stubs stay no-op. Reuses the harness of test_f2b.py, same
pattern as test_e1a.py/test_m1a.py/test_b2.py.
Run: python tools/fbstub/test_e1b.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    # a real map via the dev girone jump (S class, mi=0, classic maze -- W=15,H=17,TUN=7)
    p.evaluate("cancelAnimationFrame(raf);devJump(1,0)")
    check("on a real map for this suite", p.evaluate("({W,H,TUN,house:MET.house})") is not None)

    # ---------------- losRC: geometry discovered at runtime (robust to the exact maze layout)
    geo = p.evaluate("""(()=>{
      const findRowRun=(y,len)=>{for(let x0=1;x0+len<W-1;x0++){let ok=true;
        for(let i=0;i<=len;i++){const x=x0+i;if(wall(x,y)||inHouse(x,y)){ok=false;break}}
        if(ok)return x0}return null};
      const findWallBetween=()=>{for(let y=0;y<H;y++){if(isTun(y))continue;
        for(let x=2;x<W-2;x++){if(wall(x,y)&&!wall(x-2,y)&&!wall(x+2,y)&&!inHouse(x-2,y)&&!inHouse(x+2,y))return{y,xa:x-2,xb:x+2}}}
        return null};
      let openRow=null;
      for(let y=0;y<H;y++){if(isTun(y))continue;const x0=findRowRun(y,3);if(x0!=null){openRow={y,x0};break}}
      const wallCase=findWallBetween();
      const h=MET.house,hy=Math.floor((h[1]+h[3])/2),hx0=h[0]-2,hx1=h[2]+2;
      return {openRow,wallCase,house:{hy,hx0,hx1,valid:hx0>=0&&hx1<W}};
    })()""")
    check("found an open same-row run for the 'open' case", geo["openRow"] is not None, geo)
    check("found a wall-between case", geo["wallCase"] is not None, geo)
    check("house rectangle leaves room on both sides for the door-block case", geo["house"]["valid"], geo)

    if geo["openRow"]:
        y, x0 = geo["openRow"]["y"], geo["openRow"]["x0"]
        r = p.evaluate("losRC({x:%d,y:%d},{x:%d,y:%d},5)" % (x0, y, x0 + 3, y))
        check("same row open, going right: hit with dir=1 dist=3", r == {"dir": 1, "dist": 3}, r)
        r2 = p.evaluate("losRC({x:%d,y:%d},{x:%d,y:%d},5)" % (x0 + 3, y, x0, y))
        check("same row open, going left: hit with dir=3 dist=3", r2 == {"dir": 3, "dist": 3}, r2)
        r3 = p.evaluate("losRC({x:%d,y:%d},{x:%d,y:%d},1)" % (x0, y, x0 + 3, y))
        check("beyond maxTiles -> null", r3 is None, r3)
        r4 = p.evaluate("losRC({x:%d,y:%d},{x:%d,y:%d},5)" % (x0, y, x0 + 3, y + 1))
        check("diagonal -> null", r4 is None, r4)
        r5 = p.evaluate("losRC({x:%d,y:%d},{x:%d,y:%d},5)" % (x0, y, x0, y))
        check("from == to -> {dir:null,dist:0}", r5 == {"dir": None, "dist": 0}, r5)

    if geo["wallCase"]:
        wy, xa, xb = geo["wallCase"]["y"], geo["wallCase"]["xa"], geo["wallCase"]["xb"]
        r = p.evaluate("losRC({x:%d,y:%d},{x:%d,y:%d},10)" % (xa, wy, xb, wy))
        check("wall strictly between -> null", r is None, r)

    hy, hx0, hx1 = geo["house"]["hy"], geo["house"]["hx0"], geo["house"]["hx1"]
    r = p.evaluate("losRC({x:%d,y:%d},{x:%d,y:%d},20)" % (hx0, hy, hx1, hy))
    check("the ghost house (door) lying between -> null", r is None, r)

    # tunnel wrap: the two tunnel-edge tiles are NOT treated as adjacent via wrap-around
    r = p.evaluate("losRC({x:0,y:TUN},{x:W-1,y:TUN},1)")
    check("tunnel wrap-around is never used for sight (edge tiles stay 'far', not adjacent)", r is None, r)
    check("no console errors (losRC)", not errs, errs)

    # ---------------- MPROJ: spawn/update geometry, on the same open run found above
    y, x0 = geo["openRow"]["y"], geo["openRow"]["x0"]

    r = p.evaluate("""(()=>{
      MPROJ.clear();MPROJ.spawn(%d,%d,1,4,'test');
      MPROJ.update(0.1);
      return MPROJ.list[0];
    })()""" % (x0, y))
    check("MPROJ moves by speed*dt", r is not None and abs(r["x"] - (x0 + 0.4)) < 1e-9 and abs(r["y"] - y) < 1e-9, r)

    r = p.evaluate("""(()=>{
      G.state='pause';
      const before=JSON.stringify(MPROJ.list[0]);
      if(G.state!=='pause')update(0.1); // the real loop()'s own pause gate
      const afterPaused=JSON.stringify(MPROJ.list[0]);
      G.state='play';
      update(0.016);
      const afterPlay=JSON.stringify(MPROJ.list[0]);
      return {frozen:before===afterPaused,moved:before!==afterPlay};
    })()""")
    check("MPROJ freezes while the game is paused (hooked inside update(), which loop() skips)", r["frozen"], r)
    check("MPROJ advances again once unpaused", r["moved"], r)

    r = p.evaluate("""(()=>{
      MPROJ.clear();MPROJ.spawn(%d,%d,1,1000,'test'); // huge speed: guaranteed to overshoot past any wall/edge in one small step
      MPROJ.update(0.05);
      return MPROJ.list.length;
    })()""" % (x0, y))
    check("removed on hitting a wall or leaving the grid", r == 0, r)

    r = p.evaluate("""(()=>{
      MPROJ.clear();
      for(let i=0;i<20;i++)MPROJ.spawn(%d,%d,1,0,'test');
      return MPROJ.list.length;
    })()""" % (x0, y))
    check("maxActive respected (spawned 20, cfg caps at MPROJ_CFG.maxActive)",
          r == p.evaluate("MPROJ_CFG.maxActive"), r)

    # a hit on a normal (non-invulnerable, non-powered, no active ability) player
    r = p.evaluate("""(()=>{
      MPROJ.clear();G.state='play';G.invuln=0;G.power=0;G.st=null;
      const [px,py]=pos(G.pl);
      MPROJ.spawn(px,py,0,0,'test');
      MPROJ.update(0.016);
      return {state:G.state,t:G.t,left:MPROJ.list.length};
    })()""")
    check("a hit on a normal player costs a life via the ghost-contact death path (killPlayer)",
          r["state"] == "dying" and abs(r["t"] - 1.3) < 1e-9, r)
    check("the projectile is removed after the hit", r["left"] == 0, r)

    for setup, label in [
        ("G.invuln=5;G.power=0;G.st=null", "invulnerable"),
        ("G.invuln=0;G.power=8;G.st=null", "powered up (ghosts scared)"),
        ("G.invuln=0;G.power=0;G.st={on:true}", "an active secret ability"),
    ]:
        r = p.evaluate("""(()=>{
          MPROJ.clear();G.state='play';%s;
          const [px,py]=pos(G.pl);
          MPROJ.spawn(px,py,0,0,'test');
          MPROJ.update(0.016);
          return {state:G.state,left:MPROJ.list.length};
        })()""" % setup)
        check(f"a hit while {label}: no death, projectile still removed",
              r["state"] == "play" and r["left"] == 0, r)
    p.evaluate("G.invuln=0;G.power=0;G.st=null")
    check("no console errors (MPROJ hit cases)", not errs, errs)

    # clear() on death and on girone start
    r = p.evaluate("""(()=>{
      MPROJ.spawn(%d,%d,1,0,'test');
      const before=MPROJ.list.length;
      G.state='dying';G.t=0.001;update(0.02); // forced death -> resetActors(true) -> MPROJ.clear()
      return {before,afterDeath:MPROJ.list.length};
    })()""" % (x0, y))
    check("MPROJ.clear() runs on a forced death respawn", r["before"] > 0 and r["afterDeath"] == 0, r)

    r = p.evaluate("""(()=>{
      MPROJ.spawn(%d,%d,1,0,'test');
      const before=MPROJ.list.length;
      cancelAnimationFrame(raf);devJump(1,0); // girone start -> resetActors() -> MPROJ.clear()
      return {before,afterStart:MPROJ.list.length};
    })()""" % (x0, y))
    check("MPROJ.clear() runs on girone start", r["before"] > 0 and r["afterStart"] == 0, r)

    r = p.evaluate("""(()=>{
      MPROJ.spawn(%d,%d,1,0,'test');
      const before=MPROJ.list.length;
      G.grid=G.grid.map(row=>row.map(ch=>ch==='.'?' ':ch)); // clear every pellet but one...
      G.pl.dir=null;G.pl.prog=0; // ...the one the player is standing on, so eating it empties the grid
      G.grid[G.pl.ty][G.pl.tx]='.';
      G.state='play';G.t=0;
      update(1/60);
      return {before,afterEnd:MPROJ.list.length,state:G.state};
    })()""" % (x0, y))
    check("MPROJ.clear() runs at girone end (all pellets eaten)", r["before"] > 0 and r["afterEnd"] == 0 and r["state"] == "clear", r)
    check("no console errors (MPROJ clear points)", not errs, errs)

    # nothing in the quicksave
    p.evaluate("cancelAnimationFrame(raf);devJump(1,0)")
    r = p.evaluate("""(()=>{
      MPROJ.spawn(1,1,1,2,'test');
      quicksave();
      const j=JSON.stringify(S.quick);
      return {hasKey:'MPROJ' in S.quick,inJson:j.includes('MPROJ')||j.includes('"owner"')};
    })()""")
    check("MPROJ is never part of the quicksave", not r["hasKey"] and not r["inJson"], r)
    p.evaluate("MPROJ.clear()")

    ctx.close(); b.close()

    # ---------------- re-run test_e1a.py in-process is out of scope for this file's exit code;
    # the brief asks to re-run it as a separate invocation (see the session report).
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
