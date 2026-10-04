#!/usr/bin/env python3
"""Mocked test of cleanup.py (no Firebase, no key, fixed clock). Run: python tools/players/test_cleanup.py"""
import contextlib, datetime, io, os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cleanup as C

RES = []


def check(n, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + n, extra if not ok else "")


UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
D = datetime.timedelta


def ms(t):
    return None if t is None else int(t.timestamp() * 1000)


class Meta:
    def __init__(self, created, last): self.creation_timestamp, self.last_sign_in_timestamp = ms(created), ms(last)


class User:
    def __init__(self, uid, name, created=NOW - D(days=100), last=None, dom="@mangiasassi.invalid"):
        self.uid, self.email, self.user_metadata = uid, name + dom, Meta(created, last)


class Page:
    def __init__(self, users, nxt=None): self.users, self.nxt = users, nxt
    def get_next_page(self): return self.nxt


class Auth:
    def __init__(self, users, split=2):
        pages = None
        chunks = [users[i:i + split] for i in range(0, len(users), split)] or [[]]
        for ch in reversed(chunks):
            pages = Page(ch, pages)
        self.first = pages
    def list_users(self): return self.first


class Boom(AssertionError):
    pass


class Doc:
    def __init__(self, id_, data=None): self.id, self.data = id_, data or {}
    def to_dict(self): return dict(self.data)
    def delete(self, *a, **k): raise Boom("delete called")
    def update(self, *a, **k): raise Boom("update called")
    def set(self, *a, **k): raise Boom("set called")


class Col:
    def __init__(self, docs): self.docs = docs
    def stream(self): return iter(self.docs)
    def list_documents(self): return iter(self.docs)
    def document(self, id_): raise Boom("document() write path used")
    def add(self, *a, **k): raise Boom("add called")


class DB:
    def __init__(self, **cols): self.cols = cols
    def collection(self, n): return Col(self.cols.get(n, []))


conf = lambda days, secs=0: NOW - D(days=days, seconds=secs)
users = [
    User("UIDalpha11", "alphaone", last=NOW - D(days=40)),            # A (31 days)
    User("UIDexact30", "exactthirty"),                                # confirmed exactly 30 d -> not A
    User("UIDjust301", "justover30"),                                 # 30 d + 1 s -> A
    User("UIDfresh01", "freshplayer"),                                # fine
    User("UIDorphan1", "orphanuser", created=NOW - D(hours=25)),      # B
    User("UIDorph24h", "orphan24h", created=NOW - D(hours=24)),       # exactly 24 h -> not B
    User("UIDorph23h", "orphan23h", created=NOW - D(hours=23)),       # not B
    User("UIDcancel1", "canceller", last=NOW - D(days=1)),            # C cancelled
    User("UIDdue0001", "dueperson", last=NOW - D(days=20)),           # C due
    User("UIDpend001", "pendingone", last=NOW - D(days=5)),           # C pending
    User("UIDseven01", "sevenexact", last=NOW - D(days=30)),          # exactly 7 d -> pending
    User("UIDseven02", "overseven1", last=NOW - D(days=30)),          # 7 d + 1 s -> due
    User("UIDdevdoc1", "somedevuser"),                                # devs doc, old, unconfirmed, delreq
    User("UIDdev3old", "dev3"),                                       # name exempt, old, unconfirmed, delreq
    User("UIDmasterx", "master", created=NOW - D(days=200)),          # exempt orphan-looking
]
devs = [Doc("UIDdevdoc1", {"role": "dev1"})]
players = [
    Doc("UIDalpha11", {"username": "alphaone", "confirmed": conf(31)}),
    Doc("UIDexact30", {"username": "exactthirty", "confirmed": conf(30)}),
    Doc("UIDjust301", {"username": "justover30", "confirmed": conf(30, 1)}),
    Doc("UIDfresh01", {"username": "freshplayer", "confirmed": conf(2)}),
    Doc("UIDcancel1", {"username": "canceller", "confirmed": conf(2)}),
    Doc("UIDdue0001", {"username": "dueperson", "confirmed": conf(2)}),
    Doc("UIDpend001", {"username": "pendingone", "confirmed": conf(2)}),
    Doc("UIDseven01", {"username": "sevenexact", "confirmed": conf(2)}),
    Doc("UIDseven02", {"username": "overseven1", "confirmed": conf(2)}),
    Doc("UIDdevdoc1", {"username": "somedevuser", "confirmed": conf(90)}),
    Doc("UIDdev3old", {"username": "dev3", "confirmed": conf(90)}),
    Doc("UIDnoauth1", {"username": "noauthperson", "confirmed": conf(1)}),   # D
]
delreq = [
    Doc("ghostrequester", {"ts": NOW - D(days=3)}),                    # C junk
    Doc("canceller", {"ts": NOW - D(days=3)}),
    Doc("dueperson", {"ts": NOW - D(days=8)}),
    Doc("pendingone", {"ts": NOW - D(days=2)}),
    Doc("sevenexact", {"ts": NOW - D(days=7)}),
    Doc("overseven1", {"ts": NOW - D(days=7, seconds=1)}),
    Doc("somedevuser", {"ts": NOW - D(days=20)}),
    Doc("dev3", {"ts": NOW - D(days=20)}),
]
saves = [Doc("UIDalpha11"), Doc("UIDalpha11_dev"), Doc("UIDnoauth1"), Doc("UIDnoauth1_dev"), Doc("UIDlostsave")]   # D: 3
# the "just over 7 d" request's own user must have signed in BEFORE the request, else it counts as cancelled
for u in users:
    if u.uid == "UIDseven02":
        u.user_metadata = Meta(NOW - D(days=100), NOW - D(days=30))

db = DB(devs=devs, players=players, delreq=delreq, saves=saves)
auth = Auth(users)
read = C.read_all(auth, db)
r = C.analyse(*read, NOW)
has = lambda lst, n: any(x.startswith(n[:2] + "… (" + str(len(n)) + ")") for x in lst)

# a) one case per category
check("a) pagination read every user", read[0] and len(read[0]) == len(users), len(read[0]))
check("a) A: unconfirmed lands in A", has(r["A"], "alphaone") and "31 g" in r["A"][0])
check("a) B: orphan lands in B", has(r["B"], "orphanuser"))
check("a) C-junk", has(r["C_junk"], "ghostrequester") and len(r["C_junk"]) == 1)
check("a) C-cancelled", has(r["C_cancelled"], "canceller") and len(r["C_cancelled"]) == 1)
check("a) C-due", has(r["C_due"], "dueperson"))
check("a) C-pending", has(r["C_pending"], "pendingone"))
check("a) D counts", r["D_players"] == 1 and r["D_saves"] == 3, (r["D_players"], r["D_saves"]))
check("a) totals", r["totals"] == {"auth": 15, "exempt": 3, "players": 12, "delreq": 8}, r["totals"])
# b) exempt
allout = [x for k in ("A", "B", "C_junk", "C_cancelled", "C_due", "C_pending") for x in r[k]]
check("b) exempt accounts in no list", not any(x.startswith(("so…", "de…", "ma…")) for x in allout), allout)
check("b) exempt delreq ignored, not junk", r["exempt_delreq"] == 2)
# c) boundaries (strict "older than")
check("c) confirmed exactly 30 d: not A; +1 s: A", not has(r["A"], "exactthirty") and has(r["A"], "justover30"))
check("c) orphan exactly 24 h / 23 h: not B", not has(r["B"], "orphan24h") and not has(r["B"], "orphan23h"))
check("c) delreq exactly 7 d: pending; +1 s: due", has(r["C_pending"], "sevenexact") and has(r["C_due"], "overseven1") and not has(r["C_due"], "sevenexact"))

# d) no write call of any kind; full run completes
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleanup.py"), encoding="utf-8").read()
check("d) source has no write/delete call", not re.search(r"\.(delete|update|set|add|batch|commit|delete_user|delete_users|create_user|update_user)\(|\.document\(", src))
tmp = tempfile.mkdtemp()
summ = os.path.join(tmp, "summary.md")
os.environ["GITHUB_STEP_SUMMARY"] = summ
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        rc = C.run(Auth(users), db, NOW)
    err = None
except Exception as e:
    rc, err = None, e
out = buf.getvalue()
check("d) full run completes on mocks that raise on any write", rc == 0 and err is None, err)

# e) public-log hygiene
secret = [u.uid for u in users] + [u.email for u in users] + [d.id for d in delreq] + ["noauthperson", "UIDnoauth1", "UIDlostsave"]
secret += [n for n in ("alphaone", "exactthirty", "justover30", "orphanuser", "canceller", "dueperson", "pendingone", "somedevuser", "noauthperson", "ghostrequester", "mangiasassi", "invalid")]
text_summ = open(summ, encoding="utf-8").read()
leaks = [s for s in set(secret) if s in out or s in text_summ]
check("e) stdout + summary contain no uid / email / full username", not leaks, leaks)
check("e) header and masked lines present", out.startswith("DRY-RUN — nothing deleted") and "al… (8) · 31 g" in out and "gh… (14) · 3 g" in out and "2026-10-04 12:00 UTC" in out)
check("e) summary file mirrors stdout", out in text_summ)

# f) permission / other errors
class PermissionDeniedError(Exception):
    pass


class BadAuth:
    def __init__(self, exc): self.exc = exc
    def list_users(self): raise self.exc


for label, exc, expect_rc in (("PermissionDenied", PermissionDeniedError("403 secret@mangiasassi.invalid UIDx"), 1),):
    b = io.StringIO()
    with contextlib.redirect_stdout(b):
        rc = C.run(BadAuth(exc), db, NOW)
    o = b.getvalue()
    check("f) auth permission error -> Italian message, exit 1, nothing else", rc == 1 and o == C.MSG_AUTH_DENIED + "\n", o)
b = io.StringIO()
with contextlib.redirect_stdout(b):
    rc = C.run(BadAuth(RuntimeError("boom with secret@mangiasassi.invalid")), db, NOW)
check("f) other error -> short message (class name only), exit 1", rc == 1 and "RuntimeError" in b.getvalue() and "secret" not in b.getvalue(), b.getvalue())


class FsBad(DB):
    def collection(self, n): raise PermissionDeniedError("403")


b = io.StringIO()
with contextlib.redirect_stdout(b):
    rc = C.run(auth, FsBad(), NOW)
check("f) firestore permission error -> exit 1, its own message", rc == 1 and b.getvalue() == C.MSG_FS_DENIED + "\n", b.getvalue())

print(f"{sum(RES)}/{len(RES)}")
sys.exit(0 if all(RES) else 1)
