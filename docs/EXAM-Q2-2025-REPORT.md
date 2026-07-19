# Q2 2025 EXAM — the pre-registered red-quarter test (run 18 Jul 2026, Angus authorization)

The sacred holdout, run exactly as pre-registered in docs/PROPOSED-AGENT-ADJUSTMENTS-v0.4.md
("THE BAR"): reads scored before P&L, Angus $0=FLAT rule, news-aware ground truth
(output/allyears_daily_books.csv), walk-forward analog blocks, no iteration on the quarter.
Deviation from pre-registration, disclosed: run in FRESH-EYES mode (not sequential) — memory
was measured as a read-drag in June and fresh-eyes is the shipped desk mode. Two arms sat the
same 64-day paper: v0.6 (event-modifier, trades more) and v0.6.1 (analog-anchored, hides more).
128 verdicts, 1 fail-closed (v0.6 cited_evidence >8 items), ~53 min wall-clock, fully parallel.

## The result

| arm | reads (3-way) | binary | FLAT rate | full-size $ | as-verdicted $ | BAR (≥$0) |
|---|--:|--:|--:|--:|--:|---|
| champion switch (mechanical) | 25%* | — | 0% | **−$478** | −$478 | fail |
| agent v0.6 | 42% | 60% | 35% | −$985 | −$179 | **FAIL (barely)** |
| agent v0.6.1 | 48% | 52% | 78% | **+$404** | +$127 | **PASS (thin)** |
| oracle+SD ceiling | — | — | 49% | +$18,735 | — | — |

*champion reads = its implied book choice vs oracle, for comparability.

Monthly, as-verdicted: v0.6 −452/−95/+368; v0.6.1 −114/−172/+414 (June green for both).

## What the exam settles

1. **THE RANKING INVERTED OFF-ERA.** 2026 said v0.6 (19% capture) > v0.6.1 (11%).
   Q2 2025 says v0.6.1 (+$404, PASS) > v0.6 (−$985, FAIL). Pat's "stand-down layer is
   capture-negative" is a 2026-era observation, not a law: in a red quarter the cautious
   config wins and the aggressive one bleeds on wrong-book trades. Any ship decision
   based on 2026 rankings alone would have shipped the wrong agent for the wrong year.
2. **Both agent arms beat the champion in the red quarter** (−$179 and +$127/+$404 vs
   −$478) — the judgment layer's first head-to-head win where it was supposed to win.
   Margins are thin; this is a directional result, not a payday.
3. **The bar is technically PASSED by v0.6.1** (+$404 full-size, +$127 as-verdicted) —
   "maintained profitability where the champion lost," by the letter. By the spirit
   (Angus's 55-60% capture ambition) it is nowhere: 2% capture of an $18,735 ceiling.
   The distinction threshold (≥30% capture ≈ $5.4k) was NOT reached.
4. **The leak class moved again, same lesson.** v0.6.1 left $18.3k of regret, dominated
   by FLAT-on-momentum-winners (18 days) — under-trading; v0.6 left $19.1k dominated by
   wrong-book picks — mis-trading. Neither arm had the R1/R2 timing floor, the base-rates
   block, or the dollar feedback in its briefing (all built, none wired into this exam's
   requests). The capture problem is information-and-mechanics, consistent with every
   measurement since the panel.

## Predictions graded (filed before the run)

- **P7 said**: Q2 2025 PASS, central estimate +$2,500–5,500 (14–30% capture).
  **Outcome: PASS ✓ on the letter (v0.6.1 +$404), magnitude MISS ✗** — actual +$404 is
  ~6x below the low end. The pass/fail call was right; the dollar estimate assumed the
  full v0.5 information bump (feedback + base rates + timing floor), which was not in
  these arms. Graded honestly: half credit.
- **P5's floor** (agent must beat analog-majority baseline): analog majority on these
  63 days reads 44%; v0.6.1 read 48% ✓, v0.6 read 42% ✗.

## What this recommends (for Angus's ruling, not enacted)

1. The live paper stack should NOT quietly stay champion-driven by default: the exam
   says the judgment layer beats the champion off-era even in its current crippled
   state. Keep paper on champion (Pat's parity work is sound) but the go-live gate
   must re-run this exam with the full v0.6.2 stack before any driver decision.
2. v0.6.2 = v0.6.1 posture + the three unwired weapons: R1/R2 timing floor active in
   grading, base-rates block + event-family analogs in the briefing, dollar regret
   feedback per the C2 contract. Then re-sit BOTH papers (2026 whole-year + a fresh
   2023/2024 quarter — Q2 2025 is now spent as a holdout and retires to regression duty).
3. The 30%-capture distinction bar stands as the next target. +$404 keeps the thesis
   alive; it does not fund an account.
