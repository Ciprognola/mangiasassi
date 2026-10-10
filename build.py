#!/usr/bin/env python3
"""Build the playable demo from src/demo.html + assets/.

Outputs:
  index.html            full standalone page (open it in any browser, or serve it with GitHub Pages)
  dist/artifact.html    same page without the <html>/<head>/<body> wrapper (for a claude.ai artifact)

Assets come straight from Mangiasassi's index.html (PRSPR.idle, PRSPR.blink, PR_INTRO_B64) and are
embedded as base64, so the result is one self-contained file like the main game.
"""
import base64, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(ROOT, "assets")


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def frames(prefix):
    out, i = [], 0
    while os.path.exists(os.path.join(A, f"{prefix}{i}.png")):
        out.append(b64(os.path.join(A, f"{prefix}{i}.png")))
        i += 1
    return out


def main():
    src = open(os.path.join(ROOT, "src", "demo.html"), encoding="utf-8").read()
    sprites = {"idle": frames("prof_idle"), "blink": frames("prof_blink")}
    assert len(sprites["idle"]) == 7 and len(sprites["blink"]) == 3, "missing sprite frames"
    assert src.count("/*SPRITES*/null") == 1 and src.count('"__INTRO__"') == 1
    body = src.replace("/*SPRITES*/null", json.dumps(sprites, separators=(",", ":")))
    body = body.replace('"__INTRO__"', '"' + b64(os.path.join(A, "prof_intro.mp3")) + '"')

    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    open(os.path.join(ROOT, "dist", "artifact.html"), "w", encoding="utf-8").write(body)

    m = re.match(r"\s*(<title>.*?</title>)", body, re.S)
    head, rest = m.group(1), body[m.end():]
    full = ("<!doctype html>\n<html lang=\"it\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
            + head + "\n" + rest.replace("<div class=\"prs\"", "</head>\n<body>\n<div class=\"prs\"", 1)
            + "\n</body>\n</html>\n")
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(full)
    print("index.html", len(full) // 1024, "KB")


if __name__ == "__main__":
    main()
