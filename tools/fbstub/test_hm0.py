#!/usr/bin/env python3
"""0.5_1 (HM0) tests: the dev-only «Controller» accordion with «Prova controller» (Opzioni › Sviluppatore).
Read-only: it shows the gamepad buttons and axes and logs keys, it never acts on the game and saves nothing.
A) invisible with dev mode off, present with it on. B) a pressed button shows in the live view and in the log,
then its release. C) an axis above 0.5 is shown, a small one (0.1) is not. D) a key while open is logged.
E) closing the accordion stops the polling. F) «Copia risultati» copies the summary (and falls back to a
selected textarea when the clipboard fails). G) bite: HM0_MUTATE=nopoll serves a build with the polling
disabled, and B must fail. Reuses the harness of test_f2b.py. Run: python tools/fbstub/test_hm0.py"""
import functools, http.server, os, shutil, sys, tempfile, threading
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "test_f2b.py"), encoding="utf-8").read()
exec(compile(src[:src.index("def dev_click")], os.path.join(HERE, "test_f2b.py"), "exec"))  # harness only

MUT = os.environ.get("HM0_MUTATE", "")
# a fake standard pad: 17 buttons, 4 axes, always reported by navigator.getGamepads (slot 0)
PAD = """(()=>{
  window.__pad={id:'Test Pad',index:0,mapping:'standard',connected:true,
    buttons:Array.from({length:17},()=>({pressed:false,value:0})),axes:[0,0,0,0],timestamp:0};
  Object.defineProperty(navigator,'getGamepads',{configurable:true,value:()=>[window.__pad,null,null,null]});
})()"""


def mutant_base():
    """a copy of the build with the polling switched off (ctrlStart returns at once), served on its own port"""
    d = tempfile.mkdtemp(prefix="hm0_mut_")
    body = open(os.path.join(ROOT, "index.html"), encoding="utf-8", newline="").read()
    assert body.count("function ctrlStart(){") == 1
    body = body.replace("function ctrlStart(){", "function ctrlStart(){return;", 1)
    for rel in ("index.html", os.path.join("dev", "index.html")):
        os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
        open(os.path.join(d, rel), "w", encoding="utf-8", newline="").write(body)

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    port = 8795
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=d))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d/" % port, d


def open_ctrl(p):
    """Opzioni -> Sviluppatore -> «Controller» accordion (real clicks)"""
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    p.click("[data-otab=dev]"); p.wait_for_timeout(300)
    if not p.evaluate("document.querySelector('details[data-acc=ctrl]').open"):
        p.click("details[data-acc=ctrl] > summary"); p.wait_for_timeout(300)


def log_text(p):
    return p.evaluate("(document.querySelector('#ctrlLog')||{}).innerText||''")


def live_text(p):
    return p.evaluate("(document.querySelector('#ctrlLive')||{}).textContent||''")


if MUT == "nopoll":
    BASE, MUT_DIR = mutant_base()
    print("MUTANT build (polling disabled) at", BASE, flush=True)
elif MUT:
    raise SystemExit("unknown HM0_MUTATE=" + MUT)

srv = serve()
with sync_playwright() as pw:
    b = launch_browser(pw)

    # ============================================================ A) dev mode off / on
    ctx, p, errs = page(b, site="dev", dev=False, toggle=False)
    settle(p)
    p.click("[data-tile=opt]"); p.wait_for_timeout(300)
    check("A) dev mode off: no Sviluppatore tab and no Controller accordion",
          not p.evaluate("!!document.querySelector('[data-otab=dev]')") and not p.evaluate("!!document.querySelector('details[data-acc=ctrl]')"))
    check("A) no console errors (dev off)", not errs, errs)
    ctx.close()

    ctx, p, errs = page(b, site="dev", extra_init=PAD)
    settle(p)
    open_ctrl(p)
    check("A) dev mode on: the Controller accordion is present and carries «Prova controller»",
          p.evaluate("!!document.querySelector('details[data-acc=ctrl]')") and "Prova controller" in p.evaluate("document.querySelector('details[data-acc=ctrl]').innerText"))
    check("A) the pad is listed: 'Test Pad', standard, 17 tasti, 4 assi",
          "Test Pad" in live_text(p) and "standard" in live_text(p) and "17 tasti" in live_text(p) and "4 assi" in live_text(p), live_text(p))

    # ============================================================ B) button press and release
    p.evaluate("window.__pad.buttons[0]={pressed:true,value:1}"); p.wait_for_timeout(300)
    check("B) pressed button 0 is shown in the live view", "0 (1.00)" in live_text(p), live_text(p))
    check("B) log has «gamepad 0: tasto 0 premuto»", "gamepad 0: tasto 0 premuto" in log_text(p), log_text(p))
    p.evaluate("window.__pad.buttons[0]={pressed:false,value:0}"); p.wait_for_timeout(300)
    check("B) log has «gamepad 0: tasto 0 rilasciato»", "gamepad 0: tasto 0 rilasciato" in log_text(p), log_text(p))
    check("B) no console errors (press)", not errs, errs)

    # ============================================================ C) axes above 0.5 shown, small ones hidden
    p.evaluate("window.__pad.axes[0]=0.8;window.__pad.axes[1]=0.1"); p.wait_for_timeout(300)
    lv = live_text(p)
    check("C) axis 0 = 0.8 shown in the live view", "asse 0 = 0.80" in lv, lv)
    check("C) axis 1 = 0.1 not shown", "asse 1" not in lv, lv)
    check("C) crossing 0.5 is logged", "gamepad 0: asse 0 = 0.80" in log_text(p), log_text(p))
    p.evaluate("window.__pad.axes[0]=0;window.__pad.axes[1]=0"); p.wait_for_timeout(200)

    # ============================================================ D) keyboard logged while open
    check("D) accordion still open here", p.evaluate("document.querySelector('details[data-acc=ctrl]').open"))
    p.keyboard.press("ArrowUp"); p.wait_for_timeout(200)
    check("D) «tastiera: ArrowUp / ArrowUp» in the log", "tastiera: ArrowUp / ArrowUp" in log_text(p), log_text(p))

    # ============================================================ E) closing stops the polling
    p.click("details[data-acc=ctrl] > summary"); p.wait_for_timeout(300)
    t1 = p.evaluate("CTRL.ticks"); p.wait_for_timeout(600); t2 = p.evaluate("CTRL.ticks")
    check("E) closed accordion: no more polling ticks, loop handle cleared", t1 == t2 and p.evaluate("CTRL.raf") == 0, (t1, t2, p.evaluate("CTRL.raf")))

    # ============================================================ F) «Copia risultati»
    p.click("details[data-acc=ctrl] > summary"); p.wait_for_timeout(300)
    p.evaluate("(()=>{navigator.clipboard.writeText=t=>{window.__clip=t;return Promise.resolve()};return 0})()")
    p.click("#ctrlCopy"); p.wait_for_timeout(300)
    clip = p.evaluate("window.__clip||''")
    check("F) copied text has the pad id and the log", "Test Pad" in clip and "gamepad 0: tasto 0 premuto" in clip, clip[:200])
    p.evaluate("(()=>{navigator.clipboard.writeText=()=>Promise.reject(new Error(\"denied\"));return 0})()")
    p.click("#ctrlCopy"); p.wait_for_timeout(300)
    check("F) clipboard failure: a selected textarea shows the text",
          p.evaluate("(()=>{const t=document.getElementById('ctrlTa');return !!t&&!t.hidden&&t.value.indexOf('Test Pad')>=0})()"))
    check("F) no console errors (copy)", not errs, errs)
    ctx.close()

    if MUT:
        print("MUTANT run done: B is expected to fail", flush=True)
    shutil.rmtree(MUT_DIR, ignore_errors=True) if MUT else None
srv.shutdown()
print("%d/%d checks passed" % (sum(RES), len(RES)), flush=True)
sys.exit(0 if all(RES) else 1)
