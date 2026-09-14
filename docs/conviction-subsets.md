# SPECIFIC-SUBSET SEARCH — do particular pairs/triples of order-flow/depth signals mark a better sub-population?

**Question.** BR-94 settled that individual flow/depth signals are chance-level
selectors. A separate pass is counting stacked agreement (`cc_*`). This pass
asks the narrower, specific-combination question the trader actually asks at
the moment of entry: *"CVD agrees, AND there's a wall, AND nothing's opposing
me — is THAT sub-population better?"* — for every pair and triple of the 18
signals in `scripts/conviction_lib.py`, in every session x mechanism cell,
checked against a calibrated null before anything is believed.

**Bottom line up front: no.** One cell out of nine clears its null on both
win% and EV; it is exactly what a 9-cell, 8,721-test search is expected to
throw up by chance (~0.82 cells expected), and its own confidence interval
crosses zero. Every other cell's best-looking result is beaten by the
majority of pure-noise searches of identical size. **Nothing survives.**

Code: `/tmp/claude-0/.../scratchpad/subset_search.py`,
`subset_analyze.py`, `subset_deepdive.py`, `subset_clean.py` (session-scratch,
not committed). Read-only on `output/htf_ma_census/race_wide.parquet`; no
parquet touched.

---

## 1. SEARCH SPACE — exact size, exact enumeration

- **Signals:** all 18 `s_*` columns from `conviction_lib.ALL_SIGNALS`
  (12 flow + 6 depth), computed with **global medians** — `signals(load())`
  called on the whole book, per the task's own template, *not* re-derived per
  cell. `s_closeloc`/`s_rangex` are LAW-2-flagged (risk-coupled, BR-43) and
  are **included** in the primary space (matching the template exactly) but
  every top result is checked below for whether it leans on them, and the
  whole search is re-run on the 16-signal LAW-2-clean subspace as a
  robustness check (§5).
- **Subsets:** every combination of size 2 and size 3 from the 18 signals —
  C(18,2) + C(18,3) = **153 + 816 = 969 subsets**. A candidate's
  sub-population is the rows where **every** signal in the subset reads
  exactly 1.0 (agreement); NaN (unavailable) fails the same as disagreement,
  so availability gates are enforced automatically.
- **Cells:** the 9 (session x mech) cells — LONDON/NY_PRE/NY_AM x M1/M2/M3.
  Every candidate is scored **only inside its own cell**; nothing pooled
  across session or mechanism, matching the standing rule.
- **Total attempted:** 969 x 9 = **8,721 (subset, cell) tests**, enumerated
  exhaustively (no sampling).
- **Population floor, applied before any ranking:** n >= 25 fights **and**
  >= 15 distinct `sess_day`. This removed 30–41% of attempts per cell
  (557–698 of 969 survived the floor — depth wall signals are ~40% available,
  so triples that lean on `s_wall_sz`/`s_wall_near` shrink hardest).
- **Null:** `conviction_lib.permute(B, seed)` — outcome shuffled within each
  (session, mech) cell, signals and cell sizes untouched — run at **10 seeds**
  (91001–91010). Because permutation never touches the signal columns, the
  set of subsets that clear the n/day floor is **identical between real data
  and every permutation** — only each candidate's win%/EV can move. That
  makes the real-vs-null comparison apples-to-apples by construction.
- **Total evaluations:** 8,721 attempted x 11 (1 real + 10 null) = **95,931**.

## 2. BEST REAL SUBSETS (per cell — never pooled), best-on-EV and best-on-win%

Dual currency, Law 3. n/days are the sub-population size; CI is
`dboot_mean` (day-clustered, 2,000 draws) on that exact subset's `out`.
Signal names below drop the `s_` prefix (`d30` = `s_d30`, `sup_res` =
`s_sup_res`, etc. — full names in `conviction_lib.ALL_SIGNALS`).

| session | mech | best-EV subset | n | days | win% | EV | 95% CI |
|---|---|---|---:|---:|---:|---:|---|
| LONDON | M1 | d30 + rangex⚑ + sup_res | 25 | 19 | 52.0 | +0.625 | wide, n at floor |
| LONDON | M2 | no_opp + wall_sz + wall_near | 27 | 16 | 63.0 | +0.379 | — |
| LONDON | M3 | d30 + rangex⚑ + wall_sz | 31 | 18 | 51.6 | +0.197 | — |
| NY_PRE | M1 | volx + eff + thick | 29 | 27 | 51.7 | +0.738 | (−0.01, +1.53) |
| NY_PRE | M2 | d5 + no_opp + wall_sz | 25 | 21 | 28.0 | +0.367 | — |
| NY_PRE | M3 | d15 + no_opp + dep_imb | 25 | 19 | 48.0 | +0.709 | — |
| NY_AM | M1 | d5 + sup_res + thick | 38 | 29 | 50.0 | +0.458 | — |
| NY_AM | M2 | d15 + cvd + dep_imb | 30 | 19 | 86.7 | +0.491 | (+0.12, +0.86) |
| **NY_AM** | **M3** | **eff + wall_sz + thick** | **32** | **23** | **78.1** | **+0.396** | **(−0.03, +1.02)** |

⚑ = LAW-2 risk-coupled feature (closeloc/rangex) in the winning subset —
already a reason to discount that cell's "best" before the null test even
runs (BR-43: these move mechanically with realised risk, not independently).

**NY_PRE-M1's +0.738 is the single highest EV in the entire 8,721-slot
search**, pooled across every cell. Held up against its own null next.

By win%, the standout numbers are NY_AM's three mechs (77–87%) and LONDON-M1
(57%) beating all 10 of their own nulls — addressed in §4, because win% alone
is exactly the metric Law 3 warns is misleading.

## 3. BEST-OF-NULL DISTRIBUTION — the decisive section

For each cell, the same 969-subset search was re-run on 10 permutations and
the **best (max) EV / win%** recorded from each — the honest comparison,
because it compares "best of 969" against "best of 969," not a hand-picked
winner against a distribution it was never a candidate in.

**EV — real best vs. null best-of-10:**

| session | mech | real best EV | null EV: mean±sd (min–max) | nulls >= real |
|---|---|---:|---|---:|
| LONDON | M1 | +0.625 | 0.809 ± 0.077 (0.699–0.931) | **10/10** |
| LONDON | M2 | +0.379 | 0.464 ± 0.217 (0.069–0.834) | 7/10 |
| LONDON | M3 | +0.197 | 0.520 ± 0.173 (0.306–0.830) | **10/10** |
| NY_PRE | M1 | +0.738 | 0.959 ± 0.374 (0.513–1.752) | 6/10 |
| NY_PRE | M2 | +0.367 | 0.729 ± 0.409 (0.237–1.614) | 7/10 |
| NY_PRE | M3 | +0.709 | 0.660 ± 0.197 (0.360–0.953) | 4/10 |
| NY_AM | M1 | +0.458 | 0.550 ± 0.140 (0.321–0.743) | 7/10 |
| NY_AM | M2 | +0.491 | 0.438 ± 0.154 (0.268–0.704) | 3/10 |
| **NY_AM** | **M3** | **+0.396** | **0.204 ± 0.092 (0.070–0.356)** | **0/10** |

Pooled ("the whole 8,721-slot search's single best result", real vs. each
null's own whole-search best): **real = +0.738 (NY_PRE-M1)**; null
best-of-whole-search = **1.145 ± 0.325 (0.730–1.752)** — **9 of 10 null
searches produced a better number than the best result anywhere in the real
search.** The single most attractive-looking real subset, out of 8,721
attempts, is worse than what noise alone typically produces at this budget.

**win% — real best vs. null best-of-10** (for completeness/dual-currency,
not the deciding metric — see §4):

| session | mech | real best win% | null win%: mean±sd (min–max) | nulls >= real |
|---|---|---:|---|---:|
| LONDON | M1 | 57.1 | 46.9 ± 3.9 (40.6–53.8) | **0/10** |
| LONDON | M2 | 63.0 | 57.4 ± 6.1 (48.5–66.7) | 3/10 |
| LONDON | M3 | 60.7 | 61.1 ± 3.9 (56.0–68.0) | 6/10 |
| NY_PRE | M1 | 53.8 | 51.3 ± 5.2 (42.3–60.0) | 3/10 |
| NY_PRE | M2 | 44.0 | 51.3 ± 4.0 (45.5–56.8) | 10/10 |
| NY_PRE | M3 | 53.8 | 57.1 ± 4.5 (48.6–65.5) | 8/10 |
| NY_AM | M1 | 77.4 | 58.5 ± 4.9 (50.0–66.0) | **0/10** |
| NY_AM | M2 | 86.7 | 76.9 ± 5.0 (71.1–85.2) | **0/10** |
| **NY_AM** | **M3** | **78.1** | **70.3 ± 3.5 (65.6–76.9)** | **0/10** |

## 4. VERDICT

**On EV — the currency that decides whether a subset is worth trading — the
real search beats its calibrated null in 1 of 9 cells (NY_AM-M3).** Under
the exchangeability the permutation test guarantees, a cell's real result
"beating all 10 nulls" has an ~1-in-11 (9.1%) chance under a true null;
across 9 independent cells the expected count is 0.82, and P(observing >= 1)
= 56% — **finding exactly one is unremarkable.** The pooled whole-search
comparison is more damning still: the single best EV anywhere in the real
8,721-test search (+0.738) is beaten by 9 of 10 equal-sized pure-noise
searches.

**On win% alone, 4 of 9 cells beat all 10 nulls** — more than the ~0.82
expected by chance (binomial P(X>=4 | n=9, p=1/11) ≈ 0.6%). This looks
striking in isolation, which is exactly why Law 3 forbids reading win% on its
own: **90 of the 5,520 real qualifying candidates (1.6%) post win% >= 65%
with EV <= 0** — e.g. `s_cvd+s_deltaz+s_rangex` in NY_AM-M2, n=58/38 days,
win% 75.9%, **EV −0.002**. High win rate with flat-to-negative EV is baked
into this search's own noise floor, not a special property of the 4 cells
that cleared it. Three of those four win%-winning cells (NY_AM x3) *also*
carry positive, cell-plausible EV for the identical subset — the fourth
(LONDON-M1) does not clear EV against its null (10/10 nulls beat it) — so
win%-only clearance is not treated as a finding anywhere in this report.

**The one subset that clears both currencies against the null in the same
cell** is NY_AM-M3's `s_eff + s_wall_sz + s_thick` (efficiency-vs-median AND
big support-wall AND above-median depth thickness): 0/10 nulls beat it on
EV, 0/10 beat it on win%. It does not use a LAW-2-flagged feature. It is also
the **only** result that survives when the search is re-run on the 16-signal
LAW-2-clean subspace (§5) — same subset, same 0/10.

**It still fails on its own terms.** n=32, days=23 — barely above the floor.
Its 95% day-clustered CI is **(−0.033, +1.017)** — the interval **includes
zero**. And it is 1 of 9 cells in a search where ~0.82 such clean sweeps are
expected from noise alone; observing 1 is not distinguishable from that
expectation (§ above). A pre-registered method that treats "beats a 10-draw
null and has a CI that still crosses zero" as a discovery would be exactly
the kind of overclaim BR-97 exists to prevent.

**VERDICT: the real winners do not exceed the null's best-of distribution.
The search found nothing.**

## 5. Robustness check (not required, run for due diligence)

Re-ran the identical method on the 16-signal LAW-2-clean subspace (excludes
`s_closeloc`, `s_rangex`): C(16,2)+C(16,3) = 680 subsets x 9 cells = 6,120
tests, 10 more permutations. Result is unchanged cell-for-cell: **NY_AM-M3's
`s_eff+s_wall_sz+s_thick` is again the only cell at 0/10 nulls beating real
on EV** (+0.396 vs null 0.200 ± 0.092, range 0.070–0.356); every other cell's
best-EV subset is again beaten by 3–10 of its 10 nulls. Dropping the
risk-coupled features changes which subset tops a few cells (e.g. LONDON-M1's
winner switches from a `rangex`-containing triple to `no_opp+eff+thick`) but
changes no cell's pass/fail outcome. The one-cell result is stable to this
variant; the null verdict is stable to it too.

## 6. Winner's-curse illustration (why "best-of-969-vs-null-best-of-969" is
the only fair test, not "this subset vs. its own null")

Testing each cell's real-best subset against **that same fixed subset's own**
null distribution (i.e., what a p-hacker would report) makes every single one
of them look decisive — because the subset was hand-picked FOR being extreme
in the real data:

| subset (cell) | real EV | this-exact-subset's null EV (10 perms) |
|---|---:|---|
| eff+wall_sz+thick (NY_AM-M3) | +0.396 | mean −0.195, range (−0.32, +0.10) |
| d15+cvd+dep_imb (NY_AM-M2) | +0.491 | mean −0.095, range (−0.34, +0.11) |
| volx+closeloc+wall_near (NY_AM-M1) | +0.436 | mean −0.066, range (−0.26, +0.14) |
| thru_delta+rangex+wall_sz (LONDON-M1) | +0.381 | mean −0.157, range (−0.57, +0.19) |
| volx+eff+thick (NY_PRE-M1) | +0.738 | mean +0.118, range (−0.41, +1.00) |

Every one of these "beats its own null" 9 or 10 times out of 10 — that is
guaranteed by construction, not evidence. It is the exact mechanism the task
warned about: *"the best-looking subset will always look excellent."* The
only test that isn't circular is §3's best-of-969-vs-best-of-969 comparison,
and that is the one four of these five candidates fail outright (only
NY_AM-M3 clears it, and even it stalls at a CI that crosses zero).

## 7. WHAT COMBINATION SEARCH SAYS

Searching 969 specific pairs/triples of order-flow and depth signals across
9 session x mechanism cells (8,721 tests, 95,931 with the null) finds **no
subset whose win rate and EV jointly clear a calibrated noise floor.** One
candidate — NY_AM-M3's efficiency + support-wall-size + depth-thickness
triple (n=32, 23 days, 78.1% win, +0.396R) — is the search's best showing,
survives a LAW-2-clean robustness re-run, and is exactly what this search's
own noise floor is expected to produce about once (~0.82 cells expected, 1
observed) — and its own confidence interval crosses zero. Consistent with
BR-94 (individual signals chance-level) and BR-97/98 (stacked counts and
cross-mechanism magnitude matches also chance-level): **specific combinations
of order-flow/depth signals do not mark a materially better sub-population
in this book, at this entry timing, checked honestly against the search's
own size.** A null here is the expected and correctly-reported result.
