---
date: 2026-08-07 (rev b — post code-audit)
kind: ranked comparison — every baselined strategy, both traders
script: scripts/baseline_comparison.py
data: baseline-comparison.csv
exit: all scored on the IDENTICAL locked convention (EXIT-CONVENTION-LOCKED.md)
---

# Every baselined strategy, ranked

All rows use the **same exit**: target 2R, break-even at 1R, no trailing, stop fills first on a
same-bar conflict, 16:00 ET cap, costs reported separately at $25/round-turn. The **same
09:45–10:15 ET window** (except `zxck-10am-keyopen`, whose level *is* the 10:00 open so it cannot
start earlier). So the numbers are directly comparable.

> ### ⚠️ Rev b — two code defects were found and fixed. Every number below moved.
> An adversarial audit of the four baseline scripts found:
> 1. **`ash_raw_baseline.py`: the liquidity-sweep gate tested price *position*, not *crossing*.**
>    A level already breached before 09:45 registered a sweep on bar 0, which also collapsed the
>    MSS lookback to a single bar. **30 of the shipped 37 trades had `s == 0`; on 25 of 37 price
>    was already beyond the level before the window opened.** Card conditions #2 and #3 did not
>    bind on most of the sample. **n 37 → 24.**
> 2. **Same-bar fill-and-stop**: a minute that filled the entry *and* traded through the stop was
>    carried forward as a live trade. Present in `zxck_keyopen_baseline.py` (**24 of 146 fill
>    bars, 3 trades mis-scored, −5.0R**), already fixed earlier in the wick-ce and ifvg/cisd
>    harnesses, and **measured at 0 of 24 on `ash-unicorn-sb`** — it does not bind there, because
>    the FVG-edge entry and the order-block stop are rarely inside one minute of each other.
>
> Both are **bug fixes, not spec changes**: the card always said "liquidity sweep", and A8/R11
> always said stop-first. The code now does what the cards said.

| # | card | n | win/BE/loss | avg R | cost | **expectancy** | total | maxDD | t | effect | effect net |
|---|---|---|---|---|---|---|---|---|---|---|---|
| — | *`ash-unicorn-sb` (matched span)* | *19* | *52.6/26.3/21.1* | *+0.842* | *0.058* | *+0.784* | *+16.0R* | *1.0R* | *+2.819* | *+0.647* | *+0.602* |
| **1** | **`ash-unicorn-sb`** (its baseline) | **24** | **50.0/20.8/29.2** | +0.708 | 0.054 | **+0.655** | **+17.0R** | **3.0R** | **+2.539** | **+0.518** | **+0.480** |
| 2 | `zxck-cisd` | 40 | 22.5/22.5/45.0 | +0.068 | 0.024 | **+0.044** | +2.7R | 4.5R | +0.351 | +0.055 | +0.036 |
| 3 | `zxck-10am-keyopen` | 115 | 22.6/24.3/53.0 | −0.078 | 0.083 | **−0.162** | −9.0R | 16.0R | −0.699 | −0.065 | −0.135 |
| 4 | `zxck-ifvg-50` | 186 | 19.9/3.8/76.3 | −0.366 | **0.250** | **−0.616** | **−68.0R** | 68.0R | **−4.165** | −0.305 | −0.514 |
| 5 | `zxck-wick-ce` | 38 | 13.2/2.6/84.2 | −0.579 | 0.166 | **−0.745** | −22.0R | 21.0R | **−3.464** | −0.562 | −0.710 |
| — | `zxck-gap-fill-edge` | **12** | — | — | — | **UNTESTABLE** | — | — | — | — | — |

**Reference points:** random-walk null for this exit = **25 / 25 / 50**.
Deflation bar at N = 293 trials = **+0.6978**.
`effect = t/√n` on gross R; `effect net` subtracts each trade's own cost first.

---

## The answer: `ash-unicorn-sb`, and it is not close

It is the **only** strategy with a positive expectancy that is not statistically zero. Second
place (`zxck-cisd`) has **t = +0.351** — indistinguishable from nothing — and its outcome mix
*is* the null (22.5/22.5/45.0 against 25/25/50).

**It still does not clear the bar.** Effect **+0.518** gross, **+0.480** net, against **+0.6978**.
About **three quarters** of the bar gross, **69%** net.

### What the sweep fix did to it

| | before the fix | after |
|---|---|---|
| n | 37 | **24** |
| win / BE / loss | 15 / 10 / 12 | **12 / 5 / 7** |
| win rate | 40.5% | **50.0%** |
| avg R | +0.486 | **+0.708** |
| total | +18.0R | **+17.0R** |
| max DD | 3.0R | **3.0R** |
| effect | +0.367 | **+0.518** |

The change is **purely subtractive and verified so**: the 24 survivors are a strict subset of the
old 37, **no new trade appeared, and not one surviving trade's R changed**. The 13 removed trades
were **3 wins / 5 BE / 5 losses, net +1.0R** — i.e. the discarded events were, as a group,
approximately the null, and essentially all of the profit was already coming from the trades that
genuinely swept.

**So the per-trade numbers went up while the sample went down.** That is what it looks like when a
gate that was not binding starts binding. **This is not a better result — it is the same result on
a smaller, cleaner sample**, and the smaller sample is *further* from the ~49 trades the power
calculation asks for, not closer.

### On the matched-span row — read it, do not use it

Restricting `ash-unicorn-sb` to the zxck cards' span (2025-06-01 →) gives a *better* number:
**+0.784R, effect +0.647**. **That row is shown for comparison fairness only. It is not the
card's baseline.** Adopting it because it flatters the result would be exactly the selection this
programme exists to catch — and at **n = 19** it is thinner than the sample it is meant to
validate.

---

## What the losers actually tell us

The three negative cards fail for **three different and identifiable reasons**, which is more
useful than the fact that they lose.

### `zxck-wick-ce` (−0.745R) — the stop sits where price just was
Entry is the wick's **midpoint**; the stop is its **tip**. Risk is half the wick every time, and
the stop is in territory price traversed moments earlier. 84% losses against a 50% null. It is
worse than a coin flip because the geometry works against it.

### `zxck-ifvg-50` (−0.616R) — his 5-point stop is inside single-bar noise
| NQ 1-min bar range, 09:45–10:15 | |
|---|---|
| p25 | 14.2 pt |
| **median** | **21.0 pt** |
| p90 | 42.5 pt |

**A fixed 5pt stop is smaller than 99% of individual 1-minute bars in this window**, and it puts
**a quarter of every R into costs** before the market moves. t = −4.165 on n=186 — it loses
reliably, not by chance. Net of costs its effect is **−0.514**, the second-worst in the set.

This is the most transferable finding here: **his tight-stop numbers do not survive contact with
NQ's 09:45–10:15 volatility.** It says nothing about the concept on a timeframe or instrument
where 5 points is not noise — he names neither, and that gap is on the card.

### `zxck-10am-keyopen` (−0.162R) — it is simply the null
22.6/24.3/53.0 against 25/25/50. The setup selects *when* to be in the market, not *which way*.
The same-bar fix cost it 5.0R across the full 146-trade book and moved the decidable subset from
−0.127R to −0.162R.

---

## Honest caveats on the ranking

1. **`ash-unicorn-sb` has never been tested as taught.** Its ES leading trigger — a declared
   entry component — is unimplemented, and the ES data was declined. Every number on it is the
   strategy *minus* a gate he requires.
2. **Three of the five losers carry assumptions that are ours**, tagged on their cards: the
   `ifvg-50` bias gate (Brake's), the `cisd` timeframe (ours by selection among his three), the
   `wick-ce` liquidity side (unresolved by instruction), and the 09:45–10:15 window itself (ours
   on every zxck card).
3. **Sample sizes are not comparable.** n ranges 12 → 186. `zxck-ifvg-50`'s −0.616R at n=186 is a
   far more secure negative than `zxck-cisd`'s +0.044R at n=40 is a positive — and the winner is
   now the **second-thinnest** book in the table.
4. **Every one of these is an arm in the ledger**, and each one raises the bar the winner has to
   clear. Five baselines were spent to confirm that four of them lose.
5. **The audit is the reason to trust the ranking, and the reason to distrust its precision.**
   Two defects were live in shipped numbers. Both were found by reading code against cards, not
   by the results looking wrong — the pre-fix `ash-unicorn-sb` looked *fine*.

---

## The standing conclusion

**One candidate is plausible and unconfirmed. Everything else is retired, negative, or untestable.**

`ash-unicorn-sb` at effect +0.518 needs either a materially larger effect — nothing in this
programme provides one, and the order-flow hypotheses failed out-of-sample on n=115 — or
**forward accumulation**, which raises t without raising N. That is the only cheap route left,
and the pre-registered forward protocol's first eligible date is **2026-08-08**.

The sweep fix makes that route **longer**: at 24 trades over 16.3 months the card runs at ~1.5
trades/month, so reaching n≈49 is roughly **17 more months**, not the ~9 estimated at n=37.
