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

## 0.3_3 — 2026-09-23
- **v0.4 bugfix B4 — "Rocciamon" card (G3) now appears unlocked in Lista desideri › Giochi after the
  first real professor game.** `gamesHTML()` previously only recognised G1 (Mangiaroccia, always on) and
  G2 (El Gamblador, unlocked via `S.p.gam.seen`); every other slot rendered as a permanently locked "???".
  Slot index 2 (G3) is now unlocked when `S.p.pr.seen` is true (or in `SIM()` mode), same pattern as G2 —
  `S.p.pr.seen` is only ever set by a real professor battle (`prBattleStart()`, guarded by `!PR.test`), so
  dev-test battles don't unlock the card. Added a matching canvas icon (reuses the existing `profImg()`
  professor portrait, same draw code already used for the locked "Il Professore" character card) and
  honoured `S.ov["game_2"]` label/colour overrides and the dev-mode card-edit dialog, exactly like G1/G2.
- No new state: reuses the existing `S.p.pr.seen` flag from chunk 1 (0.2_40) — no `DEF`/migration changes.
- Tested: `node --check` passes both inline `<script>` blocks. Not tested: real playback/in-game review by
  the owner, whether the Duskull/pokéball icon (vs. the professor portrait reused here) is what's wanted.

## 0.3_4 — 2026-09-23
- **v0.4 bugfix B1a — real gapless Web Audio loop player, wired to the main menu track.** Confirmed during
  0.3_3 planning that `makeLoopPlayer`, described in older docs as already shipped in 0.2_28→0.2_29, never
  actually existed in the code (`git log --all -S makeLoopPlayer` returns nothing) — `initMusic()`/`bgm` was
  a plain `new Audio(url)` with `.loop=true` the whole time, which is exactly what leaves an audible gap at
  the loop point on MP3 (the owner's reported B1 symptom: "restarts correctly but there's still silence
  right before the loop").
- Added **`trimSilence(buf,thresh,capSec)`**: scans a decoded `AudioBuffer` from both ends across all
  channels for the first/last sample at or above `thresh` (`0.001`), capped at `capSec` (`500ms`) per side
  so a deliberately quiet intro/outro isn't eaten. Verified with a Node stub test (4 synthetic-buffer cases:
  normal head/tail silence, silence longer than the cap, no silence, and an all-silent buffer as a
  degenerate-safety case) — all matched expected trim points.
- Added **`loopTrack(url,{vol,loop})`**: fetches + `decodeAudioData`s the track via the existing `getAC()`,
  plays a single `AudioBufferSourceNode` (→ `GainNode` → destination) with `loop=true` and
  `loopStart`/`loopEnd` set to the trimmed range, so there's exactly one seamless loop point instead of a
  restart. Exposes an `<audio>`-like surface (`play()` returning a Promise, `pause()`, a `volume`
  getter/setter mapped to the gain, `paused`, and a `currentTime=0` setter for the existing "restart from
  the top" call site) so every `bgm.*` call site needed no changes beyond `initMusic()` itself. `pause()`
  remembers position (modulo the loop range) and `play()` resumes from it, matching `<audio>`'s behaviour.
  Falls back to plain `new Audio(url)` + `loop=true` if there's no `AudioContext` or decoding throws. The
  decoded buffer is cached per URL, so switching screens doesn't re-decode; loading a custom "menuMusic"
  IndexedDB override or resetting to the built-in track both still go through `initMusic()` → a fresh
  `loopTrack`, so the override path is unaffected.
- Swapped only `initMusic()`/`bgm`. `syncMusic()`, the periodic `bgm.paused` watchdog, the
  `visibilitychange` handler, and the dev-panel "▶ preview" / "restart" buttons all kept working unchanged
  against the new object's `<audio>`-like surface.
- **Trimmed silence amounts are not known from this session** — there's no `decodeAudioData` outside a real
  browser (no `ffmpeg`/`ffprobe` available here to cross-check offline), so the actual head/tail trim for
  the embedded `MUSIC_B64` track and any custom-uploaded menu track can only be measured live. Added a
  `window.__mgsAudioDebug` flag: when set truthy in the browser console before the track first plays,
  `loopTrack` logs the trimmed head/tail ms via `console.debug`. **Ask the owner to check the console with
  that flag set** to get the real numbers for this track.
- Not tested: real playback/loop-point audio in a browser, real device. **iOS flag for the owner**: Web
  Audio (`AudioContext`) is muted by the hardware silent switch, whereas HTML `<audio>` was not — this is a
  behaviour change on iPhone specifically and should be checked there.
- Docs: corrected CLAUDE.md §4's Audio line and the §7 `0.2_28 → 0.2_29` row, which both incorrectly stated
  the loop player already shipped in that range under the name `makeLoopPlayer`.

## 0.3_5 — 2026-09-23
- **v0.4 bugfix B1a-fix — `loopTrack().play()` is now idempotent (fixes a real bug found in review of
  0.3_4).** `<audio>.play()` on an already-playing element is a no-op; the 0.3_4 `loopTrack()` did not
  match that — every call created a **new** `AudioBufferSourceNode` and overwrote `st.src`, orphaning
  whatever was already playing (it kept sounding and could never be reached to stop). This was live and
  reachable: `syncMusic()` calls `bgm.play()` on every screen change within menu/wish/opt/dev, and the
  dev-panel restart button does `currentTime=0` (which itself replayed) immediately followed by another
  `.play()` call — two stacking, un-stoppable copies of the menu track per press. Same race if two
  `play()` calls overlapped while the buffer was still mid-decode.
- Fix: added a play token (`st.tk`) and an in-flight flag (`st.pending`). `play()` now no-ops immediately
  if already playing or already starting; otherwise it claims a token and re-checks `st.paused` and the
  token **after every `await`** (buffer decode, `ac.resume()`) before creating a source, so a `pause()` or
  a newer `play()`/`currentTime=0` that happened while waiting cancels the stale attempt instead of letting
  it finish and orphan a source. `startSource()` also stops any existing `st.src` immediately before
  creating a new one, as a second, unconditional guard. `pause()` bumps the token too, so nothing pending
  can complete after a pause. Added `get currentTime()` for `<audio>` parity, and fixed position-tracking
  math (`capturePos()` now re-bases its elapsed-time origin on every read, so repeated reads while playing
  no longer double-count elapsed time — a bug the fix introduced and caught while writing it).
  `currentTime=0` now restarts exactly once (stop the live source, `pos=0`, replay if not paused); the
  dev-panel restart button's own trailing `.play()` call correctly becomes a no-op against the guard above,
  matching what real `<audio>` already did.
- **Verified in headless Chromium** (Playwright, `sync_playwright`, matching the `probe.py` pattern from
  earlier builds): wrapped `AudioBufferSourceNode.prototype.start`/`stop` to track live (started,
  not-yet-stopped) sources, then drove the exact scenario from review — `go('menu')`, five rounds of
  `go('wish')` → `go('opt')` → `go('menu')`, then the dev restart button's exact statement
  (`bgm.currentTime=0;bgm.play()`) fired twice back to back. Result: **exactly 1 live source** throughout
  and after the double restart-press, **0 live sources** after `go('game')` (menu music correctly stops
  once the screen leaves menu/wish/opt/dev). Re-ran the probe a second time to confirm it wasn't a fluke —
  same result both times.
- **Real trim numbers for the embedded menu track** (measured live via the same probe, `window.__mgsAudioDebug`
  console output — this is the number 0.3_4 couldn't get without a browser): **57 ms head / 9 ms tail**,
  both well under the 500 ms cap.
- Not tested: real playback/device audio, iOS (Web Audio muted by the silent switch, flagged in 0.3_4,
  still applies), a custom-uploaded menu-music override's actual trim amount (will vary per file — check
  the same `window.__mgsAudioDebug` console line after uploading one).

## 0.3_6 — 2026-09-23
- **v0.4 bugfix B1b — `bgmGam` (blackjack table) and `prMusic` (professor) moved onto `loopTrack`.**
  `bgmGam`: `gamMusicInit()` now builds a `loopTrack` instead of `new Audio`; the existing `if(bgmGam)return`
  guard already meant it's only created once per session, and the custom-upload / reset handlers already
  null it out to force a fresh decode — both kept working unchanged.
- `prMusic`: replaced "create a brand-new `Audio` object every call" with a **per-slot cache**,
  `PR_TRACKS[slot]`, populated by a new `prTrackFor(slot)` — decodes once per slot and reuses the same
  `loopTrack` instance on every later `prMusic(slot,…)` call (restarting it from position 0 each time via
  the existing `currentTime=0` setter, matching the old "always a fresh `Audio`" behaviour without a
  redecode). Keyed by slot, not URL, because an IndexedDB override's blob URL is different every time it's
  read — `prTrackInvalidate(slot)` (called from both the dev-panel upload handler and the "Ripristina"
  reset handler, the same places that already touched `musicPr_<slot>` in IndexedDB) discards the cached
  track so the next call redecodes the new file.
- Added **`loopTrack().preload()`** (just exposes the existing internal decode step without playing) and
  **`loopTrack().stop()`** (stops the source, resets position to 0, `paused=true` — a full reset, unlike
  `pause()` which remembers position to resume later). `prMusOut()` now calls `.stop()` after its fade-out
  instead of the old `<audio>`-specific `a.pause();a.removeAttribute("src");a.load()`; `prFade()` needed no
  change since it only ever touches `.volume`, which `loopTrack` already exposed.
- Added **`prWarmMusic()`**, called at the very start of `prIntroYes()`: pre-decodes the battle/win/lose
  slots (via `preload()`, no playback) while the intro dialogue is still running, so B2/B3's timing (battle
  music starting with the transition, win/lose starting the instant the fight is decided) never waits on an
  MP3 decode on a phone.
- Small robustness fix caught in this session's own review of 0.3_5: `play()`'s `finally` now only clears
  `st.pending` `if(tk===st.tk)`, so a stale/superseded call finishing late can't clear a newer call's
  in-flight flag.
- **Verified in headless Chromium** (Playwright, same wrapped-`start`/`stop` live-source counter as 0.3_5),
  driving the real call sequence rather than full simulated gameplay (battle turn logic/RNG is separately
  covered by `pbSim`, not re-exercised here): `prStart()` into the professor screen (confirms `bgm` is
  correctly paused by the existing `syncMusic()`/`musicWanted()` gating the instant screen leaves
  menu/wish/opt/dev) → `prWarmMusic()` (0 live sources — decode-only, nothing plays) → `prMusic('intro')` →
  `prMusic('battle')` → `prMusic('win')` → back to the menu. **Exactly 1 live source at every step** (the
  previous slot's source is always cleanly stopped once its crossfade finishes, never orphaned), 1 (`bgm`)
  once back on the menu, `win` correctly still `paused===false` mid-playback. One blackjack enter/leave
  (`gamMusicInit()`+`gamMusic(true)` → `gamMusic(false)`) also showed a clean +1/-1 with no leaked source.
  My first pass at this probe (calling `prMusic()` directly without a real screen transition, and with
  waits shorter than the 400 ms default crossfade) produced misleading counts of 2–3 — that was a
  probe-fidelity bug, not an app bug; the corrected probe (real `prStart()`, 600 ms waits) is the one whose
  numbers are reported here.
- Not tested: real device/iOS, a full real professor battle played end-to-end through actual UI turns
  (gameplay/RNG correctness is `pbSim`'s job, not this chunk's).

## 0.3_7 — 2026-09-23
- **v0.4 A0 — built-in audio layer.** Added `const BUILTIN_AUD={}` (empty until the first approved
  submission is hardcoded into it): a middle tier between a developer's own per-browser IndexedDB upload
  and the game's shipped defaults. Lookup order everywhere is now **IndexedDB override → `BUILTIN_AUD` →
  original default** (a synthesized sound for character/table SFX and the achievement jingle, silence for
  voice lines — unchanged from today — or the embedded `*_B64` track for music).
- **Keys are identical to export `target` strings** (`sound.uomoRoccia.eat`, `music.pr.battle`, …, exactly
  as `expAudioItems()`/`exportTargetsMd()` already generate them), so an approved submission's manifest
  entry pastes straight into `BUILTIN_AUD` with no renaming. Added `sndTarget(c,s)` (the shared
  target-string builder) and `decodeSlotAudio(idbKey,builtinTarget)` (the shared 3-tier decode used by
  `loadSounds()` and by the "Rimuovi suono personalizzato" dev-panel handler, which used to hard-null the
  slot instead of falling back to a built-in). `initMusic()`, `gamMusicInit()`, and `prMusUrl()` each gained
  one line checking `BUILTIN_AUD` before their existing embedded-track default. `wipeData()` now calls
  `loadSounds()` again after clearing IndexedDB instead of manually nulling every SFX slot, so a wipe
  correctly falls back to a built-in track/sound if one exists, not straight to silence/synth.
- Full key table (target · what it is · original default) added to **DEVELOPERS.md** under a new "Audio
  target names" section, and repeated below for the record:

  | `target` | What it is | Original default |
  |---|---|---|
  | `sound.uomoRoccia.eat/.foe/.power/.die` | Uomo roccia's 4 character sounds | Synthesized |
  | `sound.algidone.eat/.foe/.power/.die` | Algidone's 4 character sounds | Synthesized |
  | `sound.ach` | Achievement jingle | Synthesized |
  | `sound.gam.<13 slots>` (`deal,flip,shuffle,chip,win,lose,push,bj,bust,lighter,select,confirm,collect`) | El Gamblador table SFX | None (silent) |
  | `sound.vo.<24 ids>` (El Gamblador dealer lines) | Dealer voice lines | None (silent) |
  | `sound.vo.<9 ids>` (`pr_q,pr_c_no,pr_c_yes,pr_no,pr_y1,pr_y2,pr_y3,pr_pk,pr_ang`) | Professor voice lines | None (silent) |
  | `music.menu` | Main menu music | Embedded `MUSIC_B64` |
  | `music.gam` | El Gamblador table music | Embedded `GAM_MUSIC_B64` |
  | `music.pr.intro/.battle/.win/.lose` | Professor music (4 slots) | Embedded `PR_*_B64` per slot |

- **Memory: `loopTrack().release()`** — drops a track's decoded `AudioBuffer` (a menu-length MP3 decodes
  to tens of MB of PCM) while keeping the lightweight instance alive; the next `play()`/`preload()`
  transparently redecodes from the same URL. Wired into `bjExit()` for `bgmGam` (released every time
  blackjack is left) and into `prExit()` for every cached `PR_TRACKS[slot]` (released on exit;
  `prWarmMusic()` redecodes them the next time the professor scene starts). The main menu track is
  deliberately **not** released — it's cheap to keep and is the one track played most often. Known gap:
  the professor **win-and-decline-to-continue** path (`pbEnding`'s `else{...go("menu")}` branch) returns to
  the menu without calling `prExit()`, so that specific exit doesn't release `PR_TRACKS` — flagging this
  since only `prExit()` was in scope for this chunk.
- **Verified in headless Chromium**, with two synthetic test WAV clips (0.3 s and 0.6 s, injected into
  `BUILTIN_AUD`/IndexedDB only for the test, not committed): confirmed override beats built-in beats
  default for one SFX key (`sound.uomoRoccia.eat`, decoded-buffer duration distinguishes which tier
  actually won: null → 0.3 s → 0.6 s → back to 0.3 s → null) and for one music key (`music.menu`, confirmed
  via which source `initMusic()` actually reads: the built-in `data:` URI when no override exists, an
  IndexedDB blob once one is added). Also confirmed the memory-release mechanism functionally: entering
  blackjack decodes `bgmGam` once, `bjExit()` releases it, re-entering redecodes and plays correctly
  (`paused` goes back to `false`); the professor flow's 4 `PR_TRACKS` slots all end up `paused` after
  `prExit()`, and playing a slot again afterward redecodes and works fine. (This confirms the release
  mechanism behaves correctly — it does not measure actual heap/GC memory reclaimed, which headless
  probing isn't well suited to.)
- Not tested: real device/iOS, an actual approved submission going through this path end-to-end (no
  submissions exist yet — `BUILTIN_AUD` ships empty).

## 0.3_8 — 2026-09-23
- **Follow-up fix — `PR_TRACKS` memory release now also covers both win-branch exits.** 0.3_7's
  release-on-exit only fired from `prExit()`, but review pointed out that a **won** professor battle
  never calls `prExit()` at all — neither the "continue at girone 3" branch (`startGame(...)`) nor the
  "back to menu" branch (`go("menu")`) — so `PR_TRACKS` stayed decoded for the entire rest of that session
  after a win. Extracted the release loop into **`prReleaseMusic()`** and call it from `prExit()` and from
  the shared point right after `pbTeardown()` in `pbEnding()`'s win branch (covers both the "sì" and "no"
  outcomes of the continue-at-girone-3 question in one place, since they diverge only after that line).
- **v0.4 P1 — popup unlock framework.** New persisted state `S.p.pop={queue:[],seen:{},needsSeed:false}`
  (`DEF` + migration — see the seeding note below). Shown **only on the home menu**, one at a time, as a
  centred modal (reuses the existing `openModal()`/`.box` pixel-style modal, not a new full-screen screen).
  Enter = "Guarda", Esc = "Non ora" (wired into the existing global modal keydown handler alongside the
  older single-button "Avanti" pattern).
- **Event types wired**: **asset/ghost** (an item becomes buyable for the *current* character — checked
  against `planeUnlock(i)`/`rockUnlock(i)`, the same threshold `cardHTML` already uses), **character** (El
  Gamblador / Il Professore's card becomes visible in Giocatore, via the existing `S.p.gam.seen`/
  `S.p.pr.seen` flags), **mini-game** (the same two flags also unlock their Giochi cards, G2/G3 — a
  *separate* popup from "character" since they lead to different tabs). **milestone** is wired as a stub
  only (`POP_TITLE`/`popBodyHTML`/`popGoto` all handle the type) — nothing pushes it yet; R4 will push
  `{type:"milestone",items:[...]}` onto the same queue once the roadmap exists.
- **Grouped per type**: one scan (`scanNewUnlocks()`, run once per `renderMenu()`) collects every
  newly-crossed item of the same type into a single queue entry with an `items` array, rather than one
  popup per item. "Guarda" navigates to Lista desideri, tab `planes`/`rocks` (asset — picks the first
  item's kind when a group mixes both), `player` (character) or `games` (mini-game).
- **Old-save seeding**: a save from before this build (detected via the same raw-pre-merge-capture pattern
  the `S.p.gam`/`S.p.pr` migration already uses, not just "does `.pop` exist" — see the bug below) gets
  `needsSeed=true`; the first `scanNewUnlocks()` call (lazily, once all game functions are defined) then
  runs `seedPopSeen()`, which marks everything **already** unlocked **for both characters** as seen before
  doing its normal diff, so an existing player isn't flooded. A brand-new save starts with an empty `seen`
  map instead, so a first-time player does see the very first popup (their starting plane/rock at level 1
  count as a "new" unlock the moment they first reach the menu) — this is intentional, not a seeding gap.
- **Bug found and fixed during this session's own testing**: the first version of the migration computed
  `needsSeed` as `!!store.get("mgs_v1")` and merged it via `Object.assign({...defaults},S.p.pop||{})` —
  but `S.p.pop` is *never* actually absent by that point, because the earlier `S.p=Object.assign(DEF.p,
  S.p)` step had already back-filled it from `DEF.p.pop`'s own default (`needsSeed:false`), so the
  Object.assign always kept the stale `false`. Old saves never got seeded and would have been flooded.
  Fixed by capturing `_hadSave`/`_hadPop` from the *raw* pre-merge save object (same technique as the
  existing `sp.ch` check on the line above it) and setting `needsSeed=true` explicitly only when a save
  existed before and genuinely never had `.pop`.
- **Never enqueues from `SIM()` or a dev-test run** (`G.dev`): `scanNewUnlocks()` bails immediately in both
  cases, and the auto-show at the end of `renderMenu()` has the same guard.
- **Dev panel**: one preview button per event type (Asset / Personaggio / Minigioco / Traguardo) under a
  new "Popup di sblocco" row in Strumenti di test → Obiettivi, each calling `popPreview(type)` with sample
  data — never touches the real queue or `persist()`.
- **Popup strings** (Italian, in-universe, as shown in-game):
  - Titles: *"Novità in negozio!"* (asset) · *"Nuovo personaggio!"* (character) · *"Nuovo minigioco!"*
    (mini-game) · *"Traguardo raggiunto!"* (milestone stub)
  - Body: *"Ora puoi acquistare: **Nome1**, **Nome2**."* (asset) · *"Ora disponibile: **Nome**."*
    (character) · *"Ora disponibile nei Giochi: **Nome**."* (mini-game)
  - Buttons: *"Guarda"* / *"Non ora"* (per the owner's answer, logged in CLAUDE.md §10.9)
- **Verified in headless Chromium**, three scenarios exactly as requested: (A) fresh save via the real
  `wipeData()`, leveled to 10 → exactly **one** grouped popup (`Sopwith Camel`, `Supermarine Spitfire`,
  `Rame`) → clicking "Guarda" correctly lands on `screen="wish"`, `tab="planes"`, queue empties; (B) an old
  save (level 20/15, `gam`/`pr` already `seen`) loaded in a **fresh isolated browser context** (to avoid a
  real, pre-existing `visibilitychange`→`persist()` handler racing a same-page `localStorage` + `reload()`
  test technique and silently overwriting the injected save — a probe-methodology pitfall worth flagging
  for future test scripts, not an app bug) → `needsSeed` true → false after one menu visit, queue stays
  **empty**, 18 keys pre-seeded as seen; leveling that save further afterward correctly starts producing
  normal new popups again; (C) `SIM()` mode (level 100 on every character) → queue stays **empty** even
  though every asset would otherwise qualify.
- Not tested: real device/touch (Enter/Esc keyboard shortcut is desktop-only by nature), an actual roadmap
  milestone popup (nothing to trigger it yet), the mixed-group tab-choice heuristic (picks the first item's
  kind) with a real plane+rock unlock happening in the same level-up in practice.
- **Follow-up from the P1 review**: checked whether any single level unlocks both a plane/gym item and a
  rock/snack item at once (`planeUnlock(i)` vs `rockUnlock(i)`) — **yes**, levels **1, 37 and 73** do (e.g.
  level 1 is everyone's starting plane+rock, already observed live in testing). The tab-choice heuristic
  above is exercised for real, not just in theory; the proper fix (group popups per *tab*, not per *shop
  section*) is deferred to R4 as instructed.

## 0.3_9 — 2026-09-23
- **v0.4 R1 — roadmap: state, entry button, snake screen, regular girone tiles.** New persisted state
  `S.p.road={claimed:{}}` in `DEF` + migration (simple `Object.assign`, no old-save seeding needed — nothing
  has ever been "claimed" before this feature existed, so an empty default is correct for every save, old
  or new alike).
- **Entry**: a new icon button `#road` (a simple mountain-path glyph) sits right next to the trophy `#trop`
  in the home `.brand` bar, per the owner's decision logged in §10.9. Opens `screen="road"`.
- **Screen** (`renderRoad`/`bindRoad`): 50 tiles, tile 1→50, laid out as a boustrophedon (snake) path —
  rows of 5, alternating left-to-right/right-to-left so tile *N* and *N+1* are always adjacent — with small
  arrow connectors between tiles and at each row-end turn. Scrollable (`.roadwrap`), auto-scrolls to the
  player's current tile (`min(50, cs().gir+1)`, outlined) on open.
- **Tile faces**: number, except **3 = ⬤** (pokéball placeholder), **5 = ♠** (playing-card-suit
  placeholder), **10/15/…/50 = "?"** — `roadFace(n)`. These are plain Unicode glyphs, not drawn/generated
  character art (no rule against that here — same category as the "?" already used elsewhere for
  locked/mystery cards), but they're placeholders; happy to swap for real icons if/when art arrives.
- **Regular-tile unlock — per-character, as decided**: `roadUnlocked(n)` is simply `cs().gir>=n`, the
  existing per-character cumulative girone counter (excludes dev/test runs already, via the existing
  `if(!G.dev)` guard on `c0.gir++`). **All 50 tiles use this same rule for now**, including 3, 5 and the
  "?" tiles — R2 will swap tiles 3 and 5 specifically to their dedicated conditions (a real professor
  battle / 10 blackjack hands won) without touching this function for the other 48.
- **States implemented**: locked (grey, dim) and unlocked (coloured). The CSS for **claimable** (pulsing
  yellow, reusing the exact `abpulse` keyframe the ability button already uses) and **claimed** (dimmed,
  distinct from locked) is included so R2/R3 only need to flip which state a tile reports, not build new
  rendering — but no tile can reach either state yet since no reward data exists until R2/R3.
  **Claimed state is deliberately global** (`S.p.road.claimed`, not per-character) per the owner's answer,
  even though this chunk doesn't populate it yet.
- Tapping a locked tile toasts "Sblocca al girone N"; tapping an unlocked regular tile toasts "Girone N
  raggiunto"; tapping an unlocked tile 3/5/"?" toasts "Premio in arrivo" (placeholder — R2/R3 replace this
  with the real expand-to-"Riscatta" flow).
- **Verified in headless Chromium** with a screenshot: confirmed the snake layout, alternating row
  direction and connectors render correctly; confirmed **per-character isolation** — setting only
  `S.p.ch.roccia.gir=12` showed tiles 1–12 unlocked and 13 (current) locked on roccia, while switching to
  algidone (still `gir=0`) showed tile 1 locked and marked current, proving the two characters' progress
  don't leak into each other; confirmed tile faces (⬤/♠/"?") render at the right indices; confirmed the
  locked-tile toast fires.
- **Bug caught and fixed while building this** (not a logic bug this time — a text-editing mistake): the
  edit that inserted this whole section accidentally left the section-header comment above `const MAZE=…`
  unterminated (`/* ============ GAME ============` missing its closing `*/`), which silently swallowed
  `const MAZE=…` and everything after it into a comment — `node --check` still passed (a shifted comment
  boundary is still syntactically valid JS) but the page threw `MAZE is not defined` at runtime the moment
  anything touched it. Caught immediately by the headless probe failing to even reach the menu; fixed by
  restoring the closing `*/`. Flagging the general lesson: an unterminated block comment is exactly the
  kind of error `node --check` cannot catch, so a runtime smoke-test (even a trivial one) after any edit
  near a large `/* */` section header is worth keeping in the routine.
- Not tested: real device/touch, R2/R3's actual claim flow (not built yet), whether the placeholder
  ⬤/♠ glyphs read well against the game's existing pixel art style.

## 0.3_10 — 2026-09-23
- **v0.4 R2 — special tiles 3 and 5, `S.p.gam.won`, new achievement, "?" tiles.** Two pre-checks the owner
  asked for before building, both confirmed rather than assumed:
  - `cs().gir` really is what R1 needed it to be: incremented only at the one real girone-clear site
    (guarded `if(!G.dev)`, so dev/test runs are excluded), and never reset anywhere — not by `startGame()`,
    not by "Nuovo gioco"/Hardcore (those only touch the current run's `G.stage`, a completely separate
    field). Confirmed cumulative and correct as-is; no new counter needed.
  - The achievements screen with a 5th category tab was checked visually in headless Chromium at 320/360/
    390px width (the injected tab, not yet committed, just for the fit check): all 5 fit on one row down to
    320px (the narrowest common phone width), with only the longer "Uomo roccia" label wrapping to two
    lines — still fully readable and tappable, no overflow/clipping/scrollbar. Proceeded rather than
    stopping to report, since it genuinely fit.
- **Tile 3** now unlocks on `S.p.pr.seen` (a real professor battle) — **not** `S.p.pr.visits` (the
  "No"-branch kick-out alone), per the owner's answer. **Tile 5** unlocks on the new **`S.p.gam.won>=10`**.
  Both conditions are in `roadUnlocked(n)`, special-cased ahead of the fallback `cs().gir>=n` used by the
  other 48 tiles (including the "?" ones, unchanged from R1: they still unlock with their girone, tap shows
  "Premio in arrivo", not claimable — confirmed as the spec default, no change needed there). Both tile 3
  and 5's conditions are **global**, not per-character (they're shared, character-independent features),
  consistent with the owner's R1 answer that special/reward tiles are global.
- **`S.p.gam.won`** (new counter, `DEF.p.gam` + migration: `{visits,seen,won:0}`) increments in `bjHand()`
  the moment a hand resolves as a win (`kind==="win"||"dbust"||"bj"`), gated on `!B.dbg` — `B.dbg` is set by
  `bjMake({dbg:!o.run,...})`, and the only call site that ever passes `run:false` is the dev-panel's
  `#mggam` quick-test button, so this reliably excludes dev/test hands the same way `G.dev` does for the
  maze game.
- **New achievement** (31st): **`{id:"m1",n:"Il banco trema",c:"min",ev:"bjwon",m:"max",goal:10,r:[200,120]}`**
  — same reward tier as the closest comparable "reach 10" achievement (`g6`, Collezionista). Fires via
  `ach("bjwon",{n:S.p.gam.won})` right after the counter increments, same pattern every other counter
  achievement already uses (`m:"max"` because the event passes the *current total*, not a delta — using
  `"sum"` here would have double-counted). **New category "Minigiochi" (key `min`)** added to `ACH_CATS`,
  for this and future mini-game achievements (per the owner's decision).
- **Tile faces for 3 and 5 reuse existing art, no new art drawn**: tile 3 draws `prBallCv()` (the exact
  pixel-art pokéball already used in the professor's throw-scene animation, memoized so this doesn't
  redecode/redraw it, just reuses the cached canvas); tile 5 draws `cardCv(1,0)` (the same playing-card
  canvas generator El Gamblador's own table art and the G2 Giochi-card icon already use). Wired through a
  new `"road"` case in `paintCanvases()`'s existing dispatcher, matching how every other screen's small
  icon canvases already work (`data-draw="road:N:100"`).
- **Verified in headless Chromium**: tile 3 stays locked with `pr.visits=5,pr.seen=false` and unlocks the
  moment `pr.seen=true`; tile 5 stays locked at `gam.won=9` and unlocks at `gam.won=10`; firing `ach("bjwon",
  {n:10})` correctly completes achievement `m1` and it shows up under the new "Minigiochi" tab; a screenshot
  confirms the reused pokéball/card art renders correctly on the roadmap tiles. Also ran the **new standing
  headless smoke test** (menu renders, zero console errors, a run starts) added to CLAUDE.md §6 rule 4 in
  this same commit, per the owner's instruction — it passed.
- **CLAUDE.md §6 rule 4 updated**: the headless Chromium smoke test (load `index.html`, menu renders, no
  console errors, start a run) is now a standing step after `node --check`, specifically called out as the
  thing that would have caught 0.3_9's unterminated-comment bug immediately (a syntax-valid but
  runtime-broken file `node --check` cannot detect on its own).
- Not tested: real device/touch, a real 10-hand blackjack session played through actual UI turns (the
  counter logic itself is simple and directly verified above, but not exercised via real gameplay), R3's
  actual claim flow for tiles 3/5 (still not built).
- **Queued for R4, not done here** (per the owner's instruction): grouping popups per Lista-desideri *tab*
  rather than per shop section (needed because levels 1/37/73 unlock a plane and a rock together), and
  skipping popups for items the player already owns on a fresh save.

## 0.3_11 — 2026-09-23
- **Pre-R3 questions, answered without needing any code** (all confirmed by direct inspection/probe, no
  gaps found):
  1. Can a SIM-mode blackjack win leak `S.p.gam.won` into the real save? **No** — `S.p.gam.won` lives under
     `S.p`, and `simOn()`/`simOff()` already clone the whole `S.p` into a working copy and restore the
     original wholesale on exit, the same mechanism that already protects every other stat (`sordi`, `lvl`,
     …). Structurally impossible to leak, nothing to add.
  2. Do natural blackjack and double-down wins increment the counter, and is a push excluded? **Yes and
     yes** — `bjSettle()`'s `kind:"bj"` (natural) and `kind:"win"`/`"dbust"` (doubled hands resolve through
     the same classification, just for a bigger stake) are all included in 0.3_10's `win` check;
     `kind:"push"` is never included. This codebase has **no split mechanic** at all (`bjChoose`'s options
     are only hit/stand/double/surrender), so that part didn't apply.
  3. Does "Il banco trema" show "x/10" progress like other counter achievements? **Yes**, automatically —
     it's just another entry in the shared `ACH` array, rendered by the same generic progress bar/text every
     other achievement already uses. Verified via probe: shows "4 / 10" after 4 simulated wins.
- **v0.4 R3 — gift container + generic reward claim, with a readiness gate.** New **`ROAD_REWARDS`**
  registry: `{3:{type:"skin",id:"geka",char:"roccia",name:"Cappello GEKA SNC",ready:false},
  5:{type:"skin",id:"kebab",char:"algidone",name:"Costume kebab",ready:false}}`. `ready` starts `false` for
  both and is meant to flip to `true` **only** in K2/K3 respectively — nothing in this build ever sets it.
- **Readiness gate**: `roadState(n)` now returns `"claimable"` (the pulsing-yellow state, CSS already
  written in R1) only when a tile is unlocked, not yet claimed, **and** its `ROAD_REWARDS` entry has
  `ready:true`. While `ready:false` (i.e. right now, for both tiles), an unlocked tile 3/5 behaves exactly
  like a "?" tile: unlocked colour, no pulse, tapping toasts "Premio in arrivo", not claimable. Verified on a
  fresh save with both unlock conditions satisfied (`pr.seen=true`, `gam.won=10`) that neither tile opens
  the gift modal while `ready` stays `false`, and that flipping `ready` (simulating what K2 will do) is the
  *only* thing that changes this.
- **`skins:[]`/`skin:null`** added to `CHDEF()` and to the existing per-character migration loop (same
  pattern as `gir`), since granting a reward needs somewhere to put it — C1 (customisation page) will read
  these later, nothing reads `skin` (the equipped one) yet.
- **Claim flow**: tapping a claimable tile opens a modal (not full-screen, reusing `openModal()`) showing a
  small **procedural pixel gift box** (`giftCv()`, plain filled rectangles — box, ribbon, bow — memoized like
  `prBallCv()`) with a CSS `giftwobble` keyframe animation (idle rotate + bounce, disabled under
  `prefers-reduced-motion`). Tapping the box swaps in the reveal panel: the reward's name and, since neither
  skin has real art yet, **the character's normal portrait** (reuses the existing `hero:<char>` canvas
  dispatch already used elsewhere) — exactly the fallback the owner specified. Closing calls
  **`roadGrantReward(rw)`** (generic on `rw.type`, today only handles `"skin"`: pushes `rw.id` into
  `S.p.ch[rw.char].skins` if not already present) and sets `S.p.road.claimed[n]=true`, **always against
  `rw.char`**, regardless of which character is currently selected/being played.
- **Dev panel**: one "Anteprima regalo" button per `ROAD_REWARDS` entry (Strumenti di test → Regali del
  percorso), calling `roadPreviewGift(n)` — runs the identical gift-box/reveal animation but skips the
  grant/claim/`persist()` entirely.
- **Verified in headless Chromium**: on a fresh save, satisfied both unlock conditions but confirmed no gift
  modal opens while `ready:false`; flipped `ready` and confirmed the tile becomes `claimable`; claimed it —
  reveal showed the correct name and roccia's portrait, `S.p.ch.roccia.skins` became `["geka"]`,
  `S.p.ch.algidone.skins` stayed untouched, `S.p.road.claimed[3]` became `true`, and re-tapping the now-
  claimed tile is a safe no-op (no modal, no re-grant); ran the dev preview for tile 5 and confirmed
  `S.p.road.claimed[5]` and `S.p.ch.algidone.skins` were both untouched afterward. Screenshots confirm the
  gift box and reveal panel render correctly. Also ran the standing smoke test (menu renders, no console
  errors, a run starts) — passed.
- Not tested: real device/touch (the perpetual wobble animation made Playwright's own actionability check
  refuse a "natural" click in testing — had to force it; worth a quick real-finger check that the wobble
  doesn't make tapping awkward on an actual phone), C1 (nothing reads `skins`/`skin` yet, by design).

## 0.3_12 — 2026-09-23
- **v0.4 R4 — milestone popups wired to the roadmap, plus three queued fixes.**
- **Milestone popups**: `scanNewUnlocks()` (called on every home-menu render, same as every other popup
  type) now also checks every `ROAD_REWARDS` entry — fires a `{type:"milestone",items:[...]}` popup **once
  ever per tile**, the moment that tile is both unlocked (R2's condition) **and** its registry entry has
  `ready:true`. Deliberately does **not** mark the tile "seen" until both conditions are actually met, so a
  future build flipping `ready:true` (K2/K3) is what actually fires it for players who met the unlock
  condition long before — verified: with `pr.seen=true` but `ready` still `false`, no milestone is queued
  on repeated menu visits; flipping `ready` (test-only, see below) on a *later* visit fires it immediately.
  "?" tiles and not-ready rewards never fire (there's no registry entry for "?" tiles, and the `ready` check
  gates the only two that exist). Guarded by the same `if(SIM()||(G&&G.dev))return` every other popup type
  already uses — verified SIM mode enqueues nothing even with the tile-5 condition fully met, and turning
  SIM back off correctly lets the real save's own state fire it independently afterward.
- **"Guarda" → roadmap, scrolled and highlighted**: `popGoto` for `milestone` sets a one-shot
  `roadHighlightTile` and navigates to `screen="road"`; `renderRoad()` auto-scrolls to that tile instead of
  the usual "current girone" tile and adds a new `.hl` outline class (distinct from `.cur`, so "here's what
  the popup was about" doesn't get confused with "here's your progress") — cleared immediately after that
  one render. Enter/Esc reuse the existing popup keydown handler unchanged (no popup-type-specific code
  there). Verified with a screenshot: tile 3 shows both the `claimable` pulse and the `.hl` ring together.
- **Fix — popup grouping per Lista-desideri *tab*, not per shop.** `scanNewUnlocks()` used to collect every
  newly-unlocked plane *and* rock into one combined `"asset"` group; since levels 1, 37 and 73 unlock a
  plane and a rock at the same time (found during the P1 review), "Guarda" could land on a tab that didn't
  show every item the popup listed. Now collects planes and rocks into two separate arrays and pushes up to
  two separate queue entries, so every group is single-kind and `popGoto`'s existing
  `items[0].kind==="plane"?"planes":"rocks"` is now always correct for every item in that group, not just
  the first one. Verified at level 37 (which unlocks both): two separate popups appeared, back to back,
  each landing on the correct tab in turn.
- **Fix — skip items the player already owns.** Same function: an unlocked plane/rock is only added to the
  popup's `items` array if `!cs().ownP.includes(i)` / `!cs().ownR.includes(i)` — it's still marked "seen"
  either way (so it's never re-checked), just not shown if already owned. Fixes a fresh save's starting
  plane+rock (unlocked from level 1, and already owned by `CHDEF()`) triggering a nonsensical "you can now
  buy the thing you already have" popup on the very first menu visit. Verified: a freshly wiped save's queue
  is empty right after the wipe.
- **Fix — gift modal click target.** The wobble animation used to be on `#giftbox` itself (the click
  target), which made the box perpetually "not stable" — Playwright's own actionability check refused a
  natural click in 0.3_11's testing and had to be forced. Restructured: `#giftbox` is now a static outer
  container (slightly larger than the gift), with a new inner `.giftwrap` div carrying the `giftwobble`
  animation and the canvas; the click handler still attaches to the now-static `#giftbox`. Verified: a
  *natural*, unforced Playwright click on `#giftbox` now succeeds and opens the reveal.
- **CLAUDE.md doc fixes, same commit**: §4 code map now notes that roccia's `fd*` frames are used moving
  **up** and `fu*` moving **down** (named by crop row, not content — verified directly in `drawHero`), and
  that `fu1`/`fu2` and Algidone's `al_r7` are intentionally unused in the maze cycles (verified via the
  exact modulo/sequence arithmetic in `drawHero`/`drawAlg`), not dead code to prune. §8's "Algidone/Uomo
  roccia up/down sprites" open-bug entry is **removed entirely** — the owner confirmed in-game that
  Algidone's DOWN view looks right; no code change was needed, it was a stale report. §10.8 now shows R1–R4
  all `done`.
- Not tested: real device/touch, K1/K2/K3 (nothing flips `ROAD_REWARDS[n].ready` in the committed build —
  every `ready:true` state used above was set only inside the headless test, never shipped).

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

## 0.3_13 — 2026-09-24
- **Amendment to R1 — roadmap girone count is now global (both characters combined), not per-character.**
  Owner correction to the §10.9-logged R1 decision ("Regular tiles are per-character"): the 50-tile path
  is a single shared progression, so a regular/"?" tile's unlock threshold is now the **sum** of
  `S.p.ch.roccia.gir` and `S.p.ch.algidone.gir`, not the current character's `cs().gir` alone. New helper
  `roadGir()` (sums `.gir` across `Object.values(S.p.ch)`) replaces the three `cs().gir` call sites inside
  the roadmap module: `roadUnlocked()`'s regular-tile branch, `renderRoad()`'s current-tile marker, and the
  screen header ("Girone N"). Tiles 3 and 5 were already global (§10.9 R2, dedicated conditions unrelated
  to girone count) and are unchanged. The unrelated `cs().gir` read inside the per-character career modal
  ("Gironi completati") is intentionally left alone — that stat is character-specific by design, only the
  roadmap reads it globally now.
- No new state, no migration: `roadGir()` is computed from the existing per-character `.gir` fields, which
  already exist in `DEF`/`CHDEF()` and already load on old saves. `S.p.road.claimed` was already global
  (§10.9 R1), so claim state is unaffected by this change.
- Consequence for existing saves noted for the owner: a player who has completed gironi on both characters
  will see more roadmap tiles already unlocked than before (the combined count can only be ≥ either
  character's own count). This does **not** trigger a flood of milestone popups — `scanNewUnlocks()`'s
  milestone branch only watches `ROAD_REWARDS` (tiles 3/5), which never used girone count in the first
  place; regular/"?" tiles carry no popup event at all.
- Updated the module's own doc comment (just above `ROAD_N`) to describe the new global rule instead of the
  superseded per-character one, and added a decision-log amendment row + updated the R1 row's chunk-table
  note in CLAUDE.md §10.9 (see that file's own diff) rather than silently rewriting the original logged
  answer.
- **Verified in headless Chromium**: injected `roccia.gir=2`, `algidone.gir=3` on a fresh save → `roadGir()`
  reads 5, screen header shows "Girone 5", tile 4 (`4<=5`) shows `unlocked`, tile 6 (`6>5`) stays `locked`.
  Menu renders with zero console errors; a real run still starts normally via `startGame()`.
- Not tested: real device/touch, in-game review by the owner, the R2 popup path for tiles 3/5 (unchanged
  by this build, already covered by 0.3_10's testing).

## 0.3_14 — 2026-09-24
- **v0.4 K1a — skin system, data layer only (no player-visible change, no draw-path change).** K1 was split
  into K1a (this build) and K1b (the actual overlay hook, next) per the owner's instruction; K1b's three
  design decisions are logged in CLAUDE.md §10.9 (Acciaio keeps the skin on, drawn *under* the steel tint;
  Cinghiale hides the skin entirely; Algidone's power-up "rolling" frames show a skin only if that skin
  actually provides those frames, missing-frame rule otherwise).
- **`refs/skins/SPRITE_INVENTORY.md`**: every place either character visually appears — 19 numbered
  draw-paths, from the maze (all 4 directions, eating, Acciaio, Cinghiale, death-spin) through the menu
  scene, every static-portrait canvas (Lista desideri card, gift-reveal preview, HUD lives icons, splash
  logo), and the professor mini-game (dialogue portrait box, pond-throw cutscene) — with the exact frame
  keys each one reads, and which function draws it. Flags every procedural (non-bitmap) element explicitly
  (Cinghiale's `drawBoar` is 100% code-drawn, matching the "skin hidden" decision with no overlay needed)
  and every place the character does **not** actually appear despite being part of the same scene (the
  professor's own idle/angry/walk scenes draw only the professor, never the player; the battle screen draws
  the player's chosen rock/snack asset, not their human body). Also documents a pre-existing, unrelated
  quirk found along the way: `drawMiniPlaceholder` always draws Uomo roccia's portrait regardless of the
  active character — flagged for K1b to decide on, not touched in this build.
- **Two genuinely new, non-obvious findings surfaced while building the inventory** (beyond what CLAUDE.md
  §4 already documented for `fu1`/`fu2`/`al_r7`): `f3` and `fd3` (Uomo roccia's side/up walk cycles both
  run `[0,1,2,1]`, never reaching index 3) are likewise defined but never drawn by any current code path;
  and `fd_e0`/`fd_e1`/`fu_e0`/`fu_e1` (the up/down eat-bite frames) are **completely dead** — up/down eating
  uses a procedural rock-icon overlay (`drawFaceEatFX`) instead, so `eatKey`/`eatImg` are never actually
  called with an "fd"/"fu" prefix from any real draw path. All four are still exported as base frames (an
  artist can still draw overlays for them for future-proofing) and flagged, not pruned — same "not dead
  weight to prune" policy CLAUDE.md already states for the other three.
- **46 base-frame PNGs** exported pixel-exact, decoded directly from the current build's embedded `SPR`
  (Uomo roccia, 18 frames — the pellet-animation keys `rock`/`r1`/`r2` are excluded, they're item art, not
  the avatar) and `SPR2` (Algidone, all 28 frames) constants, to `refs/skins/base/uomo_roccia/<key>.png` and
  `refs/skins/base/algidone/<key>.png`. Filenames match the exact in-game sprite key. 732 KB total on disk;
  **not embedded in `index.html`** (reference material only, exactly like the existing `refs/` reference
  sheets).
- **`refs/skins/README.md`**: short artist-facing how-to — copy a base PNG, draw only the accessory on
  transparency, keep the canvas size identical, name the file `sk_<skin-id>_<frameKey>.png`, right-facing
  side view only (left is a code flip), up/down views never flipped, unused frames can be skipped.
- **Data layer** (`index.html`, right after `loadImgs()`/`tintRock`): `const SKINS={}` (empty in this
  build — K2/K3 populate it), `loadSkinImgs()` decodes every `SKINS[id].frames[frameKey]` into
  `IMG["sk_"+id+"_"+frameKey]`, **validating at load** that the overlay's decoded pixel size exactly matches
  its base frame's (`IMG[frameKey]`) — a mismatch is skipped with a `console.warn`, never a thrown error,
  and that frame simply renders without the skin (the missing-frame rule). Wired into boot right after
  `loadImgs()`: `loadImgs().then(loadSkinImgs).then(()=>{...})`. Helper `skinImg(char,frameKey)` returns the
  loaded overlay Image or `null`, looked up via **the given character's own** `S.p.ch[char].skin` (already
  existing state from R3's reward-granting code, not new) — deliberately *not* the currently-played
  character, so a Lista desideri card can show each character's own equipped skin regardless of which one
  is active. `SKINS`/`loadSkinImgs`/`skinImg` are the only public surface K1b needs; no draw-path function
  calls `skinImg` yet.
- **Verified in headless Chromium**: with `SKINS` empty, `skinImg()` returns `null` everywhere (no
  behaviour change). Registered a temporary in-memory test skin with a correctly-sized `f0` overlay and a
  deliberately wrong-sized `f1` overlay, ran `loadSkinImgs()`: the matching frame loads and `skinImg()`
  returns it once equipped on `S.p.ch.roccia.skin`; the mismatched frame is rejected with exactly the
  expected console warning and `skinImg()` returns `null` for it; a frame never provided at all
  (`f2`) also returns `null`; equipping the skin on roccia does **not** leak it to `skinImg('algidone',...)`.
  Menu renders with zero console errors throughout, and a real run still starts normally.
- Not tested: real device/touch, an actual artist-drawn skin end to end (nothing populates `SKINS` yet),
  K1b's draw-path integration (next chunk).

## 0.3_15 — 2026-09-24
- **v0.4 K1b — skin overlay hook wired into every draw path, plus per-skin render mode.** Every `SKINS`
  entry now carries `mode:"overlay"` (drawn on top of the base frame — accessories) or `mode:"replace"`
  (drawn instead of the base frame, same size — full costumes that recolour the character, where an overlay
  would leak the original colours through). A `replace` skin still falls back to the base frame for any
  frame it doesn't provide, same as `overlay`. `skinImg()` now returns `{img,mode}` instead of a bare image.
- **Hook**: a shared `drawSkinned(ctx,char,frameKey,im,dx,dy,dw,dh)` helper draws base+skin with **identical**
  arguments to whatever `drawImage` call it replaces (same `dx,dy,dw,dh`, inside the caller's own
  `save`/`restore`, inheriting whatever flip/scale/smoothing/alpha the caller already set) — wired into the
  three low-level functions (`drawFace`, `drawEat`, `drawAlg`), which alone covers most of
  `SPRITE_INVENTORY.md`'s draw-paths (maze all 4 directions + eating, menu-scene eating, battle-interjection
  bite, death-spin, Acciaio/power-up/burn tinting via `drawTinted`) without touching those call sites.
  `drawFaceEatFX`'s procedural rock-icon overlay is untouched by design — the walk frame `drawHero` draws
  alongside it already carries the skin.
- **Five call sites that draw `IMG.al_st`/`al_w0` directly** instead of going through `drawAlg()` — the
  Lista desideri/gift-reveal card, the maze HUD lives icons, the splash logo, the pond-cutscene cached
  portrait (`prPlayerCv`), the professor dialogue talking-portrait (`prDrawPlayer`), and the home-menu scene
  (`drawScene`) — were each updated individually to call `drawSkinned` in place of their own `drawImage`,
  same identical-arguments rule. Their Uomo roccia counterparts already went through `drawFace`/`drawEat`
  and needed no change.
- **Verified Acciaio needs no special handling**: `drawTinted` renders its callback to an offscreen canvas
  and tints the *whole* buffer — since the hook lives inside `drawHero`'s own callees, whatever the skin
  draws gets the steel tint for free, in both `overlay` and `replace` mode, confirmed by direct test on
  `drawTinted(...,fn=drawFace/drawAlg,...)`. Cinghiale (`drawBoar`) needs **no hook at all** — 100%
  procedural pixel art with no `IMG` reference, matching the "skin hidden" decision with zero code changes.
- **`drawMiniPlaceholder`'s hardcoded-to-Uomo-roccia icon reported, not fixed**: it also draws 3 rolling
  rock icons alongside the portrait, which only makes sense for Uomo roccia — reads as an intentional
  "Mangiaroccia" brand icon for the mini-game card, not a "your active character" portrait that happens to
  be wrong. Left as-is; flag if that reading is incorrect.
- **Dev-only skin test tool**: a new "Skin di prova (K1b)" row in Opzioni → Sviluppatore → Strumenti di
  test, 5 buttons (Roccia/Algidone × overlay/replace, plus "Disattiva"). Sets an in-memory `DEV_SKIN_TEST`
  variable — never written to `S.p.ch[*].skin` or any persisted state, so it's automatically never saved;
  gated on `devOn` and cleared on logout. `overlay` mode renders a magenta outline + diagonal cross at the
  frame's exact bounds (for alignment checks); `replace` mode renders the base frame tinted a clearly
  different magenta/blue hue. A new `activeSkin(char,frameKey,baseIm)` combines the dev test (when active)
  with the real `skinImg()` lookup, so every draw path only ever calls one function.
- **Reward rename (§10.9 amendment to R3)**: `ROAD_REWARDS[5]` is now `id:"bk"`, `name:"Costume BK"` (was
  `"kebab"`/"Costume kebab"), still `ready:false`. The BK costume uses the real Burger King logo —
  owner-approved brand-parody treatment, same as the existing McDonald's cup art; logged, no other code
  impact.
- **`refs/skins/README.md`** corrected: documents the two render modes, and the *real* reachable frame set
  per character (Uomo roccia: 10 frames — `f0-f2, e0-e1, fd0-fd2, fu0, fu3`; skippable: `f3, fd3, fu1, fu2,
  fd_e*, fu_e*`. Algidone: 27 frames, only `al_r7` skippable) instead of the earlier "draw everything"
  framing. Also documents the upcoming sheet + `<skin>_cells.json` + `cut_from_cells.py` delivery workflow.
- **`refs/skins/SPRITE_INVENTORY.md`** updated: marks the K1b hook as wired, and reclassifies the
  procedural item-art overlays (roccia's eating rock icon, Algidone's eating snack icon, the Acciaio ring/
  sweep visual) as explicitly **"no skin — pending owner decision"** rather than just "not a skin target" —
  Cinghiale stays a settled decision (hidden), not pending.
- **`refs/skins/cut_from_cells.py` intentionally not written this build** — no real skin sheet or
  `_cells.json` exists yet to build or test it against; documented as the plan in §10.6, to be written when
  K2's GEKA cap sheet actually arrives.
- **Verified in headless Chromium**: baseline with dev off is provably a no-op (`skinImg()` returns `null`
  everywhere, `activeSkin()` falls straight through to it, no character has `.skin` set on a fresh save).
  With dev skin active: `replace` mode pixel-sampled as strongly tinted magenta/blue on both roccia
  (`drawFace`) and Algidone (`drawAlg`); `overlay` mode pixel-sampled as visibly different from `replace`
  (natural colours, only the outline is magenta); a `replace`-mode skin missing a frame (`al_r0`) correctly
  falls back to `null` (plain base) while a provided frame (`al_st`) resolves with the right mode. The real
  dev-panel button was clicked through the actual DOM (not called directly) and correctly set/cleared
  `DEV_SKIN_TEST` via the production click handler; logout correctly cleared it. Built a 28-cell synthetic
  gallery (every frame direction/mode/character/Acciaio-tint combination, all through the real production
  draw functions) plus 21 real in-game screenshots (menu scene, splash logo, Lista desideri cards — proving
  each character's card reflects *that* character's own skin regardless of which one is active — career
  modal confirming no character art there, maze in all 4 directions + eating + power-up tinting for both
  characters) — published as an artifact for owner review, linked in chat. Zero console errors across the
  entire run.
- Not tested: real device/touch, an actual artist-drawn skin end to end (still nothing in `SKINS` — K2/K3
  populate it), in-game review by the owner.

## 0.3_16 — 2026-09-24
- **Pre-work, before C1**: `drawMiniPlaceholder`'s hardcoded-to-roccia icon (flagged in 0.3_15) confirmed
  **intentional** by the owner — it's the "Mangiaroccia" mini-game brand icon, not a per-character portrait.
  Noted as settled in `refs/skins/SPRITE_INVENTORY.md`. CLAUDE.md §1 gained a merge policy: if a push is
  rejected because `origin/main` moved, a merge is only allowed when the incoming commits touch none of the
  files the local commit changed (report it); any overlap stops and asks — never rebase, never force-push.
- **v0.4 C1 — character customisation page.** New full screen `screen="cust"` (`renderCust`/`bindCust`),
  not a modal (§10.9 decision) — matches the other full pages (Lista desideri, Opzioni, Percorso).
- **Entry**: a "Personalizza" button next to "Usa"/"Selezionato" on a character's card in Lista desideri ›
  Giocatore, shown only when `S.p.ch[k].skins.length>0` for **that** card's own character — independent of
  which character is currently active/played. On a real save, with no `ROAD_REWARDS` entry `ready:true` yet,
  nobody owns a costume, so the button is correctly invisible for both characters (verified).
- **Live preview**: a canvas animated at ~12fps through a real walk cycle, calling `drawFace`/`drawAlg`
  **directly** (never `drawHero`, which picks the *active* character) so the preview always shows the
  character whose card was opened, regardless of who's currently selected. A 4-direction toggle (▲▶▼◀)
  switches the preview through up/right/down/left using the same frame-selection logic `drawHero` uses
  internally (walk-cycle sequence, `fd`/`fu` prefix, flip only for the side view).
- **Costume section**: "Nessuno" + one button per owned costume (`cc.skins`), selecting one sets
  `S.p.ch[char].skin` immediately and persists — verified directly in `localStorage`, not just in memory.
  Costume display names come from `SKINS[id].name`, falling back to the matching `ROAD_REWARDS` entry's name
  if the registry doesn't have one yet, then the raw id. **Potere segreto** and **Squadra rocciamon**
  sections are inert placeholders reading "In arrivo", no player-facing "skin"/"asset" wording anywhere.
- **Dev-testing reachability without touching save data**: the "Personalizza" button's visibility condition
  also accepts `devOn && DEV_SKIN_TEST.char===k` (the K1b dev-skin-test toggle) as an alternative to real
  ownership — this only affects whether the *button appears*, never `S.p.ch[*].skins`/`.skin`. Verified: with
  the dev test active the page opens and the live preview shows the test overlay/replace correctly, but
  `S.p.ch.roccia.skins.length` and `.skin` stay exactly as they were (`0`/`null`) — nothing leaks into the
  save. The Costume section shows only "Nessuno" in that case, plus an explanatory note for the tester.
- **Navigation**: back button returns to Lista desideri › Giocatore (`go("wish")`, `tab` untouched so the
  Giocatore tab is still showing); `Escape` does the same, newly wired into the existing global keydown
  handler for `screen==="cust"` specifically (no other full screen besides modals had an Esc shortcut before
  this).
- **Verified in headless Chromium at a 320px-wide viewport** (phone-width requirement): every screenshot
  taken at that width — preview, all 4 directions, costume list, equipped state, placeholders — fits with no
  horizontal scroll. Confirmed: fresh save shows no Personalizza button anywhere; dev-skin-test reachability
  works and leaks nothing into the save; selecting a real granted test costume persists to `localStorage`
  and survives; switching back to "Nessuno" clears it; a real run still starts fine afterward. Zero console
  errors throughout.
- Not tested: real device/touch, the live preview with actual K2/K3 artwork (still nothing real in `SKINS`
  at this point in the session), in-game review by the owner.

## 0.3_17 — 2026-09-24
- **v0.4 K2 — GEKA SNC cap (Uomo roccia), first real skin.** Frames arrived pre-cut in
  `refs/skins/geka/frames/` + `geka_frames.json` (§10.9 K2/K3 pre-cut delivery format), nothing to cut.
- **Render mode changed from `overlay` to `replace`** (§10.9 amendment to the K1b default): the owner's art
  is full heads drawn with the cap already on, not an isolated cap graphic, so an overlay would have drawn
  the new head on top of the old one instead of replacing it.
- **New capability: oversized skin frames with an offset.** GEKA's frames are all larger than their base
  frame (the cap extends past the head's own crop, e.g. `f0` is 103×92 vs its base's 96×85 with `oy:7`).
  `SKINS[id].frames[key]` can now be `{b64,ox,oy}` instead of a bare base64 string (`ox,oy` = where the base
  frame's own top-left sits inside the larger skin image); a bare string still works for exactly-same-size
  frames. `loadSkinImgs()`'s validation changed from exact-size match to `width>=base.width &&
  height>=base.height` (still warns + skips a too-small frame, never throws), and stashes `ox`/`oy` directly
  on the loaded `Image` as `.skOx`/`.skOy`.
- **New `drawSkinLayer(ctx,skImg,base,dx,dy,dw,dh,flip)`** does the actual offset-aware compositing:
  `sx=dw/base.width, sy=dh/base.height`, draws the skin at `dx-ox*sx, dy-oy*sy`, size `skImg.width*sx ×
  skImg.height*sy`. When the caller already applied a horizontal flip (`ctx.scale(-1,1)`), the X offset is
  mirrored first (`skImg.width-base.width-ox`) so oversized art stays on the correct side once mirrored,
  instead of jumping to the wrong edge. `drawSkinned()` now takes a `flip` parameter (all 9 call sites
  updated: `drawFace`/`drawEat` pass their own `flip` var, `drawAlg` passes `sideArt&&o.flip`, the menu
  scene's Algidone branch passes its own turn-around flip condition, the remaining static-portrait call
  sites never flip so pass nothing) and, in **`replace` mode, skips drawing the base frame entirely** —
  the offset-positioned skin image alone covers it, rather than drawing the base underneath first and then
  overdrawing it at the base's own (now-wrong) rect.
- **`SKINS.geka`** embedded: `char:"roccia"`, `mode:"replace"`, `name:"Cappello GEKA SNC"`, all 10 real
  frames (`f0-f2, e0-e1, fd0-fd2, fu0, fu3`) as `{b64,ox,oy}`. `ROAD_REWARDS[3].ready` flipped to `true` —
  tile 3 now actually claims and grants the cap, no longer behaves like a "?" tile once unlocked.
- **`index.html` size delta: +146,666 bytes (+143.2 KB)** — the 10 embedded PNG frames account for
  essentially all of it (~140 KB base64), the rest is the offset-compositing code itself.
- **Verified in headless Chromium**, extensively:
  - Registration sanity: `SKINS.geka` has the right mode/char/10 frames, `IMG.sk_geka_f0` loaded at its
    declared 103×92 with `skOx:0,skOy:7` matching `geka_frames.json` exactly.
  - Maze, all 4 directions + side eating, with the cap equipped: **left-facing verified visually** — the
    mirrored offset math keeps the cap art coherent (not flipped to the wrong side or misaligned) when the
    character turns around; **up-facing verified visually** — the cap's large `oy` offset correctly places
    it above the head's own crop instead of being clipped.
  - **Acciaio-equivalent tint** (the power-up reversal, same `drawTinted` code path Acciaio uses) confirmed
    tinting the **entire replace-mode composite** red, not just the base head — `drawTinted` still needs no
    skin-specific handling, exactly as predicted in K1b.
  - Menu scene, Lista desideri card, and the C1 Personalizza preview (all 4 directions) all show the cap
    correctly. Career modal confirmed unaffected (text only, as already documented).
  - Pond-throw cutscene (`prTestKick`, phase-polled rather than timed) shows the cap on the thrown/splashed
    player portrait. Professor dialogue portrait (`prDrawPlayer`, reached via the real intro → "sì" flow,
    polled for the `spk:"plr"` line) shows the cap on the talking portrait.
  - **Full real (non-dev) claim flow from a wiped save**: `S.p.pr.seen=true` + combined gironi ≥3 → tile 3
    `claimable` → milestone popup correctly queued (and correctly ordered behind the save's other pending
    popups) → "Guarda" opens the roadmap on tile 3 → claiming opens the gift modal → opening the gift marks
    `S.p.road.claimed[3]` and adds `"geka"` to `S.p.ch.roccia.skins` → the real (non-dev) Personalizza button
    now appears on the Lista desideri card → selecting "Cappello GEKA SNC" there sets
    `S.p.ch.roccia.skin="geka"`, persisted to `localStorage` → a fresh run started afterward shows the
    character wearing it. Zero console errors across the entire run.
- Not tested: real device/touch, in-game review by the owner, K3 (Algidone's costume — next).

## 0.3_18 — 2026-09-24
- **v0.4 K3 — Costume BK (Algidone), second real skin, same pipeline as K2.** Frames arrived pre-cut in
  `refs/skins/bk/frames/` + `bk_frames.json`, nothing to cut. `al_r7` intentionally absent from the 27
  frames — it's never shown in game (unused index in the rolling animation's `%7` cycle, documented since
  K1a), so there's nothing to draw a costume variant for.
- **`SKINS.bk`** embedded: `char:"algidone"`, `mode:"replace"`, `name:"Costume BK"`, all 27 real frames
  (`al_st`, `al_w0-7`, `al_d_st`, `al_d0-3`, `al_u0-5`, `al_r0-6`) as `{b64,ox,oy}` — reusing the exact same
  offset-aware compositing (`drawSkinLayer`) K2 built, no code changes needed beyond the embed itself.
  `ROAD_REWARDS[5].ready` flipped to `true` — tile 5 now actually claims and grants the costume.
- **`index.html` size delta: +380,195 bytes (+371.3 KB)** — 27 embedded PNG frames (larger than GEKA's 10:
  full-body art vs. head crops), essentially all base64.
- **Verified in headless Chromium**, extensively:
  - Registration sanity: `SKINS.bk` has the right mode/char/27 frames, confirmed `al_r7` is **not** in the
    registry and never got an `IMG.sk_bk_al_r7` entry; `al_w3`'s declared offset (`w:76,h:100,ox:1,oy:0`)
    matches what actually loaded.
  - Maze, all 4 directions + the two side-walk frames that actually carry a 1px offset (`al_w3`, `al_w7`,
    the ones the task flagged specifically) — **verified both facings of each**, confirming the mirror math
    holds even for a small offset, not just GEKA's larger ones.
  - **Rolling during power-up** (`al_r0-6`) shows the costume's compact rolling-ball pose correctly.
  - **Power-up reversal tint** (Algidone's Acciaio-equivalent — same `drawTinted` path, green instead of
    roccia's red) confirmed tinting the whole replace-mode costume, rolling pose included.
  - Menu scene, Lista desideri card, splash logo (algidone selected), HUD lives icons, the C1 Personalizza
    preview (all 4 directions), the pond-throw cutscene (phase-polled), and the professor dialogue portrait
    (reached via the real intro → "sì" flow, polled for `spk:"plr"`) all show the costume correctly.
  - **Full real (non-dev) claim flow from a wiped save**: `S.p.gam.won=10` → tile 5 `claimable` → milestone
    popup correctly queued behind the save's other pending popups → "Guarda" opens the roadmap on tile 5 →
    claiming opens the gift modal → opening it marks `S.p.road.claimed[5]` and adds `"bk"` to
    `S.p.ch.algidone.skins` → the real Personalizza button appears → selecting "Costume BK" sets
    `S.p.ch.algidone.skin="bk"`, persisted to `localStorage` → a fresh run shows the character wearing it,
    HUD lives icons included. Zero console errors across the entire run.
- Not tested: real device/touch, in-game review by the owner. Both roadmap skin rewards (K2, K3) are now
  fully shipped — remaining v0.4 work is M0-M9 (Algidone's mini-game) and REL.

## 0.3_19 — 2026-09-24
- **M1 — "Ferma Algidone!" engine skeleton** (`screen="fa"`). Nothing player-facing yet: reachable only from the dev
  panel (new "Ferma Algidone! — scheletro motore (M1)" row). Writes no progress.
  - Level data format `FA_LEVELS[]` (pure data): girders, ladders incl. broken ones, start/Algidone/goal/grill zones,
    per-floor palette, plus the promoted design decisions (safe zone `safeXEnd:90`, `flameMinX:150`, `wallGirder:0`).
    Floor 1 "Coccia" = the D2/D5 layout in a 360×560 logical world (HUD will sit above the canvas in M4).
  - `startFerma`/`faExit`, `ensureFA` lazy image loader, fixed-timestep loop (60 Hz accumulator, max 5 steps/frame),
    responsive canvas (uniform fit, DPR-aware, integer-safe pixel rendering), code-drawn girders/ladders from the
    palette, dev-only debug zone overlay. Esc / back / ✕ leave to the menu.
  - Real art embedded per the round-4 amendment: **`fa_bg_coccia`** backdrop (the first chunk that draws it),
    scaled to 360 px wide and centre-cropped. The other 38 frames are embedded by the chunk that first draws them.
- **`index.html` size delta: +77,471 bytes** (one 53 KB PNG as base64 + ~5 KB of code).
- Verified in headless Chromium: menu renders, a maze run starts, dev-entry screen loads, loop ticks, backdrop + girder
  pixels drawn, Esc returns to the menu, resize re-fits the canvas, zero console errors.
- Not tested: real device/touch, iOS/Safari. Backdrop is busy behind the girders — legibility is for the owner to judge
  before M2 (girders can be given a darker outline without touching the art).


## 0.3_20 — 2026-09-24
- **Bugfix**: the dev-panel "Ferma Algidone!" button (`#mgfa`, added in 0.3_19) did nothing. Root cause: `bindOpt` only forwards
  a whitelist of selectors to `bindDev`'s click handler, and `#mgfa` was missing from it, so the click fell through to
  `optClick` and was ignored (no error). Added `#mgfa` to the whitelist; nothing else changed.
- **`index.html` size delta: +6 bytes** (`#mgfa,` in the whitelist; version string is the same length).
  to this build: measured against the committed 0.3_19 file, the diff itself is 2 lines / +4 chars).
- Verified in headless Chromium by **clicking the real button** (desktop 1280x800 and mobile 390x780 with touch tap): splash → menu →
  Opzioni → Sviluppatore → Strumenti di test → Avvia → `screen="fa"` canvas renders, ✕ returns to the menu, zero console errors.
- Not tested: real phone. The 0.3_19 smoke test called `startFerma()` directly, which is why it missed this.

## 0.3_21 — 2026-09-24
- Ferma Algidone!: layout change. Algidone is now **top right, facing left**, mirrored at draw time (`ctx.scale(-1,1)`), PNGs untouched.
  Embedded `fa_alg_idle0/1` (first frames drawn; drawn at x0.5, feet on the top girder, 2-frame idle).
- `FA_LEVELS[0]`: top girder now slopes down to the LEFT (20,102)→(340,80) (≥79 px headroom kept: art top at y≈3); goal zone
  moved beside him (x 215–275, not under him); ladder to the top stays at x=60 (far from Algidone). **Bottom girder flipped** to slope
  down to the RIGHT (20,419)→(340,441) so, with 5 girders and items starting right, the zigzag ends at the grill (bottom right)
  instead of rolling onto the spawn. Spawn (bottom left), safe zone x<90, flame bound x≥150, grill and walls unchanged.
- `FA.debug` zones updated (Algidone footprint added, zones follow the slopes).
- **`index.html` size delta: +39,644 bytes** (two idle frames + code).
- Verified by real clicks (desktop + mobile touch), zero console errors. Not tested: real device.

## 0.3_22 — 2026-09-24
- **M2 — Ferma Algidone! player movement** (dev entry only, no save changes, no items/HUD/lives).
  - Climber = Uomo roccia head only, always (whatever character is selected): side `f0`–`f3` walking, `fu0`–`fu3` climbing with a
    code-driven tilt/squash, jump = code-only stretch/squash. Drawn through `drawFace`, so the equipped **GEKA** hat shows via the
    existing skin hook.
  - Physics from D3 (`FA_PHYS`: g 980, walk 120, climb 105, jump -330, snap 28, coyote 80 ms, buffer 100 ms, fall 95 px), fixed
    timestep (accumulator already clamped: hidden tab / lag spike can't teleport).
  - DK rules: no jump on a ladder; grab only within the snap tolerance and only in the direction the ladder serves; broken ladders
    stop at the gap and can't be entered from above; walking off an edge = fall (a girder can't be re-landed once left);
    walls at the bottom-girder ends.
  - Fall damage measured only from where the ground was left in free fall (reset on landing/ladder grab/respawn); threshold 95 px.
    Fatal → stub `faDie(cause)` = respawn at start + debug label "Ultimo danno". Slopes, girder steps, leaving a ladder never count.
  - Goal zone: sets `FA.goal` + debug text only (win message is M4).
  - Input: arrows/WASD + Space/Z, and an on-screen portrait pad (▲ ◀ ▼ ▶ + Salta, hold via pointer events).
- **`index.html` size delta: +6,283 bytes** (code only, no art).
- Verified headless (real key presses / real touch events via CDP, desktop + mobile, 30 checks, zero console errors): walk, jump apex
  (~53 px measured vs 55.6 theoretical), no jump on ladder, broken ladder, snap tolerance, full climb g0→g4 and goal flag,
  1-floor drops survive (62/63 px), the two 107 px steps are fatal, synthetic 2-floor fall fatal, walls, lag-spike clamp, GEKA hat
  drawn, ✕ returns to the menu. Maze run still starts.
- Not tested: touch feel on a real phone, real-device performance, other skins on the climber (only GEKA), iOS/Safari.
- **Heads-up for the owner**: girder-to-girder gaps are 62/63/85/106–107 px depending on the end, so with the 95 px threshold the
  edge steps g3-left→g2 and g2-right→g1 (107 px) are fatal while the others are survivable. Same as D3's geometry; tuning is M9.

## 0.3_23 — 2026-09-24
- Owner feedback on M2. **Climbing view by direction**: UP (ArrowUp/W, on-screen ▲) uses the `fd` set, DOWN (ArrowDown/S, ▼) the `fu` set —
  the same convention as the maze (`drawHero`, fix 0.2_43; names follow the crop row, not what the frame shows). `fd` shows an upside-down
  face, `fu` the back of the head. Standing still on a ladder keeps the last direction (`FA.p.cdir`).
- **Scale +20%**: climber head 30→36 px, hitbox 22×31 (`FA_PHYS.hw/hh`, drawn in the debug overlay), Algidone ×0.5→×0.6 (≈74×95).
  World height 560→600, whole level shifted down 40 px; gaps between girders, jump and physics untouched. Algidone's head top is at y≈23.
- **Fall threshold 95→115 px** (largest single-floor drop is 107; a 2-floor fall is ≥125, still fatal). M9 may retune.
- **`index.html` size delta: about +0.9 KB** (code only). Real-click/key tests (30 checks) re-run and pass; 107 px steps now survive.

## 0.3_24 — 2026-09-24
- **M3 — Algidone throws + items** (Ferma Algidone!, dev entry only, no save changes; lives/HUD/scoring are M4).
  - Algidone: idle ↔ throw cycle with `fa_alg_throw0-3` (mirrored like idle, x0.6); the item spawns on the release frame (frame 2).
    Pause between throws 1.6–3.0 s (D2). Eat/angry frames not used.
  - Engine with per-level config (`FA_LEVELS[i].items`: throw weights, throw pause, ladder chance, meat, grill). Floor 1 = salsicce + porchetta
    (3:1). **Carne (bounce), griglia + flame spawn are built but off on floor 1**; dev panel button **"+ carne/griglia"** starts a run with them on.
  - Salsicce roll downhill along the zigzag (verso = pendenza della trave, so g0 rolls right to the grill), code-driven roll rotation, sometimes
    take a ladder down (D2: 6% per step within 5 px; ladders that lead DOWN from that girder, unbroken only — D2's demo looked at the wrong ladder set);
    porchetta slow (34), hitbox 60 tall (> jump apex ~53) = un-jumpable, wobbles; carne bounces (2 hops per floor, then down a floor);
    grill art (`fa_griglia0-1`) bottom right, a sausage falling over it spawns a flame that patrols x>=150 (max 3), 6 s.
  - Hits need vertical overlap (never x alone); bottom-girder items are harmless left of x=90; "jumped over" is an event (`FA.jumps`, debug counter only).
    A hit calls `faDie`, which now also clears ALL items/flames and restarts the throw delay at 2.5 s (full death rules = M4).
  - Item contact width is a forgiving `FA_PHYS.hitw`=16 (body box stays 22): with the +20% body a standing jump could no longer clear a sausage.
  - Embedded only what M3 draws: `fa_alg_throw0-3`, `fa_salsiccia`, `fa_porchetta0`, `fa_carne0-1`, `fa_fiamma0-3`, `fa_griglia0-1` (art untouched).
- **`index.html` size delta: +102,286 bytes.**
- Verified headless (real clicks/keys/touch + deterministic stepping, 23 M3 checks + 30 M2 regression checks, zero console errors): idle↔throw and spawn on
  the release frame, zigzag g4→g0 to the grill, ladder drops, D2 ladder rate, jumping a sausage counts and doesn't hit, standing still hits, porchetta hits
  at 3 timings, safe zone, vertical overlap (item 63 px above = no hit), respawn clears items, dev toggle by real click (meat hops, flame spawns, x>=150).
- Measured: the clear-jump window over a sausage is only ~22–26 px of takeoff distance (~0.06–0.09 s) — same tightness as the D2 demo. Flagged for M9.
- Not tested: touch feel on a real phone, real-device performance.

## 0.3_25 — 2026-09-24
- Owner feedback on M3 (Ferma Algidone! only):
  - **Touch layout**: d-pad bottom-left (66 px buttons), big round yellow SALTA (104 px) bottom-right, 40 px gap, vertically aligned;
    the dev achievement toast now also avoids `#fapad` (it was covering the pad). Keyboard unchanged.
  - **Porchetta is clearable**: hitbox = sprite (36×19). Needs a running jump (window ≈0.25 s; standing impossible).
  - **Ladder refuge**: any player ≥ ~17 px up a ladder (incl. broken ones: 35/41 px) lets items pass under.
  - **Sausage jump window** ≈0.23 s standing (target ≥0.2): contact width 10 (body box 22), sausage hitbox r8×h14. Apex/gravity untouched.
  - **Items ×0.6**. **Grill ending**: item slides in, `fa_griglia1` flare, code smoke puff + sparks, glow settles; same hook spawns the flame (floor 3).
  - **Meat hop** capped to 34 px. **Building** `fa_bld_coccia` as a layer behind the girders (×0.6, bottom on the top girder); world 600→610.
- **`index.html` size delta: +75,812 bytes** (the 54 KB building PNG as base64 + code).
- Verified headless (real clicks/keys/CDP touch + deterministic stepping): 24 new checks, 22 M3, 30 M2 regression (one flaky timing failure under CPU load, passes on rerun); maze run starts.
- Not tested: real-phone touch feel.

## 0.3_26 — 2026-09-24
- **M4 — Ferma Algidone! lives, death rules, stock, score, HUD, pause** (dev entry only; no save/reward changes; no difficulty scaling).
  - **HUD** (D5 layout, DOM bar above the canvas): score · stock-pile icon + stock bar · 3 life icons (Uomo roccia head, via the skin hook) · pause button.
    Stock pile = `fa_scorte0-3` (full → 2/3 → 1/3 → empty); the bar goes red under 25 percent.
  - **Stock**: 90 s steady drain (`FA_LEVELS[i].stock`), refilled on every respawn / restart; empty = exactly one life.
  - **Death rules (§10.9)**: hit/fall/empty stock → 0.8 s pause + red flash, player blinks, everything frozen → all items and flames cleared → respawn at start →
    2 s blinking invulnerability (blocks hits; falls and empty stock still count) → throws resume after a 2.5 s grace. Last life → game over panel "Scorte perse!" (Riprova / Esci).
  - **Scoring** (D5 values): +10 per sausage/meat jumped, +20 flame, **+30 porchetta**; "+N" pop-up; goal bonus = floor(stock) × 10; goal → "Piano completato!" panel (Rigioca / Esci); kick-out animation is M5.
  - **Algidone**: `fa_alg_eat0-2` now and then between throws (22 percent of cycles, 1.65 s), `fa_alg_angry0-1` while the player is on the top two girders or stock is under 25 percent; mirrored.
  - **Pause**: HUD button, Esc, P; auto-pause on `visibilitychange`; panel Riprendi / Esci; timer, items, Algidone all frozen; input ignored. Esc in a game-over/win panel exits.
  - Removed the ✕ button (exit is in the pause panel).
- Embedded only what M4 draws: `fa_alg_eat0-2`, `fa_alg_angry0-1`, `fa_scorte0-3`. **`index.html` size delta: +119849 bytes.**
- Verified headless (real clicks/keys/touch + deterministic stepping): 30 new M4 checks (HUD, steady drain, empty = one life, death rules, invulnerability, 3 deaths → game over, Riprova, jump scores, goal bonus, win/over freeze, eat/angry, real-click pause, Esc/P, visibilitychange, Esci) + M2 31 / M3 22 / M25 24 regressions; zero console errors. Two timing-flaky checks in my own scripts (random throw count; key-hold polling).
- Not tested: real-phone feel, real background-tab behaviour (visibilitychange was dispatched, not a real tab switch).

## 0.3_27 — 2026-09-24
Ferma Algidone! — owner feedback after the phone test of 0.3_25/0.3_26.
- **Hit through girders (fixed).** Reproduced headless: with the player under the narrow-gap girder ends (gap 62-66 px, jump apex 55 px + 31 px body) a jump put the head into the
  box of an item rolling on the girder above, with the girder in between. Root cause: `faCollide` only tested box overlap, never what lies between. New `faSeparated()`:
  an item hits only if no girder surface lies between the item's base and the player's feet (centre of the body while on a ladder) at their x. 23 through-girder hits in the
  repro grid (4 girder pairs x 6 x positions x sausage/porchetta x stand/jump/run-jump; the 4 left are fall-off-the-edge artefacts of the test) -> 0. Ladder-drop hits (player on
  the landing girder / on the ladder), same-girder hits and the ladder refuge unchanged; jump-window measurements identical before and after.
- **Cooked sausage**: `fa_salsiccia.png` has not been replaced since `60c07bf` - waiting for art, nothing changed.
- **Stock**: no refill on respawn; the value is kept across deaths and reset only at floor start / Riprova / Rigioca. Each death: Algidone plays the eat animation during the death pause
  and the stock drops 10 s (clamped at 0). Normal drain is paused in the death pause and in the pause menu (as before). Stock empty = **immediate game over "Scorte perse!"**
  regardless of lives; if the death penalty empties it, game over follows the death pause. Hits/falls still cost one life.
- **Eat frames**: `review/eat_compare.png` (idle0-1, throw0, eat0-2 drawn exactly as in game). The draw path is identical (124x158 cell, x0.6, bottom-centre, mirror, smoothing off);
  the difference is in the art (eat1/eat2 beardless, puffed cheeks). Game now uses `eat0` only; bite/chew is code (squash + bob) after the grab.
- **`index.html` size delta: +1232 bytes.**
- Verified headless: repro grid before/after, regression (ladder drop x2, refuge, same-girder hit), 9 stock checks, real-click desktop (keys) + mobile (touch) smoke, 0 console errors.
- Not tested: real-phone feel of the new hit rule.

## 0.3_28 — 2026-09-24
M5 — Ferma Algidone! floor 1 "Coccia": intro card + kick-out win sequence.
- **Intro card** (`faIntro`) at floor entry: first start, Riprova, Rigioca; not on respawn. Follows the girone-card pattern (panel with picture, title, text): `fa_bld_coccia` at x1 (294 px, smoothing off,
  `image-rendering:pixelated`), "Piano 1 — Coccia" + "Algidone si è preso Coccia! Fermalo prima che finisca le scorte!". Auto-closes after 2.5 s; tap on the card or Enter skips. Stock, throws and
  player are frozen meanwhile. Pausing during the card and resuming re-shows it. No downscale on a 390 px phone (card 338 px wide); on phones under ~340 px the picture shrinks by at most a few px (`max-width:100%`).
- **Kick-out** on reaching the goal zone (`faWin` -> state `kick`): stock frozen, throws stopped, items cleared, no hits possible. Climber headbutt (code-only lunge + hop + lean on the existing head frames) ->
  `fa_alg_kick0` hit -> `kick1` on a 35 px arc away from the player (right, mirrored as always) -> `kick2` sitting dazed at x=320 (kept in frame, small squash on landing and a bob) -> climber celebrates with two hops
  (code-only). 3.1 s in total, then the "Piano completato!" panel with the stock bonus counting up (~1.2 s; the score counts with it). Panel stays Rigioca / Esci (floors 2-3 are M6).
- Embedded `fa_alg_kick0-2`. `eat1`/`eat2` stay embedded but are no longer drawn (see 0.3_27). **`index.html` size delta: +66317 bytes.**
- Dev button **"Test uscita Algidone"** in the Ferma Algidone! dev accordion (`#mgfk`, added to the `bindOpt` whitelist): starts a dev run with the player in the goal zone, no intro. Saves nothing.
- Fixed while testing: the intro's tap-to-skip handler also caught the pause panel's "Riprendi" (both live in `#fapanel`); now skips only when not paused.
- Verified headless with real clicks (desktop keys/mouse, mobile touch): intro open/frozen/auto-close/skip (tap + Enter), pause during intro, no intro on respawn, Riprova and Rigioca show it again, kick timeline
  frames (`review/m5_kick_d.png`, `m5_kick_m.png`), bonus count-up, dev button, 0 console errors.
- Not tested: real-phone feel and timing of the kick-out, the card on phones narrower than 340 px.

## 0.3_29 — 2026-09-24
Ferma Algidone! — owner feedback 2 after the phone test of 0.3_27/0.3_28.
- **Cooked sausage**: the owner's new `fa_salsiccia.png` (77x29, already horizontal, cut from the `fa_bld_fabbrica` sign) embedded (it arrived as `refs/ferma_algidone/fa_salsiccia.png`, commit `1c69976`;
  moved into `frames/` replacing the old file). Drawn x0.5 (39x15), no base rotation (a lying sausage rolls along its axis, so it no longer spins); hitbox unchanged (r8 x h14).
  Standing-jump window re-measured at 0.25 px steps: **0.229 s** (jump-press distance 15.5-31.25 px at 70 px/s), same as before - the hitbox did not change. Art issue 1 resolved.
- **Eating**: the full `fa_alg_eat0-2` animation (grab -> bite -> chew) is back, the eat0-only code chew is gone. The 10 s death bite uses it. Art improvement of eat1/eat2 is logged in §8 as a future patch.
- **Ladder grab**: only when the player's centre is within +-8 px of the ladder centre (`FA_PHYS.snap` 28 -> 8), then it snaps to the centre; same for grabbing down (verified at 0, +-7 grab / +-9, 20 no).
- **Desktop keys**: Up/W = climb when inside a ladder's grab zone (direction the ladder serves), otherwise jump (on key press, not while held). Space/Z still jump. Touch controls unchanged.
- **Extra bottom row**: measured the empty space below the level (floor 1 has no grill): 112 world px = 115 px on a 390x844 phone / 107 px on 360x800, against a girder gap of 85 (87 / 81 px), so it fits **without growing the world** (610 stays).
  New bottom girder (slopes down-right, spawn left, safe zone x<90, flames x>=150, end walls, grill at its low end). The old bottom girder now slopes down-left and starts at x=110, so items dropping off its left end land
  on the new bottom at x=110 and roll right to the grill - **never on the spawn**. New ladder x=210 (new bottom -> old bottom). All indices shifted (start still gi 0, Algidone/goal/building gi 5).
  The chasm under the left part of the second girder is now a fatal fall (the old bottom girder no longer reaches x<110). Fall threshold unchanged (115; the widest single drop is 107).
  Floor 3's grill (M6b) does not fit below the new bottom girder in a 610 world (dev "+ carne/griglia" grill is placed at y=551 for now): decide in M6b (grow the world ~35 px or a smaller grill).
  `refs/ferma_algidone/review/layout_extra_row.png` (new layout on both phone sizes).
- **Floor exit = Algidone climbs away** (floors 1-2; dev run on floor 1): stock frozen, throws stopped, items cleared, no hits. Algidone (code only, `fa_alg_throw1` arms up) tilts/bobs and climbs a code-drawn ladder off the top
  of the screen in about 2.5 s (ladder slides in first), the climber celebrates with two hops, then the stock-bonus panel (Rigioca / Esci until M6). The kick-out stays in the code for the last floor (`lv.last`) and the dev preview.
- **Dev buttons**: "Test uscita Algidone" (the floor's exit = climb) and new "Test cacciata finale" (kick-out preview); both dev runs, save nothing, both in the `bindOpt` whitelist.
- **`index.html` size delta: +13635 bytes.**
- Verified headless: real clicks/keys (desktop) and touch (mobile) - intro/pause/skip/Riprova/Rigioca flow, both dev buttons in real time, climb + kick frame strips (`review/m6_climb_d.png`, `m6_kickfinal_m.png`),
  real ArrowUp/Space, ladder-grab boundary tests, sausage window, girder-hit grid on the new indices (0), scripted spawn-to-goal run through every row, 90 s item-flow run (0 frames of items in the safe zone), 0 console errors.
- Not tested: real-phone feel of the tighter grab, the new layout and the climb-away.

## 0.3_30 — 2026-09-24
M6a — Ferma Algidone! floor 2 "Macelleria" (conveyor belts) + floor progression.
- **Floor progression**: the floor-1 win panel now has **Avanti** / Esci; Avanti loads floor 2 with its intro card (`fa_bld_macelleria` at x1, natural 213x126, "Piano 2 — Macelleria" + "Algidone ha rilevato la
  Macelleria! I nastri cambiano verso quando meno te lo aspetti: tieni il passo!"). **Score and lives carry over, stock resets to 90 s per floor.** Riprova (game over) restarts the **current floor** (3 lives, score back to
  what it was on entering the floor) - I think that is better than going back to floor 1 since the earlier floors are already cleared. On the last available floor the panel is Rigioca / Esci and Rigioca restarts from floor 1
  (score 0, 3 lives). The panel picks Avanti automatically as soon as a next floor exists (M6b).
- **Level** (`FA_LEVELS[1]`): backdrop `fa_bg_macelleria`, building `fa_bld_macelleria` in-level x0.6 (same recipe as Coccia), same 360x610 world and the same 6-row structure/ladders as floor 1, palette recoloured
  (red girders, white ladders). Rows 2 and 4 are **conveyor belts** (flat).
- **Conveyors** (`g.conveyor={v,rev,dir}`, `g.flow` = exit end): code-drawn belt (dark body, yellow chevrons scrolling in the direction of travel, end rollers); the chevrons blink red for the last 0.7 s before a reversal.
  The belt carries the player (never off an end by itself: the push stops 6 px from the ends; walking off is still possible) and items: an item's speed = its own roll speed in the flow direction + the belt's, so nothing ever stalls
  (belt 45 < sausage 70 / meat 55). Row 4 runs constantly toward the exit end; row 2 reverses every 5 s. Belts freeze during intro, death pause, pause and the exit sequences.
- **Items on floor 2**: sausages + porchetta as on floor 1 where girders remain (rolling downhill, ladder drops, refuge, jump windows); **meat** (`fa_carne`, x0.6) does not hop here (`meatHop:false`): it slides like a sausage,
  rides the belts and drops off the ends; bouncing meat returns on floor 3. Throw weights 3/1/2, pause 1.4-2.6 s, ladder drop 6 %. Spawn-safe rules carry over (verified: 0 frames of items in the safe zone in a 90 s run).
- **Exit** = the same climb-away as floor 1; after floor 2 the panel is Rigioca / Esci until M6b.
- **Dev**: new "Piano 2 (nastri)" button (dev run, saves nothing, in the whitelist); "Test uscita Algidone" / "Test cacciata finale" unchanged (floor 1).
- **Proposed tunables for M9** (logged in §10.9): belt speed 45 px/s, reversal period 5 s (only row 2), warning 0.7 s, floor-2 throw pause 1.4-2.6 s, weights 3/1/2.
- Layout image: `refs/ferma_algidone/review/m6a_layout.png` (390x844 and 360x800).
- Embedded `fa_bg_macelleria` and `fa_bld_macelleria`. **`index.html` size delta: +92230 bytes.**
- Verified headless: real clicks + touch for the whole flow (dev exit -> Avanti -> floor 2 intro at natural size -> play -> game over -> Riprova -> exit -> Rigioca), belt push/clamp/against-belt walking, reversal,
  items on belts (with/against), meat without hop, scripted spawn-to-goal run through every row of floor 2, 90 s item flow (belts and meat exercised, 0 safe-zone frames), floor-1 regressions (intro, stock, girder hits,
  ladder grab, Up key, sausage window still 0.229 s), 0 console errors.
- Not tested: real-phone feel of the belts (speed, readability of the chevrons, the reversal warning), floor-2 difficulty.

## 0.3_31 — 2026-09-24
Owner feedback 3 after the phone test of 0.3_29/0.3_30 (all OK).
- **Costume BK investigation (no reward bug).** Headless on a REAL non-dev save (no dev role, no sim): `S.p.gam.won` = 10 -> roadmap tile 5 `claimable` -> milestone popup "Traguardo raggiunto!" -> Guarda -> road with the tile
  highlighted -> tap -> gift container -> open -> `S.p.ch.algidone.skins = ['bk']` **while playing Uomo roccia** -> "Personalizza" appears on Algidone's card -> equip -> the card canvases change and `activeSkin` returns the BK
  frames (`al_st`, `al_w0`) / GEKA frames (`f0`, `fd0`). Tile 3 -> GEKA hat works the same way. Reward mapping, grant, migration, card button and draw hooks are all fine.
  **Root cause of "not available": the condition was not met.** `S.p.gam.won` only increases when a hand is won in a REAL run (`B.dbg` false): the El Gamblador random encounter from girone 5 onwards (15 percent per eligible girone,
  and it needs a price of at least 50). The dev button, `SIM` and the Giochi card (a display-only card, it does not launch anything) never count. The progress is stored as `S.ach.prog.m1` (achievement "Il banco trema", category
  Minigiochi, 10 hands). **One real defect found and fixed:** tapping a locked tile 3 or 5 said "Sblocca al girone 3/5", which is wrong (neither depends on the girone; tile 3 was meant to have no hint) -> now "Tessera ancora bloccata".
- **Reward preview shows the skin worn**: the gift pop-out and the milestone popup draw the character wearing the reward (`hero:<char>:<scale>:<skin>`, a preview override `SKIN_PV` that never touches the equipped skin).
  Checked for Costume BK (Algidone) and the GEKA hat (Uomo roccia). There is no separate roadmap-tile expand: tapping a claimable tile opens the gift directly, so tile faces (pokéball / cards) are unchanged.
- **"Sblocca tutto" (sim overlay) extended** - still an overlay on a copy (`S.realP`), never writes real progress, never queues popups; turning it off restores the real state (verified byte-identical). Newly covered:
  both characters' skins (owned, equippable, "Personalizza" visible), all roadmap tiles (tiles 3 and 5 claimable; the other tiles just unlocked, "?" stay "Premio in arrivo"), a **Ferma Algidone!** card (G4) in Giochi with one
  button per existing floor (dev-style test run, saves nothing). Already covered before: level 100, 999999 sordi, all assets/ghosts, the El Gamblador / Rocciamon cards and the two extra Giocatore cards (shown, not playable
  as characters - not implemented yet).
- **Row 2 left end**: player-only invisible stop (`lv.stopLeft:[2]`, floors 1 and 2): walking left stops at the girder end, jumping there works (also while holding left: no drift over the edge), other rows still walk off,
  items are unaffected.
- **`index.html` size delta: +2173 bytes.**
- Verified headless (real clicks + touch): the BK/GEKA paths above, popup/gift screenshots (`review/reward_preview_m.png`), sim on/off round trip incl. the Giochi card and a floor-2 launch, row-2 stop on both floors, floor 1/2 regressions
  (intro, Avanti/Riprova/Rigioca, belts, spawn-to-goal), 0 console errors.
- Not tested: playing 10 real blackjack hands through a real run (the increment line was read, not exercised), the Obiettivi screen text for "Il banco trema".

## 0.3_32 — 2026-09-24
M6b — Ferma Algidone! floor 3 "Fabbrica di salsicce" + the final win.
- **Progression**: the floor-2 win panel now has **Avanti** -> floor 3 intro card (`fa_bld_fabbrica` at x1, natural 280x218, "Piano 3 — Fabbrica di salsicce" + "Algidone ha rilevato la Fabbrica di salsicce! Svita tutti i bulloni:
  senza, la sua fabbrica crolla."). Score/lives carry, stock 90 s, Riprova = current floor. Only floor 3 ends the run: its panel is Rigioca (from floor 1) / Esci.
- **Level** (`FA_LEVELS[2]`, `last:true`): backdrop `fa_bg_fabbrica`, building `fa_bld_fabbrica` in-level x0.6 on the top girder, the floor-1 six-row structure/ladders, hazard-yellow girders / light-blue ladders, row-2 player stop kept.
  No goal zone: **removing the last bolt wins**.
- **Bolts** (DK "100m" style, `lv.bolts`): 8 (two on each of rows 1-4, away from the ladder tops). Walking over one on the ground removes it (+50 points, sparks); **0.5 s later a 26 px hole opens in the girder** (`FA.gaps`), so it is a
  gap to jump over. Standing still on a fresh bolt drops you through the hole; falling through follows the normal fall rules (single-row drops are survivable). Items fall through holes too (rolling items, meat over a hole).
  Bolts are drawn in code (pulsing silver hexagon); girders are drawn in segments; HUD shows the bolts left (small hex + number between score and stock). Holes stay after a death; Riprova/Rigioca restore all bolts.
- **Hazards**: sausages + porchetta as before; **bouncing meat** (`fa_carne0-1` with the squash frame; hop unchanged at 34 px: it clears the girder above by about 5 px at the tightest spot, no retune); **grill ON the bottom
  girder at its low end** (x1.2 = 54x40, `fa_griglia0-1`, coals brighten on a hit; it is an obstacle: the player stops beside it, items slide into it). Every item that reaches the grill spawns a **flame** (`fa_fiamma0-3`, max 3, speed 60,
  6 s life) that patrols the bottom girder between x=150 and the grill, never near the spawn. **Proposal (implemented, tunable): flames may climb the ladder at x=210 to the second girder** with 35 percent chance per pass, never higher.
- **Final win**: last bolt -> state `collapse`: stock/throws frozen, items cleared, no hits. The structure shakes (1 s, growing), girders fall top-first (all except the bottom girder and the one the player stands on), ladders and
  the building fall with them, dust; Algidone (angry frames while it shakes) falls with `fa_alg_kick1` from the top girder to the bottom girder (x=190, away from the grill) and lands sitting dazed (`fa_alg_kick2`, small squash);
  the climber celebrates with two hops; 3.7 s in total. Then the victory panel **"Algidone è a terra!" / "Coccia, Macelleria e Fabbrica sono di nuovo al sicuro."** with the total score and the stock bonus counting up (Rigioca / Esci).
  The old headbutt kick-out (M5) is removed (`kick0` stays embedded, unused; `kick1/kick2` are used by the collapse). "Test cacciata finale" now plays this real sequence on floor 3 (holes already open).
- **Dev**: new "Piano 3 (bulloni)" button (dev run, saves nothing, in the whitelist); "Test cacciata finale" = the collapse; "Test uscita Algidone" = floor 1 climb-away; the "Sblocca tutto" Ferma card now lists floors 1-3.
- **Engine fixes** found on the way: items falling now land on the first girder below that actually supports them at that x (skips shorter girders and holes; before, an item leaving the left end of a belt row landed on the shorter girder
  below at a clamped position); items riding a belt can no longer be pushed backwards (porchetta 34 px/s against a 45 px/s belt drifted to -11): minimum 12 px/s toward the exit end (floor 2).
- **Proposed values, tunable in M9**: 8 bolts, +50 each, hole width 26, hole delay 0.5 s, flame speed 60 / life 6 s / max 3 / climb 35 percent, meat hop 34 px, weights 3/1/2, throw pause 1.4-2.6 s, collapse 3.7 s.
- Layout: `refs/ferma_algidone/review/m6b_layout.png` (390x844 and 360x800), collapse strips `m6b_collapse_d.png` / `m6b_collapse_m.png`. Embedded `fa_bg_fabbrica`, `fa_bld_fabbrica`. **`index.html` size delta: +155513 bytes.**
- Verified headless (real clicks, keys and touch): dev floor-1 exit -> Avanti -> floor 2 exit -> Avanti -> floor 3 intro (natural size) -> play -> game over -> Riprova -> last bolt by really walking onto it (keys and touch) -> collapse -> final panel
  -> Rigioca; the scripted all-8-bolts run; bolt pick / hole timing / jump over a hole / walking into a hole / standing on a bolt; sausage falling through a hole; meat clearance; flames (range, spawn, climb, cap; 0 safe-zone frames);
  floor 1/2 regressions (belts, stops, girder hits, sausage window 0.229 s, ladder grab, sim card); 0 console errors.
- Not tested: real-phone feel (bolt spacing, hole width, flame difficulty, the collapse timing and shake), floor-3 difficulty balance.

## 0.3_33 — 2026-09-24
Owner feedback 4 after the phone test of 0.3_31/0.3_32 (gameplay good).
- **Building scale per floor**: floor 2's `fa_bld_macelleria` (213x126) was tiny and crammed next to Algidone (x0.6). Buildings now match Coccia's on-screen width (176 px): Macelleria **x0.826** (176x104),
  Fabbrica **x0.629** (176x137, was x0.6 = 168 wide), both centred at x=270 like Coccia; Algidone stays x0.6 on every floor. `review/building_scale_m.png` (floors 2 and 3 on a 390x844 phone).
- **Riprova always restarts from floor 1** (3 lives, score 0), on any floor - amends 0.3_30's "Riprova = current floor". Rigioca (final panel) also restarts from floor 1.
- **Sblocca tutto**: the two future Giocatore cards (El Gamblador, Il Professore) read "In arrivo" instead of "Bloccato" while it is active (real state still says "Bloccato").
- **`index.html` size delta: +47 bytes.** Verified headless (touch): both buildings, Riprova from floor 3 -> floor 1 / score 0 / 3 lives, card labels real vs sim, floor-3 smoke, 0 console errors.
- Not tested: how the larger buildings look on a real phone.

## 0.3_34 — 2026-09-24
M7 — Ferma Algidone! audio (synth placeholders) + sound in every kind of run.
- **Root cause of the silence in dev runs**: Ferma Algidone! had **no audio at all yet** - M7 was not built, so no code path played a sound (nothing gated behind dev / test / `SIM()`; `beep`/`playSnd` only look at the Options "suono" switch,
  and the AudioContext was fine). Now every run type plays sound exactly like a real one: the dev floor buttons, "Sblocca tutto" (sim) launches from the Giochi card and the future real entry. Dev only blocks saving, never audio.
  Belt and braces: `startFerma` resumes the AudioContext inside the user gesture and the first pad touch resumes it again.
- **12 slots** in a new A0-layer bucket `SND.fa` (lookup: IndexedDB override -> built-in -> synth), keys `snd_fa_<slot>`, export targets **`sound.fa.<slot>`** (character `shared`): `jump` (salto), `land` (atterraggio), `climb` (passo sulla scala, one tic per 0.16 s),
  `throw` (lancio di Algidone), `hit` (colpo o caduta), `ping` (oggetto scavalcato), `win` (piano completato and the final victory), `low` (scorta sotto il 25 percento: one beep every 2 s), `bolt` (bullone tolto), `belt` (avviso di inversione,
  fired with the red chevron blink), `flame` (vampata della griglia / fiamma), `collapse` (crollo finale, ~1.6 s rumble). No music (M0 Q13). Synth levels in the same range as the maze sounds; the Options sound switch mutes them (verified).
- **Dev panel**: Options > Sviluppatore > Audio > "Ferma Algidone! · Suoni (12)" with Carica / ▶ / Rimuovi per slot (the generic `data-sf` / `data-sp` / `data-sr` handlers, already whitelisted; no sound on the dev buttons themselves).
  Options reset clears the IDB layer; `expAudioItems` and the export targets doc (`exportTargetsMd`) list the new targets.
- **`index.html` size delta: +3216 bytes.**
- Verified headless (real keys + touch, spies on `playSnd` and on the oscillator/buffer nodes): every slot fires from the real game code (jump, land, climb, throw, ping, hit, low in a floor-1 dev run; belt on floor 2; flame, bolt, collapse, win on floor 3;
  win on the floor-1 exit), AudioContext `running`, 14 oscillator nodes in a run, 0 when muted; upload of a real wav -> `SND.fa.jump` set, ▶ plays the custom buffer, export lists `sound.fa.jump`, Rimuovi restores the synth; launch from the
  Sblocca tutto Giochi card plays sound; 0 console errors.
- Not tested: actual audible output and loudness on a real phone (headless cannot hear), iOS/Safari audio unlock.

## 0.3_35 — 2026-09-25
**M8a — Ferma Algidone! integration part 1** (entry, encounter rule, Giochi card, unlock popup, save, dev buttons). No new art; no sordi/exp/achievements yet (M8b).
- **Save**: `S.p.fa={enc:0,seen:false}` (save-wide, both characters) in `DEF` + migration; old saves load with 0/false (verified with a save that has no `fa`).
- **Trigger** (`bjAfterClear`, El Gamblador's own logic untouched: guaranteed at girone 5 when `bjPrice>=50`, else 15 % from girone 6): Ferma rolls 15 % on the same gaps from girone 5 when El Gamblador does not fire
  (so normally from 6, and at 5 only if El Gamblador skipped it via the price gate); **forced** when `enc===0` from the gap of girone 10 on; a forced Ferma beats a random El Gamblador; one mini-game per gap. No price gate for Ferma.
  If Ferma fires at a gap where `miniInterlude()` would show (multiples of 5), the interlude card is shown after Continua / "Non ora" exactly as it would have been. Nuovo gioco and Hardcore identical. Dev runs and SIM never roll by themselves.
- **Invite** (`faInvite`, a centred modal with the Algidone icon): "Non ora" (declining counts nothing) hidden only on the forced first-ever encounter; "Fermalo!" -> `enc++`, `seen=true`, persist, then play.
- **Encounter mode** (`startFerma({run:true,encounter:N})`, `N=min(enc,3)`, `FA.enc={n,run,mult5}`): intro card adds "Obiettivo: 1 piano / N piani"; starts at floor 1 and ends after floor N: floors before N show **Avanti** only, the last floor (win panel, or the floor-3 final panel) and game over show
  one button **Continua**; pause "Esci" = encounter lost. No Riprova/Rigioca. `faExit` returns to the maze (`faBackToMaze`) as El Gamblador does (state "ready", 1.6 s), or to the interlude card when one was due.
- **Giochi card G4 "Ferma Algidone!"**: unlocked when `S.p.fa.seen`; icon = `fa_alg_idle0` drawn as in game (mirrored, x0.6, art untouched); honours `S.ov["game_3"]` label/colour/scale (+ dev pencil). Real player: one **Gioca** button = practice (3 floors, Riprova, no rewards);
  "Sblocca tutto" keeps its three floor buttons. Label fits (109 of 109 px in a 174 px card).
- **Popup**: the unlock queues the P1 "Nuovo minigioco!" popup once ever (`game:3`, also seeded in `seedPopSeen`); Guarda opens Lista desideri > Giochi. Fixed the double punctuation "Ferma Algidone!." in the popup body.
- **Dev** (in the `bindOpt` whitelist, save nothing): "Incontro 1 piano / 2 piani / 3 piani" (encounter mode, test, Continua -> menu) and "Forza incontro: no/sì" (the next gap of a dev jump / SIM run triggers Ferma at 100 %, one-shot; simulated encounter number cycles 1, 2, 3+).
  Dev/test/SIM encounters never touch `S.p.fa` and never queue popups. "Sblocca tutto" unchanged.
- **`index.html` size delta: +4274 bytes.**
- Verified headless (real clicks, desktop + mobile tap, `Math.random` stubbed only inside `bjAfterClear`): gap 6 -> invite with "Non ora" (declining leaves `fa` at 0/false); gap 6 with price>=50 -> El Gamblador and no Ferma; girone 5 with price>=50 -> El Gamblador; girone 5 with price 0 -> Ferma may roll;
  encounter 1 ends after floor 1 (Continua -> maze, stage kept, `enc:1`), encounter 2 after floor 2 (Avanti then Continua), encounter 3 after the floor-3 final panel, 4th encounter stays N=3; game over -> Continua; pause Esci -> maze; forced at girone 10 (enc 0) without "Non ora", Continua -> the "Girone 10 / Mangiaroccia ricomincia" card;
  girone 10 with enc>=1 and no roll -> interlude only; home -> popup -> Guarda -> Giochi card with Gioca -> practice (Riprova, `enc` null); old save without `fa` loads; dev buttons and Forza incontro leave `mgs_v1` byte-identical, queue empty; Sblocca tutto card keeps its floor buttons; 0 console errors.
- Not tested: real-device touch feel and timing of the invite/panels, and a random (unstubbed) encounter rate over many runs.

## 0.3_36 — 2026-09-25
**M8b — Ferma Algidone! integration part 2** (rewards, achievements, roadmap tile 10). Owner phone test of 0.3_35: OK.
- **Rewards** (amends the "formula x N" proposal): on an encounter **win** (last floor N cleared) the encounter's final score, stock bonus included, is added to the maze run's `G.score`; the normal end-of-run payout converts it (difficulty + limiter, `finishRun`). Loss, pause/Esci, practice (Giochi card), dev tests and SIM pay nothing
  (`faReal()`: `FA.enc.run && !FA.enc.dev && !SIM()`; paid once per encounter, `FA.paid`). The score is paid at the win panel, shown as "Punti" there.
- **Achievements** (category Minigiochi `min`, now 4 slots, total **34**), event `faclear` fired the moment a floor is cleared (`faWin` floors 1-2, `faFinalWin` floor 3), so they stay unlocked even if the encounter is lost later, real encounters only: **"Fuori da Coccia!"** (m2, clear floor 1, +150 sordi / +90 exp),
  **"Algidone è a terra"** (m3, clear floor 3 = all 3 floors, +400 / +240), **"Senza un graffio"** (m4, clear any floor without losing a life on that floor, +250 / +150; `FA.floorLives` set per floor). Existing unlock/popup path; it fires during the climb/collapse animation (no gameplay) and the popup sits above the pad, clear of the panel button (screenshot checked).
  Achievements screen at 360 px: 5 tabs, 4 rows in Minigiochi, no horizontal overflow.
- **Roadmap tile 10**: unlocks on the first real floor-1 clear (`S.p.fa.f1`, new field in `DEF` + migration; old saves get false), no longer on the girone count. No `ROAD_REWARDS[10]`, so it behaves like a "?" tile: "Premio in arrivo", not claimable, no pulse, no popup. Locked tap says "Tessera ancora bloccata" (no hint, like 3 and 5).
  Face = `fa_salsiccia` drawn untouched at x1 (in-game it is x0.5; the tile is bigger). "Sblocca tutto" shows it unlocked.
- **`index.html` size delta: +1855 bytes.**
- Verified headless (real clicks, desktop + mobile tap, `Math.random` stubbed only inside `bjAfterClear`): encounter 1/2/3 wins add exactly the encounter score to the run (+880 / +1770 / +2660 with an instant win, i.e. stock bonus only), payout at run end through the pause menu (score 6310 -> +819 sordi);
  loss and pause-Esci after a cleared floor add 0; m2/m4 fire at the first floor-1 clear, m3 at the floor-3 clear, none fires twice; a floor cleared after a death fires m2 but not m4; practice, dev "Incontro" and a SIM encounter leave the save byte-identical (no achievements, no f1, no score);
  tile 10 locked (toast "Tessera ancora bloccata") before and "unlocked" ("Premio in arrivo", class `rtile unlocked`, queue empty) after the first real floor-1 clear; old save without `f1` loads; 0 console errors.
- Typical scores for the balance pass (M9, not tuned now): a maze girone is ~130 pellets x10 + 200 clear + ghosts, so roughly **1,500-2,500 per girone**. An encounter scores the stock bonus (up to ~900 per floor for an instant win, ~400-600 for a normal clear) plus jumps (+10..30 each): roughly
  **N=1 ~500-900, N=2 ~1,000-1,700, N=3 ~1,500-2,600** (measured max with instant wins: 880 / 1770 / 2660).
- Not tested: real-device feel and the achievement popup timing on a phone; a full real play-through of an encounter (wins were triggered through `faWin`/`faFinalWin`).

## 0.3_37 — 2026-09-25
**M9b — Ferma Algidone! difficulty scaling + tap targets** (the owner's picks from `refs/ferma_algidone/M9_BALANCE.md`). Owner phone test of 0.3_36: OK.
- **Difficulty** (implements M0 Q8; `FA_DIFF`, `FA.dm`): Facile / Media / Difficile = item speed x0.88 / x1 / x1.12 (every spawned item, flames included; belts unchanged), throw pauses x1.25 / x1 / x0.85, stock drain x0.85 / x1 / x1.15. **Media is the old behaviour**:
  a seeded 120 s simulation of all three floors gives identical spawn traces (time, type, speed hash), spawn counts, throw counts and stock drain on 0.3_36 and 0.3_37. Encounters use the run's difficulty (`G.diff`, also for the achievement multiplier: `faClear` now passes it),
  practice (Giochi card), dev "Incontro N" and the floor buttons use the menu difficulty (`S.opts.diff`). Stock bonus formula and payout multipliers unchanged.
- **"Algidone è a terra"**: 400 -> **600 sordi**, exp 240 -> **360** (difficulty multipliers as for the others: 600 / 450 / 900 sordi).
- **Tap targets, Ferma only** (global `.btn` untouched): `#fapanel .btn` (Continua, Avanti, Riprova, Rigioca, Esci, Riprendi), the invite buttons (`#fai-no`, `#fai-yes`) and the Giochi "Gioca" (`[data-fagame]`) have `min-height:44px`; the Ferma pause button (`#fahud .pause`) is 44x44 (was 38).
  The HUD row grows by a few px, so at 360x640 the play canvas goes from 249x422 to 246x416 (x0.68); nothing overlaps at 360x640, 360x800 or 390x844. Review screenshots refreshed (`refs/ferma_algidone/review/m9_*`, plus new `m9_*_giochi.png`).
- **`index.html` size delta: +630 bytes.**
- Verified headless (real clicks for the Options difficulty button, the Giochi "Gioca" tap, the invite; desktop + mobile tap): measured per difficulty (simulated 60-120 s per floor): item speeds sausage 61.6 / 70 / 78.4, porchetta 29.9 / 34 / 38.1, meat 48.4 / 55 / 61.6, flame 52.8 / 60 / 67.2;
  stock drain over 10 s = 8.5 / 10 / 11.5; mean pause between throws on floor 1 = 2.71 / 2.20 / 1.93 s (base mean 2.3 s x 1.25 / 1 / 0.85); practice card uses the menu difficulty; dev "Incontro" uses the menu difficulty; a real encounter uses `G.diff` (hard) even when the menu says easy;
  N=3 encounter on Media pays 150 + 600 + 250 = 1000 sordi in achievements (popups 150/90, 250/150, 600/360); all Ferma buttons measured 44 px tall (panel 316-336 wide, pause 44x44, invite 96x44 / 106x44, Gioca 63x44); old save without `fa` loads; practice, dev "Incontro" and SIM leave `mgs_v1` byte-identical; 0 console errors.
- Not tested: how the three difficulties feel on a phone (multipliers are the owner's picks, unplayed), the taller pause button on real devices.

## 0.4 — 2026-09-25 — Ferma Algidone!
**Release build `"0.4"`** (bare version, tag `v0.4`). Summary of 0.3_1 → 0.3_37; the per-build entries above stay the detailed record.
- **Bugfixes**: main menu music loops without the silent gap (B1: shared gapless Web Audio loop player `loopTrack`, later also used by El Gamblador and the professor tracks); battle music starts with the battle transition (B2); the win/lose track starts right after the last faint (B3);
  "Rocciamon" appears in Lista desideri › Giochi after the first real professor battle (B4).
- **Built-in audio layer** (A0): lookup IndexedDB override → built-in (`BUILTIN_AUD`, hardcoded from submissions) → synth default, with matching export targets. No audio submission is built in yet: they are processed after 0.4.
- **Unlock popups** (P1): a centred popup on the home menu, once ever per event, for new assets, characters, mini-games and roadmap milestones ("Guarda" / "Non ora"); old saves are seeded so nobody is flooded.
- **Percorso (roadmap)**: 50 tiles, one per girone (combined across both characters), special tiles 3 (pokéball, real professor battle), 5 (carte, 10 blackjack hands won) and 10 (first real floor-1 clear of Ferma Algidone!), "?" tiles every 5th; gift container with an animated present; new achievement "Il banco trema".
- **Costumi (skins) and Personalizza** (K1-K3, C1): skin system drawn in every place the player appears (`overlay` / `replace` modes), Cappello GEKA SNC (Uomo roccia) and Costume BK (Algidone) as roadmap rewards, and the Personalizza screen (costume selector + two "In arrivo" placeholders: potere segreto, squadra rocciamon).
- **Ferma Algidone! (new mini-game)**: a Donkey-Kong-style climb: Uomo roccia reaches Algidone, who took over Coccia and throws salsicce, porchetta and carne. **3 floors**: Coccia (girders and ladders), Macelleria (reversing conveyor belts), Fabbrica di salsicce (bolts + holes, bouncing meat, grill and flames, collapse finale).
  Stock timer, 3 lives, synth sound effects (`sound.fa.<slot>`), portrait touch controls.
- **Encounters**: after El Gamblador's gaps, 15 % from girone 5 (effective 12.75 %), forced at girone 10; 1, 2, then 3 floors; "Continua" returns to the maze run. Giochi card G4 (practice, no rewards) + unlock popup.
- **Rewards and achievements**: an encounter win adds its final score to the run score (converted at run end); new **Minigiochi** achievements "Fuori da Coccia!", "Algidone è a terra" (600 sordi), "Senza un graffio" (34 total); roadmap tile 10 unlocks on the first real floor-1 clear ("Premio in arrivo").
- **Difficulty**: Facile / Media / Difficile scale Ferma's item speed, throw pauses and stock drain (Media = baseline). Ferma-only 44 px tap targets.
- **Size**: `index.html` **5,625,868 bytes** vs **4,311,167 bytes** for the 0.3 build (**1,314,701 bytes**, +30.5 %), mostly the embedded Ferma Algidone! art (backdrops, buildings, Algidone frames, items), the two skins and the new audio/dev code (LF-normalised).
- Release smoke test (real clicks, dev mode OFF, desktop + mobile tap, an old 0.3-style save): 23/23 checks — splash, maze run, El Gamblador, Rocciamon (professor battle), Ferma Algidone! (encounter + practice) start and exit cleanly; Percorso (50 tiles), Obiettivi (34), Personalizza and Lista desideri › Giochi open; the dev tab and every dev button are absent and injected clicks on them do nothing; 0 console errors.
- Not tested: real-device audio and touch feel beyond the owner's phone tests of each build, iOS/Safari.
- Post-0.4: audio submissions A1…An, and the 0.5 backlog (CLAUDE.md §8).

## docs — 2026-09-25

- v0.4.5 plan (D1), 0.4 plan archived to docs/releases/0.4.md, firestore.rules, bugs/BUGS.md. No build.

## infra — 2026-09-25

- dev branch deployed at /dev/, stable at the root (I2 part A). No validate-submission workflow exists in the repo, so nothing to retarget.

## 0.4_1 — 2026-09-25

- I2b: dev site (`/dev/`) uses its own save: `mgs_v1_dev`, `mgs_dev_dev`, IndexedDB `mgs_dev`, copied once from `mgs_v1`/`mgs_dev` on first open (IDB not copied). Constants `IS_DEVSITE`, `SAVE_KEY`, `DEV_KEY`, `IDB_NAME`. Label "DEV <version>" (top centre, non-interactive) only on /dev/. `wipeData` follows the keys.
- Size: index.html 5,632,575 bytes (+6,707 vs 0.4).

## docs — 2026-09-25 (I3)

- validate-submission workflow added (`.github/workflows/validate-submission.yml`, job "validate", PRs to dev/main touching submissions/**; runs the existing `scripts/validate_submission.py`, which finds the changed packages itself via git diff — it takes no folder argument).
- Screens library `refs/screens/` (93 screens, 1.9 MB) + `SCREENS.md`; scripts `tools/screens/capture.py` and `make_index.py`. Ids are canonical. No build.

## docs — 2026-09-25 (E1a)

- Dev-mode audit report `refs/dev/DEV_AUDIT.md` (E1a); screens not-captured list (`tools/screens/not_captured.txt`, SCREENS.md regenerated). No build.

## 0.4_2 — 2026-09-25

- E1b dev-mode cleanup (owner picks 3–10, 12, 14–16 of DEV_AUDIT.md):
  - Sblocca tutto now ends with dev mode: the ✎ toggle calls `simOff()` (Trello #12); load already reverts it. "Esci" already did.
  - One dev map select (5 themes + 10 extra + the two old test maps "Prova torrenti"/"Prova mappa larga") + Vai, dev run, nothing saved; Girone 4 / 7 kept; the four map buttons and the old select are gone.
  - Removed: "Come si modifica" text, Mangiaroccia "Avvia", "Popup di prova" (now the "Obiettivo" button of the popup previews), "Testo grezzo", the debug achievements and the "Debug" achievements tab (old saves keep their d1–d5 data untouched; 34 real achievements unchanged).
  - "Livello di prova — scrive nel salvataggio" label; Ferma debug overlay is a toggle ("Overlay debug"), off by default, in memory only.
  - `bindOpt` whitelist replaced by `data-dev` on each accordion body of the Sviluppatore tab (all ids kept; `#xopen` moved to `bindDev`). Accordion "Obiettivi" renamed "Anteprime" (id `obj` unchanged).
  - Role split kept (pick 15). The I3 note about the El Gamblador click is corrected: it was two capture runs at once, not the game (SCREENS.md notes, capture.py comment).
  - Screens library regenerated (93 screens, 1.55 MB): dev-*, fa-* (no overlay), wish-*.
- Size: index.html 5,624,483 bytes (−2,207 vs 0.4_1, LF-normalised).

## 0.4_3 — 2026-09-25

- F1 Firebase dev login (DEV_AUDIT picks 1–2): login modal with username + password ("Accedi"), Firebase Auth email/password (`<user>@mangiasassi.invalid`), role read from Firestore `devs/{uid}` (master, dev1…dev5; dev1…dev5 behave as the old dev1, account name kept in `acct`); Italian errors (wrong credentials, too many attempts, offline, account without role); Account accordion "Connesso come …", Cambia password (reauthenticate + update), Esci (sign out, cache cleared, dev off, Sblocca tutto off).
- SDK v12.19.0 loaded with dynamic `import()` only when needed (login modal, or at startup when the dev cache has a Firebase session), 8 s timeout, never blocks the menu; separate sessions per site (app name `mgs` / `mgs_dev`); cache `{role,acct,fb:true,devOn}`, background verification, offline keeps the session; old local-login cache cleared; `file://` shows "Accesso disponibile solo dal sito".
- Removed the hardcoded credentials, the local check, `S.creds` (deleted from old saves on load), the Credenziali block and "+ Sviluppatore" / "Rimuovi".
- Tests: `tools/fbstub/` (stub SDK, `test_f1.py`, 34 checks); `capture.py` seeds a stub session for dev screens (re-captured `opt-login-modal`, `dev-tab`, `dev-acc-account`).
- DEVELOPERS.md: how to log in and change the password.
- Size: index.html 5,629,738 bytes (+5,255 vs 0.4_2, LF-normalised).

## 0.4_4 — 2026-09-25

- F6a "Segnala un bug": bug icon (code-drawn, 44+ px tap area) in the top bar of every screen for logged-in devs (menu, Lista desideri, Opzioni, Percorso, Obiettivi, Personalizza, maze HUD, El Gamblador, Ferma Algidone!, professor scenes/battle, Partita finita); hidden when logged out; player path behind `BUG_PLAYERS=false` (0.5, hook `bugPlayerSession()` for F2).
- Tapping it freezes the game like its pause without the pause menu (maze, El Gamblador, Ferma; professor via a frozen clock and pausable sleeps); popup "Hai un insetto?" (1000 chars + counter, Indietro / Invia, Esc = Indietro, keys blocked from the game).
- Send to Firestore `bugs` (uid, text, screen, version, char, ts, ua, meta{acct,site,girone,diff,viewport}); offline / failed sends go to the local queue `mgs_bugq` (max 20, `meta.qts` keeps the original time), flushed on load (after verification), `online`, and after each send; permission errors keep the report queued without a retry loop.
- `screenId()`: state → canonical screen id (one table, `SCREEN_IDS`); reused by F5.
- Tests: `tools/fbstub/test_f6.py` (46 checks; stub extended with `addDoc`/`collection`/`serverTimestamp`, deny/hang flags). Screens: new `bug-popup`; library re-captured (icon now visible in the dev screens).
- CSS: `.btn.ok` (green), `.btn:disabled`.
- Size: index.html 5,641,827 bytes (+12,089 vs 0.4_3, LF-normalised).

## 0.4_5 — 2026-09-25

- Bug icon also on the splash ("Roccia sì o roccia no?"), the "sad" countdown and the "bye" screens (logged-in devs only, same rules as F6a; no overlap at 360×640 / 390×844). The splash question is a modal: after Indietro it is redrawn; the sad countdown is frozen while the popup is open (`sadArm`). New ids `sad-countdown`, `bye-goodbye` in `SCREEN_IDS` / SCREENS.md (`sad` has no UI path today; `bye` is the Android quit).
- Tests: `test_f6.py` 63 checks.
- Size: index.html 5,642,247 bytes (+420 vs 0.4_4, LF-normalised).

## infra — 2026-09-25 (F6b)

- Bug export workflow `.github/workflows/bugs-export.yml` (daily 06:00 UTC + manual run, checks out `dev`, secret FIREBASE_SA) with `tools/bugs/export_bugs.py` (Firestore `bugs` where not exported → `bugs/inbox/<date>_<id>.json`, doc marked `exported`/`exportedAt`; mocked test `tools/bugs/test_export_bugs.py`); commits "bugs: export N report(s)" as github-actions[bot] to `dev`.
- Triage procedure CLAUDE.md §1c; `bugs/BUGS.md` sections explained; `bugs/inbox/`, `bugs/triaged/` created. 0.5 privacy note added (§8, §10.4). No build.

## infra — 2026-09-25 (F6b follow-up)

- `bugs-export.yml` copied to `main` (workflow-only commit `ef4cfee`, needed for the schedule and "Run workflow"; the job still checks out `dev`); both copies must stay identical. §1: exception for the bot's own rebase. §8: "sad" screen unreachable (observation for 0.5). No build.

## infra/docs — 2026-09-25 (F3a)

- Submission format v2 (F3a): spec `docs/submissions-v2.md`, DEVELOPERS.md rewritten (login, Invia testi, Scarica pacchetto, PR to `dev`, before/base version, bug icon); `scripts/validate_submission.py` v2 (schemaVersion 1 and 2, folder mode `validate_submission.py <folder>`, `-testi` folders, tests `scripts/test_validate_submission.py` + fixtures `submissions/_fixtures/`); `firestore.rules`: `edits` collection (owner publishes it in the console); text-edit export in `tools/bugs/export_bugs.py` (two-phase: export → commit/push → mark; packages validated, failing ones committed and listed in the commit message; tests extended). CLAUDE.md §5 (conflict check, review columns), §10.3 (F3a done, F3b), §10.4. Workflow copied to `main`. No build.
- Triage: 3 bug reports (pipeline tests) moved from `bugs/inbox/` to `bugs/triaged/` (2 entries in NEW).

## 0.4_6 — 2026-09-25

- F3b submission format v2 in the game: the export dialog now has two actions, both needing a Firebase dev session (otherwise disabled, "Accedi per inviare"):
  - **Invia testi**: each text/colour/scale change → one Firestore `edits` doc (fields exactly as the rules: uid, acct, kind, char, screen when known, target, before = built-in value without the local override, value, note ≤ 300, base = VERSION, ts, meta); the change stays applied locally and is marked "inviato"/"in coda", not re-sent unless edited again; offline / network failure → local queue `mgs_editq` (max 200, `meta.qts`), flushed on load, `online` and after each send; permission error keeps it queued without a retry loop.
  - **Scarica pacchetto**: ZIP with only audio and sprite changes and a schemaVersion 2 manifest (developer = account, baseVersion, site, exportedAt, note, `before` {sha256, bytes, w/h or durationMs} of the built-in asset via crypto.subtle, `file`, `meta` measured by the tool); audio > 300 KB goes under `flagged/` inside the package; nothing to export → disabled with a hint. `expSpriteItems()` is the hook for the skin/sprite tool (F4): today the dev mode produces no sprites.
- `window.mgExport` removed (DEV_AUDIT pick 11). Root `VERSION` file synced (it had stayed at 0.4_1) — from now on bump `const VERSION` and the root file together (§6).
- Tests: `tools/fbstub/test_f3b.py` (34 checks incl. the downloaded ZIP passing `scripts/validate_submission.py`); F1/F6a tests still pass. `export-dialog` re-captured.
- Size: index.html 5,648,571 bytes (+6,324 vs 0.4_5, LF-normalised).

## 0.4_7 — 2026-09-25

- F5 text edit by long-press: with dev mode on and a Firebase dev session, holding any text for 3 s (yellow outline from 0.3 s; moves > 10 px or an earlier release cancel) opens the popup «Modifica testo» (screen id, current text read-only, Proposta ≤ 500 with counter, Nota ≤ 300, colour + scale for menu sections and card names, Annulla/Salva, Esc = Annulla); the game freezes like for the bug report and the tap that ends the long press does nothing. Never on inputs, `data-nolp` controls (d-pad, Ferma pad) or the popups themselves.
- DOM text works anytime (full current line for the typewriter boxes of El Gamblador, professor and battle); canvas text only while the game is paused or a dialogue waits for input: in dev mode only, `fillText`/`strokeText` are wrapped to record text rects (removed when dev mode ends).
- Known keys (tile labels, card names, BJ/PR lines) preview live via the existing `S.tiles` / `S.ov` / `S.gtext`; other texts are saved as proposals with a locator (`mgs_editprops`), listed «anteprima non disponibile» and sent by «Invia testi» without a target. A text change with a locator needs no target (validator + docs/submissions-v2.md + export updated; validator tests 37).
- Pen icons and the old edit dialog removed (`S.ov` store kept; «+»/«−» for custom tiles/cards kept). Dead `exportTargetsMd` removed. DEV_AUDIT / DEVELOPERS.md updated. Root `VERSION` = 0.4_7.
- Tests: `tools/fbstub/test_f5.py` (42 checks); F1 (34), F3b (34), F6a (63) still pass. Screens: new `dev-textedit-popup`, library re-captured (97 screens; pens gone).
- Size: index.html 5,657,865 bytes (+9,294 vs 0.4_6, LF-normalised).

## docs — 2026-09-25 (F5 decisions)

- F5 owner decisions logged (§10.4), F3c cancelled, SESSION HANDOFF rewritten, DEVELOPERS.md: keep `{…}` placeholders in a proposal. No build.

## 0.4_8 — 2026-09-26

- F4a skin tool part 1: Opzioni → Sviluppatore → new accordion «Costumi» (`devUI()`-gated like every other accordion, so every dev role sees it, not master-only), a character selector (Uomo roccia / Algidone) and «Scarica foglio», same ZIP/download path as «Scarica pacchetto» (`expZip`/`expDownload`).
- The sheet is built at runtime from the live `IMG[]` bitmaps and the game's own draw functions — never from `refs/`, so it always matches the build it came from. One row per set (Lato, Mangia, Su, Giù, Rotola, Riferimenti last), frames in game order, scale ×4 nearest-neighbour, each cell = the base frame + a 25% transparent margin on every side (room for a costume to overhang, e.g. a hat brim). Rows wrap automatically before 4096 px so the canvas cap is never hit by construction (roccia 1804×2924, algidone 3708×3651 today — both comfortably one sheet, but the code pages into `_1`/`_2`… sheets if a future frame set needed it).
- Uomo roccia: 10 real frames (`f0,f1,f2,e0,e1,fd0,fd1,fd2,fu0,fu3`), 8 skipped (`f3,fd3,fu1,fu2,fd_e0,fd_e1,fu_e0,fu_e1`, all dead per SPRITE_INVENTORY.md), 2 reference cells (the procedural up/down eating rock icon). The Ferma Algidone! climber draws through the same `drawFace()`/`f0-2`/`fd*`/`fu*` frames as the maze (confirmed in code, `faDrawPlayer`) — already skin-hooked with no new art needed; the sheet's `used` metadata credits Ferma next to the maze usage on those keys instead of adding a duplicate row.
- Algidone: 27 real frames (everything but `al_r7`, skipped as dead), 3 reference cells (Cinghiale, code-only, lato/su/giù via `drawBoar`). Algidone's own Ferma Algidone! frames (`FAIMG.alg_*`, the thrower NPC) are a separate, non-skinnable asset set and are correctly left out — he isn't the played character there.
- `<char>_cells.json` (schema 1): backward compatible with `cut_from_cells.py` (`skin`,`mode`,`sheet{w,h}`,`frames{key:{x,y,w,h}}` = the cell rect) plus `char`, `baseVersion`, `scale`, `margin`, per-frame `base{x,y,w,h}` (sheet px), `set`, `dir`, a `flip` note, `used` (where the frame appears), `refs[]` and `skipped[]` with reasons. Placeholders `skin:"nuovo"`, `mode:"overlay"` (F4b sets the real ones). `<char>_GUIDE.png` (grey bg, pink cell borders, the live frame drawn at its real position + key/direction label, header with character/build), `<char>_DRAW_HERE.png` (same size, fully transparent), `LEGGIMI.txt` (Italian, draw-on-a-layer / overlay vs replace / leave a cell empty / "in arrivo" for F4b).
- `refs/skins/cut_from_cells.py` updated for schema 1 (`scale`/`margin`): each cut `sk_<skin>_<key>.png` comes out downscaled 1/scale back to native resolution (still bigger than the base frame — the margin is kept, in case the artist actually drew past it), with `ox`/`oy` for every frame written to `<skin>_offsets.json` (normal here, not a sign of anything unusual). Legacy sheets with no `scale` field (the K1b `geka`/`bk` kit) are cut exactly as before, unchanged.
- Tests: `tools/fbstub/test_f4a.py` (49 checks) — hidden with dev off or logged out, visible for every dev role, both characters exported and unzipped (desktop + mobile touch), every PNG ≤ 4096 px, every key exists in `IMG[]` this build, no cross-character keys, GUIDE base rect pixel-matches the live frame at ×4 (≤1/255 rounding tolerance from compositing the same frame in two different engines) for every real frame, DRAW_HERE fully transparent, `cut_from_cells.py` round-trips an F4a sheet to native sizes, old `geka`/`bk` cells.json still cut unchanged, export never touches the save. `node --check` + smoke test, zero console errors.
- Not tested: real-device download (iOS Safari / a phone browser's download UI), opening the PNGs in an actual drawing app.
- Size: index.html 5,673,067 bytes (LF-normalised; +15,186 vs the 0.4_7 count in the previous entry, +16 vs that from a follow-up doc edit in the same session).

## 0.4_9 — 2026-09-26

- F4a2: Algidone's Ferma Algidone! thrower (`FAIMG.alg_*`, the NPC that throws items — never the played character) joins the skin sheet as its own row («Ferma Algidone! (lanciatore)»), same rules as F4a (×4, 25% margin, map fields, `used`): 13 real frames (`alg_idle0-1`, `alg_angry0-1`, `alg_throw0-3`, `alg_eat0-2`, `alg_kick1-2`), 1 skipped (`alg_kick0`, dead code — only `alg_kick1`/`alg_kick2` are ever referenced). This pushes Algidone's sheet past one page for the first time: it now exports as 2 numbered sheets (`_1`/`_2`, 3816×3260 and 3816×3535, both ≤ 4096 px/side and under 16M px), splitting cleanly at a row boundary (never mid-row); roccia's sheet is unaffected (still one page).
- Skin hook on the thrower: `faAlgFrame()`/`faAlgPose()` now return `{key,im}` (not just the image) so the draw call in `faDraw`'s NPC block can go through `drawSkinned(c,"algidone",pose.key,im,-w/2,-h,w,h,a.flip)` — identical `dx,dy,dw,dh`/flip/save-restore as before (K1b rules). The thrower wears whatever skin is equipped for Algidone, whoever is actually climbing (Uomo roccia today). Since Ferma's art lazy-loads (`ensureFA()`/`FAIMG`, unlike the always-loaded `SPR`/`SPR2`), `loadSkinImgs()`'s base-frame check now accepts `FAIMG[fk]` as well as `IMG[fk]`, and `ensureFA()` re-runs `loadSkinImgs()` once `FAIMG` is populated, so a skin's `alg_*` frames aren't silently dropped by the boot-time pass that ran before Ferma's assets existed. Verified with `DEV_SKIN_TEST` in both overlay and replace on every thrower frame, and with BK actually equipped: since BK has no art for these keys yet, the thrower renders pixel-identical to 0.4_8 (confirmed by screenshot diff in the test) — no player-visible change in this build.
- Skin coverage: `SKINS.<id>.na` (optional array of frame keys a skin intentionally has no art for; empty today for GEKA and BK — only the owner fills it). The «Costumi» accordion now also shows, per character, one line per skin («`<nome>`: X/Y frame — mancano: …», computed at runtime from the sheet's real frame keys minus `na`): GEKA is 10/10, BK is 27/40 (missing exactly the 13 new thrower frames). New script `tools/fbstub/test_skin_coverage.py` writes `refs/skins/SKIN_COVERAGE.md`, the same matrix (frame × skin: ok / manca / na / procedurale) as a committed doc; Cinghiale's 3 reference poses show as "procedurale — da convertire" in every skin's column until they become real frames.
- Standing rule added (CLAUDE.md §6 rule 11, also §9): any chunk that adds or changes a frame, pose or animation must, in the same build, add it to the F4a sheet and update `SPRITE_INVENTORY.md`/`SKIN_COVERAGE.md`, and list any new gap as "art owed" (§8). REL gate: `SKIN_COVERAGE.md` regenerated at release, any `manca` added since the last stable release blocks the merge to `main` unless the owner names the gap as accepted. Grandfathered for 0.4.5 (already live, not blocking): BK on the Ferma thrower frames, BK on Cinghiale — both now tracked in §8 "Skin art owed".
- `SPRITE_INVENTORY.md` item 18 corrected: it used to say Ferma Algidone!'s climber was "not built yet" (a stale note describing an earlier, different plan) — the climber (Uomo roccia) is built and was already skin-hooked before this chunk (it reuses `drawFace`/`f0-2`/`fd*`/`fu*`, confirmed in code); the thrower's own hook is what this chunk actually adds.
- Boar investigation (report only, no code): `drawBoar()` is fully procedural (canvas primitives, 3 direction variants, continuous sine-based walk/bob/shake, no tint hook); the stress bar, stun stars, wall-smash dust and the shared ability-duration bar all live outside it and would stay procedural regardless. Proposal to make it skinnable: bake fixed base frames from `drawBoar` per direction (same technique as today's reference cells) and hook them like every other character, keeping the motion/effects as procedural transforms around the sprite. Sizes S (3 frames, loses the walk cycle) / **M (6 frames, recommended)** / L (9-12 frames). Logged in §10.4, tracked as chunk F4c pending an owner decision.
- Tests: `tools/fbstub/test_f4a.py` extended to 67 checks (Ferma row keys/pixel-compare/no cross-character leakage, multi-page sheet handling, coverage lines in the accordion, the thrower hook under `DEV_SKIN_TEST` and with BK equipped, a real Ferma run from the Giochi card's «Gioca», per-page `cut_from_cells.py` round trip); new `tools/fbstub/test_skin_coverage.py` (9 checks). `node --check` + smoke test, zero console errors.
- Not tested: real-device download, opening the multi-page sheet in an actual drawing app, the boar proposal itself (report only).
- Size: index.html 5,676,647 bytes (+3,580 vs 0.4_8, LF-normalised).

## 0.4_10 — 2026-09-26

- F4c: Cinghiale skinnable, option M from the 0.4_9 boar report (owner-approved, ships in 0.4.5 before F4b). The body-drawing code (rects/ellipses/triangles, 3 direction variants) moved unchanged into a new `drawBoarBody(ctx,u,lg,o,face)` — same pixels, just without the mirror `ctx.scale(-1,1)`, which the caller now applies once regardless of whether it ends up drawing the procedural body or a frame.
- 6 base frames baked once at boot (`bakeBoarFrames()`, called right before `loadSkinImgs()` in the boot chain): `boar_lato0/1`, `boar_su0/1`, `boar_giu0/1` (2 leg-swing extremes × 3 directions, `anim` chosen so the leg-phase `sin` hits ±1, `moving:true` so the motion-blur streak is included). Since there's no static PNG to size or anchor against, `bakeBoarFrame(dir,phase)` does a two-pass render — measure the alpha bounding box on a scratch canvas, then redraw tightly cropped (6 px padding) into the final one — and stores the origin offset as `canvas.boarAx/boarAy` (plays the role `skOx/skOy` plays for a real image). Sizes: `boar_lato*` 235×135, `boar_su*` 116×210, `boar_giu*` 116×200 (native, baked at scale ×120 — the same reference scale K1b's ref cells used; displayed at runtime scaled by `c/BOAR_C` so procedural and framed rendering stay proportional).
- These 6 frames replace the 3 boar reference cells on Algidone's sheet: a new row «Cinghiale» (mixed directions in one row — `SKIN_DEF.sets` entries can now be a plain key string, using the row's own `dir`, or a `[key,dir]` pair for a row that mixes directions; `skinRows`/`skinCoverage` both updated to resolve it) with the same map fields (`used`, `flip`, `base{x,y,w,h}`) as every other real frame. Algidone's sheet is now **3 pages** (3816×3260, 3816×3144, 3816×2768, all ≤ 4096 px/side and under 16M px) — Cinghiale's row alone needed the 3rd.
- Hook in `drawBoar()`: picks the frame key from direction + leg phase, checks `activeSkin("algidone",key,base)` — **replace** mode draws that frame (`drawSkinLayer`, scaled/positioned via `c/BOAR_C` and the baked origin) *instead of* the procedural body; **overlay** mode draws the procedural body first, then the frame on top with the same positioning; no skin or a frame the skin doesn't provide → procedural `drawBoarBody` only. Verified pixel-identical to 0.4_9 for `(face,anim,moving)` across all 4 faces × both moving states × 3 anim values (0 mismatches, diffed frame-by-frame against the actual 0.4_9 build); a 12-case SHA-256 subset is now a permanent golden-hash regression check in `tools/fbstub/test_f4a.py`. Verified with BK actually equipped (still no Cinghiale art — grandfathered) rendering identically to no skin, and with `DEV_SKIN_TEST` overlay/replace visibly changing every one of the 6 frames including the mirrored side view. Every other Cinghiale effect (stress bar, "STORDITO"/"STRESS N%" text, stun sparkle stars, wall-smash dust `G.parts`, the shared ability-duration bar) lives outside `drawBoar` and was never touched.
- Coverage: the 6 `boar_*` keys are now real frames for `skinCoverage`/`SKIN_COVERAGE.md` — BK's gap grows from 13 (Ferma thrower) to 19 (+ Cinghiale), still grandfathered (§8 "Skin art owed", now naming the 6 frame keys); GEKA (roccia-only) is unaffected. `SPRITE_INVENTORY.md`'s Cinghiale entries corrected (it's no longer purely procedural; the K1b "no hook at all" note updated).
- Fixed along the way (found while writing this chunk's own tests, not a regression from a shipped build): `skinCoverage()` and `test_skin_coverage.py`'s own frame extraction both read a set's `keys` array assuming every entry was a plain string; a `[key,dir]` pair (introduced by this same chunk for the new mixed-direction Cinghiale row) would have been treated as the key itself. Fixed before either ever ran against a build with that row.
- Tests: `tools/fbstub/test_f4a.py` extended to 77 checks (Cinghiale row keys/per-key direction/pixel-compare, zero boar ref cells left, the golden-hash regression, BK-equipped and `DEV_SKIN_TEST` overlay/replace on every boar frame, a real run reaching girone 7, pressing the ability button and moving in every direction with Cinghiale active); `tools/fbstub/test_skin_coverage.py` extended to 12 checks. `node --check` + smoke test, zero console errors.
- Not tested: real-device download, opening the sheet in an actual drawing app.
- **Process note**: a bare regex scan run directly against `index.html` mid-session printed base64 into this session's own output (caught and reported to the owner immediately; no base64 landed in any committed file). The base64 handling rule was tightened as a result — see CLAUDE.md §10.4 ("git hygiene").
- Size: index.html 5,679,594 bytes (+2,947 vs 0.4_9, LF-normalised).

## 0.4_11 — 2026-09-26

- F4b1 item 0 (new standing tool): `tools/strip_index.py` writes a copy of `index.html` to `/tmp` with every run of 200+ base64 characters replaced by `<B64 n>`, printing only the output path/size. Mandatory first step of every session from now on — never `grep`/`cat`/`sed`/`head`/a regex scan on `index.html` directly, search only the stripped copy. Logged in CLAUDE.md §10.4: base64 leaked into a session's own output in **both** the 0.4_9 and 0.4_10 sessions, not just one as previously recorded.
- Sheet fixes from the owner's phone test of 0.4_10 (F4c):
  - Cinghiale's motion-blur "speed line" streaks used to be baked into the 6 `boar_*` base frames; they're now a separate effect (`drawBoarStreaks`, called by `drawBoar` at the same point in the draw order, for the procedural body and a skinned boar alike). The baked frames tightened to the body's own bounds through its motion: `boar_lato0/1` 194×135 (was 235×135), `boar_su0/1` 116×178 (was 116×210), `boar_giu0/1` 116×168 (was 116×200). No-skin rendering stays pixel-identical to 0.4_10 (12-case golden-hash regression, unchanged, still passes); the streak is confirmed to still visibly draw on top of a skinned boar in both replace and overlay modes.
  - Labels on the ×4 sheets were unreadable at that scale: frame labels now ≥28px, the header ≥48px, on both characters, every page (`SKIN_LBLH` 22→80, `SKIN_SECLBLH` 24→48, `SKIN_HDRH` 64→130 to fit them; labels only ever in GUIDE, never DRAW_HERE, unchanged). Page counts/sizes shift as a result — roccia stays one sheet (1804×3400, was 1804×2924); algidone stays 3 sheets (3816×3712/3408/2530, was 3816×3260/3144/2768). A pre-fix sheet is naturally rejected by the size-matching check in the new import tool (below), since its page sizes no longer match this build's layout.
- «Parti da» on «Scarica foglio»: a new selector («Base», the default, or any existing skin of that character). With a real skin selected, GUIDE shows each cell exactly as the game renders it with that skin (replace → the skin frame only; overlay → base + overlay; a frame the skin lacks → base, as always); DRAW_HERE gets that skin's own frames at ×4 in their real position (ox/oy respected), empty where the skin has none. `cells.json` adds `from`, the real `mode` (no longer always the `"overlay"` placeholder when starting from a skin), and a per-frame `sha256` of the skin's stored bytes (`null` when missing). Verified with GEKA (roccia, replace): cutting the DRAW_HERE region back down with the shared box filter reproduces GEKA's own `f0` frame byte-for-byte (nearest-neighbour ×4 upscale then box-average ×4 downscale of an exact integer factor is lossless).
- «Carica costume» (new, dev only, inside Costumi): a file picker for one or more PNG sheet pages, a target (Nuovo costume with an Italian name + auto-derived id, or Aggiorna `<esisting skin>` with its mode fixed), and a mode toggle (overlay/replace, new skins only, default overlay). Each uploaded page is matched to this build's own sheet layout by exact pixel size (`skinLayout(char)`, shared with the export path so both always agree); an ambiguous same-size match falls back to a page number embedded in the filename; no match at all, or a fully opaque image (a GUIDE screenshot or a photo uploaded by mistake) → the exact errors specified. Warnings (non-blocking): an empty cell, pixels drawn outside every cell, a cut frame over 200 KB, and «invariato» for a frame whose cut bytes exactly match the target skin's own stored bytes.
- Cutting is **one algorithm implemented twice**, not two approximations: a premultiplied-alpha box filter with proportional source slices (robust to a cell size that isn't an exact multiple of 4) and "round half up", identical arithmetic in `index.html`'s new `skinBoxDownscale()` and `refs/skins/cut_from_cells.py`'s rewritten `box_downscale()` (replacing the old `Image.resize(..., LANCZOS)`, which was never guaranteed to match a browser canvas's own resampling). Documented as one shared algorithm in `refs/skins/README.md`; a dedicated test feeds identical synthetic pixels through both implementations and asserts byte-identical output.
- Live local preview (new `SKIN_IMPORT_PV`, in-memory only — never `S`, `localStorage` or `IndexedDB`): a single override checked once inside `skinImg()` covers every existing draw path with no other call-site changes (maze in every direction + eating, menu, cards, career modal, cutscenes, the Ferma Algidone! climber and thrower, Cinghiale, Acciaio's tint). Vanishes on reload (nothing to persist), on logout (`fbDrop`) and when dev mode is turned off (`#devt`). Updating an existing skin merges the preview with that skin's own frames, imported frames winning for any key present in both. Shows a coverage line («Anteprima: X/Y — mancano: …») and a «Rimuovi anteprima» button.
- Explicitly out of scope for this build (F4b2, next): exporting the imported skin as a developer submission package. `DEV_SKIN_TEST` is untouched and still works exactly as before.
- Tests: new `tools/fbstub/test_f4b1.py` (53 checks — boar frames baked without streaks and the streak's own visible contribution, label font sizes on the real sheets, «Parti da» cells.json fields + the GEKA DRAW_HERE round-trip, JS/Python cutter byte-parity on a non-multiple-of-4 size, importing a new skin (empty/oversized/outside-cells warnings), the three exact error messages, updating BK across its real 3 pages, «invariato» detection (tested against a fake skin whose stored frame is bytes this same tool produced, since BK's own pre-F4a encoding will never byte-match a fresh re-encode of identical pixels), ambiguous same-size pages resolved by filename, the preview visible in the menu/maze/Ferma climber/Cinghiale/Ferma thrower with `S` byte-for-byte unchanged throughout, and it vanishing on dev-off/logout/reload); `tools/fbstub/test_f4a.py` (still 77) re-verified green against every change in this build, including a small fix inside `cut_from_cells.py` discovered by its own round-trip test (see below). `node --check` + smoke test, zero console errors.
- Bug fixed before it shipped (found by `test_f4a.py`'s own round-trip test after the box-filter rewrite, not a regression in an already-delivered build): the first `box_downscale()` draft assumed the input was an exact multiple of the ×4 factor, which a sheet **cell** (margin included) isn't always even though the base frame inside it always is — generalised to a proportional-slice box filter that works for any ratio, in both languages.
- Also fixed: `skinImportRun` (and this build's own tests) must `await ensureFA()` before computing Algidone's layout, exactly like `skinBuildSheet` already did — found while testing "Carica costume" against Algidone, where skipping it silently produced an incomplete (missing the Ferma Algidone! row) 2-page layout instead of the real 3-page one.
- Not tested: real-device file picker (phone gallery / camera roll upload flow), opening the sheet or drawing a costume in an actual drawing app (Aseprite/Photopea/Photoshop).
- Size: index.html 5,693,559 bytes (+13,965 vs 0.4_10, LF-normalised).

## 0.4_12 — 2026-09-26

- F4b2 item 1 (cutter check, from the owner's phone test of 0.4_11): the box filter (`skinBoxDownscale`/`box_downscale`) already averaged with premultiplied alpha, so a transparent neighbour never darkened an opaque pixel — the real bug was upstream, in the *geometry*. `skinRows`' margin was rounded to the nearest whole pixel, not to a whole ×4 block, so a cell (base frame + margin) could land on a size that isn't an exact multiple of 4 whenever a native frame's width or height is odd; the box filter then had to average across a fractional block, genuinely blending what should have been two separate native pixels. Fixed by rounding the margin **up** to the next whole ×4 block per axis — every cell is now always an exact multiple of `SKIN_SCALE`, so the base frame's own native origin lands exactly on an output-pixel boundary and the filter always averages a clean, non-overlapping block. This reflows the sheet again: roccia 1804×3410 (was 1804×3400), algidone's 2nd/3rd pages 3816×3420/2534 (was 3816×3408/2530) — an 0.4_11 sheet now also fails the size-match check, same as any older one. Verified: a clean ×4-aligned test pattern (covering both the base rect and the margin) round-trips through the cutter byte-for-byte with zero blending, in both JS and Python; an opaque block surrounded by fully-transparent neighbours keeps its exact colour (no dark halo).
- F4b2 item 2: while a preview (`SKIN_IMPORT_PV`, F4b1) exists, «Scarica pacchetto» now includes it. `expSpriteItems()` — an F3b-era hook that always returned `[]`, reserved "for F4" — turns the preview into one `type:"skin"` change per frame (an «invariato» one, already tracked at import time, is left out): `target:"skin.<id>.<frameKey>"`, `file:"skins/<id>/sk_<id>_<frameKey>.png"` at native size, `meta:{skinId,skinName,mode,action:"new"|"update",frameKey,w,h,ox,oy,base_w,base_h}`, `before` = sha256/bytes of the target skin's own existing frame (`null` for a new skin or a frame it didn't have), `screen` = the character's maze screen id. `expBuildPackage`'s sprite-item loop is generalised (its own `file` path, `type` and `meta` shape) rather than duplicated. The export dialog lists the pending preview (name, character, mode, new/update, exportable frame count) and warns that it's lost on reload — download first. `EXP_LIM.sprite` (200 KB/frame) was undefined until now (the size check had silently been a no-op since no sprite item was ever produced); set alongside this change.
- F4b2 item 3: `docs/submissions-v2.md` documents `type:"skin"` (target format, `meta` fields, `before`, note now optional for this type); `scripts/validate_submission.py` validates it (`TYPES_V2` + a dedicated `meta` check: non-empty `skinId`/`skinName`/`frameKey`, `mode` ∈ {overlay,replace}, `action` ∈ {new,update}, sizes/offsets like sprite); new fixtures `submissions/_fixtures/valid-skin-new`, `valid-skin-update`, `broken-skin-mode`, `broken-skin-meta`. `DEVELOPERS.md` gets a short "Making a costume in the game" section (download sheet → draw on DRAW_HERE → Carica costume → check the live preview → Scarica pacchetto → PR upload, same as any other package).
- F4b2 item 4: §5 procedure (CLAUDE.md) extended for `type:"skin"` changes — group by `skinId`, embed as a new or merged `SKINS` registry entry, regenerate `SKIN_COVERAGE.md`/`SPRITE_INVENTORY.md` in the same build (§6 rule 11), and for a brand-new skin add one line to the new §8 "Costumi da assegnare" (a skin is never given to a player automatically; the owner decides its unlock separately — empty today, no skin submission processed yet).
- F4b2 item 5: `DEV_SKIN_TEST` fully removed — the symbol, `devSkinOutlineImg`/`devSkinTintImg`, its "Skin di prova (K1b)" panel and click handler, and the `fbDrop` reset. `activeSkin()` kept as a one-line passthrough to `skinImg()` so its call sites (`drawBoar`, `drawSkinned`) needed no changes. The Personalizza-page dev-testing fallbacks that used to check `DEV_SKIN_TEST` now check `SKIN_IMPORT_PV` instead (same behaviour: reach/show the page for a character without owning a real skin, while a preview is active). No player-visible change.
- Tests: new `tools/fbstub/test_f4b2.py` (30 checks — cutter anchoring against this build's own real geometry incl. the no-dark-halo case, JS/Python parity on the same pattern, exporting a new skin and an update to BK with only the changed frame going out, the 200 KB/frame error, `DEV_SKIN_TEST` fully gone); `tools/fbstub/test_f4a.py` (still 77, its `DEV_SKIN_TEST` tests migrated to `SKIN_IMPORT_PV`) and `tools/fbstub/test_f4b1.py` (still 53, same migration for its own preview tests) re-verified green; `scripts/test_validate_submission.py` (41, incl. the 4 new skin fixtures; the pre-existing "unknown type" mutation test now uses a genuinely bogus type since `skin` is legitimate now); `tools/fbstub/test_f3b.py` (34, needed the same Chromium-launch fallback the newer test files already use to run in this sandbox — unrelated to any code change here). `node --check` + smoke test, zero console errors.
- Not tested: uploading a real submission package through an actual GitHub PR from a phone, drawing a costume in a real drawing app.
- Size: index.html 5,694,118 bytes (+559 vs 0.4_11, LF-normalised).

## 0.4_13 — 2026-09-26

- F2a: player login, flag off (F2 split into F2a player login / F2b cloud save). Same Firebase session per site as F1 (app `mgs`/`mgs_dev`), same `<username>@mangiasassi.invalid` mapping, invite-only (no sign-up UI). `plLogin()` performs the identical sign-in + `devs/{uid}` role check as the existing dev flow: a role found is treated exactly like today's dev login (`role`/`acct` set, `devOn` left untouched); no role sets a new, separate player session (`playerAcct`) instead. The dev-only 5-tap secret modal (`loginModal()`) is untouched — it stays the sole entry point for a dev with dev mode off, and still rejects a no-role account.
- New flag `PLAYER_LOGIN=false` next to `BUG_PLAYERS`. While off, the new Opzioni › Generali › «Account» accordion only renders for a dev with dev mode on (`devOn&&!!role`), so the feature can be tested; a logged-out visitor or a plain player sees nothing new. `bugPlayerSession()` (an F2 hook that always returned `null`) now returns `!!playerAcct` for real, but `canReport()` stays false for players since `BUG_PLAYERS` is still off — no bug icon, no dev UI, no Sblocca tutto, no SIM for a logged-in player, ever.
- Player session state mirrors the dev one: `PLAYER_KEY` (`mgs_player`/`mgs_player_dev`), `persistPlayer()`, restored synchronously from cache at boot (no wait for network) and verified in the background by `plVerify()` (user gone → logged out; unreachable → stays, same pattern as `fbVerify`). `plAccountHTML()` renders the logged-out form (username/password/«Entra», with «Accedi con l'account che ti ha dato El Cipro») or, logged in, the account line + «Esci» + F1's own «Cambia password» fields reused as-is (`#cpo/#cpn/#cpr/#cpe/#cpw`, `fbChangePw()` untouched). Errors are the same Italian `fbErr()` mapping as the dev login (wrong credentials, offline/unreachable). `wipeData()` also drops `PLAYER_KEY` and resets `playerAcct`.
- New screen id `opt-generali-account` (Generali tab, «Account» accordion open) — already covered for free by the existing `optOpen.gen`-based generic case in `screenId()`, just added to `SCREEN_IDS`/`refs/screens/SCREENS.md` with a real screenshot (`tools/screens/capture.py`'s `sc_options_dev` opens it before switching to the Sviluppatore tab, since reaching it today needs a dev session).
- Tests: new `tools/fbstub/test_f2a.py` (37 checks — flag off/no UI, dev-mode-only visibility, full login/logout/Cambia-password cycle, wrong credentials, offline, a restored player session has zero dev reach (`devUI()`, `SIM()`, `canReport()` all false, no bug icon, no Sviluppatore tab, no Account accordion), session survives reload, dropped when the stub user disappears, mobile touch, `wipeData()`); `tools/fbstub/test_f1.py` (33/34 — pre-existing "Esc closes the login" flake in this sandbox, confirmed unrelated to this build by re-running against the unmodified 0.4_12 `index.html`, out of scope to fix here), `test_f5.py` (42/42), `test_f6.py` (63/63), `test_f4a.py` (77/77), `test_f4b1.py` (53/53), `test_f4b2.py` (30/30), `test_skin_coverage.py` (12/12), `test_f3b.py` (34/34), `scripts/test_validate_submission.py` (41/41) — all green. `test_f1.py`, `test_f5.py`, `test_f6.py` needed the same Chromium-launch-fallback already used by the newer test files to run in this sandbox (environment-only, no code-under-test change); `tools/screens/capture.py` got the same fallback so the new screenshot could actually be taken here.
- Not tested: real Firebase accounts, real phones.
- Size: index.html 5,698,661 bytes (+4,543 vs 0.4_12, LF-normalised).

## 0.4_14 — 2026-09-26

- F2b: cloud save, flag off. New `CLOUD_SAVE=false` next to `PLAYER_LOGIN`/`BUG_PLAYERS`. `cloudOn()` = a Firebase session (dev or player) AND (`CLOUD_SAVE` OR (dev site AND the local test toggle `mgs_cloudtest_dev`, «Salvataggio cloud (test)» in the Account accordion)). Stable with the flag off: zero Firestore save calls, UI unchanged.
- Firestore doc `saves/{uid}` (stable) / `saves/{uid}_dev` (dev site), fields exactly `data` (the save JSON, ≤ 900000 chars), `rev`, `ts` (serverTimestamp), `ver`. Every upload is a `runTransaction`: re-read, refuse a newer `ver`, write `rev`+1 (1 on create) only if the cloud rev matches the local base rev, otherwise the conflict popup. The Firestore module was already imported whole by `fbLoad` (`Fs.getDoc/runTransaction/serverTimestamp`): no import change needed.
- What is uploaded: the string `persist()` stored (`mgs_v1`/`mgs_v1_dev`), never the live `S`, with the SIM copy resolved to the real data and the dev-only fields removed (`tiles`, `ov`, `extra`, `gtext`, `sim`, `realP`, `realQuick`, `realAch`), keys sorted so equal content hashes equally on every device. Never uploaded during SIM/Sblocca tutto, dev jump/map runs, `PR.test` battles, Ferma tests. Applying a cloud copy keeps this device's own `tiles`/`ov`/`extra`/`gtext`. A save over 900000 chars is never uploaded («Salvataggio troppo grande per il cloud»).
- Local keys (`_dev` on the dev site): `mgs_cloud` `{uid,rev,sum,dirty,ts}`, `mgs_v1_cloudbak` `{data,from,ts,summary}` (one backup slot), and `mgs_v1_ts` (time of the last real save, for the device card's date — not in the brief, flagged). `mgs_v1`'s structure is unchanged.
- Sync after login and at boot after `fbVerify`/`plVerify`: first-sync and same-uid rules as briefed (`saveIsFresh()`), newer `ver` never applied nor overwritten («Aggiorna il gioco per sincronizzare», order 0.4_14 < 0.4.5 < 0.4.5_1). Apply = backup of the local save, write, reload, only from a menu screen (deferred mid-run until the menu). Uploads debounced 30 s (trailing) after a real persist; immediate at `finishRun` and on `pagehide`/hidden (max once per 10 s). Offline → «in attesa di rete», retried on `online`/next trigger/next start; permission error → stopped until next start/login («non disponibile»).
- Conflict popup «Due salvataggi diversi» (new screen id `cloud-conflict`): cards «Nel cloud» / «Su questo dispositivo» with both characters' levels, sordi and date, «Usa questo» on each, «Decidi dopo» (no sync until next start); freezes the game and blocks keys like the bug popup, Esc = Decidi dopo.
- Account accordion: status line, «Sincronizza ora», the dev-site test toggle, «Ripristina backup» (dev site only, swaps backup and save, marks dirty). On the dev site a player session now sees the accordion too (stable unchanged). Logout clears `mgs_cloud` only (save and backup kept); «Cancella dati locali» also clears `mgs_cloud`, the backup and `mgs_v1_ts`.
- `firestore.rules`: the placeholder `saves/{uid}` rule is replaced by the validated `saves/{docId}` block (create rev 1, update rev+1, no delete); the owner pastes it in the console.
- Tests: new `tools/fbstub/test_f2b.py`; the stub `firebase-firestore.js` gained `saves` (getDoc, runTransaction, serverTimestamp, rules checks, kept in localStorage across reloads). `tools/screens/capture.py` `sc_cloud` + `make_index.py` entry → `refs/screens/cloud-conflict.png`.
- Test results: `test_f2b.py` 106/106 (desktop + mobile touch, real clicks: all four first-sync cases, same-uid cases incl. dirty + newer cloud → popup, both popup choices + backup, «Decidi dopo» + Esc, debounce 6 persists → 1 upload after 30 s, run-end flush, SIM/Sblocca tutto/dev jump/`PR.test` → no upload, stable flag off → zero save calls and no cloud UI, offline boot + retry on `online`, permission error stops, newer `ver` blocked, size limit, logout keeps save + backup, dev-only fields excluded/preserved, `_dev` doc and keys vs stable doc via a flag-on copy, apply deferred mid-run until the menu, «Ripristina backup», old saves). Existing suites: `test_f2a` 37/37, `test_f3b` 34/34, `test_f5` 42/42, `test_f6` 63/63, `test_f4a` 77/77, `test_f4b1` 53/53, `test_f4b2` 30/30, `test_skin_coverage` 12/12, `test_f1` 33/34 (the known sandbox flake "Esc closes the login", not touched). `node --check` on every script block + smoke (menu renders, a run starts, no console errors).
- Not tested: the real Firestore rules and network, real Firebase accounts, iOS/Android background flush (`pagehide`/hidden is best effort), slow phones.
- Size: index.html 5,716,325 bytes (+17,664 vs 0.4_13, LF checkout).

## 0.4_15 — 2026-09-26

- X1 (F2b fixes + resized-sheet check). 0.4_14 approved after the owner's phone test (rules published, cloud save works); all 7 decisions of its report accepted.
- Android back: the `mgback` handler first checks the shared `BUG` guard, so with the bug popup, the long-press «Modifica testo» popup or the cloud conflict popup open, back does exactly that popup's own cancel (Indietro / Annulla / «Decidi dopo»): popup closed, freeze released, capture key handler inert, game responding again. No other back behaviour changed.
- Conflict popup cards: the character name and «Liv. N» on separate lines (content unchanged); `refs/screens/cloud-conflict.png` recaptured. The card title «Su questo dispositivo» and the date line still wrap at 390 px (flagged, not changed).
- «Carica costume»: a page scaled uniformly from one page of this build's sheet (width and height both different, same factor within 0.5%) now fails with «L'app ha ridimensionato il foglio: esportalo a dimensione originale», checked before «Foglio di un'altra versione» (same width + other height stays that one). No automatic rescaling. LEGGIMI.txt gained a «Dal telefono» section (layered drawing app e.g. ibisPaint X, new transparent layer, hide GUIDE, export only your layer as PNG at 100% with a transparent background, «Carica costume»).
- test_f1 "Esc closes the login": not a timing flake — after a failed login the disabled «Accedi» button drops focus to `<body>`, so Esc never reaches the login modal's own key listener (fails 6/6 here). Needs a game-code fix, so per the brief it was only investigated and reported (CLAUDE.md §10.4); test unchanged.
- Docs: §8 0.5 note on dev-added extras vs synced saves.
- Tests: `test_f6` 66/66 (+3: back on the bug popup mid-maze), `test_f5` 45/45 (+3: back on «Modifica testo» mid-maze), `test_f2b` 115/115 (+9: back on the conflict popup at the splash and mid-run, keys and taps work again), `test_f4b1` 59/59 (+6: halved, ×0.6 and doubled pages → new message, same width/other height → old message, a correct page still imports, LEGGIMI steps; one run hit a timing failure in the unrelated multi-page BK import, green on rerun), `test_f2a` 37/37, `test_f3b` 34/34, `test_f4a` 77/77, `test_f4b2` 30/30, `test_skin_coverage` 12/12, `test_f1` 33/34 (above). `node --check` on every script block + smoke (in the suites).
- Not tested: the real Android back button on a device (the wrapper's sources aren't in the repo; tests dispatch `mgback` on `window`), real phones, a real ibisPaint export.
- Size: index.html 5,717,191 bytes (+866 vs 0.4_14, LF checkout).

## 0.4.5 — 2026-09-26

**Release build** (bare `"0.4.5"`, tag `v0.4.5`): the DEV tools release. No player-facing UI changes on the stable site — everything below is dev-only or shipped flag-off.

- **F1** — Firebase dev login (roles master/dev1…dev5), "Cambia password", the old local login removed.
- **F3** — submission format v2: text/colour/scale edits sent straight from the game («Invia testi», Firestore `edits`, exported daily into normal packages) alongside the existing ZIP + PR upload («Scarica pacchetto») for audio/sprites/skins, with before-value + conflict checks.
- **F5** — text edit by 3-second long-press (DOM live preview for known keys, canvas texts as reviewed proposals); the old pen icons are gone.
- **F6** — «Segnala un bug» (devs only in this release; the player path is built but stays behind `BUG_PLAYERS=false`), daily export + owner triage into `bugs/BUGS.md`.
- **F4** — the skin creation tool: export a character's full sprite sheet, import a drawn sheet with a live local preview (never touches your save), export it as a submission package once you're happy. Cinghiale and the Ferma Algidone! thrower are skinnable too.
- **F2** — player login and cloud save, both built and tested but shipped with their flags off (`PLAYER_LOGIN=false`, `CLOUD_SAVE=false`); switched on in 0.5.
- **I2/I3** — separate `dev`/`main` branches (Pages deploys `main` at `/` and `dev` at `/dev/`), and a screens library (`refs/screens/`, `tools/screens/capture.py`) of every screen/popup as a canonical reference.
- **E1** — a dev-mode audit and cleanup pass.
- Full detail for every 0.4_1…0.4_15 build is above; the release plan and its decisions log are archived at `docs/releases/0.4.5.md`.
- REQ (tile-10 reward skin) and B1 (maze hitboxes) move to 0.5 — no owner art/screenshot yet; added to the 0.5 backlog (§8).
- Checks before this release: all test suites green except the known `test_f1` "Esc closes the login" (root-caused, not fixed — 0.5 backlog); `node --check` + smoke test; a save made on the tagged `v0.4` build still loads here with progress, achievements, extras, texts/colours and no console errors; `refs/skins/SKIN_COVERAGE.md` regenerated — every remaining `manca` is one of the grandfathered BK gaps (13 Ferma thrower + 6 Cinghiale frames), nothing new.
- Not tested: real devices, the live Pages deploy after this release.

## 0.4.5_35 — 2026-10-01 — FR1d: Algidone anger (ladder outbursts, last girder), floor-3 layout sequence per difficulty

- 0.4.5_34 phone test OK, all FR1c deviations accepted (CLAUDE.md §10.9).
- **Floor-3 layout now follows a per-difficulty sequence, not `floor(e)`**: floor 3 only comes up every 3rd girone, so FR1c's continuous `e` could skip a whole layout tier on faster difficulties (Media jumped straight from L1 to L3, never playing L2). `FA_RUN.diff[id].bolts` now lists the layout index per real loop (facile `[0,0,1,2]`, media `[0,1,2]`, difficile `[1,2]`, the last entry repeating beyond the list), picked by `faBoltLayoutIdx()`. Practice/the maze encounter are unaffected (always L1).
- **Algidone gets angry**: climbing a ladder **upward** onto a higher girder starts a 3.5 s outburst — his existing angry pose, and every throw wait halved (`×outK=.5`) for its duration, re-drawing a wait already in progress immediately if it's longer than the outburst would ever draw, so the burst is felt at once; climbing again mid-burst restarts the timer. Climbing down never triggers anything. While standing on the single girder just below him (any floor), he's permanently angry and slightly slower-but-still-faster throws (`×topK=.65`); leaving that girder (falling, a hole, death) ends it immediately. A death/respawn clears both states. Own tuning table per mode (`FA_RUN.anger`/`FA_PRAC.anger`/`FA_ENC.anger`, same starting values, §10.0).
- **Removed**: the old "bar under 25% → angry pose" rule (now purely position/ladder-driven) — the low-stock beep is unchanged, still reading the bar. Dev readout gains «· rabbia N.Ns» during an outburst or «· rabbia ∞» on the last girder, and its floor-3 layout fact now reads the real sequence pick instead of `floor(e)`.
- Size: +10,166 bytes (`index.html`).
- Tests: new `tools/fbstub/test_fr1d.py` (45/45: the layout sequence at gironi 3/6/9/12/15 for all three difficulties plus practice/encounter, an upward climb starting the outburst and scaling throw waits while a downward one does nothing and a second climb mid-burst restarts the timer, a long already-running wait redrawn the instant the burst starts, the last girder's constant angry pose and `topK` ending the moment it's left, scheduled bites and the low-stock beep unaffected by a bar under 25%, death clearing both anger states, the three anger tables proven independent of each other, and a no-anger/no-climb baseline plus the maze itself golden against the previous build). Re-run unchanged: `test_fr0a` 27/27, `test_fr0b` 29/29, `test_fr1a1` 33/33, `test_fr1a2` 71/71, `test_fr1b1` 50/50, `test_fr1b2` 46/46, `test_fr1c` 42/42, `test_famus` 34/34, `test_s1` 16/16, `test_jg` 15/15, `test_f2b` 117/117, `test_m1a` 112/112, `test_m1b` 36/36. Known flakes (§8), both green on this run: `test_toast_diag` 43/43, `test_f4b1` 59/59. `node --check` on every script block green.
- Not tested: real phone, touch input, audio, how the outburst/last-girder speed-up actually *feels* in hand-played runs.

## 0.4.5_34 — 2026-10-01 — FR1c: music exclusivity, Ferma secret toast, win-panel save, Ferma difficulty per level

- 0.4.5_33 phone test OK, all four FR1b2 deviations accepted (CLAUDE.md §10.9).
- **Music exclusivity, everywhere**: the shared loop player (`loopTrack`) now registers every instance it creates (menu, El Gamblador, the professor, Ferma) in one set, and starting any track synchronously stops every other one first — including a track whose own async decode/play is still in flight (invalidated through its own existing start token, no extra bookkeeping needed). Fixes the menu song playing together with `music.fa` on starting a Ferma game from the main page (root cause: `startFerma` bypasses the menu's own `render()`/`syncMusic()` pipeline entirely, so nothing ever told the menu track to stop — now the act of `music.fa` starting does it directly, with no timing window). Sound effects (`sound.*`) don't use `loopTrack` and are unaffected.
- **The maze-only secret toast no longer shows during a Ferma run**: reaching girone 7 in a Ferma run still unlocks `S.p.sec` (Ferma gironi count, §10.6), but the «Segreto sbloccato» toast — about Mangiaroccia's own secret-ability button, meaningless mid-Ferma — is queued and shown once, prefixed «Segreto sbloccato in Mangiaroccia: », the next time the player is back on the main menu. A maze run's own toast is unchanged (shown immediately, as always).
- **«Salva ed esci» on the Ferma run's win panel** (all three floors, real runs only — not shown in a dev run): saves exactly the state «Avanti» would start the next girone with (its own `onGironeAdvance` call, lives refilled, girPts reset, score including the floor bite bonus and the girone loop bonus), then the usual `S.quick`/persist/toast/back-to-menu. «Gioco corrente» resumes at that next girone. Buttons: «Avanti» / «Salva ed esci» / «Esci».
- **Ferma run difficulty now scales per difficulty level, not just per loop**: `FA_RUN.diff` (facile/media/difficile, keyed by the real `easy`/`medium`/`hard` ids) replaces the one-size-fits-all `FA_RUN.loop` throw/item factors. A continuous progression level `e=(girone−1)/3×rate` (higher on harder difficulties) now drives throw wait, item speed and the time bar's L/N; the floor-3 bolt layout is `FA_BOLTS[min(2,⌊e⌋)]`. The girone reward bonus stays on the real discrete loop, unaffected — rewards unchanged. Dev readout gains «· e N.N».
- Size: +10,312 bytes (`index.html`).
- Tests: new `tools/fbstub/test_fr1c.py` (42/42: the music race dropped deterministically even with an artificially delayed menu-track reload, practice/encounter/run all exclusive and the menu resuming cleanly after each, the secret toast queued through a real girone-7 Ferma run and shown once on the next menu visit while a maze run's own toast is golden-unchanged, the win-panel save matching «Avanti»'s own next-girone state bit for bit including career gironi not double-counted, a full per-difficulty table for gironi 1-12 with its monotonicity/cross-difficulty/layout-order assertions, an FA_MAX_ITEMS sanity check, practice/encounter/the maze golden against the previous build). Four existing tests needed updating for the new invariant (not just a re-run), each a direct, intended consequence of this chunk and nothing else: `test_fr1a1.py` (win-panel button list now includes «Salva ed esci»), `test_fr1a2.py` (§b's bar L/N table recomputed for the per-difficulty `e`, medium being the dev-run default), `test_fr1b1.py` (§a's loop-factor table replaced by the same per-difficulty `e` one), `test_fr1b2.py` (§e's girone→layout mapping, which turns out difficulty-dependent — see deviations). Re-run unchanged: `test_fr0a` 27/27, `test_fr0b` 29/29, `test_famus` 34/34, `test_s1` 16/16, `test_jg` 15/15, `test_f2b` 117/117, `test_m1a` 112/112, `test_m1b` 36/36. Known flakes (§8), both green on this run: `test_toast_diag` 43/43, `test_f4b1` 59/59. `node --check` on every script block green.
- Not tested: real phone, touch input, audio output (the music-exclusivity fix especially wants an ear on a real device).

## 0.4.5_33 — 2026-10-01 — FR1b2: Ferma floor-3 bolt layouts per loop + validator, eat-driven bar in practice/encounter

- 0.4.5_32 phone test OK, all FR1b1 deviations accepted (CLAUDE.md §10.9).
- **Floor-3 bolt layouts per loop** (Ferma run only): `FA_BOLTS=[L1,L2,L3]` (L1 = today's layout, unchanged, same array reference as `FA_LEVELS[2].bolts`; L2 = 8 bolts, L3 = 10 with 3 on two girders, both hand-designed harder — farther from the ladders on average, more bolts, longer route); `faInitBelts` picks `FA_BOLTS[min(loop,2)]` in a run, always L1 in practice/the maze encounter. A pure validator `faBoltCheck(bolts)` (no DOM, no FA state, transferable) checks R1 (on the girder), R2 (clear of every ladder, incl. broken), R3 (holes don't overlap, platform between them walkable), R4 (nothing in the start's safe zone) and R5 (no dead end — a BFS over every order bolts could be picked in, walking/ladder/jump moves only, `FA_JUMP_SPAN` = 85% of the real jump's max horizontal reach so a single 26 px hole is always comfortably jumpable); `faBoltStats` reports ladder-distance and route-length stats for comparison. Dev readout gains «· bulloni L1/L2/L3» on floor 3 of a run.
- **Eat-driven time bar in practice and the maze encounter too** (was Ferma-run-only since FR1a2): own tables `FA_PRAC.bar`/`FA_ENC.bar` (loop-1 values, independent of the run's own and of each other, §10.0). Both now get scheduled bites only (the 22% random eat is gone), a death costs one life and nothing else (no bite, no stock loss — the old −10 s rule is gone everywhere), the floor bonus is uneaten bites × 100 (the old `floor(stock)×10` is gone everywhere), and an empty bar runs the same last-bite ending (slow motion, fade, popup) before: practice shows today's Riprova/Esci, the encounter is treated as a loss (back to the maze, no reward) exactly like today's 0-lives case. Dev «Ultimo morso» now works in every mode's pause menu, not just a run's.
- Removed as dead (no longer referenced anywhere): `FA_EAT_P` (22% random-eat chance), `FA_DEATH_STOCK` (10 s death penalty), the continuous stock-drain branch in `faStep`.
- Size: +16,445 bytes (`index.html`).
- Tests: new `tools/fbstub/test_fr1b2.py` (46/46: FA_BOLTS[0] golden against the previous build, faBoltCheck passing on L1/L2/L3 and failing on 4 hand-made bad layouts incl. a genuine R5-only dead end found via the floor's own grill wall, L2/L3's stats both exceeding L1's, the right layout loading at gironi 3/6/9/12 and always L1 in practice/encounter, the new bar behaviour in practice and the encounter, an encounter win/loss paying/not paying the host maze run, the run's own bar/bolts untouched against the previous build, «Ultimo morso» dev-gated everywhere). Updated for the new practice/encounter invariant (superseding the pre-FR1b2 golden comparisons by design): `test_fr1a1.py` (one control check, 33/33), `test_fr1a2.py` (section h rewritten, 71/71), `test_famus.py` (one scheduled-bite check replacing the random-eat one, 34/34). Re-run unchanged: `test_fr1b1` 50/50, `test_fr0a` 27/27, `test_fr0b` 29/29, `test_s1` 16/16, `test_jg` 15/15, `test_f2b` 117/117, `test_m1a` 112/112, `test_m1b` 36/36. Known flakes (§8), both green on this run: `test_f4b1` 59/59, `test_toast_diag` 43/43. `node --check` on every script block green.
- Not tested: real phone, touch input, audio, a Ferma run played by hand through loop 2/3 to feel the harder bolt layouts.

## 0.4.5_32 — 2026-10-01 — FR1b1: Ferma loop difficulty, loop bonus, quicksave

- 0.4.5_31 phone test OK, all four FA-MUS deviations accepted (CLAUDE.md §10.9).
- **Loop difficulty, Ferma run only**: from loop 1 on (every 3 gironi), Algidone throws faster (throw wait ×0.9 per loop, floor ×0.6) and items move quicker (×1.05 per loop, cap ×1.3), on top of the difficulty setting. Practice and the maze encounter unchanged.
- **Girone loop bonus**: the same idea as the maze's own bonus (§10.4), with its own cap ×2.0. `girPts` tracks every point scored in the girone, including the floor-end bite bonus; the bonus counts up in the same animated number as the floor bonus, and shows as a second panel line «Bonus girone ×M +P» when positive.
- **Quicksave for the Ferma run**: a snapshot (girone, score, lives — nothing about the level in progress) is taken at the start of every girone. The run's pause menu gets «Salva ed esci» (same spot as the maze's); «Gioco corrente» now recognises a Ferma save and resumes that girone fresh (full time bar, new bite schedule). A dev run never saves. Cloud save carries a Ferma `S.quick` exactly like a maze one, no changes needed there.
- Size: +3064 bytes (`index.html`, LF-normalised).
- Tests: new `tools/fbstub/test_fr1b1.py` (50/50: loop factors at 7 gironi incl. the caps, the girone bonus math and its reset, that «Partita finita»'s payout reflects the bonus-inflated score, a save/resume round trip losing mid-floor progress by design, a golden check that the maze's own quicksave/resume is untouched, a dev run never writing `S.quick`, and a Ferma `S.quick` surviving the cloud-save string round trip). Re-run green: test_fr1a2 67/67 (two pre-existing button-list checks updated for the new «Salva ed esci» entry), test_fr1a1 33/33, test_famus 34/34, test_fr0a 27/27, test_fr0b 29/29, test_f2b 117/117, test_u1 27/27, test_s1 16/16. `node --check` + headless smoke test green.
- Not tested: real phone; a Ferma run played by hand through several loops to feel the difficulty ramp and the bonus sizes.

## 0.4.5_31 — 2026-10-01 — FA-MUS: Ferma Algidone! soundtrack, bite sound

- 0.4.5_30 phone test OK, all seven FR1a2 deviations accepted (CLAUDE.md §10.9). The earlier ffmpeg stop was correct — no ffmpeg or audio library available in this environment, only an unrelated app's bundled binary; the owner cut the loop in Claude chat (§6 rule 7: 54.4s of the 111s original, beat-aligned, 0.8s equal-power crossfade, MP3 48 kbps mono) and uploaded `refs/ferma_algidone/fa_music_loop.mp3`, embedded as-is.
- **Ferma Algidone! now has music** (`music.fa`, `FA_MUSIC_B64`): plays in practice, the maze encounter and a Ferma run alike, across intro cards, floors, gironi, deaths and respawns; paused with the game (pause menu and backgrounding, via the existing `faPause`); silent on leaving to the maze, the menu track resumes on leaving to the menu; respects the music on/off/volume options.
- **Last-bite ending**: the music slows to ×0.3 with the action, then fades out over the same second the screen fades to black, and stops the instant the «Algidone ha finito tutto!» popup shows.
- **`loopTrack` gained a generic `rate` (playbackRate) property**, alongside the existing `volume` one, reset on `release()` — every other track defaults to rate 1, unaffected.
- **Dev tools**: upload/reset for `music.fa` (open to every dev, Opzioni › Sviluppatore › Ferma Algidone!), export target `music.fa`; a new SFX slot `sound.fa.bite` (synth placeholder, dev upload/reset/export) plays at every scheduled bite in a run and every eat in practice/encounter.
- Size: +446 180 bytes (`index.html`, LF-normalised — the embedded MP3, base64, is the entire delta).
- Tests: new `tools/fbstub/test_famus.py` (34/34: starts in all three modes and survives a floor change/death, pause/resume, exit-to-maze silence vs exit-to-menu, the last-bite rate/fade/stop sequence, the music-off case, dev upload/reset/export, the bite sound on a scheduled bite and on a practice eat, and that the other three tracks still start with rate 1). Re-run green: test_fr1a2 67/67, test_fr1a1 33/33, test_u1 27/27, test_toast_diag (counts in the commit), test_f3b/test_f4a/test_f4b1 (A0/M7 audio-adjacent suites). `node --check` + headless smoke test green.
- Not tested: real-device audio above all — how the track actually sounds looped, the last-bite slow-down/fade/stop heard live, the bite sound's synth placeholder, and volume levels relative to the other tracks.

## 0.4.5_30 — 2026-10-01 — Ferma HUD fix + FR1a2: the Ferma run's time bar

- 0.4.5_29 phone test: all OK except «Esci» hidden by the bug icon; FR1a1 deviations accepted (CLAUDE.md §10.9).
- **Fix — Ferma HUD vs the bug icon**: every panel button was already the topmost element at both phone sizes; the real problem was the run HUD row (score, pile, bar, lives, «Girone N», bug icon, pause) needing 394 px and overflowing screens narrower than that, so the pause button (the way to «Esci») sat under/off the screen beside the icon. The girone label (`#fawv`) moved out of the HUD into the stage (top-left, non-interactive); the HUD now fits 360/390/412. The bug icon stayed where it was on every screen.
- **FR1a2 — eat-driven time bar, Ferma run only**: `FA_RUN.bar` table (L1 120 s, −15 s/loop, min 75; N1 12 bites, −2/loop, min 6, then ±1 at random). Algidone no longer eats at random in a run: bites fall due every `(L/N)(1±15%)` s of play time (each due time measured from the previous due time), wait for a throw in progress, then the usual eat animation; each bite removes exactly 1/N of the bar, drained smoothly. The clock runs only while playing (not in the intro card, pause, death animation, win sequence or last-bite ending; it runs during the respawn invulnerability). A death costs no bite and no bar. Floor win: bar frozen, bonus = uneaten bites × 100 (replaces `floor(stock)*10` in a run). Last bite: ×0.3 slow motion for 1.5 s, 1 s fade to black, popup «Algidone ha finito tutto!» / «Continua» → `runPayout` → «Partita finita». Game over = 0 lives or empty bar.
- Dev: readout «morsi X/N · prossimo Ys» under the girone label; «Ultimo morso» in the run's pause menu (one bite left, next in 1 s).
- Unchanged: practice (Giochi) and the maze encounter (continuous drain, random eat, 10 s death stock loss, `floor(stock)*10`) — golden-tested against 0.4.5_29; maze, music, quicksave, encounters, loop difficulty scaling.
- Size: +3693 bytes (`index.html`, LF-normalised).
- Tests: new `tools/fbstub/test_fr1a2.py` (67/67). Re-run green: test_fr1a1 33/33, test_fr0b 29/29, test_fr0a 27/27, test_u1 27/27, test_toast_diag 43/43, test_s1 16/16, test_f6 60/60. `node --check` + headless smoke test green.
- Not tested: real phone (HUD/tap on a real device, feel of the bite pace and of the slow-motion ending), audio (no eat sound exists today, none added); a whole Ferma run played by hand.

## 0.4.5_29 — 2026-10-01 — FR1a1: Ferma Algidone! run shell

- 0.4.5_28 phone test OK (FR0 complete); FR0b deviations accepted; FR1a split into FR1a1 / FR1a2 / FA-MUS (CLAUDE.md §10.8/§10.9).
- **«Ferma Algidone!» is playable as a run** from «Nuovo gioco» / «Hardcore» (Uomo roccia's chooser; Algidone still goes straight to the maze). `startFermaRun` → `FA.run` (G=null), `FA.score`/`FA.lives` aliased onto it; own table `FA_RUN={lives:3,hardRefill:false}`.
- Girone g plays level (g−1) mod 3, looping after the floor-3 collapse. Floor win → `onGironeClear` (career gironi, girone achievements); «Avanti» → `onGironeAdvance` + lives refill (not in Hardcore). Every run win panel is «Avanti» + «Esci» (no Riprova/Rigioca); the lost panel is «Continua».
- Soft respawn in a run: a death costs one life only (no 10 s stock loss, no forced eat); bolts/holes, belts, stock, score carry on; items cleared, 2 s invulnerability, throw grace as today.
- End: 0 lives → lost panel → `runPayout(FA.run)` → «Partita finita» (split out of `finishRun` as `runOverScreen`, shared by both games; «Ancora!» restarts the same game); pause/win-panel «Esci» → quiet end with payout. No quicksave (FR1b).
- `activeRun()`: `dfc`, `gcar`, `curD`, `ach`'s dev check and `faReal` read the active run (maze values unchanged, golden-tested).
- Display: intro card «Girone N · <piano>», HUD «Girone N» (run only). Dev: «Partita Ferma dal girone N» next to «Vai al girone».
- Unchanged: practice, the maze encounter, stock bar, stock bonus, throws/eats, difficulty, `bjAfterClear`, music.
- Size: +3947 bytes (`index.html`, LF-normalised).
- Tests: new `tools/fbstub/test_fr1a1.py` (33/33); re-run listed in the session report. `test_s1.py` updated (the only existing test touched): its three «In arrivo» lock checks (option disabled, locked click does nothing, arrow skip) became one check that both options are enabled — the lock is gone by design (18 → 16 checks).
- Not tested: real phone (touch pad, HUD width with «Girone N» on a real device, audio); a Ferma run played by hand end to end (wins are driven by `faWin`/`faFinalWin` + `faStep`, deaths by `faDie`).

## 0.4.5_28 — 2026-10-01 — FR0b: girone hooks, runPayout, host runs, no behaviour change

- 0.4.5_27 phone test OK; FR0a deviations accepted; both logged in CLAUDE.md §10.9 with the step-0 stop and the owner's option-1 decision.
- **Two girone hooks** in the run-layer block, each reading only its run argument: `onGironeClear(run)` = the last-pellet moment (career gironi +1, `ach("clear")`, `ach("stage",{n:run.girone})` with the OLD girone, all behind `!run.dev`); `onGironeAdvance(run)` = the end of the 1.6 s timer (`run.girone++`, g5 unlock, sec unlock + toast). The pellet code and the "clear" branch now call them where those statements were; every other maze statement stays in place and order. No `ach()` change.
- **`runPayout(run,o)`** = the run-level half of `finishRun` (sordi/XP, 4 achievements, `S.quick=null`, `persist()`, `cloudFlush()`); `finishRun(o)` keeps its signature and effect order and does the maze-only rest (`G=null`, over screen / menu + toast, «Ancora!»).
- **Host runs**: `FA.enc.host = G.run` for a real Ferma encounter, `faEncPay` adds to it; `B.host = G.run` for `startGamblador({run:true})`, used by `bjScore`/`bjSetScore` and the buy-in. Practice/non-run tables untouched.
- `tools/fbstub/sim_e6_results.json` added to `.gitignore`.
- Size: +936 bytes (`index.html`, LF-normalised).
- Tests: new `tools/fbstub/test_fr0b.py` (golden comparison against the previous build 0.4.5_27 on: a real girone clear sampled at both moments incl. g5/sec, quitting inside the clear window, `finishRun` quiet/normal + «Ancora!», a `devJump` clear, the Ferma encounter pay-out, El Gamblador win and loss through real hands; plus the hooks and `runPayout` on plain run objects with `G=null`, and a dev run object). Re-run: `test_fr0a`, `test_m1a`, `test_m1b`, `test_f2b`, `test_u1` (forced Ferma invite / `bjAfterClear`), `test_b2`, `test_e5a`, `test_e5b`, `test_s1` (counts in the session report). `node --check` + headless smoke test green.
- Not tested: real phone; a Ferma encounter played to the end by hand (the pay-out is called directly after a real invite → `startFerma`); El Gamblador's raise/double/surrender paths (only stand hands, win and loss).

## 0.4.5_27 — 2026-09-30 — FR0a: run layer (G.run + aliases), no behaviour change

- 0.4.5_26 phone test OK (banner ×1.8 at girone 8, ×1.44 at girone 4), logged in CLAUDE.md §10.9 with the owner's FR0 answers (Q1–Q4) and the step-0 audit.
- **Run layer** (new self-contained block before `devJump`): `RUN_ALIAS` (name on `G` → run field, `stage→girone`), `mkRun(o)` (plain run object with today's defaults), `RUN_PROTO` (one get/set pair per alias onto `this.run`), `mkMazeG(o)` (the one builder of a fresh maze `G`, used by `startGame`'s new-game branch and by `devJump`), `mazeGFromSave(q)` (resume). Every maze `G` is `Object.create(RUN_PROTO)`: `G.stage`/`G.score`/`G.lives`/… are inherited accessors onto `G.run`, never own properties, so every existing reader/writer (HUD, `update`, `finishRun`, `bjSetScore`, `faEncPay`, dev UI) is untouched.
- **Quicksave** unchanged in code: its JSON clone now carries `run` and none of the aliased names. **Resume**: a quicksave with `run` fills any missing run field from `mkRun`; an old-shaped one (loose `stage`/`score`/…) moves them into a new run and deletes them as own props; missing `girPts` → 0, missing `game` → `"maze"`; every other migration default (incl. remaining aura time) unchanged.
- Deviation from the brief: `newRun(o)` already exists (S1's game chooser), so the run builder is named `mkRun(o)`.
- Size: +1615 bytes (`index.html`, LF-normalised).
- Tests: new `tools/fbstub/test_fr0a.py` (27/27: real «Nuovo gioco» click, girone clear via `update`, alias writes, no own aliased props / JSON carries `run`, same run key set from `startGame` and `devJump`, quicksave→resume round trip, old-shaped quicksave, professor-win start, dev jump to girone 8 writing nothing). Re-run unchanged: `test_m1a` 112/112, `test_m1b` 36/36, `test_b2` 99/99, `test_f2b` 117/117, `test_e5b` 35/35. `node --check` + headless smoke test green.
- Not tested: real phone — please start a new run, clear a girone, save mid-girone from the pause menu and resume it with «Gioco corrente», and resume a quicksave made on 0.4.5_26 (old shape).

## 0.4.5_26 — 2026-09-28 — E6b: girone-bonus cap

- Owner decisions from the E6a report (`docs/releases/0.5-E6a-report.md`), logged in CLAUDE.md §10.9: Flag 1
  (bonus share up to ~52% at gironi 7–8) → cap the multiplier, nothing else. Flags 2–5 → no code change (girone
  6's slowness is the L-map/weak-bot combination, not the abilities per the ablation numbers; shooting's low
  hit rate matches the E3 phone test's own "feels fair" verdict; contact-dominated deaths and chain-driven
  girPts variance are both by design).
- **`GIR_BONUS.maxMult: 1.8`** (new field, next to `st2`/`st3`). At girone clear, `mult` is now
  `Math.min(GIR_BONUS.maxMult, classMult*(1+st2*n2+st3*n3))` — the one line touched. `girPts`, the bonus
  formula (`bonus=Math.round(girPts*(mult-1))`), the «Bonus girone ×N.N +P» banner and `finishRun`'s own
  order (limiter → `DIFF.mult` → `.7`, all after the bonus) are unchanged. The Ferma run's own `loopMult`
  table (§10.6, not built yet) is a separate table and is not touched by this cap.
- Effect: gironi 1–6 unchanged (their own max is ×1.68, under the cap already); gironi 7+ (and any girone
  9+ draw with enough stage-3 ghosts) now cap at ×1.8 instead of climbing past it — bonus share tops out
  around 44% of the girone's own points instead of ~52%.
- Tests: `test_m1b.py` extended (36/36) — the mult table for gironi 1–12 now expects the capped values
  (7/8: ×1.8, was ×2.03/×2.1), an explicit uncapped-vs-capped pair (girone 6 vs 8) plus a synthetic
  far-past-the-cap case (20× stage-3 weight, raw ×8.4) proving it clamps to exactly ×1.8 rather than
  merely landing near it, and the existing girone-7 clear-line/bonus-amount check now exercises the capped
  value end to end. `node --check` + headless smoke test green.
- Not tested: real phone — please clear a girone 7 or 8 and confirm the bonus banner reads «×1.8», not the
  old higher number.

## infra/docs — 2026-09-28 — E6a: balance measurement (no game change)

- Owner feedback logged first: 0.4.5_25 (E5b wall-breaking) phone-tested OK. **E5 complete.**
- New `tools/fbstub/sim_e6.py` (kept in the repo, re-run for E6b): headless-Chromium harness that drives
  `update(1/60)` directly (dev mode, `cancelAnimationFrame(raf)`) with a simple seeded-BFS bot, no secret
  abilities, playing both characters through gironi 1–12 at Normale, once scheduled and once with the dev
  Stadio override forcing stage 1 (the ablation baseline) — 5 seeds each, 240 runs, 192s wall time.
  Instrumentation wraps `MPROJ.spawn`/`GREASE.add`/`PANINO.startIntro`/`PANINO.eatSplit`/`smashFx`/
  `killPlayer` for event counts; nothing in `index.html` changes.
- Two real bugs in the bot itself were caught and fixed before trusting any numbers (both documented in
  code comments in `sim_e6.py`): a one-tick decision-timing lag against the game's own `step()`/`chooseP()`
  re-consultation, and a "nearest pellet" re-pick every tick that let two similarly-distant pellets swap
  which one looked nearer, ping-ponging the bot forever. Both reproduced deterministically (the second one
  with ghosts disabled entirely, isolating it from anything ability-related) and fixed before the real
  sweep ran.
- Report: `docs/releases/0.5-E6a-report.md` — per-character tables (map class/ghosts/stages, clear time or
  timeout, deaths by cause, sprint/shoot/grease/panino rates, girPts/bonus share), a stage-1-ablation delta
  table per character, 5 flagged anomalies with direction (no values changed), and caveats on the bot's own
  limits. No VERSION bump — report-only, `index.html` untouched.

## 0.4.5_25 — 2026-09-28 — E5b: Super Panino wall-breaking
- **Scope**: only the merged Super Panino host (E5a, 0.4.5_24). Normal ghosts, aerei, grease and the merge/split/eat rules are unchanged; `chooseE` (normal ghosts' own direction choice) was never touched. Spec: CLAUDE.md §10.3 ("breaks walls in its path via the shared smashable() helper; protected cells never").
- Owner feedback logged first: 0.4.5_24 (E5a merge/intro/burger/speed/contact/split/eating) phone-tested OK — no code change needed.
- **`PANINO_CFG` additions**: `breakMax:8` (max walls broken per merge), `breakPause:.3` (seconds held still after each break) — both from the brief's own numbers, no §10.3 number existed for either so no conflict to report.
- **`PANINO.choose(e)`** (new, the host's own direction choice — "inside the PANINO module" per the brief, never touching `chooseE`): candidate directions = the 4 minus the reverse; a candidate is open when the next cell is floor **or** `smashable(nx,ny)` with the per-merge break budget (`e.pan.breaks`) not yet exhausted. Picks the candidate closest to the player with probability `e.chase` (already forced to 0.9 while merged), otherwise a random open candidate — the same shape as `chooseE`'s own chase roll, just against this wider candidate set. A dead end (nothing open) falls back to the reverse, same as `chooseE`. Entering a smashable cell breaks it there and then (see below) and holds — `e.dir=null`, so `step()`'s own tile-boundary check consumes none of that frame's movement.
- **Reused, not duplicated, per the brief's own instruction**: `smash(x,y)` was split into `smashFx(x,y)` (grid→floor, crack/debris/smoke particles, `G.shake` — the part that has nothing to do with the player) and a thinner `smash(x,y)` (calls `smashFx`, then does the player-only bits: `G.st` stress/hit-count bookkeeping, `sfxSmash`). `PANINO.choose` calls `smashFx` + its own `sfxSmash(e.pan.breaks)` directly — reusing the one existing SFX exactly as asked, without incrementing the player's own boar-ability stress/hit counters (which would have been wrong: a ghost's break has nothing to do with the player's Cinghiale stress bar). No second copy of the grid/dust/shake code exists anywhere.
- **The hold**: `e.pan.pauseT` (seconds remaining) is checked one level up, in the main per-ghost loop — while it's `>0` the loop just counts it down and skips `step()`/`choose()` entirely for that ghost that frame (no movement at all, matching "holds still"); once it reaches 0, normal stepping resumes and the next `PANINO.choose` call finds the cell already floor. The intro freeze, the 12s life, contact, eating and the split from E5a are all unchanged — `breakPause` time ticks inside that same 12s, exactly as specified, because the life countdown (already pulled out of `E1UpdateGhost` in E5a for the same "keeps running while scared" reason) never stops just because the host is paused.
- **Persistence**: broken cells are ordinary `G.grid` mutations, and `G.grid` was already part of `quicksave()`'s existing deep clone — no special-casing needed, exactly like a player's own smash. Confirmed by test: a cell broken mid-merge stays floor after the split and only reverts once the next girone's `freshGrid()` runs.
- **Pellets**: a wall cell never held a pellet to begin with (`"#"` vs `"."` are always distinct grid values), so "the same rule as a player smash" is satisfied automatically — a broken cell is always plain floor (`" "`), never a pellet. No code needed here beyond reusing `smashFx`.
- Art owed (§6 rule 11, §8): unchanged from E5a — the merged body is still `burgerCv()` scaled up; breaking reuses the existing crack/debris/smoke particle set, no new art.
- **E5 is now complete** (merge/intro/eat/split from E5a + wall-breaking from E5b); next up is E6 (balance pass).
- Tests: new `tools/fbstub/test_e5b.py` (35 checks) — breaking through to reach the far side of a wall (cell becomes floor), a 30-simulated-second sweep on one S/M/L map each confirming every protected cell that was a wall stays a wall, `breakMax` respected, and the host never clipping a wall tile; the `breakPause` hold (position unchanged right after a break, then moving on); a scared Super Panino breaking nothing; a lone never-merged stage-3 attrezzo breaking nothing (with the *other* ghosts in the scene forced to stage 1 so they can't naturally pair up with each other mid-test and confuse the result — a real flake caught while writing the test, not a game bug); neither ghost breaking anything after a split; a broken cell staying floor after the split and only reverting at the next girone start; the pellet rule; and the dev button through a real click. `test_e5a.py` (66/66), `test_p1b.py` (21/21) and `test_e1a.py` (21/21) re-run clean. `node --check` + headless smoke test green.
- Not tested: real phone — please watch a Super Panino punch through a wall (girone 8+, or the Stadio/Forza-Super-Panino dev tools), confirm the impact reads clearly and the brief hold before it moves on feels right, not instant and not sluggish.

## 0.4.5_24 — 2026-09-28 — E5a: Attrezzi Super Panino merge (fills ABIL.panino)
- **Scope**: only the "attrezzi" family (Algidone's enemies), stage 3 — merge, intro, merged movement/contact/eating, timed split. **No wall-breaking** (that's E5b). Aerei and grease (E4) are unaffected. Spec: CLAUDE.md §10.3.
- Owner feedback logged first: 0.4.5_23 (E4 grease) phone-tested OK — no code change needed.
- **`PANINO_CFG`**: `{range:1,introT:1.0,life:12,size:1.6,speedMult:1.25,chase:.9,score:3200,hitExtra:.3,graceStart:6,reMergeCd:10,maxActive:1}` — exactly §10.3's own numbers, no conflict with the brief's fallback this time.
- **Data model**: both ghosts stay in `G.en` and keep stage 3 (ghost count and M1b's bonus `stageMult`, which reads `G.en[].stage`, are unaffected). Host = whichever of the pair the per-ghost loop reaches first (its own array order, never compared explicitly) and carries `e.pan={partner:<index>,t,chaseSave}`; the partner gets a plain `e.merged=true` flag — hidden: not stepped, not drawn, no collision, no abilities, checked with one `if(e.merged)continue` right at the top of both the main update loop and the ghost-draw loop.
- **Trigger** (`ABIL.panino.update`→`PANINO.check`, dispatched per-ghost like grease so it only ever runs on an `E1Active` stage-3 attrezzi ghost): scans other stage-3 attrezzi ghosts for one that's also `E1Active`, off its own `reMergeCd`, and within Chebyshev range 1; skipped for the first `graceStart` (6s) of a girone **and after a death respawn** — reusing `G.anim` for this needed no new field at all, since `resetActors()` already resets it to 0 on both girone start and every death respawn (§4). Capped at `maxActive` (1) via a single `G.en.filter(x=>x.pan).length` check.
- **Intro** (~1s, `PANINO_CFG.introT`): a dedicated `G.state="panintro"`, the exact same early-return pattern `"ready"/"dying"/"clear"` already use in `update(dt)` — while it holds, nothing else in the function runs at all (player, ghosts, projectiles, power-up timer, respawn aura, grease lifetimes, cooldowns, the girone: all genuinely frozen, not faked). `PANINO.drawIntro` renders the slide-together + white flash + «SUPER PANINO!» text on top of the maze; `PANINO.finishIntro()` (called when `G.t` runs out) seeds the real 12s life onto the host and returns the state to `"play"`.
- **Merged** (12s life): host keeps its **normal** `step()`/`chooseE()` movement — walls stay walls, matching the "no wall-breaking in E5a" scope — with `chase` forced to `0.9` (saved/restored the same way E2's sprint does) and speed ×1.25 as one more multiplicative factor on the shared ghost speed line. The life countdown ticks **directly in the main per-ghost loop**, not through `E1UpdateGhost`/`ABIL.panino.update` — that path gates on `E1Active`, which excludes a scared ghost, but §10.3 explicitly wants "the 12s keep running" while scared. **Real bug caught by the first test run, fixed before it shipped**: the life field starts at a placeholder `t:0` during the intro (the real value is only seeded at `finishIntro`); the very first version of this tick ran unconditionally and re-split the pair on the *same frame* the merge began. Fixed by skipping the tick while `G.state==="panintro"`.
- **Grease pause**: `ABIL.grease.update` gained one line, `if(g.pan)return`, so a merged host's own grease timer pauses (not resets) for the duration — §10.3's "both ghosts' grease countdowns pause".
- **Contact**: reuses the existing ghost-contact check verbatim, with `PANINO_CFG.hitExtra` (0.3) added to the hit radius only while `e.pan` is set — same invulnerability/power-up/active-ability gate as any other ghost, no special-casing needed.
- **Power-up / eaten**: `activatePower()` needed no changes — it already scares every non-eaten ghost and calls `E1CancelGhost`, which now resolves to a no-op for `panino` specifically (`reset()` only touches cooldown bookkeeping), so the merge survives being scared exactly as required. `eatPlane(e)` gained one guard at the top, `if(e.pan){PANINO.eatSplit(e);return}`, routing a scared host's capture to its own flat +3200 award (added straight to `G.score`/`G.girPts`, **not** through the normal chain-doubling path — `G.chain` is left untouched on purpose) and puts both ghosts into the usual eaten/eyes state.
- **Split** (`PANINO.split`, life expiry) places the partner on the nearest open tile within 2 rings of the host's *current* tile (never a wall or the house), moving opposite the host's own direction, restores the host's original chase, and starts `reMergeCd` (10s) on both ghosts via their own `g.ab.panino.cd`.
- **Clear points**: `PANINO.clear()` sits next to the existing `GREASE.clear()`/`MPROJ.clear()` calls — inside `resetActors()` (girone start + every death respawn; `G.en` is rebuilt from scratch there anyway, so this is a defensive no-op in practice) and at the girone-end "all pellets eaten" transition (where it's the one call site that actually matters, since `G.en` isn't rebuilt until ~1.6s later). `quicksave()` never persists a live merge either: it splits any active pair in the **cloned** save object only (`PANINO.snapshotSplit`, same placement rule as a real split) and resets a stray `"panintro"` state back to `"play"` — the live game object is untouched.
- **Dev aid**: «Forza Super Panino» (`#jgPan`, next to the girone-jump tools, `data-dev`-gated) merges the first two `E1Active` stage-3 attrezzi immediately, ignoring range/`graceStart`/`reMergeCd` — still plays the real intro. Toasts «Servono 2 attrezzi stadio 3 fuori casa» when fewer than two exist. Since Opzioni has no in-game entry point, the realistic dev workflow is: `devJump` into a girone with 2+ stage-3 attrezzi, then `go('menu')`/pause-save back to Options without nulling `G` (only `finishRun` does that) — the button then still operates on that same live game object.
- Art owed (§6 rule 11, §8): the merged body is `burgerCv()` scaled up with the stage-3 double marker — procedural, same status as grease's puddle; the intro flash/text are procedural too.
- Tests: new `tools/fbstub/test_e5a.py` (66 checks) — every trigger gate (range, stage, scared/eaten/waiting/in-house, `graceStart`, `reMergeCd`, aerei never eligible, `maxActive`), the intro freeze (nothing moves/decays for `introT`, then seeded to the full life), merged behaviour (ghost count/stage unchanged, partner truly inert and never collides, host ×1.25 speed / 0.9 chase restored after split), contact (kills at the larger radius, respects invulnerability), grease pausing while merged, a 20s simulated chase confirming the host never overlaps a wall, the natural split's placement, power-up persistence with the life timer still ticking while scared, the eaten-split's flat +3200 (chain untouched, both ghosts eaten), clearing on death/girone-start/girone-end and quicksave, and the new dev button both through a real click and its absence for a player. `test_e1a.py` (21/21), `test_e4.py` (29/29) and `test_m1b.py` (31/31) re-run clean. `node --check` + headless smoke test (menu renders, a real Uomo roccia run starts through the S1 game-chooser popup, a 5-ghost Algidone run ticks 120 frames — zero console errors throughout) green.
- Not tested: real phone — please look for two stage-3 Attrezzi (girone 8+, or via the Stadio dev override) meeting up, confirm the merge/intro/burger reads clearly, and that it can be eaten during a power-up for a big score jump.

## 0.4.5_23 — 2026-09-27 — E4: Attrezzi grease (fills ABIL.grease)
- **Scope**: only the "attrezzi" family (Algidone's enemies), stage ≥ 2 — stage 3 keeps grease alongside Super Panino, per the owner's own §10.3 decision. Aerei are unaffected. Spec: CLAUDE.md §10.3.
- **Conflicts reported, resolved per the brief's own rule ("where §10.3 gives a number, use it")**: the brief's `GREASE_CFG` fallback specified `dropEvery:1.5s`, `maxPerGhost:4`, `life:5s`; §10.3 specifies **every 8s**, **max 3 per ghost**, **fades out after 10s** instead. Built and tested to §10.3's numbers, not the fallback block. `slowMult` (×0.6) matches both — no conflict there.
- **`GREASE_CFG`**: `{dropEvery:8,life:10,maxPerGhost:3,slowMult:.6,color:'#c8a23a'}`.
- **`GREASE` module** (a shared floor-puddle list, not per-ghost state): `add(x,y,owner)` refuses a tile already holding a puddle or inside the house (`inHouse`), and evicts the calling ghost's own oldest puddle first once it already holds `maxPerGhost`; `update(dt)` counts every puddle's remaining life down and drops it at 0; `draw(ctx)` renders a procedural glossy ellipse per puddle, alpha fading over the puddle's own remaining-life value (so the last second fades visibly) — called in `draw()` right after the glowing-rock block, before the ghost-drawing loop starts, so puddles sit under the actors; `at(tile)` is the lookup both the player-speed line and the tests use; `clear()` empties the list.
- **Behaviour** (`g.ab.grease={t}`, a plain countdown — no phase machine needed, unlike sprint/shoot): while `E1Active(e)` (E1a's own stage/scared/eaten/waiting/in-house gate) and the ghost has a direction (`g.dir!=null`, i.e. actually moving, not sitting mid-spawn), `t` counts down from `dropEvery`; at 0 it calls `GREASE.add(g.tx,g.ty,g)` on the ghost's current tile and resets to `dropEvery`.
- **Player slow**: the existing player speed line gained one more multiplicative factor, `(GREASE.at({x:P.tx,y:P.ty})?GREASE_CFG.slowMult:1)` — applies regardless of invulnerability or an active secret ability (grease is terrain, not a hit, matching the brief's explicit "puddles do nothing while invulnerable? NO"). Ghosts read nothing from `GREASE` at all, so they're structurally unaffected, not just untested.
- **Clear points**: `GREASE.clear()` added next to `MPROJ.clear()` at both places that already clear projectiles — `resetActors()` (girone start and every death respawn) and the girone-end "all pellets eaten" transition. Never written onto `G`, so never in the quicksave (same pattern as `MPROJ`/`E1_STAGE_OV`).
- Art owed (§6 rule 11, §8): the puddle is a procedural glossy ellipse today — no skin art exists or is required yet.
- Tests: new `tools/fbstub/test_e4.py` (29 checks) — drop timing (nothing before `dropEvery`, exactly one puddle at the ghost's own tile once it elapses), no duplicate puddle on an occupied tile, never inside the house, `maxPerGhost` with oldest-first eviction, lifetime + removal, the player's ×0.6 speed on/off a puddle, ghosts confirmed unaffected while standing on their own puddle, every no-drop gate (scared/eaten/waiting/in-house), `clear()` on both a forced death and girone start, absence from the quicksave, and that Uomo roccia's aerei and stage-1 attrezzi never get a `grease` entry at all. `test_e1a.py` (21/21), `test_e2.py` (31/31) and `test_e3.py` (41/41) re-run clean. `node --check` + headless smoke test (menu renders, a run starts, zero console errors throughout) green.
- Not tested: real phone — please look for the amber puddle under a stage-2+ Attrezzo (girone 4+, or via the Stadio dev override) and confirm Algidone visibly slows while crossing one.

## 0.4.5_22 — 2026-09-27 — E3: Aerei shooting (fills ABIL.shoot)
- **Scope**: only stage-3 Aerei (Uomo roccia's enemies); Attrezzi/stage-2 unaffected. Spec: CLAUDE.md §10.3.
- **Conflicts reported, resolved per the brief's own rule ("where §10.3 gives a number, use it")**: the brief's `SHOOT_CFG` fallback specified a projectile at `1.5×` the player's current speed and a `7s` cooldown; §10.3 specifies a **flat 7 tiles/s** and a **4s cooldown** instead. Built and tested to §10.3's numbers, not the fallback block — `speedMult` became `projSpeed:7` (a flat rate, not a multiplier), `cd:4` (not 7). `range`/`cdStartMax`/`gapAfterSprint`/`color` had no §10.3 number, so the brief's fallbacks stand unchanged.
- **`SHOOT_CFG`**: `{range:8,aim:.5,projSpeed:7,cd:4,cdStartMax:4,gapAfterSprint:1.5,color:'#ff3040'}`.
- **Behaviour** (`g.ab.shoot={phase,t,cd,dir}`): `idle` counts `cd` down, then enters `aim` (0.5s, holds still) when sprint is idle, at least 1.5s have passed since that ghost's last sprint ended, and `losRC` (E1b, reused verbatim) confirms line of sight within 8 tiles — the direction is captured once and stored, not re-checked continuously. At the end of aim: one projectile via `MPROJ.spawn` (E1b, reused verbatim — no new projectile code) at the flat `projSpeed`, along the stored direction; `cd=SHOOT_CFG.cd`.
- **The 1.5s gap enforced both ways** via two shared per-ghost timestamps (`g.lastSprintEnd`, `g.lastShotEnd`, not nested inside either ability's own state, since both abilities read/write across each other): `ABIL.sprint`'s idle→wind trigger gained one extra condition (time since the ghost's last shot ≥ `SHOOT_CFG.gapAfterSprint`) — the only change made to `ABIL.sprint` this build, exactly as scoped. A **cancelled** aim (scared/eaten/power-up/girone-end, via the existing `E1CancelGhost`) never fires and does not set `lastShotEnd` — the gap is specifically "after a shot", not after every aim attempt.
- **Bug found and fixed in the same build**: the shared ghost speed line (touched for the sprint multiplier in E2) checked only `sprint.phase==="wind"` to hold the ghost still — a stage-3 ghost could keep moving while "aiming". Now also checks `shoot.phase==="aim"`. Caught by `test_e3.py`'s own "no movement during aim" check before it ever reached a build; the fix is one boolean added to that one line, nothing else touched.
- **Visuals** (procedural, `ABIL.shoot.draw`, skipped while scared/eaten per `E1DrawGhost`): a flashing colour-pulse overlay (sprite-flash proxy, same constraint as E2's sprint jitter — `draw(ctx,g)` has no access to the sprite drawn earlier in the loop) plus a short pulsing aim line in the locked direction.
- Art owed (§6 rule 11, §8): aim flash + aim line + projectile are procedural today — no skin art exists or is required yet.
- Tests: new `tools/fbstub/test_e3.py` (41 checks) — start-cooldown range, LOS/range/wall/diagonal aim gating, the aim→fire timeline (zero movement, exactly one projectile, direction, flat speed, cd), the 4s cooldown, "never aims while sprint is active", the 1.5s gap both ways (via a direct time-skip rather than looping real ticks, so the ghost's own ordinary movement can't wander it off the test's LOS alignment), every no-aim gate, a power-up cancelling mid-aim with no projectile, a real fired shot going through the shared `MPROJ` hit path (lethal normally, harmless powered-up), stage-2 Aerei and all Attrezzi never getting a `shoot` entry, and reset-to-idle on both a forced death and a girone start. `test_e2.py` (31/31), `test_e1a.py` (21/21) and `test_e1b.py` (29/29) re-run clean. `node --check` + headless smoke test (including 10 simulated seconds of real play) green.
- Not tested: real phone — please look for the red aim flash + aim line on a stage-3 Uomo roccia enemy (girone 9+ with enough stage-3 ghosts, or via the Stadio dev override), and that a hit projectile costs a life as expected.

## 0.4.5_21 — 2026-09-27 — sprint tuning (owner phone-test feedback)
- Owner feedback on 0.4.5_20: sprint works but triggers a bit too often; power-ups already counter it fine, so only a slightly longer gap is wanted.
- `SPRINT_CFG`: `cd` 6→8, `cdStartMax` 3→4. Nothing else in the ability changed (range/wind/mult/dur/shakePx/color all as 0.4.5_20).
- Tests: `test_e2.py` updated to the new values (most checks already read `SPRINT_CFG.cd`/`cdStartMax` live, so only the fixed-margin "no re-trigger within the cooldown" check needed its iteration count widened to stay meaningfully short of the new ~8s cd); 31/31 green. `node --check` + headless smoke test green.
- Not tested: real phone — please confirm the lower frequency feels right.

## 0.4.5_20 — 2026-09-27 — E2: Aerei sprint (fills ABIL.sprint)
- **Scope**: only the "aerei" family (Uomo roccia's enemies), stage ≥ 2; Attrezzi/Algidone untouched. Spec: CLAUDE.md §10.3.
- **`SPRINT_CFG`** (own tuning table): `{range:6,wind:.6,mult:1.8,dur:1.5,cd:6,cdStartMax:3,shakePx:2,color:'#ffb000'}`.
- **Behaviour** (`g.ab.sprint={phase,t,cd,chaseSave}`): `idle` counts `cd` down, then rolls `losRC` (E1b) to the player's tile within `range`; `wind` (0.6s) holds the ghost still (speed forced to 0), no path choice; `run` (1.5s) applies `×1.8` speed and forces a deterministic chase by temporarily setting `e.chase=1` (reusing `chooseE`'s own existing `Math.random()<e.chase` branch — no change to `chooseE` itself, "normal path choices at junctions" for free) — restored on exit. After `run`, `cd=SPRINT_CFG.cd` (the full 6s, not the shorter random start range).
- **Interrupts** (scared / eaten / girone end, while mid wind-up or run only — an idle ghost's own countdown is left alone): a new generic `E1CancelGhost(e)` (iterates the ghost's own abilities and calls each `reset()`, not sprint-specific) is called from `activatePower()`, `eatPlane()` and the girone-end trigger (alongside `MPROJ.clear()`); `ABIL.sprint.reset()` only actually cancels when the ghost isn't already `idle`, restoring `chase` and setting the full `SPRINT_CFG.cd`. A death respawn or girone start goes through the ordinary `reset()`+`onSpawn()` pair (E1a), which always ends on `onSpawn`'s fresh randomised `cd` — the two paths (interrupted mid-ability vs. a fresh ghost) land on the two different cd values the brief describes, without extra branching.
- **Movement safety**: the only shared-code touch is the ghost speed line in `update()`'s ghost loop (`e.speed=…*(phase==="run"?SPRINT_CFG.mult:1)`, `0` during `wind`). Checked whether `step()`'s per-frame stepping could overshoot a tile at ×1.8 (max ≈0.4 tiles/frame at a 0.05s-clamped `dt` — `step()`'s own `while(d>1e-6)` loop already re-evaluates `choose()`/`wall()` at every tile boundary for *any* speed) and confirmed with a 20-simulated-second stress test (`test_e2.py`) that a sprinting ghost never lands on a wall tile or an illegal `prog`; no clamp/split was needed beyond what `step()` already does.
- **Visuals** (procedural, `ABIL.sprint.draw`, skipped while scared/eaten per the existing `E1DrawGhost` rule): `wind` — a small `±shakePx` jitter of 3 dust marks in `SPRINT_CFG.color`; `run` — 3 fading trailing circles behind the ghost's own direction. The ability's `draw(ctx,g)` signature (no `X,Y,c`, per E1a) means this draws an overlay near the ghost, not a literal shake of the sprite itself, which is drawn earlier in the same loop and out of this chunk's scope to touch.
- Art owed (§6 rule 11, §8): sprint's wind-up jitter and run trail are procedural today — no skin art exists or is required for them yet.
- Tests: new `tools/fbstub/test_e2.py` (31 checks) — LOS/range/wall trigger gating, the wind→run→cooldown timeline (~0.6s/~1.5s/~×1.8/no re-trigger within ~6s), the 0–3s start cooldown range, every no-sprint gate (scared/eaten/waiting/in-house, already covered by E1a's own dispatcher but re-verified here), a power-up cancelling mid wind-up and mid run, the 20s movement-safety stress test, Algidone never getting a `sprint` entry at all, and the reset-to-idle-with-fresh-cd behaviour on both a forced death and a girone start. `test_e1a.py` (21/21) and `test_e1b.py` (29/29) re-run clean. `node --check` + headless smoke test (including 10 simulated seconds of real play) green.
- Not tested: real phone — please look for the amber wind-up jitter and the brief speed-line trail on a stage-2+ Uomo roccia enemy (girone 7+, or via the Stadio dev override).

## 0.4.5_19 — 2026-09-27 — E1b: line-of-sight helper + maze projectile module
- **Scope**: two self-contained helper modules for E2 (sprint) and E3 (shooting), CLAUDE.md §10.3. No visible gameplay change — nothing calls them yet, the ABIL stubs stay no-op.
- **`losRC(from,to,maxTiles)`**: same row or column only (diagonal → `null`), plain (non-wrapped) distance so the two tunnel-edge tiles are never treated as adjacent, `from==to` → `{dir:null,dist:0}`. Blocking = `wall(x,y)` (the exact test the player's movement uses) **or** `inHouse(x,y)`: the map data has no separate "door" tile (`freshGrid` opens the whole house rectangle to floor), so the door is modelled as the same rectangle blocking sight from outside — the same zone `protectedCell` already treats as one for Cinghiale.
- **`MPROJ`/`MPROJ_CFG`**: `{radius:.18,color:'#ffe066',maxActive:12,playerR:.4}` (`playerR` is a new, dedicated hit radius for a thin projectile — no shared "player hitbox" constant existed to reuse). `spawn(x,y,dir,speed,owner)` (tile units, ignored past `maxActive`), `update(dt)` (moves by `speed*dt`, removes on leaving the grid — no tunnel wrap — or entering a wall, and on a player hit), `draw(ctx)` (a small procedural glowing orb, reads the global `cell` for scale), `clear()`.
- **Player hit**: circle overlap (`radius+playerR`); if the player is not invulnerable, not powered up (`G.power>0` ⇒ ghosts scared) and has no active secret ability (`G.st.on`), it goes through the **same death path a ghost contact uses** — factored the three-line `G.state="dying";G.t=1.3;playSnd("die")` out of the ghost-collision site into `killPlayer()`, called from both places (no duplicated death code). Otherwise the projectile just disappears; either way it's removed.
- **Hooked next to the E1a dispatcher**: `MPROJ.update(dt)` right after the ghost loop in `update(dt)` (so it freezes exactly when the rest of the maze does — `loop()`'s own pause gate skips the whole `update(dt)` call); `MPROJ.draw(ctx)` right after the particle draw in `draw()`. `MPROJ.clear()` runs from `resetActors` (girone start and every death respawn, alongside `E1InitGhosts()`) and separately at the girone-end trigger (all pellets eaten). Never written onto `G`, so never in the quicksave.
- Tests: new `tools/fbstub/test_e1b.py` (29 checks) — losRC's six required cases (open/wall/beyond-range/diagonal/tunnel-wrap/house-door), discovered at runtime against the real map geometry rather than hardcoded coordinates; MPROJ's movement, pause-freeze, wall/off-grid removal, `maxActive`, the hit gate's three immunity cases plus the normal-player death case, `clear()` at all three trigger points, and absence from `S.quick`. `test_e1a.py` re-run clean (21/21). `node --check` + headless smoke test green.
- Not tested: real phone — no visible change is expected in this build.

## 0.4.5_18 — 2026-09-27 — E1a: ghost stage ability framework (skeleton only)
- **Scope**: the framework E2-E5 plug abilities into (CLAUDE.md §10.3). No gameplay change this build except a visible stage-2/3 marker outline; ghost movement, chase, targets and release timing are untouched.
- **Data**: `STAGE_ABIL` (family → stage → ability ids: `aerei` stage2 `['sprint']`/stage3 `['sprint','shoot']`, `attrezzi` stage2 `['grease']`/stage3 `['grease','panino']` — stage-3 attrezzi keep grease, per the owner's decision) and `STAGE_MARK` (stage 2 = thin amber glow `#ffb000`, stage 3 = thicker double red glow `#ff3040`). Family reuses the existing `gcar()==="algidone"` check the maze draw code already uses to pick ghost art (`ALG`), rather than duplicating it (`E1Family()`).
- **Registry**: `ABIL` — one module per ability id (`sprint`, `shoot`, `grease`, `panino`), each `{id,onSpawn,update,draw,reset}`; all four functions are NO-OP stubs in this build, commented with the chunk that fills them in (E2/E3/E4/E5). Per-ghost state lives in `g.ab` (container created by the dispatcher; each ability's own `onSpawn` is responsible for populating its own key once it's no longer a stub).
- **Dispatcher**: `E1InitGhost`/`E1InitGhosts` (reset then onSpawn per ability of the ghost's stage) run at the end of `resetActors` — covers girone start and every death respawn alike, since both already go through that one function. `E1UpdateGhost` gates the per-frame `update` call on stage ≥ 2, not scared/eaten, not waiting, not inside the house (`E1Active`); called once per ghost right after its own `step()` in the maze's main loop. `E1DrawGhost`/`E1DrawMarker` draw the stage marker then each active ability's own `draw`, right after the ghost sprite in `draw()`; skipped for stage 1 and while scared/eaten.
- **Dev aid**: «Stadio» override (`#jgStOv`, auto/1/2/3) next to the girone-jump field in the "Salta al girone" dev accordion — forces every ghost's stage from the next `resetActors` (girone start or death reset) via `E1_STAGE_OV`, a module-level variable never written onto `G`, so it never reaches the quicksave; the `#jgro` dev readout appends `· stadio N` while an override is active. Absent from the DOM for a player (same dev-only accordion as `#jgN`/`#jgGo`).
- **Save compatibility**: an old quicksave resumed after this build (no `.ab` on its ghosts) gets one repaired via `E1InitGhost` in the `startGame(resume)` patch-up block, alongside the existing `mode`/`gt`/`stage` repairs.
- Tests: new `tools/fbstub/test_e1a.py` (21 checks) — table shape (both families/stages, every ability id fully registered), family-by-character, the update dispatcher's full gating matrix (stage/scared/eaten/waiting/in-house) via a spy on `ABIL.sprint.update`, reset+onSpawn call counts on girone start and after a forced death, marker-draw gating via a spy on `E1DrawMarker`, the Stadio override end-to-end through the real UI (readout text included) and its absence for a player, and that the override never lands in `S.quick`. Per the brief's cost rule, only `test_e1a.py` + `test_m1a.py` (112/112) + `test_b2.py` (99/99) were re-run, not the full suite; `node --check` + headless smoke test (menu renders, zero console errors, a run starts) both green.
- Not tested: real phone — please look for the amber/red glow outline on stage-2/3 ghosts (no other visible change expected).

## 0.4.5_17 — 2026-09-27 — fix: B2 «fantasmi sovrapposti» (house/wait start on L maps)
- **Owner phone test (0.4.5_16 retest)**: the 5th-ghost fix worked (all 5 present on L maps), but a new bug appeared — ghosts overlapping/stacked on each other at the start of a girone on L maps (5 ghosts); once released and chasing they looked and moved separately. Scope confirmed by the owner as house/wait-position only — chase/target/scatter untouched.
- **Reproduced first, then fixed** (Playwright, headless, against the pre-fix build): dev girone-jump to G8 (class L), logged every ghost's tile/pixel/state/wait at t=0/0.5/1/2s and right after a forced death. Ghost 0 (`tx13,ty12`) and ghost 4 (`tx13,ty12`) sat on the exact same tile from t=0 through t=1s, only separating once ghost 0 left the house at ~1s (matches "no stacking noticed once chasing"); S maps (mi 0-4) and M maps (mi 5,6,7,10,12,13) showed 3/4 fully distinct tiles at every timestamp — not affected.
- **Cause**: every map's `meta.ghosts` house-slot list has exactly 4 entries; `resetActors` picks each ghost's start with `MET.ghosts[i%MET.ghosts.length]`, so on an L map (5 ghosts, `CLASS_GHOSTS.L=5`) the 5th ghost (i=4) wraps back to slot 0 — the same tile as ghost 1 — and is drawn exactly on top of it for as long as both are still waiting. S (n=3) and M (n=4) never reach the wraparound. Confirms the owner's hypothesis (a); hypothesis (b) and the `chooseE` avoidance guess (both recorded unverified in §8 B2) were not the cause — the overlap is pixel-identical from t=0, not a chase-time convergence.
- **Fix**: gave each of the 4 L-class maps (Palude, Vulcano, Fabbrica, Gran Labirinto) a 5th house slot — bottom-center of the 3×3 house rectangle, at least one full tile from every other slot, still inside the house. `st.length` becoming 5 makes `i%st.length` a direct index for i=0..4 with no wraparound; no other code changed. Ghosts 1-4's slots and the 5th ghost's wait rule (4th's wait + 2.5 s flat, from 0.4.5_16) are byte-for-byte unchanged, and the same `resetActors` is used on the death-reset path, so the fix applies there too automatically.
- Tests: new `tools/fbstub/test_b2.py` (99 checks) — every map of every class × girone-start and post-death-respawn: ghost count unchanged, no two ghosts share a tile, every ghost inside the house; ghosts 1-4 keep their exact pre-existing slots on the 4 L maps; the 5th ghost's wait-gap formula re-checked across easy/medium/hard. `test_m1a.py` unchanged, all 112 checks green (one intermittent console-error flake reproduced identically on the unpatched 0.4.5_16 baseline too, ~1 run in 4-5 — pre-existing, unrelated to this fix, consistent with §6's note that real-time polling is flaky under CPU load). `node --check` + smoke test (menu renders, zero console errors, a run starts).
- Not tested: real phone — please retest girone 8/9 (and any other L girone) for stacked ghosts at the start.

## 0.4.5_16 — 2026-09-27 — fix: 5th ghost on large maps + dev girone readout
- **Owner phone test**: girone 8 (class L) showed at most 4 ghosts. **Investigation** (`devJump` called directly for every path — dev-jump number field, `#jg7`+clear, and a normal girone-by-girone run — for every L/M/S map and both characters): the class/ghost-count/stage logic itself was airtight on all three paths and every one of the 15 maps — `mapClassOf(G.mapi)`, `G.en.length` and the count of ghosts actually drawn (spied on `drawPlane`/`drawGym`/`drawGymArt`) always agreed with the class (S 3 / M 4 / L 5), and a 30-jump girone-9 sweep never disagreed with its own picked map either. **Cause**: `resetActors` rebuilds `G.en` — including every `wait` timer — from scratch on *every* respawn after a death, which is the pre-existing Pac-Man "ghosts return to the house" behaviour, unchanged by M1a. The 5th ghost's wait, extended naively from the 4-ghost formula (`(i*2.2+1.2)*dfc().wait`), grew to 10-15 s depending on difficulty — at Facile the gap after the 4th ghost (2.2×1.5=3.3 s) also slipped past this build's own ≤3 s bound. Girone 8 is fast (near-max ghost speed) and 5-wide, so a death is common well before the slowest ghost(s) ever left the house — repeated deaths keep resetting that clock, so the two longest-wait (stage-3) ghosts could go unseen for an entire test session even though they were always present in `G.en` and always drawn once released.
- **Fix**: the 5th ghost's wait is no longer `(4*2.2+1.2)*dfc().wait` (which grew with difficulty and could exceed the 3 s gap at Facile); it is now the 4th ghost's wait **plus a flat 2.5 s**, not re-scaled by difficulty — the gap after the 4th ghost is ≤3 s on every difficulty, by construction, and the formula for ghosts 1-4 (S/M classes included) is untouched.
- **Dev girone readout**: `devOn` only, `#jgro` — a small corner line over the maze canvas (`position:absolute`, `pointer-events:none`, never over the HUD or controls), e.g. «G8 · L · 5 · st 1,1,1,3,3» (girone · class · ghost count · stages in ghost order), updated by `updateHud()`. Absent entirely from the DOM for a player (element is only added to `buildGameDOM`'s markup when `devOn`).
- Tests: `tools/fbstub/test_m1a.py` extended (+70 checks, 112 total) — every one of the 15 maps × both characters (`G.en.length` = drawn count = the class count, every ghost leaves the house within ~17 s with the player made invulnerable so a death never contaminates the check), girone 8 via all three paths (dev-jump field, `#jg7`+clear, a real girone-by-girone run), a 30-jump girone-9 sweep (count always matches the picked map's own class), and the readout's presence (dev) / absence (player). Full regression (f1/f2a/f2b/p1b/u1/u2/u3/u4/s1/jg/m1b) green; `node --check` + smoke test.
- Not tested: real phone (the actual fix — please retest girone 8/9 on all three paths and check the corner readout).

## 0.4.5_15 — 2026-09-27 — M1b: girone bonus multipliers
- **`GIR_BONUS`** (§10.4, next to `pickMap`/`GIRONI`): `{cls:{S:1.0,M:1.2,L:1.4},st2:.10,st3:.25}`. At girone clear, `mult = cls[classe] × (1 + st2×n_stage2 + st3×n_stage3)`, read off the just-finished girone's own `G.en[].stage` (never a fresh `gironeSpec`/random draw — the same "one source of truth per girone" rule as M1a). Matches the brief's own table exactly (1, 1.1, 1.2, 1.44, 1.44, 1.68, 2.03, 2.1 for gironi 1-8) and its g9+ formula.
- **`G.girPts`**: this girone's own points only (pellets +10, ghost-eat chain bonus, the +200 clear bonus) — excludes carried score, the professor-win seeded score at girone 3, and any previous bonus (none of those ever touch `girPts`). Reset to 0 at every girone start (the clear→advance transition; a fresh run/Hardcore/professor-win/dev-jump G is simply a new object, so it starts at 0 with no extra code). Carried in the quicksave (plain object clone, no extra plumbing); an old quicksave without the field resumes with `girPts=0` (`G.girPts=G.girPts||0` migration).
- At girone clear: `bonus = Math.round(girPts × (mult−1))`, added once to `G.score` (so `finishRun`'s limiter/`DIFF.mult`/`.7` apply on top of it, unchanged — no edit to `finishRun` was needed). Shown as **«Bonus girone ×M +P»** on the existing clear-screen banner (a second, smaller line under "Ripulito!", mirroring the "ready" screen's own girone/theme subtitle — a toast wasn't needed, there was room) only when `bonus>0` (girone 1's mult is exactly 1.0, so no line there). `M` is `Math.round(mult*100)/100` printed as a plain JS number, which already drops trailing zeros (×1.1, ×1.44, ×2.03). Hardcore uses the same rule (no Hardcore-specific branch existed to touch).
- Tests: new `tools/fbstub/test_m1b.py` (31 checks: the mult table for gironi 1-8 and the g9+ formula for 9/10/12; a real girone clear — one pellet placed at the player's own cell, `update()` — adds pellet+clear+bonus exactly once, with the line shown/absent correctly at gironi 1/2/7; girPts resets at the next girone; a mid-girone quicksave keeps girPts, an old-shaped one resumes at 0; the girone-3 professor-seeded score stays outside girPts and unmultiplied; `finishRun`'s gain formula unchanged, isolated from unrelated achievement-reward side effects by pre-marking every achievement done for that one call). Full regression (f1/f2a/f2b/p1b/u1/u2/u3/u4/s1/m1a/jg) green; `node --check` + smoke test.
- Not tested: real phone (how the second banner line reads on a real screen).

## 0.4.5_14 — 2026-09-27 — dev tool: jump to any girone
- Owner-approved testing aid for E1-E6 (need gironi 2, 8, 9+). Next to the existing `#jg4`/`#jg7` buttons (kept as they are) in the «Salta al girone» accordion: a number field `#jgN` (1-20, default 1) + a button `#jgGo` «Vai al girone». Clamped in the click handler (`Math.min(20,Math.max(1,...))`). Calls `devJump(n)` with no explicit `mi`, so it goes through the exact same `pickMap(n)`/`resetActors` path as `#jg4`/`#jg7` and a real run — the girone's real class, ghost count and stages (M1a's `gironeSpec`/`pickMap`, already built to make one class draw per girone) — nothing new to wire. The map-picker dropdown + «Vai» is untouched (still forces girone 4 with the chosen map).
- Tests: new `tools/fbstub/test_jg.py` (15 checks: the field sits in the same `data-dev` accordion body as `#jg4`/`#jg7`; real-click jumps to 1/2/8/9/15 give the right class/ghost-count/stages; 0/999/-5 clamp to 1/20/1; `#jg4`/`#jg7`/the map picker still work). Full regression (f1/f2a/f2b/p1b/u1/u2/u3/u4/s1/m1a) green; `node --check` + smoke test.
- Not tested: real phone.

## 0.4.5_13 — 2026-09-27 — M1a: map classes, GIRONI schedule, 3/4/5 ghosts
- **Map classes by grid width** (§10.2): `MAP_CLASS={S:[0-4],M:[5,6,7,10,12,13],L:[8,9,11,14]}` (S = the 5 standard 15×17 mazes, M/L = the 10 extra hand-authored maps), `CLASS_GHOSTS={S:3,M:4,L:5}`, `mapClassOf(mi)` reverse lookup. **`GIRONI`** = the fixed girone 1-8 schedule from §10.2 (`{cls,ghosts:[stage,…]}` per girone, ghosts.length = the class count); `stagesForClass(cls,stage)` = the girone-9+ rule (every ghost ≥ stage 2, +1 at stage 3 every 2 gironi: `min(n,2+floor((stage-8)/2))`, verified against the brief's own g9:2/g10:3/g11:3/g12:4 example); `pickClassForGirone(stage)` (table for 1-8, random S20/M40/L40 from 9) and `gironeSpec(stage)={cls,ghosts}` (a single call — no double random draw between the class choice and the per-ghost stages) are the two functions everything else is built from.
- **`pickMap(stage)`** replaces the old `pickMap(prev)` (level-10-gated, uniform-random pool): picks a random map inside the girone's class, no immediate repeat within that class (`G.lastMi={S,M,L}`, remembered per run, carried by the quicksave, `!G.lastMi` on an old one migrates from the current `mapi`). One function, called from every place a girone starts: `startGame`'s fresh-run branch (new run / Hardcore / the professor-win girone-3 restart, all funnel through the same `opt.stage`), the girone-clear advance, and `devJump` (an explicit dev map override still skips it, same as before).
- **Ghost count 3/4/5**: `resetActors` derives the count from `mapClassOf(G.mapi)` (not from a second random draw), reusing `MET.ghosts`' 4 house starts with wrap-around for the 5th (same linear `wait` formula naturally gives it a longer wait than the 4th); 5th `chase` = the average of the difficulty's 4 values; new 5th `TINTS` colour. Every existing loop over `G.en` was already generic (`for...of`/`.map`, no hardcoded length or index) — collisions, scared/eaten, power-up, abilities, HUD, drawing all work unchanged at 3 or 5. Each ghost also gets a `.stage` (1/2/3, from `gironeSpec`) — stored only, per the brief: **no ability/behaviour/drawing effect yet** (that's E1+).
- **Level-10 map lock removed**: `mapsUnlocked()` deleted (was only used inside the old `pickMap`). Achievement `g4` keeps its trigger/sordi/XP; its description dropped "sblocca 10 nuove mappe" (now just "Raggiungi il livello 10 con un personaggio") and the map-unlock toast on unlocking it is gone. CLAUDE.md §2 rewritten to describe the class/schedule instead of "chosen at random per girone" / "unlocked by the level-10 achievement".
- Tests: new `tools/fbstub/test_m1a.py` (42 checks) — `gironeSpec`/`stagesForClass` against the exact table and formula for gironi 1-14, the g9+ split (~600 draws), real dev-jump girones 4/7 (M/L, real clicks) plus the map-picker forced onto an S map (all via `mapClassOf`/ghost count, not by asserting a specific map name), 200-pick no-repeat-within-class for S/M/L, a level-5/no-`g4` save still reaching M and L maps via the real `startGame(stage)` path, the g4 text, and an old-shaped quicksave (no `lastMi`, ghosts with no `.stage`) resuming and migrating cleanly. Full regression (f1/f2a/f2b/p1b/u1/u2/u3/u4/s1) green; `node --check` + smoke test.
- Not tested: real phone.

## 0.4.5_12 — 2026-09-27 — U4 feedback: Algidone's rank names (owner)
- **`RANKS_ALG` replaced with the owner's own 10 names** (0.4.5_10's proposal was not approved): 1 Mangiatore modesto · 10 Usurpatore di Snacks · 20 Snacks Manager · 30 Mangiatore Professionista · 40 Bevitore di Bevande · 50 Re degli Snacks · 60 Amico del Colesterolo · 70 Perfettamente Sferico · 80 Regina delle Bevande · 90 Abbuffatore Seriale — 10 entries, not 11: the last one covers levels 90–100. `RANKS` (Uomo roccia) unchanged, still 11 entries (1…100).
- `rankTable`/`rankOf` already worked with any table length (no change). **`careerModal`'s milestone list was hardcoded to the fixed levels `[1,10,…,100]`** (would have shown "undefined" at Liv.100 for Algidone, since `RANKS_ALG` has no `100` key any more) — now derives its rows from `Object.keys(rankTable(charKey()))` directly, with "current milestone" read off the next threshold in that same list instead of an assumed step of 10 / top of 100. Level-up popup (`celebrate`) already looked up each level directly and needed no change.
- `tools/fbstub/test_u4.py` updated: separate `LV_ROCCIA`/`LV_ALG` threshold lists (11 vs 10 entries), `rankOf` expectations for levels 99/100 (Algidone: both resolve to the level-90 rank; Uomo roccia: 99 → Maestro dei cieli, 100 → Re delle pietre), and a length/threshold-sharing check replacing the old "same length" one. 30/30 green; full regression (f1/f2a/f2b/f2c/p1b/u1/u2/u3/s1) also green.
- Not tested: real phone.

## 0.4.5_11 — 2026-09-27 — S1: game choice at «Nuovo gioco»
- **Uomo roccia**: «Nuovo gioco» and «Hardcore» open a small chooser «Che partita fai?» (Hardcore says so): «Mangiaroccia» starts the maze as before; «Ferma Algidone! · In arrivo» is shown disabled and can't be started (not even by arrow keys); «Indietro» closes it without starting anything. **Algidone** starts the maze directly. With a quicksave the «Nuova partita» overwrite confirm still comes first.
- Self-contained module (§10.0): table `RUN_GAMES` (`id`, `idx` of the Giochi card, `name`, `enabled`), `RUN_START` (id → start function) and `newRun(o)`; FR1 only has to set `enabled:true` for `ferma` and add `RUN_START.ferma`. The run remembers its game in `G.game` (saved in the quicksave; old saves and old runs count as `maze`; «Ancora!» restarts the same game).
- **`nextMinigame()`** now follows the run's game (`runGameOf(G.game)`, respecting the `S.ov["game_N"]` label overrides) instead of always returning «Mangiaroccia».
- Tests: new `tools/fbstub/test_s1.py` (18 checks). The other test files that start a run from the tile now go through the helper `tools/fbstub/gp.py` (`pick_maze`, a no-op when no chooser is up).
- Not tested: real phone.

## 0.4.5_10 — 2026-09-27 — U4
- **Algidone's ranks** (`RANKS_ALG`, same thresholds 1…100 as `RANKS`, which stays Uomo roccia's): 1 Pivello · 10 Tesserato · 20 Frequentatore · 30 Culturista · 40 Powerlifter · 50 Istruttore · 60 Personal trainer · 70 Campione di panca · 80 Leggenda della sala pesi · 90 Maestro del ferro · 100 Re della palestra (proposal, to approve; editable by long-press). `rankTable(ck)` / `rankOf(level,ck)` (was defined but never called) now drive the career modal milestone list and `celebrate(a,b,cb,ck)`, whose milestone message now names the new rank («Sei al livello 10: ora sei <b>Tesserato</b>…»).
- **Arrow-key navigation (web)**: self-contained `KNAV` module: arrows move a visible white ring (`.kf`) between the menu tiles, or between the buttons of an open popup (nearest in that direction); Enter clicks it. The ring appears only after an arrow key and is removed on any pointer/touch press, so touch users never see it. Existing shortcuts untouched (Esc/Enter on popups, single-button popups, maze/minigame arrows, text fields, bug popup guard).
- **Menu music** also on Obiettivi (`ach`), Percorso (`road`) and Personalizza (`cust`) (`musicWanted`); the maze and minigames stay silent.
- Tests: new `tools/fbstub/test_u4.py` (30 checks). Not tested: physical keyboards on iOS/Android, real audio output.

## 0.4.5_9 — 2026-09-27 — U3: professor achievement, tile 3, tile hints, gift tags
- **New achievement «Batti il professore»** (`m5`, Minigiochi, 300 sordi / 180 exp, event `prwin`): granted by `pbEnding` on a real professor win only (not `PR.test`, not SIM, not a loss or Fuga); also sets `S.p.pr.won`. Lists/counts consistent: 35 achievements, Minigiochi 5 entries / 5 places (`ACH_CATS`), no placeholder.
- **Tile 3 (GEKA hat)** unlocks only on `S.p.pr.won` (was: any real battle seen). Migration (old saves have no `won`): `pr.won=false`, and if the save had seen a real battle or claimed tile 3, `S.p.road.keep3=true` keeps it. No retroactive achievement: no old save can prove a win (only `visits`/`seen` were stored), so none is granted.
- **Locked tiles 3, 5, 10** get a golden inset border; tapping opens «Tessera bloccata» with the achievement that opens it («Batti il professore» / «Il banco trema» / «Fuori da Coccia!», `ROAD_HINT`) and «Vai all'obiettivo» → Obiettivi on the right category, entry highlighted and scrolled into view. Other locked tiles keep the old toast.
- **«sblocca regalo!» tag** on achievements linked to a roadmap tile with a ready gift (`giftTile`): «Batti il professore» (GEKA) and «Il banco trema» (BK); «Fuori da Coccia!» (tile 10, no gift defined yet) gets it automatically once tile 10 has a reward.
- Tests: new `tools/fbstub/test_u3.py` (27 checks). CLAUDE.md: 35 achievements, §10.9 mapping note.
- Not tested: real phone; a real professor battle end to end (the win path is tested through `pbEnding` with the UI stubbed).

## 0.4.5_8 — 2026-09-27 — U2: rocks 4–9 colours
- Owner decision: rocks 4–9 (no art of their own until now, drawn as the grey base rock) take the colour of their **battle type** (`PB_TCOL[types[1]||types[0]]`, the same source and formula as the battle screen's `pbRockTint`, now shared as `rockTintF`), applied to the base rock frames for the **pellets** (`rockFrames(k>=4)` = tinted `rock/r1/r2`), to the **side-view eating** frames (`eatVar` multiplies the grey pixels by the tint, the face is untouched), to the **up/down eating** icon (`drawFaceEatFX`) and to the **menu-scene** rock, bite and crumbs. New `rockKind(i)` (1–3 own art, 4–9 tinted, 0 base) is used only on those Uomo roccia paths; `artRock` and everything else (Negozio cards, battle, blackjack prop) unchanged. Rocks 0–3 and all snacks unchanged; Algidone never uses a rock tint. Snacks 4–9 stay the base burger (palette/art for them added to §8 art-owed).
- §6 rule 11: no frame/pose added or changed (e0/e1 and the rock frames are the same art, recoloured at draw time) — skin coverage unchanged, no `manca` gained.
- Tests: new `tools/fbstub/test_u2.py` (12 checks: per-pixel tint of pellet/eat frames for rocks 4–9, 0–3 unchanged, snacks unchanged, no cross-character).
- Not tested: how the six colours look on a real phone.

## 0.4.5_7 — 2026-09-27 — El Gamblador portrait from the table sprites
- Owner feedback: his picture still looked like the presentation sprite (`BJSPR.pres`). Available dealer frames in `BJSPR`: `idle` ×6 (108×113, cigarette, hands on the table), `dealP` ×7, `dealS` ×4, `shuffle` ×3, `collect` ×4, `check` ×3, `win` ×2, `lose` ×2, `expr` ×7 (94×~110 close-ups: neutral/smile/talk/raise/serious/annoyed/tired), `pres` (the poster), `chips` ×5, `back`, `shoe`, `discard`, `ashtray`. **Picked `idle[0]`** (the idle pose as at the table, with the cigarette, sunglasses on his head, bow tie), cropped to the upper 84 rows (face, bow tie, vest; `GAMB_CROP`) so it reads at card size.
- `gambImg()` now returns that crop (canvas, `null` until loaded) and `gambDraw(x)` paints it; used by the Giochi card, the unlock popup (`char:gam`) and the Negozio › Giocatore card. The old two-playing-cards branch of the Giochi card is removed. No new art.
- Tests: `test_u1` (27 checks) compares all three canvases to the reference crop and to `BJSPR.pres`.
- Not tested: real phone.

## 0.4.5_6 — 2026-09-27 — U1
- **«Mr. Stone»**: page `<title>`, error overlay, `<noscript>`, menu `<h1>`, splash `<h1>` and splash popup `<h3>` (the only player-visible uses of the old title). Repo, URL, file names, storage keys and identifiers unchanged; the texts stay editable by long-press as before.
- **Giochi**: existing but still locked games (G2 El Gamblador, G3 Rocciamon, G4 Ferma Algidone!) show «???» + **«non sbloccato»**; «In arrivo» stays only for things that don't exist yet (G5/G6 cards, «Altri giochi in arrivo», Personalizza items, «Altri personaggi»). Unlocked cards unchanged.
- **El Gamblador picture**: his Giochi card (when unlocked) now draws `gambImg()` (the dealer presentation sprite) instead of the two playing cards; the unlock popup for `char:gam` shows the same picture (`gambImg` repaints any open `gamb` canvas when it finishes loading). No new art.
- **Forced Ferma Algidone! encounter**: from girone **8** (was 10) when the player has never met it (`bjAfterClear`); random 15% chance from girone 5 unchanged.
- Tests: new `tools/fbstub/test_u1.py` (23 checks).
- Not tested: real phone.

## 0.4.5_5 — 2026-09-27 — maze respawn aura
- Owner feedback on P1b: no more blinking. After losing a life the character gets a soft glow in the colour of their own power-up (Uomo roccia: the gold of the Roccia luminosa glow; Algidone: yellow/red of the coppa, `RESPAWN_AURA`, no new art), for **5 s** (`RESPAWN_INVULN`, was 2). The aura is the timer: full until the last 1.5 s (`RESPAWN_FADE`), then it shrinks in opacity and blurs outward, gone exactly when the protection ends. Own maze constants; Ferma keeps its 2 s. Works for every skin/character, normal and Hardcore; quicksave/resume now keeps the remaining time (was reset to 0); Acciaio/Cinghiale immunity unchanged.
- `test_p1b` (21 checks): 5 s window, overlap doesn't kill then does, aura drawn during and not after, resume keeps the time.
- Not tested: how the aura reads on a real phone screen.

## 0.4.5_4 — 2026-09-26 — P1b
- **Maze respawn invulnerability**: after losing a life `G.invuln=RESPAWN_INVULN` (2 s, counts down in play, the player blinks; ghosts pass through). Acciaio/Cinghiale immunity, quicksave/resume and Hardcore unchanged.
- **`protectedCell(x,y)`** (standalone helper, reused by E5): outer ring, tunnel rows, ghost house rect + 1-cell margin (walls and door); `smashable()` now uses it, so Cinghiale can't break the house or tunnel rows.
- **«sad» screen deleted**: `renderSad`, `sadArm`, `sadTimer/sadN`, render/`mgback`/freeze cases, the `sad-countdown` screen id, its `capture.py`/`make_index.py`/`SCREENS.md` entries and PNG, and its `test_f6` checks.
- `test_f2b`: the «newer build» fixture is derived from `VERSION` (`NEWER_VER`, next minor). New `tools/fbstub/test_p1b.py` (17 checks).
- CLAUDE.md corrections (§2/§4): terrain only on extra/dev maps, «Non ora» = first-ever table, both abilities immune, 2 s respawn invulnerability, TOAST/DIAG/protectedCell in the code map; the «sad» backlog note removed. Level-10 map-unlock text untouched (M1a).
- Not tested: real phone.

## 0.4.5_3 — 2026-09-26 — toast module, cloud toggle without re-render, diagnostics log
- **F1**: the cloud test switch (Opzioni › Account) now only rewrites the Account section in place (`optRefreshAccount`): no full re-render, scroll and open accordion stay. The reload that follows a cloud apply / «Ripristina backup» also saves and restores the scroll position (`mgs_resume.y`).
- **F2 — one toast module (`TOAST`)**. Old mechanisms found: (1) `toast()` (42 calls, menu/Opzioni/Percorso/maze/dev screens; a `<div>` inside `#root`, absolute at the bottom, destroyed by any `render()` — the reason toasts flashed and vanished, and it sat over d-pad/buttons); (2) the achievement popup `#ach-pop` (`achPopup`/`pumpPop`, bottom, closable, dodges the d-pad via `popBottom()` — rich content with a close button, deliberately left as it is); (3) the crash overlay `#errbox` (red, bottom, tap to close, deliberately left); (4) canvas banners drawn in-game («Pronti?», «Ripulito!», BJ result banner, Ferma «+50» texts) and dialogue/panel popups (`openModal`, `faPanel`, BJ/Professor dialogue boxes) — not toasts; (5) `.banner` CSS class, unused.
  New `TOAST` (self-contained, §10.0): container `#toasts` outside `#root`, one at a time (queue, duplicates dropped), fade in/out, `pointer-events:none`, 2.5 s minimum, +45 ms per character, 5 s maximum. Position identical on phone and desktop: top-centre under the top bar; if that would cover a button/summary/card it moves onto the top bar's own band between its controls (`TOAST.place` scores each candidate against every interactive element). In gameplay it is compact and **held in the queue while the run is in play** (maze `G.state==="play"`, Ferma `FA.state==="play"` and not paused) and appears when the game is paused/ready/over — the less invasive of the two options; El Gamblador and Il Professore (dialogue-driven, nothing under the top bar) use only the compact form.
- **D0 — `DIAG`** (dev diagnostics, self-contained): ring buffer of 200 entries `{t,screen,kind,msg}` in `mgs_diag` (`mgs_diag_dev` on the dev site, ≤50 KB, oldest dropped, flushed on hide/reload). Records window errors, unhandled rejections, console.error/warn, auth state + `fbVerify`/`plVerify` results (kind/role only), cloud statuses/apply/upload/conflict/restore/write-verify failures, reloads/resumes, screen changes, bug-icon taps and whether the popup opened. `DIAG.clean()` covers emails and any 28+ character id/token. UI: Opzioni › Sviluppatore › «Diagnostica» (newest first, «Copia», «Svuota»). Dev bug reports carry the last 30 entries in `meta.diag`; player reports nothing.
- Tests: new `tools/fbstub/test_toast_diag.py` (43 checks); `test_f6` meta expectation now includes `diag`. f1/f2a/f2b/f2c/f3b/f5/f6 green.
- Not tested: real phone (safe-area inset, touch), real clipboard permissions on iOS.

## 0.4.5_2 — 2026-09-26 — cloud-save reload fix (phone feedback on 0.4.5_1)
- **A/C (older bug, also in stable 0.4.5, not caused by P1a)**: applying a cloud copy (`cloudApplyNow`) or «Ripristina backup» (`cloudRestore`) did a bare `location.reload()`, and every load starts at the splash question. New `cloudReload(msg)` stores the screen (Opzioni + open accordion) in `sessionStorage` `mgs_resume`; `cloudResumeBoot()` (boot, replaces the unconditional `go("splash")`) goes straight back with a toast («Salvataggio del cloud caricato» / «Backup ripristinato»). The automatic apply at boot (splash) still reloads as before.
- **D (hardening; root cause on the phone not reproduced)**: `cloudWrite`/`cloudBackup` swallowed a full-storage error into memory (lost on reload) and then reloaded, so a restore could silently do nothing or a save be replaced without a backup. Both now verify the write really landed; otherwise nothing is overwritten, no reload, toast «Spazio insufficiente…» and status «Spazio insufficiente su questo dispositivo». Same guard on the conflict popup's «Usa questo» (device copy).
- **B (bug icon unresponsive on the splash)**: not reproducible headless (tap opens the popup, «Indietro» restores the splash question, dev and player sessions). Working theory, unproven: the background `fbVerify` dropped the dev session after the reload (icon stays drawn but `canReport()` is false; the next load has no icon).
- Tests: new `tools/fbstub/test_f2c.py` (22 checks: A–D, dev + player session, touch taps, full-storage case); `test_f2b` restore test expects Opzioni. f1/f2a/f2b/f2c/f3b/f5/f6 green (f6 had one flaky failure in one run, green on rerun).

## 0.4.5_1 — 2026-09-26 — P1a (0.5 plan)
- **Login Esc bug**: after a failed dev/player login attempt the focus returns to the password field (the disabled button had dropped it to `<body>`), so Esc closes the popup again (`loginModal`, `plLoginGo`). `test_f1` «Esc closes the login» is green again (34/34).
- **Cloud-conflict cards at 390 px**: below 480 px the two cards stack in one column and the title/date stay on one line (CSS only). New check in `test_f2b`.
- **`test_f4b1` waits**: the 12 fixed waits after «Carica costume» are replaced by `import_go()` = click + wait for `skinImpBusy===false` (59/59). `test_f2b`: the «newer build» fixture uses ver `0.9` instead of a hardcoded `0.4.5_1` (which is now the current build).
- Docs: CLAUDE.md §10 replaced by the 0.5 plan (separate commit).
- Not tested: real phone, real Android back/keyboard.

## infra — 2026-09-26

- `.github/workflows/tag-release.yml` — tags a release and publishes its GitHub Release on push to `main`, replacing the manual tagging step from the 0.4.5 release (Claude Code cloud sessions get an HTTP 403 pushing tags with their own git credentials; a workflow's `contents: write` token can). No-op unless the root `VERSION` file is a bare release version (digits and dots only); finds the newest first-parent commit on `main` whose message is exactly `Release <version>`, tags it `v<version>` (skipped if the tag already exists) and creates a GitHub Release from that version's `CHANGELOG.md` section (skipped if the release already exists) — idempotent, safe to rerun or to fire manually.
- No game-code change; `index.html`/`VERSION` untouched.
- Tested locally (Actions can't run here): the workflow's shell logic run verbatim (extracted from the parsed YAML) against a scratch clone with a local bare "origin" and a stub `gh` — resolves the target to `a2f33d4` ("Release 0.4.5"), a rerun changes nothing (tag and release both skipped), the CHANGELOG extraction matches the 0.4.5 section exactly, a `VERSION` of `0.4.5_1` exits early with no git/gh calls, and a `VERSION` naming a release that was never committed fails with a clear message and touches nothing. Deleted this session's own leftover local `v0.4.5` tag (from the previous session's failed push) before testing; nothing was pushed to the real `origin` by any of this.
- Not tested: the real Action run on GitHub.
