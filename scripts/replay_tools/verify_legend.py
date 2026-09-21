"""Cross-check a chart legend read against orchestrator-computed values.

The TradingView legend can display a HOVERED bar's values rather than the last
bar's. That is invisible to the briefing's chart_freshness_self_check, because the
orchestrator reads the legend from the same frame the screenshot shows - both agree
with each other while both describe the wrong bar. Found on day 3 at A4 10:53, where
the legend reported BB basis 30760.53 against a true 30698.16 (a ~08:18 value).

Usage:
    from scripts.replay_tools.verify_legend import check
    ok, detail = check(sess_day, day_next, dec, legend_dict)

Returns (True, detail) when the legend agrees with computation inside tolerance, and
(False, detail) when it does not. The caller states the outcome in the briefing; it
never silently substitutes one for the other.
"""
import sys
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")

TOL = 2.0  # points


def check(sess_day, day_next, dec, legend, tol=TOL):
    from scripts.replay_tools.brief04 import levels_at, flat_levels, grid_2m
    # the legend describes the last COMPLETE 2m bar, which closes at grid_2m(dec) -
    # that is dec itself at an even minute and dec-1 at an odd one. Comparing against
    # levels computed as-of dec instead produced spurious 2-7pt failures at every odd
    # decision minute on day 3.
    ref = grid_2m(dec)
    lv = flat_levels(levels_at(sess_day, day_next, ref))
    pairs = [("bb_basis_2m_last_completed_plot", "bb_ma_2m"),
             ("vwap", "vwap"), ("vwap_p1", "vwap_p1"), ("vwap_m1", "vwap_m1")]
    rows, worst = [], 0.0
    for lk, ck in pairs:
        if lk not in legend or ck not in lv or lv[ck] is None:
            continue
        d = abs(float(legend[lk]) - float(lv[ck]))
        worst = max(worst, d)
        rows.append({"field": lk, "legend": float(legend[lk]),
                     "computed": round(float(lv[ck]), 2), "diff": round(d, 2)})
    ok = worst <= tol
    return ok, {"verified": ok, "compared_as_of": ref, "tolerance_pts": tol, "worst_diff_pts": round(worst, 2),
                "comparisons": rows,
                "why": ("the legend can display a HOVERED bar rather than the last bar. The "
                        "briefing's own freshness self-check cannot catch that, because the "
                        "orchestrator reads the legend from the same frame the screenshot shows. "
                        "This compares it against values computed independently from committed bars.")}


if __name__ == "__main__":
    import json
    sd, dn, dec, legend = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])
    ok, detail = check(sd, dn, dec, legend)
    print(json.dumps(detail, indent=1))
    sys.exit(0 if ok else 1)
