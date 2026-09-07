# RESULT-2 — NQ-bot, the 30-point cap removed (PREREGISTRATION-2.md)

**Status: holdout-2 READ 2026-09-07 — VERDICT: ABORT under the pre-registered rules (no pass for the cap-free family; the cap question is closed on this bot). One read; this pre-registration is finished.**

## 0. Identity

| item | value |
|---|---|
| pre-registration | `PREREGISTRATION-2.md`, blob `8427b725…`, commit `66aaeb93` — written before any holdout-2 data was assembled |
| change under test | the 30-point maximum-stop cap removed (`--cap-lifted`), on the three live cells of the pass-marked family (`RESULT.md` §B) |
| verdict rule | minimum across V2-1 (10pt floor, gate removed, RTH), V2-2 (10pt floor, gate kept, RTH), V2-3 (2×ATR14, gate removed, RTH); mean > 0 and session-block bootstrap LB > 0 at **97.5%** in every cell; seed 20260907 |
| driver | `retest_backtest.py` (fast paths, level recording on), `run_holdout2.sh` = §5 as code; execution model = the bot's own close-based evaluation (`RESULT.md` §C.1) |

## A. Holdout-2 data — provenance and integrity, recorded before the read

| item | value |
|---|---|
| source | the repository's own raw Databento files, delivered unedited with Databento's manifests: `data/reference/nq_2017_2019_raw/glbx-mdp3-20160902-20200101.ohlcv-1m.csv.zst` (job GLBX-20260903-VHT7FR9HD9) and `nq_2020_2022_raw/glbx-mdp3-20200101-20230101.ohlcv-1m.csv.zst` (job GLBX-20260903-MEGV83QD59); GLBX.MDP3, ohlcv-1m, `NQ.FUT` parent symbology (every contract). Pulled by the user's other research programme on 2026-09-03 for its own 2020–22 holdout; **never run by, or on behalf of, this bot** |
| construction | unadjusted NQ front month, roll at the start of the Monday-of-expiry-week session (`build_nq_series.py --roll monday_of_expiry_week`), contract codes resolved decade-aware; fourteen contracts NQU8 → NQZ1 in clean quarterly sequence; 1,109,754 bars 2018-07-31 22:00 UTC → 2021-09-30 |
| window | engine starts cold on 2018-08-01; verdict counts entries 2018-09-01 → 2021-08-31 (three years; includes the 2020 crash) |
| sessions | 799 trading days 2018-08-01 → 2021-09-01, median 1,365 one-minute bars per day, six days under 1,000 (holidays / half days), no gap longer than a weekend |
| overlap check | September 2021, 29,749 minutes shared with the bot's own series: prices a constant offset per contract (bot − tape +2,389.25 during NQU1, sd 0.01; +2,396.51 during NQZ1, sd 0.20 — the bot's roll adjustment, as in `RESULT.md` §0); volumes identical on 94.0% of minutes, the rest differing by a median 23 contracts (vendor revisions and the roll week). Same instrument. |
| union | the tape plus the bot's checked-in files, prepared by the bot's own `prepare_historical_data.py` (2,314,536 bars, HTF rebuilt); the bot's bars kept where both exist, none of which the runs reach (they end 2021-08-31) |
| roll-convention note | the other programme's own 2020–22 series rolled by session-day volume, one to two sessions earlier on some quarters (its `roll_days.json`); this test uses the convention pre-registered in `PREREGISTRATION-2.md` §2, consistently |
| kill switch | armed from the cold start, as the bot's backtests are; a trip is reported as §2 requires |
| reads | one, covering the three cells, the three capped controls, the untouched control, the 2× slippage stress and the intrabar counterfactual (`run_holdout2.sh`) |

## B. Holdout-2 — read once, 2026-09-07 (runs 06:08–07:45 UTC)

### B.1 Verdict — PREREGISTRATION-2.md §4: **ABORT, no verdict read**

Entries 2018-09-01 → 2021-08-31, cold start 2018-08-01, bootstrap one-sided 97.5% (the table's
column is labelled LB95 by the tool; the level used is 0.025, seed 20260907).

| config | n | WR% | PF | net $ | mean $/tr | boot LB95 | maxDD $ | RTH% | mean stop | months + | mean>0 | LB>0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V2-1_C1a_C3a | 3253 | 56.9 | 1.166 | +17,223 | +5.29 | +1.91 | 3,727 | 99.7 | 17.17 | 24/36 | yes | yes |
| V2-2_C1a_C3b | 1078 | 54.36 | 1.242 | +9,648 | +8.95 | +1.68 | 2,018 | 99.5 | 12.82 | 23/34 | yes | yes |
| V2-3_C1b_C3a | 56 | 46.43 | 0.694 | -444 | -7.93 | -26.25 | 656 | 98.2 | 12.74 | 0/2 | NO | NO |
| untouched (control, not a candidate) | 848 | 43.75 | 0.961 | -1,112 | -1.31 | -7.97 | 2,917 | 59.9 | 8.62 | 10/20 | NO | NO |

| config | mean $/tr (1x) | mean $/tr (2x slippage) | sign flip |
|---|---|---|---|
| V2-1_C1a_C3a | 5.295 | -0.946 | YES |
| V2-2_C1a_C3b | 8.95 | -5.554 | YES |
| V2-3_C1b_C3a | -7.931 | empty (0 trades) | n/a |

**VERDICT:** ABORT — no verdict read: V2-1_C1a_C3a: sign flips under 2x slippage; V2-2_C1a_C3b: sign flips under 2x slippage; V2-3_C1b_C3a: n=56 < 300

Two abort conditions fired, each sufficient on its own:
1. **V2-3 (2×ATR14, cap-free) has 56 holdout trades.** The bot's cumulative $1,000 kill switch
   tripped in the autumn of 2018, on the 101st trade of the cold start (−$1,065.52), and the bot
   never traded again. Its capped control tripped on the identical trade with the identical
   number — the cap never bound in those 101 trades — so this is the 2×ATR reading failing the
   cold start, not the cap.
2. **The mean flips negative under 2× slippage in V2-1 and V2-2** (+5.29 → −0.95; +8.95 → −5.55),
   both of those stress runs also tripping the kill switch (at 620 and 186 trades).

**Consequence:** the cap-free family cannot pass; the 30-point cap stays; the cap question is
closed on this bot. The pass-marked family of `RESULT.md` §B stands as it is. No third family
without a new document and data none of this has touched — and there is no such bar data left in
the repository.

### B.2 The controls — the passed configuration meets 2018–2021

| config | n | WR% | PF | net $ | mean $/tr | boot LB95 | maxDD $ | RTH% | mean stop | months + | mean>0 | LB>0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| capped_C1a_C3a | 3064 | 55.45 | 1.181 | +16,437 | +5.37 | +2.08 | 3,572 | 99.8 | 14.25 | 23/36 | yes | yes |
| capped_C1a_C3b | 1063 | 54.0 | 1.186 | +7,247 | +6.82 | -0.14 | 2,018 | 99.6 | 12.36 | 23/34 | yes | NO |
| capped_C1b_C3a | 56 | 46.43 | 0.694 | -444 | -7.93 | -26.25 | 656 | 98.2 | 12.74 | 0/2 | NO | NO |
| untouched (control, not a candidate) | 848 | 43.75 | 0.961 | -1,112 | -1.31 | -7.97 | 2,917 | 59.9 | 8.62 | 10/20 | NO | NO |

The passed 10-point cells hold up on three years before their own history, the 2020 crash
included: +$5.37 and +$6.82 per trade, profit factors 1.18–1.19, drawdowns $2,000–3,600. Roughly
half the development rate and a quarter of last year's. The gate-kept cell's lower bound at 97.5%
is −$0.14 — a coin's width from zero. Cap-free and capped 10-point cells land within a dollar of
each other (+5.29 vs +5.37; +8.95 vs +6.82): **the cap was never the lever**, and the large
cap-free gains on 2025–26 were a property of that year's volatility. The untouched bot loses money
here (−$1.31 per trade) and shut itself down in 2019.

### B.3 The kill switch, and what the tripped cells look like without it (§2, reported alongside)

| config | n | WR% | PF | net $ | mean $/tr | boot LB95 | maxDD $ | RTH% | mean stop | months + | mean>0 | LB>0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V2-3_capfree_noKS | 3117 | 62.53 | 1.261 | +26,370 | +8.46 | +4.54 | 2,825 | 99.7 | 25.57 | 24/36 | yes | yes |
| capped_C1b_C3a_noKS | 2301 | 59.67 | 1.191 | +11,481 | +4.99 | +1.55 | 2,662 | 99.8 | 17.9 | 22/36 | yes | yes |
| stress2x_V2-1_noKS | 3250 | 52.12 | 1.03 | +3,331 | +1.02 | -2.37 | 8,267 | 99.8 | 17.06 | 17/36 | yes | NO |
| untouched_noKS | 2342 | 44.75 | 0.953 | -3,417 | -1.46 | -5.35 | 9,316 | 59.4 | 8.46 | 19/36 | NO | NO |

With the switch disabled, the 2×ATR cap-free reading earns +$8.46 per trade on 3,117 trades
(lower bound +$4.54, drawdown $2,825, mean stop 25.6 pt) — the best mean of any cell on this
window. Its first 101 trades lost $1,065; everything after was profitable. That is the bot as
shipped: a cumulative $1,000 stop measured from process start, which a cold start in a bad month
converts into a permanent halt. The pre-registration counted it, so the abort stands; the number is
reported so the reader can see what it cost. The 2× slippage variant of V2-1 run to completion is
+$1.02 per trade (lower bound −$2.37): no sign flip, no edge either — **in 2018–2021 the margin per
trade is of the order of the slippage assumption**, which is the honest content of abort
condition 2.

### B.4 Stress — 2× slippage (as run, kill switch on)

| config | n | WR% | PF | net $ | mean $/tr | boot LB95 | maxDD $ | RTH% | mean stop | months + | mean>0 | LB>0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V2-1_C1a_C3a | 571 | 49.91 | 0.965 | -540 | -0.95 | -6.30 | 2,537 | 99.6 | 12.78 | 4/8 | NO | NO |
| V2-2_C1a_C3b | 185 | 45.41 | 0.844 | -1,028 | -5.55 | -18.32 | 1,415 | 99.5 | 11.19 | 9/16 | NO | NO |
| V2-3_C1b_C3a | 0  | | | | | | | | | | | |

### B.5 Disclosed counterfactual — resting-order stops on 1-minute bars

| config | n | WR% | PF | net $ | mean $/tr | boot LB95 | maxDD $ | RTH% | mean stop | months + | mean>0 | LB>0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V2-1 | 3680 | 45.6 | 0.618 | -40,924 | -11.12 | -13.36 | 41,183 | 99.7 | 17.01 | 3/36 | NO | NO |
| V2-2 | 1195 | 41.0 | 0.655 | -12,505 | -10.46 | -14.55 | 13,575 | 99.5 | 13.08 | 6/34 | NO | NO |
| V2-3 | 3562 | 53.51 | 0.704 | -32,299 | -9.07 | -11.68 | 32,463 | 99.7 | 25.78 | 5/36 | NO | NO |

Same shape as on the development window (`RESULT.md` §C.1): every cell loses about $9–11 per trade
with resting stops. The bot's parameters only work with close-evaluated exits.

### B.6 What this read establishes

- The three original changes are what make the bot tradeable: over 2018–2026, nine years of
  separate sealed runs, the passed 10-point configuration earned +$10.65 per trade on 9,824 trades
  (PF 1.29, worst drawdown $3,572, one losing year, 2019, of −$2,626) against the untouched bot's
  +$4.92 with double the drawdown and three losing years (`RESULT.md` §B, this file §B.2,
  assembled in the session log of 2026-09-07).
- The edge is regime-dependent: about $5 a trade in 2018–2021, $11 in 2021–2024, $19–23 in
  2025–26. In thin years it is decided by execution cost.
- Removing the cap does not help where it was not already helping. The 2×ATR reading is the
  best long-run cell and the most fragile at a cold start. Neither is a change to make on this
  evidence.
- The kill switch is a run-level artefact that makes every cold-started backtest of this bot
  path-dependent on its first weeks. A live deployment restarts the count with every process
  restart; that is a design question for whoever runs it, not a research finding.

### B.7 Seals

| output | sha256 |
|---|---|
| `HOLDOUT2_verdict.json` | `c11b860cb02a763f…` |
| `controls_capped.json` | `6e284769338d8251…` |
| `h2_V21_C1a_C3a_capfree.json` | `86f52242f3d61790…` |
| `h2_V22_C1a_C3b_capfree.json` | `bc28ced92d201841…` |
| `h2_V23_C1b_C3a_capfree.json` | `db869809daafbb0f…` |
| `h2_ctl_C1a_C3a_capped.json` | `a1f4fae6d147c45c…` |
| `h2_ctl_C1a_C3b_capped.json` | `dee211691896b98e…` |
| `h2_ctl_C1b_C3a_capped.json` | `8cbe2468f4be8911…` |
| `h2_intrabar_V21.json` | `1fe76f9e133ccfaf…` |
| `h2_intrabar_V22.json` | `8b8fc9d3af04f153…` |
| `h2_intrabar_V23.json` | `9db3ef661cc508f8…` |
| `h2_nokill_V23_C1b_C3a_capfree.json` | `c5e2a1061ba854b5…` |
| `h2_nokill_ctl_C1b_C3a_capped.json` | `6087faaee083586e…` |
| `h2_nokill_stress_V21.json` | `fe5f99db6b798cf0…` |
| `h2_nokill_untouched.json` | `be4e9a32452c8362…` |
| `h2_stress_V21.json` | `25715c1b6f868efb…` |
| `h2_stress_V22.json` | `74b83950f419c554…` |
| `h2_stress_V23.json` | `259c9f75e7fc7c74…` |
| `h2_untouched.json` | `c8580290f0534754…` |
| `intrabar_counterfactual.json` | `fb5fa6087f5f3aff…` |
| `stress_2x_slippage.json` | `a8d830e275d4c6b9…` |
| `variants_kill_switch_disabled.json` | `00fd44709814f7c0…` |

Outputs committed gzipped; seals refer to the uncompressed JSON. Analysis tables:
`HOLDOUT2_verdict.*`, `controls_capped.*`, `stress_2x_slippage.*`, `intrabar_counterfactual.*`,
`variants_kill_switch_disabled.*`.
