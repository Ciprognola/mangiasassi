#!/usr/bin/env python3
"""0.4.5_9 (U3) tests: «Batti il professore» achievement only on a real win, tile 3 unlock + migration of old saves, golden border + link on the
locked tiles 3/5/10, «sblocca regalo!» tag only on gift achievements. Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_u3.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

STUB = """(()=>{const nop=async()=>{};for(const f of ['pbSay','prMusicStop','prMusic','prBlack','pbTeardown','prReleaseMusic','prSleep','prSay','prThrowOut','prExit'])window[f]=nop;
 window.pbAsk=async()=>1;window.go=function(s){window.__go=s};window.startGame=function(){window.__sg=1};0})()"""


def fresh_page(b, sv=None):
    ctx, p, errs = page(b, site="stable", local=norm(b, sv or save()), toggle=False, dev=False)
    settle(p, 600)
    return ctx, p, errs


def win_case(p, label, setup, res, won):
    p.evaluate("S.p.pr.won=false;delete S.ach.done.m5;delete S.ach.prog.m5;S.sim=false;PR={test:false};window.__go=null;0")
    p.evaluate(setup + ";0")
    p.evaluate("pbEnding(%s,{reward:10})" % res); p.wait_for_timeout(400)
    s = p.evaluate("({won:S.p.pr.won,ach:!!S.ach.done.m5})")
    check(label, s == {"won": won, "ach": won}, s)


def old(pr, claimed=None):
    sv = save(); sv["p"]["pr"] = pr
    if claimed:
        sv["p"]["road"] = {"claimed": claimed}
    return sv


with sync_playwright() as pw:
    srv = serve(); b = launch_browser(pw)
    # ---- achievement list
    ctx, p, errs = fresh_page(b)
    r = p.evaluate("({n:ACH.length,min:ACH.filter(a=>a.c==='min').map(a=>a.id),cat:ACH_CATS.find(c=>c[0]==='min')[2],m5:ACH.find(a=>a.id==='m5')})")
    check("«Batti il professore» is in Minigiochi; lists and counts consistent (35 total, Minigiochi 5 places = 5 entries)", r["n"] == 35 and len(r["min"]) == 5 and r["cat"] == 5 and r["m5"]["n"] == "Batti il professore" and r["m5"]["ev"] == "prwin", r)
    check("reward in line with the other Minigiochi (between «Fuori da Coccia!» 150/90 and «Algidone è a terra» 600/360)", r["m5"]["r"] == [300, 180], r["m5"]["r"])
    p.evaluate("achTab='min';go('ach')"); p.wait_for_timeout(400)
    t = p.evaluate("({rows:document.querySelectorAll('.scroll .ach:not(.ph)').length,ph:document.querySelectorAll('.scroll .ach.ph').length})")
    check("Obiettivi › Minigiochi shows 5 entries and no placeholder", t == {"rows": 5, "ph": 0}, t)
    # ---- real win only
    p.evaluate(STUB)
    win_case(p, "real win -> achievement + won flag", "", "{winner:'own'}", True)
    win_case(p, "dev/test battle win (PR.test) -> nothing", "PR={test:true}", "{winner:'own'}", False)
    win_case(p, "SIM («Sblocca tutto») win -> nothing", "S.sim=true", "{winner:'own'}", False)
    win_case(p, "lost battle -> nothing", "", "{winner:'foe'}", False)
    win_case(p, "running away (Fuga) -> nothing", "", "{run:true}", False)
    check("no console errors (achievement)", not errs, errs); ctx.close()

    # ---- migration of old saves (no `won` field)
    ctx, p, errs = fresh_page(b, old({"visits": 2, "seen": True}))
    s = p.evaluate("({st:roadState(3),keep:!!S.p.road.keep3,won:S.p.pr.won,ach:!!S.ach.done.m5})")
    check("old save that had seen a real battle: tile 3 stays unlocked (claimable), no retroactive achievement (a win can't be proven)", s["st"] in ("claimable", "unlocked") and s["keep"] and s["won"] is False and not s["ach"], s)
    p.evaluate("persist()"); p.reload(); p.wait_for_selector("#rsi"); p.click("#rsi"); p.wait_for_timeout(500)
    check("...and after a reload (migration persisted)", p.evaluate("roadState(3)") in ("claimable", "unlocked"))
    ctx.close()
    ctx, p, errs = fresh_page(b, old({"visits": 1, "seen": True}, {"3": True}))
    check("old save with tile 3 claimed keeps it claimed", p.evaluate("roadState(3)") == "claimed")
    ctx.close()
    ctx, p, errs = fresh_page(b, old({"visits": 0, "seen": False}))
    check("old save that never saw a battle: tile 3 locked", p.evaluate("roadState(3)") == "locked" and not p.evaluate("!!S.p.road.keep3"))
    p.evaluate("S.p.pr.seen=true;persist()")
    check("a NEW battle start (seen) does not unlock tile 3 any more", p.evaluate("roadState(3)") == "locked")
    p.evaluate("S.p.pr.won=true;persist()")
    check("after the win tile 3 unlocks", p.evaluate("roadState(3)") in ("claimable", "unlocked"))
    ctx.close()

    # ---- border + link on 3/5/10 (fresh save: all locked)
    ctx, p, errs = fresh_page(b)
    p.evaluate("go('road')"); p.wait_for_timeout(500)
    gold = p.evaluate("[...document.querySelectorAll('.rtile.locked.gold')].map(e=>+e.dataset.road)")
    check("locked tiles 3, 5 and 10 (only) have the golden border", sorted(gold) == [3, 5, 10], gold)
    for tile, name in ((3, "Batti il professore"), (5, "Il banco trema"), (10, "Fuori da Coccia!")):
        p.evaluate("go('road')"); p.wait_for_timeout(300)
        p.evaluate("document.querySelector('[data-road=\"%d\"]').scrollIntoView({block:'center'})" % tile); p.wait_for_timeout(150)
        p.click('[data-road="%d"]' % tile); p.wait_for_selector("#rhg", timeout=3000)
        txt = p.evaluate("document.querySelector('#modal').innerText")
        check(f"tile {tile}: tapping shows what unlocks it («{name}»)", name in txt and "Tessera bloccata" in txt, txt[:120])
        p.click("#rhg"); p.wait_for_timeout(500)
        s = p.evaluate("({screen,tab:achTab,name:(document.querySelector('.ach.hl b')||{}).textContent||'',vis:(()=>{const e=document.querySelector('.ach.hl');if(!e)return false;const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight})()})")
        check(f"tile {tile}: the link opens Obiettivi on that entry, highlighted and in view", s["screen"] == "ach" and s["tab"] == "min" and name in s["name"] and s["vis"], s)
    p.evaluate("go('road')"); p.wait_for_timeout(300); p.click('[data-road="4"]'); p.wait_for_timeout(200)
    check("another locked tile keeps the old toast (no modal)", not p.evaluate("!!document.querySelector('#rhg')"))
    check("no console errors (roadmap)", not errs, errs); ctx.close()
    ctx, p, errs = fresh_page(b, old({"visits": 1, "seen": True}))
    p.evaluate("go('road')"); p.wait_for_timeout(400)
    gold = p.evaluate("[...document.querySelectorAll('.rtile.gold')].map(e=>+e.dataset.road)")
    check("once tile 3 is unlocked it loses the border (5 and 10 keep it)", sorted(gold) == [5, 10], gold)
    ctx.close()

    # ---- «sblocca regalo!» tag only on gift achievements
    ctx, p, errs = fresh_page(b)
    tags = p.evaluate("""(()=>{const out=[];for(const c of ACH_CATS){achTab=c[0];go('ach');for(const e of document.querySelectorAll('.scroll .ach[data-ach]'))out.push([e.dataset.ach,!!e.querySelector('.gifttag'),(e.querySelector('.gifttag')||{}).textContent||''])}return out})()""")
    tagged = sorted(a for a, t, _ in tags if t)
    check("«sblocca regalo!» only on the achievements that lead to a ready roadmap gift (m5 → tile 3 GEKA, m1 → tile 5 BK); not on m2 (tile 10 has no gift yet) or any other", tagged == ["m1", "m5"] and all(x[2] == "sblocca regalo!" for x in tags if x[1]), tagged)
    check("no console errors (tags)", not errs, errs); ctx.close()
    b.close()
print("%d / %d passed" % (sum(RES), len(RES)))
sys.exit(0 if all(RES) else 1)
