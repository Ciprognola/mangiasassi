#!/usr/bin/env python3
"""F2b headless tests (Firebase stub, never real credentials): cloud save, CLOUD_SAVE flag off.
Serves the repo at / (stable), /dev/ (dev site: keys and doc with _dev) and /flagon/ (stable with CLOUD_SAVE=true, only
to check the stable doc/keys). The stub keeps saves/{docId} in localStorage "__fbstub_saves" and checks writes like firestore.rules.
Run: python tools/fbstub/test_f2b.py   (about 2 minutes: the debounce check waits the real 30 s)"""
import functools, http.server, json, os, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fbstub
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PORT = 8793
BASE = "http://127.0.0.1:%d/" % PORT
VIEW = {"width": 390, "height": 844}
RES = []
UID = "uid_master"
USERS = dict(fbstub.USERS)
USERS["norole"] = {"pw": "pw-norole", "role": None}


def check(name, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name, str(extra)[:300], flush=True)


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        flag = False
        for pre in ("/dev/", "/flagon/"):
            if path.startswith(pre):
                flag = pre == "/flagon/"
                path = "/" + path[len(pre):]
        if flag and path == "/index.html":
            body = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read().replace("const CLOUD_SAVE=false;", "const CLOUD_SAVE=true;", 1).encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
            return
        self.path = path
        return super().do_GET()


def serve():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(H, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


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


def save(r=14, a=8, sordi=4200, **extra):
    s = {"p": {"sordi": sordi, "best": 5200, "char": "roccia", "g5": True,
               "ch": {"roccia": {"ownP": [0, 1, 2], "ownR": [0, 1], "selP": 0, "selR": 0, "lvl": r, "exp": 30, "gir": 12, "skins": [], "skin": None},
                      "algidone": {"ownP": [0, 1], "ownR": [0], "selP": 0, "selR": 0, "lvl": a, "exp": 10, "gir": 6, "skins": [], "skin": None}}},
         "opts": {"fs": 1, "sound": False, "music": False, "diff": "medium"}}
    s.update(extra)
    return s


NORM = {}


def norm(b, s):
    """the save exactly as this build's persist() writes it (boot migration adds the DEF fields a hand-written seed lacks):
    seeding normalized saves keeps 'dirty' about real changes only"""
    k = json.dumps(s, sort_keys=True)
    if k not in NORM:
        ctx = b.new_context(viewport=VIEW)
        ctx.add_init_script("if(!sessionStorage.getItem('__seeded')){sessionStorage.setItem('__seeded','1');localStorage.setItem('mgs_v1',%s)}" % json.dumps(json.dumps(s)))
        p = ctx.new_page(); p.goto(BASE + "index.html"); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(600)
        NORM[k] = p.evaluate("JSON.parse(localStorage.getItem('mgs_v1'))")
        ctx.close()
    return json.loads(json.dumps(NORM[k]))


def cdoc(s, rev=1, ver="0.4_13"):
    return {"data": json.dumps(s, sort_keys=True, separators=(",", ":")), "rev": rev, "ts": 1790000000000, "ver": ver}


SITES = {"dev": ("dev/", "_dev", "mgs_dev"), "stable": ("", "", "mgs"), "flagon": ("flagon/", "", "mgs")}


def page(b, site="dev", local=None, cloud=None, M=None, bak=None, toggle=True, dev=True, player=False, has_touch=False, extra_init="", **flags):
    path, sfx, app = SITES[site]
    ctx = b.new_context(viewport=VIEW, has_touch=has_touch)
    seed = {}
    if local is not None:
        seed["mgs_v1" + sfx] = json.dumps(local)
    if M is not None:
        seed["mgs_cloud" + sfx] = json.dumps(M)
    if bak is not None:
        seed["mgs_v1_cloudbak" + sfx] = json.dumps(bak)
    if toggle:
        seed["mgs_cloudtest_dev"] = "true"
    if dev:
        seed["mgs_dev" + sfx] = json.dumps({"role": "master", "acct": "master", "fb": True, "devOn": True})
    if player:
        seed["mgs_player" + sfx] = json.dumps({"acct": "norole", "fb": True})
    if cloud is not None:
        seed["__fbstub_saves"] = json.dumps(cloud)
    ctx.add_init_script("if(!sessionStorage.getItem('__seeded')){sessionStorage.setItem('__seeded','1');const s=%s;for(const k in s)localStorage.setItem(k,s[k])}" % json.dumps(seed))
    fbstub.install(ctx, users=USERS, session="norole" if player and not dev else "master", app=app, **flags)
    ctx.add_init_script("if(sessionStorage.getItem('__off'))window.__fbs.offline=true;" + extra_init)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    p.goto(BASE + path + "index.html"); p.wait_for_selector("#rsi, #clpop")
    return ctx, p, errs


def settle(p, ms=1500):
    """let the boot sync (and a possible apply + reload) finish, then get past the splash"""
    p.wait_for_timeout(ms)
    p.wait_for_selector("#rsi, #root .brand", timeout=10000)
    if p.evaluate("!!document.querySelector('#rsi')"):
        p.click("#rsi"); p.wait_for_timeout(700)


def tap_or_click(p, sel, touch=False):
    (p.tap if touch else p.click)(sel)


def open_account(p, touch=False):
    tap_or_click(p, "[data-tile=opt]", touch); p.wait_for_timeout(300)
    sel = "details.acc[data-acc=account] > summary"
    if not p.evaluate("!!document.querySelector('%s')" % sel):
        return False
    tap_or_click(p, sel, touch); p.wait_for_timeout(250)
    return True


def change_diff(p, k):
    """a real persist of player data: Opzioni -> Generali -> Gioco -> difficulty (the Gioco accordion must be open)"""
    p.click("[data-diff=%s]" % k); p.wait_for_timeout(120)


def open_game_acc(p):
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc[data-acc=game]').open"):
        p.click("details.acc[data-acc=game] > summary"); p.wait_for_timeout(200)


def docs(p):
    return p.evaluate("JSON.parse(localStorage.getItem('__fbstub_saves')||'{}')")


def cl(p):
    return p.evaluate("({ok:CL.ok,stop:CL.stop,later:CL.later,status:CL.status,pend:!!CL.pend,conf:!!CL.conf,M:JSON.parse(localStorage.getItem(CLOUD_KEY)||'null'),txt:cloudStatText()})")


def local(p, sfx="_dev"):
    return p.evaluate("JSON.parse(localStorage.getItem('mgs_v1%s')||'null')" % sfx)


def bakk(p, sfx="_dev"):
    return p.evaluate("JSON.parse(localStorage.getItem('mgs_v1_cloudbak%s')||'null')" % sfx)


def pagehide(p):
    p.evaluate("window.dispatchEvent(new Event('pagehide'))"); p.wait_for_timeout(600)


def dev_click(p, sel):
    """Opzioni -> Sviluppatore -> the accordion holding sel -> click (real clicks)"""
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(%s)').open" % sel.replace("'", "\\'")):
        p.click("details.acc:has(%s) > summary" % sel); p.wait_for_timeout(250)
    p.click(sel); p.wait_for_timeout(600)


srv = serve()
with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ unit: version order + saveIsFresh
    ctx, p, errs = page(b, site="dev", toggle=False)
    v = p.evaluate("[verCmp('0.4_14','0.4.5'),verCmp('0.4.5','0.4.5_1'),verCmp('0.4','0.4_14'),verCmp('0.4_14','0.4_14'),verCmp('0.4.5_1','0.4_14'),verCmp('0.4_9','0.4_14')]")
    check("version order: 0.4_14 < 0.4.5 < 0.4.5_1, 0.4 < 0.4_14, 0.4_9 < 0.4_14", v == [-1, -1, -1, 0, 1, -1], v)
    fr = p.evaluate("[saveIsFresh({}),saveIsFresh(JSON.parse(JSON.stringify(DEF))),saveIsFresh(%s),saveIsFresh({p:{lvl:5}}),saveIsFresh({p:{sordi:0},ach:{done:{x:1}}}),saveIsFresh({ov:{a:{label:'x'}},gtext:{b:'y'}})]" % json.dumps(save()))
    check("saveIsFresh: empty/DEF/dev-only-overrides fresh; progress, legacy lvl, an achievement not fresh", fr == [True, True, False, False, False, True], fr)
    ctx.close()

    # ============================================================ first sync 1: no C, L with progress -> upload (dev site: _dev doc + keys)
    L0 = dict(norm(b, save()), ov={"char_roccia": {"label": "Pietrone"}}, gtext={"bj_hi": "Ciao"})
    ctx, p, errs = page(b, site="dev", local=L0); settle(p)
    d = docs(p).get(UID + "_dev")
    c = cl(p)
    check("first sync, no cloud copy, local progress -> uploaded as rev 1", d is not None and d["rev"] == 1 and c["M"] and c["M"]["rev"] == 1 and not c["M"]["dirty"], (d and d["rev"], c))
    up = json.loads(d["data"]) if d else {}
    check("uploaded copy has the progress and NO dev-only fields (tiles/ov/extra/gtext/sim/realP/realQuick/realAch)",
          up.get("p", {}).get("ch", {}).get("roccia", {}).get("lvl") == 14 and not any(k in up for k in ["tiles", "ov", "extra", "gtext", "sim", "realP", "realQuick", "realAch"]), sorted(up.keys()))
    check("dev site: only the saves/{uid}_dev doc, _dev keys (mgs_cloud_dev yes, mgs_cloud no)",
          set(p.evaluate("window.__fbs.saveDocs")) == {UID + "_dev"} and p.evaluate("localStorage.getItem('mgs_cloud_dev')!==null&&localStorage.getItem('mgs_cloud')===null"), p.evaluate("window.__fbs.saveDocs"))
    check("upload written with ver = this build", d and d["ver"] == p.evaluate("VERSION"))
    check("status: 'Cloud: sincronizzato alle HH:MM'", c["txt"].startswith("Cloud: sincronizzato alle "), c["txt"])
    check("no console errors (first sync upload)", not errs, errs)
    ctx.close()

    # ============================================================ first sync 2: no C, L fresh -> nothing uploaded, M written at rev 0
    ctx, p, errs = page(b, site="dev"); settle(p)
    c = cl(p)
    check("first sync, no cloud copy, fresh local -> nothing uploaded, M rev 0", not docs(p) and c["M"] and c["M"]["rev"] == 0 and c["ok"], c)
    check("no console errors (fresh, no cloud)", not errs, errs)
    ctx.close()

    # ============================================================ first sync 3: C exists, L fresh (with this device's own dev-only fields) -> apply C, keep dev fields
    Cs = norm(b, save(r=20, a=11, sordi=777))
    ctx, p, errs = page(b, site="dev", local={"ov": {"char_roccia": {"label": "Pietrone"}}, "gtext": {"bj_hi": "Ciao"}}, cloud={UID + "_dev": cdoc(Cs, rev=3)}); settle(p, 2500)
    s = p.evaluate("({r:S.p.ch.roccia.lvl,a:S.p.ch.algidone.lvl,so:S.p.sordi,ov:S.ov.char_roccia&&S.ov.char_roccia.label,gt:S.gtext.bj_hi})")
    c = cl(p); bk = bakk(p)
    check("first sync, cloud copy + fresh local -> cloud applied (page reloaded with it)", s["r"] == 20 and s["a"] == 11 and s["so"] == 777, s)
    check("apply keeps this device's dev-only fields (S.ov / S.gtext)", s["ov"] == "Pietrone" and s["gt"] == "Ciao", s)
    check("apply: M = cloud rev, not dirty; old local went to the backup (from device)", c["M"]["rev"] == 3 and not c["M"]["dirty"] and bk and bk["from"] == "device", (c["M"], bk and bk["from"]))
    check("apply: no upload afterwards (cloud still rev 3)", docs(p)[UID + "_dev"]["rev"] == 3)
    check("no console errors (apply)", not errs, errs)
    # ---- Ripristina backup (dev site): swaps backup and current save, marks dirty
    check("Account accordion shows «Ripristina backup» on the dev site", open_account(p) and p.evaluate("!!document.querySelector('#clrb')"))
    p.click("#clrb"); p.wait_for_timeout(200); p.click("#cy"); p.wait_for_timeout(2500)
    p.wait_for_selector("#rsi, #root .brand")
    s2 = p.evaluate("({r:S.p.ch.roccia.lvl,so:S.p.sordi,ov:S.ov.char_roccia&&S.ov.char_roccia.label})")
    bk2 = bakk(p); M2 = p.evaluate("JSON.parse(localStorage.getItem('mgs_cloud_dev'))")
    check("Ripristina backup: the old (fresh) local save is back, dev fields kept", s2["r"] == 1 and s2["so"] == 0 and s2["ov"] == "Pietrone", s2)
    d2 = docs(p)[UID + "_dev"]
    check("Ripristina backup: the backup now holds the cloud-applied save", bk2 and json.loads(bk2["data"])["p"]["ch"]["roccia"]["lvl"] == 20, bk2 and bk2["from"])
    check("Ripristina backup marked dirty -> the restored save is uploaded at the next start (rev 4)", d2["rev"] == 4 and json.loads(d2["data"]).get("p", {}).get("sordi", 0) == 0 and M2["rev"] == 4 and not M2["dirty"], (M2, d2["rev"]))
    check("no console errors (restore backup)", not errs, errs)
    ctx.close()

    # ============================================================ first sync 4: both have progress, equal hash -> just M (toggle on by a real click)
    ctx, p, errs = page(b, site="dev", local=norm(b, save()), toggle=False); settle(p)
    check("toggle off on the dev site: no save calls at boot", not p.evaluate("window.__fbs.saveCalls"))
    pay = p.evaluate("cloudLocal().pay")
    p.evaluate("localStorage.setItem('__fbstub_saves',JSON.stringify({%s:{data:%s,rev:4,ts:1790000000000,ver:'0.4_13'}}))" % (json.dumps(UID + "_dev"), json.dumps(pay)))
    check("Account accordion shows «Salvataggio cloud (test)» + status + Sincronizza ora", open_account(p) and p.evaluate("!!document.querySelector('[data-clt]')&&!!document.querySelector('#clst')&&!!document.querySelector('#clsy')"))
    check("toggle off: status 'Cloud: disattivato', Sincronizza ora disabled", p.evaluate("document.querySelector('#clst').textContent") == "Cloud: disattivato" and p.evaluate("document.querySelector('#clsy').disabled"))
    p.click("[data-clt='1']"); p.wait_for_timeout(900)
    c = cl(p)
    check("equal hash on both sides -> M written with the cloud rev, no upload, no popup", c["M"] and c["M"]["rev"] == 4 and docs(p)[UID + "_dev"]["rev"] == 4 and not p.evaluate("!!document.querySelector('#clpop')"), c)
    p.click("[data-clt='0']"); p.wait_for_timeout(300)
    check("toggle back off -> 'Cloud: disattivato'", p.evaluate("document.querySelector('#clst').textContent") == "Cloud: disattivato")
    check("no console errors (equal hash / toggle)", not errs, errs)
    ctx.close()

    # ============================================================ first sync 5: both have progress, different -> conflict popup; «Usa questo» cloud
    ctx, p, errs = page(b, site="dev", local=norm(b, save(r=14, a=8, sordi=4200)), cloud={UID + "_dev": cdoc(norm(b, save(r=22, a=3, sordi=90)), rev=2)}); p.wait_for_timeout(1500)
    txt = p.evaluate("document.querySelector('#clpop')&&document.querySelector('#clpop').innerText") or ""
    check("first sync, different progress -> popup «Due salvataggi diversi»", "Due salvataggi diversi" in txt and "Nel cloud" in txt and "Su questo dispositivo" in txt, txt[:200].replace(chr(10), " | "))
    check("popup cards: levels of both characters + sordi + date", all(x in txt for x in ["Liv. 22", "Liv. 3", "90 sordi", "Liv. 14", "Liv. 8", "4200 sordi", "Salvato il"]), txt.replace(chr(10), " | ")[:300])
    check("screenId() = cloud-conflict", p.evaluate("screenId()") == "cloud-conflict")
    p.keyboard.press("Enter"); p.wait_for_timeout(200)
    check("popup blocks keys (Enter does nothing)", p.evaluate("!!document.querySelector('#clpop')"))
    p.click("#clc"); p.wait_for_timeout(2500); settle(p, 300)
    s = p.evaluate("({r:S.p.ch.roccia.lvl,so:S.p.sordi})"); bk = bakk(p); c = cl(p)
    check("«Usa questo» on Nel cloud -> cloud save applied after reload", s == {"r": 22, "so": 90}, s)
    check("... the device save went to the backup (from device), M = cloud rev 2", bk and bk["from"] == "device" and json.loads(bk["data"])["p"]["sordi"] == 4200 and c["M"]["rev"] == 2, (bk and bk["from"], c["M"]))
    check("no console errors (conflict -> cloud)", not errs, errs)
    ctx.close()

    # ============================================================ conflict popup: «Usa questo» device (mobile touch)
    Cd = cdoc(norm(b, save(r=22, a=3, sordi=90)), rev=2)
    ctx, p, errs = page(b, site="dev", local=norm(b, save(r=14, a=8, sordi=4200)), cloud={UID + "_dev": Cd}, has_touch=True); p.wait_for_timeout(1500)
    check("touch: popup shown", p.evaluate("!!document.querySelector('#clpop')"))
    p.tap("#cld"); p.wait_for_timeout(900)
    d = docs(p)[UID + "_dev"]; bk = bakk(p); c = cl(p)
    check("«Usa questo» on the device -> local uploaded through the transaction as rev 3", d["rev"] == 3 and json.loads(d["data"])["p"]["sordi"] == 4200 and c["M"]["rev"] == 3, (d["rev"], c["M"]))
    check("... the cloud copy went to the backup (from cloud)", bk and bk["from"] == "cloud" and bk["data"] == Cd["data"], bk and bk["from"])
    check("... local save untouched, popup closed", local(p)["p"]["sordi"] == 4200 and not p.evaluate("!!document.querySelector('#clpop')"))
    settle(p, 100)
    check("touch: Account accordion + «Sincronizza ora» tap", open_account(p, touch=True) and p.evaluate("!!document.querySelector('#clsy')"))
    p.tap("#clsy"); p.wait_for_timeout(700)
    check("touch: Sincronizza ora with nothing new -> still rev 3, synced status", docs(p)[UID + "_dev"]["rev"] == 3 and p.evaluate("document.querySelector('#clst').textContent").startswith("Cloud: sincronizzato"))
    check("no console errors (conflict -> device, touch)", not errs, errs)
    ctx.close()

    # ============================================================ «Decidi dopo» (and Esc) -> no sync until the next start
    ctx, p, errs = page(b, site="dev", local=norm(b, save()), cloud={UID + "_dev": cdoc(norm(b, save(r=30)), rev=5)}); p.wait_for_timeout(1500)
    p.click("#cll"); p.wait_for_timeout(300); settle(p, 100)
    c = cl(p)
    check("«Decidi dopo» -> popup closed, later set, nothing written", not p.evaluate("!!document.querySelector('#clpop')") and c["later"] and docs(p)[UID + "_dev"]["rev"] == 5 and local(p)["p"]["ch"]["roccia"]["lvl"] == 14, c)
    open_game_acc(p); change_diff(p, "hard"); pagehide(p)
    check("... after «Decidi dopo» a persist + pagehide uploads nothing, the game keeps saving locally", docs(p)[UID + "_dev"]["rev"] == 5 and local(p)["opts"]["diff"] == "hard")
    p.reload(); p.wait_for_selector("#rsi, #clpop"); p.wait_for_timeout(1500)
    check("next start -> the popup comes back", p.evaluate("!!document.querySelector('#clpop')"))
    p.keyboard.press("Escape"); p.wait_for_timeout(300)
    check("Esc = Decidi dopo", not p.evaluate("!!document.querySelector('#clpop')") and cl(p)["later"])
    p.reload(); p.wait_for_selector("#rsi, #clpop"); p.wait_for_timeout(1500)
    check("popup again at the next start (for the back button)", p.evaluate("!!document.querySelector('#clpop')"))
    p.evaluate("window.__kd=0;window.addEventListener('keydown',()=>{window.__kd++})"); p.keyboard.press("Enter"); p.wait_for_timeout(100); kd0 = p.evaluate("window.__kd")
    p.evaluate("window.dispatchEvent(new Event('mgback'))"); p.wait_for_timeout(400)
    check("Android back (mgback) = Decidi dopo: popup closed, later set, BUG cleared, splash question back", not p.evaluate("!!document.querySelector('#clpop')") and cl(p)["later"] and p.evaluate("BUG===null") and p.evaluate("!!document.querySelector('#rsi')") and p.evaluate("screen") == "splash")
    p.keyboard.press("Enter"); p.wait_for_timeout(100)
    check("after back: keys reach the game again (blocked while open)", kd0 == 0 and p.evaluate("window.__kd") == 1, (kd0, p.evaluate("window.__kd")))
    p.click("#rsi"); p.wait_for_timeout(700)
    check("after back: taps work (splash -> menu)", p.evaluate("screen") == "menu")
    check("no console errors (decidi dopo)", not errs, errs)
    ctx.close()

    # ============================================================ same uid: C.rev == M.rev (nothing / dirty -> upload), newer + clean -> apply, newer + dirty -> popup, C missing -> upload
    ctx, p, errs = page(b, site="dev", local=norm(b, save())); settle(p)
    check("setup: synced at rev 1", docs(p)[UID + "_dev"]["rev"] == 1)
    p.reload(); settle(p)
    check("same uid, C.rev == M.rev, not dirty -> nothing uploaded", docs(p)[UID + "_dev"]["rev"] == 1 and cl(p)["ok"])
    open_game_acc(p); change_diff(p, "hard")
    check("a real persist marks M dirty", cl(p)["M"]["dirty"] is True)
    p.reload(); settle(p)
    check("same uid, C.rev == M.rev, dirty -> uploaded at boot (rev 2)", docs(p)[UID + "_dev"]["rev"] == 2 and not cl(p)["M"]["dirty"])
    p.evaluate("(()=>{const a=JSON.parse(localStorage.getItem('__fbstub_saves'));const d=JSON.parse(a['%s'].data);d.p.sordi=12345;a['%s']={data:JSON.stringify(d),rev:3,ts:Date.now(),ver:'0.4_14'};localStorage.setItem('__fbstub_saves',JSON.stringify(a))})()" % (UID + "_dev", UID + "_dev"))
    p.reload(); settle(p, 2500)
    check("same uid, cloud newer, device clean -> cloud applied", p.evaluate("S.p.sordi") == 12345 and cl(p)["M"]["rev"] == 3)
    p.evaluate("(()=>{const a=JSON.parse(localStorage.getItem('__fbstub_saves'));const d=JSON.parse(a['%s'].data);d.p.sordi=5;a['%s']={data:JSON.stringify(d),rev:4,ts:Date.now(),ver:'0.4_14'};localStorage.setItem('__fbstub_saves',JSON.stringify(a))})()" % (UID + "_dev", UID + "_dev"))
    open_game_acc(p); change_diff(p, "easy")
    p.reload(); p.wait_for_timeout(1500)
    check("same uid, cloud newer AND device dirty -> conflict popup", p.evaluate("!!document.querySelector('#clpop')"))
    p.click("#cll"); p.wait_for_timeout(200)
    p.evaluate("localStorage.setItem('__fbstub_saves','{}')")
    p.reload(); settle(p)
    d = docs(p).get(UID + "_dev")
    check("same uid, cloud copy missing -> uploaded again (create, rev 1)", d and d["rev"] == 1, d and d["rev"])
    check("no console errors (same uid cases)", not errs, errs)
    ctx.close()

    # ============================================================ transaction finds an unexpected rev -> popup (pagehide flush path)
    ctx, p, errs = page(b, site="dev", local=norm(b, save())); settle(p)
    p.evaluate("(()=>{const a=JSON.parse(localStorage.getItem('__fbstub_saves'));const d=JSON.parse(a['%s'].data);d.p.sordi=1;a['%s']={data:JSON.stringify(d),rev:7,ts:Date.now(),ver:'0.4_14'};localStorage.setItem('__fbstub_saves',JSON.stringify(a))})()" % (UID + "_dev", UID + "_dev"))
    open_game_acc(p); change_diff(p, "hard"); pagehide(p)
    check("upload transaction sees an unexpected rev -> conflict popup, nothing written", p.evaluate("!!document.querySelector('#clpop')") and docs(p)[UID + "_dev"]["rev"] == 7)
    check("no console errors (unexpected rev)", not errs, errs)
    ctx.close()

    # ============================================================ debounce: many persists -> one upload after 30 s
    ctx, p, errs = page(b, site="dev", local=norm(b, save())); settle(p)
    open_game_acc(p)
    for k in ["hard", "easy", "hard", "medium", "hard", "easy"]:
        change_diff(p, k)
    p.wait_for_timeout(1000)
    check("debounce: 6 persists -> nothing uploaded yet", docs(p)[UID + "_dev"]["rev"] == 1)
    p.wait_for_timeout(30500)
    d = docs(p)[UID + "_dev"]
    check("debounce: exactly one upload after 30 s, with the last value", d["rev"] == 2 and json.loads(d["data"])["opts"]["diff"] == "easy", d["rev"])
    p.wait_for_timeout(1500)
    check("debounce: no further upload", docs(p)[UID + "_dev"]["rev"] == 2 and not cl(p)["M"]["dirty"])
    check("no console errors (debounce)", not errs, errs)
    ctx.close()

    # ============================================================ run-end flush (real run, Abbandona)
    ctx, p, errs = page(b, site="dev", local=norm(b, save())); settle(p)
    p.click("[data-tile=new]"); p.wait_for_timeout(1500)
    check("a real run starts", p.evaluate("screen") == "game")
    p.click("#ps"); p.wait_for_timeout(300); p.click("#q"); p.wait_for_timeout(300)
    if p.evaluate("!!document.querySelector('#cy')"):
        p.click("#cy")
    p.wait_for_timeout(900)
    check("run end (finishRun) flushes at once, no 30 s wait", docs(p)[UID + "_dev"]["rev"] == 2 and p.evaluate("screen") == "menu", docs(p)[UID + "_dev"]["rev"])
    open_game_acc(p); change_diff(p, "hard"); pagehide(p)
    check("a second flush within 10 s is skipped (debounce armed instead)", docs(p)[UID + "_dev"]["rev"] == 2 and p.evaluate("!!CL.deb"))
    check("no console errors (run-end flush)", not errs, errs)
    ctx.close()

    # ============================================================ SIM / Sblocca tutto, dev run, PR.test -> no upload
    ctx, p, errs = page(b, site="dev", local=norm(b, save())); settle(p)
    dev_click(p, '[data-sim="1"]')
    check("Sblocca tutto on (real click)", p.evaluate("SIM()") and p.evaluate("cloudBlocked()"))
    p.click("#back"); p.wait_for_timeout(300)
    open_game_acc(p); change_diff(p, "hard"); pagehide(p); p.wait_for_timeout(300)
    check("SIM: persist + pagehide upload nothing (still rev 1), M not marked dirty", docs(p)[UID + "_dev"]["rev"] == 1 and not cl(p)["M"]["dirty"])
    p.click("#back"); p.wait_for_timeout(300)
    dev_click(p, '[data-sim="0"]'); p.click("#back"); p.wait_for_timeout(300)
    check("SIM off: real data back, now dirty (the difficulty change is real)", not p.evaluate("SIM()") and cl(p)["M"]["dirty"] and p.evaluate("S.p.ch.roccia.lvl") == 14)
    dev_click(p, "#jg4")
    check("dev jump run: screen game, G.dev, cloudBlocked()", p.evaluate("screen") == "game" and p.evaluate("G.dev") and p.evaluate("cloudBlocked()"))
    pagehide(p); p.wait_for_timeout(300)
    check("dev run: pagehide uploads nothing", docs(p)[UID + "_dev"]["rev"] == 1)
    p.evaluate("go('menu')"); p.wait_for_timeout(400)
    dev_click(p, "#mgrob"); p.wait_for_timeout(600)
    check("PR.test battle: screen pr, PR.test, cloudBlocked()", p.evaluate("screen") == "pr" and p.evaluate("!!(PR&&PR.test)") and p.evaluate("cloudBlocked()"))
    pagehide(p); p.wait_for_timeout(300)
    check("PR.test: pagehide uploads nothing", docs(p)[UID + "_dev"]["rev"] == 1)
    check("no console errors (SIM/dev run/PR.test)", not errs, errs)
    ctx.close()

    # ============================================================ stable, flag off: zero save calls, UI unchanged
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=True); settle(p)
    open_account(p)
    check("stable: Account accordion (dev in dev mode) has NO cloud block", not p.evaluate("!!document.querySelector('#clst')||!!document.querySelector('[data-clt]')||!!document.querySelector('#clsy')"))
    p.click("details.acc[data-acc=game] > summary"); p.wait_for_timeout(200); change_diff(p, "hard"); pagehide(p)
    p.click("#back"); p.wait_for_timeout(200); p.click("[data-tile=new]"); p.wait_for_timeout(1200)
    p.click("#ps"); p.wait_for_timeout(300); p.click("#q"); p.wait_for_timeout(900)
    check("stable, flag off (even with the dev test key set): zero Firestore save calls", not p.evaluate("window.__fbs.saveCalls") and p.evaluate("localStorage.getItem('mgs_cloud')===null"), p.evaluate("window.__fbs.saveCalls"))
    check("stable: cloudOn() false", p.evaluate("cloudOn()") is False)
    check("no console errors (stable flag off)", not errs, errs)
    ctx.close()
    ctx, p, errs = page(b, site="stable", player=True, dev=False, local=norm(b, save())); settle(p)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    check("stable: a player session still sees no Account accordion (F2a rule unchanged)", not p.evaluate("!!document.querySelector('details.acc[data-acc=account]')"))
    ctx.close()

    # ============================================================ dev site: a player session sees the Account accordion (status, logout, sync)
    ctx, p, errs = page(b, site="dev", player=True, dev=False, local=norm(b, save())); settle(p)
    check("dev site: player session -> Account accordion with status, Esci, Sincronizza ora", open_account(p) and p.evaluate("!!document.querySelector('#clst')&&!!document.querySelector('#plo')&&!!document.querySelector('#clsy')"))
    d = docs(p).get("uid_norole_dev")
    check("dev site: the player's own doc saves/uid_norole_dev synced", d and d["rev"] == 1, d and d["rev"])
    p.click("#plo"); p.wait_for_timeout(300)
    check("player logout: mgs_cloud_dev cleared, save kept", p.evaluate("localStorage.getItem('mgs_cloud_dev')") is None and local(p) is not None)
    check("no console errors (player on dev site)", not errs, errs)
    ctx.close()

    # ============================================================ flag on (stable keys + doc) - /flagon/ serves CLOUD_SAVE=true
    ctx, p, errs = page(b, site="flagon", local=norm(b, save()), toggle=False); settle(p)
    d = docs(p)
    check("stable with CLOUD_SAVE=true: doc saves/{uid} (no _dev), keys mgs_cloud", list(d.keys()) == [UID] and p.evaluate("localStorage.getItem('mgs_cloud')!==null&&localStorage.getItem('mgs_cloud_dev')===null"), list(d.keys()))
    check("stable with the flag on: no test toggle / no Ripristina backup", open_account(p) and not p.evaluate("!!document.querySelector('[data-clt]')||!!document.querySelector('#clrb')") and p.evaluate("!!document.querySelector('#clst')"))
    check("no console errors (flag on)", not errs, errs)
    ctx.close()

    # ============================================================ offline boot -> game plays, retry once online
    ctx, p, errs = page(b, site="dev", local=norm(b, save()), offline=True); settle(p)
    p.click("[data-tile=new]"); p.wait_for_timeout(1200)
    check("offline boot: a run starts normally", p.evaluate("screen") == "game")
    check("offline: nothing in the cloud, status 'in attesa di rete'", not docs(p) and cl(p)["txt"] == "Cloud: in attesa di rete", cl(p)["txt"])
    p.evaluate("window.__fbs.offline=false;window.dispatchEvent(new Event('online'))"); p.wait_for_timeout(900)
    check("back online -> synced (uploaded rev 1) without leaving the run", docs(p).get(UID + "_dev", {}).get("rev") == 1 and p.evaluate("screen") == "game")
    check("no console errors (offline boot)", not errs, errs)
    ctx.close()

    # ============================================================ permission error stops the loop
    ctx, p, errs = page(b, site="dev", local=norm(b, save()), denySaves=True); settle(p)
    n0 = p.evaluate("window.__fbs.saveCalls")
    c = cl(p)
    check("permission error -> stop, status 'Cloud: non disponibile'", c["stop"] and c["txt"] == "Cloud: non disponibile" and n0 == 1, (c, n0))
    open_game_acc(p); change_diff(p, "hard"); pagehide(p)
    p.evaluate("window.dispatchEvent(new Event('online'))"); p.wait_for_timeout(500)
    check("... no further save calls (persist, pagehide, online)", p.evaluate("window.__fbs.saveCalls") == 1)
    check("no console errors (permission)", not errs, errs)
    ctx.close()

    # ============================================================ newer ver in the cloud -> never applied, never overwritten
    ctx, p, errs = page(b, site="dev", cloud={UID + "_dev": cdoc(norm(b, save(r=40)), rev=9, ver="0.4.5_1")}); settle(p)
    c = cl(p)
    check("cloud copy from a newer build -> not applied (local still fresh), no write", p.evaluate("S.p.ch.roccia.lvl") == 1 and docs(p)[UID + "_dev"]["rev"] == 9 and c["status"] == "ver", c)
    check("status «Aggiorna il gioco per sincronizzare» in the Account accordion", open_account(p) and p.evaluate("document.querySelector('#clst').textContent") == "Aggiorna il gioco per sincronizzare")
    check("no console errors (newer ver)", not errs, errs)
    ctx.close()

    # ============================================================ size limit
    ctx, p, errs = page(b, site="dev", local=norm(b, save(p={"sordi": 5, "junk": "x" * 900100}))); settle(p)
    check("save over 900000 chars -> never uploaded, status «Salvataggio troppo grande per il cloud»", not docs(p) and cl(p)["txt"] == "Salvataggio troppo grande per il cloud", cl(p)["txt"])
    check("no console errors (size)", not errs, errs)
    ctx.close()

    # ============================================================ logout keeps the save (dev logout from the Sviluppatore tab)
    ctx, p, errs = page(b, site="dev", local=norm(b, save()), bak={"data": "{}", "from": "cloud", "ts": 1790000000000, "summary": {}}); settle(p)
    check("setup: synced", p.evaluate("localStorage.getItem('mgs_cloud_dev')") is not None)
    dev_click(p, "#lo")
    check("dev logout: mgs_cloud_dev cleared; local save and backup kept", p.evaluate("localStorage.getItem('mgs_cloud_dev')") is None and local(p)["p"]["sordi"] == 4200 and bakk(p) is not None)
    check("no console errors (logout)", not errs, errs)
    ctx.close()

    # ============================================================ apply deferred mid-run until the menu
    ctx, p, errs = page(b, site="dev", local=norm(b, save())); settle(p)
    p.evaluate("(()=>{const a=JSON.parse(localStorage.getItem('__fbstub_saves'));const d=JSON.parse(a['%s'].data);d.p.sordi=31337;a['%s']={data:JSON.stringify(d),rev:2,ts:Date.now(),ver:'0.4_14'};localStorage.setItem('__fbstub_saves',JSON.stringify(a))})()" % (UID + "_dev", UID + "_dev"))
    p.evaluate("sessionStorage.setItem('__off','1')"); p.reload(); settle(p)
    p.click("[data-tile=new]"); p.wait_for_timeout(1200)
    p.evaluate("window.__mark=1;sessionStorage.removeItem('__off');window.__fbs.offline=false;window.dispatchEvent(new Event('online'))"); p.wait_for_timeout(900)
    if p.evaluate("!!document.querySelector('#clpop')"):
        check("mid-run conflict popup freezes the maze (G.state pause)", p.evaluate("G.state") == "pause")
        p.evaluate("window.dispatchEvent(new Event('mgback'))"); p.wait_for_timeout(500)
        check("mid-run Android back = Decidi dopo: popup closed, maze running, no pause menu", not p.evaluate("!!document.querySelector('#clpop')") and p.evaluate("G.state") == "play" and not p.evaluate("!!document.querySelector('#r')") and cl(p)["later"])
        p.evaluate("CL.later=false;window.dispatchEvent(new Event('online'))"); p.wait_for_timeout(900)  # back on track for the deferred-apply check below
        p.click("#clc"); p.wait_for_timeout(500)
    check("mid-run: nothing applied yet (no reload, still in the run, apply pending)", p.evaluate("window.__mark") == 1 and p.evaluate("screen") == "game" and cl(p)["pend"])
    p.click("#ps"); p.wait_for_timeout(300); p.click("#q"); p.wait_for_timeout(300)
    if p.evaluate("!!document.querySelector('#cy')"):
        p.click("#cy")
    p.wait_for_timeout(2500); p.wait_for_selector("#rsi, #root .brand")
    if p.evaluate("!!document.querySelector('#clpop')"):
        p.click("#clc"); p.wait_for_timeout(2500)
    check("back at the menu -> cloud copy applied (page reloaded)", p.evaluate("typeof window.__mark") == "undefined" and p.evaluate("S.p.sordi") == 31337)
    check("no console errors (deferred apply)", not errs, errs)
    ctx.close()

    # ============================================================ Android back (mgback) on a conflict popup that opens mid-run = Decidi dopo, the maze runs again
    ctx, p, errs = page(b, site="dev", local=norm(b, save())); settle(p)
    open_game_acc(p); change_diff(p, "hard"); p.click("#back"); p.wait_for_timeout(300)
    check("setup: device dirty", cl(p)["M"]["dirty"] is True)
    p.evaluate("(()=>{const a=JSON.parse(localStorage.getItem('__fbstub_saves'));const d=JSON.parse(a['%s'].data);d.p.sordi=777;a['%s']={data:JSON.stringify(d),rev:2,ts:Date.now(),ver:'0.4_14'};localStorage.setItem('__fbstub_saves',JSON.stringify(a))})()" % (UID + "_dev", UID + "_dev"))
    p.evaluate("sessionStorage.setItem('__off','1')"); p.reload(); settle(p)
    p.click("[data-tile=new]"); p.wait_for_timeout(1500)
    p.evaluate("sessionStorage.removeItem('__off');window.__fbs.offline=false;window.dispatchEvent(new Event('online'))"); p.wait_for_timeout(900)
    check("mid-run: cloud newer + device dirty -> popup, maze frozen", p.evaluate("!!document.querySelector('#clpop')") and p.evaluate("G.state") == "pause")
    p.evaluate("window.dispatchEvent(new Event('mgback'))"); p.wait_for_timeout(300)
    p.wait_for_timeout(600)
    check("mid-run Android back = Decidi dopo: popup closed, maze running, no pause menu, BUG cleared", not p.evaluate("!!document.querySelector('#clpop')") and p.evaluate("G.state") == "play" and not p.evaluate("!!document.querySelector('#r')") and cl(p)["later"] and p.evaluate("BUG===null"))
    check("... nothing applied or uploaded (local kept, cloud rev 2)", p.evaluate("S.p.sordi") == 4200 and docs(p)[UID + "_dev"]["rev"] == 2)
    check("no console errors (mid-run back)", not errs, errs)
    ctx.close()

    # ============================================================ old saves still load (legacy, pre two characters) + upload as progress
    OLD = {"p": {"lvl": 5, "exp": 10, "ownP": [0, 1], "selP": 1, "sordi": 300, "best": 900}, "opts": {"sound": False, "music": False}}
    ctx, p, errs = page(b, site="dev", local=OLD); settle(p)
    check("old save loads (roccia lvl 5, sordi 300)", p.evaluate("S.p.ch.roccia.lvl") == 5 and p.evaluate("S.p.sordi") == 300)
    check("old save is not 'fresh' -> uploaded at first sync", docs(p).get(UID + "_dev", {}).get("rev") == 1)
    p.click("[data-tile=new]"); p.wait_for_timeout(1200)
    check("old save: a run starts", p.evaluate("screen") == "game")
    check("no console errors (old save, dev site)", not errs, errs)
    ctx.close()
    ctx, p, errs = page(b, site="stable", local=OLD, dev=False, toggle=False); settle(p)
    p.click("[data-tile=new]"); p.wait_for_timeout(1200)
    check("old save on stable (flag off): loads, run starts, no errors", p.evaluate("S.p.ch.roccia.lvl") == 5 and p.evaluate("screen") == "game" and not errs, errs)
    ctx.close()

    b.close()
srv.shutdown()

print(sum(RES), "/", len(RES), "passed")
sys.exit(0 if all(RES) else 1)
