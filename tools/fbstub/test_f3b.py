#!/usr/bin/env python3
"""F3b headless tests (Firebase stub): «Invia testi» -> Firestore edits, offline queue, «Scarica pacchetto» -> ZIP v2 validated by
scripts/validate_submission.py. Run: python tools/fbstub/test_f3b.py"""
import base64, hashlib, io, json, os, struct, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "screens"))
import capture as C, fbstub
from playwright.sync_api import sync_playwright

RES = []
DEVC = {"role": "master", "acct": "master", "fb": True, "devOn": True}
ALLOWED = {"uid", "acct", "kind", "char", "screen", "target", "locator", "before", "value", "note", "base", "ts", "meta"}


def check(name, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name, extra)


def wav(ms, rate=8000):
    n = rate * ms // 1000
    data = bytes([128]) * n
    return b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate, 1, 8) + b"data" + struct.pack("<I", n) + data


def png(w, h, col=(200, 30, 30)):
    from PIL import Image
    b = io.BytesIO(); Image.new("RGB", (w, h), col).save(b, "PNG"); return b.getvalue()


def page(b, dev=True, **kw):
    ctx = b.new_context(viewport=C.VIEW, has_touch=True, accept_downloads=True)
    if dev:
        ctx.add_init_script("if(!sessionStorage.getItem('__seeded')){sessionStorage.setItem('__seeded','1');localStorage.setItem('mgs_dev',%s)}" % json.dumps(json.dumps(DEVC)))
        kw.setdefault("session", "master")
    fbstub.install(ctx, **kw)
    p = ctx.new_page(); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and errs.append(m.text))
    return ctx, p, errs


def menu(p):
    p.goto(C.BASE + "index.html"); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(900)


def open_export(p):
    p.evaluate("go('opt')"); p.wait_for_timeout(300); p.click("[data-otab=dev]"); p.wait_for_timeout(250)
    if not p.evaluate("document.querySelector('details.acc:has(#xopen)').open"):
        p.click("details.acc:has(#xopen) > summary"); p.wait_for_timeout(250)
    p.click("#xopen"); p.wait_for_timeout(700)


def seed_edits(p):
    p.evaluate("""(()=>{S.tiles.find(t=>t.id==='new').label='Nuova partita';S.ov.game_0={color:'#112233'};S.ov.game_1={scale:1.2};S.gtext.intro='Ciao, bella serata';persist()})()""")


srv = C.serve()
with sync_playwright() as pw:
    b = pw.chromium.launch()
    # ---------------------------------------------------------------- Invia testi
    ctx, p, errs = page(b); menu(p); seed_edits(p)
    check("window.mgExport removed", p.evaluate("typeof mgExport") == "undefined")
    open_export(p)
    check("dialog: 4 text changes listed, Invia testi enabled, no general-note requirement for texts", "4 modifiche" in p.evaluate("document.querySelector('#modal').innerText") and not p.evaluate("document.querySelector('#xs').disabled"))
    p.click("details:has-text('Elenco') > summary"); p.fill("[data-en='tile.new.label']", "più chiaro"); p.click("#xs"); p.wait_for_timeout(900)
    docs = p.evaluate("window.__fbs.edits||[]"); by = {d["target"]: d for d in docs}
    check("4 docs written, one per change", len(docs) == 4 and set(by) == {"tile.new.label", "game.0.color", "game.1.scale", "dialogue.gam.intro"}, sorted(by))
    check("only the allowed field set per doc", all(set(d) <= ALLOWED and {"uid", "acct", "kind", "char", "target", "before", "value", "base", "ts", "meta"} <= set(d) for d in docs), [sorted(d) for d in docs][:1])
    check("kinds", (by["tile.new.label"]["kind"], by["game.0.color"]["kind"], by["game.1.scale"]["kind"], by["dialogue.gam.intro"]["kind"]) == ("text", "colour", "scale", "text"))
    ver = p.evaluate("VERSION")
    check("before = built-in value (no local override)", by["tile.new.label"]["before"] == "Nuovo gioco" and by["game.0.color"]["before"] == "#23364c" and by["game.1.scale"]["before"] == "1" and by["dialogue.gam.intro"]["before"] == p.evaluate("BJ_LINES.intro[0]"), {k: v["before"] for k, v in by.items()})
    check("values, base, acct, uid, ts, note, screen, char", by["tile.new.label"]["value"] == "Nuova partita" and by["game.1.scale"]["value"] == "1.2" and all(d["base"] == ver and d["acct"] == "master" and d["uid"] == "uid_master" and d["ts"] == {"__ts": True} for d in docs)
          and by["tile.new.label"]["note"] == "più chiaro" and "note" not in by["game.0.color"] and by["tile.new.label"]["screen"] == "menu-home-roccia" and by["dialogue.gam.intro"]["screen"] == "bj-dealer-line" and by["tile.new.label"]["char"] == "shared" and "locator" not in by["tile.new.label"], by["tile.new.label"])
    check("changes stay applied locally", p.evaluate("S.tiles.find(t=>t.id==='new').label") == "Nuova partita")
    p.click("details:has-text('Elenco') > summary")
    check("dialog re-opens with 'inviato' marks and Invia testi disabled", p.evaluate("document.querySelector('#modal').innerText.split('inviato').length") == 5 and p.evaluate("document.querySelector('#xs').disabled") is True)
    p.evaluate("closeModal()"); open_export(p); check("not re-sent when nothing changed", p.evaluate("document.querySelector('#xs').disabled") and len(p.evaluate("window.__fbs.edits")) == 4)
    p.evaluate("S.tiles.find(t=>t.id==='new').label='Nuova partita!';persist()"); p.evaluate("closeModal()"); open_export(p)
    check("edited again -> 1 to send", not p.evaluate("document.querySelector('#xs').disabled"))
    p.click("#xs"); p.wait_for_timeout(800); check("re-sent only the edited one", len(p.evaluate("window.__fbs.edits")) == 5 and p.evaluate("window.__fbs.edits[4].value") == "Nuova partita!")
    # overlong text is blocked
    p.evaluate("closeModal();S.gtext.deal='x'.repeat(501);persist()"); open_export(p)
    check("501-char text blocks sending", p.evaluate("document.querySelector('#xs').disabled") and "troppo lungo" in p.evaluate("document.querySelector('#modal').innerText"))
    check("no console errors (Invia testi)", not errs, errs); ctx.close()
    # ---------------------------------------------------------------- offline queue
    ctx, p, errs = page(b); menu(p); seed_edits(p); ctx.set_offline(True); p.wait_for_timeout(200); open_export(p); p.click("#xs"); p.wait_for_timeout(700)
    q = p.evaluate("JSON.parse(localStorage.getItem('mgs_editq')||'[]')")
    check("offline: 4 edits queued (original time in meta.qts), nothing sent", len(q) == 4 and all("qts" in x["meta"] for x in q) and not p.evaluate("(window.__fbs.edits||[]).length"))
    toast_ok = "verranno inviati appena sei online" in p.evaluate("document.body.innerText")
    p.click("details:has-text('Elenco') > summary")
    check("offline: toast + 'in coda' marks", toast_ok and p.evaluate("document.querySelector('#modal').innerText").count("in coda") >= 4)
    ctx.set_offline(False); p.wait_for_timeout(2000)
    check("'online' flushes the edit queue", len(p.evaluate("window.__fbs.edits||[]")) == 4 and p.evaluate("JSON.parse(localStorage.getItem('mgs_editq')||'[]').length") == 0)
    check("flushed docs still respect the field set", all(set(d) <= ALLOWED for d in p.evaluate("window.__fbs.edits")))
    ctx.close()
    ctx, p, errs = page(b, denyBugs=True); menu(p); seed_edits(p); open_export(p); p.click("#xs"); p.wait_for_timeout(700)
    check("permission error: toast, kept in queue, no retry loop", "Invio non riuscito" in p.evaluate("document.body.innerText") and p.evaluate("JSON.parse(localStorage.getItem('mgs_editq')||'[]').length") == 4 and p.evaluate("EDIT_NOFLUSH"))
    ctx.close()
    # ---------------------------------------------------------------- logged out (no role): disabled state
    ctx, p, errs = page(b, dev=False); menu(p); seed_edits(p); p.evaluate("role=null;acct=null;exportDialog()"); p.wait_for_timeout(600)
    check("logged out: both buttons disabled + 'Accedi per inviare'", p.evaluate("document.querySelector('#xs').disabled && document.querySelector('#xk').disabled") and "Accedi per inviare" in p.evaluate("document.querySelector('#modal').innerText"))
    ctx.close()
    # ---------------------------------------------------------------- Scarica pacchetto (ZIP v2)
    A_NEW, A_BUILT, A_BIG = wav(300), wav(500), wav(40000)  # the big one is > 300 KB -> flagged/
    S_NEW, S_BUILT = png(4, 3), png(2, 2)
    ctx, p, errs = page(b); menu(p)
    p.evaluate("""async(a)=>{const bl=(b64,t)=>new Blob([Uint8Array.from(atob(b64),c=>c.charCodeAt(0))],{type:t});
      await IDB.set('snd_algidone_eat',bl(a.new,'audio/wav'));await IDB.set('snd_algidone_foe',bl(a.big,'audio/wav'));
      BUILTIN_AUD['sound.algidone.eat']=a.built;
      expSpriteItems=async()=>[{character:'roccia',target:'sprite.rock.f0',blob:bl(a.png,'image/png'),built:bl(a.pbuilt,'image/png'),frameKey:'f0',anchor:'center',ox:1,oy:2,base_w:2,base_h:2,screen:'maze-play-roccia'}]}""",
               {"new": base64.b64encode(A_NEW).decode(), "big": base64.b64encode(A_BIG).decode(), "built": base64.b64encode(A_BUILT).decode(), "png": base64.b64encode(S_NEW).decode(), "pbuilt": base64.b64encode(S_BUILT).decode()})
    open_export(p)
    check("package: 3 files counted (2 audio + 1 sprite)", "3 file" in p.evaluate("document.querySelector('#modal').innerText"))
    p.click("#xk"); p.wait_for_timeout(500); check("package: general note required", "nota generale" in p.evaluate("document.querySelector('#xe').innerText").lower())
    p.fill("#xn", "prova pacchetto v2")
    with p.expect_download() as dl:
        p.click("#xk")
    d = dl.value; zp = os.path.join(tempfile.mkdtemp(), d.suggested_filename); d.save_as(zp)
    check("zip name mangiasassi_<acct>_<date>.zip", d.suggested_filename.startswith("mangiasassi_master_") and d.suggested_filename.endswith(".zip"), d.suggested_filename)
    tmp = tempfile.mkdtemp(); zipfile.ZipFile(zp).extractall(tmp)
    date = os.listdir(os.path.join(tmp, "submissions", "master"))[0]; pkg = os.path.join(tmp, "submissions", "master", date)
    man = json.load(open(os.path.join(pkg, "manifest.json"), encoding="utf-8"))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "validate_submission.py"), pkg], capture_output=True, text=True, cwd=ROOT)
    check("extracted package passes validate_submission.py as v2", r.returncode == 0 and "Submission structure OK" in r.stdout, r.stdout[-300:] + r.stderr[-200:])
    ch = {c["target"]: c for c in man["changes"]}
    check("manifest header (schemaVersion 2, developer=acct, baseVersion=VERSION, site, exportedAt, note)", man["schemaVersion"] == 2 and man["developer"] == "master" and man["baseVersion"] == p.evaluate("VERSION") and man["site"] == "stable" and man["exportedAt"].endswith("Z") and man["note"] == "prova pacchetto v2", {k: man[k] for k in man if k != "changes"})
    e = ch["sound.algidone.eat"]
    check("audio: before = sha256/bytes/duration of the built-in asset", e["before"]["sha256"] == hashlib.sha256(A_BUILT).hexdigest() and e["before"]["bytes"] == len(A_BUILT) and abs(e["before"]["durationMs"] - 500) < 30, e["before"])
    check("audio: meta bytes/mime/duration of the new file", e["meta"]["bytes"] == len(A_NEW) and e["meta"]["mime"] == "audio/wav" and abs(e["meta"]["durationMs"] - 300) < 30 and e["file"] == "sound_algidone_eat.wav" and e["note"] == "prova pacchetto v2" and e["character"] == "algidone", e)
    fb_ = ch["sound.algidone.foe"]
    check("audio > 300 KB goes under flagged/ (before null: no built-in)", fb_["file"] == "flagged/sound_algidone_foe.wav" and fb_["before"] is None and os.path.exists(os.path.join(pkg, "flagged", "sound_algidone_foe.wav")), fb_["file"])
    sp = ch["sprite.rock.f0"]
    check("sprite: before + meta measured", sp["before"] == {"sha256": hashlib.sha256(S_BUILT).hexdigest(), "bytes": len(S_BUILT), "w": 2, "h": 2} and sp["meta"] == {"frameKey": "f0", "w": 4, "h": 3, "anchor": "center", "ox": 1, "oy": 2, "base_w": 2, "base_h": 2} and sp["screen"] == "maze-play-roccia" and sp["character"] == "roccia", sp)
    check("package holds only audio/sprite changes (no text)", all(c["type"] in ("audio", "sprite") for c in man["changes"]))
    check("no console errors (package)", not errs, errs); ctx.close()
    # ---------------------------------------------------------------- nothing to export / smoke
    ctx, p, errs = page(b); menu(p); open_export(p)
    check("no audio/sprite: 'Scarica pacchetto' disabled with a hint", p.evaluate("document.querySelector('#xk').disabled") and "Nessun audio o sprite" in p.evaluate("document.querySelector('#modal').innerText"))
    p.evaluate("closeModal()"); p.evaluate("go('menu')"); p.wait_for_timeout(300); p.click("[data-tile=new]"); p.wait_for_timeout(1500)
    check("a run starts", p.evaluate("screen") == "game"); check("no console errors (smoke)", not errs, errs); ctx.close()
    b.close()
srv.shutdown()
print(sum(RES), "/", len(RES), "passed"); sys.exit(0 if all(RES) else 1)
