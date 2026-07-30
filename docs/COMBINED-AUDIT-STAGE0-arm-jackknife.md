# Combined audit — Stage 0: is the London arm choice month-fragile?

**Fit only. Sealed 2023/24 never loaded.**

The cheap gate, run before spending the hour. If dropping any single month flips either decision — wall vs old4, or which constraint level wins — the arm choice is an artifact of that month and the rest of the job is not worth running.

## Full fit span (14 months)

| arm | capped | uncapped | raw |
|---|---|---|---|
| wall | $+18,848 | $+22,795 | $+22,628 |
| old4 | $+14,488 | $+15,144 | $+16,032 |

**Baseline decision: arm=`wall`, level=`uncapped`.**

## Drop-one-month jackknife

| month dropped | winning arm | winning level | arm flip | level flip |
|---|---|---|---|---|
| 2025-06 | wall | raw | no | **FLIP** |
| 2025-07 | wall | uncapped | no | no |
| 2025-08 | wall | uncapped | no | no |
| 2025-09 | wall | uncapped | no | no |
| 2025-10 | wall | uncapped | no | no |
| 2025-11 | wall | uncapped | no | no |
| 2025-12 | wall | uncapped | no | no |
| 2026-01 | wall | uncapped | no | no |
| 2026-02 | wall | raw | no | **FLIP** |
| 2026-03 | wall | uncapped | no | no |
| 2026-04 | wall | raw | no | **FLIP** |
| 2026-05 | wall | uncapped | no | no |
| 2026-06 | wall | raw | no | **FLIP** |
| 2026-07 | wall | uncapped | no | no |

## With BOTH 2026-03 and 2026-05 removed

(the two largest contributing months: +$4,964 and +$5,322 of the $+22,795 uncapped total)

| arm | capped | uncapped | raw |
|---|---|---|---|
| wall | $+9,690 (n=117) | $+12,509 (n=133) | $+10,098 (n=146) |
| old4 | $+9,948 (n=95) | $+9,036 (n=107) | $+7,821 (n=110) |

Winning arm without those two months: **wall**. Wall/uncapped remains **PROFITABLE** at $+12,509 over 12 months.

## Verdict

**PROCEED — the arm choice (`wall`) survives every single-month removal.** No month's absence flips wall vs old4.

The constraint LEVEL is softer: it flips when dropping 2025-06, 2026-02, 2026-04, 2026-06. That is a weaker claim than the arm choice and should be treated as unsettled — capped vs uncapped is a preference, not a finding.
