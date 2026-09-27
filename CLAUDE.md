# CLAUDE.md — Mangiasassi

Permanent project context for Claude Code. Read it fully at the start of every session.

## SESSION HANDOFF
**2026-09-27: the owner has no local VS Code/Windows checkout for now — every session from here runs as a Claude Code cloud session** (no exception; the "may run as cloud" wording below is now "will run as cloud" until this note is removed). The owner reviews builds only via the live `/dev/` Pages site on their phone, never local files. Practical effects on a cloud session, already covered below but worth restating: the checkout is plain LF (§6 practical notes — skip the CRLF round-trip, still read/write with `newline=""`); git identity/remote are already configured by the harness; everything else in this file (branch, chunking, testing, commit format) is unchanged. This note was added right after recovering from a real incident (below) — a cloud/local difference did not cause it, but it's a reminder that nobody but the next session will see a bad patch before it's pushed, so the safeguard below matters even more now.

**Recovered 2026-09-27**: the 0.4.5_11 (S1) docs patch (commit `1eb6884`) used an unbounded `s.index(nl, i)` to replace the SESSION HANDOFF line and silently deleted ~186 lines (§0 Division of labour through most of §4 Code map) — `git diff --stat` was checked but the insertion/deletion counts weren't sanity-checked against what a one-line edit should look like, so it shipped. Fixed in `1258a71` by restoring from the last known-good commit and reapplying just the two intended edits. **Rule going forward**: any `s.index(a); ...; s.index(b, i)`-style patch to CLAUDE.md/CHANGELOG.md must bound the replaced span with an anchor on *both* ends (not just search forward for the next separator), and `git diff --stat` must be eyeballed against the expected size of the edit — a doc tweak showing 100+ line churn is a stop-and-investigate signal, not something to push through.

0.5 plan in §10. Built and phone-tested: 0.4.5_12 (U4 feedback: Algidone rank names), 0.4.5_13 (M1a: map classes/GIRONI schedule/3-4-5 ghosts/level-10 lock removed), 0.4.5_14 (dev jump to any girone), 0.4.5_15 (M1b: girone bonus multipliers). 0.4.5_16 (5th-ghost wait fix + dev girone readout): the fix works — all 5 ghosts now present on large maps — but opened **B2 «fantasmi sovrapposti»** (ghosts overlapping/not visually separate while moving, §8, §10.9). Next: plan and fix B2, then E1 (Opus 5.5 / high) — ghost stage framework. B1 waits for the owner's screenshot. Dev-branch builds are `0.4.5_N`. Sessions may run as Claude Code cloud sessions: then the brief starts with a cloud preamble; follow it.

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
yellow when ready. **While an ability is active the player is immune to ghosts (both Acciaio and Cinghiale).** Ability exit buttons: "basta ti prego" (roccia) / "basta basta" (Algidone).

### Core mechanics
- 100-level progression per character, separate careers, XP, unlockable assets, ranks (`RANKS`: Recluta →
  Re delle pietre), hidden **limiter** on earnings (`limiter(l)`), `expNeed(l)` with a harder curve from lv 60.
- Three difficulties (Facile / Media / Difficile) with hidden multipliers — **harder rewards more**.
- Power-up reverses enemy behaviour for 15 s. After losing a life the maze gives **5 s respawn protection shown as an aura** in the character's power-up colour (`RESPAWN_INVULN`; Ferma keeps its own 2 s).
- **Gironi** (rounds): each girone plays a themed maze map of a class — S (grid mi 0–4, 3 ghosts), M (6 themed maps, 4 ghosts) or L (4 themed maps, 5 ghosts) — picked at random within that class (`GIRONI` schedule, `gironeSpec(stage)`, `pickMap(stage)`, §4). Gironi 1–8 follow a fixed class/ghost-stage schedule; from girone 9 the class is random (S 20% / M 40% / L 40%) and ghost stages keep climbing. After girone 5: Nuovo gioco / Hardcore split.
- **Terrain** (only on the 10 extra maps and the 2 dev maps — the 5 standard themed maps have none): water and lava drawn as sinuous generated *streams along corridors* (not filled areas).
  Lava = 60 % speed, kills after 3 s of contact. Water = 75 % speed, extinguishes burning 4× faster, with
  steam hiss + bubbles when entering while burning. A map-hardening pass stops lava blocking pellets.
- **10 extra hand-authored maps** are the M/L classes above, reached through the girone schedule from girone 3 on (no separate unlock — the level-10 achievement `g4` still gives sordi/XP, just not a map lock); big maps cap pellets at 130 spread evenly, and use a following camera.
- **35 achievements** across 5 categories (incl. Minigiochi, 5 entries since «Batti il professore», 0.4.5_9); 50 cycling "Partita finita" quotes per character, some
  achievement-triggered.
- Desktop scaling supported up to 3440×1440; Enter/Esc shortcuts on popups.

### Mini-games (all implemented — do not rebuild)
1. **Mangiaroccia** — the core maze game. `screen="game"`.
2. **El Gamblador** — blackjack after girone 5. `screen="bj"`, all `bj*` functions. Sprite-animated dealer
   whose cigarette smoke tracks per-frame tip positions; streaming wood table borders, props on the rails,
   centred cards, 2×2 menu grid, raise/stake logic with a chip stack and ±100 buttons, dealer lines.
   "Puntata" and fiches stay on the **left** (shifted slightly right). "Non ora" is hidden only on the **first-ever
   table** (lifetime counter `S.p.gam.visits`, never reset), not once per run.
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
- **Map classes / girone schedule (M1a, 0.4.5_13; dev-jump #jgN/#jgGo 0.4.5_14; bonus M1b 0.4.5_15; 5th-ghost wait fix + dev readout 0.4.5_16)**: `MAP_CLASS` (S/M/L by grid width, next to `STDMAPS`), `CLASS_GHOSTS`, `mapClassOf(mi)`; `GIRONI` (gironi 1-8, `{cls,ghosts:[stage,…]}`), `stagesForClass(cls,stage)` (girone 9+ rule), `pickClassForGirone(stage)`, `gironeSpec(stage)` (one class draw, reused for both the map class and the ghost stages — never two independent random draws for the same girone). `pickMap(stage)` (was `pickMap(prev)`, level-10-gated) picks inside the class, no immediate repeat (`G.lastMi={S,M,L}`, per-run, in the quicksave, migrated on an old one); dev UI `#jgN`+`#jgGo` (§4 "Dev mode") go through the same `devJump(n)`. `resetActors` sizes/tints/stages `G.en` from `mapClassOf(G.mapi)` (3/4/5 ghosts; the 5th reuses a `MET.ghosts` start + the difficulty's average chase; **0.4.5_16**: its `wait` is the 4th ghost's own wait **+ a flat 2.5 s**, not re-scaled by `dfc().wait` like ghosts 1-4 are — a difficulty-independent gap so it's never more than 3 s, fixing a case where a death (which resets every ghost's `wait`, unchanged pre-M1a behaviour) kept happening before the naively-extended per-index formula's longest waits ever elapsed). `mapsUnlocked()` deleted. **Dev girone readout (0.4.5_16)**: `#jgro`, added to `buildGameDOM`'s markup only when `devOn` (absent from the DOM otherwise), a corner line over the canvas (`position:absolute`, `pointer-events:none`) updated by `updateHud()` — «G8 · L · 5 · st 1,1,1,3,3» (girone · class · ghost count · stages). **`GIR_BONUS`** (`{cls:{S,M,L},st2,st3}`): at girone clear, `mult` from the just-finished girone's own `G.en[].stage` (no fresh draw); `G.girPts` (this girone's own points: pellets/ghosts/the +200 clear bonus, reset at every girone start, carried by the quicksave, migrates to 0 on an old one) drives `bonus=round(girPts*(mult-1))`, added once to `G.score` before `finishRun`'s existing limiter/`DIFF.mult`/`.7` (unchanged); shown as a second banner line under "Ripulito!" (`G.girBonusTxt`, only when `bonus>0`). Tests: `tools/fbstub/test_m1a.py`, `tools/fbstub/test_jg.py`, `tools/fbstub/test_m1b.py`.
- **Blackjack**: `bj*`, entry `startGamblador`.
- **Professor**: `prIntro → prIntroYes → prBattleStart`; scenes `prSceneProf, prSceneKick, prThrowOut, prPond,
  prSceneBattle`; dev `prTest, prTestKick, prTestBattle, prDevPanel`.
- **Battle**: `PB_LIB/pbLib` (moves), `pbMon, pbBattle, pbDamage, pbTurn, pbAI, pbAct`, anim `pbAnimMove, pbFxDraw`,
  UI `pbPanel, pbBox, pbCommand, pbFight, pbEnding`, sim `pbSim`. Each fighter currently has 4 fixed moves.
- **Achievements**: `ach, unlockAch, renderAch, bindAch`.
- **Toast (0.4.5_3)**: one self-contained module `TOAST` (+ `toast(msg)` wrapper): container `#toasts` outside `#root`, queue of one, fade, `pointer-events:none`, 2.5–5 s, top-centre under the top bar (moves onto the bar band if it would cover a control, `TOAST.place`), compact and held while the maze/Ferma run is in play (`TOAST.hold`). The achievement popup `#ach-pop` and the crash overlay `#errbox` are separate on purpose. Tests: `tools/fbstub/test_toast_diag.py`.
- **Diagnostics (0.4.5_3)**: self-contained `DIAG` (defined right after `store`, before everything else): 200-entry ring buffer in `mgs_diag` (`_dev` on the dev site, ≤50 KB, survives reloads), `DIAG.log(kind,msg)` / `DIAG.clean()` (masks emails and 28+ char ids — never log uid/email/tokens); hooks on window errors, rejections, console.error/warn, auth/`fbVerify`, cloud outcomes, reloads, screen changes, bug-icon taps. UI: Opzioni › Sviluppatore › «Diagnostica». Dev bug reports get `meta.diag` (last 30), player reports nothing.
- **Game chooser (0.4.5_11)**: `RUN_GAMES` / `RUN_START` / `newRun(o)` (next to `tileAction`): Uomo roccia's «Nuovo gioco»/«Hardcore» asks Mangiaroccia or Ferma Algidone! (`enabled:false` = «In arrivo» until FR1); Algidone starts the maze directly; `G.game` (`maze` default, saved in the quicksave) drives `nextMinigame()`. Tests: `tools/fbstub/test_s1.py`; other tests start runs through `tools/fbstub/gp.py` `pick_maze`.
- **Arrow navigation + ranks (0.4.5_10, names replaced 0.4.5_12)**: `KNAV` (self-contained, next to `closeModal`): capture-phase keydown, ring class `.kf` on the current menu tile / popup button, Enter clicks it, any pointer/touch press clears it. `RANKS` (Uomo roccia, 11 entries 1…100) / `RANKS_ALG` (Algidone, owner's own gym-themed names as of 0.4.5_12, **10 entries 1…90** — the 90 rank covers through level 100, no 100 key); `rankTable(ck)`, `rankOf(l,ck)` (table-length-agnostic, no change needed). `careerModal`'s milestone rows (was hardcoded `[1,10,…,100]`) now iterate `Object.keys(rankTable(charKey()))` directly — any table length works, no "undefined" row. `musicWanted` now includes `ach`, `road`, `cust`. Tests: `tools/fbstub/test_u4.py`.
- **Protected cells (0.4.5_4)**: `protectedCell(x,y)` = outer ring, tunnel rows, ghost house (`MET.house`) + 1-cell margin (walls, door); `smashable()` uses it. Standalone — Super Panino (E5) reuses it. Tests: `tools/fbstub/test_p1b.py`.
- **Export (F3b, format v2, docs/submissions-v2.md)**: `exportDialog` (two actions; both need a Firebase dev session, otherwise disabled with "Accedi per inviare"); texts/colours/scales: `expTextChanges` (with the built-in `before`) → `expTextEdits` → `expSendTexts` → `editSubmit`/`editPost` (Firestore `edits`, fields exactly as the rules) with the local queue `mgs_editq` (`editQueue`/`editFlush`, flushed like the bug queue) and the sent marks `mgs_editsent` (`expSentState`: new / queued / sent, both keys `_dev` on the dev site); audio + sprites: `expBuildPackage` (`expAudioItems`, `expSpriteItems` = hook for F4, `expBuiltinB64`, `expSha256`, `expZip`) → ZIP `submissions/<acct>/<date>/`. `exportTargetsMd` (v1 target list) is kept but no longer exposed; `window.mgExport` is gone. Tests: `tools/fbstub/test_f3b.py`.

### Dev mode
Tap **"Build locale" five times** in Options to open the login modal (username + password, **Firebase Auth**; the game appends `@mangiasassi.invalid`, §10.2). The role comes from Firestore `devs/{uid}.role` (`master`, `dev1`…`dev5`): internally `role` is `'master'` or `'dev1'` (every dev1…dev5 behaves as `dev1`, master-only = Sblocca tutto + menu/GAM music uploads), `acct` keeps the account name (shown in the Account accordion, default developer name of the export). `isMaster()` is the helper.
The SDK (`fbLoad`, v12.19.0 from gstatic) is loaded with `import()` only when the login modal opens or when the dev cache says a session exists: the game never waits for it (8 s timeout = offline). Two separate Firebase sessions per site (app name `mgs` / `mgs_dev`). Cache `mgs_dev` (`mgs_dev_dev` on /dev/) = `{role,acct,fb:true,devOn}`: restored at load, verified in the background (`fbVerify`: no user / role removed → dev off + SIM off; unreachable → the session stays valid). A cache without `fb:true` (old local login) is cleared. `file://` builds cannot log in.
Developer options must be **completely invisible** when the dev toggle is off; Sblocca tutto ends with dev mode. Dev jump/map runs, `PR.test` battles and Ferma tests save no progress and never set real unlock flags (`seen`, achievements). Headless tests: `tools/fbstub/` (stub SDK + `test_f1.py`; never real credentials).
**Jump to any girone (0.4.5_14)**: next to `#jg4`/`#jg7` (kept, unchanged) in the «Salta al girone» accordion, `#jgN` (number, 1-20) + `#jgGo` call `devJump(n)` clamped in the click handler; `devJump` already ran the girone's real spec through `pickMap(n)`/`resetActors` (M1a), so no separate wiring was needed. Tests: `tools/fbstub/test_jg.py`.

### Player login (F2a, flag off)
`PLAYER_LOGIN=false`: one account, one login for everyone, same Firebase session/mapping as the dev login above (`@mangiasassi.invalid`, invite-only, no sign-up UI — the owner creates accounts in the console). `plLogin(user,pass)` does the identical sign-in + `devs/{uid}` role check as the dev flow: a role found is a dev, handled exactly like today's dev login (`role`/`acct` set, `devOn` untouched); no role → a **player** session (`playerAcct`, a plain username string or `null`). The secret 5-tap dev modal (`loginModal()`) is untouched and stays the only way in for a dev with dev mode off. Player session state mirrors the dev one: `PLAYER_KEY` (`mgs_player`/`mgs_player_dev`), `persistPlayer()`, restored synchronously at boot from cache, verified in the background by `plVerify()` (same pattern as `fbVerify`: user gone → logged out, unreachable → stays). `bugPlayerSession()` (the F2 hook, previously always `null`) now returns `!!playerAcct` for real; `canReport()` stays false for players while `BUG_PLAYERS` is off, so no bug icon. A player never reaches dev UI, Sblocca tutto or SIM. UI: Opzioni › Generali › «Account» accordion (`plAccountHTML()`, in-universe Italian: «Accedi con l'account che ti ha dato El Cipro», F1's own «Cambia password» fields reused as-is). While the flag is off the accordion only renders for a dev with dev mode on (`devOn&&!!role`, so the feature itself can be tested); a logged-out visitor or a plain player sees nothing. Screen id `opt-generali-account` (falls out of `screenId()`'s existing `optOpen.gen`-based case for free). Tests: `tools/fbstub/test_f2a.py`.

### Cloud save (F2b, flag off)
`CLOUD_SAVE=false` (next to `PLAYER_LOGIN`/`BUG_PLAYERS`). `cloudOn()` = a Firebase session (dev `role&&acct` or `playerAcct`) AND (`CLOUD_SAVE` OR (dev site AND the local test toggle `mgs_cloudtest_dev`, «Salvataggio cloud (test)» in the Account accordion)); stable with the flag off makes zero save calls and shows no cloud UI. Doc `saves/{uid}` (stable) / `saves/{uid}_dev` (dev site), fields exactly `data`/`rev`/`ts`/`ver` (rules in `firestore.rules`); every upload is a `runTransaction` (`cloudUpload`) that re-reads the doc, refuses a newer `ver` (`verCmp`: numeric base first, then `_N`) and writes `rev`+1 only if the cloud rev equals the local base rev, otherwise → conflict. What is uploaded is the string `persist()` wrote (`cloudLocal()`: SIM copies resolved to `realP`/`realAch`/`realQuick`, then `CLOUD_DEVONLY` = `tiles`/`ov`/`extra`/`gtext` and `CLOUD_SIMF` = `sim`/`realP`/`realQuick`/`realAch` removed, keys sorted by `cloudCanon` so equal content = equal hash `cloudSum` on every device). Local keys (`_dev` suffix on the dev site): `mgs_cloud` = `{uid,rev,sum,dirty,ts}` (last synced copy; `persist()` → `cloudOnPersist()` marks `dirty` when the real save's hash differs), `mgs_v1_cloudbak` = `{data,from,ts,summary}` (one backup slot), `mgs_v1_ts` = time of the last real `persist()` (the date on the device card). Sync (`cloudSyncRun`, via `cloudStart`/`cloudSync`): after login (`loginModal`, `plLoginGo`) and at boot after `fbVerify`/`plVerify`; first sync per uid vs same uid rules as the F2b brief (`saveIsFresh()`); `cloudApply` never reloads mid-run: `CL.pend` waits for `render()` on a menu screen (`cloudPendCheck`, `cloudCanApply`), and an automatic apply re-decides if the local save changed meanwhile (an explicit «Usa questo» on the cloud card applies anyway, the device copy goes to the backup). Uploads (`cloudPush`): debounced 30 s trailing after a real persist (`cloudArm`), immediate at `finishRun` and on `pagehide`/`visibilitychange` hidden (`cloudFlush`, max once per 10 s, listeners registered after the game's own persist-on-hide); never while `cloudBlocked()` (SIM/Sblocca tutto, `G.dev` runs, `PR.test`, Ferma tests). Offline/network error → status «in attesa di rete», `dirty` kept, retried on `online`/next trigger/next start; permission error → `CL.stop` until next start/login. Conflict popup `cloudConfShow()` (screen id `cloud-conflict`, freezes + blocks keys through the shared `BUG` guard, Esc = «Decidi dopo» → `CL.later` until next start; «Sincronizza ora» re-asks; each card puts the character name and «Liv. N» on separate lines since 0.4_15). **Android back (0.4_15)**: the app's back button reaches the page as the window event `mgback`; its handler first checks the shared `BUG` guard, so with the bug popup, «Modifica testo» or the conflict popup open, back = that popup's own cancel (`BUG.close`: Indietro / Annulla / «Decidi dopo») — popup closed, freeze released, `BUG=null` (the capture key handler goes inert), nothing else in `mgback` changed. Account accordion (`cloudAccHTML`, shown also for a player session on the dev site): status line `#clst`, «Sincronizza ora» `#clsy`, test toggle `[data-clt]`, «Ripristina backup» `#clrb` (dev site only, swaps backup and save, marks dirty, reload). Logout (`fbDrop`, `plLogout`, `plVerify` drop) → `cloudReset()` clears `mgs_cloud` only; `wipeData()` → `cloudWipe()` also clears the backup and `mgs_v1_ts`. Applying/restoring sets `CLOUD_LOCK` so no `persist()` (e.g. the pagehide one) overwrites the new save before the reload. **0.4.5_2**: the reload goes through `cloudReload(msg)` (screen + open accordion in `sessionStorage` `mgs_resume`, read by `cloudResumeBoot()` at boot) so the user returns to Opzioni with a toast, never the splash question; `cloudWrite`/`cloudBackup` verify the write landed (full storage → nothing overwritten, toast «Spazio insufficiente»). Tests: `tools/fbstub/test_f2c.py`. Tests: `tools/fbstub/test_f2b.py` (stub keeps `saves` in localStorage `__fbstub_saves` and checks writes like the rules).

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
.github/workflows/             pages deploy + validate-submission + bugs-export (bugs-export.yml lives on BOTH main and dev — main is needed for the schedule/manual run — and the two copies must stay identical) + tag-release (main only: tags + publishes a release once VERSION on main is a bare release version)
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
3. **One chunk → one build → one commit** (`v0.4.5_NN: short description`). Bump `const VERSION="0.4.5_NN"` every time
   (numbering switched to `0.4.5_NN` at the v0.4.5 release, after `0.3_NN` → `0.4_NN` at v0.4; the release build itself is bare `"0.4.5"`,
   the next delivered build is `"0.4.5_1"`, then `"0.4.5_2"`, and so on — see §7).
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
    existing skin — added to §8 "Skin art owed" (status `wait-assets`). **Release gate** (§9): regenerate
    `SKIN_COVERAGE.md` at release time; any `manca` on a frame added since the last stable release blocks the
    merge to `main` unless the owner accepts that specific gap by name. Grandfathered since before this rule
    existed (listed in §8, not blocking): BK on the Ferma Algidone! thrower frames, BK on Cinghiale.

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
- Each chunk: bump `const VERSION` **and the root `VERSION` file together** to `0.4.5_N`, CHANGELOG entry with size delta, commit, push to `dev`.
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

| Range | Content |
|---|---|
| 0.4_1 → 0.4_15 | v0.4.5 release: DEV tools — F1 Firebase dev login, F6 bug reports + daily export/triage, F3 submission format v2 (Invia testi + Scarica pacchetto), F5 long-press text edit, F4 skin tool (sheet export/import/preview/submission, Cinghiale + Ferma thrower skinnable), F2 player login + cloud save (both flag off), I2/I3 dev-stable branches + screens library, E1 dev-mode audit/cleanup. Full detail in CHANGELOG.md; plan and decisions log archived in `docs/releases/0.4.5.md` |
| **0.4.5** | **Release build** (bare `"0.4.5"`, tag `v0.4.5`): all of the above. No player-facing UI changes on the stable site — every new feature ships flag-off or dev-only. The next delivered build is `"0.4.5_1"` |

**`v0.4.5` tag** points at the release commit `v0.4.5: release`. **Numbering switch at the v0.4.5 release**: the release build carries the bare `"0.4.5"`; builds after it bump `0.4.5_NN` from `0.4.5_1` (counter resets).

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

- **Palette/art for snacks 4–9** (not a skin; decided 2026-09-27 with U2): snacks 4–9 have no art or colours and are drawn as the base burger everywhere (pellets, eating, battle). Rocks 4–9 now take their battle-type colour (0.4.5_8); snacks stay as they are until the owner supplies a palette or art. `wait-assets`.

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
- **REQ — tile-10 reward skin (Uomo roccia)**, made with the F4 skin tool. Moved from 0.4.5 (2026-09-26, owner's decision, no time). Needs: the owner's art (drawn with «Scarica foglio»/«Carica costume» or supplied to the artist per DEVELOPERS.md) and a name for the costume.
- **B1 — maze hitboxes around assets.** Moved from 0.4.5 (2026-09-26, owner's decision, no time). Needs: a screenshot or bug report describing the problem.
- **B2 — fantasmi sovrapposti (ghosts overlapping).** Found on the owner's phone at 0.4.5_16: on L maps (5 ghosts) the ghosts overlap each other and are not visually separate while moving. Not yet known whether S/M classes (3/4 ghosts) are affected too. Status: **to plan in Claude chat, before E1.** Planning hypotheses (recorded as given, not investigated): (a) the 5th ghost reuses a house start (`MET.ghosts[i%MET.ghosts.length]`, i.e. the same tile as ghost 1), so while it's still waiting it is drawn exactly on top of that other ghost; (b) once released, the 5th ghost starts from that same tile and chases with a near-identical value (the average of the difficulty's 4 chase values), so it can end up following the same path as another ghost. Claude Code's own guess from the 0.4.5_16 code (unverified): `chooseE` has no ghost-to-ghost avoidance at all — it only avoids walls and reversing direction — so two ghosts on the same tile with similar chase values are likely to keep picking the same turns and drift together instead of separating, rather than this being only a start-position coincidence.
- **Login Esc bug** (found during 0.4_15's X1 chunk): after a failed dev/player login attempt, focus leaves the modal (the disabled «Accedi» button drops it to `<body>`), so Esc no longer closes the login popup until the user clicks back into the form. Root cause in CLAUDE.md history (X1, 0.4_15); `test_f1`'s "Esc closes the login" check stays red until this is fixed.
- **Cloud-conflict card wrapping**: the card title «Su questo dispositivo» and the date line «Salvato il … alle …» still wrap onto two lines at 390 px (found in X1, 0.4_15 — only the name/level wrap was in that chunk's scope).
- **`test_f4b1` fixed waits**: several checks use a fixed `wait_for_timeout` after a heavy operation (e.g. the multi-page BK import) instead of waiting for the real state, which can fail under load (seen once during REL, 2026-09-26, green on rerun). Replace with waits for the actual DOM/state change.

### Post-0.4 — audio submissions (A1…An)
One build per approved audio submission (Uomo roccia sounds, Algidone sounds, Blackjack voiceover, Professore voiceover, professor intro music, and the new `sound.fa.<slot>` set for Ferma Algidone!). They will arrive eventually and
are processed **after the 0.4 release** via the §5 procedure and the A0 built-in layer (keep the running slot table in §10.9; music: half-length + crossfade loop per §6 rule 7). Not a dependency of REL.

### 0.5 note — player bug reports and privacy
Before player bug reports go live (0.5, `BUG_PLAYERS=true`): the repo is public — player reports must not store uid/ua/account in `bugs/` (strip them in the export or keep those reports private).

### 0.5 note — extras and cloud save
A synced save may refer to dev-added extra objects that exist only on another device (extras aren't synced). Devs only, harmless; revisit when extras become player-facing.

### Later phases
- Firebase: set up (§10.2); login and cloud save are chunks F1/F2.

---

## 9. Delivery checklist

- [ ] `git pull --ff-only` at session start
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
- [ ] Commit `v0.4.5_NN: …`, push to `dev`
- [ ] **Release only**: `SKIN_COVERAGE.md` regenerated against the release build; no `manca` on a frame added
      since the last stable release, unless the owner names that gap as accepted (§6 rule 11)
- [ ] **Release only**: merge `dev` → `main` with a commit message exactly `Release <version>` (e.g.
      `Release 0.4.5`) — tags and the GitHub Release are created by `.github/workflows/tag-release.yml` on
      the push to `main`, not by the session. Sessions never push a tag themselves.

---
## 10. Current release — 0.5 (plan from Claude chat, 2026-09-26)

Source of facts: `docs/releases/0.5-P0.md`. Line numbers there drift — re-grep before use.
Dev builds are numbered `0.4.5_N` until the 0.5 release. One chunk per build; stop for the owner's phone test after each chunk.
Any question a chunk raises → ask as [Q], log the answer in §10.9. Player-facing text in Italian, in-universe; the owner edits wording later via long-press.

### 10.0 Sandbox rules (apply to every 0.5 feature)
- The single-HTML game is a sandbox; after its 1.0 a clean build imports its features. Every new feature must stay transferable:
  data in tables (constants/objects at the top of its section), logic in self-contained modules with clear hooks
  (e.g. `onSpawn / update / draw` per ghost ability, a run-layer object for runs). No tangling with unrelated maze code.
- **Each feature/mode keeps its own tuning table** (lives, timings, speeds, rewards). Changing one mode's values never changes another's — e.g. Mangiaroccia lives and Hardcore are not affected by anything in the Ferma Algidone! run, and vice versa.

### 10.1 Decisions (final)
- «Lista desideri» → «Negozio»: done by a dev via long-press (`tile.wish.label`) + «Invia testi». Not a chunk.
- «Mr. Stone»: in-game title only (all title strings, P0 §7). Repo and URL unchanged.
- Asset libraries stay tied to each character. Characters unlock as found in the game. Difficulty stays in Opzioni. Costumes unlock via progression/quests (no shop).
- Enemy art stays procedural; enemies stay outside the skin system and §6 rule 11.
- **Level-10 map lock removed**: `mapsUnlocked()` no longer gates maps; the girone schedule (10.2) picks the map class. Achievement `g4` keeps its sordi/XP; update its description text.
- El Gamblador «Non ora»: keep today's behaviour (hidden only at the first-ever table). Fix the §2 text.
- Maze: after losing a life, a **5 s aura in the character's own power-up colour** (Roccia luminosa gold / Algidone cup yellow-red) — the aura is the protection and the timer: it fades over the last 1.5 s and vanishes exactly when the invulnerability ends. No blinking. Own maze constants (`RESPAWN_INVULN`, `RESPAWN_FADE`, `RESPAWN_AURA`), independent of Ferma's own 2 s respawn. Quicksave/resume keeps the remaining time. Maze lives otherwise unchanged.
- `smashable()` also protects the ghost house and tunnel rows (shared helper, reused by Super Panino).
- «sad» screen: delete (`renderSad`, `sadArm`, render case) — unreachable.
- Maze stays without music in 0.5.
- Forced Ferma Algidone! encounter in the maze: girone 8 instead of 10.
- Caverna/Neon uncapped pellets (141/139): leave as is.
- Moved out of 0.5: pre-run loadout with multipliers (0.7 or post-1.0); mini-game buying, «premium», full shop (post-1.0). 0.6 unchanged.

### 10.2 Maze — map classes, ghosts, girone schedule
Map class by grid width:
| Class | Maps (`mi`) | Ghosts |
|---|---|---|
| S | 0–4 (15×17) | 3 |
| M | 5 Caverna, 6 Cristalli, 7 Rovine, 10 Tundra, 12 Deserto, 13 Neon | 4 |
| L | 8 Palude, 9 Vulcano, 11 Fabbrica, 14 Gran Labirinto | 5 |

- 3 ghosts: use the first 3 `MET.ghosts` starts. 5 ghosts: the 5th reuses a house start with a longer `wait`; add a 5th `TINTS` entry; its `chase` = average of the difficulty's 4 values.
- Schedule (same for Hardcore; no immediate map repeat within a class):

| Girone | Class | Ghost stages |
|---|---|---|
| 1 | S | all stage 1 |
| 2 | S | 1× stage 2 |
| 3 | M | all stage 1 (professor-win runs start here) |
| 4 | M | 2× stage 2 |
| 5 | M | 2× stage 2, then El Gamblador |
| 6 | L | 2× stage 2 |
| 7 | L | 2× stage 2 + 1× stage 3 |
| 8 | L | 2× stage 3 (forced Ferma encounter by now) |
| 9+ | random S 20% / M 40% / L 40% | all ≥ stage 2; +1 stage-3 ghost every 2 gironi (up to all) |

- Keep this as one data table (`GIRONI`) + a function `gironeSpec(stage)` → `{cls, ghosts:[stage,…]}`.

### 10.3 Ghost stage abilities (starting values; E6 balances)
Stage is per ghost. Scared (`s`) or eaten (`g`) ghosts never use abilities. Each stage shows a procedural marker (e.g. outline colour/glow) so the player can read it. All values in one table per ability.
- **Aeroplani (Uomo roccia's enemies)**
  - Stage 2 — sprint: when the player is in the same row/column within 6 tiles, wind-up 0.6 s (shake + particles, visible), then ×1.8 speed for 1.5 s; cooldown 6 s.
  - Stage 3 — also shoots: on line of sight along a row/column within 8 tiles, one projectile at 7 tiles/s, stopped by walls; cooldown 4 s; **never while winding up or sprinting**. A hit kills like a ghost (respects invulnerability and active abilities).
- **Attrezzi (Algidone's enemies)**
  - Stage 2 — grease: drops a grease patch on its tile every 8 s (max 3 active per ghost); player ×0.6 speed on it; each patch fades out after 10 s. Ghosts unaffected.
  - Stage 3 — Super Panino: when two stage-3 attrezzi come within 1 tile, short intro animation (≈1 s, game paused), they merge into one Super Panino: ≈1.6 tiles, faster, chase 0.9, breaks walls in its path via the shared `smashable()` helper (protected cells never). Lasts 12 s, then splits back into the two stage-3 attrezzi. During a power-up it can be eaten for 3200.
- Needed systems (none exist today, P0 §3c): a small maze projectile list and a row/column line-of-sight helper, both as self-contained modules.

### 10.4 Rewards (maze and Ferma run)
- At each girone clear, the points earned **in that girone** get a bonus: `girPts × (classMult × stageMult − 1)`, shown as «Bonus girone ×N.N».
  - classMult: S 1.0 / M 1.2 / L 1.4.
  - stageMult: 1 + 0.10 per stage-2 ghost + 0.25 per stage-3 ghost (Super Panino counts as its two ghosts).
  - Ferma run: its own table — loopMult = 1 + 0.2 × loop.
- `finishRun` unchanged: limiter, `DIFF.mult`, `.7` apply afterwards → multipliers first, then limiter.

### 10.5 Nuovo gioco — game choice (S1)
- Uomo roccia: «Nuovo gioco» (and «Hardcore») asks «Mangiaroccia» or «Ferma Algidone!». Algidone: starts the maze directly (he can't play his own game).
- Fix `nextMinigame()` so the interlude card follows the current run's game.
- Until FR1 lands, the «Ferma Algidone!» choice shows «In arrivo».

### 10.6 Ferma Algidone! run
- Built on a **run layer** (FR0): a mode-agnostic run object holding girone counter, score, lives, flags (`g5`, `sec`), career/Percorso counters, girone achievements, encounter hooks, `finishRun`, quicksave. Maze `G` and Ferma both use it. FR0 = no behaviour change.
- All Ferma-run numbers live in its own table `FA_RUN` (independent of the maze and of Ferma practice/encounter values).
- Girone g plays level `(g−1) mod 3`; loop = `floor((g−1)/3)`. Floor 3 collapse → next girone = level 1 of the next loop.
- **Ferma gironi count** toward career gironi, Percorso and girone achievements, exactly like maze gironi.
- **Lives**: `FA_RUN.lives = 3` at run start, refilled at each girone (own setting; maze lives/Hardcore untouched).
- **Death**: costs one life and nothing else — no bite, no loss on the time bar. The player respawns at the start of the level **without a hard reset of the level**: time bar, bite schedule, picked bolts/holes, score and Algidone's state carry on; only the items in flight are cleared; 2 s invulnerability (existing).
- **Time bar** (looks like today's stock bar, no numbers): drains only when Algidone eats. The random 22% eat chance is replaced by a scheduled bite every `L/N` s (±15%); throws continue in between. Each bite removes 1/N of the bar.
  - Loop 1: L = 120 s, N = 12. Each loop: L −15 s (min 75), N −2 (min 6), then ±1 random.
  - Last bite: slow motion, fade to black, lost popup → the run ends (`finishRun`).
  - Floor-end bonus = uneaten bites × 100 (replaces `floor(stock)*10`).
- **Game over** = 0 lives or empty time bar; either ends the run.
- Per loop, on top of the difficulty setting: throw interval ×0.9^loop (floor ×0.6), item speed ×1.05^loop (cap ×1.3).
- Floor 3 bolts: three hand-authored layouts (loop 1 = today's, loop 2, loop 3+), harder each time, plus a validator (test) that keeps every bolt/hole clear of ladder x's 60/190/210/230/300 and the floor beatable.
- Encounters between gironi: El Gamblador mandatory at girone 5, then 15% per girone; `miniInterlude` on multiples of 5. **No Ferma encounter inside a Ferma run.** Encounters return to the Ferma run.
- Quicksave at girone boundaries only; «Gioco corrente» restarts the current level.
- Practice (Giochi) and the maze encounter also switch to the eat-driven bar (their own loop-1 values); there, too, a death costs a life only (no bite), same respawn rule.

### 10.7 Player accounts (Firebase Spark)
- L0 (Claude chat, not Claude Code): rules update + check that `FIREBASE_SA` has the Firebase Authentication Admin role.
- Registration: open, in-game, client SDK `createUserWithEmailAndPassword`, email `<username>@mangiasassi.invalid`. Username: 3–16 chars, `a–z 0–9 _ -`, stored lowercase; reserved: master, dev1–dev5, admin, algidone, gamblador, professore, mrstone, usagi. No password recovery.
- New doc `players/{uid}`: `username, created, confirmed` (timestamps).
- Confirmation: popup at the first open after 25 days since `confirmed`; tap to confirm → `confirmed = now`. Unconfirmed at 30 days → account + save deleted. Dev accounts exempt.
- Deletion request: after 5 wrong passwords (counter per device) the player can request deletion of that username → doc `delreq/{username}` `{ts}`, creatable without sign-in. Executed after 7 days, **cancelled if the account signed in after the request**. Then the player can register again.
- Cleanup: scheduled GitHub Action (Admin SDK, `FIREBASE_SA`) runs daily: 30-day unconfirmed deletions + due deletion requests (Auth user, `players`, `saves`).
- Player bug reports: flags on (`PLAYER_LOGIN`, `CLOUD_SAVE`, `BUG_PLAYERS`); rules let any signed-in user create `bugs`; the export strips `uid`, `ua` and account for player reports (public repo).

### 10.8 Chunks (order, model, effort)
| Phase | Chunk | Content | Model / effort |
|---|---|---|---|
| 1 | P1a | Login Esc bug; cloud-conflict card wrap at 390 px; `test_f4b1` fixed waits → real-state waits | Sonnet 5 / medium |
| 1 | P1b | Maze 2 s respawn invulnerability; `smashable()` protects house + tunnel rows; delete «sad» screen; CLAUDE.md §2/§4 corrections (terrain only on extra maps, «Non ora», Cinghiale immunity) | Sonnet 5 / medium |
| 1 | B1 | Maze hitboxes — **waits for the owner's screenshot** | Sonnet 5 / high |
| 2 | U1 | «Mr. Stone» title; Giochi «???» + «non sbloccato»; El Gamblador picture on his card and unlock popup (`gambImg`); forced Ferma encounter at girone 8 | Sonnet 5 / medium |
| 2 | U2 | Eaten-stone animation recoloured to the chosen rock (all rocks) and snacks | Sonnet 5 / high |
| 2 | U3 | Unlock hints: golden border on roadmap tiles 3/5/10 linking to their achievement, «sblocca regalo!» on gift achievements, new «batti il professore» achievement; GEKA hat only after beating the professor (keep for current owners) | Sonnet 5 / high |
| 2 | U4 | Algidone's own rank names (use `rankOf`; propose names, owner approves); arrow-key menu navigation on web; menu music in Achievements, Percorso, Personalizza | Sonnet 5 / medium |
| 2 | S1 | Game choice at «Nuovo gioco» (10.5), `nextMinigame` fix | Sonnet 5 / medium |
| 3a | M1a | Map classes, `GIRONI` schedule, 3/4/5 ghosts, level-10 lock removed, `g4` text | Sonnet 5 / high |
| 3a | M1b | Girone bonus multipliers (10.4) + «Bonus girone» line | Sonnet 5 / medium |
| 3a | E1 | Ghost stage framework: per-ghost stage, ability module hooks, stage markers, projectile + line-of-sight modules | Opus 5.5 / high |
| 3a | E2 | Aerei stage 2 sprint with wind-up | Sonnet 5 / high |
| 3a | E3 | Aerei stage 3 shooting | Sonnet 5 / high |
| 3a | E4 | Attrezzi stage 2 grease | Sonnet 5 / medium |
| 3a | E5 | Attrezzi stage 3 Super Panino | Opus 5.5 / high |
| 3a | E6 | Balance pass (headless sims of gironi 1–12, report numbers before changing) | Sonnet 5 / high |
| 3b | FR0 | Run layer extraction, no behaviour change | Opus 5.5 / high |
| 3b | FR1a | Ferma run: looping levels, girone counting, lives + soft respawn, eat-driven time bar, last-bite ending | Opus 5.5 / high |
| 3b | FR1b | Loop difficulty scaling, 3 bolt layouts + validator test, loopMult rewards, quicksave; practice/encounter bar switch | Sonnet 5 / high |
| 3b | FR2 | Encounters inside the Ferma run (El Gamblador g5 mandatory, 15%, interlude) | Sonnet 5 / high |
| 4 | L0 | Firebase console + rules — Claude chat, not Claude Code | — |
| 4 | L1 | Registration UI, username rules, `players/{uid}` | Sonnet 5 / high |
| 4 | L2 | Player flags on + 25/30-day confirmation popup | Sonnet 5 / medium |
| 4 | L3 | Cleanup GitHub Action (Admin SDK) | Sonnet 5 / high |
| 4 | L4 | Deletion request after 5 wrong passwords | Sonnet 5 / medium |
| 4 | L5 | Player bug reports + export stripping | Sonnet 5 / medium |
| 5 | REQ | Tile-10 reward costume — **waits for the owner's art + name** | Sonnet 5 / medium |
| 5 | REL | Release 0.5 (§9 checklist) | Sonnet 5 / medium |

### 10.9 Answers log
(log [Q] answers here, with the chunk and date)

- 2026-09-27 · P1b (0.4.5_5): owner feedback — the maze respawn blinking is replaced by a 5 s aura in the power-up colour (was 2 s blinking); the aura is the timer; §10.1 and §2 updated.
- 2026-09-27 · U2 (0.4.5_8) [Q answered]: rocks 4–9 get colours from their existing battle-type colours (`PB_TCOL`, same formula as `pbRockTint`), applied to pellets, side/up/down eating and the menu bite; snacks 4–9 stay as they are and "palette/art for snacks 4–9" goes on the §8 art-owed list. No other new art.
- 2026-09-27 · U3 (0.4.5_9): tile→achievement mapping for the locked-tile hint `ROAD_HINT` = 3 → `m5` «Batti il professore», 5 → `m1` «Il banco trema», 10 → `m2` «Fuori da Coccia!» (all exist, no [Q]). Tile 3 now opens only on `S.p.pr.won` (real professor win, not test/SIM); old saves that had seen a real battle or claimed tile 3 keep it (`S.p.road.keep3`); no retroactive achievement because no old save can prove a win (only `visits/seen` existed). «sblocca regalo!» shows only where the linked tile has a ready gift (m5 → GEKA, m1 → BK); m2/tile 10 has no gift yet, so no tag until one exists.
- 2026-09-27 · U4 (0.4.5_10) [proposal for the owner to approve at the phone test]: Algidone's ranks — 1 Pivello, 10 Tesserato, 20 Frequentatore, 30 Culturista, 40 Powerlifter, 50 Istruttore, 60 Personal trainer, 70 Campione di panca, 80 Leggenda della sala pesi, 90 Maestro del ferro, 100 Re della palestra.
- 2026-09-27 · U4 (0.4.5_12): owner's Algidone rank names approved (10 names, thresholds 1,10…90; 90 covers to 100) — 1 Mangiatore modesto, 10 Usurpatore di Snacks, 20 Snacks Manager, 30 Mangiatore Professionista, 40 Bevitore di Bevande, 50 Re degli Snacks, 60 Amico del Colesterolo, 70 Perfettamente Sferico, 80 Regina delle Bevande, 90 Abbuffatore Seriale. Replaces the 0.4.5_10 proposal above.
- 2026-09-27 · M1a (0.4.5_13): built exactly to §10.2/the level-10 lock line of §10.1, no [Q] raised. `gironeSpec(stage)` and `pickMap(stage)` share one class draw per girone (never two independent random picks for the same girone, which would risk a map class and a ghost count that disagree at girone 9+). No ghost abilities/markers/behaviour added (E1+); `.stage` is stored on each ghost only.
- 2026-09-27 · dev girone-jump (0.4.5_14): owner-approved testing aid for E1-E6, no [Q]. `devJump(n)` already ran the real M1a spec (`pickMap`/`resetActors`) for any `n`, so the new `#jgN`/`#jgGo` needed no new plumbing — just the field, the button and the clamp.
- 2026-09-27 · M1b (0.4.5_15): built exactly to §10.4, no [Q] raised. Display: `×M` is a plain `Math.round(mult*100)/100` (JS already drops trailing zeros — ×1.1/×1.44/×2.03, no `.toFixed`). The bonus mult is read from the just-cleared girone's own `G.en[].stage` rather than a fresh `gironeSpec`/`pickClassForGirone` call, for the same reason M1a's `pickMap`/`gironeSpec` share one draw — a second random class pick at girone 9+ could disagree with the map that was actually played.
- 2026-09-27 · 5th-ghost fix (0.4.5_16): owner's phone test found girone 8 (L, should be 5 ghosts) showing at most 4. Reproduced with direct `devJump` calls across all 15 maps × both characters × all three reach-girone-8 paths — class/count/draw logic was already 100% consistent everywhere; the real cause was the 5th ghost's naively-extended wait timer (up to 15 s at Facile) combined with the pre-existing "a death resets every ghost's wait" mechanic on a fast, 5-wide girone — the slowest ghost(s) could go an entire test session without ever leaving the house. Fixed the wait gap (flat 2.5 s after the 4th ghost, not difficulty-scaled) and added the dev-only girone readout so ghost count/class/stage never again needs eyeballing on screen.
- 2026-09-27 · 0.4.5_16 phone-test result: the fix works (all 5 ghosts present on L maps). New bug found: the ghosts overlap each other («fantasmi sovrapposti»), not visually separate while moving. Logged as **B2** in §8 (0.5 backlog) with the owner's planning hypotheses and Claude Code's own unverified guess; not fixed now — planned in Claude chat before E1.
