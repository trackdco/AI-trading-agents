# FINDINGS — Asia at half size: KILLED (2026-09-03)

His ask, after seeing Asia earn +0.07/trade against New York's +0.16. Tested as
a pure multiplier (0.5× on fills 18:00–03:00 ET), so occupancy is untouched and
the railed dumps are the truth. Rule: the conviction-sizing bar, unchanged —
ADOPT if drawdown-matched R/day improves ≥ +5% in BOTH halves. Run on flat and
armed, all three eras. Six chances to pass.

| era | book | IS lift | OOS lift | maxDD flat → half | verdict |
|---|---|---:|---:|---|---|
| 2017–19 | flat | +11.0% | −1.1% | −88.5 → −88.6 | FAIL |
| 2017–19 | armed | +0.4% | −4.0% | −55.4 → −57.1 | FAIL |
| 2020–22 | flat | −4.4% | −2.7% | −39.4 → −39.3 | FAIL |
| 2020–22 | armed | −2.1% | −0.4% | −30.1 → −29.2 | FAIL |
| 2023–26 | flat | −0.5% | −7.2% | −18.1 → −18.0 | FAIL |
| 2023–26 | armed | +6.9% | +0.2% | −14.0 → −12.9 | FAIL |

**Zero of six.** Nine of twelve half-cells are negative.

## Why it fails

Half-sizing Asia only pays if Asia carries a disproportionate share of the
*drawdown*. It does not. The max drawdown barely moves in any era (−18.1 → −18.0;
−39.4 → −39.3) because the deep days are New York days — 2022-11-29's −24.6R
was almost entirely NY-session. So the drawdown-match scale is ~1.00, the sizing
buys no extra room, and the trade is simply "give up half of Asia's +1R/day
for nothing." Raw R falls in every era: −459R on 2023–26 flat, −277R on
2020–22 flat.

Contrast conviction sizing, which passed: it downsized the trades that
*cluster into bad days*, so the drawdown shrank faster than the mean. Asia is
low-EV but low-variance — the wrong thing to shrink.

## What stands

Asia is weak but positive and does not hurt the tail. Trade it at full size,
or not at all — and "not at all" is a skip, which changes occupancy and would
need an engine run. Not requested; the size result makes it unlikely to pay.

Script: `scripts/asia_half_size.py`.
