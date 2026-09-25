#!/usr/bin/env python3
"""Tests for scripts/validate_submission.py (schemaVersion 1 and 2). Run: python scripts/test_validate_submission.py
Static fixtures live in submissions/_fixtures/ (valid-* must pass, broken-* must fail); the other broken cases are built in a temp dir."""
import copy, json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VAL = os.path.join(ROOT, "scripts", "validate_submission.py")
FIX = os.path.join(ROOT, "submissions", "_fixtures")
RES = []


def run(folder):
    p = subprocess.run([sys.executable, VAL, folder], capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout + p.stderr


def check(name, ok, extra=""):
    RES.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name, extra)


def leaf(case):  # submissions/_fixtures/<case>/<acct>/<date>
    d = os.path.join(FIX, case)
    a = os.listdir(d)[0]
    return os.path.join(d, a, os.listdir(os.path.join(d, a))[0])


for case in sorted(os.listdir(FIX)):
    if case.startswith("valid-"):
        rc, out = run(leaf(case)); check(f"fixture {case} passes", rc == 0, out.strip()[-120:] if rc else "")
EXPECT = {"broken-dev-mismatch": "must match the folder name", "broken-sprite-size": "PNG is 1x1", "broken-no-before": "'before' is required", "broken-colour": "#rrggbb"}
for case, want in EXPECT.items():
    rc, out = run(leaf(case)); check(f"fixture {case} fails with '{want}'", rc == 1 and want in out, out.strip()[-160:])

# programmatic mutations of the valid v2 package
src = leaf("valid-v2")
base = json.load(open(os.path.join(src, "manifest.json"), encoding="utf-8"))
MUT = [
    ("bad schemaVersion", lambda m: m.update(schemaVersion=3), "schemaVersion must be 1 or 2"),
    ("missing site", lambda m: m.pop("site"), "'site' must be"),
    ("bad baseVersion", lambda m: m.update(baseVersion="V0.4"), "'baseVersion' must look like"),
    ("bad exportedAt", lambda m: m.update(exportedAt="ieri"), "'exportedAt'"),
    ("missing general note", lambda m: m.pop("note"), "general 'note'"),
    ("empty changes", lambda m: m.update(changes=[]), "non-empty list"),
    ("v1 character in v2", lambda m: m["changes"][0].update(character="uomoRoccia"), "'character' must be"),
    ("unknown type", lambda m: m["changes"][0].update(type="skin"), "'type' must be"),
    ("duplicate id", lambda m: m["changes"][1].update(id="c1"), "duplicate id"),
    ("text too long", lambda m: m["changes"][0].update(value="x" * 501), "longer than 500"),
    ("note too long", lambda m: m["changes"][0].update(note="x" * 301), "at most 300"),
    ("bad screen id", lambda m: m["changes"][0].update(screen="Menu Home"), "screen id"),
    ("bad locator", lambda m: m["changes"][2].update(locator="qui"), "'locator'"),
    ("scale out of range", lambda m: m["changes"][2].update(value="5"), "between 0.5 and 2"),
    ("scale not a number", lambda m: m["changes"][2].update(value="grande"), "written as text"),
    ("before wrong type", lambda m: m["changes"][0].update(before=5), "'before' must be"),
    ("file before without sha", lambda m: m["changes"][3].update(before={"bytes": 3}), "'before' for files"),
    ("sprite meta missing", lambda m: m["changes"][3].pop("meta"), "'meta' is required"),
    ("sprite meta bad", lambda m: m["changes"][3]["meta"].update(base_w=0), "meta.base_w"),
    ("file change without note", lambda m: m["changes"][3].pop("note"), "'note' is required for file changes"),
    ("audio meta wrong bytes", lambda m: m["changes"][4]["meta"].update(bytes=999), "meta.bytes is 999"),
    ("audio meta bad mime", lambda m: m["changes"][4]["meta"].update(mime="video/mp4"), "audio meta needs"),
    ("file path escapes", lambda m: m["changes"][3].update(file="../x.png"), "simple relative path"),
    ("file missing", lambda m: m["changes"][3].update(file="nope.png"), "not found"),
]
for name, fn, want in MUT:
    with tempfile.TemporaryDirectory() as d:
        dst = os.path.join(d, "dev3", "2026-09-26"); shutil.copytree(src, dst)
        m = copy.deepcopy(base); fn(m)
        json.dump(m, open(os.path.join(dst, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False)
        rc, out = run(dst)
        check(f"broken v2: {name}", rc == 1 and want in out, out.strip()[-160:] if want not in out else "")
with tempfile.TemporaryDirectory() as d:  # F5: a text proposal has a locator and no target
    dst = os.path.join(d, "dev3", "2026-09-26-testi"); os.makedirs(dst)
    m = {"schemaVersion": 2, "developer": "dev3", "baseVersion": "0.4_7", "site": "dev", "exportedAt": "2026-09-26T08:00:00Z", "note": "proposte",
         "changes": [{"id": "p1", "type": "text", "character": "shared", "screen": "menu-home-roccia", "locator": {"text": "Lista desideri", "pos": "menu-home-roccia .tile[2]"}, "before": "Lista desideri", "value": "Desideri"}]}
    json.dump(m, open(os.path.join(dst, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False)
    rc, out = run(dst); check("v2: text proposal with a locator and no target is valid", rc == 0, out.strip()[-160:])
    del m["changes"][0]["locator"]; json.dump(m, open(os.path.join(dst, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False)
    rc, out = run(dst); check("broken v2: no target and no locator", rc == 1 and "'target' is required" in out)
# oversize sprite / audio, flagged audio only warns, wrong folder name
with tempfile.TemporaryDirectory() as d:
    dst = os.path.join(d, "dev3", "2026-09-26"); shutil.copytree(src, dst)
    open(os.path.join(dst, "rock.png"), "ab").write(b"\0" * (201 * 1024)); rc, out = run(dst)
    check("broken v2: sprite over 200 KB", rc == 1 and "sprite limit" in out)
    dst2 = os.path.join(d, "dev3", "2026-09-27"); shutil.copytree(src, dst2)
    m = copy.deepcopy(base); m["changes"][4].update(file="flagged/eat.mp3"); m["changes"][4]["meta"]["bytes"] = 301 * 1024
    os.makedirs(os.path.join(dst2, "flagged")); open(os.path.join(dst2, "flagged", "eat.mp3"), "wb").write(b"\0" * (301 * 1024))
    json.dump(m, open(os.path.join(dst2, "manifest.json"), "w", encoding="utf-8"))
    rc, out = run(dst2); check("v2: audio over 300 KB under flagged/ only warns", rc == 0 and "flagged" in out, out.strip()[-160:])
    dst3 = os.path.join(d, "dev3", "manuale"); shutil.copytree(src, dst3); rc, out = run(dst3)
    check("broken: folder name must be a date", rc == 1 and "<YYYY-MM-DD>" in out)
    dst4 = os.path.join(d, "master", "2026-09-26"); shutil.copytree(src, dst4); rc, out = run(dst4)
    check("broken: developer vs folder account (acct master, developer dev3)", rc == 1 and "must match the folder name 'master'" in out)
print(sum(RES), "/", len(RES), "passed"); sys.exit(0 if all(RES) else 1)
