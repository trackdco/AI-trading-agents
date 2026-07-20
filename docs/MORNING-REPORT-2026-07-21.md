# MORNING REPORT — overnight engine audit + entry-timing fix (for Brake/Angus)

**TL;DR:** The champion engine is fundamentally SOUND (no lookahead, no material inflation).
Fixing the one confirmed correctness bug Brake ruled on — entries activating a full minute late —
produced a **big, consequential result**: it revealed that the champion's *dollar* edge substantially
leaned on that bug. Corrected, the champion makes **~$8k not ~$14k** over Feb–Jul. The damage is
entirely in the **E4 (market-entry, WAR-day) arm**; the **E3 (limit) arm actually improves**.
**Recommendation: keep the fix (it's correct), and re-evaluate the champion — especially the E4
market-entry arm — under correct timing before trusting the +$14k.**

---

## 1. What I did overnight
1. Completed the P0 engine audit (3 parallel auditors: fill-realism, lookahead, timezone) — all
   cross-verified.
2. Applied the two fixes Brake authorized (entry timing + resting-fill gating).
3. **Measured the fix's champion P&L impact** before/after, capped and uncapped.
4. Ran an independent adversarial verification of the fix + the finding (3 more agents).
5. [pending] DST fix (bug #3), test updates, full suite green.

## 2. Audit verdict: engine is SOUND
- **No lookahead** — verified empirically (prefix-invariance: indicators 80/80, triggers 22/22).
- **No material inflation** — stop-first ties, trade-through fills, correct slippage, min-stop floor,
  correct R/$; all confirmed by code-trace + probes.
- The only leaky resampler in the repo is on the SUPERSEDED `brake-43x58e` naive engine, not the
  champion. Ignore that naive engine's numbers.

## 3. The entry-timing fix and its impact (THE headline)
The bug: an entry order activated one bar LATE (the fill step ran before order-placement in the
per-bar loop), contradicting the engine's own docstring ("active for bars ≥ ts"). Fixed so orders
activate on the trigger's own bar.

Champion (E3+V8 non-WAR / E4 WAR, 08:00–10:15), today's engine:

| config | trades | net $ | win% | net R | exp |
|---|--:|--:|--:|--:|--:|
| capped (max2/day) baseline | 132 | **+$14,009** | 32.6% | +27.2 | +0.206R |
| capped fixed | 145 | **+$7,949** | 29.0% | +37.1 | +0.256R |
| uncapped baseline | 161 | **+$14,808** | 34.2% | +34.1 | +0.212R |
| uncapped fixed | 177 | **+$8,438** | 29.4% | +44.0 | +0.249R |

Note the baseline (+$14,009) reproduces the canonical champion (+$13,857) — so this is the real thing.

**The paradox: R goes UP, dollars go DOWN.** Resolved by splitting the arms (uncapped):

| arm | baseline | fixed |
|---|---|---|
| **E3 (limit)** | 19t / +$3,246 / **42%** win | 19t / +$2,728 / **63%** win |
| **E4 (market)** | 142t / +$11,562 / **33%** win | 158t / +$5,710 / **25%** win |

- **E3 limit entries: the fix HELPS** (win 42%→63%). The bug was costing genuine limit fills.
- **E4 market entries: the fix HURTS** (win 33%→25%, $ halves). A market order that filled a minute
  late was catching a small pullback (better price). At the correct immediate fill, E4 is much worse.
- The champion is dominated by E4 (158/177 trades), so net dollars fall.

Mechanisms confirmed on real trades:
- **Timing**: e.g. 2026-04-23 long — baseline filled 08:04 @ 27038.25, fixed filled 08:03 @ 27041.50
  (exactly one bar earlier, at the real bar open).
- **Cap crowding** (capped only): 2026-04-30 — baseline caught the 09:14 short (+$1,665); fixed filled
  two earlier losers and the 2-trade/day budget was spent before 09:14, missing the monster.
- Exit mix shifts toward more stops (uncapped stops 104→124, targets 50→43).

## 4. What this means (for Angus)
- **The fix is correct — do NOT revert.** A limit/market order entering a minute late is not a real,
  tradeable edge; it flattered the backtest.
- **The E4 (market-entry, WAR-day) arm's dollar edge was largely a fill-bug artifact.** It should be
  re-examined; the E3 (limit) approach is the robust one and gets BETTER under correct timing.
- The E3/E4/management tournament should be **re-run on the fixed engine** — the previous winner was
  chosen under buggy fills.
- Everything here is in-sample Feb–Jul; treat as a strong lead pending the OOS discipline.

## 5. Adversarial verification (3 independent agents)
**(a) Raw-bar hand-trace — CONFIRMED.** Independently traced fills against the raw 1-minute bars:
- The baseline vs fixed fill is exactly ONE bar apart in 96.9% of matched E4 pairs; every fill price
  is a real bar open + an identical ~1-tick adverse slippage — so the engines differ ONLY by which
  bar they enter on.
- The buggy engine's higher win rate is mechanical: entering one bar LATE **skips the trigger bar's
  own adverse intrabar excursion.** All 3/3 stop→target outcome-flips are explained exactly (the
  trigger bar's high/low hit the stop on the immediate fill; the late fill entered after the spike and
  survived). 27 of 29 "extra" fills the fixed engine takes are stops — valid losing signals the bug
  skipped.
- Conclusion: the fixed engine correctly enters *into* the spike (realistic); the bug entered *after*
  it (unrealistic). The E4 33% win rate was inflated; 25% is real.

**(b) Fix code-correctness trace — [pending].**
**(c) Red-team refutation attempt — [pending].**

## 6. Remaining engineering (status)
- [ ] Update 4 E4/EC tests to the corrected `≥ ts` timing (they encoded the 1-bar-late bug).
- [ ] DST fix (bug #3) + regression test; confirm zero change to Jan–Jul champion.
- [ ] Full test suite green.

## 7. Artifacts
- Fix patch: `patches/engine-entry-timing-fix.patch`
- Measurement harness: `scripts/_measure_timing_fix.py` (+ `_diff_champion.py`) — run from a
  getting-started checkout.
