# Strategy index — all traders

Master table of every strategy card in the repo. Append rows; do not rewrite others'.

| id | name | trader | sessions | instruments | maturity | card |
|---|---|---|---|---|---|---|
| `ash-unicorn-sb` | Unicorn Model / ICT Silver Bullet | ash10hazard | New York | NQ (ES confirm) | core (3 videos, rev c) | `research/candidates/ash10hazard-unicorn-silver-bullet.md` |

— added by ash10hazard-analyst, 2026-08-05

**2026-08-05d — restructured to Angus's repo convention:** transcripts live at
`research/transcripts/<trader>/` (`<videoId>.md` = timestamped transcript, `CATALOG.txt`,
`EXTRACTION-*.md`); strategy cards live at `research/candidates/`. — ash10hazard-analyst

---

## zxcked / Powell — Stage 1+2 ingest, no cards built yet

**These are CANDIDATES, not cards.** Stage 2 produced the list; none has been specified to card
level, none has a prereg, none has been tested, and none is in the trial ledger.

Corpus: 39 transcripts / 38 unique videos, 2025-05-31 → 2026-05-19.
`research/zxcked/` · overview `channel-overview.md` · catalog `CATALOG-INGESTED.txt`.

| id | name | trader | sessions | instruments | gap-entry | maturity |
|---|---|---|---|---|---|---|
| `zxck-wick-ce` | Rejection block / wick CE | Powell | NY AM | NQ | no | candidate — his #1, most complete spec |
| `zxck-10am-keyopen` | 10:00 ET key-open limit | Powell | NY AM | NQ | **YES** | candidate — his #2, full spec |
| `zxck-displacement-rb` | Displacement-validated rejection block | Powell | NY AM | NQ | **YES** | candidate — his good/bad discriminator |
| `zxck-ifvg-50` | Inverse-FVG 50% mark | Powell | not stated | NQ | **YES** | candidate — stated standalone 3× |
| `zxck-gap-fill-edge` | Full gap fill at the far FVG edge | Powell | not stated | NQ | **YES** | candidate — inverse of ash's near-edge entry |
| `zxck-fib-trigger-stack` | Fib + rejection-block trigger at 10:00 | Powell | NY AM | NQ | **YES** | candidate |
| `zxck-cisd` | CISD retest | Powell | NY AM | NQ | no | candidate |
| `zxck-cisd-inversion` | CISD + FVG inversion | Powell | NY AM | NQ | **YES** | candidate |
| `zxck-pxh-pxl` | PXH/PXL daily bias state machine | Powell | daily | NQ | no | candidate — bias input, not an entry |
| `zxck-nwog-bias` | Unfilled NWOG/NDOG bias | Powell | all | NQ | **YES** | candidate — bias input |
| `zxck-gap-close-through` | Opening-gap close-through entry | Powell | all | NQ | **YES** | candidate |
| `zxck-amd-pdarray` | AMD into a PD array | Powell | NY | NQ | partial | candidate — range undefined |
| `zxck-mmxm-breaker` | MMXM breaker entry | Powell | NY | NQ | partial | candidate — consolidation undefined |
| `zxck-mmxm-bias` | MMXM as bias only | Powell | all | NQ | no | candidate — bias input |
| `zxck-news-draw` | News high/low opposing draw | Powell | 08:30 ET, news only | NQ | partial | candidate |
| `zxck-news-behaviour` | NFP-reverses / CPI-continues | Powell | NY | NQ | no | candidate — two claims, grade separately |
| `zxck-nowick-gap` | No-bottom-wick gap magnet | Powell | all | NQ | **YES** | candidate |
| `zxck-5m-trigger` | 5-minute vs 1-minute entry trigger | Powell | NY AM | NQ | no | candidate — **a pre-stated A/B** |
| `zxck-4h-both-wicks` | ~97% both-wicks base rate | Powell | all | NQ | no | **measurement, not a trade — free to run** |
| `zxck-open-as-target` | Un-manipulated open as the draw | Powell | NY | NQ | no | candidate |
| `zxck-open-proximity` | Nearest-extreme manipulation prior | Powell | NY open | NQ | no | candidate |
| `zxck-keyopen-wick` | Key open × rejection block | Powell | NY | NQ | no | candidate |
| `zxck-wick-start` | Rejection-block start-of-wick entry | Powell | all | NQ | no | candidate — fill-rate variant of `zxck-wick-ce` |
| `zxck-breaker-eqh` | Breaker with equal highs/lows inside | Powell | NY | NQ | no | candidate |
| `zxck-session-bias` | Session-extreme bias refinement | Powell | NY | NQ | no | candidate — **"significant" undefined** |
| `zxck-smt-exit` | SMT-divergence exit | Powell | NY | NQ + **ES** | no | **blocked — no ES data** |
| `zxck-15s-cisd-scalp` | 15-second CISD scalp | Powell | NY | NQ | no | **blocked — no sub-minute data** |

**Overlap with `ash-unicorn-sb`:** Powell's 10:00 ET key open sits inside ash10hazard's AM1
window (09:45–10:15 ET), same instrument, incompatible entries — a genuine A/B on the same half
hour where neither spec was written with the other in mind. Both are blocked on the same missing
**ES** data.

**Cheapest first move:** `zxck-4h-both-wicks` is a base-rate measurement with a pre-stated number
(97%), not a trade. It costs no selection budget and it either supports or kills the stated
mechanism behind `zxck-10am-keyopen`.

— added by zxcked/Powell ingest, 2026-08-07
