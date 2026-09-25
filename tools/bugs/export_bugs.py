#!/usr/bin/env python3
"""Firestore -> repo export (F6b bug reports, F3a text edits). Two phases, so nothing is marked before it is safely pushed:

  export_bugs.py export --pending <file> [--inbox bugs/inbox] [--subs submissions] [--bugs-msg f] [--edits-msg f]
      bugs  : every `bugs` doc with exported != true      -> bugs/inbox/<YYYY-MM-DD>_<docId>.json
      edits : every `edits` doc with exported != true     -> submissions/<acct>/<YYYY-MM-DD>-testi/manifest.json (schemaVersion 2,
              one change per doc, grouped by account + UTC day), each new/updated package checked with scripts/validate_submission.py
      writes the list of exported doc paths to <pending>, and the commit messages to --bugs-msg / --edits-msg.
  export_bugs.py mark --pending <file>
      sets exported=true + exportedAt on those docs (run by the workflow only after the push succeeded).

Credentials: the service-account JSON is read from the environment variable FIREBASE_SA (Actions secret), parsed in memory only:
never written to disk, never printed. The export logic takes any Firestore-like client, so it is tested with a mock
(tools/bugs/test_export_bugs.py) and no real key. firestore.rules is never touched (the Admin SDK bypasses the rules)."""
import argparse, datetime, json, os, re, subprocess, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ACCT_RE = re.compile(r"^(master|dev[1-5])$")


def iso(v):
    """Firestore Timestamp / datetime -> ISO 8601 UTC string; everything else unchanged (recursively)."""
    if isinstance(v, datetime.datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=datetime.timezone.utc)
        return v.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(v, dict):
        return {k: iso(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [iso(x) for x in v]
    return v


def day_of(ts, today):
    return ts[:10] if isinstance(ts, str) and len(ts) >= 10 else today.isoformat()


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


# ------------------------------------------------------------------ bugs
def export_bugs(db, out_dir, today):
    """-> (file names, [doc paths to mark])"""
    files, refs = [], []
    for doc in db.collection("bugs").stream():
        data = doc.to_dict() or {}
        if data.get("exported") is True:
            continue
        out = iso(data)
        name = f"{day_of(out.get('ts'), today)}_{doc.id}.json"
        rec = {"id": doc.id}
        rec.update(out)
        write_json(os.path.join(out_dir, name), rec)
        files.append(name)
        refs.append("bugs/" + doc.id)
    return files, refs


# ------------------------------------------------------------------ text edits (submission format v2, docs/submissions-v2.md)
def ver_key(v):
    return tuple(int(x) for x in re.findall(r"\d+", str(v))) or (0,)


def edit_to_change(doc_id, d):
    ch = {"id": doc_id, "type": d.get("kind"), "character": d.get("char"), "target": d.get("target"),
          "before": d.get("before"), "value": d.get("value")}
    for k in ("screen", "locator", "note"):
        if d.get(k) not in (None, ""):
            ch[k] = d[k]
    if d.get("base"):
        ch["base"] = d["base"]
    if d.get("ts"):
        ch["sentAt"] = d["ts"]
    return ch


def export_edits(db, subs_dir, today, validate=None):
    """-> (packages [dir], [doc paths to mark], [skipped msgs], [validation failures])"""
    groups, refs_by, skipped = {}, {}, []
    for doc in db.collection("edits").stream():
        data = doc.to_dict() or {}
        if data.get("exported") is True:
            continue
        d = iso(data)
        acct = d.get("acct")
        if not isinstance(acct, str) or not ACCT_RE.match(acct):
            skipped.append(f"edits/{doc.id}: unknown account '{acct}' (left in Firestore)")
            continue
        key = (acct, day_of(d.get("ts"), today))
        groups.setdefault(key, []).append((doc.id, d))
        refs_by.setdefault(key, []).append("edits/" + doc.id)
    packages, refs, failures = [], [], []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    for (acct, day), items in sorted(groups.items()):
        pdir = os.path.join(subs_dir, acct, day + "-testi")
        mpath = os.path.join(pdir, "manifest.json")
        man = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else None
        changes = list(man["changes"]) if man else []
        have = {c.get("id") for c in changes}
        for doc_id, d in items:
            if doc_id not in have:
                changes.append(edit_to_change(doc_id, d))
        bases = [c["base"] for c in changes if c.get("base")] or ["0.0"]
        sites = {(d.get("meta") or {}).get("site") for _, d in items}
        man = {"schemaVersion": 2, "developer": acct, "baseVersion": min(bases, key=ver_key),
               "site": "stable" if sites == {"stable"} else "dev", "exportedAt": now,
               "note": f"Modifiche inviate dal gioco con «Invia testi» ({len(changes)})", "changes": changes}
        write_json(mpath, man)
        packages.append(pdir)
        refs += refs_by[(acct, day)]
        if validate:
            ok, out = validate(pdir)
            if not ok:
                failures.append((pdir, out))
    return packages, refs, skipped, failures


def run_validator(pdir):
    p = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "validate_submission.py"), pdir], capture_output=True, text=True, cwd=REPO)
    return p.returncode == 0, (p.stdout + p.stderr).strip()


# ------------------------------------------------------------------ marking + client + CLI
def mark(db, refs, server_ts):
    for r in refs:
        col, doc_id = r.split("/", 1)
        db.collection(col).document(doc_id).update({"exported": True, "exportedAt": server_ts})


def real_client():
    import firebase_admin
    from firebase_admin import credentials, firestore
    sa = os.environ.get("FIREBASE_SA", "")
    if not sa.strip():
        sys.exit("FIREBASE_SA is not set")
    try:
        cred = credentials.Certificate(json.loads(sa))
    except Exception:
        sys.exit("FIREBASE_SA is not a valid service-account JSON")  # never echo the value
    firebase_admin.initialize_app(cred)
    return firestore.client(), firestore.SERVER_TIMESTAMP


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["export", "mark"])
    ap.add_argument("--pending", required=True)
    ap.add_argument("--inbox", default=os.path.join(REPO, "bugs", "inbox"))
    ap.add_argument("--subs", default=os.path.join(REPO, "submissions"))
    ap.add_argument("--bugs-msg")
    ap.add_argument("--edits-msg")
    a = ap.parse_args()
    db, ts = real_client()
    today = datetime.datetime.now(datetime.timezone.utc).date()
    if a.phase == "export":
        files, brefs = export_bugs(db, a.inbox, today)
        pk, erefs, skipped, fails = export_edits(db, a.subs, today, run_validator)
        json.dump({"refs": brefs + erefs}, open(a.pending, "w"))
        if a.bugs_msg:
            open(a.bugs_msg, "w", encoding="utf-8").write(f"bugs: export {len(files)} report(s)\n")
        if a.edits_msg:
            msg = f"submissions: export {len(erefs)} text edit(s)\n"
            for pdir, out in fails:
                msg += f"\nvalidator FAILED for {os.path.relpath(pdir, REPO)}:\n{out}\n"
            open(a.edits_msg, "w", encoding="utf-8").write(msg)
        print(f"bugs: {len(files)}, text edits: {len(erefs)} in {len(pk)} package(s), validator failures: {len(fails)}, skipped: {len(skipped)}")
        for s in skipped:
            print("skipped:", s)
    else:
        refs = json.load(open(a.pending))["refs"]
        mark(db, refs, ts)
        print(f"marked {len(refs)} document(s) exported")


if __name__ == "__main__":
    main()
