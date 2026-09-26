#!/usr/bin/env python3
"""F2a headless tests (Firebase stub): player login, PLAYER_LOGIN flag off.
Run: python tools/fbstub/test_f2a.py"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "screens"))
import capture as C, fbstub
from playwright.sync_api import sync_playwright

RES = []


def check(name, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name, extra, flush=True)


def launch_browser(pw):
    try:
        return pw.chromium.launch()
    except Exception:
        import glob
        base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
        cands = glob.glob(os.path.join(base, "chromium-*", "chrome-linux", "chrome")) if base else []
        if cands:
            return pw.chromium.launch(executable_path=cands[0])
        raise


def page(b, dev_cache=None, player_cache=None, has_touch=False, **kw):
    ctx = b.new_context(viewport=C.VIEW, has_touch=has_touch)
    init = ""
    if dev_cache is not None:
        init += "if(!sessionStorage.getItem('__seeded_dev')){sessionStorage.setItem('__seeded_dev','1');localStorage.setItem('mgs_dev',%s)}" % json.dumps(json.dumps(dev_cache))
    if player_cache is not None:
        init += "if(!sessionStorage.getItem('__seeded_pl')){sessionStorage.setItem('__seeded_pl','1');localStorage.setItem('mgs_player',%s)}" % json.dumps(json.dumps(player_cache))
    if init:
        ctx.add_init_script(init)
    fbstub.install(ctx, **kw)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    return ctx, p, errs


def menu(p):
    p.goto(C.BASE + "index.html"); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(700)


def reveal(p, touch=False):
    for _ in range(5):
        (p.tap if touch else p.click)("#ver"); p.wait_for_timeout(100)


def go_options(p, touch=False):
    (p.tap if touch else p.click)("[data-tile=opt]"); p.wait_for_timeout(300)


def open_account_acc(p, touch=False):
    """Opzioni -> Generali -> the Account accordion, if it's there."""
    go_options(p, touch)
    sel = "details.acc[data-acc=account] > summary"
    if not p.evaluate("!!document.querySelector('%s')" % sel):
        return False
    (p.tap if touch else p.click)(sel); p.wait_for_timeout(200)
    return True


DEV_MASTER_ON = {"role": "master", "acct": "master", "fb": True, "devOn": True}
STATE = "({playerAcct,role,devOn,cache:localStorage.getItem('mgs_player')})"
PLE = "document.querySelector('#ple') ? document.querySelector('#ple').innerText : null"

srv = C.serve()
with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ flag off: no Account UI for a logged-out user or a plain player
    ctx, p, errs = page(b, dev=False); menu(p)
    go_options(p)
    check("logged out, no dev session: no Account accordion at all", not p.evaluate("!!document.querySelector('details.acc[data-acc=account]')"))
    check("no console errors (logged out)", not errs, errs)
    ctx.close()

    # ============================================================ dev in dev mode: Account IS visible (so the feature can be tested)
    ctx, p, errs = page(b, dev_cache=DEV_MASTER_ON, session="master"); menu(p); p.wait_for_timeout(300)
    check("dev in dev mode: Account accordion visible in Generali", open_account_acc(p))
    check("dev in dev mode: shows the logged-out player login form (#plu/#plp/#plk)", p.evaluate("!!document.querySelector('#plu') && !!document.querySelector('#plp') && !!document.querySelector('#plk')"))
    check("no console errors (dev sees Account)", not errs, errs)
    ctx.close()

    # ============================================================ player login / logout / Cambia password
    ctx, p, errs = page(b, dev_cache=DEV_MASTER_ON, session="master"); menu(p); p.wait_for_timeout(300)
    open_account_acc(p)
    p.fill("#plu", "norole"); p.fill("#plp", "pw-norole"); p.click("#plk"); p.wait_for_timeout(600)
    s = p.evaluate(STATE)
    check("player login: playerAcct set, role/devOn (the dev's own) untouched", s["playerAcct"] == "norole" and s["role"] == "master" and s["devOn"] and s["cache"] is not None, s)
    check("player login: UI switches to 'Connesso come norole' + Esci", "norole" in p.evaluate("document.body.innerText") and p.evaluate("!!document.querySelector('#plo')"))
    check("player login: Cambia password fields present (F1's #cpo/#cpn/#cpr/#cpe/#cpw reused)", p.evaluate("!!document.querySelector('#cpo') && !!document.querySelector('#cpw')"))
    # Cambia password actually works through the reused fbChangePw()
    p.fill("#cpo", "pw-norole"); p.fill("#cpn", "abcdef"); p.fill("#cpr", "abcdef"); p.click("#cpw"); p.wait_for_timeout(500)
    check("player Cambia password: reuses fbChangePw() for real", p.evaluate("window.__fbs.pwSet") == 6)
    p.click("#plo"); p.wait_for_timeout(300)
    s2 = p.evaluate(STATE)
    check("player logout: playerAcct cleared, dev session (role) untouched", s2["playerAcct"] is None and s2["role"] == "master" and s2["cache"] is None, s2)
    check("no console errors (login/logout/cambia password)", not errs, errs)
    ctx.close()

    # ============================================================ wrong credentials -> clear Italian error, nothing set
    ctx, p, errs = page(b, dev_cache=DEV_MASTER_ON, session="master"); menu(p); p.wait_for_timeout(300)
    open_account_acc(p)
    p.fill("#plu", "norole"); p.fill("#plp", "nope"); p.click("#plk"); p.wait_for_timeout(500)
    check("wrong password: clear Italian error, no session set", "errati" in (p.evaluate(PLE) or "") and p.evaluate(STATE)["playerAcct"] is None, p.evaluate(PLE))
    check("no console errors (wrong credentials)", not errs, errs)
    ctx.close()

    # ============================================================ offline -> clear error, the game still starts normally
    ctx, p, errs = page(b, dev_cache=DEV_MASTER_ON, session="master", offline=True); menu(p); p.wait_for_timeout(300)
    check("offline: menu still renders / a run still starts", p.evaluate("screen") == "menu")
    open_account_acc(p)
    p.fill("#plu", "norole"); p.fill("#plp", "pw-norole"); p.click("#plk"); p.wait_for_timeout(600)
    check("offline: clear 'sei offline' error on player login attempt", "sei offline" in (p.evaluate(PLE) or ""), p.evaluate(PLE))
    p.click("#back"); p.click("[data-tile=new]"); p.wait_for_timeout(1200)
    check("offline: a real run still starts fine", p.evaluate("screen") == "game")
    check("no console errors (offline)", not errs, errs)
    ctx.close()

    # ============================================================ a logged-in player never gets dev controls, no bug icon, canReport() false
    ctx, p, errs = page(b, player_cache={"acct": "norole", "fb": True}, session="norole", users={"norole": {"pw": "pw-norole", "role": None}}); menu(p); p.wait_for_timeout(1000)
    st = p.evaluate("({playerAcct,role,devOn,devUI:devUI(),canReport:canReport(),bugPlayerSession:bugPlayerSession(),sim:SIM()})")
    check("restored player session: playerAcct set from cache, no role/devOn/dev-UI/SIM", st["playerAcct"] == "norole" and st["role"] is None and not st["devOn"] and not st["devUI"] and not st["sim"], st)
    check("a logged-in player: bugPlayerSession() true, but canReport() stays false (BUG_PLAYERS still off)", st["bugPlayerSession"] is True and st["canReport"] is False, st)
    check("a logged-in player: no bug icon anywhere", not p.evaluate("!!document.querySelector('#bugb')"))
    go_options(p)
    check("a logged-in player: no Sviluppatore tab, no Account accordion either (PLAYER_LOGIN off and not a dev)", not p.evaluate("!!document.querySelector('[data-otab=dev]')") and not p.evaluate("!!document.querySelector('details.acc[data-acc=account]')"))
    check("no console errors (player has no dev reach)", not errs, errs)
    ctx.close()

    # ============================================================ session restored on reload, dropped when the stub user disappears
    ctx, p, errs = page(b, player_cache={"acct": "norole", "fb": True}, session="norole", users={"norole": {"pw": "pw-norole", "role": None}}); menu(p); p.wait_for_timeout(1000)
    check("player session restored immediately from cache (no wait for network)", p.evaluate("playerAcct") == "norole")
    p.reload(); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(1000)
    check("player session survives a reload", p.evaluate("playerAcct") == "norole")
    check("no console errors (restore/reload)", not errs, errs)
    ctx.close()
    # cached player session but the stub has no signed-in user at all -> dropped in the background
    ctx, p, errs = page(b, player_cache={"acct": "norole", "fb": True}); menu(p); p.wait_for_timeout(1200)
    check("cached player session without a Firebase user is dropped", p.evaluate("playerAcct") is None and p.evaluate("localStorage.getItem('mgs_player')") is None)
    check("no console errors (dropped session)", not errs, errs)
    ctx.close()

    # ============================================================ mobile touch: full login/logout flow
    ctx, p, errs = page(b, dev_cache=DEV_MASTER_ON, session="master", has_touch=True); menu(p); p.wait_for_timeout(300)
    check("touch: Account accordion opens", open_account_acc(p, touch=True))
    p.fill("#plu", "norole"); p.fill("#plp", "pw-norole"); p.tap("#plk"); p.wait_for_timeout(600)
    check("touch: player login works", p.evaluate("playerAcct") == "norole")
    p.tap("#plo"); p.wait_for_timeout(300)
    check("touch: player logout works", p.evaluate("playerAcct") is None)
    check("no console errors (touch)", not errs, errs)
    ctx.close()

    # ============================================================ wipeData drops any player session too
    ctx, p, errs = page(b, player_cache={"acct": "norole", "fb": True}, session="norole", users={"norole": {"pw": "pw-norole", "role": None}}); menu(p); p.wait_for_timeout(1000)
    p.evaluate("go('opt')"); p.wait_for_timeout(200)
    p.evaluate("wipeData()"); p.wait_for_timeout(600)
    check("wipeData() also drops the player session", p.evaluate("playerAcct") is None and p.evaluate("localStorage.getItem('mgs_player')") is None)
    check("no console errors (wipeData)", not errs, errs)
    ctx.close()

    # ============================================================ smoke
    ctx, p, errs = page(b, dev=False); menu(p)
    check("smoke: menu renders", p.evaluate("screen") == "menu")
    p.click("[data-tile=new]"); p.wait_for_timeout(1500)
    check("smoke: a run starts", p.evaluate("screen") == "game")
    check("no console errors (smoke)", not errs, errs)
    ctx.close()

    b.close()
srv.shutdown()

# ------------------------------------------------------------ node --check on every script block
import re, subprocess
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
WORK = "/tmp/f2a_test"
os.makedirs(WORK, exist_ok=True)
h = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
blocks = re.findall(r"<script[^>]*>([\s\S]*?)</script>", h)
nodeok = True
for i, blk in enumerate(blocks):
    fp = os.path.join(WORK, "s%d.js" % i)
    open(fp, "w", encoding="utf-8").write(blk)
    r = subprocess.run(["node", "--check", fp], capture_output=True, text=True)
    if r.returncode != 0:
        nodeok = False; print(r.stderr)
check("node --check passes on every <script> block", nodeok)

print(sum(RES), "/", len(RES), "passed")
sys.exit(0 if all(RES) else 1)
