# Headline P&L — which number the live system trades (reconciled)

Three figures circulate for the combined 3-session (NY pre + gold + London) canon. They are
**different sizings of the same trade set**, all **USD** (NQ/MNQ, CME; MNQ = $2/pt). This
reconciles them and states plainly what goes live.

## The numbers, with sources

| Figure | Source (file:line) | What it is |
|---|---|---|
| **~+$106k / 2yr** | `docs/CANON-MECHANICAL.md:233` ("COMBINED with NY canon: ~+$106k/2yr"), `docs/LIVE-STACK.md:135` ("+$106k book") | Legacy headline under a **larger, pre-dollar-risk sizing** (old static micro counts — see `scripts/baseline_dollar_risk.py:2-7`). ≈1.89× the floor figure. **Not what trades.** |
| **+$55,989.81 / 2yr** (383 trades) — **ARMING REFERENCE** | `output/baseline_book_news.parquet`; `scripts/canon_news_clean.py` | The leakage-clean canon **plus the pre-open news blackout plus the 09:55–10:00 dead-zone cut** (ANGUS 2026-07-26; the zone's 3 canon trades were 0-for-3, and the champion population shows −23R/10% win there in both years — `docs/GOLDEN-WINDOW-DISSECTION.md` §4). Previous step (news only): +$55,617.56/386. The blackout-only detail that follows describes correction 2 (ANGUS 2026-07-26: no NY entry that would be open going into a pre-open high-impact release — `src/canon/news_gate.py`, `docs/FINDING-canon-has-no-news-blackout.md`). Floor schedule, deterministic. **A1/A2 parity targets THIS book.** NY +$34,111 / London +$21,506 (London unchanged). Win 51.8%, 13/13 months green, worst month +$733, maxDD $1,459. |
| ~~+$52,522.81 / 2yr (404 trades)~~ — **superseded 2026-07-26** | `output/baseline_book_clean.parquet`; `scripts/leakage_clean_compare.py` | The leakage-clean canon: the pre-window `C` check uses `pm_sofar_conf` (truncated at fill) instead of the look-ahead `conf_PM` (`docs/FINDING-conf_PM-lookahead-pre-window.md`). Floor schedule, deterministic. Superseded by the news-blackout book above; retained as the leakage-fix-only step. NY +$31,016 / London +$21,506. |
| ~~+$56,065.18 / 2yr (400 trades)~~ — **PRE-LOOKAHEAD-FIX** | `output/baseline_book.parquet`; `docs/PARITY-CHECK.md:24,67`; `docs/LAUNCH-RUNBOOK.md:109` | Superseded. The same trades but with the look-ahead `conf_PM` in the pre-window `C` check — inflated ~$3.5k. Retained as the historical baseline only; do NOT use as the live reference. 2025 +$28,949 / 2026 +$27,117. |
| **DD-scaled live P&L** (MC: funded-year median **~$237k with the spine**, ~$302k naked) | `docs/SAFETY-SPINE.md:146-165` | The **actual live sizing**: the dollar-risk schedule that scales the per-trade $-at-risk **up** as available drawdown grows and **down** toward the floor on a bad run. |

## What the live system will actually trade — plainly

- **Sizing rule:** the **dollar-risk conviction schedule** (`SAFETY-SPINE.md:146-160`), stop-width-normalized. Per-trade $-at-risk = a conviction tier (0.25 → 2.25) × an available-DD tier:
  - at the **floor** (≤ $3k available DD): $50 / $100 / $150 / **$200** / **$300** / **$400** for the six convictions;
  - scaling **up** as available DD grows (e.g. at $10k DD: $181 … $1,450), a hard **40-micro clamp** as the ceiling.
  - contracts = `min(40, round(risk_$ / (stop_pts × $2)))` in **MNQ micros** ($2/pt).
- **So the live 2-year P&L is not a single fixed number** — it is path-dependent on the account's available-DD trajectory. The MC estimate at Lucid 50k is **~$237k funded-year median with the spine active**.
- **The frozen arming reference (+$55,989.81)** is the **floor-only, DD-scaling-off** version — deliberately path-independent so it can be reproduced to the cent and used as the parity ground truth. It is the **conservative floor** of the live schedule, not a cap: live P&L rides **above** it whenever available DD is above $3k.
- **The ~$106k is a legacy figure** under the superseded larger sizing and should not be quoted as the live target. When a single headline is needed, use **+$55,989.81 (floor, reproducible)** for parity/validation and the **DD-scaled MC (~$237k funded-year)** for the live expectation.

## Currency

All figures are **US dollars**. Instrument NQ (CME); execution in **MNQ micros at $2/point**;
the dollar-risk schedule is denominated in USD-at-risk per trade.

## No divergence

This is a sizing reconciliation, not a defect: the $56,065.18 parity gate reproduces
byte-for-byte (agents included, `src/desk/canon_runtime.py`), and the $106k / DD-scaled
figures are different sizings of the identical decisions.
