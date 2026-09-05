# FINDINGS — clean-room re-implementation by a blind agent (2026-09-04)

His ask: "run it with a blind agent." A fresh agent was given three files and
nothing else — `SPEC-va-book-clean-room.md` (the rules as prose, 1,197
words), the exact bar tape the engine reads, and the news calendar. It was
told not to open anything outside that folder, had no results, no expected
figures, and no engine code. It wrote its own backtester from the document
and ran it. Then the two trade lists were joined on (session-day, signal
minute, direction, level).

| | engine (armed VA book) | blind agent |
|---|---:|---:|
| trades | 6,486 | 6,486 |
| matched | — | **6,486 / 6,486** |
| identical result, R and risk | — | **100.0%** |
| EV net | +0.1833 | +0.1833 |
| net R | +1,189 | +1,189 |
| 2023 / 2024 / 2025 / 2026 net R | +264 / +357 / +302 / +267 | identical |

**Zero trades differ.** Not one signal, fill, stop, arming decision, exit or
SAR price came out differently when a stranger built the strategy from the
written rules alone.

What this establishes, and what it does not:
- The prose spec is **complete**: every edge case that changes a trade —
  the volume-profile expansion, the signal-window bounds, the signal candle
  counting toward arming, ties scored as stops, SAR at the opposing
  candle's close, the occupancy nanosecond — is written down well enough
  that a reader with no other context lands on the same 6,486 trades.
  Angus's external pipeline (§38) reached a 3.6% count gap on this book
  after seven interrogation rounds; this document closes it to zero.
- The engine has no hidden behaviour. Anything the engine does that the
  spec does not say would have shown up as a difference.
- It does **not** say the strategy works live — same limitation as every
  other test today. It says the document the live engine will be built
  from is the right document.
- The agent listed eight ambiguities it resolved by the most literal
  reading (`docs/blind_summary.txt`). All eight matched the engine. Those
  sentences should be tightened in the spec anyway, since the next reader
  may not choose literally.

Scope: the value-area book, armed, 2023–26. The three-book empire's VWAP
and 8-level rules are not yet written as clean-room prose; this document is
the template for them and the seed of the frozen spec file.

Files: `docs/SPEC-va-book-clean-room.md`, `scripts/blind_backtest.py` (the
agent's code, untouched), `scripts/blind_diff.py`, `docs/blind_summary.txt`.
