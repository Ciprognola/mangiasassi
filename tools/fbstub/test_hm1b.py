#!/usr/bin/env python3
"""0.5_3 (HM1b) tests: the focus ring (KNAV) on every screen, shared by the pad and the arrow keys, plus L1/R1 tabs.
A) Opzioni: down moves the ring over the accordion headers; A opens one; inside it a range slider (injected: the
game has none yet) moves with right and fires input/change; a checkbox (injected, same reason) toggles with A.
B) Opzioni with dev mode: R1 goes to Sviluppatore, L1 back to Generali.
C) Lista desideri: R1 to Rocce; the D-pad moves across the grid; a card below the fold scrolls into view; A on «Usa»
selects the character like a tap.
D) «Partita finita»: the ring reaches «Menu» and «Ancora!»; A on «Ancora!» starts a new run.
E) El Gamblador invite card: the ring reaches «Non ora» and «Siediti»; A on «Siediti» seats the player like a tap.
F) A text input (login username): A focuses it; the D-pad does nothing while focused; B blurs it.
G) Maze playing: the D-pad still drives setDir and no ring appears.
H) Keyboard: ArrowDown on Opzioni moves the ring; Enter opens the accordion.
I) bite: KNAV_MUTATE=menuonly serves the old candidate rule (menu tiles only) and A and C must fail.
Reuses the harness of test_hm1.py (fake Pocket Taco, real clicks and presses).
Run: python tools/fbstub/test_hm1b.py   (PYTHONIOENCODING=utf-8 on Windows)"""
import functools, http.server, os, shutil, sys, tempfile, threading
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
__file__ = os.path.join(HERE, "test_f2b.py")
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only
from gp import pick_maze

MUT = os.environ.get("KNAV_MUTATE", "")
PAD = """(()=>{
  window.__pad={id:'GameSir-Pocket 1 (Vendor: 3537 Product: 1132)',index:0,mapping:'',connected:true,
    buttons:Array.from({length:17},()=>({pressed:false,value:0})),axes:[0,0,0,0],timestamp:0};
  Object.defineProperty(navigator,'getGamepads',{configurable:true,value:()=>[window.__pad,null,null,null]});
})()"""
BTN = {"a": 0, "b": 1, "l1": 4, "r1": 5, "select": 8, "start": 9, "up": 12, "down": 13, "left": 14, "right": 15}
RING = "(document.querySelector('.kf')||null)"


def pad_set(p, name, val):
    p.evaluate("window.__pad.buttons[%d].pressed=%s" % (BTN[name], "true" if val else "false"))


def press(p, name, ms=130):
    pad_set(p, name, True); p.wait_for_timeout(ms); pad_set(p, name, False); p.wait_for_timeout(160)


def ring_id(p):
    return p.evaluate("(document.querySelector('.kf')||{}).id||''")


def ring_tag(p):
    return p.evaluate("(document.querySelector('.kf')||{}).tagName||''")


def press_until(p, name, pred, n=30):
    """press name until pred() holds (the layout decides the path); returns True when it holds"""
    for _ in range(n):
        if pred():
            return True
        press(p, name)
    return pred()


def dev_on_site_open(p):
    p.click("[data-tile=opt]"); p.wait_for_timeout(500)


def dev_open(p, sel):
    """Opzioni -> Sviluppatore -> the accordion holding sel -> click (real clicks)"""
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(%s)').open" % sel):
        p.click("details.acc:has(%s) > summary" % sel); p.wait_for_timeout(250)
    p.click(sel); p.wait_for_timeout(600)


def mutant_base():
    """the build with the old candidate rule (menu tiles only), served on its own port"""
    d = tempfile.mkdtemp(prefix="hm1b_mut_")
    body = open(os.path.join(ROOT, "index.html"), encoding="utf-8", newline="").read()
    old = "    if(KNAV_GAME.includes(screen))return[];\r\n    return within(root);"
    assert body.count(old) == 1, body.count(old)
    body = body.replace(old, "    if(KNAV_GAME.includes(screen))return[];\r\n    return screen===\"menu\"?within(root).filter(e=>e.matches(\"[data-tile]\")):[];", 1)
    for rel in ("index.html", os.path.join("dev", "index.html")):
        os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
        open(os.path.join(d, rel), "w", encoding="utf-8", newline="").write(body)

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    port = 8797
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=d))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d/" % port, d


if MUT == "menuonly":
    BASE, MUT_DIR = mutant_base()
    print("MUTANT build (menu-only candidates) at", BASE, flush=True)
elif MUT:
    raise SystemExit("unknown KNAV_MUTATE=" + MUT)

srv = serve()
with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ A) Opzioni: ring over accordions, A opens, slider, checkbox
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    dev_on_site_open(p)
    press(p, "down")  # first press places the ring
    reached = press_until(p, "down", lambda: ring_tag(p) == "SUMMARY", 30)
    check("A) the D-pad moves the ring onto an accordion header", reached, ring_tag(p))
    press(p, "a"); p.wait_for_timeout(300)
    opened = p.evaluate("[...document.querySelectorAll('details.acc')].some(d=>d.open)")
    check("A) A opens the focused accordion", opened, p.evaluate("[...document.querySelectorAll('details.acc')].map(d=>d.open)"))
    p.evaluate("""(()=>{const d=document.querySelector('details.acc[open]');if(!d)return 0;
      const r=document.createElement('input');r.type='range';r.id='t_rng';r.min=0;r.max=10;r.step=1;r.value=2;
      r.addEventListener('input',()=>{window.__rngIn=(window.__rngIn||0)+1});r.addEventListener('change',()=>{window.__rngCh=(window.__rngCh||0)+1});
      const c=document.createElement('input');c.type='checkbox';c.id='t_chk';c.addEventListener('change',()=>{window.__chk=c.checked});
      d.querySelector(':scope>summary').after(c);d.appendChild(r);return 0})()""")  # the game has no slider or checkbox yet: injected here
    p.wait_for_timeout(200)
    on_chk = press_until(p, "down", lambda: ring_id(p) == "t_chk", 10)
    check("A) the ring reaches the injected checkbox under the header", on_chk, ring_id(p))
    if on_chk:
        press(p, "a"); p.wait_for_timeout(200)
        check("A) A toggles the checkbox (checked, change fired)", p.evaluate("document.getElementById('t_chk').checked") and p.evaluate("window.__chk===true"), p.evaluate("document.getElementById('t_chk').checked"))
    on_rng = press_until(p, "down", lambda: ring_id(p) == "t_rng", 30)
    if not on_rng:
        print("   trace:", p.evaluate("KNAV.items().map(e=>(e.id||e.tagName)+'@'+Math.round(e.getBoundingClientRect().top))"), flush=True)
    check("A) the ring reaches the injected range slider inside the open accordion", on_rng, ring_id(p))
    if on_rng:
        press(p, "right"); press(p, "right")
        check("A) right raises the slider value (2 → 4)", p.evaluate("document.getElementById('t_rng').value") == "4", p.evaluate("document.getElementById('t_rng').value"))
        check("A) and fires input/change like a drag", p.evaluate("(window.__rngIn||0)>=2&&(window.__rngCh||0)>=2"), p.evaluate("[window.__rngIn,window.__rngCh]"))
    check("A) no console errors (Opzioni)", not errs, errs)
    ctx.close()

    # ============================================================ B) dev mode: R1 to Sviluppatore, L1 back
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    dev_on_site_open(p)
    press(p, "down")
    press(p, "r1"); p.wait_for_timeout(400)
    check("B) R1 switches Opzioni to Sviluppatore", p.evaluate("optTab") == "dev", p.evaluate("optTab"))
    check("B) the ring sits on a control of the new tab (not on the tab row)", p.evaluate("!!document.querySelector('.kf')&&!document.querySelector('.kf').closest('.tabs')"), ring_tag(p))
    press(p, "l1"); p.wait_for_timeout(400)
    check("B) L1 switches back to Generali", p.evaluate("optTab") == "gen", p.evaluate("optTab"))
    check("B) no console errors (tabs)", not errs, errs)
    ctx.close()

    # ============================================================ C) Lista desideri: R1, grid, scroll into view, A on «Usa»
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    p.click("[data-tile=wish]"); p.wait_for_timeout(500)
    press(p, "down")
    press(p, "r1"); p.wait_for_timeout(400)
    check("C) R1 goes to Rocce", p.evaluate("tab") == "rocks", p.evaluate("tab"))
    ids = set()
    for d in ["right", "right", "down", "down", "left", "down"]:
        press(p, d); ids.add(p.evaluate("(document.querySelector('.kf')||{}).outerHTML||''")[:80])
    check("C) the D-pad moves the ring across the grid", len(ids) >= 3, len(ids))
    for _ in range(12):
        press(p, "down")
    below = p.evaluate("(()=>{const k=document.querySelector('.kf');if(!k)return false;const r=k.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&!!k.closest('.scroll')})()")
    scrolled = p.evaluate("(document.querySelector('.scroll')||{}).scrollTop>0")
    check("C) a card below the fold scrolls into view when focused", below and scrolled, (below, scrolled))
    press(p, "r1"); p.wait_for_timeout(400)
    check("C) R1 again reaches the Giocatore tab", p.evaluate("tab") == "player", p.evaluate("tab"))
    before = p.evaluate("S.p.char")
    found = press_until(p, "down", lambda: p.evaluate("(document.querySelector('.kf')||{}).dataset&&document.querySelector('.kf').dataset.char!==undefined"), 30)
    check("C) the ring reaches a «Usa» button", found, ring_tag(p))
    if found:
        press(p, "a"); p.wait_for_timeout(500)
        after = p.evaluate("S.p.char")
        check("C) A on «Usa» selects that character like a tap", after != before and p.evaluate("screen") == "wish", (before, after))
    check("C) no console errors (wish)", not errs, errs)
    ctx.close()

    # ============================================================ D) «Partita finita»: Menu / Ancora!
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    dev_open(p, "#jgGo"); p.wait_for_function("typeof G==='object'&&G&&G.state==='play'", timeout=12000)
    p.evaluate("finishRun({})"); p.wait_for_timeout(500)
    check("D) the run ends on the «Partita finita» screen", p.evaluate("screen") == "over", p.evaluate("screen"))
    seen = set()
    for _ in range(4):
        press(p, "down"); seen.add(ring_id(p))
        press(p, "left"); seen.add(ring_id(p))
        press(p, "right"); seen.add(ring_id(p))
    check("D) the ring reaches «Menu» and «Ancora!»", {"mn", "ag"} <= seen, seen)
    if "ag" in seen:
        press_until(p, "down", lambda: ring_id(p) == "ag", 12)
        press(p, "a"); p.wait_for_timeout(800)
        check("D) A on «Ancora!» starts a new run", p.evaluate("screen") == "game" and p.evaluate("!!G"), p.evaluate("screen"))
    check("D) no console errors (over)", not errs, errs)
    ctx.close()

    # ============================================================ E) El Gamblador invite card: Non ora / Siediti
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    dev_open(p, "#mggam"); p.wait_for_timeout(900)
    check("E) the invite card is up", p.evaluate("!document.getElementById('bpres').hidden && !!document.getElementById('bp-yes')"), p.evaluate("screen"))
    seen = set()
    for _ in range(8):
        press(p, "down"); seen.add(ring_id(p))
        press(p, "right"); seen.add(ring_id(p))
        press(p, "left"); seen.add(ring_id(p))
    check("E) the ring reaches «Non ora» and «Siediti»", {"bp-no", "bp-yes"} <= seen, seen)
    press_until(p, "down", lambda: ring_id(p) == "bp-yes", 12)
    press(p, "a"); p.wait_for_timeout(700)
    check("E) A on «Siediti» seats the player (card gone or hidden, like a tap)", p.evaluate("(e=>!e||e.hidden)(document.getElementById('bpres'))"), p.evaluate("!!document.getElementById('bpres')"))
    check("E) no console errors (invite)", not errs, errs)
    ctx.close()

    # ============================================================ F) text input: A focuses, D-pad does nothing, B blurs
    ctx, p, errs = page(b, site="dev", dev=False, toggle=False, extra_init=PAD)  # logged out on the dev site: the login form shows
    settle(p)
    dev_on_site_open(p)
    p.click("details.acc[data-acc=account] > summary"); p.wait_for_timeout(300)
    found = press_until(p, "down", lambda: ring_id(p) == "plu", 3) or press_until(p, "up", lambda: ring_id(p) == "plu", 40)  # the first press rings «Entra» (primary), the username is above it
    check("F) the ring reaches the login username field", found, ring_id(p))
    if found:
        press(p, "a"); p.wait_for_timeout(200)
        check("F) A focuses the field", p.evaluate("document.activeElement.id") == "plu", p.evaluate("document.activeElement.id"))
        press(p, "down"); press(p, "right")
        check("F) the D-pad does nothing while the field has focus", p.evaluate("document.activeElement.id") == "plu" and ring_id(p) == "plu", (p.evaluate("document.activeElement.id"), ring_id(p)))
        press(p, "b"); p.wait_for_timeout(200)
        check("F) B blurs the field", p.evaluate("document.activeElement.id") != "plu", p.evaluate("document.activeElement.id"))
    check("F) no console errors (text input)", not errs, errs)
    ctx.close()

    # ============================================================ G) maze playing: D-pad drives setDir, no ring
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    p.click("[data-tile=new]"); p.wait_for_timeout(700); pick_maze(p); p.wait_for_timeout(500)
    p.wait_for_function("typeof G==='object'&&G&&G.state==='play'", timeout=12000)
    press(p, "left")
    check("G) left sets the direction like ArrowLeft (G.pl.next = 3)", p.evaluate("G.pl.next") == 3, p.evaluate("G.pl.next"))
    check("G) no focus ring appears in the maze", p.evaluate("!document.querySelector('.kf')"), ring_tag(p))
    check("G) no console errors (maze)", not errs, errs)
    ctx.close()

    # ============================================================ H) keyboard: ArrowDown moves the ring, Enter opens
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False)
    settle(p)
    dev_on_site_open(p)
    p.keyboard.press("ArrowDown"); p.wait_for_timeout(150)
    check("H) ArrowDown on Opzioni places the ring", p.evaluate("!!document.querySelector('.kf')"), ring_tag(p))
    got = False
    for _ in range(30):
        if ring_tag(p) == "SUMMARY":
            got = True
            break
        p.keyboard.press("ArrowDown"); p.wait_for_timeout(120)
    check("H) the keyboard reaches an accordion header", got, ring_tag(p))
    if got:
        p.keyboard.press("Enter"); p.wait_for_timeout(300)
        check("H) Enter opens the accordion", p.evaluate("[...document.querySelectorAll('details.acc')].some(d=>d.open)"), p.evaluate("[...document.querySelectorAll('details.acc')].map(d=>d.open)"))
    check("H) no console errors (keyboard)", not errs, errs)
    ctx.close()

    if MUT:
        print("MUTANT run done: A and C are expected to fail", flush=True)
        shutil.rmtree(MUT_DIR, ignore_errors=True)
srv.shutdown()
print("%d/%d checks passed" % (sum(RES), len(RES)), flush=True)
sys.exit(0 if all(RES) else 1)
