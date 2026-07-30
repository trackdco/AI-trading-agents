# FOR ANGUS — London spot-check sheet (the human calibration pass)

**The ask: pull each trade up on a chart (NQ, the listed TF, the listed day) and rule ONE of: (a) my setup — I'd have taken it; (b) my setup but I'd have skipped it, because ___; (c) NOT my setup — detector drift. Reply with the row number and a/b/c. The February hand-log did exactly this for NY; London's rebuild never got its own pass. Rulings feed the rev-3 signature, not any automatic change.**

Book: the rev-3 stack (08:00-09:45, wall gate, score-0 veto, one-position-at-a-time). Times are FILL times; the trigger candle closes 1-4 minutes earlier on the listed TF. V8 = shipped management outcome; V1 = BE-at-1R candidate outcome for the same entry. NOTE on 41/129 trades the fill improved through the resting limit, so the fill price sits closer to the stop than the risk-pts column (sizing basis = order-time limit-to-stop distance; limits only ever improve).

## A. Ten seeded-random trades (representative sample)

| day | fill | dir | tf | pattern | fill px | stop | risk pts | target | walls | V8 outcome | V1 outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2025-07-18 | 04:14 ET / 09:14 UK | long | 3min | B | 23275.50 | 23266.00 | 9.5 | walkout_daily_vwap_upper_2 | one wall | partial+stop +0.41R | be_stop -0.03R |
| 2025-08-22 | 03:02 ET / 08:02 UK | long | 1min | B2 | 23147.25 | 23134.25 | 13.0 | walkout_profile_val | both walls | partial+target +1.63R | target +2.87R |
| 2025-09-15 | 04:31 ET / 09:31 UK | short | 5min | A | 24102.75 | 24113.50 | 10.8 | walkout_london_session_low | both walls | partial+stop +0.59R | be_stop -0.02R |
| 2026-02-05 | 03:26 ET / 08:26 UK | short | 5min | B | 25108.75 | 25122.50 | 19.5 | london_session_low | both walls | partial+stop +0.92R | be_stop -0.01R |
| 2026-02-23 | 03:16 ET / 08:16 UK | long | 3min | B | 24896.50 | 24880.25 | 16.2 | walkout_daily_vwap_upper_1 | both walls | partial+stop +0.11R | stop -1.02R |
| 2026-03-09 | 04:04 ET / 08:04 UK | short | 3min | B2 | 24282.75 | 24311.50 | 28.8 | london_session_low | both walls | stop -1.01R | be_stop -0.01R |
| 2026-03-19 | 04:15 ET / 08:15 UK | long | 2min | B2 | 24578.50 | 24574.50 | 10.5 | london_session_high | both walls | stop -0.40R | be_stop -0.02R |
| 2026-04-08 | 03:21 ET / 08:21 UK | long | 5min | B2 | 25164.50 | 25149.75 | 14.8 | walkout_profile_vah | both walls | partial+stop +0.24R | be_stop -0.02R |
| 2026-04-20 | 03:30 ET / 08:30 UK | long | 5min | B2 | 26658.75 | 26648.75 | 10.0 | profile_vah | both walls | stop -1.02R | stop -1.02R |
| 2026-05-20 | 03:47 ET / 08:47 UK | short | 2min | A | 29044.00 | 29053.00 | 9.5 | daily_vwap_mid | one wall | partial+stop +0.21R | be_stop -0.03R |

## B. The twelve worst 1-lot losers (every big loss, individually)

| day | fill | dir | tf | pattern | fill px | stop | risk pts | target | walls | V8 outcome | V1 outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2025-09-02 | 04:06 ET / 09:06 UK | long | 5min | A | 23304.00 | 23267.75 | 36.2 | daily_vwap_mid | both walls | stop -1.01R | stop -1.01R |
| 2025-10-31 | 04:26 ET / 08:26 UK | short | 5min | A | 26176.25 | 26193.50 | 17.2 | walkout_daily_vwap_lower_2 | one wall | stop -1.01R | stop -1.01R |
| 2026-01-05 | 04:28 ET / 09:28 UK | short | 2min | B | 25505.25 | 25519.50 | 14.2 | london_session_low | both walls | stop -1.02R | stop -1.02R |
| 2026-02-10 | 03:31 ET / 08:31 UK | short | 5min | B | 25350.25 | 25366.75 | 25.0 | walkout_daily_vwap_lower_2 | one wall | stop -0.67R | stop -0.67R |
| 2026-03-09 | 04:04 ET / 08:04 UK | short | 3min | B2 | 24282.75 | 24311.50 | 28.8 | london_session_low | both walls | stop -1.01R | be_stop -0.01R |
| 2026-03-17 | 04:13 ET / 08:13 UK | short | 5min | B | 24773.25 | 24793.25 | 20.0 | walkout_asia_session_low | both walls | stop -1.01R | be_stop -0.01R |
| 2026-03-19 | 05:16 ET / 09:16 UK | long | 5min | B2 | 24566.00 | 24551.25 | 14.8 | london_session_high | one wall | stop -1.02R | be_stop -0.02R |
| 2026-03-24 | 05:30 ET / 09:30 UK | long | 1min | B | 24358.00 | 24343.75 | 14.2 | asia_session_high | both walls | stop -1.02R | stop -1.02R |
| 2026-04-29 | 04:43 ET / 09:43 UK | short | 3min | B | 27230.50 | 27248.25 | 17.8 | walkout_asia_session_low | one wall | stop -1.01R | stop -1.01R |
| 2026-06-16 | 04:39 ET / 09:39 UK | short | 2min | A | 30877.25 | 30896.50 | 19.2 | daily_vwap_mid | both walls | stop -1.01R | ? +nanR |
| 2026-06-16 | 03:52 ET / 08:52 UK | short | 5min | B | 30826.25 | 30842.25 | 16.0 | walkout_profile_val | both walls | stop -1.02R | ? +nanR |
| 2026-06-26 | 04:12 ET / 09:12 UK | short | 5min | B2 | 29492.50 | 29514.00 | 21.5 | london_session_low | one wall | stop -1.01R | be_stop -0.01R |

Context for section B: all twelve were autopsied in docs/LONDON-VETO-SCAN.md — no shared mechanical cause survived the guards; several fade value hard (1-2sigma wrong side of VWAP) or enter at range extremes. The question for the human eye is whether these look like honest losses on valid setups, or like trades you would have refused on context the detector cannot see.
