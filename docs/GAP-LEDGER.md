# THE GAP LEDGER — what reduces to rules, what stays judgement

Requested by the v2 framework (Pat's point 6): *"whatever doesn't reduce to
a rule stays out of the tested strategy, explicitly — documented as an
untestable gap, not quietly assumed."* This repo's stance is the mirror
image — the gap is the product, carried by judgement agents and validated
by out-of-fit weeks and his trade-by-trade acceptance — but the LEDGER is
the same document either way: both projects need to know where the line
sits. Updated 2026-08-20.

## REDUCES TO RULES — mechanical today, exportable to v2 for hard grading

| item | where it lives | corpus-scale status |
|---|---|---|
| candidate detection (two-level break, close-through second leg, pending queues) | `scripts/offline_scan.py`, certified | the corpus IS this |
| chop state v2 (window-local trailing range vs frozen quartiles) | `scripts/chop_state.py` | CHOP 27.9% vs TRENDING 23.2% 2R-rate, n≈19k — real at scale |
| windows, caps, 09:10-era cutoffs, NY_PRE cut, FOMC closure (T39) | runbook + macro contract | policy, not hypothesis |
| stop floor (0.75× trailing 2m range), T55 clearance | trigger/manage contracts | mechanical definitions |
| freshness (zone touched before?) | enriched corpus (`zone_touches_session`) | corpus test in progress |
| ladders (TP1 band + TP2 ≥1R beyond) | T27/T78 | mechanical construction |
| level-truth, reach, re-read, vote, T82-check | runbook §2e duties | orchestrator arithmetic |

## DOES NOT (YET) REDUCE — the judgement residue the agents carry

| item | why it resists reduction | current mitigation |
|---|---|---|
| the DIRECTIONAL READ at a window open | two Mondays wrecked in opposite directions while the tape's mechanical trigger quality was normal (26.6% vs 25.2%) — the information is in the chart gestalt, not the features we compute | 2-of-3 vote (reproducibility, not correctness); HIS labels at volume are the only known upgrade path |
| what counts as a REJECTION worth taking | the j49 lesson: "a rejection at a band edge in a market that keeps going isn't a rejection" — behaviour, not geometry | T-doctrine prose + his sheet reads |
| conviction / trade quality beyond the grade rubric | his own words: "the difference is just because I've looked at the charts for so long. I don't know if I could communicate explicit indications" | grades retired from sizing; labeling drive may recover some of it |
| management judgement at a level (hold vs trail vs exit on the stall/break table) | the manager beat every fixed bracket policy tested (+25.91R vs mechanical variants); the edge is in the reading, not the schedule | schedule is default-not-cage; receipts on every proposed constraint (the dead-zone ban priced −4.2R and did not ship) |
| escalation judgement (when the thesis is wrong enough to challenge) | inherently a disagreement between two readings | escalation reform + mandatory re-read counter bound it |

## THE BRIDGE

His labels at volume (the labeling deck) move items DOWN this page: any
label-pattern that reduces to a feature rule is exported to v2 and graded
at p≤0.01/walk-forward/holdout; whatever pattern resists reduction stays
here, as sourced doctrine executed by agents — and this ledger says so out
loud instead of hand-waving past it.

Standing corrections this ledger already forced: the T80 "structural
second leg" receipt was a base-rate artifact (93% of sequential candidates
are structural; leg type sorts nothing at n=3,442) — T80 stands on his
leeway ruling, not on that receipt. The second-London-drag is not a tape
property (25.6% vs 25.4% at scale); the plausible mechanism is same-edge
re-attempts specifically, which is what T82 targets.
