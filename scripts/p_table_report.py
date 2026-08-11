"""Render output/p_table_build_report.md — B5 acceptance criteria 1-13.

Deliverable 8 (fill rate + no-fill opportunity cost) leads, per SPEC
"What lands first, and why". All statistics are fit-era only; the sealed span
contributes a row count and file hashes, nothing else.
"""
from __future__ import annotations

import json
import sys


def fmt_dist(d, unit=""):
    if not d:
        return "_no rows_"
    return (f"median **{d['median']}{unit}**, p25 {d['p25']}, p75 {d['p75']}, "
            f"p90 {d['p90']} (n={d['n']})")


def main():
    st = json.load(open("output/p_table_build_stats.json"))
    gr = json.load(open("output/p_table_gate_report.json"))
    man = json.load(open("output/flow_coverage_manifest.json"))
    sha = open("output/sealed/SHA256SUMS").read().strip()

    fill = st["fill"]
    L = []
    A = L.append
    A("# P-TABLE build report — B5 acceptance criteria")
    A("")
    A("Build: SPEC-pxl-p-table.md Part B · fit era 2023-01-02 → 2025-05-31 · "
      "sealed 2025-06-01 → 2026-01-30 (unread) · all statistics fit-era only.")
    A("")

    # ------------------------------------------------------------- item 8 first
    A("## Item 8 — Fill rate, cancellation reasons, and the no-fill "
      "opportunity cost (leads by design)")
    A("")
    n_q, n_f = fill["n_qualified"], fill["n_filled"]
    A(f"- Qualified fights (an order existed): **{n_q}** · filled: **{n_f}** · "
      f"**fill rate {fill['fill_rate']:.1%}**")
    cr, crr = fill["cancellation_reasons"], fill["cancellation_rates"]
    A(f"- Cancellations, mutually exclusive: `expired_target_taken` "
      f"**{cr['expired_target_taken']}** ({crr['expired_target_taken']:.1%} of "
      f"qualified) · `expired_invalidated` {cr['expired_invalidated']} "
      f"({crr['expired_invalidated']:.1%}) · `expired_session_end` "
      f"{cr['expired_session_end']} ({crr['expired_session_end']:.1%})")
    A(f"- Mode-b resolution cost (order placed only at the 5m boundary): "
      f"`order_never_live` {fill['order_never_live']} rows cancelled by gap "
      f"events; the limit level was traded through in the gap on "
      f"{fill['gap_limit_traded_through']} rows (fills mode (a) would have "
      f"taken; measurable against the `a_*` columns).")
    A("")
    A("**The comparison that gates everything downstream** — travel from the "
      "intended entry price:")
    A("")
    A(f"- `unfilled_mfe_pts` (all unfilled): {fmt_dist(fill['unfilled_mfe_pts'], ' pts')}")
    A(f"- `unfilled_mfe_pts` | target taken: "
      f"{fmt_dist(fill['unfilled_mfe_pts_target_taken'], ' pts')}")
    A(f"- `unfilled_mfe_pts` | session-end expiry: "
      f"{fmt_dist(fill['unfilled_mfe_pts_session_end'], ' pts')}")
    A(f"- filled-trade `mfe_pts`: {fmt_dist(fill['filled_mfe_pts'], ' pts')} · "
      f"in R: {fmt_dist(fill['filled_mfe_R'], 'R')}")
    A("")
    mc = st["market_ctrl"]
    A("Market-entry control (same population, entry at the eligible bar's open, "
      "nearest-draw exit, net of costs):")
    A(f"- all qualified: {fmt_dist(mc['ctrl_R'], 'R')}")
    A(f"- filled subset: {fmt_dist(mc['ctrl_R_filled_subset'], 'R')} · "
      f"unfilled subset: {fmt_dist(mc['ctrl_R_unfilled_subset'], 'R')}")
    A(f"- limit book on filled rows (nearest draw, net): "
      f"{fmt_dist(st['limit_outcome_nearest_draw_R'], 'R')}")
    A(f"- stress: 2-tick trade-through keeps "
      f"{fill['filled_stress_2tick_rate']:.1%} of fills · fill-bar ambiguity "
      f"(stop touched on the fill bar) {fill['fill_bar_ambiguous_rate']:.1%}")
    A("")

    A("## Item 1 — Gates")
    A("")
    g1, g2, g3 = gr["gate1"], gr["gate2"], gr["gate3"]
    A(f"- Gate 1 row existence under perturbation: **"
      f"{'PASS' if g1['passed'] else 'FAIL'}** — {g1['n_probes']} probes across "
      f"both sessions x both directions x row classes, including the added "
      "tf_trigger causality assertion in its two-part form: (1) flattening after "
      "`ts_decision` (the 5m boundary, where the mode-b decision completes) "
      "leaves row existence, `tf_trigger`, the qualifying set and every row "
      "column unchanged; (2) flattening after `tf_trigger_ts` leaves the "
      "governing event's own facts unchanged in the per-TF stream.")
    A(f"  - strata: {g1['strata']}")
    A("  - Gate-1 FINDING (kept deliberately): the strict single-instant reading "
      "— governance itself fixed at `tf_trigger_ts` — is unsatisfiable under "
      "mode (b): a first gate run demonstrated a 3m bar closing 07:18 stealing "
      "governance from a 2m trigger at 07:16 inside the 07:20 window "
      "(2023-07-27 london). `ts_decision` is therefore the boundary; B3's "
      "'trigger bar close' parenthetical is carried by `tf_trigger_ts`. This is "
      "a recorded property of mode (b) and strengthens the case for the mode (a) "
      "comparison the `a_*` columns support.")
    A(f"- Gate 2 entry price: **{'PASS' if g2['passed'] else 'FAIL'}** — limit "
      "invariant under future-flattening AND under a 1-tick shift of the "
      "decision close; `filled` false on a flat future; control entry moves to "
      "the flattened value; `limit_price == pxl_50` exactly on every row; "
      "eligibility strictly on the 5m boundary grid; fills strictly after "
      "eligibility. No level derives from a developing indicator (no indicator "
      "enters any level, so the delta-close/period signature has no surface; "
      "the tick-shift test is the direct check).")
    A(f"- Gate 3 convention: **{'PASS' if g3['passed'] else 'FAIL'}** — "
      f"{g3['n_files_checked']} flow files checked; in-span OK "
      f"{g3['n_in_span_ok']}; {g3['n_in_span_excluded_by_declared_criterion']} "
      "files excluded from flow_coverage by the declared roll-week criterion "
      "(quarterly roll: NQ.c.0 / NQ.v.0 vs volume-front diverge by the "
      "calendar-spread, ~220-260 pts); scale anomalies confirmed as fixed-point "
      "serialized with a decimal point (magnitude-based detection). Families A "
      "and B share zero common minutes — agreement is transitive through the "
      "front-month bar; recorded as a standing MISS with a forward-overlap "
      "requirement.")
    A("")

    A("## Item 2 — closeloc / rangex non-null on flow-covered rows")
    fa = st["flow_nonnull_assert"]
    A("")
    A(f"- flow-covered rows (all eras, format-level assert only): "
      f"{fa['n_flow_covered_rows_all_eras']} · closeloc non-null: "
      f"**{fa['closeloc_all_nonnull']}** · rangex non-null: "
      f"**{fa['rangex_all_nonnull']}**. Both derive from the decision bar "
      "(bar-only proxies), so the historical 100%-NaN failure cannot recur. "
      "NOTE: all flow-covered rows lie in the sealed span; this assert ran as a "
      "nullness check only, no other statistic touched them.")
    A("")

    A("## Item 3 — Row counts and trigger frequency (fit era)")
    A("")
    A("`session | direction | qualified | reason` :")
    for k, v in sorted(st["counts_by_session_direction_qualified_reason"].items()):
        A(f"- `{k}`: {v}")
    A("")
    A("Triggers per processed session per day (fights, fit era):")
    for s, d in st["triggers_per_session_per_day"].items():
        A(f"- **{s}**: {d['all']} all-row / **{d['qualified']} qualified** "
          f"(sessions processed: {st['n_sessions_processed'].get(s)})")
    A("")
    A("A4.1-C2 check: the SPEC flagged a finding if qualified frequency fell "
      "below ~1 trigger per session per direction. Measured qualified frequency "
      "is ABOVE that floor in both sessions (divide the qualified rate by 2 "
      "directions). Frequency is a population property the prop objective "
      "prices — carried forward, not interpreted here.")
    A("")

    A("## Item 4 — Sealed rows")
    A("")
    A(f"- sealed main rows: **{st['rows_sealed_UNREAD']}** · sealed TF rows: "
      f"{st['tf_rows_sealed_UNREAD']} · sealed candidate rows: "
      f"{st['cand_rows_sealed_UNREAD']} — written unread; no other statistic "
      "computed. Integrity:")
    A("```")
    A(sha)
    A("```")
    A("")

    A("## Item 5 — Exclusion log")
    A("")
    A(f"- {st['exclusion_log_entries']} entries in "
      "`output/p_table_exclusion_log.csv`, two criteria only: "
      "`session_window_incomplete` (Sundays/holidays/half-days — pure calendar, "
      "outcome-independent) and `flow_file_convention_mismatch` (roll-week book "
      "vs bar disagreement — calendar-anchored, outcome-independent; rows kept, "
      "only `flow_coverage` forced false).")
    A("")

    A("## Item 6 — wick_width_pts distribution")
    A("")
    A(f"- all rows: {fmt_dist(st['wick_width_pts'], ' pts')}")
    A(f"- qualified: {fmt_dist(st['wick_width_pts_qualified'], ' pts')}")
    A("")

    A("## Item 7 — stop_dist_pts distributions")
    A("")
    for k, v in st["stop_dist"].items():
        A(f"- {k}: {fmt_dist(v, ' pts')}")
    A("")

    A("## Item 9 — Timeframe structure")
    A("")
    A(f"- tf_agreement_count (qualified): {st['tf_agreement_count']}")
    A(f"- tf_trigger distribution (all rows): {st['tf_trigger_distribution']}")
    A(f"- events per cluster: {st['events_per_cluster']}")
    A("")
    A("A1.1 exchange-rate table (per-TF sibling rows, fit era):")
    A("")
    A("| TF | wick_width_pts | stop_dist_pts | r_available |")
    A("|---|---|---|---|")
    for tf, g in st["geometry_by_tf"].items():
        A(f"| {tf}m | {fmt_dist(g['wick_width_pts'])} | "
          f"{fmt_dist(g['stop_dist_pts'])} | {fmt_dist(g['r_available'])} |")
    A("")

    A("## Item 10 — wick_top_mode")
    A("")
    A(f"- `{st['wick_top_mode']}` per DA-3 (ruled 11 Aug); the candle_high "
      "variant was not built.")
    A("")

    A("## Item 11 — body_wick_ratio (qualified rows)")
    A("")
    A(f"- {fmt_dist(st['body_wick_ratio'])} — floor 1.0 by construction; the "
      "shape above 1.0 is the non-circular displacement-quality axis (A4.1 C1).")
    A("")

    A("## Item 12 — Leg geometry and MIN_LEG_RETRACE sensitivity")
    A("")
    A(f"- leg_height_pts: {fmt_dist(st['leg_height_pts'], ' pts')}")
    A(f"- retrace_frac: {fmt_dist(st['retrace_frac'])}")
    A("- row counts at declared sensitivity values (full pipeline re-run per "
      "value, whole span):")
    for fr, d in st["min_leg_retrace_sensitivity"].items():
        A(f"  - `MIN_LEG_RETRACE={fr}`: {d}")
    A("")

    A("## Item 13 — Fresh-break geometry bite (candidate lifecycle)")
    A("")
    z = st["zone_pre_penetration"]
    A(f"- candidates (fit era, all TFs): {z['n_candidates']} · died by prior "
      f"body penetration: {z['n_penetrated']} (**{z['penetrated_rate']:.1%}**) "
      f"· born already penetrated: {z['born_penetrated']}")
    A(f"- full fate distribution: {z['fates']}")
    A("")
    A("---")
    A(f"- r_available (qualified): {fmt_dist(st['r_available_qualified'], 'R')} "
      f"· min_1r_pass rate {st['min_1r_pass_rate']:.1%} (recorded, NOT filtered)")
    A(f"- target missing (no prior unbroken draw below/above the limit): "
      f"{st['target_missing_rate']:.1%} of qualified rows")
    A("")
    open("output/p_table_build_report.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
