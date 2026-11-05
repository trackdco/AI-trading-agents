# No-edge baseline

Seed 20261103, 1500 paths, 60 trading days, 2 trades a day, win rate 50%, average win equal to average loss. No slippage and no commission. A pass is the eval target under that firm's consistency rule. Where a funded account is chained, it is a fresh account and the payout columns include it. Lucid fees are 0 because the help centre did not print a price.

| account | risk $ | pass | bust | E[fees] | E[payouts] | E[trader $] | cost per payout | EV / eval | note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| topstep_combine_50k | 200 | 15.0% | 57.9% | 134 | 0.13 | 70 | 995 | -64 | standard path, $49/mo + $149 |
| topstep_combine_50k | 400 | 25.8% | 74.2% | 95 | 0.13 | 151 | 723 | 56 | standard path, $49/mo + $149 |
| topstep_combine_50k | 1,000 | 25.6% | 74.4% | 87 | 0.09 | 157 | 998 | 70 | standard path, $49/mo + $149 |
| topstep_combine_100k | 400 | 12.3% | 71.9% | 215 | 0.09 | 78 | 2,478 | -137 | standard path, $99/mo + $149 |
| topstep_combine_150k | 400 | 3.1% | 45.5% | 518 | 0.03 | 23 | 19,933 | -495 | standard path, $199/mo + $149 |
| lucidflex_eval_50k | 400 | 26.1% | 73.9% | unconfirmed | 0.15 | 163 | 0 | 163 | 40% consistency, fee not published |
| lucidflex_eval_100k | 400 | 12.7% | 70.9% | unconfirmed | 0.00 | 0 | inf | 0 | eval only, fee not published |
| lucidflex_eval_150k | 400 | 2.6% | 47.2% | unconfirmed | 0.00 | 0 | inf | 0 | eval only, fee not published |
| lucidpro_eval_25k | 400 | 35.1% | 64.9% | unconfirmed | 0.00 | 0 | inf | 0 | no eval consistency, DLL none |
| lucidpro_eval_50k | 400 | 26.9% | 73.0% | unconfirmed | 0.00 | 0 | inf | 0 | no eval consistency, DLL $1,200 |
| lucidpro_eval_100k | 400 | 12.6% | 70.8% | unconfirmed | 0.00 | 0 | inf | 0 | no eval consistency, DLL $1,800 |
| lucidpro_eval_150k | 400 | 2.4% | 45.5% | unconfirmed | 0.00 | 0 | inf | 0 | no eval consistency, DLL $2,700 |

## Same firm, with an edge

Win rate 50%, average win 1.5× the loss. Expectancy is +0.25R per trade. This is a hypothetical distribution, not a measured setup.

| account | risk $ | pass | bust | E[fees] | E[payouts] | E[trader $] | cost per payout | EV / eval | note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| topstep_combine_50k | 200 | 86.3% | 9.9% | 213 | 1.89 | 2,502 | 112 | 2,289 | +0.25R, Topstep 50K standard |
| topstep_combine_50k | 1,000 | 41.4% | 58.6% | 111 | 0.95 | 1,687 | 117 | 1,576 | +0.25R, Topstep 50K standard |

Static floor, no consistency, no trail, risk $250, up to 400 days: pass rate 41.9%. The closed form is 2,000 / 5,000 = 40%.

Paths that have neither passed nor busted are still open at day 60. On the 150K rows that share is about half, so those pass rates are censored by the horizon, not a finished probability.

The Lucid rows with EV above zero use a fee of $0 because the help centre did not print a price. That EV is not a reason to buy an account. Topstep's small positive EV at $400 and $1,000 of risk is the cheap subscription against a payout, before slippage, commission, and the trades the firm rejects. It is not an edge.

