---
date: 2026-08-05
status: TOMBSTONE — CLOSED. Geometry searched, kill earned on the third attempt.
tags: [london, po3, tombstone, geometry, process]
sources: ["output/london_po3_geometry.md", "docs/PREREG-london-po3-geometry.md", "research/candidates/london-po3-ifvg.md"]
---

# TOMBSTONE — can the London pre-open range's failed break be traded profitably? (CLOSED 2026-08-05)

## 1. The question

The pre-open London range (06:00–08:00 London) is broken on 92–93% of days. Those
breaks fail — price closes back inside — on 84–85% of occasions, which beats a
placebo range with no claim on the open by +12pp (2025) and +14pp (2026),
era-consistent. **Can the reversal after that failure be traded for money?**

## 2. Spans consumed, and what was NOT spent

- **Consumed:** 2025-01-01 → 2026-07-15, 1-minute NQ candles. Plus, in earlier
  trials, the tape 2025-06 → 2026-07 and 295 depth days.
- **NOT spent, across all three kill attempts:** the 2023/24 candle span, the six
  sealed months (2023-07/09/11, 2024-03/04/10), and `data/reference/depth_london_2023_24`
  (128 sealed days). **This family died without ever costing the programme a holdout
  look.**

## 3. Whose idea

EzTrades, stated as three components — *time* (the 03:00 ET manipulation), *PO3*
(accumulation → manipulation → distribution), and an *inverse fair value gap* on a
1–3 minute chart as the trigger, *"ideally a V-shaped inverse within a few candles."*
Corroborated on the clock by two independent sources and by our own `LDN-WIN-01`
measurement, which put 03:00 ET as the volume peak of the whole London session in
both eras.

The final calibration was ordered by Angus:

> *"look at all we tested to get the IB fade model shipped, look at all we did to get
> the canon shipped. if u arent testing jack shit and just sending it off, its
> obviously not gonna do well"*

## 4. Engine caveat, stated plainly

§7.1 item 4 asks for the real engine on canon fills. **This was not that.** Every
number in this family — census, L1, conditioning, flow, depth, and this calibration —
comes from the L1-class bar simulator (`scripts/london_obk_l1.py` /
`scripts/london_po3_geometry.py`): 1-minute bars, conservative intrabar tie-break
(stop checked before target), 1pt and 2pt cost stacks, $160 fixed risk. Entry is the
fail bar's **close** and the path starts on the **next bar**, so there is no gap
between decision and simulation — this family does **not** carry the entry-bar-skip
defect that voided `NYA-LVL-01`. That was verified, not assumed.

The candidate never reached a stage where the canon engine would have been run.

## 5. The result

**Geometry grid — 6 stops × 7 targets, all declared before the run, identical event
set in every cell (359 events, 318 sessions).**

| | PF strict, best | PF strict, worst | cells PF>1.0 in both eras |
|---|---:|---:|---:|
| 42 declared cells | 0.97 | 0.63 | **0** |

| best cells | WR | payoff | PF strict | 2025 | 2026 | maxDD $ |
|---|---:|---:|---:|---:|---:|---:|
| `E+F12/FAR` | 29% | 2.36 | 0.97 | 0.89 | 1.10 | 9,401 |
| `E/FAR` | 26% | 2.78 | 0.97 | 0.87 | 1.12 | 13,484 |
| `FIX15/TRAIL` | 42% | 1.27 | 0.91 | 0.94 | 0.86 | 4,045 |
| `E/MID` (as-declared default) | 33% | 1.78 | 0.87 | 0.83 | 0.93 | 16,112 |

**Event universe — widening loses money faster.** Re-entry triples the trade count
(359 → 1,109) and drops PF from 0.87 to 0.77. Extending the window to 11:00 London
adds 13% more trades at PF 0.85. Both together: 1,529 trades at 0.81.

**Prior classes, for completeness.** Flow at entry: 0 of 6 declared features confirmed
in their predicted direction; the pre-declared mechanism variable (`delta_sweep`)
pointed the *wrong* way. Depth at entry: 9 of 32 cells survived every era, exactly 1
paid at strict cost, and it failed its selection-corrected permutation null at
family-wise **p = 0.42**.

## 6. Mechanism — why it fails, not just that it fails

**The premise is true and the payoff is still not there.** The break does fail, and it
fails specifically more often after the pre-open range than after a placebo range. But
the reversal is *shallow relative to what it costs to be wrong*:

- Fading the break requires a stop beyond the sweep extreme, and the sweep extreme is
  set by the very displacement that makes the setup identifiable. **The better the
  signal, the wider the stop.** Median risk 14 pts, p90 39.8.
- The reversal reaches the far edge of the range on ~20% of occasions and the midpoint
  on ~46%. At the far edge you get a 2.4–3.0:1 payoff at a 23–29% hit rate. At the
  midpoint you get 1.5–1.8:1 at 30–37%. **Both multiply out to roughly 0.9.**
- That product is stable across every stop rule tested. Flooring the stop at 12 pts
  (which removes a genuinely awful 19%-WR, PF-0.52 tightest quintile) moves PF by
  ~0.06. Capping it makes things worse, because the cap places the stop inside the
  sweep extreme and the retest takes you out. **The stop was never where the problem
  lived.**

The trade is a fair coin with a fair payoff, and the cost stack is what makes it
negative. There is no geometry that changes the shape of the underlying excursion
distribution — only how you sample from it.

**A correction the run forces:** the source's own far-edge target was **better** than
the midpoint target I substituted after the census. The far-edge family takes the top
three slots and five of the top six. My trial-1 inference — that a ~20% traverse rate
disqualified the far edge — confused hit rate with expectancy, and trial 2 flagged it
without settling it. His geometry beat mine. It still loses.

## 7. Conclusion

**KILLED on expectancy, after a complete declared search across all three variable
classes** — geometry (42 cells), flow at entry (6 features), depth at entry (32 cells
plus its null). The kill condition was written into
`docs/PREREG-london-po3-geometry.md` §6 before the run and it fired exactly as
declared.

**The measured premise survives the candidate** and belongs to whatever uses the
London pre-open range next: 92–93% break rate, 84–85% failure rate, **+12/+14pp over
a placebo range, era-consistent, z = 3.43 / 2.94.**

## 8. Reopening burden

This family reopens only on **one** of:

1. **A new variable class, not a new arm inside an existing one.** In-trade flow
   (flow state *during* the trade, per §5.12.5 — the canon's evidence says flow is
   near-worthless at entry and decisive inside the trade) is the one declared class
   never run here, and it is the only cheap reopening path. It needs its own prereg
   and its own null.
2. **A mechanically-defined arm A (IFVG).** Still barred — *"a V-shaped inverse within
   a few candles"* is not a definition, and any definition written now would be
   written after seeing this data.
3. **ES data enabling the SMT-divergence confluence**, which was dropped for data
   reasons and never tested. That is a genuinely untested part of the as-taught spec.
4. **A triple-era result at least as strong as this grid is weak** — i.e. an
   independent sample showing PF > 1.0 at strict cost in every era at some geometry,
   pre-declared.

**Three kills, zero holdout looks.** Nothing about reopening this costs the programme
a sealed span, which is the one thing that stayed disciplined throughout.

## 9. Artifacts

- `docs/PREREG-london-po3-geometry.md` — the grid, the objective, the promotion rule
  and the kill condition, all committed before the run
- `scripts/london_po3_geometry.py`
- `output/london_po3_geometry.md`, `output/london_po3_geometry.parquet`
- `research/candidates/london-po3-ifvg.md` — full trial history, trials 1–4
- `output/trial_ledger.parquet` — 46 rows from this trial; 144 for the family

## 10. The process finding, which outlives the candidate

**This family was killed three times and only the third kill was legal.** Kill 1 ran
the weakest variable class (flow at entry) at the weakest moment and called it
decisive. Kill 2 closed one of five named gaps and declared the search "genuinely
complete" while the same document listed stop caps as un-run. Kill 3 tested the
arithmetic and earned it.

**The pattern in kills 1 and 2 is the same one that produced the bugs in `NYA-LVL-01`:
declaring completeness that had not been reached.** There, it made results look better
than they were; here, it made a candidate look deader than it had been shown to be.
Both are the same error — asserting that a question is closed because I stopped
asking it.

**The counter-rule, and it is cheap:** before writing "the search is complete", diff
the candidate against the §5.11 checklist item by item and paste the table into the
verdict. LDN-PO3-01 would have scored 2 of 9 in writing, and neither premature kill
would have been written.
