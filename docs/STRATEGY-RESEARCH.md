# Strategy research

One run. The holdout was not used to change a rule, a cost, or the survival test.

## Data

Primary series: `data/reference/nq_1m_master.parquet`, NQ 1-minute bars, 2023-01-02 18:00 ET through 2026-07-15 19:59 ET, 1,251,240 bars. This is the repo's unspliced front-month series. No Databento key is present in this environment, and `yfinance` is not installed. A short Yahoo `NQ=F` print would be a different continuous contract, so it was not mixed in.

Order-flow delta, where used, comes from the committed minute footprints in `data/reference/cvd/` (side B is the buy aggressor). Those files cover June 2025 through July 2026 continuously. The sparse 2023/24 holdout months were left out of the delta test. Depth snapshots were not used: the archive stores the last book of the minute, which is future data at the minute label.

Splits, by entry time, America/New_York:

- Train: through 2024-06-30
- Validation: 2024-07-01 through 2025-06-30, also split at 2025-01-01
- Holdout: 2025-07-01 through 2026-07-15

## Costs and the 0.25R / 90% claim

MNQ round turn is $1.22 on TopstepX, which is 0.61 points. Slippage is one tick on entry and one tick on exit, 0.50 points. Total cost is 1.11 points per trade, taken on every result below. Lucid's commission card was not on the help pages read earlier, so the same cost is used there.

A random walk that aims for 0.25R before costs does not win 90% of the time, and it is not flat after costs. The break-even win rate is the win rate that nets zero once the stop and the target have both been worsened by the cost. The random-walk column is the probability of touching the target before the stop from the slipped entry, with no drift.

| intended target | stop | break-even win rate | random-walk win rate | random-walk net R |
|---|---:|---:|---:|---:|
| 0.25R | 8 pt | 91.1% | 82.5% | -0.108 |
| 0.25R | 16 pt | 85.5% | 81.2% | -0.054 |
| 0.25R | 40 pt | 82.2% | 80.5% | -0.021 |
| 0.50R | 8 pt | 75.9% | 68.8% | -0.107 |
| 0.50R | 16 pt | 71.3% | 67.7% | -0.054 |
| 0.50R | 40 pt | 68.5% | 67.1% | -0.022 |
| 1.00R | 8 pt | 56.9% | 51.6% | -0.107 |
| 1.00R | 16 pt | 53.5% | 50.8% | -0.054 |
| 1.00R | 40 pt | 51.4% | 50.3% | -0.021 |
| 2.00R | 8 pt | 38.0% | 34.4% | -0.107 |
| 2.00R | 16 pt | 35.6% | 33.9% | -0.054 |
| 2.00R | 40 pt | 34.3% | 33.5% | -0.021 |

At a 16-point stop, 0.25R breaks even near 86% wins, not 80%. A no-drift path wins about 81% and still loses about 0.05R a trade. A true 90% win rate at that stop would be about +0.06R after costs. The rest of this note asks whether any tested rule reaches that, out of sample.

## What was tested

31 bar strategies, chosen before the run: CRT on the closed 15-minute and 60-minute candle and on the first 1-minute reclaim inside the next 15-minute candle; 15- and 30-minute opening-range breaks and fades; VWAP extensions of 20 and 40 points, a VWAP pullback, prior-day and overnight highs and lows, gap fill and gap continuation, a 15-bar stretch fade, a volume-spike continuation and exhaustion, and the 09:30-10:00 drive taken at 10:00. Targets are 0.25R, 1R, or the structural opposite side where that side exists.

Fill model: signal on the closed bar, market at the next bar's open, one tick worse. If the stop and the target are both touched in a bar, the stop is first. A gap through the stop fills at the open. Positions are flat at 15:55 ET, which is inside both the Topstep 15:10 CT flatten and the Lucid 16:45 ET flatten. Stops closer than 2 points or wider than 200 are skipped. A 2-point stop is inside the cost, and those trades are left in so the damage is visible. One position at a time.

## Survival rule

Validation must have at least 100 trades, mean net R above zero, sign-flip p below 0.05, both validation halves positive, and a deflated-Sharpe probability of at least 0.95 given the number of variants. Benjamini-Hochberg at q=0.10 is applied to the validation p-values of the whole catalog. The holdout, touched once, must have at least 100 trades, mean net R above zero, and sign-flip p below 0.05. The sibling target on the same signal, if one was pre-registered, must not be worse than -0.02R on the holdout.

## Ranked results

Ranked by validation mean net R. Train is not the selection sample. Holdout is not the selection sample.

| strategy | train n | train mean R | train win | val n | val mean R | val win | val p | val DSR | hold n | hold mean R | hold win | hold p | hold max DD R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vwap20_rev_struct | 373 | -0.108 | 21.2% | 253 | 0.259 | 25.7% | 0.143 | 0.109 | 267 | 0.042 | 22.5% | 0.402 | 47.157 |
| orb15_break_100 | 384 | 0.022 | 51.8% | 238 | 0.078 | 55.0% | 0.092 | 0.205 | 233 | 0.007 | 51.9% | 0.445 | 19.565 |
| crt60_close_struct | 574 | -0.022 | 46.5% | 402 | 0.056 | 50.0% | 0.224 | 0.091 | 385 | 0.010 | 48.6% | 0.435 | 23.123 |
| orb30_break_025 | 377 | -0.035 | 76.9% | 216 | 0.029 | 81.5% | 0.168 | 0.138 | 182 | -0.044 | 74.2% | 0.906 | 10.594 |
| vwap20_rev_100 | 373 | -0.231 | 45.6% | 253 | 0.022 | 56.1% | 0.364 | 0.042 | 267 | -0.087 | 50.2% | 0.925 | 26.109 |
| on_break_025 | 292 | -0.013 | 75.0% | 111 | 0.014 | 79.3% | 0.369 | 0.044 | 91 | 0.003 | 76.9% | 0.480 | 4.828 |
| orb15_break_025 | 384 | -0.020 | 79.7% | 238 | 0.014 | 81.9% | 0.319 | 0.054 | 233 | 0.017 | 81.1% | 0.277 | 7.271 |
| open_drive_025 | 342 | -0.026 | 78.9% | 208 | 0.004 | 81.2% | 0.466 | 0.026 | 207 | -0.045 | 76.8% | 0.898 | 11.268 |
| gap_fill_struct | 289 | -0.063 | 47.8% | 171 | -0.012 | 50.3% | 0.560 | 0.013 | 161 | -0.002 | 49.7% | 0.506 | 21.699 |
| crt60_close_025 | 684 | -0.044 | 78.8% | 488 | -0.019 | 79.7% | 0.801 | 0.001 | 474 | -0.038 | 78.7% | 0.952 | 21.711 |
| pd_break_025 | 270 | -0.116 | 77.4% | 178 | -0.043 | 79.2% | 0.873 | 0.000 | 192 | -0.200 | 67.7% | 1.000 | 38.639 |
| vol_cont_100 | 1200 | -0.091 | 49.3% | 735 | -0.065 | 49.7% | 0.952 | 0.000 | 723 | -0.046 | 50.2% | 0.902 | 39.927 |
| crt15_close_100 | 2456 | -0.088 | 49.7% | 1559 | -0.071 | 49.3% | 0.996 | 0.000 | 1615 | -0.082 | 48.7% | 1.000 | 137.669 |
| crt15_close_025 | 3069 | -0.127 | 74.3% | 1973 | -0.081 | 77.2% | 1.000 | 0.000 | 2175 | -0.081 | 77.2% | 1.000 | 181.736 |
| vol_cont_025 | 1206 | -0.085 | 78.4% | 741 | -0.107 | 75.8% | 1.000 | 0.000 | 737 | -0.099 | 76.0% | 1.000 | 72.855 |
| crt15_close_struct | 2426 | -0.090 | 43.8% | 1563 | -0.119 | 42.0% | 1.000 | 0.000 | 1691 | -0.049 | 44.7% | 0.939 | 121.788 |
| gap_fill_025 | 289 | -0.063 | 76.5% | 176 | -0.123 | 71.6% | 0.999 | 0.000 | 169 | -0.140 | 69.8% | 0.999 | 26.224 |
| pd_fade_100 | 264 | -0.174 | 47.3% | 173 | -0.140 | 47.4% | 0.962 | 0.000 | 186 | -0.120 | 47.8% | 0.946 | 31.110 |
| vol_exh_025 | 658 | -0.134 | 74.9% | 437 | -0.150 | 72.8% | 1.000 | 0.000 | 463 | -0.090 | 76.9% | 1.000 | 42.178 |
| vwap_pb_100 | 258 | -0.194 | 46.9% | 159 | -0.194 | 44.7% | 0.994 | 0.000 | 170 | -0.194 | 44.7% | 0.994 | 36.485 |
| vwap20_rev_025 | 373 | -0.328 | 60.9% | 253 | -0.211 | 68.8% | 1.000 | 0.000 | 267 | -0.253 | 65.9% | 1.000 | 68.112 |
| vwap_pb_025 | 258 | -0.265 | 63.2% | 159 | -0.253 | 65.4% | 1.000 | 0.000 | 170 | -0.301 | 61.2% | 1.000 | 53.735 |
| on_fade_025 | 297 | -0.307 | 61.6% | 184 | -0.256 | 66.8% | 1.000 | 0.000 | 204 | -0.248 | 65.7% | 1.000 | 51.743 |
| gap_go_025 | 205 | -0.283 | 63.9% | 139 | -0.281 | 64.7% | 1.000 | 0.000 | 157 | -0.272 | 63.7% | 1.000 | 42.740 |
| pd_fade_025 | 264 | -0.282 | 62.9% | 173 | -0.300 | 61.3% | 1.000 | 0.000 | 186 | -0.237 | 66.1% | 1.000 | 47.341 |
| vwap40_rev_025 | 350 | -0.344 | 61.4% | 250 | -0.313 | 60.8% | 1.000 | 0.000 | 265 | -0.217 | 69.1% | 1.000 | 57.945 |
| crt15_intra_025 | 6557 | -0.374 | 51.9% | 4526 | -0.359 | 56.3% | 1.000 | 0.000 | 4607 | -0.316 | 59.0% | 1.000 | 1453.772 |
| orb15_fade_100 | 353 | -0.063 | 53.5% | 245 | -0.365 | 36.7% | 1.000 | 0.000 | 248 | -0.082 | 50.0% | 0.898 | 20.296 |
| orb15_fade_025 | 353 | -0.262 | 65.2% | 245 | -0.375 | 56.3% | 1.000 | 0.000 | 248 | -0.200 | 69.0% | 1.000 | 48.999 |
| stretch_100 | 3983 | -0.483 | 41.1% | 3180 | -0.468 | 39.0% | 1.000 | 0.000 | 3339 | -0.475 | 38.7% | 1.000 | 1591.506 |
| stretch_025 | 3983 | -0.678 | 26.4% | 3181 | -0.668 | 32.2% | 1.000 | 0.000 | 3339 | -0.670 | 31.4% | 1.000 | 2235.965 |

## Survivors

None. No variant passed the validation gates and the holdout gates together. No setup card was written. The empty slot in `config/setup_card.yaml` stays empty.

## CRT

CRT here means: a completed higher-timeframe candle sets the range; the next candle, or the first closed 1-minute bar inside that next window, trades outside one side and closes back inside; the entry is the next 1-minute open, stop beyond the sweep, target either 0.25R, 1R, or the other side of the range. The range candle is closed before the sweep is judged.

| CRT variant | val mean R | val win | hold mean R | hold win | hold n |
|---|---:|---:|---:|---:|---:|
| crt60_close_struct | 0.056 | 50.0% | 0.010 | 48.6% | 385 |
| crt60_close_025 | -0.019 | 79.7% | -0.038 | 78.7% | 474 |
| crt15_close_100 | -0.071 | 49.3% | -0.082 | 48.7% | 1615 |
| crt15_close_025 | -0.081 | 77.2% | -0.081 | 77.2% | 2175 |
| crt15_close_struct | -0.119 | 42.0% | -0.049 | 44.7% | 1691 |
| crt15_intra_025 | -0.359 | 56.3% | -0.316 | 59.0% | 4607 |

Resampling the holdout CRT trades into the prop lifecycle, sized so each trade risks the policy's dollar risk:

| book | firm | policy | EV | 95% CI |
|---|---|---|---:|---|
| crt15_close_025 | topstep 50000 | baseline | $-151 | $-154 to $-148 |
| crt15_close_025 | topstep 50000 | angus_025 | $-276 | $-279 to $-272 |
| crt15_close_025 | lucidflex 50000 | baseline | $-100 | $-100 to $-100 |
| crt15_close_025 | lucidflex 50000 | angus_025 | $-300 | $-300 to $-300 |
| crt15_intra_025 | topstep 50000 | baseline | $-58 | $-59 to $-57 |
| crt15_intra_025 | topstep 50000 | angus_025 | $-147 | $-147 to $-147 |
| crt15_intra_025 | lucidflex 50000 | baseline | $-100 | $-100 to $-100 |
| crt15_intra_025 | lucidflex 50000 | angus_025 | $-300 | $-300 to $-300 |
| crt60_close_025 | topstep 50000 | baseline | $-197 | $-200 to $-194 |
| crt60_close_025 | topstep 50000 | angus_025 | $-411 | $-417 to $-406 |
| crt60_close_025 | lucidflex 50000 | baseline | $-100 | $-100 to $-100 |
| crt60_close_025 | lucidflex 50000 | angus_025 | $-297 | $-299 to $-295 |

## Delta divergence

Separate from the catalog above, because the footprint only exists from June 2025. Selection sample is June-December 2025. Holdout is 2026. Side B minus side A. A 20-bar extreme with disagreeing minute delta is faded. Two variants, so a lone p-value near 0.05 is not a discovery.

| strategy | select n | select mean R | select win | hold n | hold mean R | hold win | hold p |
|---|---:|---:|---:|---:|---:|---:|---:|
| delta_div_025 | 1876 | -0.417 | 50.5% | 1860 | -0.374 | 55.9% | 1.000 |
| delta_div_100 | 1867 | -0.277 | 45.3% | 1853 | -0.202 | 47.3% | 1.000 |

## Prop-structure search

The question is whether the eval fee being small, and the payout being real, makes a no-skill stream of trades a positive-EV purchase. The search covers 576 policies: risk $150, $400 or $1,000; target 0.25R, 0.5R, 1R or 2R; 1, 2 or 4 trades a day; a daily loss stop at 2R or none; a daily profit stop at 2R or none; retire after the first payout or trade on until bust; one attempt or up to three. Topstep uses the published monthly fee and the $149 activation. LucidFlex uses an assumed $100 one-time fee, because the help centre describes a fee and does not print it. LucidPro is not in this search: the funded payout caps did not extract cleanly from the help page, and inventing them would overstate the firm.

Gross zero is a random walk at the intended payoff, then commission and slippage. Net zero is a two-point distribution whose expectancy is exactly zero after costs. Net +0.05R and +0.1R are the same, with that expectancy. Each published interval is from 1,500 fresh paths, not from the paths that picked the policy. The horizon is 100 eval days and 120 funded days. A path still open at the horizon keeps whatever cash it has taken and is otherwise worth zero. That censors long grinds.

Two policies were declared before the search and are not chosen by it.

- Baseline: risk $200 / 1R / 2/day / day-stop none / day-bank none / retire bust / attempts 1 / stop 16pt
- Angus 0.25R policy: risk $200 / 0.25R / 4/day / day-stop 2R / day-bank 2R / retire 1 / attempts 3 / stop 16pt

### Pre-declared policies at gross zero (no skill, costs on)

| firm | policy | EV | 95% CI |
|---|---|---:|---|
| lucidflex 100K | angus_025 | $-300 | $-300 to $-300 |
| lucidflex 150K | angus_025 | $-300 | $-300 to $-300 |
| lucidflex 50K | angus_025 | $-300 | $-300 to $-300 |
| topstep 100K | angus_025 | $-865 | $-874 to $-856 |
| topstep 150K | angus_025 | $-2,381 | $-2,398 to $-2,364 |
| topstep 50K | angus_025 | $-306 | $-310 to $-302 |
| lucidflex 100K | baseline | $-99 | $-100 to $-98 |
| lucidflex 150K | baseline | $-100 | $-100 to $-100 |
| lucidflex 50K | baseline | $-86 | $-91 to $-81 |
| topstep 100K | baseline | $-329 | $-335 to $-322 |
| topstep 150K | baseline | $-861 | $-871 to $-851 |
| topstep 50K | baseline | $-105 | $-112 to $-98 |

### Confirmation of the policy the search ranked first

Search rank used 200 paths. The numbers here are a new sample. LucidFlex fee in the EV is the assumed $100.

| firm | edge | policy | EV | 95% CI |
|---|---|---|---:|---|
| topstep 50K | gross 0 | risk $1000 / 1R / 1/day / day-stop 2R / day-bank none / retire bust / attempts 3 / stop 16pt | $116 | $61 to $171 |
| topstep 50K | net +0.00R | risk $1000 / 0.25R / 2/day / day-stop 2R / day-bank none / retire bust / attempts 3 / stop 16pt | $450 | $370 to $530 |
| topstep 50K | net +0.05R | risk $1000 / 0.25R / 4/day / day-stop none / day-bank none / retire bust / attempts 3 / stop 16pt | $4,263 | $3,883 to $4,643 |
| topstep 50K | net +0.10R | risk $1000 / 0.25R / 4/day / day-stop 2R / day-bank none / retire bust / attempts 3 / stop 16pt | $15,111 | $14,506 to $15,716 |
| topstep 100K | gross 0 | risk $1000 / 2R / 2/day / day-stop 2R / day-bank none / retire bust / attempts 1 / stop 16pt | $-3 | $-47 to $42 |
| topstep 100K | net +0.00R | risk $1000 / 0.5R / 4/day / day-stop 2R / day-bank none / retire bust / attempts 3 / stop 16pt | $351 | $227 to $475 |
| topstep 100K | net +0.05R | risk $1000 / 0.25R / 4/day / day-stop 2R / day-bank none / retire bust / attempts 3 / stop 16pt | $4,924 | $4,501 to $5,348 |
| topstep 100K | net +0.10R | risk $1000 / 0.25R / 4/day / day-stop 2R / day-bank 2R / retire bust / attempts 3 / stop 16pt | $23,396 | $22,563 to $24,230 |
| topstep 150K | gross 0 | risk $1000 / 2R / 2/day / day-stop 2R / day-bank none / retire bust / attempts 1 / stop 16pt | $44 | $-31 to $120 |
| topstep 150K | net +0.00R | risk $1000 / 2R / 4/day / day-stop 2R / day-bank 2R / retire bust / attempts 3 / stop 16pt | $447 | $285 to $609 |
| topstep 150K | net +0.05R | risk $1000 / 0.25R / 4/day / day-stop none / day-bank 2R / retire bust / attempts 3 / stop 16pt | $5,709 | $5,259 to $6,158 |
| topstep 150K | net +0.10R | risk $1000 / 0.25R / 4/day / day-stop none / day-bank 2R / retire bust / attempts 3 / stop 16pt | $26,625 | $25,679 to $27,571 |
| lucidflex 50K | gross 0 | risk $400 / 2R / 1/day / day-stop none / day-bank 2R / retire bust / attempts 3 / stop 16pt | $11 | $-25 to $47 |
| lucidflex 50K | net +0.00R | risk $400 / 1R / 2/day / day-stop none / day-bank 2R / retire bust / attempts 3 / stop 16pt | $141 | $92 to $189 |
| lucidflex 50K | net +0.05R | risk $1000 / 0.25R / 4/day / day-stop none / day-bank none / retire bust / attempts 3 / stop 16pt | $1,924 | $1,780 to $2,067 |
| lucidflex 50K | net +0.10R | risk $1000 / 0.25R / 4/day / day-stop 2R / day-bank none / retire bust / attempts 3 / stop 16pt | $4,967 | $4,794 to $5,139 |
| lucidflex 100K | gross 0 | risk $1000 / 2R / 1/day / day-stop 2R / day-bank none / retire bust / attempts 3 / stop 16pt | $57 | $2 to $112 |
| lucidflex 100K | net +0.00R | risk $400 / 2R / 4/day / day-stop 2R / day-bank none / retire bust / attempts 3 / stop 16pt | $220 | $160 to $280 |
| lucidflex 100K | net +0.05R | risk $1000 / 0.25R / 4/day / day-stop 2R / day-bank none / retire bust / attempts 3 / stop 16pt | $2,694 | $2,538 to $2,849 |
| lucidflex 100K | net +0.10R | risk $1000 / 0.25R / 4/day / day-stop none / day-bank none / retire bust / attempts 3 / stop 16pt | $6,086 | $5,917 to $6,255 |
| lucidflex 150K | gross 0 | risk $1000 / 2R / 1/day / day-stop 2R / day-bank 2R / retire bust / attempts 3 / stop 16pt | $143 | $81 to $205 |
| lucidflex 150K | net +0.00R | risk $1000 / 2R / 4/day / day-stop 2R / day-bank 2R / retire bust / attempts 3 / stop 16pt | $542 | $440 to $644 |
| lucidflex 150K | net +0.05R | risk $1000 / 0.25R / 4/day / day-stop none / day-bank none / retire bust / attempts 3 / stop 16pt | $3,079 | $2,931 to $3,228 |
| lucidflex 150K | net +0.10R | risk $1000 / 0.25R / 4/day / day-stop none / day-bank 2R / retire bust / attempts 3 / stop 16pt | $6,400 | $6,245 to $6,555 |

## Verdict: is zero edge +EV on these prop firms?

**No.**

A strategy with no market edge, after the published MNQ commission and one tick of slippage each side, is not a positive-EV purchase under either policy that was declared before the search. Every one of those intervals sits below zero. CRT's own holdout trades, resampled into the same accounts, are also below zero: the firm keeps the fee and the trade stream does not earn it back.

The search did find gross-zero policies whose fresh-sample interval sits above zero. They are the maximum of 576 policies, they bet $400 to $1,000 a trade, and they are a payout lottery: the mean is pulled up by the rare account that passes and withdraws, while a typical path loses the fee. That is not evidence that a no-skill entry rule has an edge. It is evidence that, after hunting through hundreds of bet sizes, the capped-fee structure can show a positive mean. The pre-declared policies, which were not hunted, do not.

Net zero, which already assumes the trader has clawed back commissions and slippage, is a different statement. Where that row is positive, it says the payout asymmetry can pay a trader who is exactly flat after costs. It does not say a coin-flip entry is flat after costs. The break-even table shows it is not.

Resets do not fix this. Up to three attempts are inside the search. Paying the fee again multiplies a negative attempt; it does not create the win rate the small target needs.

## What raw ticks would change

A tick tape would let a stop and a target be ordered inside the minute, instead of this model's stop-first rule. That helps the small-target variants if the target really prints before the stop, and it hurts them if the stop does. It would also let CRT be defined on a sweep of a few ticks rather than a whole 1-minute bar, and it would make absorption and stacked imbalance real rather than minute proxies. It would not remove the commission. Any 0.25R result that is only a point or two wide dies on $1.22 and a tick whether or not the tape is finer. The minute bars are enough to reject the claim that a no-drift 0.25R trade, or the CRT rules above, are a prop-firm edge.

## The prop-farm claim

These are the claims from @lndhmtapes (Kairos), tested on the rules in `config/prop_rules.yaml`. Nothing here places an order. Cross-account hedging is not tested. Lucid bans it, and so does the note he wrote himself.

### The live wording, next to Angus

Angus trades these accounts. On 3 Nov 2026 he said LucidFlex evals use a 50% consistency rule, that 40% may be the Pro rule or an older one, and that a funded LucidFlex account has no consistency rule, so a trader can take a large day first and then farm days of +$150. The help pages were fetched again the same day. The funded half of that matches the pages. The eval half does not. Pro is not the 40% rule either. The Pro evaluation page, <https://support.lucidtrading.com/en/articles/12890029-lucidpro-evaluation-account>, has no consistency column and says "Pass the evaluation in one trading day."

| question | Angus | live page |
|---|---|---|
| Eval consistency | 50% is the Flex rule. 40% may be Pro or older. | Evaluation account, <https://support.lucidtrading.com/en/articles/12945790-lucidflex-evaluation-account>: the 50K row is "40% (50% with add-on)" and the page says "Pass in as few as 3 days with 40% consistency, or 2 days with the 50% consistency add-on." Consistency page, <https://support.lucidtrading.com/en/articles/12945805-lucidflex-consistency-percentage>: "In LucidFlex evaluation accounts your Consistency Percentage must be 40% or less to be eligible to upgrade to a LucidFlex funded account. If you added the 50% consistency add-on at checkout, it must be 50% or less." Customization, <https://support.lucidtrading.com/en/articles/16226050-lucidflex-customization>: "40% (standard): your largest day must be 40% or less of your evaluation profit. Lowest price. 50% (add-on): your largest day can be up to 50%, so you can pass in as few as 2 days. Added at checkout for a small fee." |
| Funded / payout consistency | No consistency rule. A big day one, then +$150 days, is allowed. | Funded account, <https://support.lucidtrading.com/en/articles/12945795-lucidflex-funded-account>: "LucidFlex funded accounts have an optional Daily Loss Limit, no consistency rule and no payout buffer." And: "There is no Consistency Percentage on LucidFlex funded accounts." Payouts, <https://support.lucidtrading.com/en/articles/12945796-lucidflex-payouts>, page date 28 Jul 2026: "There are two requirements must be met in LucidFlex to qualify for a payout." The two are five days at the minimum daily profit ($150 on a 50K) and positive net profit in the cycle. The page does not add a consistency percentage. The 50K cap is "50% of Profit up to $2,000." |

The formula on the consistency page is "Largest Single Day Profit / Account Profit = Consistency Percentage." The same page says the requirement "applies only during the evaluation stage." The 50% add-on has an example cushion, not a formula: on a 50K the table shows $1,500 at 50% and a cushion of $1,560, and the 25K, 100K and 150K rows are the same 4% step. The page says the table is an example, "not a fixed dollar amount," and that the cushion is a percentage of the actual day. Two days of exactly $1,500 are already 50%, so they pass the add-on without that cushion. The simulator keeps that plain ratio. Both the 40% standard and the 50% add-on are in the recipe tables below. The standard is not changed to 50%.

### The earlier no-edge LucidFlex rows, at both percentages

These are the gross-zero books from the prop-structure search, rerun at 1,500 paths. Each pair uses one seed, so the only change is the eval percentage. The fee is the assumed $100. This is a fresh seed, not a revision of the earlier point estimates. On this seed the two columns match on every row: no path was passed by 50% and failed by 40%. A best day large enough to sit between those two lines did not decide a pass here. The pre-declared $200 stake was never going to. The 2R, $1,000 rows could have, and did not.

| book | rule | EV | 95% CI |
|---|---|---:|---|
| 50K baseline | 40% | $-91 | $-95 to $-87 |
| 50K baseline | 50% | $-91 | $-95 to $-87 |
| 50K angus 0.25R | 40% | $-300 | $-300 to $-300 |
| 50K angus 0.25R | 50% | $-300 | $-300 to $-300 |
| 100K baseline | 40% | $-100 | $-100 to $-99 |
| 100K baseline | 50% | $-100 | $-100 to $-99 |
| 100K angus 0.25R | 40% | $-300 | $-300 to $-300 |
| 100K angus 0.25R | 50% | $-300 | $-300 to $-300 |
| 150K baseline | 40% | $-100 | $-100 to $-100 |
| 150K baseline | 50% | $-100 | $-100 to $-100 |
| 150K angus 0.25R | 40% | $-300 | $-300 to $-300 |
| 150K angus 0.25R | 50% | $-300 | $-300 to $-300 |
| 50K searched gross-zero | 40% | $24 | $-11 to $59 |
| 50K searched gross-zero | 50% | $24 | $-11 to $59 |
| 100K searched gross-zero | 40% | $105 | $44 to $166 |
| 100K searched gross-zero | 50% | $105 | $44 to $166 |
| 150K searched gross-zero | 40% | $189 | $124 to $255 |
| 150K searched gross-zero | 50% | $189 | $124 to $255 |

### Reproducing +$250 to +$300 per attempt

His slideshow, not the farm recipe: one ±$500 trade a day, 50/50, no commission in the payoff, Topstep 50K. He reports a pass rate of about 25–28%, about $220 to get funded at $49 a month, 97% of funded accounts dead within a year, 60% of funded accounts paid before they die because Topstep pays from $125, an average payout of about $700, a median of $225, and a net of about +$300 per attempt. Apex at 80% off is the +$250. Apex is not in the rule file, so that half is not run.

The no-cost coin that takes the maximum payout, charges the $49 month and the $149 activation, and grades the floor from the close is the row that meets the descriptive statistics. Pass 26.7%. Of funded accounts, 57.9% are paid and 100.0% are dead by day 252. Median cash among funded accounts $225. Mean cash among funded accounts $687. Mean payouts among funded accounts 0.98. Fees per passed account $375, of which the activation is $149, so the subscription piece is $226. EV per eval purchase $83 ($61 to $106). The same paths, stated per funded account, are mean funded cash minus every eval fee spent to produce that account: $312. Those two are the same object. Per-purchase EV equals the pass rate times the per-funded net.

The table changes one assumption at a time, 2,500 paths, still a ±$500 coin with no commission unless the row says otherwise. "Per funded" is funded cash minus fees per passed account.

| assumption | pass | funded, paid | median cash if funded | mean cash if funded | fees per pass | EV per purchase | per funded |
|---|---:|---:|---:|---:|---:|---|---|
| published XFA, max payout, activation, no cost | 26.8% | 64.2% | $225 | $767 | $373 | $106 ($78 to $134) | $395 |
| no activation | 26.8% | 61.8% | $225 | $699 | $224 | $128 ($97 to $158) | $475 |
| trader keeps 100%, not 90% | 27.8% | 59.9% | $250 | $796 | $366 | $119 ($85 to $154) | $430 |
| $125 minimum payout | 29.0% | 61.2% | $112 | $208 | $357 | $-43 ($-51 to $-35) | $-149 |
| fixed $778 request, trader keeps $700 | 27.0% | 36.1% | $0 | $780 | $371 | $110 ($75 to $146) | $409 |
| 3 winning days, not 5 | 26.4% | 69.4% | $225 | $616 | $375 | $64 ($41 to $86) | $241 |
| no winning-day requirement | 27.5% | 77.0% | $225 | $486 | $373 | $31 ($18 to $45) | $113 |
| funded starts at $50,000, payout floor $0 | 27.3% | 65.4% | $1,800 | $1,336 | $369 | $264 ($233 to $295) | $967 |
| funded starts at $50,000, payout floor $50,000 | 26.1% | 64.4% | $1,800 | $1,190 | $378 | $212 ($186 to $238) | $812 |
| no trailing floor | 39.6% | 62.4% | $225 | $766 | $353 | $163 ($126 to $201) | $413 |
| $35 MNQ cost, max payout, intraday | 11.7% | 40.1% | $0 | $259 | $617 | $-42 ($-48 to $-35) | $-359 |

Per-purchase EV falls near +$250 to +$320 in: funded starts at $50,000, payout floor $0 at $264 ($233 to $295), median $1,800, pass 27.3%. That row does not also have his $225 median.

His descriptive statistics line up with the no-activation row, not with a +$300 purchase. That row, 2,500 paths: pass 26.8%, 61.8% of funded accounts paid, median $225, mean funded cash $699, fees per pass $224. Those are his 25–28%, about 60%, $225, about $700, and about $220. Its per-purchase EV is $128 ($97 to $158). Its per-funded net is $475.

The 4,000-path row that also charges the $149 activation has per-purchase EV $83 ($61 to $106) and a per-funded point of $312. Dividing that purchase interval by the pass rate spreads the per-funded net from $228 to $397. His +$300 sits inside that spread and outside the purchase interval. A second sample of the same activation-on rule, the first variant row, put the per-funded net at $395. So +$300 is a number the per-funded arithmetic can print. It is not a number the per-purchase interval contains, and it is not stable to a fresh sample. The subscription piece of the activation-on row is $226, which is the ~$220, and the $375 fees-per-pass is what you get once the $149 is included. The $225 median is 90% of a $250 request under the maximum-payout rule. The $125 minimum raises how many funded accounts get paid. It does not produce the median dollar. Mean funded cash of $687 is the "average payout about $700."

Assumption differences, from his slideshow to the model that produced the earlier −$100:

- His trade is +$500 or −$500, one a day, and the trade itself is worth zero. The earlier baseline risked $200 twice a day, then paid $1.22 and one tick each side, so the trade was already negative. That is why one number was about −$100 and the other is positive before costs are put back.
- His pass rate, about 25–28%, is the trailing floor. A static $2,000 floor on a fair ±$500 coin passes near 40%. The "no trailing floor" row is that object. It does not have his pass rate.
- The $220 figure is months of the $49 subscription allocated to each pass. The published path also charges $149 after a pass. Dropping the activation raises the per-purchase EV by about that $149 times the pass rate. It does not add $200.
- Putting the $35 MNQ cost back on, and grading the breach intraday, is the last row of the variant table. That is the slideshow coin under the cost model used everywhere else in this file.
- A funded account that starts at $50,000 instead of the XFA's $0, a payout that does not keep 10%, and a request sized so the trader keeps $700 are the other rows. Compare each one's pass rate and median with the 25–28% and $225 before calling it his slideshow.
- 54% and 60% win rates, in the coin table above, are not +$1,400 and +$3,300. The gap between those rows and the 50/50 row is the win rate.
- LucidFlex funded having no consistency rule was already how the recipe was run. The live page confirms it. The 40% versus 50% rows are the eval rule, and only the eval rule.


### The ±$500 coin, against the earlier −$100

His slideshow coin is one trade a day that closes at **+$500 or −$500**. The trade's own expectancy is zero. There is no commission in that payoff. He reports about **+$300 per Topstep attempt** and about +$250 on an Apex account at 80% off. Apex is not simulated. He also says a pass is about 25–28%, that about 60% of Topstep funded accounts get a payout before they die because the minimum request is $125, that the median Topstep payout is $225 and the average about $700, that 97% of funded accounts are dead within a year, and that the cost of getting funded is about $220 at $49 a month.

The earlier gross-zero result in the prop-structure search is a different bet. The pre-declared baseline risked **$200 twice a day**. Each trade was a random walk aimed at a target, then charged the published MNQ commission of $1.22 and one tick of slippage each side, so the trade was already negative before the firm took a fee. That row was **−$105** on Topstep 50K (−$112 to −$98) and **−$86** on LucidFlex 50K (−$91 to −$81) at an assumed $100 Lucid fee. The Lucid number sat on the fee because a $200 stake rarely reached a $3,000 target inside the horizon. CRT resampled into the same small stake did the same thing and printed the fee.

The table is his coin, one attempt, 4,000 paths, up to 252 trading days. The interval is a 95% interval on the mean. `No activation` drops the $149 Topstep charges after a pass. `$125 payout` requests the minimum whenever half the balance covers it. `Max payout` requests half the balance, capped at $2,000. Intraday mode busts the account when the planned loss is larger than the room under the current floor, which is how Topstep monitors the line. LucidFlex's own check is the close, so its intraday row is a re-grade. The Lucid fee is one-time and the dollar amount is not on the help page.

| setup | pass | ever paid | of funded, paid | of funded, dead in a year | median cash if funded | fees | fees per pass | EV per attempt |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Topstep ±$500, no cost, max payout, activation, end of day | 26.7% | 15.4% | 57.9% | 100.0% | $225 | $100 | $375 | $83 ($61 to $106) |
| Topstep ±$500, no cost, $125 payout, activation, end of day | 26.6% | 15.6% | 58.7% | 93.3% | $112 | $99 | $374 | $-42 ($-49 to $-36) |
| Topstep ±$500, no cost, $125 payout, no activation, end of day | 27.3% | 15.8% | 58.1% | 94.7% | $112 | $61 | $223 | $-7 ($-14 to $-1) |
| Topstep ±$500, no cost, $125 payout, activation, intraday | 27.3% | 15.5% | 56.7% | 96.5% | $112 | $100 | $367 | $-62 ($-66 to $-57) |
| Topstep ±$500, $14.52 cost, $125 payout, activation, intraday | 15.7% | 7.0% | 44.3% | 98.1% | $0 | $78 | $499 | $-58 ($-62 to $-55) |
| Topstep ±$500, $35 cost, $125 payout, activation, intraday | 13.2% | 5.5% | 41.7% | 99.2% | $0 | $75 | $563 | $-63 ($-66 to $-61) |
| Topstep ±$500, $35 cost, max payout, activation, intraday | 11.5% | 5.1% | 44.8% | 100.0% | $0 | $72 | $623 | $-36 ($-42 to $-29) |
| Topstep 54% win, no cost, $125 payout, activation, end of day | 40.6% | 27.9% | 68.8% | 79.5% | $112 | $122 | $300 | $69 ($54 to $85) |
| Topstep 60% win, no cost, $125 payout, activation, end of day | 66.0% | 53.6% | 81.3% | 50.6% | $450 | $159 | $241 | $725 ($688 to $762) |
| LucidFlex ±$500, no cost, max payout, end of day, fee $50 | 26.9% | 14.3% | 53.2% | 95.9% | $450 | $50 | $186 | $97 ($82 to $112) |
| LucidFlex ±$500, no cost, max payout, end of day, fee $100 | 27.3% | 15.0% | 55.0% | 95.7% | $450 | $100 | $367 | $53 ($38 to $68) |
| LucidFlex ±$500, no cost, max payout, end of day, fee $150 | 27.0% | 14.6% | 54.1% | 96.1% | $450 | $150 | $557 | $-6 ($-21 to $8) |
| LucidFlex ±$500, no cost, max payout, end of day, fee $200 | 27.3% | 14.4% | 52.7% | 95.8% | $450 | $200 | $733 | $-50 ($-65 to $-35) |
| LucidFlex ±$500, no cost, $500 payout, end of day, fee $100 | 27.4% | 14.6% | 53.4% | 93.8% | $450 | $100 | $365 | $22 ($10 to $33) |
| LucidFlex ±$500, no cost, max payout, intraday, fee $100 | 26.4% | 14.4% | 54.6% | 98.4% | $450 | $100 | $380 | $5 ($-5 to $16) |
| LucidFlex ±$500, $14.52 cost, max payout, end of day, fee $100 | 23.2% | 11.4% | 49.0% | 97.3% | $0 | $100 | $431 | $29 ($15 to $43) |
| LucidFlex ±$500, $35 cost, max payout, end of day, fee $100 | 16.8% | 7.9% | 47.1% | 99.1% | $0 | $100 | $596 | $-30 ($-39 to $-21) |

The row that matches his accounting most closely is the no-activation, $125-payout, no-cost Topstep coin: EV $-7 ($-14 to $-1), pass 27.3%, 58.1% of funded accounts get paid, median cash among funded accounts $112, mean cash among funded accounts $197, 94.7% of funded accounts dead by day 252, fees per passed account $223. His +$300, 25–28% pass, 60% of funded paid, $225 median, $700 average, 97% dead, and ~$220 to get funded sit next to those six numbers. Where a figure matches, it is this row and not the row with the activation.

Charging the $149 activation and grading the breach intraday, still with no commission, is $-62 ($-66 to $-57), below zero. Adding $14.52, his one-NQ round turn, is $-58 ($-62 to $-55). Adding $35, which is what $500 of risk costs in MNQ at a 16-point stop under the commission used everywhere else in this file, is $-63 ($-66 to $-61). Taking the maximum payout instead of $125, with no commission and the activation, is $83 ($61 to $106). A $500 day is 17% of the $3,000 target, so Topstep's 55% consistency rule does not raise the target. Intraday and end-of-day grading agree while the stop fits under the floor. They split once the room is under $500.

His 54% and 60% win-rate claims, on the same $125 Topstep book with the activation and no commission, are $69 ($54 to $85) and $725 ($688 to $762). He quotes +$1,400 and +$3,300. The gap between those and the 50/50 row is the win rate, not the fee.

On LucidFlex 50K the same no-cost coin, end of day, maximum payout, is $97 ($82 to $112) at a $50 fee, $53 ($38 to $68) at $100, and $-50 ($-65 to $-35) at $200. With the $35 MNQ cost and a $100 fee it is $-30 ($-39 to $-21). The intraday re-grade at $100 and no cost is $5 ($-5 to $16). Lucid's minimum request is $500, not $125, and the payout is half of cycle profit rather than half of a balance that started at zero. There is no activation fee. A $500 day does not trip the 40% eval consistency rule. The earlier −$100 was not this coin failing. It was a smaller, already-costed bet that never got to a payout.

### His LucidFlex recipe

The recipe, as he describes it: an eval day is +$1,500 with probability 60% or a −$2,000 bust. Two of those wins reach the $3,000 target. A funded day is then +$3,400 or −$2,000 with probability 39%, then days of +$150 with probability 95%. The big day counts as one of the five winning days. Profit of $4,000 pays half, capped at $2,000, and the trader keeps 90%, which is $1,800. He stops at 4 payouts. The rule is 5, and this sim allows 5. Those probabilities are his claims about a signal. They are not measurements from this repo. A 60% chance to make $1,500 while risking $2,000 is +$100 on the day before any fee.

Two +$1,500 days make the best day 50% of the profit. The default eval rule is 40%, so those two days do not pass. A third +$1,500 day makes the best day 33% and passes. The 50% add-on passes on day two. Its price is not on the help page, and it is not added on top of the fee. The cushion he mentions, about $1,560, is an example on the page and not a formula. This sim uses a plain ratio and no cushion. A missed +$150 day loses $150 and is retried, which is what the rulebook allows, except the one row where a miss fails the account. That fail rule is what his 81% joint probability assumes.

The household cannot run 100 evals at once. The notes cite Lucid's general FAQ for 10 evals, 5 funded, and 10 combined. The batch section buys a new eval only when the cash covers the fee and a slot is free. 3,000 paths for the per-eval table. The interval is on the mean.

| book | pass | payout rate per eval | payouts per 100 evals | EV per eval |
|---|---:|---:|---:|---|
| 25K 40% end of day fee $100 | 25.7% | 10.2% | 16.0 | $44 ($26 to $62) |
| 25K 40% intraday fee $100 | 21.7% | 8.9% | 13.6 | $23 ($6 to $39) |
| 25K 50% add-on end of day fee $100 | 36.6% | 14.7% | 23.9 | $114 ($93 to $136) |
| 25K 50% add-on intraday fee $100 | 36.0% | 13.6% | 21.3 | $91 ($71 to $112) |
| 50K 40% end of day fee $50 | 26.4% | 10.3% | 15.8 | $232 ($197 to $266) |
| 50K 40% end of day fee $80 | 26.9% | 10.1% | 16.4 | $213 ($176 to $250) |
| 50K 40% end of day fee $100 | 27.1% | 10.2% | 17.2 | $208 ($170 to $246) |
| 50K 40% end of day fee $150 | 27.2% | 11.7% | 19.5 | $198 ($158 to $239) |
| 50K 40% end of day fee $200 | 29.3% | 10.9% | 18.0 | $122 ($83 to $162) |
| 50K 40% intraday fee $50 | 22.6% | 8.5% | 8.5 | $102 ($85 to $120) |
| 50K 40% intraday fee $100 | 21.1% | 8.4% | 8.4 | $51 ($33 to $68) |
| 50K 40% intraday fee $150 | 21.0% | 7.7% | 7.7 | $-12 ($-29 to $5) |
| 50K 50% add-on end of day fee $50 | 35.1% | 14.1% | 21.3 | $331 ($292 to $369) |
| 50K 50% add-on end of day fee $80 | 36.5% | 13.3% | 21.9 | $311 ($269 to $353) |
| 50K 50% add-on end of day fee $100 | 36.9% | 14.2% | 22.3 | $298 ($257 to $340) |
| 50K 50% add-on end of day fee $150 | 35.9% | 13.5% | 21.3 | $230 ($189 to $270) |
| 50K 50% add-on end of day fee $200 | 34.6% | 13.8% | 22.4 | $200 ($157 to $243) |
| 50K 50% add-on intraday fee $50 | 34.9% | 13.6% | 13.6 | $192 ($170 to $214) |
| 50K 50% add-on intraday fee $100 | 36.8% | 14.3% | 14.3 | $156 ($134 to $179) |
| 50K 50% add-on intraday fee $150 | 34.6% | 13.5% | 13.5 | $91 ($69 to $113) |
| 100K 40% end of day fee $100 | 27.2% | 11.0% | 17.8 | $300 ($252 to $348) |
| 100K 40% intraday fee $100 | 21.6% | 8.3% | 13.5 | $204 ($161 to $247) |
| 100K 50% add-on end of day fee $100 | 36.4% | 14.5% | 23.5 | $429 ($374 to $484) |
| 100K 50% add-on intraday fee $100 | 36.7% | 14.0% | 21.8 | $390 ($340 to $441) |
| 50K 50% add-on end of day fee $100, a missed $150 day fails the account | 37.2% | 10.9% | 17.4 | $213 ($175 to $250) |
| 50K 50% add-on end of day fee $100, same payoffs at 50/50 | 23.7% | 7.8% | 11.4 | $89 ($62 to $116) |
| 50K 50% add-on intraday fee $100, same payoffs at 50/50 | 23.5% | 7.9% | 7.9 | $30 ($14 to $46) |
| 50K 40% end of day fee $100, same payoffs at 50/50 | 16.0% | 4.9% | 7.1 | $17 ($-4 to $39) |

At his hit rates, the 50K with the 50% add-on, end-of-day grading and a $100 fee is pass 36.9%, payout rate 14.2%, 22.3 payouts per 100 evals, EV $298 ($257 to $340). He quotes a 36% pass, an 11% chance an eval ever pays, about 22 payouts per 100 evals, and about +$290 per eval ($29k on $10k of fees). The same book at the default 40% rule is pass 27.1%, EV $208 ($170 to $246). Replacing his hit rates with a 50/50 coin on the same dollar payoffs is $89 ($62 to $116), above zero. Forcing a missed $150 day to fail the account, which is his 95% assumption rather than the rulebook, is $213 ($175 to $250).

Intraday grading is the open-loss check. On the 50K the first funded trade risks the full $2,000, which still fits. A $2,000 withdrawal then locks the floor at $50,100 and leaves about $1,900. The next trade still risks $2,000. End of day can close that trade green. Intraday liquidates it on the way down, so the winner is never banked. At his hit rates that re-grade is $156 ($134 to $179) against $298 ($257 to $340) at the close. The 50/50 version graded intraday is $30 ($14 to $46). His martingale post is the same point, with a pass rate of 64–67% at the close and 15–19% on the open loss. That book is not re-run. He already measured it as a net loser, and it has no stop to grade except the firm's line.

### A household for one month

One household, a $2,000 starting bankroll, 21 trading days, his hit rates, the 50K recipe, 600 households. A passed eval does not trade again the same day. New evals are bought only when a slot is free and the cash covers the fee. The 10th and 90th percentiles are one household's month, not the uncertainty on the mean. P(month negative) is the chance fees exceed payouts. P(can't buy another) is the chance less than one fee is left. A third-party card says Lucid treats a breach-and-rebuy batch as gambling. That sentence was not on the Lucid pages read for the rule file, so it is not in the sim, and it is the rule risk around the table.

| fee | consistency | grading | mean month | 95% CI of the mean | 10th to 90th | P(month negative) | P(can't buy another) | P(a payout) | mean payouts |
|---:|---|---|---:|---|---|---:|---:|---:|---:|
| $50 | 50% add-on | end of day | $12,206 | $11,892 to $12,520 | $7,332 to $17,232 | 0.2% | 0.2% | 99.8% | 9.41 |
| $50 | 50% add-on | intraday | $8,938 | $8,700 to $9,176 | $5,379 to $13,034 | 0.5% | 0.3% | 99.7% | 7.79 |
| $50 | 40% | end of day | $9,238 | $8,881 to $9,595 | $3,200 to $14,832 | 2.3% | 1.0% | 99.3% | 7.25 |
| $50 | 40% | intraday | $5,643 | $5,391 to $5,895 | $1,179 to $9,105 | 5.0% | 1.3% | 99.2% | 5.40 |
| $80 | 50% add-on | end of day | $8,745 | $8,391 to $9,098 | $3,292 to $13,654 | 3.3% | 2.7% | 97.8% | 8.62 |
| $80 | 40% | end of day | $5,914 | $5,522 to $6,305 | $-641 to $12,666 | 13.2% | 6.5% | 94.7% | 6.29 |
| $100 | 50% add-on | end of day | $6,447 | $6,057 to $6,837 | $-2,000 to $12,203 | 13.8% | 10.8% | 91.3% | 7.74 |
| $100 | 50% add-on | intraday | $3,532 | $3,257 to $3,808 | $-1,671 to $7,803 | 18.3% | 9.3% | 94.8% | 6.52 |
| $100 | 40% | end of day | $4,107 | $3,726 to $4,489 | $-2,000 to $10,546 | 25.8% | 16.5% | 90.0% | 5.60 |
| $100 | 40% | intraday | $1,562 | $1,315 to $1,809 | $-2,000 to $6,001 | 39.0% | 22.0% | 90.7% | 4.37 |
| $150 | 50% add-on | end of day | $2,115 | $1,804 to $2,426 | $-1,950 to $7,650 | 39.2% | 27.7% | 84.8% | 6.00 |
| $150 | 40% | end of day | $942 | $655 to $1,230 | $-1,950 to $6,329 | 54.0% | 42.7% | 77.7% | 4.11 |
| $200 | 50% add-on | end of day | $-3 | $-216 to $209 | $-2,000 to $3,998 | 63.2% | 46.8% | 75.5% | 4.93 |
| $200 | 40% | end of day | $-835 | $-1,025 to $-645 | $-2,000 to $2,730 | 79.8% | 68.3% | 69.0% | 3.00 |

### Account size, at the same fee

The recipe scales with the max-loss line. The eval win is half the profit target, the loss is the full max loss, and the big win is 1.7 times that max loss. The small day is the account's own minimum winning day, $100, $150 or $200. The fee in this comparison is a flat $100, which is his 50K assumption, not a published card. A real fee that scales with size would move the ranking.

End of day, 50% add-on, fee $100: 25K $114 ($93 to $136), 50K $298 ($257 to $340), 100K $429 ($374 to $484). The same three graded on the open loss: 25K $91 ($71 to $112), 50K $156 ($134 to $179), 100K $390 ($340 to $441). He says the 50K wins at every farm size. The two rows are the test, at a fee that does not grow with the account. A 25K request must be at least $500 and the cap is $1,000 before the split. A 100K cap is $2,500.

Across the 50K end-of-day 50% add-on, the fee sensitivity is:

- Fee $50: $331 ($292 to $369), above zero.
- Fee $80: $311 ($269 to $353), above zero.
- Fee $100: $298 ($257 to $340), above zero.
- Fee $150: $230 ($189 to $270), above zero.
- Fee $200: $200 ($157 to $243), above zero.

### Does a signal add anything inside that policy?

The 5-minute rule is his, and it was not fitted here. The 09:30–09:35 ET candle sets the direction and the stop, the entry is the 09:35 open, there is no target, and the trade is flat before 15:55. A session with a missing minute in that candle is skipped. The R column is one MNQ after $1.22 and one tick each side. The NQ dollar column uses the unslipped points and then subtracts his $14.52 once, so the tick is not charged twice. Holdout is July 2025 through July 2026. The earlier window is shown so the holdout is not the only number. It was not used to keep the rule.

- 5-minute, before July 2025: n=639, win 21.6%, mean R 0.103 (-0.140 to 0.345), PF 1.13, mean $ at 1 NQ after his $14.52 $84, mean $ at 1 MNQ after our costs $8, median MAE 1.12R
- 5-minute, holdout: n=266, win 28.2%, mean R 0.094 (-0.181 to 0.370), PF 1.13, mean $ at 1 NQ after his $14.52 $6, mean $ at 1 MNQ after our costs $-0, median MAE 1.11R

The three-bar gap is the reading of his IFVG post that can be coded without inventing a second rule: the first gap of at least one point between 09:30 and 11:00, one trade a day, stop beyond the gap, target 2R. He reported that family as a loser. CRT at 15 minutes and 0.25R is already in the table above: holdout mean R −0.081, win 77.2%, n=2175. His own 4-hour CRT post found profit factor 0.84.

- Three-bar gap, before July 2025: n=640, win 31.7%, mean R -0.131 (-0.239 to -0.022), PF 0.82
- Three-bar gap, holdout: n=267, win 35.2%, mean R -0.002 (-0.174 to 0.170), PF 1.00

Inside the 50K farm each step still risks that step's dollars, and the day's result is a draw from the holdout R. That is the signal sized to the farm, not one NQ. The coin next to it is his dollar payoffs at 50%, not at 60/39/95. Both pay a $100 fee and use the 50% add-on.

- His hit rates, from the recipe table: $298 ($257 to $340).
- Same payoffs, 50% coin, end of day: $89 ($62 to $116).
- Holdout 5-minute R, sized to the same risks, end of day: pass 4.0%, payout rate 0.1%, EV $-98 ($-100 to $-96).
- The same 5-minute book, graded intraday: $-98 ($-100 to $-97).
- Holdout three-bar gap, sized the same way, end of day: pass 13.3%, payout rate 1.5%, EV $-72 ($-80 to $-63).

The holdout 5-minute win rate is 28.2%. That is the rate that has to become a 60% eval day and a 95% day of +$150 if this rule is the farm's signal. Sizing the holdout R up to the farm's dollar risk is the EV row above, set next to the 50/50 coin and next to his 60/39/95 book. The difference from the coin is what the rule adds. The difference from his book is what the rule does not.

Not tested, because the post does not give a rule that can be run once: the first-hour session bias, and the Kairos Max overnight entry. Absorption at the day's high or low was not retested. It needs the MBP-10 tape, and the minute book in this repo is the end-of-minute snapshot.

### Verdict

The no-cost Topstep coin, taking $125 and skipping the activation, is $-7 ($-14 to $-1), below zero. That is the version of his claim this simulator can reproduce, and it is the version that leaves out the $149. With the activation and an intraday breach it is $-62 ($-66 to $-57), below zero. With the $35 MNQ cost as well it is $-63 ($-66 to $-61), below zero. The earlier −$100 was the $200 costed baseline, not this coin priced with no commission. On LucidFlex the ±$500 coin at a $100 fee is $53 ($38 to $68), above zero, and $-30 ($-39 to $-21), below zero, once the $35 cost is on. The fee is unconfirmed. The sign follows the fee row above. His recipe is not that coin. At the 60/39/95 hit rates, a 50K, the 50% add-on, end-of-day grading and a $100 fee, EV is $298 ($257 to $340), above zero. The default 40% rule, same fee, is $208 ($170 to $246), above zero. The open-loss re-grade of the 50% book is $156 ($134 to $179), above zero. The same payoffs at 50/50 are $89 ($62 to $116), above zero. Set that row next to the hit-rate row before treating the payout cap as the source of the profit. Per eval, the 50% end-of-day 50K book is $50 above zero ($331), $80 above zero ($311), $100 above zero ($298), $150 above zero ($230), $200 above zero ($200). A household with his hit rates, a $2,000 bankroll and a $100 fee has a 13.8% chance the month's cash is negative and a 10.8% chance it cannot buy another eval. At $200 those figures are 63.2% and 46.8%. The 10th percentile of a single month is $-2,000 at $100 and $-2,000 at $200. That is the risk of ruin for the month. It is not a lifetime bust probability. The 5-minute holdout, sized to the farm, is $-98 ($-100 to $-96), below zero. With the activation and the MNQ cost, the no-skill Topstep coin sits below zero. On Lucid the recipe is a bet that the 60/39/95 rates are real, that the account is graded at the close, that the 50% add-on is the rule in force, and that the fee is on the side of the table whose interval is above zero. Those are claims about a signal and a price, not a property of the payout cap.

