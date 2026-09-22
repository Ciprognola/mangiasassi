#!/usr/bin/env python3
"""
Crop up/down animation frames out of the reference character sheets in refs/
(refs/algidone_sheet.jpeg, refs/uomoroccia_sheet.jpeg).

Pipeline: background removal (flood fill from the corners, so interior dark
pixels of the character -- cape shadows, hair -- are kept, unlike a global
colour threshold) -> alpha -> per-region grid segmentation via row/column
projection of the alpha mask -> per-frame tight trim -> scale to a target
height -> individual PNGs + one labelled contact sheet per character for
visual approval.

Nothing here touches index.html -- this only writes into refs/cut/.

Usage:
    python3 tools/cut_sprites.py
"""
import os
from collections import deque
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "refs")
OUT = os.path.join(REFS, "cut")

BG_TOLERANCE = 30  # per-channel distance from sampled corner colour treated as background
MIN_BAND = 2        # minimum thickness (px) of a foreground row/col band to count as content
PAD = 3              # padding kept around each trimmed frame, in source-resolution px


def flood_bg_mask(im):
    """Boolean mask (True = background) via 4-way flood fill from all four
    corners, using a colour-distance tolerance from each corner's own sampled
    colour. Keeps dark pixels enclosed by the character instead of nuking them
    like a global threshold would."""
    w, h = im.size
    px = im.load()
    visited = [[False] * h for _ in range(w)]
    bg = [[False] * h for _ in range(w)]
    q = deque()

    def close(c1, c2):
        return all(abs(c1[i] - c2[i]) <= BG_TOLERANCE for i in range(3))

    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    for cx, cy in corners:
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


def apply_alpha(im, bg_mask):
    w, h = im.size
    out = im.convert("RGBA")
    px = out.load()
    for x in range(w):
        col = bg_mask[x]
        for y in range(h):
            if col[y]:
                r, g, b, _ = px[x, y]
                px[x, y] = (r, g, b, 0)
    return out


def bands(flags):
    out = []
    start = None
    for i, v in enumerate(flags):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= MIN_BAND:
                out.append((start, i - 1))
            start = None
    if start is not None and len(flags) - start >= MIN_BAND:
        out.append((start, len(flags) - 1))
    return out


def segment_grid(im):
    """Row projection then, per row, column projection of an RGBA image's
    alpha channel. Returns a list of rows, each a list of (x0,y0,x1,y1)
    boxes left-to-right, in the given image's own coordinate space."""
    w, h = im.size
    a = im.split()[-1]
    apx = a.load()
    row_has = [any(apx[x, y] for x in range(w)) for y in range(h)]
    rows = bands(row_has)
    grid = []
    for (ry0, ry1) in rows:
        col_has = [any(apx[x, y] for y in range(ry0, ry1 + 1)) for x in range(w)]
        cols = bands(col_has)
        row_boxes = [(cx0, ry0, cx1, ry1) for (cx0, cx1) in cols]
        if row_boxes:
            grid.append(row_boxes)
    return grid


def tight_trim(im):
    bbox = im.split()[-1].getbbox()
    return im.crop(bbox) if bbox else im


def scale_to_height(im, target_h):
    w, h = im.size
    if h == 0:
        return im
    scale = target_h / h
    return im.resize((max(1, round(w * scale)), target_h), Image.LANCZOS)


def save_named_frames(sheet_rgba, crop_box, names, target_h, out_dir, pad=PAD, min_row_h=50):
    """Crop sheet_rgba to crop_box, auto-segment into a single reading-order
    list of frames (rows concatenated top-to-bottom, left-to-right within a
    row), then save the first len(names) of them under the given names.
    Rows thinner than min_row_h (divider lines, digit-label captions under
    each frame) are dropped before flattening. Extra detected frames beyond
    len(names), or a shortfall, are reported so a bad crop_box / region
    layout doesn't silently mislabel frames."""
    sub = sheet_rgba.crop(crop_box)
    grid = segment_grid(sub)
    grid = [row for row in grid if max(y1 - y0 for x0, y0, x1, y1 in row) >= min_row_h]
    ordered = [box for row in grid for box in row]
    if len(ordered) != len(names):
        print(f"    WARNING: region {crop_box} expected {len(names)} frames, "
              f"found {len(ordered)} -- check the contact sheet before trusting labels")
    saved = []
    for name, box in zip(names, ordered):
        x0, y0, x1, y1 = box
        x0p, y0p = max(0, x0 - pad), max(0, y0 - pad)
        x1p, y1p = min(sub.width, x1 + 1 + pad), min(sub.height, y1 + 1 + pad)
        frame = tight_trim(sub.crop((x0p, y0p, x1p, y1p)))
        frame = scale_to_height(frame, target_h)
        frame.save(os.path.join(out_dir, f"{name}.png"))
        print(f"    {name}.png ({frame.width}x{frame.height})")
        saved.append((name, frame))
    return saved


def build_contact_sheet(frames, out_path, cols=4):
    if not frames:
        print("  no frames to build a contact sheet from")
        return
    cell_w = max(f.width for _, f in frames) + 20
    cell_h = max(f.height for _, f in frames) + 34
    rows = (len(frames) + cols - 1) // cols
    canvas = Image.new("RGB", (cell_w * cols, cell_h * rows), (30, 30, 30))
    tile = 8
    for y in range(0, canvas.height, tile):
        for x in range(0, canvas.width, tile):
            if (x // tile + y // tile) % 2 == 0:
                for yy in range(y, min(y + tile, canvas.height)):
                    for xx in range(x, min(x + tile, canvas.width)):
                        canvas.putpixel((xx, yy), (45, 45, 45))
    draw = ImageDraw.Draw(canvas)
    for i, (name, frame) in enumerate(frames):
        r, c = divmod(i, cols)
        cx0, cy0 = c * cell_w, r * cell_h
        canvas.paste(frame, (cx0 + 10, cy0 + 10), frame)
        draw.text((cx0 + 4, cy0 + cell_h - 20), name, fill=(255, 210, 60))
    canvas.save(out_path)
    print(f"  contact sheet -> {out_path}")


def load_rgba(sheet_name):
    im = Image.open(os.path.join(REFS, sheet_name)).convert("RGBA")
    bg = flood_bg_mask(im)
    return apply_alpha(im, bg)


def build_algidone():
    print("Algidone: cropping FRONT (DOWN) and BACK (UP) walk rows...")
    rgba = load_rgba("algidone_sheet.jpeg")
    out_dir = os.path.join(OUT, "algidone")
    os.makedirs(out_dir, exist_ok=True)
    all_frames = []

    # "FRONT (DOWN) WALK ANIMATION": 2 sub-rows of 4 under the header, frames
    # 1-4 walk cycle, 5 front idle, 6-8 turning into the back pose. Box found
    # by isolating this region from the portrait/header noise that defeats
    # whole-sheet segmentation (see tools/cut_sprites.py history / CLAUDE.md).
    down = save_named_frames(
        rgba, (340, 55, 1024, 520),
        ["down_1", "down_2", "down_3", "down_4", "down_5", "down_turn6", "down_turn7", "down_turn8"],
        target_h=100, out_dir=out_dir)
    all_frames += down

    # "BACK (UP) WALK ANIMATION": one row, 6 frames. Measured bounds y=(578,752);
    # crop tight to it so the divider line above (y~557-569) and the digit
    # captions below (y~761-774) don't leak in.
    up = save_named_frames(
        rgba, (0, 573, 1024, 757),
        ["up_1", "up_2", "up_3", "up_4", "up_5", "up_6"],
        target_h=100, out_dir=out_dir)
    all_frames += up

    build_contact_sheet(all_frames, os.path.join(out_dir, "_contact_sheet.png"))


def build_uomoroccia():
    print("Uomo roccia: cropping DOWN (front-face) and UP (back-of-head) frames...")
    rgba = load_rgba("uomoroccia_sheet.jpeg")
    out_dir = os.path.join(OUT, "uomoroccia")
    os.makedirs(out_dir, exist_ok=True)
    all_frames = []

    # Row 2 of the sheet (0-indexed, measured y=(358,541)): full front face,
    # 4 walk/talk variants + rock-entering-top + crumb burst + plain.
    # "existing style" rows 0-1 (side profile, y<350) are skipped -- that art
    # is already in the game.
    down = save_named_frames(
        rgba, (0, 353, rgba.width, 546),
        ["fd0", "fd1", "fd2", "fd3", "fd_eat0", "fd_eat1", "fd_plain"],
        target_h=88, out_dir=out_dir)
    all_frames += down

    # Row 3 (measured y=(570,753)): back-of-head, same 7-slot pattern.
    up = save_named_frames(
        rgba, (0, 565, rgba.width, 758),
        ["fu0", "fu1", "fu2", "fu3", "fu_eat0", "fu_eat1", "fu_plain"],
        target_h=88, out_dir=out_dir)
    all_frames += up

    build_contact_sheet(all_frames, os.path.join(out_dir, "_contact_sheet.png"))


if __name__ == "__main__":
    build_algidone()
    build_uomoroccia()
    print("Done. Nothing in index.html was touched -- review refs/cut/*/_contact_sheet.png before any embedding step.")
