# Changelog — Mangiasassi

Detailed build-by-build log. CLAUDE.md §7 stays as the short summary table; this file is the
detailed record, one entry per delivered version. This file was bootstrapped on 2026-09-22 from
CLAUDE.md §7 (which only had range-level detail for everything before 0.2_40) — see that section
for anything not itemised below.

## Pre-0.2_40 summary (bootstrapped, range-level detail only)

| Range | Content |
|---|---|
| 0.1_1 → 0.2_5 | The OG Chat: whole game built — both characters, progression, difficulties, power-up, 5 maps, menu scene, 30 achievements, El Gamblador, dev mode |
| 0.2_7 → 0.2_19 | 1st patch: desktop scaling + shortcuts + Hardcore split + locked El Gamblador card (0.2_8); 50 quotes per character (0.2_9); BJ table rebuild (0.2_10); steel ability (0.2_11); dev girone-jump buttons (0.2_12); boar ability (0.2_13); boar 4-direction sprites, smoke, wall-break particles (0.2_14); per-map dimensions, water/lava streams, following camera, map hardening, 10 new maps (0.2_15–0.2_19) |
| 0.2_20 → 0.2_27 | Fix 2: BJ pause fix, dealer centring, raise logic, raise UI, dealer lines, options redesign with tabs (Generali/Sviluppatore) + accordions, ZIP writer + manifest builder, export dialog UI |
| 0.2_28 → 0.2_29 | Menu music swap ×2; gapless Web Audio loop player |
| 0.2_30 → 0.2_39 | "Roccia no" chunks 1–9 complete: professor sprites, dialogue box, no-branch, sì-branch, 70 battle profiles, engine, battle screen, endings, export/dev-tools integration + 3 music tracks; plus quick fixes (dev quick-battle button, quit flow returns to "Roccia sì o roccia no?", typo, in-universe win/lose text, snack DEF/SpD rebalance) |

## 0.2_40 — 2026 (exact date not recorded pre-bootstrap)
- Chunk 1 — professor menu-lock parity: `S.p.pr={visits,seen}` + migration, `profImg()` using
  `PRSPR.blink`, `"prof"` case in `paintCanvases`, locked "Il Professore" card, `seen` set only on
  real battles.

## 0.2_41 — 2026-09-22
- Embedded 23 new sprite frames as `SPR`/`SPR2` keys, cropped from owner-supplied reference sheets
  (`refs/algidone_sheet.jpeg`, `refs/uomoroccia_sheet.jpeg`) via the new `tools/cut_sprites.py`:
  - Uomo roccia (into `SPR`): `fd0-3` + `fd_e0/fd_e1` (facing down / front, walk + eat), `fu0-3` +
    `fu_e0/fu_e1` (facing up / back of head, walk + eat).
  - Algidone (into `SPR2`): `al_d0-3` + `al_d_st` (facing down, walk + idle), `al_u0-5` (facing up,
    walk).
  - Needed owner-supplied reference art (both JPEGs in `refs/`); no new asset requested this round.
  - `index.html` grew 3,725,080 → 4,157,533 bytes (+432 KB, ~+11.6%) from the new embedded PNGs.
  - **Not wired into any drawing code yet** — `drawFace`/`drawAlg`/`drawHero` are unchanged, so
    these keys load but are unused. That wiring, plus the known Algidone-DOWN flip bug, is the next
    chunk in CLAUDE.md §8.
  - `node --check` passes on both inline `<script>` blocks. No save-data shape changed, so no
    migration entry needed.

## 0.2_42 — 2026-09-22
- Wired the up/down sprites embedded in 0.2_41 into `drawFace`/`drawEat`/`drawAlg`/`drawHero`
  (backlog §8 chunks 3+4, done together since chunk 4's fix was naturally part of getting chunk 3
  right the first time):
  - `drawFace`/`drawEat` take an optional `prefix` ("fu"/"fd"/default "f") to pick the sprite set;
    `eatImg`/`eatVar` generalized the same way (`eatKey()` helper) so custom rock-quality recoloring
    also works for the new directional eat frames, not just the side view.
  - `drawHero`/`drawAlg` pick the frame set from `o.dir` (0=up,1=right,2=down,3=left) and **never
    apply the horizontal flip for up/down** — enforced inside `drawFace`/`drawEat`/`drawAlg`
    themselves (not just by the caller), so this holds regardless of what future code calls them.
  - `o.dir` added to the render object in `draw()` (`dir:P.face==null?1:P.face`) and to the dying-
    animation `drawAlg` call; this is what backlog chunk 4 flagged as missing.
  - Discovered mid-implementation: the reference sheet's "BACK (UP) WALK ANIMATION" row has a
    turn-transition baked into frames 2-3 (`fu1`/`fu2` — a 3/4-turn and a front-ish open-mouth pose,
    not back-of-head), which would have flashed a wrong orientation mid-walk-cycle. Fixed by using a
    `[0,3,0,3]` frame sequence for facing-up instead of the side view's `[0,1,2,1]`; `fu1`/`fu2`
    stay embedded but unused by the walk cycle.
  - Verified with a headless Chrome probe (Playwright, pointed at the system Chrome install, no
    browser download): called `drawFace`/`drawEat`/`drawAlg` directly for all
    dir×moving×eat/power combinations for both characters — zero runtime errors, and confirmed
    pixel-identical output between `flip:true`/`flip:false` for both up and down on both characters.
    Also screenshotted all 4 directions × both characters for a visual check.
  - Not tested: real device/touch input, and in-game visual review by the owner (the probe renders
    the sprite functions directly on an offscreen canvas, not the full running game).
  - `node --check` passes on both inline `<script>` blocks. No save-data shape changed.

## 0.2_43 — 2026-09-23
- Bugfix pass on the four sprite regressions the owner found in 0.2_42 (left/right untouched):
  - **Uomo roccia up/down swapped**: `fd0..3`/`fu0..3` were cropped in sheet-row order, not by
    what they show — `fd` is the front-face row (rock enters from the top) and `fu` is the
    back-of-head row (rock enters near the collar). CLAUDE.md §8's original reference notes say
    row 3 = UP, row 4 = DOWN, which makes UP the front-face set and DOWN the back-of-head set —
    the opposite of what 0.2_42 wired. Fixed by swapping the `dir→prefix` mapping in `drawHero`
    (and moving the `fu1`/`fu2` turn-transition frame-skip so it follows whichever direction now
    resolves to `fu`, not a hardcoded `dir===0`). No embedded sprite data touched — pure mapping
    fix.
  - **Up/down larger than left/right**: `drawFace`/`drawEat` scaled the new portrait-shaped
    `fu`/`fd` crops by forcing them to the side view's *width*, then deriving height from their
    own aspect ratio — but a front/back head crop is narrower than a side-profile silhouette at
    the same height, so this over-stretched their height. Both functions now match the side
    view's on-screen *height* for `fu`/`fd` and derive width from the crop's own aspect ratio
    instead, and `drawEat`'s overlay is now centered (`-iw/2`) for `fu`/`fd` rather than
    left-anchored like the side view (which needs the offset because its mouth sits toward one
    side; a front/back head doesn't).
  - **Up/down chewing looked like a plain mouth open/close**: this was mostly the two bugs above
    — once the eat overlay is the right scale and centered under the head instead of shifted and
    oversized, the existing two-frame "rock enters → crumb burst" pair reads as a continuous bite
    like the side view's `e0`/`e1`, not a jarring pop. No new art, same frame count (2) and the
    same `.13`s toggle threshold as left/right.
  - **Algidone roll animation missing up/down**: `drawAlg`'s vertical branch always picked a walk
    frame (`al_u*`/`al_d*`) and never checked `o.power`, so Cinghiale's roll froze on a walk pose
    when moving vertically. There's no dedicated up/down roll art, so restored the pre-0.2_41
    behaviour: whenever rolling, fall back to the side-view roll sprite (`al_r*`, flippable)
    regardless of direction, same as when every direction used that side view before the up/down
    sprites existed.
  - Verified with a headless Chrome probe (system Chrome via Playwright's `channel:"chrome"`,
    no browser download needed): called `drawFace`/`drawEat`/`drawAlg` directly for all
    dir×moving×eat/power combinations for both characters, screenshotted the grid, confirmed
    up/down now matches side-view scale, rock-entry direction matches CLAUDE.md's UP/DOWN notes,
    and Algidone's roll sprite now renders (flippable) in all 4 directions instead of only 2.
  - Not tested: real device/touch input, in-game visual review by the owner (the probe renders
    the sprite functions directly, not the full running game). `node --check` passes on both
    inline `<script>` blocks. No save-data shape changed.

## 0.2_44 — 2026-09-23
- Bugfix: Uomo roccia's up/down eating still looked downscaled after 0.2_43's mapping/scale fix
  (owner caught it after the build; directional mapping was already correct). Root cause was
  different from 0.2_43's: `cut_sprites.py` independently normalizes every crop to the same
  height regardless of how much extra rock art it contains, so `fd_e0`/`fd_e1`/`fu_e0`/`fu_e1`
  (each = head + a floating rock chunk) squeeze the *head* itself into less than the walk frames'
  full height to make room for the rock. Forcing the total image to match the walk frame's height
  (0.2_43's fix) therefore still shrank the head whenever the rock was in shot.
  - Per the owner's suggested options, went with the "static frame + rock debris" combination
    instead of trying to rescale the mismatched dedicated crops: `drawHero` now draws the normal,
    correctly-scaled walk frame for up/down even while eating, and a new `drawFaceEatFX` overlays
    a small rock icon (reusing `rockFrames`/`artRock`, same as the side view's recolor) that
    shrinks and fades near the mouth over the same 0.26s eat window, positioned near the top for
    "up" and near the collar for "down" to match the rock-entry direction from 0.2_43. `fd_e0`/
    `fd_e1`/`fu_e0`/`fu_e1` stay embedded but unused (same precedent as `fu1`/`fu2`).
  - Left/right eating (`drawEat`, `e0`/`e1`) is untouched -- the `fu`/`fd` special case added in
    0.2_43 was removed from `drawEat` since it's no longer called for those prefixes.
  - Verified with the same headless-Chrome probe pattern, this time calling `drawHero` directly
    (not `drawFace`/`drawEat` individually) so the screenshot matches what the game actually
    calls: all 4 directions across idle/walk/three eat-progress points, both characters. Up/down
    heads now stay full-size throughout eating; the rock icon visibly shrinks and fades.
  - Not tested: real device/touch input, in-game visual review by the owner. `node --check`
    passes both inline `<script>` blocks. No save-data shape changed.

## 0.2_45 — 2026-09-23
- Gameplay tuning trio (backlog §8 "Queued", all three approved together, one build):
  - **El Gamblador spawns sooner/more often**: `bjAfterClear()` used to gate the table behind a
    guaranteed appearance at girone 5, then a 70% checkpoint chance every 5 gironi after (7-55%
    otherwise, score-scaled) -- meaning zero chance before girone 5. Now guarantees the first
    table at girone 3, checkpoints every 3 gironi at 75%, and raises the in-between base odds to
    12-60%. Verified with a headless-Chrome probe calling `bjAfterClear()` 4000×/stage with score
    fixed at 0: girone 3 hits 100% of the time (previously 0%), gironi 6/9/12 hit ~75%, and the
    non-checkpoint gironi in between hit ~11-12% each (previously 0% before girone 5).
  - **Ability cooldown now survives death**: `resetActors()` unconditionally set `G.st=null` on
    every call, including the life-loss respawn path (`resetActors(true)`, called from `update()`
    when `G.lives--` without hitting zero) -- refunding the remaining Cinghiale/Acciaio cooldown
    every time the player died. `resetActors` now only clears `G.st` to `null` on a real new
    game/girone reset; on a life-loss respawn (`keep=true`) it cancels any active ability
    (`on:false`) but carries the existing `cd` over. Verified: seeding `G.st.cd=17` before
    `resetActors(true)` leaves `cd===17` after; a plain `resetActors()` (new game/girone) still
    clears `G.st` to `null` as before.
  - **Big maps appear more often after level 10**: `pickMap()` picked uniformly across all of
    `MAPS` once unlocked (5 standard + 10 big = 15), so the 10 big maps only got their plain
    10/15 (~67%) share. Now explicitly rolls a 75% chance to draw from the big-map pool and 25%
    from the standard pool once the level-10 achievement (`g4`) is unlocked; locked players are
    unaffected (still `STDMAPS`-only). Verified over 20000 draws: ~74.9% landed on a big map
    (previously ~67% naturally), and a locked run never went past index 4.
  - Verified with a headless Chrome probe (Playwright, system Chrome) exercising all three
    functions directly with mocked `G`/`S` state and stubbed `startGamblador`/`miniInterlude`/
    `bjPrice`, rather than a full playthrough. Not tested: real device/touch, in-game feel review
    by the owner (these are tuning numbers -- a judgment call, not a fixed spec, so further
    adjustment after playtesting is expected). `node --check` passes both inline `<script>`
    blocks. No save-data shape changed.

## 0.2_46 — 2026-09-23
- Owner playtested 0.2_45 and asked for two corrections plus a real bug found along the way:
  - **Trasformati was showing from girone 1**: `abilOn()` only checked the persistent
    `S.p.sec` unlock flag, never the *current run's* girone -- so once a player had unlocked
    the secret ability in any past run, the button showed starting from girone 1 of every
    future run. `abilOn()` now also requires `G.stage>=7` in the current run (dev mode still
    bypasses both checks, for testing). The unlock trigger itself (in the girone-clear handler)
    moved from `G.stage>=6` to `G.stage>=7` to match. `S.p.sec` itself is untouched by this --
    it's per-save player data, was never reset by a new run, and still isn't; only the
    per-run *display* gate changed. Updated the dev "Salta al girone" panel's girone-6 jump
    button to girone 7 to match (id `jg6`→`jg7`), including its label/description.
  - **El Gamblador reverted to guaranteed-at-5, rare after**: 0.2_45's every-3-gironi/75%
    checkpoint scheme was more aggressive than wanted. `bjAfterClear()` is back to a guaranteed
    table at girone 5, then a flat 15% chance every girone after (no more checkpoint/score
    scaling) -- the every-5-gironi `miniInterlude()` pacing beat when gambling doesn't trigger
    is unchanged from before 0.2_45.
  - Verified with a headless Chrome probe: `abilOn()` is false for every stage/sec combination
    except `stage>=7 && sec` (or `dev:true`, which bypasses both); the unlock simulation fires
    exactly on the girone 6→7 transition and not on 5→6; `bjAfterClear()` hits girone 5 at
    100%, gironi 3-4 at 0%, and gironi 6/7/10/15 at ~15% each over 6000 trials/stage.
  - Not tested: real device/touch, in-game review by the owner. `node --check` passes both
    inline `<script>` blocks. No save-data shape changed.

## 0.2_47 — 2026-09-23
- **Chunk 8 — movesets**: 20-move learnset spread over levels 1-100 for the professor
  mini-game's battle profiles, scoped to just the 70 hand-authored `PB_DATA` entries (25
  aircraft + 10 rocks per character) per the owner's call -- not the `pbGen()` fallback used
  for arbitrary dev-added extra assets, which keeps its original 2-move generated kit.
  - Owner chose the deterministic/procedural option over hand-authoring ~1400 entries: a new
    `pbLearnset(ck,kind,idx)` reuses `pbGen()`'s hash-seeded technique to pick the extra moves
    from the existing ~50-move `PB_LIB`, biased towards the profile's own type(s) (STAB) first
    and falling back to off-type moves (mostly Normal-type utility/status moves, since `PB_LIB`
    has the most coverage there) once a type's pool runs out.
  - Both signature moves and the profile's original 2 preferred library moves are pinned to
    level ≤5 (`sig0`/`lib0` at 1, `sig1`/`lib1` at 5) -- at or below `pbFoeLevel`'s minimum
    possible value (5) -- so the moveset only ever *adds* moves at higher levels; the kit a
    matchup uses today can't shrink once a future chunk wires level-gating in. The remaining 16
    moves spread evenly from level 10 to 100.
  - **Pure data, no behaviour change**: `pbMon()` (what the battle engine actually uses) is
    untouched and still builds the fixed 4-move kit from `sigs`+`lib` exactly as before --
    confirmed identical move names/count before and after this change. Exposing the learnset in
    the engine/move menu is a separate, not-yet-started chunk (backlog's "chunk 9").
  - Verified with a headless Chrome probe: all 70 real profiles (roccia plane/rock, algidone
    plane/rock) produce exactly 20 entries with non-decreasing levels in 1-100, no duplicate
    move names within a learnset, and every slot resolves to a real move object; an
    out-of-range index (past the real profile lists, i.e. `pbGen()` territory) correctly
    returns `null`; a sample learnset was eyeballed for thematic sense (a NOR/FLY plane's
    learnset leads with FLY/FIG moves, fills the midgame with NOR utility moves, and closes
    with varied off-type flavor moves at the top end).
  - Not tested: real device/touch, in-game review by the owner (there's no player-visible
    surface yet -- this data isn't read by anything the player can reach). `node --check`
    passes both inline `<script>` blocks. No save-data shape changed.

## 0.2_48 — 2026-09-23
- **Chunk 9 — level-gated moves**: wires chunk 8's learnset data into the battle engine.
  `pbMon()` now builds a fighter's actual battle-usable moves via a new `pbKnownMoves()`
  instead of always using the fixed `sigs`+`lib` kit directly.
  - The move-select box (`#pbmv`) is a hardcoded 4-row CSS grid (`grid-template-rows:repeat(4,1fr)`,
    classic Game Boy-style layout) and a fighter can have up to 20 moves unlocked by level 100 --
    asked the owner how to reconcile that, and per their call, kept the box at exactly 4 slots
    (zero UI/CSS changes) rather than reworking it into a scrollable list. A fighter's usable kit
    is always its 4 *highest-level* learnset moves at or below its current level; older moves get
    replaced as it levels up, same default behavior as Pokemon without a move relearner.
  - Both signature moves and the original 2 preferred library moves are still pinned to level ≤5
    (chunk 8), which is `pbFoeLevel`'s minimum possible value -- so at the lowest real level (5)
    the known-move set is exactly the old fixed 4-move kit (verified as an exact set match), and
    every matchup only ever *gains* access to different/more advanced moves as it levels up, never
    loses the ability to fight.
  - `pbGen()` placeholder profiles (dev-added extra assets, outside chunk 8's scope) have no
    learnset (`pbLearnset()` returns `null` for them), so `pbKnownMoves()` falls back to the
    original fixed `sigs`+`lib` kit for them, unchanged.
  - Verified with a headless Chrome probe: level 5 known-moves match the legacy fixed kit as a
    set; every real level (5 and up, matching `pbFoeLevel`'s actual range) always yields exactly
    4 moves; level 100 includes newly-learned moves beyond the original 4; placeholder profiles
    are byte-for-byte unchanged; `pbMatch()` builds cleanly across a level spread (5/22/51/100);
    a full headless `pbBattle`/`pbAI`/`pbTurn` fight runs to completion with no errors. Also ran
    `pbSim()` (the existing balance simulator) across all 250 rock×plane pairs per character:
    win rate lands at 56.8% (roccia) / 53.4% (algidone), close to the ~59%/58% documented after
    the last balance pass -- a modest dip worth another dedicated balance pass later, but not a
    regression severe enough to block this chunk.
  - Not tested: real device/touch, in-game review by the owner (first chunk where the learnset
    is actually player-reachable -- worth a firsthand look at how the kit evolves across a real
    playthrough). `node --check` passes both inline `<script>` blocks. No save-data shape
    changed.

## 0.2_49 — 2026-09-23
- **Night-street cutscene revamp** (the "Roccia no" club-ejection scene, `prThrowOut`/
  `prSceneKick`): replaced every procedurally-drawn element with real art cropped from the
  owner's new reference sheets in `refs/` (`punto snai.png`, `moon.png`, `pond.png`,
  `additional assets.png`), plus rain and a reworked throw arc. New `tools/cut_scene_assets.py`
  (same flood-fill + tight-trim approach as `tools/cut_sprites.py`, plus a small/thin-component
  filter for the sheets' crosshair grid-guide lines) produced the 8 cleaned, palette-reduced
  PNGs now in `refs/cut/scene/` and embedded as `PRSCN`/`PRSCNIMG` (lazy-loaded alongside
  `PRIMG` in `prRender`, ~31KB total added to the build).
  - **Building**: "Option B" from the club sheet, standing on the ground line on the left,
    sized as a fraction of the canvas (`prClubRect`) so it holds at any screen size. Its exit
    point is `CLUB_DOOR_XF`/`CLUB_DOOR_YF` (fractions of the sprite, since this scene has no
    fixed pixel grid) resolved per-frame by `prClubDoor(W,H)` -- the one thing chunk 5's throw
    arc depends on.
  - **Moon**: reference option 2 (cream, cratered), same spot, with a soft translucent radial
    glow blending into the sky gradient.
  - **Puddle**: reference option 2 (muddy rim, cigarette butts) via `prPuddleRect`, to the
    right of the building where the player lands.
  - **Splash**: rather than faking multiple frames out of the single crown-splash reference
    (option 5), animated it in code -- a scale/fade envelope (rise 0-.16s, fall .16-.55s) layered
    under the existing procedural ripple-rings and flying-drop code, which already carried the
    settle. No new frame data needed.
  - **Street props**: 4 of the suggested items (#2 rusty trash can, #14 velvet rope post, #18
    tyre, #20 fast-food rubbish) from the props sheet, laid out by `prPropSpots` -- rope post by
    the door, the rest clustered past the puddle -- clear of the door, the puddle and the throw
    arc between them.
  - **Player thrown out**: the toss trajectory now runs `prClubDoor(W,H)` -> `prPuddleRect(W,H)`
    instead of the old fixed fractions, so it still lands correctly if the building/puddle
    layout or screen size changes. Still reads the character through the existing
    `prPlayerCv()` (never hardcoded -- draws whichever of Uomo roccia/Algidone is selected).
  - **Rain + sound**: `prDrawRain` draws 3 parallax streak layers (46 short lines/frame total)
    with tiny drip splashes at the ground line, overlaid whenever the outdoor background is
    drawn (toss/splash phases -- the walk phase is still indoors in `prBgHall`). `prRainStart`/
    `prRainStop` loop filtered white noise via Web Audio (bandpass + lowpass, gain fade in/out),
    started at the very beginning of `prThrowOut` (so it's audible faintly through the door
    before the player is even outside) and faded out at the end; also stopped from `prCleanup`
    if the scene is abandoned mid-cutscene (dev "Esci dalla prova"). Respects `S.opts.sound`
    like the rest of the game's audio; the existing `prSplash()` impact sound is unchanged.
  - Verified with a headless Chrome probe (Playwright, system Chrome) running the full
    `prTestKick()` cutscene to completion with no runtime errors, screenshotted at 5 points
    (walk/toss/splash-rise/splash-fall/settle) for both characters and at both a phone-portrait
    viewport (390×780) and a wide desktop one (1100×700, exercising the scaled 480px column);
    building/moon/puddle/props/splash/rain and the door-to-puddle arc all rendered correctly in
    every case. Also spot-checked frame pacing during the rain-heavy settle phase (~144fps in
    headless Chrome, no stalls).
  - Guessed/adapted from the brief: `CLUB_DOOR_X`/`CLUB_DOOR_Y` became `CLUB_DOOR_XF`/
    `CLUB_DOOR_YF` (fractions, not literal pixels) since this scene already sizes everything by
    canvas fraction rather than a fixed pixel grid; door position within the sprite (62%
    across, 74% down, between the two lit glass panels) and prop placement were eyeballed
    against the reference art rather than specified. `refs/betting_shop`, `refs/moon`,
    `refs/pond` and `refs/README_assets.md` mentioned in the brief as prior guide art don't
    exist in this repo (only the new sheets do), so nothing there was consulted or removed.
  - Not tested: real device/touch input, in-game review by the owner. `node --check` passes
    both inline `<script>` blocks. No save-data shape changed.

## 0.2_50 — 2026-09-23
- Owner reviewed 0.2_49 and asked for a layout pass: the club building read as "barely visible"
  and the 3 non-door props were scattered randomly.
  - **Building scaled up**: `prClubRect` was sizing the sprite off width (42% of the canvas)
    with height following the sprite's own aspect ratio -- on the portrait-ish canvas this game
    actually runs at, that made the *height* tiny (well under the old placeholder block's
    `H*.5`), which is what read as "barely visible" even though the width looked reasonable.
    Now sized at 55% of canvas width (up from 42%), which reads clearly larger at any aspect
    ratio since it's the dominant dimension here.
  - **Ground strip shrunk**: the plain sidewalk band below the scene dropped from 28% to 16% of
    the canvas height (new `GROUND_YF=.84`, was an inline `.72`), freeing vertical room so the
    bigger building doesn't crowd the sky/moon.
  - **Puddle and props repositioned**: `prPuddleRect` now sits in the outer part of whatever
    width is actually left over past the building (`avail=W-clubWidth`), instead of a fixed
    `W*.66` that could land under the (now bigger) building. `prPropSpots` places the tyre/
    trash/food cluster inside that same leftover gap (at 28%/60%/86% across it) instead of
    always past the puddle; the rope post stays on the building's own footprint next to the
    door. This removes the width-budgeting bug in the first attempt at this same fix, where the
    computed prop gap collapsed to ~0px and all three props landed on top of each other.
  - Verified with a headless Chrome probe: dumped `prClubRect`/`prPuddleRect`/`prClubDoor`/
    `prPropSpots`' actual computed pixel rects for both a phone-portrait (390×780) and a wide
    (1100×700 -> 480-column) canvas and confirmed no overlap between the building, puddle and
    props in either case; re-ran the same 5-screenshot, both-characters visual check as 0.2_49
    to confirm the building, moon, puddle, splash, props, rain and the door-to-puddle throw arc
    still all render correctly at the new sizes/positions.
  - Not tested: real device/touch, in-game review by the owner. `node --check` passes both
    inline `<script>` blocks. No save-data shape changed.

## 0.2_51 — 2026-09-23
- Owner: still too small, "asset details are not visible" -- scale the club building up 50%
  more and crop at least 30% off its left margin; resize everything else to match.
  - **Re-cropped the source asset**: `tools/cut_scene_assets.py`'s club crop box now starts
    ~35% further right in the reference sheet, dropping the plain facade + the horse/jockey
    window (the least legible part of the sprite at in-game size) so the CLUB sign and the SNAI
    runner window -- the parts that actually read -- fill more of the same draw width. New
    native aspect 145:150 (was 209:150), re-embedded via the same `refs/cut/scene/` ->
    `PRSCN` pipeline as 0.2_49.
  - **Render width up 50%**: `prClubRect` now draws at 82.5% of canvas width (55% × 1.5, was
    55%). Combined with the narrower crop this makes the sign/doors noticeably bigger rather
    than just filling more of the same small render.
  - **Moon bigger too**: diameter up from 13% to 19% of canvas width (~1.5×).
  - **Puddle and props resized to fit what's left**: a building at 82.5% width leaves very
    little room on a narrow phone, so `prPuddleRect` now guarantees a non-overlapping position
    (`cr.w+pw/2+margin`, not just "centered in leftover space" -- that formula let the puddle
    sit *under* the building once the building got this big) at a modestly bigger fixed size
    (27% of canvas width, was 24%). `prPropSpots` clamps the tyre/trash/food cluster into
    whatever gap is actually left between the building and the puddle (`at(f) = gapL + (gapR-
    gapL)*f`) rather than fixed canvas fractions that could land past either edge -- on a
    narrow phone that gap is only a few pixels wider than the icons themselves, so the three
    end up close together as one small pile rather than spread out; still clear of the door,
    the puddle's main body and the throw arc.
  - Verified with a headless Chrome probe: dumped the actual computed pixel rects for a phone
    (390×780) and a wide (1100×700 -> 480-column) canvas and confirmed the building and puddle
    no longer overlap (the bug in the first attempt at "bigger building" last version) at
    either size; re-ran the same 5-screenshot, both-characters visual check -- CLUB sign and
    SNAI window are now clearly legible at both sizes, the door-to-puddle throw arc and splash
    still land correctly on the smaller puddle.
  - Not tested: real device/touch, in-game review by the owner. `node --check` passes both
    inline `<script>` blocks. No save-data shape changed.

## 0.2_52 — 2026-09-23
- Owner: proportions are fine now, but drop the loose props (they read as randomly scattered),
  use a higher-resolution club asset, move the puddle fully back on screen, and let the
  building itself bleed off the left edge for more room.
  - **Dropped the tyre/trash/food cluster**: `prPropSpots` now only returns the rope post by
    the door; the three-prop "pile" from 0.2_51 (which only existed because there wasn't
    enough room to spread them out) is gone rather than kept awkward. Removed the now-unused
    `prop_trashcan.png`/`prop_tyre.png`/`prop_food.png` from `refs/cut/scene/`, the extraction
    tool, and the `PRSCN` embed (was dead weight in the build once nothing drew them).
  - **Club asset at much higher quality**: `tools/cut_scene_assets.py`'s club pixelization went
    from `target_h=150, colors=32` to `target_h=300, colors=96` -- close to the source crop's
    own 330px resolution and a much bigger palette, so the neon text and the SNAI runner figure
    are crisp instead of blocky/muddy at this size. Every other asset here stays at its original
    small pixel-art scale; this one asset is the exception, per the owner's call.
  - **Building anchored 30% off the left edge**: `prClubRect` draws at `x:-bw*.3` instead of
    `x:0`, so only ~70% of its (still 82.5%-of-canvas-wide) render actually shows on screen.
    Same on-screen sign/door size as 0.2_51, but the building's visible right edge moves from
    ~82.5% of the canvas to ~57.75%, freeing real room for the puddle.
  - **Puddle moved fully back on screen**: `prPuddleRect` now sizes and centers itself within
    that freed room (`visRight` to the canvas edge) instead of the fixed-size, edge-clamped
    version from 0.2_51 that ran past the right edge on both screen sizes tested. It's bigger
    than before (up to 34% of canvas width) and fits with margin on both a phone and a wide
    canvas.
  - Verified with a headless Chrome probe: dumped `prClubRect`/`prPuddleRect`'s computed pixel
    rects for a phone (390×780) and a wide (1100×700 -> 480-column) canvas -- confirmed the
    puddle is now fully within `[0,W]` with margin on both sides at both sizes (previously it
    ran 60-94px past the right edge); re-ran the same 5-screenshot, both-characters visual
    check -- the building's left crop reads naturally as "part of the frame", the CLUB sign/
    SNAI window are sharp, no loose props, and the puddle (plus the door-to-puddle throw arc
    and splash) is fully visible.
  - Not tested: real device/touch, in-game review by the owner. `node --check` passes both
    inline `<script>` blocks. No save-data shape changed.

## 0.2_53 — 2026-09-23
- Owner: scale the building up another 30%, reduce how much disappears off the left edge from
  30% to 10%, drop the rope post too, and recalibrate the throw animation to match.
  - **Building bigger again**: `prClubRect`'s draw width went from 82.5% to 107.25% of the
    canvas (`× 1.3`), and the left-edge crop from 30% to 10% (`x:-bw*.1`, was `-bw*.3`) -- the
    full "CLUB" word is now on screen (was cropped to "UB" before) at a noticeably bigger size.
  - **Rope post removed**: `prPropSpots` is gone entirely along with its call site in
    `prBgOut`; there are no street props left in the scene at all now. Cleaned the asset out of
    `tools/cut_scene_assets.py` and the `PRSCN` embed the same way the tyre/trash/food cluster
    was removed in 0.2_52.
  - **Puddle recalibrated, with a floor**: at this building size there's very little canvas
    width left over (as little as ~14px on a narrow phone), so `prPuddleRect`'s existing
    "fit whatever room is left" formula would have shrunk it to almost nothing. Added a
    `Math.max(W*.14, ...)` floor so it stays a small but visible puddle instead of vanishing --
    it now runs slightly past the right edge on both screen sizes tested (~20-25px), which is
    the trade-off of prioritizing the building at this size on a narrow canvas.
  - **Throw animation**: no changes needed -- `prClubDoor`/the toss trajectory in `prSceneKick`
    already read `prClubRect`/`prPuddleRect` live each frame, so the door position and the arc
    endpoint recalculated automatically from the new building/puddle rects.
  - Verified with a headless Chrome probe: dumped `prClubRect`/`prPuddleRect`/`prClubDoor`'s
    computed pixel rects for a phone (390×780) and a wide (1100×700 -> 480-column) canvas;
    re-ran the same 5-screenshot, both-characters visual check -- the full CLUB sign and SNAI
    window are large and sharp, the throw arc still starts at the door and lands in the puddle,
    and the splash still plays correctly on the smaller puddle.
  - Flagging for the owner: the puddle is now quite small and clips slightly past the right
    edge on a narrow phone -- worth a look to confirm this trade-off (bigger building vs.
    smaller/partially-clipped puddle) is what's wanted before going further in this direction.
  - Not tested: real device/touch, in-game review by the owner. `node --check` passes both
    inline `<script>` blocks. No save-data shape changed.

## 0.2_54 — 2026-09-23
- Owner: keep the building's size/proportions as they are, move it 15% further into the left
  margin, and resize the puddle so it fits nicely.
  - **Left crop 10% → 15%**: `prClubRect`'s draw width is untouched (still 107.25% of the
    canvas); only `x` changed from `-bw*.1` to `-bw*.15`, so 85% of the sprite shows instead of
    90%. This frees a little more room on the right without shrinking the building at all.
  - **Puddle rebuilt to fit the room, not sized independently then clipped**: 0.2_53's
    `prPuddleRect` picked a size first (with a floor so it wouldn't vanish) and only then
    checked it against the available space -- worked out to running 38-47px past the canvas
    edge, or briefly *overlapping the building* before a follow-up fix in the same session. The
    formula is rewritten to size the puddle from the room actually available
    (`avail = W - visibleBuildingRight`) minus a small margin on each side, so by construction
    it sits fully on screen next to the building rather than needing to be clamped afterward.
    It's necessarily small given how much of the canvas the building now covers -- flagged
    below.
  - Verified with a headless Chrome probe: dumped `prClubRect`/`prPuddleRect`'s computed pixel
    rects for a phone (390×780) and a wide (1100×700 -> 480-column) canvas and confirmed the
    puddle no longer overlaps the building and stays within (or very close to) `[0,W]` at both
    sizes; re-ran the same 5-screenshot, both-characters visual check -- building crop/size
    unchanged as intended, puddle is fully visible (or clipped by only a few px on the phone
    size) rather than mostly off-canvas.
  - Flagging for the owner again: even sized to fit, the puddle reads quite small at this
    building size -- there just isn't much canvas width left over once the building covers
    ~85-90% of it. If it should read as more prominent, the building's draw width itself
    (currently 107.25% of canvas, `prClubRect`) is the lever to pull, since "keep it this big
    and also make the puddle bigger" isn't geometrically possible on a narrow phone.
  - Not tested: real device/touch, in-game review by the owner. `node --check` passes both
    inline `<script>` blocks. No save-data shape changed.

## 0.2_55 — 2026-09-23
- Owner gave a concrete crop target this time (previous attempts were percentage guesses):
  move the building left until the left door is half cut off, so the puddle has real room and
  can be fully visible; scale down the thrown-character animation to match if needed.
  - **Crop point measured directly off the asset**: found the left door panel's pixel bounds on
    the 291×300 `club_b.png` (roughly x=48-100, center x=74) and set a new `CLUB_CROP_XF=74/291`
    (~25.4%) used as the left-edge fraction in `prClubRect`, replacing the arbitrary 15% from
    0.2_54. Building's own size is untouched, same as every version since 0.2_53.
  - **Puddle now fully on screen**: with the extra room this crop frees up (~20% of canvas
    width vs. ~9% before), `prPuddleRect`'s existing "fill the available room with a margin"
    formula (from 0.2_54, unchanged in shape) now produces a puddle that fits with margin on
    both sides at every size tested, instead of needing the floor that caused clipping before.
    Added an upper cap (`Math.min(W*.3, ...)`) so it can't overgrow if a lot of room ever opens
    up.
  - **Thrown-character size now follows the puddle**: was a flat `Math.min(W*.28,120)` that
    dwarfed the smaller puddle from 0.2_53/54; now `Math.min(pr.w*1.4, W*.28)`, so it scales
    with whatever the puddle's actual size is instead of needing separate manual tuning next
    time the puddle changes.
  - Verified with a headless Chrome probe: dumped `prClubRect`/`prPuddleRect`'s computed pixel
    rects for a phone (390×780) and a wide (1100×700 -> 480-column) canvas -- puddle is fully
    within `[0,W]` with ~10-12px margin on both sides at both sizes, no overlap with the
    building; re-ran the same 5-screenshot, both-characters visual check -- the left door panel
    reads as roughly half-cut (its icon and "Vincendo/Benvenuti" text are visibly split), the
    right door and SNAI/runner window are fully visible, the puddle is clearly readable (not a
    speck) with no clipping, and the smaller thrown character reads as proportioned to it
    through the toss and splash.
  - Not tested: real device/touch, in-game review by the owner. `node --check` passes both
    inline `<script>` blocks. No save-data shape changed.

## 0.2_56 — 2026-09-23
- Owner's last request for this cutscene revamp before handing off: double the puddle size,
  move it left so it stays fully on screen, and stop the thrown character from fading away --
  it should settle half-submerged and stay that way.
  - **Puddle doubled**: `prPuddleRect` now takes the same "fit the leftover gap" size as 0.2_55
    and doubles it (`pw=base*2`). At that size it no longer fits in the gap without also
    running off the right edge, so its position is clamped to stay fully within `[0,W]`
    (shifting left, over part of the building's footprint, rather than off the canvas) --
    exactly the "move it left so it doesn't cut outside the setting" ask. Visually the overlap
    with the building reads fine since the building's own art has empty facade space there and
    the puddle draws on top.
  - **Character stops disappearing**: the splash-phase draw had an unbounded downward drift
    (`pr.cy+t*70`, kept moving for the whole 2s phase) and a fade to `alpha:0` over 0.8s -- the
    character fully vanished well before the scene ends. Replaced with a capped sink
    (`Math.min(t,.35)*46`, settles after a third of a second and holds) and no fade at all; a
    clip rect at the character's own vertical centre keeps exactly its top half visible for the
    rest of the phase, reading as "lying half-in the puddle" instead of sinking away.
  - Verified with a headless Chrome probe: dumped `prPuddleRect`'s computed pixel rect for a
    phone (390×780) and a wide (1100×700 -> 480-column) canvas -- confirmed it stays within
    `[0,W]` with margin at both sizes even at double size; re-ran the same 5-screenshot,
    both-characters visual check -- puddle is clearly bigger and fully visible with no edge
    clipping at either size, and at the settle frame both Uomo roccia and Algidone are still
    visible half-in the puddle (not faded out) with a believable "sitting in it" read.
  - **Chunks remaining before the v0.3 milestone** (see `CLAUDE.md` §8 for the full detail;
    listed here so the next session picks up cleanly):
    - Chunks 4+5 (pub sprite, dirty-pond sprite+splash) -- **superseded**: this whole cutscene
      revamp (0.2_49-0.2_56) already replaced the pond/splash placeholder art these chunks were
      originally scoped around with real reference art. Worth re-scoping or closing rather than
      executing as originally written.
    - Chunk 6 (Duskull sprite), Chunk 7 (battle background/layout rework), and the professor-
      sprite-shadow bugfix all still need reference art/screenshots from the owner before they
      can be executed -- none were provided this session.
    - Movepicker (choose equipped moves out of the 20-move learnset, menu or pre-battle) --
      raised by the owner 2026-09-23, not yet broken into approved chunks.
    - Rebalance simulation pass for the professor fight -- `pbSim()` win rate sits at 56.8%
      (roccia) / 53.4% (algidone) as of 0.2_48, down from the ~59%/58% documented after the
      last balance pass; not yet scheduled.
    - Ability balancing (8s active / 25s cooldown for Cinghiale/Acciaio) -- deferred, no owner
      direction yet on target numbers.
    - Audio pending from the owner: a better-fitting intro track (current one was cut in half
      and looped).
    - Later-phase items untouched this session: B/C "Esporta modifiche" (export UI + validation
      pass), D/E Firebase login + cloud save (owner's console setup, **D**, must happen before
      any in-game work, **E**).
  - Not tested: real device/touch, in-game review by the owner. `node --check` passes both
    inline `<script>` blocks. No save-data shape changed.

## 0.2_57 — 2026-09-23
- **Chunk 6 — real Duskull sprite**: the professor's "sending out" cutscene (`prSceneProf`,
  triggered from `prSendOut`) drew a small procedurally-generated placeholder ghost. Replaced it
  with the owner-supplied `refs/duskull.png` reference (post-pokéball appearance):
  - Reference was a pixel-art render over a baked-in checkerboard (not real alpha — the PNG's own
    alpha channel was fully opaque). Keyed the checker out with a border-seeded flood fill
    (tolerant of the two checker grays, careful not to eat the skull's similarly-pale cream color
    since that's a distinct hue), cropped to content, downscaled 3× with nearest-neighbour to a
    native pixel-art resolution (120×110), and quantized to a 48-colour palette — final asset is
    ~4.6 KB before base64.
  - Added as a new `"dusk"` entry in `PRSPR` (loaded automatically through the existing
    `prLoadImgs()`/`PRIMG` pipeline, no loader changes needed). `prDuskCv()` now returns
    `PRIMG.dusk[0]` instead of drawing pixels by hand; the white "materializing" silhouette is
    still derived at runtime via `source-in` compositing, unchanged. Removed the ~14 lines of
    procedural skull-drawing code.
  - Draw call in `prSceneProf` switched from `scale()` + fixed `-20,-22` offsets (tuned for the
    old 40×44 canvas) to explicit destination width/height centred on the anchor, so the new
    120px-wide source image renders at the same on-screen size and position the placeholder used;
    guarded against the frame being drawn before the image finishes loading.
  - Verified with a headless Chromium probe (`prTest()` → advance dialogue → pick "Sì" → wait for
    `PR.sc.dusk`): screenshotted the emerge animation mid-materialize and fully-formed — sprite
    renders at the right size/position with the purple glow and white-flash fade both intact.
- **Professor-sprite shadow bugfix** (found while QA-ing the above, not blocked on new reference
  after all): the owner-supplied `refs/duskull.png` and `refs/UI_emerald.png` were provided for
  chunks 6/7 only, but reviewing the emerge cutscene surfaced the actual shape of the long-flagged
  "shadow" bug well enough to fix without further reference art.
  - Root cause: extracting `PRSPR.idle`/`PRSPR.walk` from the source photo (background removal +
    convex-hull fill, per CLAUDE.md §2) left a warm reddish-brown blob filling the gap between the
    legs on every full-body frame — fully *opaque* (not a transparent hole connected to the
    background), so it reads as a leftover ground shadow baked into the sprite rather than a
    render-time drop shadow. Confirmed by extracting and upscaling the embedded frames; not
    present in the bust-only frames (`blink`/`angry`/`point`/`shoo`), which have no legs.
  - Fixed by inpainting: for each `idle`/`walk` frame, flagged pixels in the lower half (legs
    only — hair, face and hands are never touched, both by color heuristic and a hard y-cutoff)
    whose color reads as that warm brown rather than the suit's navy, then iteratively replaced
    each with the most common color among its already-fixed opaque neighbours (mode, not a blended
    average, so the palette stays the small flat-color set the rest of the art uses) until the
    patch was gone. Re-encoded as indexed-palette PNGs with a single transparent index (alpha in
    these sprites is binary, no antialiasing) to match the original encoding — net size change for
    all 16 fixed frames combined was about −1.4 KB, not the +25 KB a naive RGBA re-save produced
    first.
  - Verified visually: upscaled every `idle` frame and all affected `walk` frames before/after —
    gap now reads as ordinary inner-thigh trouser shading, no residual off-color patch; a headless
    probe re-rendered the intro dialogue and walk/kick cutscene to confirm nothing else regressed.
- Not tested: real device/touch, in-game review by the owner. `node --check` passes both inline
  `<script>` blocks. No save-data shape changed; no new `DEF`/migration fields needed.

## 0.2_58 — 2026-09-23
- **Chunk 7 — battle screen visual rework**, readapted from `refs/UI_emerald.png`. The existing
  layout already matched Emerald's *structure* (foe box top-left, own box bottom-right above the
  message panel, foe smaller/upper-right on a distant platform, own bigger/lower-left and closer)
  so this was a polish pass on top of that structure rather than a rebuild:
  - `pbBg`: sky gradient softened toward the horizon (was a flat two-stop blue/white), grass
    recolored more saturated, and the random speckle "grass blade" dashes replaced with a banded
    checkerboard dither (alternating tinted cells in 4-row bands) closer to the actual GBA
    battle-background dither look.
  - `pbPlat`: platform ellipses recolored to a warmer sandy/khaki palette and given a thin dark
    rim stroke for a crisper cel-shaded edge, instead of the previous soft brown gradient blob.
  - `.pbbox` (the HP nameplates): border recolored to a dark olive-green (was slate gray),
    background warmed toward parchment cream, and added a small triangular "tail" (`:after`,
    mirrored between the two boxes) pointing down-and-toward its combatant — the speech-bubble
    notch Emerald's own HP boxes have. HP bar fill and housing given a two-tone gradient (light
    top edge, darker bottom) for a beveled look instead of flat color.
  - `pbLayout`: combatant/platform size now also scales with the available field height
    (`sh`, not just canvas width), with the size ceiling raised — so on a tall phone or a
    desktop-scaled window the field actually uses the extra room instead of just leaving more
    empty grass around the same small sprites. Mobile-portrait sizing is unaffected (still
    width-gated there); verified the size increase kicks in on a 1280×820 and a 400×900 viewport
    without breaking the HUD layout.
  - Left the position/HP-box/message-panel structure itself alone — it was already the right
    shape for Emerald's layout, so this stayed a recolor/redraw pass, not a rearrange.
- Verified with a headless Chromium probe (`prTestBattle`) across four viewports (480×800,
  1280×820, 400×900, plus the original baseline) and through the command screen, move-select
  panel and a mid-animation attack impact frame — all read correctly with the new theme, no
  layout breakage.
- Not tested: real device/touch, in-game review by the owner. `node --check` passes both inline
  `<script>` blocks. No save-data shape changed.

## 0.2_59 — 2026-09-23
- **Professor-battle reward boosted and rerouted into the maze game's active score**. Owner ask:
  boost the win reward by at least +40%, and make it show up as the *active score* in the pac-man
  game when continuing at girone 3, rather than a silent currency top-up.
  - `pbReward(L)`: base multiplier raised from 50 to 70 (a clean ×1.4 on the whole formula, so
    every level gets exactly +40%, e.g. level 5 goes from 96 to 134 sordi).
  - `pbEnding`'s win branch no longer credits `S.p.sordi` immediately. If the player picks "sì" to
    continue at girone 3, the reward is passed as the new run's starting score
    (`startGame(false,{stage:3,score:M.reward})`, `startGame` gained a `opt.score` field) — it
    shows up in the HUD instantly and converts to sordi on its own at the end of that run through
    the normal scoring formula, same as any other points, so it's never double-credited. If the
    player picks "no", the direct sordi credit (+ the `sordi` achievement counter) still happens
    exactly as before, since there's no run left to carry it.
  - Verified with a headless Chromium probe driving a full non-test win (real `prIntro()` flow,
    not `prTestBattle`, since dev-test battles skip the girone-3 question entirely): confirmed
    `G.score` lands on exactly `pbReward(foeLevel)` when continuing, `S.p.sordi` is untouched at
    that moment (no double count), and declining still credits the full reward straight to sordi.
- **Sordi earned from playing the maze game itself reduced by 30%**: `finishRun`'s score→sordi
  conversion (`gain=Math.floor(score*(1-lim)*D.mult)`) now has an extra `*.7` factor. XP and the
  achievement-reward economy are untouched — this only affects the core per-run payout.
- **Dev mode now survives closing/reopening the app.** `role`/`devOn` used to live only in memory
  and reset on every reload, so anyone who'd logged in as a developer had to log back in every
  time. Added a small `mgs_dev` localStorage key (separate from the `mgs_v1` save blob, same
  pattern as the existing `EXP_NAMEKEY` setting) holding `{role,devOn}`; read once at startup,
  written on login, on the dev-mode toggle, on logout, and cleared on "cancella dati locali". Dev
  mode now stays on until the user explicitly logs out or wipes local data, as asked.
  - Verified with a headless probe: set role/devOn, reload the page, confirmed both survive and
    `devUI()` is still true; logged out, reloaded again, confirmed both are cleared.
- Not tested: real device/touch, in-game review by the owner. `node --check` passes both inline
  `<script>` blocks. No save-data schema changes — the new dev-session flag lives outside the
  `mgs_v1` blob, so no `DEF`/migration entry was needed.

## 0.3 — 2026-09-23
- **Version numbering switched from `0.2_NN` to `0.3_NN`**, matching the `v0.3` release/tag cut this
  session. `const VERSION` in `index.html` is bare `"0.3"` for this exact release build; every build
  delivered from here on bumps `0.3_NN` starting at `0.3_1` (the counter resets rather than continuing
  from `_59`) — CLAUDE.md §6 rule 3, the §9 delivery checklist, and the README's example were all
  updated to match.
- No gameplay/engine changes in this entry — purely the version-string and documentation update that
  closes out the `v0.3` release housekeeping (see the `0.2_57`–`0.2_59` entries above for what actually
  shipped in the milestone, and the "docs: reconcile version history..." commit for the CLAUDE.md/README
  cleanup that came just before this).
- Not tested beyond `node --check` on both script blocks (no logic touched). No save-data changes.

## 0.3_1 — 2026-09-23
- **v0.4 bugfix B2 — battle music now starts with the battle transition, not after it.** Previously
  `prBattleStart()` stopped the menu/dialogue music, ran the full 2-second `pbTransition()` sweeping-bars
  animation, and only then started `prMusic("battle",…)` at the top of `pbFight()` — a silent gap for the
  whole transition. `prMusic("battle",{fadeIn:700})` is now called at the very start of `pbTransition()`
  itself (it already crossfades out whatever was playing, so the separate `prMusicStop(700)` call in
  `prBattleStart()` was removed as redundant). `pbFight()` keeps its own `prMusic("battle",…)` call as a
  guard (`if(PRM.slot!=="battle")`) so `prTestBattle()`'s dev quick-battle button — which skips
  `pbTransition()` entirely — still gets battle music at the same point as before.
- Tested: `node --check` passes both inline `<script>` blocks. Not tested: real playback/audio timing in
  a browser, real device/touch, in-game review by the owner. No save-data changes.

## 0.3_2 — 2026-09-23
- **v0.4 bugfix B3 — win/lose track now starts right after the last faint, not after the first
  dialogue line.** In `pbEnding()`, both the win branch (`prMusicStop(400);prMusic("win",{fadeIn:300})`)
  and the lose branch (`prMusicStop(400);prMusic("lose",{fadeIn:300})`) used to fire only after
  `await pbSay(pb_ui_win1/lose1,{wait:true})` had already resolved — i.e. only once the player tapped
  through the first result line, which could be an arbitrary delay after the battle was actually decided.
  Both calls now run first, immediately when `pbEnding()` is entered for that branch, before either
  dialogue line. `PR.test` behaviour (skips the girone-3 question / skips the throw-out animation) and
  the flee (`res.run`) branch are untouched.
- Tested: `node --check` passes both inline `<script>` blocks. Not tested: real playback/audio timing in
  a browser, real device/touch, in-game review by the owner. No save-data changes.
