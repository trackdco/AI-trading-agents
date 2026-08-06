# Lookahead leak — damage measurement (2026-08-06)

Angus found a lookahead leak in the canon's depth check and ordered the live-sim
run stopped. Traced, confirmed in BOTH engines, and measured here.

Reproduce: `python -m scripts.leak_damage_canon` / `python -m scripts.leak_damage_shelf`

## The bug

**Canon.** `scripts/condense_depth.py:46-54` keeps the LAST book state within each
minute (`groupby("minute").tail(1)`) but stamps it with `r["minute"]` — the minute's
START. So the snapshot labelled `10:15` is really the book at ~`10:15:59`.
`src/canon/features.py:69` then selects `dep[dep.ts <= minute]` and takes the max.
Fills are minute-aligned (verified: `fill_ts` seconds are all zero), so a fill at
`10:15:00` reads the `10:15:59` book — **59 seconds of future**. Live cannot do this;
the ingestor reads the book at the moment of fill. `depth_at`'s own docstring says
"the live ingestor MUST call this exact function", so live and backtest genuinely
diverged.

Depth is load-bearing in FOUR places: `W` (pre-market HARD gate), `D` (gold HARD gate
AND a 2x-weighted score bit), `WALLSZ` and the `dep_wall_below_d >= 2.75` cut (both
gold admission gates in `funded_book.load_book`).

**Shelf.** `nya_ibc_desk_run.build_shelf_trades:138-147` reads flow features AT the
fill minute. `fp_minutes.delta` is signed volume summed over the WHOLE minute;
`flow_features.cvd` is a cumsum INCLUSIVE of it. The touch is intra-minute, so 3 of
the 4 conviction flags leak (`delta_with`, `stretched`, `near_target`); only `early`
(touch at exactly 10:00) is clean, being the clock.

## Method

Honest read = the last state genuinely available before the fill: `dep.ts < minute`
for depth; `delta[m-1]` and `cvd[m]-delta[m]` and `vwap/sd` at `k0-1` for the shelf.

Both harnesses reproduce the shipped (leaky) numbers exactly before switching the
read — canon WALLSZ reproduces 100.00%, shelf CONFIRMED reproduces at n=29 / 96.6%
against the frozen spec's 97%. So the honest-vs-leaky delta is the leak, not a
rewrite.

**Measured on the FULL candidate population, not `S.valid`.** `valid` is itself the
survivor set of the leaky gates, so filtering on it hides candidates the leaky read
rejected but an honest read admits. Every refusal in this book is depth-driven
(947 `gold_no_wall_ahead` + 736 `pre_wall_behind` in fit) and every refused row
carries its outcome, so the honest book is fully measurable off the same rows. The
first pass made this mistake and understated the honest set by ~300 trades.

## Canon: the depth family is ~90% lookahead

96.7% of candidates (5104/5279) get a different book state under the honest read.

| gold, 1-lot | n | WR | sum | mean | lift vs base |
|---|---|---|---|---|---|
| all candidates (no gate) | 3777 | 35.7% | $+26,632 | $+7.1 | — |
| leaky gate (shipped) | 625 | 53.0% | $+92,473 | $+148.0 | **+17.2pp** |
| honest gate | 933 | 37.6% | $+5,380 | $+5.8 | **+1.9pp** |

| pre-market, 1-lot | n | WR | sum | mean | lift vs base |
|---|---|---|---|---|---|
| all candidates (no gate) | 1502 | 32.6% | $+28,881 | $+19.2 | — |
| leaky W gate | 394 | 47.2% | $+63,901 | $+162.2 | **+14.6pp** |
| honest W gate | 682 | 34.5% | $+25,486 | $+37.4 | **+1.8pp** |

**89% of gold's apparent edge and 88% of pre-market's was lookahead.** The gates were
not selecting good trades; they were reading the next 60 seconds. Honestly they are
near-inert — +1.9pp / +1.8pp over simply taking every candidate. Note the honest
gates admit MORE trades (933 vs 625, 682 vs 394) at far worse win rates: with the
future removed, the "quality" filter stops discriminating.

The set turnover is near-total: of the 625 leaky-admitted gold trades, 329 (53%) were
admitted ONLY because of the leak.

## Shelf: base strategy intact, conviction tier not established

Outcomes are IDENTICAL under both reads — the entry trigger and the management walk
never touch the fill minute's aggregate — so only the tier, and therefore the
sizing, moves. That isolates the conviction layer exactly.

| | CONFIRMED | BASE | tier separation |
|---|---|---|---|
| leaky (shipped) | n=29, 96.6% WR, +34.8R | n=83, 63.9% WR, +47.7R | **+32.7pp**, perm-p=0.0001, CI [+19.9,+44.6] |
| honest | n=26, 84.6% WR, +22.3R | n=86, 68.6% WR, +60.3R | **+16.0pp**, perm-p=0.082, CI [-1.7,+31.8] |

Tier flips on 27/112 (24.1%). 15 trades were CONFIRMED only thanks to the leak
(93.3% WR).

**The base strategy is untouched: 112 trades, 72.3% WR, +82.5R.** It never read the
leak and needs no rebuild.

**The conviction tier does not survive.** Honestly it separates by +16.0pp but at
p=0.082 with a 95% CI crossing zero — directionally positive, not established. The
frozen spec's 97% CONFIRMED tier was a leak artefact. Flat sizing yields +82.5R;
the honest tiered split is not distinguishable from it on this sample.

## One caveat that matters, in the canon's favour

The honest backtest is a CONSERVATIVE lower bound, not a fair estimate of live. Our
depth data is one snapshot per minute, so the freshest non-future read available to
the backtest is the previous minute's close — up to ~60s stale. Live reads the book
at the exact moment of fill, which is strictly fresher. So live has better
information than this honest backtest, and the true honest edge is somewhere at or
above +1.9pp — though nothing here suggests it approaches +17.2pp, since that number
is built from information no live system can ever have.

**This is fixable in the data, not just the code.** `condense_depth.py` should stamp
each snapshot with the TRUE `ts` of the last update rather than `minute`. Then
`dep.ts < fill_time` is both honest and maximally fresh, and the depth family
deserves a genuine re-test before being written off. The raw MBP-10 is needed to
re-condense.

## Verdict

- **Canon depth family: dead as it stands.** Every gold trade in the book was
  admitted through a leaky gate. Re-condense with true timestamps, then re-test
  honestly and pre-registered. Do not assume it survives.
- **Shelf base strategy: alive, unaffected.** Ship-relevant work stands.
- **Shelf conviction tier: withdraw.** Re-derive from scratch honestly if wanted;
  the current 97% figure cannot be cited.
- **The halted 32-day live-sim:** behavioural findings remain provisionally
  informative (both sides traded the identical stream), but every absolute dollar
  figure is void.
