#!/usr/bin/env python3
"""F6b: export the not-yet-exported bug reports from Firestore `bugs` into bugs/inbox/<YYYY-MM-DD>_<docId>.json,
then mark each document exported=true + exportedAt (Admin SDK, bypasses the rules; firestore.rules is not touched).

Credentials: the service-account JSON arrives in the environment variable FIREBASE_SA (GitHub Actions secret). It is only
ever parsed in memory: never written to disk, never printed.

    FIREBASE_SA='{...}' python tools/bugs/export_bugs.py [out_dir]      # default out_dir = bugs/inbox
The export logic (`export`) takes any client with the small Firestore-like interface used below, so it is tested with a mock
(tools/bugs/test_export_bugs.py) and no real key.
"""
import datetime, json, os, sys


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


def export(db, out_dir, server_ts, today=None):
    """Returns the list of written file names. A document is marked exported only after its file is on disk."""
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for doc in db.collection("bugs").stream():
        data = doc.to_dict() or {}
        if data.get("exported") is True:
            continue
        out = iso(data)
        ts = out.get("ts")
        day = ts[:10] if isinstance(ts, str) and len(ts) >= 10 else today.isoformat()
        name = f"{day}_{doc.id}.json"
        rec = {"id": doc.id}
        rec.update(out)
        with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="\n") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        doc.reference.update({"exported": True, "exportedAt": server_ts})
        written.append(name)
    return written


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
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "bugs", "inbox")
    db, ts = real_client()
    files = export(db, out_dir, ts)
    print(f"exported {len(files)} report(s)")


if __name__ == "__main__":
    main()
