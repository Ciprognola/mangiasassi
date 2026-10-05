#!/usr/bin/env python3
"""0.5_5 (HM1d) tests: Lista desideri levels (tabs, then the panel, then the card), organic grid moves, and the
Obiettivi list (achievement entries are candidates; the ring follows them while scrolling).
a) Lista desideri entry: the ring lands on the active tab; left/right move along the tabs without selecting; up/down
   do nothing; A on Rocce selects it and puts the ring on its first card.
b) Panel: the D-pad never lands on a tab; right/left go to the card next to it in the same row; down goes to the card
   below in the same column; at an edge nothing happens.
c) Card group still works: A enters a card with «Usa», «Usa» is reachable, B goes back to the card.
d) B from a card → ring on the active tab; B again → today's back (menu).
e) L1/R1 → the new tab is active and the ring is on it.
f) Obiettivi: down from the tab row → the first entry; down walks every entry in order; an entry that starts off-screen
   is scrolled into view and #kring contains it, with yellow pixels in a screenshot.
g) A pointer press clears the ring and resets the panel level.
h) Keyboard parity for a, b and d.
Bite: HM1D_MUTATE=notab (Lista desideri flat again) must fail a/d; =grid (organic moves off) must fail b; =ach (entries not
candidates) must fail f.
Reuses the harness and the fake Pocket Taco of test_hm1c.py.
Run: python tools/fbstub/test_hm1d.py   (PYTHONIOENCODING=utf-8 on Windows)"""
import functools, http.server, os, shutil, sys, tempfile, threading
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
__file__ = os.path.join(HERE, "test_f2b.py")
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

MUT = os.environ.get("HM1D_MUTATE", "")
EXPECT = {"notab": ("a", "d"), "grid": ("b",), "ach": ("f",)}  # the failing checks each mutation must cause
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


def press_until(p, name, pred, n=30, via=press):
    for _ in range(n):
        if pred():
            return True
        via(p, name)
    return pred()


def ring_text(p):
    return p.evaluate("((document.querySelector('.kf')||{}).textContent||'').trim().slice(0,30)")


def ring_tile(p):
    return p.evaluate("(document.querySelector('.kf')||{}).dataset&&document.querySelector('.kf').dataset.tile||''")


def in_tabs(p):
    return p.evaluate("!!(document.querySelector('.kf')&&document.querySelector('.kf').closest('.tabs'))")


def on_tab(p):
    return p.evaluate("!!(document.querySelector('.kf')&&document.querySelector('.kf').classList.contains('on')&&document.querySelector('.kf').closest('.tabs'))")


def ring_card_index(p):
    """index of the ring among the panel's cards (-1 when the ring is not on a card)"""
    return p.evaluate("(()=>{const k=document.querySelector('.kf');const cs=[...document.querySelectorAll('.scroll .card')];return cs.indexOf(k)})()")


def card_count(p):
    return p.evaluate("document.querySelectorAll('.scroll .card').length")


def ring_card_cols(p):
    """number of grid columns of the panel (from the computed layout)"""
    return p.evaluate("(()=>{const g=document.querySelector('.scroll .grid');return g?getComputedStyle(g).gridTemplateColumns.split(' ').length:0})()")


def enter_wish_from_menu(p):
    """the menu first: D-pad onto the Lista desideri tile, A (the keys path, so the ring is on the active tab on entry)"""
    ok = press_until(p, "down", lambda: ring_tile(p) == "wish", 25)
    press(p, "a"); p.wait_for_timeout(500)
    return ok


def kring(p):
    """the overlay against the ring: displayed, rect contains the element (±4px), yellow pixels in a screenshot"""
    info = p.evaluate("""(()=>{const k=document.getElementById('kring'),e=document.querySelector('.kf');if(!k||!e)return null;
      const a=k.getBoundingClientRect(),b=e.getBoundingClientRect();
      return {disp:getComputedStyle(k).display!=='none',inside:a.left<=b.left+4&&a.top<=b.top+4&&a.right>=b.right-4&&a.bottom>=b.bottom-4,
        x:a.left,y:a.top,w:a.width,h:a.height}})()""")
    if not info or not info["disp"] or not info["inside"] or info["w"] <= 0:
        return False, info
    shot = os.path.join(tempfile.mkdtemp(prefix="hm1d_"), "ring.png")
    p.screenshot(path=shot, clip={"x": info["x"], "y": info["y"], "width": info["w"], "height": info["h"]})
    from PIL import Image
    im = Image.open(shot).convert("RGB")
    n = sum(1 for px in im.getdata() if all(abs(px[i] - YEL[i]) <= 24 for i in range(3)))
    return n >= 40, n


def mutant_base():
    """the build with one HM1d step switched off, served on its own port"""
    d = tempfile.mkdtemp(prefix="hm1d_mut_")
    body = open(os.path.join(ROOT, "index.html"), encoding="utf-8", newline="").read()
    rules = {
        "notab": ('screen==="wish"&&c===root?KNAV.wishLevel()', 'false?KNAV.wishLevel()'),
        "grid": ("const organic=!!cur.closest", "const organic=false&&!!cur.closest"),
        "ach": ('[role=button],[data-ach]";', '[role=button]";'),
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
    port = 8799
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=d))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d/" % port, d


if MUT:
    if MUT not in EXPECT:
        raise SystemExit("unknown HM1D_MUTATE=" + MUT)
    BASE, MUT_DIR = mutant_base()
    print("MUTANT build (%s) at %s" % (MUT, BASE), flush=True)

srv = serve()
with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ a) entry, tab level
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    reached = enter_wish_from_menu(p)
    chk("a) the menu D-pad reaches the Lista desideri tile and A enters it", reached and p.evaluate("screen") == "wish", p.evaluate("screen"))
    chk("a) on entry the ring is on the active tab (Aeroplani)", on_tab(p) and ring_text(p) == "Aeroplani", ring_text(p))
    press(p, "right")
    chk("a) right moves the ring to the next tab without selecting it", ring_text(p) == "Rocce" and p.evaluate("tab") == "planes", (ring_text(p), p.evaluate("tab")))
    press(p, "down")
    chk("a) down does nothing on the tab row", ring_text(p) == "Rocce" and in_tabs(p), ring_text(p))
    press(p, "up")
    chk("a) up does nothing on the tab row", ring_text(p) == "Rocce" and in_tabs(p), ring_text(p))
    press(p, "a"); p.wait_for_timeout(400)
    chk("a) A on Rocce selects it", p.evaluate("tab") == "rocks", p.evaluate("tab"))
    chk("a) and puts the ring on its first card", ring_card_index(p) == 0, (ring_text(p), ring_card_index(p)))
    chk("a) no console errors (entry)", not errs, errs)
    ctx.close()

    # ============================================================ b) panel: no tab, organic grid moves
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    enter_wish_from_menu(p)
    press(p, "a"); p.wait_for_timeout(300)  # A on the active tab (Aeroplani) enters the panel
    chk("b) the panel starts on the first card", ring_card_index(p) == 0, (ring_text(p), ring_card_index(p)))
    cols = ring_card_cols(p)
    chk("b) the grid has two columns on a phone", cols == 2, cols)
    tabs_hit = False
    for d in ["right", "down", "left", "up", "down", "right", "up", "left"]:
        press(p, d)
        if in_tabs(p):
            tabs_hit = True
    chk("b) the D-pad never lands on a tab from the panel", not tabs_hit, "")
    press(p, "left")
    press(p, "right")
    chk("b) right goes to the card next to it in the same row", ring_card_index(p) == 1, ring_card_index(p))
    press(p, "left")
    chk("b) left goes back to the first card", ring_card_index(p) == 0, ring_card_index(p))
    press(p, "down")
    chk("b) down goes to the card in the same column of the next row", ring_card_index(p) == 2, ring_card_index(p))
    press(p, "up")
    chk("b) up goes back to the first card", ring_card_index(p) == 0, ring_card_index(p))
    n = card_count(p)
    # walk to the last card: the last one sits at the bottom right or bottom left
    for _ in range(40):
        if ring_card_index(p) >= n - 1:
            break
        press(p, "down" if ring_card_index(p) + 2 < n else "right")
    last = ring_card_index(p)
    chk("b) the walk reaches the last card", last == n - 1, (last, n))
    press(p, "down")
    chk("b) at the bottom edge down does nothing", ring_card_index(p) == last, ring_card_index(p))
    press(p, "up"); press(p, "right")  # the right column of the same row: 23
    chk("b) right from the left card of a row goes to the right card of that row", ring_card_index(p) == last - 1, ring_card_index(p))
    press(p, "right")
    chk("b) at the right edge right does nothing", ring_card_index(p) == last - 1, ring_card_index(p))
    # an irregular row (test-only, like the slider of HM1b): the first card is narrowed, so the card in the next row is
    # nearer by distance; the card beside it must still win (the same row, perpendicular overlap)
    p.click("[data-tab=planes]"); p.wait_for_timeout(400)
    press(p, "down"); press(p, "a"); p.wait_for_timeout(300)  # entering the panel re-renders it: the width goes in after that
    p.evaluate("(()=>{const c=document.querySelector('.scroll .card');c.style.width='40px';return 0})()")
    chk("b) irregular row: the first card is the ring", ring_card_index(p) == 0, ring_card_index(p))
    press(p, "right")
    chk("b) irregular row: right picks the card beside it, not the nearer card in the next row", ring_card_index(p) == 1, ring_card_index(p))
    chk("b) no console errors (panel)", not errs, errs)
    ctx.close()

    # ============================================================ c) card group still works
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    enter_wish_from_menu(p)
    p.click("[data-tab=player]"); p.wait_for_timeout(400)  # a real click clears the ring: start again on the active tab
    press(p, "down"); press(p, "a"); p.wait_for_timeout(300)  # enter the Giocatore panel
    press(p, "right")  # the Algidone card (its «Usa» is the only control)
    chk("c) the ring is on the card with «Usa»", p.evaluate("(()=>{const k=document.querySelector('.kf');return !!k&&k.classList.contains('card')&&!!k.querySelector('[data-char]')})()"), ring_text(p))
    card = p.evaluate("(window.__cd=document.querySelector('.kf'),1)")
    press(p, "a"); p.wait_for_timeout(200)
    chk("c) A enters the card: the ring is on «Usa»", p.evaluate("!!document.querySelector('.kf')&&!!document.querySelector('.kf').dataset.char"), ring_text(p))
    press(p, "b"); p.wait_for_timeout(200)
    chk("c) B goes back to the card", p.evaluate("document.querySelector('.kf')===window.__cd"), ring_text(p))
    chk("c) and leaves the group", p.evaluate("KNAV.grp===null"), "")
    chk("c) no console errors (card)", not errs, errs)
    ctx.close()

    # ============================================================ d) B from a card → tab; B again → back
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    enter_wish_from_menu(p)
    press(p, "a"); p.wait_for_timeout(300)
    chk("d) the ring is on a card before B", ring_card_index(p) == 0, ring_text(p))
    press(p, "b"); p.wait_for_timeout(200)
    chk("d) B from a card → the ring is on the active tab", on_tab(p) and ring_text(p) == "Aeroplani", ring_text(p))
    press(p, "b"); p.wait_for_timeout(500)
    chk("d) B again → today's back (menu)", p.evaluate("screen") == "menu", p.evaluate("screen"))
    chk("d) no console errors (back)", not errs, errs)
    ctx.close()

    # ============================================================ e) L1/R1 switch tab and put the ring on it
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    enter_wish_from_menu(p)
    press(p, "r1"); p.wait_for_timeout(400)
    chk("e) R1 switches to Rocce", p.evaluate("tab") == "rocks", p.evaluate("tab"))
    chk("e) the ring is on the new active tab", on_tab(p) and ring_text(p) == "Rocce", ring_text(p))
    press(p, "l1"); p.wait_for_timeout(400)
    chk("e) L1 switches back to Aeroplani with the ring on it", p.evaluate("tab") == "planes" and on_tab(p) and ring_text(p) == "Aeroplani", (p.evaluate("tab"), ring_text(p)))
    chk("e) no console errors (tabs)", not errs, errs)
    ctx.close()

    # ============================================================ f) Obiettivi: entries are candidates, the ring follows
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    p.click("#trop"); p.wait_for_timeout(500)
    chk("f) the Obiettivi screen opens", p.evaluate("screen") == "ach", p.evaluate("screen"))
    ids = p.evaluate("[...document.querySelectorAll('.scroll [data-ach]')].map(e=>e.dataset.ach)")
    chk("f) the list has entries", len(ids) >= 10, len(ids))
    entered = press_until(p, "down", lambda: p.evaluate("(document.querySelector('.kf')||{}).dataset&&document.querySelector('.kf').dataset.ach!==undefined"), 12)
    chk("f) down from the tab row reaches the first entry", entered and p.evaluate("document.querySelector('.kf').dataset.ach") == ids[0], (ring_text(p), ids[:1]))
    walked = [p.evaluate("document.querySelector('.kf').dataset.ach")]
    offscreen_checked = False
    offscreen_ok = True
    for i in range(1, len(ids)):
        off = p.evaluate("(()=>{const k=document.querySelector('.kf');const cur=[...document.querySelectorAll('.scroll [data-ach]')];const nx=cur[cur.indexOf(k)+1];return !!nx&&nx.getBoundingClientRect().bottom>innerHeight})()")
        press(p, "down"); p.wait_for_timeout(350)
        walked.append(p.evaluate("(document.querySelector('.kf')||{}).dataset&&document.querySelector('.kf').dataset.ach||''"))
        if off:
            offscreen_checked = True
            ok, npx = kring(p)
            inview = p.evaluate("(()=>{const r=document.querySelector('.kf').getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight})()")
            if not (ok and inview):
                offscreen_ok = False
                print("   off-screen entry check failed:", ok, npx, inview, flush=True)
    chk("f) down walks every entry in order to the last one", walked == ids, (walked[:3], len(walked), len(ids)))
    chk("f) an entry that started off-screen was scrolled into view with the ring around it", offscreen_checked and offscreen_ok, offscreen_checked)
    chk("f) no console errors (Obiettivi)", not errs, errs)
    ctx.close()

    # ============================================================ g) a pointer press clears the ring and the panel level
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    enter_wish_from_menu(p)
    press(p, "a"); p.wait_for_timeout(300)
    p.mouse.move(2, 2); p.mouse.down(); p.mouse.up(); p.wait_for_timeout(200)
    cleared = p.evaluate("(()=>{const k=document.getElementById('kring');return !document.querySelector('.kf')&&(!k||getComputedStyle(k).display==='none')&&KNAV.grp===null&&KNAV.panel===false})()")
    chk("g) a pointer press clears the ring, hides #kring and resets the panel level", cleared, "")
    chk("g) no console errors (pointer)", not errs, errs)
    ctx.close()

    # ============================================================ h) keyboard parity for a, b, d
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False)
    settle(p)
    p.keyboard.press("ArrowDown"); p.wait_for_timeout(150)
    if not press_until(p, "down", lambda: ring_tile(p) == "wish", 25, via=key):
        # the menu's first keyboard placement varies between «Percorso» and «Nuovo gioco» on load (also on 0.5_4, not HM1d's
        # subject): place the ring on the wish tile directly so this check is about the Lista desideri keys
        p.evaluate("KNAV.set(document.querySelector('[data-tile=wish]'))")
    key(p, "a"); p.wait_for_timeout(500)
    chk("h) Enter on the Lista desideri tile: the ring is on the active tab", on_tab(p) and ring_text(p) == "Aeroplani", ring_text(p))
    key(p, "right")
    chk("h) ArrowRight moves along the tabs without selecting", ring_text(p) == "Rocce" and p.evaluate("tab") == "planes", ring_text(p))
    key(p, "down")
    chk("h) ArrowDown does nothing on the tab row", in_tabs(p) and ring_text(p) == "Rocce", ring_text(p))
    key(p, "left")
    key(p, "a"); p.wait_for_timeout(400)
    chk("h) Enter selects the tab and enters the panel (first card)", p.evaluate("tab") == "planes" and ring_card_index(p) == 0, (p.evaluate("tab"), ring_text(p)))
    key(p, "right")
    chk("h) ArrowRight in the panel goes to the next card", ring_card_index(p) == 1, ring_card_index(p))
    key(p, "down")
    chk("h) ArrowDown in the panel goes down the column (never a tab)", not in_tabs(p) and ring_card_index(p) == 3, (ring_card_index(p), ring_text(p)))
    key(p, "b"); p.wait_for_timeout(200)
    chk("h) Escape from a card → the active tab", on_tab(p), ring_text(p))
    key(p, "b"); p.wait_for_timeout(500)
    chk("h) Escape again on the tab row does nothing on the keyboard, as today (B is the pad's back)", p.evaluate("screen") == "wish", p.evaluate("screen"))
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
