#!/usr/bin/env python3
"""F1 headless tests with the Firebase stub (no real Firebase, no real credentials). Run: python tools/fbstub/test_f1.py"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "screens"))
import capture as C, fbstub
from playwright.sync_api import sync_playwright

RES = []


def check(name, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name, extra)


def page(b, **kw):
    ctx = b.new_context(viewport=C.VIEW, has_touch=True)
    cache = kw.pop("cache", None)
    if cache is not None:  # seeded once per tab session, so a reload keeps what the game wrote
        ctx.add_init_script("if(!sessionStorage.getItem('__seeded')){sessionStorage.setItem('__seeded','1');localStorage.setItem('mgs_dev',%s)}" % json.dumps(json.dumps(cache)))
    fbstub.install(ctx, **kw)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    return ctx, p, errs


def open_menu(p, url=None):
    p.goto(url or C.BASE + "index.html"); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(700)


def reveal(p):
    for _ in range(5):
        p.click("#ver"); p.wait_for_timeout(100)


def login(p, user, pw):
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); reveal(p)
    p.fill("#lu", user); p.fill("#lp", pw); p.click("#lk"); p.wait_for_timeout(700)


STATE = "({role:role,acct:acct,devOn:devOn,sim:S.sim,cache:localStorage.getItem('mgs_dev')})"
ERR = "document.querySelector('#le').innerText"
srv = C.serve()
with sync_playwright() as pw:
    b = pw.chromium.launch()
    # 1 master login (username is trimmed and lowercased)
    ctx, p, errs = page(b); open_menu(p); login(p, "Master ", "pw-master")
    s = p.evaluate(STATE); check("login master", s["role"] == "master" and s["acct"] == "master" and s["devOn"], s)
    p.click("[data-tile=opt]"); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    p.click("details.acc:has([data-sim]) > summary"); check("master sees Sblocca tutto", p.evaluate("!!document.querySelector('[data-sim]')"))
    p.reload(); p.wait_for_selector("#rsi"); s0 = p.evaluate(STATE); check("reload restores dev immediately from cache", s0["role"] == "master" and s0["devOn"], s0)
    p.click("#rsi"); p.wait_for_timeout(1200); s = p.evaluate(STATE); check("reload: background verify keeps session", s["role"] == "master" and s["devOn"], s)
    check("no console errors (login/reload)", not errs, errs)
    p.click("[data-tile=opt]"); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    p.click("details.acc:has(#lo) > summary"); p.wait_for_timeout(200)

    def cpw(o, n, r):
        p.fill("#cpo", o); p.fill("#cpn", n); p.fill("#cpr", r); p.click("#cpw"); p.wait_for_timeout(500)
        return p.evaluate("document.querySelector('#cpe').innerText")

    check("cambia pw: short", "6 caratteri" in cpw("pw-master", "abc", "abc"))
    check("cambia pw: mismatch", "coincidono" in cpw("pw-master", "abcdef", "abcdeg"))
    check("cambia pw: wrong current", "attuale" in cpw("wrong", "abcdef", "abcdef"))
    cpw("pw-master", "abcdef", "abcdef"); check("cambia pw: ok", p.evaluate("window.__fbs.pwSet") == 6)
    p.click("#lo"); p.wait_for_timeout(600)
    s = p.evaluate(STATE); check("Esci clears role, cache, dev, sim and signs out", s["role"] is None and not s["devOn"] and s["cache"] is None and not s["sim"] and p.evaluate("window.__fbs.signedOut") == 1, s)
    p.reload(); p.wait_for_selector("#rsi"); s = p.evaluate(STATE); check("after Esci, reload: dev off", s["role"] is None and not s["devOn"])
    ctx.close()
    # 2 dev3 behaves as dev1
    ctx, p, errs = page(b); open_menu(p); login(p, "dev3", "pw-dev3")
    s = p.evaluate(STATE); check("login dev3 -> role dev1, acct dev3", s["role"] == "dev1" and s["acct"] == "dev3" and s["devOn"], s)
    p.click("[data-tile=opt]"); p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    for a in ("test", "audio"):
        p.click(f"details.acc[data-acc={a}] > summary"); p.wait_for_timeout(150)
    check("dev3: no Sblocca tutto, no menu-music upload", p.evaluate("document.querySelectorAll('[data-sim],#mf').length") == 0)
    p.click("details.acc:has(#lo) > summary"); check("dev3 account line", "dev3" in p.evaluate("document.querySelector('[data-acc=account]').innerText"))
    ctx.close()
    # 3 errors
    ctx, p, errs = page(b); open_menu(p); p.click("[data-tile=opt]"); p.wait_for_timeout(300); reveal(p)
    for user, pw_, want in (("master", "nope", "errati"), ("norole", "pw-norole", "senza ruolo"), ("a@b", "x", "senza @"), ("", "", "Inserisci")):
        p.fill("#lu", user); p.fill("#lp", pw_); p.click("#lk"); p.wait_for_timeout(500)
        check(f"error '{want}'", want in p.evaluate(ERR), p.evaluate(ERR))
    p.evaluate("window.__fbs.tooMany=true"); p.fill("#lu", "master"); p.fill("#lp", "pw-master"); p.click("#lk"); p.wait_for_timeout(500)
    check("error too many attempts", "Troppi tentativi" in p.evaluate(ERR))
    p.evaluate("window.__fbs.tooMany=false;window.__fbs.offline=true"); p.click("#lk"); p.wait_for_timeout(500)
    check("error offline", "sei offline" in p.evaluate(ERR))
    p.keyboard.press("Escape"); p.wait_for_timeout(200); check("Esc closes the login", not p.evaluate("!!document.querySelector('#lu')"))
    check("role stays null after failures", p.evaluate(STATE)["role"] is None)
    ctx.close()
    # 4 stale local-login cache
    ctx, p, errs = page(b, cache={"role": "master", "devOn": True}); open_menu(p)
    s = p.evaluate(STATE); check("old local-login cache cleared", s["role"] is None and not s["devOn"] and s["cache"] is None, s)
    ctx.close()
    # 5 old save with creds: migrated, the rest loads
    ctx = b.new_context(viewport=C.VIEW); fbstub.install(ctx)
    ctx.add_init_script("if(!localStorage.getItem('mgs_v1'))localStorage.setItem('mgs_v1',JSON.stringify({creds:{master:{u:'m',p:'secret'}},p:{sordi:321}}))")
    p = ctx.new_page(); open_menu(p); p.evaluate("persist()")
    s = p.evaluate("({creds:!!S.creds,sordi:S.p.sordi,raw:localStorage.getItem('mgs_v1')})")
    check("old save: creds dropped, rest loads", not s["creds"] and s["sordi"] == 321 and "secret" not in s["raw"], s["sordi"])
    ctx.close()
    # 6 cached session, SDK blocked (offline) -> keeps dev mode
    ctx, p, errs = page(b, cache={"role": "dev1", "acct": "dev2", "fb": True, "devOn": True}, mode="block"); open_menu(p); p.wait_for_timeout(1500)
    s = p.evaluate(STATE); check("offline with cache keeps dev mode", s["role"] == "dev1" and s["acct"] == "dev2" and s["devOn"], s)
    ctx.close()
    # 7 cached session but Firebase has no user -> dropped
    ctx, p, errs = page(b, cache={"role": "master", "acct": "master", "fb": True, "devOn": True}); open_menu(p); p.wait_for_timeout(1500)
    s = p.evaluate(STATE); check("cache without a Firebase user is dropped", s["role"] is None and not s["devOn"] and s["cache"] is None, s)
    ctx.close()
    ctx, p, errs = page(b, cache={"role": "master", "acct": "master", "fb": True, "devOn": True}, session="master", users={"master": {"pw": "x", "role": None}}); open_menu(p); p.wait_for_timeout(1500)
    check("role removed in Firestore -> dropped", p.evaluate(STATE)["role"] is None); ctx.close()
    ctx, p, errs = page(b, cache={"role": "master", "acct": "master", "fb": True, "devOn": True}, session="dev3"); open_menu(p); p.wait_for_timeout(1500)
    s = p.evaluate(STATE); check("role changed (master -> dev3) is updated", s["role"] == "dev1" and s["acct"] == "dev3", s); ctx.close()
    # 8 SDK never answers: the menu is not delayed; login shows the offline message after the 8 s timeout
    ctx, p, errs = page(b, mode="hang", cache={"role": "master", "acct": "master", "fb": True, "devOn": True}); t0 = time.time(); open_menu(p)
    check("menu with a hanging SDK is immediate", time.time() - t0 < 4 and p.evaluate("screen") == "menu" and p.evaluate("role") == "master", round(time.time() - t0, 2))
    p.click("[data-tile=opt]"); p.wait_for_timeout(200); reveal(p)
    p.fill("#lu", "master"); p.fill("#lp", "pw-master"); p.click("#lk"); p.wait_for_timeout(9500)
    check("SDK timeout -> offline message", "sei offline" in p.evaluate(ERR), p.evaluate(ERR))
    check("no errors with a hanging SDK", not errs, errs); ctx.close()
    # 9 file:// build
    ctx = b.new_context(viewport=C.VIEW); fbstub.install(ctx); p = ctx.new_page()
    p.goto("file:///" + C.ROOT.replace("\\", "/") + "/index.html"); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(600)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300); reveal(p)
    check("file: shows 'solo dal sito'", "solo dal sito" in p.evaluate("document.querySelector('#modal').innerText") and not p.evaluate("!!document.querySelector('#lu')"))
    ctx.close()
    # 10 a run starts with a dev session
    ctx, p, errs = page(b, cache={"role": "master", "acct": "master", "fb": True, "devOn": True}, session="master"); open_menu(p)
    p.click("[data-tile=new]"); p.wait_for_timeout(1500); check("a run starts", p.evaluate("screen") == "game")
    check("no console errors (run)", not errs, errs); ctx.close()
    b.close()
srv.shutdown()
print(sum(RES), "/", len(RES), "passed"); sys.exit(0 if all(RES) else 1)
