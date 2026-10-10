# CLAUDE.md — Torneo Appalokniax (branch `appalokniax`)

This branch is a **separate project** that lives in the Mangiasassi repo: a small standalone HTML demo announcing
the Appalokniax tournament. It is an orphan branch — it shares no history or files with `main`/`dev`, and the
Mangiasassi rules in `main`'s CLAUDE.md (dev branch workflow, VERSION bumps, submissions, CHANGELOG) do **not**
apply here. Never merge this branch into `main` or `dev`, and never merge them into it.

Owner: Ciprognola. All player-facing text is **Italian**.

## The event (context)
Participants bring their own game made with AI; everyone plays every game; a jury of 3 picks the winner, who gets
a gambling budget to use the same night. The event is in November; judges and games are announced later.

## Build
- Edit `src/demo.html` (CSS + markup + script; `/*SPRITES*/null` and `"__INTRO__"` are placeholders).
- Run `python3 build.py` → writes `index.html` (full page) and `dist/artifact.html` (no html/head/body wrapper,
  for a claude.ai artifact preview; `dist/` is gitignored).
- Commit `src/`, `index.html` and any new assets together. Never hand-edit `index.html` and never print the
  base64 inside it.
- Check: `node --check` on the extracted script, then a headless Playwright walkthrough (click `#pstart`, tap the
  stage to advance, pick menu items with `[data-pi="0"]` = Sì, `[data-pi="1"]` = No). Real-device audio and touch
  are not verified headless — say so.

## Web page
Live at `https://ciprognola.github.io/mangiasassi/appalokniax/`. The Pages deploy lives on `main` (and `dev`):
`jekyll-gh-pages.yml` copies this branch's `index.html` to `/appalokniax/`. On this branch,
`.github/workflows/redeploy-pages.yml` re-runs that deploy whenever a push changes `index.html`, so pushing a
rebuilt `index.html` is all it takes to update the page (allow 1–2 minutes).

## Assets (taken from `main`'s index.html, unchanged)
`assets/prof_idle0-6.png` = `PRSPR.idle` (full-body standing loop), `assets/prof_blink0-2.png` = `PRSPR.blink`
(dialogue-box portrait: 0 rest, 1 blink, 2 mouth open), `assets/prof_intro.mp3` = `PR_INTRO_B64`. Other professor
frames (`angry`, `point`, `shoo`, `walk`) and the other tracks stay in `main` and can be extracted the same way
if a later brief needs them (`const PRSPR={…}` is JSON: key → array of base64 PNGs).

## Script map (`src/demo.html`)
- Text: `T` (fixed lines), `NO_LINES` + `nextNo()` (shuffled bag, no repeat until all 5 shown, never twice in a row).
- Audio: `beep`, `blip` (190 Hz square, every other letter), `ping`; music `musPlay/musVol/musStop` (gapless loop
  with silence trim, like `loopTrack`); crowd `crowdStart/crowdStop` (synthesized murmur, choir, claps, whistles).
- Dialogue API (same semantics as Mangiasassi): `say`, `choice`, `hideBox`, `black`, `profAlpha`, `arenaAlpha`.
- Scene: `drawScene` (arena, then professor; `S.side` "c"/"r" slides him), `drawArena` (200×120 low-res canvas,
  width grows on wide screens via `arenaFit`), `drawPortrait`.
- Sequence: `play()` — the whole demo flow in order.

## Open interpretations (confirm with the owner before changing)
- The professor fades in after «Ottimo! Gran bella scelta!» (as in «Roccia no», where he appears after «Sì»);
  before that the screen is black with only the dialogue box.
- The dialogue box hides while the professor slides and the arena fades in or out.
- A «Tocca per iniziare» screen comes first (browsers only play sound after a tap) and a «Ricomincia» screen last.
- Small text fixes vs the brief: accents (più, terrà, perché), «i loro giochi», capital «Mmmh» and «Gloria».
