# Torneo Appalokniax — demo

Annuncio interattivo del torneo Appalokniax: una chat con il professore di Mangiasassi, nello stesso stile
della scena «Roccia no» (box di dialogo Pokémon, testo a macchina da scrivere con i blip, ping a ogni tocco).

Apri `index.html` in un browser: è un file unico, con sprite e musica già dentro.

## Cosa succede

1. Schermo nero, il professore chiede: «Benvenuto al torneo di Appalokniax! Pensi di averne la stoffa?» → Sì / No.
2. **No** → una delle 5 risposte del professore, in ordine casuale, mai ripetute finché non sono uscite tutte
   (poi si rimescola, e mai la stessa due volte di fila). Poi di nuovo Sì / No.
3. **Sì** → «Ottimo! Gran bella scelta!», poi il professore compare al centro con la musica d'introduzione.
4. Due battute sul torneo; il professore scivola a destra e al centro compare un'arena pixel art con la folla
   che esulta (suono sintetizzato); battuta finale sull'arena.
5. Torna al centro, lo sfondo torna nero, ultima battuta («… Buona fortuna!»), dissolvenza e «Ricomincia».

## File

| Percorso | Cosa |
|---|---|
| `index.html` | la demo giocabile (generata, non modificarla a mano) |
| `src/demo.html` | il sorgente: CSS, markup e script, con due segnaposto per gli asset |
| `assets/` | asset presi da Mangiasassi `main`: `PRSPR.idle` (7 frame), `PRSPR.blink` (3 frame del ritratto), `PR_INTRO_B64` (musica) |
| `build.py` | `python3 build.py` → riscrive `index.html` (e `dist/artifact.html`) inserendo gli asset in base64 |

## Da dove viene il codice

Ripreso dal minigioco del professore in `index.html` di `main` (sezione `PROFESSORE (minigioco "Roccia no")`):
`prSay` / `prChoice` / `prBlack` / `prAlpha` / `prBlip` / `prPing` / `prDrawProf` e il CSS `.prs .pdlg .pmenu`.
Nuovi in questa demo: l'arena pixel art (`drawArena`), la folla (`crowdStart` / `crowdStop`) e lo scorrimento
laterale del professore (`S.side`).
