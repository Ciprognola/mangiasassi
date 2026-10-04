#!/usr/bin/env python3
"""0.4.5_10 (U4) tests: rank names per character (career modal + celebrate), arrow-key navigation of the menu tiles and popup buttons
(visible ring only after a key, never for touch), menu music on Obiettivi / Percorso / Personalizza and not in the maze.
Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_u4.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

ROCCIA = ["Recluta", "Allievo pilota", "Pilota", "Capitano", "Maggiore", "Comandante", "Colonnello", "Asso", "Leggenda", "Maestro dei cieli", "Re delle pietre"]
ALG = ["Mangiatore modesto", "Usurpatore di Snacks", "Snacks Manager", "Mangiatore Professionista", "Bevitore di Bevande", "Re degli Snacks", "Amico del Colesterolo", "Perfettamente Sferico", "Regina delle Bevande", "Abbuffatore Seriale"]
LV_ROCCIA = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
LV_ALG = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90]
RING = "[...document.querySelectorAll('.kf')].map(e=>e.dataset.tile||e.id||e.textContent.trim().slice(0,20))"

with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    sv = save(); sv["p"]["ch"]["roccia"]["lvl"] = 55; sv["p"]["ch"]["algidone"]["lvl"] = 55
    ctx, p, errs = page(b, site="stable", local=norm(b, sv), toggle=False, dev=False)
    settle(p, 600)

    # ---------------- ranks
    for ck, names, LV in (("roccia", ROCCIA, LV_ROCCIA), ("algidone", ALG, LV_ALG)):
        p.evaluate("S.p.char='%s';go('menu')" % ck); p.wait_for_timeout(300)
        p.click("#career"); p.wait_for_selector(".ms"); rk = p.evaluate("[...document.querySelectorAll('.ms .rk')].map(e=>e.textContent)")
        lv = p.evaluate("[...document.querySelectorAll('.ms .n')].map(e=>e.textContent)")
        exp = [n if LV[i] <= 55 else "???" for i, n in enumerate(names)]
        check(f"career modal ({ck}): the milestone list uses that character's ranks at the same thresholds (unreached = ???)", rk == exp and lv == ["Liv.%d" % l for l in LV], rk)
        p.click("#ok"); p.wait_for_timeout(150)
        r = p.evaluate("[%s].map(l=>rankOf(l,'%s'))" % (",".join(map(str, [1, 9, 10, 19, 20, 55, 99, 100])), ck))
        want = [names[0], names[0], names[1], names[1], names[2], names[5], names[9], names[10] if len(names) > 10 else names[9]]
        check(f"rankOf({ck}) follows the thresholds", r == want, r)
        p.evaluate("celebrate(9,10,null,'%s')" % ck); p.wait_for_timeout(200)
        txt = p.evaluate("document.querySelector('#modal').innerText")
        check(f"celebrate ({ck}, level 10): «Nuovo traguardo» with the character's own rank «{names[1]}»", "Nuovo traguardo" in txt and names[1] in txt and (ROCCIA[1] not in txt or ck == "roccia"), txt[:140])
        p.evaluate("closeModal()")
        p.evaluate("celebrate(10,11,null,'%s')" % ck); p.wait_for_timeout(150)
        check(f"celebrate ({ck}): a normal level-up has no rank line", "Livello 11" in p.evaluate("document.querySelector('#modal').innerText"))
        p.evaluate("closeModal()")
    check("RANKS has 11 thresholds (1..100), RANKS_ALG has 10 (1..90, covering through 100) and they share the first 10",
          p.evaluate("Object.keys(RANKS).length===11 && Object.keys(RANKS_ALG).length===10 && Object.keys(RANKS).slice(0,10).join()===Object.keys(RANKS_ALG).join()"))
    p.evaluate("S.p.char='roccia';go('menu')"); p.wait_for_timeout(300)

    # ---------------- arrow navigation on the menu
    tiles = p.evaluate("[...document.querySelectorAll('#root .tile[data-tile]')].map(e=>e.dataset.tile)")
    check("(precondition) no ring before any key", p.evaluate(RING) == [])
    seen = set(); order = []
    for k in ["ArrowDown"] * (len(tiles) + 2) + ["ArrowRight", "ArrowLeft"] + ["ArrowUp"] * (len(tiles) + 2):
        p.keyboard.press(k); p.wait_for_timeout(40)
        r = p.evaluate(RING); check_one = len(r) <= 1
        if not check_one:
            check("ring: never more than one element", False, r)
        if r: seen.add(r[0]); order.append(r[0])
    check("arrow keys reach every menu tile (%s)" % ",".join(tiles), seen >= set(tiles), (sorted(seen), tiles))
    check("the ring is a visible outline", p.evaluate("(()=>{const e=document.querySelector('.kf');return !!e&&parseFloat(getComputedStyle(e).outlineWidth)>=2})()"))
    # Enter activates the focused tile: go to «Opzioni»
    p.evaluate("KNAV.off()")
    for _ in range(len(tiles) + 3):
        p.keyboard.press("ArrowDown"); p.wait_for_timeout(30)
        if p.evaluate(RING) == ["opt"]: break
    check("(precondition) ring on «Opzioni»", p.evaluate(RING) == ["opt"], p.evaluate(RING))
    p.keyboard.press("Enter"); p.wait_for_timeout(400)
    check("Enter activates the focused tile (Opzioni opens), ring gone", p.evaluate("screen") == "opt" and p.evaluate(RING) == [])
    p.evaluate("go('menu')"); p.wait_for_timeout(300)
    # mouse / touch removes the ring
    p.keyboard.press("ArrowDown"); p.wait_for_timeout(60)
    had = p.evaluate(RING) != []
    p.mouse.move(5, 5); p.mouse.down(); p.mouse.up(); p.wait_for_timeout(60)
    check("a pointer press hides the ring", had and p.evaluate(RING) == [])
    # arrows do nothing in the maze
    p.click("[data-tile=new]"); pick_maze(p); p.wait_for_function("G&&G.state==='play'", timeout=8000)
    p.keyboard.press("ArrowLeft"); p.wait_for_timeout(100)
    check("in the maze the arrows still steer (no ring, no interference)", p.evaluate(RING) == [] and p.evaluate("G.pl.next===3||G.pl.dir===3"))
    # ---------------- popup buttons
    p.evaluate("cancelAnimationFrame(raf);go('menu')"); p.wait_for_timeout(300)
    p.evaluate("confirmBox('Prova','Test','Sì','No',()=>{window.__y=1},()=>{window.__n=1})"); p.wait_for_timeout(200)
    p.keyboard.press("ArrowRight"); p.wait_for_timeout(50)
    r1 = p.evaluate(RING); p.keyboard.press("ArrowLeft"); p.wait_for_timeout(50); r2 = p.evaluate(RING)
    check("popup: arrows move the ring between its buttons", len(r1) == 1 and len(r2) == 1 and r1 != r2, (r1, r2))
    p.keyboard.press("Enter"); p.wait_for_timeout(200)
    check("popup: Enter activates the focused button and closes it", not p.evaluate("!!document.querySelector('#modal .ov')") and (p.evaluate("!!(window.__y||window.__n)")))
    p.evaluate("confirmBox('Prova','Test','Sì','No',()=>{},()=>{})"); p.wait_for_timeout(150)
    p.keyboard.press("Enter"); p.wait_for_timeout(150)
    check("popup with no ring: Enter does what it did before (nothing on a two-button popup)", p.evaluate("!!document.querySelector('#modal .ov')"))
    p.evaluate("closeModal()")
    p.evaluate("celebrate(9,10,null,'roccia')"); p.wait_for_timeout(150)
    p.keyboard.press("Enter"); p.wait_for_timeout(200)
    check("single-button popup: the existing Enter shortcut still closes it", not p.evaluate("!!document.querySelector('#modal .ov')"))
    check("no console errors (keyboard/ranks)", not errs, errs); ctx.close()

    # ---------------- touch users never see the ring
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False, has_touch=True)
    settle(p, 600)
    p.tap("[data-tile=opt]"); p.wait_for_timeout(300); p.evaluate("go('menu')"); p.wait_for_timeout(300)
    p.tap("#career"); p.wait_for_timeout(200)
    check("touch: taps never leave a ring", p.evaluate(RING) == [])
    ctx.close()

    # ---------------- music
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=False)
    settle(p, 600)
    p.evaluate("S.opts.music=true;window.__pl=0;window.__pa=0;const o=bgm.play,q=bgm.pause;bgm.play=function(){window.__pl++;return o.apply(this,arguments)};bgm.pause=function(){window.__pa++;return q.apply(this,arguments)};0")
    for scr in ("menu", "ach", "road", "cust", "wish", "opt"):
        p.evaluate("window.__pl=0;window.__pa=0;go('%s')" % scr); p.wait_for_timeout(500)
        s = p.evaluate("({want:musicWanted(),pl:window.__pl,pa:window.__pa})")
        check(f"menu music wanted and started on «{scr}»", s["want"] and s["pl"] > 0 and s["pa"] == 0, s)
    p.evaluate("go('menu')"); p.wait_for_timeout(300); p.click("[data-tile=new]"); pick_maze(p); p.wait_for_function("G&&G.state==='play'", timeout=8000)
    p.evaluate("window.__pl=0;window.__pa=0;syncMusic()"); p.wait_for_timeout(300)
    s = p.evaluate("({want:musicWanted(),pl:window.__pl,pa:window.__pa,paused:bgm.paused})")
    check("the maze stays silent (music not wanted, paused)", not s["want"] and s["pa"] > 0 and s["pl"] == 0 and s["paused"], s)
    check("no console errors (music)", not errs, errs); ctx.close()
    b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
