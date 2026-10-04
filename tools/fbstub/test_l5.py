#!/usr/bin/env python3
"""L5 headless tests (Firebase stub, never real credentials): player bug reports. The bug icon for a signed-in player
(BUG_PLAYERS), the privacy line (players only), the 5-per-day limit (mgs_bugday, players only, devs unlimited) and the
offline queue counting toward it. Serves the repo at / (stable). Run: python tools/fbstub/test_l5.py"""
import functools, http.server, json, os, sys, threading
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fbstub
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PORT = 8805
BASE = "http://127.0.0.1:%d/" % PORT
VIEW = {"width": 390, "height": 844}
RES = []
ERRS = []
USERS = dict(fbstub.USERS)
USERS["pippo"] = {"pw": "pw-pippo", "role": None}  # a plain player account (test only)
ALLOWED = sorted(["uid", "text", "screen", "version", "char", "ts", "ua", "meta"])


def check(name, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name, str(extra)[:300], flush=True)


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/dev/"):
            path = "/" + path[5:]
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


def page(b):
    ctx = b.new_context(viewport=VIEW)
    fbstub.install(ctx, users=dict(USERS), app="mgs")
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    ERRS.append(errs)
    return ctx, p, errs


def go(p):
    p.goto(BASE + "index.html"); p.wait_for_selector("#rsi")
    p.click("#rsi"); p.wait_for_timeout(700)


def acc_open(p):
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    p.click("details.acc[data-acc=account] > summary"); p.wait_for_timeout(200)


def login(p, name, pw):
    p.fill("#plu", name); p.fill("#plp", pw); p.click("#plk"); p.wait_for_timeout(600)


def has_bug(p):
    return p.evaluate("!!document.querySelector('#bugb')")


def popup(p):
    return p.evaluate("!!document.querySelector('#bgt')")


def send(p, text):
    """One real tap on the bug icon, a text, Invia. False if no popup opened (the daily limit)."""
    p.click("#bugb"); p.wait_for_timeout(250)
    if not popup(p):
        return False
    p.fill("#bgt", text); p.click("#bgk"); p.wait_for_timeout(700)
    return True


def bugs(p):
    return p.evaluate("window.__fbs.bugs||[]")


def ls(p, k):
    return p.evaluate("(()=>{try{return JSON.parse(localStorage.getItem(%s))}catch(e){return null}})()" % json.dumps(k))


def toast_text(p):
    return p.evaluate("document.body.innerText")


def main():
    with sync_playwright() as pw:
        b = launch_browser(pw)
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(H, directory=ROOT))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            # a) bug icon: signed-in player on every top bar, logged out none
            ctx, p, errs = page(b); go(p)
            check("a) logged out: no bug icon on the menu", not has_bug(p))
            acc_open(p); login(p, "pippo", "pw-pippo")
            check("a) signed-in player: the account is connected", p.evaluate("document.body.innerText.includes('Connesso come pippo')"))
            check("a) signed-in player: bug icon on Opzioni", has_bug(p))
            p.click("#back"); p.wait_for_timeout(300)
            check("a) signed-in player: bug icon on the menu", has_bug(p))
            check("a) no console errors", not errs, errs[:3])
            ctx.close()

            # b) player report: one write, allowed fields only, uid = the player's own, privacy line present
            ctx, p, errs = page(b); go(p); acc_open(p); login(p, "pippo", "pw-pippo")
            p.click("#bugb"); p.wait_for_timeout(250)
            check("c) player popup: privacy line above the text box", "Non scrivere dati personali: le segnalazioni sono pubbliche." in p.evaluate("(document.querySelector('.bugpriv')||{}).innerText||''"))
            p.keyboard.press("Escape"); p.wait_for_timeout(200)
            send(p, "il menu ha un problema")
            w = bugs(p)
            check("b) player report: exactly one bugs write", len(w) == 1, len(w))
            check("b) player report: only the allowed field set", w and sorted(w[0]) == ALLOWED, list(w[0]) if w else None)
            check("b) player report: uid is the player's own", w and w[0].get("uid") == "uid_pippo", w[0].get("uid") if w else None)
            ctx.close()

            # c) the privacy line is for players only: a developer's popup has none
            ctx, p, errs = page(b); go(p); acc_open(p); login(p, "master", "pw-master")
            check("c) developer is signed in", p.evaluate("document.body.innerText.includes('Connesso come master')") or has_bug(p), "")
            p.click("#bugb"); p.wait_for_timeout(250)
            check("c) developer popup: no privacy line", popup(p) and not p.evaluate("!!document.querySelector('.bugpriv')"))
            p.keyboard.press("Escape"); p.wait_for_timeout(200)

            # d) developer: 7 reports, no limit
            for i in range(7):
                send(p, "dev %d" % i)
            check("d) developer: 7 reports all sent (no daily limit)", len(bugs(p)) == 7, len(bugs(p)))
            ctx.close()

            # d) player: 5 ok, 6th toast and no popup, next day allowed again
            ctx, p, errs = page(b); go(p); acc_open(p); login(p, "pippo", "pw-pippo")
            sent = [send(p, "segnalazione %d" % i) for i in range(5)]
            check("d) 5 reports per day: all open and send", all(sent) and len(bugs(p)) == 5, (sent, len(bugs(p))))
            check("d) mgs_bugday counts 5 for today", (ls(p, "mgs_bugday") or {}).get("n") == 5, ls(p, "mgs_bugday"))
            opened = send(p, "la sesta")
            check("d) 6th: no popup opens", opened is False and not popup(p))
            check("d) 6th: the toast says so", "Hai già inviato 5 segnalazioni oggi: riprova domani." in toast_text(p))
            check("d) 6th: no write", len(bugs(p)) == 5, len(bugs(p)))
            p.evaluate("localStorage.setItem('mgs_bugday', JSON.stringify({day:'1999-01-01',n:5}))")  # yesterday's count
            p.wait_for_timeout(2500)  # the toast is short-lived
            opened = send(p, "il giorno dopo")
            check("d) next day: allowed again", opened and len(bugs(p)) == 6, len(bugs(p)))

            # e) offline: a queued report counts toward the 5 and is sent later
            p.evaluate("localStorage.setItem('mgs_bugday', JSON.stringify({day:'%s',n:4}))" % p.evaluate("(()=>{const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')})()"))
            ctx.set_offline(True); p.wait_for_timeout(200)
            opened = send(p, "senza rete")
            check("e) offline: the report is queued", opened and len(ls(p, "mgs_bugq") or []) == 1, ls(p, "mgs_bugq"))
            check("e) offline: the queued report counts (now 5 today)", (ls(p, "mgs_bugday") or {}).get("n") == 5, ls(p, "mgs_bugday"))
            ctx.set_offline(False); p.wait_for_timeout(200)
            p.evaluate("window.dispatchEvent(new Event('online'))"); p.wait_for_timeout(1500)
            check("e) back online: the queued report is sent", len(bugs(p)) == 7 and len(ls(p, "mgs_bugq") or []) == 0, (len(bugs(p)), ls(p, "mgs_bugq")))
            send(p, "sesta, oltre il limite")
            check("e) the 6th (after the queued one) is refused", not popup(p) and len(bugs(p)) == 7)
            check("e) no console errors", not errs, errs[:3])
            ctx.close()
        finally:
            srv.shutdown()
            b.close()
    print(sum(RES), "/", len(RES), "passed")
    return 0 if all(RES) else 1


if __name__ == "__main__":
    sys.exit(main())
