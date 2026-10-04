#!/usr/bin/env python3
"""0.4.5_14 tests: dev jump to any girone (#jgN + #jgGo, next to #jg4/#jg7), real spec (gironeSpec/pickMap),
clamped to 1-20. Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_jg.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only


def open_jump_acc(p):
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details.acc:has(#jgGo)').open"):
        p.click("details.acc:has(#jgGo) > summary"); p.wait_for_timeout(250)


def jump_to(p, n):
    open_jump_acc(p)
    p.fill("#jgN", str(n)); p.click("#jgGo"); p.wait_for_timeout(500)


EXPECT = {
    1: {"cls": "S", "ghosts": [1, 1, 1]},
    2: {"cls": "S", "ghosts": [1, 1, 2]},
    8: {"cls": "L", "ghosts": [1, 1, 1, 3, 3]},
}


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    # ---------------- #jgN/#jgGo sit inside the accordion, alongside #jg4/#jg7 (still there)
    open_jump_acc(p)
    check("«Vai al girone» sits in the same accordion as #jg4/#jg7 (data-dev via the accordion body)",
          p.evaluate("!!document.querySelector('.accb[data-dev] #jgGo') && !!document.querySelector('.accb[data-dev] #jgN') && !!document.querySelector('.accb[data-dev] #jg4') && !!document.querySelector('.accb[data-dev] #jg7')"))
    p.evaluate("go('menu')"); p.wait_for_timeout(250)

    # ---------------- girones 1, 2, 8, 9, 15: real spec (class, ghost count, stages) via the real UI
    for g in (1, 2, 8, 9, 15):
        jump_to(p, g)
        r = p.evaluate("({stage:G.stage,cls:mapClassOf(G.mapi),n:G.en.length,stages:G.en.map(e=>e.stage),dev:G.dev,screen})")
        expSpec = p.evaluate("gironeSpec(%d)" % g) if g >= 9 else None  # g9+ is randomized: read what pickMap/resetActors actually used
        if g in EXPECT:
            want = EXPECT[g]
            check(f"«Vai al girone» {g}: real spec (class {want['cls']}, {len(want['ghosts'])} ghosts, stages {want['ghosts']})",
                  r["stage"] == g and r["cls"] == want["cls"] and r["n"] == len(want["ghosts"]) and r["stages"] == want["ghosts"] and r["screen"] == "game" and r["dev"], r)
        else:
            n_expected = {"S": 3, "M": 4, "L": 5}[r["cls"]]
            check(f"«Vai al girone» {g}: real spec (girone-9+ class {r['cls']}, {n_expected} ghosts, every ghost >= stage 2)",
                  r["stage"] == g and r["n"] == n_expected and all(s >= 2 for s in r["stages"]) and r["screen"] == "game" and r["dev"], r)
        p.evaluate("go('menu')"); p.wait_for_timeout(250)
    check("no console errors (jump to any girone)", not errs, errs)

    # ---------------- clamped to 1-20
    open_jump_acc(p)
    p.fill("#jgN", "0"); p.click("#jgGo"); p.wait_for_timeout(400)
    check("«Vai al girone» 0 is clamped to 1", p.evaluate("G.stage") == 1)
    p.evaluate("go('menu')"); p.wait_for_timeout(250)
    open_jump_acc(p)
    p.fill("#jgN", "999"); p.click("#jgGo"); p.wait_for_timeout(400)
    check("«Vai al girone» 999 is clamped to 20", p.evaluate("G.stage") == 20)
    p.evaluate("go('menu')"); p.wait_for_timeout(250)
    open_jump_acc(p)
    p.fill("#jgN", "-5"); p.click("#jgGo"); p.wait_for_timeout(400)
    check("«Vai al girone» -5 is clamped to 1", p.evaluate("G.stage") == 1)
    check("no console errors (clamping)", not errs, errs)

    # ---------------- #jg4/#jg7 and the map picker still work as before
    p.evaluate("go('menu')"); p.wait_for_timeout(250)
    open_jump_acc(p)
    p.click("#jg4"); p.wait_for_timeout(500)
    check("#jg4 unchanged: girone 4, class M, 4 ghosts", p.evaluate("G.stage") == 4 and p.evaluate("mapClassOf(G.mapi)") == "M" and p.evaluate("G.en.length") == 4)
    p.evaluate("go('menu')"); p.wait_for_timeout(250)
    open_jump_acc(p)
    p.click("#jg7"); p.wait_for_timeout(500)
    check("#jg7 unchanged: girone 7, class L, 5 ghosts", p.evaluate("G.stage") == 7 and p.evaluate("mapClassOf(G.mapi)") == "L" and p.evaluate("G.en.length") == 5)
    p.evaluate("go('menu')"); p.wait_for_timeout(250)
    open_jump_acc(p)
    p.select_option("#jmsel", "0"); p.click("#jmg"); p.wait_for_timeout(500)
    check("map picker unchanged: forces girone 4 with the chosen map (mi 0)", p.evaluate("G.stage") == 4 and p.evaluate("G.mapi") == 0)
    check("no console errors (#jg4/#jg7/map picker)", not errs, errs)
    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
