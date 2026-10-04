#!/usr/bin/env python3
"""Player-account cleanup (L3a dry-run, L3b live). Reads Auth users + Firestore and prints what would be deleted.

  cleanup.py            DRY-RUN (default): deletes and writes NOTHING; no write call is reachable from this path
  cleanup.py --live     LIVE: performs the deletions listed below

Run by .github/workflows/players-cleanup.yml: manual (mode dry-run or live) and daily at 06:30 UTC (live).

Reads: all Auth users (paginated), collections devs, players, delreq, and the document ids of saves.
Categories (non-exempt accounts only; exempt = a uid with a devs doc, or an email name master / dev1-dev5):
  A unconfirmed : players.confirmed older than 30 days -> players/{uid}, saves/{uid}, saves/{uid}_dev, then the Auth user
  B orphan      : Auth user with no players and no devs doc, created more than 24 h ago -> saves/{uid}, saves/{uid}_dev, Auth user
  C delreq      : junk (no such user) -> the delreq doc; cancelled (signed in OR token refreshed after the request) -> the delreq doc;
                  due (request older than 7 days) -> players/{uid}, both saves, Auth user, then the delreq doc; else pending
  E stray       : players docs and saves docs with no Auth user (never for a uid with a devs doc) -> that document
All "older than" rules are strict (exactly on the limit = not yet). A uid that is both A and C3 is processed once, with C3's steps.

Live safety:
  - cap, checked before any deletion: more than 25 accounts or more than 100 documents -> nothing deleted, exit 2;
  - a devs doc is re-read before an account's first delete and again right before its Auth delete: an exempt account is skipped;
  - a failure stops that item only (its later steps are not run; the next run retries it), the others still run, exit 1 at the end;
  - a missing document and an Auth UserNotFound count as done (idempotent).

The repo is PUBLIC and so are the Actions logs: output carries only masked names (2 letters + ... + length + age), never a uid, an
email, a full username or anything from the credentials. Credentials: env FIREBASE_SA (service-account JSON), parsed in memory only."""
import argparse, datetime, json, os, sys

UTC = datetime.timezone.utc
DOM = "@mangiasassi.invalid"
EXEMPT_NAMES = {"master", "dev1", "dev2", "dev3", "dev4", "dev5"}
CONF_DAYS, ORPHAN_HOURS, DELREQ_DAYS = 30, 24, 7
ACCOUNT_CAP, DOC_CAP = 25, 100
MSG_AUTH_DENIED = "PERMESSO NEGATO: il service account non può leggere gli utenti Auth — serve il ruolo Firebase Authentication Admin"
MSG_FS_DENIED = "PERMESSO NEGATO: il service account non può leggere Firestore"
MSG_CAP = "LIMITE SUPERATO: {a} account / {d} documenti — nessuna eliminazione"
HDR_DRY = "DRY-RUN — nothing deleted"
HDR_LIVE = "LIVE — eliminazioni eseguite"
HDR_LIVE_NO = "LIVE — eliminazioni NON eseguite"
TITLES = [
    ("A", "A) non confermati (> 30 giorni)", "utente Auth + players + saves"),
    ("B", "B) orfani (> 24 h, senza players né devs)", "utente Auth + saves"),
    ("C1", "C1) delreq spazzatura (utente inesistente)", "il doc delreq"),
    ("C2", "C2) delreq annullate (accesso dopo la richiesta)", "il doc delreq"),
    ("C3", "C3) delreq scadute (> 7 giorni)", "utente Auth + players + saves + il doc delreq"),
    ("E", "E) documenti orfani (senza utente Auth)", "il documento"),
]


def utc(v):
    """datetime / epoch milliseconds -> aware UTC datetime (None stays None)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.datetime.fromtimestamp(v / 1000.0, UTC)
    if isinstance(v, datetime.datetime):
        return v.replace(tzinfo=UTC) if v.tzinfo is None else v.astimezone(UTC)
    return None


def latest(*ts):
    vals = [t for t in ts if t is not None]
    return max(vals) if vals else None


def name_of(email):
    e = (email or "").lower()
    return e[:-len(DOM)] if e.endswith(DOM) else None


def mask(name, age):
    n = name or "?"
    return f"{n[:2]}… ({len(n)}) · {int(age.total_seconds() // 86400)} g"


def class_names(exc):
    return " ".join(c.__name__ for c in type(exc).__mro__)


def is_perm(exc):
    names = class_names(exc)
    low = (names + " " + str(exc)).lower()
    return "permissiondenied" in names.lower() or "forbidden" in low or "insufficient permission" in low or "403" in low


class StageError(Exception):
    def __init__(self, stage, cause):
        super().__init__(stage)
        self.stage, self.cause = stage, cause


class Skipped(Exception):
    pass


def read_users(auth):
    out, page = [], auth.list_users()
    while page:
        for u in page.users:
            md = u.user_metadata
            out.append({"uid": u.uid, "email": u.email, "created": utc(md.creation_timestamp),
                        "last": utc(md.last_sign_in_timestamp),
                        "refresh": utc(getattr(md, "last_refresh_timestamp", None))})
        page = page.get_next_page()
    return out


def read_all(auth, db):
    try:
        users = read_users(auth)
    except Exception as e:
        raise StageError("auth", e)
    try:
        devs = {d.id for d in db.collection("devs").stream()}
        players = {d.id: (d.to_dict() or {}) for d in db.collection("players").stream()}
        delreq = {d.id: (d.to_dict() or {}) for d in db.collection("delreq").stream()}
        saves = {r.id for r in db.collection("saves").list_documents()}
    except Exception as e:
        raise StageError("firestore", e)
    return users, devs, players, delreq, saves


def fs(coll, doc):
    return ("fs", coll, doc)


def build_plan(users, devs, players, delreq, saves, now):
    """Pure: -> {"items": [...], "pending": [labels], "exempt_delreq": n, "accounts": n, "docs": n}.
    Each item = {cat, label, uid, name, steps}; steps are ("fs", collection, doc_id) or ("auth", uid), in run order."""
    by_uid = {u["uid"]: u for u in users}
    by_name = {}
    for u in users:
        n = name_of(u["email"])
        if n:
            by_name[n] = u
    exempt_uids = {u["uid"] for u in users if u["uid"] in devs or name_of(u["email"]) in EXEMPT_NAMES}
    items, pending, exempt_delreq = [], [], 0

    def add(cat, label, uid, name, steps):
        items.append({"cat": cat, "label": label, "uid": uid, "name": name, "steps": steps})

    for u in users:
        if u["uid"] in exempt_uids:
            continue
        uid, n = u["uid"], name_of(u["email"])
        p = players.get(uid)
        if p is not None:
            c = utc(p.get("confirmed"))
            if c is not None and now - c > datetime.timedelta(days=CONF_DAYS):
                label = mask(p.get("username") if isinstance(p.get("username"), str) else n, now - c)
                add("A", label, uid, n, [fs("players", uid), fs("saves", uid), fs("saves", uid + "_dev"), ("auth", uid)])
        elif uid not in devs and u["created"] is not None and now - u["created"] > datetime.timedelta(hours=ORPHAN_HOURS):
            add("B", mask(n, now - u["created"]), uid, n, [fs("saves", uid), fs("saves", uid + "_dev"), ("auth", uid)])
    for uname, d in sorted(delreq.items()):
        ts = utc(d.get("ts"))
        u = by_name.get(uname.lower())
        age = (now - ts) if ts else datetime.timedelta(0)
        if u is not None and u["uid"] in exempt_uids:
            exempt_delreq += 1
        elif u is None:
            add("C1", mask(uname, age), None, None, [fs("delreq", uname)])
        elif ts is not None and latest(u["last"], u["refresh"]) is not None and latest(u["last"], u["refresh"]) > ts:
            add("C2", mask(uname, age), None, None, [fs("delreq", uname)])
        elif ts is not None and age > datetime.timedelta(days=DELREQ_DAYS):
            uid = u["uid"]
            add("C3", mask(uname, age), uid, uname, [fs("players", uid), fs("saves", uid), fs("saves", uid + "_dev"),
                                                    ("auth", uid), fs("delreq", uname)])
        else:
            pending.append(mask(uname, age))
    # one account, one set of steps: C3 wins over A (its steps include A's and the delreq)
    c3 = {it["uid"] for it in items if it["cat"] == "C3"}
    items = [it for it in items if not (it["cat"] == "A" and it["uid"] in c3)]
    stray = 0
    for pid in sorted(players):
        if pid not in by_uid and pid not in devs:
            stray += 1
            add("E", f"players n.{stray}", pid, None, [fs("players", pid)])
    for s in sorted(saves):
        base = s[:-4] if s.endswith("_dev") else s
        if base not in by_uid and base not in devs:
            stray += 1
            add("E", f"saves n.{stray}", base, None, [fs("saves", s)])
    accounts = sum(1 for it in items for st in it["steps"] if st[0] == "auth")
    docs = sum(1 for it in items for st in it["steps"] if st[0] == "fs")
    return {"items": items, "pending": pending, "exempt_delreq": exempt_delreq, "accounts": accounts, "docs": docs,
            "totals": {"auth": len(users), "exempt": len(exempt_uids), "players": len(players), "delreq": len(delreq)}}


def exempt_now(db, uid, name):
    if name in EXEMPT_NAMES:
        return True
    return bool(db.collection("devs").document(uid).get().exists)


def delete_auth(auth, uid):
    try:
        auth.delete_user(uid)
    except Exception as e:
        if "UserNotFoundError" in class_names(e):
            return
        raise


def execute(plan, auth, db):
    """Live only. Mutates item['status'] and returns the counters. Failure text is the exception CLASS name only."""
    st = {"acc": 0, "docs": 0, "fail": 0, "skip": 0}
    for it in plan["items"]:
        uid, name = it["uid"], it["name"]
        try:
            if uid is not None and exempt_now(db, uid, name):
                raise Skipped()
            for step in it["steps"]:
                if step[0] == "auth":
                    if exempt_now(db, uid, name):
                        raise Skipped()
                    delete_auth(auth, uid)
                    st["acc"] += 1
                else:
                    db.collection(step[1]).document(step[2]).delete()
                    st["docs"] += 1
            it["status"] = "eliminato"
        except Skipped:
            st["skip"] += 1
            it["status"] = "saltato (dev)"
        except Exception as e:
            st["fail"] += 1
            it["status"] = f"fallito ({type(e).__name__})"
    return st


def render(plan, now, live=False, st=None, capped=False):
    t = plan["totals"]
    if capped:
        head = [HDR_LIVE_NO, MSG_CAP.format(a=plan["accounts"], d=plan["docs"])]
    else:
        head = [HDR_LIVE if live else HDR_DRY]
    L = head + ["Esecuzione: " + now.strftime("%Y-%m-%d %H:%M UTC"), "",
                f"Utenti Auth: {t['auth']} · dev esenti: {t['exempt']} · players: {t['players']} · delreq: {t['delreq']}", ""]
    for cat, title, what in TITLES:
        items = [it for it in plan["items"] if it["cat"] == cat]
        if live and not capped:
            L.append(f"{title}: {len(items)}")
        else:
            L.append(f"{title}: {len(items)}" + (f" — eliminerebbe {what}" if items else ""))
        for it in items:
            L.append("  " + it["label"] + (f" — {it['status']}" if live and not capped and "status" in it else ""))
    L.append(f"C4) delreq in attesa: {len(plan['pending'])} (nessuna azione)")
    L.extend("  " + x for x in plan["pending"])
    if plan["exempt_delreq"]:
        L.append(f"delreq di account esenti ignorate: {plan['exempt_delreq']}")
    if live and not capped:
        L += ["", f"Eliminati: account {st['acc']} · documenti {st['docs']} · falliti {st['fail']} · saltati (dev) {st['skip']}"]
    else:
        L += ["", f"Da eliminare: account {plan['accounts']} · documenti {plan['docs']}"]
    return "\n".join(L) + "\n"


def emit(text):
    sys.stdout.write(text)
    sp = os.environ.get("GITHUB_STEP_SUMMARY")
    if sp:
        with open(sp, "a", encoding="utf-8", newline="\n") as f:
            f.write("```\n" + text + "```\n")


def run(auth, db, now=None, live=False):
    """-> exit code: 0 ok, 1 some item failed (live), 2 cap exceeded (live, nothing deleted), 1 on a read error.
    `auth` needs list_users() and (live) delete_user(); `db` needs collection(name).stream()/.list_documents() and (live)
    document(id).get()/.delete()."""
    now = now or datetime.datetime.now(UTC)
    try:
        data = read_all(auth, db)
    except StageError as e:
        if is_perm(e.cause):
            emit((MSG_AUTH_DENIED if e.stage == "auth" else MSG_FS_DENIED) + "\n")
        else:
            emit(f"Errore durante la lettura ({e.stage}): {type(e.cause).__name__}\n")
        return 1
    plan = build_plan(*data, now)
    if not live:
        emit(render(plan, now))
        return 0
    if plan["accounts"] > ACCOUNT_CAP or plan["docs"] > DOC_CAP:
        emit(render(plan, now, live=True, capped=True))
        return 2
    st = execute(plan, auth, db)
    emit(render(plan, now, live=True, st=st))
    return 1 if st["fail"] else 0


def real_clients():
    import firebase_admin
    from firebase_admin import auth, credentials, firestore
    sa = os.environ.get("FIREBASE_SA", "")
    if not sa.strip():
        sys.exit("FIREBASE_SA is not set")
    try:
        cred = credentials.Certificate(json.loads(sa))
    except Exception:
        sys.exit("FIREBASE_SA is not a valid service-account JSON")  # never echo the value
    firebase_admin.initialize_app(cred)
    return auth, firestore.client()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Player-account cleanup (dry-run by default).")
    ap.add_argument("--live", action="store_true", help="perform the deletions (default: dry-run, deletes nothing)")
    args = ap.parse_args()
    a, d = real_clients()
    sys.exit(run(a, d, live=args.live))
