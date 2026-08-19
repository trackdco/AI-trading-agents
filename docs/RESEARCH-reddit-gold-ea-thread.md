# AUDIT — Reddit thread: XAUUSD trend EA (u/Loose-Object-8913) + MGC turn bot (u/One_Conflict_1987)

**RESEARCH ONLY. Nothing here is measured.** Two self-described systems, neither with a
single performance number attached. Recorded for provenance and cross-referenced against
what this repo has already measured.

## Evidence limits — read first

Both authors are describing work in progress. **Neither posts a win rate, profit factor,
sample size, date range, or cost assumption.** One is "running on demo", the other is
"early sandbox" and still wiring up its data feed. There is no result in this thread to
confirm or refute — only two designs.

The OP's replies carry no information: each restates the other participant's message back
to them, and one reply is a verbatim copy of the message it answers. The extractable
content is the OP's opening post and three of `One_Conflict_1987`'s replies.

---

## Model A — XAUUSD H4/H1 trend continuation EA (u/Loose-Object-8913)

Six years discretionary XAUUSD, now an MT5 EA. Stated premise: *"strong higher-timeframe
trend · shallow pullbacks · continuation moves during active sessions."*

| component | stated | tier |
|---|---|---|
| instrument | XAUUSD spot, MetaTrader 5 | STATED |
| bias timeframe | H4, *"EMA structure"* | STATED / periods **UNDEFINED** |
| execution timeframe | H1 | STATED |
| entry arm 1 | pullback entries during established trends | STATED / mechanics **UNDEFINED** |
| entry arm 2 | breakout entries during strong momentum | STATED / mechanics **UNDEFINED** |
| stop / target | ATR-based | STATED / period and multiples **UNDEFINED** |
| sizing | optional pyramiding during strong trends | STATED / trigger, adds, cap **UNDEFINED** |
| sessions | *"active sessions"* named in the premise | **never appears in the rules** |
| results | none given | — |

**Nothing here is codable.** Every parameter that would decide the outcome is missing:
EMA periods and what "structure" means (cross, slope, stack), what makes a trend
"established", how a pullback is measured or how shallow is shallow, ATR period and
multiples, and every pyramiding parameter.

**One structural gap is worth naming beyond the missing numbers.** The two entry arms —
pullback-in-trend and breakout-on-momentum — can both be live on the same bar, and no
precedence rule is given. A trend strong enough to break out is also a trend you would buy
the pullback in. Whichever arm fires first will dominate the book, and which one that is
was never decided.

## Model B — MGC turn detector (u/One_Conflict_1987)

The more specific of the two, and the only source of a testable rule.

| component | stated | tier |
|---|---|---|
| instrument | MGC (micro gold futures), short-term; environment built to take any ticker | STATED |
| inputs | price + volume | STATED |
| volume role | **confirmation only, never a trigger** — *"improves confidence in a real turn, either direction"*; explicitly direction-agnostic | STATED |
| core signal | first and second derivatives of a **smoothed** price curve | STATED / smoother **UNDEFINED** |
| **the rule** | second derivative *"should compress and reverse, then hold for two 5 minute candles"* | **STATED — codable** |
| selectivity | *"mostly it doesn't trade — only A+ setups initially"* | STATED |
| known cost | entries and exits are *"a little late"* by design | STATED, self-identified |
| stops / targets | — | **absent entirely** |
| stack | ThinkScript prototype → Python, Schwab API | STATED |
| stated blocker | *"having a robust data set to backtest ideas fully"* | STATED |

**The one codable claim:** a smoothed price series' second derivative compresses toward
zero, reverses sign, and holds that sign for two consecutive 5-minute bars → turn confirmed,
enter in the reversal direction.

**The smoother is the model, and it is undefined.** A second derivative of unsmoothed price
is almost pure noise; everything about whether this works lives in the smoothing choice and
in what "compress" means numerically. Both are sweep variables, not details:

- smoother: EMA / Savitzky-Golay / Kalman / spline, and its window
- "compress": |d²| below an absolute threshold, or below a rolling percentile, and of what
- volume confirmation: no threshold given
- exits: no stop, no target, no time limit stated anywhere

---

## Cross-reference against what this repo has already measured

This is the part worth keeping. Four of the ideas in this thread have been measured here.

**1. ATR-based risk — SUPPORTED, and it is the strongest thing in the thread.** Model A's
choice of ATR-based stops and targets is the one design decision this repo actively
endorses. Measured on GC: a 30-point risk cap fires on 0.6% of 2023–25 trades and 29.5% of
2026 days, while 0.5 × prior-day ATR fires 8.8% and 7.1%. **Percent-of-price does not
transfer either** (19.4% vs 52.7%). Gold's 2023→2026 shift is a volatility regime change,
not a price-level one — its 15-minute opening range went 4.5 → 18.5 points while going
0.23% → 0.40% of price. Any gold parameter in points is silently a different parameter each
year. See `.claude/skills/gold-orb-models/references/null-result.md`.

**2. Pullback continuation — bad prior, with a specific diagnosis.** The
breakout-pullback-continuation model was refuted by its own author on 5 years of S&P
(~130 trades, unprofitable; TP sweeps and stop-order variants all worse), and his diagnosis
transfers to any pullback-entry model including Model A's: **the strongest breakouts have
momentum and do not pull back, so waiting for a pullback adversely selects the weak ones.**
That is a mechanism, not a coincidence, and Model A inherits it.

**3. Breakout-on-momentum — the family this repo just retired.** Different timeframe and
anchor from the ORB work, so not a refutation of Model A, but the entry family is closed on
GC after four independent falsifications. Model A's second arm is starting from a
measured-negative prior on the same metal.

**4. Pyramiding — measured and failed.** BR-44 in this repo: conviction sizing FAILED.
Model A lists it as optional, which is the right default.

**5. "Mostly it doesn't trade" — this repo's most consistently wrong instinct.** Selectivity
has cost money at every scale here. The most selective ORB stack was the worst cell in its
study; the most selective iFVG stack (NY + obvious p90) was −0.194R against −0.144R for the
unfiltered book; the tomtrades ablation found every confluence subtracting with the full
stack worst of all; and BR-39 found frequency beats EV under a payout cap. Filtering to
"A+ setups" is the intervention most likely to feel right and measure worst.

**6. Volume as confirmation — partially measured, and it did not hold.** Breakout-bar
relative volume against a slot-matched 14-day baseline gave +0.021R at 1.2×, +0.047R at
1.5×, +0.008R at 2.0× — a non-monotone spike, not a stable effect. That was measured on
breakouts rather than turns, so it is a prior and not a refutation of Model B's use. Note
that Model B's framing — *volume confirms that a turn is real, in either direction* — is a
strictly weaker and more defensible claim than "volume predicts direction", and it is the
version worth testing.

**7. Spot vs futures volume — Model B is right and it matters.** `One_Conflict_1987`'s point
that spot is noisy and futures volume is the better input matches a finding already recorded
here: **spot gold has no real volume**, which is why volume-derived levels (VAH/POC/VAL)
break on XAUUSD. This is recorded as an amendment in `docs/DECLARATIONS-gold-vah-break.md`.
It also means Model A, on XAUUSD spot, could not add a volume filter even if it wanted one.

**8. Their stated blocker is the one this repo already solved.** *"Having a robust data set
to backtest ideas fully"* — GC 1-minute OHLCV for 2023-01-02 → 2026-08-11, 1,276,717 bars
over 936 session days, is committed to this branch at `748df23`.

---

## What is actually testable from this thread

One thing: **Model B's second-derivative turn rule.** It is a candidate generator, which is
exactly the interface the ORB harness now exposes — `run(bars, cfg, ctx, signal_fn=...)`
taking `Candidate(signal_tmin, fill_tmin, direction, stop_ref, meta)`. The exits, ATR risk
cap, ratchet, time stop, breakers and cost model all apply unchanged. See
`src/research/orb/README.md`.

What would have to be declared before running it, because the source does not specify them:
the smoother and window, the numeric definition of "compress", the stop reference (the model
states none — the natural choice is the pre-turn extreme), the target, and the volume
confirmation threshold. Each is a sweep variable and each must be published per value.

**Model A is not testable as stated** and could not be made so without inventing the
parameters that decide it, which would be measuring my own model and attributing it to
someone else.
