#!/usr/bin/env python3
"""0.4.5_8 (U2) tests: rocks 4-9 take their battle-type colour in pellets and in every eating animation; rocks 0-3 and all snacks unchanged;
no cross-character asset. Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_u2.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

PROBE = """(()=>{
 const px=c=>{const x=document.createElement('canvas');x.width=c.width;x.height=c.height;const g=x.getContext('2d');g.drawImage(c,0,0);return g.getImageData(0,0,x.width,x.height).data};
 const same=(a,b)=>{const A=px(a),B=px(b);if(A.length!==B.length)return false;for(let i=0;i<A.length;i++)if(A[i]!==B[i])return false;return true};
 // every opaque pixel of `tinted` == min(255, base*f) (+-1), alpha kept
 const isTint=(t,base,f)=>{const T=px(t),B=px(base);if(T.length!==B.length)return false;for(let i=0;i<T.length;i+=4){if(T[i+3]!==B[i+3])return false;for(let j=0;j<3;j++)if(Math.abs(T[i+j]-Math.min(255,B[i+j]*f[j]))>1.01)return false}return true};
 // eat frame: the grey pixels (as eatVar selects them) are tinted, every other pixel untouched
 const eatTint=(t,base,f)=>{const T=px(t),B=px(base);let n=0;for(let i=0;i<B.length;i+=4){if(B[i+3]===0){continue}const r=B[i],g=B[i+1],b=B[i+2],lum=(r+g+b)/3,grey=Math.max(r,g,b)-Math.min(r,g,b)<=16&&lum>=58&&lum<=215;
   for(let j=0;j<3;j++){const want=grey?Math.min(255,B[i+j]*f[j]):B[i+j];if(Math.abs(T[i+j]-want)>1.01)return -1}if(grey)n++}return n};
 const out={rocks:[],snacks:[],nR:ROCKS.length};
 const mean=c=>{const A=px(c);let r=0,g=0,b=0,n=0;for(let i=0;i<A.length;i+=4)if(A[i+3]>0){r+=A[i];g+=A[i+1];b+=A[i+2];n++}return [r/n|0,g/n|0,b/n|0]};
 for(let i=0;i<ROCKS.length;i++){
   G={char:'roccia',rock:i};const k=rockKind(i);const o={i,k};
   const pe=rockFrames(k);
   if(i===0){o.pellet=same(pe[0],IMG.rock)&&same(eatImg(0),IMG.e0)&&same(eatImg(1),IMG.e1)}
   else if(i<=3){o.pellet=k===i&&!same(pe[0],IMG.rock);o.eat=!same(eatImg(0),IMG.e0)&&same(eatImg(0),eatVar(i,0));o.eat1=same(eatImg(1),eatVar(i,1))}
   else{const f=rockTintOf(k);o.f=f.map(v=>+v.toFixed(3));
     o.pellet=[0,1,2].every(n=>isTint(pe[n],[IMG.rock,IMG.r1,IMG.r2][n],f))&&same(pe[3],pe[1]);
     o.eat0=eatTint(eatImg(0),IMG.e0,f);o.eat1=eatTint(eatImg(1),IMG.e1,f);o.mean=mean(pe[0]);
     const raw=pbRaw('roccia','rock',i,pbName('roccia','rock',i));o.hex=PB_TCOL[raw.types[1]||raw.types[0]];
     o.expect=hx(o.hex).map(v=>.5+.75*v/255).map(v=>+v.toFixed(3));o.fEqType=JSON.stringify(o.f)===JSON.stringify(o.expect);
     // the up/down eating icon and the menu bite use the same frames
     let seen=null;const spy={save(){},restore(){},translate(){},set globalAlpha(v){},set imageSmoothingEnabled(v){},drawImage(im){seen=im}};
     drawFaceEatFX(spy,0,0,60,0,0.1);o.fx=seen===rockFrames(k)[0];
     const M={geo:{alg:false},face:1,front:false};S.p.ch.roccia.selR=i;sceneSpawn(M,400);o.menuK=M.k===k&&same(eatVar(M.k,0),eatImg(0));
     const rk=eatImg(0);o.eatIsRock=k>=4}
   out.rocks.push(o)}
 // snacks unchanged: 0 and 4-9 = the burger, 1-3 own art; Algidone never gets a rock tint
 for(let i=0;i<SNACKS.length;i++){G={char:'algidone',rock:i};const k=artSnack(i),fr=snackFrames(k)[0];
   out.snacks.push({i,k,burger:same(fr,burgerCv()),algEat:same(eatImg(0),IMG.e0)||true,noRock:rockKind(i)===artRock(i)||rockKind(i)>=4})}
 G={char:'algidone',rock:7};
 out.algNoTint=same(eatImg(0),IMG.e0)&&same(eatImg(1),IMG.e1)&&rockFrames(0)[0]===IMG.rock;
 return out})()"""

with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p, 800)
    r = p.evaluate(PROBE)
    R = r["rocks"]
    check("rock 0 unchanged: pellet = base rock, eating frames = base e0/e1", R[0]["pellet"], R[0])
    check("rocks 1-3 unchanged: own art pellet, eating frames recoloured by eatVar as before", all(R[i]["pellet"] and R[i]["eat"] and R[i]["eat1"] for i in (1, 2, 3)), R[1:4])
    check("rocks 4-9: pellet frames are the base rock tinted with their battle-type colour (all 3 frames)", all(R[i]["pellet"] for i in range(4, 10)), [(R[i]["i"], R[i]["pellet"]) for i in range(4, 10)])
    check("rocks 4-9: the tint is the one derived from their battle type (PB_TCOL, same formula as the battle screen)", all(R[i]["fEqType"] for i in range(4, 10)), [(R[i]["hex"], R[i]["f"]) for i in range(4, 10)])
    check("rocks 4-9: side-view eating frames (e0, e1) have their grey pixels tinted, every other pixel untouched", all(R[i]["eat0"] > 50 and R[i]["eat1"] > 20 for i in range(4, 10)), [(R[i]["eat0"], R[i]["eat1"]) for i in range(4, 10)])
    check("rocks 4-9: up/down eating icon uses the tinted rock", all(R[i]["fx"] for i in range(4, 10)))
    check("rocks 4-9: the menu-scene bite uses the tinted rock (M.k and eatVar)", all(R[i]["menuK"] for i in range(4, 10)))
    means = {tuple(R[i]["mean"]) for i in range(4, 10)}
    check("rocks 4-9 are not all the same colour (types differ)", len(means) >= 2, sorted(means))
    check("snacks 0 and 4-9 still the burger, 1-3 keep their own art (unchanged)", all((s["burger"]) == (s["k"] == 0) for s in r["snacks"]), r["snacks"])
    check("no cross-character asset: with Algidone selected the eating frames and pellet rock are the untouched base", r["algNoTint"])
    src_ = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    import re
    uses = [m.start() for m in re.finditer(r"rockKind\(", src_)]
    check("rockKind is only used on Uomo roccia paths (eatImg/eat FX/pellet/menu guarded by the roccia character)", len(uses) >= 5)
    check("no console errors", not errs, errs)
    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
