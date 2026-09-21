# Developer guide - Mangiasassi
How to send in text, audio and sprite changes. No Git knowledge needed, everything can be done in the browser.

**Live test build:** https://ciprognola.github.io/mangiasassi/

## The big picture
1. You change things **locally** (in your own copy of the game, using developer mode).
2. You send the changes here as a **package** (a folder with a `manifest.json` + your files).
3. An automatic check verifies the package structure.
4. The maintainer has Claude verify and list every change. Approved changes are hardcoded into the next build (e.g. `V0.2_6`), which goes live automatically.

You never edit the game itself (`index.html`). Only verified builds go there. That keeps the game stable for everyone.

## One-time setup
1. You'll get an email from GitHub inviting you to the `mangiasassi` repository. Accept it (create a free GitHub account first if you don't have one).
2. Bookmark the repo: https://github.com/Ciprognola/mangiasassi

## Step 1 - Make your changes locally
1. Open the game and go to **Options**. Tap **Build locale** 5 times to enable developer mode.
2. Edit texts, audio or sprites as needed.
3. Tap **Esporta modifiche** to download your package (`.zip`). It contains the `manifest.json` and your files.

> Until the export button is in the game, build the package by hand: copy `submissions/_template/manifest.json`, fill it in, and put your audio/sprite files next to it.

## Step 2 - Prepare the folder on your computer
Create this exact structure (the export does it for you):

```
submissions/
  your-name/
    2026-09-21/          <- today's date, YYYY-MM-DD
      manifest.json
      eat.mp3
      plane.png
```
Use the same `your-name` every time, lowercase, no spaces.

## Step 3 - Upload it
1. In the repo, click **Add file -> Upload files**.
2. Drag the whole `submissions` folder into the page.
3. At the bottom choose **Create a new branch for this commit and start a pull request**. Name the branch `your-name-2026-09-21`.
4. Click **Propose changes**, then **Create pull request** and fill in the short form.

## Step 4 - Wait for the green check
A check called **validate** runs by itself in about a minute.
- **Green:** done. The maintainer will review it.
- **Red:** click **Details** and read the message, then fix it. To fix, open your pull request -> **Files changed** -> use the "..." menu on the file -> **Edit file** / delete and upload again on the same branch. The check re-runs automatically.
- Yellow warnings don't block you, but read them.

## manifest.json reference
| Field | Meaning |
|---|---|
| `schemaVersion` | Always `1` |
| `developer` | Your name, same as the folder |
| `date` | Same as the folder date |
| `baseVersion` | Version you built on, e.g. `V0.2_5` (see the `VERSION` file) |
| `changes` | List of changes (below) |

Each change:

| Field | Meaning |
|---|---|
| `type` | `text`, `audio` or `sprite` |
| `character` | `uomoRoccia`, `algidone` or `shared` |
| `target` | Which game element it replaces (the export fills this in) |
| `value` | New text (text changes only, max 500 characters) |
| `file` | File name inside your folder (audio and sprite only) |
| `note` | Short reason for the change (required) |

## Rules
- **Assets never cross characters.** Uomo roccia uses only planes and rocks. Algidone uses only gym equipment and snacks. Use `shared` only for things truly used by both, and say why in `note`.
- **All game text is in Italian.**
- **File limits** (the game is one HTML file with everything embedded, so size matters): audio `.mp3`/`.ogg`/`.wav` up to 300 KB each; sprites `.png`/`.webp` up to 200 KB each; 2 MB total per submission.
- **Only add files inside your own submission folder.** The check rejects anything else.
- **One submission per topic.** Smaller packages are reviewed faster.
- If the live build has moved on since you started (`VERSION` changed), you'll get a warning. That's fine, the reviewer checks for conflicts.

## Questions
Open an issue on the repo or contact the maintainer directly.
