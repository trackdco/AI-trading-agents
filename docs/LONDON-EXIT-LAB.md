# London exit lab — fixed RRs, conviction RRs, walls as targets (110 trades)

**FIT ONLY. Bar-walk counterfactuals (conventions in script header) — these RANK exit ideas; an engine V-variant run confirms a winner. Entry stack frozen; 1 NQ lot dollars.**

## 1. Fixed-RR sweep, BE at +1R (declared grid)

| TP | net | WR(+) | scratch | full loss | mean R | maxDD |
|---|---|---|---|---|---|---|
| 1.5R | $+18,432 | 60% | 17% | 23% | +0.673 | $1,465 |
| 2.0R | $+17,285 | 44% | 34% | 23% | +0.645 | $1,465 |
| 2.5R | $+18,630 | 36% | 41% | 23% | +0.682 | $1,465 |
| 3.0R | $+20,615 | 34% | 44% | 23% | +0.782 | $1,465 |
| 4.0R | $+22,385 | 26% | 51% | 23% | +0.827 | $1,720 |
| 5.0R | $+21,255 | 20% | 57% | 23% | +0.773 | $1,720 |

Engine references: V1 (menu targets, BE@1R) +$22,360 · V8 shipped +$17,941. A fixed-RR row beating V1's net on a bar-walk is a candidate, not a conclusion.

## 2. Best fixed TP by conviction grade (descriptive — tiny cells)

| grade | n | 1.5R | 2.0R | 2.5R | 3.0R | 4.0R | 5.0R |
|---|---|---|---|---|---|---|---|
| A+ | 40 | $+11,098 | $+12,390 | $+12,025 | $+12,995 | $+15,840 | $+16,350 |
| mid | 51 | $+5,522 | $+3,685 | $+4,640 | $+4,900 | $+4,035 | $+1,315 |
| neither | 19 | $+1,812 | $+1,210 | $+1,965 | $+2,720 | $+2,510 | $+3,590 |

**Grade-scaled TP combo (A+ 4R / mid 1.5R / neither 2.5R): $+23,328** — assembled from §2's best-per-grade cells AFTER looking, so it carries selection inflation by construction. Declared candidate for an engine V-variant + forward data; not evidence.

## 3. The wall as a target — the data cannot reach that question

- Every trade has a wall-ahead reading (it is the nearest large level in the VISIBLE 10-level MBP book): distances q25/med/q75 = 5/7/10pt = 0.36/0.53/0.82R. Only 9 trades have a wall at >= 1.5R.
- Targets live ~3R out (median 3.02R) — BEYOND the visible book. Testing 'TP at the far liquidity wall' needs full-depth heatmap data (a data-purchase decision for Angus, same category as the 10:00+ window extension).
- The magnet idea is ALREADY the strategy's entry logic: `LON_FAR_MIN = 4.5` — scorer comment verbatim: 'wall AHEAD farther than this = magnet not choke'. FAR is the wall-as-draw check; the visible-book version of Brake's hypothesis was validated into the gate during the rebuild.

## Read it

- Same-bar ambiguity resolves AGAINST every rule tested; bar-walks understate BE benefits (the V1 engine run beat its own bar-walk by ~3x). Rankings here are directional.
- The wall-magnet test is as-of-fill depth: live walls can be pulled or spoofed (research caveat) — a reach-rate edge here is an upper bound on what live wall-targeting captures.
- Grade cells (§2) are 19-51 trades; by-grade RR tuning is declared hypothesis material for forward data, not config.
