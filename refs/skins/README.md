# How to draw a skin for Mangiasassi

A skin is an accessory or alternative clothing drawn **on top of** a character's existing base art — a
hat, a costume piece, and so on. It is never a full character redraw.

## Steps

1. Pick the character you're drawing for and open `base/uomo_roccia/` or `base/algidone/` — one PNG per
   sprite frame, already cropped exactly as the game uses it.
2. For each frame you want to add the accessory to, copy that PNG and draw **only the accessory** on a
   transparent background. Leave the rest of the canvas fully transparent — don't redraw the character
   underneath, it's already there in the game and your layer is composited on top of it at runtime.
3. **Keep the exact same canvas size** as the base PNG you copied (same width × height, in pixels). The
   game checks this — an overlay whose size doesn't match its base frame is rejected at load time and that
   frame silently renders without the skin.
4. Name your file with the `sk_<skin-id>_` prefix followed by the base frame's key, e.g. a skin called
   `geka` drawing on `f0.png` becomes `sk_geka_f0.png`. Use the exact same `<skin-id>` for every frame of
   the same skin.
5. You don't have to draw every frame. **Unused frames can be skipped** — see `SPRITE_INVENTORY.md` for
   which frames are actually reachable in the game today (a few are defined but never drawn). Any frame you
   don't provide simply renders without the skin (never an error, never a placeholder).

## Orientation rules

- Draw the **right-facing** side view only (`f*`/`al_w*`/`al_r*` etc. as they're named — check
  `SPRITE_INVENTORY.md`'s direction column). The game flips it horizontally in code for left-facing —
  never draw a separate left-facing version.
- **Up and down views are never flipped.** `fd*` frames are the character moving **up**, `fu*` frames are
  moving **down** — named by the crop row in the original reference sheet, not by what they show, so don't
  rely on the name alone; check `SPRITE_INVENTORY.md`'s direction column if unsure.
- Algidone's up/down sets (`al_u*`/`al_d*`) follow the same rule: draw them as-is, never mirrored.

## What NOT to do

- Don't redraw or recolour the character itself — only add new pixels for the accessory.
- Don't change the canvas size from the base frame.
- Don't mix a skin between characters — a skin belongs to exactly one of Uomo roccia / Algidone, and its
  frames only ever apply to that character's own frame set.
- Don't worry about Cinghiale (Algidone's boar transformation) or the death-spin/Acciaio glow — those are
  handled by the game engine, not by drawing extra frames.
