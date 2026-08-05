# Channel overview — ash10hazard

**Analyst:** ash10hazard-analyst · **Last updated:** 2026-08-05
**Channel:** https://www.youtube.com/@ash10hazard · 50 most recent videos enumerated,
3 tutorials transcribed and carded.

---

## Who he is, as far as the content shows

UK-based (references UK local time for NY session `[1cMWnAxElA0 @ 00:00]`), trades **NQ
futures only**, uses **ES purely as a confirmation instrument**. Self-describes as a
19-year-old profitable trader `[channel title: "Week In The Life OF A Profitable 19 YR OLD
Trader In Madrid"]`. Prop-firm funded — promotes an Alpha Futures affiliate code.

## Philosophy

Pure **ICT / Smart Money Concepts**. One model, applied repeatedly:
liquidity sweep → market structure shift → inverse order block paired with a fair value gap
→ enter on the FVG fill.

He offers **no market mechanism** — no claim about who is on the other side or why the
pattern persists. The nearest thing to a thesis is that price delivery is *algorithmic*:
> *"there are lots of times where outside a macro, a trade will algorithmically play out
> perfectly"* `[1cMWnAxElA0 @ 01:04]`

This distinguishes him from thesis-driven sources: **the model is a pattern, not an
explanation.**

## Session and instrument

| | |
|---|---|
| Instrument | NQ (traded), ES (confirmation only) |
| Session | New York, 09:30 → 14:15 ET `[1cMWnAxElA0 @ 00:21]` |
| Macro windows | 09:45–10:15, 10:45–11:15, 11:45–12:15, 13:45–14:15 ET |
| Entry timeframes | 1m–5m |
| Structure timeframes | 5m / 15m; bias on 4H/1H/15m/5m |

**London relevance:** although a NY trader, he consumes **London and Asia session extremes
as sweep targets** `[1cMWnAxElA0 @ 02:07]`, and one carded example trades a London-highs
sweep `[@ 08:50]`. See `research/_shared/session-map.md`.

## Recurring building blocks

`liquidity-sweep` · `momentum-shift` (his "market structure shift") · `fvg-fill` ·
`order-block-tap` · `multi-tf-alignment` (bias, and NQ/ES correlation) · `session-timing`
(macros) · `structure-stop` · SMT divergence (optional)

## Strategies carded

| id | name | status |
|---|---|---|
| `ash-unicorn-sb` | Unicorn Model / ICT Silver Bullet | core — 3 videos, rev c |

**Possible second model, not yet carded:** *gap continuation* — entering continuation moves
out of 5m/15m gaps `[1cMWnAxElA0 @ 02:07]`. Described once, one example given, never
revisited. Needs a dedicated video before it earns a card.

## How reliable is the content as evidence?

**Weak, with one point in its favour.**

- Of ~50 recent videos, roughly **40 are P&L headlines** (`+$4K`, `+$7.5K`, `+$12K`), and the
  visible history contains **one loss** plus two breakevens. That distribution is not
  achievable in real trading and indicates selective publication.
- The content is a **funnel**: every tutorial closes on Discord subscription, one-to-one
  mentorship, and an Alpha Futures affiliate code with a discount deadline
  `[UBIHB1oB784 @ 09:13]`.
- View counts are 46–1,500 — a small channel, not an established source.
- **In his favour:** in `pD5l_gEje9I @ 04:46, 08:30` he discloses that a live trade
  underperformed the walkthrough (2R → 1R) and explains why — a correction against his own
  interest, and the only such instance found so far.

**All performance figures are tagged `[trader-claimed, unverified]` throughout the cards.**

## What is specifiable vs what is not

| specifiable | not specifiable |
|---|---|
| session window, macro windows | order-block identification |
| liquidity sweep (5m/15m levels, session extremes) | "clear where price is drawing to" gate |
| market structure shift | which stop variant to use ("if the RR is good enough") |
| FVG identification and fill entry | trailing — explicitly discretionary in all 3 videos |
| bias via 4H/1H/15m/5m imbalance alignment | how many bias timeframes must align |
| stop at structure, break-even at 50% | early exit on an obstructing imbalance |

He states the judgement layer cannot be taught:
> *"if you understand price action, then you'll know. But, it's kind of hard to teach it to
> you unless you've been in the Discord watching me trade every day."* `[1cMWnAxElA0 @ 04:42]`

**Implication for the team:** a faithful backtest of the full model is not possible from the
public content. A mechanised subset is testable, but the mechanisation choices are **ours**
and must be labelled as such in any adaptation.

## Known blocker

**No ES data in this repo.** Two of his six checklist conditions (structure shift, inverse
order block) are specified on ES. Any NQ-only reconstruction tests a strictly weaker model.
Recorded per team decision 2026-08-05 not to pursue ES acquisition for now.
