# Cross-strategy correlations

Append-only. Each entry: the ids, the component(s), relationship type, the condition it
holds under, and a testable hypothesis.

---

**2026-08-05 — `ash-unicorn-sb` × existing London validation work** — added by ash10hazard-analyst

Not a strategy-to-strategy pairing yet (only one card exists), but recording the overlap
against measured results so nobody re-tests settled ground:

| component | related prior measurement | relationship |
|---|---|---|
| `liquidity-sweep` (session extremes) | `docs/VERDICT-LDN-SWP-01.md` — Asia-range sweep, null after a circularity fix | **Redundant-adjacent.** His sweep targets include Asia/London highs; ours tested Asia-range sweeps in London. Different session, same component family. |
| `momentum-shift` + `fvg-fill` | none | **Untested.** No prior work on FVG entries or structure shifts in this repo. |
| `order-block-tap` | none | **Untested**, and not specifiable from source `[@ 05:47]`. |
| `session-timing` (macro windows) | none | **Untested.** See hypothesis below. |

**Testable hypothesis H1 (cheap, non-circular, no strategy required):**
Price behaviour inside the fixed macro windows (09:45–10:15, 10:45–11:15, 11:45–12:15,
13:45–14:15 ET) differs measurably from the rest of 09:30–14:15 — in realised range, volume,
or directional persistence.
*Why it is worth running first:* the clock times are declared by the framework in advance,
so testing them is not circular; it needs no strategy and no outcome selection; and it
underpins every ICT-derived candidate, not just this card.
*Caveat (⚠️ SUPERSEDED 2026-08-07):* this said `ash-unicorn-sb` does **not** require the macro
windows `[@ 01:26]`. **That citation was formally superseded in card rev d** — the macro is a
MANDATORY gate: *"Even if it's 1 minute outside, you should not take that trade"*
`[qngA8aIfV0M @ 03:48]`. The H1 logged below (macro-window behaviour vs rest-of-session) was
never run. Original text kept for the record: `ash-unicorn-sb` itself does not require the
macro windows, so a
null here would not falsify this card — it would falsify the channel's marketing framing.

— added by ash10hazard-analyst, 2026-08-05

---

**2026-08-05 — `ash-unicorn-sb` internal component notes after 3 videos** — added by ash10hazard-analyst

Recording component quality for future recombination, now that the card is at rev c:

| component | quality as a graftable part | note |
|---|---|---|
| `liquidity-sweep` | **strong** — fully specifiable | 5m/15m levels + session extremes; the "internal level" gate is the only soft edge |
| `multi-tf-alignment` (bias) | **strong** — newly specifiable | 4H/1H/15m/5m imbalance alignment `[UBIHB1oB784 @ 01:07]`. A clean, portable bias filter that could be grafted onto any directional model |
| `fvg-fill` (entry) | **strong** | 3-candle pattern, mechanical |
| `momentum-shift` | **medium** | needs a swing definition we supply |
| `structure-stop` + BE at 50% | **strong** | break-even at 50% of entry→TP is his most consistently stated rule, confirmed in all 3 videos |
| `order-block-tap` | **weak — do not graft** | identification never specified |
| trailing / `runner` | **weak — do not graft** | stated then overridden in all 3 videos; he says his own rule would have lost the demonstrated trade `[UBIHB1oB784 @ 07:40]` |

**Graft candidates for the team:** his **bias filter** and his **break-even-at-50%** rule are
the two cleanest, most portable pieces. Both are fully specified, both are independent of the
ICT framing, and both could be tested as standalone modifications to an existing strategy.

**Do not graft** the order-block or trailing components — they are judgement, not rules.

— added by ash10hazard-analyst, 2026-08-05
