#!/usr/bin/env python3
"""0.4.5_13 (M1a) tests: map classes S/M/L (grid width), the GIRONI girone schedule (gironeSpec), 3/4/5 ghosts,
level-10 map lock removed (mapsUnlocked deleted, g4 achievement text). Reuses the harness of test_f2b.py.
Run: python tools/fbstub/test_m1a.py"""
import json, os, sys
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


GIRONI_18 = {
    1: {"cls": "S", "ghosts": [1, 1, 1]},
    2: {"cls": "S", "ghosts": [1, 1, 2]},
    3: {"cls": "M", "ghosts": [1, 1, 1, 1]},
    4: {"cls": "M", "ghosts": [1, 1, 2, 2]},
    5: {"cls": "M", "ghosts": [1, 1, 2, 2]},
    6: {"cls": "L", "ghosts": [1, 1, 1, 2, 2]},
    7: {"cls": "L", "ghosts": [1, 1, 2, 2, 3]},
    8: {"cls": "L", "ghosts": [1, 1, 1, 3, 3]},
}
CLASS_N = {"S": 3, "M": 4, "L": 5}


def s3count(n, g):
    return min(n, 2 + max(0, (g - 8) // 2))


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    # ---------------- gironeSpec: exact table for gironi 1-8
    for g in range(1, 9):
        r = p.evaluate("gironeSpec(%d)" % g)
        check(f"gironeSpec({g}) matches the §10.2 schedule", r == GIRONI_18[g], r)
    # ---------------- gironeSpec: g9+ stage-3 formula (checked via stagesForClass directly, class-independent of the random draw)
    for g in (9, 10, 11, 12, 13, 14):
        for cls, n in CLASS_N.items():
            arr = p.evaluate("stagesForClass('%s',%d)" % (cls, g))
            want3 = s3count(n, g)
            ok = len(arr) == n and arr.count(3) == want3 and arr.count(2) == n - want3 and all(v in (2, 3) for v in arr)
            check(f"stagesForClass({cls},{g}): {n} ghosts, every one >=2, {want3} at stage 3", ok, arr)
    # ---------------- g9+ class split ~ 20/40/40
    tally = p.evaluate("(()=>{const t={S:0,M:0,L:0};for(let i=0;i<600;i++)t[gironeSpec(9).cls]++;return t})()")
    tot = sum(tally.values())
    frac = {k: v / tot for k, v in tally.items()}
    check("g9+ class split is roughly S 20% / M 40% / L 40%", abs(frac["S"] - .2) < .08 and abs(frac["M"] - .4) < .08 and abs(frac["L"] - .4) < .08, frac)

    # ---------------- real gironi via the dev girone-jump: ghost count per class
    dev_click(p, "#jg4")
    r = p.evaluate("({cls:mapClassOf(G.mapi),n:G.en.length,stages:G.en.map(e=>e.stage)})")
    check("dev girone-jump: girone 4 -> class M, 4 ghosts", r["cls"] == "M" and r["n"] == 4, r)
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    dev_click(p, "#jg7")
    r = p.evaluate("({cls:mapClassOf(G.mapi),n:G.en.length,stages:G.en.map(e=>e.stage)})")
    check("dev girone-jump: girone 7 -> class L, 5 ghosts", r["cls"] == "L" and r["n"] == 5, r)
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    # the map picker ("Salta al girone" -> select an S map -> Vai) forces mi directly: an S map still means 3 ghosts
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector(\"details.acc:has(#jmg)\").open"):
        p.click("details.acc:has(#jmg) > summary"); p.wait_for_timeout(250)
    p.select_option("#jmsel", "0"); p.click("#jmg"); p.wait_for_timeout(600)
    r = p.evaluate("({cls:mapClassOf(G.mapi),n:G.en.length,stages:G.en.map(e=>e.stage)})")
    check("dev map picker on an S map -> class S, 3 ghosts", r["cls"] == "S" and r["n"] == 3, r)
    check("no console errors (dev girone-jump)", not errs, errs)

    # ---------------- pickMap: no immediate repeat within a class, over 200 picks, for each class
    r = p.evaluate("""(()=>{
      const out={};
      for(const [cls,stageForCls] of [["S",1],["M",3],["L",6]]){
        G={lastMi:{S:null,M:null,L:null}};const seq=[];
        for(let i=0;i<200;i++)seq.push(pickMap(stageForCls));
        let repeat=false;for(let i=1;i<seq.length;i++)if(seq[i]===seq[i-1])repeat=true;
        out[cls]={repeat,allInClass:seq.every(mi=>mapClassOf(mi)===cls),poolSize:new Set(seq).size};
      }
      return out})()""")
    for cls in ("S", "M", "L"):
        o = r[cls]
        check(f"pickMap ({cls}): 200 picks, no immediate repeat, every pick in class {cls}", not o["repeat"] and o["allInClass"], o)
    check("pickMap (S, 200 picks): visits more than one of the 5 S maps", r["S"]["poolSize"] > 1, r["S"])

    # ---------------- level-10 lock removed: a save below level 10, no g4 achievement, still gets M/L maps
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    r = p.evaluate("""(()=>{
      delete S.ach.done.g4;S.p.ch.roccia.lvl=5;S.sim=false;
      cancelAnimationFrame(raf);
      startGame(false,{stage:4});const m=mapClassOf(G.mapi),n4=G.en.length;
      cancelAnimationFrame(raf);
      startGame(false,{stage:6});const l=mapClassOf(G.mapi),n6=G.en.length;
      return {lvl:S.p.ch.roccia.lvl,g4:!!(S.ach.done&&S.ach.done.g4),m,n4,l,n6}
    })()""")
    check("level < 10, no g4 achievement: girone 4 still gives an M map (4 ghosts)", r["lvl"] < 10 and not r["g4"] and r["m"] == "M" and r["n4"] == 4, r)
    check("level < 10, no g4 achievement: girone 6 still gives an L map (5 ghosts)", r["l"] == "L" and r["n6"] == 5, r)
    check("no console errors (level-10 lock removed)", not errs, errs)

    # ---------------- g4 achievement text: no mention of unlocking maps
    d = p.evaluate("ACH.find(a=>a.id==='g4').d")
    check("achievement g4 description no longer mentions unlocking maps", "mapp" not in d.lower() and "Raggiungi il livello 10" in d, d)

    # ---------------- old quicksave (pre-M1a shape: no G.lastMi, ghosts with no .stage) resumes cleanly
    p.evaluate("""(()=>{
      setDims(6);const g=freshGrid(6),st=MET.ghosts,ch=[.52,.38,.24,.41],tn=['#e5484d','#3ec7e0','#ff9a3c','#ff7ac6'];
      const en=st.map((s,i)=>({tx:s[0],ty:s[1],dir:null,prog:0,wait:(i*2.2+1.2)*.52,chase:ch[i],tint:tn[i],mode:'n',gt:0}));
      S.quick={game:'maze',stage:4,score:800,lives:3,hard:false,grid:g,parts:[],diff:'medium',char:'roccia',mapi:6,plane:0,rock:0,
        pl:{tx:MET.start[0],ty:MET.start[1],dir:null,next:null,prog:0,lastH:1},en,power:0,pu:null,since:0,open:8,chain:0,still:false,
        state:'ready',t:1.6,invuln:0,anim:0,st:null,fx:[],shake:0,burn:0,inW:false,cam:null};
      persist();
    })()""")
    p.evaluate("cancelAnimationFrame(raf);G=null;go('menu')"); p.wait_for_timeout(300)
    p.click("[data-tile=cur]"); p.wait_for_function("G&&(G.state==='ready'||G.state==='play')", timeout=5000); p.wait_for_timeout(300)
    r = p.evaluate("({lastMi:G.lastMi,stages:G.en.map(e=>e.stage),mapi:G.mapi,cls:mapClassOf(G.mapi)})")
    check("old quicksave (no lastMi) resumes: lastMi migrated with the current map remembered for its class",
          r["lastMi"] is not None and r["lastMi"][r["cls"]] == r["mapi"], r)
    check("old quicksave (ghosts with no .stage) resumes: every ghost gets a default stage", all(isinstance(s, int) for s in r["stages"]), r)
    check("no console errors (old quicksave)", not errs, errs)

    # ---------------- (0.4.5_16, fix: 5th ghost on large maps) every map of each class x both characters:
    # G count = drawn count (spy on the enemy draw calls) = the class count, and every ghost leaves the house
    DRAWN = """()=>{
      let n=0;const o1=drawPlane,o2=drawGym,o3=drawGymArt;
      drawPlane=function(...a){n++;return o1.apply(this,a)};
      drawGym=function(...a){n++;return o2.apply(this,a)};
      drawGymArt=function(...a){n++;return o3.apply(this,a)};
      draw();
      drawPlane=o1;drawGym=o2;drawGymArt=o3;
      return n;
    }"""
    ALL_MAPS = {"S": [0, 1, 2, 3, 4], "M": [5, 6, 7, 10, 12, 13], "L": [8, 9, 11, 14]}
    for ck in ("roccia", "algidone"):
        for cls, maps in ALL_MAPS.items():
            for mi in maps:
                p.evaluate("cancelAnimationFrame(raf);S.p.char='%s';devJump(1,%d);G.state='play';G.t=0;G.invuln=99999" % (ck, mi))
                r = p.evaluate("({enLen:G.en.length,drawn:(%s)()})" % DRAWN)
                want = CLASS_N[cls]
                check(f"{ck} mi={mi} ({cls}): G.en.length={want} and the same number are drawn", r["enLen"] == want and r["drawn"] == want, r)
                p.evaluate("for(let i=0;i<340;i++)update(0.05)")  # ~17s, invuln forced so a death never resets ghost positions mid-check
                left = p.evaluate("G.en.map(e=>e.dir!==null)")
                check(f"{ck} mi={mi} ({cls}): every ghost leaves the house within ~17s", all(left), {"left": left, "waits": p.evaluate("G.en.map(e=>+e.wait.toFixed(2))")})
    check("no console errors (per-map ghost count/draw/release)", not errs, errs)

    # ---------------- girone 8 via all three paths: class L, 5 ghosts
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    # path (a): #jgN=8 + #jgGo (real UI)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(#jgGo)').open"):
        p.click("details.acc:has(#jgGo) > summary"); p.wait_for_timeout(250)
    p.fill("#jgN", "8"); p.click("#jgGo"); p.wait_for_timeout(500)
    ra = p.evaluate("({cls:mapClassOf(G.mapi),n:G.en.length})")
    check("girone 8 path (a) #jgN+#jgGo: class L, 5 ghosts", ra["cls"] == "L" and ra["n"] == 5, ra)
    # path (b): #jg7, then clear the girone to reach 8
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    dev_click(p, "#jg7")
    rb = p.evaluate("""(()=>{
      G.state='play';G.t=0;
      G.grid=G.grid.map(row=>row.map(ch=>ch==='.'?' ':ch));
      G.grid[G.pl.ty][G.pl.tx]='.';G.pl.prog=0;G.pl.dir=null;G.pl.next=null;
      update(1/60);update(1.7);
      return {stage:G.stage,cls:mapClassOf(G.mapi),n:G.en.length};
    })()""")
    check("girone 8 path (b) #jg7 then clear: class L, 5 ghosts", rb["stage"] == 8 and rb["cls"] == "L" and rb["n"] == 5, rb)
    # path (c): a normal run, jump to girone 1 (not a dev-flagged jump: G.dev=false) then clear up to girone 8
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    p.evaluate("cancelAnimationFrame(raf);devJump(1);G.dev=false")
    for _ in range(7):
        rc = p.evaluate("""(()=>{
          G.state='play';G.t=0;
          G.grid=G.grid.map(row=>row.map(ch=>ch==='.'?' ':ch));
          G.grid[G.pl.ty][G.pl.tx]='.';G.pl.prog=0;G.pl.dir=null;G.pl.next=null;
          update(1/60);update(1.7);
          return {stage:G.stage,cls:mapClassOf(G.mapi),n:G.en.length};
        })()""")
    check("girone 8 path (c) a normal run advanced girone by girone: class L, 5 ghosts", rc["stage"] == 8 and rc["cls"] == "L" and rc["n"] == 5, rc)
    check("no console errors (girone 8, three paths)", not errs, errs)

    # ---------------- girone 9: 30 jumps, class always matches the actual ghost count (no map/spec mismatch)
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    tally9 = p.evaluate("""(()=>{
      const t={S:0,M:0,L:0};let bad=0;
      for(let i=0;i<30;i++){cancelAnimationFrame(raf);devJump(9);const cls=mapClassOf(G.mapi);if(G.en.length!==({S:3,M:4,L:5})[cls])bad++;t[cls]++}
      return {t,bad};
    })()""")
    check("girone 9, 30 jumps: ghost count always matches the picked map's class (no mismatch)", tally9["bad"] == 0, tally9)

    # ---------------- dev readout: present for a dev, absent for a player
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    p.evaluate("cancelAnimationFrame(raf);devJump(8)"); p.wait_for_timeout(300)
    readout = p.evaluate("(document.getElementById('jgro')||{}).textContent")
    check("dev readout shows girone/class/count/stages", readout == "G8 · L · 5 · st 1,1,1,3,3", readout)
    check("no console errors (readout)", not errs, errs)
    ctx.close()

    ctx2, p2, errs2 = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p2, 600)
    p2.click("[data-tile=new]"); p2.wait_for_timeout(400)
    if p2.evaluate("!!document.querySelector('[data-rg]')"):
        p2.click("[data-rg=maze]")
    p2.wait_for_function("G&&G.state==='play'", timeout=8000)
    check("no dev readout for a player run", not p2.evaluate("!!document.getElementById('jgro')"))
    check("no console errors (player, no readout)", not errs2, errs2)
    ctx2.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
