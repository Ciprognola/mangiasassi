# Developer guide - Mangiasassi
How to send in text, colour, size, audio and sprite changes. No Git knowledge needed, everything can be done in the browser.

**Dev site (where you work):** https://ciprognola.github.io/mangiasassi/dev/ — the stable game stays at https://ciprognola.github.io/mangiasassi/. The dev site has its own save, so you can play and test freely.

> The buttons **Invia testi** and **Scarica pacchetto** are in the game from build 0.4_6, and the long-press text edit from 0.4_7. The skin tool is coming too.

## The big picture
1. You **log in** on the dev site and change things in developer mode.
2. **Texts, colours and sizes** are sent straight from the game (**Invia testi**) and reach the maintainer by themselves the next day. Nothing to upload.
3. **Audio and sprites** are downloaded as a ZIP (**Scarica pacchetto**) and uploaded to GitHub with the web upload.
4. The maintainer has Claude check and list every change. Approved changes go into the next build, which goes live automatically.

You never edit the game itself (`index.html`). Only checked builds go there, which keeps the game stable for everyone.

## Log in
1. Open the dev site, go to **Opzioni** and tap **Build locale** 5 times.
2. Type the **username** the owner gave you (just the name, like `dev3`, no `@`) and your password, then **Accedi**.
3. Login only works from the site (not from a file on your computer) and needs internet the first time. After that you stay logged in on that device, also offline.
4. There is no password reset by email. Forgot it? Ask the owner. To change it yourself: Opzioni → **Sviluppatore** → **Account** → **Cambia password**. **Esci** logs you out.

## Texts, colours and sizes (no upload)
1. Change what you want in developer mode.
2. Tap **Invia testi**. The changes go to the maintainer and appear in the repo the next day as a package in your name.
3. That's all. You can send again whenever you like.

### Editing a text: hold it for 3 seconds
Logged in with developer mode on, **press and hold any text for 3 seconds** (a yellow outline fills around it while you hold). A small window opens: it shows the screen, the current text, a box for your **Proposta**, an optional **Nota** and, for menu sections and card names, the colour and size. **Salva** keeps it; **Annulla** (or Esc) throws it away. The game pauses while the window is open.
- Menu sections, card names and the Gamblador/professor lines are edited **live**: you see the change right away.
- Any other text (battle moves, HUD, texts drawn in the game) has **«anteprima non disponibile»**: you don't see it change, it is sent as a *proposal* with the current text and its position, and the reviewer applies it by hand.
- Text drawn inside the game (on the canvas) can only be edited while the game is paused or a dialogue is waiting for you to tap. Menu texts and dialogue boxes work any time. Buttons and game controls are never edited by accident: the tap that ends a long press does nothing.
- If the current text contains placeholders in curly braces (like `{price}`), **keep them** in your proposal: the game fills them in.
- Then send it with **Invia testi** as above.

## Audio and sprites (ZIP + upload)
1. Add your audio/sprite files in developer mode, then tap **Scarica pacchetto**. You get a `.zip` with a `manifest.json` and your files (the game fills in every technical detail: sizes, frame data, what the file replaces).
2. Unzip it. You get a folder like this (the name is your account, the date is today):
```
submissions/
  dev3/
    2026-09-26/
      manifest.json
      eat.mp3
      plane.png
```
3. In the repo (https://github.com/Ciprognola/mangiasassi) switch to the branch **dev**, click **Add file -> Upload files** and drag the whole `submissions` folder in.
4. At the bottom choose **Create a new branch for this commit and start a pull request**, name the branch `dev3-2026-09-26`, click **Propose changes**, then **Create pull request**. **Make sure the pull request goes to `dev`** (not `main`).
5. Wait for the **validate** check (about a minute). **Green:** done. **Red:** click **Details**, read the message, fix the file (pull request -> **Files changed** -> "..." -> **Edit file** / upload again on the same branch); it re-runs by itself. Yellow warnings don't block you, but read them.

## "Before" and the base version — nothing to type
Every change remembers the game version you started from (the *base version*) and what the thing looked like then (the *before* value). The tool records both. If someone changed the same thing in the meantime, the reviewer sees «changed since 0.4_6» next to your change and the owner decides. You don't have to do anything.

## Rules
- **Assets never cross characters.** Uomo roccia uses only planes and rocks. Algidone uses only gym equipment and snacks. Use `shared` only for things truly used by both, and say why in the note.
- **All game text is in Italian.**
- **Limits** (the game is one HTML file with everything embedded, so size matters): audio `.mp3`/`.ogg`/`.wav` up to 300 KB each (bigger files are converted by Claude); sprites `.png`/`.webp` up to 200 KB each; text up to 500 characters; notes up to 300; 2 MB total per package.
- **Only add files inside your own folder** `submissions/<your account>/<date>/`. The check rejects anything else.
- **One package per topic.** Smaller packages are reviewed faster.
- Audio and sprite changes need a short **note** saying why.

## What happens after
The reviewer lists your changes for the owner. After approval they become one build on the dev site (you'll see the new version number in the corner), and later a release. Nothing you send is published before that.

## Found a bug?
Logged in, tap the small **bug icon** at the top of any screen: the game pauses, you write a few lines and send. The game adds the screen, version and device by itself. No internet? It is saved and sent later.

## Technical reference
The exact format is in [docs/submissions-v2.md](docs/submissions-v2.md). Old packages (`schemaVersion: 1`, see `submissions/_template` and `_example`) are still accepted.

## Audio target names (`type: audio`)
When you upload audio in dev mode, **the export fills in `target` for you** — you never type it by
hand. This table exists so you know which slot each `target` refers to, and what it sounds like until a
submission for it is approved. Every `target` here doubles as the key used internally once a submission
is hardcoded in (`BUILTIN_AUD`), so what you see in your exported `manifest.json` is exactly the name that
ends up shipped.

**Lookup order** (in every browser, for every one of these): your own dev-mode upload (stored locally,
until you tap "Ripristina" or wipe local data) → the shipped built-in track/sound (once a submission for
it has been approved and hardcoded into a build) → the game's original default (a synthesized sound
effect, or silence for voice lines, or the original embedded music track).

| `target` | What it is | Original default (before any submission) |
|---|---|---|
| `sound.uomoRoccia.eat` / `.foe` / `.power` / `.die` | Uomo roccia's 4 character sounds | Synthesized |
| `sound.algidone.eat` / `.foe` / `.power` / `.die` | Algidone's 4 character sounds | Synthesized |
| `sound.ach` | Achievement-unlocked jingle | Synthesized |
| `sound.gam.deal` / `.flip` / `.shuffle` / `.chip` / `.win` / `.lose` / `.push` / `.bj` / `.bust` / `.lighter` / `.select` / `.confirm` / `.collect` | El Gamblador's 13 table SFX | None (silent) |
| `sound.vo.<id>` — El Gamblador lines: `intro, pricefirst, pricenext, lighter, shuffle, deal, checkbj, turn, stand, double, surrender, playerbj, dealerbj, bust, dealerbust, win, lose, push, again, raise, raiseok, raiseback, broke, leave` | The dealer's 24 voice lines | None (silent) |
| `sound.vo.<id>` — Il Professore lines: `pr_q, pr_c_no, pr_c_yes, pr_no, pr_y1, pr_y2, pr_y3, pr_pk, pr_ang` | The professor's 9 voice lines | None (silent) |
| `sound.fa.jump` / `.land` / `.climb` / `.throw` / `.hit` / `.ping` / `.win` / `.low` / `.bolt` / `.belt` / `.flame` / `.collapse` | Ferma Algidone!'s 12 sound effects (`character: shared`; file names `sound_fa_<slot>.mp3`, e.g. `sound_fa_jump.mp3`): salto, atterraggio, passo sulla scala, lancio di Algidone, colpo/caduta, oggetto scavalcato, piano completato / vittoria finale, scorta bassa (beep every 2 s under 25 %), bullone tolto, avviso di inversione del nastro, vampata della griglia / fiamma, crollo finale (~1.6 s). No music for this mini-game | Synthesized |
| `music.menu` | Main menu music | The game's original menu track |
| `music.gam` | El Gamblador table music | The game's original table track |
| `music.pr.intro` / `.battle` / `.win` / `.lose` | Professor mini-game music (4 slots) | The game's original tracks for each |

## Making a costume in the game (`Carica costume`)
No drawing app skills beyond drawing itself needed — the game builds and cuts the sheet for you.
1. Opzioni → Sviluppatore → **Costumi**, pick a character, tap **Scarica foglio** (optionally «Parti da» an existing costume, to draw over what's already there). You get a `_GUIDE.png` (reference: shows every frame's real position) and a `_DRAW_HERE.png` (blank, transparent) — draw only on the second one, keeping the exact same canvas size.
2. Back in **Costumi**, under **Carica costume**: choose the character, a new costume's name (or "Aggiorna" an existing one, whose mode you can't change), Overlay/Replace for a new costume, then pick your finished `_DRAW_HERE.png` file(s) and tap **Importa**.
3. Check the **preview** right there in the game — it shows live everywhere that character's frames are drawn (maze, menu, Ferma Algidone!, everything), without touching your save. Fix and re-import if something looks off; the preview is replaced by each new import, never stacked.
4. Once happy, tap **Scarica pacchetto** (same as audio/sprites, §"Audio and sprites" above) — it includes every changed frame automatically. **The preview is only in memory: it's gone if you reload the page, so download the package before you do anything else.**
5. Unzip and upload through GitHub exactly like any other package (§"Audio and sprites", steps 2-5).

A brand-new costume isn't given to any player automatically — the owner decides how it's unlocked once it's approved.

## Skin delivery format (artists)
A skin (costume/accessory drawn on the character, always for **one** character: Uomo roccia or Algidone) arrives as art under `refs/skins/<skin>/`. A skin declares a render mode:
`overlay` (an accessory drawn on top of the base frame) or `replace` (drawn instead of the base frame, for a full costume that recolours the character). Frames a skin does not provide simply render without it.

**Pre-cut (preferred):** `refs/skins/<skin>/frames/sk_<skin>_<frameKey>.png`, one transparent PNG per frame, already cut (max 200 KB each), plus `refs/skins/<skin>/<skin>_frames.json` giving the `mode` and, per frame, `file, w, h, base_w, base_h, ox, oy`
(`ox, oy` = where the base frame's top-left sits inside the skin image: a skin frame can be **larger** than its base, e.g. a cap brim or a cape). `refs/skins/SPRITE_INVENTORY.md` lists every frame key per character with its pixel size, direction and use; artists draw against that list.

**Template + cells (optional fallback):** the artist draws on a template sheet and supplies a matching `<skin>_cells.json` describing the cell mapping; `refs/skins/cut_from_cells.py` cuts it into the same `sk_<skin>_<frameKey>.png` naming.

If a direction or frame is missing, the maintainer lists the missing frames and asks for them — they are never created or adapted for you.

## Questions
Open an issue on the repo or contact the maintainer directly.
