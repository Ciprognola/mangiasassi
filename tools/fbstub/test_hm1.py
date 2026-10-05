#!/usr/bin/env python3
"""0.5_2 (HM1) tests: controller input (PAD). A fake Pocket Taco (17 buttons, the 0.5_1 preset indices) drives the
existing actions: the menu focus ring (KNAV), the maze (setDir, abilPress, #stl, pauseMenu), Ferma (FA_KEYS through
the keyboard path, faJump, faPause), Blackjack (bjMove, bjConfirm, bjPause), the professor (keys through pr/pbKey).
A) menu: right moves the focus ring; A opens the focused tile. B) Opzioni: B returns to the menu. C) maze: left
turns like ArrowLeft; Start pauses; down + A resumes. D) maze: A activates the ability (ready), A again exits; B
toggles Fermo. E) Ferma: right held moves the player, release stops it; A jumps; Start pauses and resumes.
F) Blackjack: A confirms; Start sets bjPauseT. G) professor dialogue: A advances. H) menu: down held 1 s moves the
focus at least 3 times. I) «Prova controller» open: nothing else is driven. J) bite: PAD_MUTATE=noroute serves a
build with routing disabled, and A and C must fail. Reuses the harness of test_f2b.py.
Run: python tools/fbstub/test_hm1.py"""
import functools, http.server, os, shutil, sys, tempfile, threading
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
__file__ = os.path.join(HERE, "test_f2b.py")
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only
from gp import pick_maze

MUT = os.environ.get("PAD_MUTATE", "")
PAD = """(()=>{
  window.__pad={id:'GameSir-Pocket 1 (Vendor: 3537 Product: 1132)',index:0,mapping:'',connected:true,
    buttons:Array.from({length:17},()=>({pressed:false,value:0})),axes:[0,0,0,0],timestamp:0};
  Object.defineProperty(navigator,'getGamepads',{configurable:true,value:()=>[window.__pad,null,null,null]});
})()"""
BTN = {"a": 0, "b": 1, "select": 8, "start": 9, "up": 12, "down": 13, "left": 14, "right": 15}


def pad_set(p, name, val):
    p.evaluate("window.__pad.buttons[%d].pressed=%s" % (BTN[name], "true" if val else "false"))


def press(p, name, ms=130):
    pad_set(p, name, True); p.wait_for_timeout(ms); pad_set(p, name, False); p.wait_for_timeout(120)


def hold(p, name, ms):
    pad_set(p, name, True); p.wait_for_timeout(ms); pad_set(p, name, False); p.wait_for_timeout(120)


def spy(p, expr_name):
    """count calls of a global function or KNAV.move, without changing what it does"""
    if expr_name == "KNAV.move":
        p.evaluate("(()=>{window.__n={};const o=KNAV.move;KNAV.move=function(d){__n.mv=(__n.mv||0)+1;return o.call(this,d)};return 0})()")
    else:
        p.evaluate("(()=>{window.__n=window.__n||{};const o=%s;%s=function(){__n.%s=(__n.%s||0)+1;return o.apply(this,arguments)};return 0})()" % (expr_name, expr_name, expr_name, expr_name))


def count(p, name):
    return p.evaluate("(window.__n||{}).%s||0" % name)


def dev_open(p, sel):
    """Opzioni -> Sviluppatore -> the accordion holding sel -> click (real clicks)"""
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(%s)').open" % sel):
        p.click("details.acc:has(%s) > summary" % sel); p.wait_for_timeout(250)
    p.click(sel); p.wait_for_timeout(600)


def mutant_base():
    """the build with routing disabled (padAct returns at once), served on its own port"""
    d = tempfile.mkdtemp(prefix="hm1_mut_")
    body = open(os.path.join(ROOT, "index.html"), encoding="utf-8", newline="").read()
    assert body.count("function padAct(n,ph){") == 1
    body = body.replace("function padAct(n,ph){", "function padAct(n,ph){return;", 1)
    for rel in ("index.html", os.path.join("dev", "index.html")):
        os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
        open(os.path.join(d, rel), "w", encoding="utf-8", newline="").write(body)

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    port = 8796
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=d))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d/" % port, d


if MUT == "noroute":
    BASE, MUT_DIR = mutant_base()
    print("MUTANT build (routing disabled) at", BASE, flush=True)
elif MUT:
    raise SystemExit("unknown PAD_MUTATE=" + MUT)

srv = serve()
with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ A) menu: right moves the ring, A opens it
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    ring = "(document.querySelector('.kf')||{}).dataset&&document.querySelector('.kf').dataset.tile"
    press(p, "right")  # the first press only places the ring on the first tile
    first = p.evaluate(ring)
    second = first
    for d in ["right", "down", "left", "up"]:  # the layout decides which way has a neighbour: try each one
        if second != first:
            break
        press(p, d); second = p.evaluate(ring)
    check("A) the D-pad moves the focus ring to another tile", bool(second) and second != first, (first, second))
    press(p, "a"); p.wait_for_timeout(700)
    opened = p.evaluate("screen!=='menu'||!!(document.getElementById('modal')&&document.getElementById('modal').firstChild)")
    check("A) A opens the focused tile (a screen or a popup)", opened, p.evaluate("screen"))
    check("A) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ B) Opzioni: B returns to the menu
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    p.click("[data-tile=opt]"); p.wait_for_timeout(500)
    press(p, "b"); p.wait_for_timeout(400)
    check("B) B on Opzioni returns to the menu (Android-back path)", p.evaluate("screen") == "menu", p.evaluate("screen"))
    check("B) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ C) maze: left like ArrowLeft, Start pauses, down + A resumes
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    p.click("[data-tile=new]"); p.wait_for_timeout(700); pick_maze(p); p.wait_for_timeout(500)
    p.wait_for_function("typeof G==='object'&&G&&G.state==='play'", timeout=12000)
    press(p, "left")
    check("C) left sets the direction like ArrowLeft (G.pl.next = 3)", p.evaluate("G.pl.next") == 3, p.evaluate("G.pl.next"))
    press(p, "start"); p.wait_for_timeout(300)
    check("C) Start pauses: G.state 'pause' and the pause modal", p.evaluate("G.state") == "pause" and p.evaluate("!!document.getElementById('r')"), p.evaluate("G.state"))
    press(p, "down"); press(p, "a"); p.wait_for_timeout(400)
    check("C) down + A on Riprendi resumes the run", p.evaluate("G.state") == "play", p.evaluate("G.state"))
    check("C) no console errors (maze)", not errs, errs)
    ctx.close()

    # ============================================================ D) maze ability (girone 7 via the dev jump), B toggles Fermo
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    dev_open(p, "#jg7"); p.wait_for_function("typeof G==='object'&&G&&G.state==='play'", timeout=12000)
    p.wait_for_timeout(300)
    check("D) the ability is available (abilOn)", p.evaluate("abilOn()"))
    press(p, "a"); p.wait_for_timeout(300)
    check("D) A with the ability ready activates it (G.st.on)", p.evaluate("!!(G.st&&G.st.on)"), p.evaluate("G.st&&G.st.on"))
    press(p, "a"); p.wait_for_timeout(300)
    check("D) A again exits the ability (same as «basta ti prego»)", p.evaluate("!(G.st&&G.st.on)"), p.evaluate("G.st&&G.st.on"))
    press(p, "b"); p.wait_for_timeout(200)
    check("D) B toggles Fermo (G.still on)", p.evaluate("!!G.still"), p.evaluate("G.still"))
    press(p, "b"); p.wait_for_timeout(200)
    check("D) B again releases Fermo", not p.evaluate("!!G.still"), p.evaluate("G.still"))
    check("D) no console errors (ability)", not errs, errs)
    ctx.close()

    # ============================================================ E) Ferma: held right moves, release stops, A jumps, Start pauses
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    dev_open(p, "#mgfa"); p.wait_for_timeout(500)
    p.wait_for_function("typeof FA==='object'&&FA&&FA.state==='intro'", timeout=12000)
    press(p, "a"); p.wait_for_function("FA.state==='play'", timeout=6000)
    x0 = p.evaluate("FA.p.x")
    hold(p, "right", 500)
    x1 = p.evaluate("FA.p.x")
    check("E) right held moves the player (like ArrowRight)", x1 > x0 + 5, (x0, x1))
    check("E) release clears the key (FA_KEYS.r unset)", not p.evaluate("FA_KEYS.r"), p.evaluate("FA_KEYS.r"))
    p.wait_for_timeout(300)
    x2 = p.evaluate("FA.p.x"); p.wait_for_timeout(300); x3 = p.evaluate("FA.p.x")
    check("E) after release the player stops (no more horizontal movement)", x2 == x3, (x2, x3))
    press(p, "a", ms=40); p.wait_for_timeout(40)
    check("E) A jumps (player airborne or rising)", p.evaluate("!FA.p.onGround||FA.p.vy<0"), (p.evaluate("FA.p.onGround"), p.evaluate("FA.p.vy")))
    p.wait_for_timeout(900)
    press(p, "start"); p.wait_for_timeout(300)
    check("E) Start pauses Ferma (FA.paused + panel)", p.evaluate("FA.paused") and p.evaluate("document.getElementById('fapanel').classList.contains('on')"), p.evaluate("FA.paused"))
    press(p, "start"); p.wait_for_timeout(300)
    check("E) Start again resumes", not p.evaluate("FA.paused"), p.evaluate("FA.paused"))
    check("E) no console errors (Ferma)", not errs, errs)
    ctx.close()

    # ============================================================ F) Blackjack: A confirms, Start pauses
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    dev_open(p, "#mggam"); p.wait_for_timeout(900)
    check("F) El Gamblador table is up", p.evaluate("screen") == "bj", p.evaluate("screen"))
    press(p, "a"); press(p, "a"); p.wait_for_timeout(700)  # 0.5_3: the invite card is an overlay: A rings «Siediti», A seats the player
    spy(p, "bjConfirm")
    press(p, "a"); p.wait_for_timeout(200)
    check("F) A confirms the selection (bjConfirm)", count(p, "bjConfirm") >= 1, p.evaluate("window.__n"))
    press(p, "start"); p.wait_for_timeout(300)
    check("F) Start sets bjPauseT", p.evaluate("!!bjPauseT"), p.evaluate("bjPauseT"))
    check("F) no console errors (blackjack)", not errs, errs)
    ctx.close()

    # ============================================================ G) professor dialogue: A advances
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    dev_open(p, "#mgrow"); p.wait_for_timeout(1500)
    check("G) the professor test scene is up", p.evaluate("screen") == "pr", p.evaluate("screen"))
    spy(p, "prAdvance")
    press(p, "a"); p.wait_for_timeout(300)
    check("G) A advances the dialogue (prAdvance / prPick via Enter)", count(p, "prAdvance") >= 1, p.evaluate("window.__n"))
    check("G) no console errors (professor)", not errs, errs)
    ctx.close()

    # ============================================================ H) menu: down held 1 s moves the focus at least 3 times
    ctx, p, errs = page(b, site="stable", dev=False, toggle=False, extra_init=PAD)
    settle(p)
    spy(p, "KNAV.move")
    hold(p, "down", 1000)
    check("H) down held 1 s moves the focus at least 3 times (repeat after 400 ms, every 150 ms)", count(p, "mv") >= 3, count(p, "mv"))
    ctx.close()

    # ============================================================ I) «Prova controller» open: A does nothing else
    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details[data-acc=ctrl]').open"):
        p.click("details[data-acc=ctrl] > summary"); p.wait_for_timeout(300)
    spy(p, "KNAV.move")
    press(p, "right"); press(p, "a"); p.wait_for_timeout(300)
    check("I) with the Controller accordion open, the D-pad does not move the focus", count(p, "mv") == 0, count(p, "mv"))
    check("I) and A does nothing else (still on Opzioni, no popup)", p.evaluate("screen") == "opt" and not p.evaluate("!!(document.getElementById('modal')&&document.getElementById('modal').firstChild)"), p.evaluate("screen"))
    check("I) the test panel still logs the buttons", "tasto 15 premuto" in p.evaluate("(document.getElementById('ctrlLog')||{}).innerText||''"), p.evaluate("(document.getElementById('ctrlLog')||{}).innerText||''")[:120])
    check("I) no console errors (accordion)", not errs, errs)
    ctx.close()

    if MUT:
        print("MUTANT run done: A and C are expected to fail", flush=True)
        shutil.rmtree(MUT_DIR, ignore_errors=True)
srv.shutdown()
print("%d/%d checks passed" % (sum(RES), len(RES)), flush=True)
sys.exit(0 if all(RES) else 1)
