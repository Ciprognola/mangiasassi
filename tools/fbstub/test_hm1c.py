#!/usr/bin/env python3
"""0.5_4 (HM1c) tests: navigation fixes after the 0.5_3 phone test.
a) Opzioni tab row: left/right move the ring between tabs without selecting; A selects; edges do nothing.
b) Lista desideri tab row: the same rule.
c) L1/R1 still switch tabs directly.
d) The ring is visible for every candidate type (#kring rect contains the element, yellow pixels in a screenshot).
e) Lista desideri two levels: cards first, A enters a card, D-pad stays inside, A on «Usa» acts like a tap, B returns to the card.
f) Opzioni accordions two levels: A opens and enters, D-pad stays inside, A on a text input focuses, B blurs, B returns to the
   header, down skips the content, B closes an open header, B on a closed header = today's back.
g) A pointer press clears the ring, hides #kring and resets the group.
h) Keyboard parity: a, e and f again with arrows, Enter and Escape.
Bite: HM1C_MUTATE=tabgeo (step 1 off, a must fail), =ring (overlay hidden, d must fail), =flat (groups off, e and f must fail).
Reuses the harness and the fake Pocket Taco of test_hm1b.py.
Run: python tools/fbstub/test_hm1c.py   (PYTHONIOENCODING=utf-8 on Windows)"""
import functools, http.server, os, shutil, sys, tempfile, threading
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
__file__ = os.path.join(HERE, "test_f2b.py")
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

MUT = os.environ.get("HM1C_MUTATE", "")
EXPECT = {"tabgeo": ("a",), "ring": ("d",), "flat": ("e", "f")}  # the failing checks each mutation must cause
FAILS = []
PAD = """(()=>{
  window.__pad={id:'GameSir-Pocket 1 (Vendor: 3537 Product: 1132)',index:0,mapping:'',connected:true,
    buttons:Array.from({length:17},()=>({pressed:false,value:0})),axes:[0,0,0,0],timestamp:0};
  Object.defineProperty(navigator,'getGamepads',{configurable:true,value:()=>[window.__pad,null,null,null]});
})()"""
BTN = {"a": 0, "b": 1, "l1": 4, "r1": 5, "select": 8, "start": 9, "up": 12, "down": 13, "left": 14, "right": 15}
YEL = (255, 210, 63)


def chk(name, ok, extra=""):
    check(name, ok, extra)
    if not ok:
        FAILS.append(name)


def pad_set(p, name, val):
    p.evaluate("window.__pad.buttons[%d].pressed=%s" % (BTN[name], "true" if val else "false"))


def press(p, name, ms=130):
    pad_set(p, name, True); p.wait_for_timeout(ms); pad_set(p, name, False); p.wait_for_timeout(200)


def key(p, name):
    p.keyboard.press({"up": "ArrowUp", "down": "ArrowDown", "left": "ArrowLeft", "right": "ArrowRight", "a": "Enter", "b": "Escape"}[name])
    p.wait_for_timeout(200)


def ring_tag(p):
    return p.evaluate("(document.querySelector('.kf')||{}).tagName||''")


def ring_text(p):
    return p.evaluate("((document.querySelector('.kf')||{}).textContent||'').trim().slice(0,30)")


def press_until(p, name, pred, n=30, via=press):
    for _ in range(n):
        if pred():
            return True
        via(p, name)
    return pred()


def in_tabs(p):
    return p.evaluate("!!(document.querySelector('.kf')&&document.querySelector('.kf').closest('.tabs'))")


def ring_is_card(p):
    return p.evaluate("!!document.querySelector('.kf')&&document.querySelector('.kf').classList.contains('card')")


def ring_is_group_card(p):
    return p.evaluate("(()=>{const k=document.querySelector('.kf');return !!k&&k.classList.contains('card')&&!!k.querySelector('button')})()")


def reach_group_card(p, n=40):
    """walk to the selected tab, then down: the Algidone card (the one with «Usa») is directly below Giocatore"""
    for _ in range(n):
        if ring_is_group_card(p):
            return True
        if p.evaluate("(()=>{const k=document.querySelector('.kf');return !!k&&k.classList.contains('on')})()"):
            press(p, "down")  # the selected tab (Giocatore): straight down lands on the Algidone card
        elif p.evaluate("!!(document.querySelector('.kf')&&document.querySelector('.kf').closest('.tabs'))"):
            press(p, "right")  # along the tab row to the selected tab
        else:
            press(p, "down")
    return ring_is_group_card(p)


def kring(p):
    """the overlay against the ring: displayed, rect contains the element (±4px), yellow pixels in a screenshot"""
    info = p.evaluate("""(()=>{const k=document.getElementById('kring'),e=document.querySelector('.kf');if(!k||!e)return null;
      const a=k.getBoundingClientRect(),b=e.getBoundingClientRect();
      return {disp:getComputedStyle(k).display!=='none',inside:a.left<=b.left+4&&a.top<=b.top+4&&a.right>=b.right-4&&a.bottom>=b.bottom-4,
        x:a.left,y:a.top,w:a.width,h:a.height}})()""")
    if not info or not info["disp"] or not info["inside"] or info["w"] <= 0:
        return False, info
    shot = os.path.join(tempfile.mkdtemp(prefix="hm1c_"), "ring.png")
    p.screenshot(path=shot, clip={"x": info["x"], "y": info["y"], "width": info["w"], "height": info["h"]})
    from PIL import Image
    im = Image.open(shot).convert("RGB")
    n = sum(1 for px in im.getdata() if all(abs(px[i] - YEL[i]) <= 24 for i in range(3)))
    return n >= 40, n


def check_ring(p, label):
    ok, n = kring(p)
    chk("d) ring visible: " + label, ok, n)


def dev_on_site_open(p):
    p.click("[data-tile=opt]"); p.wait_for_timeout(500)


def open_acc(p, acc):
    """Opzioni, current tab: A on the accordion header (keeps the ring on it, as a player would)"""
    press_until(p, "down", lambda: p.evaluate("(document.querySelector('.kf')||{}).parentElement&&document.querySelector('.kf').parentElement.dataset.acc==='%s'" % acc), 40)
    press(p, "a"); p.wait_for_timeout(300)


def mutant_base():
    """the build with one HM1c step switched off, served on its own port"""
    d = tempfile.mkdtemp(prefix="hm1c_mut_")
    body = open(os.path.join(ROOT, "index.html"), encoding="utf-8", newline="").read()
    rules = {
        "tabgeo": ("if(tr&&(dir===1||dir===3)){", "if(false){"),
        "ring": ("#kring{position:fixed;", "#kring{display:none!important;position:fixed;"),
        "flat": ("  isGroup(a){return a.classList", "  isGroup(a){return false;return a.classList"),
    }
    old, new = rules[MUT]
    assert body.count(old) == 1, (MUT, body.count(old))
    body = body.replace(old, new, 1)
    for rel in ("index.html", os.path.join("dev", "index.html")):
        os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
        open(os.path.join(d, rel), "w", encoding="utf-8", newline="").write(body)

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    port = 8798
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=d))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d/" % port, d


if MUT:
    if MUT not in EXPECT:
        raise SystemExit("unknown HM1C_MUTATE=" + MUT)
    BASE, MUT_DIR = mutant_base()
    print("MUTANT build (%s) at %s" % (MUT, BASE), flush=True)

srv = serve()
with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ a) Opzioni tab row
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    dev_on_site_open(p)
    press(p, "down")
    reached = press_until(p, "down", lambda: in_tabs(p), 40)
    chk("a) the ring reaches the Opzioni tab row", reached, ring_text(p))
    if reached:
        chk("a) the ring starts on «Generali»", ring_text(p) == "Generali", ring_text(p))
        press(p, "right")
        chk("a) right moves the ring to «Sviluppatore»", ring_text(p) == "Sviluppatore" and in_tabs(p), ring_text(p))
        chk("a) and does not select it (Generali still active)", p.evaluate("optTab") == "gen", p.evaluate("optTab"))
        press(p, "a"); p.wait_for_timeout(400)
        chk("a) A selects «Sviluppatore», the ring stays on it", p.evaluate("optTab") == "dev" and ring_text(p) == "Sviluppatore", (p.evaluate("optTab"), ring_text(p)))
        press(p, "right")
        chk("a) right on the last tab does nothing", ring_text(p) == "Sviluppatore", ring_text(p))
        press(p, "left")
        chk("a) left goes back to «Generali»", ring_text(p) == "Generali", ring_text(p))
        press(p, "left")
        chk("a) left on the first tab does nothing", ring_text(p) == "Generali", ring_text(p))
    chk("a) no console errors (Opzioni tabs)", not errs, errs)
    ctx.close()

    # ============================================================ b) Lista desideri tab row, c) L1/R1 still direct
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    p.click("[data-tile=wish]"); p.wait_for_timeout(500)
    press(p, "down")
    reached = press_until(p, "down", lambda: in_tabs(p), 40)
    chk("b) the ring reaches the Lista desideri tab row", reached, ring_text(p))
    if reached:
        first = p.evaluate("tab")
        press(p, "right")
        chk("b) right moves the ring to the next tab, not selected", p.evaluate("tab") == first and in_tabs(p), (first, p.evaluate("tab")))
        press(p, "a"); p.wait_for_timeout(400)
        chk("b) A selects that tab", p.evaluate("tab") != first, p.evaluate("tab"))
        chk("b) the ring stays on the selected tab", in_tabs(p) and "on" in p.evaluate("(document.querySelector('.kf')||{}).className||''"), ring_text(p))
        press(p, "left")
        chk("b) left moves back", p.evaluate("tab") != first and ring_text(p) != "", ring_text(p))
    t0 = p.evaluate("tab")
    press(p, "r1"); p.wait_for_timeout(300)
    t1 = p.evaluate("tab")
    chk("c) R1 switches the tab directly", t1 != t0, (t0, t1))
    press(p, "l1"); p.wait_for_timeout(300)
    chk("c) L1 switches back directly", p.evaluate("tab") == t0, (t0, p.evaluate("tab")))
    chk("b) no console errors (wish tabs)", not errs, errs)
    ctx.close()

    # ============================================================ d) ring visibility per candidate type
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    press(p, "down")
    check_ring(p, "menu tile")
    dev_on_site_open(p)
    press(p, "down")
    press_until(p, "up", lambda: in_tabs(p), 40)
    check_ring(p, "tab")
    press_until(p, "down", lambda: ring_tag(p) == "SUMMARY", 40)
    check_ring(p, "accordion header")
    press(p, "a"); p.wait_for_timeout(300)
    press_until(p, "down", lambda: ring_tag(p) == "BUTTON" and p.evaluate("!!document.querySelector('.kf').closest('details.acc[open]')"), 40)
    check_ring(p, "button inside an open Opzioni accordion")
    p.evaluate("""(()=>{const d=document.querySelector('details.acc[open]');
      const s=document.createElement('select');s.id='t_sel';s.innerHTML='<option>a</option><option>b</option>';
      const i=document.createElement('input');i.type='text';i.id='t_txt';i.value='x';
      d.querySelector('.accb').append(i,s);return 0})()""")
    p.wait_for_timeout(200)
    if press_until(p, "down", lambda: p.evaluate("(document.querySelector('.kf')||{}).id")=="t_txt", 40):
        check_ring(p, "text input")
    else:
        chk("d) ring visibility: text input reached", False, ring_text(p))
    if press_until(p, "down", lambda: p.evaluate("(document.querySelector('.kf')||{}).id")=="t_sel", 40):
        check_ring(p, "select")
    else:
        chk("d) ring visibility: select reached", False, p.evaluate("(document.querySelector('.kf')||{}).id"))
    chk("d) no console errors (ring types, dev)", not errs, errs)
    ctx.close()

    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    press(p, "down")
    press(p, "b")  # today's back on the menu: a quit popup with buttons
    p.wait_for_timeout(400)
    if p.evaluate("!!modalEl().firstChild"):
        press_until(p, "down", lambda: p.evaluate("!!document.querySelector('.kf')&&!!document.querySelector('.kf').closest('#modal')"), 20)
        check_ring(p, "#modal button")
    else:
        chk("d) ring visibility: a #modal popup opens on B", False, p.evaluate("screen"))
    ctx.close()

    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    p.click("[data-tile=wish]"); p.wait_for_timeout(500)
    press_until(p, "down", lambda: ring_is_card(p), 30)
    check_ring(p, "Lista desideri card")
    p.click("[data-tab=player]"); p.wait_for_timeout(400)
    reach_group_card(p)
    press(p, "a"); p.wait_for_timeout(200)
    check_ring(p, "a control inside a Lista desideri card («Usa»)")
    chk("d) no console errors (ring types, wish)", not errs, errs)
    ctx.close()

    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    p.click("details.acc:has(#mggam) > summary"); p.wait_for_timeout(250)
    p.click("#mggam"); p.wait_for_timeout(900)
    if p.evaluate("!document.getElementById('bpres').hidden && !!document.getElementById('bp-yes')"):
        press_until(p, "down", lambda: ring_text(p) == "Siediti" or p.evaluate("(document.querySelector('.kf')||{}).id")=="bp-yes", 12)
        check_ring(p, "invite card button")
    else:
        chk("d) ring visibility: the invite card is up", False, p.evaluate("screen"))
    ctx.close()

    # ============================================================ e) Lista desideri two levels
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    p.click("[data-tile=wish]"); p.wait_for_timeout(500)
    p.click("[data-tab=player]"); p.wait_for_timeout(400)
    got = reach_group_card(p)
    chk("e) the D-pad reaches a card with controls (top level)", got, ring_tag(p))
    p.evaluate("window.__cd=document.querySelector('.kf')")
    moves_clean = True
    for d in ["right", "down", "left", "down", "right"]:
        press(p, d)
        inside = p.evaluate("(()=>{const k=document.querySelector('.kf');return !!k&&!k.classList.contains('card')&&!!k.closest('.card')})()")
        if inside:
            moves_clean = False
    chk("e) moving between cards never lands on a control inside a card", moves_clean, "")
    p.click("[data-tab=player]"); p.wait_for_timeout(400)  # a real click clears the ring: walk back from the tab row
    reach_group_card(p)
    p.evaluate("window.__cd=document.querySelector('.kf')")
    press(p, "a"); p.wait_for_timeout(200)
    inner_ok = p.evaluate("(()=>{const k=document.querySelector('.kf');return !!k&&k!==window.__cd&&k.closest('.card')===window.__cd})()")
    chk("e) A on the card puts the ring on its first control", inner_ok, ring_text(p))
    stuck = True
    for d in ["right", "right", "down", "down", "left", "up"]:
        press(p, d)
        if not p.evaluate("(()=>{const k=document.querySelector('.kf');return !!k&&k.closest('.card')===window.__cd})()"):
            stuck = False
    chk("e) the D-pad cannot leave the card", stuck, "")
    chk("e) and the ring stays on a control of that card", p.evaluate("(()=>{const k=document.querySelector('.kf');return !!k&&k.closest('.card')===window.__cd})()"), "")
    press(p, "b"); p.wait_for_timeout(200)
    back_ok = p.evaluate("(()=>{const k=document.querySelector('.kf');return !!k&&k===window.__cd&&k.classList.contains('card')})()")
    chk("e) B puts the ring back on the card", back_ok, ring_text(p))
    chk("e) and leaves the group (KNAV.grp null)", p.evaluate("KNAV.grp===null"), "")
    usa_ok = p.evaluate("!!document.querySelector('[data-char]')")
    if usa_ok:
        press(p, "a"); p.wait_for_timeout(200)  # enter the card: its only control is «Usa»
        chk("e) A on the card lands on «Usa»", p.evaluate("!!document.querySelector('.kf')&&!!document.querySelector('.kf').dataset.char"), ring_text(p))
        before = p.evaluate("S.p.char")
        press(p, "a"); p.wait_for_timeout(500)
        chk("e) A on «Usa» acts like a tap (the character changed)", p.evaluate("S.p.char") != before, (before, p.evaluate("S.p.char")))
    else:
        chk("e) a «Usa» button exists in the player tab", False, "")
    chk("e) no console errors (wish groups)", not errs, errs)
    ctx.close()

    # ============================================================ f) Opzioni accordions two levels
    ctx, p, errs = page(b, site="dev", dev=False, toggle=False, extra_init=PAD)  # logged out: the Account accordion has inputs
    settle(p)
    dev_on_site_open(p)
    press(p, "down")
    open_acc(p, "account")
    opened = p.evaluate("!!document.querySelector('details.acc[data-acc=account]').open")
    chk("f) A on a closed header opens it", opened, "")
    inside = p.evaluate("(()=>{const k=document.querySelector('.kf');return !!k&&!!k.closest('details.acc[data-acc=account]')&&!k.matches('summary')})()")
    chk("f) and enters it (ring on its first control)", inside, ring_tag(p))
    press(p, "down")
    chk("f) the D-pad stays inside", p.evaluate("!!document.querySelector('.kf')&&!!document.querySelector('.kf').closest('details.acc[data-acc=account]')"), ring_tag(p))
    if press_until(p, "down", lambda: p.evaluate("!!document.querySelector('.kf')&&document.querySelector('.kf').matches('input:not([type=hidden])')"), 20):
        press(p, "a"); p.wait_for_timeout(200)
        chk("f) A on a text input focuses it", p.evaluate("document.activeElement===document.querySelector('.kf')"), "")
        before = p.evaluate("(document.querySelector('.kf')||{}).id")
        press(p, "down")
        chk("f) D-pad does nothing while the input is focused", p.evaluate("(document.querySelector('.kf')||{}).id")==before, "")
        press(p, "b")
        chk("f) B blurs the input", p.evaluate("document.activeElement.tagName")!="INPUT", "")
        press(p, "b"); p.wait_for_timeout(200)
        chk("f) B again puts the ring on the header", ring_tag(p) == "SUMMARY" and p.evaluate("(document.querySelector('.kf')||{}).parentElement.dataset.acc")=="account", ring_tag(p))
        chk("f) and the accordion stays open", p.evaluate("!!document.querySelector('details.acc[data-acc=account]').open"), "")
    else:
        chk("f) a text input is reachable inside the Account accordion", False, ring_tag(p))
    press(p, "down")
    chk("f) down from the open header skips its content to the next header", ring_tag(p) == "SUMMARY" and p.evaluate("(document.querySelector('.kf')||{}).parentElement.dataset.acc")!="account", ring_text(p))
    press_until(p, "up", lambda: p.evaluate("!!document.querySelector('.kf')&&document.querySelector('.kf').parentElement.dataset.acc==='account'"), 20)
    press(p, "b"); p.wait_for_timeout(200)
    chk("f) B on the open header closes it, the ring stays on it", not p.evaluate("!!document.querySelector('details.acc[data-acc=account]').open") and p.evaluate("!!document.querySelector('.kf')&&document.querySelector('.kf').parentElement.dataset.acc==='account'"), "")
    press(p, "b"); p.wait_for_timeout(400)
    chk("f) B on a closed header = today's back (menu)", p.evaluate("screen")=="menu", p.evaluate("screen"))
    chk("f) no console errors (accordions)", not errs, errs)
    ctx.close()

    # ============================================================ g) a pointer press resets everything
    ctx, p, errs = page(b, site="dev", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    dev_on_site_open(p)
    press(p, "down")
    open_acc(p, "account")
    p.mouse.move(2, 2); p.mouse.down(); p.mouse.up(); p.wait_for_timeout(200)
    cleared = p.evaluate("(()=>{const k=document.getElementById('kring');return !document.querySelector('.kf')&&(!k||getComputedStyle(k).display==='none')&&KNAV.grp===null})()")
    chk("g) a pointer press clears the ring, hides #kring and resets the group", cleared, "")
    chk("g) no console errors (pointer)", not errs, errs)
    ctx.close()

    # ============================================================ h) keyboard parity
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    dev_on_site_open(p)
    p.keyboard.press("ArrowDown"); p.wait_for_timeout(150)
    press_until(p, "down", lambda: in_tabs(p), 40, via=key)
    if in_tabs(p):
        key(p, "right")
        chk("h) ArrowRight moves the ring to the next tab, not selected", ring_text(p) == "Sviluppatore" and p.evaluate("optTab") == "gen", ring_text(p))
        key(p, "a")
        chk("h) Enter selects it and the ring stays on it", p.evaluate("optTab") == "dev" and ring_text(p) == "Sviluppatore", "")
        key(p, "left")
    else:
        chk("h) the keyboard reaches the tab row", False, "")
    press_until(p, "down", lambda: ring_tag(p) == "SUMMARY", 40, via=key)
    key(p, "a"); p.wait_for_timeout(300)
    key(p, "down")
    chk("h) keyboard: inside an opened header the ring stays in the group", p.evaluate("!!document.querySelector('.kf')&&!!document.querySelector('.kf').closest('details.acc[open]')"), ring_tag(p))
    key(p, "b")
    chk("h) Escape returns to the group header", ring_tag(p) == "SUMMARY", ring_tag(p))
    key(p, "b")
    chk("h) Escape on an open header closes it", p.evaluate("!document.querySelector('details.acc[open]')"), "")
    chk("h) no console errors (keyboard)", not errs, errs)
    ctx.close()

    if MUT:
        shutil.rmtree(MUT_DIR, ignore_errors=True)
srv.shutdown()
print("%d/%d checks passed" % (sum(RES), len(RES)), flush=True)
if MUT:
    seen = set(n[:1] for n in FAILS)
    ok = all(x in seen for x in EXPECT[MUT])
    print("MUTANT %s: failing checks = %s; expected to fail: %s -> %s" % (MUT, FAILS, EXPECT[MUT], "BITES" if ok else "NOT CAUGHT"), flush=True)
    sys.exit(0 if ok else 1)
sys.exit(0 if all(RES) else 1)
