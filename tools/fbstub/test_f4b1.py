#!/usr/bin/env python3
"""F4b1 headless tests (Firebase stub): sheet fixes (streak split, label sizing, "Parti da"),
"Carica costume" import, live in-memory preview.
Run: python tools/fbstub/test_f4b1.py"""
import base64, hashlib, io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "screens"))
import capture as C, fbstub
from playwright.sync_api import sync_playwright
from PIL import Image

sys.path.insert(0, os.path.join(ROOT, "refs", "skins"))
import cut_from_cells as CFC  # box_downscale: must stay byte-identical to index.html's skinBoxDownscale

RES = []
DEVC = {"role": "master", "acct": "master", "fb": True, "devOn": True}
WORK = "/tmp/f4b1_test"
import shutil
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


def set_val(p, sel, v):
    p.eval_on_selector(sel, "(el,v)=>{el.value=v;el.dispatchEvent(new Event('change',{bubbles:true}))}", v)


def make_layer_png(path, layout, char, fill_fn, size=None):
    """Builds a synthetic DRAW_HERE-style RGBA PNG for one sheet page (as skinLayout() geometry
    describes it) and writes it to path. fill_fn(cell)->None|(r,g,b,a) decides what (if anything)
    goes in each non-ref cell's base rect; None leaves the cell fully empty."""
    w, h = size or (layout["w"], layout["h"])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for row in layout["geom"]["laid"]:
        for cell in row["cells"]:
            if cell.get("ref"):
                continue
            cx, cy = 28 + cell["x"], 130 + row["rowY"]
            color = fill_fn(cell)
            if color is None:
                continue
            bx, by, bw, bh = cx + cell["baseX"], cy + cell["baseY"], cell["baseW"], cell["baseH"]
            for yy in range(by, by + bh):
                for xx in range(bx, bx + bw):
                    px[xx, yy] = color
    im.save(path)
    return im


srv = C.serve()
with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ 1a: boar frames baked WITHOUT streaks
    ctx, p, errs = page(b); menu(p)
    sizes = p.evaluate("({lato0:[IMG.boar_lato0.width,IMG.boar_lato0.height],su0:[IMG.boar_su0.width,IMG.boar_su0.height],giu0:[IMG.boar_giu0.width,IMG.boar_giu0.height]})")
    check("boar frames: lato tightened (194x135, was 235x135 with the streak baked in)", sizes["lato0"] == [194, 135], sizes["lato0"])
    check("boar frames: su tightened (116x178, was 116x210)", sizes["su0"] == [116, 178], sizes["su0"])
    check("boar frames: giu tightened (116x168, was 116x200)", sizes["giu0"] == [116, 168], sizes["giu0"])
    # streaks are a real separate effect: stubbing out drawBoarStreaks changes a moving frame but not a still one
    diff_moving = p.evaluate("""()=>{
      const snap=(moving)=>{const c=document.createElement('canvas');c.width=300;c.height=300;const x=c.getContext('2d');x.translate(150,150);x.imageSmoothingEnabled=false;drawBoar(x,0,0,60,{face:1,anim:.2,moving});return c.toDataURL()};
      const withStreak=snap(true);
      const orig=drawBoarStreaks;drawBoarStreaks=function(){};
      const withoutStreak=snap(true);
      drawBoarStreaks=orig;
      const stillA=snap(false),stillB=snap(false);
      return{changed:withStreak!==withoutStreak,stillSame:stillA===stillB};
    }""")
    check("boar: drawBoarStreaks visibly contributes pixels when moving (separate effect, not baked)", diff_moving["changed"], diff_moving)
    check("boar: a still frame is unaffected by the streak effect either way", diff_moving["stillSame"])
    check("no console errors (boar streak split)", not errs, errs)
    ctx.close()

    # ============================================================ 1b: label sizes on the actual x4 sheets (both chars)
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    fonts = p.evaluate("""async()=>{
      const seen=[];const orig=CanvasRenderingContext2D.prototype.fillText;
      CanvasRenderingContext2D.prototype.fillText=function(t,x,y){seen.push({font:this.font,t});return orig.apply(this,arguments)};
      try{await skinBuildSheet('roccia',null);await skinBuildSheet('algidone',null)}finally{CanvasRenderingContext2D.prototype.fillText=orig}
      return seen;
    }""")
    def fpx(font):
        m = re.search(r"(\d+)px", font); return int(m.group(1)) if m else 0
    header = [f for f in fonts if "foglio" in f["t"]]
    frames = [f for f in fonts if " · " in f["t"]]
    check("labels: header line uses >=48px on every page (both characters)", header and all(fpx(f["font"]) >= 48 for f in header), [f["font"] for f in header])
    check("labels: frame labels use >=28px on every cell (both characters)", frames and all(fpx(f["font"]) >= 28 for f in frames), set(f["font"] for f in frames))
    check("no console errors (label sizes)", not errs, errs)
    ctx.close()

    # ============================================================ 2: "Parti da" on the sheet export
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    zbytes = p.evaluate("""async()=>{
      const r=await skinBuildSheet('roccia','geka');
      let s="";for(const b of r.zip)s+=String.fromCharCode(b);
      return btoa(s);
    }""")
    import zipfile
    z = zipfile.ZipFile(io.BytesIO(base64.b64decode(zbytes)))
    cj = json.loads(z.read("uomo_roccia_cells.json"))
    check('"Parti da": cells.json records from/mode', cj.get("from") == "geka" and cj.get("mode") == "replace", (cj.get("from"), cj.get("mode")))
    geka_frames = p.evaluate("SKINS.geka.frames")
    sha_ok = True; sha_bad = None
    for k, fr in cj["frames"].items():
        raw = geka_frames[k]; b64v = raw["b64"] if isinstance(raw, dict) else raw
        expect = hashlib.sha256(base64.b64decode(b64v)).hexdigest()
        if fr.get("sha256") != expect:
            sha_ok = False; sha_bad = k
    check('"Parti da": per-frame sha256 matches SHA-256 of the skin\'s own stored bytes for every frame GEKA covers', sha_ok, sha_bad)
    # DRAW_HERE round-trip: cutting the DRAW_HERE region where the GEKA f0 frame itself was drawn
    # (its own native size x4, positioned via ox/oy like drawSkinLayer does) with the shared box
    # filter must reproduce SKINS.geka.frames.f0 byte-for-byte (nearest-neighbour x4 upscale then
    # box-average x4 downscale of an exact integer factor is lossless).
    dh = Image.open(io.BytesIO(z.read("uomo_roccia_DRAW_HERE.png"))).convert("RGBA")
    f0 = cj["frames"]["f0"]
    orig_raw = geka_frames["f0"]; orig_b64 = orig_raw["b64"] if isinstance(orig_raw, dict) else orig_raw
    ox0 = orig_raw.get("ox", 0) if isinstance(orig_raw, dict) else 0
    oy0 = orig_raw.get("oy", 0) if isinstance(orig_raw, dict) else 0
    orig_im = Image.open(io.BytesIO(base64.b64decode(orig_b64))).convert("RGBA")
    dx0, dy0 = f0["base"]["x"] - ox0 * 4, f0["base"]["y"] - oy0 * 4
    dw0, dh0 = orig_im.width * 4, orig_im.height * 4
    crop = dh.crop((dx0, dy0, dx0 + dw0, dy0 + dh0))
    cut = CFC.box_downscale(crop, 4)
    check('"Parti da": DRAW_HERE round-trip (box-cut) reproduces the original GEKA f0 frame byte-for-byte', cut.tobytes() == orig_im.tobytes(), (cut.size, orig_im.size))
    check("no console errors (Parti da)", not errs, errs)
    ctx.close()

    # ============================================================ direct JS vs Python cutter parity, on a size NOT
    # evenly divisible by the x4 factor (exercises the proportional-slice generalisation, not just the easy case)
    ctx, p, errs = page(b); menu(p)
    import random
    random.seed(7)
    sw, sh = 27, 19  # native output would be round(27/4)=7 x round(19/4)=5 -- deliberately not a multiple of 4
    test_im = Image.new("RGBA", (sw, sh))
    px = test_im.load()
    for y in range(sh):
        for x in range(sw):
            px[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    flat = list(test_im.tobytes())
    js_out = p.evaluate("""(a)=>{const src=new Uint8ClampedArray(a);const r=skinBoxDownscale(src,27,0,0,27,19,4);return{w:r.w,h:r.h,data:[...r.data]}}""", flat)
    py_out = CFC.box_downscale(test_im, 4)
    check("cutter parity: JS skinBoxDownscale and Python box_downscale agree on output size", (js_out["w"], js_out["h"]) == py_out.size, ((js_out["w"], js_out["h"]), py_out.size))
    check("cutter parity: JS and Python cutters give BYTE-IDENTICAL pixels on the same (non-multiple-of-4) input", bytes(js_out["data"]) == py_out.tobytes())
    check("no console errors (cutter parity)", not errs, errs)
    ctx.close()

    # ============================================================ 3: "Carica costume" import -- new skin (roccia, single page)
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    layout = p.evaluate("skinLayout('roccia').pages[0]")
    all_cells = [c for row in layout["geom"]["laid"] for c in row["cells"] if not c.get("ref")]
    keys_in_sheet = [c["key"] for c in all_cells]
    empty_key = keys_in_sheet[0]  # left empty on purpose -> "Cella vuota" warning

    def fill_new(cell):
        if cell["key"] == empty_key:
            return None
        return (10, 200, 30, 180)

    path_new = os.path.join(WORK, "roccia_new_1.png")
    im_new = make_layer_png(path_new, layout, "roccia", fill_new)
    # a few pixels strictly outside every cell -> "outside" warning
    im_new.putpixel((2, 2), (255, 0, 0, 255)); im_new.putpixel((3, 2), (255, 0, 0, 255))
    im_new.save(path_new)

    p.click("[data-skinchar='roccia']"); p.wait_for_timeout(150)
    set_val(p, "#skinImpTarget", "new")
    set_val(p, "#skinImpName", "Test Import")
    p.click("[data-skinimpmode='overlay']")
    p.set_input_files("#skinImpFiles", path_new)
    p.click("#skinImpGo"); p.wait_for_timeout(600)
    pv = p.evaluate("SKIN_IMPORT_PV && {char:SKIN_IMPORT_PV.char,id:SKIN_IMPORT_PV.id,mode:SKIN_IMPORT_PV.mode,keys:Object.keys(SKIN_IMPORT_PV.frames)}")
    check("import (new skin): preview set for roccia, mode overlay, no target id", pv and pv["char"] == "roccia" and pv["mode"] == "overlay" and pv["id"] is None, pv)
    check("import (new skin): every non-empty, non-outside frame got imported except the deliberately empty one", pv and set(pv["keys"]) == set(keys_in_sheet) - {empty_key}, pv and set(keys_in_sheet) - {empty_key} - set(pv["keys"]))
    out_txt = p.evaluate("document.querySelector('#skinImpOut').innerText")
    check('import (new skin): "Cella vuota" warning shown for the deliberately blank cell', empty_key in out_txt and "vuota" in out_txt.lower(), out_txt)
    check('import (new skin): outside-cells warning shown', "fuori dai riquadri" in out_txt, out_txt)
    check('import (new skin): "Rimuovi anteprima" button appears once a preview exists', p.evaluate("!!document.querySelector('#skinImpClear')"))
    check("no console errors (import new skin)", not errs, errs)
    ctx.close()

    # ------------------------------------------------------------ oversized-frame warning (>200 KB): none of roccia's
    # real frames are big enough natively to ever hit 200 KB even as pure noise, so this exercises the code path
    # directly against a synthetic oversized cell (skinLayout stubbed for one page only, restored right after)
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    p.click("[data-skinchar='roccia']"); p.wait_for_timeout(150)
    p.evaluate("""()=>{
      window.__origLayout2=skinLayout;
      const fakeCell={key:'f0',x:0,cellW:1300,cellH:1300,baseX:50,baseY:50,baseW:1200,baseH:1200,dir:'lato',setLabel:'Lato'};
      skinLayout=(char)=>char!=='roccia'?window.__origLayout2(char):
        {pages:[{n:1,w:1400,h:1400,geom:{laid:[{secLabel:'Lato',rowY:0,cells:[fakeCell]}],h:1350}}],totalW:1400,sheetW:1400,warn:[]};
    }""")
    big_path = os.path.join(WORK, "big_noise.png")
    big_im = Image.new("RGBA", (1400, 1400), (0, 0, 0, 0))
    pxb = big_im.load()
    for yy in range(50, 50 + 1200):
        for xx in range(50, 50 + 1200):
            pxb[xx, yy] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
    big_im.save(big_path)
    set_val(p, "#skinImpTarget", "new"); set_val(p, "#skinImpName", "Big")
    p.set_input_files("#skinImpFiles", big_path)
    p.click("#skinImpGo"); p.wait_for_timeout(2000)
    txt = p.evaluate("document.querySelector('#skinImpOut').innerText")
    check("import: oversized-frame warning fires when a cut frame's PNG exceeds 200 KB", "200 KB" in txt, txt)
    check("no console errors (oversized frame)", not errs, errs)
    ctx.close()

    # ============================================================ 3: import errors -- stale page, opaque GUIDE-like image, opaque photo-like image
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    p.click("[data-skinchar='roccia']"); p.wait_for_timeout(150)
    set_val(p, "#skinImpTarget", "new"); set_val(p, "#skinImpName", "Errori")
    stale = Image.new("RGBA", (1804, 2924), (0, 0, 0, 0))  # 0.4_10-era roccia sheet size, no longer valid
    stale_path = os.path.join(WORK, "stale.png"); stale.save(stale_path)
    p.set_input_files("#skinImpFiles", stale_path); p.click("#skinImpGo"); p.wait_for_timeout(400)
    txt = p.evaluate("document.querySelector('#skinImpOut').innerText")
    check("import error: stale 0.4_10-sized page -> exact Italian error", "riscarica il foglio" in txt, txt)
    # 0.4_15: a page shrunk/enlarged uniformly by a phone app -> its own message; same width + other height = an old sheet
    for (sw, sh, why) in ((layout["w"] // 2, layout["h"] // 2, "halved"), (round(layout["w"] * .6), round(layout["h"] * .6), "x0.6 (phone export)"), (layout["w"] * 2, layout["h"] * 2, "doubled")):
        rs = Image.new("RGBA", (sw, sh), (0, 0, 0, 0)); rs_path = os.path.join(WORK, "resized_%dx%d.png" % (sw, sh)); rs.save(rs_path)
        p.set_input_files("#skinImpFiles", rs_path); p.click("#skinImpGo"); p.wait_for_timeout(400)
        txt = p.evaluate("document.querySelector('#skinImpOut').innerText")
        check("import error: page resized uniformly (%s, %dx%d) -> «L'app ha ridimensionato il foglio: esportalo a dimensione originale»" % (why, sw, sh), "L'app ha ridimensionato il foglio: esportalo a dimensione originale" in txt and "riscarica" not in txt, txt)
    old_v = Image.new("RGBA", (layout["w"], layout["h"] - 10), (0, 0, 0, 0))  # 0.4_11-era roccia height (1804x3400): same width, other height
    old_path = os.path.join(WORK, "old_version.png"); old_v.save(old_path)
    p.set_input_files("#skinImpFiles", old_path); p.click("#skinImpGo"); p.wait_for_timeout(400)
    txt = p.evaluate("document.querySelector('#skinImpOut').innerText")
    check("import error: same width, different height (old sheet, %dx%d) stays «Foglio di un'altra versione»" % (layout["w"], layout["h"] - 10), "Foglio di un'altra versione: riscarica il foglio" in txt and "ridimensionato" not in txt, txt)
    p.set_input_files("#skinImpFiles", path_new); p.click("#skinImpGo"); p.wait_for_timeout(600)
    pv = p.evaluate("SKIN_IMPORT_PV && Object.keys(SKIN_IMPORT_PV.frames).length")
    check("a correct page still imports as before (after the resize/old-sheet errors)", pv == len(keys_in_sheet) - 1, pv)
    lg = p.evaluate("SKIN_LEGGIMI('Uomo roccia','roccia')")
    check("LEGGIMI.txt has the «Dal telefono» steps (layers, hide GUIDE, export 100% transparent, Carica costume)",
          "Dal telefono" in lg and "ibisPaint X" in lg and "Nascondi il livello GUIDE" in lg and "100%" in lg and "«Carica costume»" in lg, lg[-500:])

    guide_like = Image.new("RGBA", (layout["w"], layout["h"]), (201, 204, 209, 255))  # GUIDE bg colour, fully opaque
    guide_path = os.path.join(WORK, "guide_like.png"); guide_like.save(guide_path)
    p.set_input_files("#skinImpFiles", guide_path); p.click("#skinImpGo"); p.wait_for_timeout(400)
    txt = p.evaluate("document.querySelector('#skinImpOut').innerText")
    check("import error: opaque GUIDE-like screenshot -> exact Italian error", "sfondo trasparente" in txt, txt)

    photo_like = Image.new("RGBA", (layout["w"], layout["h"]))
    ppx = photo_like.load()
    for y in range(layout["h"]):
        for x in range(layout["w"]):
            ppx[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
    photo_path = os.path.join(WORK, "photo_like.png"); photo_like.save(photo_path)
    p.set_input_files("#skinImpFiles", photo_path); p.click("#skinImpGo"); p.wait_for_timeout(400)
    txt = p.evaluate("document.querySelector('#skinImpOut').innerText")
    check("import error: opaque photo-like image -> same exact Italian error", "sfondo trasparente" in txt, txt)
    check("no console errors (import errors)", not errs, errs)
    ctx.close()

    # ============================================================ 3: import -- update BK (algidone), multi-page, "invariato" detection
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    p.click("[data-skinchar='algidone']"); p.wait_for_timeout(150)
    p.evaluate("async()=>{await ensureFA()}")  # skinImportRun awaits this itself now; the test needs the same layout to build matching pages
    alg_layout = p.evaluate("skinLayout('algidone').pages")
    bk_frames = p.evaluate("SKINS.bk.frames")
    unchanged_key = next(c["key"] for pg in alg_layout for row in pg["geom"]["laid"] for c in row["cells"] if not c.get("ref") and c["key"] in bk_frames)
    paths = []
    for i, pg in enumerate(alg_layout):
        def fill_upd(cell, bk=bk_frames, uk=unchanged_key):
            if cell["key"] == uk:
                return "SAME"  # marker: fill with the skin's own decoded pixels below
            if cell["key"] in bk:
                return None  # leave frames BK doesn't need to touch untouched (would show as new import elsewhere)
            return (5, 5, 5, 0)  # nothing new outside BK's own set, keep the page mostly empty
        pth = os.path.join(WORK, "algidone_upd_%d.png" % (i + 1))
        im = Image.new("RGBA", (pg["w"], pg["h"]), (0, 0, 0, 0))
        pxu = im.load()
        for row in pg["geom"]["laid"]:
            for cell in row["cells"]:
                if cell.get("ref") or cell["key"] != unchanged_key:
                    continue
                raw = bk_frames[unchanged_key]; b64v = raw["b64"] if isinstance(raw, dict) else raw
                src = Image.open(io.BytesIO(base64.b64decode(b64v))).convert("RGBA")
                up = src.resize((src.width * 4, src.height * 4), Image.NEAREST)
                cx, cy = 28 + cell["x"] + cell["baseX"], 130 + row["rowY"] + cell["baseY"]
                im.paste(up, (cx, cy))
        im.save(pth); paths.append(pth)
    set_val(p, "#skinImpTarget", "bk")
    p.set_input_files("#skinImpFiles", paths)
    p.click("#skinImpGo"); p.wait_for_timeout(1500)
    pv = p.evaluate("SKIN_IMPORT_PV && {char:SKIN_IMPORT_PV.char,id:SKIN_IMPORT_PV.id,mode:SKIN_IMPORT_PV.mode}")
    check("import (update BK): preview targets bk, mode fixed to BK's own (replace)", pv and pv["id"] == "bk" and pv["mode"] == "replace" and pv["char"] == "algidone", pv)
    txt = p.evaluate("document.querySelector('#skinImpOut').innerText")
    check("import (update BK): the re-uploaded frame (identical pixels to BK's own al_st) is imported, not left empty", unchanged_key not in [l.split(": ")[1] for l in txt.splitlines() if l.startswith("Cella vuota")], txt)
    cov = p.evaluate("(()=>{const c=skinImportPvCoverage();return c})()")
    check("import (update BK): preview coverage merges BK's existing frames with the (re-)imported one", cov and cov["have"] >= 27, cov)
    check("no console errors (import update BK, multi-page)", not errs, errs)
    ctx.close()

    # "invariato" detection, tested deterministically: BK's own PNG encoding pipeline predates this tool and will
    # essentially never byte-match a freshly re-encoded canvas PNG even for identical pixels (different encoders),
    # so this checks the comparison logic itself by re-uploading the SAME generated sheet against a fake skin
    # whose stored frame is the exact bytes this tool itself produced on a first pass -- same encoder both times.
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    p.click("[data-skinchar='roccia']"); p.wait_for_timeout(150)
    set_val(p, "#skinImpTarget", "new"); set_val(p, "#skinImpName", "Round Trip")
    p.set_input_files("#skinImpFiles", path_new)
    p.click("#skinImpGo"); p.wait_for_timeout(800)
    first_b64 = p.evaluate("SKIN_IMPORT_PV.frames.f1.toDataURL('image/png').split(',')[1]")
    p.evaluate("(b)=>{SKINS._testinv={char:'roccia',mode:'overlay',name:'x',na:[],frames:{f1:b}};SKIN_IMPORT_PV=null;render()}", first_b64)
    p.wait_for_timeout(150)
    set_val(p, "#skinImpTarget", "_testinv")
    p.set_input_files("#skinImpFiles", path_new)
    p.click("#skinImpGo"); p.wait_for_timeout(800)
    txt2 = p.evaluate("document.querySelector('#skinImpOut').innerText")
    check('"invariato" detection: re-uploading a sheet whose cut bytes match the target skin\'s stored frame marks it «invariato»', "Invariato: f1" in txt2, txt2)
    p.evaluate("delete SKINS._testinv")
    check("no console errors (invariato detection)", not errs, errs)
    ctx.close()

    # ============================================================ 3: ambiguous same-size pages resolved by filename (synthetic, since
    # the real sheet's pages all happen to have distinct sizes this build -- forces the branch via a stubbed skinLayout)
    ctx, p, errs = page(b); menu(p); open_skins_acc(p)
    p.click("[data-skinchar='roccia']"); p.wait_for_timeout(150)
    amb_setup = p.evaluate("""()=>{
      window.__origLayout=skinLayout;
      const real=skinLayout('roccia');
      const W=real.pages[0].w,H=real.pages[0].h;
      const fake=(char)=>{
        if(char!=='roccia')return window.__origLayout(char);
        const g=JSON.parse(JSON.stringify(real.pages[0].geom));
        const only=(k)=>({laid:g.laid.map(r=>({...r,cells:r.cells.filter(c=>c.ref||c.key===k)})).filter(r=>r.cells.length)});
        return{pages:[{n:1,w:W,h:H,geom:only('f0')},{n:2,w:W,h:H,geom:only('f1')}],totalW:W,sheetW:W,warn:[]};
      };
      skinLayout=fake;
      return[W,H];
    }""")
    fake_geom = p.evaluate("skinLayout('roccia').pages")
    for n, key in ((1, "f0"), (2, "f1")):
        pg = next(pg for pg in fake_geom if pg["n"] == n)
        pth = os.path.join(WORK, "ambiguous_%d.png" % n)
        base_wh = p.evaluate("(k)=>{const im=skinBaseImg(k);return[im.width,im.height]}", key)
        color = (0, 255, 0, 255) if key == "f0" else (0, 0, 255, 255)
        make_layer_png(pth, pg, "roccia", lambda c, col=color: col)
        set_val(p, "#skinImpTarget", "new"); set_val(p, "#skinImpName", "Ambiguous " + key)
        p.set_input_files("#skinImpFiles", pth); p.click("#skinImpGo"); p.wait_for_timeout(400)
        pv = p.evaluate("SKIN_IMPORT_PV && Object.keys(SKIN_IMPORT_PV.frames)")
        check("ambiguous pages: filename '_%d' resolves to the page carrying '%s' (not the other same-size page)" % (n, key), pv == [key], pv)
    check("no console errors (ambiguous page disambiguation)", not errs, errs)
    ctx.close()

    # ============================================================ 4: live preview shows everywhere the skin system draws, S untouched, vanishes on reload/logout/dev-off
    ctx, p, errs = page(b); menu(p)
    save_before = p.evaluate("JSON.stringify(S)")

    def snap_menu():
        p.evaluate("go('menu')"); p.wait_for_timeout(150)
        return p.evaluate("document.getElementById('mstage').toDataURL()")

    base_menu = snap_menu()
    p.evaluate("""()=>{
      const mk=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').fillStyle='rgba(255,46,196,.6)';c.getContext('2d').fillRect(0,0,w,h);return c};
      const im=mk(IMG.f0.width,IMG.f0.height);
      SKIN_IMPORT_PV={char:'roccia',id:null,mode:'overlay',name:'x',frames:{f0:im,f1:im,f2:im}};
      render();
    }""")
    pv_menu = snap_menu()
    check("preview: menu portrait changes once SKIN_IMPORT_PV is set for roccia", pv_menu != base_menu)

    # maze
    p.evaluate("go('menu')"); p.wait_for_timeout(150)
    p.evaluate("tileAction('new')"); p.wait_for_timeout(1200)
    maze_snap = "()=>document.getElementById('cv').toDataURL()"
    p.wait_for_timeout(150); with_pv = p.evaluate(maze_snap)
    p.evaluate("SKIN_IMPORT_PV=null"); p.wait_for_timeout(150)
    without_pv = p.evaluate(maze_snap)
    check("preview: maze rendering changes with SKIN_IMPORT_PV set vs cleared", with_pv != without_pv)
    check("preview never touches S (byte-identical JSON before/after using it)", p.evaluate("JSON.stringify(S)") == save_before)

    # Ferma climber + Cinghiale (algidone side)
    p.evaluate("go('menu')"); p.wait_for_timeout(200)
    p.evaluate("S.p.fa=S.p.fa||{};S.p.fa.seen=true")
    p.evaluate("go('wish')"); p.wait_for_timeout(150); p.evaluate("tab='games';render()"); p.wait_for_timeout(150)
    p.click("[data-fagame]"); p.wait_for_timeout(1500)
    fa_snap = "()=>{faDraw();return document.getElementById('fac').toDataURL()}"
    fa_base = p.evaluate(fa_snap)
    p.evaluate("""()=>{
      const mk=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').fillStyle='rgba(255,46,196,.6)';c.getContext('2d').fillRect(0,0,w,h);return c};
      const im=mk(IMG.f0.width,IMG.f0.height);
      SKIN_IMPORT_PV={char:'roccia',id:null,mode:'overlay',name:'x',frames:{f0:im,f1:im,f2:im,fd0:im,fd1:im,fd2:im,fu0:im,fu3:im}};
    }""")
    fa_pv = p.evaluate(fa_snap)
    check("preview: Ferma Algidone! climber (Uomo roccia) changes with the preview", fa_pv != fa_base)
    p.evaluate("SKIN_IMPORT_PV=null")

    # Cinghiale (boar) + Ferma thrower, algidone
    boar_snap = "()=>{const c=document.createElement('canvas');c.width=300;c.height=300;const x=c.getContext('2d');x.translate(150,150);x.imageSmoothingEnabled=false;drawBoar(x,0,0,60,{face:1,anim:.2,moving:true});return c.toDataURL()}"
    boar_base = p.evaluate(boar_snap)
    p.evaluate("""()=>{
      const mk=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').fillStyle='rgba(255,46,196,.6)';c.getContext('2d').fillRect(0,0,w,h);return c};
      const im=mk(IMG.boar_lato0.width,IMG.boar_lato0.height);
      SKIN_IMPORT_PV={char:'algidone',id:null,mode:'overlay',name:'x',frames:{boar_lato0:im,boar_lato1:im}};
    }""")
    boar_pv = p.evaluate(boar_snap)
    check("preview: Cinghiale changes with the preview (streak effect still drawn on top, unaffected)", boar_pv != boar_base)
    p.evaluate("SKIN_IMPORT_PV=null")

    thrower_snap = """()=>{
      const im=IMG.alg_idle0||FAIMG.alg_idle0;
      const c=document.createElement('canvas');c.width=200;c.height=200;const x=c.getContext('2d');x.imageSmoothingEnabled=false;
      drawSkinned(x,'algidone','alg_idle0',im,0,0,im.width*3,im.height*3,false);
      return c.toDataURL();
    }"""
    thrower_base = p.evaluate(thrower_snap)
    p.evaluate("""()=>{
      const mk=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').fillStyle='rgba(255,46,196,.6)';c.getContext('2d').fillRect(0,0,w,h);return c};
      const im=mk((IMG.alg_idle0||FAIMG.alg_idle0).width,(IMG.alg_idle0||FAIMG.alg_idle0).height);
      SKIN_IMPORT_PV={char:'algidone',id:null,mode:'overlay',name:'x',frames:{alg_idle0:im}};
    }""")
    thrower_pv = p.evaluate(thrower_snap)
    check("preview: Ferma Algidone! thrower (Algidone NPC) changes with the preview", thrower_pv != thrower_base)
    p.evaluate("SKIN_IMPORT_PV=null")
    check("no console errors (live preview)", not errs, errs)
    ctx.close()

    # dev-off clears it (fresh context: the FA screen's own loop must not be left running)
    ctx, p, errs = page(b); menu(p)
    p.evaluate("SKIN_IMPORT_PV={char:'roccia',id:null,mode:'overlay',name:'x',frames:{}}")
    p.evaluate("go('menu')"); p.wait_for_timeout(150); p.click("#devt"); p.wait_for_timeout(150)
    check("preview: vanishes when dev mode is turned off", p.evaluate("SKIN_IMPORT_PV") is None)
    check("no console errors (dev off)", not errs, errs)
    ctx.close()

    # logout (fbDrop) clears it
    ctx, p, errs = page(b); menu(p)
    p.evaluate("SKIN_IMPORT_PV={char:'roccia',id:null,mode:'overlay',name:'x',frames:{}}")
    p.evaluate("fbDrop()")
    check("preview: vanishes on logout (fbDrop)", p.evaluate("SKIN_IMPORT_PV") is None)
    check("no console errors (logout)", not errs, errs)
    ctx.close()

    # reload clears it (in-memory only, never persisted)
    ctx, p, errs = page(b); menu(p)
    p.evaluate("SKIN_IMPORT_PV={char:'roccia',id:null,mode:'overlay',name:'x',frames:{}}")
    p.reload(); p.wait_for_selector("#rsi")
    check("preview: gone after a reload (never written to S/localStorage/IndexedDB)", p.evaluate("typeof SKIN_IMPORT_PV==='undefined'?null:SKIN_IMPORT_PV") is None)
    check("no console errors (reload)", not errs, errs)
    ctx.close()

    # ============================================================ smoke: menu renders, a run still starts, zero console errors
    ctx, p, errs = page(b); menu(p)
    check("smoke: menu screen renders", p.evaluate("screen") == "menu")
    p.evaluate("tileAction('new')"); p.wait_for_timeout(1500)
    check("smoke: a run starts", p.evaluate("screen") == "game")
    check("no console errors (smoke)", not errs, errs)
    ctx.close()

    b.close()
srv.shutdown()

print(sum(RES), "/", len(RES), "passed")
sys.exit(0 if all(RES) else 1)
