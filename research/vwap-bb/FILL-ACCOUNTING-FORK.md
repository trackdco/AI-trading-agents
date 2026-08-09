# THE 302-FILL FORK — A5 quoted in full, three worked examples, geometry only

**Written 2026-08-08, Amendment 05 item 3.** No outcome is computed anywhere below — every number
is a distance or a ratio between prices already fixed at signal time (entry limit, stop, target)
or at fill time (the actual next-bar open). No exit, no P&L, no win/loss.

---

## 1. §5.4, as amended, quoted in full — the operative clause

**§5.4, current text (the main body, carrying A5's edit inline):**

> *"Stop: beyond the wick extreme of the trigger candle / displacement origin. Structural, never
> widened (Vault-enforced). **Minimum stop distance: 10.00 points (40 ticks). Effective stop =
> max(structural stop, 10.00 pt).** The floor applies at order placement only; once placed the
> stop is never widened, and a structural stop already beyond 10.00 pt is used unchanged. A
> trigger whose E1 entry falls on the wrong side of the wick extreme remains invalid — the floor
> does not rescue it."*

**Amendment A5 in full, as recorded in the log:**

> ### A5 — 2026-08-08 — §5.4: minimum stop distance of 10.00 points
>
> **Change.** §5.4 now carries a floor: effective stop = **max(structural stop, 10.00 pt)**. The
> floor applies at placement only; the "never widened" rule is unchanged, and a structural stop
> already beyond 10.00 pt is used as-is.
>
> **Reason — fill realism and measured spread, not performance.**
>
> 1. **The measured spread makes tighter stops meaningless.** Top-of-book spread over 5,781 RTH
>    snapshots on 99 sessions is **0.75 pt median (3 ticks), 1.50 pt at p90**
>    (`research/STATE.md` COSTS). A 10.00 pt stop is **40 ticks — 13.3× the median spread and
>    6.7× the p90.** Below roughly that scale the stop is not measuring structure, it is
>    measuring the width of the book.
> 2. **It bounds cost as a fraction of risk.** At the measured base stop-exit cost of 0.975 pt,
>    a 10 pt stop puts costs at **9.75% of risk**. The frozen geometry's 3.12 pt median put them
>    at **31.2%**, which moved cost-adjusted breakeven from 40.6% to 46.4% on its own.
> 3. **It never excludes behaviour the author demonstrated.** The hand log's smallest in-scope
>    stop is **11.00 pts**; the floor sits below it. Every trade Angus actually took under the
>    settled session convention is admissible under A5. This uses the author's recorded stop
>    *distances*, not his P&L.
> 4. **It sits inside the feasible region**, jointly with A4 — the two are coupled, since a floor
>    on R raises the distance a target must reach to clear 1.5R
>    (`target-stop-reconciliation.md` §5).
>
> **Grounds.** **No outcome was computed, no P&L, no configuration compared, nothing ranked.**
>
> **Tag: [FIAT].** §5.4 stated no minimum.
>
> **Consequences, recorded so they are not rediscovered later:**
> - A5 is a **floor, not a repair.** The 29.6% of triggers whose E1 entry falls on the wrong side
>   of the wick extreme remain invalid and are still skipped. The E1-plus-wick pairing is
>   degenerate at both ends and that is **still an open gate-4 item**.
> - With A4, the minimum target distance becomes 15.00 pts (10.00 × 1.5).
> - The §1 note that "median trade resolves ~30 min" was derived under the old geometry. Wider
>   stops lengthen holds, so the 30-minute one-position lockout used in the signal count is a
>   **declared placeholder that A5 makes more approximate, not less**.

**What A5 settles and what it doesn't.** It fixes the **stop** floor and says the floor applies
"at order placement only" — decisive for **A-11** (stop and target are fixed from the intended
limit, not re-derived from the fill; both implementations agree on this). **It says nothing about
what happens when the fill differs from the limit** — that is accounting rule 4.2 in
`PREREGISTRATION.md`, quoted in `stage2_smoke.py`'s own docstring: *"entry fills at the OPEN of
the bar after the signal bar closes."* No conditional, no "if the open reaches the limit." **The
detector takes this literally: it fills at the next bar's open unconditionally, whether that is
better or worse than the limit.**

The blind build's alternative reading (`AMBIGUITIES.md` A-10): *"if a bar opens through the limit
the fill is the (better) open, otherwise the fill is the limit itself"* — a true limit-order
simulation, never filling worse than the limit.

---

## 2. Three worked examples, real trades, geometry only

All three: `entry` = the intended limit (A14-rounded), `stop_px`/`tgt_px` = fixed at placement
from that limit (A-11, undisputed), `fill_px` = the actual next-bar open. **Detector accounting**
uses `fill_px` as the position's reference price for realised R and reward. **Blind-build
accounting** ("true limit") uses `fill_px` only when it already beats the limit; otherwise it
falls back to the limit itself.

### Example A — typical case (median-sized gap), at the A5 floor

**2023-01-26, 1m, long.** Limit **11987.00**, fill **11995.25** (worse for a long — paid more),
stop **11977.00**, target **12015.75**.

| | entry used | realised R | reward | realised R:R |
|---|---|---|---|---|
| **screened at signal time** | 11987.00 | **10.00** | 28.75 | **2.875** |
| **detector accounting** | 11995.25 (fill) | **18.25** | 20.50 | **1.123** |
| **blind-build accounting** | 11987.00 (limit — open didn't beat it) | **10.00** | 28.75 | **2.875** |

**Detector takes 8.25 points more risk (+82.5%) than the screened R, and the realised R:R falls
from 2.875 to 1.123 — below the very 1.5R floor this trade was admitted on.** Blind-build
accounting reproduces the screened geometry exactly.

### Example B — larger gap, same direction of effect

**2024-08-05, 3m, long.** Limit **17912.25**, fill **17968.00** (worse), stop **17857.25**,
target **18004.75**.

| | entry used | realised R | reward | realised R:R |
|---|---|---|---|---|
| **screened at signal time** | 17912.25 | **55.00** | 92.50 | **1.682** |
| **detector accounting** | 17968.00 (fill) | **110.75** | 36.75 | **0.332** |
| **blind-build accounting** | 17912.25 (limit) | **55.00** | 92.50 | **1.682** |

**Detector's realised R more than doubles (2.01×) and the R:R collapses by 80%, well under the
admission floor.** Same pattern as Example A, larger scale.

### Example C — the fork is one-directional: when the fill is *better*, both conventions agree

**2024-12-27, 5m, long.** Limit **21674.50**, fill **21591.00** (better for a long — paid less),
stop **21558.75**, target **21866.50**.

| | entry used | realised R | reward | realised R:R |
|---|---|---|---|---|
| **screened at signal time** | 21674.50 | **115.75** | 192.00 | **1.659** |
| **detector accounting** | 21591.00 (fill) | **32.25** | 275.50 | **8.543** |
| **blind-build accounting** | 21591.00 (open already beat the limit) | **32.25** | 275.50 | **8.543** |

**No divergence.** When the market opens through the limit favourably, a true limit order would
have filled at that same better price — both conventions land on the identical number. **The
fork only bites in the unfavourable direction**, which is exactly why it is a one-sided,
conservative-vs-favourable question rather than a symmetric one.

---

## 3. Which is more conservative, and by how much — the aggregate, not just three examples

Full 1,472-trade admission list, geometry only:

| | |
|---|---|
| Fills **worse** than the limit (detector accounting bears the full gap) | **1,279 of 1,472 — 86.9%** |
| Fills **better** than the limit (both conventions agree, per Example C) | 183 of 1,472 — 12.4% |
| Fills **exact** | 10 of 1,472 — 0.7% |
| R inflation on the "worse" trades (detector R − screened R_int), points | **median +8.25 · mean +12.18 · p25 +4.00 · p75 +15.75** |
| Of the "worse" trades, realised R:R falls **below the 1.5R admission floor** | **960 of 1,279 (75.1%)** |
| As a share of **all** 1,472 admitted trades | **65.2%** |

**The detector's accounting is the more conservative of the two, and by a large, population-wide
margin — not a tail effect.** Under a true limit-order simulation, every trade's realised geometry
would be *at least as good as* what screened it (Example C's case, or the unchanged floor case).
Under the detector's actual accounting, **65.2% of ALL admitted trades — not just the unlucky
ones — carry a realised risk:reward that no longer clears the very 1.5R bar they were let through
on**, purely because the next bar's open moved against the position before it could fill.

**This is a materially larger and more precisely quantified finding than "the detector is the
conservative reading."** It says the admission gate's own stated promise — nothing is admitted
below 1.5R — is **true only at the instant of signal, not at the instant of fill**, for roughly
two-thirds of what gets admitted. `OUT-OF-SCOPE-BRANCHES.md`'s existing doctrine already named
next-bar-open as "strictly worse" than the spec's intended limit; this quantifies exactly how much
worse, in points and in the fraction of the population it touches.

---

## 4. What this does and does not decide

**Does not decide the fork.** Per Amendment 05 item 4's own framing, the recommendation to keep
the detector's behaviour and amend A5 to say so explicitly is **a default, not a verdict** — this
document supplies the quantified basis for that decision, it does not make it. Keeping the
detector's convention means keeping a rule under which two-thirds of admitted trades run at a
worse-than-screened R:R by construction; switching to true-limit accounting removes that but
requires an explicit amendment (and, given the population-wide scale just measured, arguably
deserves the same scrutiny A5 itself got before being written in).

**Does not touch N_trials.** Nothing here compared outcomes, ranked a configuration, or selected
a reading by result. It quantifies the geometric consequence of two already-stated readings of
one accounting rule.

**N_trials: 1 of 5, unchanged.**
