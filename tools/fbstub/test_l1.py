#!/usr/bin/env python3
"""L1 headless tests (Firebase stub, never real credentials): player registration, username rules, players/{uid} + repair at login.
Serves the repo at / (stable) and /dev/ (dev site: Firebase app name mgs_dev, keys with _dev).
L1_MUTATE=reserved|fields serves a deliberately broken page (proves the checks bite; the working tree is never touched).
Run: python tools/fbstub/test_l1.py"""
import functools, http.server, json, os, re, subprocess, sys, threading
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fbstub
from gp import pick_maze
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PORT = 8801
BASE = "http://127.0.0.1:%d/" % PORT
VIEW = {"width": 390, "height": 844}
RES = []
MUT = os.environ.get("L1_MUTATE")
MUTATIONS = {
    "reserved": ('if(PL_RESERVED.includes(u))return"Questo nome è riservato.";', ""),
    "fields": ("{username:name,created:fb.Fs.serverTimestamp(),confirmed:fb.Fs.serverTimestamp()}",
               "{username:name,created:fb.Fs.serverTimestamp(),confirmed:fb.Fs.serverTimestamp(),extra:1}"),
}
RESERVED = ["master", "dev1", "dev2", "dev3", "dev4", "dev5", "admin", "algidone", "gamblador", "professore", "mrstone", "usagi"]


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


def page(b, dev_site=True, dev_cache=None, player_cache=None, **kw):
    ctx = b.new_context(viewport=VIEW)
    init = ""
    sfx = "_dev" if dev_site else ""
    if dev_cache is not None:
        init += "if(!sessionStorage.getItem('__sd')){sessionStorage.setItem('__sd','1');localStorage.setItem('mgs_dev%s',%s)}" % (sfx, json.dumps(json.dumps(dev_cache)))
    if player_cache is not None:
        init += "if(!sessionStorage.getItem('__sp')){sessionStorage.setItem('__sp','1');localStorage.setItem('mgs_player%s',%s)}" % (sfx, json.dumps(json.dumps(player_cache)))
    if init:
        ctx.add_init_script(init)
    kw.setdefault("app", "mgs_dev" if dev_site else "mgs")
    fbstub.install(ctx, **kw)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    return ctx, p, errs


def menu(p, dev_site=True):
    p.goto(BASE + ("dev/" if dev_site else "") + "index.html"); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(700)


def acc_open(p):
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    sel = "details.acc[data-acc=account] > summary"
    if not p.evaluate("!!document.querySelector('%s')" % sel):
        return False
    p.click(sel); p.wait_for_timeout(200)
    return True


def reg(p, name, pw, pw2=None):
    if not p.evaluate("!!document.querySelector('#plp2')"):
        p.click("#plreg"); p.wait_for_timeout(150)
    p.fill("#plu", name); p.fill("#plp", pw); p.fill("#plp2", pw if pw2 is None else pw2); p.click("#plr")


def F(p, expr):
    return p.evaluate("window.__fbs." + expr)


ERR = "(document.querySelector('#ple')||{}).innerText||null"
USERS = dict(fbstub.USERS)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(H, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()

with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ a) plNameCheck
    ctx, p, errs = page(b, dev_site=False); menu(p, False)
    r = p.evaluate("""(()=>{const c=plNameCheck;return{
      ok:c("Ab_c"),okUp:c("AB_C"),okTrim:c("  abc  "),okDash:c("a-b"),max16:c("a".repeat(16)),
      s2:c("ab"),s17:c("a".repeat(17)),empty:c(""),nul:c(null),sp:c("a b"),agrave:c("à"),agrave3:c("àbc"),dot:c("a.b"),at:c("a@b"),
      res:${R}.map(n=>[c(n),c(n.toUpperCase())])}})()""".replace("${R}", json.dumps(RESERVED)))
    LEN, CH, RS = "Il nome deve avere da 3 a 16 caratteri.", "Solo lettere a–z, numeri, _ e -.", "Questo nome è riservato."
    check("a) plNameCheck: 'Ab_c' / 'AB_C' / trimmed / 'a-b' / 16 chars are valid (null)", r["ok"] is None and r["okUp"] is None and r["okTrim"] is None and r["okDash"] is None and r["max16"] is None, r)
    check("a) 2 and 17 characters, empty, null → length message", r["s2"] == LEN and r["s17"] == LEN and r["empty"] == LEN and r["nul"] == LEN, r)
    check("a) 'a b', 'àbc', 'a.b', 'a@b' → charset message; 'à' (1 char) rejected", r["sp"] == CH and r["agrave3"] == CH and r["dot"] == CH and r["at"] == CH and r["agrave"] == LEN, r)
    check("a) every reserved name (lower and UPPER case) → reserved message", all(x[0] == RS and x[1] == RS for x in r["res"]), r["res"])
    check("a) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ b) success + g) dev-site visibility
    ctx, p, errs = page(b, users=dict(USERS)); menu(p)
    check("g) dev site, logged out: Account accordion is there", acc_open(p))
    check("g) …with the login form (#plu/#plp/#plk) and the link «Non hai un account? Crealo»",
          p.evaluate("!!document.querySelector('#plu')&&!!document.querySelector('#plp')&&!!document.querySelector('#plk')&&document.querySelector('#plreg').innerText.includes('Non hai un account? Crealo')"))
    p.click("#plreg"); p.wait_for_timeout(150)
    check("g) the link swaps to the registration form (Nome utente / Password / Ripeti password, «Crea account», «Ho già un account»)",
          p.evaluate("!!document.querySelector('#plu')&&!!document.querySelector('#plp')&&!!document.querySelector('#plp2')&&document.querySelector('#plr').innerText==='Crea account'&&document.querySelector('#plback').innerText==='Ho già un account'&&!document.querySelector('#plk')"))
    check("g) the no-recovery warning line is shown", "Niente email: se dimentichi la password non si può recuperare. Annotala!" in p.evaluate("document.body.innerText"))
    p.click("#plback"); p.wait_for_timeout(150)
    check("g) «Ho già un account» goes back to the login form", p.evaluate("!!document.querySelector('#plk')&&!document.querySelector('#plp2')"))
    reg(p, "Ciao_Bello", "segreto1")
    p.wait_for_function("playerAcct==='ciao_bello'", timeout=5000); p.wait_for_timeout(300)
    check("b) createUser called once with '<lowercased name>@mangiasassi.invalid'", F(p, "createCalls") == ["ciao_bello@mangiasassi.invalid"], F(p, "createCalls"))
    w = F(p, "playerWrites")
    check("b) players/{uid} written once with exactly username/created/confirmed (server timestamps)",
          len(w or []) == 1 and w[0]["id"] == "uid_ciao_bello" and sorted(w[0]["data"].keys()) == ["confirmed", "created", "username"] and w[0]["data"]["username"] == "ciao_bello"
          and w[0]["data"]["created"] == {"__ts": True} and w[0]["data"]["confirmed"] == {"__ts": True}, w)
    check("b) the stub accepted the doc (rule-shaped)", "uid_ciao_bello" in (F(p, "players") or {}))
    st = p.evaluate("({a:playerAcct,c:localStorage.getItem('mgs_player_dev'),role,devOn})")
    check("b) player session set and persisted (mgs_player_dev), no dev role", st["a"] == "ciao_bello" and st["c"] and json.loads(st["c"])["acct"] == "ciao_bello" and st["role"] is None and not st["devOn"], st)
    check("b) toast «Benvenuto, ciao_bello!» shown", "Benvenuto, ciao_bello!" in p.evaluate("(document.querySelector('#toasts')||{}).innerText||''"))
    check("b) account body now «Connesso come ciao_bello»", "Connesso come ciao_bello" in p.evaluate("document.body.innerText"))
    check("b) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ c) name taken
    u = dict(USERS); u["preso"] = {"pw": "x12345", "role": None}
    ctx, p, errs = page(b, users=u); menu(p); acc_open(p)
    reg(p, "preso", "segreto1")
    p.wait_for_function("(document.querySelector('#ple')||{}).innerText==='Nome già preso.'", timeout=5000)
    st = p.evaluate("({a:playerAcct,c:localStorage.getItem('mgs_player_dev'),dis:document.querySelector('#plr').disabled})")
    check("c) email-already-in-use → «Nome già preso.», button re-enabled, no session, nothing persisted", st["a"] is None and st["c"] is None and st["dis"] is False, st)
    check("c) no profile write attempted", not F(p, "playerWrites"))
    check("c) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ d) client-side validation: no Firebase call
    ctx, p, errs = page(b, users=dict(USERS)); menu(p); acc_open(p)
    reg(p, "abcd", "12345"); p.wait_for_timeout(200)
    e1 = p.evaluate(ERR)
    reg(p, "abcd", "123456", "654321"); p.wait_for_timeout(200)
    e2 = p.evaluate(ERR)
    reg(p, "dev1", "123456"); p.wait_for_timeout(200)
    e3 = p.evaluate(ERR)
    reg(p, "ab", "123456"); p.wait_for_timeout(200)
    e4 = p.evaluate(ERR)
    check("d) short password → «La password deve avere almeno 6 caratteri.»", e1 == "La password deve avere almeno 6 caratteri.", e1)
    check("d) mismatch → «Le password non coincidono.»", e2 == "Le password non coincidono.", e2)
    check("d) reserved / too-short name → the plNameCheck messages", e3 == RS and e4 == LEN, (e3, e4))
    check("d) none of them reached Firebase (no createUser, no profile write, SDK not even loaded)", not F(p, "createCalls") and not F(p, "playerWrites") and p.evaluate("_fb===null"))
    check("d) the button is still enabled", p.evaluate("!document.querySelector('#plr').disabled"))
    check("d) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ e) profile write fails → session kept; repaired later, exactly once
    ctx, p, errs = page(b, users=dict(USERS), denyPlayers=True); menu(p); acc_open(p)
    reg(p, "ritardo", "segreto1")
    p.wait_for_function("playerAcct==='ritardo'", timeout=5000); p.wait_for_timeout(500)
    check("e) players write refused: the session is kept (playerAcct set, persisted), toast shown, no error text", p.evaluate("playerAcct")=="ritardo" and p.evaluate("localStorage.getItem('mgs_player_dev')") is not None
          and "Benvenuto, ritardo!" in p.evaluate("(document.querySelector('#toasts')||{}).innerText||''"))
    check("e) …and no profile exists yet", not F(p, "players"))
    p.evaluate("window.__fbs.denyPlayers=false")
    p.evaluate("plVerify()"); p.wait_for_timeout(600)
    n1 = len(F(p, "playerWrites")); pl = F(p, "players")
    check("e) the next plVerify creates players/{uid}", list((pl or {}).keys()) == ["uid_ritardo"], pl)
    p.evaluate("plVerify()"); p.wait_for_timeout(500)
    p.evaluate("plVerify()"); p.wait_for_timeout(500)
    check("e) further verifications write nothing more (exactly once)", len(F(p, "playerWrites")) == n1, (n1, len(F(p, "playerWrites"))))
    check("e) no console errors", not errs, errs)
    ctx.close()
    # …and through a normal login: an account with no profile gets it created at sign-in
    u = dict(USERS); u["tardi"] = {"pw": "pw-tardi", "role": None}
    ctx, p, errs = page(b, users=u); menu(p); acc_open(p)
    p.fill("#plu", "tardi"); p.fill("#plp", "pw-tardi"); p.click("#plk")
    p.wait_for_function("playerAcct==='tardi'", timeout=5000); p.wait_for_timeout(600)
    w = F(p, "playerWrites")
    check("e) a login without a profile creates it once (username from the account's name)", len(w or []) == 1 and w[0]["data"]["username"] == "tardi" and "uid_tardi" in (F(p, "players") or {}), w)
    check("e) the login form still behaves (session set, no error)", p.evaluate("playerAcct")=="tardi" and p.evaluate(ERR) is None)
    p.evaluate("plVerify()"); p.wait_for_timeout(500)
    check("e) a verify afterwards finds it and writes nothing", len(F(p, "playerWrites")) == 1)
    check("e) no console errors", not errs, errs)
    ctx.close()

    # ============================================================ f) dev accounts / invalid console names
    ctx, p, errs = page(b, users=dict(USERS)); menu(p); acc_open(p)
    p.fill("#plu", "master"); p.fill("#plp", "pw-master"); p.click("#plk")
    p.wait_for_function("role==='master'", timeout=5000); p.wait_for_timeout(600)
    check("f) a dev signing in through the player form: role set, no playerAcct", p.evaluate("role")=="master" and p.evaluate("playerAcct") is None)
    check("f) …and players is never read or written", not F(p, "playerReads") and not F(p, "playerWrites"))
    ctx.close()
    ctx, p, errs = page(b, users=dict(USERS), dev_cache={"role": "master", "acct": "master", "fb": True, "devOn": True}, player_cache={"acct": "master", "fb": True}, session="master"); menu(p); p.wait_for_timeout(500)
    p.evaluate("plVerify()"); p.wait_for_timeout(700)
    check("f) plVerify over a dev's Firebase session (stale playerAcct): players never read or written", not F(p, "playerReads") and not F(p, "playerWrites"))
    ctx.close()
    u = dict(USERS); u["admin"] = {"pw": "pw-admin", "role": None}; u["ab"] = {"pw": "pw-ab", "role": None}
    ctx, p, errs = page(b, users=u); menu(p); acc_open(p)
    p.fill("#plu", "admin"); p.fill("#plp", "pw-admin"); p.click("#plk")
    p.wait_for_function("playerAcct==='admin'", timeout=5000); p.wait_for_timeout(600)
    check("f) a console account named «admin» (reserved): signs in as before, no players write", not F(p, "playerWrites") and not F(p, "playerReads"))
    p.evaluate("plVerify()"); p.wait_for_timeout(400)
    check("f) …also after a verify", not F(p, "playerWrites"))
    ctx.close()
    ctx, p, errs = page(b, users=u); menu(p); acc_open(p)
    p.fill("#plu", "ab"); p.fill("#plp", "pw-ab"); p.click("#plk")
    p.wait_for_function("playerAcct==='ab'", timeout=5000); p.wait_for_timeout(600)
    check("f) a console account with a too-short name: no players write", not F(p, "playerWrites") and not F(p, "playerReads"))
    ctx.close()

    # ============================================================ g) stable site, flag off
    ctx, p, errs = page(b, dev_site=False, users=dict(USERS)); menu(p, False)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    check("g) stable, PLAYER_LOGIN off, logged out: no Account accordion (unchanged)", not p.evaluate("!!document.querySelector('details.acc[data-acc=account]')") and not p.evaluate("!!document.querySelector('#plreg')"))
    check("g) …and plAccountHTML() is not reachable from the UI: SDK never loaded", p.evaluate("_fb===null"))
    check("g) no console errors", not errs, errs)
    ctx.close()
    ctx, p, errs = page(b, users=dict(USERS), dev_cache={"role": "master", "acct": "master", "fb": True, "devOn": False}, session="master"); menu(p); p.wait_for_timeout(400)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    check("g) dev site, a dev with dev mode OFF: no Account accordion (as before)", not p.evaluate("!!document.querySelector('details.acc[data-acc=account]')"))
    ctx.close()

    # ============================================================ h) rules file
    rules = open(os.path.join(ROOT, "firestore.rules"), encoding="utf-8").read()
    m = re.search(r"function reserved\(\) \{\s*return \[([^\]]*)\];", rules)
    rr = re.findall(r"'([^']+)'", m.group(1)) if m else None
    ctx, p, errs = page(b, dev_site=False); menu(p, False)
    jr = p.evaluate("PL_RESERVED"); jre = p.evaluate("PL_NAME_RE.source")
    ctx.close()
    check("h) PL_RESERVED equals reserved() in firestore.rules (same names, same order)", rr == jr == RESERVED, (rr, jr))
    mm = re.search(r"u\.matches\('([^']+)'\)", rules)
    check("h) PL_NAME_RE equals the rules' validName() pattern", bool(mm) and mm.group(1) == jre.replace("\\/", "/"), (mm and mm.group(1), jre))
    pb = re.search(r"match /players/\{uid\} \{(.*?)\n    \}\n", rules, re.S)
    check("h) firestore.rules has match /players/{uid} with hasOnly+hasAll on username/created/confirmed, request.time stamps, update = confirmed only, no delete",
          bool(pb) and "hasOnly(['username','created','confirmed'])" in pb.group(1) and "hasAll(['username','created','confirmed'])" in pb.group(1)
          and "created == request.time" in pb.group(1) and "confirmed == request.time" in pb.group(1) and "affectedKeys().hasOnly(['confirmed'])" in pb.group(1)
          and "allow delete: if false;" in pb.group(1) and "validName(request.resource.data.username)" in pb.group(1)
          and "'@mangiasassi.invalid'" in pb.group(1))
    db = re.search(r"match /delreq/\{username\} \{(.*?)\n    \}\n", rules, re.S)
    check("h) firestore.rules has match /delreq/{username}: create with only ts == request.time, nothing else", bool(db) and "validName(username)" in db.group(1) and "hasOnly(['ts'])" in db.group(1) and "allow read, update, delete: if false;" in db.group(1))
    bb = re.search(r"match /bugs/\{id\} \{\s*allow create: if (\w+)\(?\)?", rules)
    check("h) bugs create is open to any signed-in user (signedIn(), not isDev()); rest of the block unchanged", bool(bb) and bb.group(1) == "signedIn" and "hasOnly(['uid','text','screen','version','char','ts','ua','meta'])" in rules and "allow read, update, delete: if false;" in rules)
    check("h) edits create is still dev-only", "match /edits/{id} {\n      allow create: if isDev()" in rules.replace("\r\n", "\n"))
    check("h) devs/saves blocks untouched (read own devs doc, write false; saves mine())", "match /devs/{uid} {" in rules and "function mine()" in rules)

    # ============================================================ i) SDK unreachable / offline
    for lab, kw in (("SDK blocked", dict(mode="block")), ("offline", dict(offline=True))):
        ctx, p, errs = page(b, users=dict(USERS), **kw); menu(p); acc_open(p)
        reg(p, "nuovonome", "segreto1")
        p.wait_for_function("(document.querySelector('#ple')||{}).innerText.includes('offline')", timeout=15000)
        st = p.evaluate("({a:playerAcct,dis:document.querySelector('#plr').disabled})")
        check("i) %s: «sei offline» message, button re-enabled, no session" % lab, st["a"] is None and st["dis"] is False, st)
        p.click("#back"); p.click("[data-tile=new]"); pick_maze(p); p.wait_for_timeout(1200)
        check("i) %s: the game keeps running (a real run starts)" % lab, p.evaluate("screen") == "game")
        check("i) %s: no console errors" % lab, not errs, errs)
        ctx.close()
    ctx, p, errs = page(b, users=dict(USERS), tooMany=True); menu(p); acc_open(p)
    reg(p, "nuovonome", "segreto1")
    p.wait_for_function("(document.querySelector('#ple')||{}).innerText.includes('Troppi tentativi')", timeout=5000)
    check("i) too-many-requests → the existing message", p.evaluate("playerAcct") is None)
    ctx.close()

    # ============================================================ smoke
    ctx, p, errs = page(b, dev_site=False); menu(p, False)
    check("smoke: menu renders", p.evaluate("screen") == "menu")
    p.click("[data-tile=new]"); pick_maze(p); p.wait_for_timeout(1500)
    check("smoke: a run starts", p.evaluate("screen") == "game")
    check("smoke: no console errors", not errs, errs)
    ctx.close()
    b.close()
srv.shutdown()

# ------------------------------------------------------------ node --check on every script block
WORK = os.path.join(os.environ.get("TEMP", "/tmp"), "l1_test")
os.makedirs(WORK, exist_ok=True)
h = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
nodeok = True
for i, blk in enumerate(re.findall(r"<script[^>]*>([\s\S]*?)</script>", h)):
    fp = os.path.join(WORK, "s%d.js" % i)
    open(fp, "w", encoding="utf-8").write(blk)
    r = subprocess.run(["node", "--check", fp], capture_output=True, text=True)
    if r.returncode != 0:
        nodeok = False; print(r.stderr)
check("node --check passes on every <script> block", nodeok)

print(sum(RES), "/", len(RES), "passed")
sys.exit(0 if all(RES) else 1)
