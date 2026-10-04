#!/usr/bin/env python3
"""L2 headless tests (Firebase stub, never real credentials): player flags on + the 25-day account confirmation popup.
Serves the repo at / (stable) and /dev/ (dev site). L2_MUTATE=extra|threshold serves a deliberately broken page
(proves the checks bite; the working tree is never touched).
Run: python tools/fbstub/test_l2.py"""
import functools, http.server, json, os, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fbstub
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PORT = 8802
BASE = "http://127.0.0.1:%d/" % PORT
VIEW = {"width": 390, "height": 844}
RES = []
MUT = os.environ.get("L2_MUTATE")
MUTATIONS = {
    "extra": ("{confirmed:X.fb.Fs.serverTimestamp()}", "{confirmed:X.fb.Fs.serverTimestamp(),extra:1}"),
    "threshold": ("warn:25,del:30", "warn:24,del:30"),
}
DAY = 86400000


def check(name, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name, str(extra)[:300], flush=True)


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/dev/"):
            path = "/" + path[5:]
        if MUT and path == "/index.html":
            old, new = MUTATIONS[MUT]
            s = open(os.path.join(ROOT, "index.html"), encoding="utf-8", newline="").read().replace("\r\n", "\n")
            assert s.count(old) == 1, "mutation anchor"
            body = s.replace(old, new, 1).encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
            return
        self.path = path
        return super().do_GET()


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


def page(b, dev_site=False, dev_cache=None, player_cache=None, **kw):
    ctx = b.new_context(viewport=VIEW)
    init = ""
    sfx = "_dev" if dev_site else ""
    if dev_cache is not None:
        init += "localStorage.setItem('mgs_dev%s',%s);" % (sfx, json.dumps(json.dumps(dev_cache)))
    if player_cache is not None:
        init += "localStorage.setItem('mgs_player%s',%s);" % (sfx, json.dumps(json.dumps(player_cache)))
    if init:
        ctx.add_init_script(init)
    kw.setdefault("app", "mgs_dev" if dev_site else "mgs")
    fbstub.install(ctx, **kw)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    return ctx, p, errs


def go(p, dev_site=False, click=True):
    p.goto(BASE + ("dev/" if dev_site else "") + "index.html"); p.wait_for_selector("#rsi")
    if click:
        p.click("#rsi"); p.wait_for_timeout(700)


def F(p, expr):
    return p.evaluate("window.__fbs." + expr)


def pop(p):
    return p.evaluate("(document.querySelector('#plcpop')||{}).innerText||null")


def seeded(days, name="pippo"):
    now = time.time() * 1000
    return {"uid_" + name: {"username": name, "created": now - 40 * DAY, "confirmed": now - days * DAY}}


USERS = dict(fbstub.USERS); USERS["pippo"] = {"pw": "pw-pippo", "role": None}
PLAYER = {"acct": "pippo", "fb": True}


def player_page(b, days, dev_site=False, click=True, **kw):
    ctx, p, errs = page(b, dev_site, player_cache=PLAYER, users=dict(USERS), session="pippo", players=seeded(days), **kw)
    go(p, dev_site, click)
    return ctx, p, errs


srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(H, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()

with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ a) flags
    ctx, p, errs = page(b, users=dict(USERS)); go(p)
    f = p.evaluate("({pl:PLAYER_LOGIN,cs:CLOUD_SAVE,bp:BUG_PLAYERS})")
    check("a) PLAYER_LOGIN and CLOUD_SAVE true, BUG_PLAYERS false", f == {"pl": True, "cs": True, "bp": False}, f)
    check("a) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ b) stable, logged out
    ctx, p, errs = page(b, users=dict(USERS)); go(p)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    sel = "details.acc[data-acc=account] > summary"
    has = p.evaluate("!!document.querySelector('%s')" % sel)
    check("b) stable, logged out: the Account accordion is there", has)
    if has:
        p.click(sel); p.wait_for_timeout(200)
    t = p.evaluate("document.body.innerText")
    check("b) login form + «Non hai un account? Crealo» + the new help line",
          p.evaluate("!!document.querySelector('#plk')") and "Non hai un account? Crealo" in t and "Accedi con il tuo account, oppure creane uno qui sotto." in t, t[-300:])
    check("b) the old «El Cipro» help line is gone", "ti ha dato El Cipro" not in t)
    p.click("#plreg"); p.wait_for_timeout(150)
    check("b) «Crea account» is reachable", p.evaluate("document.querySelector('#plr')&&document.querySelector('#plr').innerText==='Crea account'"))
    check("b) no cloud UI (no #clst/#clsy/test toggle) while logged out", not p.evaluate("!!document.querySelector('#clst')||!!document.querySelector('#clsy')||!!document.querySelector('[data-clt]')"))
    check("b) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ c) player signed in: cloudOn, no test toggle
    for dev_site in (False, True):
        tag = "dev site" if dev_site else "stable"
        ctx, p, errs = player_page(b, 0, dev_site)
        p.click("[data-tile=opt]"); p.wait_for_timeout(300)
        p.click("details.acc[data-acc=account] > summary"); p.wait_for_timeout(300)
        check("c) %s, player signed in: cloudOn() true" % tag, p.evaluate("cloudOn()") is True)
        check("c) %s: cloud status line + «Sincronizza ora» shown, «Salvataggio cloud (test)» toggle not rendered" % tag,
              p.evaluate("!!document.querySelector('#clst')&&!!document.querySelector('#clsy')&&!document.querySelector('[data-clt]')&&!document.body.innerText.includes('Salvataggio cloud (test)')"))
        ctx.close()
    ctx, p, errs = page(b, True, player_cache=PLAYER, users=dict(USERS), session="pippo", players=seeded(0))
    ctx.add_init_script("localStorage.setItem('mgs_cloudtest_dev','true')")
    go(p, True)
    check("c) dev site: even with the old test key in storage the toggle stays hidden and cloudOn() stays true",
          p.evaluate("cloudOn()") is True and not p.evaluate("!!document.querySelector('[data-clt]')"))
    ctx.close()

    # ============================================================ d) the 25-day threshold
    for days, want in ((20, None), (24, None), (25, "entro 5 giorni"), (29, "entro domani"), (30, "entro oggi"), (31, "entro oggi")):
        ctx, p, errs = player_page(b, days + 0.01); p.wait_for_timeout(600)
        t = pop(p)
        if want is None:
            check("d) confirmed %d days ago: no popup" % days, t is None and p.evaluate("modalEl().firstChild===null"), t)
        else:
            check("d) confirmed %d days ago: popup «%s»" % (days, want),
                  t is not None and "Sei ancora dei nostri?" in t and "Conferma il tuo account " + want + ", altrimenti verrà cancellato insieme al salvataggio nel cloud." in t, t)
        check("d) %d days: no console errors" % days, not errs, errs)
        ctx.close()

    # ============================================================ e) once per open; waits while a run is on
    ctx, p, errs = player_page(b, 26, click=False); p.wait_for_timeout(800)
    check("e) on the splash (not a menu screen): nothing shown yet, but pending", pop(p) is None and p.evaluate("!!PLC.pend"))
    p.evaluate("screen='game';plConfirmPend()"); p.wait_for_timeout(1300)
    check("e) while a run is on: still nothing, even after the retry window", pop(p) is None and p.evaluate("!!PLC.pend"))
    p.evaluate("screen='menu';render()"); p.wait_for_timeout(300)
    check("e) back on a menu render: the popup appears", pop(p) is not None and "entro 4 giorni" in pop(p), pop(p))
    p.click("#plcl"); p.wait_for_timeout(200)
    p.evaluate("plVerify()"); p.wait_for_timeout(500); p.evaluate("render()"); p.wait_for_timeout(300)
    check("e) at most once per open: a later verify + render shows nothing", pop(p) is None)
    check("e) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ f) «Piu' tardi» / Esc
    ctx, p, errs = player_page(b, 27); p.wait_for_timeout(500)
    check("f) popup shown", pop(p) is not None)
    p.click("#plcl"); p.wait_for_timeout(200)
    check("f) «Più tardi»: closed, nothing written, guard released", pop(p) is None and not F(p, "playerUpdates") and p.evaluate("BUG===null"))
    ctx.close()
    ctx, p, errs = player_page(b, 27); p.wait_for_timeout(500)
    check("f) a fresh open (nothing was written) shows it again", pop(p) is not None)
    p.keyboard.press("Escape"); p.wait_for_timeout(200)
    check("f) Esc = «Più tardi»", pop(p) is None and not F(p, "playerUpdates") and p.evaluate("BUG===null"))
    ctx.close()
    ctx, p, errs = player_page(b, 27); p.wait_for_timeout(500)
    p.evaluate("window.dispatchEvent(new Event('mgback'))"); p.wait_for_timeout(200)
    check("f) Android back (mgback) = «Più tardi»", pop(p) is None and not F(p, "playerUpdates"))
    ctx.close()

    # ============================================================ g) «Confermo»
    ctx, p, errs = player_page(b, 28); p.wait_for_timeout(500)
    p.click("#plcy"); p.wait_for_timeout(500)
    up = F(p, "playerUpdates")
    check("g) one update, only {confirmed: server timestamp}", up == [{"id": "uid_pippo", "data": {"confirmed": {"__ts": True}}}], up)
    check("g) toast «Account confermato!», popup closed, guard released",
          "Account confermato!" in p.evaluate("(document.querySelector('#toasts')||{}).innerText||''") and pop(p) is None and p.evaluate("BUG===null"))
    age = p.evaluate("Date.now()") - F(p, "players.uid_pippo.confirmed")
    check("g) the doc is now confirmed «now»", age < 60000, age)
    p.evaluate("PLC.done=false;PLC.pend=null;plVerify()"); p.wait_for_timeout(600)
    check("g) the next open/verify finds a fresh confirmation: no popup", pop(p) is None)
    check("g) no console errors", not errs, errs)
    ctx.close()
    ctx, p, errs = player_page(b, 28, denyUpdate=True); p.wait_for_timeout(500)
    p.click("#plcy"); p.wait_for_timeout(500)
    tt = p.evaluate("(document.querySelector('#toasts')||{}).innerText||''")
    check("g) a refused update: error toast (existing generic message), popup closed, game still on the menu",
          "Operazione non riuscita" in tt and pop(p) is None and p.evaluate("screen")=="menu", tt)
    p.evaluate("PLC.done=false;PLC.pend=null;_plEns.clear();plVerify()"); p.wait_for_timeout(600)
    check("g) …and it comes back at the next open (nothing was confirmed)", pop(p) is not None)
    ctx.close()

    # ============================================================ h) dev sessions: no popup
    ctx, p, errs = page(b, users=dict(USERS), dev_cache={"role": "master", "acct": "master", "fb": True, "devOn": True}, player_cache={"acct": "master", "fb": True},
                        session="master", players=seeded(40, "master"))
    go(p); p.wait_for_timeout(500)
    p.evaluate("plVerify()"); p.wait_for_timeout(700)
    check("h) dev session (even with a stale playerAcct and an old players doc): no popup, players never read or written",
          pop(p) is None and not F(p, "playerReads") and not F(p, "playerWrites") and not F(p, "playerUpdates"))
    check("h) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ i) read fails / offline
    ctx, p, errs = player_page(b, 40, offline=True); p.wait_for_timeout(700)
    check("i) players read fails (offline stub): no popup, no error toast, the menu is there",
          pop(p) is None and p.evaluate("screen")=="menu" and p.evaluate("!!document.querySelector('[data-tile=opt]')") and "ancora dei nostri" not in p.evaluate("document.body.innerText"))
    check("i) no console errors", not errs, errs)
    ctx.close()

    b.close()

srv.shutdown()
ok = sum(RES); print("\n%d/%d" % (ok, len(RES)))
sys.exit(0 if ok == len(RES) else 1)
