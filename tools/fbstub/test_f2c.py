#!/usr/bin/env python3
"""0.4.5_2 regression tests: cloud apply / «Ripristina backup» must return to Opzioni (never the splash question),
the bug icon must work on the splash, and a full browser storage must never overwrite a save without a backup.
Reuses the harness of test_f2b.py (Firebase stub, never real credentials).
Run: python tools/fbstub/test_f2c.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only: check/page/save/cdoc/norm/...

FRESH = save(r=1, a=1, sordi=0)
for k in ("roccia", "algidone"):
    FRESH["p"]["ch"][k].update(exp=0, gir=0, ownP=[0], ownR=[0])
NOW = """({screen, splash:!!document.querySelector('#rsi'), bug:!!document.querySelector('#bugb'), lvl:S.p.ch.roccia.lvl,
 accOpen:!!document.querySelector('details.acc[data-acc=account][open]'), toast:(document.querySelector('.toast')||{}).textContent||'', tab:optTab})"""


def opt_account(p, touch=False):
    tap_or_click(p, "[data-tile=opt]", touch); p.wait_for_timeout(300)
    tap_or_click(p, "details.acc[data-acc=account] > summary", touch); p.wait_for_timeout(250)


def run_dev_player(b, player):
    tag = "player" if player else "dev"
    uid = "uid_norole" if player else "uid_master"
    fresh, cld = norm(b, FRESH), norm(b, save(r=22, a=3, sordi=90))
    ctx, p, errs = page(b, site="dev", local=fresh, cloud={uid + "_dev": cdoc(cld, rev=2, ver="0.4.5")}, toggle=False, dev=not player, player=player, has_touch=True)
    settle(p, 800)
    opt_account(p, True)
    s0 = p.evaluate(NOW)
    p.tap("[data-clt='1']"); p.wait_for_selector('.toast', timeout=8000); p.wait_for_timeout(200)
    s = p.evaluate(NOW)
    check(f"A ({tag}): enabling cloud save keeps me in Opzioni › Account (no splash question)", s["screen"] == "opt" and not s["splash"] and s["accOpen"], s)
    check(f"A ({tag}): the cloud copy was loaded and a toast says so", s["lvl"] == 22 and "Salvataggio del cloud caricato" in s["toast"], s)
    check(f"A ({tag}): bug icon visibility unchanged by the reload ({'shown' if not player else 'hidden'})", s["bug"] == (not player) and s["bug"] == s0["bug"], (s0, s))
    check(f"A ({tag}): no console errors", not errs, errs)
    # restore
    check(f"C ({tag}): «Ripristina backup» is offered", p.evaluate("!!document.querySelector('#clrb')"))
    p.tap("#clrb"); p.wait_for_timeout(200); p.tap("#cy"); p.wait_for_selector(".toast", timeout=8000); p.wait_for_timeout(200)
    s = p.evaluate(NOW)
    check(f"C/D ({tag}): restore returns to Opzioni (not the splash), toast, save swapped back", s["screen"] == "opt" and not s["splash"] and s["lvl"] == 1 and "Backup ripristinato" in s["toast"], s)
    check(f"C ({tag}): bug icon still {'shown' if not player else 'hidden'} after restore", s["bug"] == (not player), s)
    p.tap("#clrb"); p.wait_for_timeout(200); p.tap("#cy"); p.wait_for_selector(".toast", timeout=8000); p.wait_for_timeout(200)
    s = p.evaluate(NOW)
    check(f"D ({tag}): second restore (swap back) also works and stays in Opzioni", s["screen"] == "opt" and s["lvl"] == 22, s)
    check(f"D ({tag}): no console errors", not errs, errs)
    ctx.close()


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    run_dev_player(b, False)
    run_dev_player(b, True)

    # B: bug icon on the splash reacts to a tap; «Indietro» brings the splash question back
    ctx, p, errs = page(b, site="dev", local=norm(b, save()), toggle=False, has_touch=True)
    p.wait_for_selector("#rsi"); p.wait_for_timeout(600)
    check("B: bug icon present on the splash", p.evaluate("!!document.querySelector('#bugb')"))
    p.tap("#bugb"); p.wait_for_timeout(400)
    check("B: tapping it on the splash opens «Hai un insetto?»", p.evaluate("!!document.querySelector('#bgt')"))
    p.tap("#bgx"); p.wait_for_timeout(300)
    check("B: after «Indietro» the splash question is back and the icon still works", p.evaluate("!!document.querySelector('#rsi')&&!!document.querySelector('#bugb')"))
    ctx.close()

    # D: browser storage full -> nothing is overwritten, no reload, a toast explains
    fresh, cld = norm(b, FRESH), norm(b, save(r=22, a=3, sordi=90))
    bak = {"data": json.dumps(cld), "from": "device", "ts": 1790000000000, "summary": {}}
    ctx, p, errs = page(b, site="dev", local=norm(b, save(r=5, a=2, sordi=10)), cloud={"uid_master_dev": cdoc(cld, rev=2, ver="0.4.5")}, M={"uid": "uid_master", "rev": 2, "sum": "x", "dirty": False, "ts": 1790000000000}, bak=bak, toggle=True)
    settle(p, 1200)
    opt_account(p)
    before = p.evaluate("localStorage.getItem('mgs_v1_dev')")
    p.evaluate("(()=>{const o=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='mgs_v1_cloudbak_dev')throw new DOMException('full','QuotaExceededError');return o.call(this,k,v)};window.__marker=1})()")
    p.click("#clrb"); p.wait_for_timeout(200); p.click("#cy"); p.wait_for_timeout(1500)
    s = p.evaluate(NOW + " && Object.assign(" + NOW + ",{marker:window.__marker,same:localStorage.getItem('mgs_v1_dev')})")
    check("D: storage full -> no reload, save untouched, «Spazio insufficiente» toast", s["marker"] == 1 and s["same"] == before and "Spazio insufficiente" in s["toast"], s)
    ctx.close()
    b.close()

print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
