# news_lab — red-folder event study for NQ

Built 12 Aug 2026 in-chat, for handoff to Claude Code on
`trackdco/AI-trading-agents`. Read SPEC.md first; PREREG-L3.md before any
sealed scoring. House rules apply: R first / points alongside, no revised
data, seal enforced in code, no invented dates.

## What is TESTED vs NOT (be honest with yourselves)

TESTED HERE (this sandbox, real repo data):
- `census.load_bars` on the repo's actual
  `glbx-mdp3-20251002-20260131.ohlcv-1m.csv.zst` (115,596 bars, NQZ5/NQH6
  dominant-contract selection working)
- `census.measure_event` + `run_census` end-to-end on the three real FOMC
  decisions in that window (2025-10-29, 2025-12-10, 2026-01-28) — sane
  output; Dec-10 SEP meeting shows a 122.5pt release bar and a 20pt short
  stop filling 108pts into the hole (−5.4R on a −1R design). The gap tables
  are not theoretical.
- Unit tests: census math exact on synthetic bars; causal_z lookahead gate;
  Wilson sanity (43 events cannot separate 60% from 50% — pooling can).

NOT TESTED HERE (sandbox network is locked to GitHub/PyPI — first runs on
the box, in this order):
- `vintage.py` ALFRED fetcher (needs FRED_API_KEY; free)
- `events.scrape_bls_year` / `scrape_bea_schedule` (page-layout dependent;
  they RAISE on parse failure rather than guessing)
- `consensus.fetch_week` FF scraper (bot protection varies; manual CSV
  fallback is first-class: `data/consensus_manual.csv`)
- `predictors.fetch_cleveland` (set CLEV_NOWCAST_URL from the live page)
- `predictors.kalshi_discover` (run once, record tickers by hand)

## Run order (box)
```
export FRED_API_KEY=...            # free key
python -m pytest tests/ -q         # must pass before anything else
# L0
python -c "from newslab.events import *; ..."        # seeds+rules, then scrapers per year
# L0b
python -c "from newslab.vintage import fill_actuals; ..."
python -c "from newslab.consensus import ...; ..."
# gates: see SPEC.md — 10-event hand spot-check is NOT optional
# L1
python -c "from newslab.census import load_bars, run_census, continuation_table, gapfill_table; ..."
# L2 predictors, gate as-of < release ts
# L3: ceiling test first; freeze PREREG; only then NEWSLAB_UNSEAL=1
```

## Known gaps (tasks, not surprises)
1. **Bars end 2026-01-31.** Window to Jul 2026 needs a Databento top-up
   (price with their cost endpoint first) or Sierra .scid export.
2. Core-PPI FRED series id marked TO-VERIFY in config.py — verify, don't
   guess.
3. ISM actual/forecast come from the calendar scrape only (no FRED first
   print exists) — flagged in `actual_source`.
4. FOMC "surprise" needs a definition ruling from Angus: decision vs
   priced (CME FedWatch as-of) is the honest one; statement/dot-shift is
   not codeable v1. Until ruled, FOMC rows sit in the census (reaction
   lane) but out of L3.
5. Claims holiday-week rows carry needs_verification=True — resolve from
   DOL archives before GATE L0.

## Env
- NEWSLAB_SEAL_FROM (default 2025-10-01) — Angus's ruling to freeze
- NEWSLAB_UNSEAL=1 — sealed scoring, only after prereg sha committed
- NEWSLAB_PREREG_SHA — stamped into every L3 verdict line
- FRED_API_KEY, CLEV_NOWCAST_URL
