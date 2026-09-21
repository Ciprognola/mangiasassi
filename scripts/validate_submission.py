#!/usr/bin/env python3
"""Automatic pre-check for developer submissions (runs on every pull request).
It only checks structure, so Claude can spend effort on content review."""
import json, os, re, subprocess, sys

BASE = os.environ.get("BASE_REF", "main")
ACTOR = os.environ.get("ACTOR", "")
OWNER = "ciprognola"

AUDIO_EXT = {".mp3", ".ogg", ".wav"}
SPRITE_EXT = {".png", ".webp"}
MAX_AUDIO = 300 * 1024
MAX_SPRITE = 200 * 1024
MAX_TOTAL = 2 * 1024 * 1024
MAX_TEXT = 500
CHARACTERS = {"uomoRoccia", "algidone", "shared"}
TYPES = {"text", "audio", "sprite"}

errors, warnings = [], []
err = errors.append
warn = warnings.append

if ACTOR.lower() == OWNER:
    print("Maintainer PR: structure check skipped.")
    sys.exit(0)

changed = subprocess.check_output(
    ["git", "diff", "--name-only", f"origin/{BASE}...HEAD"], text=True).split("\n")
changed = [c for c in changed if c]
if not changed:
    err("No changed files found.")

pat = re.compile(r"^submissions/([^/_][^/]*)/(\d{4}-\d{2}-\d{2})/(.+)$")
dirs = {}
for path in changed:
    m = pat.match(path)
    if not m:
        err(f"'{path}' is outside submissions/<your-name>/<YYYY-MM-DD>/. "
            "Developers may only add files there (never index.html, builds/, VERSION or other folders).")
        continue
    dirs.setdefault((m.group(1), m.group(2)), []).append(m.group(3))

current = ""
if os.path.exists("VERSION"):
    current = open("VERSION").read().strip()

for (dev, date), files in dirs.items():
    base = f"submissions/{dev}/{date}"
    mpath = f"{base}/manifest.json"
    if not os.path.exists(mpath):
        err(f"{base}: manifest.json is missing.")
        continue
    try:
        man = json.load(open(mpath, encoding="utf-8"))
    except Exception as e:
        err(f"{mpath}: not valid JSON ({e}).")
        continue

    if man.get("schemaVersion") != 1:
        err(f"{mpath}: schemaVersion must be 1.")
    if str(man.get("developer", "")).lower() != dev.lower():
        err(f"{mpath}: 'developer' must match the folder name '{dev}'.")
    if man.get("date") != date:
        err(f"{mpath}: 'date' must match the folder date '{date}'.")
    bv = str(man.get("baseVersion", ""))
    if not re.match(r"^V\d+\.\d+_\d+$", bv):
        err(f"{mpath}: 'baseVersion' must look like V0.2_5.")
    elif current and bv != current:
        warn(f"{mpath}: built on {bv} but the live build is {current}. Claude will check for conflicts.")

    changes = man.get("changes")
    if not isinstance(changes, list) or not changes:
        err(f"{mpath}: 'changes' must be a non-empty list.")
        continue

    total = 0
    referenced = {"manifest.json"}
    for i, c in enumerate(changes, 1):
        tag = f"{mpath} change #{i}"
        t = c.get("type")
        if t not in TYPES:
            err(f"{tag}: 'type' must be one of {sorted(TYPES)}.")
            continue
        if c.get("character") not in CHARACTERS:
            err(f"{tag}: 'character' must be one of {sorted(CHARACTERS)}.")
        if not str(c.get("target", "")).strip():
            err(f"{tag}: 'target' is required.")
        if not str(c.get("note", "")).strip():
            err(f"{tag}: 'note' is required (say why you made this change).")
        if c.get("character") == "shared":
            warn(f"{tag}: character 'shared' - explain in 'note' why it applies to both characters.")
        if t == "text":
            v = c.get("value")
            if not isinstance(v, str) or not v.strip():
                err(f"{tag}: text changes need a non-empty 'value'.")
            elif len(v) > MAX_TEXT:
                err(f"{tag}: text longer than {MAX_TEXT} characters.")
        else:
            f = str(c.get("file", ""))
            if not f or ".." in f or f.startswith("/") or "\\" in f:
                err(f"{tag}: 'file' must be a simple relative path inside the folder.")
                continue
            fp = os.path.join(base, f)
            referenced.add(f)
            if not os.path.exists(fp):
                err(f"{tag}: file '{f}' not found in the submission folder.")
                continue
            ext = os.path.splitext(f)[1].lower()
            size = os.path.getsize(fp)
            total += size
            if t == "audio":
                if ext not in AUDIO_EXT:
                    err(f"{tag}: audio must be one of {sorted(AUDIO_EXT)}.")
                if size > MAX_AUDIO:
                    err(f"{tag}: '{f}' is {size//1024} KB, audio limit is {MAX_AUDIO//1024} KB.")
            else:
                if ext not in SPRITE_EXT:
                    err(f"{tag}: sprite must be one of {sorted(SPRITE_EXT)}.")
                if size > MAX_SPRITE:
                    err(f"{tag}: '{f}' is {size//1024} KB, sprite limit is {MAX_SPRITE//1024} KB.")
    if total > MAX_TOTAL:
        err(f"{base}: total asset size {total//1024} KB exceeds {MAX_TOTAL//1024} KB.")
    for f in files:
        if f not in referenced:
            warn(f"{base}/{f}: file is not referenced by manifest.json.")

for w in warnings:
    print(f"::warning::{w}")
for e in errors:
    print(f"::error::{e}")
if errors:
    print(f"\n{len(errors)} problem(s) found. Fix them and upload the corrected files to the same branch.")
    sys.exit(1)
print("Submission structure OK. Waiting for maintainer + Claude review.")
