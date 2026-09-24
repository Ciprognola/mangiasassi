# Skin kit — GEKA SNC cap (Uomo roccia) + Burger King costume (Algidone)

Put this folder in the repo as `refs/skins/` content: `refs/skins/geka/`, `refs/skins/bk/`, plus `cut_from_cells.py` next to them.

## How to draw (both skins)
1. Open `<skin>_template_GUIDE.png` in your editor (Aseprite, Photopea, Photoshop…). Do **not** resize or crop it.
2. Add a new transparent layer on top. Draw inside the pink-bordered cells only — every cell is exactly the size of that game frame.
3. Hide the guide layer, export only your layer as `<skin>_DRAWN.png` (same size as the template, transparent background).
4. Leave a cell empty if you don't have that frame yet — the game shows that frame without the skin, and the cut script lists it as missing.

`<skin>_template_DRAW_HERE.png` is an empty transparent sheet of the right size, if your editor prefers starting from a file.
`<skin>_cells.json` gives every cell's position — Claude Code cuts with it: `python3 cut_from_cells.py geka/geka_cells.json geka/geka_DRAWN.png out/`.
`<skin>_reference_board.png` puts each game frame next to the matching part of your design, with what is still missing.

Side frames face RIGHT (left is flipped by code). Up/down frames are never flipped.

## GEKA SNC cap — mode OVERLAY — 10 frames
Draw **only the cap**, on transparency. Everything you don't paint shows the normal Uomo roccia underneath.
- Side walk: f0, f1, f2 · Side eating: e0, e1 (draw the cap only, the rock is part of the game frame)
- Moving UP: fd0, fd1, fd2 (`fd` = face visible, named by crop row)
- Moving DOWN: fu0, fu3 (back of head) — **missing in your design**: the reference back view has no cap. Use the top-view cap as a guide.
- Not needed (never shown): f3, fd3, fu1, fu2, fd_e*, fu_e*

## Burger King costume — mode REPLACE — 27 frames
The costume changes cap, cape colour, logo, gloves and boots — almost every pixel. As an overlay, any red pixel you miss would show through, so this skin draws the **whole character in costume** in each cell (the cell replaces the game frame).
- Idle + moving down (front): al_st, al_d_st, al_d0–al_d3 — covered by your design
- Side walk: al_w0–al_w7 — **partial**: only crown head + cape from the side; side body (shirt/logo, gloves, boots) and walk poses missing
- Moving up (back): al_u0–al_u5 — **partial**: crown + cape from behind; back legs/boots missing
- Rolling (power-up): al_r0–al_r6 — **partial**: 6 balls for 7 frames, poses must follow the game's rotation order
- Not needed: al_r7
