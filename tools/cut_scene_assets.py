#!/usr/bin/env python3
"""
Crop the night-street cutscene assets (club building, moon, puddle, splash,
street props) out of the owner's AI-generated reference sheets in refs/
(refs/punto snai.png, refs/moon.png, refs/pond.png, refs/additional assets.png).

Pipeline per asset: crop a generous region around the chosen sheet option ->
flood-fill background removal from the crop's own corners (handles both the
grid-mural sheets and the plain-white pond sheet) -> drop small/thin leftover
grid-guide-line fragments -> tight-trim -> LANCZOS downscale to the game's
pixel-art scale -> palette quantization.

Nothing here touches index.html -- this only writes into refs/cut/scene/.
The embedded base64 in index.html (PRSCN) was produced from this script's
output; if the source sheets change, rerun this and re-embed by hand
(a small node snippet reading refs/cut/scene/*.png into PRSCN keys).

Usage:
    python3 tools/cut_scene_assets.py
"""
import os
from collections import deque
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "refs")
OUT = os.path.join(REFS, "cut", "scene")


def flood_bg_mask(im, tol=30):
    w, h = im.size
    px = im.load()
    visited = [[False] * h for _ in range(w)]
    bg = [[False] * h for _ in range(w)]
    q = deque()

    def close(c1, c2):
        return all(abs(c1[i] - c2[i]) <= tol for i in range(3))

    for cx, cy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if visited[cx][cy]:
            continue
        seed = px[cx, cy][:3]
        q.append((cx, cy))
        visited[cx][cy] = True
        while q:
            x, y = q.popleft()
            if not close(px[x, y][:3], seed):
                continue
            bg[x][y] = True
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny]:
                    visited[nx][ny] = True
                    q.append((nx, ny))
    return bg


def drop_thin_or_small(bg, w, h, min_size=6, min_thick=4):
    """Remove connected foreground components that are either tiny (leftover
    speckle) or a thin line (a sheet-wide grid-guide line sliced by the crop)
    -- keeps chunky real content like droplets/rocks/props."""
    visited = [[False] * h for _ in range(w)]
    comps = []
    for x0 in range(w):
        for y0 in range(h):
            if bg[x0][y0] or visited[x0][y0]:
                continue
            q = deque([(x0, y0)])
            visited[x0][y0] = True
            comp = []
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                               (x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)):
                    if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny] and not bg[nx][ny]:
                        visited[nx][ny] = True
                        q.append((nx, ny))
            comps.append(comp)
    newbg = [row[:] for row in bg]
    for comp in comps:
        xs = [p[0] for p in comp]
        ys = [p[1] for p in comp]
        bw = max(xs) - min(xs) + 1
        bh = max(ys) - min(ys) + 1
        if len(comp) < min_size or bw < min_thick or bh < min_thick:
            for (x, y) in comp:
                newbg[x][y] = True
    return newbg


def cutout(src_path, box, tol=30, erase=None, bgfill=(255, 255, 255), filter_thin=True,
           min_size=6, min_thick=4):
    im = Image.open(os.path.join(REFS, src_path)).convert("RGB").crop(box)
    if erase:
        d = ImageDraw.Draw(im)
        for r in erase:
            d.rectangle(r, fill=bgfill)
    w, h = im.size
    bg = flood_bg_mask(im, tol=tol)
    if filter_thin:
        bg = drop_thin_or_small(bg, w, h, min_size=min_size, min_thick=min_thick)
    out = im.convert("RGBA")
    px = out.load()
    for x in range(w):
        for y in range(h):
            if bg[x][y]:
                r, g, b, a = px[x, y]
                px[x, y] = (r, g, b, 0)
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    return out


def pixelize(im, target_h=None, target_w=None, colors=32):
    w, h = im.size
    scale = (target_h / h) if target_h else (target_w / w)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    small = im.resize((nw, nh), Image.LANCZOS)
    rgb = small.convert("RGB")
    alpha = small.split()[3]
    q = rgb.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG).convert("RGB")
    out = q.convert("RGBA")
    out.putalpha(alpha)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)

    # club building asset sheet -> "Option B" (top-right of the 2x2 grid),
    # with the left ~35% (plain facade + the horse/jockey window, the least
    # legible part at in-game size) cropped off so the CLUB sign and the
    # SNAI runner window read bigger at the same draw width
    club = cutout("punto snai.png", (858, 62, 1180, 392), tol=28, filter_thin=False)
    pixelize(club, target_h=150, colors=32).save(os.path.join(OUT, "club_b.png"))

    # moon sheet -> option 2 (cream, cratered, soft glow); crop excludes the
    # number label below each circle
    moon = cutout("moon.png", (415, 5, 808, 268), tol=30, filter_thin=False)
    pixelize(moon, target_h=50, colors=16).save(os.path.join(OUT, "moon2.png"))

    # pond sheet -> puddle option 2 (muddy rim, cigarette butts); white bg
    # with thin crosshair guide lines needing the small-island filter, plus
    # an explicit erase over the "2." label
    puddle = cutout("pond.png", (408, 0, 816, 324), tol=30, erase=[(0, 0, 65, 60)])
    puddle = puddle.crop((0, 28, puddle.width, puddle.height))
    puddle = puddle.crop(puddle.getbbox())
    px = puddle.load()
    for x in list(range(112, 124)) + list(range(252, 264)):
        for y in range(0, min(60, puddle.height)):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 0)
    puddle = puddle.crop(puddle.getbbox())
    pixelize(puddle, target_w=150, colors=24).save(os.path.join(OUT, "puddle.png"))

    # pond sheet -> splash option 5 (crown + droplets), same guide-line
    # cleanup as the puddle, tuned for this cell's line positions
    splash = cutout("pond.png", (0, 648, 408, 972), tol=30, erase=[(0, 0, 65, 75)])
    px = splash.load()
    for x in range(splash.width):
        for y in range(0, 2):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 0)
    for x in list(range(98, 110)) + list(range(242, 254)):
        for y in range(0, 42):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 0)
    splash = splash.crop(splash.getbbox())
    px = splash.load()
    for x in range(splash.width):
        for y in range(82, 86):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 0)
    splash = splash.crop(splash.getbbox())
    pixelize(splash, target_w=150, colors=24).save(os.path.join(OUT, "splash.png"))

    # additional assets sheet -> #2 trash can, #14 rope post, #18 tyre, #20 fast food
    props = [
        ("prop_trashcan.png", (168, 80, 272, 240), 40, 16),
        ("prop_rope.png", (1100, 335, 1195, 490), 44, 16),
        ("prop_tyre.png", (600, 575, 820, 742), 32, 16),
        ("prop_food.png", (1160, 580, 1350, 725), 34, 20),
    ]
    for name, box, target_h, colors in props:
        tol = 20 if "tyre" in name else 45
        min_size = 8 if "tyre" in name else 15
        im = cutout("additional assets.png", box, tol=tol, min_size=min_size)
        pixelize(im, target_h=target_h, colors=colors).save(os.path.join(OUT, name))

    print("done ->", OUT)


if __name__ == "__main__":
    main()
