#!/usr/bin/env python3
"""0.4.5_11 (S1) tests: game chooser at «Nuovo gioco»/«Hardcore» for Uomo roccia only, Ferma option enabled since 0.4.5_29 (was locked «In arrivo»), Algidone straight to the maze,
overwrite confirm first, nextMinigame follows the run's game. Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_s1.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

CH = "({modal:!!document.querySelector('#modal .ov'),title:(document.querySelector('#modal h3')||{}).textContent||'',run:!!G,game:G&&G.game,hard:G&&G.hard,lives:G&&G.lives,char:G&&G.char,screen:screen})"


def fresh(b, char="roccia", g5=True, quick=False):
    sv = save(); sv["p"]["char"] = char; sv["p"]["g5"] = g5
    ctx, p, errs = page(b, site="stable", local=norm(b, sv), toggle=False, dev=False)
    settle(p, 600)
    p.evaluate("G=null;go('menu')"); p.wait_for_timeout(300)
    return ctx, p, errs


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = fresh(b)
    p.click("[data-tile=new]"); p.wait_for_selector("[data-rg]")
    s = p.evaluate(CH)
    check("Uomo roccia: «Nuovo gioco» asks which game first (no run started yet)", s["modal"] and "partita" in s["title"].lower() and not s["run"], s)
    txt = p.evaluate("[...document.querySelectorAll('[data-rg]')].map(b=>({id:b.dataset.rg,t:b.textContent.trim(),dis:b.disabled}))")
    # 0.4.5_29 (FR1a1): the Ferma run exists now -- the option is enabled, no «In arrivo» (its own flow is tested in test_fr1a1.py)
    check("options: «Mangiaroccia» and «Ferma Algidone!» both available (FR1a1: no more «In arrivo»)", txt == [{"id": "maze", "t": "Mangiaroccia", "dis": False}, {"id": "ferma", "t": "Ferma Algidone!", "dis": False}], txt)
    p.click("#rgx"); p.wait_for_timeout(200)
    check("«Indietro» closes the chooser without starting anything", not p.evaluate("!!document.querySelector('#modal .ov')") and not p.evaluate("!!G"))
    p.click("[data-tile=new]"); p.wait_for_selector("[data-rg=maze]"); p.click("[data-rg=maze]"); p.wait_for_function("G&&G.state", timeout=8000)
    s = p.evaluate(CH)
    check("«Mangiaroccia» starts the maze run (G.game = maze, 3 lives, Uomo roccia)", s["run"] and s["game"] == "maze" and not s["hard"] and s["lives"] == 3 and s["char"] == "roccia" and s["screen"] == "game", s)
    ctx.close()

    ctx, p, errs = fresh(b)
    p.click("[data-tile=hard]"); p.wait_for_selector("[data-rg]")
    check("Hardcore also asks (and says so)", "Hardcore" in p.evaluate("document.querySelector('#modal p').textContent"))
    p.click("[data-rg=maze]"); p.wait_for_function("G&&G.state", timeout=8000)
    s = p.evaluate(CH)
    check("Hardcore → Mangiaroccia: maze with 4 lives and no refill (hard)", s["run"] and s["hard"] and s["lives"] == 4 and s["game"] == "maze", s)
    ctx.close()

    # overwrite confirm first
    ctx, p, errs = fresh(b)
    p.evaluate("S.quick={stage:3,score:100,lives:2,grid:[],en:[],pl:{}};persist()")
    p.click("[data-tile=new]"); p.wait_for_selector("#cy")
    check("with a quicksave the overwrite confirm still comes first", "Nuova partita" in p.evaluate("document.querySelector('#modal h3').textContent") and not p.evaluate("!!document.querySelector('[data-rg]')"))
    p.click("#cy"); p.wait_for_selector("[data-rg]", timeout=3000)
    check("…then, once confirmed, the game chooser", p.evaluate("!!S.quick")==False and p.evaluate("!!document.querySelector('[data-rg=maze]')"))
    ctx.close()

    # Algidone: straight to the maze
    for tile in ("new", "hard"):
        ctx, p, errs = fresh(b, char="algidone")
        p.click("[data-tile=%s]" % tile); p.wait_for_function("G&&G.state", timeout=8000)
        s = p.evaluate(CH)
        check(f"Algidone «{tile}»: straight into the maze, no chooser", s["run"] and s["char"] == "algidone" and s["game"] == "maze" and s["screen"] == "game" and not s["modal"], s)
        ctx.close()

    # nextMinigame follows the run's game
    ctx, p, errs = fresh(b)
    p.click("[data-tile=new]"); p.click("[data-rg=maze]"); p.wait_for_function("G&&G.state==='play'", timeout=8000)
    p.evaluate("cancelAnimationFrame(raf)")
    r = p.evaluate("(()=>{const o={};o.maze=nextMinigame().name;G.game='ferma';o.ferma=nextMinigame().name;S.ov['game_3']={label:'Ferma!!'};o.ov=nextMinigame().name;delete S.ov['game_3'];G.game='maze';S.ov['game_0']={label:'Sassi'};o.ov0=nextMinigame().name;delete S.ov['game_0'];G.game=undefined;o.legacy=nextMinigame().name;return o})()")
    check("nextMinigame(): Mangiaroccia for a maze run, Ferma Algidone! for a Ferma run, label overrides respected, old runs (no G.game) = maze", r == {"maze": "Mangiaroccia", "ferma": "Ferma Algidone!", "ov": "Ferma!!", "ov0": "Sassi", "legacy": "Mangiaroccia"}, r)
    p.evaluate("G.game='ferma';G.state='play';miniInterlude()"); p.wait_for_timeout(200)
    check("the interval card names the run's game", "Ferma Algidone!" in p.evaluate("document.querySelector('#modal').innerText"))
    p.evaluate("closeModal();G.game='maze';quicksave();G=null;go('menu')"); p.wait_for_timeout(300)
    p.click("[data-tile=cur]"); p.wait_for_function("G&&G.state", timeout=6000)
    check("quicksave/resume keeps the game (and an old save without it resumes as maze)", p.evaluate("G.game")=="maze")
    p.evaluate("cancelAnimationFrame(raf);(()=>{const c=JSON.parse(JSON.stringify(S.quick));delete c.game;S.quick=c;G=null;go('menu')})()"); p.wait_for_timeout(300)
    p.click("[data-tile=cur]"); p.wait_for_function("G&&G.state", timeout=6000)
    check("old quicksave without `game` resumes as a maze run", p.evaluate("G.game")=="maze")
    p.evaluate("G.lives=1;G.state='dying';G.t=0.01"); p.wait_for_selector("#ag", timeout=6000); p.click("#ag"); p.wait_for_function("G&&G.state", timeout=6000)
    check("«Ancora!» after a game over restarts the same game", p.evaluate("G.game")=="maze" and p.evaluate("G.stage")==1)
    check("no console errors", not errs, errs); ctx.close()
    b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
