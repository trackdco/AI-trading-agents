# Champion v1.1 — FROZEN as the replay baseline (pass 30, Angus go-ahead)

Blend v1 + the three journal cuts. This exact spec is baseline A in the three-way replay
(static champion vs agent-no-news vs agent-with-news). Changes = new version, new doc.

## Spec
- Window 08:00–10:15 ET · max 2 trades/day · per-session budgets when other sessions open
- Regime switch (pre-open): trailing-20-day imbalanced-day share ≥ 0.5 → WAR day, else BALANCE
  (day types per `output/amt_daytypes.csv` method; vector in `output/regime_vector.csv`)
- BALANCE book: E3 reclaim limits + V8 management (50% at first structure, 5m-swing trail,
  premarket BE 09:29), champion config otherwise (B3 filter, min-stop 6, walkout, named list)
- WAR book: E4 market-on-confirmation, tight-stop only (|close − stop_ref| ≤ 15 pts), V0
- CUT 1: skip if effective fill-to-stop risk < 5.0 pts (both books)
- CUT 2: skip B-pattern triggers whose fill lands in the 09:00–09:59 hour
- CUT 3: BALANCE book skips htf_flag == with_trend triggers (the fade book only fades)

## Reference results (Feb 2 – Jul 15 2026, 1 NQ, commissions in — in-sample; forward pending)
100 trades · 45.0% win · +915.7 pts · +$17,814 · months: +6,599 / +4,250 / +3,705 / +10 /
+3,765 / −515 (Jul = half month) · journal: `output/journal_champion.csv` (pre-cut superset)

## Status
- In-sample champion; the three cuts are journal-mined (see loser-journal artifact) —
  forward validation = July back half + live paper-fills.
- Oracle ceiling for daily routing between the two books: $37,014/6mo (L2 benchmark) —
  the regime-resolution prize the agents are chasing.
