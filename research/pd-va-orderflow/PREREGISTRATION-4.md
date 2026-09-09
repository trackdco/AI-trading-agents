# PRE-REGISTRATION 4 — the video's order-flow entry, tested on the footprint tape

**Written 2026-09-09, before the test engine exists.** The daily-bias claim has already failed
(`EXTRACTED-RULES.md` §11). This tests the remaining half: does the order-flow confirmation at the
level — absorption of the opposing side, then aggression of the trade side with an imbalance, then
an inversion close — add anything over simply trading the level.

## 1. Data

- Footprint: NQ front month, per-minute per-price buyer-/seller-aggressor volume, 2025-06-01 →
  2026-07-19 (`data/reference/cvd/footprint_*.parquet`, 13 months, ~285 cash sessions).
- Bars: the repository's raw NQ 1-minute tape for the same window (unadjusted, so footprint prices
  and bar prices are the same price space). Exits are evaluated on 1-minute highs/lows.
- No fit/test split is possible on 13 months; this is **one measurement with its readings fixed
  here**, reported as the minimum across readings. The user has seen this period's price action
  through the bot work; none of these setups has been looked at.

## 2. Levels and bias (mechanical)

- Previous cash session (09:30–15:59 ET) volume profile from the **footprint's own traded volume per
  price** (the video's tool does the same): POC = modal price, value area = 70% built outward from
  POC → VAH, VAL. Overnight profile (18:00 → 09:29 ET of the trading day) the same way → ON-VAH,
  ON-POC, ON-VAL.
- Bias from the 09:30 one-minute bar's open: above VAH bullish, below VAL bearish, inside neutral.
- Setups: bullish → long at PD VAH; bearish → short at PD VAL; neutral → short at PD VAH and long at
  PD VAL. The level must be approached from the trade's side (a long at VAH requires price to have
  been above VAH earlier in the session).
- Entries 09:31 → 15:30 ET; everything flat at the 15:59 close. One position at a time. At most two
  attempts per level per session.

## 3. The order-flow sequence (long case; short is the mirror)

Let T be the "big cell" threshold: the 98th percentile of single (minute, price, side) cell volumes
over the previous five sessions' RTH minutes (**reading T-a**); the 95th percentile (**reading T-b**).

1. **Tap** — a 1-minute bar with low ≤ VAH ≤ high, approached from above.
2. **Absorption** — in the tap bar or the following four bars: a bar whose lower wick (prices below
   min(open, close)) contains at least one seller-aggressor cell ≥ T, and whose close ≥ VAH (no
   follow-through below the level). The absorbed cluster = those cells; its top = the inversion
   level; its bar's low = the stop reference.
3. **Aggression with imbalance** — within the next three bars: a bar closing up whose body contains
   a buyer-aggressor cell ≥ T and at least one **buy imbalance**: at a body price p, buyer volume at
   p ≥ 3 × seller volume at p − 0.25 (with seller volume there > 0, or buyer volume at p ≥ T if it
   is 0). The imbalance price = the highest such p.
4. **Inversion** — that bar's close > the top of the absorbed cluster.

Entry readings, both run: **E-market** at the next bar's open + 0.5 pt; **E-limit** at the
imbalance price, filled if a later bar (within ten) trades to it, else no trade.

Stop: one tick below the lowest low from the absorption bar through the aggression bar.
Target readings, both run: **X-on** the first overnight-profile level beyond entry in the trade
direction that is at least 1R away (ON-VAL, ON-POC, ON-VAH in order), all out; **X-2R** a fixed 2R.
Both: time exit at the 15:59 close. If stop and target are both touched in one bar, the stop wins.

Fork set: T {a, b} × E {market, limit} × X {on, 2R} = **8 readings**. All run. Verdict = minimum.

## 4. The baseline the confirmation must beat

At every first tap of a level that produces a sequence-eligible situation, the **unfiltered
trade**: enter at the tap bar's close + 0.5 pt, stop one tick beyond the tap bar's extreme, the same
targets and time exit. Same sessions, same levels, no order flow. If the confirmed trades do not
beat this on mean net $ per trade, the order flow is decoration.

## 5. Costs and accounting

One NQ contract, $20/pt. Slippage 0.5 pt on every market fill (entries, stops, time exits); none on
limit fills and target fills. Commission $2.50 per side. Net $ and R (= net $ / stop $) per trade.

## 6. What counts

Reported: n, win rate, mean net $ and R, PF, session-block bootstrap LB95 (10,000, seed 20260909),
max drawdown, per-bias split, and the baseline. **"Order flow adds" only if, in all eight readings,
mean net $ > 0 with LB95 > 0 and mean net $ exceeds the baseline's.** Anything less: not
demonstrated. No re-cut of the sequence definitions after the run.

Out of scope: gamma levels (no data); ICT entries; partial exits (all-out, disclosed).
