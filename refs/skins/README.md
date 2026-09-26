# How to draw a skin for Mangiasassi

A skin is drawn against a character's existing base art in one of two modes:

- **`overlay`** — for an accessory (a hat, a badge, anything added on top). Drawn *on top of* the base
  frame. Draw **only the new pixels** on a transparent background — the character underneath is already
  there in the game and stays fully visible.
- **`replace`** — for a full costume that recolours the character (cape, gloves, boots, logo — anything
  that isn't just "adding" something). Drawn *instead of* the base frame, same canvas size. Redraw the
  whole character in the costume; there's no base showing through to worry about leaving transparent.

Every skin is one or the other, decided once per skin (not per frame) when it's added to the game's
`SKINS` registry. Ask which mode your skin needs before starting if it isn't already clear.

## Real frame set (what's actually reachable in the game today)

Not every base PNG in `base/` is currently drawn on screen — a few are defined in the sprite sheet but
never reached by any walk/eat cycle (see `SPRITE_INVENTORY.md` for the full breakdown). You can skip these
without losing anything:

- **Uomo roccia** — draw **10 frames**: `f0, f1, f2, e0, e1, fd0, fd1, fd2, fu0, fu3`.
  Skippable (exist as base PNGs, never actually drawn): `f3, fd3, fu1, fu2, fd_e0, fd_e1, fu_e0, fu_e1`.
- **Algidone** — draw **27 frames**: everything in `base/algidone/` except `al_r7`.
  Skippable: `al_r7` only.

You don't have to draw every one of the "real" frames either — any frame you don't provide simply renders
without the skin (never an error, never a placeholder). But the skippable ones above are dead weight; don't
spend time on them unless asked.

## Steps

1. Pick the character you're drawing for and open `base/uomo_roccia/` or `base/algidone/` — one PNG per
   sprite frame, already cropped exactly as the game uses it.
2. For each frame in the real set above, draw it in your skin's mode (see above): only the new pixels for
   `overlay`, the whole costumed character for `replace`.
3. **Keep the exact same canvas size** as the base PNG you copied (same width × height, in pixels). The
   game checks this — a frame whose size doesn't match its base is rejected at load time and that frame
   silently renders without the skin, in either mode.
4. Name your file with the `sk_<skin-id>_` prefix followed by the base frame's key, e.g. a skin called
   `geka` drawing on `f0.png` becomes `sk_geka_f0.png`. Use the exact same `<skin-id>` for every frame of
   the same skin.
5. **Delivery**: draw your skin's frames on a single template sheet, plus a `<skin-id>_cells.json` mapping
   each cell of the sheet to its frame key — both go under `refs/skins/<skin-id>/`. A cutting script
   (`refs/skins/cut_from_cells.py`) turns the sheet into the individual `sk_<skin-id>_<frameKey>.png` files
   from there. You don't need to cut anything yourself.

## Cutting algorithm (F4a/F4a2/F4c sheets, F4b1)

The character-sheet workflow (`skinBuildSheet` in `index.html`, "Scarica foglio") draws every frame at
×4 with a transparent margin, and `<skin-id>_cells.json` records each cell's rect. Turning a filled-in
sheet back into per-frame PNGs at native resolution — downscaling by exactly 1/4 — is **one algorithm**,
implemented **twice** (`refs/skins/cut_from_cells.py`'s `box_downscale()` for the offline/Python workflow,
`index.html`'s `skinBoxDownscale()` for the in-game "Carica costume" import, F4b1) and required to produce
byte-identical pixels in both places — not "close enough" the way two different libraries' resampling
(e.g. Pillow's LANCZOS vs. a browser canvas's own scaling) would be.

The algorithm: a premultiplied-alpha box filter. Each output pixel is the average of the source pixels in
its proportional slice `[floor(ox*w/ow), floor((ox+1)*w/ow))` of the input (the cell, margin included,
isn't always an exact multiple of 4 even though the base frame inside it always is — a plain "4×4 block"
box filter breaks on that edge case). Colour channels are weighted by alpha before averaging and divided
by the summed alpha (so a fully transparent source pixel never bleeds colour into a partially-covered
output pixel), and every result is rounded "half up" (`int(x+.5)` in Python, `Math.floor(x+.5)` in JS).
Every intermediate sum is an exact integer well inside a double's precision, so the two languages'
floating-point division gives the identical result bit-for-bit. A test proving this (`tools/fbstub/test_f4b1.py`,
"cutter parity") feeds the same synthetic pixels through both implementations and asserts byte-identical
output. Changing this algorithm in one file without the other breaks that guarantee — change both, together.

## Orientation rules

- Draw the **right-facing** side view only (`f*`/`al_w*`/`al_r*` etc. as they're named — check
  `SPRITE_INVENTORY.md`'s direction column). The game flips it horizontally in code for left-facing —
  never draw a separate left-facing version.
- **Up and down views are never flipped.** `fd*` frames are the character moving **up**, `fu*` frames are
  moving **down** — named by the crop row in the original reference sheet, not by what they show, so don't
  rely on the name alone; check `SPRITE_INVENTORY.md`'s direction column if unsure.
- Algidone's up/down sets (`al_u*`/`al_d*`) follow the same rule: draw them as-is, never mirrored.

## What NOT to do

- In `overlay` mode, don't redraw or recolour the character itself — only add new pixels for the accessory.
- Don't change the canvas size from the base frame, in either mode.
- Don't mix a skin between characters — a skin belongs to exactly one of Uomo roccia / Algidone, and its
  frames only ever apply to that character's own frame set.
- Don't worry about Cinghiale (Algidone's boar transformation) — the skin is hidden entirely while
  transformed, by design, so there's nothing to draw for it.
- Don't worry about the death-spin or the Acciaio glow either — both reuse whichever frame (and skin) is
  already showing; nothing extra to draw.
