"""Build one trigger briefing: scanner candidate + saved legend -> mkspec -> mk49.

Usage: runcand.py <run> <sd> <dn> <dec> <cid> <thesis> <macro_out> <fills> \
                  <position_state.json|-> <escalation.json> <levels_closed.json> \
                  [prior_take ...]
Everything carrying judgement is passed in; this file only wires the pieces.
"""
import json, sys, os
T = "/Users/barbelldaddy/.claude/jobs/2411401a/tmp"
sys.path.insert(0, T)
import mkspec, mk49


def main():
    run, sd, dn, dec, cid, thesis, macro, fills = sys.argv[1:9]
    ps = json.load(open(sys.argv[9])) if sys.argv[9] != "-" else {"state": "FLAT"}
    esc = json.loads(sys.argv[10])
    closed = None if sys.argv[11] == "-" else json.loads(sys.argv[11])
    prior = sys.argv[12:]

    cands = json.load(open(f"{T}/cands/{sd}.json"))
    c = next(x for x in cands if x["dec"] == dec)
    legends = json.load(open(f"{T}/{run}_{sd}_legends.json"))
    lg = legends[dec]
    legend = {k: v for k, v in lg.items() if k not in ("cid", "cursor", "bar_start")}

    ov = None
    if os.path.exists(f"{T}/override_{run}_{sd}_{dec.replace(':','')}.json"):
        ov = json.load(open(f"{T}/override_{run}_{sd}_{dec.replace(':','')}.json"))

    spec = mkspec.build(run, sd, dn, c, cid,
                        f"{run}_{sd}_{cid}_{dec.replace(':','')}.png",
                        thesis, macro, legend, lg["bar_start"], int(fills),
                        ps, esc,
                        levels_closed=closed or mkspec.levels_closed_from(c),
                        override=ov)
    json.dump(spec, open(f"{T}/{run}_{sd}_{cid}.json", "w"), indent=1)

    lsets = json.load(open(f"{T}/lsets/{sd}.json"))
    ls = lsets[dec]

    # GUARD. The level-set is PRECOMPUTED, so preflight cannot vouch for it -
    # preflight compares the chart legend against a live recompute and never looks
    # at this file. A corrupt level-set would therefore reach the agent unchallenged
    # inside level_visits_this_session. It happened once (2026-06-21 03:42 came back
    # with session-open values and NaN profiles after a parallel run raced two writers
    # onto one file), so the two are now tied together: bb_ma_2m is computed from bar
    # closes and must equal the chart's BB basis, which the legend already carries.
    import math
    nan = [k for k, v in ls.items()
           if v is None or (isinstance(v, float) and math.isnan(v))]
    if nan:
        raise SystemExit(f"LEVEL-SET CORRUPT at {sd} {dec}: NaN levels {nan}. "
                         "Recompute serially before adjudicating.")
    # Tolerance is deliberately LOOSE (25pt). This is a CORRUPTION detector, not a
    # parity check - parity is preflight's job, against a live recompute. At an ODD
    # decision minute the chart legend describes the bar closing at dec-1 while the
    # level-set computes as-of dec, so the two sit one bar apart and legitimately
    # differ by a few points (measured 2.12pt at 09:03, 2.57pt at 09:45). A 2pt
    # tolerance would halt every odd minute. The failure this exists to catch was
    # 660pt wide.
    legend_bb = legend.get("bb_basis_2m_last_completed_plot")
    if legend_bb is not None and abs(float(ls["bb_ma_2m"]) - float(legend_bb)) > 25.0:
        raise SystemExit(
            f"LEVEL-SET DISAGREES WITH THE CHART at {sd} {dec}: level-set bb_ma_2m "
            f"{ls['bb_ma_2m']} vs chart BB basis {legend_bb}. Both are the 20-period "
            "mean of 2m closes and cannot be this far apart. Recompute serially.")

    out, fires, lv, cs = mk49.build(spec, ls, prior)
    print(out)
    print("  outer_band_gate_fires", fires)
    print("  chop_state", cs["state"], "| zone", cs["zone_now"], "|", cs["reason"])
    stale = {n: d for n, d in lv.items() if not d["fresh"]}
    print("  STALE levels:", {n: (d["level"], d["level_visits_this_session"], d["tests_15m_60min"])
                              for n, d in stale.items()} or "none")


if __name__ == "__main__":
    main()
