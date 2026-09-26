#!/usr/bin/env python3
"""Base64 guard (F4b1 item 0): writes a copy of index.html to /tmp with every run of 200+
base64 characters replaced by "<B64 n>" (n = original run length in characters).
Prints ONLY the output path and its size -- never any file content.

Usage: python3 tools/strip_index.py [path/to/index.html]
Always run this first, every session, before searching index.html with any tool
(grep/cat/sed/head/regex scripts): search only the output file it prints, never the
real index.html directly. See CLAUDE.md §6 practical notes.
"""
import os
import re
import sys
import tempfile

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
OUT = os.path.join(tempfile.gettempdir(), "index_stripped.html")

B64_RUN = re.compile(r"[A-Za-z0-9+/=]{200,}")


def strip(match):
    n = len(match.group(0))
    return "<B64 " + str(n) + ">"


with open(SRC, encoding="utf-8", newline="") as f:
    data = f.read()

stripped = B64_RUN.sub(strip, data)

with open(OUT, "w", encoding="utf-8", newline="") as f:
    f.write(stripped)

print(OUT, os.path.getsize(OUT), "bytes")
