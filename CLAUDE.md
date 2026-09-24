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

**Exception for the v0.4 release (§10):** the owner explicitly asked for the 0.4 design questions to be asked
*in the working session*, with small structural demos, instead of bouncing every question back to Claude.
So: when a §10 chunk is marked **[Q]**, ask its listed questions (with `AskUserQuestion`-style short options where
possible), wait for answers, then write every answer into **§10.9 Decisions log** before implementing.
Anything *not* covered by a §10 question still follows the rule above: stop and report.

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

**If a push is rejected because `origin/main` moved** (someone — usually the owner via the web UI — committed
while you were working): `git fetch origin` and inspect what changed (`git show --stat` on the new commit(s))
before doing anything else. A merge is allowed **only** when the incoming commits touch **none** of the files
your own commit changed — `git merge origin/main` (never `rebase`, never `push --force`), then report what was
merged. Any file overlap at all → **stop and ask** the owner how to reconcile, don't merge or resolve it
yourself.

### 1b. SECOND COMMAND — check for developer submissions (submissions come first)

Right after the pull, look for submission packages that have not been processed yet:

```bash
find submissions -name manifest.json -not -path 'submissions/_*' | sort
cat submissions/PROCESSED.md 2>/dev/null     # packages already handled (create it on first use)
```

Any `manifest.json` whose folder is **not** listed in `submissions/PROCESSED.md` is **pending**. If there is at
least one pending package, it goes **before any other task of the session**, following §5 "Submission-first
procedure". Tell the owner at the start of the session: "N submission(s) pending: …".

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
- **Audio**: `beep, noiseBurst, initMusic, syncMusic, playSnd, loadSounds`, `SND` buckets, and a gapless
  Web Audio loop player (`loopTrack`, built on `trimSilence`) added in 0.3_4 — a single
  `AudioBufferSourceNode` with `loopStart`/`loopEnd` trimmed to the decoded buffer's non-silent range,
  because HTML `<audio loop>` leaves an audible gap on MP3. Exposes an `<audio>`-like surface
  (`play/pause/volume/paused/currentTime`) and falls back to plain `<audio>` if there's no `AudioContext`
  or decoding fails. `initMusic()`/`bgm` use it as of 0.3_4; `bgmGam` (0.3_6) and `prMusic`'s per-slot
  `PR_TRACKS` cache (0.3_6, `prTrackFor`/`prTrackInvalidate`/`prWarmMusic`) use it too.
- **Hero drawing**: `drawFace(ctx,cx,cy,w,frame,flip)`, `drawEat`, `drawAlg(ctx,X,Y,c,o)`, `drawHero(…)`.
  Render object built in `draw()`: `o={moving,power,eat,flip:P.lastH<0,anim,dir:P.face??1}`.
  Directions: `P.face` 0=up 1=right 2=down 3=left; `DX=[0,1,0,-1]`, `DY=[-1,0,1,0]`; `P.lastH` = last horizontal.
  Roccia's `fd*`/`fu*` frames are named by crop **row**, not by what they show: moving **UP** uses the
  `fd*` set and moving **DOWN** uses `fu*` (`drawHero`). `fu1`/`fu2` and Algidone's `al_r7` are defined but
  never referenced by the maze walk/roll cycles (skipped/out-of-range on purpose, not dead weight to prune).
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
CHANGELOG.md                   changelog of the project — kept current, see below
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
`CHANGELOG.md` is the detailed build-by-build log, kept current through the 0.3 release (`## 0.3 —
2026-09-23`). **Every commit appends one entry to it**: version, date, one line per change, and a note if
it needed a reference/asset from the owner. §7 here stays as the short summary; the log is the detailed
record.

### Developer submission flow
Collaborators edit text / audio / sprites in dev mode and export a package (ZIP + `manifest.json`,
`schemaVersion: 1`; per change: `type` (text|audio|sprite), `character`, `target`, `value` or `file`, required
`note`). Limits: **300 KB per audio, 200 KB per sprite, 500 chars per text value, 2 MB total.**
Colours and scales export as `type: text` targets. Audio over 300 KB is **flagged** to `flagged/`, not blocked —
Claude converts it. One general note per export, editable per change.
Process: validator runs on the PR → Claude reviews and lists every change for the owner → only after approval
is it hardcoded into a new static-named build (e.g. `V.04_14`).

### Submission-first procedure (standard from v0.4)
The developer exports from dev mode (**Esporta modifiche**, web app or local build) and uploads the package
into `submissions/<name>/<YYYY-MM-DD>/` through a PR. Once the `validate` check is green the owner merges the PR
(it only adds files under `submissions/`, never touches `index.html`). The next Claude Code session finds it via §1b.

1. Run `python3 scripts/validate_submission.py <package folder>` locally too; report its output.
2. **List every change** for the owner in a table: `type · character · target · file/value · size · note`,
   plus anything flagged (audio > 300 KB in `flagged/`, cross-character assets, non-Italian text, unknown targets).
3. **Wait for the owner's approval** ("ok", "approva", or a partial list). Nothing is embedded before that.
4. Implement the approved changes as one build (convert flagged audio per §6 rule 7 first), bump `VERSION`,
   commit `v0.3_NN: submission <name>/<date> — <summary>`.
5. Append a line to `submissions/PROCESSED.md`: `<folder> · <build> · approved/rejected items · date`.
   Rejected packages are listed too, so they are never picked up again.
6. **Export bugfixing is in scope**: if the export itself produced something wrong (bad target name, missing
   file, wrong manifest field, audio slot that doesn't map), fix the export code (`exportDialog`, `expAudioItems`,
   `expTextChanges`, …) in a **separate** build right after the submission build, and note it in the log.

---

## 6. Working rules (owner's standing preferences)

1. **Usage-limit aware.** State the recommended model + effort before a heavy task (Sonnet low for scaffolding,
   medium for game-file changes, high only for genuinely hard debugging).
2. **Minimal, surgical edits.** The file is huge. `grep -n` to locate, then targeted replacement. Never reformat
   or rewrite whole sections. Never print base64.
3. **One chunk → one build → one commit** (`v0.3_NN: short description`). Bump `const VERSION="0.3_NN"` every time
   (numbering switched from `0.2_NN` to `0.3_NN` at the v0.3 release; the release build itself is bare `"0.3"`,
   the next delivered build is `"0.3_1"`, then `"0.3_2"`, and so on — see §7).
4. **Syntax-check before committing**:
   ```bash
   python3 -c "import re;h=open('index.html',encoding='utf-8').read();[open(f'/tmp/s{i}.js','w',encoding='utf-8').write(b) for i,b in enumerate(re.findall(r'<script[^>]*>([\s\S]*?)</script>',h))]"
   for f in /tmp/s*.js; do node --check "$f" || echo "FAIL $f"; done
   ```
   Where logic can be isolated, run a small Node stub test too. For UI-level verification, headless
   Playwright/Chromium has worked before (probe.py pattern).
   **Standing step, after `node --check` passes, before every commit:** a trivial headless Chromium smoke
   test — load `index.html`, confirm the menu screen actually renders, confirm zero console errors, start a
   run. `node --check` only validates syntax; it cannot catch a runtime-only failure like an unterminated
   `/* */` block comment silently swallowing real code into a comment (still syntactically valid JS, but
   throws — or worse, just silently breaks something — the moment the page runs), which is exactly what
   happened and was caught this way during 0.3_9.
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
| 0.2_28 → 0.2_29 | Menu music swap ×2. A gapless Web Audio loop player was planned for this range but
  never actually shipped — `initMusic()`/`bgm` stayed a plain `<audio loop>` element until 0.3_4, which is
  when `loopTrack`/`trimSilence` were really built (§4, §10.8 B1a/B1b). The `makeLoopPlayer` name in older
  notes never existed in the code. |
| 0.2_30 → 0.2_39 | "Roccia no" chunks 1–9 complete: professor sprites, dialogue box, no-branch, sì-branch, 70 battle profiles, engine, battle screen, endings, export/dev-tools integration + 3 music tracks; plus quick fixes (dev quick-battle button, quit flow returns to "Roccia sì o roccia no?", typo, in-universe win/lose text, snack DEF/SpD rebalance) |
| 0.2_40 | **Chunk 1** — professor menu-lock parity: `S.p.pr={visits,seen}` + migration, `profImg()` using `PRSPR.blink`, `"prof"` case in `paintCanvases`, locked "Il Professore" card, `seen` set only on real battles |
| 0.2_41 | **Chunk 2** — procedural up/down views (`drawFaceUD`, `drawAlgUD`), `dir` added to the render object |
| 0.2_42 | Revert: roccia procedural up/down removed (looked bad; `drawFaceUD` left defined but unused). Algidone UP kept; DOWN flip fix attempted — owner reported DOWN still broken |
| 0.2_43 → 0.2_44 | Up/down sprite bugfixes: swapped `fd`/`fu` mapping, fixed a separate downscale bug in `cut_sprites.py`'s crop normalization |
| 0.2_45 → 0.2_46 | Gameplay tuning: El Gamblador timing, ability cooldown surviving death, bigger-map weighting, further El Gamblador timing pass |
| 0.2_47 → 0.2_48 | **Chunk 8** — full 20-move learnsets per fighter; **Chunk 9** — level-gated move selection wired into the battle engine (`pbSim` win rate drifted to 56.8%/53.4%, flagged for a future rebalance pass) |
| 0.2_49 → 0.2_56 | Night-street cutscene revamp (`prThrowOut`/`prSceneKick`): real cropped art from owner reference sheets replacing every procedural element (club building, moon, puddle, props), then seven owner-driven layout/size/crop iteration passes |
| 0.2_57 → 0.2_58 | **v0.3 milestone closed**: **Chunk 6** — real Duskull sprite from owner reference, replacing the procedural placeholder; also fixed the professor leg-shadow bug (found during chunk-6 QA, no extra reference needed). **Chunk 7** — battle screen visual rework from the Emerald reference (dithered ground, sandy platforms, HP-box redesign with tail notch, height-aware sizing) |
| 0.2_59 | Pre-release fixes: battle-win reward +40% and rerouted to seed the girone-3 run's active score instead of a silent sordi credit; maze-game sordi payout −30%; dev mode (`role`/`devOn`) now persists across reloads via a new `mgs_dev` key |

**`v0.3` tag** points at the doc-reconciliation commit right after 0.2_59 — the "Roccia no" professor mini-game,
its balance pass, and the Emerald-style battle screen are all shipped as of that build. See `CHANGELOG.md` for
full detail on every entry above.

**Numbering switch at the v0.3 release**: the release build itself carries the bare version `"0.3"` (no
suffix — that's what `const VERSION` reads in the tagged commit). Every build delivered **after** the release
bumps `0.3_NN` starting at `0.3_1`, the same `V<base>_<n>` pattern as before with the base rolled from `0.2` to
`0.3`; the counter resets rather than continuing the old `_59`. Rule 3 in §6 and the delivery checklist in §9
already reflect this — update both again the next time the base rolls (0.4, ...).

---

## 8. Backlog — post-0.3

### Queued — need reference art/screenshots from the owner
- **Chunks 4+5** — pub sprite (professor's "cacciata") and dirty-pond sprite with splash sound/animation.
  **Superseded**: the night-street cutscene revamp (0.2_49–0.2_56) already replaced this placeholder art
  with real reference art end-to-end. Worth explicitly closing rather than carrying forward, unless the
  owner wants a further pass on it specifically.
- Deferred: El Gamblador extra intro sprite; ability balancing (8 s / 25 s Acciaio/Cinghiale — no target
  numbers yet).
- ~~Audio pending from the owner: a better-fitting intro track for the professor mini-game~~ → moved into the
  v0.4 scope (§10, "Custom music professor intro"), arrives as a submission.

### Future — recorded during v0.4 planning, NOT part of 0.4 (owner's words, kept as written)
Do not implement any of these until they are planned into chunks in a later release.
- **Customisation page — secret power slot**: the placeholder to change the player's secret power (the
  "trasformati") becomes a real selector.
- **Customisation page — squadra rocciamon slot**: the placeholder becomes a real team selector. "This feature
  will allow the player in the future to select their own assets and choose a preferred moveset."
- **Rocciamon levelling by girone**: "rocciamon will have a higher level based on at what girone the battle
  encounter is (feature to be designed in a future release, will be considered as a random encounter such as
  el gamblador after the first script encounter)."
- **Asset experience**: "The player will be required to level up their assets by fighting against ghosts, this
  can be done with the first scripted battle choosing 'no' or simply by fighting and winning in random
  encounters. Experience and level of each asset will be shown and added up in the respective asset section,
  whilst the ghost level is scripted based on at what girone they are. This also to be defined in the future."
  ⚠ This changes today's rule "the player's asset always matches the ghost's level exactly" (§3) — that rule
  stays in force until this future feature is designed.
- **Algidone's mini-game — other playable characters**: El Gamblador and Il Professore as the climbing
  character (0.4 ships with Uomo roccia only).
- **Roadmap "?" rewards** at tiles 10, 15, 20 … 50: containers exist in 0.4, the rewards themselves are defined later.
- (Already listed above) Movepicker and professor rebalance — they naturally fit together with the asset-experience
  and customisation-page items.

### New feature ideas — not yet planned into chunks
Raised by the owner directly in a Claude Code session (2026-09-23); need breakdown into approved chunks
by Claude (the planning side) before Claude Code executes them.
- **Movepicker** — let the player choose which moves to equip out of the 20-move learnset (built in chunks
  8/9, 0.2_47/0.2_48), either before a battle or as asset configuration in the menu for each selectable
  asset/ghost. Today a fighter's 4 battle moves are auto-picked (its 4 highest-level learnset moves at or
  below current level, oldest dropped first as it levels up); this would let the player choose instead.
- **Rebalance simulation pass for the professor fight** — `pbSim()`'s win rate sits at 56.8% (roccia) /
  53.4% (algidone) over all 250 rock×plane pairs per character as of 0.2_48, down from the ~59%/58%
  documented in §2 "Balance history" after the last pass. Not treated as a blocking regression, but worth a
  dedicated rebalance once the movepicker (if built) lands, rather than chasing a moving target. The 0.2_59
  economy changes (reward +40%, maze sordi −30%) don't affect this win-rate number — they're currency, not
  battle-engine balance.

### Later phases
- **B/C — "Esporta modifiche"**: finish the export UI and verify a real export against
  `validate_submission.py`, then update `DEVELOPERS.md`.
- **D/E — Firebase login + cloud save**, max 10 manually created accounts: Firebase Auth (email/password),
  Firestore per-player saves, rules isolating each player. **D** (console setup) is the owner's job and must be
  done before **E** (in-game implementation). Don't start E without a working config.

---

## 9. Delivery checklist

- [ ] `git pull --ff-only` at session start, commits from `a5fc3ee` visible
- [ ] Pending submissions checked (§1b) and handled first
- [ ] Task was already planned in Claude (or is a §10 chunk with its [Q] answers logged in §10.9) — scope unchanged
- [ ] Minimal targeted edits, no base64 printed
- [ ] `VERSION` bumped
- [ ] `node --check` passes on every script block
- [ ] Old saves still load (new fields in `DEF` + migration)
- [ ] Italian text, in-universe wording, no cross-character assets
- [ ] Historical log updated with this version's entry
- [ ] Short patch note: what changed, how to test, what wasn't tested
- [ ] Commit `v0.3_NN: …`, push (Pages redeploys automatically)
- [ ] §10.8 chunk table: status updated for the chunk just delivered

---

## 10. v0.4 RELEASE — plan for Claude Code (VS Code)

This is a **whole release**, not a quick task. Work it in many small chunks (§10.8), one chunk = one build =
one commit, in the order given unless the owner says otherwise. Before each chunk, state the recommended
model + effort from the table.

### 10.0 Ground rules for this release
- **Versioning**: work builds stay `0.3_NN` (continue the counter). The final release build is the bare `"0.4"`
  and gets the `v0.4` tag; after it the base rolls to `0.4_NN` (update §6 rule 3, §7 and §9 then).
- **Submissions first** (§1b / §5): any pending package is handled before the next chunk.
- **[Q] chunks**: ask the listed questions first, log answers in §10.9, then build. Ask a few questions at a time,
  with 2–4 concrete options each and a recommended default.
- **Assets**: request owner art only when the chunk that needs it starts, saying exactly what (size, frames,
  directions, transparent PNG). **Never draw, generate or adapt character/skin assets yourself.** Placeholder
  coloured shapes are fine only inside `prototypes/` and for the mini-game engine chunks before art arrives.
- **Save compatibility** for every new field (`DEF` + migration block + `CHDEF()` where per-character).
- **Dev/test runs and `SIM()` mode never write progress**, never enqueue popups, never unlock roadmap tiles.
- Italian, in-universe player text. No "asset", "fantasma", "skin" in player-facing strings unless the owner
  approves the word (see §10.9) — e.g. "costume", "accessorio", "premio".

### 10.1 Scope (owner's list)
**Features**: Skins · Algidone's mini-game · Progress roadmap · Character's customisation page
**Enhancements**: Custom sounds Uomo roccia · Custom sounds Algidone · Custom voiceover Blackjack · Custom
voiceover Professore · Popup unlock (assets, ghosts, characters, mini-games, progress milestones) · Custom music
professor intro
**Bugfixing**: Main menu music loop fix · Battle music starts with the beginning of the battle animation ·
Victory/lost song starts just after the defeat · After one game with the professor, the game "Rocciamon" appears
in the "Giochi" section of the "Lista desideri"

### 10.2 Bugfixes
- **B1 Main menu music loop** — menu track uses `initMusic`/`bgm`/`syncMusic`; the gapless Web Audio loop
  player `makeLoopPlayer` exists (0.2_29). First check whether the menu track really goes through it after the
  0.3 changes. **[Q]** one question to the owner: what exactly is wrong (audible gap/click at the loop point,
  restarts when changing screen, stops after a mini-game, plays twice…)? Fix only that.
- **B2 Battle music with the battle animation** — today `prBattleStart()` stops music, `await pbTransition()`
  runs the sweeping-bars intro, and only afterwards `prMusic("battle",{fadeIn:700})` starts. Expected: battle
  music starts **when the transition animation starts** (short fade-in, no silent gap).
- **B3 Win/lose song right after the defeat** — in `pbEnding()` the `prMusic("win"/"lose")` calls come after
  other waits. Expected: the result track starts **immediately after the last faint** (the moment the battle is
  decided), before the dialogue / black fades. Keep `PR.test` behaviour.
- **B4 Rocciamon in Giochi** — `gamesHTML()` only knows G1 Mangiaroccia and G2 El Gamblador; card index 2+ is
  "???". Expected: after the **first real professor game** (`S.p.pr.seen`), card **G3 "Rocciamon"** appears
  unlocked in Lista desideri › Giochi (with a canvas icon — pokéball or Duskull, reuse existing art). Honour
  `S.ov["game_2"]` label/colour overrides like the other cards. This also feeds the popup (§10.3) later.

### 10.3 Enhancements
**Custom sounds / voiceover / music (A-chunks)** — all of this audio arrives **only as developer submissions**
(Esporta modifiche → `submissions/` → §5 procedure). No audio is requested in chat for these items.
- **A0 Built-in audio layer (prerequisite)**: today defaults are synthesized (`DEFSND`) and custom audio lives
  per-browser in IndexedDB (`snd_<char>_<slot>`, `snd_gam_*`, `snd_vo_*`). To *hardcode* approved submission
  audio, add a built-in layer: `BUILTIN_AUD={key:base64}` decoded at load. Lookup order everywhere:
  **IndexedDB override (dev upload in this browser) → built-in (hardcoded from submissions) → synth default.**
  Covers: `SND.roccia/algidone` slots (`eat, foe, power, die`), `SND.gam` (`BJ_SLOTS`), `SND.vo` (`BJ_LINES`,
  `PR_LINES`), professor music slots (`prMusic` — incl. `intro`). "Reset" in Options clears only the IDB layer.
  Export targets must match these keys so a submission maps 1:1.
- **A1…An**: one build per approved submission: Uomo roccia sounds, Algidone sounds, Blackjack voiceover,
  Professore voiceover, professor intro music (music: half-length + crossfade loop per §6 rule 7).
  Keep a running table in §10.9 of which slots are now built-in. Report the `index.html` size delta each time.
- Export/import bugs found while processing are fixed per §5 step 6.

**Popup unlock (P-chunks)** — a centred modal (not full-screen, game pixel style) shown on the **home menu**,
one at a time from a persisted queue. Two buttons: accept ("Vedi") / dismiss ("Dopo") — wording **[Q]**.
Enter = accept, Esc = dismiss. Each event fires **once ever** (`S.p.pop={queue:[],seen:{}}`).

| Event | Trigger | Accept goes to |
|---|---|---|
| New asset / ghost available | current character's level reaches `planeUnlock(i)` / `rockUnlock(i)` (item becomes buyable) | Lista desideri, tab of that item (tab 0 = aerei/attrezzi = "ghosts", tab 1 = rocce/snack) |
| New character | a character card becomes visible/unlocked in Giocatore (El Gamblador, Il Professore, future ones) | Lista desideri › Giocatore |
| New mini-game | a Giochi card unlocks (El Gamblador, Rocciamon, Algidone's mini-game) | Lista desideri › Giochi |
| Roadmap milestone | a special/reward tile becomes claimable (§10.4) | Roadmap screen, tile highlighted |

- Several unlocks at once (e.g. level-up gives 2 items) → **[Q]** one popup each, or one grouped popup? Default: grouped per type.
- **Old saves**: on first load of the build that ships P1, mark everything already unlocked as `seen` so existing
  players aren't flooded. Exception: roadmap milestones (they didn't exist before) fire once.
- Dev panel: a button per event type to preview the popup (no save change).

### 10.4 Progress roadmap (R-chunks)
- **Entry**: the achievements entry on the home screen is the trophy icon button `#trop` in the `.brand` bar
  (not a tile). **Decided:** add a matching icon button `#road` (path/map icon) **right next to it**.
- **Screen** `screen="road"` (`renderRoad`/`bindRoad`): a **snake-like path of 50 square tiles**, tile 1 → 50,
  rows alternating direction with a connecting path, scrollable, auto-scroll to the player's current tile.
  Each square = one **girone**.
- **Tile faces**: number, except **3 = pokéball**, **5 = playing-cards symbol**, **10, 15, 20, 25, 30, 35, 40,
  45, 50 = "?"**.
- **States**: locked (grey) · unlocked (coloured) · claimable (**pulsing yellow**, like the ability button) · claimed.
- **Regular tiles**: unlocked when gironi completed ≥ N (`cs().gir`, cumulative, dev runs excluded).
  **[Q]** per character or combined? Default: current character (matches the career modal).
- **Tile 3 (pokéball)**: unlocked **only** when the player has played the professor mini-game ("Roccia no" at the
  start, real game: `S.p.pr.seen`, which is set only by a real battle). **[Q]** does being kicked out on the
  professor's "No" branch also count (`S.p.pr.visits`)? Default: no, a battle is required. **No hint anywhere** on how to unlock it (no tooltip, no text). Next time the
  player is on the home menu → milestone popup → roadmap. Tap the pulsing tile → it expands with **"Riscatta"**.
- **Tile 5 (cards)**: unlocked after the player has **won 10 blackjack hands** in total (owner decision — not 1).
  Needs a new stat (`S.p.gam.won`, hands won across all runs, dev/test runs excluded — no such counter exists
  today; old saves start at 0). Reaching 10 hands won also grants a **new achievement** (31st; name + category
  **[Q]**), with progress shown like the other counter achievements. Then home → milestone popup → same claim flow.
- **"?" tiles**: default: unlock with their girone like normal tiles, tap shows "Premio in arrivo", not
  claimable yet (rewards are future, §8). **[Q]** confirm.
- **Gift container** (reward window): a modal that does **not** take the whole screen, one-time per reward,
  showing an **animated birthday gift package** (procedural pixel art: idle wobble/bounce). Tap the gift → it
  opens → the reward pops out (preview + name) → close. Build it generic: reward = `{type:"skin",id,char}` so
  future reward types reuse it.
- A **character-related reward** (Uomo roccia or Algidone) also unlocks that character's **customisation page** (§10.5).
- **Reward mapping** — default: tile 3 → **GEKA SNC hat** (Uomo roccia), tile 5 → **kebab costume** (Algidone).
  **[Q]** confirm. Rewards go to their character regardless of who is being played.
- State: `S.p.road={claimed:{}}` (+ whatever the questions add) in `DEF` + migration.

### 10.5 Character's customisation page (C1)
- In Lista desideri › Giocatore, **"Personalizza"** appears next to **"Usa"** on a character's card once that
  character owns at least one skin.
- Page (screen or large modal, **[Q]**) with three sections:
  1. **Costume/skin** — "Nessuno" + owned skins, live preview canvas of the character wearing it, select = equip.
  2. **Potere segreto** ("trasformati") — **placeholder**, disabled, "In arrivo".
  3. **Squadra rocciamon** — **placeholder**, disabled, "In arrivo".
- State per character: `skins:[]`, `skin:null` in `CHDEF()` + migration.
- The placeholders' real behaviour is **future** (§8) — build only the empty containers.

### 10.6 Skins (K-chunks)
- Skins are **accessories or alternative clothing drawn on top of the existing avatar** of Uomo roccia or
  Algidone. While selected, the character wears it **in every sprite and every place the player appears**:
  maze (all directions incl. up/down, eat frames, abilities Acciaio/Cinghiale), menu scene, Lista desideri
  previews, career/portraits, professor cut-scenes (walk, thrown into the pond), battle interjection, Algidone's
  mini-game climber, any future appearance.
- **K1 (system)**: overlay layer per sprite frame, same size/anchor as the base frame, keys `sk_<skin>_<frameKey>`,
  hooked into every draw path (`drawHero`, `drawFace`, `drawEat`, `drawAlg`, up/down views, scene/cut-scene
  draws, card canvases). Also write **`refs/skins/SPRITE_INVENTORY.md`**: every frame key per character, pixel size,
  direction, whether it's a bitmap or **procedural** (drawn by code — flag these: an overlay for them still needs
  owner art), and where it's used. This is the checklist artists draw against.
- **Asset sheets** come from the owner, one per skin, when the chunk asks. Two delivery formats, both land
  under `refs/skins/<skin>/`:
  - **Pre-cut (preferred, §10.9 K2/K3)**: `refs/skins/<skin>/frames/sk_<skin>_<frameKey>.png` — one file per
    frame, already cut — plus `<skin>_frames.json` giving `mode` and, per frame, `file,w,h,base_w,base_h,ox,oy`
    (`ox,oy` = where the base frame's top-left sits inside the skin image, since a skin frame can be **larger**
    than its base frame — parts of the art drawn outside it, e.g. a cape). Nothing to cut; embed directly.
  - **Template + cells.json (optional fallback, §10.9 K1b)**: the owner draws the skin on a template sheet and
    supplies a matching `<skin>_cells.json` describing the cell mapping. `refs/skins/cut_from_cells.py` cuts the
    sheet into the same `sk_<skin>_<frameKey>.png` naming from there.
  `tools/cut_sprites.py` remains the tool for the game's own non-skin reference-sheet cutting (professor,
  cutscene assets, etc.), unchanged — unrelated to either skin format above.
- **Missing frame rule**: if a direction/frame is missing from the sheet, **print a WARNING listing the missing
  frames and ask the owner to upload them. Do not create or adapt them.** Until provided, that frame renders
  without the skin.
- **Per-skin render mode** (§10.9 K1b): every skin declares `mode:"overlay"` (accessory drawn on top of the
  base frame, e.g. a hat) or `mode:"replace"` (drawn instead of the base frame at the same size, for a full
  costume that recolours the character rather than just adding to it). A `replace` skin still falls back to
  the base frame for any frame it doesn't provide.
- **K2 GEKA SNC hat** — Uomo roccia, a hat with the text "GEKA SNC". `mode:"replace"` (§10.9 amendment — the
  owner's art is full heads drawn with the cap already on, not an isolated cap graphic; the K1b default of
  `overlay` didn't fit the actual art that arrived).
- **K3 Costume BK** — Algidone, a Burger King-branded costume (real BK logo, brand-parody style, owner-approved
  — same treatment as the existing McDonald's cup art). `mode:"replace"` (recolours cape/logo/gloves/boots, an
  overlay would leak the base character's colours through). Reward id `"bk"` (§10.9 R3 amendment; was `"kebab"`).
- Sprite limit 200 KB each; report the size delta. Skins belong to one character only (no crossing).

### 10.7 Algidone's mini-game (M-chunks) — **high effort, the key feature of 0.4**
**Concept (owner's words):** Algidone just got control of **"Coccia"**, a renowned place that sells excellent meat.
He is throwing **sausages, porchetta and pieces of meat** at you (**Uomo roccia** for now; El Gamblador or Il
Professore in a future release) while you try to reach him in a **classic Donkey Kong game**. Kick Algidone out
of Coccia before he eats all their stock! Losing works as in regular Donkey Kong. There are different levels, and
**at each floor Algidone takes control of a more important meat producer** — like a factory or a whole intensive farm.

**Working method — ask a lot, show demos.** The owner wants many questions and **small structural demos while
developing** (level structure, item types, climbing animation, everything creative). Demos live in
`prototypes/algidone/NN-name.html`: standalone, coloured blocks, no embedded art, playable on the Pages site at
`/prototypes/algidone/…`, never linked from the game. Link the demo in your reply and ask for feedback before
moving the idea into `index.html`.

**Question bank for M0 (ask in rounds of 3–4, log everything in §10.9):**
1. Name of the mini-game and of its Giochi card (working title "Coccia").
2. Unlock & entry: when does it first appear (after girone N? random encounter like El Gamblador? from the
   Giochi card?), how often, can it be replayed from the menu?
3. Floors: list of meat producers in order (1 Coccia → … → factory → … → intensive farm → ?), how many floors,
   one screen per floor or several stages per floor? Loop after the last floor with higher speed (like DK)?
4. Stage types: classic DK set (sloped girders + rolling barrels, conveyor belts, elevators, rivets to remove)
   mapped to each producer?
5. Items: sausages roll along girders like barrels? porchetta = big/slow/can't be jumped? meat pieces fall or
   bounce like DK springs? any fire-type equivalent (e.g. a grill flame)? how fast does variety grow per floor?
6. "Before he eats all their stock": a stock bar that drains over time (DK bonus timer)? empty = lose a life?
7. Player verbs: walk, climb, jump — plus a hammer equivalent (e.g. "roccia luminosa" to smash meat)?
   Uomo roccia's Acciaio ability usable here or not?
8. Lives, difficulty link to Facile/Media/Difficile, scoring (jump-over points, smash points, stock bonus).
9. Win per floor: how is Algidone "kicked out" (animation), cut-scene between floors with the new producer?
10. Rewards: sordi / exp / achievements / a roadmap tile?
11. Controls: mobile (d-pad + jump button? swipe?), desktop keys; screen orientation.
12. Art: new frames needed — Uomo roccia climbing/jumping, Algidone throwing/eating/kicked out, Coccia building,
    each producer's scenery, meat items. (Ask for **the Coccia building asset** first, when M5 starts.)
13. Audio: music per floor? jump/hit/climb/throw sounds (synth placeholders first, real ones via submissions).

**Demos to offer during M0**: D1 level layout grid (girders + ladders) · D2 item types moving (roll / fall /
bounce) · D3 climb + jump feel (gravity, jump arc, ladder snapping) · D4 floor progression map (the producers
list as a vertical tower) · D5 HUD + stock bar + lives.

Skins (§10.6) apply to the climber. Player-facing text in Italian.

**Art spec — `refs/ferma_algidone/` package** (arrived early, committed via the web UI as `60c07bf`; validated: 39/39 frames
exist, sizes match `ferma_algidone_frames.json`, all animation keys resolve, all 14 `fa_alg_*` share one 124×158 cell, max
54 KB). Pre-cut, transparent, **1 art pixel = 1 image pixel**, draw with `imageSmoothingEnabled=false`. Anchors:
`bottom-center` (feet/base), `center` (free item), `fill` (backdrop). Girders, ladders, broken ladders, conveyors,
elevators/rivets stay **code-drawn** (recoloured per floor); sausage roll-rotation, porchetta wobble, flame/grill glow are code.
**Never edit, recolour, redraw or regenerate this art — report problems instead.**

| Key(s) | Native size | Anim / use | In-game draw size (logical px, demos' 360-px-wide layout) |
|---|---|---|---|
| `fa_alg_idle0-1` | 124×158 cell | Algidone idle (top of the tower) | ×0.6 → 74×95 (was ×0.5; 0.3_23), feet on the top girder; world grown to 360×610 for the headroom |
| `fa_alg_throw0-3` | cell | grab → lift → release → recover (game spawns the item at release) | same ×0.5 |
| `fa_alg_eat0-2` | cell | grab ham → bite → chew (stock draining) | same ×0.5 |
| `fa_alg_angry0-1` | cell | stomp with dust → furious with steam (player close / stock low) | same ×0.5 |
| `fa_alg_kick0-2` | cell | hit → flying (cap flies off) → sitting dazed (floor-win kick-out) | same ×0.5 |
| `fa_salsiccia` | 52×32 | rolling sausage (rotated to horizontal) | ×0.6 → 31×19 (0.3_25; hitbox r 8 × h 14, deliberately smaller than the sprite) |
| `fa_porchetta0` | 60×31 | porchetta, main frame | ×0.6 → 36×19 (0.3_25; hitbox = sprite, 36×19) |
| `fa_porchetta1` | 88×56 | alternative: roll with a slice cut off (optional, not a squash frame) | ×0.5 if used |
| `fa_carne0-1` | 44×32 | bouncing meat: normal / squashed on landing (floor 3) | ×0.6 → 26×19 (0.3_25) |
| `fa_fiamma0-3` | 25×32 | flame flicker (floor 3) | ×0.6 → 15×19 (0.3_25) |
| `fa_griglia0-1` | 45×33 | grill at the bottom: coals dim / bright | fill D1's 80-px grill zone → ×1.78 (≈80×59) |
| `fa_scorte0-3` | 55×58 | stock pile: full → 2/3 → 1/3 → empty (stock bar / Algidone's crate) | ×0.5 → 27×29 |
| `fa_scorte_b0-3` | 56×60 | alternative stock-pile set | same as above (pick one set in M4) |
| `fa_bld_coccia` | 294×215 | floor-1 **in-level layer** (behind the girders, in front of the backdrop, ×0.6 = 176×129, bottom on the top girder at x=270; 0.3_25) **+ intro card** (M5, ×1) | ×0.6 in level / ×1 on the card |
| `fa_bld_macelleria` | 213×126 | floor-2 in-level layer (M6, same recipe) + intro card | ×0.6 in level / ×1 on the card |
| `fa_bld_fabbrica` | 280×218 | floor-3 in-level layer (M6, same recipe) + intro card | ×0.6 in level / ×1 on the card |
| `fa_bg_coccia` / `fa_bg_macelleria` / `fa_bg_fabbrica` | 270×480 | level backdrops (portrait), behind the code structure | scale to 360 px wide (×1.33, cover-cropped vertically) — painted scenery, only non-integer case |

The climber (Uomo roccia, head only) has **no new art**: see the Q12 row in §10.9. Sizes are decisions for M1+ and may be
retuned by the chunk that first draws each thing if the layout demands it (say so in the log).

### 10.8 Chunk table
Model/effort = recommendation for Claude Code. Status: `todo` / `wait-assets` / `wait-Q` / `done (0.3_NN)`.

| ID | Chunk | Needs | Model · effort | Status |
|---|---|---|---|---|
| B1a | Shared Web Audio loop player (`loopTrack`) + main menu track | [Q] symptom (answered) | Sonnet · medium | done (0.3_4, fixed 0.3_5) |
| B1b | Move `bgmGam`/`prMusic` onto the shared loop player | B1a | Sonnet · medium | done (0.3_6) |
| B2 | Battle music starts with battle transition | — | Sonnet · medium | done (0.3_1) |
| B3 | Win/lose track right after the last faint | — | Sonnet · medium | done (0.3_2) |
| B4 | Rocciamon card (G3) in Giochi after first real professor game | — | Sonnet · low | done (0.3_3) |
| A0 | Built-in audio layer (IDB → built-in → synth) + matching export targets | — | Sonnet · medium | done (0.3_7) |
| A1…An | One build per approved audio submission (roccia sounds, algidone sounds, BJ voiceover, professor voiceover, professor intro music) | submissions | Sonnet · medium | wait-assets |
| P1 | Popup unlock framework + asset/ghost/character/mini-game triggers + old-save seeding + dev preview | [Q] wording, grouping (answered) | Sonnet · medium | done (0.3_8) |
| R1 | Roadmap state, entry button, snake screen, regular girone tiles | [Q] per-character (answered, amended 0.3_13 → combined) | Sonnet · medium | done (0.3_9, amended 0.3_13) |
| R2 | Special tiles 3 and 5 (10 hands won), `S.p.gam.won`, new blackjack achievement, "?" tiles | [Q] achievement, "?" (answered) | Sonnet · medium | done (0.3_10) |
| R3 | Gift container (animated gift) + generic reward claim | [Q] reward mapping (answered) | Sonnet · medium | done (0.3_11) |
| R4 | Milestone popups wired to the roadmap | P1, R2 | Sonnet · low | done (0.3_12) |
| K1a | Skin system, part 1 — data layer only: `SPRITE_INVENTORY.md`, exported base-frame PNGs, `SKINS` registry + `skinImg()` + load validation (empty registry, no draw-path changes, no player-visible change) | — | Sonnet · high | done (0.3_14) |
| K1b | Skin system, part 2 — overlay hook wired into every draw path per §10.9's Acciaio/Cinghiale/`al_r*` decisions | K1a | Sonnet · high | done (0.3_15) |
| C1 | Customisation page ("Personalizza", skin selector, 2 placeholders) | K1, [Q] screen/modal (answered: full screen) | Sonnet · medium | done (0.3_16) |
| K2 | GEKA SNC hat (Uomo roccia) | asset sheet | Sonnet · medium | done (0.3_17) |
| K3 | Costume BK (Algidone) | asset sheet | Sonnet · medium | done (0.3_18) |
| M0 | Design rounds + demos D1–D5 (may span several sessions) | [Q] bank | Sonnet · medium | done (prototypes only, no build) |
| M1 | Engine skeleton: new `screen`, level data format, girders/ladders render, fixed-timestep loop (+ Coccia backdrop art) | M0 | Sonnet · high | done (0.3_19) |
| M2 | Player movement: walk, climb, jump, gravity, collisions; climb = head-only `fu0`–`fu3` animated in code (§10.9 Q12 amendment). **Acceptance (§10.9 DK death rules):** fall damage measured only from where the player left the ground in free fall (~1 floor threshold), reset on landing / ladder grab / respawn; walking slopes, stepping between girder segments and leaving a ladder never count | M1 | Sonnet · high | done (0.3_22) |
| M3 | Algidone thrower + item types and behaviours | M2 | Sonnet · high | done (0.3_24) |
| M4 | Lives, hits/death, stock bar, scoring, HUD, pause. **Acceptance (§10.9 DK death rules):** death = short pause/blink → clear ALL items and flames → respawn at start → ~2 s blinking invulnerability → throws resume after a grace delay; spawn area is safe (no flame patrol, no item hits during invulnerability); item hits require vertical overlap on the same level (never compare x alone); stock drain gives tens of seconds per floor and costs a life only when it truly empties; reaching the goal zone shows a win message | M3 | Sonnet · medium | done (0.3_26) |
| M5 | Floor 1 "Coccia": building art + kick-out win sequence | Coccia building + backdrop **arrived** (`refs/ferma_algidone/`, §10.7) | Sonnet · medium | todo |
| M6 | Further floors (factory, intensive farm, …) — one chunk per floor if large | M5, art | Sonnet · medium | todo |
| M7 | Audio: synth placeholders + music/sfx slots that match export targets | A0 | Sonnet · medium | todo |
| M8 | Integration: unlock/entry, Giochi card, popup, rewards, achievements, dev test buttons, save migration | P1 | Sonnet · medium | todo |
| M9 | Mobile controls polish + balance pass | M8 | Sonnet · medium | todo |
| REL | Release build "0.4": VERSION, CHANGELOG, README, DEVELOPERS.md (new audio targets), roll base to 0.4 in §6/§7/§9, tag `v0.4` | all | Sonnet · low | todo |

Suggested order: B1–B4 → A0 → P1 → R1–R4 → K1 → C1 → K2/K3 (as art arrives) → M0 … M9 → REL.
Submissions (A1…An) slot in whenever they appear. While waiting for art, continue with the next chunk that
doesn't need it.

### 10.9 Decisions log
Every answer to a [Q] goes here: date · chunk · question · answer. Also the table of audio slots made built-in.

| Date | Chunk | Question | Answer |
|---|---|---|---|
| 2026-09-23 | R1 | Roadmap entry point | Icon button next to the trophy (`#trop`) in the home `.brand` bar, not a tile |
| 2026-09-23 | R2 | Tile 5 unlock condition | **10** blackjack hands won in total (not 1); the new achievement triggers at 10 too |
| 2026-09-23 | B1 | Main menu music loop symptom | The track restarts correctly at the loop point, but there's still silence/a gap right before it loops (not a click, not a screen-change restart, not double-playback) |
| 2026-09-23 | P1 | Popup accept/dismiss wording | "Guarda" (accept) / "Non ora" (dismiss) |
| 2026-09-23 | P1 | Grouping when several unlocks fire at once | Grouped per type (one popup per unlock type, not one per item) — spec default confirmed |
| 2026-09-23 | R1 | Roadmap tiles per-character or combined | Regular tiles (`cs().gir`) are **per-character**. Special/reward-tile claimed state stays **global** in `S.p.road.claimed` — claiming once marks it claimed on both characters' roadmaps, never claimable twice |
| 2026-09-23 | R2 | Does the professor "No" branch count for tile 3 | **No** — only `S.p.pr.seen` (a real battle) unlocks tile 3, `S.p.pr.visits` alone does not |
| 2026-09-23 | R2 | New achievement (31st, 10 BJ hands won) name/category | Name **"Il banco trema"**, in a **new category "Minigiochi"** (key `min`), which will also hold future mini-game achievements. Must confirm the achievements screen still fits phone width with 5 sections before implementing — if not, stop and report rather than redesign |
| 2026-09-23 | R2 | "?" tiles unlock condition | Unlock with their girone like regular tiles; tapping shows "Premio in arrivo", not claimable yet — spec default confirmed |
| 2026-09-23 | R3 | Reward mapping | Tile 3 → GEKA SNC hat (Uomo roccia), tile 5 → kebab costume (Algidone) — spec default confirmed |
| 2026-09-23 | R2 | Tile 3/5 faces | Reuse existing art: the pixel pokéball from the professor throw scene for tile 3, existing El Gamblador card art for tile 5. "?" stays text (no new art needed) |
| 2026-09-23 | R3 | Readiness gate | `ROAD_REWARDS` registry with a `ready:false` flag per reward, flipped to `true` only in K2/K3 (never elsewhere). A tile whose reward isn't ready behaves exactly like a "?" tile — unlocked, "Premio in arrivo", not claimable, no pulse — even once its own unlock condition (R2) is met. Only `ready:true` rewards can pulse/claim |
| 2026-09-24 | R1 (amendment) | Roadmap tiles per-character or combined | **Supersedes** the 2026-09-23 R1 answer above. Regular/"?" tiles now unlock on the **combined** girone count across both characters (`roadGir()` = sum of `S.p.ch.roccia.gir` + `S.p.ch.algidone.gir`), not the active character's `cs().gir` alone. Tiles 3/5 and `S.p.road.claimed` were already global and are unaffected. Shipped 0.3_13 |
| 2026-09-24 | K1b | Skin visibility during Acciaio | Skin stays **on**; the overlay is drawn **under** the steel effect, so the accessory picks up the steel look too, not drawn on top unaffected |
| 2026-09-24 | K1b | Skin visibility during Cinghiale | Skin is **hidden** while transformed into the boar |
| 2026-09-24 | K1b | Skin visibility during power-up rolling (Algidone `al_r*`) | Shown **only if that skin provides those specific frames**; otherwise falls back to the standard missing-frame rule (render plain, no skin, no error) |
| 2026-09-24 | K1b | Per-skin render mode | Every `SKINS` entry now carries `mode:"overlay"\|"replace"`. `overlay` = drawn right after the base frame (accessories, e.g. the GEKA cap). `replace` = drawn **instead of** the base frame at the same size (full costumes, e.g. Algidone's BK costume — it recolours cape/logo/gloves/boots, so an overlay would leak red pixels from the base). In `replace` mode, a frame the skin doesn't provide falls back to the normal base frame (same missing-frame rule as `overlay`) |
| 2026-09-24 | R3 (amendment) | Tile 5 reward identity | **Supersedes** the original R3 entry for tile 5. Reward is now id `"bk"`, name **"Costume BK"** (was `"kebab"`/"Costume kebab"). `ROAD_REWARDS[5]` updated; still `ready:false` (K3 flips it). Shipped 0.3_15 |
| 2026-09-24 | K3 (early) | BK costume art uses the real Burger King logo | Owner decision: keep it as-is for now, same brand-parody style already used for the McDonald's cup art. Logged for the record; no code impact in K1b |
| 2026-09-24 | K1b | Skin art delivery workflow | Skins arrive as an artist-drawn sheet on a template, plus a `<skin>_cells.json` describing the cell mapping, both under `refs/skins/<skin>/`. Cut by a new `refs/skins/cut_from_cells.py` (**not written yet** — no real sheet/cells.json exists to build or test it against; it gets written when the first skin sheet actually arrives, likely at the start of K2). This **replaces** `tools/cut_sprites.py` as the skin-specific cutting workflow — that tool stays as-is for its original (non-skin) reference-sheet cutting use. Documented in §10.6 |
| 2026-09-24 | K1b | Dev-only skin test tool | A debug-only skin toggle in the dev panel, both modes: `overlay` mode draws a magenta outline + corner cross at each frame's exact bounds (so alignment is visually verifiable); `replace` mode draws the base frame tinted a clearly-different magenta/blue hue. Never written to `S.p.ch[*].skin` or any persisted state — a plain in-memory variable (`DEV_SKIN_TEST`), so it's automatically never saved. Gated on `devOn`; invisible and inert with dev mode off |
| 2026-09-24 | K1b (post-review) | `drawMiniPlaceholder`'s hardcoded-to-roccia icon | **Confirmed intentional** — it's the "Mangiaroccia" mini-game brand icon, not a per-character portrait. Left unskinned, settled, no further action |
| 2026-09-24 | K2 | GEKA render mode | **Supersedes** the K1b default (§10.6 said `overlay`). The owner's actual art is full heads drawn with the cap already on, so GEKA ships as `mode:"replace"` like BK, not `overlay` |
| 2026-09-24 | K2/K3 | Pre-cut skin delivery format | New preferred workflow (documented in §10.6): a skin can arrive **pre-cut** as `refs/skins/<skin>/frames/sk_<skin>_<frameKey>.png` + `<skin>_frames.json` (`mode`, and per frame `file,w,h,base_w,base_h,ox,oy`). The template-sheet + `<skin>_cells.json` + `cut_from_cells.py` kit (§10.9 K1b) stays as an optional alternative when a skin isn't pre-cut |
| 2026-09-24 | C1 | Screen vs modal | **Full screen**, `screen="cust"` (`renderCust`/`bindCust`), not a modal — matches the other full pages (Lista desideri, Opzioni, Percorso) rather than the smaller `openModal()` popups |
| 2026-09-24 | K2 | Oversized-frame offset draw math | Implemented exactly as specified: `sx=dw/base_w, sy=dh/base_h` from the base call's own destination rect; skin frame drawn at `dx-ox*sx, dy-oy*sy`, size `skinW*sx × skinH*sy`. When the caller has applied a horizontal flip, the offset is mirrored as `skinW-base_w-ox` before the above math, so art that extends past one edge of the base frame (e.g. a cap brim) stays on the correct side once mirrored. Verified visually: the up-facing cap (large `oy`) sits correctly above the head, and the left-facing (mirrored) cap doesn't jump to the wrong side |
| 2026-09-24 | K-chunks (post-K3) | The 3 procedural places flagged in `SPRITE_INVENTORY.md` | **Settled — no skin needed**, closing the "pending owner decision" flag from K1b. Both eating icons draw the **item being eaten** (rock/snack), not the character, so there's nothing on the character for a skin to touch. The Acciaio ring/sweep effect is drawn on top of whatever `drawTinted` already rendered — since the skin is part of that rendered character (K1b/K2), the effect already applies to a costumed character with no further work. Marked settled in `SPRITE_INVENTORY.md` |
| 2026-09-24 | Roadmap (verification) | Tile 3 unlock condition re-confirmed | Re-checked directly against `roadUnlocked(3)` (index.html): it returns `!!(S.p.pr&&S.p.pr.seen)` **exclusively** — a real professor battle — and never falls through to the girone-count path (`roadGir()>=n`), which only regular tiles use. No bug; the K2 changelog/report's "girone threshold → popup" phrasing was loose (that test happened to set a girone count alongside `S.p.pr.seen`, but only the latter gates tile 3) |
| 2026-09-24 | M0 Q1 | Mini-game + Giochi card name | **"Ferma Algidone!"** (replaces the working title "Coccia" as the player-facing name). Used for both the mini-game itself and its Giochi card unless a later chunk says the card needs a shorter/different label (El Gamblador's card is a single word, "Rocciamon"'s card differs from the professor mini-game's own name, so there's precedent either way — ask again at M8 if it needs to diverge) |
| 2026-09-24 | M0 Q2 | Unlock & entry | Hybrid: a **low-rate random encounter from girone 5 onward** (same trigger shape as El Gamblador's own girone-5+ probabilistic check), with a **guaranteed forced first encounter by girone 10** if it hasn't randomly happened yet. Replayable from the Giochi card afterward, same as every other mini-game. Exact random-encounter rate **not yet specified** — El Gamblador's own rate (15% per eligible girone, `Math.random()<.15`) is a plausible starting point but needs its own confirmation, likely at M8 balance time, not M0 |
| 2026-09-24 | M0 Q3 | Floor count for the first ship | **Fewer floors to start (2-3)**, expand later in a follow-up chunk once the core loop is proven. Producer order for the first 2-3 still needs picking (Q3's full producer list wasn't answered yet — floor *count* was, not the *names*) |
| 2026-09-24 | M0 Q11 | Controls & orientation | **Portrait**, on-screen d-pad + jump button — matches every other screen in the game (maze, El Gamblador, professor battles all portrait) and matches classic arcade Donkey Kong's own cabinet orientation. Decides the layout of every M0 demo from here on |
| 2026-09-24 | M0 Q3 (producers) | Floor/producer order for the first ship | **Coccia → Macelleria → Fabbrica di salsicce** (3 floors: the restaurant, then a butcher shop, then a full sausage factory — a visible escalation in scale each floor, matching "a more important meat producer" each time). Bigger producers (intensive farm, etc.) are a later expansion, not v1 |
| 2026-09-24 | M0 Q4 | Stage mechanics per floor | **One new classic-DK element per floor**: floor 1 "Coccia" stays girders + ladders only (as already prototyped in D1/D3); floor 2 "Macelleria" adds conveyor belts; floor 3 "Fabbrica di salsicce" adds elevators or rivets-to-remove as the finale gimmick (which of the two still open, decide when that floor is actually built) |
| 2026-09-24 | M0 Q7 | Hammer-equivalent & Acciaio usability | **Neither.** No smash pickup — pure walk/climb/jump/dodge, like most of classic DK. Acciaio (and Cinghiale) stay **maze-only**, disabled in this mini-game, consistent with El Gamblador and the professor battle already being independent of maze abilities |
| 2026-09-24 | M0 Q6 | Stock bar behaviour | **Steady timer**, like DK's own bonus countdown — drains at a constant rate for the whole floor, resets each floor, empty = lose a life. Exact drain rate/duration not yet specified (balance detail for M4/M9, not M0) |
| 2026-09-24 | M0 Q5 (round 3) | Item behaviours | **Salsicce**: roll along girders like DK barrels, and sometimes drop down a ladder at random; jumping over one scores. **Porchetta**: big, slow, cannot be jumped — dodge via ladder or timing only. **Pezzi di carne**: bounce like DK springs, introduced from floor 3. **Grill**: a sausage that reaches the grill at the bottom spawns a flame enemy (DK oil-drum equivalent) |
| 2026-09-24 | M0 Q5 (round 3) | Item variety per floor | Floor 1 Coccia: salsicce + occasional porchetta. Floor 2 Macelleria: adds meat riding the conveyor belts (Q4's per-floor mechanic). Floor 3 Fabbrica di salsicce: adds bouncing pezzi di carne + the grill's flame spawns |
| 2026-09-24 | M0 Q8 | Lives, difficulty scaling, scoring | **3 lives.** Points for jumping over items; a stock-left bonus on reaching Algidone. Facile/Media/Difficile scale throw rate, item speed, and stock-timer speed (harder = faster on all three, consistent with the maze's own "harder rewards more" pattern) — exact multipliers are a balance detail for later, not M0 |
| 2026-09-24 | M0 Q9 | Floor win sequence | Reach Algidone → short kick-out animation → an intro card for the next producer (mirrors the existing girone-intro card pattern in the maze). v1 ends after floor 3 with a final victory screen; a DK-style faster loop after that is explicitly **future** (§8), not v1 |
| 2026-09-24 | M0 Q10 | Rewards | Sordi + exp via the **existing** reward formula (no new economy). New **"Minigiochi"** achievements (same category `min` as "Il banco trema", §10.9 R2): clear Coccia, clear all 3 floors, clear a floor without losing a life. Exact names still TBD (Italian, decided when M8 actually adds them) |
| 2026-09-24 | M0 (round 3) | Run impact of the random encounter | Same shape as El Gamblador: triggers mid-run, doesn't end it. **Losing costs nothing** — no reward, run continues as if it hadn't happened. **Winning pays out** (sordi/exp/achievements per the row above) and the run continues afterward |
| 2026-09-24 | M0 (round 3) | Roadmap tile 10 | **New milestone tile**, same pattern as tile 3 (professor) / tile 5 (blackjack). Unlock condition (asked, owner's own default confirmed): **first real clear of floor 1 "Coccia."** Reward stays `{type:"skin"?...}` **undefined** — behaves like a "?" tile (`ready:false`, "Premio in arrivo") until a reward is actually planned. **Not implemented now** — this is an M8 task, logged here only so the decision isn't lost |
| 2026-09-24 | M0 (round 3) | Item art | Every item (salsicce, porchetta, pezzi di carne, flame, grill) stays a **coloured placeholder** through M0-M4. Real art requested only when M5/M6 actually start, with exact sizes/frames specified then — **nothing requested now** |

| 2026-09-24 | M0-fix (DK death rules) | D2/D3/D5 were unplayable: player kept respawning and taking damage | Root causes found headless: (1) `checkCollisions` compared **x only**, so an item on *any* girder at the player's x counted as a hit; (2) every sausage lands on the bottom girder at x=20 and rolls across the spawn point, the flame could patrol it, and death cleared no items; (3) buffered jump overwrote `airStartY`, fall distance not reset on ladder grab. **Rules adopted (required for M2/M4):** death = short pause/blink (0.8 s) → clear ALL items/flames → respawn at start → 2 s blinking invulnerability → throws resume after 2.5 s; fall damage measured only from where the ground was left in free fall, reset on landing/ladder grab/respawn, threshold ≈1 floor (95 px); spawn zone safe (items on the bottom girder are harmless left of x=90, flames confined to x≥150); hits need vertical overlap on the same level, porchetta hitbox taller than a jump (still un-jumpable); stock 90 s per floor in the demo, refilled on respawn; reaching the goal zone next to Algidone shows "Piano completato!" and resets. Demo-only: "Invincibile" toggle, on-screen "Ultimo danno: <causa>" label |
| 2026-09-24 | M0 Q12 | Climber art | **Reuse existing Uomo roccia frames** for walk/jump; only a small climb pair is requested from the owner later (at M5, pre-cut like skins). No full new set. Skins keep applying |
| 2026-09-24 | M0 Q12 | Other art for the M5/M6 request list | Algidone throw + eat (incl. kicked-out), meat items (salsicce, porchetta, pezzi di carne, flame, grill), Coccia building/backdrop (asked first), Macelleria/Fabbrica di salsicce backdrops. Exact sizes/frames specified when M5/M6 start |
| 2026-09-24 | M0 Q13 | Audio for M7 | Synth placeholders for a **basic SFX set** (jump, land, climb step, throw, hit/death, jumped-item ping, floor win) plus a **stock-low warning beep**. **No music** in v1 placeholders (music per floor / single loop not chosen). Real audio arrives later via submissions (A0 layer) |
| 2026-09-24 | M0 | Demos D1–D5 status | D4 floor map (`05-floor-map.html`) shipped. All five demos exist; the question bank is fully asked. M0 awaits owner sign-off on D4 to close |
| 2026-09-24 | M0 (sign-off) | M0-fix / D4 / stock | Playability fix **approved**. D4 floor map **accepted**. Stock timer: keep **90 s** as the default, tune in M9 |
| 2026-09-24 | M0 Q12 (amendment, lean art) | Climber art | **Supersedes** the Q12 "small climb pair" row. Uomo roccia is **head only (no body/limbs)** and climbs using the existing **`fu0`–`fu3`** frames animated in code (alternating tilt/squash). Jump, death, kick-out (headbutt) and celebrate are **code-only on existing frames**. **No new climber art, no new GEKA frames** |
| 2026-09-24 | M0 (skins) | Algidone as thrower vs skins | Algidone in this mini-game is an **NPC**: always drawn **plain**; the BK costume never shows on him (default; owner may overturn later) |
| 2026-09-24 | M0-fix (promotion) | Safe spawn zone & walls | **Real design decisions for M3/M4, not demo-only hacks:** items harmless left of x=90 on the bottom girder, flames confined to x≥150, walls at the ends of the bottom girder (coordinates are the demos' 360-wide space; scale with the layout) |
| 2026-09-24 | M0 (amendment to round 3 "item art") | Item art timing | **Supersedes** "placeholder through M0–M4": the art has arrived early (`refs/ferma_algidone/`). Use the **real art in whichever chunk first draws that thing**: M1 backdrop, M3 items, M4 stock pile, M5 Coccia card/kick-out, M6 floors 2–3. No placeholders where real art exists. Package committed on its own as `60c07bf` (web upload, no VERSION bump, `index.html` untouched) |
| 2026-09-24 | M0 (art tracking) | 3 open art issues from the package README (owner decides; **do not edit/recolour/redraw/regenerate**) | (1) `fa_salsiccia` is pink/raw vs the brown/cooked sausage in Algidone's hands (`fa_alg_throw0-1`) — accept or owner regenerates. (2) `fa_alg_eat1`/`eat2`: face looks beardless/different — acceptable, owner may regenerate. (3) `fa_alg_kick1`: duplicate cap (still wearing one while another flies off) — comedic, minor. (Macelleria backdrop issue already resolved: regenerated 9:16.) Package validation also noted: the `project` string in `ferma_algidone_frames.json` has mojibake in its em dash — cosmetic, JSON is otherwise valid |
| 2026-09-24 | 0.3_21 layout | Algidone position | **Algidone top right, facing left, mirrored at draw time** (`ctx.scale(-1,1)`; PNGs never edited; every `fa_alg_*` animation mirrors the same way, so mirrored text on his belt is expected). Items start from the right; top girder slopes down-left; goal zone beside him (215–275); ladder to the top at x=60. **Bottom girder flipped to slope down-right** (grill at bottom right is the sink; items never roll onto the spawn). Spawn, safe zone x<90, flame x≥150, walls and grill unchanged. Items dropping from girder 1's right end land at the grill edge (M3 detail) |
| 2026-09-24 | M2 | Player implementation choices | Climber always Uomo roccia head-only (`drawFace`, GEKA hat via the skin hook, whatever character is selected). D3 physics values (`FA_PHYS`) kept as-is; ladder snap 28 px; grab only in the direction the ladder serves (up from `gBot`, down from `gTop`, never down onto a broken ladder). Walking off an edge falls; a girder can't be re-landed once left (the D3 demo's ±8 px landing margin let the player stand on an invisible extension of the girder end). Fall threshold 95 px unchanged, so the 107 px steps (g3-left→g2, g2-right→g1) are fatal — flagged to the owner, tune in M9. `faDie` is a stub (respawn + debug label) until M4 |
| 2026-09-24 | 0.3_23 (M2 feedback) | Scale, threshold, climb view | Climber head 36 px + hitbox 22×31, Algidone ×0.6, world 360×600 (level shifted +40, gaps unchanged, top space for M4 HUD). **Fall threshold raised 95→115 px** (all single-floor drops survivable, 2-floor fatal; M9 may retune). Climb view: up=`fd`, down=`fu` (maze convention), last direction kept when still |
| 2026-09-24 | 0.3_24 (M3) | Item engine choices | Items roll **downhill** (direction from the girder slope). Ladder drops use ladders that lead DOWN from the item's girder (D2 checked the wrong set). Porchetta hitbox 60 tall (un-jumpable), drawn ×0.5 (30×16) as instructed — looks smaller than its hitbox, flagged. Carne + grill/flame off on floor 1, on via dev button "+ carne/griglia". Player contact width vs items `hitw`=16 (body 22): forgiving, needed to keep a sausage jumpable after the +20% scale. `faDie` clears items, throws resume after 2.5 s |
| 2026-09-24 | 0.3_25 (M3 feedback) | Controls, porchetta, windows, scale, grill, meat, building | **Controls** (Ferma Algidone! only): d-pad bottom-left (66 px buttons), big round yellow "SALTA" 104 px bottom-right, 40 px gap, separate pointer captures. **Amends round 3 "porchetta cannot be jumped": porchetta is now clearable** (hitbox = sprite 36×19, no invisible box); only with a running jump (standing is impossible), window ≈0.25 s; worth more points than a sausage (M4). **Ladder refuge:** climbing ≥~17 px up any ladder (regular or the short broken ones: 35 and 41 px of height) lets items pass underneath. Sausage standing-jump window ≈0.23 s (was 0.06–0.09) via contact width 10 (body 22), sausage hitbox r8×h14; jump apex/gravity unchanged. Items ×0.6. **Grill:** item slides into the grill, `fa_griglia1` flare + code smoke puff + sparks, glow settles; same hook spawns the floor-3 flame; on floor 1 (grill off) items still just exit. **Meat hop capped** to 34 px (`FA_MEAT_HOP`=200) so it never reaches the girder above; floor 3 may retune. **Building:** `fa_bld_coccia` is an in-level layer (order: backdrop → building → girders/ladders → items/Algidone/player → HUD), ×0.6, bottom on the top girder at x=270; world height 600→610 (level shifted +10, gaps unchanged) |
| 2026-09-24 | 0.3_26 (M4) | HUD, stock, scoring, death, pause choices | HUD = D5 layout in the DOM bar (score · stock-pile icon + bar · 3 head icons · pause); stock pile = set A `fa_scorte0-3` (set B offered for comparison, not embedded). **Stock 90 s** steady, refilled on respawn/restart, empty = one life. **Death**: 0.8 s pause+flash → clear ALL → respawn → 2 s invulnerable blink (blocks hits, not falls/empty stock) → throws after 2.5 s grace. **Scores (D5 + choices)**: jump +10 sausage/meat, +20 flame, **+30 porchetta**; goal bonus floor(stock)×10. Algidone: eat 22 percent of cycles, angry on top two girders or stock under 25 percent. Game over "Scorte perse!" Riprova/Esci; win "Piano completato!" Rigioca/Esci; pause panel Riprendi/Esci; Esc/P/HUD button/visibilitychange. ✕ button removed |
| 2026-09-24 | 0.3_27 (owner phone test of 0.3_25/0.3_26) | Accepted as-is | Death pause 0.8 s + 2 s blink, sausage/porchetta jump windows, items x0.6, stock pile set A, mirrored belt text, building x0.6, climb view up=`fd`/down=`fu`, no grill on floor 1, `kick1` double cap (kept, comedic) |
| 2026-09-24 | 0.3_27 | Stock behaviour | **Amends M0 Q6 / M4:** stock keeps its value across deaths (no refill on respawn), resets only at floor start / Riprova / Rigioca. Each death: Algidone eats during the death pause and stock -10 s (clamp 0). Empty = **immediate game over** "Scorte perse!" regardless of lives. Hits/falls still cost one life. Drain paused in death pause + pause menu |
| 2026-09-24 | 0.3_27 | Hit through girders | Root cause: box overlap only. Rule: an item hits only if no girder surface lies between its base and the player's feet (body centre on a ladder) at that x (`faSeparated`). Ladder-drop hits, refuge and jump windows unchanged |
| 2026-09-24 | 0.3_27 | Eat frames | Draw path identical to the others; the difference is in the art. Only `fa_alg_eat0` is used; bite/chew animated in code. Art issue 2 stays open (owner may regenerate eat1/eat2). Cooked-sausage art: still waiting |
| 2026-09-24 | M0 → M1 | M0 closed | All rounds/demos done and signed off; M1 (engine skeleton) starts |

**Built-in audio slots** (filled by A-chunks):

| Slot key | Source submission | Build |
|---|---|---|
| | | |
