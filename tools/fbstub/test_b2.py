#!/usr/bin/env python3
"""0.4.5_17 (B2) tests: "fantasmi sovrapposti" on L maps at girone start (house/wait phase only).
Root cause: resetActors() picked each ghost's house slot with MET.ghosts[i%MET.ghosts.length]; every
map's meta.ghosts list only had 4 slots, so on an L map (5 ghosts) the 5th ghost (i=4) wrapped back to
slot 0 and was drawn exactly on top of ghost 0 while both were still waiting in the house. Fix: gave
each of the 4 L-class maps (Palude, Vulcano, Fabbrica, Gran Labirinto) a 5th house slot (bottom-center
of the house rectangle, at least one full tile from every other slot). Ghosts 1-4 and the wait-timer
formula are untouched. Reuses the harness of test_f2b.py, same pattern as test_m1a.py.
Run: python tools/fbstub/test_b2.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

CLASS_MAPS = {"S": [0, 1, 2, 3, 4], "M": [5, 6, 7, 10, 12, 13], "L": [8, 9, 11, 14]}
CLASS_N = {"S": 3, "M": 4, "L": 5}


def ghost_snapshot(p):
    return p.evaluate("G.en.map(e=>({tx:e.tx,ty:e.ty,inHouse:inHouse(e.tx,e.ty)}))")


def check_distinct_and_housed(label, snap, want_n):
    tiles = [(g["tx"], g["ty"]) for g in snap]
    check(f"{label}: ghost count = {want_n}", len(snap) == want_n, snap)
    check(f"{label}: no two ghosts share a tile/pixel position", len(set(tiles)) == len(tiles), tiles)
    check(f"{label}: every ghost is inside the house", all(g["inHouse"] for g in snap), snap)


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
    settle(p, 600)

    # ---------------- every map of every class: at girone start (t=0) and right after a death respawn,
    # every ghost has a distinct house slot, all inside the house, count unchanged (B2)
    for cls, maps in CLASS_MAPS.items():
        for mi in maps:
            p.evaluate("cancelAnimationFrame(raf);devJump(1,%d)" % mi)
            snap0 = ghost_snapshot(p)
            check_distinct_and_housed(f"mi={mi} ({cls}) at girone start", snap0, CLASS_N[cls])

            # force one death (real state machine: dying -> lives-- -> resetActors(true))
            p.evaluate("G.state='dying';G.t=0.001;update(0.02)")
            snap1 = ghost_snapshot(p)
            check_distinct_and_housed(f"mi={mi} ({cls}) right after a death respawn", snap1, CLASS_N[cls])
    check("no console errors (B2 per-map house slots)", not errs, errs)

    # ---------------- ghosts 1-4 keep their pre-existing slots on the 4 L maps (only a 5th slot was added)
    OLD_SLOTS = {
        8: [[13, 9], [12, 9], [14, 9], [13, 8]],
        9: [[13, 9], [12, 9], [14, 9], [13, 8]],
        11: [[13, 12], [12, 12], [14, 12], [13, 11]],
        14: [[13, 12], [12, 12], [14, 12], [13, 11]],
    }
    for mi, want in OLD_SLOTS.items():
        p.evaluate("cancelAnimationFrame(raf);devJump(1,%d)" % mi)
        got = p.evaluate("G.en.slice(0,4).map(e=>[e.tx,e.ty])")
        check(f"mi={mi} (L): ghosts 1-4 keep their original house slots", got == want, got)

    # ---------------- 5th ghost's wait rule unchanged: 4th's wait + 2.5s flat, regardless of difficulty
    for diff in ("easy", "medium", "hard"):
        p.evaluate("cancelAnimationFrame(raf);S.opts.diff='%s';devJump(1,8)" % diff)
        w = p.evaluate("({w4:G.en[3].wait,w5:G.en[4].wait})")
        check(f"mi=8 (L), diff={diff}: 5th ghost's wait = 4th's wait + 2.5s (unchanged rule)",
              abs(w["w5"] - w["w4"] - 2.5) < 1e-9, w)
    p.evaluate("S.opts.diff='medium'")
    check("no console errors (5th-ghost wait rule)", not errs, errs)

    ctx.close(); b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
