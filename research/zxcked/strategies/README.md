---
date: 2026-08-07
kind: Stage-2 card set — where each Stage-1 candidate ended up
trader: Powell
---

# zxcked / Powell — Stage 2 card set

**Nothing is silently dropped.** Every one of the 27 Stage-1 candidates resolves to a card, a
shared component, a measurement, or a blocked item. Where several candidates collapsed into one
card, that is recorded as a decision, not an omission.

## The card set — re-verdicted 2026-08-07 (rev b)

| card | verdict | GAP-entry? | NY? | status |
|---|---|---|---|---|
| **`zxck-10am-keyopen`** | **CONFIRMED** | **YES** | YES | 🟢 **GREENLIT** — every part is his |
| **`zxck-gap-fill-edge`** | **CONFIRMED** | **YES** | partial | 🟢 **GREENLIT** — a *variant* of wick-ce, one trial not two |
| **`zxck-ifvg-50`** | **CONFIRMED** ↑ | **YES** | partial | 🟢 **GREENLIT** — ⚠️ bias gate is `[stated-by-user]`, weaker footing than the other two |
| `zxck-cisd` | **CONFIRMED** | no | YES | parked for pooling — the FVG inversion is a bonus, so not a gap entry |
| `zxck-wick-ce` | PARTIAL | no | YES | Q3 left unresolved **by instruction**; both conflicting quotes preserved |
| `zxck-news-draw` | PARTIAL — **PARKED** | partial | YES | CPI-skip locked, but Q-H2 (the data high/low window) is undefined and it **defines the level** |
| `zxck-mmxm-breaker` | INSUFFICIENT — PARKED | partial | YES | shelved; no range definition invented |
| `zxck-amd-pdarray` | **WITHDRAWN** | — | — | AMD is his name for the engineered-liquidity shape, not a model |

**Greenlit for Stage 3: `zxck-10am-keyopen` and `zxck-gap-fill-edge`** — the only cards that are
both Confirmed and gap-entry.

**Exit convention is locked** across every card — see `EXIT-CONVENTION-LOCKED.md`. Identical to
`ash-unicorn-sb`: target 2R, break-even at 1R, no trailing, stop-first on a same-bar conflict,
capped 16:00 ET, costs reported separately. Powell's Apex-driven trailing and his 1:4–1:6 band
stay recorded as `[trader-claimed, unverified]` and are **not** scored.

## Candidates that became COMPONENTS, not cards

These are **used by every card**. Carding them separately would double-count the same trades in
the trial ledger — the failure §6.0 exists to prevent.

| candidate | now lives at |
|---|---|
| `zxck-pxh-pxl` | `zxck-COMPONENTS.md` §A1 — bias input, no entry of its own |
| `zxck-session-bias` | §A2 (and **"significant" is undefined** — Q-B1 in the components list) |
| `zxck-mmxm-bias` | §A3 |
| `zxck-nwog-bias` | §A4 |
| `zxck-open-proximity` | §A5 |
| `zxck-breaker-eqh` | §B — engineered liquidity inside a breaker |
| `zxck-wick-start` | §C / `zxck-wick-ce` — an entry-point variant, not a model (Q-A1) |
| `zxck-displacement-rb` | §C3 / `zxck-wick-ce` — a quality rule (Q-A4 decides gate vs tell) |
| `zxck-ifvg-trigger` | §C — the 1m/3m scale of `zxck-ifvg-50` (Q-C1) |
| `zxck-5m-trigger` | §C1 — **a pre-stated A/B, not a strategy**: 1m vs 5m trigger timeframe |
| `zxck-cisd-inversion` | `zxck-cisd` — variant (Q-E4) |
| `zxck-fib-trigger-stack` | `zxck-10am-keyopen` — he says the fib *"is not a strategy. It is a confluence"* `[tNyT7tHOmGI @ 02:23]`, so it is not carded alone |
| `zxck-keyopen-wick` | `zxck-10am-keyopen` × `zxck-wick-ce` — an intersection, not a third model |
| `zxck-gap-close-through` | `zxck-10am-keyopen` §entry — he says to treat an opening gap *"like a key open"* `[rwPo6UyVOo8 @ 01:39]` |

## Measurements — no trade, no selection budget

| item | what it is |
|---|---|
| `zxck-4h-both-wicks` | his ~97% claim about 4H candles wicking both sides of their open. **A base rate on data we hold.** It either supports or kills the mechanism behind `zxck-10am-keyopen`. Cheapest first move in the programme. |
| `zxck-open-as-target` | the inverted case — carded inside `zxck-10am-keyopen` |
| `zxck-nowick-gap` | *"a 15-minute gap with no bottom wick… extremely rare that it never comes back"* `[WEeXKMzaJjY @ 05:37]` — a magnet base rate |
| `zxck-news-behaviour` | NFP reverses at open / CPI continues. **Two claims — grade separately.** Feeds Q-H1. |

## Blocked on data we do not hold

| item | blocker |
|---|---|
| `zxck-smt-exit` | **ES 1-minute.** Same blocker as `ash-unicorn-sb`'s ES leading trigger — two independent traders now need it |
| `zxck-15s-cisd-scalp` | **sub-minute bars.** We hold 1-minute |

## Status

**rev b, 2026-08-07.** 18 of 23 questions self-resolved from the transcripts; Brake answered Q3,
Q20 and Q22 and ratified the fixed 10pt floor. **Three cards are Confirmed, two of them
gap-entry and greenlit.** Nothing has been backtested, no prereg exists, and nothing is in the
trial ledger.
