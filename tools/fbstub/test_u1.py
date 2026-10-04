#!/usr/bin/env python3
"""0.4.5_6 (U1) tests: «Mr. Stone» title, Giochi locked/unlocked cards, El Gamblador picture (card + unlock popup), forced Ferma encounter at girone 8.
Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_u1.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

INK = """(sel)=>{const c=document.querySelector(sel);if(!c)return -1;const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i]>0)n++;return n}"""
CARDS = "[...document.querySelectorAll('.grid .card')].map(c=>({name:c.querySelector('.nm').innerText,st:(c.querySelector('.st')||{}).innerText||'',locked:c.classList.contains('locked')}))"


REFJS = """(()=>{const r=document.createElement('canvas');r.width=r.height=96;gambDraw(r.getContext('2d'));return r.toDataURL()})()"""
PRESJS = """new Promise(res=>{const im=new Image();im.onload=()=>{const r=document.createElement('canvas');r.width=r.height=96;const x=r.getContext('2d'),q=Math.min(92/im.naturalWidth,92/im.naturalHeight);x.imageSmoothingEnabled=true;x.drawImage(im,48-im.naturalWidth*q/2,94-im.naturalHeight*q,im.naturalWidth*q,im.naturalHeight*q);res(r.toDataURL())};im.src=BJSPR.pres})"""


def games_tab(p):
    p.evaluate("tab='games';go('wish')"); p.wait_for_timeout(700)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    # ------------- title
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    p.wait_for_timeout(500)
    check("page <title> is «Mr. Stone»", p.evaluate("document.title") == "Mr. Stone")
    check("splash: title and popup say «Mr. Stone»", p.evaluate("document.querySelector('#root h1').innerText") == "Mr. Stone" and p.evaluate("document.querySelector('#modal h3').innerText") == "Mr. Stone")
    check("<noscript> text says «Mr. Stone»", "Mr. Stone" in p.evaluate("document.querySelector('noscript').textContent"))
    p.evaluate("window.dispatchEvent(new ErrorEvent('error',{message:'prova'}))"); p.wait_for_timeout(200)
    check("error overlay says «Errore Mr. Stone»", "Errore Mr. Stone" in p.evaluate("(document.getElementById('errbox')||{}).textContent||''"))
    p.click("#rsi"); p.wait_for_timeout(600)
    check("menu <h1> is «Mr. Stone»", p.evaluate("document.querySelector('.brand h1').innerText") == "Mr. Stone")
    seen = []
    for scr in ("menu", "opt", "wish", "ach", "road"):
        p.evaluate("go('%s')" % scr); p.wait_for_timeout(350); seen.append("Mangiasassi" in p.evaluate("document.body.innerText"))
    check("no player-visible «Mangiasassi» on menu / Opzioni / Negozio / Obiettivi / Percorso", not any(seen), seen)
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    check("index.html contains no «Mangiasassi» at all (repo/URL/keys/identifiers never used the word)", "Mangiasassi" not in html)
    check("no console errors (title)", not errs, errs); ctx.close()

    # ------------- Giochi cards, locked
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p, 600); games_tab(p)
    cs = p.evaluate(CARDS)
    check("Giochi (nothing unlocked): G2/G3/G4 are «???» + «non sbloccato», locked", all(cs[i]["name"] == "???" and cs[i]["st"] == "non sbloccato" and cs[i]["locked"] for i in (1, 2, 3)), cs)
    check("Giochi: G5/G6 (don't exist yet) keep «???» + «In arrivo»", all(cs[i]["name"] == "???" and cs[i]["st"] == "In arrivo" for i in (4, 5)), cs)
    check("Giochi: Mangiaroccia unchanged («Disponibile»)", cs[0]["st"] == "Disponibile" and "Mangiaroccia" in cs[0]["name"], cs[0])
    check("Giochi: the header «Altri giochi in arrivo» stays", "Altri giochi in arrivo" in p.evaluate("document.body.innerText"))
    locked_ink = p.evaluate("(%s)('.grid .card:nth-child(2) canvas')" % INK)
    check("no console errors (locked cards)", not errs, errs); ctx.close()

    # ------------- unlocked + El Gamblador picture
    sv = save(); sv["p"].update({"gam": {"visits": 1, "seen": True, "won": 0}, "pr": {"visits": 1, "seen": True}, "fa": {"enc": 1, "seen": True, "f1": False}})
    ctx, p, errs = page(b, site="stable", local=norm(b, sv), toggle=False, dev=False)
    settle(p, 600); games_tab(p); p.wait_for_timeout(600)
    cs = p.evaluate(CARDS)
    check("Giochi (all unlocked): real names, «Disponibile», not locked", [c["name"] for c in cs[:4]] != ["???"] * 4 and all(cs[i]["st"] in ("Disponibile", "") or "Gioca" in cs[i]["st"] or cs[i]["st"] == "" for i in (0, 1, 2)) and not any(cs[i]["locked"] for i in (0, 1, 2, 3)), cs)
    check("Giochi: El Gamblador's card shows his name", "Gamblador" in cs[1]["name"], cs[1])
    ink = p.evaluate("(%s)('.grid .card:nth-child(2) canvas')" % INK)
    check("Giochi: El Gamblador's card is drawn with his presentation picture (much more ink than the two playing cards it used to show)", ink > 3000, ink)
    ref = p.evaluate(REFJS); pres = p.evaluate(PRESJS)
    card = p.evaluate("document.querySelector('.grid .card:nth-child(2) canvas').toDataURL()")
    check("Giochi card draws the dealer's idle frame from the blackjack sprites (not BJSPR.pres)", card == ref and card != pres and len(ref) > 2500)
    p.evaluate("tab='player';go('wish')"); p.wait_for_timeout(700)
    neg = p.evaluate("(()=>{const c=document.querySelector('canvas[data-draw^=\"gamb\"]');return c&&c.toDataURL()})()")
    check("Negozio › Giocatore card draws the same dealer frame (not BJSPR.pres)", neg == ref and neg != pres, bool(neg))
    check("the crop is the idle_0 frame of BJSPR (108x84 crop of a 108x113 frame)", p.evaluate("[gambImg().width,gambImg().height,_gpi.src===BJSPR.idle[0]]") == [108, 84, True])
    check("no console errors (unlocked cards)", not errs, errs); ctx.close()

    # unlock popup for char:gam
    sv = save(); sv["p"].update({"gam": {"visits": 1, "seen": True, "won": 0}})
    ctx, p, errs = page(b, site="stable", local=norm(b, sv), toggle=False, dev=False)
    settle(p, 600)
    p.evaluate("S.p.pop.queue=[{type:'char',items:[{key:'gam',name:'El Gamblador'}]}];go('menu')"); p.wait_for_selector("#popg", timeout=5000); p.wait_for_timeout(800)
    has = p.evaluate("!!document.querySelector('#modal canvas[data-draw^=\"gamb\"]')"); ink = p.evaluate("(%s)('#modal canvas[data-draw^=\"gamb\"]')" % INK)
    check("unlock popup for El Gamblador shows his picture", has and ink > 3000, (has, ink))
    pop = p.evaluate("document.querySelector('#modal canvas[data-draw^=\"gamb\"]').toDataURL()")
    check("unlock popup draws the dealer's idle frame (not BJSPR.pres)", pop == p.evaluate(REFJS) and pop != p.evaluate(PRESJS))
    p.click("#popd"); p.wait_for_timeout(300)
    p.evaluate("S.p.pop.queue=[{type:'game',items:[{idx:2,name:'Rocciamon'}]}];go('menu')"); p.wait_for_selector("#popg", timeout=5000)
    check("other popups unchanged (no gamb picture on a «game» popup)", not p.evaluate("!!document.querySelector('#modal canvas[data-draw^=\"gamb\"]')"))
    check("no console errors (popup)", not errs, errs); ctx.close()

    # ------------- forced Ferma encounter at girone 8
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p, 600); p.click("[data-tile=new]"); pick_maze(p); p.wait_for_function("G&&G.state==='play'", timeout=8000)
    p.evaluate("cancelAnimationFrame(raf);window.__fi=null;faInvite=function(o){window.__fi=o};Math.random=()=>0.99;S.p.fa.enc=0;0")
    res = {}
    for st in (5, 7, 8, 9):
        p.evaluate("G.stage=%d;G.dev=false;window.__fi=null;G.state='clear';bjAfterClear(G.run);0" % st); res[st] = p.evaluate("window.__fi&&window.__fi.forced")
    check("forced Ferma invite: not at girone 5 or 7, yes at 8 (and later) when never met", not res[5] and not res[7] and res[8] is True and res[9] is True, res)
    p.evaluate("S.p.fa.enc=1;G.stage=8;window.__fi=null;bjAfterClear(G.run);0")
    check("not forced once the player has met Ferma (random chance only, stubbed to none)", p.evaluate("window.__fi") is None)
    check("no console errors (forced encounter)", not errs, errs); ctx.close()
    b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
