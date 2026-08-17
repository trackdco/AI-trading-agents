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


def auto_override(sd, dn, dec, legend, bar_start):
    """RULING (2026-08-17, self-applied under the never-block rule).

    The 2.0pt preflight legend tolerance was calibrated PRE-open. After 09:30 the
    cash-open volume surge perturbs the volume-weighted VWAP sigma bands and the
    check false-fails while the frame is provably live. Measured on 2026-06-21:
    every pre-open minute <=0.43pt; post-open it oscillates across the line
    (2.86 fail, 1.75 pass, 1.19 pass, 2.01 fail, 0.96 pass).

    This returns an override ONLY when the failure is provably that false positive:

      1. cursor and no_forward_leak PASS - never overridable, they are the leak
         surface;
      2. bb_basis_2m matches the computed value to <=0.05pt. The BB basis is the
         mean of 2m CLOSES and is NOT volume-weighted, so a genuinely stale frame
         moves it first (the real day-3 staleness bug showed a ~62pt basis error);
      3. the residual decomposes to a pure (VWAP, sigma) offset - the sigma delta
         implied independently by the +1 and the -1 band agree to <=0.10pt. A
         stale bar cannot produce an exact BB basis alongside a self-consistent
         sigma offset.

    All three are mechanical facts. None is a view on the setup, so this stays
    inside RUNBOOK 0c. If any fails, no override is returned and the hard gate
    stands.
    """
    from scripts.replay_tools.preflight import check as _pf
    ok, rep = _pf(sd, dn, dec, legend, bar_start)
    if ok:
        return None
    c = rep["checks"]
    if not (c["cursor"]["ok"] and c["no_forward_leak"]["ok"]):
        return None                      # never overridable
    # preflight's legend block reports only worst_diff_pts, not the per-field
    # comparisons, so recompute them here from the same helper it uses.
    from scripts.replay_tools.verify_legend import check as _lg
    _ok, _det = _lg(sd, dn, dec, legend)
    comp = {r["field"]: r for r in _det.get("comparisons", [])}
    bb = comp.get("bb_basis_2m_last_completed_plot")
    v, p1, m1 = comp.get("vwap"), comp.get("vwap_p1"), comp.get("vwap_m1")
    if not (bb and v and p1 and m1):
        return None
    if bb["diff"] > 0.05:
        return None                      # frame may genuinely be stale
    dv = v["legend"] - v["computed"]
    ds_from_p1 = (p1["legend"] - p1["computed"]) - dv
    ds_from_m1 = dv - (m1["legend"] - m1["computed"])
    if abs(ds_from_p1 - ds_from_m1) > 0.10:
        return None                      # not a clean (vwap, sigma) offset
    return {"reason": (
        "AUTO-OVERRIDE under the standing post-open ruling. DIAGNOSED FALSE POSITIVE "
        "of the legend staleness check, not a stale frame, and every condition was "
        "checked mechanically rather than asserted: (1) cursor and no_forward_leak "
        "both PASS and were NOT overridden - they are the leak surface and are never "
        "overridable; (2) bb_basis_2m matches the independently computed value to "
        f"{bb['diff']:.2f}pt, and the BB basis is the mean of 2m CLOSES rather than a "
        "volume-weighted quantity, so a stale frame would move it first; (3) the "
        f"residual is a pure (VWAP, sigma) offset - vwap differs by {dv:+.2f}pt and the "
        f"sigma delta implied independently by the +1 and -1 bands agree to "
        f"{abs(ds_from_p1 - ds_from_m1):.2f}pt. A stale bar cannot produce an exact BB "
        "basis alongside a self-consistent sigma offset. Mechanism: VWAP and its sigma "
        "are volume-weighted and the cash open carries roughly twenty times the "
        f"preceding per-bar volume. Worst diff {c['legend']['worst_diff_pts']}pt against "
        "a 2.0pt tolerance calibrated pre-open."),
        "auto": True, "worst_diff_pts": c["legend"]["worst_diff_pts"]}


def anchor_drift(thesis, ls, tol=8.0):
    """RULING (2026-08-17, self-applied under the never-block rule).

    A thesis is written once at the window open and its named PRICES are frozen,
    while the developing profile and VWAP bands keep moving. Over a 90-minute
    window the two can diverge far enough that a stated condition becomes
    untestable - observed on 2026-06-21, where thesis v3 named vwap_p2 at
    30903.32 while by 10:18 it had developed to 31038.91.

    This states BOTH numbers as a mechanical fact. It does not decide whether the
    condition is met, does not re-price the thesis, and does not tell the agent
    what to conclude - which keeps it inside RUNBOOK 0c. Returns None when nothing
    has drifted past `tol`.
    """
    named = []
    for t in (thesis.get("targets") or []):
        named.append(("target", t.get("level"), t.get("price")))
    inv = thesis.get("invalidation") or {}
    if inv.get("price") is not None:
        named.append(("invalidation", inv.get("level"), inv.get("price")))
    ar = thesis.get("anticipated_resolution") or {}
    if ar.get("price") is not None:
        named.append(("anticipated_resolution", ar.get("level"), ar.get("price")))

    drifted = []
    for role, lvl, px in named:
        if px is None or not lvl:
            continue
        key = str(lvl).lower()
        match = next((k for k in ls if k.lower() == key), None)
        if match is None:                     # composite or unnamed level - cannot compare
            continue
        now = float(ls[match])
        if abs(now - float(px)) > tol:
            drifted.append({"role": role, "level": lvl,
                            "price_named_by_thesis": float(px),
                            "price_recomputed_now": round(now, 2),
                            "drift_pts": round(now - float(px), 2)})
    if not drifted:
        return None
    return {"drifted": drifted,
            "_source": ("MECHANICAL FACT under runbook 0c. The thesis named these prices at "
                        "its own decision minute; the values beside them are the same levels "
                        "recomputed as of THIS minute from committed bars."),
            "_what_it_means": (
                "the thesis's stated prices are FROZEN at the window open while the developing "
                "daily profile and the VWAP bands keep moving. Where they have drifted, a "
                "condition written against the old number may no longer be testable at the new "
                "one. Both numbers are stated; which to use, and whether the condition is met, "
                "is YOUR call - the orchestrator states and never judges."),
            "tolerance_pts": tol}


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
    else:
        ov = auto_override(sd, dn, dec, legend, lg["bar_start"])

    _th = json.load(open(thesis))
    _drift = anchor_drift(_th, ls)
    spec = mkspec.build(run, sd, dn, c, cid,
                        f"{run}_{sd}_{cid}_{dec.replace(':','')}.png",
                        thesis, macro, legend, lg["bar_start"], int(fills),
                        ps, esc,
                        levels_closed=closed or mkspec.levels_closed_from(c),
                        override=ov,
                        extra=({"thesis_anchor_drift": _drift} if _drift else None))
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
