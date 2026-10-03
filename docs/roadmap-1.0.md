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
