# CLAUDE.md — Mangiasassi

Permanent project context for Claude Code. Read it fully at the start of every session.

## SESSION HANDOFF
F5 (0.4_7) approved. 0.4_8 (F4a, skin tool part 1: export full character sheet + map) built, awaiting the owner's phone test. Next chunk: F4b (skin tool part 2, import + local preview + export as submission), brief arrives from a new Claude chat. Sessions may run as Claude Code cloud sessions: then the brief starts with a cloud preamble; follow it.

---


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

In 0.4.5 every decision arrives pre-made in the brief; there are no in-session question rounds.

---

## 1. FIRST COMMAND OF EVERY SESSION — sync git

Claude Code works and pushes on `dev`. `main` changes only at a release (merge dev → main), except workflow/docs chunks explicitly marked "on main".

```bash
git status                              # must be clean
git fetch origin
git checkout dev
git pull --ff-only origin dev
git log --oneline dev..origin/main      # owner web uploads / main-only commits
grep -n 'const VERSION' index.html      # confirm which build you're actually editing
```

If origin/main has commits that dev lacks (owner web uploads), merge origin/main into dev only when they touch none of the files changed on dev since the last merge; otherwise stop and ask. Never rebase, never force-push, never rewrite web commits. If `--ff-only` fails, stop and ask. Exception: the bugs-export bot may rebase its own unpushed commit; Claude Code never rebases.

**If a push to `dev` is rejected because `origin/dev` moved**: `git fetch origin` and inspect the new commit(s) (`git show --stat`) first. A merge is allowed **only** when the incoming commits touch **none** of the files your own commit changed — `git merge origin/dev` (never `rebase`, never `push --force`), then report what was merged. Any file overlap → **stop and ask**.

### 1b. SECOND COMMAND — check for developer submissions (submissions come first; read on `dev`)
Right after the pull, look for submission packages that have not been processed yet:

```bash
find submissions -name manifest.json -not -path 'submissions/_*' | sort
cat submissions/PROCESSED.md 2>/dev/null     # packages already handled (create it on first use)
```

Any `manifest.json` whose folder is **not** listed in `submissions/PROCESSED.md` is **pending**. If there is at
least one pending package, it goes **before any other task of the session**, following §5 "Submission-first
procedure". Tell the owner at the start of the session: "N submission(s) pending: …".

### 1c. THIRD COMMAND — triage the bug reports (after pending submissions, before any chunk)
If `bugs/inbox/` has files (ignore `.gitkeep`): before any chunk (after pending submissions), triage them. Read each report; compare with the known bugs in §8, `bugs/BUGS.md` (NEW / TO REVIEW / FIXED) and the recent CHANGELOG. New → add to `## NEW`. Looks like a known bug → `## TO REVIEW` with a pointer to the item it seems to match. Identical reports (same `meta.acct` + same text) are merged into one entry listing all dates. Entry format: `- <date> · <screen> · <version> · <acct> — <text, first 200 chars> ([report](triaged/<file>))`. Move each processed file to `bugs/triaged/`. **Classify only: never fix anything during triage.** Commit "bugs: triage N report(s)", push `dev`, and tell the owner how many landed in NEW / TO REVIEW. (Reports arrive from the daily export workflow `.github/workflows/bugs-export.yml`, §10.2/§10.4.)

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
- **34 achievements** across 5 categories (incl. Minigiochi); 50 cycling "Partita finita" quotes per character, some
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
- **Export (F3b, format v2, docs/submissions-v2.md)**: `exportDialog` (two actions; both need a Firebase dev session, otherwise disabled with "Accedi per inviare"); texts/colours/scales: `expTextChanges` (with the built-in `before`) → `expTextEdits` → `expSendTexts` → `editSubmit`/`editPost` (Firestore `edits`, fields exactly as the rules) with the local queue `mgs_editq` (`editQueue`/`editFlush`, flushed like the bug queue) and the sent marks `mgs_editsent` (`expSentState`: new / queued / sent, both keys `_dev` on the dev site); audio + sprites: `expBuildPackage` (`expAudioItems`, `expSpriteItems` = hook for F4, `expBuiltinB64`, `expSha256`, `expZip`) → ZIP `submissions/<acct>/<date>/`. `exportTargetsMd` (v1 target list) is kept but no longer exposed; `window.mgExport` is gone. Tests: `tools/fbstub/test_f3b.py`.

### Dev mode
Tap **"Build locale" five times** in Options to open the login modal (username + password, **Firebase Auth**; the game appends `@mangiasassi.invalid`, §10.2). The role comes from Firestore `devs/{uid}.role` (`master`, `dev1`…`dev5`): internally `role` is `'master'` or `'dev1'` (every dev1…dev5 behaves as `dev1`, master-only = Sblocca tutto + menu/GAM music uploads), `acct` keeps the account name (shown in the Account accordion, default developer name of the export). `isMaster()` is the helper.
The SDK (`fbLoad`, v12.19.0 from gstatic) is loaded with `import()` only when the login modal opens or when the dev cache says a session exists: the game never waits for it (8 s timeout = offline). Two separate Firebase sessions per site (app name `mgs` / `mgs_dev`). Cache `mgs_dev` (`mgs_dev_dev` on /dev/) = `{role,acct,fb:true,devOn}`: restored at load, verified in the background (`fbVerify`: no user / role removed → dev off + SIM off; unreachable → the session stays valid). A cache without `fb:true` (old local login) is cleared. `file://` builds cannot log in.
Developer options must be **completely invisible** when the dev toggle is off; Sblocca tutto ends with dev mode. Dev jump/map runs, `PR.test` battles and Ferma tests save no progress and never set real unlock flags (`seen`, achievements). Headless tests: `tools/fbstub/` (stub SDK + `test_f1.py`; never real credentials).

### Long-press text edit (F5)
`lpEnabled()` = Firebase dev session + dev mode on. Hold 3 s (pointer moves > 10 px or an earlier release cancel; a yellow outline fills after 0.3 s) on any DOM text or on canvas text → popup «Modifica testo» (screen id `dev-textedit-popup`, freezes the game via `bugFreeze()`, `BUG` guard shared with the bug popup so Esc = Annulla and no key reaches the game); the click that follows the release is swallowed. Never on inputs/textareas, `[data-nolp]` (d-pad, Ferma pad, the popups themselves). **DOM text** works anytime (`lpDomTarget`: nearest element with own text, text under the finger inside a container, and the FULL current line for the typewriter boxes `#btxt`/`#ptxt`/`#pbtx` via `B.say`/`PR.say`/`PR.pb.txt`). **Canvas text**: only in dev mode `lpInstall()` wraps `CanvasRenderingContext2D.fillText/strokeText` (removed again by `lpUninstall()`, driven by `lpSync()` from `render()`, login/logout, `fbDrop`) and records `{text, rect}` per canvas for the latest frames (`canvas.__lp`, `lpRec`); `lpCanvasHit` picks the smallest rect under the finger; `lpCanvasOk()` allows it only while the game is paused (maze pause, Ferma paused/over/win, BJ paused or waiting for a choice, professor waiting for a tap/choice/battle command) — ignored while the game runs. `lpKnown()` resolves known override keys (`tile.<id>.label`, card names `item.*/game.*/char.*`, BJ/PR lines → `S.tiles` / `S.ov` / `S.gtext`, applied live, colour + scale fields as the old pens); everything else is a **proposal**: no target, `locator {text,pos}` (pos = screen id + DOM path or `canvas #id x,y,w,h`), stored in `mgs_editprops` (`_dev`), listed in the export dialog as «anteprima non disponibile» and sent by «Invia testi» (F3b, keys `loc:<hash>`). Per-change notes: `mgs_editnotes`. The pens are gone (the `S.ov` store stays; «+» / «−» for custom tiles/cards stay). Tests: `tools/fbstub/test_f5.py`.

### Skin tool (F4a)
Opzioni → Sviluppatore → accordion «Costumi» (`devUI()`-gated, so every dev role sees it, not master-only): character selector + «Scarica foglio» → `skinExportSheetUI` → `skinBuildSheet(char)` → same `expZip`/`expDownload` path as «Scarica pacchetto». `SKIN_DEF` (per character: `sets` = ordered frame-key rows with a label/direction, `used` = where each real frame is drawn, `skipped` = dead frames with a reason, `refs` = procedural poses rendered live for context only) is the only hand-authored data; every pixel comes from `IMG[]` and the game's own draw functions (`drawFace`, `drawFaceEatFX`, `drawBoar`) at export time, never from `refs/`. `skinRows`/`skinPaginate`/`skinPageGeom` lay the sheet out at scale ×4 with a 25% transparent margin per cell (room to overhang the base frame), wrapping rows before 4096 px and paging into further numbered sheets if a row set ever needed more (not the case today: roccia 1804×2924, algidone 3708×3651, one sheet each). Output: `<char>_GUIDE.png` (grey bg, pink cell borders, live frame drawn at its true position, header/labels), `<char>_DRAW_HERE.png` (same size, fully transparent), `<char>_cells.json` (schema 1: `char`/`baseVersion`/`scale`/`margin`, per-frame `base{x,y,w,h}`/`set`/`dir`/`flip`/`used`, `refs[]`, `skipped[]`; placeholder `skin:"nuovo"`/`mode:"overlay"` for F4b to set), `LEGGIMI.txt`. The Ferma Algidone! climber reuses roccia's `f0-2`/`fd*`/`fu*` frames via `drawFace` (`faDrawPlayer`) — already skin-hooked, no separate frame set; Algidone's own Ferma frames (`FAIMG.alg_*`, the thrower NPC) are a different, non-skinnable asset and stay out. `refs/skins/cut_from_cells.py` reads schema-1 sheets too now (downscales each cut PNG by 1/scale, writes `ox`/`oy` to `<skin>_offsets.json` from the margin) while legacy `geka`/`bk` sheets (no `scale` field) cut exactly as before. Tests: `tools/fbstub/test_f4a.py`.

### Segnala un bug (F6a) and `screenId()`
`canReport()` (`!!role || (BUG_PLAYERS && bugPlayerSession())`, `BUG_PLAYERS=false` until 0.5, `bugPlayerSession()` is the F2 hook) → `bugBtn(cls)` puts the icon `#bugb` in every top bar (menu `.brand`, `.top` screens, maze/BJ/Ferma HUD, professor `.prs`, over screen); one capture-phase click listener opens `bugOpen()`. `bugFreeze()` freezes the running game like its pause but without the pause menu (maze `G.state="pause"`, BJ `bjPauseT`, Ferma `FA.paused`, professor `timeFreeze()` = frozen `performance.now` + pausable `prSleep` records in `PR.sp`) and returns the resume function; while the popup is open a capture-phase key handler stops every key. Send: `bugSubmit` → `bugPost` (Firestore `bugs`, fields exactly as `firestore.rules`) or the local queue `mgs_bugq` (`_dev` on the dev site, max 20, `meta.qts` = original time), `bugFlush` on verify/login, `online` event and after each send; permission errors keep the report queued and stop flushing (`BUG_NOFLUSH`). `screenId()` maps the current state to a canonical id of `refs/screens/SCREENS.md` (table `SCREEN_IDS`; base id when the variant has none, `unknown:<screen>` otherwise); F5 reuses it. Tests: `tools/fbstub/test_f6.py`.

### Ferma Algidone! (screen fa)

**Ferma Algidone! code map** (`index.html`, `grep -n 'FA_\|fa[A-Z]'`): data `FA_LEVELS[0..2]` (fields: `title/blurb/introArt`, `girders` with optional `flow`/`conveyor:{v,rev,dir}`, `ladders`, `bolts`, `grill:{x1}`, `stopLeft`, `items` incl. `meatHop`/`grill`/`flameClimb`, `last`, `goal` (floors 1-2 only));
world 360×610; `FA_PHYS`; loop `faLoop` → `faStep` → `faDraw`; entry `startFerma({level,test,debug,extra,goal,finale,run,encounter,mult5})` (dev buttons, the Giochi card "Gioca" = practice, and the real encounter `faInvite`→accept; `FA.enc={n,run,mult5}` only in encounter mode; `faBackToMaze/faResume` return to the maze; `FA_FORCE` = dev "Forza incontro"); items `faSpawn/faItemsStep/faCollide/faSeparated/faGrillHit`;
belts `faInitBelts` (also inits bolts/holes) `faBeltV/faBeltStep/faDrawBelt`; bolts `faBoltPick/faBoltsStep/faInGap/faDrawBolts/faDrawGirder`; grill `faGrill()`; HUD `faHud`; panels `faPanel`; audio `faSnd(slot)` → `playSnd(slot,"fa")`, `FA_SLOTS`, `DEFSND.fa`;
state `FA.state` = `intro|play|dying|climb|collapse|win|over` + `FA.paused`; floors `faLoadFloor(i,lives,score)`, `faRestart` (Riprova = floor 1), `faNextFloor` (Avanti), `faAct` (`retry|next|replay|exit|resume`); `faIntro/faIntroEnd`, `faDie`, `faFinishDeath`, `faOver`,
`faWin` → `faClimbStep` (floors 1-2) → `faWinPanel` (+`faCountStep`); `faFinalWin` → `faCollapseStep` → `faFinalPanel` (floor 3), `faColOff`, `faAlgPose`; `faExit` returns to the menu. Demos (Pages, never linked): `prototypes/algidone/` 01–05. Review images: `refs/ferma_algidone/review/`.

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
.github/workflows/             pages deploy + validate-submission + bugs-export (bugs-export.yml lives on BOTH main and dev — main is needed for the schedule/manual run — and the two copies must stay identical)
DEVELOPERS.md                  browser-only guide, no Git knowledge required
CODEOWNERS                     → Ciprognola
LICENSE                        MIT
CLAUDE.md                      this file
docs/releases/                 archived release plans (0.4.md, …)
bugs/                          bug triage (BUGS.md); bugs/inbox/ = exported reports waiting for triage, bugs/triaged/ = processed ones
tools/bugs/                    export_bugs.py (Firestore → bugs/inbox/, run by the workflow) + mocked test
firestore.rules                copy of the Firestore rules published in the console
tools/                         helper scripts
tools/screens/                 screens library scripts (capture.py, make_index.py)
refs/                          reference art and review images
refs/screens/                  screens library: one PNG per screen + SCREENS.md (canonical ids)
```

GitHub Pages deploys from `main` via GitHub Actions on every push.

### The historical log
`CHANGELOG.md` is the detailed build-by-build log, kept current through the 0.3 release (`## 0.3 —
2026-09-23`). **Every commit appends one entry to it**: version, date, one line per change, and a note if
it needed a reference/asset from the owner. §7 here stays as the short summary; the log is the detailed
record.

### Developer submission flow
**Format v2 (from build 0.4_6) — spec: [docs/submissions-v2.md](docs/submissions-v2.md).** Text / colour / scale edits travel from the game straight to Firestore `edits` («Invia testi»); the daily workflow (`bugs-export.yml`, `tools/bugs/export_bugs.py`) turns them into normal packages `submissions/<acct>/<YYYY-MM-DD>-testi/` on `dev`. Audio, sprites (and later skins) stay a ZIP («Scarica pacchetto») uploaded by PR to `dev` into `submissions/<acct>/<YYYY-MM-DD>/`. `<acct>` = the Firebase account name (dev1…dev5, master). `manifest.json` `schemaVersion: 2` records `baseVersion`, `site` and, per change, `before` (value or `{sha256,bytes,…}` at the base version), `screen` (canonical id), `locator`, `meta` (sprite/audio measurements, filled in by the tool) and `note`. Schema v1 packages are still accepted (no conflict check).
Limits: **300 KB per audio (bigger → `flagged/`, Claude converts), 200 KB per sprite, 500 chars per text value, 300 per note, 2 MB total.**
Process: validator (`scripts/validate_submission.py`, tests `scripts/test_validate_submission.py`, fixtures `submissions/_fixtures/`) runs on the PR / on the bot's export → Claude reviews and lists every change for the owner → conflict check → only after approval is it hardcoded into a new build.

### Submission-first procedure (standard from v0.4)
The developer sends text edits from dev mode (**Invia testi**, exported by the bot into `submissions/<acct>/<YYYY-MM-DD>-testi/`) or downloads a ZIP (**Scarica pacchetto**; until 0.4_6: **Esporta modifiche**) and uploads it
into `submissions/<acct>/<YYYY-MM-DD>/` through a PR to `dev`. Once the `validate` check is green the owner merges the PR
(it only adds files under `submissions/`, never touches `index.html`). The next Claude Code session finds it via §1b.

1. Run `python3 scripts/validate_submission.py <package folder>` locally too; report its output.
2. **List every change** for the owner in a table: `type · character · target · screen · file/value · size · base version · conflict · note`,
   plus anything flagged (audio > 300 KB in `flagged/`, cross-character assets, non-Italian text, unknown targets).
3. **Conflict check** (v2 packages): compare each change's `before` with the target's current value in the latest `dev` build (text/colour/scale: the string; files: sha256/bytes of the embedded asset). Equal → conflict column «—». Different → «changed since <baseVersion>», the owner decides. Target unknown in the current build → flagged. v1 packages: «n/a».
4. **Wait for the owner's approval** ("ok", "approva", or a partial list). Nothing is embedded before that.
5. Implement the approved changes as one build (convert flagged audio per §6 rule 7 first), bump `VERSION`,
   commit `v0.4_NN: submission <name>/<date> — <summary>`.
6. Append a line to `submissions/PROCESSED.md`: `<folder> · <build> · approved/rejected items · date`.
   Rejected packages are listed too, so they are never picked up again.
7. **Export bugfixing is in scope**: if the export itself produced something wrong (bad target name, missing
   file, wrong manifest field, audio slot that doesn't map), fix the export code (`exportDialog`, `expAudioItems`,
   `expTextChanges`, …) in a **separate** build right after the submission build, and note it in the log.

---

## 6. Working rules (owner's standing preferences)

1. **Usage-limit aware.** State the recommended model + effort before a heavy task (Sonnet low for scaffolding,
   medium for game-file changes, high only for genuinely hard debugging).
2. **Minimal, surgical edits.** The file is huge. `grep -n` to locate, then targeted replacement. Never reformat
   or rewrite whole sections. Never print base64.
3. **One chunk → one build → one commit** (`v0.4_NN: short description`). Bump `const VERSION="0.4_NN"` every time
   (numbering switched to `0.4_NN` at the v0.4 release, after `0.2_NN` → `0.3_NN` at v0.3; the release build itself is bare `"0.4"`,
   the next delivered build is `"0.4_1"`, then `"0.4_2"`, and so on — see §7).
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
10. Owner's briefs arrive pasted from Claude web, one build per message. If a brief looks cut off, say so at the start of your reply and list what you received before building.

### Practical notes (verification, patch scripts, git)

- **Verification = real clicks.** Playwright (Python, headless Chromium): click the UI entry point, never call the function (`bindOpt` forwards to `bindDev` every click inside a `data-dev` block of the Sviluppatore tab (each accordion body carries it); **new dev-panel buttons need the `data-dev` attribute (or sit inside an accordion body)**). Path: splash `#rsi` → `[data-tile=opt]` →
  `[data-otab=dev]` → open the accordion (`details.acc:has(#id) > summary`) → click (`#mgfa` floor 1, `#mgfa2` floor 2, `#mgfa4` floor 3, `#mgfk` floor-1 exit test, `#mgfk2` collapse test); desktop + mobile touch (`has_touch`, `tap`). Dev mode:
  `store.set('mgs_dev',{role:'master',devOn:true})` + reload ("Sblocca tutto" = role master, `[data-sim="1"]`). For deterministic logic: freeze with `window.requestAnimationFrame=()=>0;cancelAnimationFrame(FA.raf)` (cancelling alone is NOT enough) and call `faStep(1/60)`;
  silence throws with `Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9`; `faLoadFloor(i,3,0);faIntroEnd()` jumps to a floor. Playwright quirks: an `evaluate` string whose last value is a function gets invoked - wrap in `(()=>{...})()`; never name a page-side
  variable `L` or another global const. Audio can be checked by spying on `playSnd` and on `BaseAudioContext.prototype.createOscillator/createBufferSource`. Scratch scripts are NOT in the repo and are lost between sessions - rebuild them; they go stale when level indices or Riprova semantics change.
  `node --check` every `<script>` block first, then the smoke test. Real-time polling is flaky under CPU load.
- **Patch scripts:** edit `index.html` with a Python script that asserts each anchor appears exactly once; the working copy is CRLF, so read with `newline=""`, normalise `chr(13)+chr(10)`→`chr(10)` for multi-line anchors and convert back on write. Use raw strings (`r'''...'''`) for JS containing
  `\u00e8`-style escapes. Never print base64; embed art in the chunk that first draws it. Measure size deltas against `git show HEAD:index.html` with CRLF normalised.
- **Git Bash heredocs with quotes break on this machine** — write longer scripts with the Write tool (avoid `\n` inside one-line `python -` patches: it becomes a real newline). Console output of non-ASCII needs `PYTHONIOENCODING=utf-8`.
- **Docs are committed together with the code.** Build doc text with `.replace` (no `%` formatting), and check `git diff --stat` shows CHANGELOG/CLAUDE.md before committing.
- Each chunk: bump `const VERSION` **and the root `VERSION` file together** to `0.4_NN` (`0.4.5_N` after the 0.4.5 release), CHANGELOG entry with size delta, update the §10.3 row, commit, push (to `dev` once I2 is done).
- Owner commits often land via the GitHub web UI (art uploads land at odd paths) — always `git pull --ff-only` first (§1). Briefs arrive pasted from Claude web, one build per message: if one looks cut off, say so first (§6 rule 10).

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
already reflect this. **Rolled again at v0.4** (below).

| Range | Content |
|---|---|
| 0.3_1 → 0.3_13 | v0.4 bugfixes and framework: B1-B4 (menu music gapless loop, battle music start, win/lose track, Rocciamon card), A0 built-in audio layer, P1 unlock popups, R1-R4 Percorso roadmap (tiles 3/5, gift container, milestone popups), roadmap tiles combined across characters (0.3_13) |
| 0.3_14 → 0.3_18 | Skins: K1a/K1b system (registry, overlay/replace modes, every draw path), C1 Personalizza page, K2 Cappello GEKA SNC, K3 Costume BK |
| 0.3_19 → 0.3_34 | Ferma Algidone! mini-game (M0 design + demos, M1-M7): engine, movement, thrower and items, lives/stock/HUD, floor 1 Coccia, floor 2 Macelleria (belts), floor 3 Fabbrica (bolts, grill, flames, collapse finale), owner-feedback passes, synth audio `sound.fa.<slot>` |
| 0.3_35 → 0.3_37 | Integration: M8a random encounters (1/2/3 floors), Giochi card, popup, `S.p.fa`; M8b encounter rewards, Minigiochi achievements, roadmap tile 10; M9a balance report, M9b difficulty scaling + 44 px tap targets |
| **0.4** | **Release build** (bare `"0.4"`, tag `v0.4`): Ferma Algidone!, encounters, Percorso, costumi + Personalizza, unlock popups, audio layer, 34 achievements. The next delivered build is `"0.4_1"` |

**`v0.4` tag** points at the release commit `v0.4: release — Ferma Algidone!`. **Numbering switch at the v0.4 release**: the release build carries the bare `"0.4"`; builds after it bump `0.4_NN` from `0.4_1` (counter resets).

---

## 8. Backlog — post-0.3

Player-facing items below are 0.5+; the 0.5 (bugfixes/UI-UX, player login on) and 0.6 (features) plans are drafted in Claude chat — do not act on them.

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
- **Algidone eat animation** — `fa_alg_eat1`/`eat2` look different from the other frames (beardless); enhance in a future patch (owner regenerates the frames or another fix is planned). The game uses the frames as they are (0.3_29).
- **Ferma Algidone! encounter progression** — **decided (owner-approved 0.3_33 planning, built in M8)**: a random encounter asks for N floors — 1 the first time, 2 the second, 3 from the third on; no Riprova inside encounters; game over = encounter lost, no reward, the maze run continues (M0 round 3 rule unchanged). This covers the earlier idea "first encounter ends at floor 1, harder later". Note: the headbutt kick-out (M5) was removed in 0.3_32 (replaced by the floor-3 collapse); it is recoverable from build 0.3_28 (`faKickStep`, `FA_KICK`) if it is ever wanted again.
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

### 0.5 backlog
Moved to 0.4.5 as B1: maze hitboxes around assets.

### Post-0.4 — audio submissions (A1…An)
One build per approved audio submission (Uomo roccia sounds, Algidone sounds, Blackjack voiceover, Professore voiceover, professor intro music, and the new `sound.fa.<slot>` set for Ferma Algidone!). They will arrive eventually and
are processed **after the 0.4 release** via the §5 procedure and the A0 built-in layer (keep the running slot table in §10.9; music: half-length + crossfade loop per §6 rule 7). Not a dependency of REL.

### 0.5 observation — "sad" screen
`screen="sad"` (`renderSad`, 3-2-1 countdown back to the splash) has no path that reaches it (no `go("sad")` anywhere): dead code or a missing trigger? Decide in 0.5; nothing changed now.

### 0.5 note — player bug reports and privacy
Before player bug reports go live (0.5, `BUG_PLAYERS=true`): the repo is public — player reports must not store uid/ua/account in `bugs/` (strip them in the export or keep those reports private).

### Later phases
- Firebase: set up (§10.2); login and cloud save are chunks F1/F2.

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
- [ ] Commit `v0.4_NN: …`, push (Pages redeploys automatically)
- [ ] §10.3 chunk table: status updated for the chunk just delivered

---
## 10. v0.4.5 RELEASE — DEV tools

### 10.0 Ground rules
- Versioning: builds 0.4_NN (first is 0.4_1). Release build = bare "0.4.5", tag v0.4.5. After the release, dev-branch builds are 0.4.5_N (update §6 rule 3, §7, §9 then).
- From chunk I2 on, Claude Code pushes only to branch `dev`; `main` changes only at the release (merge dev → main, never force-push, never rebase).
- One chunk = one build = one commit, then STOP for the owner's phone test. Each feature is tested and approved before the next chunk. Briefs come from Claude chat, fully decided: no in-session design questions this release. Anything not covered → stop and report.
- Never draw, edit, recolour or regenerate art. Italian in-universe text for players; dev-only screens may use plain Italian dev wording.
- Dev runs and SIM() never write progress. Save compatibility for every new field (DEF + migration + CHDEF()).
- Player-facing parts built in this release stay behind flags that are OFF (player login, cloud save, player bug reports). They are switched on in 0.5.
- The game must work fully when Firebase is unreachable (offline, blocked, slow): only dev login, bug reports and cloud save become unavailable. Never block startup on Firebase.

### 10.1 Scope
F1 dev login via Firebase · F2 player login + cloud save (flag off) · F3 submission format v2 · F4 skin creation tool · F5 text edit by long-press · F6 report a bug (devs only; player path built, flag off) · REQ tile-10 reward skin made with F4 · E1 dev-mode audit + cleanup · I2 dev/stable branches · I3 screens library · B1 maze hitboxes.
Not in scope: everything in §8 marked 0.5+, and the 0.5/0.6 drafts.

### 10.2 Firebase (set up by the owner, 2026-09-25)
- Project id `mangiasass` (no final "i"), Spark (free) plan. Auth: Email/Password on, authorized domain ciprognola.github.io. Firestore (default) database, europe-west1, production mode.
- Web config (public by design, security = rules):
  apiKey "AIzaSyA6wGraS0bw4hpHUUjru2APjnfcIEkpG8c", authDomain "mangiasass.firebaseapp.com", projectId "mangiasass", storageBucket "mangiasass.firebasestorage.app", messagingSenderId "666619489138", appId "1:666619489138:web:a181c869f0d61ae3214beb". SDK: modular v12.19.0 from https://www.gstatic.com/firebasejs/12.19.0/.
- Accounts: master, dev1…dev5, created in the console as <username>@mangiasassi.invalid. Devs type only the username; the game appends "@mangiasassi.invalid". Passwords never appear in the repo. No reset email can arrive → F1 adds "Cambia password" for logged-in devs; otherwise the owner deletes and recreates the user (new UID → new role doc).
- Roles: Firestore `devs/{uid}`, field `role` = master|dev1…dev5, edited only by the owner in the console.
- Collections: `devs`, `saves/{uid}` (F2), `bugs/{id}` (F6). Firebase Storage is NOT used (paid plan): sprites/audio keep the GitHub PR upload of §5.
- `firestore.rules` in the repo is a copy of the rules published in the console. The console is the live one: any rules change = the owner pastes it in the console, Claude Code keeps the file identical.

### 10.3 Chunk table
| ID | Chunk | Needs | Model · effort | Status |
|---|---|---|---|---|
| D1 | Docs: archive 0.4 plan, this plan, firestore.rules, bugs/BUGS.md | — | Sonnet · low | done (docs) |
| I2 | dev branch + Pages deploying main at / and dev at /dev/, §1 git rules updated | — | Sonnet · medium | done (0.4_1) |
| I3 | Screens library: Playwright script in tools/screens/, PNGs in refs/screens/, SCREENS.md | — | Sonnet · medium | done (docs) |
| E1a | Dev-mode audit report (refs/dev/DEV_AUDIT.md), no build | — | Sonnet · medium | done (report) |
| E1b | Dev-mode cleanup from the owner's picks | E1a picks | Sonnet · medium | done (0.4_2) |
| F1 | Firebase dev login, roles, Cambia password, old local login removed | — | Sonnet · high | done (0.4_3) |
| F6a | Bug report button + popup, devs only, player path flag off | F1, I3 | Sonnet · medium | done (0.4_4) |
| F6b | Bug pipeline: GitHub Action → bugs/inbox/, triage into bugs/BUGS.md | F6a, service account (owner) | Sonnet · medium | done (infra) |
| F3a | Submission format v2: spec (docs/submissions-v2.md), DEVELOPERS.md, validator v2 + tests, Firestore `edits` rules, text-edit export in the bot | I3, F6b | Sonnet · high | done (docs/infra) |
| F3b | Game side (build 0.4_6): export dialog split into «Invia testi» → Firestore edits and «Scarica pacchetto» → ZIP v2 with before/hash/meta; delete `window.mgExport` (audit pick 11); sync the root `VERSION` file | F3a, owner publishes the rules | Sonnet · high | done (0.4_6) |
| F5 | Text edit by 3 s long-press, pens removed | F3, E1b | Sonnet · high | done (0.4_7) |
| F4a | Skin tool part 1: export full character sheet + map | F3 | Sonnet · high | done (0.4_8) |
| F4b | Skin tool part 2: import sheet, local preview, export as submission | F4a | Sonnet · high | todo |
| REQ | Tile-10 reward skin (Uomo roccia) made with F4 | owner art | Sonnet · medium | wait-assets |
| B1 | Maze hitboxes around assets | screenshot / bug report | Sonnet · medium | wait-assets |
| F2 | Player login + cloud save, flag off | F1 | Sonnet · high | todo |
| REL | Release "0.4.5": VERSION, CHANGELOG, DEVELOPERS.md, roll base to 0.4.5_N in §6/§7/§9, regenerate refs/screens/, tag v0.4.5, merge dev → main | all | Sonnet · low | todo |

### 10.4 Decisions log
| Date | Chunk | Decision |
|---|---|---|
| 2026-09-25 | all | Release 0.4.5 = DEV tools. Builds 0.4_NN, release "0.4.5", tag v0.4.5, then 0.4.5_N on the dev branch. Player-facing items go to 0.5 |
| 2026-09-25 | I2 | Branches: `main` = stable (site root), `dev` = Claude Code's pushes (site /dev/). Release = merge dev → main |
| 2026-09-25 | F6 | Bug reports only for logged-in devs in 0.4.5. Player reporting is built but flag off; enabled in 0.5 with public login. No anonymous sign-in |
| 2026-09-25 | F6 | Triage file = bugs/BUGS.md with sections NEW / TO REVIEW (suspected duplicates of known bugs still go to TO REVIEW, with a pointer to the backlog item) / FIXED. Not in CLAUDE.md |
| 2026-09-25 | F3 | Sprites and audio keep the GitHub PR upload; bug reports go through Firestore; how text edits travel is decided in the F3 spec |
| 2026-09-25 | F5 | Text is identified by screen id + current text + position, not by moving every string into a table. Canvas text (battle, dialogues, Ferma HUD) via hooks in the dialogue/draw functions. Pen icons are removed when F5 ships; their colour/scale fields move into the long-press popup |
| 2026-09-25 | F4 | The sheet export also includes procedural frames rendered as reference images. An uploaded skin gets a live local preview in dev mode (never saved to progress) |
| 2026-09-25 | REQ | Tile-10 reward skin is for Uomo roccia (the Ferma Algidone! climber). Name and art from the owner |
| 2026-09-25 | I3 | Screens library = Playwright PNGs in the repo (not Figma), regenerated at each release |
| 2026-09-25 | F1 | Usernames map to <username>@mangiasassi.invalid. Old hardcoded local credentials are retired (they are readable in the public source); the owner set new passwords in the console |
| 2026-09-25 | I2 | The dev site uses its own save (mgs_v1_dev, mgs_dev_dev, IDB name + _dev), copied once from the stable save on first open; label 'DEV <version>' only on /dev/. Build numbers in §10.3 shift by one (E1b = 0.4_2, …) |
| 2026-09-25 | I3 | Screen ids in refs/screens/SCREENS.md are canonical; F5/F6 send them. Regenerate with tools/screens/capture.py at each release (add to the REL row) |
| 2026-09-25 | E1b | Owner picks from DEV_AUDIT.md: yes to all 16. Built 3–10, 12, 14–16; 1–2 go with F1, 11 with F3, 13 after F4b. Sblocca tutto ends with dev mode (fixes Trello #12) |
| 2026-09-25 | E1b | Unrequested extras accepted: 2 extra test maps, all maps start at girone 4, accordion renamed Anteprime. Standing rule: no extras outside the brief, propose them in the report |
| 2026-09-25 | F1 | Separate Firebase sessions per site (app name mgs / mgs_dev); dev1–dev5 behave as the old dev1; file:// builds can't log in, devs work from /dev/; old local login and S.creds removed |
| 2026-09-25 | F6a | Icon in every top bar, devs only (BUG_PLAYERS=false until 0.5); auto info = screen id, version, character, girone, difficulty, device, time, account; no screenshot; offline queue (max 20) sent later |
| 2026-09-25 | F6b | Daily export + manual run; docs marked exported (kept in Firestore); triage by Claude Code at session start (§1c), classify only, duplicates merged |
| 2026-09-25 | 0.5 note | Before player bug reports go live: the repo is public — player reports must not store uid/ua/account in bugs/ (strip or keep them private) |
| 2026-09-25 | F3 | Text, colour and scale edits travel from the game straight to Firestore `edits` (no ZIP, no folder), exported by the daily workflow into normal packages `submissions/<acct>/<date>-testi/`; sprites, audio and (later) skins stay a ZIP uploaded by PR to `dev`. The base version and the «before» value of every change are recorded automatically; sprite measurements are filled in by the tool. Conflict check (before vs the current build) added to the review (§5). The export workflow now marks Firestore docs exported only after the push succeeded (two-phase). Spec: docs/submissions-v2.md |
| 2026-09-25 | F3a | Two-phase export accepted (push first, then mark docs exported) |
| 2026-09-25 | F3b | Export dialog split: Invia testi → Firestore edits (queued offline), Scarica pacchetto → ZIP v2; sent texts stay applied locally, marked inviato; window.mgExport removed |
| 2026-09-25 | F3b | Accepted: unsupported audio formats are left out of the package with a warning; edits queue max 200 |
| 2026-09-25 | §1b | The text packages exported from the owner's F3b test (submissions/master/<date>-testi/) are TESTS: reject every change, record them in PROCESSED.md as "rejected — owner F3b test", do not list them for approval |
| 2026-09-25 | F5 | Long-press 3 s with a progress outline while holding; canvas text only while paused or while a dialogue waits for input (DOM text anytime); known keys preview live, other texts are sent as proposals with a locator (a text change with a locator needs no target: validator + spec updated). Pens removed, «+»/«−» kept, dead exportTargetsMd deleted |
| 2026-09-25 | F5 (report) | «+»/«−» for custom tiles/cards stay (not pens). Locator-without-target change (validator, docs/submissions-v2.md, export script, tests) accepted. Placeholder prefill ({price} etc.) in the proposal box accepted |
| 2026-09-25 | F3c | Cancelled: file packages stay «Scarica pacchetto» + PR upload to `dev`; `firestore.rules` in the repo is the published version (no packages collection). Indicative remaining builds: F4a 0.4_8, F4b 0.4_9, REQ 0.4_10, B1 0.4_11, F2 0.4_12, then REL "0.4.5" |
| 2026-09-25 | F1 | No offline backup login: if Firebase is unreachable dev mode is unavailable (a session already logged in stays valid offline) |
| 2026-09-26 | F4a (report) | The Ferma Algidone! climber (Uomo roccia) already draws through `drawFace()`/`f0-2`/`fd*`/`fu*` (`faDrawPlayer`, confirmed in code) — already skin-hooked, no new frames or draw-path work needed before the REQ tile-10 skin. SPRITE_INVENTORY.md's item 18 ("Coccia climber, not built yet") is stale, describing an earlier, different plan; not edited this session (planning-side doc) |
| 2026-09-26 | F4a (report) | Reference cells built: roccia = the procedural up/down eating rock icon (2 cells); algidone = Cinghiale lato/su/giù via `drawBoar` (3 cells). Not pre-decided in the brief beyond "Cinghiale boar, up/down eat rock icon, any procedural climber pose, placeholders" — no procedural climber pose or other placeholder art exists to render, so nothing was added for those |

**Built-in audio slots** (filled by A-chunks):

| Slot key | Source submission | Build |
|---|---|---|
| | | |

v0.4 plan + decisions log: docs/releases/0.4.md
