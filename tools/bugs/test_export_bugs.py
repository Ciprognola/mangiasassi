#!/usr/bin/env python3
"""Mocked test of export_bugs.export (no Firestore, no key). Run: python tools/bugs/test_export_bugs.py"""
import datetime, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_bugs

RES = []
def check(n, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + n, extra)

class Ref:
    def __init__(self, doc): self.doc = doc
    def update(self, d): self.doc.data.update(d)

class Doc:
    def __init__(self, id_, data): self.id, self.data, self.reference = id_, data, Ref(self)
    def to_dict(self): return dict(self.data)

class Col:
    def __init__(self, docs): self.docs = docs
    def stream(self): return iter(list(self.docs))

class DB:
    def __init__(self, docs): self.docs = docs
    def collection(self, name):
        assert name == "bugs"; return Col(self.docs)

T = datetime.datetime(2026, 9, 25, 23, 30, tzinfo=datetime.timezone.utc)
docs = [
    Doc("a1", {"uid": "u1", "text": "ciao è un problema", "screen": "menu-home-roccia", "version": "0.4_5", "char": "roccia", "ts": T, "ua": "UA", "meta": {"acct": "dev1", "site": "dev", "girone": None, "qts": 5}}),
    Doc("b2", {"uid": "u2", "text": "x", "screen": "fa-floor1-play", "version": "0.4_5", "char": "algidone", "ts": T - datetime.timedelta(days=2), "ua": "UA", "meta": {}}),
    Doc("c3", {"uid": "u3", "text": "già esportato", "ts": T, "exported": True}),
    Doc("d4", {"uid": "u4", "text": "senza ts"}),
]
with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, "inbox")
    files = export_bugs.export(DB(docs), out, "SERVER_TS", today=datetime.date(2026, 9, 26))
    check("exports only the not-yet-exported docs", sorted(files) == ["2026-09-23_b2.json", "2026-09-25_a1.json", "2026-09-26_d4.json"], files)
    rec = json.load(open(os.path.join(out, "2026-09-25_a1.json"), encoding="utf-8"))
    check("all fields, ts as ISO string, meta included", rec["id"] == "a1" and rec["ts"] == "2026-09-25T23:30:00Z" and rec["meta"]["qts"] == 5 and rec["text"] == "ciao è un problema" and rec["uid"] == "u1", rec)
    check("docs marked exported + exportedAt", all(x.data.get("exported") is True and x.data.get("exportedAt") == "SERVER_TS" for x in docs if x.id != "c3"))
    check("already exported doc untouched", "exportedAt" not in docs[2].data)
    again = export_bugs.export(DB(docs), out, "SERVER_TS")
    check("second run exports nothing", again == [])
    check("no credentials anywhere in the output", "private_key" not in "".join(open(os.path.join(out, f), encoding="utf-8").read() for f in os.listdir(out)))
print(sum(RES), "/", len(RES), "passed"); sys.exit(0 if all(RES) else 1)
