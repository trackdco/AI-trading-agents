# P-TABLE build report — B5 acceptance criteria

Build: SPEC-pxl-p-table.md Part B · fit era 2023-01-02 → 2025-05-31 · sealed 2025-06-01 → 2026-01-30 (unread) · all statistics fit-era only.

## Item 8 — Fill rate, cancellation reasons, and the no-fill opportunity cost (leads by design)

- Qualified fights (an order existed): **4815** · filled: **2927** · **fill rate 60.8%**
- Cancellations, mutually exclusive: `expired_target_taken` **1412** (29.3% of qualified) · `expired_invalidated` 114 (2.4%) · `expired_session_end` 362 (7.5%)
- Mode-b resolution cost (order placed only at the 5m boundary): `order_never_live` 966 rows cancelled by gap events; the limit level was traded through in the gap on 1773 rows (fills mode (a) would have taken; measurable against the `a_*` columns).

**The comparison that gates everything downstream** — travel from the intended entry price:

- `unfilled_mfe_pts` (all unfilled): median **31.5 pts**, p25 15.25, p75 60.875, p90 107.85 (n=1787)
- `unfilled_mfe_pts` | target taken: median **28.375 pts**, p25 14.5, p75 54.5, p90 90.7 (n=1412)
- `unfilled_mfe_pts` | session-end expiry: median **61.0 pts**, p25 39.5, p75 114.5, p90 202.75 (n=261)
- filled-trade `mfe_pts`: median **20.5 pts**, p25 8.5, p75 46.625, p90 87.1 (n=2927) · in R: median **5.889R**, p25 2.467, p75 12.444, p90 21.111 (n=2927)

Market-entry control (same population, entry at the eligible bar's open, nearest-draw exit, net of costs):
- all qualified: median **-1.009R**, p25 -1.071, p75 0.5, p90 1.125 (n=4661)
- filled subset: median **-1.047R**, p25 -1.105, p75 -1.007, p90 0.931 (n=2906) · unfilled subset: median **0.211R**, p25 -0.251, p75 0.864, p90 1.785 (n=1755)
- limit book on filled rows (nearest draw, net): median **-1.143R**, p25 -1.182, p75 -1.083, p90 1.241 (n=2927)
- stress: 2-tick trade-through keeps 94.2% of fills · fill-bar ambiguity (stop touched on the fill bar) 43.8%

## Item 1 — Gates

- Gate 1 row existence under perturbation: **PASS** — 24 probes across both sessions x both directions x row classes, including the added tf_trigger causality assertion in its two-part form: (1) flattening after `ts_decision` (the 5m boundary, where the mode-b decision completes) leaves row existence, `tf_trigger`, the qualifying set and every row column unchanged; (2) flattening after `tf_trigger_ts` leaves the governing event's own facts unchanged in the per-TF stream.
  - strata: {'london|-1|multi_bar_break': 2, 'london|-1|qualified': 2, 'london|-1|structure_unaligned': 2, 'london|1|multi_bar_break': 2, 'london|1|qualified': 2, 'london|1|structure_unaligned': 2, 'ny_am|-1|multi_bar_break': 2, 'ny_am|-1|qualified': 2, 'ny_am|-1|structure_unaligned': 2, 'ny_am|1|multi_bar_break': 2, 'ny_am|1|qualified': 2, 'ny_am|1|structure_unaligned': 2}
  - Gate-1 FINDING (kept deliberately): the strict single-instant reading — governance itself fixed at `tf_trigger_ts` — is unsatisfiable under mode (b): a first gate run demonstrated a 3m bar closing 07:18 stealing governance from a 2m trigger at 07:16 inside the 07:20 window (2023-07-27 london). `ts_decision` is therefore the boundary; B3's 'trigger bar close' parenthetical is carried by `tf_trigger_ts`. This is a recorded property of mode (b) and strengthens the case for the mode (a) comparison the `a_*` columns support.
- Gate 2 entry price: **PASS** — limit invariant under future-flattening AND under a 1-tick shift of the decision close; `filled` false on a flat future; control entry moves to the flattened value; `limit_price == pxl_50` exactly on every row; eligibility strictly on the 5m boundary grid; fills strictly after eligibility. No level derives from a developing indicator (no indicator enters any level, so the delta-close/period signature has no surface; the tick-shift test is the direct check).
- Gate 3 convention: **PASS** — 510 flow files checked; in-span OK 270; 17 files excluded from flow_coverage by the declared roll-week criterion (quarterly roll: NQ.c.0 / NQ.v.0 vs volume-front diverge by the calendar-spread, ~220-260 pts); scale anomalies confirmed as fixed-point serialized with a decimal point (magnitude-based detection). Families A and B share zero common minutes — agreement is transitive through the front-month bar; recorded as a standing MISS with a forward-overlap requirement.

## Item 2 — closeloc / rangex non-null on flow-covered rows

- flow-covered rows (all eras, format-level assert only): 1592 · closeloc non-null: **True** · rangex non-null: **True**. Both derive from the decision bar (bar-only proxies), so the historical 100%-NaN failure cannot recur. NOTE: all flow-covered rows lie in the sealed span; this assert ran as a nullness check only, no other statistic touched them.

## Item 3 — Row counts and trigger frequency (fit era)

`session | direction | qualified | reason` :
- `london|long|False|multi_bar_break`: 696
- `london|long|False|structure_unaligned`: 2356
- `london|long|True|-`: 1600
- `london|short|False|multi_bar_break`: 634
- `london|short|False|structure_unaligned`: 2320
- `london|short|True|-`: 1537
- `ny_am|long|False|multi_bar_break`: 136
- `ny_am|long|False|structure_unaligned`: 1107
- `ny_am|long|True|-`: 845
- `ny_am|short|False|multi_bar_break`: 142
- `ny_am|short|False|structure_unaligned`: 1047
- `ny_am|short|True|-`: 833

Triggers per processed session per day (fights, fit era):
- **ny_am**: 5.183 all-row / **2.116 qualified** (sessions processed: 793)
- **london**: 11.501 all-row / **3.946 qualified** (sessions processed: 795)

A4.1-C2 check: the SPEC flagged a finding if qualified frequency fell below ~1 trigger per session per direction. Measured qualified frequency is ABOVE that floor in both sessions (divide the qualified rate by 2 directions). Frequency is a population property the prop objective prices — carried forward, not interpreted here.

## Item 4 — Sealed rows

- sealed main rows: **3589** · sealed TF rows: 5224 · sealed candidate rows: 59006 — written unread; no other statistic computed. Integrity:
```
ac371339038ba212cf6362af9a075002c54129213b4693d180c6cf7706ddc43b  p_table_sealed.parquet
77ec9067e6c69cfa3a37d23c23992646b78155bac94533780b715c1e47a242e1  p_table_tf_sealed.parquet
c6d17bc5c98ce84bfd7023a66f9c58945fa7d84601a665dcb98b92e6e9f1628a  p_table_candidates_sealed.parquet
```

## Item 5 — Exclusion log

- 351 entries in `output/p_table_exclusion_log.csv`, two criteria only: `session_window_incomplete` (Sundays/holidays/half-days — pure calendar, outcome-independent) and `flow_file_convention_mismatch` (roll-week book vs bar disagreement — calendar-anchored, outcome-independent; rows kept, only `flow_coverage` forced false).

## Item 6 — wick_width_pts distribution

- all rows: median **2.0 pts**, p25 1.0, p75 4.25, p90 8.0 (n=13253)
- qualified: median **2.5 pts**, p25 1.0, p75 5.0, p90 9.5 (n=4815)

## Item 7 — stop_dist_pts distributions

- base: median **3.0 pts**, p25 2.5, p75 4.0, p90 6.0 (n=13253)
- atr015: median **2.25 pts**, p25 1.5, p75 4.25, p90 7.25 (n=13199)
- atr025: median **3.0 pts**, p25 1.75, p75 5.5, p90 9.75 (n=13199)
- atr033: median **3.75 pts**, p25 2.25, p75 6.75, p90 11.5 (n=13199)

## Item 9 — Timeframe structure

- tf_agreement_count (qualified): {'1': 3994, '2': 665, '3': 138, '4': 18}
- tf_trigger distribution (all rows): {'3': 2068, '1': 6586, '2': 2984, '5': 1615}
- events per cluster: {'1': 10325, '2': 2274, '4': 109, '3': 545}

A1.1 exchange-rate table (per-TF sibling rows, fit era):

| TF | wick_width_pts | stop_dist_pts | r_available |
|---|---|---|---|
| 1m | median **1.5**, p25 0.75, p75 3.0, p90 5.75 (n=8376) | median **2.75**, p25 2.25, p75 3.5, p90 4.75 (n=8376) | median **2.786**, p25 1.667, p75 4.778, p90 7.769 (n=7044) |
| 2m | median **2.25**, p25 1.25, p75 4.5, p90 8.475 (n=4132) | median **3.25**, p25 2.5, p75 4.25, p90 6.25 (n=4132) | median **3.333**, p25 2.091, p75 5.5, p90 8.75 (n=3133) |
| 3m | median **2.75**, p25 1.5, p75 5.75, p90 10.25 (n=2646) | median **3.5**, p25 2.75, p75 5.0, p90 7.25 (n=2646) | median **3.737**, p25 2.385, p75 6.222, p90 9.398 (n=1853) |
| 5m | median **3.75**, p25 2.0, p75 7.25, p90 13.25 (n=1790) | median **3.75**, p25 3.0, p75 5.5, p90 8.75 (n=1790) | median **4.185**, p25 2.818, p75 6.768, p90 10.387 (n=1016) |

## Item 10 — wick_top_mode

- `body` per DA-3 (ruled 11 Aug); the candle_high variant was not built.

## Item 11 — body_wick_ratio (qualified rows)

- median **3.333**, p25 2.214, p75 5.5, p90 10.0 (n=4593) — floor 1.0 by construction; the shape above 1.0 is the non-circular displacement-quality axis (A4.1 C1).

## Item 12 — Leg geometry and MIN_LEG_RETRACE sensitivity

- leg_height_pts: median **13.75 pts**, p25 7.5, p75 26.5, p90 48.45 (n=13253)
- retrace_frac: median **0.659**, p25 0.519, p75 0.818, p90 0.929 (n=13253)
- row counts at declared sensitivity values (full pipeline re-run per value, whole span):
  - `MIN_LEG_RETRACE=0.236`: {'ny_am|qualified': 5447, 'ny_am|not_qualified': 7819, 'london|not_qualified': 17951, 'london|qualified': 9676}
  - `MIN_LEG_RETRACE=0.382`: {'ny_am|qualified': 2146, 'ny_am|not_qualified': 3016, 'london|not_qualified': 7661, 'london|qualified': 4019}
  - `MIN_LEG_RETRACE=0.5`: {'london|not_qualified': 2412, 'ny_am|not_qualified': 1133, 'ny_am|qualified': 742, 'london|qualified': 1129}

## Item 13 — Fresh-break geometry bite (candidate lifecycle)

- candidates (fit era, all TFs): 215746 · died by prior body penetration: 78185 (**36.2%**) · born already penetrated: 42775
- full fate distribution: {'invalidated': 106356, 'triggered_unaligned_warmup': 4085, 'penetrated': 78185, 'triggered_qualified_warmup': 2116, 'broken_not_active': 2391, 'broken_multibar': 2132, 'triggered_unaligned': 9351, 'triggered_qualified': 5980, 'broken_multibar_warmup': 1107, 'session_end': 4043}

---
- r_available (qualified): median **3.077R**, p25 1.778, p75 5.098, p90 8.2 (n=3182) · min_1r_pass rate 61.8% (recorded, NOT filtered)
- target missing (no prior unbroken draw below/above the limit): 33.9% of qualified rows

