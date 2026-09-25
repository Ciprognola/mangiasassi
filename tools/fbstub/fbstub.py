"""Playwright helper: serves the stub modules for https://www.gstatic.com/firebasejs/** and seeds window.__fbs.
    install(ctx, users={...}, offline=False, mode="stub"|"block"|"hang")"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
USERS = {"master": {"pw": "pw-master", "role": "master"}, "dev3": {"pw": "pw-dev3", "role": "dev3"},
         "norole": {"pw": "pw-norole", "role": None}}  # fake passwords, test only


def install(ctx, users=None, offline=False, mode="stub", session=None, app="mgs", **flags):
    cfg = {"users": users or USERS, "offline": offline}
    cfg.update(flags)  # e.g. denyBugs=True, hangBugs=True (F6a)
    init = "window.__fbs=%s;" % json.dumps(cfg)
    if session:  # an already signed-in user for the given Firebase app name
        init += "localStorage.setItem('__fbstub_user_%s',%s);" % (app, json.dumps(session))
    ctx.add_init_script(init)

    def handle(route):
        name = route.request.url.split("/")[-1]
        if mode == "block":
            return route.abort()
        if mode == "hang":
            return  # never answered: the SDK load times out
        path = os.path.join(HERE, name)
        if os.path.exists(path):
            return route.fulfill(status=200, content_type="application/javascript", headers={"access-control-allow-origin": "*"}, body=open(path, encoding="utf-8").read())
        route.abort()

    ctx.route("https://www.gstatic.com/firebasejs/**", handle)
