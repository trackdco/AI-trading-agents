# FINDING — the canon captures 11% of Angus's hand-logged trades (14% of his P&L)

**2026-07-26.** Ground-truth audit answering: *"I was smacking 3R+ trades 3-5 times a week —
it's clearly doing shit I was not."* Every hand-logged trade (28 Feb 2026 exact-time,
17 Mar 2026 ±25min; `data/reference/*hand_log*.csv`) matched by day + minute + direction
against all three system layers. Reproduce: `python scripts/capture_audit_handlog.py`
(full 45-row table in `output/capture_audit_handlog.csv`).

## The decomposition

| where the trade died | trades | Angus P&L | share |
|---|---|---|---|
| TAKEN by the canon | 5 | $6,026 | 14% |
| candidate, killed by canon checklist (score<3) | 9 | $6,931 | 16% |
| **raw detector fired; never reached the canon candidate set** | **30** | **$30,418** | **70%** |
| never detected | 1 | $0 | 0% |

The canon's candidate universe (`trade_matrix`, 970 rows) is the **champion engine's output
fills** (`universal_orderflow` → `trade_angles`), so every engine gate/window/cap filters
candidates BEFORE canon scoring ever sees them.

## Three layers

1. **The clock (~40% of his P&L).** 11 trades at 10:15+ worth $14,040 (his richest slice —
   Mar-9 10:45 +$4,640, Mar-10 10:20 +$3,460) cannot exist: the candidate set ends 10:13.
   Plus 5 trades in 09:30–09:40 worth $3,533 (4W/1L). **ANGUS RULING: the 09:30–09:40 cut is
   intentional and stays** ("i wait to see what the open gives me"); the 10:15–10:30
   extension is under active investigation (`scripts/late_a_orderflow.py`).
2. **Engine gates (~$18.6k in-window).** 20 in-window trades were in the trigger caches but
   died crossing the engine (bb_vwap cluster gate, confluence, 2/day cap, cancel-22,
   rr_floor, fills). Per-gate attribution: the golden-leak-hunt workflow.
3. **Checklist mis-scores his winners.** Of 9 candidates killed, 7 were profitable
   (avg +1.5R) scoring 0–2 (e.g. Feb-04 09:48 3.30R → score 2; Mar-11 10:05 +$2,260 →
   score 0). The 5 taken averaged 7.9R — the frozen pooled-2025 thresholds recognize his
   extreme setups and are blind to his ordinary 3R ones.

## Caveats
45 trades is a small ground truth; Mar times ±25min; "detector fired nearby" ≠ "engine could
have filled it" (the workflow quantifies that step); Feb $ at his sizing, Mar = points × $20.
