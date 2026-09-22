# CLAUDE.md — Mangiasassi

Permanent project context for Claude Code. Read it fully at the start of every session.

Owner: **Ciprognola** ("El Cipro") — product owner and master developer.
Repo: `https://github.com/Ciprognola/mangiasassi` · Live: `https://ciprognola.github.io/mangiasassi/`
Licence: MIT. Game language: **Italian** (all UI text, dialogue and new strings stay in Italian).

---

## 0. DIVISION OF LABOUR — read this first

| Where | What happens there |
|---|---|
| **Claude (web/app, the "Mangiapietra" project)** | All planning, design, investigation, roadmaps, chunk breakdowns, balance decisions, asset preparation decisions, review of developer submissions |
| **Claude Code (VS Code, this repo)** | **Execution only** — implement an already-approved chunk, commit, push |

So in Claude Code:
- Expect a task that is already scoped. Do not redesign it, do not expand it, do not add "while I was in there" extras.
- If the task is ambiguous, underspecified, or you think the plan is wrong → **stop and say so**. Don't improvise a different plan; the owner takes it back to Claude for replanning.
- One approved chunk = one build = one commit. Don't batch several chunks unless told to.
- If you discover something that changes the plan (a bug, a blocker, a bad assumption), report it and wait.

---

## 1. FIRST COMMAND OF EVERY SESSION — sync git

Three commits were made **directly on GitHub's web UI, starting at `a5fc3ee`**. They are not in the local
clone, which is why VS Code's Git Graph doesn't show them.

```bash
git status                              # must be clean
git fetch origin
git log --oneline main..origin/main     # should show a5fc3ee + the 2 after it
git pull --ff-only origin main
grep -n 'const VERSION' index.html      # confirm which build you're actually editing
```

Never force-push, never rebase `main`, never rewrite those web commits. If `--ff-only` fails, stop and ask.

---

## 2. What the game is

An Italian **Pac-Man-style 2D game**, built as **one self-contained HTML file** (~3.7 MB): HTML + CSS + JS +
every sprite and audio track embedded as base64. No framework, no npm, no build step. An Android WebView
wrapper exists in parallel and is kept updated internally.

**The original source template no longer exists** — the built HTML file *is* the source. Every change is a
patch applied to the current build.

### Two characters, strictly separated asset libraries
Never let assets cross between characters. This has been a repeated correction.

| | Uomo roccia (`"roccia"`) | Algidone (`"algidone"`) |
|---|---|---|
| Eats | Rocce | Snacks |
| Chased by | Aeroplani | Attrezzi da palestra |
| Power-up | Roccia luminosa | Drink / coppa McDonald's |
| Secret ability | **Acciaio** — immunity + teleport, animated steel look | **Cinghiale** — smashes walls, stress bar, stun |
| Prefix in overrides | *(none)* | `alg_` |

Abilities last 8 s with a 25 s cooldown (balancing flagged as a future task). The ability button pulses
yellow when ready. Ability exit buttons: "basta ti prego" (roccia) / "basta basta" (Algidone).

### Core mechanics
- 100-level progression per character, separate careers, XP, unlockable assets, ranks (`RANKS`: Recluta →
  Re delle pietre), hidden **limiter** on earnings (`limiter(l)`), `expNeed(l)` with a harder curve from lv 60.
- Three difficulties (Facile / Media / Difficile) with hidden multipliers — **harder rewards more**.
- Power-up reverses enemy behaviour for 15 s.
- **Gironi** (rounds): themed maze maps (steel, water, fire, ice, forest) chosen at random per girone.
  After girone 5: Nuovo gioco / Hardcore split.
- **Terrain**: water and lava drawn as sinuous generated *streams along corridors* (not filled areas).
  Lava = 60 % speed, kills after 3 s of contact. Water = 75 % speed, extinguishes burning 4× faster, with
  steam hiss + bubbles when entering while burning. A map-hardening pass stops lava blocking pellets.
- **10 extra hand-authored maps** unlocked by the level-10 achievement; big maps cap pellets at 130 spread
  evenly, and use a following camera.
- **30 achievements** across 4 categories; 50 cycling "Partita finita" quotes per character, some
  achievement-triggered.
- Desktop scaling supported up to 3440×1440; Enter/Esc shortcuts on popups.

### Mini-games (all implemented — do not rebuild)
1. **Mangiaroccia** — the core maze game. `screen="game"`.
2. **El Gamblador** — blackjack after girone 5. `screen="bj"`, all `bj*` functions. Sprite-animated dealer
   whose cigarette smoke tracks per-frame tip positions; streaming wood table borders, props on the rails,
   centred cards, 2×2 menu grid, raise/stake logic with a chip stack and ±100 buttons, dealer lines.
   "Puntata" and fiches stay on the **left** (shifted slightly right). "Non ora" hidden only on the first
   appearance per run.
3. **"Roccia no" / Il Professore** — Pokémon-Emerald-style mini-game reached by answering "Roccia no" on the
   splash question. `screen="pr"`. Scenes/dialogue = `pr*`, battle engine = `pb*`. See §3.

### Recurring Italian phrases
"Ma che sei gojo?", "Sì, deo caro", "Noneee", "Roccia sì o roccia no?". Player-visible text must stay
in-universe — never use developer words like "asset" or "fantasma" in player-facing strings.

---

## 3. The professor mini-game ("Roccia no") — built in 9 chunks, all complete

- **Entry**: splash → "Roccia no" → `prIntro()`. **"No" branch**: angry line, walk frames on a club corridor,
  white flash, player arcs into a dirty pond with synthesized splash/ripples/drops, fade to black.
  **"Sì" branch**: professor idle fade-in + music, three intro lines, pokéball throw arc, pixel-art Duskull
  emerges, the player's asset interjects using its own portrait and blip pitch → battle.
- **Professor sprites** `PRSPR`: `idle, blink, angry, point, shoo, walk` (extracted from a reference JPG with
  Python/PIL: background removal + convex-hull fill for face gaps).
- **Dialogue box** reuses the El Gamblador typewriter pattern: "tu tu tu" blips while typing, "ping" on advance.
- **Battle data**: 70 profiles — 25 aircraft + 25 gym tools as professor ghosts, 10 rocks + 10 snacks as
  player assets. Gen-3 stat formulas, IVs, EVs, neutral natures, a type chart, Italian move names.
  Asset *quality* shifts stat totals multiplicatively; it does **not** change level.
  **The player's asset always matches the ghost's level exactly.**
  Bulk weighting (PS ×2.6, defences ×1.5) prevents two-hit KOs.
- **Engine** (`pbBattle` and friends): priority, speed, accuracy, crits, STAB, all status conditions, stat
  stages, multi-hit, recoil, drain, Fuga, Italian AI. Headless simulator `pbSim` is used for balancing.
- **Battle screen**: Emerald-style field, sky and platforms, HP boxes with animated bars,
  LOTTA/ZAINO/SQUADRA/FUGA menu, move-detail panel, type-coloured attack animations and particles, event
  narration, transition with sweeping bars and rising beeps, keyboard + mouse navigation.
- **Endings**: win → professor shock/insult lines, sordi awarded via the existing reward formula, then a
  yes/no prompt to start a new run at **girone 3**. Lose → the pond throw-out animation is reused.
  Dev-test battles skip all save-data changes.
- **Balance history**: snacks had far lower physical defence than rocks while most gym equipment uses
  physical moves → every snack got **DEF +25, SpD +12** (offence and HP untouched). Simulated win rate moved
  56 % → 58 %, matching Uomo roccia's 59 %. A full audio-and-balance pass is planned as its own version.
- **Known past traps**: a name clash between two `pbFx` functions caused repeated chunk-7 failures (one was
  renamed `pbAddFx`). Effect durations were in seconds where milliseconds were expected, leaving a white dot
  on sprites — fixed by dividing by 1000 at insertion. Watch for both patterns.

---

## 4. Code map (single file, top → bottom)

`grep -n` to locate; line numbers drift constantly.

- **Sprites**: `const SPR={…}` (roccia `f0`–`f3` side profile, `e0`,`e1` eat frames, `rock`, `r1`, `r2`),
  `const SPR2={…}; Object.assign(SPR,SPR2)` (Algidone `al_st` 72×100, `al_w0..7` walk 75×100, `al_r0..7` run),
  `const PRSPR={…}` (professor). Loaded to `IMG[key]` by `loadImgs()`.
  Procedural art: `genBase, outline, scaleUp, rockFrames, planeCv, gymCv, burgerCv, cupCv, artGrid, snackFrames`.
  **Never print or open these base64 lines** — hundreds of KB each.
- **Data**: `PLANES, ROCKS, GYM, SNACKS, CHARS, RANKS, DIFF`, unlock/price formulas, `limiter`, `expNeed`.
- **State**: `store` (localStorage wrapper, key **`mgs_v1`**), `DEF`, live `S`, `persist()`, `DEF_TILES`,
  `CHDEF()` = `{ownP,ownR,selP,selR,lvl,exp,gir}` per character.
  Roles `role` (`null|'dev1'|'master'`), `devOn`, `devUI()`; sim mode `simOn/simOff/SIM()` (lv 100, 999999 sordi,
  preserves real save). Globals: `screen` (`menu|game|bj|pr|over`), `G` (run), `P` (player actor).
- **Audio**: `beep, noiseBurst, initMusic, syncMusic, playSnd, loadSounds`, `SND` buckets, and a Web Audio
  buffer loop player (`makeLoopPlayer`) used because HTML `<audio>` loops leave a gap in MP3.
- **Hero drawing**: `drawFace(ctx,cx,cy,w,frame,flip)`, `drawEat`, `drawAlg(ctx,X,Y,c,o)`, `drawHero(…)`.
  Render object built in `draw()`: `o={moving,power,eat,flip:P.lastH<0,anim,dir:P.face??1}`.
  Directions: `P.face` 0=up 1=right 2=down 3=left; `DX=[0,1,0,-1]`, `DY=[-1,0,1,0]`; `P.lastH` = last horizontal.
- **Menu/UI**: `shell, go, renderMenu, bindMenu, tileAction, careerModal, cardHTML, paintCanvases, renderWish,
  renderOpt, loginModal, openModal/closeModal/confirmBox, toast`.
- **Core loop**: `startGame, buildGameDOM, update, loop, draw, step, chooseP/chooseE, activatePower, smash,
  steelOn/Off, boarOn/Off, updateHud, pauseMenu, quicksave, finishRun, nextMinigame`.
- **Blackjack**: `bj*`, entry `startGamblador`.
- **Professor**: `prIntro → prIntroYes → prBattleStart`; scenes `prSceneProf, prSceneKick, prThrowOut, prPond,
  prSceneBattle`; dev `prTest, prTestKick, prTestBattle, prDevPanel`.
- **Battle**: `PB_LIB/pbLib` (moves), `pbMon, pbBattle, pbDamage, pbTurn, pbAI, pbAct`, anim `pbAnimMove, pbFxDraw`,
  UI `pbPanel, pbBox, pbCommand, pbFight, pbEnding`, sim `pbSim`. Each fighter currently has 4 fixed moves.
- **Achievements**: `ach, unlockAch, renderAch, bindAch`.
- **Export**: `exportDialog, exportBuild, expZip, expCrc32, expTextChanges, expAudioItems, exportTargetsMd`.

### Dev mode
Tap **"Build locale" five times** in Options to reveal the login. Roles: `dev1` (developer) and `master`.
Developer options must be **completely invisible** when the dev toggle is off. Dev jump buttons
("Salta al girone 4/6") and `PR.test` battles start test runs that **save no progress** and never set real
unlock flags (`seen`, achievements).

---

## 5. Repo layout & infrastructure

```
index.html                     the game (the source of truth) — always the latest build
VERSION
builds/                        delivered versioned builds
<historical log>               changelog of the project — CURRENTLY OUT OF DATE, see below
submissions/                   developer submission packages + README
android/                       WebView wrapper
scripts/validate_submission.py structure + size validator
.github/workflows/             pages deploy + validate-submission
DEVELOPERS.md                  browser-only guide, no Git knowledge required
CODEOWNERS                     → Ciprognola
LICENSE                        MIT
CLAUDE.md                      this file
```

GitHub Pages deploys from `main` via GitHub Actions on every push.

### The historical log
There is a historical log file in the repo (find it — likely `CHANGELOG.md` or similar in the root).
**It is currently out of date.** First maintenance task: bring it in line with §7 of this file, up to the
build now sitting in `index.html`. From then on, **every commit appends one entry to it**: version, date,
one line per change, and a note if it needed a reference/asset from the owner. §7 here stays as the short
summary; the log is the detailed record.

### Developer submission flow
Collaborators edit text / audio / sprites in dev mode and export a package (ZIP + `manifest.json`,
`schemaVersion: 1`; per change: `type` (text|audio|sprite), `character`, `target`, `value` or `file`, required
`note`). Limits: **300 KB per audio, 200 KB per sprite, 500 chars per text value, 2 MB total.**
Colours and scales export as `type: text` targets. Audio over 300 KB is **flagged** to `flagged/`, not blocked —
Claude converts it. One general note per export, editable per change.
Process: validator runs on the PR → Claude reviews and lists every change for the owner → only after approval
is it hardcoded into a new static-named build (e.g. `V.04_14`).

---

## 6. Working rules (owner's standing preferences)

1. **Usage-limit aware.** State the recommended model + effort before a heavy task (Sonnet low for scaffolding,
   medium for game-file changes, high only for genuinely hard debugging).
2. **Minimal, surgical edits.** The file is huge. `grep -n` to locate, then targeted replacement. Never reformat
   or rewrite whole sections. Never print base64.
3. **One chunk → one build → one commit** (`v0.2_NN: short description`). Bump `const VERSION="0.2_NN"` every time.
4. **Syntax-check before committing**:
   ```bash
   python3 -c "import re;h=open('index.html',encoding='utf-8').read();[open(f'/tmp/s{i}.js','w',encoding='utf-8').write(b) for i,b in enumerate(re.findall(r'<script[^>]*>([\s\S]*?)</script>',h))]"
   for f in /tmp/s*.js; do node --check "$f" || echo "FAIL $f"; done
   ```
   Where logic can be isolated, run a small Node stub test too. For UI-level verification, headless
   Playwright/Chromium has worked before (probe.py pattern).
5. **Save compatibility is mandatory.** New state fields go in `DEF` *and* in the load/migration block
   (follow the `S.p.gam` / `S.p.pr` pattern). Old saves must keep loading.
6. **Say plainly what was and wasn't tested.** Real-device behaviour — iOS/Safari, touch input, audio output,
   performance on slow phones — is never verified here; flag it.
7. **Audio**: ask for files only when needed; all music tracks get cut to half-length with a seamless crossfade
   loop before embedding, re-encoded ~128 kbps (48 kbps mono for long loops). Custom music uploaded via dev
   tools overrides the built-in track in that browser until reset in Options.
8. Short replies, terse summaries. The owner directs with short commands ("continua", "passa alla X") and
   prefers you to proceed rather than ask, unless a decision is genuinely blocking.
9. Open source: keep it readable. UI/UX improvements are welcome when they're part of the approved task.

---

## 7. Version history

`V<base>_<n>`. One increment per delivered build.

| Range | Content |
|---|---|
| 0.1_1 → 0.2_5 | The OG Chat: whole game built — both characters, progression, difficulties, power-up, 5 maps, menu scene, 30 achievements, El Gamblador, dev mode |
| 0.2_7 → 0.2_19 | 1st patch: desktop scaling + shortcuts + Hardcore split + locked El Gamblador card (0.2_8); 50 quotes per character (0.2_9); BJ table rebuild (0.2_10); steel ability (0.2_11); dev girone-jump buttons (0.2_12); boar ability (0.2_13); boar 4-direction sprites, smoke, wall-break particles (0.2_14); per-map dimensions, water/lava streams, following camera, map hardening, 10 new maps (0.2_15–0.2_19) |
| 0.2_20 → 0.2_27 | Fix 2: BJ pause fix, dealer centring, raise logic, raise UI, dealer lines, options redesign with tabs (Generali/Sviluppatore) + accordions, ZIP writer + manifest builder, export dialog UI |
| 0.2_28 → 0.2_29 | Menu music swap ×2; gapless Web Audio loop player |
| 0.2_30 → 0.2_39 | "Roccia no" chunks 1–9 complete: professor sprites, dialogue box, no-branch, sì-branch, 70 battle profiles, engine, battle screen, endings, export/dev-tools integration + 3 music tracks; plus quick fixes (dev quick-battle button, quit flow returns to "Roccia sì o roccia no?", typo, in-universe win/lose text, snack DEF/SpD rebalance) |
| 0.2_40 | **Chunk 1** — professor menu-lock parity: `S.p.pr={visits,seen}` + migration, `profImg()` using `PRSPR.blink`, `"prof"` case in `paintCanvases`, locked "Il Professore" card, `seen` set only on real battles |
| 0.2_41 | **Chunk 2** — procedural up/down views (`drawFaceUD`, `drawAlgUD`), `dir` added to the render object |
| 0.2_42 | Revert: roccia procedural up/down removed (looked bad; `drawFaceUD` left defined but unused). Algidone UP kept; DOWN flip fix attempted — **owner reports DOWN still broken** |

---

## 8. Backlog — v0.3 milestone

### ▶ In progress: real up/down sprites from reference art
Reference sheets (place in `refs/` if not already committed):
- **Algidone** (1024×1024): FRONT/DOWN walk rows at y≈80–270 (frames 1–4) and y≈300–490 (frame 5 front,
  6–8 turn/back); **BACK/UP walk** at y≈560–760, 6 frames at x ≈ (47–201) (224–361) (381–517) (542–672)
  (698–828) (853–982). Roll row y≈820–960 (not needed yet). Background ≈ rgb(13,13,13).
- **Uomo roccia** (1376×768): rows 1–2 side view (existing style); **row 3 = facing UP** (mouth toward top,
  4 walk frames + 3 eat frames with the rock entering from the top); **row 4 = facing DOWN** (mouth toward
  bottom, eat frames with the rock at the bottom). Row 4 frames 2–3 look inconsistent — confirm before using.

Chunks: (1) `tools/cut_sprites.py` — crop, key out the dark background to alpha, trim, scale to match existing
sprite heights, export a preview contact sheet for approval; (2) embed as new `SPR2` keys (`al_u*`, `al_d*`,
`fu*`, `fd*`, eat variants), watching file size; (3) wire into `drawAlg` / `drawHero` — **never horizontally
flip front or back views** — and reposition the eating overlay per direction; (4) fix Algidone DOWN: check that
`P.face` is really 2 when moving down and that `dir` is passed at every call site (the menu preview call
`drawAlg(ctx,0,c*.33,c,{…})` has no `dir`).

### Queued
**Gameplay tuning trio** (small, can share one build if the owner approves):
- **El Gamblador spawns sooner** — currently triggered after girone 5. Reduce the wait so it comes up
  earlier / more often. Trigger lives in `nextMinigame` (and the girone counter `cs().gir`).
- **Ability cooldown must survive death** — the special ability (Cinghiale / Acciaio) cooldown currently
  resets when the player loses a life. It must carry over: losing a life should not refund the 25 s.
  Check where cooldown state is re-initialised on respawn (`resetActors`, `startGame`, `updateAbil`,
  `steelOn/Off`, `boarOn/Off`) and move it out of the per-life reset.
- **Bigger maps appear more often after level 10** — the 10 extra hand-authored maps unlock with the
  level-10 achievement; raise their weight in the per-girone random map pick so big maps show up more
  frequently once unlocked.

- **Chunk 8 — movesets**: 20-move learnset per asset and ghost spread over levels 1–100 (pure data).
- **Chunk 9 — level-gated moves**: engine + move menu expose everything unlocked at or below current level.
- **Chunks 4+5** — pub sprite (professor's "cacciata") and dirty-pond sprite with splash sound/animation.
- **Chunk 6** — Duskull sprite. **Chunk 7** — battle background/layout rework. **Bugfix** — remove shadows under
  professor sprites. *(These four need references/screenshots from the owner.)*
- Deferred: El Gamblador extra intro sprite; ability balancing (8 s / 25 s); a dedicated audio-and-balance pass.
- Audio pending from the owner: a better-fitting intro track (the current one was cut in half and looped).

### Later phases
- **B/C — "Esporta modifiche"**: finish the export UI and verify a real export against
  `validate_submission.py`, then update `DEVELOPERS.md`.
- **D/E — Firebase login + cloud save**, max 10 manually created accounts: Firebase Auth (email/password),
  Firestore per-player saves, rules isolating each player. **D** (console setup) is the owner's job and must be
  done before **E** (in-game implementation). Don't start E without a working config.

---

## 9. Delivery checklist

- [ ] `git pull --ff-only` at session start, commits from `a5fc3ee` visible
- [ ] Task was already planned in Claude — scope unchanged
- [ ] Minimal targeted edits, no base64 printed
- [ ] `VERSION` bumped
- [ ] `node --check` passes on every script block
- [ ] Old saves still load (new fields in `DEF` + migration)
- [ ] Italian text, in-universe wording, no cross-character assets
- [ ] Historical log updated with this version's entry
- [ ] Short patch note: what changed, how to test, what wasn't tested
- [ ] Commit `v0.2_NN: …`, push (Pages redeploys automatically)
