#!/usr/bin/env python3
"""Player-account cleanup, DRY-RUN (L3a): reads Auth users + Firestore and prints what L3b would delete. It deletes and writes NOTHING.

  cleanup.py            (run by .github/workflows/players-cleanup.yml, workflow_dispatch only)

Reads: all Auth users (paginated), collections devs, players, delreq, and the document ids of saves.
Categories (non-exempt accounts only; exempt = a uid with a devs doc, or an email name master / dev1-dev5):
  A unconfirmed : players.confirmed older than 30 days            -> Auth user + players/{uid} + saves/{uid} + saves/{uid}_dev
  B orphan      : Auth user with no players and no devs doc, created more than 24 h ago -> Auth user + both saves
  C delreq      : junk (no such user) -> the delreq doc; cancelled (signed in after the request) -> the delreq doc;
                  due (request older than 7 days) -> Auth user + players + both saves + the delreq doc; else pending
  D info        : players docs with no Auth user; saves docs whose uid has no Auth user (counted only)
All "older than" rules are strict (exactly on the limit = not yet).
The repo is PUBLIC and so are the Actions logs: output carries only masked names (2 letters + ... + length + age), never a uid, an
email, a full username or anything from the credentials. Credentials: env FIREBASE_SA (service-account JSON), parsed in memory only."""
import datetime, json, os, sys

UTC = datetime.timezone.utc
DOM = "@mangiasassi.invalid"
EXEMPT_NAMES = {"master", "dev1", "dev2", "dev3", "dev4", "dev5"}
CONF_DAYS, ORPHAN_HOURS, DELREQ_DAYS = 30, 24, 7
MSG_AUTH_DENIED = "PERMESSO NEGATO: il service account non può leggere gli utenti Auth — serve il ruolo Firebase Authentication Admin"
MSG_FS_DENIED = "PERMESSO NEGATO: il service account non può leggere Firestore"


def utc(v):
    """datetime / epoch milliseconds -> aware UTC datetime (None stays None)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.datetime.fromtimestamp(v / 1000.0, UTC)
    if isinstance(v, datetime.datetime):
        return v.replace(tzinfo=UTC) if v.tzinfo is None else v.astimezone(UTC)
    return None


def name_of(email):
    e = (email or "").lower()
    return e[:-len(DOM)] if e.endswith(DOM) else None


def mask(name, age):
    n = name or "?"
    return f"{n[:2]}… ({len(n)}) · {int(age.total_seconds() // 86400)} g"


def is_perm(exc):
    names = " ".join(c.__name__ for c in type(exc).__mro__)
    low = (names + " " + str(exc)).lower()
    return "permissiondenied" in names.lower() or "forbidden" in low or "insufficient permission" in low or "403" in low


class StageError(Exception):
    def __init__(self, stage, cause):
        super().__init__(stage)
        self.stage, self.cause = stage, cause


def read_users(auth):
    out, page = [], auth.list_users()
    while page:
        for u in page.users:
            md = u.user_metadata
            out.append({"uid": u.uid, "email": u.email, "created": utc(md.creation_timestamp), "last": utc(md.last_sign_in_timestamp)})
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


def analyse(users, devs, players, delreq, saves, now):
    """Pure: -> dict of lists of (masked label) per category, plus totals. Never touches a client."""
    by_uid = {u["uid"]: u for u in users}
    by_name = {}
    for u in users:
        n = name_of(u["email"])
        if n:
            by_name[n] = u

    def exempt(u):
        return u["uid"] in devs or name_of(u["email"]) in EXEMPT_NAMES

    exempt_uids = {u["uid"] for u in users if exempt(u)}
    r = {"A": [], "B": [], "C_junk": [], "C_cancelled": [], "C_due": [], "C_pending": [], "D_players": 0, "D_saves": 0, "exempt_delreq": 0}
    for u in users:
        if u["uid"] in exempt_uids:
            continue
        uid, n = u["uid"], name_of(u["email"])
        p = players.get(uid)
        if p is not None:
            c = utc(p.get("confirmed"))
            if c is not None and now - c > datetime.timedelta(days=CONF_DAYS):
                r["A"].append(mask(p.get("username") if isinstance(p.get("username"), str) else n, now - c))
        elif uid not in devs and u["created"] is not None and now - u["created"] > datetime.timedelta(hours=ORPHAN_HOURS):
            r["B"].append(mask(n, now - u["created"]))
    for uname, d in sorted(delreq.items()):
        ts = utc(d.get("ts"))
        u = by_name.get(uname.lower())
        age = (now - ts) if ts else datetime.timedelta(0)
        if u is not None and (u["uid"] in exempt_uids):
            r["exempt_delreq"] += 1
        elif u is None:
            r["C_junk"].append(mask(uname, age))
        elif ts is not None and u["last"] is not None and u["last"] > ts:
            r["C_cancelled"].append(mask(uname, age))
        elif ts is not None and age > datetime.timedelta(days=DELREQ_DAYS):
            r["C_due"].append(mask(uname, age))
        else:
            r["C_pending"].append(mask(uname, age))
    r["D_players"] = sum(1 for uid in players if uid not in by_uid)
    r["D_saves"] = sum(1 for s in saves if (s[:-4] if s.endswith("_dev") else s) not in by_uid)
    r["totals"] = {"auth": len(users), "exempt": len(exempt_uids), "players": len(players), "delreq": len(delreq)}
    return r


def render(r, now):
    t = r["totals"]
    L = ["DRY-RUN — nothing deleted", "Esecuzione: " + now.strftime("%Y-%m-%d %H:%M UTC"), "",
         f"Utenti Auth: {t['auth']} · dev esenti: {t['exempt']} · players: {t['players']} · delreq: {t['delreq']}", ""]

    def cat(title, what, items):
        L.append(f"{title}: {len(items)}" + (f" — eliminerebbe {what}" if items else ""))
        L.extend("  " + x for x in items)

    cat("A) non confermati (> 30 giorni)", "utente Auth + players + saves", r["A"])
    cat("B) orfani (> 24 h, senza players né devs)", "utente Auth + saves", r["B"])
    cat("C1) delreq spazzatura (utente inesistente)", "il doc delreq", r["C_junk"])
    cat("C2) delreq annullate (accesso dopo la richiesta)", "il doc delreq", r["C_cancelled"])
    cat("C3) delreq scadute (> 7 giorni)", "utente Auth + players + saves + il doc delreq", r["C_due"])
    L.append(f"C4) delreq in attesa: {len(r['C_pending'])} (nessuna azione)")
    L.extend("  " + x for x in r["C_pending"])
    if r["exempt_delreq"]:
        L.append(f"delreq di account esenti ignorate: {r['exempt_delreq']}")
    L += ["", f"D) solo informativo: players senza utente Auth: {r['D_players']} · saves senza utente Auth: {r['D_saves']}"]
    return "\n".join(L) + "\n"


def emit(text):
    sys.stdout.write(text)
    sp = os.environ.get("GITHUB_STEP_SUMMARY")
    if sp:
        with open(sp, "a", encoding="utf-8", newline="\n") as f:
            f.write("```\n" + text + "```\n")


def run(auth, db, now=None):
    """-> exit code. `auth` needs list_users(); `db` needs collection(name).stream() / .list_documents() — reads only."""
    now = now or datetime.datetime.now(UTC)
    try:
        data = read_all(auth, db)
    except StageError as e:
        if is_perm(e.cause):
            emit((MSG_AUTH_DENIED if e.stage == "auth" else MSG_FS_DENIED) + "\n")
        else:
            emit(f"Errore durante la lettura ({e.stage}): {type(e.cause).__name__}\n")
        return 1
    emit(render(analyse(*data, now), now))
    return 0


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
    a, d = real_clients()
    sys.exit(run(a, d))
