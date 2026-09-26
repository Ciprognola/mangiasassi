#!/usr/bin/env python3
"""0.4.5_3 tests: F1 (cloud toggle / restore keep scroll + accordion, no full re-render), F2 (one toast module: position, never over a
control, duration, queue, held during play), D0 (diagnostics log: persistence, cap, no personal data, UI, bug-report meta).
Reuses the harness of test_f2b.py (Firebase stub, never real credentials). Run: python tools/fbstub/test_toast_diag.py"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

PHONE = {"width": 390, "height": 844}
DESK = {"width": 1280, "height": 800}
LONG = "Spazio insufficiente: il salvataggio del cloud non è stato sostituito"

RECTS = """(()=>{
 const sel="button,summary,input,select,textarea,a,[data-tile],.card,.rtile,[role=button]";
 const t=document.querySelector('#toasts .toast');if(!t)return null;const tr=t.getBoundingClientRect();
 const bad=[...document.querySelectorAll(sel)].filter(e=>!e.closest('#toasts')).filter(e=>{const r=e.getBoundingClientRect();
   if(r.width<3||r.height<3||getComputedStyle(e).visibility==='hidden'||r.bottom<0||r.top>innerHeight)return false;
   const w=Math.min(tr.right,r.right)-Math.max(tr.left,r.left),h=Math.min(tr.bottom,r.bottom)-Math.max(tr.top,r.top);return w>2&&h>2}).map(e=>e.id||e.className||e.tagName);
 return {top:Math.round(tr.top),left:Math.round(tr.left),w:Math.round(tr.width),h:Math.round(tr.height),right:Math.round(tr.right),vw:innerWidth,pe:getComputedStyle(t).pointerEvents,bad}})()"""


def show_toast(p, msg=LONG):
    p.evaluate("toast(%s)" % json.dumps(msg)); p.wait_for_selector("#toasts .toast.on", timeout=3000); p.wait_for_timeout(350)
    r = p.evaluate(RECTS)
    return r


def wait_gone(p):
    p.wait_for_function("!document.querySelector('#toasts .toast')", timeout=8000)


def toast_screens(b, label, view):
    VIEW.clear(); VIEW.update(view)
    ctx, p, errs = page(b, site="dev", local=norm(b, save()), toggle=False)
    settle(p, 800)
    dev_ok = lambda r, nm: check(f"toast ({label}) {nm}: shown, no tap capture, inside the viewport, over no control, top-centre", r and r["pe"] == "none" and r["bad"] == [] and r["left"] >= 0 and r["right"] <= r["vw"] and r["top"] < 140, r)
    # menu
    dev_ok(show_toast(p), "menu"); wait_gone(p)
    # Opzioni, Generali with the Account accordion open
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("details.acc[data-acc=account] > summary"); p.wait_for_timeout(250)
    dev_ok(show_toast(p), "Opzioni"); wait_gone(p)
    p.click("[data-otab=dev]"); p.wait_for_timeout(250)
    dev_ok(show_toast(p, "Corto"), "Opzioni › Sviluppatore"); wait_gone(p)
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    # maze: not while playing (held), then over the paused game
    p.click("[data-tile=new]"); p.wait_for_function("G&&G.state==='play'", timeout=8000)
    p.evaluate("toast(%s)" % json.dumps(LONG)); p.wait_for_timeout(700)
    check(f"toast ({label}) maze: held back while the run is in play", p.evaluate("!document.querySelector('#toasts .toast')"))
    p.evaluate("G.state='pause'"); p.wait_for_selector("#toasts .toast.on", timeout=3000); p.wait_for_timeout(350)
    dev_ok(p.evaluate(RECTS), "maze (paused)"); wait_gone(p)
    p.evaluate("G.state='ready';G.t=5")
    dev_ok(show_toast(p, "Segreto sbloccato: Trasformati!"), "maze (ready)"); wait_gone(p)
    # Ferma Algidone!
    p.evaluate("cancelAnimationFrame(raf);startFerma({test:true})"); p.wait_for_function("FA&&FA.state==='play'", timeout=10000)
    p.evaluate("toast(%s)" % json.dumps(LONG)); p.wait_for_timeout(700)
    check(f"toast ({label}) Ferma: held back while playing", p.evaluate("!document.querySelector('#toasts .toast')"))
    p.evaluate("faPause(true)"); p.wait_for_selector("#toasts .toast.on", timeout=3000); p.wait_for_timeout(350)
    dev_ok(p.evaluate(RECTS), "Ferma (paused)"); wait_gone(p)
    check(f"toast ({label}): no console errors", not errs, errs)
    ctx.close()


def logic(b):
    VIEW.clear(); VIEW.update(PHONE)
    ctx, p, errs = page(b, site="dev", local=norm(b, save()), toggle=False)
    settle(p, 800)
    # duration: short text >= 2.5 s, long text <= 5 s, one at a time (queue), not inside #root (survives a render)
    t0 = time.time(); p.evaluate("toast('Corto')"); p.wait_for_selector("#toasts .toast.on"); p.evaluate("render()"); p.wait_for_timeout(100)
    check("toast survives a full render() (lives outside #root)", p.evaluate("!!document.querySelector('#toasts .toast')&&!document.querySelector('#root .toast')"))
    wait_gone(p); d1 = time.time() - t0
    check("short toast stays 2.5-3.2 s", 2.4 <= d1 <= 3.4, round(d1, 2))
    t0 = time.time(); p.evaluate("toast('x '.repeat(400))"); p.wait_for_selector("#toasts .toast.on"); wait_gone(p); d2 = time.time() - t0
    check("very long toast is capped at 5 s", 4.6 <= d2 <= 5.8, round(d2, 2))
    p.evaluate("toast('Uno');toast('Due');toast('Tre')"); seen = []
    for _ in range(40):
        seen.append(p.evaluate("[...document.querySelectorAll('#toasts .toast')].map(e=>e.textContent)")); p.wait_for_timeout(250)
    check("queue: never more than one toast on screen, all three shown in order", max(len(x) for x in seen) == 1 and [x[0] for x in seen if x][::1][0] == "Uno" and any(x == ["Due"] for x in seen) and any(x == ["Tre"] for x in seen), seen[:12])
    check("no console errors (toast logic)", not errs, errs)
    ctx.close()


def cloud_scroll(b):
    """F1: toggling the cloud test switch re-renders nothing; a reload (apply / restore) comes back to the same scroll position + open accordion"""
    fresh = save(r=1, a=1, sordi=0)
    for k in ("roccia", "algidone"):
        fresh["p"]["ch"][k].update(exp=0, gir=0, ownP=[0], ownR=[0])
    fresh = norm(b, fresh); cld = norm(b, save(r=22, a=3, sordi=90)); plain = norm(b, save())
    VIEW.clear(); VIEW.update({"width": 390, "height": 460})
    setscroll = "(()=>{const s=document.querySelector('.scroll');s.scrollTop=Math.min(s.scrollHeight-s.clientHeight,%d)})()"
    jsclick = "document.querySelector('[data-clt=\"%d\"]').click()"

    def open_acc(p):
        p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("details.acc[data-acc=account] > summary"); p.wait_for_timeout(250)

    # (a) no cloud copy yet: the switch only updates the section in place
    ctx, p, errs = page(b, site="dev", local=plain, toggle=False)
    settle(p, 800); open_acc(p)
    p.evaluate(setscroll % 80); p.wait_for_timeout(150)
    y0 = p.evaluate("document.querySelector('.scroll').scrollTop")
    check("(precondition) Opzioni is scrollable in the test viewport", y0 > 20, y0)
    p.evaluate("window.__renders=0;const o=window.render;window.render=function(){window.__renders++;return o.apply(this,arguments)};0")
    p.evaluate(jsclick % 1); p.wait_for_timeout(900)
    s = p.evaluate("({y:document.querySelector('.scroll').scrollTop,open:!!document.querySelector('details.acc[data-acc=account][open]'),renders:window.__renders,clsy:!document.querySelector('#clsy').disabled,st:document.querySelector('#clst').textContent})")
    check("F1: toggling cloud on causes no full re-render, keeps scroll and the open accordion, updates the section in place", s["renders"] == 0 and abs(s["y"] - y0) <= 2 and s["open"] and s["clsy"], (y0, s))
    p.evaluate(jsclick % 0); p.wait_for_timeout(300)
    s = p.evaluate("({y:document.querySelector('.scroll').scrollTop,renders:window.__renders,clsy:document.querySelector('#clsy').disabled})")
    check("F1: toggling it off: same, «Sincronizza ora» disabled again", s["renders"] == 0 and abs(s["y"] - y0) <= 2 and s["clsy"], s)
    check("F1: no console errors", not errs, errs); ctx.close()

    # (b) a newer cloud copy is applied at the toggle -> the reload comes back to the same place
    ctx, p, errs = page(b, site="dev", local=fresh, cloud={UID + "_dev": cdoc(cld, rev=2, ver="0.4.5")}, toggle=False)
    settle(p, 800); open_acc(p)
    p.evaluate(setscroll % 80); p.wait_for_timeout(150)
    y0 = p.evaluate("document.querySelector('.scroll').scrollTop")
    with p.expect_navigation(timeout=10000):
        p.evaluate(jsclick % 1)
    p.wait_for_selector("details.acc[data-acc=account][open]", timeout=8000); p.wait_for_timeout(500)
    s = p.evaluate("({y:document.querySelector('.scroll').scrollTop,screen:screen,splash:!!document.querySelector('#rsi'),lvl:S.p.ch.roccia.lvl})")
    check("F1: after the reload (cloud copy applied) same screen, accordion open, scroll position kept", s["screen"] == "opt" and not s["splash"] and s["lvl"] == 22 and abs(s["y"] - y0) <= 6, (y0, s))
    p.evaluate(setscroll % 90); p.wait_for_timeout(150)
    y1 = p.evaluate("document.querySelector('.scroll').scrollTop")
    p.evaluate("document.querySelector('#clrb').click()"); p.wait_for_selector("#cy"); 
    with p.expect_navigation(timeout=10000):
        p.evaluate("document.querySelector('#cy').click()")
    p.wait_for_selector("details.acc[data-acc=account][open]", timeout=8000); p.wait_for_timeout(500)
    s = p.evaluate("({y:document.querySelector('.scroll').scrollTop,screen:screen,lvl:S.p.ch.roccia.lvl})")
    check("F1: after «Ripristina backup» same screen, accordion open, scroll kept", s["screen"] == "opt" and s["lvl"] == 1 and abs(s["y"] - y1) <= 6, (y1, s))
    check("F1: no console errors (reload)", not errs, errs)
    ctx.close()


def diag(b):
    VIEW.clear(); VIEW.update(PHONE)
    ctx, p, errs = page(b, site="dev", local=norm(b, save()), toggle=False)
    settle(p, 1000)
    p.evaluate("DIAG.log('test','sopravvive alla ricarica')"); p.evaluate("DIAG.flush()"); p.reload(); p.wait_for_selector("#rsi")
    check("D0: entries survive a reload", p.evaluate("DIAG.all().some(e=>e.msg==='sopravvive alla ricarica')"))
    p.click("#rsi"); p.wait_for_timeout(600)
    kinds = p.evaluate("[...new Set(DIAG.all().map(e=>e.kind))]")
    check("D0: boot, screen changes and the fbVerify result are recorded", all(k in kinds for k in ("boot", "screen", "auth")), kinds)
    p.evaluate("(()=>{for(let i=0;i<450;i++)DIAG.log('spam','riga '+i+' '+'x'.repeat(280));DIAG.flush()})()")
    n = p.evaluate("DIAG.all().length"); sz = p.evaluate("(localStorage.getItem('mgs_diag_dev')||'').length")
    check("D0: cap holds (<=200 entries, stored <=50 KB)", 0 < n <= 200 and sz <= 50000, (n, sz))
    p.evaluate("DIAG.clear()")
    p.evaluate("(()=>{DIAG.log('t','utente marco@mangiasassi.invalid uid abcdefghijklmnopqrstuvwxyz012345 token eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMyJ9.abcdefghijklmnop');console.error('errore con marco@mangiasassi.invalid e ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef1234');window.dispatchEvent(new ErrorEvent('error',{message:'boom marco@x.y'}))})()")
    txt = p.evaluate("DIAG.text()")
    check("D0: emails and long ids/tokens are never stored", "@" not in txt and "abcdefghijklmnopqrstuvwxyz012345" not in txt and "eyJhbGci" not in txt and "ABCDEFGHIJKLMNOPQRSTUVWXYZ" not in txt, txt[:400])
    check("D0: console.error and window errors are recorded", "console.error" in txt and "boom" in txt, txt[:300])
    # real session data must not leak: fbVerify/boot in the stub uses uid_master / master@mangiasassi.invalid
    p.evaluate("DIAG.clear()"); p.reload(); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(1500)
    txt = p.evaluate("DIAG.text()")
    check("D0: nothing from the session leaks (no uid, no email)", "uid_master" not in txt and "@" not in txt and "mangiasassi.invalid" not in txt, txt[:300])
    # UI
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(250)
    p.click("details.acc[data-acc=diag] > summary"); p.wait_for_timeout(250)
    check("D0: «Diagnostica» accordion lists the entries", p.evaluate("document.querySelector('#dgl').innerText.length")>5 and p.evaluate("!!document.querySelector('#dgc')&&!!document.querySelector('#dgx')"))
    ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=BASE.rstrip("/"))
    p.click("#dgc"); p.wait_for_timeout(400)
    clip = p.evaluate("navigator.clipboard.readText()")
    cur = p.evaluate("DIAG.text()").split(chr(10)); miss = [l for l in clip.replace(chr(13), "").split(chr(10)) if l not in cur]
    check("D0: «Copia» puts the plain-text log in the clipboard", len(clip) > 5 and "screen" in clip and not miss, (miss[:3], len(clip)))
    p.click("#dgx"); p.wait_for_timeout(300)
    check("D0: «Svuota» empties it", p.evaluate("DIAG.all().length<=1") and "vuoto" in p.evaluate("document.querySelector('#dgl').innerText") or p.evaluate("DIAG.all().length")<=2)
    # bug reports: dev attach the last 30, players none
    p.evaluate("(()=>{for(let i=0;i<50;i++)DIAG.log('t','v'+i)})()")
    m = p.evaluate("bugInfo().meta.diag")
    check("D0: a dev bug report carries the last 30 entries in meta", isinstance(m, list) and len(m) == 30 and m[-1].endswith("v49"), m and m[-2:])
    p.evaluate("(()=>{window.__r=role;role=null})()")
    check("D0: without a dev role (player report) nothing is attached", p.evaluate("!('diag' in bugInfo().meta)"))
    check("D0: no console errors", not [e for e in errs if "boom" not in e and "errore con" not in e], errs)
    ctx.close()
    # icon tap is logged
    ctx, p, errs = page(b, site="dev", local=norm(b, save()), toggle=False)
    p.wait_for_selector("#rsi"); p.wait_for_timeout(500); p.click("#bugb"); p.wait_for_timeout(300)
    t = p.evaluate("DIAG.text()")
    check("D0: a bug-icon tap and whether the popup opened are logged", "tocco sull'icona" in t and "popup aperto" in t, t[:300])
    ctx.close()


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    logic(b)
    toast_screens(b, "390 px", PHONE)
    toast_screens(b, "desktop", DESK)
    cloud_scroll(b)
    diag(b)
    b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
