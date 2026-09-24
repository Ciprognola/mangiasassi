# Skin sprite inventory (K1a data layer, K1b draw-path hook, K2/K3 shipped skins)

Every place Uomo roccia or Algidone visually appears in the game, the frame keys involved, and whether
each frame is a real bitmap (skinnable) or code-drawn (not skinnable). Base frames are exported pixel-exact
from the current build (`index.html`) to `refs/skins/base/<char>/<key>.png` — these are the canvases an
artist draws skin overlays on top of. See `README.md` in this folder for the artist-facing how-to,
including the `overlay`/`replace` render modes added in K1b.

**Status as of K3**: the overlay/replace hook is wired into every bitmap draw-path listed below (via
`drawFace`, `drawEat`, `drawAlg` and the handful of call sites that draw `al_st` directly), and two real
skins ship through it (`SKINS.geka`, `SKINS.bk`). All three procedural places are **settled — no skin
needed** (owner decision, 2026-09-24): the two eating icons draw the item being eaten, not the character;
the Acciaio visual effect sits on top of whatever `drawTinted` already rendered, so it already applies to a
costumed character automatically. See the "Procedural" table below.

**Never crossed**: every location below only ever shows the *current* character. Nothing here reads or
mixes assets between Uomo roccia and Algidone.

## Base frame keys (bitmap, exported)

### Uomo roccia — `refs/skins/base/uomo_roccia/` (18 files, from `SPR`)

| Key | Size (px) | Direction | Used by (current draw paths) |
|---|---|---|---|
| `f0` | 96×85 | side | walk cycle frame 0 / idle (maze, menu scene, all static portraits) |
| `f1` | 96×86 | side | walk cycle frame 1 |
| `f2` | 96×89 | side | walk cycle frame 2 (also the fixed "idle/portrait" frame everywhere a static face is shown) |
| `f3` | 96×86 | side | **unused** — not in the walk cycle (`[0,1,2,1]`), not referenced as a fixed frame anywhere |
| `e0` | 117×94 | side | eating bite frame 0 (`drawEat`, side view + battle-interjection bite) |
| `e1` | 113×94 | side | eating bite frame 1 |
| `fd0` | 78×88 | up | walk cycle frame 0 (maze moving **up** — named `fd` by crop row, see CLAUDE.md §4) |
| `fd1` | 78×88 | up | walk cycle frame 1 |
| `fd2` | 75×88 | up | walk cycle frame 2 |
| `fd3` | 77×88 | up | **unused** — up walk cycle is also `[0,1,2,1]`, never reaches index 3 |
| `fd_e0` | 58×88 | up | **fully dead** — `eatKey("fd",0)` is never called; up/down eating uses the procedural rock-icon overlay (`drawFaceEatFX`) instead, not this bitmap |
| `fd_e1` | 57×88 | up | **fully dead**, same reason |
| `fu0` | 75×88 | down | walk cycle frame 0 (maze moving **down** — named `fu`, see CLAUDE.md §4) |
| `fu1` | 85×88 | down | **unused** — down walk cycle is `[0,3,0,3]`, a turn-transition pose baked into the sheet, intentionally skipped (documented in CLAUDE.md §4 already) |
| `fu2` | 69×88 | down | **unused**, same reason as `fu1` |
| `fu3` | 75×88 | down | walk cycle frame 3 (the second pose actually used, alternating with `fu0`) |
| `fu_e0` | 63×88 | down | **fully dead**, same reason as `fd_e0`/`fd_e1` |
| `fu_e1` | 85×88 | down | **fully dead**, same reason |

Excluded from the character base set (these are **item** art, not the avatar): `rock`, `r1`, `r2` — the
default rock pellet's own animation frames, drawn independently of the character. Skinning the character
never touches these; a future "rocce" item customisation would be a separate feature.

### Algidone — `refs/skins/base/algidone/` (28 files, all of `SPR2`)

| Key | Size (px) | Direction | Used by (current draw paths) |
|---|---|---|---|
| `al_st` | 72×100 | side | idle (maze, menu scene, every static portrait, dialogue talking-bob) |
| `al_w0`…`al_w7` | 75×100 | side | walk cycle, 8 frames cycled by `Math.floor(anim*11)%8` |
| `al_r0`…`al_r6` | 67×64 | side | **power-up "rolling" state** (maze `power>0` — the Pac-Man-style reversal, not Cinghiale), 7 of 8 frames cycled by `%7` |
| `al_r7` | 67×64 | side | **unused** — already documented in CLAUDE.md §4 (out of the `%7` range on purpose) |
| `al_d0`…`al_d3` | ~70-74×100 | down | walk cycle, 4 frames cycled by `%4` |
| `al_d_st` | 73×100 | down | idle while facing down |
| `al_u0`…`al_u5` | ~75-89×100 | up | walk cycle, 6 frames cycled by `%6`; `al_u0` also doubles as the up-facing idle frame |

Every Algidone key is used somewhere — no dead frames in `SPR2`.

## Procedural (not bitmap — no base frame; all settled, none need a skin)

| What | Function | Skin status |
|---|---|---|
| Cinghiale (boar transformation) | `drawBoar()` | **Settled, not pending.** 100% code-drawn pixel art (rects/ellipses/triangles), no `IMG` reference at all. Per §10.9 K1b decision: skin is hidden entirely while transformed — no overlay, by design, not an open question. |
| Up/down eating icon | `drawFaceEatFX()` (roccia) | **Settled — no skin needed.** A small rock icon fades in/shrinks near the mouth while eating up/down — it draws the **rock being eaten**, not the character, so there's nothing on the character for a skin to touch here. Reuses the item's own art (`rockFrames`/`IMG.rock`) regardless of an equipped skin, by design. |
| Any-direction eating icon (Algidone) | inline in `drawAlg()` | **Settled — no skin needed.** Same reasoning: it draws the **snack being eaten** (`snackFrames`), not the character. |
| Acciaio visual effect (ring + diagonal sweep highlight) | inline in the maze `draw()` around `drawTinted(...)` | **Settled — no skin needed.** It's a pure vector effect (colour/alpha only) drawn *on top of* whatever `drawTinted` already rendered — since the skin is part of that rendered character (confirmed in K1b/K2), the ring and sweep already sit over a costumed character automatically. Nothing further to build. |
| Death-spin transform | inline in the maze `draw()` | Not procedural art — it's a real bitmap frame (`f2` / `al_st`-equivalent via `drawAlg`) rotated + scaled by code, **already skinned** via the same `drawFace`/`drawAlg` hook. Listed under its draw-path entry below, not here. |

## Every place a character appears (draw-path → frame keys)

1. **Maze gameplay, normal movement** — `draw()` → `drawHero()`/`drawAlg()`, all 4 directions + eating:
   - Side (left/right, mirrored via `flip`): roccia `f0,f1,f2` (walk) + `e0,e1` (eating, via `drawEat`); Algidone `al_st` (idle) / `al_w0-7` (walk) + procedural snack icon
   - Up: roccia `fd0,fd1,fd2` (walk) + procedural rock icon while eating (no bitmap eat frame used); Algidone `al_u0` (idle) / `al_u0-5` (walk)
   - Down: roccia `fu0,fu3` (walk) + procedural rock icon while eating; Algidone `al_d_st` (idle) / `al_d0-3` (walk)
   - Algidone power-up "rolling": `al_r0-6`, **side art only** — there's no dedicated up/down roll art, so Algidone always shows the side-view roll sprite while the power-up is active even if facing up/down (existing behaviour, not new)
2. **Maze gameplay, Acciaio (steel ability)** — same frames as #1, drawn through `fn` (=`drawHero`) inside `drawTinted()`. `drawTinted` renders `fn` to an offscreen canvas *then* tints the whole buffer blue via `source-atop` compositing — so **whatever the overlay hook draws inside `drawHero`/`drawFace`/`drawAlg` automatically inherits the steel tint for free**, no special-casing needed in K1b. Matches the §10.9 decision (skin stays on, gets the steel look).
3. **Maze gameplay, Cinghiale (boar ability)** — `drawBoar()`, entirely separate, no character frames at all. Matches the §10.9 decision (skin hidden).
4. **Maze gameplay, power-up reversal tint / lava burn tint** — same `drawTinted(fn,...)` pattern as #2, same frames, same automatic-inherit behaviour.
5. **Maze gameplay, death spin** — fixed frame, side view only, rotated/scaled procedurally: roccia `f2` (frame index 2, via `drawFace`), Algidone via `drawAlg` with `moving:false` (→ `al_st`).
6. **Home menu scene** (`startMenuScene`/`drawScene`, the animated character idling/eating on the main menu) — side view only: roccia frames cycling `0/1/2` (idle/open/chew) + `e0/e1` while biting; Algidone `al_st`/`al_w0`.
7. **Lista desideri › Giocatore character card** (`cardHTML`, `paintCanvases` case `"hero"`) — static portrait, side view only: roccia `f2`; Algidone `al_st`.
8. **Roadmap gift-reveal preview** (R3's `#giftreveal` canvas) — reuses the exact same `paintCanvases` `"hero"` case as #7 (`data-draw="hero:<char>:130"`), same frames.
9. **Maze HUD lives icons** (the small row of life icons during a run) — static portrait, side view only: roccia `f2`; Algidone `al_st` (small crop).
10. **Splash/loading screen logo** (`renderSplash`, `#logo` canvas) — static portrait, side view only: roccia `f2`; Algidone `al_st`. Shows whichever character is currently selected.
11. **Mini-game placeholder card** (`drawMiniPlaceholder`) — static portrait, **hardcoded to roccia `f2` regardless of the active character** (no Algidone branch at all), plus 3 rolling rock icons alongside it. **Confirmed intentional by the owner** (2026-09-24, post-K1b): this is the "Mangiaroccia" brand icon for the mini-game card itself, not a "your active character" portrait — left unskinned by design, not a bug. No hook needed here, ever.
12. **Professor mini-game — dialogue portrait box** (`prDrawPlayer`/`PR_SPK.plr`, only shown for lines with `spk:"plr"`, e.g. the "Sì" branch's `pr_pk` interjection line) — animated talking portrait in an 88×100 box: roccia cycles `f0,f1,f2,f1` while talking (frame `f0` when silent) with a 1px bob; Algidone `al_st` scaled, with the same bob (no mouth-cycle frames — Algidone has no dedicated "talking" frames, only the bob).
13. **Professor mini-game — pond-throw cutscene** ("No" branch, `prPlayerCv()` → cached 96×96 canvas reused by `prSceneKick`'s toss/splash phases) — static portrait, side view only: roccia `f2`; Algidone `al_st`. The cutscene then rotates/scales/clips this cached canvas procedurally (arc through the air, submerge in the pond) — the character art itself is just the same static portrait as #7/#9/#10.
14. **Professor mini-game — professor scene** (`prSceneProf`, the idle/angry professor + pokéball throw + Duskull emergence) — **the human player character does NOT appear here at all.** Only the professor (`PRSPR`/`PRIMG`) and the procedurally-drawn pokéball/Duskull are drawn. The player only appears via #12 (the separate dialogue portrait box) when a `spk:"plr"` line plays over this scene.
15. **Professor mini-game — kick-out walk/flash phase** (`prSceneKick`, before the toss) — same as #14: only the professor (`PRIMG.walk`) is drawn. The player doesn't appear until the toss/splash phase, which is #13.
16. **Professor battle screen** (`pbActor`, the actual Gen-3-style fight) — draws the player's chosen **Rocciamon asset** (a rock or snack sprite via `rockFrames`/`snackFrames`), **not** the human character's body. Out of scope for character skins — belongs to the separate, not-yet-built "squadra rocciamon" customisation slot (§10.5/§8), a different feature.
17. **Career modal** (`careerModal`, the level/rank popup opened from a character card) — **text only, no character art at all.** The visual portrait is on the surrounding card (#7), not inside this modal.
18. **Algidone's mini-game ("Coccia") climber** — **not built yet** (M-chunks are all `todo`). Will need its own frame set and a skin-overlay hook when M1/M2 land; flagged here so K1b's hook design doesn't need to special-case it now, but M-chunks should reuse the same `skinImg()` helper once the climber sprite exists.
19. **Character customisation page** (C1, §10.5) — **not built yet.** Will need a live skin-preview canvas; expected to reuse the same static-portrait pattern as #7/#8/#9/#10/#13, but no code exists yet to hook into.

## K1b implementation notes (done)

- The hook lives inside the **three** low-level draw functions (`drawFace`, `drawEat`, `drawAlg`), via a
  shared `drawSkinned(ctx,char,frameKey,im,dx,dy,dw,dh)` helper that draws base+skin with **identical**
  `drawImage` arguments to what the function already used (same `dx,dy,dw,dh`, same `save`/`restore`, same
  flip/scale/smoothing/alpha already set by the caller) — so every call site above (maze, menu, cards, HUD,
  splash, cutscene, dialogue box) picked it up automatically, without touching each call site's own sizing
  math. `drawFaceEatFX`'s rock-icon overlay is untouched (item art, see the Procedural table) — the walk
  frame drawn alongside it by `drawHero` already carries the skin on its own.
- Five places that draw `IMG.al_st`/`al_w0` **directly** instead of going through `drawAlg()` — the Lista
  desideri/gift-reveal card, the maze HUD lives icons, the splash logo, the pond-cutscene cached portrait
  (`prPlayerCv`), the professor dialogue talking-portrait (`prDrawPlayer`), and the menu scene (`drawScene`)
  — were each updated individually to call `drawSkinned` in place of their own `ctx.drawImage`, same
  identical-arguments rule. Their roccia counterparts already went through `drawFace`/`drawEat` and needed
  no change.
- Acciaio's tint (`drawTinted`) needs **no special handling** — confirmed by test: it tints whatever the
  hook draws, since the hook lives inside `drawHero`'s own callees.
- Cinghiale (`drawBoar`) needs **no hook at all** — it never calls into the low-level draw functions.
- `drawMiniPlaceholder`'s hardcoded-to-roccia icon (#11) was **left as-is, not fixed** — reported to the
  owner and **confirmed intentional**: it's the "Mangiaroccia" brand icon for the mini-game card, not a
  per-character portrait. Settled, not open.
