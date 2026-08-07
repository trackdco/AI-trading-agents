# Glossary — normalized terminology across traders

Canonical term first; each trader's word for it mapped to it. Use canonical **component
tags** on cards so the same concept matches across traders even when their words differ.

| canonical | ash10hazard's term | notes on his usage |
|---|---|---|
| `liquidity-sweep` | "sweep", "sweep of buy-side / sell-side liquidity" | Broader than the textbook: he accepts **internal** 15-min levels, not just swing points, "if it's clear where price is drawing to" `[1cMWnAxElA0 @ 01:48]` — an undefined gate |
| `momentum-shift` | "shift in market structure", "MSS" | Requires it on **both NQ and ES** `[@ 05:26]` |
| `fvg-fill` | "fair value gap", "gap", "imbalance" | Entry is the *fill* of the FVG `[@ 05:47]` |
| `order-block-tap` | "order block", "inverse order block" | Identification method never specified `[@ 05:47]` |
| `session-timing` | "macro", "PM macro", "AM macro" | Named 30-min windows; he treats them as **confluence, not a filter** `[@ 01:26]` |
| `structure-stop` | "stop at the recent swing high/low" | Variant at "two previous swing highs" with undefined trigger `[@ 06:09]` |
| — | "draw on liquidity" | His term for the target/magnet level; no canonical tag yet |
| — | "PD arrays" | Used once `[1cMWnAxElA0 @ 03:59]`, never defined |
| — | "breakaway gap" | An FVG left behind by the displacement leg itself. He claims *"it's very low probable that price actually returns to a breakaway gap"* `[UBIHB1oB784 @ 04:53]`. Distinct from the entry FVG. |
| — | "SMT" | Divergence between NQ and ES on a swept level — one sweeps, the other does not. **Explicitly optional** `[pD5l_gEje9I @ 01:46]` |
| — | "mitigation block" / "breaker block" | Both are inverted order blocks; which name applies depends on whether the previous short-term high/low was swept `[pD5l_gEje9I @ 00:42, UBIHB1oB784 @ 01:07]` |
| `multi-tf-alignment` | "bias" | Specifically: trading out of a gap in the same direction on 4H, 1H, 15m and 5m `[UBIHB1oB784 @ 01:07]` |

— added by ash10hazard-analyst, 2026-08-05

---

## Powell (zxcked) — terminology, mapped to canonical tags

Where his word differs from ash10hazard's for the same object, both point at one canonical term
so the two traders stay comparable.

| canonical | Powell's term | ash10hazard's term | notes on Powell's usage |
|---|---|---|---|
| `liquidity-sweep` | "sweep", "manipulation", "Judas", "inducement" | "sweep" | "Inducement" is specifically a fake move *engineering* the stops he then sweeps `[55KRVFLqzwA @ 00:48]` |
| `fvg-fill` | "imbalance", "gap", "fair value gap", "inefficiency" | "fair value gap", "gap" | **Enters the FAR edge on a gap fill** `[86DOt135Wts @ 00:50]` — the opposite side to ash10hazard's near-edge entry |
| `order-block-tap` | "order block" | "order block" | Validated by an imbalance INSIDE it `[lRgsHGWzO9E @ 01:13]` — ash never specifies identification at all |
| `momentum-shift` | "CISD", "change in state of delivery" | "MSS", "market structure shift" | **Not the same object.** His CISD = close beyond a candle's OPEN, then retest that open `[0u1L00q77bw @ 02:16]`. Ash's MSS = a break of a swing extreme. Do not map one onto the other without care. |
| `session-timing` | "key open" | "macro" | Powell's are **price levels at a time** (10:00, midnight, 18:00, 09:30, 13:00); ash's are **30-minute windows**. Both are time-anchored, but one is a line and one is a box. |
| `structure-stop` | "below the rejection block" / "cover the PD-array midpoint" | "recent short-term low" | Powell sizes the stop to the PD array itself `[xae9AiV5Ps4 @ 06:51]` |
| `multi-tf-alignment` | "top down analysis", "bias" | "bias" | Powell's aggregation IS stated (daily → 4H → 1H); ash's is not |
| `smt` | "SMT", "divergence" | "SMT" | Powell uses it as an **exit** too `[4COROwkO3DI @ 03:41]`; ash only as an optional entry filter |
| — | **"rejection block" / "wick CE"** | — | **No ash10hazard equivalent.** A wick that swept liquidity and closed against itself; entry at its 50% (CE), start, or 25%. **NOT the ICT rejection block** — he requires a directional candle CLOSE and says so while rejecting the ICT definition `[a3LzCUZU5ko @ 01:34]`, `[AGmRZ9Te9NY @ 03:11]` |
| — | **"engineered liquidity"** | (implicit in "sweep") | Equal highs/lows are the best form `[rzfgAEYhxCg @ 04:51]`. **The only gate in either corpus with a number: must sit >2 points from the CE** `[xae9AiV5Ps4 @ 02:16]` |
| — | **"displacement"** | (our `F1_disp_delta` measures the same idea) | One 1-minute candle that is simultaneously a rejection block, an inverse FVG and a CISD `[pMv3USznFdU @ 06:39]`. **His price-only version of the question our order-flow F1 asks with delta.** |
| — | "PXH / PXL" | — | Previous day/session high & low, run as a state machine `[jBS22-pX3dU @ 00:23]` |
| — | "NWOG / NDOG" | — | New week / new day opening gap. *"The most powerful PD array there is"* `[jBS22-pX3dU @ 05:34]`; unfilled = sufficient bias on its own `[AGmRZ9Te9NY @ 01:12]` |
| — | "data high / data low" | — | The high and low of the news reaction. Whichever is taken first, the other is the draw `[c15YLeAKc2A @ 00:00]` |
| — | "MMXM", "V-shape / A-shape" | — | Market maker model; **bias only**, entries delegated to LTF PD arrays `[asi9nTJywN4 @ 01:13]` |
| — | "CE" | — | Consequent encroachment = the 50% of a wick or gap. Used constantly and never spelled out. |
| — | "OTE" / "golden pocket" | — | Fib 0.62–0.79 `[6opmiyFvJBA @ 01:54]`; 0.79 is *"the most premium"* and beyond it is overextended `[xae9AiV5Ps4 @ 08:03]` |
| — | "soup" | — | His verb for taking an entry at a level (from "souping" = sniping). Appears throughout; no technical content. |

### ⚠️ One unresolved conflict, recorded not resolved

**Equal highs/lows near the entry.** Powell treats them as the best engineered liquidity
`[rzfgAEYhxCg @ 04:51]`; a third-party video in the same playlist treats them as a
disqualifier `[9NDGx9MYuXw @ 01:32]`.

**Powell resolves it himself**, and his version is the one to use: unswept equal highs are a
reason to WAIT — *"this would actually have needed to sweep that liquidity for me to even
consider taking this"* `[pMv3USznFdU @ 05:04]`. Once swept, they become the fuel. The third-party
framing is not wrong so much as describing the pre-sweep state.

— added by zxcked/Powell ingest, 2026-08-07
