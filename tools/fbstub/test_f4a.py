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
ALL_KEYS_ALGIDONE = {"al_st"} | {"al_w%d" % i for i in range(8)} | {"al_r%d" % i for i in range(8)} | {"al_d0", "al_d1", "al_d2", "al_d3", "al_d_st"} | {"al_u%d" % i for i in range(6)}


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
        expect_names = {expect_folder + "_GUIDE.png", expect_folder + "_DRAW_HERE.png", expect_folder + "_cells.json", "LEGGIMI.txt"}
        check(char + ": zip has exactly GUIDE/DRAW_HERE/cells.json/LEGGIMI.txt (single sheet)", names == expect_names, names)
        cj = json.loads(z.read(expect_folder + "_cells.json"))
        check(char + ": cells.json schema/char/skin/mode/scale/margin fields", cj.get("schema") == 1 and cj.get("char") == expect_folder and cj.get("skin") == "nuovo" and cj.get("mode") == "overlay" and cj.get("scale") == 4 and cj.get("margin") == .25, cj.get("schema"))
        # every PNG <= 4096px per side
        guide = Image.open(io.BytesIO(z.read(expect_folder + "_GUIDE.png")))
        drawh = Image.open(io.BytesIO(z.read(expect_folder + "_DRAW_HERE.png")))
        check(char + ": GUIDE.png <= 4096px per side", guide.width <= 4096 and guide.height <= 4096, guide.size)
        check(char + ": DRAW_HERE.png <= 4096px per side and same size as GUIDE", drawh.size == guide.size and drawh.width <= 4096 and drawh.height <= 4096, drawh.size)
        # DRAW_HERE fully transparent
        check(char + ": DRAW_HERE.png fully transparent", drawh.convert("RGBA").getchannel("A").getextrema() == (0, 0))
        # every key in cells.json exists in the build; no cross-character keys
        real_keys = set(cj["frames"].keys())
        ref_keys = {r["key"] for r in cj["refs"]}
        skip_keys = {s["key"] for s in cj["skipped"]}
        exist = p.evaluate("(ks)=>ks.every(k=>!!(IMG&&IMG[k]&&IMG[k].width))", list(real_keys | skip_keys))
        check(char + ": every frame/skipped key exists in IMG (this build)", exist)
        other = frame_keys_used("algidone" if char == "roccia" else "roccia")
        check(char + ": no cross-character keys (nothing from the other character's frame set)", not (real_keys | skip_keys) & other, (real_keys | skip_keys) & other)
        check(char + ": real+skipped keys cover the full documented set", (real_keys | skip_keys) == frame_keys_used(char), (real_keys | skip_keys) ^ frame_keys_used(char))
        check(char + ": ref cells are grey/'SOLO RIFERIMENTO' entries, never in frames", len(ref_keys) > 0 and not (ref_keys & real_keys))
        # base rect in GUIDE == live frame at x4 for every real frame. Both sides are composited onto the
        # same flat grey backdrop before comparing (the GUIDE's own bg colour) with a tolerance of 1/255 per
        # channel: the GUIDE composites in the browser's canvas compositor, the reference composites in PIL,
        # and the two round semi-transparent (anti-aliased) sprite-edge pixels a shade differently -- a real
        # positioning/scaling bug would show up as a large difference, not a +-1 rounding artifact.
        import base64
        worst = 0; worst_key = None
        for onek in real_keys:
            base = cj["frames"][onek]["base"]
            crop = guide.convert("RGBA").crop((base["x"], base["y"], base["x"] + base["w"], base["y"] + base["h"]))
            fresh_b64 = p.evaluate("([k,w,h])=>{const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.imageSmoothingEnabled=false;x.drawImage(IMG[k],0,0,w,h);return c.toDataURL()}", [onek, base["w"], base["h"]])
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

for char, (cj, z, data) in all_frame_keys.items():
    folder = cj["char"]
    cells_path = os.path.join(work, folder + "_cells.json")
    json.dump(cj, open(cells_path, "w"))
    drawn = Image.new("RGBA", (cj["sheet"]["w"], cj["sheet"]["h"]), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(drawn)
    for k, c in cj["frames"].items():
        d.rectangle([c["x"], c["y"], c["x"] + c["w"] - 1, c["y"] + c["h"] - 1], fill=(10, 200, 30, 255))
    drawn_path = os.path.join(work, folder + "_drawn.png")
    drawn.save(drawn_path)
    out_dir = os.path.join(work, folder + "_out")
    r = subprocess.run([sys.executable, cutter, cells_path, drawn_path, out_dir], capture_output=True, text=True)
    check(char + ": cut_from_cells.py round trip runs cleanly", r.returncode == 0, r.stdout + r.stderr)
    ok_sizes = True
    for k, c in cj["frames"].items():
        outp = os.path.join(out_dir, "sk_%s_%s.png" % (cj["skin"], k))
        if not os.path.exists(outp):
            ok_sizes = False; continue
        im = Image.open(outp)
        expect = (round(c["w"] / cj["scale"]), round(c["h"] / cj["scale"]))
        if im.size != expect:
            ok_sizes = False
    check(char + ": every cut frame comes out at native size (cell size / scale)", ok_sizes)
    check(char + ": offsets file written (every F4a frame has a margin-derived ox/oy)", os.path.exists(os.path.join(out_dir, cj["skin"] + "_offsets.json")))

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
