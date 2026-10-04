# Roadmap to 1.0 — new structure, handheld mode, co-op
Approved 2026-10-03, revised 2026-10-04 (Claude chat). Each phase is planned in Claude chat first; Claude Code executes chunks per CLAUDE.md §0.

## 1. Why
- index.html (0.5) is ~6.2 MB: ~5.6 MB is base64 assets (88 PNG, 5 MP3) and only ~640 KB is code (~8,200 lines, ~620 functions, one script). Every patch navigates one giant file and every submission must be hardcoded into it.
- 1.0's headline is co-op. Building it inside the monolith would mean building it twice. The previous plan (sandbox until 1.0, clean rebuild afterwards) is REPLACED: the 0.6 migration below is the new build.

## 2. Target structure
- Stays web. Vite build; static output deployed by GitHub Pages as today; the Android WebView wrapper loads the built output.
- Code: one module per screen / minigame / system. Existing JS is ported as-is in 0.6 (no TypeScript conversion during the migration). New modules are TypeScript from 0.7; the 0.8 server and the messages shared between client and server are TypeScript from day one; the rest is converted gradually.
- Assets: real files under assets/<area>/ — no base64 in code. Existing per-file submission limits stay.
- Data: texts, dialogue, characters, skins and balancing values in JSON under data/. Game language stays Italian.
- Minigames: each split into a simulation layer (state + update(inputs, dt), no DOM/canvas/audio) and a render/input layer. Required for co-op and makes tests easier.
- Size budget: total game assets ≤ 512 MB; first load ≤ 20 MB; each minigame's assets lazy-loaded when it opens.
- Folders:
  - `src/core/` — boot, screens, save, audio, input, firebase
  - `src/screens/` — menu, Giochi, Percorso, Personalizza, Opzioni, …
  - `src/minigames/<name>/` — sim.(js|ts), view.(js|ts), roles.json
  - `src/coop/` — session client, lobby, spectator view
  - `data/` — JSON: texts, dialogue, characters, skins, balance
  - `assets/<area>/` — png / ogg / mp3
  - `server/` — Cloudflare Worker + Durable Object (from 0.8)

## 3. Co-op design (1.0)
- Each player plays on their own device (phone or computer), in normal or handheld mode (§7). Only game state travels between devices; input stays local. Discord is only how the group streams the game during hangouts: no Discord Activity and no Discord login.
- Session: up to 8 players, joined via an invite link. Lobby → minigame chosen (vote, host breaks ties) → roles filled up to that minigame's cap, everyone else spectates live → round → points added to the session scoreboard → session winner gets a reward.
- Role caps live in data per minigame. Ferma Algidone!: 2 climbers + 1 player-controlled Algidone. Other minigames defined in C0 (§6).
- Netcode: host-authoritative rounds over a relay room. The round host's client runs the simulation; other active players send inputs; the host broadcasts snapshots (~15/s) to all, spectators included. Host leaves → round void, session continues. Fallback if phone hosts prove fragile (screen lock, app in background, lag): the simulation, which has no DOM, runs in the Worker instead. Decided after the co-op spike (§4).
- Server: Cloudflare Worker + Durable Objects (SQLite-backed, Workers Free plan), one object per session: presence, roles, scoreboard, relay. Firebase stays for accounts and saves; GitHub Pages stays for the game.
- In handheld mode the Select button opens the co-op features.

## 4. Release plan
| Release | Content |
|---|---|
| 0.5 | Released 2026-10-04 (tag v0.5) |
| 0.5_N «Portatile» | Handheld mode, first delivery (§7), built before 0.6 M0 |
| 0.6 «Fondamenta» | Migration only — game identical, handheld mode included; requirements in §5.1 |
| 0.7 | Former 0.6 backlog: Usagi's quest (pets, §8), il Professore vs blackjack winners, El Gamblador «lascia o raddoppia», Ferma Algidone! power-ups + moving small ladders, prizes revision; handheld layout for the remaining screens. Built in the new structure with the sim/render split. C0 is settled before 0.7 is planned |
| 0.8 | Co-op core: Worker + session room, lobby, invite link, spectating, scoreboard; first co-op minigame Ferma Algidone! (2+1); multi-client tests from day one |
| 0.9 | Co-op for the remaining minigames (Blackjack first); session rewards; balancing; handheld mode on PC (low priority) |
| 1.0 | Co-op release |
| After 1.0 | Ferma levels beyond the 3rd; il Professore / El Gamblador as playable characters; RPG cluster (movepicker + professor rebalance, asset experience, squadra and secret-power slots, Rocciamon levelling by girone — the movepicker comes earlier only if C0 makes the battle a co-op game); premium content and shop; pre-run loadout; save export/import |

- Co-op spike (recommended): a throwaway prototype in prototypes/coop/ (never linked, like prototypes/algidone/) after 0.6 M4, in parallel with 0.7. Two phones join one room running Ferma's simulation; it measures lag and what happens when the host's screen locks. About 2–3 Sonnet / medium builds; confirmed once M0 has measured the minigames.
- Blackjack is the first co-op game of 0.9: turn-based, reuses the room, roughly a third of Ferma 2+1's co-op work. Whether it moves into 0.8 is decided after M0.

## 5. 0.6 phases (chunk breakdown planned in Claude chat before each phase)
| Phase | Content | Model / effort |
|---|---|---|
| M0 | Read-only investigation: map screens, minigames, globals/shared state, save format and keys, Firebase calls, dev tools, tests. Output docs/releases/0.6-M0.md with a proposed module map. | Opus / medium |
| M1 | Extract embedded assets to files loaded at runtime; behaviour identical. | Sonnet / low–medium |
| M2 | Vite project; split code into modules in thin chunks, one area per chunk; sim/render split per minigame. | Sonnet / medium |
| M3 | Texts, dialogue, balancing → JSON; dev tools (Invia testi, Scarica pacchetto, skin tool, validator) retargeted to files; DEVELOPERS.md updated. | Sonnet / medium |
| M4 | Parity: Playwright suite + owner phone test vs 0.5; existing local and cloud saves load unchanged; switch the stable site. | Sonnet / medium + owner |

Rules during 0.6: no gameplay changes; every chunk phone-tested; save compatibility mandatory; numbering continues per CLAUDE.md §7. The handheld mode built in 0.5_N is ported as-is, like the rest of the game.

### 5.1 Requirements from later releases (for the 0.6 plan; cheap during M2)
- Same inputs give the same result: each minigame's simulation uses a seeded random generator, so a round can be replayed and tested.
- Inputs are plain command objects, through one input module (touch, keyboard, gamepad); the simulation never reads touch or keys directly. Handheld mode and co-op both rely on it.
- A minigame's state can be copied out and restored as plain data (the co-op snapshot).
- One save module with versioned migrations; existing local saves and cloud saves (saves/{uid}) load unchanged.
- Each minigame loads only when opened (§2 size budget).

## 6. Open decisions (settle in Claude chat)
- C0, before 0.7 is planned: co-op spec per minigame (roles, caps, scoring), including whether Mangiaroccia is co-op at 1.0 (one option: players control the ghosts) and whether the Rocciamon battle is; pets in co-op; session reward type; guests (recommended: guests can play, rewards need an account).
- After M0: Blackjack in 0.8 or 0.9; confirming the co-op spike.
- Handheld button meanings for Blackjack and the battle screen (proposed from the code in the handheld plan).
- Pet size in game (proposed: about 55% of Uomo roccia's height).
- Decided 2026-10-04: TypeScript timing (§2); no Discord Activity (§3); pets in 0.7 (§8); RPG cluster after 1.0 (§4).

## 7. Player experience and handheld mode («modalità portatile»)
- Principle for 1.0: the top of the screen is the shared picture (the game, which is also what the stream shows); the bottom is personal (controls, stats, pet, co-op role). Same split solo and in co-op, so handheld mode is the base layout for 1.0, not a side option.
- Reference controller: GameSir Pocket Taco (Bluetooth, Android; D-pad, A/B/X/Y, L1/R1/L2/R2, Start/Select). It clamps the phone and covers most of the lower screen, so the game display runs down to where the controller starts. The covered height is a setting.
- Selection bar just above the controller. In play it shows «Start: Pausa», a short status (for example the pet) and «Select: Co-op». When paused, its tabs (Riprendi, Comandi, Opzioni, Esci) open overlays in the top area. Menus, Opzioni and the co-op lobby also live inside the display area.
- Without a controller: on-screen D-pad, A/B and Start/Select in the lower half; they can be hidden.
- Generic commands (the names used in Opzioni › Controller):

| Button | Generic name | Mangiaroccia | Ferma Algidone! |
|---|---|---|---|
| Croce | Muovi / scegli | Muovi | Muovi |
| A | Azione principale (conferma nei menu) | Abilità | Salto |
| B | Azione secondaria (indietro nei menu) | Trasformati | — |
| L1 / R1 | Scheda precedente / successiva | — | — |
| Start | Pausa | Pausa | Pausa |
| Select | Co-op | Co-op | Co-op |

- X, Y, L2 and R2 stay free for now (the Ferma power-ups in 0.7 are a candidate).
- Each minigame's own meanings show in the pause «Comandi» tab and in a short tutorial the first time the minigame is unlocked.
- Opzioni › Controller: generic action names, remap one action at a time («premi…»), «Ripristina Pocket Taco», on-screen controls on/off.
- Input through the browser's gamepad support. The Pocket Taco's button numbers are first checked on the owner's phone with a dev-only button test screen (Chrome first, then the Android wrapper).
- Co-op: each device chooses its own mode; mixed sessions work because only game state is shared.
- PC: handheld mode with a gamepad or keyboard (upper area highlighted) is in 0.9, low priority.
- First delivery (0.5_N, before 0.6 M0): button test screen; Mangiaroccia and Ferma laid out above the controller; pause bar with its overlays; menu navigation by D-pad; Opzioni › Controller. Other screens keep the normal layout until 0.7.
- Design reference: the owner's design canvas «Mr. Stone — Modalità portatile e 1.0» (claude.ai, private to the owner).

## 8. Pets — Usagi's quest (0.7)
- Two pets share one slot: Usagi (the owner's dog) and Felix (Algidone's cat). They are different characters; the player picks one in Negozio, where the other characters are. A pet's Giocatori card stays hidden until its first successful rescue.
- Appearance: in Mangiaroccia and Ferma Algidone! runs, from girone 9 on, 25% chance per girone, at most once per run.
- Rescue: the player walks over the pet; it follows them for the rest of the run, drawn with the selected pet's sprites.
- The pet only has to survive the girone where it was found. If the player loses a life in that girone, the pet is lost; it can reappear with a 10% chance, then 5% after a second loss. After that girone it dies and respawns with the player.
- Reward at the end of the run (win or loss): a popup animation on the way back to the menu, then the reward is credited.
  - Usagi spots a hole, runs to it and digs: a truffle = one extra life for the next run (30%), a bone = +20% of the current run's score (70%).
  - Felix sees an open bakery window and jumps in from the street: a golden nugget = one extra life for the next run (30%), a fish bone = +20% of the current run's score (70%).
- Art: made by the owner in Firefly from one master image per pet; every other frame is an edit of the master. Claude derives the second frame of each animation (mirrors, leg shifts), normalises scale, ground line and palette, and sends GIF previews for approval. Frame list and prompts: the owner's guide «Pet art: frame list and Firefly prompt guide (Usagi, Felix)». When coded, the pets enter the skin tool (SKIN_DEF, CLAUDE.md §6 rule 11).

## 9. Risks
- Phone hosts in real-time co-op (screen lock, background, lag) → co-op spike; Worker fallback (§3).
- Mangiaroccia co-op is the hardest design → C0.
- Testing several players at once → Playwright with 2–3 browser contexts per round from the start of 0.8.
- Firefly character consistency → pilot (master + 2 frames) before the full set; fallbacks: a partner model or a private Custom Model.
- Gamepad support inside the Android wrapper is unverified → the button test screen is the first handheld build.
