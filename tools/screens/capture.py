#!/usr/bin/env python3
"""Screens library (I3): one 390x844 PNG per screen/popup -> refs/screens/<id>.png.

Serves the repo over http at the ROOT path (never /dev/), drives the game with real clicks
(dev buttons / "Sblocca tutto" / SIM only to reach locked content) and seeds its own save
in a fresh browser context per scenario, so it never depends on leftovers.

    python tools/screens/capture.py                # everything
    python tools/screens/capture.py --only fa- pb-  # only ids/scenarios starting with these prefixes
    python tools/screens/capture.py --no-optimize   # keep raw PNGs

Requires: playwright (python, chromium installed) and Pillow.
"""
import argparse, functools, http.server, json, os, sys, threading, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fbstub"))
import fbstub
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "refs", "screens")
PORT = 8791
BASE = f"http://127.0.0.1:{PORT}/"
VIEW = {"width": 390, "height": 844}
NOT_CAPTURED = []          # (id, reason)
DONE = []                  # captured ids


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve():
    h = functools.partial(Quiet, directory=ROOT)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


class Cap:
    def __init__(self, browser, only, seed=None, dev=False):
        self.only = only
        self.ctx = browser.new_context(viewport=VIEW, device_scale_factor=1, has_touch=True)
        init = ["window.__cap=1;"]
        if seed is not None:
            init.append("if(!localStorage.getItem('mgs_v1'))localStorage.setItem('mgs_v1',%s);" % json.dumps(json.dumps(seed)))
        if dev:
            # F1: a Firebase-style dev session in the cache + the Firebase stub (tools/fbstub) with a signed-in "master": no real Firebase, no credentials
            init.append("localStorage.setItem('mgs_dev',JSON.stringify({role:'master',acct:'master',fb:true,devOn:true}));")
        # silence audio + randomness where a clean frame matters is done per scenario
        init.append("document.addEventListener('DOMContentLoaded',()=>{const st=document.createElement('style');st.id='capstyle';st.textContent='#ach-pop{display:none!important}';document.head.appendChild(st)});")
        self.ctx.add_init_script("".join(init))
        if dev:
            fbstub.install(self.ctx, session="master")
        self.p = self.ctx.new_page()
        self.errors = []
        self.p.on("pageerror", lambda e: self.errors.append(str(e)))

    def open(self):
        self.p.goto(BASE + "index.html")
        self.p.wait_for_selector("#rsi", timeout=8000)
        return self

    def wants(self, id_):
        return not self.only or any(id_.startswith(o) for o in self.only)

    def shot(self, id_, wait=350):
        if not self.wants(id_):
            return
        time.sleep(wait / 1000)
        os.makedirs(OUT, exist_ok=True)
        self.p.screenshot(path=os.path.join(OUT, id_ + ".png"))
        DONE.append(id_)
        print("  +", id_)

    def ev(self, js):
        return self.p.evaluate(js)

    def click(self, sel, wait=300):
        self.p.click(sel, timeout=5000)
        time.sleep(wait / 1000)

    def close(self):
        self.ctx.close()


# --------------------------------------------------------------------------- helpers
def enter_menu(c):
    c.click("#rsi", 900)


def go_tile(c, tile):
    c.click(f"[data-tile={tile}]", 500)


def back(c):
    c.click("#back", 400)


def sim_on(c):
    """Real path to "Sblocca tutto": options -> Sviluppatore -> Account accordion -> [data-sim=1]."""
    go_tile(c, "opt")
    c.click("[data-otab=dev]", 300)
    c.click("details.acc:has([data-sim]) > summary", 300)
    c.click('[data-sim="1"]', 400)
    back(c)


def dev_view_off(c):
    """Keep the Sblocca tutto overlay but hide the developer UI (pens, dev toggle).
    Since E1b the ✎ button ends the overlay together with dev mode (Trello #12), so the script sets devOn directly."""
    c.ev("devOn=false;render()")
    c.p.wait_for_timeout(300)


MID_SAVE = {  # a mid-game save: some levels, sordi, both characters started
    "p": {"sordi": 4200, "best": 5200, "char": "roccia", "g5": True,
          "ch": {"roccia": {"ownP": [0, 1, 2], "ownR": [0, 1], "selP": 0, "selR": 0, "lvl": 14, "exp": 30, "gir": 12, "skins": [], "skin": None},
                 "algidone": {"ownP": [0, 1], "ownR": [0], "selP": 0, "selR": 0, "lvl": 8, "exp": 10, "gir": 6, "skins": [], "skin": None}}},
}


def new_cap(browser, only, seed="mid", dev=False):
    s = MID_SAVE if seed == "mid" else None
    return Cap(browser, only, seed=s, dev=dev).open()


# --------------------------------------------------------------------------- scenarios
def sc_splash_menu(b, only):
    c = new_cap(b, only, seed=None)
    c.shot("splash-question")
    c.click("#rsi", 900)
    c.shot("menu-home-roccia", 500)
    c.close()
    c = new_cap(b, only)
    c.ev("S.p.char='algidone';persist()")
    c.p.reload(); c.p.wait_for_selector("#rsi"); enter_menu(c)
    c.shot("menu-home-algidone", 500)
    c.close()


def sc_career(b, only):
    for ch in ("roccia", "algidone"):
        c = new_cap(b, only)
        c.ev(f"S.p.char='{ch}';persist()")
        c.p.reload(); c.p.wait_for_selector("#rsi"); enter_menu(c)
        c.click("#career", 500)
        c.shot(f"career-modal-{ch}")
        c.close()


def sc_options(b, only):
    c = new_cap(b, only)
    enter_menu(c); go_tile(c, "opt")
    c.shot("opt-generali")
    for acc in c.ev("[...document.querySelectorAll('details.acc')].map(d=>d.dataset.acc)"):
        c.click(f"details.acc[data-acc={acc}] > summary", 300)
        c.shot(f"opt-generali-{acc}")
    for _ in range(5):
        c.p.click("#ver", timeout=3000); c.p.wait_for_timeout(120)
    c.p.wait_for_timeout(300)
    c.shot("opt-login-modal")
    c.close()


def sc_options_dev(b, only):
    c = new_cap(b, only, dev=True)
    enter_menu(c); go_tile(c, "opt")
    c.click("[data-otab=dev]", 400)
    c.shot("dev-tab")
    accs = c.ev("[...document.querySelectorAll('details.acc')].map(d=>d.dataset.acc)")
    for acc in accs:
        c.click(f"details.acc[data-acc={acc}] > summary", 300)
        c.ev(f"document.querySelector('details.acc[data-acc={acc}]').scrollIntoView()")
        c.shot(f"dev-acc-{acc}")
    c.ev("(()=>{go('menu')})()")
    c.shot("dev-menu-home", 500)
    c.close()


def sc_wish(b, only):
    for ch in ("roccia", "algidone"):
        c = new_cap(b, only)
        c.ev(f"S.p.char='{ch}';persist()")
        c.p.reload(); c.p.wait_for_selector("#rsi"); enter_menu(c)
        go_tile(c, "wish")
        for tab, tid in (("planes", "planes"), ("rocks", "rocks"), ("player", "player"), ("games", "games")):
            c.click(f"[data-tab={tab}]", 500)
            name = {"planes": "enemies", "rocks": "items", "player": "giocatore-locked", "games": "giochi-locked"}[tid]
            if ch == "algidone" and tid in ("player", "games"):
                continue  # identical to the roccia one in a fresh save
            c.shot(f"wish-{name}-{ch}" if tid in ("planes", "rocks") else f"wish-{name}")
        c.close()
    # Sblocca tutto (dev overlay) for Giocatore / Giochi
    c = new_cap(b, only, dev=True)
    enter_menu(c); sim_on(c); dev_view_off(c)
    go_tile(c, "wish")
    c.click("[data-tab=player]", 500); c.shot("wish-giocatore-unlocked")
    c.click("[data-tab=games]", 500); c.shot("wish-giochi-unlocked")
    c.close()


def sc_achievements(b, only):
    c = new_cap(b, only)
    enter_menu(c); c.click("#trop", 500)
    cats = c.ev("[...document.querySelectorAll('[data-atab]')].map(x=>x.dataset.atab)")
    for k in cats:
        c.click(f"[data-atab={k}]", 300)
        c.shot(f"ach-{k}")
    c.close()


def sc_road(b, only):
    c = new_cap(b, only)
    enter_menu(c); c.click("#road", 800)
    c.shot("road-top-current")
    c.ev("document.querySelector('#roadwrap').scrollTop=0")
    c.shot("road-scrolled-top")
    c.close()
    # tile 3 (professor seen) -> milestone popup on the menu, then claimable tile, gift closed/open
    seed = json.loads(json.dumps(MID_SAVE)); seed["p"]["pr"] = {"visits": 1, "seen": True}
    c = Cap(b, only, seed=seed).open()
    enter_menu(c)
    c.p.wait_for_selector("#popg", timeout=4000)
    c.shot("popup-milestone-real")
    c.click("#popg", 800)  # "Guarda" -> Percorso with the tile highlighted
    c.shot("road-claimable-tile")
    c.click("[data-road='3']", 900)
    c.shot("gift-closed")
    c.click("#giftbox", 1500)
    c.shot("gift-opened")
    c.click("#giftok", 500)
    c.shot("road-after-claim")
    c.close()


def sc_popups(b, only):
    c = new_cap(b, only, dev=True)
    enter_menu(c)
    for t in ("asset", "char", "game", "milestone"):
        c.ev(f"popPreview('{t}')")
        c.shot(f"popup-{t}", 500)
        c.click("#popd", 300)
    c.ev("document.getElementById('capstyle').remove()")
    c.ev("popPreview('ach')")
    c.shot("popup-achievement", 600)
    c.close()


def sc_cust(b, only):
    seed = json.loads(json.dumps(MID_SAVE))
    seed["p"]["ch"]["roccia"]["skins"] = ["geka"]; seed["p"]["ch"]["algidone"]["skins"] = ["bk"]
    for ch in ("roccia", "algidone"):
        c = Cap(b, only, seed=seed).open()
        enter_menu(c); go_tile(c, "wish")
        c.click("[data-tab=player]", 400)
        c.shot("wish-giocatore-personalizza") if ch == "roccia" else None
        c.click(f"[data-cust={ch}]", 700)
        c.shot(f"cust-{ch}")
        c.click("[data-skinsel]:not([data-skinsel=''])", 500)
        c.shot(f"cust-{ch}-skin-on")
        c.close()


def sc_export(b, only):
    c = new_cap(b, only, dev=True)
    enter_menu(c); go_tile(c, "opt"); c.click("[data-otab=dev]", 300)
    c.click("details.acc:has(#xopen) > summary", 300)
    c.click("#xopen", 900)
    c.shot("export-dialog")
    c.close()


def dev_jump(c, mapi):
    """Dev run on map <mapi> (0-4 = the five themes, 5-14 = the extra maps) through the dev map select + Vai (E1b: one select, all maps)."""
    go_tile(c, "opt"); c.click("[data-otab=dev]", 300)
    c.click("details.acc:has(#jmsel) > summary", 300)
    c.p.select_option("#jmsel", str(mapi))
    c.click("#jmg", 700)


THEME_KEYS = ["steel", "water", "fire", "ice", "forest"]


def sc_maze(b, only):
    # real run: girone intro card ("Pronti?") + first frames + pause + home with Nuovo gioco / Hardcore
    c = new_cap(b, only)
    c.ev("S.p.g5=false;persist()"); c.p.reload(); c.p.wait_for_selector("#rsi"); enter_menu(c)
    c.shot("menu-home-fresh", 400)
    c.ev("S.p.g5=true;persist()"); c.p.reload(); c.p.wait_for_selector("#rsi"); enter_menu(c)
    c.shot("menu-home-nuovo-hardcore", 400)
    go_tile(c, "new")
    c.shot("maze-intro-roccia", 400)
    c.p.wait_for_timeout(3200)
    c.shot("maze-play-roccia", 100)
    c.click("#ps", 500)
    c.shot("maze-pause")
    c.close()
    # the five map themes, Uomo roccia (dev runs: no progress written)
    for i, k in enumerate(THEME_KEYS):
        c = new_cap(b, only, dev=True)
        enter_menu(c); dev_jump(c, i)
        c.p.wait_for_timeout(3200)
        c.shot(f"maze-{k}-roccia", 100)
        if k == "steel":
            c.click("#pz", 600)
            c.shot("maze-acciaio-roccia", 200)
        c.close()
    # Algidone on fire + Cinghiale
    c = new_cap(b, only, dev=True)
    c.ev("S.p.char='algidone';persist()"); c.p.reload(); c.p.wait_for_selector("#rsi"); enter_menu(c)
    dev_jump(c, 2)
    c.p.wait_for_timeout(3200)
    c.shot("maze-fire-algidone", 100)
    c.click("#pz", 600)
    c.shot("maze-cinghiale-algidone", 200)
    c.close()
    # Partita finita: dev run, last life lost (state forced: waiting for enemies to kill a bot is flaky)
    c = new_cap(b, only, dev=True)
    enter_menu(c)
    go_tile(c, "opt"); c.click("[data-otab=dev]", 300)
    c.click("details.acc:has(#jg4) > summary", 300); c.click("#jg4", 900)
    c.p.wait_for_timeout(3000)
    c.ev("G.lives=1;G.state='dying';G.t=0")
    c.p.wait_for_timeout(900)
    c.shot("maze-over")
    c.close()


BJ_JS = "(()=>{if(typeof B==='undefined'||!B)return null;return {menu:B.menu?B.menu.map(i=>i.id).join(','):'',say:(document.getElementById('btxt')||{}).innerText||'',banner:B.banner?JSON.stringify(B.banner):'',dead:!!B.dead}})()"


def bj_pick(c, mid):
    idx = c.ev(f"B.menu.findIndex(i=>i.id==='{mid}')")
    c.click(f".bmi[data-mi='{idx}']", 400)


def sc_bj(b, only):
    """El Gamblador through the dev button (dev run, 1000 punti): the invite + the table flow, driven by polling the state."""
    c = new_cap(b, only, dev=True)
    enter_menu(c)
    go_tile(c, "opt"); c.click("[data-otab=dev]", 300)
    c.click("details.acc:has(#mggam) > summary", 300); c.click("#mggam", 700)
    c.p.wait_for_selector("#bp-yes", timeout=8000)
    c.shot("bj-invite", 600)
    c.click("#bp-yes", 300)
    seen = set(); t0 = time.time()
    while time.time() - t0 < 90:
        st = c.ev(BJ_JS)
        if not st or st["dead"]:
            break
        m = st["menu"]
        if "bj-line" not in seen and st["say"].strip() and not m:
            seen.add("bj-line"); c.shot("bj-dealer-line", 100)
        if m.startswith("hit") and "bj-table" not in seen:
            seen.add("bj-table"); c.shot("bj-table-hand", 200)
            bj_pick(c, "stand"); continue
        if m.startswith("hit"):
            bj_pick(c, "stand"); continue
        if st["banner"] and "bj-result" not in seen:
            seen.add("bj-result"); c.shot("bj-result", 400)
        if m.startswith("deal") and "bj-menu" not in seen:
            seen.add("bj-menu"); c.shot("bj-menu-again", 200)
            bj_pick(c, "raise"); continue
        if m.startswith("minus") and "bj-raise" not in seen:
            seen.add("bj-raise"); bj_pick(c, "plus"); bj_pick(c, "plus"); c.shot("bj-raise-stake", 200)
            bj_pick(c, "back"); continue
        if m.startswith("deal") and "bj-raise" in seen:
            bj_pick(c, "leave"); break
        if not m and st["say"].strip() and "bj-line" in seen:
            c.p.keyboard.press("Enter")  # Enter advances the dealer line (a stage click works too: the I3 crash was two capture runs at once, not the game)
        time.sleep(0.5)
    for want in ("bj-line", "bj-table", "bj-result", "bj-menu", "bj-raise"):
        if want not in seen:
            NOT_CAPTURED.append((want, "state not reached in the scripted hand (random deal)"))
    c.close()


PR_JS = ("(()=>{if(typeof PR==='undefined'||!PR)return null;const P=PR.pb;return {menu:PR.menu?PR.menu.items.join('|'):'',"
         "say:PR.say?PR.say.text:'',done:PR.say?!!PR.say.done:false,ask:(P&&P.ask)?P.ask.kind:'',pb:!!P,dead:!!PR.dead,"
         "ptx:(P&&P.txt)?P.txt.text:'',ptxdone:(P&&P.txt)?!!P.txt.done:false,pwait:!!(P&&P.w&&P.w.hold==null),"
         "won:!!(P&&P.B&&P.B.over&&P.B.over.winner==='own')}})()")


def sc_pr(b, only):
    """Professor: real "Roccia no" entry, question, si-branch dialogue, battle (command / bag / team / moves), win ending."""
    c = new_cap(b, only, seed=None)
    c.click("#rno", 600)
    seen, lines, last_say, pending = set(), 0, "", False
    t0 = time.time()
    while time.time() - t0 < 150:
        try:
            st = c.ev(PR_JS)
        except Exception:
            break
        if not st or st["dead"]:
            break
        if st["menu"]:
            if "pr-choice" not in seen:
                seen.add("pr-choice"); c.shot("pr-choice-menu", 200)
            c.click(".pmi[data-pi='1']", 300)  # "Si" (index 1) on the first question
            continue
        ask = st["ask"]
        if ask == "cmd":
            if "pb-command" not in seen:
                seen.add("pb-command"); c.shot("pb-command", 500)
                c.click("[data-bm='bag']", 300); c.shot("pb-bag", 700)
                time.sleep(1.2); continue
            if "pb-team" not in seen:
                seen.add("pb-team"); c.click("[data-bm='team']", 300); c.shot("pb-team", 700)
                time.sleep(1.2); continue
            c.click("[data-bm='fight']", 300); continue
        if ask == "mv":
            if "pb-move" not in seen:
                seen.add("pb-move"); c.shot("pb-move-panel", 300)
            c.ev("PR.pb.B.foe.hp=1")  # the next hit ends the battle (win ending)
            c.click("[data-bv='0']", 300); continue
        if ask == "yn":
            if "pb-win-yn" not in seen:
                seen.add("pb-win-yn"); c.shot("pb-win-question", 300)
            c.click("[data-by='1']", 300)  # "no": back to the menu instead of a new run
            break
        if st["pb"]:
            if st["won"] and st["ptxdone"] and "pb-win" not in seen and st["ptx"] == c.ev("pbT('pb_ui_win1')"):
                seen.add("pb-win"); c.shot("pb-win-ending", 100)
            if st["pwait"]:
                c.p.keyboard.press("Enter")
            time.sleep(0.4); continue
        say = st["say"]
        if say != last_say:
            last_say = say; pending = bool(say)
            if pending:
                lines += 1
        if say and st["done"] and pending:
            pending = False
            name = {1: "pr-dialogue-question", 4: "pr-dialogue-yes", 6: "pr-dialogue-angry"}.get(lines)
            if name:
                c.shot(name, 100)
        if say and st["done"]:
            c.p.keyboard.press("Enter")
        time.sleep(0.4)
    for want in ("pb-command", "pb-move", "pb-win", "pb-win-yn"):
        if want not in seen:
            NOT_CAPTURED.append((want, "not reached by the scripted battle"))
    c.close()


def sc_prkick(b, only):
    """Throw-out scene (night street) and pond, via the dev button Professore · cacciata (dev test run)."""
    c = new_cap(b, only, dev=True)
    enter_menu(c); dev_button(c, "#mgrok")
    t = 0.0
    for id_, at in (("pr-throwout-club", 0.9), ("pr-throwout-street", 2.3), ("pr-pond", 3.6)):
        time.sleep(at - t); t = at
        c.shot(id_, 0)
    c.close()


def wait_fa(c, state, secs=15):
    t0 = time.time()
    while time.time() - t0 < secs:
        if c.ev("typeof FA!=='undefined'&&FA&&FA.state") == state:
            return True
        time.sleep(0.2)
    return False


def dev_button(c, sel):
    go_tile(c, "opt"); c.click("[data-otab=dev]", 300)
    c.click(f"details.acc:has({sel}) > summary", 300)
    c.click(sel, 500)


def sc_fa(b, only):
    """Ferma Algidone!: dev buttons per floor (test runs, nothing saved); invite via faInvite in a dev maze run."""
    for n, sel in ((1, "#mgfa"), (2, "#mgfa2"), (3, "#mgfa4")):
        c = new_cap(b, only, dev=True)
        enter_menu(c); dev_button(c, sel)
        if wait_fa(c, "intro", 5):
            c.shot(f"fa-intro-floor{n}", 300)
        wait_fa(c, "play", 8)
        time.sleep(2.5)
        c.shot(f"fa-floor{n}-play", 100)
        if n == 1:
            c.click("#fap", 500)
            c.shot("fa-pause", 300)
            c.ev("faPause(false)")
            c.ev("faOver()")
            c.shot("fa-game-over", 700)
        c.close()
    # floor win panel (floor-1 exit test) and final panel (floor-3 collapse test)
    c = new_cap(b, only, dev=True)
    enter_menu(c); dev_button(c, "#mgfk")
    if wait_fa(c, "win", 25):
        time.sleep(1.5)
        c.shot("fa-floor-win-panel", 500)
    else:
        NOT_CAPTURED.append(("fa-floor-win-panel", "test exit did not reach the win state in time"))
    c.close()
    c = new_cap(b, only, dev=True)
    enter_menu(c); dev_button(c, "#mgfk2")
    if wait_fa(c, "win", 30) or wait_fa(c, "over", 1):
        time.sleep(1.5)
        c.shot("fa-final-panel", 500)
    else:
        NOT_CAPTURED.append(("fa-final-panel", "collapse test did not reach the final panel in time"))
    c.close()
    # invite: same modal the maze shows in the gap between gironi (faInvite called from a dev run at girone 4)
    c = new_cap(b, only, dev=True)
    enter_menu(c)
    go_tile(c, "opt"); c.click("[data-otab=dev]", 300)
    c.click("details.acc:has(#jg4) > summary", 300); c.click("#jg4", 900)
    time.sleep(2)
    c.ev("faInvite({forced:false,dev:true,n:1,mult5:false})")
    c.shot("fa-invite", 500)
    c.close()


def sc_bug(b, only):
    """Segnala un bug (F6a): the popup from the home menu (dev session seeded with the Firebase stub)."""
    c = new_cap(b, only, dev=True)
    enter_menu(c)
    c.click("#bugb", 400)
    c.p.fill("#bgt", "Il pulsante non risponde dopo la pausa.")
    c.shot("bug-popup", 200)
    c.p.keyboard.press("Escape"); time.sleep(0.3)
    if c.wants("dev-textedit-popup"):  # F5: long-press (3 s) on a menu tile label
        r = c.ev("(()=>{const r=document.querySelector('[data-tile=wish] span').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()")
        c.p.mouse.move(r[0], r[1]); c.p.mouse.down(); time.sleep(3.4); c.p.mouse.up()
        c.shot("dev-textedit-popup", 300)
        c.p.keyboard.press("Escape"); time.sleep(0.3)
    c.ev("go('bye')"); c.shot("bye-goodbye", 300)
    c.ev("go('sad')"); c.shot("sad-countdown", 200)  # legacy screen, not reachable from the UI: shown through go()
    c.close()


SCENARIOS = [sc_splash_menu, sc_career, sc_options, sc_options_dev, sc_wish, sc_achievements, sc_road, sc_popups, sc_cust, sc_export, sc_maze, sc_bj, sc_pr, sc_prkick, sc_fa, sc_bug]


def optimize():
    from PIL import Image
    tot = 0
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".png"):
            continue
        p = os.path.join(OUT, f)
        im = Image.open(p).convert("RGB")
        im.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(p, optimize=True)
        tot += os.path.getsize(p)
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--sc", nargs="*", default=[], help="only scenarios whose function name contains one of these")
    ap.add_argument("--no-optimize", action="store_true")
    a = ap.parse_args()
    srv = serve()
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required", "--disable-dev-shm-usage"])
        for sc in SCENARIOS:
            if a.sc and not any(x in sc.__name__ for x in a.sc):
                continue
            print(sc.__name__)
            try:
                sc(b, a.only)
            except Exception as e:  # keep going: a failed scenario is reported, not fatal
                print("  !! FAILED", sc.__name__, str(e).splitlines()[0][:200])
                NOT_CAPTURED.append((sc.__name__, "script failure: " + str(e).splitlines()[0][:120]))
        b.close()
    srv.shutdown()
    if not a.no_optimize:
        print("optimized bytes:", optimize())
    print("captured", len(DONE), "screens")
    if NOT_CAPTURED:
        print("NOT CAPTURED:", NOT_CAPTURED)


if __name__ == "__main__":
    main()
