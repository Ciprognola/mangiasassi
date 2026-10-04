#!/usr/bin/env python3
"""Mocked test of cleanup.py (no Firebase, no key, fixed clock). Run: python tools/players/test_cleanup.py"""
import contextlib, datetime, io, os, re, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cleanup as C

RES = []


def check(n, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + n, "" if ok else extra)


UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
D = datetime.timedelta
DOM = "@mangiasassi.invalid"


def ago(**kw):
    return NOW - D(**kw)


def ms(t):
    return None if t is None else int(t.timestamp() * 1000)


class Boom(AssertionError):
    pass


class UserNotFoundError(Exception):  # same class name firebase_admin raises
    pass


class Meta:
    def __init__(self, created, last, refresh):
        self.creation_timestamp, self.last_sign_in_timestamp, self.last_refresh_timestamp = ms(created), ms(last), ms(refresh)


class User:
    def __init__(self, uid, name, created=None, last=None, refresh=None):
        self.uid, self.email = uid, name + DOM
        self.user_metadata = Meta(created if created is not None else ago(days=100), last, refresh)


class Page:
    def __init__(self, users, nxt): self.users, self.nxt = users, nxt
    def get_next_page(self): return self.nxt


class FAuth:
    def __init__(self, users, log, forbid=False, fail=()):
        self.users, self.log, self.forbid, self.fail = list(users), log, forbid, set(fail)

    def list_users(self):
        chunks = [self.users[i:i + 2] for i in range(0, len(self.users), 2)] or [[]]
        pg = None
        for ch in reversed(chunks):
            pg = Page(ch, pg)
        return pg

    def delete_user(self, uid):
        if self.forbid:
            raise Boom("auth delete called")
        self.log.append(("auth", uid))
        if uid in self.fail:
            raise RuntimeError("secret " + uid)
        before = len(self.users)
        self.users = [u for u in self.users if u.uid != uid]
        if len(self.users) == before:
            raise UserNotFoundError("no such user")


class Snap:
    def __init__(self, id_, data=None):
        self.id, self._d, self.exists = id_, data, data is not None
    def to_dict(self): return dict(self._d or {})


class DocRef:
    def __init__(self, db, coll, id_): self.db, self.coll, self.id = db, coll, id_
    def get(self): return Snap(self.id, self.db.docs.get(self.coll, {}).get(self.id))
    def delete(self):
        if self.db.forbid:
            raise Boom("firestore delete called")
        self.db.log.append(("fs", self.coll, self.id))
        if (self.coll, self.id) in self.db.fail:
            raise RuntimeError("secret " + self.id)
        self.db.docs.get(self.coll, {}).pop(self.id, None)
        self.db.hook(self.coll, self.id)


class ColRef:
    def __init__(self, db, coll): self.db, self.coll = db, coll
    def stream(self): return iter([Snap(i, d) for i, d in self.db.docs.get(self.coll, {}).items()])
    def list_documents(self): return iter([DocRef(self.db, self.coll, i) for i in list(self.db.docs.get(self.coll, {}))])
    def document(self, i): return DocRef(self.db, self.coll, i)


class FDB:
    def __init__(self, docs, log, forbid=False, fail=()):
        self.docs = {k: dict(v) for k, v in docs.items()}
        self.log, self.forbid, self.fail = log, forbid, set(fail)
        self.hook = lambda c, i: None
    def collection(self, c): return ColRef(self, c)


def world(users, devs=(), players=None, delreq=None, saves=(), forbid=False, fail_auth=(), fail_fs=()):
    log = []
    docs = {"devs": {d: {} for d in devs}, "players": dict(players or {}), "delreq": dict(delreq or {}),
            "saves": {s: {} for s in saves}}
    return FAuth(users, log, forbid, fail_auth), FDB(docs, log, forbid, fail_fs), log


def plan_of(auth, db):
    return C.build_plan(*C.read_all(auth, db), NOW)


def go(auth, db, live=False):
    """-> (rc, stdout, summary-file text). Each call gets its own GITHUB_STEP_SUMMARY file."""
    summ = os.path.join(tempfile.mkdtemp(), "summary.md")
    os.environ["GITHUB_STEP_SUMMARY"] = summ
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = C.run(auth, db, NOW, live=live)
    text = open(summ, encoding="utf-8").read() if os.path.exists(summ) else ""
    return rc, buf.getvalue(), text


def labels(plan, cat):
    return [it["label"] for it in plan["items"] if it["cat"] == cat]


def cats(plan, cat):
    return [it for it in plan["items"] if it["cat"] == cat]


def base_world(forbid=False):
    users = [
        User("UIDalpha11", "alphaone", last=ago(days=40)),                 # A (31 days)
        User("UIDexact30", "exactthirty"),                                  # confirmed exactly 30 d -> not A
        User("UIDjust301", "justover30"),                                   # 30 d + 1 s -> A
        User("UIDfresh01", "freshplayer"),                                  # fine
        User("UIDorphan1", "orphanuser", created=ago(hours=25)),            # B
        User("UIDorph24h", "orphan24h", created=ago(hours=24)),             # exactly 24 h -> not B
        User("UIDorph23h", "orphan23h", created=ago(hours=23)),             # not B
        User("UIDcancel1", "canceller", last=ago(days=1)),                  # C2
        User("UIDdue0001", "dueperson", last=ago(days=20)),                 # C3
        User("UIDpend001", "pendingone", last=ago(days=5)),                 # C4
        User("UIDseven01", "sevenexact", last=ago(days=30)),                # exactly 7 d -> pending
        User("UIDseven02", "overseven1", last=ago(days=30)),                # 7 d + 1 s -> due
        User("UIDdevdoc1", "somedevuser"),                                  # devs doc -> exempt
        User("UIDdev3old", "dev3"),                                         # exempt name
        User("UIDmasterx", "master", created=ago(days=200)),                # exempt name
    ]
    players = {
        "UIDalpha11": {"username": "alphaone", "confirmed": ago(days=31)},
        "UIDexact30": {"username": "exactthirty", "confirmed": ago(days=30)},
        "UIDjust301": {"username": "justover30", "confirmed": ago(days=30, seconds=1)},
        "UIDfresh01": {"username": "freshplayer", "confirmed": ago(days=2)},
        "UIDcancel1": {"username": "canceller", "confirmed": ago(days=2)},
        "UIDdue0001": {"username": "dueperson", "confirmed": ago(days=2)},
        "UIDpend001": {"username": "pendingone", "confirmed": ago(days=2)},
        "UIDseven01": {"username": "sevenexact", "confirmed": ago(days=2)},
        "UIDseven02": {"username": "overseven1", "confirmed": ago(days=2)},
        "UIDdevdoc1": {"username": "somedevuser", "confirmed": ago(days=90)},
        "UIDdev3old": {"username": "dev3", "confirmed": ago(days=90)},
        "UIDnoauth1": {"username": "noauthperson", "confirmed": ago(days=1)},   # E (no Auth user)
    }
    delreq = {
        "ghostrequester": {"ts": ago(days=3)},   # C1 junk
        "canceller": {"ts": ago(days=3)},        # C2
        "dueperson": {"ts": ago(days=8)},        # C3
        "pendingone": {"ts": ago(days=2)},       # pending
        "sevenexact": {"ts": ago(days=7)},       # pending (not strictly over 7 d)
        "overseven1": {"ts": ago(days=7, seconds=1)},  # C3
        "somedevuser": {"ts": ago(days=20)},     # exempt, ignored
        "dev3": {"ts": ago(days=20)},            # exempt, ignored
    }
    saves = ["UIDalpha11", "UIDalpha11_dev", "UIDnoauth1", "UIDnoauth1_dev", "UIDlostsave"]
    return world(users, devs=["UIDdevdoc1"], players=players, delreq=delreq, saves=saves, forbid=forbid)


def many_a(n):
    users, players = [], {}
    for i in range(n):
        uid, name = f"UIDmany{i:03d}", f"player{i:03d}"
        users.append(User(uid, name, last=ago(days=40)))
        players[uid] = {"username": name, "confirmed": ago(days=31)}
    return users, players


# ---------- a) dry-run default: nothing written, nothing reached
auth, db, log = base_world(forbid=True)
orig_execute = C.execute
C.execute = lambda *a, **k: (_ for _ in ()).throw(AssertionError("execute reached in dry-run"))
rc, out, summ = go(auth, db)
C.execute = orig_execute
check("a) dry-run default completes, rc 0, on mocks that raise on any write", rc == 0 and log == [], (rc, log))
check("a) dry-run header", out.startswith("DRY-RUN — nothing deleted"))

# ---------- plan contents (dry-run listing), base world
auth, db, log = base_world()
p = plan_of(auth, db)
check("plan A: unconfirmed lands in A, 31 g", any(x.startswith("al… (8) · 31 g") for x in labels(p, "A")))
check("plan A: exactly 30 d not A, 30 d + 1 s is A", len(labels(p, "A")) == 2 and any(x.startswith("ju… (10)") for x in labels(p, "A")))
check("plan B: orphan lands in B, 24 h / 23 h do not", len(labels(p, "B")) == 1 and labels(p, "B")[0].startswith("or… (10)"))
check("plan C1: junk only", [x[:2] for x in labels(p, "C1")] == ["gh"])
check("plan C2: cancelled only", [x[:2] for x in labels(p, "C2")] == ["ca"])
check("plan C3: due (exactly 7 d pending, +1 s due), exempt ignored", sorted(x[:2] for x in labels(p, "C3")) == ["du", "ov"] and p["exempt_delreq"] == 2)
check("plan C4: pending listed", sorted(x[:2] for x in p["pending"]) == ["pe", "se"], p["pending"])
check("plan E: 1 players + 3 saves without Auth user", len(labels(p, "E")) == 4 and sum(1 for x in labels(p, "E") if x.startswith("players")) == 1, labels(p, "E"))
check("plan totals", p["totals"] == {"auth": 15, "exempt": 3, "players": 12, "delreq": 8}, p["totals"])
check("plan counts: 5 accounts, 22 documents", (p["accounts"], p["docs"]) == (5, 22), (p["accounts"], p["docs"]))

# ---------- b) live: exact deletes per category, in order (Firestore before Auth; delreq last for C3)
def run_one(users, **kw):
    auth, db, log = world(users, **kw)
    rc, out, summ = go(auth, db, live=True)
    return rc, out, log


rc, out, log = run_one([User("UIDaaaaa1", "alphaa", last=ago(days=40))],
                       players={"UIDaaaaa1": {"username": "alphaa", "confirmed": ago(days=31)}},
                       saves=["UIDaaaaa1", "UIDaaaaa1_dev"])
check("b) A: players, saves, saves_dev, then Auth", rc == 0 and log == [("fs", "players", "UIDaaaaa1"), ("fs", "saves", "UIDaaaaa1"),
                                                                       ("fs", "saves", "UIDaaaaa1_dev"), ("auth", "UIDaaaaa1")], log)
rc, out, log = run_one([User("UIDbbbbb1", "orphanb", created=ago(hours=25))], saves=["UIDbbbbb1", "UIDbbbbb1_dev"])
check("b) B: saves, saves_dev, then Auth", rc == 0 and log == [("fs", "saves", "UIDbbbbb1"), ("fs", "saves", "UIDbbbbb1_dev"), ("auth", "UIDbbbbb1")], log)
rc, out, log = run_one([], delreq={"ghost": {"ts": ago(days=3)}})
check("b) C1: the delreq doc only", rc == 0 and log == [("fs", "delreq", "ghost")], log)
rc, out, log = run_one([User("UIDcccc01", "canceller", last=ago(days=1))],
                       players={"UIDcccc01": {"username": "canceller", "confirmed": ago(days=2)}},
                       delreq={"canceller": {"ts": ago(days=3)}})
check("b) C2: the delreq doc only, no account", rc == 0 and log == [("fs", "delreq", "canceller")], log)
rc, out, log = run_one([User("UIDdddd01", "dueperson", last=ago(days=20))],
                       players={"UIDdddd01": {"username": "dueperson", "confirmed": ago(days=2)}},
                       saves=["UIDdddd01", "UIDdddd01_dev"], delreq={"dueperson": {"ts": ago(days=8)}})
check("b) C3: players, saves, saves_dev, Auth, then the delreq doc last",
      rc == 0 and log == [("fs", "players", "UIDdddd01"), ("fs", "saves", "UIDdddd01"), ("fs", "saves", "UIDdddd01_dev"),
                          ("auth", "UIDdddd01"), ("fs", "delreq", "dueperson")], log)
rc, out, log = run_one([], players={"UIDstry01": {"username": "x"}}, saves=["UIDstry02", "UIDstry02_dev"])
check("b) E: the stray players and saves docs, nothing else", rc == 0 and log == [("fs", "players", "UIDstry01"),
                                                                                 ("fs", "saves", "UIDstry02"),
                                                                                 ("fs", "saves", "UIDstry02_dev")], log)
check("b) live header", out.startswith("LIVE — eliminazioni eseguite"), out[:60])

# ---------- c) C2 refresh rule (both modes use build_plan) — one account, one delreq
def cat_of(last, refresh, ts_days):
    users = C.read_users(FAuth([User("UIDrefre1", "refresher", last=last, refresh=refresh)], []))
    players = {"UIDrefre1": {"username": "refresher", "confirmed": ago(days=1)}}  # not an orphan, not unconfirmed
    plan = C.build_plan(users, set(), players, {"refresher": {"ts": ago(days=ts_days)}}, [], NOW)
    return [it["cat"] for it in plan["items"]] or (["pending"] if plan["pending"] else [])


check("c1) sign-in before ts, refresh after -> cancelled (C2)", cat_of(ago(days=5), ago(days=1), 3) == ["C2"])
check("c2) both before ts, age 3 d -> pending", cat_of(ago(days=5), ago(days=4), 3) == ["pending"])
check("c3) both before ts, age 8 d -> due (C3)", cat_of(ago(days=9), ago(days=9), 8) == ["C3"])
check("c4) no sign-in and no refresh (never) -> due by age", cat_of(None, None, 8) == ["C3"])
check("c5) sign-in after ts, refresh never -> cancelled", cat_of(ago(days=1), None, 3) == ["C2"])
check("c6) refresh after ts, sign-in never -> cancelled", cat_of(None, ago(days=1), 3) == ["C2"])

# ---------- d) idempotent
auth, db, log = world([User("UIDdddd02", "alphaa", last=ago(days=40))],
                      players={"UIDdddd02": {"username": "alphaa", "confirmed": ago(days=31)}}, saves=[])
rc, out, summ = go(auth, db, live=True)
check("d) missing saves docs are fine (rc 0, no failure)", rc == 0 and "fallito" not in out and "eliminato" in out, out)
auth, db, log = world([User("UIDdddd03", "alphaa", last=ago(days=40))],
                      players={"UIDdddd03": {"username": "alphaa", "confirmed": ago(days=31)}})
plan = plan_of(auth, db)
auth.users = []  # already gone from Auth between listing and deletion
st = C.execute(plan, auth, db)
check("d) Auth UserNotFound counts as done", st["fail"] == 0 and plan["items"][0]["status"] == "eliminato", st)
auth, db, log = world([User("UIDdupe001", "dupeuser", last=ago(days=100))],
                      players={"UIDdupe001": {"username": "dupeuser", "confirmed": ago(days=31)}},
                      delreq={"dupeuser": {"ts": ago(days=8)}})
plan = plan_of(auth, db)
check("d) account in A and C3 -> one item, C3's steps", len(plan["items"]) == 1 and plan["items"][0]["cat"] == "C3")
rc = go(auth, db, live=True)[0]
check("d) ...and processed once: one Auth delete, rc 0", rc == 0 and [e for e in log if e[0] == "auth"] == [("auth", "UIDdupe001")],
      log)

# ---------- e) exempt guard
auth, db, log = world([User("UIDaaaaa5", "alphaa", last=ago(days=40)), User("UIDbbbbb5", "betaaa1", last=ago(days=40))],
                      players={"UIDaaaaa5": {"username": "alphaa", "confirmed": ago(days=31)},
                               "UIDbbbbb5": {"username": "betaaa1", "confirmed": ago(days=31)}})
plan = plan_of(auth, db)
db.docs["devs"]["UIDaaaaa5"] = {"role": "dev1"}  # becomes a dev after the listing
st = C.execute(plan, auth, db)
check("e) devs doc appearing after listing -> skipped and counted", st["skip"] == 1 and st["acc"] == 1, st)
check("e) ...its docs and Auth user untouched, the other account deleted",
      not any(e[1] == "UIDaaaaa5" for e in log) and ("auth", "UIDbbbbb5") in auth.log, log)
auth, db, log = world([User("UIDaaaaa6", "alphaa", last=ago(days=40))],
                      players={"UIDaaaaa6": {"username": "alphaa", "confirmed": ago(days=31)}},
                      saves=["UIDaaaaa6"])
db.hook = lambda c, i: db.docs["devs"].update({"UIDaaaaa6": {}}) if (c, i) == ("players", "UIDaaaaa6") else None
rc, out, summ = go(auth, db, live=True)
check("e) devs doc appearing mid-item (after players) -> Auth not deleted, skipped",
      ("auth", "UIDaaaaa6") not in auth.log and "saltato (dev)" in out, (auth.log, out))

# ---------- f) cap, checked before any deletion
users, players = many_a(26)
auth, db, log = world(users, players=players)
rc, out, summ = go(auth, db, live=True)
check("f) 26 accounts -> rc 2, zero deletes, Italian message",
      rc == 2 and log == [] and auth.log == [] and "LIMITE SUPERATO: 26 account / 78 documenti — nessuna eliminazione" in out, (rc, out[:200]))
users, players = many_a(25)
auth, db, log = world(users, players=players)
rc, out, summ = go(auth, db, live=True)
check("f) 25 accounts -> proceeds", rc == 0 and len([e for e in log if e[0] == "auth"]) == 25 and not auth.users, (rc, len(auth.log)))
junk = {f"ghost{i:03d}": {"ts": ago(days=3)} for i in range(101)}
auth, db, log = world([], delreq=junk)
rc, out, summ = go(auth, db, live=True)
check("f) 101 documents -> rc 2, zero deletes", rc == 2 and log == [] and "101 documenti" in out, (rc, out[:160]))
junk = {f"ghost{i:03d}": {"ts": ago(days=3)} for i in range(100)}
auth, db, log = world([], delreq=junk)
rc, out, summ = go(auth, db, live=True)
check("f) 100 documents -> proceeds", rc == 0 and len(log) == 100 and not db.docs["delreq"], (rc, len(log)))

# ---------- g) one failing delete: its item stops, the others run, non-zero exit
auth, db, log = world([User("UIDfsfail", "failfs", last=ago(days=40)), User("UIDokay01", "okayyy1", last=ago(days=40)),
                       User("UIDauthf", "failau", last=ago(days=40))],
                      players={"UIDfsfail": {"username": "failfs", "confirmed": ago(days=31)},
                               "UIDokay01": {"username": "okayyy1", "confirmed": ago(days=31)},
                               "UIDauthf": {"username": "failau", "confirmed": ago(days=31)}},
                      saves=["UIDfsfail", "UIDokay01", "UIDauthf"],
                      fail_fs=[("players", "UIDfsfail")], fail_auth=["UIDauthf"])
rc, out, summ = go(auth, db, live=True)
check("g) failed Firestore step: its later steps not run", ("fs", "saves", "UIDfsfail") not in log and ("auth", "UIDfsfail") not in auth.log, log)
check("g) the other accounts still run", ("auth", "UIDokay01") in auth.log and ("fs", "players", "UIDokay01") in log)
check("g) failed Auth delete: that account counted as failed", "UIDauthf" in [e[1] for e in auth.log] and "fallito (RuntimeError)" in out)
check("g) non-zero exit, masked failure text only", rc == 1 and out.count("fallito (RuntimeError)") == 2 and "secret" not in out, (rc, out))

# ---------- h) public-log hygiene, both modes, stdout AND summary file
secret = ["UIDalpha11", "UIDexact30", "UIDjust301", "UIDdue0001", "UIDcancel1", "UIDdev3old", "UIDnoauth1", "UIDlostsave",
          "alphaone", "exactthirty", "justover30", "orphanuser", "canceller", "dueperson", "pendingone", "sevenexact",
          "overseven1", "somedevuser", "dev3", "ghostrequester", "noauthperson", "mangiasassi", "@"]
for mode, live in (("dry-run", False), ("live", True)):
    auth, db, log = base_world()
    rc, out, summ = go(auth, db, live=live)
    leaks = [s for s in secret if s in out or s in summ]
    check(f"h) {mode}: no uid, email or full username in stdout/summary", not leaks, leaks)
    check(f"h) {mode}: summary file mirrors stdout", out in summ)

# ---------- i) workflow file (text checks + the run line's own branch)
WF = open(os.path.join(HERE, "..", "..", ".github", "workflows", "players-cleanup.yml"), encoding="utf-8").read()
check("i) manual trigger: choice input mode, options dry-run/live, default dry-run",
      "workflow_dispatch:" in WF and "type: choice" in WF and "- dry-run" in WF and "- live" in WF and "default: dry-run" in WF)
check("i) schedule: daily 06:30 UTC", re.search(r'cron:\s*"30 6 \* \* \*"', WF) is not None)
check("i) contents read only, checks out dev, FIREBASE_SA", "contents: read" in WF and "contents: write" not in WF
      and "ref: dev" in WF and "FIREBASE_SA: ${{ secrets.FIREBASE_SA }}" in WF)
mode_line = re.search(r"MODE:\s*\$\{\{\s*(.*?)\s*\}\}", WF)
check("i) MODE = live on schedule, else the dispatch input",
      mode_line is not None and mode_line.group(1) == "github.event_name == 'schedule' && 'live' || inputs.mode", mode_line and mode_line.group(1))
run_line = re.search(r'if \[ "\$MODE" = "live" \]; then (.*?); else (.*?); fi', WF)
check("i) run line: --live only on the live branch", run_line is not None and run_line.group(1) == "python tools/players/cleanup.py --live"
      and run_line.group(2) == "python tools/players/cleanup.py", run_line and run_line.groups())


def resolve(event, mode_input):
    # emulates the GitHub expression above (schedule -> live, else the input) and the run line's own branch
    mode = "live" if event == "schedule" else mode_input
    return run_line.group(1) if mode == "live" else run_line.group(2)


check("i) dispatch, default dry-run -> no --live", resolve("workflow_dispatch", "dry-run") == "python tools/players/cleanup.py")
check("i) dispatch, live -> --live", resolve("workflow_dispatch", "live") == "python tools/players/cleanup.py --live")
check("i) schedule -> --live", resolve("schedule", None) == "python tools/players/cleanup.py --live")
src = open(os.path.join(HERE, "cleanup.py"), encoding="utf-8").read()
check("i) the CLI flag defaults to dry-run", "store_true" in src and "--live" in src and "run(a, d, live=args.live)" in src)

print(f"{sum(RES)}/{len(RES)}")
sys.exit(0 if all(RES) else 1)
