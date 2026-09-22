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
