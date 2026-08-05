# VERDICT — NYA-SB-01 (ash10hazard silver bullet), stop at the order-block edge

**Drafted for Brake's signature.** Reproduce: `python -m scripts.nya_sb01_census`.
Declared `PREREG-nya-silver-bullet.md` 08:03:40Z; stop spec amended to v3 on Brake's
instruction, validated against an external anchor before any outcome was read.
**Sealed 2023/24 untouched.**

## VERDICT: **INCONCLUSIVE ON POWER** — and it does not clear the deflation bar.

| era | n | WR @2R | p₁ | mean R | total |
|---|---|---|---|---|---|
| 2025H2 discover | 72 | **31.9%** | 0.599 | −0.042R | −3.0R |
| 2026H1 validate | 72 | **48.6%** | **0.003** | +0.467R | +33.6R |

Break-even at 1:2 is 33.3%. **The discover era is flat. Only the validate era works.**

## The stop spec is the story

Three specifications were run. Their stop sizes were checked against his own stated stops
(27/28/51/53 pts) **before** outcomes were read:

| spec | median stop | verdict on the spec |
|---|---|---|
| v1 swept level | 58 pts | void — contradicts source |
| v2 FVG far edge | 3.75 pts | void — contradicts source |
| **v3 order-block edge** | **19.2 pts** (mean 25.5) | **consistent — the only one** |

v3 is the first specification that reproduces his stop geometry, which is why its result is
worth anything at all. It also moved the outcome enormously: v1 gave −91.2R, v3 gives
+30.6R gross on the same event set. ***The stop rule, not the entry, was carrying the entire
prior result.***

## Why this still does not pass

**1. It is below the deflation bar.** Per §6.0 the bar reads from the merged ledger:

| | |
|---|---|
| best effect here (2026H1) | **+0.3239** |
| deflation bar @ N=58 | **+0.5636** |

Short by 0.24. The 2026 result is not distinguishable from the best of 58 trials by luck.

**2. Discover flat, validate strong — for the fourth time.** TRAPPED, ABSORB and the
naked-POC magnet all showed one era working and the other not. Each was noise. This is the
same shape, and the desk has now been shown it four times.

**3. The search is real and is priced.** All three stop specs are recorded as arms
(6 rows, ledger 52 → 58). I looked at outcomes under all three. Reporting v3 alone would be
rank-and-promote — the procedure §6.0 condemns and PBO 0.891 measured.

**4. Per-window instability.** PM runs 10% (2025H2) → 44% (2026H1); AM2 25% → 53%. Only AM1
is stable (48% → 52%), and AM1 is the window he names as highest-probability.

## Costs

Median stop 19.2 pts = **$384 risk** on 1-lot NQ. Commission $5 + one tick slippage each way
= **$25 = 0.065R per trade**. Over 144 trades that is **−9.4R**, taking +30.6R gross to
**+21.2R net** — still positive, but the discover era remains negative after costs.

## Secondary — does the macro gate earn its place?

| era | in macro | +1h offset | diff |
|---|---|---|---|
| 2025H2 | 31.9% | 32.3% | **−0.3pp** |
| 2026H1 | 48.6% | 41.2% | **+7.4pp** |

Era-unstable, like everything else here. No support for the macro windows being special in
the discover era.

## What this does and does not establish

**Does not kill the candidate.** Per prereg §1 and §5.9.1, three declared components remain
omitted — order-block *identification* (v3 uses OUR canon reconstruction, not his rule), the
ES leading trigger, and the bias filter. A null cannot kill a model tested without its
mandatory triggers.

**Does establish** that the mechanisable core, with a source-consistent stop, produces a
2026 result that is significant on its own but fails deflation once the desk's full search
is counted.

## Trial accounting

**6 trials** (3 stop specs × 2 eras) into NYA-SB-01. Merged ledger **52 → 58**. Bar moves
+0.5143 → +0.5636.

## Recommendation

**Do not promote. Do not run more stop variants** — that is the condemned procedure with a
fresh coat of paint. The two things that would change the picture are both inputs, not
analyses:

1. **His actual stop rule**, from him. v3 is our reconstruction; a confirmed rule would let
   one clean arm replace three.
2. **ES data.** The ES leading trigger is a declared entry component and is still missing.
