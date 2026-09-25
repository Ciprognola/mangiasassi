# M9a — Ferma Algidone! balance + controls report (build 0.3_36, no code changed)

Everything below was read from `index.html` (0.3_36) or measured headless (Playwright/Chromium, frozen rAF + `faStep(1/60)`).
**What "measured" means here:** simulated time, a parked invulnerable player, no real human. Nothing about *feel* on a phone can be measured headless — those rows say "needs your feel".
Proposals are tagged **safe** (a number only, no change of feel/rules) or **design** (changes feel or rules). "keep" = no change proposed.

## 1. Tunables

### 1.1 Encounters and lives

| Name | Where | Current | Measured / derived | Proposed | Reason |
|---|---|---|---|---|---|
| Encounter rate | `bjAfterClear`, `Math.random()<.15` (only when El Gamblador does not fire) | 15 % per gap from girone 5 | Effective rate = 15 % × (1 − 15 % El Gamblador) = **12.75 %** per gap (El Gamblador rolls first on the same gaps). Expected wait between encounters ≈ 7.8 gironi | keep | Owner confirmed 15 %; the El Gamblador interplay is the only surprise. Re-check after a real playtest |
| Forced first encounter | `bjAfterClear`, `enc===0 && st>=10` | at the gap of girone 10 | P(no random Ferma at gaps 6-9) ≈ 52 %, so about half of the players get their first one forced. Mean first-encounter girone ≈ **8.7** | keep | Matches the owner's "forced by girone 10" |
| Encounter floors | `N=min(enc,3)` | 1, 2, then 3 | 3-floor encounters start with the 3rd encounter: at 12.75 %/gap that is roughly girone 24+ | keep | Owner decision |
| Lives | `startFerma` `lives:3`, `faLoadFloor` carry | 3 per encounter; lives carry across floors | with 3 lives + a 10 s bite per death the 90 s stock is the real limit for weak players | keep | — |
| Death pause / invulnerability | `FA_DYING=.8`, `FA_INV=2`, grace before throws 2.5 s | 0.8 s / 2 s / 2.5 s | accepted on the phone (0.3_27) | keep | — |

### 1.2 Stock (the timer)

| Name | Where | Current | Measured | Proposed | Reason |
|---|---|---|---|---|---|
| Stock per floor | `FA_LEVELS[i].stock` | 90 s, linear drain 1 s/s | Ideal route with no items: **12.9 s / 13.2 s / 11.3 s** (floor 1 / 2 / 3; walk 120 px/s, climb 105 px/s, 8 bolts in the best order). 90 s = ~7× the perfect route | keep (**needs your feel**) | Nothing headless can tell how long dodging really takes. If the phone test says "too easy": 75 s = **design**; "too hard": keep |
| Death bite | `FA_DEATH_STOCK` | −10 s per death | 11 % of the stock; 3 deaths = −30 s | keep | Already accepted (0.3_27) |
| Low-stock threshold | `FA.stock<lv.stock*.25` (beep + angry Algidone) | 25 % = 22.5 s, one beep per 2 s | — | keep | — |
| Stock bonus | `FA.cnt` / `faWinPanel`: `floor(stock)*10` | ×10 per second left | up to **900** per floor; jumps give ~10-30 each (≈100-200 per floor). **~80 % of an encounter score is the time bonus** | keep | It rewards speed, which is the DK feel. Raising jump points (design) would move value to skilful dodging; not needed for balance |

### 1.3 Difficulty (Facile / Media / Difficile)

**Finding: Ferma Algidone! does not read the difficulty at all** (M0 Q8 planned it; it was never built). The only places difficulty touches an encounter are downstream:

| Where | Facile | Media | Difficile |
|---|---|---|---|
| Maze `DIFF.mult` (payout of the run score, incl. the encounter score) | 0.8 | 0.9 | 1.05 |
| Maze `DIFF.spd` / `wait` (maze enemies only, not Ferma) | 0.82 / 1.5 | 0.91 / 1.25 | 1 / 1 |
| Achievement reward multiplier `AMULT` (m2/m3/m4 too) | 0.75 | 1 | 1.5 |
| Ferma throw rate / item speed / stock drain | 1 | 1 | 1 |

| Proposal | Type | Detail |
|---|---|---|
| Scale Ferma by the difficulty chosen in Options | **design** | Treat today's values as **Media** (the version you phone-tested). Facile / Difficile: item speed ×0.88 / ×1.12, throw pauses ×1.25 / ×0.85, stock drain ×0.85 / ×1.15. Payout already scales through `DIFF.mult`, so a harder setting already pays more. Alternative: keep Ferma difficulty-free (simplest) — then Facile/Difficile only change the payout |

### 1.4 Throwing (per floor)

Measured: 300 s simulated per floor, player parked and invulnerable (worst case for item count).

| Floor | Weights sausage / porchetta / meat | Pause between throws | Measured throws per min | Max items alive (cap 14) | Note |
|---|---|---|---|---|---|
| 1 Coccia | 3 / 1 / 0 | 1.6-3.0 s | sausage 9.6, porchetta 3.6 (= **13.2/min**) | 9 | — |
| 2 Macelleria | 3 / 1 / 2 | 1.4-2.6 s | 8.4 / 3.8 / 4.2 (= **16.4/min**) | 12 | — |
| 3 Fabbrica | 3 / 1 / 2 (+ grill flames) | 1.4-2.6 s | 7.4 / 1.4 / 6.2 (= **15/min**) + **7.8 flames/min** | 10 items + max 3 flames | — |

Common: Algidone eats instead of throwing 22 % of cycles (`FA_EAT_P`, 1.65 s) when not angry. **Proposal: keep** all weights and pauses. The floor-to-floor step (13 → 16 → 15/min plus new hazards) is smooth; the hardest floor is 3 because of flames + holes, not throw rate.

### 1.5 Items and hazards

| Name | Where | Current | Measured / derived | Proposed | Reason |
|---|---|---|---|---|---|
| Sausage speed | `FA_ITEM.sausage.speed` | 70 px/s | 320 px girder = 4.6 s; standing-jump window 0.229 s (0.3_29) | keep | Accepted on the phone |
| Porchetta speed | `FA_ITEM.porchetta.speed` | 34 px/s | 9.4 s per girder; clearable only with a running jump | keep | Accepted |
| Meat speed / hop | `meat.speed`, `FA_MEAT_HOP` | 55 px/s; hop 200 → apex 34 px, 2 bounces (floor 3) | 5.8 s per girder; clearance under the girder above ≈ 5 px | keep | The hop cap was set to stay under the girder above |
| Ladder drop chance | `items.ladderP` | 0.06 per step check | — | keep | — |
| Item cap | `FA_MAX_ITEMS` | 14 | max seen 12 | keep | — |
| Belt speed | `conveyor.v` | 45 px/s | player 120 → 75 px/s against the belt, 165 with it; items always ≥ 12 px/s toward the exit | keep | Accepted (0.3_30) |
| Belt reverse / warning | `conveyor.rev`, `faBeltStep` | row 2 flips every 5 s, chevron blink + sound 0.7 s before | 0.7 s warning = about 84 px of walking | keep | If reversals feel unfair: warning 1.0 s = **safe** |
| Bolts | `FA_BOLT_SCORE`, `FA_BOLT_DELAY`, `FA_GAP` | +50 each (8 = 400), hole opens after 0.5 s, hole 26 px wide | — | keep | — |
| Flames | `faGrillHit`, `FA_ITEM.flame`, `flameClimb`, `FA_FLAME_CLIMB` | max 3, speed 60 px/s, life 6 s, climb chance 35 % per pass, climb speed 42 px/s, patrol x ≥ 150 | 39 flames spawned in 300 s, max 3 alive (cap works) | keep | — |
| Fall threshold | `FA_PHYS.fall` | 115 px | biggest single-floor drop 107 px; 2 floors fatal | keep | Set in 0.3_23 |
| Jump scores | `FA_SCORE` | sausage 10, meat 10, flame 20, porchetta 30 | — | keep | See stock bonus above |

### 1.6 Rewards vs the maze

| Name | Where | Current | Measured / derived | Proposed | Reason |
|---|---|---|---|---|---|
| Encounter score → run score | `faEncPay` | added once at the last win panel; paid at run end by `finishRun` (`floor(score×(1−limiter)×mult×.7)`) | Typical encounter: N=1 **~500-900**, N=2 **~1,000-1,700**, N=3 **~1,500-2,600** (max measured with an instant win: 880 / 1,770 / 2,660) | keep | — |
| Maze girone score | pellets + clear + ghosts | 10 per pellet (128-141 pellets per map, measured on all 15 maps) + 200 clear + 200-1,600 per ghost | **~1,300-1,400 from pellets + 200 = 1,500-1,600 without ghosts; ~1,500-2,500 with** | — | reference |
| Time per unit | — | — | Maze: perfect pellet tour (no ghosts) **32-76 s** by map (nearest-neighbour route, 5.08 tiles/s; a bot run was attempted but stalled, so this is a lower bound, **not measured play**); a human with ghosts is realistically 90-150 s (estimate) → **~800-1,300 pts/min**. Encounter N=1: ~45-60 s incl. intro and climb for ~700 → **~700-900 pts/min**; N=3: ~2,000 in ~3 min → **~650/min** and it pays **0 on a loss** | keep, revisit after the phone test | Roughly parity with the maze, slightly under for N=3. If the owner wants encounters to feel like a treat: N=3 ×1.25 = **design** |
| Payout per 1,000 score (Media, lvl 1 / 50 / 100) | `finishRun` | — | 126 / 220 / 315 sordi; exp 540 | reference | The limiter shrinks with level, so an encounter is worth more sordi late in a career |

### 1.7 Achievement rewards (sordi / exp) vs the existing 31

Existing range is 60-2,000 sordi; median about 300. Neighbours: "Cacciatore di fantasmi" 150, "Il banco trema" (10 blackjack wins, the other Minigiochi one) 200, "Cinque gironi di fila" 400, "Sterminatore" 1,200.

| Achievement | Current | Comparable to | Proposed | Reason |
|---|---|---|---|---|
| Fuori da Coccia! (clear floor 1) | 150 / 90 | Cacciatore di fantasmi 150 | keep | Reachable at the first encounter |
| Algidone è a terra (all 3 floors) | 400 / 240 | Cinque gironi di fila 400 | keep (or 600 = **safe**) | Needs the 3rd encounter (girone ~24+) and a full clear; 400 is on the low side for that effort, but the difficulty multiplier (×0.75-1.5) already spreads it |
| Senza un graffio (a floor without losing a life) | 250 / 150 | Rame a colazione 150-Completista 200 | keep | — |

## 2. Controls, portrait (0.3_36)

Measured with `getBoundingClientRect` on real touch contexts (`has_touch`, DPR 2). Screenshots: `refs/ferma_algidone/review/m9_<w>x<h>_play.png` (during play) and `m9_<w>x<h>_panel.png` (floor-win panel).

| Viewport | HUD | Play canvas (scale of the 360 logical px) | D-pad / SALTA area | D-pad buttons | SALTA | Overlap | Canvas gap to pad |
|---|---|---|---|---|---|---|---|
| 360×640 | 54 px | 249×422 (×0.69) | 164 px tall, bottom | 66×66, gap 6 | 104 round, x 240-344 | none | 0 |
| 360×800 | 54 px | 343×582 (×0.95) | 164 px tall | 66×66 | 104 | none | 0 |
| 390×844 | 54 px | 369×626 (×1.03) | 164 px tall | 66×66 | 104 | none | 0 |

- D-pad x 14-224 and SALTA x 240-344 (360 wide): a 16 px gap between them and 16 px right margin. No overlap with the HUD or the canvas at any of the three sizes.
- **Only real finding on the play screen:** at 360×640 the pad and HUD take 218 of 640 px and the level shrinks to ×0.69 (the climber's head ≈ 25 px, the sausage sprite ≈ 27 px wide). It is drawn correctly, but small. Nothing overlaps, so **no change proposed**; if it feels small on a 640 px phone: pad buttons 66 → 58 px = **safe** (gains ~16 px of height).
- **Under 44 px (real findings):**

| Element | Size now | Proposal | Type |
|---|---|---|---|
| Pause button `#fap` (HUD) | 38×38 | 44×44 (HUD is 54 px tall, it fits) | **safe** |
| Panel buttons Continua / Avanti / Riprova / Esci / Riprendi (`#fapanel .btn`) | 316-336 × **38** | min-height 44 | **safe** |
| Invite modal "Non ora" / "Fermalo!" | 96×38 / 106×38 | min-height 44 | **safe** |
| Giochi "Gioca" (`.btn.sm`) | 63×30 | min-height 44 for the Ferma card only | **safe** |

  `.btn` is 38 px tall everywhere in the game (padding 10 px + font); a global `min-height:44px` would also touch other screens, so I would scope it to the Ferma panel, the Ferma invite and the Ferma card unless you want it global.
- Pad buttons (66×66) and SALTA (104) are well above 44 px; nothing else to fix.

## 3. Picks needed (M9b)

Nothing is built. Suggested default if you just say "go": **all safe items** (pause 44 px, panel/invite/Gioca min-height 44) + **keep** every balance row. Design items to pick or drop:

1. Difficulty scaling for Ferma (1.3): yes/no, and the ×0.88/×1.12 · ×1.25/×0.85 · ×0.85/×1.15 numbers.
2. Stock 90 s (1.2): keep, or 75 s.
3. N=3 payout ×1.25 (1.6): yes/no.
4. "Algidone è a terra" 400 → 600 (1.7): yes/no (safe).
5. Pad 66 → 58 px on short phones (2): yes/no (safe).
6. Belt warning 0.7 → 1.0 s (1.5): yes/no (safe).
