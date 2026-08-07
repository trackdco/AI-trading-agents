# LDN-OBK-01 / LDN-PO3-01 — L1 mechanics

Authorised by `docs/PREREG-london-open-break-L1.md`. Bars only. 2023/24 untouched.
Conservative intrabar (stop before target). No arm dies here on expectancy
(§5.9.2); L1 produces numbers and ranks nothing.

### Continuation branch (LDN-OBK-01) — default is A/S1

**cost base (1 pt)**

| arm | n | WR | net pts | $ @160 risk | PF | R/trade |
|---|---:|---:|---:|---:|---:|---:|
| A/S1 · 2025 | 256 | 32% | -479 | $-8,130 | 0.79 | -0.198 |
| A/S1 · 2026 | 138 | 38% | +88 | $+294 | 1.06 | +0.013 |
| A/S2 · 2025 | 257 | 49% | +286 | $+52 | 1.07 | +0.001 |
| A/S2 · 2026 | 138 | 55% | +508 | $+2,035 | 1.15 | +0.092 |
| B/S1 · 2025 | 268 | 32% | -508 | $-8,531 | 0.76 | -0.199 |
| B/S1 · 2026 | 148 | 36% | -26 | $-757 | 0.98 | -0.032 |
| B/S2 · 2025 | 275 | 48% | -326 | $-523 | 0.94 | -0.012 |
| B/S2 · 2026 | 148 | 54% | +322 | $+1,616 | 1.08 | +0.068 |

**cost strict (2 pt)**

| arm | n | WR | net pts | $ @160 risk | PF | R/trade |
|---|---:|---:|---:|---:|---:|---:|
| A/S1 · 2025 | 256 | 32% | -735 | $-12,575 | 0.70 | -0.307 |
| A/S1 · 2026 | 138 | 38% | -50 | $-1,414 | 0.97 | -0.064 |
| A/S2 · 2025 | 257 | 48% | +29 | $-715 | 1.01 | -0.017 |
| A/S2 · 2026 | 138 | 54% | +370 | $+1,764 | 1.11 | +0.080 |
| B/S1 · 2025 | 268 | 32% | -776 | $-14,306 | 0.66 | -0.334 |
| B/S1 · 2026 | 148 | 36% | -174 | $-3,169 | 0.88 | -0.134 |
| B/S2 · 2025 | 275 | 47% | -601 | $-1,378 | 0.88 | -0.031 |
| B/S2 · 2026 | 148 | 53% | +174 | $+1,312 | 1.04 | +0.055 |

### Failure branch (LDN-PO3-01) — default is F1 (midpoint)

**cost base (1 pt)**

| arm | n | WR | net pts | $ @160 risk | PF | R/trade |
|---|---:|---:|---:|---:|---:|---:|
| F1 · 2025 | 234 | 34% | -149 | $-7,099 | 0.93 | -0.190 |
| F1 · 2026 | 125 | 33% | +8 | $+42 | 1.01 | +0.002 |
| F2 · 2025 | 234 | 25% | -108 | $-7,556 | 0.96 | -0.202 |
| F2 · 2026 | 125 | 28% | +343 | $+6,031 | 1.20 | +0.302 |

**cost strict (2 pt)**

| arm | n | WR | net pts | $ @160 risk | PF | R/trade |
|---|---:|---:|---:|---:|---:|---:|
| F1 · 2025 | 234 | 33% | -383 | $-10,945 | 0.83 | -0.292 |
| F1 · 2026 | 125 | 33% | -117 | $-1,387 | 0.93 | -0.069 |
| F2 · 2025 | 234 | 25% | -342 | $-11,403 | 0.87 | -0.305 |
| F2 · 2026 | 125 | 28% | +218 | $+4,602 | 1.12 | +0.230 |

### The tight-stop claim — the reason this family was greenlit

Pre-committed reading: supported only if S1 beats S2 on R/trade in BOTH
eras at BOTH cost levels.

| entry | era | cost | S1 R/trade | S2 R/trade | S1 wins |
|---|---|---|---:|---:|---|
| A | 2025 | base | -0.198 | +0.001 | no |
| A | 2025 | strict | -0.307 | -0.017 | no |
| A | 2026 | base | +0.013 | +0.092 | no |
| A | 2026 | strict | -0.064 | +0.080 | no |
| B | 2025 | base | -0.199 | -0.012 | no |
| B | 2025 | strict | -0.334 | -0.031 | no |
| B | 2026 | base | -0.032 | +0.068 | no |
| B | 2026 | strict | -0.134 | +0.055 | no |

**Default entry (A): S1 beats S2 in 0 of 4 era×cost cells.** Claim NOT supported as declared.

**Read the control before reading the verdict.** The structural-stop arms
exit on the clock 82% of the time: at a stop that
wide, a 2R target sits 100-170 pts away and NQ does not travel that far
inside the two-hour window. So S2 as specified is not really the same trade
with a wider stop — it is a two-hour hold that exits at market. Its edge over
S1 is near-zero beating negative, not a working alternative.

**The defensible statement is therefore about S1 on its own terms, and it is
not kind:** at 2R the trigger-candle stop is hit 65% of the time and the target 30%. A 2R trade needs 33.3% to break even before costs. That is break-even
geometry, and the cost stack decides it — which is exactly the shape that
killed `nypre-euro-handoff`. The tighter stop does not rescue the level break;
it gets you tapped out.

### Declared variable — minimum displacement (default arms only)

**A/S1**

| filter | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| none (as taught) | 2025 | base | 256 | 32% | -479 | 0.79 | -0.198 |
| none (as taught) | 2025 | strict | 256 | 32% | -735 | 0.70 | -0.307 |
| none (as taught) | 2026 | base | 138 | 38% | +88 | 1.06 | +0.013 |
| none (as taught) | 2026 | strict | 138 | 38% | -50 | 0.97 | -0.064 |
| >= 0.10x range | 2025 | base | 111 | 32% | -227 | 0.80 | -0.201 |
| >= 0.10x range | 2025 | strict | 111 | 32% | -338 | 0.72 | -0.288 |
| >= 0.10x range | 2026 | base | 52 | 33% | -173 | 0.74 | -0.129 |
| >= 0.10x range | 2026 | strict | 52 | 33% | -225 | 0.68 | -0.196 |

**F1**

| filter | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| none (as taught) | 2025 | base | 234 | 34% | -149 | 0.93 | -0.190 |
| none (as taught) | 2025 | strict | 234 | 33% | -383 | 0.83 | -0.292 |
| none (as taught) | 2026 | base | 125 | 33% | +8 | 1.01 | +0.002 |
| none (as taught) | 2026 | strict | 125 | 33% | -117 | 0.93 | -0.069 |
| >= 0.10x range | 2025 | base | 100 | 38% | -306 | 0.70 | -0.255 |
| >= 0.10x range | 2025 | strict | 100 | 36% | -406 | 0.63 | -0.330 |
| >= 0.10x range | 2026 | base | 47 | 34% | -210 | 0.65 | -0.200 |
| >= 0.10x range | 2026 | strict | 47 | 34% | -257 | 0.59 | -0.267 |

### How trades ended (base cost, both eras)

| arm | stop | target | time |
|---|---:|---:|---:|
| A/S1 | 65% | 30% | 5% |
| A/S2 | 14% | 3% | 83% |
| B/S1 | 65% | 31% | 4% |
| B/S2 | 17% | 3% | 80% |
| F1 | 61% | 29% | 10% |
| F2 | 67% | 13% | 20% |
