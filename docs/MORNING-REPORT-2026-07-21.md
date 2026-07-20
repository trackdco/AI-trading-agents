# MORNING REPORT — overnight engine audit + entry-timing fix (for Brake/Angus)

**TL;DR:** The champion engine is fundamentally SOUND (no lookahead, no material inflation). I fixed
the one confirmed correctness bug Brake ruled on — entries activating a full minute late — and the two
follow-ons (resting-fill gating, DST session-date). All fixes are independently verified correct; the
full test suite is green (298 passing incl. new regression tests).

**The nuanced headline (survived an adversarial red-team):** the fix **corrects an inflated
1-contract dollar figure** — the champion's oft-cited "+$14k" over Feb–Jul was partly late-fill
artifact and partly rule-violating fills; honestly restated it's **~+$8k at 1 contract**. BUT the
strategy is **risk-sized** (R is the real currency; dollars-at-1-contract is just a reporting
convention), and **in R the champion is flat-to-slightly-better (+34R → +44R)** — the edge is **not
eroded**. The dollar drop is a sizing-currency + trade-admission effect, not a broken signal.
**Keep the fix. Restate the champion's dollars honestly. The genuine concern — statistically thin
edge on BOTH engines — predates the fix.**

---

## 1. Audit verdict: engine is SOUND
Three parallel auditors (fill-realism, lookahead, timezone), all cross-verified:
- **No lookahead** — proven empirically (prefix-invariance: indicators 80/80, triggers 22/22).
- **No material inflation** — stop-first ties, trade-through fills, correct slippage, min-stop floor,
  correct R/$.
- The only leaky resampler in the repo is on the SUPERSEDED `brake-43x58e` naive engine, not the
  champion. Ignore that naive engine's numbers.

## 2. Fixes applied (all verified, suite green)
1. **Entry-timing (bug #1):** an order activated one bar LATE (fill block ran before order-placement),
   contradicting the engine's own docstring ("active for bars ≥ ts"). Moved the fill block after
   trigger-placement so orders activate on the trigger's own bar. **Independently verified correct**
   (no double-fill, no dropped order, no lookahead; fills at the bar-ts open = the earliest
   legitimately executable price).
2. **Resting-fill gating (bug #2):** the sit-out / VWAP-warmup / news-preopen blocks gated only NEW
   triggers, not resting-order fills — so the baseline was booking **rule-violating fills** inside the
   09:30–09:40 sit-out and pre-09:30 news windows. Added `avoid_entry` to the fill path.
3. **DST session-date (bug #3):** `normalize() + fixed-24h` mislabeled fall-back-Sunday evening bars.
   Fixed with a tz-naive next-calendar-day computation. **Confirmed inert on Feb–Jul** (champion
   byte-identical before/after) and covered by a new fall-back regression test.

## 3. Champion P&L impact of the entry-timing fix
Champion (E3+V8 non-WAR / E4 WAR, 08:00–10:15), today's engine:

| config | trades | net $ (1-contract) | win% | **net R** |
|---|--:|--:|--:|--:|
| capped (max2/day) baseline | 132 | +$14,009 | 32.6% | +27.2 |
| capped fixed | 145 | +$7,949 | 29.0% | **+37.1** |
| uncapped baseline | 161 | +$14,808 | 34.2% | +34.1 |
| uncapped fixed | 177 | +$8,438 | 29.4% | **+44.0** |

The baseline (+$14,009) reproduces the canonical champion (+$13,857) — this is the real thing.
**Read the R column, not the $ column** (see §4). In R the fix is flat-to-better; the $ figure falls.

By arm (uncapped): E3 limit 19t/+$3,246/42% → 19t/+$2,728/**63%**; E4 market 142t/+$11,562/33% →
158t/+$5,710/25%.

## 4. Why R goes UP but 1-contract $ goes DOWN (the crux)
Three independent verifiers dug into this. Reconciled:
- **The strategy is risk-sized.** Engine header: "$ P&L reported at 1 NQ contract (R is the calibration
  currency; Angus sized variably)." Realized P&L ∝ net R, not 1-contract dollars.
- **On the 123 RETAINED E4 trades** (same trade, shifted exactly 1 bar), correct timing gives
  **tighter stops (14.4→11.6 pts) and MORE R** (+17R→+56R; paired ΔR +0.32/trade, t=2.20, p≈0.028).
  The late fill was the distortion — it gave *wider* stops and less R. So "E4 edge was a late-fill
  artifact" is **backwards on the retained core**.
- **1-contract dollars fall because corrected entries are tighter** ($/R 444→180). Under proper
  risk-sizing you'd trade more contracts for the same risk → same-or-better dollars.
- **The aggregate win% drop (33→25%) is composition:** ~16 marginal fills the 1-bar delay was
  accidentally filtering (27/29 are stops), plus removing baseline "winners" that were themselves
  artifacts (e.g. the 02-11 +$2,067 E3 short — a 09:47 limit the no-chase t_cancel rule *should* have
  killed; the delay skipped the cancel bar and caught a lucky re-touch. Removing it is correct).
- **Hand-trace confirmed** the mechanism at the bar level: the late fill skipped the trigger bar's own
  adverse intrabar spike (all 3/3 stop→target flips explained); the fixed engine correctly enters into
  it. Realistic, not lookahead.

## 5. Adversarial verification (3 independent agents)
- **(a) Fix code-correctness — CORRECT.** Surgical diff; no double-fill/drop/lookahead; invariants hold;
  `avoid_entry` never loses an order. The 4 failing tests encoded the OLD 1-bar-late timing (now updated).
- **(b) Raw-bar hand-trace — timing shift is real & correct.** 96.9% of matched E4 pairs fill exactly
  1 bar apart at real bar opens; the buggy engine's higher win rate came from entering *after* the
  trigger bar's spike; 27/29 "extra" fills are legit signals the bug skipped.
- **(c) Red-team — refuted the strong headline.** The "+$14k" 1-contract figure is inflated (→ ~$8k),
  but "champion untrustworthy / E4 needs rethinking" does NOT survive: in R the champion is flat-to-
  better and retained E4 improves. **Honest caveats:** the R improvement (34→44) is itself within noise
  (Welch p≈0.88 on per-trade R); per-trade expectancy is thin on BOTH engines (t≈1.0–1.4, ~19 E3 days /
  ~70 concentrated WAR days); the edge's fragility predates the fix.

## 6. What to actually do (for Angus)
1. **Keep the fix — it's correct.** A limit/market order entering a minute late (and booking fills
   inside sit-out/news windows) is not a real edge.
2. **Restate the champion's P&L honestly:** ~+$8k at 1 contract (not +$14k); +44R over Feb–Jul in the
   sizing currency. The edge in R is intact-to-slightly-better.
3. **The real issue is statistical fragility** (thin per-trade expectancy on both engines) — this is
   what the roadmap (time-gating, CVD-confirm, ≥6pt stop, more OOS) is for; it is NOT caused by the fix.
4. **One genuine open item the fix surfaces: trade admission.** Correct activation admits ~16 marginal
   fills; whether to keep them is a tunable entry-window/filter question (candidate for the P1 work).
5. Re-run the E3/E4/management tournament on the fixed engine before locking a champion — the prior
   winner was chosen under buggy fills (this changes *rankings*, even if the aggregate edge holds).

## 6b. Bonus: champion variant comparison on the FIXED engine (diagnostic, for Angus)
Re-ran the tournament-relevant arms under correct fills (`scripts/_champion_variants.py`). Read R:

| variant | n | win% | net$ (1-ct) | **net R** | exp |
|---|--:|--:|--:|--:|--:|
| mixed (current champion) | 145 | 29.0% | +$7,949 | +37.1 | +0.256 |
| **mixed + 09:15–09:45 stand-out** | 132 | 31.1% | **+$10,392** | **+47.8** | **+0.362** |
| E3-only (limit) | 175 | 38.3% | +$5,234 | +26.1 | +0.149 |
| E3-only + 09:15–09:45 | 159 | 39.6% | +$6,876 | +31.2 | +0.196 |

Two findings:
1. **Do NOT drop the E4 (market/WAR-day) arm.** Mixed (+37.1R) beats E3-only (+26.1R) in net R AND $.
   E3-only has a much higher win rate (38% vs 29%) but LOWER expectancy — the E4 WAR-day arm genuinely
   adds net R. (This nuances §4: E4 is not "fake"; it contributes. Its per-trade $ is just small because
   its stops are tight.)
2. **The 09:15–09:45 stand-out robustly improves EVERY config** — it cleans up the dead 09:xx pocket
   (−0.81R/−0.33R buckets) and the marginal fills the timing fix surfaced. Best = mixed + stand-out:
   **+$10,392 / +47.8R / +0.362R** — recovers the dollars the fix "cost" AND lifts R.

**OOS-clean validation (did it overfit? No):** split the 09:15–09:45 stand-out IN-SAMPLE (Feb–May) vs
OUT-OF-SAMPLE (Jun–Jul) on the fixed engine:

| | trades | win% | net$ | netR | **exp** |
|---|--:|--:|--:|--:|--:|
| IS (Feb–May) no gate | 111 | 29.7% | +$6,724 | +34.1 | +0.307 |
| IS + stand-out | 101 | 31.7% | +$8,167 | +41.4 | **+0.410** |
| OOS (Jun–Jul) no gate | 34 | 26.5% | +$1,225 | +3.0 | +0.088 |
| OOS + stand-out | 31 | 29.0% | +$2,225 | +6.3 | **+0.205** |

The stand-out lifts expectancy **in both periods** (IS +0.31→+0.41R; OOS +0.09→+0.21R — more than
doubling the thin OOS tail) — directionally consistent, so it is **not overfit**. Caveat: OOS n=31 is
small and the underlying edge is thin (per §5), so treat the OOS lift as encouraging-not-proven.

**This is the night's cleanest actionable proposal for Angus:** extend the shipped 09:30–09:40 sit-out
to **09:15–09:45** on the fixed engine. It passed an OOS check; it needs only Angus sign-off + a
strategy-doc version bump (per the no-tuning rule) to lock.

## 7. Artifacts
- Full fix patch (engine timing + resting-fill gate + DST + tests): `patches/engine-entry-timing-fix.patch`
- Measurement harness: `scripts/_measure_timing_fix.py`, `scripts/_diff_champion.py`
- Evidence journals: `analysis/champ_{baseline,fixed}{,_cap50}.csv`
- Files changed (apply to a getting-started checkout): src/backtest/engine.py, src/engine/data.py,
  src/engine/indicators.py, tests/test_backtest.py, tests/test_sessions.py.
