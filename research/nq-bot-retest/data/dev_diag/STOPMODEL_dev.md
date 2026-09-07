## Step 1 — stop model: bot as shipped (stops on 2m close, filled at close) vs resting-order stops on 1m bars

| run | n | WR% | mean $ | LB95 $ | PF | total $ | maxDD $ | avg win / loss | both-stopped | median loss / stop | median hold (bars) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dev_C1a_C3a — close-based | 4299 | 56.9 | +11.12 | +7.99 | 1.307 | +47,802 | 3,187 | +83.2 / -84.2 | 36% | 1.38 | 4 |
| dev_ibnk_C1a_C3a — intrabar | 4446 | 44.7 | -9.73 | -11.48 | 0.682 | -43,244 | 43,663 | +46.6 / -55.2 | 45% | 1.11 | 2 |
|  intrabar counters: {'hard_stop_intrabar': 1980, 'hard_stop_gap_fill': 0, 'c1_trail_intrabar': 2457, 'c2_stop_intrabar': 2372, 'closed_on_2m_close': 94} |
|  per year (mean $/trade, n): 2021: close +5.7 (405) vs intrabar -11.7 (467); 2022: close +16.3 (1637) vs intrabar -9.0 (1947); 2023: close +8.7 (856) vs intrabar -10.6 (1022); 2024: close +8.1 (1401) vs intrabar -9.3 (1010) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dev_untouched — close-based | 4508 | 46.4 | +3.28 | +0.47 | 1.095 | +14,787 | 6,728 | +81.3 / -64.3 | 47% | 1.72 | 3 |
| dev_ibnk_untouched — intrabar | 3836 | 30.2 | -11.44 | -13.00 | 0.555 | -43,896 | 44,238 | +47.2 / -36.8 | 61% | 1.22 | 1 |
|  intrabar counters: {'hard_stop_intrabar': 2327, 'hard_stop_gap_fill': 112, 'c1_trail_intrabar': 1503, 'c2_stop_intrabar': 1447, 'closed_on_2m_close': 62} |
|  per year (mean $/trade, n): 2021: close -0.4 (347) vs intrabar -13.3 (366); 2022: close +3.0 (2017) vs intrabar -11.7 (2200); 2023: close +8.7 (631) vs intrabar -11.3 (660); 2024: close +2.2 (1513) vs intrabar -9.6 (610) |
|---|---|---|---|---|---|---|---|---|---|---|---|
