#!/usr/bin/env python3
"""Automatic pre-check for developer submissions. It only checks structure, so Claude can spend effort on content review.

Two ways to run it:
  * no arguments (the `validate` PR check): validates the packages changed in the PR (git diff against BASE_REF); maintainer PRs are skipped;
  * `python3 scripts/validate_submission.py <folder> [<folder> ...]`: validates those package folders directly
    (`submissions/<acct>/<YYYY-MM-DD>` or `<YYYY-MM-DD>-testi`; used by the text-edit export and by the tests).

Formats: schemaVersion 1 (legacy, no conflict check) and 2 (docs/submissions-v2.md)."""
import datetime, json, os, re, struct, subprocess, sys

BASE = os.environ.get("BASE_REF", "main")
ACTOR = os.environ.get("ACTOR", "")
OWNER = "ciprognola"

AUDIO_EXT = {".mp3", ".ogg", ".wav"}
SPRITE_EXT = {".png", ".webp"}
MAX_AUDIO = 300 * 1024
MAX_SPRITE = 200 * 1024
MAX_TOTAL = 2 * 1024 * 1024
MAX_TEXT = 500
MAX_NOTE = 300
CHARS_V1 = {"uomoRoccia", "algidone", "shared"}
CHARS_V2 = {"roccia", "algidone", "shared"}
TYPES_V1 = {"text", "audio", "sprite"}
TYPES_V2 = {"text", "colour", "scale", "audio", "sprite"}
SITES = {"dev", "stable"}
SCREEN_RE = re.compile(r"^[a-z0-9][a-z0-9:_-]*$")
VERSION_V2_RE = re.compile(r"^\d+\.\d+(\.\d+)?(_\d+)?$")
COLOUR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
FOLDER_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(-testi)?$")


def is_int(v, lo=None):
    return isinstance(v, int) and not isinstance(v, bool) and (lo is None or v >= lo)


def png_size(path):
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
            return struct.unpack(">II", head[16:24])
    except OSError:
        pass
    return None


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, m):
        self.errors.append(m)

    def warn(self, m):
        self.warnings.append(m)


def check_file_change(R, tag, c, base, t, v2, referenced):
    """Shared by v1 and v2: the 'file' of an audio/sprite change. Returns its size or None."""
    f = str(c.get("file", ""))
    if not f or ".." in f or f.startswith("/") or "\\" in f:
        R.err(f"{tag}: 'file' must be a simple relative path inside the folder.")
        return None
    fp = os.path.join(base, f)
    referenced.add(f)
    if not os.path.exists(fp):
        R.err(f"{tag}: file '{f}' not found in the submission folder.")
        return None
    ext = os.path.splitext(f)[1].lower()
    size = os.path.getsize(fp)
    flagged = f.startswith("flagged/")
    if t == "audio":
        if ext not in AUDIO_EXT:
            R.err(f"{tag}: audio must be one of {sorted(AUDIO_EXT)}.")
        if size > MAX_AUDIO:
            (R.warn if flagged else R.err)(f"{tag}: '{f}' is {size//1024} KB, audio limit is {MAX_AUDIO//1024} KB" + (" (flagged: Claude converts it)." if flagged else "."))
    else:
        if ext not in SPRITE_EXT:
            R.err(f"{tag}: sprite must be one of {sorted(SPRITE_EXT)}.")
        if size > MAX_SPRITE:
            R.err(f"{tag}: '{f}' is {size//1024} KB, sprite limit is {MAX_SPRITE//1024} KB.")
    return size


def check_v2_change(R, tag, c, base, referenced, seen_ids):
    t = c.get("type")
    if not isinstance(c.get("id"), str) or not c["id"].strip():
        R.err(f"{tag}: 'id' is required (a non-empty string).")
    elif c["id"] in seen_ids:
        R.err(f"{tag}: duplicate id '{c['id']}'.")
    else:
        seen_ids.add(c["id"])
    if t not in TYPES_V2:
        R.err(f"{tag}: 'type' must be one of {sorted(TYPES_V2)}.")
        return 0
    if c.get("character") not in CHARS_V2:
        R.err(f"{tag}: 'character' must be one of {sorted(CHARS_V2)}.")
    if not str(c.get("target", "")).strip():
        R.err(f"{tag}: 'target' is required.")
    if c.get("character") == "shared":
        R.warn(f"{tag}: character 'shared' - explain in 'note' why it applies to both characters.")
    sc = c.get("screen")
    if sc is not None and (not isinstance(sc, str) or not SCREEN_RE.match(sc)):
        R.err(f"{tag}: 'screen' must be a screen id from refs/screens/SCREENS.md (lowercase, e.g. menu-home-roccia).")
    loc = c.get("locator")
    if loc is not None:
        if t not in ("text", "colour", "scale"):
            R.err(f"{tag}: 'locator' only applies to text/colour/scale changes.")
        elif not isinstance(loc, dict) or not isinstance(loc.get("text"), str) or ("pos" in loc and not isinstance(loc["pos"], str)):
            R.err(f"{tag}: 'locator' must be {{text: <current text>, pos: <hint>}}.")
    note = c.get("note")
    if note is not None and (not isinstance(note, str) or len(note) > MAX_NOTE):
        R.err(f"{tag}: 'note' must be a string of at most {MAX_NOTE} characters.")
    if t in ("audio", "sprite") and not str(note or "").strip():
        R.err(f"{tag}: 'note' is required for file changes (say why you made this change).")
    if "before" not in c:
        R.err(f"{tag}: 'before' is required (the value at baseVersion; null when it did not exist).")
    bf = c.get("before")
    if t in ("text", "colour", "scale"):
        if bf is not None and not isinstance(bf, str):
            R.err(f"{tag}: 'before' must be the previous value as a string (or null).")
        elif isinstance(bf, str) and len(bf) > MAX_TEXT:
            R.err(f"{tag}: 'before' longer than {MAX_TEXT} characters.")
        v = c.get("value")
        if not isinstance(v, str) or not v.strip():
            R.err(f"{tag}: {t} changes need a non-empty string 'value'.")
        elif len(v) > MAX_TEXT:
            R.err(f"{tag}: value longer than {MAX_TEXT} characters.")
        elif t == "colour" and not COLOUR_RE.match(v):
            R.err(f"{tag}: colour must look like #rrggbb.")
        elif t == "scale":
            try:
                if not 0.5 <= float(v) <= 2.0:
                    R.err(f"{tag}: scale must be between 0.5 and 2.")
            except ValueError:
                R.err(f"{tag}: scale must be a number written as text (e.g. \"1.2\").")
        if "file" in c:
            R.warn(f"{tag}: 'file' is ignored for {t} changes.")
        return 0
    # audio / sprite
    if bf is not None:
        if not isinstance(bf, dict) or not SHA_RE.match(str(bf.get("sha256", ""))) or not is_int(bf.get("bytes"), 0):
            R.err(f"{tag}: 'before' for files must be {{sha256 (64 hex), bytes, w?, h?, durationMs?}} (or null).")
        else:
            for k in ("w", "h", "durationMs"):
                if k in bf and not is_int(bf[k], 0):
                    R.err(f"{tag}: before.{k} must be a non-negative integer.")
    size = check_file_change(R, tag, c, base, t, True, referenced)
    m = c.get("meta")
    if not isinstance(m, dict):
        R.err(f"{tag}: 'meta' is required for {t} changes.")
        return size or 0
    if t == "sprite":
        if not str(m.get("frameKey", "")).strip() or not str(m.get("anchor", "")).strip():
            R.err(f"{tag}: sprite meta needs frameKey and anchor.")
        for k in ("w", "h", "base_w", "base_h"):
            if not is_int(m.get(k), 1):
                R.err(f"{tag}: sprite meta.{k} must be a positive integer.")
        for k in ("ox", "oy"):
            if not is_int(m.get(k)):
                R.err(f"{tag}: sprite meta.{k} must be an integer.")
        if size is not None and str(c.get("file", "")).lower().endswith(".png"):
            ps = png_size(os.path.join(base, c["file"]))
            if ps and is_int(m.get("w")) and is_int(m.get("h")) and (m["w"], m["h"]) != ps:
                R.err(f"{tag}: meta says {m['w']}x{m['h']} but the PNG is {ps[0]}x{ps[1]}.")
    else:
        if not is_int(m.get("bytes"), 1) or not str(m.get("mime", "")).startswith("audio/") or not is_int(m.get("durationMs"), 0):
            R.err(f"{tag}: audio meta needs bytes, mime (audio/...) and durationMs.")
        elif size is not None and m["bytes"] != size:
            R.err(f"{tag}: meta.bytes is {m['bytes']} but the file is {size} bytes.")
    return size or 0


def check_manifest(R, base, acct, folder_date):
    mpath = f"{base}/manifest.json"
    if not os.path.exists(mpath):
        R.err(f"{base}: manifest.json is missing.")
        return
    try:
        man = json.load(open(mpath, encoding="utf-8"))
    except Exception as e:
        R.err(f"{mpath}: not valid JSON ({e}).")
        return
    if not isinstance(man, dict):
        R.err(f"{mpath}: the manifest must be a JSON object.")
        return
    sv = man.get("schemaVersion")
    if sv not in (1, 2):
        R.err(f"{mpath}: schemaVersion must be 1 or 2.")
        return
    v2 = sv == 2
    if str(man.get("developer", "")).lower() != acct.lower():
        R.err(f"{mpath}: 'developer' must match the folder name '{acct}'.")
    current = open("VERSION").read().strip() if os.path.exists("VERSION") else ""
    bv = str(man.get("baseVersion", ""))
    if v2:
        if not VERSION_V2_RE.match(bv):
            R.err(f"{mpath}: 'baseVersion' must look like 0.4_6 (the VERSION of the build the edit started from).")
        elif current and bv != current:
            R.warn(f"{mpath}: built on {bv} but the live build is {current}. Claude will run the conflict check.")
        if man.get("site") not in SITES:
            R.err(f"{mpath}: 'site' must be one of {sorted(SITES)}.")
        ea = man.get("exportedAt")
        try:
            datetime.datetime.fromisoformat(str(ea).replace("Z", "+00:00"))
        except ValueError:
            R.err(f"{mpath}: 'exportedAt' must be an ISO 8601 date-time.")
        n = man.get("note")
        if not isinstance(n, str) or not n.strip() or len(n) > 1000:
            R.err(f"{mpath}: a general 'note' (1-1000 characters) is required.")
    else:
        if man.get("date") != folder_date:
            R.err(f"{mpath}: 'date' must match the folder date '{folder_date}'.")
        if not re.match(r"^V\d+\.\d+_\d+$", bv):
            R.err(f"{mpath}: 'baseVersion' must look like V0.2_5.")
        elif current and bv != current:
            R.warn(f"{mpath}: built on {bv} but the live build is {current}. Claude will check for conflicts.")
    changes = man.get("changes")
    if not isinstance(changes, list) or not changes:
        R.err(f"{mpath}: 'changes' must be a non-empty list.")
        return
    total = 0
    referenced = {"manifest.json"}
    seen = set()
    for i, c in enumerate(changes, 1):
        tag = f"{mpath} change #{i}"
        if not isinstance(c, dict):
            R.err(f"{tag}: must be an object.")
            continue
        if v2:
            total += check_v2_change(R, tag, c, base, referenced, seen)
            continue
        t = c.get("type")
        if t not in TYPES_V1:
            R.err(f"{tag}: 'type' must be one of {sorted(TYPES_V1)}.")
            continue
        if c.get("character") not in CHARS_V1:
            R.err(f"{tag}: 'character' must be one of {sorted(CHARS_V1)}.")
        if not str(c.get("target", "")).strip():
            R.err(f"{tag}: 'target' is required.")
        if not str(c.get("note", "")).strip():
            R.err(f"{tag}: 'note' is required (say why you made this change).")
        if c.get("character") == "shared":
            R.warn(f"{tag}: character 'shared' - explain in 'note' why it applies to both characters.")
        if t == "text":
            v = c.get("value")
            if not isinstance(v, str) or not v.strip():
                R.err(f"{tag}: text changes need a non-empty 'value'.")
            elif len(v) > MAX_TEXT:
                R.err(f"{tag}: text longer than {MAX_TEXT} characters.")
        else:
            total += check_file_change(R, tag, c, base, t, False, referenced) or 0
    if total > MAX_TOTAL:
        R.err(f"{base}: total asset size {total//1024} KB exceeds {MAX_TOTAL//1024} KB.")
    for root, _, fs in os.walk(base):
        for fn in fs:
            rel = os.path.relpath(os.path.join(root, fn), base).replace("\\", "/")
            if rel not in referenced:
                R.warn(f"{base}/{rel}: file is not referenced by manifest.json.")


def split_folder(path):
    """<...>/<acct>/<folder> -> (acct, date-part-of-folder) or None."""
    path = path.rstrip("/\\")
    acct, folder = os.path.basename(os.path.dirname(path)), os.path.basename(path)
    m = FOLDER_RE.match(folder)
    return (acct, m.group(1)) if m else None


def validate_folders(folders):
    R = Report()
    for f in folders:
        sp = split_folder(f)
        if not sp:
            R.err(f"{f}: the folder must be <acct>/<YYYY-MM-DD> or <acct>/<YYYY-MM-DD>-testi.")
            continue
        check_manifest(R, f.rstrip("/\\"), sp[0], sp[1])
    return R


def finish(R, ok_msg):
    for w in R.warnings:
        print(f"::warning::{w}")
    for e in R.errors:
        print(f"::error::{e}")
    if R.errors:
        print(f"\n{len(R.errors)} problem(s) found. Fix them and upload the corrected files to the same branch.")
        return 1
    print(ok_msg)
    return 0


def main():
    if len(sys.argv) > 1:
        return finish(validate_folders(sys.argv[1:]), "Submission structure OK.")
    if ACTOR.lower() == OWNER:
        print("Maintainer PR: structure check skipped.")
        return 0
    R = Report()
    changed = subprocess.check_output(["git", "diff", "--name-only", f"origin/{BASE}...HEAD"], text=True).split("\n")
    changed = [c for c in changed if c]
    if not changed:
        R.err("No changed files found.")
    pat = re.compile(r"^submissions/([^/_][^/]*)/(\d{4}-\d{2}-\d{2}(?:-testi)?)/(.+)$")
    dirs = {}
    for path in changed:
        m = pat.match(path)
        if not m:
            R.err(f"'{path}' is outside submissions/<your-name>/<YYYY-MM-DD>/. "
                  "Developers may only add files there (never index.html, builds/, VERSION or other folders).")
            continue
        dirs.setdefault((m.group(1), m.group(2)), []).append(m.group(3))
    for (acct, folder) in dirs:
        check_manifest(R, f"submissions/{acct}/{folder}", acct, FOLDER_RE.match(folder).group(1))
    return finish(R, "Submission structure OK. Waiting for maintainer + Claude review.")


if __name__ == "__main__":
    sys.exit(main())
