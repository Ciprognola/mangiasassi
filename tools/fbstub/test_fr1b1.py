#!/usr/bin/env python3
"""0.4.5_32 (FR1b1) tests: the Ferma run's per-loop difficulty (FA_RUN.loop: throw wait / item speed), the girone
loop bonus (girPts incl. the floor-end bite bonus, mult capped at multMax, shown as "Bonus girone xM +P" in the
same count-up as the floor bonus), and quicksave (snapshot at girone start, «Salva ed esci», «Gioco corrente»
dispatch on S.quick's shape, dev runs never save, cloud-save round trip). Reuses the harness of test_f2b.py.
Run: python tools/fbstub/test_fr1b1.py"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

BASE_REF = os.environ.get("BASE_REF", "433a3e0")
OLD_PORT = 8797
OLD_DIR = tempfile.mkdtemp(prefix="mgs_old_")
open(os.path.join(OLD_DIR, "index.html"), "wb").write(subprocess.run(["git", "show", BASE_REF + ":index.html"], cwd=ROOT, capture_output=True, check=True).stdout)
NEW_BASE, OLD_BASE = BASE, "http://127.0.0.1:%d/" % OLD_PORT

FREEZE = "(()=>{cancelAnimationFrame(FA.raf);window.requestAnimationFrame=()=>0;0})()"
QUIET = "(()=>{faIntroEnd();Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;0})()"
STEP = "(n=>{for(let i=0;i<n;i++)faStep(1/60)})"


def start_dev_run(p, girone=1):
    p.evaluate("(()=>{if(FA){FA.dead=true;FA=null}S.quick=null;go('menu');startFermaRun({girone:%d,dev:true})})()" % girone)
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def start_real_run(p, girone=1, tile="new"):
    p.evaluate("(()=>{if(FA){FA.dead=true;FA=null}G=null;S.quick=null;persist();go('menu')})()"); p.wait_for_timeout(300)
    if girone == 1:
        p.click("[data-tile=%s]" % tile); p.wait_for_timeout(300); p.click("[data-rg=ferma]")
    else:
        p.evaluate("startFermaRun({girone:%d%s})" % (girone, ',hard:true' if tile == 'hard' else ''))
    p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    p.evaluate(FREEZE)


def win_floor(p):
    p.evaluate(QUIET); p.evaluate("Object.assign(FA.cfg,{sausage:0,porchetta:0,meat:0,ladderP:0});FA.alg.wait=1e9;if(FA.level<2)faWin();else faFinalWin();" + STEP + "(1000)")
    p.evaluate("for(let i=0;i<1000&&FA.state!=='win';i++)faStep(1/60)")


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=True)
    settle(p, 600)

    # ---------------- a) loop factors at gironi 1,4,7,10,13,16,19
    GIRONI_A = [1, 4, 7, 10, 13, 16, 19]
    WANT_THROW = {g: max(0.6, 0.9 ** ((g - 1) // 3)) for g in GIRONI_A}
    WANT_ITEM = {g: min(1.3, 1.05 ** ((g - 1) // 3)) for g in GIRONI_A}
    for g in sorted(WANT_THROW):
        start_dev_run(p, g)
        base = p.evaluate("FA_LEVELS[FA.level].items")
        r = p.evaluate("({tmin:FA.cfg.throwMin,tmax:FA.cfg.throwMax})")
        ratio_min, ratio_max = r["tmin"] / base["throwMin"], r["tmax"] / base["throwMax"]
        check(f"a) girone {g}: throw wait factor ×{WANT_THROW[g]}", abs(ratio_min - WANT_THROW[g]) < 1e-6 and abs(ratio_max - WANT_THROW[g]) < 1e-6, (ratio_min, ratio_max, WANT_THROW[g]))
        it = p.evaluate("faSpawn('sausage')")
        item_ratio = it["speed"] / (p.evaluate("FA_ITEM.sausage.speed") * p.evaluate("FA.dm.spd"))
        check(f"a) girone {g}: item speed factor ×{WANT_ITEM[g]}", abs(item_ratio - WANT_ITEM[g]) < 1e-6, (item_ratio, WANT_ITEM[g]))
    check("no console errors (a, run)", not errs, errs)
    # practice and encounter: loop factor stays 1 regardless of "girone" (neither has FA.run)
    p.evaluate("(()=>{if(FA){FA.dead=true;FA=null}go('menu')})()"); p.wait_for_timeout(300)
    p.evaluate("startFerma({test:true,level:2})"); p.wait_for_function("FA&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE)
    base = p.evaluate("FA_LEVELS[FA.level].items")
    r = p.evaluate("({tmin:FA.cfg.throwMin,tmax:FA.cfg.throwMax})")
    check("a) practice: throw wait factor ×1 (no FA.run)", r["tmin"] == base["throwMin"] and r["tmax"] == base["throwMax"], r)
    it = p.evaluate("faSpawn('sausage')")
    check("a) practice: item speed factor ×1", abs(it["speed"] - p.evaluate("FA_ITEM.sausage.speed") * p.evaluate("FA.dm.spd")) < 1e-6, it)
    p.evaluate("(()=>{if(FA){FA.dead=true;FA=null}go('menu')})()"); p.wait_for_timeout(300)
    p.evaluate("startFerma({test:true,encounter:2})"); p.wait_for_function("FA&&FA.state==='intro'", timeout=15000); p.evaluate(FREEZE)
    r = p.evaluate("({tmin:FA.cfg.throwMin,tmax:FA.cfg.throwMax})"); base = p.evaluate("FA_LEVELS[FA.level].items")
    check("a) encounter: throw wait factor ×1 (no FA.run)", r["tmin"] == base["throwMin"] and r["tmax"] == base["throwMax"], r)
    check("no console errors (a, practice/encounter)", not errs, errs)

    # ---------------- b) loop bonus: gironi 1-3 no line, girone 4 x1.2, girone 16 x2 (cap); girPts resets; payout includes it
    for g, want_mult, want_line in ((1, 1.0, False), (2, 1.0, False), (3, 1.0, False), (4, 1.2, True), (16, 2.0, True)):
        start_dev_run(p, g)
        p.evaluate(QUIET); p.evaluate("FA.score=100;FA.run.girPts=100")  # one deliberate mid-floor point, girPts tracked live
        win_floor(p)
        r = p.evaluate("({txt:FA.run.girBonusTxt,cnt:FA.cnt,score0:100})")
        girPts_before_bonus = 100  # the floor-end bite bonus folds in server-side; reconstruct mult from the txt/cnt
        if want_line:
            mult_str = r["txt"].split("×")[1].split(" ")[0]
            check(f"b) girone {g}: bonus line shows ×{want_mult}", abs(float(mult_str) - want_mult) < 1e-6, r["txt"])
            # bonus math: floorBonus = cnt.bonus - gb, girPts = 100+floorBonus, gb = round(girPts*(mult-1))
            gb = int(r["txt"].split("+")[1])
            floor_bonus = r["cnt"]["bonus"] - gb
            check(f"b) girone {g}: bonus = round(girPts·(mult-1)) with girPts including the floor-end bonus",
                  gb == round((100 + floor_bonus) * (want_mult - 1)), (gb, floor_bonus, want_mult))
        else:
            check(f"b) girone {g} (loop 0): no «Bonus girone» line", r["txt"] is None, r)
        p.evaluate(STEP + "(90)")
        after = p.evaluate("FA.score")
        check(f"b) girone {g}: the count-up applied the full bonus (floor + girone) to the score", after == 100 + r["cnt"]["bonus"], (after, r["cnt"]))
    check("no console errors (b, bonus math)", not errs, errs)
    # girPts resets when the next level loads
    start_dev_run(p, 4); p.evaluate(QUIET); p.evaluate("FA.score=200;FA.run.girPts=200"); win_floor(p); p.evaluate(STEP + "(90)")
    before_advance = p.evaluate("FA.run.girPts")
    p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd();0")
    after_advance = p.evaluate("({girPts:FA.run.girPts,txt:FA.run.girBonusTxt})")
    check("b) girPts (and the bonus text) reset when the next level loads", before_advance > 0 and after_advance == {"girPts": 0, "txt": None}, (before_advance, after_advance))
    check("no console errors (b, girPts reset)", not errs, errs)
    # «Partita finita» numbers include the bonuses: runPayout on the bonus-inflated FA.run gives the same
    # gain/xp as a maze run holding the same score/girone/char/diff (isolates runPayout's own math from
    # each path's achievement side effects by resetting S.ach and comparing the fresh delta of each call)
    start_dev_run(p, 4); p.evaluate("FA.run.dev=false;0")  # turn a dev run real just for this numeric check (isolated, discarded)
    p.evaluate(QUIET); p.evaluate("FA.score=300;FA.run.girPts=300"); win_floor(p); p.evaluate(STEP + "(90)")
    scoreAfterBonus = p.evaluate("FA.score")
    p.evaluate("S.ach={prog:{},done:{}};0")
    r1 = p.evaluate("(()=>{const s0=S.p.sordi;const run=JSON.parse(JSON.stringify(FA.run));const o=runPayout(run);return{gain:S.p.sordi-s0,xp:o.xp,score:o.score,stage:o.stage}})()")
    p.evaluate("S.ach={prog:{},done:{}};0")
    r2 = p.evaluate("(()=>{cancelAnimationFrame(raf);startGame(false,{});cancelAnimationFrame(raf);G.stage=4;G.score=%d;const s0=S.p.sordi;const o=runPayout(G.run);return{gain:S.p.sordi-s0,xp:o.xp,score:o.score,stage:o.stage}})()" % scoreAfterBonus)
    check("b) «Partita finita»: runPayout gives the same sordi/xp for the bonus-inflated Ferma score as for an identical maze score/girone",
          r1 == r2 and r1["score"] == scoreAfterBonus and r1["stage"] == 4, (r1, r2))
    check("no console errors (b, payout)", not errs, errs)

    # ---------------- c) save mid-level, «Gioco corrente» -> girone-start snapshot (score/lives), fresh level, full bar
    start_real_run(p, 1)
    win_floor(p); p.evaluate(STEP + "(90)")
    p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd();0")  # now at girone 2, snapshot taken
    win_floor(p); p.evaluate(STEP + "(90)")
    p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd();0")  # girone 3
    win_floor(p); p.evaluate(STEP + "(90)")
    p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd();0")  # girone 4
    win_floor(p); p.evaluate(STEP + "(90)")
    p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd();0")  # girone 5 (loop 1, level index 1 = Piano 2)
    snap = p.evaluate("({girone:FA.run.girone,level:FA.level,score:FA.score,lives:FA.lives})")
    check("c) girone 5, level index 1 (Piano 2) after 4 advances", snap["girone"] == 5 and snap["level"] == 1, snap)
    p.evaluate("FA.score+=777;FA.jumps++;0")  # mid-floor progress the snapshot must NOT carry
    p.evaluate("faPause(true)"); p.click("#fapanel [data-fa=save]"); p.wait_for_timeout(300)
    r = p.evaluate("({screen,quick:S.quick})")
    check("c) «Salva ed esci»: menu, S.quick is the girone-5-start snapshot (not the +777 mid-floor score)",
          r["screen"] == "menu" and r["quick"]["game"] == "ferma" and r["quick"]["run"]["girone"] == 5 and r["quick"]["run"]["score"] == snap["score"] and r["quick"]["run"]["lives"] == snap["lives"], (r, snap))
    p.click("[data-tile=cur]"); p.wait_for_function("FA&&FA.run&&FA.state==='intro'", timeout=15000)
    r2 = p.evaluate("({girone:FA.run.girone,level:FA.level,score:FA.score,lives:FA.lives,bar:FA.bar.left===FA.bar.N})")
    check("c) «Gioco corrente»: girone 5, level 2 fresh, score/lives = the girone-start snapshot, bar full", r2["girone"] == 5 and r2["level"] == 1 and r2["score"] == snap["score"] and r2["lives"] == snap["lives"] and r2["bar"], r2)
    check("no console errors (c)", not errs, errs)
    ctx.close()

    # ---------------- d) maze quicksave/resume: golden, unchanged
    import functools, http.server, threading
    class OH(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    osrv = http.server.ThreadingHTTPServer(("127.0.0.1", OLD_PORT), functools.partial(OH, directory=OLD_DIR))
    threading.Thread(target=osrv.serve_forever, daemon=True).start()
    for label, base_url in (("old", OLD_BASE), ("new", NEW_BASE)):
        BASE = base_url
        ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=False)
        settle(p, 600)
        p.evaluate("(()=>{cancelAnimationFrame(raf);S.quick=null;G=null;devJump(1,0);cancelAnimationFrame(raf);G.dev=false;G.score=1234;G.girPts=77;G.state='play';quicksave()})()")  # devJump(mi=0) forces the SAME map on both builds (a random pickMap would differ page to page)
        before = p.evaluate("JSON.stringify(S.quick)")
        p.evaluate("(()=>{cancelAnimationFrame(raf);G=null;go('menu')})()"); p.wait_for_timeout(300)
        p.click("[data-tile=cur]"); p.wait_for_function("G&&(G.state==='ready'||G.state==='play')", timeout=5000); p.wait_for_timeout(200)
        after = p.evaluate("JSON.stringify({run:G.run,mapi:G.mapi,grid:G.grid})")
        if label == "old":
            old_res = (before, after, list(errs))
        else:
            new_res = (before, after, list(errs))
        ctx.close()
    BASE = NEW_BASE
    check("d) maze quicksave (the object written to S.quick) identical to " + BASE_REF, old_res[0] == new_res[0], {"old": old_res[0][:150], "new": new_res[0][:150]})
    check("d) maze resume (G.run/mapi/grid after «Gioco corrente») identical to " + BASE_REF, old_res[1] == new_res[1], {"old": old_res[1][:150], "new": new_res[1][:150]})
    check("no console errors (d, old build)", not old_res[2], old_res[2])
    check("no console errors (d, new build)", not new_res[2], new_res[2])

    # ---------------- e) dev Ferma run: no «Salva ed esci», S.quick never written
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=True)
    settle(p, 600)
    start_dev_run(p, 3)
    p.evaluate(QUIET); p.evaluate("faPause(true)")
    btns = p.evaluate("[...document.querySelectorAll('#fapanel [data-fa]')].map(b=>b.dataset.fa)")
    check("e) dev run pause menu: no «save» entry", "save" not in btns, btns)
    check("e) dev run: S.quick untouched by the whole flow so far", p.evaluate("S.quick") is None)
    p.evaluate("faPause(false)")
    win_floor(p); p.evaluate(STEP + "(90)"); p.click("#fapanel [data-fa=next]"); p.evaluate("faIntroEnd();0")
    check("e) dev run: S.quick still untouched after a girone advance", p.evaluate("S.quick") is None)
    check("no console errors (e)", not errs, errs)
    ctx.close()

    # ---------------- f) a Ferma S.quick survives the cloud-save upload string round trip
    ctx, p, errs = page(b, site="stable", local=save(), toggle=False, dev=False)
    settle(p, 600)
    quick = {"game": "ferma", "run": {"girone": 8, "score": 4200, "girPts": 0, "girBonusTxt": None, "lives": 2, "hard": True, "game": "ferma", "char": "roccia", "diff": "hard", "dev": False}}
    p.evaluate("(q)=>{S.quick=q;persist()}", quick)
    r = p.evaluate("(()=>{const pay=cloudLocal().pay;return{pay,quickBack:JSON.parse(pay).quick}})()")
    check("f) S.quick (Ferma shape) survives cloudLocal()'s canon/strip round trip unchanged", r["quickBack"] == quick, r["quickBack"])
    check("no console errors (f)", not errs, errs)
    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
