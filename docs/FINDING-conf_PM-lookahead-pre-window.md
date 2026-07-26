# FINDING — `conf_PM` is a LOOKAHEAD in the pre-window `C` score check (P2 stop)

**STATUS: OPEN — a redesign + re-validation call for Pat/Angus, not an engineering fix.**
Surfaced by the P2 no-lookahead audit (the feasibility gate before building the live
feature-matrix assembly). One scored column reads information unavailable at decision time.
Per the standing rule ("any scored column needing decision-time-unavailable info → stop and
report, that's a redesign, not a build"), **P2 build is halted on the pre-window path** until
this is ruled.

## The leak, precisely

`scripts/canon_mechanical.py` scores the pre-market window with 5 binary checks (W, F, Tp, G,
**C**) → score → size ladder. The **C** check is:

```python
# canon_mechanical.py:76
T["C"] = np.where(T.win_ == "pre", (T.conf_PM == 1), (T.conf_LON == 1)).astype(float)
```

`conf_PM = sgn_conf(cvd_PM, direction)` (`scripts/trade_angles.py:69`), and `cvd_PM` is the
**cumulative CVD over the ENTIRE PM window 08:00→09:30 ET**, computed per day and joined on
`day`:

```
# dayflow_features.py:10-11, 57-61, 120 — PM window = hm in [08:00, 09:30)
Windows (NY): ... PM = 08:00->09:30 ...
```

A **pre-window trade is one that fills before 09:30** (`win_ = "pre" if fillhm < 570`,
`trade_matrix.py:43`). So for a pre trade, `cvd_PM` covers the whole 08:00–09:30 window **while
the trade fills inside that window** — `conf_PM` "knows" how the PM session's net CVD resolves
**after** entry. That is a lookahead: at fill time you cannot know the sign of a cumulative
delta that keeps accruing for up to another 90 minutes.

Note gold-window trades use `conf_LON` (London 02:00→08:00, complete before any gold fill —
clean). The leak is **pre-window only**, but the pre window is the bulk of the NY book.

## How load-bearing it is (measured on the signed-off `canon_book.parquet`)

| | value |
|---|---|
| NY taken trades | 264 |
| **pre-window** (uses `conf_PM`) | **214 (81%)** |
| gold-window (uses `conf_LON`, clean) | 50 |
| pre trades with `C == 1` (conf_PM confirmed) | **145 / 214 (68%)** |
| median pre fill time (ET) | **08:01** |
| minutes of `cvd_PM` window AFTER the fill (the lookahead span) | **median 72, mean 64, max 89** |
| pre trades with ≥15 min of post-fill lookahead | **202 / 214** |
| pre score distribution (ladder: 3→0.5, 4→1.0, 5→1.5) | {3: 78, 4: 111, 5: 25} |

At a median fill of 08:01, `cvd_PM` (08:00–09:30) is **~72 of its 90 minutes in the future**.
`conf_PM` is effectively "will the premarket session close net-up or net-down?" — evaluated at
08:01. It gates 81% of the NY book and, being 1 of 5 checks, moves trades across the 3/4/5
score→size boundaries directly.

## Why this is a redesign + re-validation, not a code fix

- A **leakage-clean variant already exists** in the matrix — `trade_matrix` carries
  `pm_sofar_cvd` / `pm_sofar_conf` (PM CVD **truncated at fill**). The canon `C` check simply
  does not use it; it uses the whole-window `conf_PM`.
- But swapping `conf_PM → pm_sofar_conf` **changes the C values → changes the pre score →
  changes which pre trades are taken and at what size → changes the book.** The pre-window edge
  in the signed-off `baseline_book.parquet` (+$56,065.18) was measured **with this lookahead**.
  So the fix is not a silent substitution — it requires **re-deriving the pre-window canon
  under the clean C and re-validating** (a new backtest, a new signed-off number, and a check
  of whether the pre edge survives at all once C can no longer peek ~72 min ahead).
- That touches the frozen canon and the signed-off anchor — a Pat/Angus rulebook call, not an
  engineering change I make unilaterally. I have not changed any scoring code.

## What IS clean (the rest of the scored path — audited)

Every other column the scoring path reads is decision-time-computable with no lookahead:

- **Depth** (W, D, WALLSZ): `dep_wall_*` / `dep_thick` — the book snapshot at fill.
- **Fill-bar** (F, BIGFD, T2): `fill_delta` / `fill_delta_conf` — the fill minute; `bp5opp`
  from the 5 completed minutes **before** fill (`gold_quality.py`, documented "zero lookahead").
- **Tape** (Tp, Tc, VWAPD, G): `d15` / `d15_conf` / `ent_vs_vwap_sd_dir` — last-15-min /
  at-fill, truncated at `fillmi` (`trade_angles.py` `M.loc[:t.fillmi]`).
- **badpa families** (X, PAQ, TRIG, R1, R2): `bbw_state` / `netpath_30` / `trigdens_30` /
  `churn_flow_30` — all windows **30/60 min BEFORE the fill** (`badpa_matrix.py:5,70-88`).
- **Prior-session context** (AGE, and `conf_ON`/`conf_LON`): `on_extreme_age` = minutes since a
  past ON extreme; ON (18:00→08:00) and LON (02:00→08:00) both **end at 08:00, before every
  fill** — complete, not lookahead.
- **gold_quality** (LONSLOPE): `lon_slope_d` = London-session slope, "London ends hours before
  any gold fill → zero lookahead" (`gold_quality.py:7-8`).
- **Path-dependent sizing** (governor, cold/R1, 2b `nth`, 2c day-P&L escalation): reads PRIOR
  taken trades' realized `eff_dollars`/`pl` — past trades, not lookahead. (Caveat, separate
  from this finding: those realized outcomes require the managed exit to be known live, which
  couples live sizing to the exit-model ruling — see `FOR-ANGUS-managed-exit-question.md`.)
- **London book** (`london_canon.py`): scores on `cvd_ON_sofar` / `conf_ON_sofar` (truncated at
  fill) + `cvd_ASIA` (prior-complete session) — designed clean, same pattern.

## The decision this forces

1. Confirm the leak (independently re-derive `cvd_PM` vs `pm_sofar_cvd` at a few pre fills).
2. Rule whether the pre-window `C` check moves to a leakage-clean `pm_sofar_conf`.
3. If so, **re-run the canon and re-validate** the pre book — the +$56,065.18 anchor must be
   re-established (or revised) under the clean C before the live lane can be trusted to
   reproduce it. This is the reference the gate's A-section measures against.

Until this is ruled, I am not building the live pre-window feature assembly (P2) — a clean live
build against a leaky reference would either fail A-section fidelity (if I compute C cleanly) or
propagate the lookahead (if I reproduce `conf_PM` — impossible live, since the future isn't
knowable). Gold and London paths are unaffected and could proceed independently if desired.
