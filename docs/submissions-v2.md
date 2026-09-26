# Submission format v2 (schemaVersion 2)

Spec for developer submissions from build 0.4_6 on (chunk F3a defines it, F3b builds the game side). The validator is `scripts/validate_submission.py` (accepts v1 and v2); tests are `scripts/test_validate_submission.py` with fixtures in `submissions/_fixtures/`.

## 1. How changes travel

| Kind | From the game | To the repo | Package folder |
|---|---|---|---|
| text, colour, scale | «Invia testi» → Firestore `edits` (one doc per change, devs only, rules in `firestore.rules`) | the daily export workflow (`.github/workflows/bugs-export.yml`, `tools/bugs/export_bugs.py`) writes a normal package | `submissions/<acct>/<YYYY-MM-DD>-testi/` (written by the bot, committed to `dev`) |
| audio, sprite, skin | «Scarica pacchetto» → ZIP | the developer uploads it with GitHub's web upload as a PR to `dev` | `submissions/<acct>/<YYYY-MM-DD>/` |

`<acct>` is the **Firebase account name** (`dev1`…`dev5`, `master`), lowercase. The validator's «developer must match the folder name» rule applies to `<acct>`. Folder date = the UTC day of the export (bot) or the day the developer chose (ZIP). Several exports on the same day extend the same `-testi` package (merged by change `id`).

## 2. manifest.json

```json
{
  "schemaVersion": 2,
  "developer": "dev3",
  "baseVersion": "0.4_6",
  "site": "dev",
  "exportedAt": "2026-09-26T08:00:00Z",
  "note": "general note (1-1000 characters, required)",
  "changes": [ { ...change... } ]
}
```

| Field | Rule |
|---|---|
| `schemaVersion` | `2` |
| `developer` | the account name, equal to `<acct>` in the folder path |
| `baseVersion` | the game `VERSION` at export time (`0.4_6`; a text package written by the bot uses the oldest `base` among its changes). Recorded automatically, nothing to type |
| `site` | `"dev"` or `"stable"` — the site the edit was made on |
| `exportedAt` | ISO 8601 date-time |
| `note` | general note, required, ≤ 1000 characters |
| `changes` | non-empty list |

### change

| Field | Applies to | Rule |
|---|---|---|
| `id` | all | unique string inside the package (for edits: the Firestore doc id) |
| `type` | all | `text`, `colour`, `scale`, `audio`, `sprite`, `skin` (a costume from the F4 skin tool's «Carica costume» preview, F4b2) |
| `character` | all | `roccia`, `algidone` or `shared` (v1 used `uomoRoccia`; v2 uses `roccia`) — `shared` needs an explanation in `note` (warning). A `skin` change is always `roccia` or `algidone`, never `shared` (a costume belongs to one character) |
| `target` | all; **optional for text changes that carry a `locator`** | the same target keys as v1 (`sound.algidone.eat`, `dialogue.win`, `tile.new.color`, …; see DEVELOPERS.md). `skin` targets look like `skin.<skinId>.<frameKey>` (e.g. `skin.geka.f0`). Long-press edits (F5) of texts with no known key have no `target`: they are proposals identified by `locator` |
| `screen` | optional | canonical screen id from `refs/screens/SCREENS.md` (lowercase kebab, or `unknown:<screen>`) when the change is visible on a screen; produced by `screenId()`. `skin` changes use the character's own maze screen id |
| `locator` | text/colour/scale, optional | `{text: <current text>, pos: <short position hint>}` for text with no `target` key: `pos` = screen id + DOM path (`menu-home-roccia .brand[0]>h1[1]`) or `canvas #<id> x,y,w,h`. Filled by the long-press text edit (F5); the reviewer finds the string in the code from `text` + `screen` |
| `before` | all, required key | text/colour/scale: the value at `baseVersion` as a string (`null` if it did not exist). audio/sprite/skin: `{sha256 (64 hex), bytes, w?, h?, durationMs?}` of the asset at `baseVersion`, or `null` (a brand-new skin, or a frame the target skin didn't have yet) |
| `value` | text/colour/scale | new value, string, ≤ 500 chars. colour = `#rrggbb`; scale = a number between 0.5 and 2 written as text (`"1.2"`) |
| `file` | audio/sprite/skin | simple relative path inside the package (`..`, absolute paths and `\` are rejected). Audio > 300 KB goes under `flagged/` (only a warning; Claude converts it). `skin` files live at `skins/<skinId>/sk_<skinId>_<frameKey>.png`, native size (the sheet's own ×4 scale already undone) |
| `meta` | audio/sprite/skin, required | sprite: `{frameKey, w, h, anchor, ox, oy, base_w, base_h}` (positive integers for sizes, integers for `ox`/`oy`; `w`/`h` must equal the PNG's real size). skin: `{skinId, skinName, mode: "overlay"\|"replace", action: "new"\|"update", frameKey, w, h, ox, oy, base_w, base_h}` (same size/offset rules as sprite, plus a non-empty `skinId`/`skinName`/`frameKey` and a valid `mode`/`action`). audio: `{bytes, mime: "audio/…", durationMs}` (`bytes` must equal the file size). Filled in by the tool, never typed |
| `note` | all | ≤ 300 chars; **required for audio/sprite**, optional for text/colour/scale/skin (a skin change already identifies itself via `meta`) |
| `base`, `sentAt` | optional | per-change base version and send time (added by the text export) |

Limits (unchanged from v1): audio 300 KB (`flagged/` above), sprite/skin 200 KB per frame, text value 500 chars, note 300 chars, 2 MB per package. Unknown extra keys are ignored.

### `skin` changes come from the F4 skin tool

The developer downloads a character sheet («Scarica foglio», optionally «Parti da» an existing costume), draws on `DRAW_HERE`, and uploads it back through «Carica costume» (Opzioni → Sviluppatore → Costumi) for a local preview — never saved to progress. While a preview exists, «Scarica pacchetto» includes it: one `skin` change per (non-unchanged) frame, native size, targeting `skin.<skinId>.<frameKey>`. Updating an existing costume only exports frames that actually changed — a frame whose cut bytes exactly match the costume's own stored bytes («invariato» in the tool) is left out entirely, not re-sent. A new costume is not equipped by any player until the owner decides how it's unlocked (§8 "Costumi da assegnare" in CLAUDE.md).

### Firestore `edits` document (what «Invia testi» writes)
`uid, acct, kind (text|colour|scale), char, screen, target, locator, before, value (string ≤ 500), note (≤ 300, optional), base (VERSION), ts (server time), meta {site, …}` — exactly the keys allowed by `firestore.rules`. The export turns each doc into one change (`kind`→`type`, `char`→`character`, `base`, `ts`→`sentAt`; `uid` is dropped).

## 3. Processing (Claude Code, §5 of CLAUDE.md)
1. Run the validator on the package (`python3 scripts/validate_submission.py <folder>`).
2. List every change: `type · character · target · screen · file/value · size · base version · conflict · note`.
3. **Conflict check** against the latest `dev` build: compare each change's `before` with the target's current value (text/colour/scale: the string; files: the sha256/bytes of the embedded asset). Equal → normal. Different → «changed since `<baseVersion>`» in the review table; the owner decides. Target unknown in the current build → flagged.
4. Wait for the owner's approval, implement as one build, append to `submissions/PROCESSED.md`.

## 4. v1 packages
`schemaVersion: 1` packages (`submissions/_template`, `_example`) are still accepted, with their old rules (`date`, `V0.2_5`-style `baseVersion`, `uomoRoccia`). They have no `before`, so no conflict check.
