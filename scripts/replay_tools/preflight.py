"""Hard gate on every chart capture before it can reach an agent.

Three capture defects were found on day 3, all invisible to the briefing's own
chart_freshness_self_check. This module makes each one impossible to repeat
silently: a briefing builder calls check() and REFUSES to emit if it fails.

  1. cursor one minute short  - the replay cursor must sit at dec-1:59, so the
     last COMPLETE 2m bar must be the one closing at grid_2m(dec). Verified against
     the bar timestamp the chart actually returned.
  2. legend hover             - the indicator legend can show a hovered bar. Verified
     against values computed independently from committed bars.
  3. forward leak             - no bar may exist at or beyond the decision minute.

Usage:
    from scripts.replay_tools.preflight import check
    ok, report = check(sd, dn, dec, legend, last_bar_epoch)
    if not ok: raise SystemExit(report)
"""
import sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
import pandas as pd

NY = "America/New_York"
TOL = 2.0


def expected_last_bar_start(day_next, dec):
    """The 2m bar visible last at cursor dec-1:59 STARTS here."""
    from scripts.replay_tools.brief04 import grid_2m
    g = grid_2m(dec)                     # minute the last complete 2m bar closes at
    t = pd.Timestamp(f"{day_next} {g}", tz=NY) - pd.Timedelta(minutes=2)
    return t


def check(sess_day, day_next, dec, legend, last_bar_epoch=None, tol=TOL):
    from scripts.replay_tools.verify_legend import check as legend_check
    rep = {"decision_minute": dec, "checks": {}}
    ok = True

    # 1 + 3 - cursor position and forward leak, from the bar the chart returned
    if last_bar_epoch is not None:
        got = pd.Timestamp(int(last_bar_epoch), unit="s", tz="UTC").tz_convert(NY)
        want = expected_last_bar_start(day_next, dec)
        cursor_ok = (got == want)
        dm = pd.Timestamp(f"{day_next} {dec}", tz=NY)
        leak_ok = (got + pd.Timedelta(minutes=2)) <= dm
        rep["checks"]["cursor"] = {
            "ok": bool(cursor_ok), "last_bar_starts": got.strftime("%H:%M"),
            "expected_starts": want.strftime("%H:%M"),
            "why": "at cursor dec-1:59 the last COMPLETE 2m bar starts at grid_2m(dec)-2min"}
        rep["checks"]["no_forward_leak"] = {
            "ok": bool(leak_ok),
            "last_bar_closes": (got + pd.Timedelta(minutes=2)).strftime("%H:%M"),
            "decision_minute": dec,
            "why": "the last bar must close at or before the decision minute"}
        ok = ok and cursor_ok and leak_ok
    else:
        rep["checks"]["cursor"] = {"ok": False, "why": "last_bar_epoch not supplied - cannot verify"}
        ok = False

    # 2 - legend not hovered
    lok, ldet = legend_check(sess_day, day_next, dec, legend, tol)
    rep["checks"]["legend"] = {"ok": bool(lok), "worst_diff_pts": ldet["worst_diff_pts"],
                               "compared_as_of": ldet.get("compared_as_of"),
                               "tolerance_pts": tol}
    ok = ok and lok

    rep["PASS"] = bool(ok)
    return ok, rep


if __name__ == "__main__":
    import json
    sd, dn, dec, legend = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])
    lbe = int(sys.argv[5]) if len(sys.argv) > 5 else None
    ok, rep = check(sd, dn, dec, legend, lbe)
    print(json.dumps(rep, indent=1))
    sys.exit(0 if ok else 1)
