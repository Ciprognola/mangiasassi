#!/usr/bin/env python3
"""F4a headless tests (Firebase stub): skin tool part 1, character sheet export.
Run: python tools/fbstub/test_f4a.py"""
import json, os, subprocess, sys, zipfile, io
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "screens"))
import capture as C, fbstub
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

RES = []
DEVC = {"role": "master", "acct": "master", "fb": True, "devOn": True}
ALL_KEYS_ROCCIA = {"f0", "f1", "f2", "f3", "e0", "e1", "fd0", "fd1", "fd2", "fd3", "fd_e0", "fd_e1", "fu0", "fu1", "fu2", "fu3", "fu_e0", "fu_e1"}
# F4a2: Ferma Algidone! thrower frames (alg_*, in FAIMG) join Algidone's own base frames (al_*, in IMG/SPR2)
ALL_KEYS_ALGIDONE = ({"al_st"} | {"al_w%d" % i for i in range(8)} | {"al_r%d" % i for i in range(8)} | {"al_d0", "al_d1", "al_d2", "al_d3", "al_d_st"} | {"al_u%d" % i for i in range(6)}
                     | {"alg_kick%d" % i for i in range(3)} | {"alg_eat%d" % i for i in range(3)} | {"alg_angry%d" % i for i in range(2)} | {"alg_throw%d" % i for i in range(4)} | {"alg_idle%d" % i for i in range(2)})


def check(name, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name, extra, flush=True)


def page(b, dev=True, has_touch=False, **kw):
    ctx = b.new_context(viewport=C.VIEW, has_touch=has_touch, accept_downloads=True)
    if dev:
        ctx.add_init_script("localStorage.setItem('mgs_dev',%s)" % json.dumps(json.dumps(DEVC)))
        kw.setdefault("session", "master")
    fbstub.install(ctx, **kw)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    return ctx, p, errs


def menu(p):
    p.goto(C.BASE + "index.html"); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(800)


def open_skins_acc(p, touch=False):
    p.evaluate("go('opt')"); p.wait_for_timeout(250)
    if touch:
        p.tap("[data-otab=dev]")
    else:
        p.click("[data-otab=dev]")
    p.wait_for_timeout(200)
    if not p.evaluate("document.querySelector('details.acc:has(#skinExpGo)').open"):
        sel = "details.acc:has(#skinExpGo) > summary"
        p.tap(sel) if touch else p.click(sel)
    p.wait_for_timeout(200)


def export_sheet(p, char, touch=False):
    sel = "[data-skinchar='%s']" % char
    if touch:
        p.tap(sel)
    else:
        p.click(sel)
    p.wait_for_timeout(150)
    with p.expect_download(timeout=20000) as dl_info:
        (p.tap if touch else p.click)("#skinExpGo")
    dl = dl_info.value
    data = open(dl.path(), "rb").read()
    return dl.suggested_filename, data


def frame_keys_used(char):
    return ALL_KEYS_ROCCIA if char == "roccia" else ALL_KEYS_ALGIDONE


def launch_browser(pw):
    """Some sandboxes preinstall a Chromium revision older than this pip playwright expects
    (see the environment's own note re: PLAYWRIGHT_BROWSERS_PATH). Fall back to whatever
    chrome-linux/chrome is actually on disk before giving up."""
    try:
        return pw.chromium.launch()
    except Exception:
        import glob
        base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
        cands = glob.glob(os.path.join(base, "chromium-*", "chrome-linux", "chrome")) if base else []
        if cands:
            return pw.chromium.launch(executable_path=cands[0])
        raise


srv = C.serve()
with sync_playwright() as pw:
    b = launch_browser(pw)
    # ------------------------------------------------------------ hidden without a dev session / dev mode off
    ctx, p, errs = page(b, dev=False); menu(p)
    p.evaluate("go('opt')"); p.wait_for_timeout(250)
    check("logged out: no Sviluppatore tab at all", not p.evaluate("!!document.querySelector('[data-otab=dev]')"))
    ctx.close()
    ctx, p, errs = page(b); menu(p)
    p.click("#devt"); p.wait_for_timeout(200)  # dev mode off (still logged in as master)
    p.evaluate("go('opt')"); p.wait_for_timeout(250)
    check("dev mode off: no Sviluppatore tab", not p.evaluate("!!document.querySelector('[data-otab=dev]')"))
    p.evaluate("go('menu')"); p.wait_for_timeout(200); p.click("#devt"); p.wait_for_timeout(200)
    open_skins_acc(p)
    check("dev on: Costumi accordion present with both character buttons + export button", p.evaluate("!!document.querySelector('[data-skinchar=roccia]') && !!document.querySelector('[data-skinchar=algidone]') && !!document.querySelector('#skinExpGo')"))
    check("no console errors so far", not errs, errs)
    ctx.close()
    # ------------------------------------------------------------ non-master dev role also sees it (devUI() is role-agnostic, not master-only)
    ctx, p, errs = page(b, session="dev3")
    ctx.add_init_script("localStorage.setItem('mgs_dev',%s)" % json.dumps(json.dumps({"role": "dev3", "acct": "dev3", "fb": True, "devOn": True})))
    menu(p); open_skins_acc(p)
    check("dev1..dev5 role (not master) also sees the Costumi accordion", p.evaluate("!!document.querySelector('#skinExpGo')"))
    ctx.close()
    # ------------------------------------------------------------ export both characters (desktop, real clicks), inspect the zip
    all_frame_keys = {}
    for char in ("roccia", "algidone"):
        ctx, p, errs = page(b); menu(p); open_skins_acc(p)
        fname, data = export_sheet(p, char)
        expect_folder = "uomo_roccia" if char == "roccia" else "algidone"
        check(char + ": filename follows <char>_foglio_<VERSION>.zip", fname == expect_folder + "_foglio_" + p.evaluate("VERSION") + ".zip", fname)
        z = zipfile.ZipFile(io.BytesIO(data))
        names = set(z.namelist())
        cj = json.loads(z.read(expect_folder + "_cells.json"))
        n_sheets = len(cj["sheets"])
        expect_names = {expect_folder + "_cells.json", "LEGGIMI.txt"}
        for sh in cj["sheets"]:
            expect_names.add(sh["guide"]); expect_names.add(sh["drawHere"])
        check(char + ": zip has exactly GUIDE/DRAW_HERE (per sheet)/cells.json/LEGGIMI.txt", names == expect_names, names)
        check(char + ": cells.json schema/char/skin/mode/scale/margin fields", cj.get("schema") == 1 and cj.get("char") == expect_folder and cj.get("skin") == "nuovo" and cj.get("mode") == "overlay" and cj.get("scale") == 4 and cj.get("margin") == .25, cj.get("schema"))
        # every PNG <= 4096px per side and under 16M pixels; DRAW_HERE fully transparent; same size as its GUIDE
        guides = {}
        sizes_ok = True; pix_ok = True; transp_ok = True; pair_ok = True
        for sh in cj["sheets"]:
            g = Image.open(io.BytesIO(z.read(sh["guide"]))); dh = Image.open(io.BytesIO(z.read(sh["drawHere"])))
            guides[sh["n"]] = g
            if g.width > 4096 or g.height > 4096 or dh.width > 4096 or dh.height > 4096: sizes_ok = False
            if g.width * g.height >= 16_000_000 or dh.width * dh.height >= 16_000_000: pix_ok = False
            if dh.convert("RGBA").getchannel("A").getextrema() != (0, 0): transp_ok = False
            if dh.size != g.size: pair_ok = False
        check(char + ": every PNG <= 4096px per side (" + str(n_sheets) + " sheet(s))", sizes_ok, [cj["sheets"]])
        check(char + ": every canvas stays under 16M pixels", pix_ok)
        check(char + ": every DRAW_HERE.png fully transparent", transp_ok)
        check(char + ": every DRAW_HERE.png matches its GUIDE.png size", pair_ok)
        # every key in cells.json exists in the build (IMG or FAIMG -- F4a2 thrower frames live in FAIMG); no cross-character keys
        real_keys = set(cj["frames"].keys())
        ref_keys = {r["key"] for r in cj["refs"]}
        skip_keys = {s["key"] for s in cj["skipped"]}
        exist = p.evaluate("(ks)=>ks.every(k=>!!(skinBaseImg(k)&&skinBaseImg(k).width))", list(real_keys | skip_keys))
        check(char + ": every frame/skipped key exists in IMG or FAIMG (this build)", exist)
        other = frame_keys_used("algidone" if char == "roccia" else "roccia")
        check(char + ": no cross-character keys (nothing from the other character's frame set)", not (real_keys | skip_keys) & other, (real_keys | skip_keys) & other)
        check(char + ": real+skipped keys cover the full documented set", (real_keys | skip_keys) == frame_keys_used(char), (real_keys | skip_keys) ^ frame_keys_used(char))
        check(char + ": ref cells are grey/'SOLO RIFERIMENTO' entries, never in frames", len(ref_keys) > 0 and not (ref_keys & real_keys))
        if char == "algidone":
            ferma_keys = {k for k in real_keys if k.startswith("alg_")}
            check("algidone: Ferma Algidone! thrower row present (13 real alg_* frames, alg_kick0 skipped)", len(ferma_keys) == 13 and "alg_kick0" not in real_keys and "alg_kick0" in skip_keys, ferma_keys)
            check("algidone: no roccia keys leaked into the Ferma row or anywhere else", not real_keys & ALL_KEYS_ROCCIA)
        # base rect in GUIDE == live frame at x4 for every real frame. Both sides are composited onto the
        # same flat grey backdrop before comparing (the GUIDE's own bg colour) with a tolerance of 1/255 per
        # channel: the GUIDE composites in the browser's canvas compositor, the reference composites in PIL,
        # and the two round semi-transparent (anti-aliased) sprite-edge pixels a shade differently -- a real
        # positioning/scaling bug would show up as a large difference, not a +-1 rounding artifact.
        import base64
        worst = 0; worst_key = None
        for onek in real_keys:
            fr = cj["frames"][onek]; base = fr["base"]; guide = guides[fr.get("sheet", 1)]
            crop = guide.convert("RGBA").crop((base["x"], base["y"], base["x"] + base["w"], base["y"] + base["h"]))
            fresh_b64 = p.evaluate("([k,w,h])=>{const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.imageSmoothingEnabled=false;x.drawImage(skinBaseImg(k),0,0,w,h);return c.toDataURL()}", [onek, base["w"], base["h"]])
            fresh = Image.open(io.BytesIO(base64.b64decode(fresh_b64.split(",", 1)[1]))).convert("RGBA")
            bg = Image.new("RGBA", fresh.size, tuple(crop.getpixel((0, 0)))[:3] + (255,))
            composited = Image.alpha_composite(bg, fresh)
            diff = ImageChops.difference(crop.convert("RGB"), composited.convert("RGB"))
            mx = max(diff.getextrema(), key=lambda ch: ch[1])[1] if diff.getbbox() else 0
            if mx > worst: worst, worst_key = mx, onek
        check(char + ": GUIDE base rect pixel-matches the live frame at x4 for every real frame (<=1/255 rounding tolerance)", worst <= 1, (worst_key, worst))
        all_frame_keys[char] = (cj, z, data)
        check(char + ": no console errors", not errs, errs)
        ctx.close()
    # ------------------------------------------------------------ mobile touch
    ctx, p, errs = page(b, has_touch=True); menu(p); open_skins_acc(p, touch=True)
    fname, data = export_sheet(p, "algidone", touch=True)
    check("mobile touch: export works (tap character button + tap Scarica foglio)", fname.startswith("algidone_foglio_") and len(data) > 1000, fname)
    check("mobile touch: no console errors", not errs, errs)
    ctx.close()
    # ------------------------------------------------------------ coverage lines in the accordion (F4a2 3b)
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    roc_cov = p.evaluate("skinCoverage('roccia')")
    check("coverage: GEKA covers all 10 of roccia's real frames (0 mancano)", len(roc_cov) == 1 and roc_cov[0]["id"] == "geka" and roc_cov[0]["have"] == roc_cov[0]["total"] == 10 and not roc_cov[0]["missing"], roc_cov)
    p.click("[data-skinchar='algidone']"); p.wait_for_timeout(150)
    alg_cov = p.evaluate("skinCoverage('algidone')")
    check("coverage: BK is missing exactly the 13 new Ferma thrower frames (grandfathered gap)", len(alg_cov) == 1 and alg_cov[0]["id"] == "bk" and alg_cov[0]["total"] == 40 and alg_cov[0]["have"] == 27 and set(alg_cov[0]["missing"]) == {k for k in ALL_KEYS_ALGIDONE if k.startswith("alg_") and k != "alg_kick0"}, alg_cov)
    txt = p.evaluate("document.body.innerText")
    check("coverage: the accordion body actually shows the BK line with a frame count", "Costume BK" in txt and "27/40" in txt)
    check("no console errors (coverage)", not errs, errs)
    ctx.close()
    # ------------------------------------------------------------ thrower skin hook (F4a2 2): DEV_SKIN_TEST overlay/replace change the thrower;
    # a real skin with no alg_* art (BK today) renders pixel-identical to no skin at all (0.4_8 baseline)
    ctx, p, errs = page(b); menu(p)
    p.evaluate("go('opt')"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(200)
    p.click("details.acc:has(#mgfa) > summary"); p.wait_for_timeout(200); p.click("#mgfa"); p.wait_for_timeout(2500)
    p.evaluate("window.requestAnimationFrame=()=>0;cancelAnimationFrame(FA.raf);FA.alg.state='throw';FA.alg.t=0;")
    # crop just the thrower's own box (the full canvas also has the roccia climber, whose own skin test would
    # otherwise change the snapshot too and give a false positive/negative for this thrower-only check)
    snap = """()=>{
      faDraw();
      const pose=faAlgPose(),im=pose.im,w=im.width*FA_PHYS.algK,h=im.height*FA_PHYS.algK,pad=w*.6;
      const c=document.getElementById('fac'),k=c.width/FA_W;
      const bx=(pose.x-pad)*k,by=(pose.y-h-pad)*k,bw=(w+2*pad)*k,bh=(h+2*pad)*k;
      const oc=document.createElement('canvas');oc.width=bw;oc.height=bh;
      oc.getContext('2d').drawImage(c,bx,by,bw,bh,0,0,bw,bh);
      return oc.toDataURL();
    }"""
    base_shot = p.evaluate(snap)
    p.evaluate("S.p.ch.algidone.skin='bk'"); bk_shot = p.evaluate(snap); p.evaluate("S.p.ch.algidone.skin=null")
    check("thrower: BK equipped (no alg_* art yet) renders pixel-identical to no skin", bk_shot == base_shot)
    p.evaluate("DEV_SKIN_TEST={char:'algidone',mode:'overlay'}"); overlay_shot = p.evaluate(snap)
    p.evaluate("DEV_SKIN_TEST={char:'algidone',mode:'replace'}"); replace_shot = p.evaluate(snap)
    p.evaluate("DEV_SKIN_TEST=null"); restored_shot = p.evaluate(snap)
    check("thrower: DEV_SKIN_TEST overlay changes the thrower's rendering", overlay_shot != base_shot)
    check("thrower: DEV_SKIN_TEST replace changes the thrower's rendering", replace_shot != base_shot)
    check("thrower: overlay and replace look different from each other", overlay_shot != replace_shot)
    check("thrower: turning DEV_SKIN_TEST off restores the exact original pixels", restored_shot == base_shot)
    p.evaluate("DEV_SKIN_TEST={char:'roccia',mode:'replace'}"); roccia_test_shot = p.evaluate(snap); p.evaluate("DEV_SKIN_TEST=null")
    check("thrower: roccia's own DEV_SKIN_TEST does not touch the (algidone) thrower", roccia_test_shot == base_shot)
    check("no console errors (thrower hook)", not errs, errs)
    ctx.close()
    # ------------------------------------------------------------ real Ferma run from the Giochi card (not a dev button)
    ctx, p, errs = page(b); menu(p)
    p.evaluate("S.p.fa=S.p.fa||{};S.p.fa.seen=true")
    p.evaluate("go('wish')"); p.wait_for_timeout(200); p.evaluate("tab='games';render()"); p.wait_for_timeout(200)
    check("Giochi card: Ferma Algidone! unlocked with a 'Gioca' button (not a dev-only path)", p.evaluate("!!document.querySelector('[data-fagame]')"))
    p.click("[data-fagame]"); p.wait_for_timeout(2500)
    check("real Ferma run started from the Giochi card", p.evaluate("screen") == "fa" and p.evaluate("!!FA"))
    check("no console errors (real Ferma run)", not errs, errs)
    ctx.close()
    # ------------------------------------------------------------ toggling character keeps the accordion open, doesn't touch the save
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    save_before = p.evaluate("JSON.stringify(S)")
    p.click("[data-skinchar='algidone']"); p.wait_for_timeout(150)
    check("switching character keeps the Costumi accordion open", p.evaluate("document.querySelector('details.acc:has(#skinExpGo)').open"))
    export_sheet(p, "roccia")
    check("export never touches the save (S unchanged)", p.evaluate("JSON.stringify(S)") == save_before)
    check("no console errors (toggle/export)", not errs, errs)
    ctx.close()
    # ------------------------------------------------------------ smoke: a run still starts, no regressions
    ctx, p, errs = page(b); menu(p); p.click("[data-tile=new]"); p.wait_for_timeout(1500)
    check("a run starts (smoke)", p.evaluate("screen") == "game")
    check("no console errors (smoke)", not errs, errs)
    ctx.close()
    b.close()
srv.shutdown()

# ------------------------------------------------------------ cut_from_cells.py: F4a round trip + legacy geka/bk still work
cutter = os.path.join(ROOT, "refs", "skins", "cut_from_cells.py")
work = "/tmp/f4a_cut_test"
if os.path.isdir(work):
    import shutil; shutil.rmtree(work)
os.makedirs(work, exist_ok=True)

from PIL import ImageDraw
for char, (cj, z, data) in all_frame_keys.items():
    folder = cj["char"]
    # a real sheet may be split into several numbered pages (F4a2: algidone's Ferma row pushed it to 2):
    # cut_from_cells.py works one sheet+cells.json+image at a time, so each page is sliced into its own
    # cells.json (that page's own frames + its own sheet{w,h}) and cut against that page's own PNG.
    by_sheet = {}
    for k, c in cj["frames"].items():
        by_sheet.setdefault(c.get("sheet", 1), {})[k] = c
    all_ok_sizes = True; all_ok_run = True; any_offsets = False
    for sh in cj["sheets"]:
        frames_n = by_sheet.get(sh["n"], {})
        if not frames_n: continue
        sub_cj = dict(cj); sub_cj["sheet"] = {"w": sh["w"], "h": sh["h"]}; sub_cj["frames"] = frames_n
        cells_path = os.path.join(work, "%s_%d_cells.json" % (folder, sh["n"]))
        json.dump(sub_cj, open(cells_path, "w"))
        drawn = Image.new("RGBA", (sh["w"], sh["h"]), (0, 0, 0, 0))
        d = ImageDraw.Draw(drawn)
        for k, c in frames_n.items():
            d.rectangle([c["x"], c["y"], c["x"] + c["w"] - 1, c["y"] + c["h"] - 1], fill=(10, 200, 30, 255))
        drawn_path = os.path.join(work, "%s_%d_drawn.png" % (folder, sh["n"]))
        drawn.save(drawn_path)
        out_dir = os.path.join(work, "%s_%d_out" % (folder, sh["n"]))
        r = subprocess.run([sys.executable, cutter, cells_path, drawn_path, out_dir], capture_output=True, text=True)
        if r.returncode != 0: all_ok_run = False
        for k, c in frames_n.items():
            outp = os.path.join(out_dir, "sk_%s_%s.png" % (cj["skin"], k))
            if not os.path.exists(outp):
                all_ok_sizes = False; continue
            im = Image.open(outp)
            expect = (round(c["w"] / cj["scale"]), round(c["h"] / cj["scale"]))
            if im.size != expect:
                all_ok_sizes = False
        if os.path.exists(os.path.join(out_dir, cj["skin"] + "_offsets.json")): any_offsets = True
    check(char + ": cut_from_cells.py round trip runs cleanly on every sheet page", all_ok_run)
    check(char + ": every cut frame comes out at native size (cell size / scale), on every page", all_ok_sizes)
    check(char + ": offsets file written (every F4a frame has a margin-derived ox/oy)", any_offsets)

for skin in ("geka", "bk"):
    cells_path = os.path.join(ROOT, "refs", "skins", skin, skin + "_cells.json")
    cfg = json.load(open(cells_path))
    drawn = Image.new("RGBA", (cfg["sheet"]["w"], cfg["sheet"]["h"]), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(drawn)
    for k, c in cfg["frames"].items():
        d.rectangle([c["x"], c["y"], c["x"] + c["w"] - 1, c["y"] + c["h"] - 1], fill=(200, 30, 10, 255))
    drawn_path = os.path.join(work, skin + "_legacy_drawn.png")
    drawn.save(drawn_path)
    out_dir = os.path.join(work, skin + "_legacy_out")
    r = subprocess.run([sys.executable, cutter, cells_path, drawn_path, out_dir], capture_output=True, text=True)
    check(skin + ": legacy cells.json (no scale/margin) still cuts with the updated script", r.returncode == 0 and str(len(cfg["frames"])) + "/" + str(len(cfg["frames"])) in r.stdout, r.stdout + r.stderr)
    ok = all(Image.open(os.path.join(out_dir, "sk_%s_%s.png" % (skin, k))).size == (c["w"], c["h"]) for k, c in cfg["frames"].items())
    check(skin + ": legacy cut sizes unchanged (== cell size, no downscale)", ok)
    check(skin + ": legacy run writes no offsets.json (scale 1, ox/oy always 0)", not os.path.exists(os.path.join(out_dir, skin + "_offsets.json")))

# ------------------------------------------------------------ node --check on every script block
h = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
import re
blocks = re.findall(r"<script[^>]*>([\s\S]*?)</script>", h)
nodeok = True
for i, blk in enumerate(blocks):
    fp = os.path.join(work, "s%d.js" % i)
    open(fp, "w", encoding="utf-8").write(blk)
    r = subprocess.run(["node", "--check", fp], capture_output=True, text=True)
    if r.returncode != 0:
        nodeok = False; print(r.stderr)
check("node --check passes on every <script> block", nodeok)

print(sum(RES), "/", len(RES), "passed")
sys.exit(0 if all(RES) else 1)
