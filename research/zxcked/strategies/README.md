---
date: 2026-08-07
kind: Stage-2 card set — where each Stage-1 candidate ended up
trader: Powell
---

# zxcked / Powell — Stage 2 card set

**Nothing is silently dropped.** Every one of the 27 Stage-1 candidates resolves to a card, a
shared component, a measurement, or a blocked item. Where several candidates collapsed into one
card, that is recorded as a decision, not an omission.

## The 8 cards

| card | verdict | GAP-entry? | NY? | blocking questions |
|---|---|---|---|---|
| `zxck-wick-ce` | **PARTIAL** | no | YES | Q-A1 entry point · Q-A3 liquidity location · Q-A4 displacement gate |
| `zxck-10am-keyopen` | **PARTIAL** | **YES** | YES | Q-B1 manipulation size · Q-B2 retest vs re-cross · Q-B3 fib mandatory |
| `zxck-gap-fill-edge` | **PARTIAL** | **YES** | partial | Q-D1 stop (core gap) · Q-D3 card vs variant |
| `zxck-cisd` | **PARTIAL** | variant | YES | Q-E1 standalone vs trigger |
| `zxck-news-draw` | **PARTIAL** | partial | YES | Q-H1 conflicts with CPI prior · Q-H3 may need 30s data |
| `zxck-ifvg-50` | **INSUFFICIENT** | **YES** | partial | Q-C2 bias/level requirement — blocking |
| `zxck-amd-pdarray` | **INSUFFICIENT** | partial | YES | Q-F1 range undefined — blocking |
| `zxck-mmxm-breaker` | **INSUFFICIENT** | partial | YES | Q-G1 consolidation undefined — blocking |

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

**All cards are committed as PARTIAL or INSUFFICIENT pending Brake's answers.** No card is
Confirmed, nothing has been backtested, no prereg exists and nothing is in the trial ledger.
