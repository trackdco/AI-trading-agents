# FINDINGS — RACE OUTCOMES, first look. REPORT-ONLY.

2026-08-08. Declaration `docs/DECLARATIONS-race-outcomes.md`, committed
before the run (`313e887c`). Entry gate: **T1 flatten PASS (20 probes,
0 bad, 17 moved)**. Calibration vs the census parquet: **exact** — 4,121
outcome rows vs 4,123 census rows, the 2-row gap fully accounted by
counted gap-through-stop exclusions, zero rows on either side otherwise.
Book: **2,227 fights, 7.60/day** at X=0.5W. ~40 CI-carrying numbers, no
declared bar — at 95% expect ~2 false "clears" per side; everything
below is a base rate.

## THE HEADLINE

**Mechanized, the race population does not price. No cell clears a
day-boot CI on the positive side — anywhere.** The pooled cost view:

| @cost | M1 (15m MA) | M2 near | M3 near |
|---|---|---|---|
| 0.5pt | −0.025 | −0.085 | −0.108 |
| 1.0pt | −0.063 | −0.141 | −0.165 |
| 1.5pt | −0.100 | −0.196 | −0.222 |

Five cells clear on the NEGATIVE side, and they are not random — they
concentrate in one shape:

- **M2-long is systematically bad**: NY_PRE near **−0.387
  [−0.576,−0.189]** and far **−0.722 [−0.908,−0.537]** (the worst cell
  in the family), LONDON near −0.262 [−0.460,−0.047], NY_AM the only
  window where it doesn't clear (and its point estimate is the cell's
  best, +0.088). Buying upside continuation off this trigger has been
  negative expectation across the fit span.
- NY_AM M3 long far (−0.269) and M3 short near (−0.173) also clear
  negative — the NY_AM continuation family is thin-margin at best.

Best positive point estimates — NY_PRE M2-short near +0.324, NY_PRE
M3-long far +0.326, NY_AM M2-long far +0.216, LONDON M1-long +0.233 —
**all span zero**. Full per-window tables are in the run log
(`scripts.race_outcomes`); windows never pooled.

## TWO STRUCTURAL FACTS THE TABLES EXPOSE

**1. The stop and the target live on different scales, and London shows
it worst.** Stops come from the winning trigger candle (median risk:
1m 10.2pt, 2m 15.5pt, 3m 18.5pt — the Law-2 flag applies to any cross-TF
comparison), while targets live on W15-scale structure. In LONDON M1 the
15m MA sits a median **4.4–5.0R away** — a 22–35% hit-rate lottery
geometry. The same trade in NY_AM is a 1.2–2.0R target at 44–50%. Same
grammar, completely different trade, purely because W15 dwarfs a 1m
candle in London.

**2. The population's excursion tail is modest.** MFE p50 0.39–0.64R,
p90 2.35–3.07R, P(≥2R) 13–20% — lighter than every previously censused
family (the old confluence population ran p90 3.5–4.5R). A quarter of
M2/M3 entries never move 1 tick in favor (p25 = 0.00R). The
first-closure race, by construction, enters as late as the move's
confirmation allows; what's left after entry is the residue.

## WHAT THIS MEANS, stated plainly

The trade check showed the redeclared grammar **finds the trader's
trades** (2 of 2 that were findable under his own declared lines). This
pass shows the grammar's full population, traded mechanically at
next-1m-open with candle stops and structure targets, **carries no edge
of its own** — it is fairly priced to slightly negative, like every raw
mechanism this programme has censused (the standing principle since the
level-family census). Two gaps between the census and the trader's
practice are on the record and unpriced here:

1. **Selection.** The census fires ~7.6/day; he took ~1.3/day on the
   screenshot days — roughly one in six. Whatever he is conditioning on
   when he passes on five of six valid triggers is exactly the part not
   in the grammar yet, and on this evidence it is where the entire edge
   would have to live.
2. **Entry timing.** He market-orders ahead of the closure (T1: ~27pt
   better than the construction on a ~15pt-risk trade — roughly 1.8R of
   entry difference on that single fill). The census prices the
   patient, mechanized version; his fills are structurally earlier.

Neither observation licenses a parameter change by itself. The three
declared lines the trade check surfaced (0.5W displacement floor, 10:30
window edge, MA-exclusive affirmation count) plus any selection layer
are the trader's declarations to make; each would then be tested against
this census as the null, not against hope.

Standing: fit-only, no holdout exists for this family (forward data is
the only out-of-sample), report-only, nothing adopted, nulls published.
