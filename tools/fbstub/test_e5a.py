#!/usr/bin/env python3
"""0.4.5_24 (E5a) tests: attrezzi stage-3 Super Panino merge (fills ABIL.panino, CLAUDE.md §10.3).
Merge/intro/merged movement+contact+eating/timed split only -- NO wall-breaking (that's E5b). Algidone's
stage-3 attrezzi only; Uomo roccia's aerei and stage-1/2 attrezzi are unaffected.

Uses the dev girone jump + the "Stadio" (E1a) override on Algidone to force stage 3 deterministically, plus
the new "Forza Super Panino" dev button (#jgPan) through a real click for the one DOM-level check.
Reuses the harness of test_f2b.py, same pattern as test_e1a.py/test_e2.py/test_e3.py/test_e4.py.
Run: python tools/fbstub/test_e5a.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("srv = serve()")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness incl. dev_click, excludes F2b's own executable suite


def setup_algidone(stage=3, girone=1, mi=0):
    return """(()=>{
      S.p.char='algidone';E1_STAGE_OV=%d;
      cancelAnimationFrame(raf);devJump(%d,%d);
      G.state='play';G.invuln=0;G.power=0;G.st=null;G.pl.dir=null;G.pl.prog=0;
      GREASE.clear();MPROJ.clear();PANINO.clear();
      const findRowRun=(y,len)=>{for(let x0=1;x0+len<W-1;x0++){let ok=true;
        for(let i=0;i<=len;i++){const x=x0+i;if(wall(x,y)||inHouse(x,y)){ok=false;break}}
        if(ok)return x0}return null};
      let openRow=null;
      for(let y=0;y<H;y++){if(isTun(y))continue;const x0=findRowRun(y,4);if(x0!=null){openRow={y,x0};break}}
      window.__geo={openRow,house:{x:MET.house[0],y:MET.house[1]},nEn:G.en.length};
      return window.__geo;
    })()""" % (stage, girone, mi)


def place_pair(x0, y, extra0="", extra1=""):
    """two adjacent (range<=1), fully-active stage-3 attrezzi ghosts at (x0,y) and (x0+1,y)."""
    return """
      const e0=G.en[0],e1=G.en[1];
      e0.tx=%d;e0.ty=%d;e0.dir=1;e0.prog=0;e0.stage=3;e0.mode='n';e0.wait=0;e0.merged=false;e0.pan=null;%s
      e1.tx=%d;e1.ty=%d;e1.dir=1;e1.prog=0;e1.stage=3;e1.mode='n';e1.wait=0;e1.merged=false;e1.pan=null;%s
      if(e0.ab)e0.ab.panino={cd:0};if(e1.ab)e1.ab.panino={cd:0};
      G.anim=10;G.state='play';
    """ % (x0, y, extra0, x0 + 1, y, extra1)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    geo = p.evaluate(setup_algidone(3))
    check("found test geometry (open row + house rectangle)", geo["openRow"] is not None, geo)
    check("class has at least 2 ghosts to pair", geo["nEn"] >= 2, geo)
    y, x0 = geo["openRow"]["y"], geo["openRow"]["x0"]
    hx, hy = geo["house"]["x"], geo["house"]["y"]

    # ---------------- trigger: merges at range<=1 with both active
    p.evaluate(setup_algidone(3))
    r = p.evaluate("(()=>{%s update(1/60); return {state:G.state,pan0:!!G.en[0].pan,merged1:!!G.en[1].merged};})()" % place_pair(x0, y))
    check("two eligible stage-3 attrezzi within range 1 merge (state -> panintro, ghost 0 = host)",
          r["state"] == "panintro" and r["pan0"] and r["merged1"], r)
    check("no console errors (trigger)", not errs, errs)

    # ---------------- no merge: not both stage 3
    p.evaluate(setup_algidone(3))
    r = p.evaluate("(()=>{%s G.en[1].stage=2; update(1/60); return G.state;})()" % place_pair(x0, y))
    check("no merge if the partner is stage 2, not 3", r != "panintro", r)

    # ---------------- no merge: scared / eaten / waiting / in the house
    for setup, label in [
        ("G.en[1].mode='s';", "scared"),
        ("G.en[1].mode='g';G.en[1].gt=5;", "eaten"),
        ("G.en[1].wait=1;", "waiting"),
        ("G.en[1].tx=%d;G.en[1].ty=%d;" % (hx, hy), "in the house"),
    ]:
        p.evaluate(setup_algidone(3))
        r = p.evaluate("(()=>{%s %s update(1/60); return G.state;})()" % (place_pair(x0, y), setup))
        check(f"no merge while the partner is {label}", r != "panintro", r)
    check("no console errors (gating)", not errs, errs)

    # ---------------- no merge during graceStart (girone start or after a death respawn)
    p.evaluate(setup_algidone(3))
    r = p.evaluate("(()=>{%s G.anim=2; update(1/60); return G.state;})()" % place_pair(x0, y))
    check("no merge inside the graceStart window (G.anim=2 < 6)", r != "panintro", r)
    r = p.evaluate("(()=>{G.anim=7; update(1/60); return G.state;})()")
    check("merges once past graceStart (same setup, G.anim advanced to 7)", r == "panintro", r)

    # ---------------- no merge while either ghost is on reMergeCd
    p.evaluate(setup_algidone(3))
    r = p.evaluate("(()=>{%s G.en[0].ab.panino.cd=5; update(1/60); return G.state;})()" % place_pair(x0, y))
    check("no merge while the candidate host is on reMergeCd", r != "panintro", r)
    r = p.evaluate("(()=>{G.en[0].ab.panino.cd=0;update(1/60);return G.state;})()")
    check("merges once reMergeCd clears (same setup)", r == "panintro", r)

    # ---------------- no merge for aerei (Uomo roccia)
    r = p.evaluate("""(()=>{
      S.p.char='roccia';E1_STAGE_OV=3;cancelAnimationFrame(raf);devJump(1,0);
      const e=G.en[0];
      return {family:E1Family(),abils:E1AbilsFor(e),hasPanino:!!(e.ab&&e.ab.panino)};
    })()""")
    check("Uomo roccia's family is 'aerei', not 'attrezzi'", r["family"] == "aerei", r)
    check("aerei ghosts never get a 'panino' entry", "panino" not in r["abils"] and not r["hasPanino"], r)
    check("no console errors (aerei unaffected)", not errs, errs)

    # ---------------- never 2 Super Panino at once (maxActive)
    geoL = p.evaluate(setup_algidone(3, girone=6, mi=8))  # L class (Palude): 5 ghosts, enough for two pairs
    check("L-class test map has 5 ghosts (need 2 pairs for this check)", geoL["nEn"] >= 4, geoL)
    yL, x0L = geoL["openRow"]["y"], geoL["openRow"]["x0"]
    r = p.evaluate("""(()=>{
      %s
      const e2=G.en[2],e3=G.en[3];
      e2.tx=%d;e2.ty=%d;e2.dir=1;e2.prog=0;e2.stage=3;e2.mode='n';e2.wait=0;e2.merged=false;e2.pan=null;if(e2.ab)e2.ab.panino={cd:0};
      e3.tx=%d;e3.ty=%d;e3.dir=1;e3.prog=0;e3.stage=3;e3.mode='n';e3.wait=0;e3.merged=false;e3.pan=null;if(e3.ab)e3.ab.panino={cd:0};
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60); // finish the first pair's intro -> merged, back to 'play'
      const stateAfterFirst=G.state,pansAfterFirst=G.en.filter(x=>x.pan).length;
      update(1/60); // now let the loop try to pair e2/e3 too
      return {stateAfterFirst,pansAfterFirst,stillOne:G.en.filter(x=>x.pan).length,pan2:!!e2.pan,pan3:!!e3.pan};
    })()""" % (place_pair(x0L, yL), x0L + 3, yL, x0L + 4, yL))
    check("first pair reaches 'merged' (back to play, one host)", r["stateAfterFirst"] == "play" and r["pansAfterFirst"] == 1, r)
    check("a second eligible pair never merges while one Super Panino is already active",
          r["stillOne"] == 1 and not r["pan2"] and not r["pan3"], r)
    check("no console errors (maxActive)", not errs, errs)

    # ---------------- intro: everything frozen for introT, then merged
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      G.power=5;G.invuln=3;GREASE.add(0,0,'z');GREASE.list[0].t=4.2;G.stage=3;
      const plBefore={tx:G.pl.tx,ty:G.pl.ty};
      update(1/60); // trigger merge -> panintro (this one tick still ran as a normal 'play' frame before the state flip, so power/invuln/grease legitimately decayed by this single tick already)
      const afterTrigger={state:G.state,power:G.power,invuln:G.invuln,greaseT:GREASE.list[0].t,stage:G.stage};
      const introT=PANINO_CFG.introT;
      let moved=false;
      for(let i=0;i<Math.floor(introT/0.05)-1;i++){
        update(0.05);
        if(G.pl.tx!==plBefore.tx||G.pl.ty!==plBefore.ty)moved=true;
      }
      const frozenSnapshot={state:G.state,power:G.power,invuln:G.invuln,greaseT:GREASE.list[0].t,stage:G.stage,moved};
      update(0.2); // push well past introT
      return {afterTrigger,frozenSnapshot,afterIntro:{state:G.state,hostPanT:G.en[0].pan?G.en[0].pan.t:null,partnerMerged:!!G.en[1].merged}};
    })()""" % place_pair(x0, y))
    at, fz = r["afterTrigger"], r["frozenSnapshot"]
    check("the trigger frame itself still ran as a normal 'play' tick (one tick of decay, then frozen)", at["state"] == "panintro", r)
    check("nothing moves/decays for the rest of the intro (power/invuln/grease-lifetime/girone unchanged since the trigger frame, player didn't move)",
          fz["state"] == "panintro" and fz["power"] == at["power"] and fz["invuln"] == at["invuln"] and fz["greaseT"] == at["greaseT"] and fz["stage"] == at["stage"] and not fz["moved"], r)
    ai = r["afterIntro"]
    check("after introT: back to 'play', host.pan.t seeded to the full life, partner still merged",
          ai["state"] == "play" and abs(ai["hostPanT"] - 12) < 0.001 and ai["partnerMerged"], r)
    GREASE_clear_stub = p.evaluate("GREASE.clear();true")
    check("no console errors (intro freeze)", not errs, errs)

    # ---------------- merged: ghost count/stage unchanged, partner inert, host speed x1.25 / chase 0.9, restored after split
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      const nBefore=G.en.length;
      G.en[0].chase=0.77; // distinctive original chase to check restoration later
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60); // -> merged
      const host=G.en[0],partner=G.en[1];
      const es=Math.min(5.7,4.3+G.stage*.18)*dfc().spd;
      const partnerBefore={tx:partner.tx,ty:partner.ty,prog:partner.prog};
      for(let i=0;i<30;i++)update(1/60); // half a second of normal chase
      const hostSpeedRatio=host.speed/es;
      const partnerUnchanged=partner.tx===partnerBefore.tx&&partner.ty===partnerBefore.ty&&partner.prog===partnerBefore.prog;
      // partner never collides: put the player exactly on the partner's (frozen) tile
      G.pl.tx=partner.tx;G.pl.ty=partner.ty;G.pl.dir=null;G.pl.prog=0;G.invuln=0;G.st=null;
      update(1/60);
      const partnerNoCollision=G.state!=='dying';
      const chaseWhileMerged=host.chase; // captured before forcing the split below
      // now force the split and check restoration
      host.pan.t=0;update(1/60);
      return {
        nBefore,nAfter:G.en.length,stagesUnchanged:host.stage===3&&partner.stage===3,
        chaseWhileMerged,hostSpeedRatio,partnerUnchanged,partnerNoCollision,
        chaseAfterSplit:host.chase,panAfterSplit:!!host.pan,mergedAfterSplit:!!partner.merged
      };
    })()""" % place_pair(x0, y))
    check("ghost count unchanged by a merge", r["nBefore"] == r["nAfter"], r)
    check("both ghosts keep stage 3 while merged (M1b bonus counts both)", r["stagesUnchanged"], r)
    check("host chase forced to 0.9 while merged", abs(r["chaseWhileMerged"] - 0.9) < 1e-9, r)
    check("host speed x1.25 while merged", abs(r["hostSpeedRatio"] - 1.25) < 0.05, r)
    check("the hidden partner is never updated (position frozen)", r["partnerUnchanged"], r)
    check("the hidden partner never collides with the player", r["partnerNoCollision"], r)
    check("host chase restored to its original value after the split", abs(r["chaseAfterSplit"] - 0.77) < 1e-9, r)
    check("no dangling pan/merged flags right after split", not r["panAfterSplit"] and not r["mergedAfterSplit"], r)
    check("no console errors (merged state)", not errs, errs)

    # ---------------- contact kills at the larger radius; no kill while invulnerable
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60);
      const host=G.en[0];
      G.pl.tx=host.tx;G.pl.ty=host.ty;G.pl.dir=null;G.pl.prog=0;G.invuln=0;G.st=null;
      update(1/60);
      return G.state;
    })()""" % place_pair(x0, y))
    check("contact with the merged host kills the player", r == "dying", r)

    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60);
      const host=G.en[0];
      G.pl.tx=host.tx;G.pl.ty=host.ty;G.pl.dir=null;G.pl.prog=0;G.invuln=5;G.st=null;
      update(1/60);
      return G.state;
    })()""" % place_pair(x0, y))
    check("no kill on contact while invulnerable", r != "dying", r)
    check("no console errors (contact)", not errs, errs)

    # ---------------- no grease drop while merged (host's own grease pauses)
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      GREASE.clear();
      G.en[0].ab.grease={t:0}; // due right now
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60); // -> merged
      update(1/60);
      return GREASE.list.length;
    })()""" % place_pair(x0, y))
    check("grease never drops from a ghost while it's part of a Super Panino merge", r == 0, r)
    check("no console errors (grease pause)", not errs, errs)

    # ---------------- 20 simulated seconds merged: the host is never on a wall tile (no wall-breaking in E5a)
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60);
      const host=G.en[0];host.pan.t=1e9; // stay merged for the whole simulated window
      let bad=[];
      for(let i=0;i<400;i++){ // 400 x 0.05s = 20s
        update(0.05);
        if(wall(host.tx,host.ty)||host.prog<0||host.prog>=1)bad.push({tx:host.tx,ty:host.ty,prog:host.prog});
      }
      return {bad:bad.slice(0,5),badCount:bad.length};
    })()""" % place_pair(x0, y))
    check("a merged Super Panino host never overlaps a wall over a 20s simulated chase (no wall-breaking in E5a)", r["badCount"] == 0, r)
    check("no console errors (20s merged safety)", not errs, errs)

    # ---------------- split after 12s: two ghosts on different non-wall/non-house tiles, stage 3, reMergeCd running
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60);
      const host=G.en[0],partner=G.en[1];
      host.pan.t=0.001;
      update(1/60);
      return {
        panGone:!host.pan,mergedGone:!partner.merged,
        stagesOk:host.stage===3&&partner.stage===3,
        differentTiles:!(host.tx===partner.tx&&host.ty===partner.ty),
        partnerOnWall:wall(partner.tx,partner.ty),partnerInHouse:inHouse(partner.tx,partner.ty),
        hostCd:host.ab.panino.cd,partnerCd:partner.ab.panino.cd
      };
    })()""" % place_pair(x0, y))
    check("split clears pan/merged", r["panGone"] and r["mergedGone"], r)
    check("both ghosts keep stage 3 after split", r["stagesOk"], r)
    check("host and partner end up on different tiles", r["differentTiles"], r)
    check("partner placed on neither a wall nor inside the house", not r["partnerOnWall"] and not r["partnerInHouse"], r)
    check("reMergeCd running on both ghosts after split", r["hostCd"] > 0 and r["partnerCd"] > 0, r)
    check("no console errors (split)", not errs, errs)

    # ---------------- power-up: merged host turns scared, merge persists, life keeps running
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60);
      const host=G.en[0];
      activatePower();
      const scaredRightAway=host.mode==='s',panRightAway=!!host.pan;
      const tBefore=host.pan.t;
      for(let i=0;i<30;i++)update(1/60); // half a second, still scared
      return {scaredRightAway,panRightAway,stillScared:host.mode==='s',stillPan:!!host.pan,ticked:host.pan.t<tBefore};
    })()""" % place_pair(x0, y))
    check("power-up turns the merged host scared without breaking the merge",
          r["scaredRightAway"] and r["panRightAway"] and r["stillScared"] and r["stillPan"], r)
    check("the merge life timer keeps ticking down while scared", r["ticked"], r)
    check("no console errors (power-up)", not errs, errs)

    # ---------------- eaten while scared: +3200 once, both ghosts eaten, no panino left
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60);
      const host=G.en[0],partner=G.en[1];
      activatePower();
      G.grid[host.ty][host.tx]=" "; // clear any pellet on the host's tile so the score delta below is the eat-split award alone
      const scoreBefore=G.score,girPtsBefore=G.girPts||0,chainBefore=G.chain||0;
      G.pl.tx=host.tx;G.pl.ty=host.ty;G.pl.dir=null;G.pl.prog=0;
      update(1/60);
      return {
        scoreDelta:G.score-scoreBefore,girPtsDelta:(G.girPts||0)-girPtsBefore,chainUnchanged:(G.chain||0)===chainBefore,
        hostEaten:host.mode==='g',partnerEaten:partner.mode==='g',
        panGone:!host.pan,mergedGone:!partner.merged,noPaninoLeft:G.en.every(e=>!e.pan)
      };
    })()""" % place_pair(x0, y))
    check("eating the merged host awards exactly +3200 once", r["scoreDelta"] == 3200 and r["girPtsDelta"] == 3200, r)
    check("the flat 3200 award does not advance the normal eat chain", r["chainUnchanged"], r)
    check("both host and partner become eaten (eyes)", r["hostEaten"] and r["partnerEaten"], r)
    check("no panino left after the eaten-split", r["panGone"] and r["mergedGone"] and r["noPaninoLeft"], r)
    check("no console errors (eaten split)", not errs, errs)

    # ---------------- clear on death respawn and girone start; nothing in the quicksave
    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60);
      const wasMerged=!!G.en[0].pan;
      G.state='dying';G.t=0.001;update(0.02); // forced death -> resetActors(true) -> fresh G.en (+ PANINO.clear())
      return {wasMerged,afterDeath:G.en.some(e=>e.pan||e.merged)};
    })()""" % place_pair(x0, y))
    check("a merge was actually active before the forced death", r["wasMerged"], r)
    check("no ghost carries pan/merged across a death respawn", not r["afterDeath"], r)

    r = p.evaluate("""(()=>{
      %s
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60);
      const wasMerged=!!G.en[0].pan;
      cancelAnimationFrame(raf);devJump(1,0); // girone start -> resetActors -> fresh G.en
      return {wasMerged,afterStart:G.en.some(e=>e.pan||e.merged)};
    })()""" % place_pair(x0, y))
    check("a merge was actually active before the girone-start jump", r["wasMerged"], r)
    check("no ghost carries pan/merged across a girone start", not r["afterStart"], r)

    p.evaluate(setup_algidone(3))
    r = p.evaluate("""(()=>{
      %s
      PANINO.startIntro(G.en[0],G.en[1]);G.t=0;update(1/60);
      quicksave();
      const j=JSON.stringify(S.quick);
      return {anyPan:S.quick.en.some(e=>e.pan),anyMerged:S.quick.en.some(e=>e.merged),inJson:j.includes('"pan":{')||j.includes('"merged":true'),stateSaved:S.quick.state};
    })()""" % place_pair(x0, y))
    check("a Super Panino is never saved into the quicksave (split first, same placement rule)",
          not r["anyPan"] and not r["anyMerged"] and not r["inJson"], r)
    check("quicksave never persists the 'panintro' freeze state", r["stateSaved"] != "panintro", r)
    p.evaluate("PANINO.clear();GREASE.clear();MPROJ.clear()")
    check("no console errors (clear points/quicksave)", not errs, errs)

    # ---------------- dev button: absent from the DOM / invisible with dev mode off
    ctx2, p2, errs2 = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p2, 600)
    p2.click("[data-tile=opt]"); p2.wait_for_timeout(300)
    check("player Opzioni has no Sviluppatore tab, so #jgPan never renders", not p2.evaluate("!!document.getElementById('jgPan')"))
    ctx2.close()

    # ---------------- dev button: through a real click, merges the first two eligible ghosts right away
    geo2 = p.evaluate(setup_algidone(3))
    y2, x02 = geo2["openRow"]["y"], geo2["openRow"]["x0"]
    p.evaluate("""(()=>{
      const e0=G.en[0],e1=G.en[1];
      e0.tx=%d;e0.ty=%d;e0.dir=1;e0.prog=0;e0.stage=3;e0.mode='n';e0.wait=0;e0.merged=false;e0.pan=null;
      e1.tx=%d;e1.ty=%d;e1.dir=1;e1.prog=0;e1.stage=3;e1.mode='n';e1.wait=0;e1.merged=false;e1.pan=null;
      G.anim=0;G.state='play'; // graceStart/range/reMergeCd are all irrelevant to the forced dev merge
      go('menu');
    })()""" % (x02, y2, x02 + 5, y2))
    dev_click(p, "#jgPan")
    r = p.evaluate("(()=>{return {state:G.state,pan0:!!G.en[0].pan,merged1:!!G.en[1].merged};})()")
    check("«Forza Super Panino» (real click) merges two eligible ghosts immediately, ignoring range/grace/cooldown",
          r["state"] == "panintro" and r["pan0"] and r["merged1"], r)
    check("no console errors (dev button)", not errs, errs)

    # toast fallback when fewer than 2 eligible ghosts exist
    p.evaluate("""(()=>{
      go('menu');
    })()""")
    r = p.evaluate("""(()=>{
      cancelAnimationFrame(raf);
      S.p.char='algidone';E1_STAGE_OV=1;devJump(1,0); // stage 1 -> nobody eligible
      TOAST.cur=null;TOAST.q=[]; // clear devJump's own toast so forceMerge's shows immediately (queue of one)
      PANINO.forceMerge();
      return document.querySelector('#toasts')?.textContent||'';
    })()""")
    check("forceMerge() toasts when fewer than 2 eligible stage-3 attrezzi exist", "attrezzi stadio 3" in r, r)

    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
