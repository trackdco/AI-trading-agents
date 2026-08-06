# VERDICT — LDN-ATC-01 L1 Stage 1 (pre-London pullback, first P&L)

**Drafted for Brake's signature.** Per `docs/VALIDATION-PROCESS.md` §5. Routes to Angus.
Reproduce: `python -m scripts.ldn_atc01_l1` (gate) then `python -m scripts.ldn_atc01_l1_report`.

Declared `docs/PREREG-london-atc-L1.md` at commit `0806db7`, **15:20:05Z**, run unchanged.
**Sealed 2023/24 untouched. No holdout look. Stage 2 not spent and still blocked.**

---

## VERDICT: **FAIL**

The declared primary is **INCONCLUSIVE ON POWER** (n=30; eras 22/8, both below the n≥30
floor), which blocks like FAIL. The declared secondary **is** adequately powered per era
(58/30) and is **negative in both** — a legal direction claim under §2.2 — so the family
does not survive on either arm.

| arm | n | 2025 | 2026 | pooled meanR (2pt) | WR |
|---|---:|---:|---:|---:|---:|
| **primary — structural target** | 30 | **−0.489** | +0.101 | **−0.332** | 50.0% |
| **secondary — fixed 1R** | 88 | **−0.204** | **−0.236** | **−0.215** | 44.3% |

Against §9.1: criterion 1 (positive in both eras) **fails on both arms** — the primary
era-flips, the secondary is negative twice. Criterion 3 (> +0.110R) **fails on both**.
Criterion 2 is not reached, and could not have saved it.

**A pass would have meant "not yet dead". This is not a pass.**

---

## 1. The gate did its job — two defects in my own harness, caught before any P&L

The prereg required the chain to reproduce the published L0 census before any economics.
It failed twice, and both were mine, not the chain's:

1. **Bar-label convention.** Databento `ts_event` is the bar **START**; I treated it as the
   close, putting every window boundary one minute late. Caught because the census's own
   `ref_px` on 2025-04-11 is 18695.50 — the close of the 06:59-START bar, not the 07:00 one.
   Pre-fix: 116 triggered vs 108, only 76% status agreement, `ref_px` matching on 7/303
   sessions and differing by up to 38.5 pts.
2. **A flat bar counted as directional.** The LTA used `~(close > open)`, which treats
   `close == open` as a pullback-direction bar and extends a run through it. 2026-07-09's
   07:45 bar closes exactly at its open; the negation form gave a run of 2 and a spurious
   trigger. Explicit `close < open` fixes it.

**After both fixes the reproduction is exact:** no_bias 87/87 · bias_no_pullback 6/6 ·
pullback_no_lta 160/160 · triggered 108/108 · eras 69/69 and 39/39 · clock 29/37/26/16 all
matching. `lta_no_trigger` 35 = published 30 **+ the 5 `fallback_only`**, exactly as
expected since the L1 default excludes the fallback arm. Bias agreed on 396/396 sessions
and `ref_px` on 309/309 to 0.0000.

**Neither defect would have been visible in the P&L.** They would have shifted the
population quietly. This is the case for the gate.

## 2. DEFECT FOUND IN THE CENSUS CHAIN — lookahead in the LTA gate

**This one is not mine and it is not cosmetic.**

The LTA is defined over the **whole 07:00–08:00 window** (4 fifteen-minute bars), but the
trigger scan runs **07:00–09:00 and takes the first occurrence**. A trigger can therefore
fire at **07:30**, gated by an LTA condition whose inputs — the 07:45 and 08:00 bars —
have not closed yet.

**29 of 108 triggers (27%) fire at 07:30 and are all in this class.** That is precisely the
cohort §6.1 of the prereg decided to include, on the reasoning that it was the most
on-mechanism part of the set. That reasoning stands; the mechanisation does not.

This is defect class D3 — *a correct signal about the wrong interval*. It is invisible to
fragility testing, because a lookahead is perfectly robust to trimming. The L0 census's own
lookahead audit certified "no column reads a bar that closes after the decision minute";
it audited each column in isolation and missed the interaction between the LTA window and
the trigger scan.

**Consequence: LDN-ATC-01's published L0 count of 108 is inflated by lookahead.** A causal
version requires either the trigger scan to start at 08:00, or the LTA to be evaluated only
over bars closed at the decision minute. Both are respecifications, not fixes, and both
need a fresh prereg.

## 3. DEFECT IN MY OWN PREREG — the structural target is already passed on 64% of triggers

§4.1 declared the primary target as the pullback origin (the 07:00 price). Measured:

| trigger clock | target still beyond entry | already passed | median distance (pts) |
|---|---:|---:|---:|
| 07:30 | **0** | **29** | **−26.0** |
| 08:00 | 19 | 18 | +4.0 |
| 08:30 | 10 | 16 | −7.2 |
| 09:00 | 10 | 6 | +8.0 |
| **all** | **39** | **69 (64%)** | — |

At 07:30 it is **never** valid — mean −32.9 pts, best case −7.0. By the time a bias-aligned
15m+30m close prints, price has typically already retraced past the pullback origin.

That is a **property of the geometry**, not a coding error, and it is a defect in the spec
I wrote and you approved. n collapses 108 → 39 valid → 30 filled. I am reporting it rather
than substituting a target that works: substituting now would be exactly the post-hoc
tuning §4.1 forbids, and the prereg is the commitment.

## 4. DESIGN ERROR IN MY §10.1 — Test B is degenerate by construction

Test B (paired entry comparison) returned **+0.000R on all 30 paired sessions**, because
the chain-stripped control uses the *same* trigger rule and the chain (pullback + LTA) is
**purely a session filter** — it never alters the entry within a session. Where both fire,
the entries are identical by construction.

Test B as I specified it cannot discriminate and never could. Only Test A is meaningful,
and its comparison group collapsed to **n=6** once the target rule removed the rest, so it
carries no weight either:

| §10.1 Test A — selection | n | meanR (2pt) |
|---|---:|---:|
| ATC, chain complete | 30 | −0.332 |
| bias but chain NOT complete | 6 | +0.074 |

Direction is *against* the chain, but at n=6 that is not a finding.

## 5. Full reporting, as §10 requires

**Fill:** 108 triggered → 69 skipped (no valid target) → 39 usable → **30 filled, 76.9%**.
Secondary arm: 108 → 88 filled (81.5%), 20 unfilled.

**Cost stacks** (primary): 2pt −0.332R / 1pt −0.278R. Secondary: 2pt −0.215R / 1pt −0.167R.
Headline is the strict 2pt stack throughout.

**Half-year (primary, 2pt):** 2025H1 −0.035 (n=12) · 2025H2 **−1.035, 0% WR** (n=10) ·
2026H1 +0.101 (n=8) · 2026H2 n=0. The 2025H2 cell is a total wipeout and is exactly the
kind of losing half that year-pooling hides.

**07:30 vs later (primary):** 07:30 **n=0** — every one removed by the target rule.
Secondary arm, where 07:30 survives: **07:30 −0.440R (n=23)** vs 08:00+ −0.135R (n=65).
The pre-open cohort is the worst part of the population on the only arm that can measure it.

**k distribution (§10.2):** mean **1.18**, median **0.65**, **66.7% of trades have k < 1.0R**.
Left tail: min 0.12, p5 0.18, p10 0.19, p25 0.41. Deciles 0.19/0.34/0.50/0.55/0.65/0.76/
1.12/1.62/3.25. The mean is carried entirely by a thin right tail. **Required Stage 2 win
rate at the realised mean k: 68.0%** — against a measured 50.0%. This is the §13 regime
where a Stage 2 failure would have been uninformative, and it is now moot.

**Risk bands on ATC's own population:** every trade has risk ≥ 9.5pt (the trigger-candle
range is never smaller), so **the CAN-01 9.5pt floor cannot be tested here** — the question
§6.2 posed is unanswerable on this population. 9.5–15pt −0.575 (n=10) · 15–25 −0.659 (n=9) ·
25+ **+0.156 (n=11)**. Only the widest band is positive.

**Exits:** target 50.0% · stop 46.7% · 10:00 flat 3.3%. MFE median 0.56R, MAE median 0.93R —
the median trade goes further against than for it.

**Bound-both-orderings: 0 cases.** No trade had stop and target inside one 1-minute bar, so
no outcome rests on an assumed intrabar sequence.

**Controls (2pt):** randomised-bias −0.382R (n=21) vs ATC −0.332R. ATC is marginally less
negative than random direction. That is not an edge.

## 6. Trial accounting

**8 trials** charged to LDN-ATC-01, as declared: primary ×2 eras, secondary ×2, randomised-
bias ×2, chain-stripped ×2. London declared total **34 → 42**.

## 7. What this does NOT establish

- **Bars only.** No depth, no flow. And per §6.1 the 07:30 cohort could never have been
  gated by either, since London depth begins at 08:00.
- **NQ applicability remains an assumption.** The source teaches gold and forex.
- **The tested spec is stricter than the taught one** — his discretionary no-trade rule is
  dropped.
- **This does not close the mechanism.** It closes *this mechanisation*. The lookahead in
  §2 and the target defect in §3 both mean the chain as censused was not a fair test of the
  taught idea. A causal respecification is a legitimate new candidate — with a fresh
  prereg, a fresh L0, and the honest note that its predecessor died on defects, not on a
  measured absence of edge.
- **Stage 2 was not spent.** The 2023/24 ruling is unaffected by this result.
