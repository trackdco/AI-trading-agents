---
videoId: 4COROwkO3DI
title: "Powell strategy live trade execution (1:7RR)"
date: 2025-10-21
duration: 7m23s
source_channel: "Powell trades (OWN)"
views: 125055
trader: Powell
prefix: zxck-
GAP_ENTRY: YES — entry off a 4-hour gap
NY_SESSION: YES — 10:00 ET key open used as the entry
---

# Live execution — a 4-hour gap + 10:00 key open trade, narrated in real time

## What makes it valuable
**A live, unedited execution** rather than a replay. Shows the decision process, including a
live SMT check on ES that changes his exit.

## THE SETUP — `[stated]`
- Delivering off a **4-hour gap** `[4COROwkO3DI @ 00:27]`
- Draw: all-time high, with relative equal highs `[@ 00:53]`
- Entry: **the 10:00 ET key open** — *"I want to use this 10 a.m. key open as an entry"* `[@ 05:38]`
- **Original stop 10 points**, giving 1:7; trailed to 5 points, then break-even `[@ 02:27–03:18]`

## THE LEG-SELECTION RULE — the reason he waited
> *"we just didn't really tap into the 4-hour gap here. We kind of left equal lows, which not
> really a big fan of. So, when we come back down, we sweep those equal lows into the gap. Way
> better setup."* `[@ 02:05]`

**Equal lows left behind = a reason to wait for the sweep, not to enter.** That is a stated,
testable entry condition.

## THE SMT EXIT RULE — `[stated]`, and it is a live decision
> *"let's add ES onto here so that we know if there's an SMT. There is… ES is almost about to
> take out this high, which is not great for my trade… if we have an SMT, you can trail
> aggressively or just close full position."* `[@ 03:41–04:27]`
He then closes on the ES break `[@ 05:13]`.

**SMT is used as an EXIT signal here, not just an entry filter.** New, and it needs ES data.

## Management philosophy
> *"Consistency is always going to beat home runs and greed."* `[@ 01:16]`
> *"my TP is like a relative equal high, so should be pretty easy target there. Low hanging
> fruit. The runner would obviously be all-time high."* `[@ 04:27]`
> *"real trading is pretty boring."* `[@ 04:51]`

## Timestamped index
| time | moment |
|---|---|
| 00:04 | trailing to the most newly formed low |
| 00:27 | the 4-hour gap is what he is delivering off |
| 01:39 | *"I have five points of risk. I don't really care. That's like $200"* |
| 02:05 | **leg selection — wait for equal lows to be swept into the gap** |
| 02:27 | **original 10-point stop = 1:7** |
| 03:41 | **live ES SMT check** |
| 04:27 | SMT ⇒ trail aggressively or close |
| 05:13 | closes on the ES high break |
| 05:38 | **10:00 key open as the entry; 4H gap as the POI; ATH as the target** |
| 06:24 | why this leg and not the earlier one |

## Candidate strategies
| id | name | one line | gap-entry? |
|---|---|---|---|
| `zxck-smt-exit` | **SMT-divergence exit** | Close or aggressively trail when ES breaks the level NQ has not | no |

## Grounding notes
- `zxck-smt-exit` **needs ES 1-minute data, which we do not hold.** Same blocker as
  ash10hazard's ES leading trigger. Two independent traders now require ES; that raises the
  value of sourcing it.
