# DECLARATIONS — the Reddit-thread second-derivative turn detector, on GC train

Written before any sweep runs, per this repo's law. Implements Model B from
`docs/RESEARCH-reddit-gold-ea-thread.md` — the one testable claim in that audit — as a
`signal_fn` for the harness documented in `src/research/orb/README.md`.

## D0 — Scope and the seal

**Train only: 2023-01-02 → 2025-08-31.** The sealed holdout, 2025-09-01 → 2026-03-01,
is **not read by any script in this work** and stays sealed regardless of what train shows.
2026-03-02 onward is separately and permanently disclosed from the ORB programme and is
also not used here.

## D1 — The codification, stated so it cannot drift

The source (`One_Conflict_1987`, quoted in full in the audit doc): the second derivative of
a smoothed price curve *"should compress and reverse, then hold for two 5 minute candles."*
Nothing else about the rule is stated — no smoother, no stop, no target, no numeric
"compress" threshold.

**Reading taken:** "compress" (magnitude shrinking to near zero) and "reverse" (sign
change) are not two conditions but one — a second derivative's magnitude passing through
zero IS a sign change. So a **turn candidate** is a bar `t0` where the smoothed series'
discrete second derivative flips sign relative to the prior bar. It **confirms** if the new
sign holds for the next two 5-minute bars (`t0+1`, `t0+2` — the literal "hold for two 5
minute candles"), and **fills at the open of the bar after that** (`t0+3`), which is why the
source itself calls its entries "a little late."

**Direction**, not stated by the source and supplied here: a flip to positive curvature
(concave-down → concave-up — a decline decelerating into a base) is read as bullish; the
mirror is bearish. This is the single largest interpretive liberty in this document.

**Smoother:** EMA on 5-minute closes, span swept per D2. The source names no smoother; EMA
is the simplest defensible reading of "smoothed price curve" and the only one implemented.
Savitzky-Golay and Kalman variants are **not built** and are not claimed to have been ruled
out — absent, not refuted, per the repo's evidence-tier convention.

**Stop:** not stated by the source. Declared here as the local price extreme (low for a
long, high for a short) over the window from two bars before the crossing through the
confirmation bar — the structure the "turn" is being traded against. An ATR-multiple
alternative was considered and **not implemented** in this pass; recorded as a gap, not
tested and not claimed negative.

**Volume confirmation:** per the source, direction-agnostic — it "improves confidence... in
a real turn, either direction," never sets direction itself. Implemented as a floor on the
confirmation bar's own 5-minute volume against a trailing, bar-shifted 14-bar mean.

**No day resets.** The smoother runs on one continuous series across the whole span with no
reset at calendar boundaries — see `src/research/gold/turn_detector.py` docstring.

**One stated limitation carried over from the harness, not fixed:** a candidate whose fill
lands after midnight relative to its confirmation bar is silently dropped (the harness looks
up the fill inside the confirmation bar's own calendar day). Small, direction-neutral,
conservative. Not corrected in this pass.

**One correctness fix that came out of building this**, applying to the shared harness and
therefore to ORB too (verified not to change any of the 35 existing ORB tests): a candidate
whose stop sits on the wrong side of its actual fill price — possible for any signal whose
stop is computed from bars strictly before the fill, since price can run past that reference
before the fill happens — is now rejected rather than mispriced as a favourable "stop."

## D2 — Sweep grid

One axis at a time off a fixed baseline, matching the discipline used throughout the ORB
programme. Everything not listed is held at its baseline value.

| | baseline | swept |
|---|---|---|
| EMA span (5m bars) | 10 (50 min) | **{5, 10, 20, 40}** |
| hold bars | 2 | fixed — the source's literal "two candles" |
| cooldown (5m bars, BR-9/BR-10) | 12 (1 h) | **{0, 6, 12, 24}** |
| stop lookback | 2 bars | fixed |
| volume confirmation | off | **{off, 1.2×, 1.5×, 2.0×} of trailing 14-bar mean** |
| target | 1.5R | **{1.0R, 1.5R, 2.0R, 2.5R}** |
| risk cap | 2.0 × prior-day ATR (tail guard, ATR units per house rule 8) | fixed |
| max trades/day | 6 | fixed |
| forced flat | 480 min from entry | fixed |
| breakers, weekday skip | off | fixed off — bare baseline |
| costs | 1 and 2 ticks/side + $3 commission | both reported |

Four axes, sixteen cells total (four values each, baseline shared), roughly 30+ trades per
parameter is not pre-verifiable here since candidate frequency is a measured, not designed,
quantity — reported per cell alongside the result rather than assumed.

## D3 — Predictions, stated before running

1. **The bare rule will not clear +0.10R.** Every entry family measured on gold this session
   has failed the promotion gate; there is no reason to expect a rule with three undefined
   parameters and one large interpretive liberty (the direction mapping) to be the exception.
2. **Volume confirmation will look like the ORB participation result: a real but small
   effect, or a non-monotone spike, not a rescue.** RVOL on breakout bars peaked
   non-monotonically at 1.5× in the ORB work; expect something similar here, not a clean
   dose-response.
3. **Shorter EMA spans will be noisier and less reliable than longer ones**, since less
   smoothing means more spurious zero-crossings — but a longer span also means fewer,
   later signals, so the honest expectation is a frequency/quality trade rather than a
   monotone win for either end.
4. **The direction-mapping choice (D1) is the most likely single point of failure.** If the
   rule is negative, it is worth checking net EV on the OPPOSITE mapping before concluding
   the underlying curvature signal carries nothing — a wrong sign convention and a genuinely
   absent effect look identical in the top-line number.

## D4 — Promotion gate

Unchanged from the ORB programme: OOS/train expectancy ≥ +0.10R/trade, PF ≥ 1.3, n ≥ 200,
stable across neighbouring cells, survives 2-tick slippage. Kill or flag as a lead only (per
the ORB precedent) if none of the above holds but a monotone dose-response is present.

## D5 — RESULTS

Appended after the runs.
