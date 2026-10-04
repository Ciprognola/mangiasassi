# Roadmap to 1.0 — new structure + co-op
Approved direction, 2026-10-03 (Claude chat). Starts only after v0.5 is released. Each phase is planned in Claude chat first; Claude Code executes chunks per CLAUDE.md §0.

## 1. Why
- index.html (0.5) is ~6.2 MB: ~5.6 MB is base64 assets (88 PNG, 5 MP3) and only ~640 KB is code (~8,200 lines, ~620 functions, one script). Every patch navigates one giant file and every submission must be hardcoded into it.
- 1.0's headline is co-op. Building it inside the monolith would mean building it twice. The previous plan (sandbox until 1.0, clean rebuild afterwards) is REPLACED: the 0.6 migration below is the new build.

## 2. Target structure
- Stays web (required by Discord Activities). Vite build; static output deployed by GitHub Pages as today; the Android WebView wrapper loads the built output.
- Code: one module per screen / minigame / system. Existing JS is ported as-is first; TypeScript for new modules, gradual conversion of the rest.
- Assets: real files under assets/<area>/ — no base64 in code. Existing per-file submission limits stay.
- Data: texts, dialogue, characters, skins and balancing values in JSON under data/. Game language stays Italian.
- Minigames: each split into a simulation layer (state + update(inputs, dt), no DOM/canvas/audio) and a render/input layer. Required for co-op and makes tests easier.
- Size budget: total game assets ≤ 512 MB; first load ≤ 20 MB; each minigame's assets lazy-loaded when it opens.

src/core/ boot, screens, save, audio, input, firebase
src/screens/ menu, Giochi, Percorso, Personalizza, Opzioni, …
src/minigames/<name>/ sim.(js|ts), view.(js|ts), roles.json
src/coop/ session client, lobby, spectator view
data/ JSON: texts, dialogue, characters, skins, balance
assets/<area>/ png / ogg / mp3
server/ Cloudflare Worker + Durable Object (from 0.8)

## 3. Co-op design (1.0)
- Session: up to 8 players, joined via invite link (browser) or a Discord voice channel (Activity). Lobby → minigame chosen (vote, host breaks ties) → roles filled up to that minigame's cap, everyone else spectates live → round → points added to the session scoreboard → session winner gets a reward.
- Role caps live in data per minigame. Ferma Algidone!: 2 climbers + 1 player-controlled Algidone. Other minigames defined in C0.
- Netcode: host-authoritative rounds over a relay room. The round host's client runs the simulation; other active players send inputs; the host broadcasts snapshots (~15/s) to all, spectators included. Host leaves → round void, session continues.
- Server: Cloudflare Worker + Durable Objects (SQLite-backed, Workers Free plan), one object per session: presence, roles, scoreboard, relay. The same Worker does the Discord OAuth token exchange. Firebase stays for accounts and saves.
- Web-first: co-op works in the browser before Discord; the Activity wraps the same build (Discord proxy/CSP URL mappings needed for Firebase and the Worker).

## 4. Release plan
| Release | Content |
|---|---|
| 0.5 | ships as planned (CLAUDE.md §10) |
| 0.6 «Fondamenta» | migration only — game identical, no new features |
| 0.7 | former 0.6 backlog (Usagi's quest, il Professore vs blackjack winners, El Gamblador «lascia o raddoppia», Ferma Algidone! power-ups + moving small ladders, prizes revision), built in the new structure with the sim/render split |
| 0.8 | co-op core: Worker + session room, lobby, invite link, spectating, scoreboard; first co-op minigame Ferma Algidone! (2+1) |
| 0.9 | Discord Activity; co-op for the remaining minigames; session rewards; balancing |
| 1.0 | co-op release |
Former 0.7 ideas (Ferma levels beyond the 3rd, il Professore / El Gamblador as playable characters) move after 1.0 unless there is room earlier.

## 5. 0.6 phases (chunk breakdown planned in Claude chat before each phase)
| Phase | Content | Model / effort |
|---|---|---|
| M0 | Read-only investigation: map screens, minigames, globals/shared state, save format and keys, Firebase calls, dev tools, tests. Output docs/releases/0.6-M0.md with a proposed module map. | Opus / medium |
| M1 | Extract embedded assets to files loaded at runtime; behaviour identical. | Sonnet / low–medium |
| M2 | Vite project; split code into modules in thin chunks, one area per chunk; sim/render split per minigame. | Sonnet / medium |
| M3 | Texts, dialogue, balancing → JSON; dev tools (Invia testi, Scarica pacchetto, skin tool, validator) retargeted to files; DEVELOPERS.md updated. | Sonnet / medium |
| M4 | Parity: Playwright suite + owner phone test vs 0.5; existing local and cloud saves load unchanged; switch the stable site. | Sonnet / medium + owner |
Rules during 0.6: no gameplay changes; every chunk phone-tested; save compatibility mandatory; numbering continues per CLAUDE.md §7.

## 6. Open decisions (settle in Claude chat)
- C0: co-op spec per minigame (roles, caps, scoring), reward type, Discord ↔ Firebase account link.
- Whether ported code is converted to TypeScript during 0.6 or gradually afterwards.
