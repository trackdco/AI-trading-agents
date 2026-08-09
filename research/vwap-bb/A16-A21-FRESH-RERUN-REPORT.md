# A16-A21 — fresh 2a/2b re-run and determinism check

**2026-08-08.** Per the closing instruction: *"re-hash, re-run 2a and 2b fresh with the
determinism check."* Spec after A16-A21: git blob
`4ad4ed815dda8446648160aa6e4f8dac66a91bde` / sha256
`9286ac1eadbedf49dba76715373cf9885b8034586933620e3d93476916aaf2b7`. **No outcome computed.**

## 1. 2a — spec-derived unit tests

93 tests (81 carried over from A1-A15, +13 new: GROUP K for A16's `limit_fill`, GROUP L for
A17's `cluster_levels_bounded`). Committed unrun, then run, per the two-commit protocol
(`test_spec_units.py` history: unrun commit, then the run commit).

**89 PASS, 4 FAIL.** The 4 failures (A8, A9, H1b, H1c) are the same pre-existing,
already-disclosed mis-constructed synthetic bars from before this round — none of A16/A17
touches trigger-candle construction or the Group-H synthetic session, and none of the four is
new. **13/13 new K/L cases pass exactly as reasoned from the amendment text before running.**
3 UNSPECIFIED-observed cases (B5, B6, L5) — B6's own scenario is separately promoted to an
asserted case (L3) now that A17 resolves what it could previously only record.

## 2. 2b — invariants over the whole trade list, fresh admission list under A1-A21

`invariants_a16.py`, built on `spec_a16.signal_candidates_a16` (A17 clustering) +
`spec_a16.admit_a16` (A16 fill). **1,470 trades**, 539 workbench sessions, 501 processed, same
three exclusion reasons as every prior run (22 holiday/short, 8 roll, 8 session-after-roll).

**10/10 invariants PASS**, including two carried unchanged from `invariants_2b.py` (1, 2, 3, 5,
6, 9, 10 — none of A16-A21 touches what they check) and:

- **Invariant 4, REWRITTEN.** The old clause ("fills at the OPEN of the bar after the signal bar
  closes") is exactly what A16 supersedes. The new text: *"fills at the limit or better if the
  one bar immediately following the signal bar reaches it; no fill, no trade."* Independently
  recomputes `limit_fill()` against every trade's own fill bar and checks it agrees with the
  recorded `fill_px`. **PASS, 0 of 1,470 violations.**
- **Invariant 11, NEW.** No admitted trade may exist whose own fill bar never reached its
  limit — A16's "no fill → no trade" as a hard, independently-rechecked invariant, not a
  restatement of what the admission code already enforces by construction. **PASS.**
- **Invariant 12, NEW.** Every admitted trade carries `sensitivity_open_px`, exactly equal to
  its own fill bar's open — A16's disclosure commitment ("every admission list... carries BOTH
  figures"), checked directly. **PASS.**

## 3. Determinism

`invariants_a16.py` run twice, independently (two separate process invocations):

```
run 1: TRADE-LIST SHA-256 (geometry only): 60dcbca918e98760ecb69e07887903f0eee48d5e4473c21109d8f9ddc4f5e687
run 2: TRADE-LIST SHA-256 (geometry only): 60dcbca918e98760ecb69e07887903f0eee48d5e4473c21109d8f9ddc4f5e687
```

**Identical.** The hash covers `session_date|cm|tf|direction|entry|stop_px|tgt_px|fill_px|`
`sensitivity_open_px|fill_min` for every trade, geometry only.

## 4. Why 1,470 (here) differs from 1,444 (`IMPLEMENTED-LEVELS-LIMIT-FILL-BUILD.md`)

Both use true single-bar limit-or-better fill (A16). The difference (26 trades, ~1.8%) is A17's
own, isolated effect: `IMPLEMENTED-LEVELS-LIMIT-FILL-BUILD.md` reused
`invariants_2b._instrumented`, which clusters via `vwapbb_signals.cluster_levels` (chaining,
pre-A17). This report's 1,470 uses `spec_a16.signal_candidates_a16`, which clusters via
`cluster_levels_bounded` (A17, mutual proximity). Same fill rule, different candidate population
upstream — this is the first isolated, geometry-only measurement of what A17 alone does to the
admission count, not a discrepancy between two reports of the same thing.

## 5. What has NOT been run

No sensitivity comparison report (limit-fill vs `sensitivity_open_px`, aggregated) has been
produced — the field is computed and invariant-checked on every trade, but no report reads it
yet. No Stage 3 seal. No pass marks signed. Per the closing instruction, this stops here for
signature.

**N_trials: 1 of 5, unchanged.** Nothing above is an outcome — unit-test pass/fail, invariant
violation counts, and a determinism hash are classification and measurement, not comparison of
results.
