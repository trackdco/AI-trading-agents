# FINDING — 10:15–10:30: same wall physics as golden, INVERTED flow physics

**2026-07-26, Angus's ask:** *"run the order flow variables that we did for the golden window
[on 10:15–10:30]. find that subset that produces the majority of the profit, cut the losers."*
Reproduce: `python -m scripts.late_a_orderflow` (matrix: `output/late_a_flow_matrix.parquet`,
292 trades, 2025-07→2026-07, canonical `src/canon/features.py` definitions, depth on 260/292).

## Survivors of the both-years rule (direction agrees 2025 AND 2026, ≥$60/t gap, n≥12/cell)

| check | on $/t | off $/t | gap | verdict |
|---|---|---|---|---|
| **W no-wall-behind** | +$155 (38% win) | −$132 (21%) | **+$288** | GOOD — same as golden |
| **D wall-ahead** | +$83 (34%) | −$167 (19%) | **+$249** | GOOD — same as golden |
| **WALLSZ ahead ≥7** | +$101 (37%) | −$114 (21%) | **+$214** | GOOD — same as golden |
| **d5_conf (flow-with, 5m)** | −$71 | +$47 | **−$118** | **BAD — INVERTED vs golden** |
| **C op_sofar_conf (open CVD with)** | −$98 | +$11 | **−$108** | **BAD — INVERTED** |
| **d30_conf (flow-with, 30m)** | −$74 | +$6 | **−$80** | **BAD — INVERTED** |

Non-survivors (fail both-years agreement): F fill_delta_conf, BIGFD, Tc d15, G vwapd, IMB,
pm_sofar_conf, PAQ, pathpos, kind. Baseline: 292t, −$11,748, 27% win, −51.8R.

**Reading:** the DEPTH checks transfer intact — walls are alpha at 10:15–10:30 exactly as in
golden. The CVD-confirmation family flips sign: by this hour the open drive is spent, so
entering WITH recent flow is chasing a move about to mean-revert. The paying trade is the
**flow-exhaustion fade into book structure** — golden's wall checks plus the OPPOSITE of
golden's flow checks. Extending the golden checklist verbatim would keep the chasers and cut
the fades: exactly wrong. (Angus's "setup types are inherently different," as an hour effect.)

## The subset (exploratory — NOT adopted)

`op_sofar_conf=OFF AND wall-ahead=ON AND d30_conf=OFF`:

| | kept 41t | cut 251t |
|---|---|---|
| P&L (1-mini) | **+$10,505** | −$22,252 |
| win | 41% | 25% |
| @ canon floor | +12.4R = +$2,487 | |
| months green | 8/11 | |
| by year | 2025 +$4,716 (45%) · 2026 +$5,789 (38%) | |

## Caveats — read before believing
1. Each component survives both years independently, but the 3-rule CONJUNCTION was chosen
   greedily in-sample on n=292. Needs the freeze-and-OOS treatment the golden checks got.
2. **2026-06 is +$6,622 of the +$10,505 (63%).** Ex that month: +$3,883 over 10 months.
3. +12.4R/13mo is ~1R/month at floor — real but modest; the 1-mini figure rides wide stops.
4. Not wired into anything. Canon windows unchanged. Adoption = new signed-off book + A1/A2.
