# FINDINGS — Conviction audit (2026-09-03)

His ask: "run an audit and variable test and see what provides higher
confluence/conviction setups, and what may be lower conviction and worse
WR. Then tell me what concepts/additions to strategy you may recommend."

Script: `scripts/conviction_audit.py` (runs on the certified dumps from
`pd_va_backtest.py --levels all --tf 1 --sar --fill-through --news-gate
--max-risk 30` and `vwap_revolve.py --tf 1 --style retest --max-risk 30`;
those live on branch `claude/tradingview-mcp-agent-setup-ql18v8`).
Populations: 8-level book 22,187 trades, session-VWAP book 33,101 trades
(depth 3 / 1R). All R below is NET of the receipts' 0.5pt/RT cost.

## 0. Rule, written before results were read

Same bar as rounds 1–3 (S20, S21, S29) so it cannot move:
split by session-day at 2024-10-21; SURVIVOR = extreme buckets ordered
the same way in both halves, spread ≥0.05R in both, n ≥400 per half per
extreme bucket; WATCH = same at ≥0.03R; CUT = a bucket negative in both
halves at n ≥400 per half. 14 features × 2 books; expect ~1 spurious
WATCH by chance. Buckets fixed in the script, not tuned.

## 1. A bug caught before it became a finding

First pass showed "small-body signal candle" and "low-volume signal
candle" as survivors with +0.10R spreads. Cause: the dumps round
`t_sig_hrs`/`fill_hrs` to 3dp (±1.8s), so about half the trades indexed
one bar late — and for a next-bar fill that bar IS the fill bar. Candle
shape was being read off the bar that produced the outcome. Fixed with
exact-minute indexing (sanity counter: 0 mismatches on 55,288 trades).
After the fix both candle features are NULL. Logged because the
uncorrected version is exactly the kind of "conviction candle" rule
that reads true and is lookahead.

## 2. What sorts conviction (SURVIVORS, both books, both halves)

**Displacement before the retest (`excur`)** — how far price ran past
the level, in units of the trade's own stop, between the signal close
and the bar before the fill. Fill-time feature: legal as an arming rule
(the limit only goes live after the run), not as hindsight.

| displacement | 8-level n / WR / net EV | VWAP n / WR / net EV |
|---|---|---|
| ≥2R past the level | 9,323 / 66.9% / **+0.202** | 10,907 / 66.1% / **+0.205** |
| 1–2R | 6,774 / 67.3% / +0.165 | 12,024 / 64.6% / +0.131 |
| 0.5–1R | 4,571 / 62.8% / +0.027 | 7,800 / 61.0% / +0.018 |
| <0.5R | 1,519 / 65.7% / −0.002 | 2,370 / 64.1% / −0.022 (CUT: neg both halves) |

Spread IS/OOS: +0.29/+0.15 (levels), +0.27/+0.20 (VWAP). Read: a retest
of a level that price has ALREADY run the target distance past — the 1R
target sits inside the prior swing — earns 0.17–0.20R net. A retest of a
shallow poke (target needs a new extreme) is a scratch. Not stop-width
in disguise: inside every stop bucket the same ordering holds
(`excur_x_stop` table; e.g. stop <1× recent range: 2R+ +0.24 vs 0.5–1R
+0.04 on levels, +0.22 vs +0.09 on VWAP).

**Session progress (`sess_pct`)** — session range so far ÷ prior-day
range, at signal time.

| day has moved | 8-level net EV | VWAP net EV |
|---|---|---|
| ≥1× prior-day range | +0.178 | +0.153 |
| 0.5–1× | +0.165 | +0.147 |
| 0.25–0.5× | +0.117 | +0.094 |
| <0.25× | **+0.065** | **+0.074** |

Spread IS/OOS +0.13/+0.10 (levels), +0.11/+0.06 (VWAP). Quiet early tape
is the low tier; a day that has already travelled is the high tier.
Overlaps the hour ladder (early Asia is both) but is a day-size sorter,
not a clock.

**The two together (post-hoc cross, shown split-half, not a rule):**

| tier | 8-level: n, WR, net EV (IS/OOS), share of book R | VWAP: same |
|---|---|---|
| A displaced ≥1R AND day moved ≥0.5× | 9,196 · 68.6% · +0.223 (+.25/+.21) · **66%** | 11,261 · 66.5% · +0.194 (+.20/+.19) · **56%** |
| B displaced only | 6,901 · 65.0% · +0.137 (+.14/+.14) · 30% | 11,670 · 64.3% · +0.139 (+.13/+.14) · 42% |
| C moved-day only | 3,693 · 64.4% · +0.034 (+.03/+.04) · 4% | 4,993 · 64.5% · +0.046 (+.08/+.02) · 6% |
| D neither | 2,397 · 62.0% · −0.002 (+.02/−.02) · 0% | 5,177 · 58.9% · −0.027 (−.06/−.00) · −4% |

41% of level trades (34% of VWAP trades) carry two-thirds (over half) of
the R. Tier D is one trade in nine and earns nothing.

## 3. Consistent gradients that fall short of the rule (reference)

- **Stop vs recent range (`stop_atr`)**: stop <1× median 1m range of the
  prior 20 bars: +0.20/+0.18 net; 1–2×: +0.08/+0.06; 2–3×: +0.05/0.00;
  3×+: +0.03/−0.01. Monotone in both books and both halves; 3×+ bucket
  too thin for the rule. This is S34's stop-width decay in vol-normalised
  units — the form that would port to gold without re-deriving 30pt.
- **Cross-book agreement (`agree`)**: when the OTHER NQ book already holds
  a same-direction position more than 5pt away (outside the G3 zone),
  this entry runs **−0.070 / −0.071 net**, negative in all four
  half-cells (levels −0.05/−0.08, VWAP −0.02/−0.10). n = 552 + 455, under
  the 400/half bar, so WATCH not CUT. Same-direction inside 5pt (what G3
  already bans): +0.10 / +0.04. Opposite-direction open: +0.20 / +0.19 —
  the best cell in the feature. Post-hoc: skipping the >5pt same-direction
  entries removes ~1,000 trades worth −72R and lowers same-direction
  stacking for free.
- **Wait to fill**: fills ≤2 min after the signal are the weakest wait
  bucket on levels (+0.12 vs +0.15–0.18 for 3–45 min); on VWAP the 46+
  min bucket is weakest (+0.06). Signs differ across books → NULL.
  Mechanically the ≤2-min fill is the no-displacement retest, so this is
  `excur` again.
- **First trade of the day**: weakest `day_r` bucket in both books
  (+0.07 / +0.11 net); replicates S21/S29. Everything after it is flat.
- **Hour (net)**: NY 09–15 every hour +0.12 to +0.22 on both books;
  02:00, 22:00, 23:00 on levels are +0.00 to +0.02 net (S17's two dead
  hours, now with the third); every VWAP hour stays ≥+0.04.

## 4. What does NOT sort (NULL, both books)

Signal-candle body/range, signal-candle volume vs the prior 20 bars,
distance to the nearest other static level (<10 / 10–25 / 25–50 / 50+
pt), distance to the nearest VWAP band, a level sitting between entry
and target, prior-day trend vs range shape × direction, cumulative day
P&L, level family, VWAP band. The classic "confluence" idea — several
levels lining up — has now been tested three ways (round-1 `conf`,
`near_stat`, `room`) and does not move WR or EV. One implication for the
live wiring: nothing about the candle that makes the signal matters
beyond the close being ≥3pt through; what matters is what price does
AFTER it.

## 5. Recommendations

Ordered by how ready each is. None is adopted here; each needs the
in-engine run (a skipped or resized trade frees the book, so post-hoc
numbers move — S34 saw +41R from that alone).

1. **G3b — widen first-in-wins to any distance.** Skip a same-direction
   entry while any other NQ book holds a same-direction position,
   regardless of price gap. Receipt-backed on both measured books
   (−0.07 net in all four half-cells), removes ~1,000 trades that lose
   money, and lowers the G6 same-direction stack. Cheapest rail to add;
   test in-engine first because n is under the bar.
2. **Conviction sizing, not a filter.** Every conditional layer so far
   was tried as a binary skip and died (S15, S16, S20, S21, S29). This
   audit gives a two-feature sorter that holds in both books and both
   halves. The tier-A cells earn ~+0.20R at ~67% WR; tier D earns 0.
   Proposal to test: full risk on tier A, half on B/C, quarter (or skip)
   on D. Sizing by conviction was never tested; it is the one layer that
   can raise R/day without subtracting trades. Post-hoc estimate for the
   filter version (arm the limit only after a ≥1R run): per-trade EV
   +0.14 → +0.19 on levels, +0.12 → +0.17 on VWAP, but total R falls
   4–3% because the dropped tiers are still slightly positive — which is
   why sizing, not skipping, is the shape.
3. **Arm-after-displacement as an executor rule.** The mechanical form of
   `excur`: the retest limit goes live only once price has traded ≥X×stop
   past the level (X swept 0.5 / 1.0). Separate from (2) because it
   changes pending occupancy (a resting order is replaced by newer own-book
   signals). Its clean win is the VWAP <0.5R cell — negative both halves.
4. **Vol-normalised stop cap.** Sweep stop ≤ {1.5, 2, 2.5}× median 1m
   range of the prior 20 bars, in-engine, against the flat 30pt. The
   decay is monotone in normalised units; a ratio cap tracks regime and
   ports to gold (S34 flagged the GC equivalent as "to be certified").
5. **Session-progress dial.** Half risk while session range < 0.25×
   prior-day range. Overlaps the hour ladder; test it as a sizing knob
   alongside (2), not as a skip.
6. **Optional trim, still optional:** 02:00 / 22:00 / 23:00 on the level
   book are net ≈0 (S17 saw two of the three). Not a rule; ~3% of trades.

Things to stop spending looks on: candle shape, candle volume, level
stacking, distance-to-level, prior-day shape. Three rounds and this one
say the same thing.

## 6. Caveats

- Post-hoc chronological, no re-simulation; the in-engine run is the
  receipt for any of §5.
- `agree` reads the other book's realised hold to know it is open at
  the signal minute — that is knowable live (the position is open), but
  the VWAP dump here is pre-dedupe, so its same_dir_le5 cell includes
  trades the live G3 already skips.
- `excur` excludes the fill bar entirely (its intrabar order is
  unknowable), which is the conservative side.
- 14 × 2 cells screened; two features survived at 3–5× the WATCH bar
  in every half, and the same two on both books. Still one audit.
