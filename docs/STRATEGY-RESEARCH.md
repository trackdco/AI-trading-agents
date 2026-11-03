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
