#!/usr/bin/env python3
"""0.4.5_18 (E1a) tests: ghost stage ability framework skeleton (STAGE_ABIL/STAGE_MARK data table,
ABIL registry of NO-OP stub modules, the reset/onSpawn/update/draw dispatcher, the dev-only "Stadio"
override). No gameplay change except the stage-2/3 marker outline. Reuses the harness of test_f2b.py,
same pattern as test_m1a.py/test_b2.py.
Run: python tools/fbstub/test_e1a.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only


def dev_click(p, sel):
    """Opzioni -> Sviluppatore -> the accordion holding sel -> click (real clicks)"""
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(%s)').open" % sel.replace("'", "\\'")):
        p.click("details.acc:has(%s) > summary" % sel); p.wait_for_timeout(250)
    p.click(sel); p.wait_for_timeout(600)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    # ---------------- table shape: both families, stages 2/3, every ability id has a full 5-part module
    r = p.evaluate("""(()=>{
      const ids=new Set();
      for(const fam of Object.keys(STAGE_ABIL))for(const st of [2,3])for(const id of STAGE_ABIL[fam][st]||[])ids.add(id);
      const shapeOk=[...ids].every(id=>ABIL[id]&&ABIL[id].id===id&&typeof ABIL[id].onSpawn==='function'&&typeof ABIL[id].update==='function'&&typeof ABIL[id].draw==='function'&&typeof ABIL[id].reset==='function');
      return {famOk:!!STAGE_ABIL.aerei&&!!STAGE_ABIL.attrezzi,stagesOk:[2,3].every(st=>!!STAGE_ABIL.aerei[st]&&!!STAGE_ABIL.attrezzi[st]),ids:[...ids].sort(),shapeOk,
        aerei2:STAGE_ABIL.aerei[2],aerei3:STAGE_ABIL.aerei[3],attr2:STAGE_ABIL.attrezzi[2],attr3:STAGE_ABIL.attrezzi[3]};
    })()""")
    check("STAGE_ABIL has both families (aerei/attrezzi)", r["famOk"], r)
    check("STAGE_ABIL has stages 2 and 3 for both families", r["stagesOk"], r)
    check("aerei stage2=['sprint'], stage3=['sprint','shoot']", r["aerei2"] == ["sprint"] and r["aerei3"] == ["sprint", "shoot"], r)
    check("attrezzi stage2=['grease'], stage3=['grease','panino'] (stage-3 keeps grease, owner decision)", r["attr2"] == ["grease"] and r["attr3"] == ["grease", "panino"], r)
    check("every referenced ability id (sprint/shoot/grease/panino) has a registered {id,onSpawn,update,draw,reset} module",
          r["shapeOk"] and r["ids"] == ["grease", "panino", "shoot", "sprint"], r)

    # ---------------- family matches the character (Uomo roccia -> aerei, Algidone -> attrezzi)
    r = p.evaluate("(()=>{S.p.char='roccia';const r=E1Family();S.p.char='algidone';const a=E1Family();S.p.char='roccia';return {r,a}})()")
    check("Uomo roccia -> family 'aerei'", r["r"] == "aerei", r)
    check("Algidone -> family 'attrezzi'", r["a"] == "attrezzi", r)

    # dev girone-jump to an L map (5 ghosts, MET/inHouse available) as the ground for the rest of the checks
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(#jgGo)').open"):
        p.click("details.acc:has(#jgGo) > summary"); p.wait_for_timeout(250)
    p.fill("#jgN", "8"); p.click("#jgGo"); p.wait_for_timeout(300)
    check("on an L map for the rest of this suite (5 ghosts)", p.evaluate("G.en.length") == 5, p.evaluate("G.en.length"))

    # ---------------- dispatcher: update only for stage>=2, never while scared/eaten/in house/waiting
    calls = p.evaluate("""(()=>{
      S.p.char='roccia';G.char='roccia'; // family=aerei -> stage>=2 abilities include 'sprint'
      const orig=ABIL.sprint.update,calls=[];
      ABIL.sprint.update=(g)=>{calls.push(g._k)};
      const mk=(over)=>Object.assign({tx:MET.house[2]+3,ty:MET.house[1],stage:2,mode:'n',wait:0,ab:{}},over);
      const cases={
        stage1:mk({stage:1}),
        stage2:mk({stage:2}),
        stage3:mk({stage:3}),
        scared:mk({stage:2,mode:'s'}),
        eaten:mk({stage:2,mode:'g'}),
        waiting:mk({stage:2,wait:1}),
        inhouse:mk({stage:2,tx:MET.house[0],ty:MET.house[1]}),
      };
      for(const k in cases){cases[k]._k=k;E1UpdateGhost(cases[k],0.016)}
      ABIL.sprint.update=orig;
      return calls;
    })()""")
    check("dispatcher calls update only for stage2/stage3 ghosts (never stage1/scared/eaten/waiting/in-house)",
          sorted(calls) == ["stage2", "stage3"], calls)

    # ---------------- reset + onSpawn run on girone start and after a forced death
    r = p.evaluate("""(()=>{
      E1_STAGE_OV=2; // force every ghost to stage 2 (family=aerei -> only 'sprint' is active) for a deterministic count
      const calls=[],origs={};
      for(const id of ['sprint','shoot','grease','panino']){
        origs[id]={reset:ABIL[id].reset,onSpawn:ABIL[id].onSpawn};
        ABIL[id].reset=(g)=>{calls.push(id+':reset');return origs[id].reset(g)};
        ABIL[id].onSpawn=(g)=>{calls.push(id+':onSpawn');return origs[id].onSpawn(g)};
      }
      cancelAnimationFrame(raf);S.p.char='roccia';devJump(1,8);
      const afterStart=calls.slice();calls.length=0;
      G.state='dying';G.t=0.001;update(0.02); // forced death -> resetActors(true)
      const afterDeath=calls.slice();
      for(const id of ['sprint','shoot','grease','panino']){ABIL[id].reset=origs[id].reset;ABIL[id].onSpawn=origs[id].onSpawn}
      E1_STAGE_OV=null;
      return {afterStart,afterDeath,enLen:G.en.length};
    })()""")
    check("girone start: reset+onSpawn run once per ghost (5 ghosts x reset+onSpawn = 10 calls, all 'sprint')",
          r["afterStart"] == ["sprint:reset", "sprint:onSpawn"] * 5, r["afterStart"])
    check("forced death respawn: reset+onSpawn run again for the fresh ghost set (same 10 calls)",
          r["afterDeath"] == ["sprint:reset", "sprint:onSpawn"] * 5, r["afterDeath"])
    check("ghost count unchanged by the dispatcher (still 5 on the L map)", r["enLen"] == 5, r["enLen"])
    check("no console errors (dispatcher reset/onSpawn)", not errs, errs)

    # ---------------- marker drawn only for stage>=2 and not while scared/eaten
    seen = p.evaluate("""(()=>{
      const orig=E1DrawMarker,seen=[];
      E1DrawMarker=(ctx,X,Y,c,stage)=>{seen.push(stage)};
      const st=[1,2,3,2,3],md=['n','n','n','s','g'];
      G.en.forEach((e,i)=>{e.stage=st[i];e.mode=md[i];e.dir=1;e.prog=0;e.wait=0;e.tx=MET.house[2]+2;e.ty=MET.house[1]});
      draw();
      E1DrawMarker=orig;
      return seen;
    })()""")
    check("marker drawn only for stage>=2, not scared, not eaten (stage1/scared/eaten skipped)", seen == [2, 3], seen)

    # ---------------- Stadio override: works via the real UI, shown in the readout, absent from the DOM for players
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(#jgGo)').open"):
        p.click("details.acc:has(#jgGo) > summary"); p.wait_for_timeout(250)
    p.select_option("#jgStOv", "3")
    p.fill("#jgN", "1"); p.click("#jgGo"); p.wait_for_timeout(300)
    r = p.evaluate("({stages:G.en.map(e=>e.stage),readout:(document.getElementById('jgro')||{}).textContent})")
    check("Stadio=3 override: every ghost forced to stage 3 from the next girone start", all(s == 3 for s in r["stages"]), r)
    check("readout shows the active override", "stadio 3" in r["readout"], r["readout"])
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(#jgGo)').open"):
        p.click("details.acc:has(#jgGo) > summary"); p.wait_for_timeout(250)
    p.select_option("#jgStOv", "")  # back to auto
    p.wait_for_timeout(150)
    check("Stadio back to auto clears the override", p.evaluate("E1_STAGE_OV") is None, p.evaluate("E1_STAGE_OV"))
    check("no console errors (Stadio override)", not errs, errs)

    # ---------------- no quicksave field for the override
    r = p.evaluate("""(()=>{
      E1_STAGE_OV=2;quicksave();
      const j=JSON.stringify(S.quick);
      const r={hasKey:'E1_STAGE_OV' in S.quick,inJson:j.includes('E1_STAGE_OV')};
      E1_STAGE_OV=null;
      return r;
    })()""")
    check("quicksave never carries the Stadio override", not r["hasKey"] and not r["inJson"], r)

    ctx.close()

    # ---------------- absent from the DOM for a player (no dev tab at all)
    ctx2, p2, errs2 = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p2, 600)
    p2.click("[data-tile=opt]"); p2.wait_for_timeout(300)
    check("player Opzioni has no Sviluppatore tab, so #jgStOv never renders", not p2.evaluate("!!document.getElementById('jgStOv')"))
    check("no console errors (player, no dev tools)", not errs2, errs2)
    ctx2.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
