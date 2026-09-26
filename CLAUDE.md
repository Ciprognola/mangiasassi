# CLAUDE.md — Mangiasassi

Permanent project context for Claude Code. Read it fully at the start of every session.

## SESSION HANDOFF
F2b (0.4_14) approved. 0.4_15 (X1: Android back on the bug / «Modifica testo» / cloud conflict popups, conflict card layout, resized-sheet check in «Carica costume» + LEGGIMI «Dal telefono») built, awaiting the owner's phone test. `test_f1` "Esc closes the login" is NOT a timing flake: a failed login disables «Accedi», focus drops to `<body>` and Esc never reaches the login modal's own listener — needs a game-code fix, reported, not done (§10.4). Next: REQ (0.4_16, wait-assets: the owner's art + name), then B1, then REL. Sessions may run as Claude Code cloud sessions: then the brief starts with a cloud preamble; follow it.

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

### Player login (F2a, flag off)
`PLAYER_LOGIN=false`: one account, one login for everyone, same Firebase session/mapping as the dev login above (`@mangiasassi.invalid`, invite-only, no sign-up UI — the owner creates accounts in the console). `plLogin(user,pass)` does the identical sign-in + `devs/{uid}` role check as the dev flow: a role found is a dev, handled exactly like today's dev login (`role`/`acct` set, `devOn` untouched); no role → a **player** session (`playerAcct`, a plain username string or `null`). The secret 5-tap dev modal (`loginModal()`) is untouched and stays the only way in for a dev with dev mode off. Player session state mirrors the dev one: `PLAYER_KEY` (`mgs_player`/`mgs_player_dev`), `persistPlayer()`, restored synchronously at boot from cache, verified in the background by `plVerify()` (same pattern as `fbVerify`: user gone → logged out, unreachable → stays). `bugPlayerSession()` (the F2 hook, previously always `null`) now returns `!!playerAcct` for real; `canReport()` stays false for players while `BUG_PLAYERS` is off, so no bug icon. A player never reaches dev UI, Sblocca tutto or SIM. UI: Opzioni › Generali › «Account» accordion (`plAccountHTML()`, in-universe Italian: «Accedi con l'account che ti ha dato El Cipro», F1's own «Cambia password» fields reused as-is). While the flag is off the accordion only renders for a dev with dev mode on (`devOn&&!!role`, so the feature itself can be tested); a logged-out visitor or a plain player sees nothing. Screen id `opt-generali-account` (falls out of `screenId()`'s existing `optOpen.gen`-based case for free). Tests: `tools/fbstub/test_f2a.py`.

### Cloud save (F2b, flag off)
`CLOUD_SAVE=false` (next to `PLAYER_LOGIN`/`BUG_PLAYERS`). `cloudOn()` = a Firebase session (dev `role&&acct` or `playerAcct`) AND (`CLOUD_SAVE` OR (dev site AND the local test toggle `mgs_cloudtest_dev`, «Salvataggio cloud (test)» in the Account accordion)); stable with the flag off makes zero save calls and shows no cloud UI. Doc `saves/{uid}` (stable) / `saves/{uid}_dev` (dev site), fields exactly `data`/`rev`/`ts`/`ver` (rules in `firestore.rules`); every upload is a `runTransaction` (`cloudUpload`) that re-reads the doc, refuses a newer `ver` (`verCmp`: numeric base first, then `_N`) and writes `rev`+1 only if the cloud rev equals the local base rev, otherwise → conflict. What is uploaded is the string `persist()` wrote (`cloudLocal()`: SIM copies resolved to `realP`/`realAch`/`realQuick`, then `CLOUD_DEVONLY` = `tiles`/`ov`/`extra`/`gtext` and `CLOUD_SIMF` = `sim`/`realP`/`realQuick`/`realAch` removed, keys sorted by `cloudCanon` so equal content = equal hash `cloudSum` on every device). Local keys (`_dev` suffix on the dev site): `mgs_cloud` = `{uid,rev,sum,dirty,ts}` (last synced copy; `persist()` → `cloudOnPersist()` marks `dirty` when the real save's hash differs), `mgs_v1_cloudbak` = `{data,from,ts,summary}` (one backup slot), `mgs_v1_ts` = time of the last real `persist()` (the date on the device card). Sync (`cloudSyncRun`, via `cloudStart`/`cloudSync`): after login (`loginModal`, `plLoginGo`) and at boot after `fbVerify`/`plVerify`; first sync per uid vs same uid rules as the F2b brief (`saveIsFresh()`); `cloudApply` never reloads mid-run: `CL.pend` waits for `render()` on a menu screen (`cloudPendCheck`, `cloudCanApply`), and an automatic apply re-decides if the local save changed meanwhile (an explicit «Usa questo» on the cloud card applies anyway, the device copy goes to the backup). Uploads (`cloudPush`): debounced 30 s trailing after a real persist (`cloudArm`), immediate at `finishRun` and on `pagehide`/`visibilitychange` hidden (`cloudFlush`, max once per 10 s, listeners registered after the game's own persist-on-hide); never while `cloudBlocked()` (SIM/Sblocca tutto, `G.dev` runs, `PR.test`, Ferma tests). Offline/network error → status «in attesa di rete», `dirty` kept, retried on `online`/next trigger/next start; permission error → `CL.stop` until next start/login. Conflict popup `cloudConfShow()` (screen id `cloud-conflict`, freezes + blocks keys through the shared `BUG` guard, Esc = «Decidi dopo» → `CL.later` until next start; «Sincronizza ora» re-asks; each card puts the character name and «Liv. N» on separate lines since 0.4_15). **Android back (0.4_15)**: the app's back button reaches the page as the window event `mgback`; its handler first checks the shared `BUG` guard, so with the bug popup, «Modifica testo» or the conflict popup open, back = that popup's own cancel (`BUG.close`: Indietro / Annulla / «Decidi dopo») — popup closed, freeze released, `BUG=null` (the capture key handler goes inert), nothing else in `mgback` changed. Account accordion (`cloudAccHTML`, shown also for a player session on the dev site): status line `#clst`, «Sincronizza ora» `#clsy`, test toggle `[data-clt]`, «Ripristina backup» `#clrb` (dev site only, swaps backup and save, marks dirty, reload). Logout (`fbDrop`, `plLogout`, `plVerify` drop) → `cloudReset()` clears `mgs_cloud` only; `wipeData()` → `cloudWipe()` also clears the backup and `mgs_v1_ts`. Applying/restoring sets `CLOUD_LOCK` so no `persist()` (e.g. the pagehide one) overwrites the new save before the reload. Tests: `tools/fbstub/test_f2b.py` (stub keeps `saves` in localStorage `__fbstub_saves` and checks writes like the rules).

### Long-press text edit (F5)
`lpEnabled()` = Firebase dev session + dev mode on. Hold 3 s (pointer moves > 10 px or an earlier release cancel; a yellow outline fills after 0.3 s) on any DOM text or on canvas text → popup «Modifica testo» (screen id `dev-textedit-popup`, freezes the game via `bugFreeze()`, `BUG` guard shared with the bug popup so Esc = Annulla and no key reaches the game); the click that follows the release is swallowed. Never on inputs/textareas, `[data-nolp]` (d-pad, Ferma pad, the popups themselves). **DOM text** works anytime (`lpDomTarget`: nearest element with own text, text under the finger inside a container, and the FULL current line for the typewriter boxes `#btxt`/`#ptxt`/`#pbtx` via `B.say`/`PR.say`/`PR.pb.txt`). **Canvas text**: only in dev mode `lpInstall()` wraps `CanvasRenderingContext2D.fillText/strokeText` (removed again by `lpUninstall()`, driven by `lpSync()` from `render()`, login/logout, `fbDrop`) and records `{text, rect}` per canvas for the latest frames (`canvas.__lp`, `lpRec`); `lpCanvasHit` picks the smallest rect under the finger; `lpCanvasOk()` allows it only while the game is paused (maze pause, Ferma paused/over/win, BJ paused or waiting for a choice, professor waiting for a tap/choice/battle command) — ignored while the game runs. `lpKnown()` resolves known override keys (`tile.<id>.label`, card names `item.*/game.*/char.*`, BJ/PR lines → `S.tiles` / `S.ov` / `S.gtext`, applied live, colour + scale fields as the old pens); everything else is a **proposal**: no target, `locator {text,pos}` (pos = screen id + DOM path or `canvas #id x,y,w,h`), stored in `mgs_editprops` (`_dev`), listed in the export dialog as «anteprima non disponibile» and sent by «Invia testi» (F3b, keys `loc:<hash>`). Per-change notes: `mgs_editnotes`. The pens are gone (the `S.ov` store stays; «+» / «−» for custom tiles/cards stay). Tests: `tools/fbstub/test_f5.py`.

### Skin tool (F4a, F4a2, F4c, F4b1)
Opzioni → Sviluppatore → accordion «Costumi» (`devUI()`-gated, so every dev role sees it, not master-only): character selector + «Scarica foglio» → `skinExportSheetUI` → `skinBuildSheet(char,fromId)` → same `expZip`/`expDownload` path as «Scarica pacchetto». `SKIN_DEF` (per character: `sets` = ordered frame-key rows with a label/direction — a `keys` entry is either a plain key string (uses the set's own `dir`) or a `[key,dir]` pair for a row that mixes directions, e.g. Cinghiale; `used` = where each real frame is drawn; `skipped` = dead frames with a reason; `refs` = procedural poses rendered live for context only, non-empty for roccia's 2 eating icons, empty for algidone since F4c) is the only hand-authored data; every pixel comes from `IMG[]`/`FAIMG[]` (via `skinBaseImg(k)=IMG[k]||FAIMG[k]`) and the game's own draw functions (`drawFace`, `drawFaceEatFX`, `drawBoarBody`) at export time, never from `refs/`. `skinLayout(char)` (F4b1: factored out of `skinBuildSheet` so «Carica costume» can recognise an uploaded page's size against the SAME geometry the export produces) calls `skinRows`/`skinPaginate`/`skinPageGeom` to lay the sheet out at scale ×4 with a 25% transparent margin per cell (room to overhang the base frame; **F4b2 item 1**: the margin is rounded UP to a whole ×4 block per axis, so every cell — and hence the region the native cutter averages — is always an exact multiple of `SKIN_SCALE`, anchoring the base frame's own native origin exactly on an output-pixel boundary instead of letting it drift when a native width/height is odd), wrapping rows before 4096 px and paging into further numbered sheets if a row set ever needed more — Algidone is 3 sheets (3816×3712, 3816×3420, 3816×2534: the Ferma row filled a 2nd page in F4a2, Cinghiale's 6 frames filled a 3rd in F4c); roccia stays one sheet (1804×3410). Labels (F4b1 1b, readable at ×4: frame labels ≥28px, header ≥48px, `SKIN_LBLH`/`SKIN_SECLBLH`/`SKIN_HDRH` sized to fit — only ever drawn in GUIDE, never DRAW_HERE) push each page taller than before; a sheet exported by an older build fails the size-match check in the import tool below (by design — see «Carica costume»). Output per sheet page: `<char>_GUIDE[_n].png` (grey bg, pink cell borders, live frame drawn at its true position, header/labels — with `fromId`, each cell shows exactly what the game would render with that skin equipped, per its own mode), `<char>_DRAW_HERE[_n].png` (same size; blank with no `fromId`, otherwise that skin's own frames at ×4 in their real position, ox/oy respected, blank where it has none); one shared `<char>_cells.json` (schema 1: `char`/`baseVersion`/`scale`/`margin`, `sheets[]` listing every page's file+size, per-frame `base{x,y,w,h}`/`set`/`dir`/`flip`/`used`/`sheet` (page number when >1), `refs[]`, `skipped[]`; with no `fromId`: placeholder `skin:"nuovo"`/`mode:"overlay"` for a brand new costume; with `fromId`: `from:<skinId>`, the skin's real `mode`, and each frame's own `sha256` — `null` if that skin lacks it), `LEGGIMI.txt`. The Ferma Algidone! climber (Uomo roccia, played) reuses roccia's `f0-2`/`fd*`/`fu*` frames via `drawFace` (`faDrawPlayer`) — already skin-hooked, no separate frame set. The **thrower** (Algidone, NPC, never played) has its own row since F4a2: 13 real `FAIMG.alg_*` frames (`alg_kick0` dead, skipped) drawn in `faDraw`'s NPC block via `drawSkinned(c,"algidone",pose.key,im,...)` — wears Algidone's own equipped skin regardless of who's climbing; `faAlgFrame`/`faAlgPose` return `{key,im}` so the draw call has a frame key to look up. Since Ferma's art lazy-loads (`ensureFA()`/`FAIMG`, unlike the always-loaded `SPR`/`SPR2`), `loadSkinImgs()` accepts a base image from `FAIMG` too and `ensureFA()` re-runs it once `FAIMG` is populated, so a skin's `alg_*` frames aren't dropped by a boot-time check that ran before Ferma's assets existed (`skinLayout`/`skinImportRun` must `await ensureFA()` first too, for the same reason — missed once in F4b1's own testing, fixed before it shipped). `refs/skins/cut_from_cells.py` reads schema-1 sheets too now (downscales each cut PNG by 1/scale, writes `ox`/`oy` to `<skin>_offsets.json` from the margin) while legacy `geka`/`bk` sheets (no `scale` field) cut exactly as before; a multi-page skin is cut one page at a time (each page's own frames + its own `sheet{w,h}`), same script, no page-spanning support needed yet.
**Cinghiale hook (F4c, streak split in F4b1)**: the boar's body-drawing code (rects/ellipses/triangles) was split out of `drawBoar` into `drawBoarBody(ctx,u,lg,face)` (same pixels, just without the mirror `ctx.scale(-1,1)`, now applied once by the caller). `bakeBoarFrames()` (idempotent, runs once at boot before `loadSkinImgs`, `loadImgs().then(()=>{bakeBoarFrames();return loadSkinImgs()})`) bakes 6 base frames (`boar_lato0/1`, `boar_su0/1`, `boar_giu0/1` — 2 leg-swing extremes × 3 directions, `anim` chosen so `Math.sin(anim*24)=±1`) into `IMG[]` via `bakeBoarFrame(dir,phase)`: a two-pass render (measure the alpha bounding box on a scratch canvas, then redraw into a tightly-cropped final canvas with `BOAR_PAD=6` px padding), storing the origin offset as `canvas.boarAx/boarAy` (same role as `skOx/skOy` elsewhere) since there's no static PNG to measure from. **F4b1**: the motion-blur "speed line" streaks behind a moving boar used to be baked into these frames; they moved out into their own `drawBoarStreaks(ctx,u,face)`, called by `drawBoar` at the same point in the draw order (before the body/frame, for the procedural render and a skinned boar alike) — the baked frames tightened to the body's own bounds (194×135 / 116×178 / 116×168 lato/su/giù, down from 235×135 / 116×210 / 116×200). `drawBoar` now: draws the streak effect first (if moving), then computes `dirKey`/`phase`/`key`, looks up `activeSkin("algidone",key,base)` — **replace** mode draws that frame via `drawSkinLayer(ctx,sk.img,base,dx,dy,dw,dh,mirrored)` (`dx,dy,dw,dh` scaled by `c/BOAR_C` from `base`/`boarAx`/`boarAy`) *instead of* calling `drawBoarBody`; **overlay** mode calls `drawBoarBody` then draws the overlay with the same `dx,dy,dw,dh`; no skin/missing frame → `drawBoarBody` only, byte-identical to before F4c and to before the F4b1 streak split alike (a 12-case golden-hash regression in `tools/fbstub/test_f4a.py` still passes unchanged). Effects outside `drawBoar` (stress bar + "STRESS N%"/"STORDITO" text, stun sparkle stars, wall-smash dust `G.parts`, the shared ability-duration bar) were never touched and stay procedural.
**Coverage (F4a2, F4c)**: `SKINS.<id>.na` (optional array, empty for GEKA/BK) lists frames a skin intentionally skips. `skinCoverage(char)` (and `tools/fbstub/test_skin_coverage.py`'s own extraction) resolve `[key,dir]` pairs to their key before comparing the sheet's real frame keys (minus `na`) against `SKINS.<id>.frames`; the accordion shows one line per skin («`<nome>`: X/Y frame — mancano: …», `skinCoverageHTML`) and the test script writes the same matrix (real frames + procedural refs, "procedurale — da convertire" for the latter — only roccia's 2 eating icons now) to `refs/skins/SKIN_COVERAGE.md`. New/changed art must keep the sheet, `SPRITE_INVENTORY.md` and `SKIN_COVERAGE.md` current in the same build (§6 rule 11); today's known gap (BK missing the 13 Ferma thrower frames + the 6 Cinghiale frames, 19 total, grandfathered) is tracked in §8 "Skin art owed". Tests: `tools/fbstub/test_f4a.py`, `tools/fbstub/test_skin_coverage.py`.
**Carica costume + anteprima locale (F4b1)**: same accordion, below «Scarica foglio». `skinImportRun()` reads the chosen PNG page(s) (`<input type="file" multiple>`, no cells.json trusted — a page is recognised purely by matching its pixel size against this build's own `skinLayout(char)`, an ambiguous same-size match falling back to a page number embedded in the filename, no match at all failing with **«Foglio di un'altra versione: riscarica il foglio»**; **0.4_15**: checked first, a page whose width AND height both differ from one page of `skinLayout(char)` by the same factor (|sx−sy| ≤ 0.005) fails with **«L'app ha ridimensionato il foglio: esportalo a dimensione originale»** — same width with another height stays «altra versione», never auto-rescaled; `SKIN_LEGGIMI` gained a «Dal telefono» section (layered app e.g. ibisPaint X, draw on a new transparent layer, hide GUIDE, export only that layer as PNG at 100% with a transparent background, «Carica costume»)), rejects a fully opaque upload (a GUIDE screenshot or an unrelated photo) with **«Esporta solo il tuo livello, con lo sfondo trasparente»**, and cuts every matched cell with `skinBoxDownscale` — the exact same premultiplied-alpha box-filter algorithm as `refs/skins/cut_from_cells.py`'s `box_downscale()` (documented once, shared, in `refs/skins/README.md`; a dedicated test proves the two implementations byte-identical on the same input). Non-blocking warnings: an empty cell, pixels drawn outside every cell, a cut frame over 200 KB, and **«invariato»** for a frame whose cut bytes exactly match the target skin's own stored bytes (sha256). Target is either a brand new costume (Italian name, `skinSlug()` id, a mode toggle overlay/replace) or an update to an existing skin of that character (mode fixed to that skin's own). The result becomes `SKIN_IMPORT_PV` — `{char,id (null for a new costume),mode,name,frames,unchanged}` (`unchanged` = a `Set` of frame keys marked «invariato» at import time, F4b2), a plain in-memory `let`, never written to `S`/`localStorage`/`IndexedDB`. `skinImg(char,frameKey)` checks it first, before the real equipped-skin lookup, for the matching character: an imported frame wins, else (when updating) falls back to that skin's own real frame, else no override — since every draw path already funnels through `skinImg`/`activeSkin`, this one check covers the maze in every direction, eating, the menu, cards, the career modal, cutscenes, the Ferma Algidone! climber and thrower, and Cinghiale (via `drawBoar`'s own `activeSkin` call) with no other call site touched. Cleared on reload (nothing persisted to begin with), on logout (`fbDrop`) and when dev mode turns off (`#devt`); shows a coverage line and a «Rimuovi anteprima» button. **Export as a submission (F4b2)**: `expSpriteItems()` (the F3b/F4 hook, previously always `[]`) turns `SKIN_IMPORT_PV` into one `type:"skin"` change per frame not in `unchanged`, `target:"skin.<id>.<frameKey>"`, `file:"skins/<id>/sk_<id>_<frameKey>.png"` (native size), `meta:{skinId,skinName,mode,action:"new"|"update",frameKey,w,h,ox,oy,base_w,base_h}`, `before` = sha256/bytes of the target skin's own existing frame (`null` for a new skin or a frame it didn't have), `screen` = the character's maze id (`SKIN_MAZE_SCREEN`). `expBuildPackage`'s sprite-item loop is generalised (own `file` path, own `type`, own `meta` shape) rather than duplicated; the 200 KB/frame, 2 MB/package limits are the existing sprite ones (`EXP_LIM.sprite`, previously unset since no sprite item was ever produced). The export dialog shows the pending preview (name, character, mode, new/update, frame count) and a reminder that it's lost on reload. Tests: `tools/fbstub/test_f4b1.py` (import/preview), `tools/fbstub/test_f4b2.py` (cutter anchoring, export, `DEV_SKIN_TEST` removal).

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
**Format v2 (from build 0.4_6) — spec: [docs/submissions-v2.md](docs/submissions-v2.md).** Text / colour / scale edits travel from the game straight to Firestore `edits` («Invia testi»); the daily workflow (`bugs-export.yml`, `tools/bugs/export_bugs.py`) turns them into normal packages `submissions/<acct>/<YYYY-MM-DD>-testi/` on `dev`. Audio, sprites and skins (F4b2) stay a ZIP («Scarica pacchetto») uploaded by PR to `dev` into `submissions/<acct>/<YYYY-MM-DD>/`. `<acct>` = the Firebase account name (dev1…dev5, master). `manifest.json` `schemaVersion: 2` records `baseVersion`, `site` and, per change, `before` (value or `{sha256,bytes,…}` at the base version), `screen` (canonical id), `locator`, `meta` (sprite/audio measurements, filled in by the tool) and `note`. Schema v1 packages are still accepted (no conflict check).
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
   commit `v0.4_NN: submission <name>/<date> — <summary>`. **`type:"skin"` changes (F4b2)**: group by `skinId`,
   embed as a `SKINS` registry entry (new skin: full entry with `name` from `meta.skinName`; update: merge the
   new/changed frames into the existing entry, never touching frames the package didn't include), regenerate
   `SKIN_COVERAGE.md`/`SPRITE_INVENTORY.md` (§6 rule 11) in the same build, and — for a brand-new skin only —
   add one line under §8 "Costumi da assegnare" (the owner decides its unlock separately; never invent one).
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
11. **New/changed art keeps the skin tool current (F4a2).** Any chunk that adds or changes a frame, pose or
    animation of a character — bitmap or procedural — must, in the **same build**: add it to the F4a sheet
    (`SKIN_DEF` in `index.html`, §4 "Skin tool (F4a)"), update `refs/skins/SPRITE_INVENTORY.md` and
    `refs/skins/SKIN_COVERAGE.md` (regenerate with `tools/fbstub/test_skin_coverage.py`), and list in the
    session report **"art owed for: `<skin>`: `<frames>`"** for anything that goes from `ok` to `manca` on an
    existing skin — added to §8 "Skin art owed" (status `wait-assets`). **REL gate** (§9, and the REL row in
    §10.3): regenerate `SKIN_COVERAGE.md` at release time; any `manca` on a frame added since the last stable
    release blocks the merge to `main` unless the owner accepts that specific gap by name. Grandfathered for
    0.4.5 (already live in stable when this rule was written, listed in §8, not blocking): BK on the Ferma
    Algidone! thrower frames, BK on Cinghiale.

### Practical notes (verification, patch scripts, git)

- **Base64 safety — run this first, every session (F4b1 item 0).** `python3 tools/strip_index.py` writes a copy
  of `index.html` to `/tmp` with every run of 200+ base64 characters replaced by `<B64 n>`, printing only the
  output path/size. Never `grep`/`cat`/`sed`/`head`/a regex scan `index.html` directly — search only the
  stripped copy, and pipe any command whose output could still touch the real file (`git diff`, `git show`)
  through `cut -c1-300` as a backstop. Base64 has leaked into a session's own output before (0.4_9 and 0.4_10
  both, §10.4) from exactly this kind of direct scan; this tool exists so it can't happen again.
- **Verification = real clicks.** Playwright (Python, headless Chromium): click the UI entry point, never call the function (`bindOpt` forwards to `bindDev` every click inside a `data-dev` block of the Sviluppatore tab (each accordion body carries it); **new dev-panel buttons need the `data-dev` attribute (or sit inside an accordion body)**). Path: splash `#rsi` → `[data-tile=opt]` →
  `[data-otab=dev]` → open the accordion (`details.acc:has(#id) > summary`) → click (`#mgfa` floor 1, `#mgfa2` floor 2, `#mgfa4` floor 3, `#mgfk` floor-1 exit test, `#mgfk2` collapse test); desktop + mobile touch (`has_touch`, `tap`). Dev mode:
  `store.set('mgs_dev',{role:'master',devOn:true})` + reload ("Sblocca tutto" = role master, `[data-sim="1"]`). For deterministic logic: freeze with `window.requestAnimationFrame=()=>0;cancelAnimationFrame(FA.raf)` (cancelling alone is NOT enough) and call `faStep(1/60)`;
  silence throws with `Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9`; `faLoadFloor(i,3,0);faIntroEnd()` jumps to a floor. Playwright quirks: an `evaluate` string whose last value is a function gets invoked - wrap in `(()=>{...})()`; never name a page-side
  variable `L` or another global const. Audio can be checked by spying on `playSnd` and on `BaseAudioContext.prototype.createOscillator/createBufferSource`. Scratch scripts are NOT in the repo and are lost between sessions - rebuild them; they go stale when level indices or Riprova semantics change.
  `node --check` every `<script>` block first, then the smoke test. Real-time polling is flaky under CPU load.
- **Patch scripts:** edit `index.html` with a Python script that asserts each anchor appears exactly once, printing nothing but anchor counts; the owner's own Windows checkout is CRLF (read with `newline=""`, normalise `chr(13)+chr(10)`→`chr(10)` for multi-line anchors and convert back on write) — a Claude Code **cloud session's** checkout is plain LF instead (confirmed 2026-09-26): read/write with `newline=""` regardless so a script works either way, but skip the CRLF round-trip normalisation on an LF checkout. Whichever it is, `git diff --stat` before committing must show only the lines actually meant to change in `index.html` — a whole-file diff means a line-ending mismatch slipped in; stop and fix it, never commit it. Use raw strings (`r'''...'''`) for JS containing
  `\u00e8`-style escapes. Never print base64; embed art in the chunk that first draws it. Measure size deltas against `git show HEAD:index.html` (CRLF-normalised only if the checkout itself is CRLF).
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

### Skin art owed (§6 rule 11)
Frames a real skin doesn't cover yet (`manca` in `refs/skins/SKIN_COVERAGE.md`), tracked so the REL gate knows
what's an accepted, named gap versus a blocker. `wait-assets` until the owner (or a submission) supplies the art.
- **BK (Algidone) — Ferma Algidone! thrower frames** (13 keys: `alg_idle0-1`, `alg_angry0-1`, `alg_throw0-3`,
  `alg_eat0-2`, `alg_kick1-2`), added to the sheet in F4a2 (0.4_9). Grandfathered: BK already shipped without
  them before this rule existed — not a merge blocker, listed here per rule 11.
- **BK (Algidone) — Cinghiale frames** (6 keys: `boar_lato0-1`, `boar_su0-1`, `boar_giu0-1`), added to the
  sheet as real cells in F4c (0.4_10, option M from the 0.4_9 investigation). Grandfathered same as the
  Ferma thrower row above — BK shipped with no Cinghiale art before either rule or these frames existed, not
  a merge blocker. 19 keys total owed for BK today (13 + 6).

### Costumi da assegnare (F4b2, §5 procedure)
A skin submission approved and hardcoded into `SKINS` is **not** automatically given to any player — someone
has to decide how it's unlocked (a career milestone, a roadmap tile reward, a shop item, …), which is a
planning decision, not something Claude Code invents while embedding the submission (§5 step 5). This section
lists every embedded costume still waiting on that decision, so it isn't forgotten. Empty today — no skin
submission has been processed yet (F4b2, 0.4_12, only built the tool; REQ is the tile-10 reward skin, whose
unlock is already decided — see the REQ row in §10.4 — so it never lands here).

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

### 0.5 note — extras and cloud save
A synced save may refer to dev-added extra objects that exist only on another device (extras aren't synced). Devs only, harmless; revisit when extras become player-facing.

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
- [ ] If a frame/pose/animation was added or changed: F4a sheet, `SPRITE_INVENTORY.md`, `SKIN_COVERAGE.md`
      updated in this build; new `manca` gaps listed as "art owed" in the report and in §8 (§6 rule 11)
- [ ] Short patch note: what changed, how to test, what wasn't tested
- [ ] Commit `v0.4_NN: …`, push (Pages redeploys automatically)
- [ ] §10.3 chunk table: status updated for the chunk just delivered
- [ ] **REL only**: `SKIN_COVERAGE.md` regenerated against the release build; no `manca` on a frame added
      since the last stable release, unless the owner names that gap as accepted (§6 rule 11)

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
| F4a2 | Algidone's Ferma thrower frames on the sheet + skin hook, skin coverage (na/accordion/SKIN_COVERAGE.md), §6 rule 11, boar investigation (report only) | F4a | Sonnet · high | done (0.4_9) |
| F4c | Cinghiale skinnable, option M (6 baked frames): sheet row, `drawBoar` hook, coverage | F4a2, owner decided 0.4.5 before F4b | Sonnet · high | done (0.4_10) |
| F4b1 | Skin tool part 2a: sheet fixes (streak split, label sizing), «Parti da», import sheet, local preview | F4a2, F4c | Sonnet · high | done (0.4_11) |
| F4b2 | Skin tool part 2b: export the imported/staged skin as a developer submission package; remove `DEV_SKIN_TEST` | F4b1 | Sonnet · high | done (0.4_12) |
| F2a | Player login, flag off (`PLAYER_LOGIN`) — one login for everyone, invite-only, Account accordion | F1 | Sonnet · high | done (0.4_13) |
| REQ | Tile-10 reward skin (Uomo roccia) made with F4 | owner art + name | Sonnet · medium | next (0.4_16), wait-assets |
| B1 | Maze hitboxes around assets | screenshot / bug report | Sonnet · medium | wait-assets |
| F2b | Cloud save, flag off (`CLOUD_SAVE`) — `saves/{uid}`, rev transactions, conflict popup, backup | F2a | Sonnet · high | done (0.4_14, approved) |
| X1 | F2b fixes + resized-sheet check: Android back on the three popups, conflict card layout, «L'app ha ridimensionato il foglio» + LEGGIMI «Dal telefono», test_f1 flake investigated | F2b, F4b1 | Sonnet · high | done (0.4_15) |
| REL | Release "0.4.5": VERSION, CHANGELOG, DEVELOPERS.md, roll base to 0.4.5_N in §6/§7/§9, regenerate refs/screens/ and `SKIN_COVERAGE.md` (§6 rule 11 gate), tag v0.4.5, merge dev → main | all | Sonnet · low | todo |

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
| 2026-09-25 | F3c | Cancelled: file packages stay «Scarica pacchetto» + PR upload to `dev`; `firestore.rules` in the repo is the published version (no packages collection). Indicative remaining builds: F4a 0.4_8, F4b 0.4_9, REQ 0.4_10, B1 0.4_11, F2 0.4_12, then REL "0.4.5" (shifted 2026-09-26 after F4a2 slotted in: F4b 0.4_10, REQ 0.4_11, B1 0.4_12, F2 0.4_13; shifted again 2026-09-26 after F4c slotted in before F4b: F4b 0.4_11, REQ 0.4_12, B1 0.4_13, F2 0.4_14; shifted again 2026-09-26 after F4b split into F4b1/F4b2: F4b1 0.4_11 (done), F4b2 0.4_12 (done), REQ 0.4_13, B1 0.4_14, F2 0.4_15) |
| 2026-09-25 | F1 | No offline backup login: if Firebase is unreachable dev mode is unavailable (a session already logged in stays valid offline) |
| 2026-09-26 | F4a (report) | The Ferma Algidone! climber (Uomo roccia) already draws through `drawFace()`/`f0-2`/`fd*`/`fu*` (`faDrawPlayer`, confirmed in code) — already skin-hooked, no new frames or draw-path work needed before the REQ tile-10 skin. SPRITE_INVENTORY.md's item 18 ("Coccia climber, not built yet") is stale, describing an earlier, different plan; not edited this session (planning-side doc) |
| 2026-09-26 | F4a (report) | Reference cells built: roccia = the procedural up/down eating rock icon (2 cells); algidone = Cinghiale lato/su/giù via `drawBoar` (3 cells). Not pre-decided in the brief beyond "Cinghiale boar, up/down eat rock icon, any procedural climber pose, placeholders" — no procedural climber pose or other placeholder art exists to render, so nothing was added for those |
| 2026-09-26 | F4a2 | Algidone's Ferma Algidone! thrower (`FAIMG.alg_*`, 13 real frames, `alg_kick0` skipped) added as its own row on Algidone's F4a sheet; drawn via `drawSkinned(c,"algidone",pose.key,im,...)` in `faDraw`'s NPC block — wears Algidone's own equipped skin regardless of who's climbing. `loadSkinImgs()` now accepts a base image from `FAIMG` as well as `IMG`; `ensureFA()` re-runs `loadSkinImgs()` once `FAIMG` is populated (it lazy-loads, unlike `SPR`/`SPR2`) so a future skin's `alg_*` frames aren't silently dropped by a boot-time check that ran too early |
| 2026-09-26 | F4a2 | `SKINS.<id>.na` added (empty for GEKA/BK today). Coverage line in the Costumi accordion and `SKIN_COVERAGE.md` both compute X/Y and "mancano" the same way: the sheet's real frame keys minus `na`, checked against `SKINS.<id>.frames` |
| 2026-09-26 | F4a2 (report) | Boar investigation (report only, no code): `drawBoar(ctx,X,Y,c,o)` is 100% procedural canvas primitives (rects/ellipses/triangles), 3 direction variants (side, mirrored for left; up/back; down/front), continuous sine-based leg-swing/bob/shake, no tint hook, no `IMG` reference. Effects that live outside it and would stay procedural regardless: the stress bar + "STORDITO"/"STRESS N%" text, the stun sparkle stars, the wall-smash dust particles (`G.parts`, shared with other effects), the shared blue ability-duration bar. Proposal: bake fixed base frames per direction from `drawBoar` at a neutral pose (same technique as today's reference cells) and hook them the same way as every other character (`drawSkinned`, base frame = current art, so nothing changes with no skin equipped); keep bob/shake/motion-blur/effects as procedural transforms around the sprite, unchanged. Sizes: **S** = 1 frame x 3 directions (3 total, loses the walk animation — a visible downgrade); **M** = 2 frames (both leg-swing extremes) x 3 directions (6 total, keeps a basic walk cycle, similar authoring cost to one existing sheet row); **L** = 3-4 frames x 3 directions (9-12 total, closest to today's continuous motion, highest cost). **Recommended: M.** Decision pending as chunk F4c (owner picks 0.4.5 or 0.5) |
| 2026-09-26 | F4c | Owner picked option M (6 frames: 2 leg-swing phases x 3 directions) from the F4a2 boar report. Ships in 0.4.5, before F4b (F4b's indicative build shifted to 0.4_11) |
| 2026-09-26 | F4c (report) | Implementation detail not pre-specified in the brief: since `drawBoar` has no static PNG to size/anchor a base frame against, each of the 6 frames is baked (once, at boot) by rendering `drawBoarBody` to a scratch canvas, measuring its own alpha bounding box, then re-rendering into a tightly-cropped final canvas (6 px padding) — `canvas.boarAx/boarAy` (the origin offset) plays the role `skOx/skOy` plays for a real PNG. Baked at `BOAR_C=120` (same scale the K1b reference cells used); displayed at runtime scaled by `c/BOAR_C` so procedural and framed rendering stay proportional |
| 2026-09-26 | git hygiene | **Base64 rule made stricter** after it was violated in two prior sessions (a bare `grep`/`git diff` against `index.html` printed base64 into the transcript) and once more in this one (a regex scan run directly on `index.html`, mid-session, before the stricter rule below was internalised — caught and flagged to the owner immediately, no base64 kept in any committed file). New standing instruction (from the owner, cloud-session preamble): never run `grep`/`cat`/`sed`/`head` — or any ad hoc text scan — on `index.html` directly; always build a stripped copy first (strip lines over ~2000 chars) and search only that; pipe every command whose output could touch `index.html` (`git diff`, `git show`) through `cut -c1-300` as a backstop. Applied throughout this session's own tooling from that point on |
| 2026-09-26 | git hygiene (correction) | The "two prior sessions" above were the **0.4_9 and 0.4_10 sessions** specifically (not left vague) — base64 leaked into a session's own tool output in both, confirmed by the owner. F4b1 item 0 turns the ad hoc "build a stripped copy" workaround into a real committed tool, `tools/strip_index.py` (redacts every run of 200+ base64 characters to `<B64 n>`, prints only the output path/size), mandatory as the first step of every session from now on (CLAUDE.md §6) |
| 2026-09-26 | F4b1 (brief) | F4b split into F4b1 (0.4_11, this build: sheet fixes + «Parti da» + import + preview) and F4b2 (0.4_12, next: export the imported/staged skin as a developer submission package, remove `DEV_SKIN_TEST`) — one chunk was too large for the one-chunk-one-build rule once the 0.4_10 phone-test fixes were folded in first |
| 2026-09-26 | F4b1 1a | The Cinghiale motion-blur streak moved from "baked into the 6 base frames" to its own effect (`drawBoarStreaks`, called by `drawBoar` in the same draw position, for the procedural body and a skinned boar alike) so a skin's frame doesn't inherit someone else's streak baked into the reference art, and so the frame's own bounding box could tighten to the body it actually contains. No-skin rendering stays pixel-identical (same golden-hash test, unchanged) |
| 2026-09-26 | F4b1 1b | Label sizes on the ×4 sheets (frame labels ≥28px, header ≥48px) were the owner's own phone-test finding, not a design choice made in this session — implemented by growing the reserved layout constants (`SKIN_LBLH`/`SKIN_SECLBLH`/`SKIN_HDRH`) to fit the bigger fonts; this reflows every page (more/less content per page) but never changes what a label says or where the pink cell border sits |
| 2026-09-26 | F4b1 2 | «Parti da» reuses the export path's own draw calls (`drawSkinLayer`) rather than a separate rendering path, so GUIDE with a real skin selected is guaranteed to show exactly what the game itself would draw — never a second implementation that could drift out of sync |
| 2026-09-26 | F4b1 3 | The Python (`cut_from_cells.py`) and JS (`index.html`, "Carica costume") cutters are **one algorithm, not two**: identical premultiplied-alpha box-filter arithmetic with proportional source slices and "round half up" rounding, tested to give byte-identical output on the same input (`tools/fbstub/test_f4b1.py`). Replaces the Python side's old `Image.resize(..., LANCZOS)`, which was never guaranteed to match a browser canvas's own resampling — the earlier "close enough" assumption is retired |
| 2026-09-26 | F4b1 4 | The imported-skin preview (`SKIN_IMPORT_PV`) is deliberately in-memory only, by construction (a plain top-level `let`, never assigned into `S` or written to `localStorage`/`IndexedDB`): there's nothing to clear on reload because nothing was ever saved, and it's explicitly reset on logout and on the dev-mode-off toggle so it can never leak into a state the player (or a future session) would see unexpectedly |
| 2026-09-26 | F4b1 (report) | A sheet exported by 0.4_10 (before the label-size fix) is correctly rejected by «Carica costume»'s size-matching check — its page dimensions no longer match this build's `skinLayout()` output, so it fails with the same «Foglio di un'altra versione» error as any other stale sheet. This is intended (item 1b's own note: "the sheet from 0.4_10 is superseded"), not a bug |
| 2026-09-26 | F4b2 (brief) | F4b1's phone test passed, approved as-is. F4b2 built as briefed: cutter/margin-anchoring fix, exporting the previewed skin as a submission, `DEV_SKIN_TEST` fully removed |
| 2026-09-26 | F4b2 1 | The margin-rounding fix moves the sheet layout again (roccia 1804×3400→1804×3410; algidone's 2nd/3rd pages 3816×3408/2530→3816×3420/2534) — an 0.4_11 sheet now also fails the size-match check, same as a pre-F4b1 one. The root cause wasn't the box filter's arithmetic (already premultiplied-alpha, already correct) but the *geometry*: a cell's margin was rounded to the nearest whole pixel, not to a whole ×4 block, so a cell size could end up not divisible by 4 whenever a native frame's width/height was odd — the F4b1 "proportional slice" generalisation was a correct-but-unnecessary workaround for that self-inflicted misalignment. Fixing the margin (round UP to a ×4 block) makes every cell exactly divisible by 4 again, so the box filter's own arithmetic (unchanged) always averages a clean, non-overlapping native block — never a blend across what should be two separate source pixels. The generalisation is kept (harmless: it degenerates to identical whole-block slices whenever the size is an exact multiple, which is now always) |
| 2026-09-26 | F4b2 2 | `expSpriteItems()` (an F3b-era hook that always returned `[]`, "for F4") is now real for skins; `EXP_LIM.sprite` (200 KB) was undefined until this build — the sprite/skin size check in `expBuildPackage` had silently been a no-op the whole time it was unused, since `size>undefined` is always false in JS. Fixed as part of wiring skins through it, not a separate bugfix build (no shipped build ever produced a sprite item, so nothing regresses) |
| 2026-09-26 | F4b2 2 | The export dialog's skin frame count uses the *actually-exportable* item count (`pv.items` post-filter), not the raw size of `SKIN_IMPORT_PV.frames` — an «invariato» frame is present in the preview (so the maze/menu/etc. still show it) but correctly excluded from what «Scarica pacchetto» ships, and the count shown matches that |
| 2026-09-26 | F4b2 5 | `activeSkin()` is kept (not deleted) as a one-line passthrough to `skinImg()` after `DEV_SKIN_TEST` removal, to avoid touching its call sites (`drawBoar`, `drawSkinned`); the two Personalizza-page dev-testing fallbacks that used to check `DEV_SKIN_TEST` (reach the page / show its button without owning a real skin) now check `SKIN_IMPORT_PV` instead, same behaviour, new mechanism. `DEV_SKIN_TEST`'s tests in `test_f4a.py` were migrated to set `SKIN_IMPORT_PV` directly with a synthetic semi-transparent tint frame (a solid opaque one made overlay and replace pixel-identical, since overlay's base layer became fully hidden underneath it either way — caught while migrating, not a product bug) |
| 2026-09-26 | F4b2 (report) | `tools/fbstub/test_f3b.py` needed the same `launch_browser()` Chromium-revision fallback already used by the newer test files (it predated that pattern) to actually run in this sandbox — added since the brief names it as a required-green suite; unrelated to any F4b2 code change |
| 2026-09-26 | F4b2 | Owner's phone test of 0.4_12 passed, approved as-is |
| 2026-09-26 | F2a (brief) | F2 split into F2a (0.4_13, this build: player login only) / F2b (0.4_14: cloud save) — same reasoning as the earlier F4b split, kept as two reviewable chunks |
| 2026-09-26 | F2a | One login for everyone (not a separate player-only flow): the same Firebase session and `@mangiasassi.invalid` mapping as F1, with the existing `devs/{uid}` role lookup deciding dev vs player after sign-in — an account either has a role (dev, exactly as F1 today) or doesn't (player, new `playerAcct` session). Invite-only: no sign-up UI, the owner creates every account in the console, same as dev accounts |
| 2026-09-26 | F2a | New flag `PLAYER_LOGIN`, next to `BUG_PLAYERS`, both still off. While off, the new Account accordion is reachable only by a dev with dev mode on (`devOn&&!!role`), so the login flow itself can be tested before it's shown to real players; a logged-out visitor or a plain player sees nothing new this build |
| 2026-09-26 | F2a (report) | `submissions/master/2026-09-25-testi/` (the owner's F5 test package, flagged for rejection at the top of this brief) was rejected and recorded in the newly-created `submissions/PROCESSED.md` (`· rejected — owner F5 test ·`), committed on its own before the F2a build, per §1b |
| 2026-09-26 | F2a (report) | Pre-existing, environment-specific test flake found while re-running `test_f1.py` in this sandbox: its "Esc closes the login" check fails intermittently. Confirmed unrelated to F2a by re-running the same (already-fixed-for-this-sandbox) test file against the untouched 0.4_12 `index.html` (`git stash`) — same failure. Left as-is (out of scope; not introduced by this build) |
| 2026-09-26 | F2a (report) | `tools/fbstub/test_f1.py`, `test_f5.py`, `test_f6.py` and `tools/screens/capture.py` needed the same `launch_browser()` Chromium-revision fallback already used by the newer test files, to actually run in this sandbox — environment-only, unrelated to any F2a code change. Used `capture.py`'s existing `dev=True` scenario machinery to take a real screenshot of the new `opt-generali-account` screen (only reachable with a dev session while `PLAYER_LOGIN` is off) rather than leaving the row without one |
| 2026-09-26 | F2a | Owner's phone test of 0.4_13 passed (signed in as master and as prova1 on two browsers, login OK), approved as-is |
| 2026-09-26 | F2b (brief) | Cloud save built behind `CLOUD_SAVE=false`: stable makes zero save calls; the dev site tests it through the local toggle `mgs_cloudtest_dev` (Account accordion, also shown to a player session on the dev site only). Doc `saves/{uid}` / `saves/{uid}_dev`, fields `data`/`rev`/`ts`/`ver`, every upload a `runTransaction` on `rev`; uploads the stored save string (never live `S`), never during SIM/Sblocca tutto/dev runs/`PR.test`; conflict popup «Due salvataggi diversi»; one backup slot; apply only from the menu |
| 2026-09-26 | F2b | `firestore.rules`: the old placeholder `match /saves/{uid}` (read/write own doc, no validation) is **replaced** by the brief's `match /saves/{docId}` block, not kept beside it — Firestore ORs overlapping matches, so keeping both would have let any write to `saves/{uid}` skip the new field/size/rev checks. devs/bugs/edits untouched |
| 2026-09-26 | F2b | Dev-only data never synced: `tiles`, `ov`, `extra`, `gtext` (sections, names/colours/scales, extra objects, texts — the "modifiche locali") and the SIM fields `sim`/`realP`/`realQuick`/`realAch`; applying a cloud copy keeps this device's own `tiles`/`ov`/`extra`/`gtext` and drops the SIM fields. Everything else in `mgs_v1` is synced (progress, `opts`, `quick`, quote rotation `qd`/`qach`/`qlast`, popups/roadmap state). `mgs_v1`'s structure is unchanged |
| 2026-09-26 | F2b (not in the brief, flagged) | (1) New local key `mgs_v1_ts` (`_dev`): time of the last real `persist()`, the only way to show the device card's «date of the save» (localStorage has no timestamps); a device whose save predates 0.4_14 shows «Data sconosciuta» until its next save. (2) «Decidi dopo» → status «Cloud: in attesa della tua scelta»; «Sincronizza ora» (an explicit request) re-asks. (3) A conflict whose two copies have the same hash is resolved silently (M written, no popup) in every case, not only at first sync. (4) cloud rev lower than M.rev (not covered) → conflict popup, like an unexpected transaction rev. (5) An automatic apply deferred mid-run re-decides at the menu if the run changed the save (→ popup), instead of silently discarding the run. (6) `wipeData()` also clears `mgs_cloud`, the backup and `mgs_v1_ts` — otherwise, after «Cancella dati locali» and a login, the empty save would be uploaded over the cloud progress as a plain dirty change |
| 2026-09-26 | F2b | Owner's phone test of 0.4_14 passed (rules published in the console, cloud save works), approved. All 7 decisions of the 0.4_14 report accepted: `mgs_v1_ts`, «Decidi dopo» status, identical copies resolved silently, lower cloud rev → popup, deferred automatic apply re-decides after a run, «Cancella dati locali» clears the sync state, no `fbLoad` change |
| 2026-09-26 | X1 (brief) | 0.4_15: Android back on the bug / «Modifica testo» / conflict popups = their own cancel; conflict card name and level on separate lines; resized-sheet error in «Carica costume» (abs(sx−sy) ≤ 0.5%, factor ≠ 1; same width + other height stays «altra versione»; no auto-rescale) + LEGGIMI «Dal telefono»; test-only fix for the test_f1 flake unless it needs game code |
| 2026-09-26 | X1 1 | Back is routed through the existing shared `BUG` guard (`if(BUG&&BUG.close){BUG.close();return}` at the top of the `mgback` handler): the three popups already set `BUG.close` to their own cancel, so one line covers all three and every other back path is untouched. The Android wrapper's sources aren't in the repo; tests dispatch `mgback` on `window`, the event the page listens for |
| 2026-09-26 | X1 (report) | The conflict card title «Su questo dispositivo» and the date line «Salvato il … alle …» still wrap onto two lines at 390 px (only the name/level wrap was in scope); proposed as an extra, not changed |
| 2026-09-26 | X1 4 (report) | test_f1 "Esc closes the login" fails deterministically here (6/6), not by timing: after a failed login attempt `loginModal`'s `go_()` sets `#lk.disabled=true`, focus falls to `<body>`, and the Esc listener lives on the modal element (`m.addEventListener("keydown",…)`), so the key never reaches it — the global keydown handler ignores a modal with more than one button. Real behaviour on desktop: after a wrong password Esc does nothing until the user clicks back into the form. Fixing it needs game code (e.g. listen for Esc at document level while the login modal is open, or refocus the field after an error); per the brief not done, test left as-is |

**Built-in audio slots** (filled by A-chunks):

| Slot key | Source submission | Build |
|---|---|---|
| | | |

v0.4 plan + decisions log: docs/releases/0.4.md
