# Channel overview — ash10hazard

**Analyst:** ash10hazard-analyst · **Last updated:** 2026-08-05
**Channel:** https://www.youtube.com/@ash10hazard · **602 videos** fully enumerated
(`channel-enumeration.txt`), **3 tutorials transcribed and carded**.

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
| Session | New York, 09:30 → 14:15 ET `[1cMWnAxElA0 @ 00:21]` — **but see London below** |
| Macro windows | 09:45–10:15, 10:45–11:15, 11:45–12:15, 13:45–14:15 ET |
| Entry timeframes | 1m–5m |
| Structure timeframes | 5m / 15m; bias on 4H/1H/15m/5m |

**London relevance — larger than the carded videos suggest.** Two distinct things:

1. He consumes **London and Asia session extremes as sweep targets** for NY entries
   `[1cMWnAxElA0 @ 02:07]`; one carded example trades a London-highs sweep `[@ 08:50]`.
2. **He also trades the London session directly.** The full enumeration contains **20**
   London-titled videos naming explicit London macro windows — *"2:45 – 3:15AM ICT LDN
   Macro"* `[-AxipzPSWnY, 94vXrtbjOh4, vzDWnl3hp4M]` and *"3:45 – 4:15AM ICT LDN"*
   `[3ujLL647TG0, Ee_tC5P-F20]`.

**None of the three carded videos cover the London application** — the card is NY-only
because the sources were. A London variant almost certainly exists and is uncarded.
See `research/_shared/session-map.md`.

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

> **⚠️ CORRECTION 2026-08-05d.** An earlier version of this section called the channel a
> highlight reel on the basis that "~40 of ~50 videos are P&L headlines and one shows a
> loss." **That was drawn from the 50 most recent videos only — an 8% sample of a
> 602-video channel — and it is materially wrong.** The full enumeration is below. Recording
> the error rather than quietly editing it.

**Fair on the full sample.** Across all **602** videos:

| category | count | share |
|---|---|---|
| P&L-headline wins (`+$…`) | 121 | 20% |
| loss / breakeven / transparency | **48** | 8% |
| everything else (tutorials, vlogs, mindset) | 433 | 72% |

A ratio of roughly **2.5 wins to 1 breakeven-or-worse** in the *headlines*. That is not a
highlight reel — it is closer to a trading diary.

He publishes things a pure funnel would not:
- *"HOW TO DEAL WITH GETTING COOKED \*FULL TRANSPARENCY\* (im still up on the month)"* `[N1EXytfVsiI]`
- *"How To Take Losses as a Profitable Trader & NEVER Break Routine"* `[3rihdEsRTSQ]`
- Repeated breakeven days, including *"+$0 4TH Breakeven on NASDAQ!"* `[d5EgTViZ0Q4]`,
  *"+$0 CHOPPY BREAKEVEN PM"* `[LcR4MSuKWsg]`, *"+$0 on NASDAQ! Cooked PA"* `[gcX606rYo2k]`
- *"How Trump COOKED an A+ ICT Silver Bullet Long"* `[ZgynHraPzvc]` — a losing setup, named as such

**Remaining caveats, which still stand:**
- The content **is** a funnel: every tutorial closes on Discord subscription, one-to-one
  mentorship, and an Alpha Futures affiliate code with a discount deadline
  `[UBIHB1oB784 @ 09:13]`.
- View counts 46–1,500 — small channel.
- No verified statement of record: no equity curve, no broker statement, no sample size. The
  headline distribution is *consistent with* honesty but does not demonstrate it.
- **In his favour:** `pD5l_gEje9I @ 04:46, 08:30` discloses a live trade underperforming the
  walkthrough (2R → 1R), with the reason given.

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
