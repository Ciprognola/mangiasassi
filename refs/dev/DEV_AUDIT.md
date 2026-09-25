# Dev-mode audit (E1a) — 2026-09-25

Build audited: 0.4_1 (`dev` branch). Report only: nothing was changed in the game. Screen ids are those of `refs/screens/SCREENS.md`.
Abbreviations: **dev OFF** = `devUI()` false (`devOn` false or no `role`). **Script use** = used by the Playwright/screens scripts (`tools/screens/capture.py`, the §6 practical notes) — deleting or renaming these breaks them.

## 1. Inventory

| # | Name | Where | What it does | Writes progress? | Visible with dev OFF? | Script use | Overlaps | Recommendation |
|---|---|---|---|---|---|---|---|---|
| 1 | "Build locale" ×5 reveal | `opt-generali` (tap the version row 5×, `#ver`) | Opens the login modal | no | yes (hidden gesture, by design) | yes (`opt-login-modal`) | F1 | REPLACED BY F1 (keep the gesture as the entry to the Firebase login) |
| 2 | Login modal | `opt-login-modal` (`loginModal`) | Checks user/password against `S.creds` (plaintext, in the save and in the public source `DEF.creds`) → role `master` or `dev1` | no (sets `role`) | only via #1 | yes | F1 | REPLACED BY F1 (retire local credentials) |
| 3 | Roles `master` / `dev1` | `role` global, `devRows()` | master-only: credentials, menu music, GAM music, "Sblocca tutto"; dev1: everything else | no | – | yes (`role:'master'`) | F1 (dev1…dev5 + master from Firestore) | KEEP the two-level split; source of the role REPLACED BY F1 |
| 4 | Dev persistence `mgs_dev` (`mgs_dev_dev` on /dev/) | localStorage `{role,devOn}` | Keeps the session across reloads | no | – | yes (seeded by `Cap(dev=True)`) | F1 | KEEP (key names unchanged) |
| 5 | ✎ dev toggle button | `menu-home-*` brand bar (`#devt`), only if `role` | Toggles `devOn`; orange dot when SIM is on | no | **yes when a role is set** (needed to turn dev back on) | no | – | KEEP (see 2a: make the SIM state visible) |
| 6 | Pen icons on tiles / cards, "+" tile, "−" | `dev-menu-home`, `wish-*` (`data-pen`, `data-cpen`, `#addTile`, `data-del`, `data-cdel`) | Opens `editDialog`: label / colour / scale → `S.ov`, `S.tiles`, `S.extra` | no (local overrides in the save) | no | screens (`dev-menu-home`) | F5 | REPLACED BY F5 (already decided: pens go, fields move to the long-press popup) |
| 7 | Overrides `S.ov`, `S.gtext`, `S.tiles`, `S.extra` | applied in every screen | Label/colour/scale/text/asset overrides | no | **yes**: overrides apply with dev OFF (by design, per browser) | no | F3, F5 | KEEP (what Esporta modifiche exports) |
| 8 | Sviluppatore tab | `opt` → `[data-otab=dev]` (`dev-tab`) | Hosts the accordions below | no | no | yes (`sim_on`, `dev_button`) | – | KEEP (restructure, §3) |
| 9 | Account: "Esci" | `dev-acc-account` (`#lo`) | Turns SIM off, clears role/devOn/`DEV_SKIN_TEST`, back to menu | no | no | – | F1 | KEEP, wire to Firebase sign-out |
| 10 | Account: "Come si modifica" help text | `dev-acc-account` | Explains the ✎ pens | no | no | no | F5 | DELETE (pens go) |
| 11 | Account: Credenziali (master) + "+ Sviluppatore" / "Rimuovi" | `dev-acc-account` (`data-c`, `#ad`, `data-rd`) | Edits master/dev usernames and passwords stored in the save | no | no | no | F1 | DELETE (REPLACED BY F1) |
| 12 | Sblocca tutto / SIM | `dev-acc-test`, master only (`data-sim`) | Overlay: lvl 100, 999,999 sordi, all assets/gironi/skins/cards; real save untouched; reverted on reload | no (`S.sim` is written to the save but undone on load, line 455) | **the overlay yes** (2a) | yes (`sim_on` for `wish-*-unlocked`) | – | KEEP + FIX (2a) |
| 13 | Salta al girone 4 / 7 / Mappa torrenti / Mappa larga | `dev-acc-test` (`#jg4 #jg7 #jgt #jgw`) | `devJump`: dev run (`G.dev`), nothing saved, `ach()` disabled | no | no | yes (`#jg4` for `maze-over`, `fa-invite`) | 14 | KEEP |
| 14 | Dev map select + "Vai" | `dev-acc-test` (`#jmsel`, `#jmg`) | Starts the 10 extra maps; the 5 base maps are NOT in the list | no | no | yes (`dev_jump` adds options 0–4 by script) | 13 | MERGE into 13 (one "Mappa" select with all 15 maps; keep girone 4 / 7) |
| 15 | Livello di prova | `dev-acc-test` (`#lvt`, `#lvs`) | Sets the selected character's level | **yes** (real save, or the SIM copy) — intended cheat | no | no | 12 | KEEP, label it as writing to the save |
| 16 | Regali del percorso (preview) | `dev-acc-test` (`data-roadprev`) | `roadPreviewGift`: gift animation, no save | no | no | no | – | KEEP |
| 17 | Skin di prova (`DEV_SKIN_TEST`) | `dev-acc-test` (`data-devskin`) | Magenta outline/tint on skin draw paths, memory only | no | no (cleared on Esci) | no | F4 (live local preview) | MERGE into F4; DELETE after F4b |
| 18 | Mangiaroccia "Avvia" | `dev-acc-test` (`#mgpac`) | `startGame(false)`: a REAL run | **yes** — normal run, sordi/exp/best saved even in dev mode | no | no | 13 | DELETE (duplicate of "Nuovo gioco") |
| 19 | El Gamblador "Avvia" + punti | `dev-acc-test` (`#mggam`, `#mgscore`) | Dev run of the table with a chosen score | no | no | yes (`bj-*`) | – | KEEP |
| 20 | Ferma Algidone! floors 1/2/3 | `dev-acc-test` (`#mgfa #mgfa2 #mgfa4`) | `startFerma({debug,test,level})`: dev run, debug zones + "Ultimo danno" label | no | no | yes (`fa-*`, bindOpt whitelist) | 21 | KEEP |
| 21 | "+ carne/griglia" (`#mgfa3`), "Test uscita" (`#mgfk`), "Test cacciata finale" (`#mgfk2`) | `dev-acc-test` | Floor-1 test with extras; goal win; collapse finale | no | no | yes (`fa-floor-win-panel`, `fa-final-panel`) | 20 | KEEP |
| 22 | "Incontro 1/2/3", "Forza incontro" | `dev-acc-test` (`#mgfe1-3`, `#mgff`) | Simulated encounters (no save); `FA_FORCE` makes the next gap start Ferma | no | no | whitelisted only | – | KEEP |
| 23 | Ferma debug overlay | `fa-floor*-play` in dev runs (`FA.debug`) | Draws logic zones + "Ultimo danno / scavalcati / oggetti" text over the top of the level | no | no | visible in every `fa-*` image | – | KEEP as a toggle (covers the HUD in screenshots) |
| 24 | Professore "Avvia" / "cacciata" | `dev-acc-test` (`#mgrow`, `#mgrok`) | `prTest` (dialogue + battle, `PR.test`), `prTestKick` | no | no | yes (`pr-throwout-*`) | – | KEEP |
| 25 | Professore · battaglia (selects + `#mgrob`) | `dev-acc-test` (`pbTestRow`) | `prTestBattle` | no | no | whitelisted | – | KEEP |
| 26 | Menu music upload/test/reset (master) | `dev-acc-audio` (`#mf`, `#mp`, `#mr`) | IDB `menuMusic` | no (IDB, per browser) | no | no | F3 | KEEP until F3, then re-check |
| 27 | Per-character sounds, jingle | `dev-acc-audio` (`data-sf`, `data-sp`, `data-sr`) | Upload/preview/remove custom sounds (IDB `snd_*`) | no | no | no | F3 | KEEP |
| 28 | El Gamblador sounds / texts+voice / music | `dev-acc-audio` (`gamDevHTML`, `#gmf`, `#gmr`, `data-vt`) | Same for the table; texts write `S.gtext` | no | no (texts stay with dev OFF, like #7) | no | F3, F5 | KEEP; texts MERGE into F5 later |
| 29 | Ferma sounds | `dev-acc-audio` | Same, slots `sound.fa.*` | no | no | no | F3 | KEEP |
| 30 | Professore music / texts+voice / battle texts | `dev-acc-audio` (`prDevPanel`, `pbDevPanel`) | Same | no | no | no | F3, F5 | KEEP; texts MERGE into F5 later |
| 31 | Obiettivi di prova (5 DBG achievements) | `dev-acc-obj` + tab `ach-*` "Debug" (`DBG`, `#dbgr`) | Fire on new game / wish / options / first eat / pause; toast + reward | **yes** (see 2c) | no | hidden by `capture.py` (`#ach-pop`) | – | DELETE |
| 32 | "Popup di prova" (achievement toast) | `dev-acc-obj` (`#popt`) → `popup-achievement` | `achPopup` sample | no | no | yes | 33 | MERGE into 33 |
| 33 | Unlock popup previews | `dev-acc-obj` (`data-popprev`) → `popup-*` | `popPreview`: modal, no save | no | no | yes (via `popPreview`) | 32 | KEEP (add "achievement" here) |
| 34 | Esporta modifiche + testo grezzo + Ripristina build originale | `dev-acc-exp` (`#xopen`, `#cp`, `#rs`) → `export-dialog` | Builds the submission zip; raw JSON copy; wipes local overrides | no (`#rs` deletes overrides) | no | yes (`export-dialog`) | F3 | KEEP; REPLACED BY F3 for the format; "Testo grezzo" DELETE |
| 35 | `window.mgExport` | global, always defined | `build`/`targets` for the export from the console | no | **yes** (reachable from the console with dev OFF) | no | F3 | MOVE (define only when logged in) or DELETE after F3 |
| 36 | `bindOpt` whitelist | code, `bindOpt` | Forwards only the listed dev button ids to `bindDev` | – | – | **yes** (the click path for every dev screenshot) | – | KEEP (new dev buttons must be added; better: a `data-dev` attribute) |
| 37 | "DEV <version>" label + separate save | `/dev/` only (I2b) | Label, `mgs_v1_dev`, `mgs_dev_dev`, IDB `mgs_dev` | no | only on /dev/ | scripts use the root site | – | KEEP |
| 38 | Dev-run flags (`G.dev`, `PR.test`, `FA.test`) | inside the runs | Block saving, `ach()`, popups, unlocks | no (`ach()` returns early on `G.dev`; Ferma/professor tests skip `S.p.fa/pr`) | no | yes | – | KEEP |

## 2. Problems found

**2a. Trello #12 — "dev mode disappears but the overlay remains in tabs": reproduced.**
Steps: dev on → Sblocca tutto → tap ✎ (`#devt`) to switch dev off → open Lista desideri, Giochi, Opzioni. The pens, "+" and the Sviluppatore tab are gone (they depend on `devUI()`), but **everything Sblocca tutto gave stays**: level 100, 999,999 sordi, all cards unlocked (as in `wish-giochi-unlocked`), all skins. Cause: SIM is independent of `devOn` (`SIM()` reads `S.sim`); the ✎ button only flips `devOn`, and with dev OFF there is no control to switch SIM off (its button is in the hidden Sviluppatore tab). It goes away only on reload (line 455 reverts `S.sim` at load), by turning dev on again → Disattiva, or "Esci". Fix options: dev off also calls `simOff()`, or a clearer "SIM attivo" badge on ✎ (the small orange dot exists but is easy to miss).

**2b. "A mouse click on the El Gamblador stage crashes headless Chromium": not a game bug, not reproduced.**
The handler (`root.onclick`: `bjSkip()` / `bjConfirm()`) has no loop or allocation. I clicked `#bstage` 12 times in four ways (Playwright `click`, raw `mouse.click`, dispatched event, screenshot+click+wait) with console/pageerror listeners: no error, no crash, each action < 0.7 s, `evaluate` back in ~0 ms. The I3 crashes happened while another capture run was alive in the background (two Chromiums on the same port and CPU): a test-setup resource problem, not the click. The "use Enter instead of clicks" workaround in `capture.py` is harmless but unnecessary; the note in the I3 report and the script comment should be corrected.

**2c. Debug achievement toasts.** They fire only with dev ON, outside dev runs, on: opening Lista desideri, opening Opzioni, new game, first eat, pause; once each until "Ripristina obiettivi di prova". They cover the bottom of every screen for a few seconds. **They write progress**: `unlockAch` adds sordi and exp (+5/+5, scaled by difficulty) to the real save and persists it, and a dev can farm them by resetting. A dev has no need to see them: recommend DELETE (pick 12).

**2d. Other findings**
- Progress writes in dev mode: #15 (by design), #18 (a normal run), #31.
- Leaks with dev OFF: #35 `window.mgExport`; ✎ visible whenever a role exists (needed); overrides #7 (by design).
- Credentials: master/dev passwords are in `DEF.creds` in the public source and, editable, in the save (#11) — F1 retires them.
- Duplicates: #13/#14, #32/#33, #17 vs F4 preview, #10 obsolete after F5.
- Unreachable: the 5 base maps have no entry in the dev map select (#14); the scripts add the options by hand.
- The Ferma debug overlay (#23) is always on in dev floors and sits over the level in every Ferma frame.

## 3. Proposed dev panel after cleanup

Sviluppatore tab, four accordions:
1. **Account** — role and username (from Firebase), Esci, Cambia password (F1). Nothing else (no credentials, no help text).
2. **Prova** (all dev runs) — "Sblocca tutto" (master) with a visible on/off state; level of test (labelled as writing to the save); "Salta al girone" 4 / 7 plus one map select with all 15 maps and Vai; Ferma Algidone! (floors 1/2/3, exit test, collapse test, Incontro 1/2/3, Forza incontro, + carne/griglia, debug overlay toggle); El Gamblador (start + points); Professore (dialogue, cacciata, battle with the two selects); previews: unlock popups (asset / char / game / milestone / achievement) and the gift.
3. **Audio** — unchanged for now (menu music, per-character sounds, jingle, El Gamblador, Ferma, Professore); the text/voice-line editors move to F5 when it ships.
4. **Consegna** — Esporta modifiche (F3 format), Ripristina build originale. F4 adds the skin tool here (or its own accordion); F6 adds "Segnala un bug" as a button on the screens themselves.

Home menu: only the ✎ toggle. Pens, "+", "−" go with F5. The "Debug" achievements category is removed.

## 4. Owner picks

(Answer as "1 yes, 2 no, …")
1. Replace the local login, role source and `S.creds` (#1–#3, #11) with F1, keeping the ×5 gesture as the entry — recommend **yes**. Scripts: `opt-login-modal` capture uses the gesture.
2. Delete the Credenziali block and "+ Sviluppatore" / "Rimuovi" (#11) — **yes** (with F1). No script use.
3. Delete the "Come si modifica" help text (#10) — **yes**.
4. Turn Sblocca tutto off whenever dev mode is switched off (fixes Trello #12) — **yes** (alternative: keep it and show a "SIM attivo" badge on ✎). `capture.py` relies on SIM staying on after `devOn=false` (for `wish-*-unlocked`): I would adapt the script (hide pens by CSS).
5. Merge the four map buttons and the map select (#13/#14) into one select of all 15 maps + Vai, keep Girone 4 / 7 — **yes**. `capture.py` (`dev_jump`, `#jg4`) must be adapted.
6. Delete "Mangiaroccia Avvia" `#mgpac` (#18; a real run that saves progress) — **yes**. Not used by scripts.
7. Keep "Livello di prova" (#15) but label it as writing to the save — **yes**.
8. Merge "Popup di prova" (#32) into the unlock-popup previews (#33) — **yes**. `capture.py` calls `popPreview`/`achPopup` directly: unaffected.
9. Make the Ferma debug overlay (#23) a toggle, default OFF — **yes**; the `fa-*` screens would be regenerated cleaner.
10. Delete "Testo grezzo" (#34) — **yes**, replaced by F3.
11. Hide `window.mgExport` unless logged in (#35) — **yes** (or delete with F3).
12. Delete the debug achievements and the "Debug" tab (#31; they write +5 sordi/exp) — **yes**. `capture.py` injects a style hiding their toast (`capstyle`); the Debug tab is not in `SCREENS.md`, so nothing else breaks.
13. Delete `DEV_SKIN_TEST` (#17) after F4b — **yes** (later, no action now).
14. Replace the `bindOpt` whitelist (#36) with a `data-dev` attribute so new dev buttons need no code edit — **yes**. The ids stay, so scripts are unaffected.
15. Keep the two-level role split (#3): master-only = Sblocca tutto and the menu/GAM music uploads — **yes**.
16. Correct the I3 note about the El Gamblador click (2b) and the Enter-workaround comment in `capture.py` — **yes** (doc-only, next docs chunk).
