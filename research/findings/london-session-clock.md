---
date: 2026-08-04
status: reference
tags: [london, session-structure]
sources: []
---

# The London session clock — standing reference for every candidate

- **Windows in ET (NQ terms):** Asian range ≈ 18:00/19:00–02:00 ET (window start
  is itself a parameter); pre-London "dead hour" 02:00–03:00 ET; London window
  03:00–06:00 ET (08:00–11:00 UK). The shop's existing London canon trades
  03:00–05:00/04:00–06:00 ET depending on DST (scripts/london_canon.py).
- **DST trap:** UK BST/GMT vs US EDT/EST diverge for ~2–3 weeks a year around the
  change dates, so the 08:00 UK cash open MOVES in ET terms during those weeks.
  Rule: mechanisms anchored to the *European cash open* (LSE 08:00 UK / Xetra
  09:00 CET) must key off the UK/CET clock, converted per-day — never a hardcoded
  ET time. Mechanisms anchored to *Globex structure* (Asian range, overnight
  extremes) can live in ET. The repo already has the per-day converter:
  `scripts.run_triggers_london.london_window_et`.
- **Structural role of the window:** first deep-liquidity repricing of overnight
  inventory before the US open; the stop pools left by the thin Asian session
  (its high/low) are the session's standing liquidity feature.
- **Natural concept pairs from the sweep:** sweep-reversal vs sweep-continuation
  are the SAME trigger event traded opposite ways, separated by *when* the sweep
  occurs (pre-London 02:00–03:00 ET sweeps tend to continue; London-open sweeps
  tend to reverse — per NQ session-stats sources, to be verified on our data).
  Failed-break fade vs CVD-exhaustion fade are level + flow versions of one
  family. Candidates from these pairs must be tested as a family, not as
  independent discoveries — the trial ledger counts them together.

# Research-environment limitation (2026-08-04)

Direct fetching of external trading sites is blocked at this environment's egress
proxy (403; only the WebSearch API path is permitted). Article summaries in this
sweep are built from search-result content; `sources` URLs are leads, not full
reads. Deep-dive rounds (post-greenlight) should re-read key sources from an
environment with open egress, or via Angus pasting material in.
