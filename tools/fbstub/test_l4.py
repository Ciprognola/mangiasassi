#!/usr/bin/env python3
"""L4 headless tests (Firebase stub, never real credentials): wrong-password counter (mgs_pwfail) and the account
deletion request (delreq/{name}) from the player login form. Serves the repo at / (stable) and /dev/ (dev site).
L4_MUTATE=threshold|extra serves a deliberately broken page (proves the checks bite; the working tree is never touched).
Run: python tools/fbstub/test_l4.py"""
import functools, http.server, json, os, sys, threading
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fbstub
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PORT = 8803
BASE = "http://127.0.0.1:%d/" % PORT
VIEW = {"width": 390, "height": 844}
RES = []
ERRS = []
MUT = os.environ.get("L4_MUTATE")
MUTATIONS = {
    "threshold": ("PL_DEL={after:5}", "PL_DEL={after:4}"),
    "extra": ("{ts:fb.Fs.serverTimestamp()}", "{ts:fb.Fs.serverTimestamp(),extra:1}"),
}
USERS = dict(fbstub.USERS)
USERS["pippo"] = {"pw": "pw-pippo", "role": None}  # a plain player account (test only)


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


def page(b, dev_site=False, **kw):
    ctx = b.new_context(viewport=VIEW)
    kw.setdefault("app", "mgs_dev" if dev_site else "mgs")
    kw.setdefault("users", dict(USERS))
    fbstub.install(ctx, **kw)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    ERRS.append(errs)
    return ctx, p, errs


def go(p, dev_site=False):
    p.goto(BASE + ("dev/" if dev_site else "") + "index.html"); p.wait_for_selector("#rsi")
    p.click("#rsi"); p.wait_for_timeout(700)


def acc_open(p):
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    sel = "details.acc[data-acc=account] > summary"
    p.click(sel); p.wait_for_timeout(200)


def fresh(b, dev_site=False, **kw):
    ctx, p, errs = page(b, dev_site, **kw)
    go(p, dev_site); acc_open(p)
    return ctx, p, errs


def login(p, name, pw):
    p.fill("#plu", name); p.fill("#plp", pw); p.click("#plk"); p.wait_for_timeout(350)


def fails(p, name, n, pw="wrong"):
    for _ in range(n):
        login(p, name, pw)


def LS(p, k):
    return p.evaluate("localStorage.getItem(%s)" % json.dumps(k))


def cnt(p, k):
    v = LS(p, k)
    return json.loads(v) if v else None


def seed(p, k, v):
    p.evaluate("localStorage.setItem(%s,%s)" % (json.dumps(k), json.dumps(json.dumps(v))))


def err(p):
    return p.evaluate("(document.querySelector('#ple')||{}).innerText||''")


def hint(p):
    return p.evaluate("(document.querySelector('#plhint')||{}).innerText||null")


def has_btn(p):
    return p.evaluate("!!document.querySelector('#pldel')")


def F(p, expr):
    return p.evaluate("(window.__fbs&&window.__fbs.%s)" % expr) or 0


def toast(p):
    p.wait_for_timeout(300)
    return p.evaluate("(document.querySelector('.toast')||{}).textContent||''")


def toast_clear(p):  # the toast queue holds one: wait until the previous message has gone
    p.wait_for_function("!document.querySelector('.toast')", timeout=8000)


def popup_open(p):
    return p.evaluate("!!document.getElementById('delpop')")


def ask(p):
    p.click("#pldel"); p.wait_for_timeout(200)


srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(H, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()

with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ a) threshold 5
    ctx, p, errs = fresh(b)
    fails(p, "pippo", 4)
    check("a) 4 wrong passwords: no deletion button", not has_btn(p) and hint(p) is None, hint(p))
    check("a) counter reads 4 after 4 wrong passwords", cnt(p, "mgs_pwfail") == {"pippo": 4}, cnt(p, "mgs_pwfail"))
    fails(p, "pippo", 1)
    check("a) the 5th wrong password shows the button with the name",
          has_btn(p) and "Hai dimenticato la password?" in (hint(p) or "") and "«pippo»" in (hint(p) or "") and "Chiedi la cancellazione" in (hint(p) or ""), hint(p))
    check("a) the login error stays the usual one", err(p) == "Utente o password errati.", err(p))
    check("a) counter reads 5 on the stable site key mgs_pwfail", cnt(p, "mgs_pwfail") == {"pippo": 5}, cnt(p, "mgs_pwfail"))
    check("a) no console errors", not errs, errs)
    ctx.close()

    ctx, p, errs = fresh(b, dev_site=True)
    fails(p, "pippo", 5)
    check("a) dev site: the counter lives in mgs_pwfail_dev", cnt(p, "mgs_pwfail_dev") == {"pippo": 5} and LS(p, "mgs_pwfail") is None, (LS(p, "mgs_pwfail_dev"), LS(p, "mgs_pwfail")))
    ctx.close()

    # ============================================================ b) per name
    ctx, p, errs = fresh(b)
    fails(p, "aaa", 3); fails(p, "bbb", 2)
    check("b) 3 wrong on aaa and 2 on bbb: no button", not has_btn(p), hint(p))
    check("b) counts kept per name", cnt(p, "mgs_pwfail") == {"aaa": 3, "bbb": 2}, cnt(p, "mgs_pwfail"))
    ctx.close()

    # ============================================================ c) successful sign-in clears
    ctx, p, errs = fresh(b)
    fails(p, "pippo", 5)
    seed(p, "mgs_delreq", {"pippo": 1700000000000})
    login(p, "pippo", "pw-pippo")
    check("c) successful sign-in: the name's counter is gone", "pippo" not in (cnt(p, "mgs_pwfail") or {}), cnt(p, "mgs_pwfail"))
    check("c) successful sign-in: the name's mgs_delreq entry is gone", "pippo" not in (cnt(p, "mgs_delreq") or {}), cnt(p, "mgs_delreq"))
    check("c) the player is signed in", p.evaluate("document.body.innerText.includes('Connesso come pippo')"))
    check("c) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ d) network and rate limit do not count
    ctx, p, errs = fresh(b)
    p.evaluate("window.__fbs.offline=true")
    fails(p, "pippo", 6)
    check("d) offline failures don't count", cnt(p, "mgs_pwfail") is None, cnt(p, "mgs_pwfail"))
    check("d) offline failures show the offline message", "sei offline" in err(p), err(p))
    p.evaluate("window.__fbs.offline=false; window.__fbs.tooMany=true")
    fails(p, "pippo", 6)
    check("d) too-many-requests doesn't count", cnt(p, "mgs_pwfail") is None, cnt(p, "mgs_pwfail"))
    check("d) too-many-requests keeps its own message", "Troppi tentativi" in err(p), err(p))
    check("d) no button after those failures", not has_btn(p))
    ctx.close()

    # ============================================================ e) reserved or invalid name
    ctx, p, errs = fresh(b)
    fails(p, "master", 6); fails(p, "ab", 6)
    check("e) reserved and invalid names: no counter", cnt(p, "mgs_pwfail") is None, cnt(p, "mgs_pwfail"))
    check("e) reserved and invalid names: never a button", not has_btn(p))
    ctx.close()

    # ============================================================ f) Conferma writes exactly delreq/{name} {ts}
    ctx, p, errs = fresh(b)
    fails(p, "pippo", 5)
    p.evaluate("persist()")
    s0 = p.evaluate("localStorage.getItem('mgs_v1')")
    si0 = F(p, "signIns")
    ask(p)
    check("f) the popup opens with title and name",
          p.evaluate("(document.getElementById('delpop')||{}).innerText||''").startswith("Cancellare l'account?") and "«pippo»" in p.evaluate("document.getElementById('delpop').innerText"))
    p.click("#dlok"); p.wait_for_timeout(500)
    w = p.evaluate("(window.__fbs.delreqWrites||[])")
    check("f) exactly one setDoc on delreq/pippo", len(w) == 1 and w[0]["id"] == "pippo", w)
    check("f) the write carries only ts = server timestamp", len(w) == 1 and list(w[0]["data"].keys()) == ["ts"] and w[0]["data"]["ts"] == {"__ts": True}, w)
    check("f) no sign-in call during the request", F(p, "signIns") == si0, (si0, F(p, "signIns")))
    check("f) toast: the request was sent", "Richiesta inviata: l'account verrà cancellato tra 7 giorni." in toast(p), "")
    check("f) the button becomes the sent line", not has_btn(p) and "Richiesta di cancellazione inviata il" in (hint(p) or ""), hint(p))
    check("f) mgs_delreq stores the name with a time", isinstance((cnt(p, "mgs_delreq") or {}).get("pippo"), int), cnt(p, "mgs_delreq"))
    check("f) the local save is byte-identical before and after the request", p.evaluate("localStorage.getItem('mgs_v1')") == s0)
    p.reload(); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(700); acc_open(p)
    login(p, "pippo", "wrong")
    check("f) after a reload the sent line is still there", "Richiesta di cancellazione inviata il" in (hint(p) or "") and not has_btn(p), hint(p))
    check("f) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ g) permission-denied and offline
    ctx, p, errs = fresh(b)
    fails(p, "pippo", 5)
    p.evaluate("window.__fbs.denyDelreq=true")
    ask(p); p.click("#dlok");
    check("g) permission-denied: «C'è già una richiesta in corso per questo nome.»", "C'è già una richiesta in corso per questo nome." in toast(p))
    check("g) permission-denied stores nothing", "pippo" not in (cnt(p, "mgs_delreq") or {}), cnt(p, "mgs_delreq"))
    p.evaluate("window.__fbs.denyDelreq=false; window.__fbs.offline=true")
    toast_clear(p)
    ask(p); p.click("#dlok")
    check("g) offline: the existing offline message", "sei offline" in toast(p))
    check("g) offline stores nothing", "pippo" not in (cnt(p, "mgs_delreq") or {}), cnt(p, "mgs_delreq"))
    check("g) the button is still there after a failed request", has_btn(p))
    ctx.close()

    # ============================================================ h) Annulla, Esc, Android back write nothing
    ctx, p, errs = fresh(b)
    fails(p, "pippo", 5)
    for name, act in [("Annulla", lambda: p.click("#dlno")), ("Esc", lambda: p.keyboard.press("Escape")), ("Android back", lambda: p.evaluate("window.dispatchEvent(new Event('mgback'))"))]:
        ask(p); act(); p.wait_for_timeout(300)
        nw = p.evaluate("(window.__fbs.delreqWrites||[]).length")
        check("h) %s closes the popup and writes nothing" % name, not popup_open(p) and nw == 0 and cnt(p, "mgs_delreq") is None, (popup_open(p), nw, cnt(p, "mgs_delreq")))
    check("h) the button is still there after cancelling", has_btn(p))
    ctx.close()

    # ============================================================ i) dev loginModal never touches the counter
    ctx, p, errs = fresh(b)
    for _ in range(5):
        p.click("#ver"); p.wait_for_timeout(100)
    p.fill("#lu", "pippo"); p.fill("#lp", "wrong")
    for _ in range(6):
        p.click("#lk"); p.wait_for_timeout(300)
    check("i) dev login: wrong passwords never touch mgs_pwfail", LS(p, "mgs_pwfail") is None and LS(p, "mgs_pwfail_dev") is None, (LS(p, "mgs_pwfail"), LS(p, "mgs_pwfail_dev")))
    ctx.close()

    # ============================================================ check for stray console errors
    check("no console errors on any page", all(not e for e in ERRS), [e for e in ERRS if e][:3])

    print("%d/%d checks passed" % (sum(RES), len(RES)), flush=True)
    b.close()

srv.shutdown()
sys.exit(0 if all(RES) else 1)
