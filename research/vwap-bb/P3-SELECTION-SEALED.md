# P3 SELECTION — SEALED UNTIL ANGUS SUBMITS HIS READING

> ## DO NOT OPEN THIS FILE BEFORE SUBMITTING THE P3 SHEET.
> It contains the detector's expected values for the P3 instant, the timeframe the
> trigger fires on, its direction, and the reason the instant was chosen. Reading any
> of it before the reading is recorded destroys the blind and P3 measures nothing.

**Released to Angus: the date and the time. Nothing else.** Amendment 03 §7.

---

## 1. The selection, and why it is not evidence about agreement rates

**The instant was chosen FROM detector output.** That is legitimate test design — P3
exists to exercise code paths P2 never reached, and selecting inputs that reach deep
paths is what a unit test does. It is **not** legitimate as evidence about how often
the detector and the chart agree, because the instants were not randomly drawn.

> **The P3 result may be cited as evidence that the code paths behave as specified.**
> **It may NOT be cited as an agreement rate.**

**Chosen instant: 2025-01-29 10:20 ET.** Test-design score 17.

Why this one:
- signal at/after 10:00 — NY VWAP has >=30 bars, so A8's sigma-band eligibility rule is satisfied AND 1m-vs-2m VWAP aggregation has largely converged, widening the comparable surface (+3)
- cluster carries 5 levels (+3)
- 3 distinct types — exercises the counter-trend confluence path (+2)
- A7 tie-break fired at level 1 among 2 candidates (+2)
- 1 structural level(s) within tolerance of the cluster — exercises ambiguity (a), structural cluster-eligibility (+3)
- adjacent gap(s) [9.87] in the local ladder sit in the 7-10 pt band — exercises ambiguity (b), chaining vs span (+3)
- range position 0.047 sits near the retired 0.20/0.80 threshold — exercises ambiguity (d) as a covariate (+1)

What P2 could not test, and this instant does — the trade survives the confluence gate,
the §7 invalidation, the location gate, the entry-beyond-wick check and the RR-floor
ladder, wins its minute under the A7 tie-break, is admitted under the session cap and
fills at the next bar's open. **Every code path listed as unexercised in**
**`PARITY-P2-RESULT.md` §7 runs at this instant.**

## 2. Expected detector values

Session 2025-01-29, contract ['NQH5']. Signal close-minute
`cm = 620` = **10:20**, i.e. the bar covering **10:18:00 – 10:19:59** has just closed.

### The trade

| | |
|---|---|
| entry timeframe | **2** |
| direction | **long** |
| trigger kind | **displacement** |
| HTF flag | **downtrend** |
| counter-trend | **True** |
| distinct cluster types | **3** |
| levels in cluster | **5** |
| tie-break level that decided | **1** |
| candidates sharing the minute | **2** |
| intended entry (E1, BB MA) | **21526.0375** |
| stop price | **21509.5000** |
| target price | **21554.2690** |
| intended R, points | **16.5375** |
| cluster low | **21517.0480** |
| cluster mid | **21526.8533** |
| fill price (next bar open) | **21538.2500** |
| fill minute | 10:20 |

### Levels at the instant, per entry timeframe

**1m** — last close cm=620 (10:20)

| | |
|---|---|
| bar O/H/L/C | 21529.5 / 21541.0 / 21524.5 / 21538.25 |
| BB basis / +2σ / −2σ | 21536.4125 / 21564.6186 / 21508.2064 |
| daily VWAP mid / σ | 21581.0311 / 54.2397 |
| NY VWAP mid / σ | 21536.6585 / 19.6105 |
| NY bars since anchor | 50 |
| POC | 21522.0 |
| session hi / lo | 21697.0 / 21494.0 |
| pre-market hi / lo | 21697.0 / 21530.5 |
| prior-day hi / lo (Globex) | [21626.0, 21159.5] |
| 4h range hi / lo (clock blocks) | [21697.0, 21530.5] |
| HTF flag | downtrend |
| clusters | [(21517.05, 21536.66, ['bb', 'poc', 'vwap'])] |

**2m** — last close cm=620 (10:20)

| | |
|---|---|
| bar O/H/L/C | 21514.75 / 21541.0 / 21509.75 / 21538.25 |
| BB basis / +2σ / −2σ | 21526.0375 / 21553.1241 / 21498.9509 |
| daily VWAP mid / σ | 21581.0311 / 54.2397 |
| NY VWAP mid / σ | 21536.6585 / 19.6105 |
| NY bars since anchor | 50 |
| POC | 21522.0 |
| session hi / lo | 21697.0 / 21494.0 |
| pre-market hi / lo | 21697.0 / 21530.5 |
| prior-day hi / lo (Globex) | [21626.0, 21159.5] |
| 4h range hi / lo (clock blocks) | [21697.0, 21530.5] |
| HTF flag | downtrend |
| clusters | [(21517.05, 21536.66, ['bb', 'poc', 'vwap'])] |

**3m** — last close cm=618 (10:18)

| | |
|---|---|
| bar O/H/L/C | 21536.5 / 21546.75 / 21508.0 / 21514.25 |
| BB basis / +2σ / −2σ | 21548.7375 / 21620.1167 / 21477.3583 |
| daily VWAP mid / σ | 21581.7401 / 54.2521 |
| NY VWAP mid / σ | 21536.8897 / 19.8091 |
| NY bars since anchor | 48 |
| POC | 21522.0 |
| session hi / lo | 21697.0 / 21494.0 |
| pre-market hi / lo | 21697.0 / 21530.5 |
| prior-day hi / lo (Globex) | [21626.0, 21159.5] |
| 4h range hi / lo (clock blocks) | [21697.0, 21530.5] |
| HTF flag | downtrend |
| clusters | [(21517.08, 21536.89, ['poc', 'vwap']), (21548.74, 21556.7, ['bb', 'vwap'])] |

**5m** — last close cm=620 (10:20)

| | |
|---|---|
| bar O/H/L/C | 21536.5 / 21546.75 / 21508.0 / 21538.25 |
| BB basis / +2σ / −2σ | 21564.3000 / 21638.2213 / 21490.3787 |
| daily VWAP mid / σ | 21581.0311 / 54.2397 |
| NY VWAP mid / σ | 21536.6585 / 19.6105 |
| NY bars since anchor | 50 |
| POC | 21522.0 |
| session hi / lo | 21697.0 / 21494.0 |
| pre-market hi / lo | 21697.0 / 21530.5 |
| prior-day hi / lo (Globex) | [21626.0, 21159.5] |
| 4h range hi / lo (clock blocks) | [21697.0, 21530.5] |
| HTF flag | downtrend |
| clusters | [(21517.05, 21536.66, ['poc', 'vwap']), (21556.27, 21564.3, ['bb', 'vwap'])] |

## 3. Known-unverifiable fields at this instant

Recorded in advance so they are not later read as passes:

- **NY VWAP σ bands.** A8 fixes the feed at 1-minute and Angus cannot render a 1m VWAP
  for January 2025. Any agreement here is coincidence; any disagreement is expected.
- **1m row.** Unreadable (A11).
- **The daily POC.** At P2 the 1m-vs-2m profile construction diverged by 44.50 points.
  Whether it converges later in a session is unknown and is not being controlled for.

## 4. Provenance

| | |
|---|---|
| selector | `research/star-trading/tools/p3_select.py` |
| detector | `stage2_smoke.signal_candidates` + the A7 admission loop, unmodified |
| pool | January-2025 admitted trades on 2m/3m/5m: **30** |
| sealed workbench parquet | **NOT opened** |
| holdout | **SEALED**; every date read ≤ 2025-01-31 |
| N_trials | **0** — no outcome was computed and nothing was ranked by profitability |
