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
