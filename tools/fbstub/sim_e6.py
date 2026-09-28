#!/usr/bin/env python3
"""E6a balance measurement (report only -- never touches index.html). Headless Chromium, dev mode,
freezes the rAF loop and drives update(1/60) directly (same pattern the other tools/fbstub tests use;
CLAUDE.md §6 mentions the equivalent faStep trick for Ferma Algidone!). A simple BFS bot plays both
characters through gironi 1-12 at Normale (medium) difficulty, once with the girone's own scheduled ghost
stages and once with the dev "Stadio" override forcing every ghost to stage 1 (the ablation baseline).
Math.random is replaced with a small seeded PRNG per run so every run is reproducible.

Run: python tools/fbstub/sim_e6.py [--seeds N] [--out PATH]
Writes a JSON array of per-run records to --out (default tools/fbstub/sim_e6_results.json, not committed
by default -- docs/releases/0.5-E6a-report.md is the actual deliverable, built from this data)."""
import argparse, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("srv = serve()")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

GIRONI = list(range(1, 13))
CHARACTERS = ["roccia", "algidone"]
TIMEOUT_S = 180

# The whole run (bot + instrumentation + tick loop) executes as ONE page.evaluate() call per (char,
# girone, seed, ablation) combination, to keep IPC overhead out of the measurement. Args are passed as a
# single object (Playwright serialises it), never string-substituted, to avoid any quoting issues.
RUN_JS = r"""
(({char, girone, seed, ablation, timeoutS}) => {
  // ---- seeded PRNG (xorshift-ish, deterministic per run) ----
  let __s = (seed >>> 0) || 1;
  Math.random = function () {
    __s ^= __s << 13; __s >>>= 0;
    __s ^= __s >>> 17;
    __s ^= __s << 5; __s >>>= 0;
    return (__s >>> 0) / 4294967296;
  };

  S.p.char = char;
  S.opts.diff = 'medium'; // Normale
  E1_STAGE_OV = ablation ? 1 : null;
  cancelAnimationFrame(raf);
  devJump(girone);
  G.lives = 999; // never let finishRun() end the run -- deaths are counted separately below
  G.invuln = 0;

  // ---- instrumentation: wrap a small set of already-existing functions, nothing in index.html changes ----
  const M = {
    sprintStarts: 0, shotsFired: 0, shotHits: 0, grease: 0, puddleTicks: 0, ticks: 0,
    paninoMerges: 0, paninoEat: 0, wallsBroken: 0,
    deaths: { ghost: 0, proj: 0, panino: 0, unknown: 0 }
  };
  const origSpawn = MPROJ.spawn.bind(MPROJ);
  MPROJ.spawn = function (...a) { M.shotsFired++; return origSpawn(...a) };
  const origGreaseAdd = GREASE.add.bind(GREASE);
  GREASE.add = function (...a) { M.grease++; return origGreaseAdd(...a) };
  const origStartIntro = PANINO.startIntro.bind(PANINO);
  PANINO.startIntro = function (...a) { M.paninoMerges++; return origStartIntro(...a) };
  const origEatSplit = PANINO.eatSplit.bind(PANINO);
  PANINO.eatSplit = function (...a) { M.paninoEat++; return origEatSplit(...a) };
  const origSmashFx = window.smashFx;
  window.smashFx = function (...a) { M.wallsBroken++; return origSmashFx(...a) };
  const origKill = window.killPlayer;
  window.killPlayer = function () {
    // cause classification: replay the same distance checks the two call sites already use, at the exact
    // moment killPlayer() actually fires -- approximate for a projectile hit blocked by invulnerability
    // (never reaches killPlayer at all, so never counted as a "shot hit" here; see report caveats)
    const [px, py] = pos(G.pl);
    let cause = null;
    for (const e of G.en) {
      if (e.merged || e.mode === 's' || e.mode === 'g') continue;
      const [ex, ey] = pos(e);
      if (Math.hypot(ex - px, ey - py) < .62 + (e.pan ? PANINO_CFG.hitExtra : 0)) { cause = e.pan ? 'panino' : 'ghost'; break }
    }
    if (!cause) for (const pr of MPROJ.list) {
      if (Math.hypot(pr.x - px, pr.y - py) < MPROJ_CFG.radius + MPROJ_CFG.playerR) { cause = 'proj'; break }
    }
    M.deaths[cause || 'unknown']++;
    if (cause === 'proj') M.shotHits++;
    return origKill.apply(this, arguments);
  };
  const prevSprintPhase = new Map();
  let currentTarget = null; // persisted across ticks -- see botDecide()'s own comment on why

  // ---- BFS bot: simple, identical shape for both characters, no secret abilities ----
  const W_ = W, H_ = H; // captured for closures below (globals, but read here for clarity)
  function bfs(startX, startY, blocked) {
    const dist = Array.from({ length: H_ }, () => new Array(W_).fill(Infinity));
    dist[startY][startX] = 0;
    const q = [[startX, startY]]; let qi = 0;
    while (qi < q.length) {
      const [x, y] = q[qi++], d = dist[y][x];
      for (let dir = 0; dir < 4; dir++) {
        let nx = x + DX[dir], ny = y + DY[dir];
        if (nx < 0 || nx >= W_) { if (!isTun(y)) continue; nx = (nx + W_) % W_ }
        if (ny < 0 || ny >= H_) continue;
        if (blocked(nx, ny)) continue;
        if (dist[ny][nx] > d + 1) { dist[ny][nx] = d + 1; q.push([nx, ny]) }
      }
    }
    return dist;
  }
  function dangerSet(r) {
    const danger = new Set();
    const mark = (cx, cy) => {
      for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
        const x = cx + dx, y = cy + dy;
        if (x < 0 || x >= W_ || y < 0 || y >= H_) continue;
        if (Math.hypot(dx, dy) <= r) danger.add(x + ',' + y);
      }
    };
    for (const e of G.en) {
      if (e.merged || e.mode === 's' || e.mode === 'g') continue;
      const [ex, ey] = pos(e);
      mark(Math.round(ex), Math.round(ey)); // same radius for a lone attrezzo/aereo and a merged Super Panino host, kept uniform for simplicity (report caveat)
    }
    for (const pr of MPROJ.list) {
      mark(Math.round(pr.x), Math.round(pr.y));
      mark(Math.round(pr.x + DX[pr.dir] * 2), Math.round(pr.y + DY[pr.dir] * 2)); // short lookahead along its path
    }
    return danger;
  }
  function botDecide() {
    if (G.state !== 'play') return;
    const P = G.pl;
    // Decide for whichever tile P.next will actually be consulted at. Recomputing every external tick
    // (rather than gating on P.prog) isn't enough on its own: when this tick's own movement crosses a
    // boundary with dt left over, step()'s while loop immediately re-calls chooseP() for the new tile
    // using the CURRENT P.next, before this outer loop gets another chance to update it -- so a decision
    // made for the tile the player is still standing on can already be one tile stale by the time it's
    // read. Anticipating the crossing (deciding for the tile about to be entered) fixes it, the same way a
    // human taps the next direction just before reaching a junction. A real bug caught by probing girone 1
    // with ghosts disabled entirely: the bot ping-ponged between two tiles forever, one tile short of a
    // pellet it could see and had even correctly targeted, purely from this one-tile decision lag.
    let px = P.tx, py = P.ty;
    if (P.dir != null && P.prog + P.speed * (1 / 60) >= 1 - 1e-6) {
      px = P.tx + DX[P.dir]; py = P.ty + DY[P.dir];
      if (px < 0) px = W_ - 1; else if (px >= W_) px = 0;
    }
    let target = null;
    if (G.power > 0) {
      // chasing a scared ghost: short-lived and the ghost itself moves, so just re-pick nearest each tick
      let bestD = Infinity;
      for (const e of G.en) {
        if (e.merged || e.mode !== 's') continue;
        const [ex, ey] = pos(e);
        const d = Math.hypot(ex - px, ey - py);
        if (d <= 4 && d < bestD) { bestD = d; target = [Math.round(ex), Math.round(ey)] }
      }
      currentTarget = null; // force a fresh pellet pick once power wears off, rather than resuming a stale one
    }
    if (!target) {
      // pellet-seeking: KEEP the same target across ticks until it's actually eaten. Re-picking "nearest"
      // fresh every single tick let two similarly-distant pellets flip which one looked nearer as the
      // player crossed between two adjacent tiles, so the bot walked back and forth between them forever
      // without making any further progress -- a real bug caught while probing girone 1 (girPts froze at
      // 40 for 150+ of the 180 simulated seconds; ghosts weren't even involved, confirmed by disabling them
      // entirely and reproducing the same freeze).
      if (currentTarget && G.grid[currentTarget[1]][currentTarget[0]] !== '.') currentTarget = null;
      if (!currentTarget) {
        const targets = [];
        for (let y = 0; y < H_; y++) for (let x = 0; x < W_; x++) if (G.grid[y][x] === '.') targets.push([x, y]);
        if (!targets.length) return; // no pellets left at all (about to clear) -- nothing to do
        const distFromPlayer = bfs(px, py, (x, y) => wall(x, y));
        let bestD = Infinity, best = null;
        for (const [tx, ty] of targets) { const d = distFromPlayer[ty] && distFromPlayer[ty][tx]; if (d != null && d < bestD) { bestD = d; best = [tx, ty] } }
        currentTarget = best;
      }
      target = currentTarget;
    }
    if (!target) return;
    // try the full "avoid within 2" radius first; if that leaves the target unreachable (a ghost is
    // squarely guarding the only way through), retreat to a smaller radius rather than dropping avoidance
    // outright -- keeps the bot from repeatedly suicide-rushing the same guarded pocket after each respawn
    let wallOrDanger = null, distFromTarget = null;
    for (const r of [2, 1, 0]) {
      const danger = r > 0 ? dangerSet(r) : null;
      wallOrDanger = danger ? ((x, y) => wall(x, y) || danger.has(x + ',' + y)) : ((x, y) => wall(x, y));
      distFromTarget = bfs(target[0], target[1], wallOrDanger);
      if (distFromTarget[py][px] < Infinity) break;
    }
    let bestDir = null, bestVal = Infinity;
    for (let dir = 0; dir < 4; dir++) {
      let nx = px + DX[dir], ny = py + DY[dir];
      if (nx < 0 || nx >= W_) { if (!isTun(py)) continue; nx = (nx + W_) % W_ }
      if (ny < 0 || ny >= H_) continue;
      if (wall(nx, ny)) continue;
      const v = distFromTarget[ny][nx];
      if (v < bestVal) { bestVal = v; bestDir = dir }
    }
    if (bestDir != null) setDir(bestDir);
  }

  // ---- drive the sim ----
  let cleared = false, timedOut = false, error = null;
  const maxTicks = Math.round(timeoutS * 60);
  try {
    for (let tick = 0; tick < maxTicks; tick++) {
      botDecide();
      update(1 / 60);
      M.ticks++;
      if (GREASE.at({ x: G.pl.tx, y: G.pl.ty })) M.puddleTicks++;
      for (const e of G.en) {
        if (!e.ab || !e.ab.sprint) continue;
        const key = G.en.indexOf(e), prev = prevSprintPhase.get(key);
        if (e.ab.sprint.phase === 'wind' && prev !== 'wind' && prev !== 'run') M.sprintStarts++;
        prevSprintPhase.set(key, e.ab.sprint.phase);
      }
      if (G.state === 'clear') { cleared = true; break }
    }
  } catch (e) {
    // a run-ending exception (seen once, rarely, from the pre-existing shoot/projectile path under some
    // seed -- not something E6a may touch or debug further in index.html) ends this run early rather than
    // the whole sweep; recorded as its own outcome so the report can say how often it happened.
    error = String(e && e.message || e);
  }
  if (!cleared && !error) timedOut = true;

  let bonusMult = null, bonusPts = 0;
  if (G.girBonusTxt) {
    const mm = /×([\d.]+) \+(\d+)/.exec(G.girBonusTxt);
    if (mm) { bonusMult = parseFloat(mm[1]); bonusPts = parseInt(mm[2], 10) }
  }
  const totalDeaths = M.deaths.ghost + M.deaths.proj + M.deaths.panino + M.deaths.unknown;
  return {
    cls: mapClassOf(G.mapi), nGhosts: G.en.length, stages: G.en.map(e => e.stage),
    cleared, timedOut, error, simSeconds: M.ticks / 60,
    deaths: M.deaths, totalDeaths,
    sprintStarts: M.sprintStarts, shotsFired: M.shotsFired, shotHits: M.shotHits,
    grease: M.grease, puddlePct: M.ticks ? 100 * M.puddleTicks / M.ticks : 0,
    paninoMerges: M.paninoMerges, paninoEat: M.paninoEat, wallsBroken: M.wallsBroken,
    girPts: G.girPts || 0, bonusMult, bonusPts
  };
})
"""


def run_one(p, char, girone, seed, ablation, timeout_s):
    return p.evaluate(RUN_JS, {"char": char, "girone": girone, "seed": seed, "ablation": ablation, "timeoutS": timeout_s})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--out", default=os.path.join(HERE, "sim_e6_results.json"))
    ap.add_argument("--probe", action="store_true", help="run a single (roccia, girone 1, seed 1, scheduled) run and print timing, then exit")
    args = ap.parse_args()

    with sync_playwright() as pw:
        srv = serve(); b = launch_browser(pw)
        ctx, p, errs = page(b, site="stable", local=norm(b, save()), toggle=False, dev=True)
        settle(p, 600)

        if args.probe:
            t0 = time.time()
            r = run_one(p, "roccia", 1, 1, False, TIMEOUT_S)
            print("probe result:", json.dumps(r))
            print("probe took %.2fs; console errors: %s" % (time.time() - t0, errs))
            ctx.close(); b.close()
            return

        seeds = list(range(1, args.seeds + 1))
        results = []
        t0 = time.time()
        total = len(CHARACTERS) * len(GIRONI) * 2 * len(seeds)
        done = 0
        for char in CHARACTERS:
            for girone in GIRONI:
                for ablation in (False, True):
                    for seed in seeds:
                        try:
                            r = run_one(p, char, girone, seed, ablation, TIMEOUT_S)
                        except Exception as ex:
                            # a page-level crash (rather than the in-page try/catch's own "error" field)
                            # would otherwise take the whole sweep down; log it, re-settle the page, move on
                            print("  RUN CRASHED %s girone=%s seed=%s ablation=%s: %s" % (char, girone, seed, ablation, ex), flush=True)
                            r = {"cls": None, "nGhosts": None, "stages": [], "cleared": False, "timedOut": False,
                                 "error": "page-crash: %s" % ex, "simSeconds": 0, "deaths": {"ghost": 0, "proj": 0, "panino": 0, "unknown": 0},
                                 "totalDeaths": 0, "sprintStarts": 0, "shotsFired": 0, "shotHits": 0, "grease": 0,
                                 "puddlePct": 0, "paninoMerges": 0, "paninoEat": 0, "wallsBroken": 0, "girPts": 0,
                                 "bonusMult": None, "bonusPts": 0}
                            settle(p, 600)
                        r.update(char=char, girone=girone, seed=seed, ablation=ablation)
                        results.append(r)
                        done += 1
                        if done % 20 == 0:
                            print("  %d/%d runs, %.1fs elapsed" % (done, total, time.time() - t0), flush=True)
        elapsed = time.time() - t0
        print("ALL RUNS DONE: %d runs in %.1fs (%.2fs/run avg)" % (len(results), elapsed, elapsed / max(1, len(results))))
        print("console errors seen: %s" % (errs[:5] if errs else "none"))
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=1)
        print("wrote", args.out)
        ctx.close(); b.close()


if __name__ == "__main__":
    main()
