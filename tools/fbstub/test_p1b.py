#!/usr/bin/env python3
"""0.4.5_4 (P1b) tests: 5 s respawn aura (invulnerability) in the maze, protectedCell()/smashable() (outer ring, tunnel rows, ghost house + door),
the «sad» screen is gone. Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_p1b.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

PLACE = "(()=>{const P=G.pl;for(const e of G.en){e.tx=P.tx;e.ty=P.ty;e.dir=null;e.prog=0;e.wait=0;e.mode='n';e.gt=0}})()"


def start(p, hard=False):
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    if hard:
        p.evaluate("S.p.g5=true;persist();render()"); p.wait_for_timeout(200)
        p.click("[data-tile=hard]")
    else:
        p.click("[data-tile=new]")
    p.wait_for_function("G&&G.state==='play'", timeout=8000)


def lose_life(p):
    """a real life loss: the normal dying branch of update() runs (state 'dying' -> lives-- -> resetActors)"""
    p.evaluate("G.state='dying';G.t=0.05"); p.wait_for_function("G&&G.state==='ready'", timeout=5000)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p, 600)

    # ---------------- (a) respawn invulnerability
    for hard in (False, True):
        tag = "Hardcore" if hard else "normal"
        start(p, hard); lives0 = p.evaluate("G.lives")
        lose_life(p)
        s = p.evaluate("({lives:G.lives,inv:G.invuln,st:G.state})")
        check(f"({tag}) losing a life sets invulnerability to 5 s", s["lives"] == lives0 - 1 and abs(s["inv"] - 5) < 0.01, s)
        p.wait_for_function("G.state==='play'", timeout=5000)
        inv = p.evaluate("G.invuln"); check(f"({tag}) it starts counting down once the run is in play", 3 < inv <= 5, inv)
        p.evaluate("window.__aura=0;if(!window.__da){window.__da=drawRespawnAura;drawRespawnAura=function(){if(G.invuln>0)window.__aura++;return window.__da.apply(this,arguments)}};window.__ov=setInterval(()=>{%s},16);0" % PLACE)
        p.wait_for_timeout(3500)
        s = p.evaluate("({st:G.state,lives:G.lives,inv:G.invuln})")
        check(f"({tag}) ghosts sitting on the player do not kill while invulnerable", s["st"] == "play" and s["lives"] == lives0 - 1 and s["inv"] > 0, s)
        p.wait_for_function("G.state==='dying'", timeout=5000)
        p.evaluate("clearInterval(window.__ov);0")
        check(f"({tag}) once the 5 s are over the same overlap kills", p.evaluate("G.state==='dying'"))
        z = p.evaluate("(()=>{let n=0;const c={createRadialGradient(){n++;return{addColorStop(){}}},save(){},restore(){},beginPath(){},arc(){},fill(){}};const iv=G.invuln;G.invuln=0;window.__da(c,10,10,20);const z=n;G.invuln=3;window.__da(c,10,10,20);G.invuln=iv;return [z,n]})()")
        check(f"({tag}) no aura once the protection has ended, aura when it is on", z == [0, 1], z)
        a1 = p.evaluate("window.__aura"); check(f"({tag}) the aura was drawn during the window (frames counted)", a1 > 100, a1)
        p.wait_for_function("G.state==='ready'||screen!=='game'", timeout=5000)
        if p.evaluate("screen") == "game":
            p.evaluate("clearInterval(window.__ov);0")
    # steel/boar immunity untouched: with an ability active a ghost still does not kill even at invuln 0
    start(p); p.evaluate("G.invuln=0;G.st={on:true,t:8,tp:9,cd:0,boar:false}"); p.evaluate("window.__ov=setInterval(()=>{%s},16);0" % PLACE); p.wait_for_timeout(800)
    check("Acciaio immunity unchanged (no death with the ability on)", p.evaluate("G.state==='play'"))
    p.evaluate("clearInterval(window.__ov);0")
    # quicksave + resume keep working after a life loss
    start(p); lose_life(p); p.wait_for_function("G.state==='play'", timeout=5000)
    p.evaluate("quicksave();go('menu')"); p.wait_for_timeout(300)
    p.click("[data-tile=cur]"); p.wait_for_function("G&&G.state==='ready'||G.state==='play'", timeout=5000)
    check("quicksave/resume after a life loss works (run resumes, lives and the remaining protection kept)", p.evaluate("G.lives")==2 and p.evaluate("G.invuln")>2, p.evaluate("[G.lives,G.invuln]"))
    check("no console errors (invulnerability)", not errs, errs)

    # ---------------- (b) protected cells
    p.evaluate("cancelAnimationFrame(raf);screen='menu';0")  # stop the maze loop: the checks below swap G for a stub
    r = p.evaluate("""(()=>{const out=[];
      for(let mi=0;mi<MAPS.length;mi++){
        setDims(mi);G={grid:freshGrid(mi)};const h=MET.house;let bad=[],free=0,prot=0;
        for(let y=0;y<H;y++)for(let x=0;x<W;x++){
          const ring=x<1||x>W-2||y<1||y>H-2,tun=isTun(y),hs=x>=h[0]-1&&x<=h[2]+1&&y>=h[1]-1&&y<=h[3]+1;
          if(smashable(x,y)){free++;if(ring||tun||hs)bad.push([x,y])}
          if(G.grid[y][x]==='#'&&(ring||tun||hs))prot++}
        out.push({mi,bad:bad.length,free,prot})}
      return out})()""")
    check("smashable(): never true on the outer ring, a tunnel row or the ghost house + door (all 15 maps)", all(o["bad"] == 0 for o in r), [o for o in r if o["bad"]])
    check("smashable(): ordinary interior walls stay smashable on every map", all(o["free"] > 10 for o in r), [o["free"] for o in r])
    r2 = p.evaluate("""(()=>{setDims(0);G={grid:freshGrid(0),st:{on:true,boar:true,stress:0},pl:null,fx:[],parts:[],shake:0};
      const DXs=[0,1,0,-1],DYs=[-1,0,1,0],h=MET.house,out={prot:null,free:null};
      const tryWall=(wx,wy)=>{ // an open neighbour of the wall, the player pushes into it
        for(let d=0;d<4;d++){const nx=wx-DXs[d],ny=wy-DYs[d];if(nx<0||ny<0||nx>=W||ny>=H||G.grid[ny][nx]==='#')continue;
          const pl={tx:nx,ty:ny,dir:null,next:d,prog:0};const before=G.grid[wy][wx];chooseP(pl);return [before,G.grid[wy][wx]]}return null};
      // a protected wall next to the house (not on the ring)
      for(let y=h[1]-1;y<=h[3]+1&&!out.prot;y++)for(let x=h[0]-1;x<=h[2]+1&&!out.prot;x++)if(G.grid[y][x]==='#'&&!(x<1||x>W-2||y<1||y>H-2)){const r=tryWall(x,y);if(r)out.prot=r}
      // an ordinary wall away from everything
      for(let y=2;y<H-2&&!out.free;y++)for(let x=2;x<W-2&&!out.free;x++)if(G.grid[y][x]==='#'&&!protectedCell(x,y)){const r=tryWall(x,y);if(r)out.free=r}
      return out})()""")
    check("Cinghiale pushing into a ghost-house wall does not break it", r2["prot"] == ["#", "#"], r2)
    check("(control) the same push into an ordinary wall does break it", r2["free"] == ["#", " "], r2)
    check("no console errors (protected cells)", not errs, errs)

    # ---------------- «sad» screen removed
    r3 = p.evaluate("({fn:typeof renderSad,arm:typeof sadArm,id:[...SCREEN_IDS].includes('sad-countdown')})")
    check("the unreachable «sad» screen is gone (renderSad, sadArm, screen id)", r3 == {"fn": "undefined", "arm": "undefined", "id": False}, r3)
    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
