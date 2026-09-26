#!/usr/bin/env python3
"""F4a2 (3c): writes refs/skins/SKIN_COVERAGE.md (matrix frame x skin: ok / manca / na / procedurale)
from the running build, and a few sanity checks on the result.
Run: python tools/fbstub/test_skin_coverage.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "screens"))
import capture as C, fbstub
from playwright.sync_api import sync_playwright

OUT = os.path.join(ROOT, "refs", "skins", "SKIN_COVERAGE.md")
RES = []


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


def build_md(data, version):
    lines = ["# Skin coverage", "",
             "Matrice fotogramma x costume, generata da questa build (`tools/fbstub/test_skin_coverage.py`), "
             "non scritta a mano: rigenerarla ad ogni chunk che tocca un fotogramma, una posa o un costume "
             "(CLAUDE.md §6 regola 11).", "",
             "Legenda: **ok** = il costume ha quel fotogramma · **manca** = fotogramma reale del foglio (F4a) "
             "senza arte per questo costume · **na** = il costume dichiara di non averne bisogno (`SKINS.<id>.na`) "
             "· **procedurale — da convertire** = posa disegnata dal codice (es. Cinghiale), non ancora un "
             "fotogramma: nessun costume puo' toccarla oggi.", "",
             "Build: " + version, ""]
    for ch in data:
        lines.append("## " + ch["name"])
        lines.append("")
        skins = ch["skins"]
        header = "| Fotogramma | Riga | " + " | ".join(s["name"] for s in skins) + " |"
        sep = "|---|---|" + "---|" * len(skins)
        lines.append(header); lines.append(sep)
        for f in ch["real"]:
            row = ["`" + f["key"] + "`", f["set"]]
            for s in skins:
                if f["key"] in s["na"]:
                    row.append("na")
                elif f["key"] in s["frames"]:
                    row.append("ok")
                else:
                    row.append("manca")
            lines.append("| " + " | ".join(row) + " |")
        for r in ch["refs"]:
            row = ["`" + r["key"] + "`", "Riferimenti (" + r["label"] + ")"] + ["procedurale — da convertire"] * len(skins)
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    return "\n".join(lines)


srv = C.serve()
with sync_playwright() as pw:
    b = launch_browser(pw)
    ctx = b.new_context(viewport=C.VIEW)
    ctx.add_init_script("localStorage.setItem('mgs_dev',JSON.stringify({role:'master',acct:'master',fb:true,devOn:true}));")
    fbstub.install(ctx, session="master")
    p = ctx.new_page()
    errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    p.goto(C.BASE + "index.html")
    p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(800)
    data = p.evaluate("""async ()=>{
        const out=[];
        for(const ch of ["roccia","algidone"]){
            if(ch==="algidone")await ensureFA();
            const def=SKIN_DEF[ch];
            const real=def.sets.flatMap(s=>s.keys.map(k=>({key:k,set:s.label})));
            const refs=(def.refs||[]).map(r=>({key:r.key,label:r.label}));
            const skins=Object.keys(SKINS).filter(id=>SKINS[id].char===ch).map(id=>({
                id, name:SKINS[id].name||id, na:SKINS[id].na||[], frames:Object.keys(SKINS[id].frames)
            }));
            out.push({name:def.name,real,refs,skins});
        }
        return out;
    }""")
    version = p.evaluate("VERSION")
    check("build reachable, VERSION read", bool(version), version)
    check("no console errors while extracting", not errs, errs)
    ctx.close(); b.close()
srv.shutdown()

md = build_md(data, version)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(md)
check("SKIN_COVERAGE.md written", os.path.exists(OUT) and os.path.getsize(OUT) > 0)

roc = next(c for c in data if c["name"] == "Uomo roccia")
alg = next(c for c in data if c["name"] == "Algidone")
check("roccia has at least one skin listed (GEKA)", any(s["id"] == "geka" for s in roc["skins"]))
check("algidone has at least one skin listed (BK)", any(s["id"] == "bk" for s in alg["skins"]))
geka = next(s for s in roc["skins"] if s["id"] == "geka")
check("GEKA covers every real roccia frame (all 'ok', matches 10/10 in the accordion)", all(f["key"] in geka["frames"] for f in roc["real"]) and len(roc["real"]) == 10)
bk = next(s for s in alg["skins"] if s["id"] == "bk")
ferma_keys = [f["key"] for f in alg["real"] if f["key"].startswith("alg_")]
check("BK is missing every Ferma thrower frame (grandfathered gap, §8)", len(ferma_keys) == 13 and all(k not in bk["frames"] for k in ferma_keys))
check("Cinghiale refs present for algidone (procedural, 3 poses)", len(alg["refs"]) == 3)
with open(OUT, encoding="utf-8") as f:
    content = f.read()
check("SKIN_COVERAGE.md contains the procedural legend for Cinghiale rows", "procedurale — da convertire" in content and "Cinghiale" in content)

print(sum(RES), "/", len(RES), "passed")
sys.exit(0 if all(RES) else 1)
