---
videoId: pMv3USznFdU
title: "Powell - Entry triggers (E7 course)"
date: 2026-04-19
duration: 9m06s
source_channel: "Archive Vault (re-host of the E7 course)"
views: 1597
trader: Powell
prefix: zxck-
GAP_ENTRY: YES — 1-minute IFVG is one of the three inner triggers
NY_SESSION: YES — 10:00 ET open present in both examples
---

# E7 entry triggers — what's INSIDE a rejection block. The displacement rule.

## The problem it solves
> *"when I go from the 5-minute and I see that we have a rejection block here — how big is this?
> This is too big. This is 35 points. So it's too big to just enter off the start of it and have
> your stop loss at the low."* `[pMv3USznFdU @ 01:09]`

**A stated size threshold behaviour: at 35 points the start-of-wick entry is abandoned for the
CE.** `[@ 01:33]`

## THE THREE INNER CONFLUENCES — `[stated]`
Scale down inside the 5-minute rejection block and look for, on the 1-minute:
1. a **1-minute rejection block**
2. a **1-minute inverse FVG**
3. a **1-minute CISD**
`[@ 02:43]`

## THE DISPLACEMENT RULE — the best diagnostic in the corpus
> *"these rejection blocks often look the same, and this is how you can differentiate between
> what's a good one and what's a bad one. The good rejection blocks on the 5-minute, if you scale
> down into the 1-minute, you'll have this one big candle that gives you three entry triggers on
> lower time frame, all in one candle. And that is just called displacement."* `[@ 06:39]`

**A good 5-minute rejection block contains ONE 1-minute candle that is simultaneously a rejection
block, an inverse FVG and a CISD.** That is a fully mechanical detector and it is his own
good/bad discriminator — the thing every other video gestures at.

## A REJECTION BLOCK HE REFUSES — the equal-highs case
> *"this is an example of a 5-minute rejection block that I would not take because we do have
> relative equal highs… this would actually have needed to sweep that liquidity for me to even
> consider taking this."* `[@ 05:04–05:51]`

**This clarifies the apparent conflict with the third-party video**: equal highs that have NOT
yet been swept are a reason to wait, not fuel. Once swept, they become the engineered liquidity.
`[stated by Powell, so this resolves it — see 9NDGx9MYuXw's note.]`

## Limits vs triggers
> *"some of you swear by limits, some of you swear by entry triggers. I use both. They perform
> well in different scenarios. Yesterday I used a one-minute entry trigger because we were so
> close to market open. So I just wanted some confirmation."* `[@ 08:10–08:33]`

**Stated selection rule: use a trigger near the open, a limit otherwise.**

## Timestamped index
| time | moment |
|---|---|
| 01:09 | **35 points is too big for a start-of-wick entry** |
| 01:33 | *"the CE is often times going to be the best option"* |
| 02:43 | **the three 1-minute inner confluences** |
| 03:07 | a mitigated 1-minute rejection block inside is a good sign |
| 03:31 | CE hit on first tap, IFVG on the second |
| 05:04 | **a setup refused because equal highs were unswept** |
| 06:39 | **THE DISPLACEMENT RULE — one candle, three triggers** |
| 07:24 | applies on 15-minute too |
| 08:10 | **limits vs triggers: trigger near the open** |

## Candidate strategies introduced
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-displacement-rb` | **Displacement-validated rejection block** | Take only 5m rejection blocks containing a 1m candle that is simultaneously a rejection block, an inverse FVG and a CISD | **YES** |

## Grounding notes
- **`zxck-displacement-rb` is the highest-value new mechanic in the entire ingest.** It converts
  his good/bad judgement into three checkable conditions on one candle, and it resolves the
  equal-highs conflict at `[@ 05:04]`.
- Note the parallel to `ash-unicorn-sb`'s F1: both traders' quality gate reduces to *"was the
  move displacement or was it hollow"*. Different measurement, same question.
