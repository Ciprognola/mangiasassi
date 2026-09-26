#!/usr/bin/env python3
"""F4b2 headless tests (Firebase stub): cutter anchoring fix (item 1), exporting the previewed
skin as a developer submission (item 2), DEV_SKIN_TEST fully removed (item 5).
Run: python tools/fbstub/test_f4b2.py"""
import base64, hashlib, io, json, os, shutil, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "screens"))
import capture as C, fbstub
from playwright.sync_api import sync_playwright
from PIL import Image

RES = []
DEVC = {"role": "master", "acct": "master", "fb": True, "devOn": True}
WORK = "/tmp/f4b2_test"
shutil.rmtree(WORK, ignore_errors=True)
os.makedirs(WORK, exist_ok=True)


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


def page(b, dev=True, **kw):
    ctx = b.new_context(viewport=C.VIEW, accept_downloads=True)
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


def open_skins_acc(p):
    p.evaluate("go('opt')"); p.wait_for_timeout(250)
    p.click("[data-otab=dev]"); p.wait_for_timeout(200)
    if not p.evaluate("document.querySelector('details.acc:has(#skinExpGo)').open"):
        p.click("details.acc:has(#skinExpGo) > summary")
    p.wait_for_timeout(200)


def open_export(p):
    p.evaluate("go('opt')"); p.wait_for_timeout(250); p.click("[data-otab=dev]"); p.wait_for_timeout(200)
    if not p.evaluate("document.querySelector('details.acc:has(#xopen)').open"):
        p.click("details.acc:has(#xopen) > summary"); p.wait_for_timeout(200)
    p.click("#xopen"); p.wait_for_timeout(700)


srv = C.serve()
with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ item 1: cutter anchoring + no dark fringes
    # Uses the REAL geometry of this build's own roccia sheet (skinLayout), so it proves the actual
    # margin-rounding fix (item 1), not a hand-picked synthetic size.
    ctx, p, errs = page(b); menu(p)
    layout = p.evaluate("skinLayout('roccia').pages[0]")
    cell = next(c for row in layout["geom"]["laid"] for c in row["cells"] if not c.get("ref"))
    check("item 1: the cell (margin included) is an exact multiple of SKIN_SCALE (4) -- the actual anchoring fix",
          cell["cellW"] % 4 == 0 and cell["cellH"] % 4 == 0 and cell["baseX"] % 4 == 0 and cell["baseY"] % 4 == 0, cell)
    # build a page-sized RGBA buffer: a clean x4-aligned checkerboard covering the WHOLE cell (base rect
    # AND margin), anchored to the base frame's own origin (cell.baseX/baseY) -- native block (nx,ny) gets
    # a deterministic solid colour; one specific block is opaque against fully-transparent neighbours to
    # test premultiplied-alpha "no dark fringe" behaviour.
    import random
    random.seed(3)
    cw, ch, bx, by = cell["cellW"], cell["cellH"], cell["baseX"], cell["baseY"]
    nw, nh = cw // 4, ch // 4
    colours = {}
    for ny in range(nh):
        for nx in range(nw):
            colours[(nx, ny)] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
    halo_nx, halo_ny = nw // 2, nh // 2  # an opaque block surrounded by fully transparent blocks
    colours[(halo_nx, halo_ny)] = (255, 220, 0, 255)
    for dnx, dny in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        colours[(halo_nx + dnx, halo_ny + dny)] = (0, 0, 0, 0)
    page_im = Image.new("RGBA", (layout["w"], layout["h"]), (0, 0, 0, 0))
    px = page_im.load()
    # native block nx/ny (0-based from the cell's own top-left corner) starts at sheet position
    # (nx*4, ny*4) -- valid because the cell width/height are themselves exact multiples of 4 (item
    # 1's fix), so a "clean x4 grid anchored at the cell's own origin" needs no extra offset math.
    for (nx, ny), col in colours.items():
        for yy in range(ny * 4, ny * 4 + 4):
            for xx in range(nx * 4, nx * 4 + 4):
                px[xx, yy] = col
    cell_path = os.path.join(WORK, "anchor_cell.png")
    page_im.save(cell_path)
    js_cut = p.evaluate("""([b64,w,h,cx,cy,cw,ch])=>{
      const bytes=atob(b64),u=new Uint8Array(bytes.length);for(let i=0;i<bytes.length;i++)u[i]=bytes.charCodeAt(i);
      const src=new Uint8ClampedArray(u.buffer);
      const r=skinBoxDownscale(src,w,cx,cy,cw,ch,4);
      return{w:r.w,h:r.h,data:[...r.data]};
    }""", [base64.b64encode(page_im.tobytes()).decode(), layout["w"], layout["h"], 0, 0, cw, ch])
    ok = True; bad = None
    for (nx, ny), col in colours.items():
        idx = (ny * js_cut["w"] + nx) * 4
        got = tuple(js_cut["data"][idx:idx + 4])
        if got != col:
            ok = False; bad = (nx, ny, got, col); break
    check("item 1: a clean x4-aligned drawing round-trips EXACTLY inside the base rect and the margin (no blended colours)", ok, bad)
    halo_idx = (halo_ny * js_cut["w"] + halo_nx) * 4
    check("item 1: an opaque block surrounded by fully-transparent neighbours keeps its exact colour (no dark halo from premultiplied alpha)",
          tuple(js_cut["data"][halo_idx:halo_idx + 4]) == (255, 220, 0, 255), js_cut["data"][halo_idx:halo_idx + 4])
    # same check against the Python reference cutter (cut_from_cells.py), proving both sides anchor identically
    sys.path.insert(0, os.path.join(ROOT, "refs", "skins"))
    import cut_from_cells as CFC
    py_cut = CFC.box_downscale(page_im.crop((0, 0, cw, ch)), 4)
    py_ok = all(py_cut.getpixel((nx, ny)) == col for (nx, ny), col in colours.items())
    check("item 1: the Python cutter (cut_from_cells.py) anchors and round-trips identically to the JS one", py_ok)
    check("no console errors (cutter anchoring)", not errs, errs)
    ctx.close()

    # ============================================================ item 2: export a NEW skin as a submission
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    p.click("[data-skinchar='roccia']"); p.wait_for_timeout(150)
    new_setup = p.evaluate("""()=>{
      const keys=['f0','f1'],frames={};
      for(const k of keys){
        const im=IMG[k],c=document.createElement('canvas');c.width=im.width;c.height=im.height;
        c.getContext('2d').fillStyle='rgba(10,200,30,.8)';c.getContext('2d').fillRect(0,0,c.width,c.height);
        frames[k]=c;
      }
      SKIN_IMPORT_PV={char:'roccia',id:null,mode:'overlay',name:'Tuta Prova',frames,unchanged:new Set()};
      return Object.keys(frames);
    }""")
    open_export(p)
    dialog_txt = p.evaluate("document.querySelector('#modal').innerText")
    check('export: pending preview listed (name, character, mode, new/update, frame count)',
          "Tuta Prova" in dialog_txt and "Uomo roccia" in dialog_txt and "overlay" in dialog_txt and "nuovo costume" in dialog_txt and "2 fotogrammi" in dialog_txt, dialog_txt)
    p.fill("#xn", "prova nuovo costume")
    with p.expect_download() as dl:
        p.click("#xk")
    d = dl.value; zp = os.path.join(WORK, "new_skin.zip"); d.save_as(zp)
    out_dir = os.path.join(WORK, "new_skin_pkg"); os.makedirs(out_dir, exist_ok=True)
    zipfile.ZipFile(zp).extractall(out_dir)
    date = os.listdir(os.path.join(out_dir, "submissions", "master"))[0]
    pkg = os.path.join(out_dir, "submissions", "master", date)
    man = json.load(open(os.path.join(pkg, "manifest.json"), encoding="utf-8"))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "validate_submission.py"), pkg], capture_output=True, text=True, cwd=ROOT)
    check("export (new skin): package passes validate_submission.py", r.returncode == 0 and "Submission structure OK" in r.stdout, r.stdout[-300:] + r.stderr[-200:])
    changes = {c["meta"]["frameKey"]: c for c in man["changes"] if c["type"] == "skin"}
    check("export (new skin): one change per frame, type skin, target skin.<slug>.<frameKey>", set(changes) == {"f0", "f1"} and all(c["target"].startswith("skin.tuta_prova.") for c in changes.values()), changes and list(changes.values())[0]["target"])
    check("export (new skin): before is null for every frame (nothing existed yet)", all(c["before"] is None for c in changes.values()))
    check("export (new skin): meta carries skinId/skinName/mode/action=new + native size/offset", all(
        c["meta"]["skinId"] == "tuta_prova" and c["meta"]["skinName"] == "Tuta Prova" and c["meta"]["mode"] == "overlay" and c["meta"]["action"] == "new"
        and c["meta"]["w"] > 0 and c["meta"]["h"] > 0 for c in changes.values()), changes)
    check("export (new skin): files land at native size under skins/<id>/", all(
        Image.open(os.path.join(pkg, c["file"])).size == (c["meta"]["w"], c["meta"]["h"]) and c["file"] == "skins/tuta_prova/sk_tuta_prova_%s.png" % k
        for k, c in changes.items()), [(k, c["file"]) for k, c in changes.items()])
    check("no console errors (export new skin)", not errs, errs)
    ctx.close()

    # ============================================================ item 2: export an UPDATE to BK -- only changed
    # frames go out (an "unchanged"/invariato one is excluded), before = sha256 of BK's own existing frame
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    p.click("[data-skinchar='algidone']"); p.wait_for_timeout(150)
    upd_setup = p.evaluate("""()=>{
      const im=IMG.al_st,changed=document.createElement('canvas');changed.width=im.width;changed.height=im.height;
      changed.getContext('2d').fillStyle='rgba(240,10,10,.9)';changed.getContext('2d').fillRect(0,0,changed.width,changed.height);
      const im2=IMG.al_w0,untouched=document.createElement('canvas');untouched.width=im2.width;untouched.height=im2.height;
      SKIN_IMPORT_PV={char:'algidone',id:'bk',mode:SKINS.bk.mode,name:SKINS.bk.name,frames:{al_st:changed,al_w0:untouched},unchanged:new Set(['al_w0'])};
      return SKINS.bk.mode;
    }""")
    open_export(p)
    dialog_txt2 = p.evaluate("document.querySelector('#modal').innerText")
    check("export: update dialog shows 'aggiornamento' and the real BK mode, 1 fotogramma (unchanged one excluded from the count)",
          "Costume BK" in dialog_txt2 and "aggiornamento" in dialog_txt2 and upd_setup in dialog_txt2 and "1 fotogrammi" in dialog_txt2, dialog_txt2)
    p.fill("#xn", "prova aggiornamento BK")
    with p.expect_download() as dl2:
        p.click("#xk")
    d2 = dl2.value; zp2 = os.path.join(WORK, "upd_skin.zip"); d2.save_as(zp2)
    out_dir2 = os.path.join(WORK, "upd_skin_pkg"); os.makedirs(out_dir2, exist_ok=True)
    zipfile.ZipFile(zp2).extractall(out_dir2)
    date2 = os.listdir(os.path.join(out_dir2, "submissions", "master"))[0]
    pkg2 = os.path.join(out_dir2, "submissions", "master", date2)
    man2 = json.load(open(os.path.join(pkg2, "manifest.json"), encoding="utf-8"))
    r2 = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "validate_submission.py"), pkg2], capture_output=True, text=True, cwd=ROOT)
    check("export (update BK): package passes validate_submission.py", r2.returncode == 0 and "Submission structure OK" in r2.stdout, r2.stdout[-300:] + r2.stderr[-200:])
    skin_changes2 = [c for c in man2["changes"] if c["type"] == "skin"]
    check("export (update BK): only the changed frame (al_st) is exported, the unchanged one (al_w0) is left out", len(skin_changes2) == 1 and skin_changes2[0]["meta"]["frameKey"] == "al_st", skin_changes2)
    bk_frames = p.evaluate("SKINS.bk.frames")
    raw = bk_frames["al_st"]; b64v = raw["b64"] if isinstance(raw, dict) else raw
    expect_sha = hashlib.sha256(base64.b64decode(b64v)).hexdigest()
    c0 = skin_changes2[0]
    check("export (update BK): before = sha256/bytes of BK's own existing al_st frame", c0["before"] and c0["before"]["sha256"] == expect_sha, c0.get("before"))
    check("export (update BK): meta.action is 'update'", c0["meta"]["action"] == "update")
    check("no console errors (export update BK)", not errs, errs)
    ctx.close()

    # ============================================================ item 2: 200 KB per-frame limit -> clear error listing the frame
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    p.click("[data-skinchar='roccia']"); p.wait_for_timeout(150)
    p.evaluate("""()=>{
      const im=IMG.e0,big=document.createElement('canvas');big.width=Math.max(im.width,600);big.height=Math.max(im.height,600);
      const x=big.getContext('2d'),d=x.createImageData(big.width,big.height);
      for(let i=0;i<d.data.length;i+=4){d.data[i]=Math.random()*255;d.data[i+1]=Math.random()*255;d.data[i+2]=Math.random()*255;d.data[i+3]=255}
      x.putImageData(d,0,0);
      const im2=IMG.f0,small=document.createElement('canvas');small.width=im2.width;small.height=im2.height;
      small.getContext('2d').fillStyle='rgba(10,200,30,.8)';small.getContext('2d').fillRect(0,0,small.width,small.height);
      // one small (well within limit) frame alongside the oversized one, so the package isn't
      // entirely empty -- Scarica pacchetto stays enabled and the size error actually surfaces
      SKIN_IMPORT_PV={char:'roccia',id:null,mode:'overlay',name:'Grosso',frames:{e0:big,f0:small},unchanged:new Set()};
    }""")
    open_export(p)
    p.fill("#xn", "prova limite")
    p.click("#xk"); p.wait_for_timeout(600)
    err_txt = p.evaluate("document.querySelector('#xe').innerText")
    check("export: a frame over 200 KB produces a clear error naming it (not silently dropped)", "200 KB" in err_txt and "skin.grosso.e0" in err_txt, err_txt)
    check("no console errors (200 KB limit)", not errs, errs)
    ctx.close()

    # ============================================================ item 5: DEV_SKIN_TEST is fully gone
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    check("DEV_SKIN_TEST: symbol no longer defined", p.evaluate("typeof DEV_SKIN_TEST") == "undefined")
    check("DEV_SKIN_TEST: helper functions no longer defined", p.evaluate("typeof devSkinOutlineImg==='undefined' && typeof devSkinTintImg==='undefined'"))
    check("DEV_SKIN_TEST: no [data-devskin] control anywhere in the dev tab", p.evaluate("!document.querySelector('[data-devskin]')"))
    check("DEV_SKIN_TEST: 'Skin di prova' panel text is gone", "Skin di prova" not in p.evaluate("document.body.innerText"))
    check("activeSkin still works as a plain passthrough to skinImg", p.evaluate("typeof activeSkin==='function'"))
    check("no console errors (DEV_SKIN_TEST removal)", not errs, errs)
    ctx.close()

    # ============================================================ smoke
    ctx, p, errs = page(b); menu(p)
    check("smoke: menu screen renders", p.evaluate("screen") == "menu")
    p.evaluate("tileAction('new')"); p.wait_for_timeout(1500)
    check("smoke: a run starts", p.evaluate("screen") == "game")
    check("no console errors (smoke)", not errs, errs)
    ctx.close()

    b.close()
srv.shutdown()

# ------------------------------------------------------------ node --check on every script block
h = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
import re
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
