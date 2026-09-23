# Mangiasassi
Italian-language 2D mobile game in the style of Pac-Man. Single self-contained HTML file, open source.

**Live build:** https://ciprognola.github.io/mangiasassi/ (redeploys automatically on every push to `main`)
**Current milestone:** v0.3 — see [CHANGELOG.md](CHANGELOG.md) for the full build-by-build log.

## How the project works
- `index.html` = the current live build. Only the maintainer replaces it; its own `const VERSION`
  (e.g. `"0.3_1"`) is the source of truth for which build is running — check it with
  `grep -n 'const VERSION' index.html` rather than the root `VERSION` file, which predates the
  current build process and is no longer kept in sync.
- `CHANGELOG.md` = the detailed, one-entry-per-build history.
- `submissions/` = developer packages (text, audio, sprites) waiting for verification.
- `android/` = Android WebView wrapper.

Developers: read [CONTRIBUTING.md](CONTRIBUTING.md).
