# Mangiasassi
Italian-language 2D mobile game in the style of Pac-Man. Single self-contained HTML file, open source.

**Live build:** https://ciprognola.github.io/mangiasassi/ (redeploys automatically on every push to `main`)
**Current milestone:** v0.4 "Ferma Algidone!" — see [CHANGELOG.md](CHANGELOG.md) for the full build-by-build log.

## How the project works
- `index.html` = the current live build. Only the maintainer replaces it; its own `const VERSION`
  (e.g. `"0.4"`, later `"0.4_1"`) is the source of truth for which build is running — check it with
  `grep -n 'const VERSION' index.html` rather than the root `VERSION` file, which predates the
  current build process and is no longer kept in sync.
- `CHANGELOG.md` = the detailed, one-entry-per-build history.
- `submissions/` = developer packages (text, audio, sprites) waiting for verification.
- `android/` = Android WebView wrapper.

Developers: read [CONTRIBUTING.md](CONTRIBUTING.md).

## Novità della 0.4 (player-facing)
- **Ferma Algidone!** — il nuovo minigioco: Algidone si è preso Coccia e tira salsicce, porchetta e carne. Sali fino a lui in 3 piani (Coccia, Macelleria, Fabbrica di salsicce), con nastri, bulloni, griglia e fiamme.
  Compare come incontro casuale tra un girone e l'altro (da 1 a 3 piani) e si allena dalla scheda nei Giochi.
- **Percorso** — 50 tessere, una per girone, con tessere speciali (pokéball, carte, Ferma Algidone!) e premi nel regalo.
- **Costumi e Personalizza** — Cappello GEKA SNC (Uomo roccia) e Costume BK (Algidone), da scegliere nella pagina Personalizza.
- **Popup di sblocco** — ti avvisano di nuovi asset, personaggi, minigiochi e traguardi.
- **Rocciamon** nei Giochi dopo la prima battaglia col Professore; 34 obiettivi, con la nuova categoria Minigiochi.
- **Audio** — musica del menu senza pausa nel loop, musica di battaglia e di vittoria/sconfitta al momento giusto.
- Difficoltà Facile / Media / Difficile anche in Ferma Algidone!.
