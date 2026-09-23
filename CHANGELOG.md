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
