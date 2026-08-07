# Journal Schema v1.0 — FROZEN (pass 30, pre-replay)

The walk-forward replay's memory is the journal; this schema is frozen before agents run.
Additions require a version bump (v1.1+) and never rename/remove v1.0 fields.
Live example: `output/journal_champion.csv` (146 rows). Producer: engine lane; consumer:
Hermes reporting mandate + regime agent context + L2 analog lookup.

## Per-trade fields (v1.0)
| field | type | meaning |
|---|---|---|
| month, day, fill | str | trade date + fill time (ET, HH:MM) |
| branch | E3bal \| E4war | which blend book took it |
| dir | long \| short | |
| pattern | A \| B \| B2 | §4 class |
| kind | reje \| disp | trigger mechanism |
| htf | with_trend \| counter_trend \| range | 15m regime flag at trigger |
| conf | int | confluence type count |
| vwap_touch | bool | candle range reached a VWAP band |
| align_votes | 0–3 | 2-of-3 HTF alignment votes (1H/4H/daily fractal trend) |
| day_type | balanced \| imbalanced | AMT pre-open classification |
| pre930 | bool | filled before cash open |
| risk_pts | float | fill → initial stop distance |
| entry, exit | float | prices |
| exit_reason | str | target/stop/be_stop/eod/partial+* |
| hold_min | int | minutes in trade |
| mfe_r, mae_r | float | peak excursions in R between fill and exit |
| points, dollars | float | size-weighted points; net dollars at 1 NQ |
| win | bool | dollars > 0 |

## Per-day regime fields (join on `day`; source `output/regime_vector.csv`)
day_type, imbal_share_20, imbal_share_10, trap_rate_10, range_pctl_20, gap_open_pts,
streak_imbal, red_folder_today — all computed strictly pre-open.

## Reserved for later versions (do not improvise names)
book_wall_ratio (depth at entry), delta_imbalance (trades footprint), regime_call /
regime_conf / playbook (agent outputs), analog_k_winrate (L2), news_ids (briefing items).
