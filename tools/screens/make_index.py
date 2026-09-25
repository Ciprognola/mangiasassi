#!/usr/bin/env python3
"""Writes refs/screens/SCREENS.md from the PNGs present in refs/screens/ + the metadata below.
Run after capture.py:  python tools/screens/make_index.py
Ids are canonical (F5/F6 send them): never rename one without updating this table and saying so in the CHANGELOG."""
import os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "refs", "screens")

# prefix or exact id -> (how to reach it, `screen`/modal, main functions, notes). Longest matching key wins.
META = {
    "splash-question": ("Open the game", "`screen=\"splash\"`", "`renderSplash` (splash), `#rsi` / `#rno`", "Roccia sì / Roccia no"),
    "menu-home-roccia": ("Roccia sì → menu (Uomo roccia selected, mid-game save)", "`menu`", "`renderMenu`, `bindMenu`, `startMenuScene`", "Home with the two split tiles (Nuovo gioco / Hardcore) because the seed save has passed girone 5"),
    "menu-home-algidone": ("Same, Algidone selected", "`menu`", "`renderMenu`", ""),
    "menu-home-fresh": ("Fresh save: before girone 5 the Nuovo gioco tile is not split", "`menu`", "`renderMenu`", ""),
    "menu-home-nuovo-hardcore": ("After girone 5: Nuovo gioco / Hardcore choice on the home tile", "`menu`", "`renderMenu` (`tsplit`), `tileAction`", "This is the \"Nuovo gioco / Hardcore\" choice"),
    "career-modal": ("Home → level bar (`#career`)", "modal", "`careerModal`", ""),
    "opt-generali": ("Home → Opzioni", "`opt`", "`renderOpt`, `bindOpt`, `optAcc`", "Generali tab; `-audio/-screen/-game/-data` = that accordion open"),
    "opt-login-modal": ("Opzioni → tap \"Build locale\" 5 times", "modal", "`loginModal`", "Old local dev login (replaced by Firebase in F1)"),
    "dev-tab": ("Opzioni → Sviluppatore tab (dev mode on)", "`opt`, `optTab=\"dev\"`", "`devRows`, `bindDev`", "One image per accordion: `dev-acc-<id>`"),
    "dev-acc": ("Sviluppatore tab → open the accordion", "`opt`, `optTab=\"dev\"`", "`devRows`, `optAcc`, `gamDevHTML`, `prDevPanel`", "account = Sblocca tutto, test = jumps/level, audio = sounds, obj = Anteprime (popup previews), exp = Consegna / Esporta modifiche"),
    "dev-menu-home": ("Dev mode on, home", "`menu`", "`renderMenu` (`devUI()` pens, +)", "Dev pens on every tile"),
    "wish-enemies": ("Home → Lista desideri → first tab (aerei / attrezzi)", "`wish`, `tab=\"planes\"`", "`renderWish`, `cardHTML`", "Enemies list; per character"),
    "wish-items": ("Lista desideri → second tab (rocce / snack)", "`wish`, `tab=\"rocks\"`", "`renderWish`, `cardHTML`", "Per character"),
    "wish-giocatore-locked": ("Lista desideri → Giocatore, fresh save", "`wish`, `tab=\"player\"`", "`renderWish`", "Locked cards"),
    "wish-giochi-locked": ("Lista desideri → Giochi, fresh save", "`wish`, `tab=\"games\"`", "`gamesHTML`", "Locked cards"),
    "wish-giocatore-unlocked": ("Same with Sblocca tutto (dev overlay)", "`wish`, `tab=\"player\"`", "`renderWish`", ""),
    "wish-giochi-unlocked": ("Same with Sblocca tutto (dev overlay)", "`wish`, `tab=\"games\"`", "`gamesHTML`", "G4 Ferma Algidone! with the floor buttons"),
    "wish-giocatore-personalizza": ("Giocatore with a costume owned", "`wish`, `tab=\"player\"`", "`renderWish`", "\"Personalizza\" button appears"),
    "ach-": ("Home → trophy button (`#trop`) → category tab", "`ach`", "`renderAch`, `bindAch`", "gen = Generali, roc = Uomo roccia, alg = Algidone, gio = Giochi, min = Minigiochi"),
    "road-": ("Home → path button (`#road`)", "`road`", "`renderRoad`, `bindRoad`, `roadState`", ""),
    "popup-milestone-real": ("Real save with the professor seen → home", "modal", "`popShow`, `scanNewUnlocks`", "Real milestone popup on the home menu"),
    "popup-": ("Dev preview of the popup (`popPreview`) over the home menu", "modal", "`popShow`, `popPreview`", "Same modal a real unlock shows; `popup-achievement` = the achievement toast"),
    "gift-": ("Percorso → tap the pulsing tile 3", "modal", "`roadClaim`, `giftCv`", "closed = before the tap, opened = reward revealed"),
    "cust-": ("Lista desideri → Giocatore → Personalizza", "`cust`", "`renderCust`, `bindCust`", "`-skin-on` = costume selected"),
    "bug-popup": ("Logged-in dev: tap the bug icon in any top bar (F6a)", "modal", "`bugOpen`, `bugFreeze`, `bugSubmit`, `screenId`", "Freezes the game like its pause (no pause menu); Indietro resumes"),
    "export-dialog": ("Opzioni → Sviluppatore → Oggetti/Esporta accordion → Esporta modifiche", "modal", "`exportDialog`, `exportBuild`", ""),
    "maze-intro": ("Home → Nuovo gioco", "`game`, `G.state=\"ready\"`", "`startGame`, `buildGameDOM`, `draw`", "Girone intro card (\"Pronti?\")"),
    "maze-play": ("Home → Nuovo gioco, ~3 s", "`game`", "`startGame`, `update`, `draw`", "Random map theme"),
    "maze-pause": ("Maze → ❚❚", "modal", "`pauseMenu`", ""),
    "maze-over": ("Maze, last life lost", "`over`", "`finishRun`", "Partita finita; state forced (`G.lives=1`, dying) on a dev run"),
    "maze-": ("Dev run on the theme's map (Opzioni → Sviluppatore → Test → Mappa select + Vai)", "`game`", "`devJump`, `draw`, `THEMES`", "Themes: steel, water, fire, ice, forest. `acciaio`/`cinghiale` = ability active"),
    "bj-invite": ("Opzioni → Sviluppatore → Minigiochi → El Gamblador (dev run)", "`bj`", "`startGamblador`, `bjPresent`", "In a real run the same card appears in the gap after a girone"),
    "bj-": ("El Gamblador dev run, scripted hand (Enter advances, menu clicks)", "`bj`", "`bjMain`, `bjHand`, `bjChoose`, `bjDraw`", "Random deal: the hand result varies"),
    "pr-": ("Splash → Roccia no → Sì (real run)", "`pr`", "`prIntro`, `prIntroYes`, `prSay`, `prChoice`", ""),
    "pb-": ("Professor battle (real run, forced win)", "`pr`, `PR.pb`", "`pbFight`, `pbCommand`, `pbAsk`, `pbEnding`", "Foe HP set to 1 by the script to reach the win ending"),
    "fa-invite": ("Dev run in the maze → `faInvite` (same modal as the real encounter)", "modal", "`faInvite`", "Called directly: the real one is random in the gap after a girone"),
    "fa-": ("Opzioni → Sviluppatore → Test → Ferma Algidone! buttons (dev runs)", "`fa`", "`startFerma`, `faLoop`, `faDraw`, `faIntro`, `faPanel`", ""),
}


def lookup(i):
    keys = [k for k in META if i == k or i.startswith(k)]
    if not keys:
        return ("", "", "", "")
    return META[max(keys, key=len)]


def main():
    ids = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith(".png"))
    size = sum(os.path.getsize(os.path.join(OUT, f + ".png")) for f in ids)
    rows = []
    for i in ids:
        how, scr, fn, note = lookup(i)
        rows.append(f"| `{i}` | [{i}.png]({i}.png) | {how} | {scr} | {fn} | {note} |")
    nc = []
    p = os.path.join(os.path.dirname(__file__), "not_captured.txt")
    if os.path.exists(p):
        nc = [l.rstrip("\n") for l in open(p, encoding="utf-8") if l.strip()]
    md = ["# Screens library", "",
          "One 390×844 screenshot per screen/popup, generated by `tools/screens/capture.py` (Playwright, headless Chromium, root path of a local server) and indexed by `tools/screens/make_index.py`.",
          "**The ids are canonical** (F5 text edit and F6 bug reports send them): never rename one without updating this file and saying so in the CHANGELOG. Regenerate at each release (REL).", "",
          f"{len(ids)} screens, {size/1048576:.2f} MB.", "",
          "| id | image | how to reach it | `screen` / modal | main functions | notes |", "|---|---|---|---|---|---|"] + rows
    md += ["", "## Not captured", ""] + (nc if nc else ["(none)"])
    md += ["", "## Notes", "",
           "- Dev runs (`G.dev`), \"Sblocca tutto\" (SIM) and a few forced states (foe HP, last life, faInvite) are used only to reach content that is otherwise random or locked; they write no progress.",
           "- Animated screens are a single frame; the maze, Ferma and battle frames vary run to run (random map, item positions).",
           "- Achievement toasts (real ones) are hidden by the script; the debug achievements were removed in 0.4_2 (E1b).",
           "- The Ferma debug overlay is off by default since 0.4_2, so the `fa-*` frames are clean.",
           "- An earlier note said a mouse click on the El Gamblador stage crashes headless Chromium: that was the test setup (two capture runs at once), not the game (E1a/E1b). The script still advances dealer lines with Enter."]
    open(os.path.join(OUT, "SCREENS.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(len(ids), "screens", round(size / 1048576, 2), "MB")


if __name__ == "__main__":
    main()
