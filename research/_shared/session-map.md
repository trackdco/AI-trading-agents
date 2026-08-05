# Session & coverage map — every carded strategy, both traders

**Updated 2026-08-07.** Built by reading the cards and the trade logs; no backtest was re-run and
nothing new was carded. Supersedes the 2026-08-05 version, whose `ash-unicorn-sb` window
(09:30–14:15 ET) predates the AM1 narrowing. Its two London notes are kept verbatim at the bottom.

## Footprint span

**2025-06-01 → 2026-07-15** — the aggressor-tagged window that defines flow coverage everywhere
below. Bar data runs 2025-01-01 → 2026-07-15, so **bars extend ~5 months earlier than flow**.

---

## The table

| card | trader | verdict | instrument | session & clock window | window derived from | entry TF | gap-entry? | log span | events | in-span | flow computed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ash-unicorn-sb` | ash10hazard | **baselined** | NQ | **NY · 09:45–10:15 ET** | **his** macro schedule `[qngA8aIfV0M @ 00:27–01:46]`, narrowed to AM1 by Brake's standing rule — and he names AM1 highest-probability *before* any test `[@ 01:46]` | 1m entry, 15m levels | **YES** | 2025-03-07 → 2026-07-15 | **37** | 29 | **29** |
| `zxck-10am-keyopen` | Powell | **Confirmed** | NQ | **NY · 10:00–10:15 ET** | level is **his** (10:00 = 4H open `[Y-oqSZmNo4U @ 00:49]`); the **15-minute cutoff is OURS** — Brake's macro rule. My first mechanization used 10:00–14:00 and was wrong | 1m | **YES** | 2025-01-06 → 2026-07-15 | **146** taken (115 decidable in-span) | 115 | **102** |
| `zxck-gap-fill-edge` | Powell | **Confirmed** | NQ | **not stated** — *"you can basically use any time frame"* `[86DOt135Wts @ 02:26]`; both traded examples are 4H wick trades | would be **OURS** | any | **YES** | — | — | — | — |
| `zxck-ifvg-50` | Powell | **Confirmed** | NQ | **not stated** anywhere | would be **OURS** | 5m/15m standalone; 1m/3m as trigger | **YES** | — | — | — | — |
| `zxck-cisd` | Powell | **Confirmed** | NQ | NY; worked example is the **09:00 ET** candle into the open. HTF variant on D/4H/1H | **his** by example, not by rule | 1m trigger; D/4H/1H standalone | **no** (inversion is a bonus) | — | — | — | — |
| `zxck-wick-ce` | Powell | **Partial** | NQ | **NY AM**, no clock window. Session-agnostic in practice — he took a London one when busy `[AGmRZ9Te9NY @ 00:23]` | **his**, loosely | 1m/3m/5m trigger | **no** | — | — | — | — |
| `zxck-news-draw` | Powell | **Partial — parked** | NQ | **08:30 ET, PPI & NFP only** (CPI skipped) | **his** for the level `[c15YLeAKc2A @ 05:36]`; the CPI skip is **ours**, ratified | 15s/30s stated, 1m acceptable | partial | — | — | — | — |
| `zxck-mmxm-breaker` | Powell | **Insufficient — parked** | NQ | NY, no clock window | — | 5m | partial | — | — | — | — |
| `zxck-amd-pdarray` | Powell | **Withdrawn** | — | — | AMD is his name for the engineered-liquidity *shape*, not a model | — | — | — | — | — | — |

`ash-unicorn-sb` has a second, empty log: `ash-unicorn-sb-forward.csv` — **0 rows**, the
pre-registered forward clock (LOOK 1 at n_forward = 20, first eligible date 2026-08-08).

---

## 1 · Fully flow-covered and ready to pool

| card | trades with a defined direction **and** computed flow |
|---|---|
| `ash-unicorn-sb` | **29** |
| `zxck-10am-keyopen` | **102** |
| **POOLED n AVAILABLE TODAY** | **131** |

Both are scored on the **identical locked exit** (2R target, break-even at 1R, no trailing,
stop-first on a same-bar conflict, 16:00 ET cap, costs separate) and the **identical flow
definitions**, so the logs concatenate without a rename. See `EXIT-CONVENTION-LOCKED.md`.

**Two things to know before treating 131 as one sample:**

- **The windows only partly overlap.** `ash-unicorn-sb` runs 09:45–10:15; `zxck-10am-keyopen`
  runs 10:00–10:15. The shared 15 minutes are the honest intersection, but roughly the first half
  of ash's window has no Powell counterpart.
- **`zxck-10am-keyopen`'s expectancy bound is entirely negative** — [−0.140R, −0.027R]. Pooling it
  adds count, not evidence of edge. It is arguably more useful as a *contrast* arm for the F2 test
  — does retracement participation separate winners in a book that has no edge? — than as
  additional support.

### ⚠️ CORRECTION 2026-08-07 — "why 102 and not 115" was answered wrongly above

I first wrote that the 13 gaps were computational (empty legs / zero displacement volume).
**That was wrong.** Brake questioned the coverage claim and the real cause is a data-derivation
defect:

**`output/fp_minutes.parquet` is missing January 2026.** It holds **60 rows for 2026-01** against
27,000–31,000 for every other month — and those 60 are the tail of `footprint_q4_2025.parquet`,
which ends 2026-01-01.

**The raw data exists.** `data/reference/cvd/footprint_jan2026.parquet` holds **1,542,534 rows**
covering 2026-01-01 → 2026-01-30. It was simply never folded into the derived frame that every
flow test reads.

| | |
|---|---|
| trading days in span with AM1 bars | **290** |
| of those, with AM1 flow | **269** (92.8%) |
| **missing** | **21 — every one of them January 2026** |
| partially covered days | **0** — coverage is all-or-nothing per day |

**Blast radius:**
- `ash-unicorn-sb` — **unaffected**. Its log jumps 2025-12-24 → 2026-03-09, so it has no January
  trades. The earlier backfill audit's conclusion still stands *for that card*.
- `zxck-10am-keyopen` — **13 trades affected**, and they are *exactly* the 13 "undefined flow"
  rows. Not a quirk; the gap. Its rev-d **R values are unaffected** (price only); only the flow
  columns would change.
- **29 scripts read `fp_minutes.parquet`**, including `london_canon.py` and `score_canon_span.py`.
  Any flow-based result computed over January 2026 anywhere in this repo is affected.

**Fix:** rebuild `fp_minutes.parquet` including `footprint_jan2026.parquet`. It is a tracked
artifact committed as prebuilt (`b9724e6`) with no in-repo builder, and it is shared with the
canon work — **so it is not being regenerated unilaterally.**

### Sign convention — checked while here, and it is correct
`delta` in `fp_minutes` correlates **+0.645** with the minute's (close − open) across 369,045
minutes, agreeing in sign on **75.5%** of non-zero minutes. It is **buy-positive**, which is the
convention `F1_disp_delta` assumes. No inversion.

---

## 2 · Blocked — and the two kinds are not interchangeable

### DATA blockers — fixable by buying or re-processing

| what | which cards | what exactly is missing |
|---|---|---|
| **intrabar sequence** | `zxck-10am-keyopen` **(bites now)**; `zxck-gap-fill-edge`, `zxck-ifvg-50` **will inherit** | **73 sessions** in-span where both sides breach ±10pt inside one bar. Unresolvable → currently **bounded**, not resolved. Fix: Databento `GLBX.MDP3` **trades** schema, NQ front month, 2025-06-01 → 2026-07-15, restricted to **10:00:00–10:15:00 ET**; strictly only those ~73 sessions' first minutes are needed |
| **flow before 2025-06-01** | `ash-unicorn-sb` (8 trades), `zxck-10am-keyopen` (31 in-log trades) | same feed, span 2025-03-01 → 2025-05-31. Recovers ash from 29 → 37 |
| **sub-minute bars** | `zxck-cisd` (15-second scalp variant); `zxck-news-draw` (30s trigger — **does not bite**, he says 1m is acceptable) | we hold 1-minute and nothing finer |
| **ES 1-minute** | `ash-unicorn-sb` (ES leading trigger), `zxck-cisd` / `zxck-wick-ce` (SMT filter), `zxck-smt-exit` | **two independent traders both require ES.** Never held |
| **depth / heatmap** | none carded — the ATAS resting-liquidity idea | one snapshot per minute **and** mis-stamped (`docs/FINDING-depth-snapshot-lookahead.md`) |

### RULE blockers — no data purchase fixes these

| what | which cards | why it stays blocked |
|---|---|---|
| **"original consolidation" undefined** | `zxck-mmxm-breaker` | he draws the box by eye. Parked by instruction; inventing a range detector would be fabrication |
| **data high/low window length undefined** | `zxck-news-draw` | any window we pick would be ours **and would define the level** — a fabricated component in a core rule |
| **engineered-liquidity side contradicts** | `zxck-wick-ce` | `[wS-dBenAIlY @ 01:11]` and `[xae9AiV5Ps4 @ 02:40]` place it on opposite sides. Left unresolved by instruction; best reading rides as `[inferred]` |
| **no window stated at all** | `zxck-gap-fill-edge`, `zxck-ifvg-50` | see §3 — a decision to make, not a data problem |

---

## 3 · ⚠️ Cards whose window sits outside — or has no defined relationship to — the footprint span

**Flagged now rather than mid-baseline.**

1. ~~**`zxck-gap-fill-edge` and `zxck-ifvg-50` have NO stated clock window.**~~ **RESOLVED
   2026-08-07 — both inherit 09:45–10:15 ET, dates 2025-06-01 → 2026-07-15.**
   Brake: *"I just want it to be the time that we have data for order flow."* Measured: flow covers
   **00:00–23:59 ET every hour** (only the 17:00 CME break missing), 271 of 271 trading days
   complete across the macro — so **flow constrains the DATE range only, never the clock**. The
   clock therefore comes from Brake's standing macro rule, and **it is OURS, not either trader's**
   — tag it `[stated-by-user]` on both cards and in any result. See `zxck-COMPONENTS.md` §F000.

2. **`ash-unicorn-sb`'s log starts 2025-03-07 — three months before flow.** 5 of its 24 trades
   sit outside the footprint span and can never be flow-covered from held data.
   *(Was 8 of 37 before the 2026-08-07 sweep-gate fix — see the card.)*

3. **`zxck-10am-keyopen`'s rev-c log spans 2025-01-06 → 2026-07-15, but its rev-d baseline is
   restricted to the footprint span** so conventions are not mixed. **Do not pool the rev-c log** —
   it contains 31 pre-flow trades scored under a different coverage regime.

4. **`zxck-news-draw` trades 08:30 ET**, well outside the 10:00–10:15 macro every other card now
   uses. Flow exists for it, but it would not pool on session with anything else.

5. **`zxck-cisd`'s HTF variant (daily/4H/1H) has no intraday window at all** — the flow features as
   defined (per-minute displacement and retracement legs) do not straightforwardly apply to a
   daily-timeframe entry.

---

## What each data source can and cannot do

| source | is | gives | **cannot** give |
|---|---|---|---|
| `data/reference/nq_1m_master.parquet` | 1-minute OHLCV | everything price-structural | intrabar sequence |
| `data/reference/cvd/footprint_*.parquet` | **minute × price × side** | CVD, signed delta, volume-at-price, absorption | **intrabar sequence** — volume-at-price is identical whether price went up-then-down or down-then-up |
| `output/fp_minutes.parquet` | per-minute vol + delta | `F1_disp_delta`, `F2_retrace_ratio` | price-level detail; sequence |
| `data/reference/depth_*/nq_depth_*.csv` | **one snapshot per minute**, 10 levels × 2 sides | static book imbalance only | placement / cancellation / refill, i.e. **any heatmap** — and it is mis-stamped |

**Which limitation actually bites, per card:** intrabar sequence bites `zxck-10am-keyopen`
**today** (73 sessions bounded rather than resolved) and will bite `gap-fill-edge` and `ifvg-50`
the moment they are baselined. Nothing carded currently needs depth. Everything else is fully
served by 1-minute bars plus the footprint.

---

## Retained notes from the 2026-08-05 version

**Note — London overlap:** `ash-unicorn-sb` is a New York strategy but consumes **London
highs/lows as sweep targets** (`[1cMWnAxElA0 @ 02:07]`, and example 3 `[@ 08:50]` trades a
London-highs sweep). So London session extremes feed a NY entry. Relevant to anyone mapping
London structure.

**Note 2 — London variant, uncarded (added 2026-08-05d):** the full 602-video enumeration shows
**20 London-session videos** naming explicit London macro windows — *"2:45–3:15AM ICT LDN Macro"*
and *"3:45–4:15AM ICT LDN"*. None of the three carded videos cover it, so `ash-unicorn-sb` is
NY-only **because its sources were**, not because he only trades NY. Anyone working London should
know a London application of the same model exists on the channel and has not been documented.

*Powell's counterpart, added 2026-08-07:* he too takes London when he cannot trade NY AM — *"This
was a London session rejection block. So, not something that I usually go for, but I was busy
during New York AM that day"* `[AGmRZ9Te9NY @ 00:23]`. **Neither trader is structurally NY-only;
both are carded that way because that is what we ingested.**

— rebuilt 2026-08-07
