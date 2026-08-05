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
*Caveat:* `ash-unicorn-sb` itself does **not** require the macro windows `[@ 01:26]`, so a
null here would not falsify this card — it would falsify the channel's marketing framing.

— added by ash10hazard-analyst, 2026-08-05
