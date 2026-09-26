#!/usr/bin/env python3
"""F5 headless tests (Firebase stub): long-press text edit. Run: python tools/fbstub/test_f5.py  (takes ~1.5 min: every long press holds 3 s)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "screens"))
import capture as C, fbstub
from playwright.sync_api import sync_playwright

RES = []
DEVC = {"role": "master", "acct": "master", "fb": True, "devOn": True}
ALLOWED = {"uid", "acct", "kind", "char", "screen", "target", "locator", "before", "value", "note", "base", "ts", "meta"}


def check(name, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name, extra, flush=True)


def page(b, dev=True, cache=None, **kw):
    ctx = b.new_context(viewport=C.VIEW, has_touch=False)
    cache = DEVC if (dev and cache is None) else cache
    if cache is not None:
        ctx.add_init_script("if(!sessionStorage.getItem('__seeded')){sessionStorage.setItem('__seeded','1');localStorage.setItem('mgs_dev',%s)}" % json.dumps(json.dumps(cache)))
        kw.setdefault("session", "master")
    fbstub.install(ctx, **kw)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    return ctx, p, errs


def menu(p):
    p.goto(C.BASE + "index.html"); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(900)


def centre(p, sel):
    return p.evaluate("(s)=>{const r=document.querySelector(s).getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}", sel)


def hold(p, x, y, secs=3.3):
    p.mouse.move(x, y); p.mouse.down(); time.sleep(secs); p.mouse.up(); p.wait_for_timeout(300)


def hold_el(p, sel, secs=3.3):
    x, y = centre(p, sel); hold(p, x, y, secs)


def popup(p):
    return p.evaluate("!!document.querySelector('#lpv')")


def launch_browser(pw):
    """Some sandboxes preinstall a Chromium revision older than this pip playwright expects; fall
    back to whatever chrome-linux/chrome is actually on disk before giving up (see test_f4a.py)."""
    try:
        return pw.chromium.launch()
    except Exception:
        import glob, os
        base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
        cands = glob.glob(os.path.join(base, "chromium-*", "chrome-linux", "chrome")) if base else []
        if cands:
            return pw.chromium.launch(executable_path=cands[0])
        raise


srv = C.serve()
with sync_playwright() as pw:
    b = launch_browser(pw)
    # ------------------------------------------------------------ enabled only for a logged-in dev with dev mode on
    ctx, p, errs = page(b, dev=False); menu(p)
    native = "[native code]"
    check("logged out: fillText wrapper NOT installed", native in p.evaluate("CanvasRenderingContext2D.prototype.fillText.toString()"))
    hold_el(p, "[data-tile=wish] span"); check("logged out: long press does nothing (normal click ran, no popup)", not popup(p) and p.evaluate("screen") == "wish")
    ctx.close()
    ctx, p, errs = page(b); menu(p)
    check("dev on: fillText wrapper installed", native not in p.evaluate("CanvasRenderingContext2D.prototype.fillText.toString()"))
    p.click("#devt"); p.wait_for_timeout(300)
    check("dev toggled off: wrapper removed", native in p.evaluate("CanvasRenderingContext2D.prototype.fillText.toString()"))
    hold_el(p, "[data-tile=wish] span"); check("dev off: no popup", not popup(p))
    ctx.close()
    # ------------------------------------------------------------ DOM label (known key), no click after the long press
    ctx, p, errs = page(b); menu(p)
    p.mouse.move(*centre(p, "[data-tile=wish] span")); p.mouse.down(); time.sleep(1.2)
    check("outline shown while holding", p.evaluate("!!document.querySelector('svg rect[stroke-dasharray]')")); p.mouse.up(); p.wait_for_timeout(300)
    check("released before 3 s: normal tap (went to Lista desideri), no popup", not popup(p) and p.evaluate("screen") == "wish" and not p.evaluate("!!document.querySelector('svg rect[stroke-dasharray]')"))
    p.evaluate("go('menu')"); p.wait_for_timeout(500)
    hold_el(p, "[data-tile=wish] span")
    check("long press on a tile label opens the popup, tile click suppressed", popup(p) and p.evaluate("screen") == "menu", p.evaluate("screen"))
    txt = p.evaluate("document.querySelector('#modal').innerText")
    check("popup: screen id, key, live preview, colour + scale fields", "dev-textedit-popup" == p.evaluate("screenId()") and "menu-home-roccia" in txt and "tile.wish.label" in txt and "anteprima dal vivo" in txt and p.evaluate("!!document.querySelector('#lpcol')&&!!document.querySelector('#lpsc')"), txt[:200])
    check("popup: current text read-only, proposal prefilled", p.evaluate("document.querySelector('#lpcur').readOnly") and p.evaluate("document.querySelector('#lpcur').value") == "Lista desideri" and p.evaluate("document.querySelector('#lpv').value") == "Lista desideri")
    p.fill("#lpv", "x" * 700); check("popup: 500-char cap + counter", p.evaluate("document.querySelector('#lpv').value.length") == 500 and p.evaluate("document.querySelector('#lpn').innerText") == "500/500")
    p.keyboard.press("Escape"); p.wait_for_timeout(200)
    check("Esc = Annulla: nothing saved", not popup(p) and p.evaluate("S.tiles.find(t=>t.id==='wish').label") == "Lista desideri" and p.evaluate("screenId()") == "menu-home-roccia")
    hold_el(p, "[data-tile=wish] span"); p.fill("#lpv", "Desideri"); p.fill("#lpnote", "più corto"); p.click("#lpk"); p.wait_for_timeout(500)
    check("Salva (known key): applied live", p.evaluate("S.tiles.find(t=>t.id==='wish').label") == "Desideri" and "Desideri" in p.evaluate("document.querySelector('[data-tile=wish]').innerText") and not popup(p))
    edits = p.evaluate("expTextEdits().list.filter(e=>e.target==='tile.wish.label')")
    check("change is in the export list (key, value, before)", len(edits) == 1 and edits[0]["value"] == "Desideri" and edits[0]["before"] == "Lista desideri", edits)
    p.evaluate("go('opt')"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(200)
    if not p.evaluate("document.querySelector('details.acc:has(#xopen)').open"): p.click("details.acc:has(#xopen) > summary")
    p.click("#xopen"); p.wait_for_timeout(600); p.click("details:has-text('Elenco') > summary")
    check("export dialog prefills the popup note", p.evaluate("document.querySelector('[data-en=\"tile.wish.label\"]').value") == "più corto")
    p.click("#xs"); p.wait_for_timeout(900)
    d = [x for x in p.evaluate("window.__fbs.edits||[]") if x.get("target") == "tile.wish.label"]
    check("Invia testi sends it with the popup note (field set unchanged)", len(d) == 1 and d[0]["note"] == "più corto" and set(d[0]) <= ALLOWED and "locator" not in d[0], d)
    check("no console errors (DOM label flow)", not errs, errs); ctx.close()
    # ------------------------------------------------------------ gameplay controls / running canvas ignored
    ctx, p, errs = page(b); menu(p); p.click("[data-tile=new]"); p.wait_for_timeout(3800)
    hold_el(p, ".dpad [data-d='0']", 3.3); check("maze d-pad (data-nolp): nothing", not popup(p))
    x, y = centre(p, "#cv"); hold(p, x, y); check("maze running: canvas long press ignored", not popup(p))
    hold_el(p, "#sc", 3.3); check("maze HUD label (DOM) works anytime", popup(p) and p.evaluate("G.state") == "pause", p.evaluate("screenId()"))
    p.keyboard.press("Escape"); p.wait_for_timeout(500); check("Annulla resumes the maze", p.evaluate("G.state") != "pause")
    hold_el(p, "#sc", 3.3); check("text edit popup open again (for the back button)", popup(p) and p.evaluate("G.state") == "pause")
    p.evaluate("window.__kd=0;window.addEventListener('keydown',()=>{window.__kd++})"); p.keyboard.press("ArrowLeft"); p.wait_for_timeout(100); kd0 = p.evaluate("window.__kd")
    p.evaluate("window.dispatchEvent(new Event('mgback'))"); p.wait_for_timeout(500)
    check("Android back (mgback) = Annulla: popup closed, maze resumed, no pause menu, BUG cleared", not popup(p) and p.evaluate("G.state") != "pause" and not p.evaluate("!!document.querySelector('#r')") and p.evaluate("BUG===null"))
    p.keyboard.press("ArrowLeft"); p.wait_for_timeout(100)
    check("after back: keys reach the game again (blocked while open)", kd0 == 0 and p.evaluate("window.__kd") == 1, (kd0, p.evaluate("window.__kd")))
    p.click("#bugb"); p.wait_for_timeout(300); hold_el(p, ".bugbox h3", 3.3); check("bug popup is never long-pressable", p.evaluate("!!document.querySelector('#bgt')") and not popup(p))
    check("no console errors (maze)", not errs, errs); ctx.close()
    # ------------------------------------------------------------ Ferma: pause-panel text (DOM) and canvas text only while paused
    ctx, p, errs = page(b); menu(p)
    p.evaluate("go('opt')"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(200); p.click("details.acc:has(#mgfa) > summary"); p.wait_for_timeout(200)
    p.click("#mgfd"); p.click("#mgfa"); p.wait_for_timeout(4500)  # overlay debug ON -> canvas text
    check("Ferma running: canvas has registered text", p.evaluate("(()=>{const c=document.querySelector('#fac');return !!(c&&c.__lp&&c.__lp.list.length)})()"))
    r = p.evaluate("(()=>{const c=document.querySelector('#fac'),q=c.__lp.list[0],r=c.getBoundingClientRect(),k=r.width/c.width;return [r.left+(q.x+q.w/2)*k,r.top+(q.y+q.h/2)*k,q.text]})()")
    hold(p, r[0], r[1]); check("Ferma playing: canvas long press ignored", not popup(p) and not p.evaluate("FA.paused"))
    p.click("#fap"); p.wait_for_timeout(500)
    hold(p, r[0], r[1]); check("Ferma paused: canvas text opens the popup (proposal, locator canvas)", popup(p) and "anteprima non disponibile" in p.evaluate("document.querySelector('#modal').innerText") and r[2][:8] in p.evaluate("document.querySelector('#lpcur').value"), r[2])
    p.keyboard.press("Escape"); p.wait_for_timeout(300)
    hold_el(p, "#fapanel h3, #fapanel .box h3, #fapanel .box b", 3.3) if p.evaluate("!!document.querySelector('#fapanel .box')") else None
    check("Ferma pause panel (DOM) text opens the popup", popup(p), p.evaluate("document.querySelector('#fapanel').innerText")[:40])
    p.fill("#lpv", "Pausa!"); p.click("#lpk"); p.wait_for_timeout(400)
    pr = p.evaluate("JSON.parse(localStorage.getItem('mgs_editprops')||'[]')")
    check("no known key: proposal stored with locator {text,pos} + screen", len(pr) == 1 and pr[0]["locator"]["text"] and pr[0]["locator"]["pos"] and pr[0]["screen"] == "fa-pause" and pr[0]["value"] == "Pausa!", pr)
    check("no console errors (Ferma)", not errs, errs); ctx.close()
    # ------------------------------------------------------------ El Gamblador dialogue mid-typing = FULL line
    ctx, p, errs = page(b); menu(p)
    p.evaluate("go('opt')"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(200); p.click("details.acc:has(#mggam) > summary"); p.wait_for_timeout(200); p.click("#mggam")
    p.wait_for_selector("#bp-yes"); p.click("#bp-yes"); p.wait_for_timeout(600)
    t0 = time.time()  # a line that waits for a tap (deterministic): the box stays on screen while we hold
    while time.time() - t0 < 30 and not p.evaluate("!!(B&&B.confirmRes&&B.say)"):
        time.sleep(0.3)
    hold_el(p, "#btxt")  # the game is frozen while the popup is open, so B.say is the line the popup was opened on
    full = p.evaluate("B.say.text"); typed = p.evaluate("bjTyped()")
    check("dialogue: popup opens on the current line and shows B.say", popup(p) and p.evaluate("document.querySelector('#lpcur').value") == full, (full, typed))
    check("known dialogue key + Salva applies gtext", "dialogue.gam." in p.evaluate("document.querySelector('#modal').innerText"))
    p.fill("#lpv", "Frase nuova"); p.click("#lpk"); p.wait_for_timeout(300)
    check("dialogue saved to S.gtext", p.evaluate("Object.values(S.gtext).includes('Frase nuova')"))
    r = p.evaluate("""(()=>{B.say={id:'intro',text:'ABCDEFGHIJKLMNOPQRSTUVWXYZ',t0:bjNow()*1000,cps:.5};document.querySelector('#btxt').textContent='ABC';return lpDomTarget(document.querySelector('#btxt')).text})()""")
    check("dialogue mid-typing (3 of 26 chars on screen): the popup text is the FULL line", r == "ABCDEFGHIJKLMNOPQRSTUVWXYZ", r)
    check("no console errors (Gamblador)", not errs, errs); ctx.close()
    # ------------------------------------------------------------ battle move name (DOM) -> proposal -> Invia testi sends locator
    ctx, p, errs = page(b); menu(p)
    p.evaluate("go('opt')"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(200); p.click("details.acc:has(#mgrob) > summary"); p.wait_for_timeout(200); p.click("#mgrob")
    t0 = time.time()
    while time.time() - t0 < 40 and p.evaluate("!(PR&&PR.pb&&PR.pb.ask)"):
        if p.evaluate("!!(PR&&PR.pb&&PR.pb.w&&PR.pb.w.hold==null)"): p.keyboard.press("Enter")
        time.sleep(0.3)
    p.click("[data-bm='fight']"); p.wait_for_timeout(500)
    name = p.evaluate("document.querySelector('[data-bv=\"0\"]').innerText.trim()")
    hold_el(p, "[data-bv='0']")
    check("battle move name opens the popup (proposal, screen pb-move-panel)", popup(p) and "anteprima non disponibile" in p.evaluate("document.querySelector('#modal').innerText"), name)
    p.fill("#lpv", "Mossa nuova"); p.click("#lpk"); p.wait_for_timeout(400)
    pr = p.evaluate("JSON.parse(localStorage.getItem('mgs_editprops')||'[]')")
    check("battle proposal stored (before = current text)", len(pr) == 1 and pr[0]["value"] == "Mossa nuova" and pr[0]["before"] and pr[0]["screen"] in ("pb-move-panel", "pb-command"), pr)
    check("battle still alive after Annulla/Salva (resume)", p.evaluate("!!PR&&!PR.dead"))
    p.evaluate("go('menu')"); p.wait_for_timeout(500); p.evaluate("go('opt')"); p.wait_for_timeout(300)
    if p.evaluate("optTab")!="dev": p.click("[data-otab=dev]")
    p.wait_for_timeout(200)
    if not p.evaluate("document.querySelector('details.acc:has(#xopen)').open"): p.click("details.acc:has(#xopen) > summary")
    p.click("#xopen"); p.wait_for_timeout(600)
    p.click("details:has-text('Elenco') > summary")
    check("export list marks it 'anteprima non disponibile'", "anteprima non disponibile" in p.evaluate("document.querySelector('#modal').innerText"))
    p.click("#xs"); p.wait_for_timeout(900)
    d = p.evaluate("window.__fbs.edits||[]")
    check("Invia testi sends the proposal: locator, no target, allowed field set", len(d) == 1 and d[0]["locator"]["text"] == pr[0]["locator"]["text"] and "target" not in d[0] and set(d[0]) <= ALLOWED and d[0]["before"] == pr[0]["before"] and d[0]["screen"] == pr[0]["screen"], d)
    check("no console errors (battle)", not errs, errs); ctx.close()
    # ------------------------------------------------------------ smoke
    ctx, p, errs = page(b); menu(p); p.click("[data-tile=new]"); p.wait_for_timeout(1500)
    check("a run starts", p.evaluate("screen") == "game"); check("no console errors (smoke)", not errs, errs); ctx.close()
    b.close()
srv.shutdown()
print(sum(RES), "/", len(RES), "passed"); sys.exit(0 if all(RES) else 1)
