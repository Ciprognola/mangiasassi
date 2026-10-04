#!/usr/bin/env python3
"""Mocked test of export_bugs (no Firestore, no key). Run: python tools/bugs/test_export_bugs.py"""
import datetime, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_bugs as E

RES = []


def check(n, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + n, extra)


class Snap:
    def __init__(self, e): self.exists = e


class Ref:
    def __init__(self, doc): self.doc = doc
    def update(self, d): self.doc.data.update(d)
    def get(self): return Snap(True)


class Missing:
    def get(self): return Snap(False)


class Doc:
    def __init__(self, id_, data): self.id, self.data, self.reference = id_, data, Ref(self)
    def to_dict(self): return dict(self.data)


class Col:
    def __init__(self, docs): self.docs = docs
    def stream(self): return iter(list(self.docs.values()))
    def document(self, id_): return self.docs[id_].reference if id_ in self.docs else Missing()


class DB:
    def __init__(self, cols): self.cols = {k: {d.id: d for d in v} for k, v in cols.items()}
    def collection(self, name): return Col(self.cols.setdefault(name, {}))


T = datetime.datetime(2026, 9, 25, 23, 30, tzinfo=datetime.timezone.utc)
bugs = [
    Doc("a1", {"uid": "u1", "text": "ciao è un problema", "screen": "menu-home-roccia", "version": "0.4_5", "char": "roccia", "ts": T, "ua": "UA", "meta": {"acct": "dev1", "site": "dev", "girone": None, "qts": 5}}),
    Doc("b2", {"uid": "u2", "text": "x", "screen": "fa-floor1-play", "version": "0.4_5", "char": "algidone", "ts": T - datetime.timedelta(days=2), "ua": "UA", "meta": {}}),
    Doc("c3", {"uid": "u3", "text": "già esportato", "ts": T, "exported": True}),
    Doc("d4", {"uid": "u4", "text": "senza ts"}),
]


def edit(id_, acct, kind, target, before, value, ts=T, base="0.4_5", **kw):
    d = {"uid": "u", "acct": acct, "kind": kind, "char": "roccia", "target": target, "before": before, "value": value, "base": base, "ts": ts, "meta": {"site": "dev"}}
    d.update(kw)
    return Doc(id_, d)


edits = [
    edit("e1", "dev3", "text", "dialogue.win", "Vittoria", "Che vittoria!", screen="maze-over", note="più vivace"),
    edit("e2", "dev3", "colour", "tile.new.color", "#f2c230", "#ffcc00", char="shared", base="0.4_4"),
    edit("e3", "dev3", "scale", "tile.wish.scale", "1", "1.2", ts=T + datetime.timedelta(hours=2)),  # next UTC day
    edit("e4", "master", "text", "dialogue.lose", None, "Peccato", locator={"text": "Peccato", "pos": "fine partita"}),
    edit("e5", "dev3", "text", "x", "a", "b", exported=True),
    edit("e6", "hacker/../x", "text", "x", "a", "b"),
]
with tempfile.TemporaryDirectory() as d:
    db = DB({"bugs": bugs, "edits": edits, "devs": [Doc("u1", {"role": "dev1"})]})  # u1 is a developer (golden output)
    inbox, subs = os.path.join(d, "inbox"), os.path.join(d, "submissions")
    files, brefs, bskip = E.export_bugs(db, inbox, datetime.date(2026, 9, 26))
    check("bugs: only the not-yet-exported docs", sorted(files) == ["2026-09-23_b2.json", "2026-09-25_a1.json", "2026-09-26_d4.json"], files)
    rec = json.load(open(os.path.join(inbox, "2026-09-25_a1.json"), encoding="utf-8"))
    check("bugs: all fields, ts as ISO string, meta included", rec["id"] == "a1" and rec["ts"] == "2026-09-25T23:30:00Z" and rec["meta"]["qts"] == 5 and rec["text"] == "ciao è un problema" and rec["uid"] == "u1", rec)
    check("bugs: nothing marked during export (two-phase)", not any("exported" in x.data and x.id != "c3" for x in bugs))
    pk, erefs, skipped, fails = E.export_edits(db, subs, datetime.date(2026, 9, 26), E.run_validator)
    check("edits: grouped by account + UTC day into <acct>/<day>-testi", sorted(os.path.relpath(p, subs).replace("\\", "/") for p in pk) == ["dev3/2026-09-25-testi", "dev3/2026-09-26-testi", "master/2026-09-25-testi"], pk)
    m = json.load(open(os.path.join(subs, "dev3", "2026-09-25-testi", "manifest.json"), encoding="utf-8"))
    check("edits: manifest v2 fields", m["schemaVersion"] == 2 and m["developer"] == "dev3" and m["baseVersion"] == "0.4_4" and m["site"] == "dev" and m["exportedAt"].endswith("Z") and m["note"] and [c["id"] for c in m["changes"]] == ["e1", "e2"], m)
    c1 = m["changes"][0]
    check("edits: change fields (type, before, value, screen, note, base, sentAt; no uid)", c1["type"] == "text" and c1["before"] == "Vittoria" and c1["value"] == "Che vittoria!" and c1["screen"] == "maze-over" and c1["note"] == "più vivace" and c1["base"] == "0.4_5" and c1["sentAt"] == "2026-09-25T23:30:00Z" and "uid" not in c1 and c1["character"] == "roccia", c1)
    m2 = json.load(open(os.path.join(subs, "master", "2026-09-25-testi", "manifest.json"), encoding="utf-8"))
    check("edits: locator kept, before null", m2["changes"][0]["locator"]["pos"] == "fine partita" and m2["changes"][0]["before"] is None)
    check("edits: already-exported and bad-account docs skipped", sorted(erefs) == ["edits/e1", "edits/e2", "edits/e3", "edits/e4"] and len(skipped) == 1 and "hacker" in skipped[0], skipped)
    check("edits: validator ran on every package and passed", not fails, fails)
    # a broken edit (bad colour) is still exported, the failure is reported
    bad = DB({"edits": [edit("z1", "dev2", "colour", "t", "#000000", "rosso")]})
    pk2, r2, s2, f2 = E.export_edits(bad, subs, datetime.date(2026, 9, 26), E.run_validator)
    check("edits: failing package is still written and listed", len(f2) == 1 and "#rrggbb" in f2[0][1] and r2 == ["edits/z1"], f2)
    # same-day rerun merges by id
    more = DB({"edits": [edit("e1", "dev3", "text", "dialogue.win", "Vittoria", "Che vittoria!"), edit("e7", "dev3", "text", "dialogue.x", "a", "b")]})
    E.export_edits(more, subs, datetime.date(2026, 9, 26))
    m = json.load(open(os.path.join(subs, "dev3", "2026-09-25-testi", "manifest.json"), encoding="utf-8"))
    check("edits: rerun the same day merges by id (no duplicates)", [c["id"] for c in m["changes"]] == ["e1", "e2", "e7"], [c["id"] for c in m["changes"]])
    E.mark(db, brefs + erefs, "SERVER_TS")
    check("mark: docs marked exported + exportedAt only in phase 2", all(x.data.get("exported") is True and x.data.get("exportedAt") == "SERVER_TS" for x in bugs if x.id != "c3") and all(x.data.get("exportedAt") == "SERVER_TS" for x in edits[:4]))
    check("mark: skipped docs untouched", "exported" not in edits[5].data and "exportedAt" not in bugs[2].data)
    files2, _, _ = E.export_bugs(db, inbox, datetime.date(2026, 9, 27))
    check("second run exports nothing", files2 == [] and E.export_edits(db, subs, datetime.date(2026, 9, 27))[0] == [])
    # f) dev report: same bytes as before L5 (uid, ua and meta.acct all kept)
    dev_bytes = open(os.path.join(inbox, "2026-09-25_a1.json"), "rb").read()
    dev_exp = json.dumps({"char": "roccia", "id": "a1", "meta": {"acct": "dev1", "girone": None, "qts": 5, "site": "dev"}, "screen": "menu-home-roccia", "text": "ciao è un problema", "ts": "2026-09-25T23:30:00Z", "ua": "UA", "uid": "u1", "version": "0.4_5"}, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    check("f) dev report: byte-identical to the pre-L5 output", dev_bytes == dev_exp.encode("utf-8"), dev_bytes[:120])

    # ---- L5: player reports
    def pdb():
        ps = [Doc(f"p{i}", {"uid": "pl1", "text": f"segnalazione {i}", "screen": "menu-home-roccia", "version": "0.4.5_43", "char": "roccia", "ts": T + datetime.timedelta(hours=i), "ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8) Chrome/120 Mobile", "meta": {"acct": "pippo", "site": "stable", "girone": 3, "diff": "medium", "viewport": "390x844", "qts": 1}}) for i in range(7)]
        ps.append(Doc("q0", {"uid": "pl2", "text": "altro giocatore", "screen": "menu-home-algidone", "version": "0.4.5_43", "char": "algidone", "ts": T, "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", "meta": {"acct": None, "site": "stable"}}))
        ps += [Doc(f"d{i}", {"uid": "dv1", "text": f"dev {i}", "ts": T + datetime.timedelta(hours=i), "ua": "UA-dev", "meta": {"acct": "dev1"}}) for i in range(7)]
        return DB({"bugs": ps, "devs": [Doc("dv1", {"role": "dev1"})]})

    inbox2 = os.path.join(d, "inbox2")
    pdb_ = pdb()
    files3, refs3, skip3 = E.export_bugs(pdb_, inbox2, datetime.date(2026, 9, 26))
    pf = os.path.join(inbox2, "2026-09-25_p0.json")
    g_txt = open(pf, encoding="utf-8").read() if os.path.exists(pf) else ""
    g_rec = json.loads(g_txt) if g_txt else {}
    # g) player report: no uid, ua, email or account anywhere in the file or its name
    blob_g = g_txt + " ".join(files3)
    check("g) player file: no uid, ua or account name in content or name", bool(g_rec) and not any(x in blob_g for x in ("pl1", "pl2", "Mozilla", "pippo", "Android 14")), files3[:3])
    check("g) player file: «giocatore» + platform present, ua gone", g_rec.get("uid") == "giocatore" and g_rec.get("platform") == "Android" and "ua" not in g_rec and g_rec.get("meta", {}).get("acct") == "giocatore", g_rec)
    check("g) player file: text, screen, version, char, ts and other meta kept", g_rec.get("text") == "segnalazione 0" and g_rec.get("screen") == "menu-home-roccia" and g_rec.get("version") == "0.4.5_43" and g_rec.get("char") == "roccia" and g_rec.get("ts") == "2026-09-25T23:30:00Z" and g_rec.get("meta", {}).get("girone") == 3, g_rec)
    # i) per-player cap: 7 from pl1 -> the 5 oldest; another player and a developer unaffected
    written_p1 = sorted(r for r in refs3 if r.startswith("bugs/p"))
    check("i) 7 reports from one player: the 5 oldest written", written_p1 == ["bugs/p0", "bugs/p1", "bugs/p2", "bugs/p3", "bugs/p4"], written_p1)
    check("i) the 2 newest marked skipped", sorted(skip3) == ["bugs/p5", "bugs/p6"], skip3)
    check("i) another player's report unaffected", "bugs/q0" in refs3)
    check("i) developer: 7 reports all written (no cap)", sum(1 for r in refs3 if r.startswith("bugs/d")) == 7)
    E.mark(pdb_, refs3, "TS", skip3)
    check("i) mark: skipped docs exported + skipped, written ones exported only", pdb_.cols["bugs"]["p5"].data.get("skipped") is True and pdb_.cols["bugs"]["p5"].data.get("exported") is True and "skipped" not in pdb_.cols["bugs"]["p0"].data)
    # j) the run's log: counts only, never a player's uid, ua or account
    import io, contextlib
    E.real_client = lambda: (pdb(), "TS")
    buf = io.StringIO()
    sys.argv = ["export_bugs.py", "export", "--pending", os.path.join(d, "pending.json"), "--inbox", os.path.join(d, "inbox3"), "--subs", os.path.join(d, "subs3")]
    with contextlib.redirect_stdout(buf):
        E.main()
    out_log = buf.getvalue()
    check("j) log prints the skipped count line", "Segnalazioni saltate (limite): 2" in out_log, out_log)
    check("j) log has no player uid, ua or account", not any(x in out_log for x in ("pl1", "pl2", "Mozilla", "pippo", "Android")), out_log)
    # h) platform mapping
    pm = [("Mozilla/5.0 (Linux; Android 14; Pixel 8)", "Android"), ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", "iOS"),
          ("Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)", "iOS"), ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "desktop"),
          ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "desktop"), ("Mozilla/5.0 (X11; Linux x86_64)", "desktop"),
          ("curl/8.0", "altro"), ("", "altro"), (None, "altro")]
    check("h) platform mapping: Android / iOS / desktop / altro", all(E.platform_of(u) == want for u, want in pm), [(u, E.platform_of(u)) for u, w in pm if E.platform_of(u) != w])

    blob = "".join(open(os.path.join(r, f), encoding="utf-8").read() for r, _, fs in os.walk(d) for f in fs)
    check("no credentials anywhere in the output", "private_key" not in blob)
print(sum(RES), "/", len(RES), "passed"); sys.exit(0 if all(RES) else 1)
