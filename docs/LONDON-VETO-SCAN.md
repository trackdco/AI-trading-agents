# London veto scan — declared no-trade conditions vs the major losers

**FIT ONLY. Sealed untouched. Vetoes mined near losses are the most overfit-prone object in this project — every candidate must clear era-consistency, the profit-trap check (vetoed NET <= 0 both eras), and a worst-of-K charge. Declared priors only; nothing ships.**

## 1. The twelve worst trades (1-lot dollars), with their pre-entry state

| day fill | $ | R | tf | pattern | wall | conv | room | vwap dir | stop/rng | post-loss? | bucket |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2025-09-02 04:06 | -735 | -1.01 | 5min | A | both | 3 | 0.85 | -1.84 | 15.0% | n | 09:00 |
| 2026-03-09 04:04 | -585 | -1.01 | 3min | B2 | both | 1 | 0.87 | -1.00 | 8.8% | n | 08:00 |
| 2026-06-26 04:12 | -440 | -1.01 | 5min | B2 | one | 2 | 0.45 | +0.00 | 2.9% | n | 09:00 |
| 2026-02-06 03:05 | -430 | -1.01 | 3min | B | one | 0 | 0.81 | -1.00 | 5.6% | n | 08:00 |
| 2026-07-13 03:32 | -420 | -1.01 | 1min | B | one | 0 | 0.22 | +1.06 | 4.1% | n | 08:30 |
| 2026-03-17 04:13 | -410 | -1.01 | 5min | B | both | 2 | 0.29 | +1.05 | 13.0% | Y | 08:00 |
| 2026-03-26 04:34 | -410 | -0.92 | 3min | A | one | 0 | 0.91 | -1.94 | 9.4% | n | 08:30 |
| 2026-02-10 03:46 | -390 | -0.94 | 5min | B | both | 3 | 0.47 | -0.23 | 17.5% | n | 08:30 |
| 2026-04-20 04:14 | -375 | -1.01 | 5min | B | both | 2 | 0.64 | -0.02 | 9.8% | Y | 09:00 |
| 2025-10-31 04:26 | -355 | -1.01 | 5min | A | one | 1 | 0.53 | -0.01 | 18.6% | n | 08:00 |
| 2026-02-10 03:31 | -340 | -0.67 | 5min | B | one | 2 | 0.61 | -1.05 | 21.4% | n | 08:30 |
| 2025-06-23 04:25 | -330 | -1.02 | 5min | B | one | 0 | 0.12 | +1.72 | 4.2% | n | 09:00 |

Book medians for reference: room 0.50, vwap dir -0.01, stop/rng 6.7%.

## 2. The veto candidates (all declared from prior docs; charged worst-of-7)

| veto cell | n | WR | mean R | net | 2025 n/R/$ | 2026 n/R/$ | p(worst-of-K) | era-bad? | net<=0 both? | VERDICT |
|---|---|---|---|---|---|---|---|---|---|---|
| V1 score-0 (no conviction condition) | 11 | 36% | +0.029 | $-442 | 3/-0.55/$-415 | 8/+0.24/$-28 | 0.370 | Y | Y | **VETO-GRADE** |
| V2 1min TF | 17 | 41% | +0.321 | $+919 | 7/+0.42/$+662 | 10/+0.25/$+256 | 0.906 | Y | n | fails |
| V3 room_ahead > 0.75 | 33 | 48% | +0.518 | $+2,974 | 16/+0.09/$-188 | 17/+0.92/$+3,161 | 0.999 | n | n | fails |
| V4 vwap dir <= -0.25 (S3 threshold) | 54 | 50% | +0.466 | $+4,674 | 26/+0.30/$+1,585 | 28/+0.62/$+3,089 | 0.996 | Y | n | fails |
| V5 post-loss at fill | 16 | 44% | +0.105 | $+580 | 5/-0.43/$-265 | 11/+0.35/$+845 | 0.506 | Y | n | fails |
| V6 neither (not B2, not both-wall) | 31 | 55% | +0.214 | $+979 | 17/+0.20/$+848 | 14/+0.23/$+131 | 0.725 | Y | n | fails |
| V7 stop/range < 4% | 26 | 69% | +1.150 | $+6,588 | 6/+0.11/$+195 | 20/+1.46/$+6,392 | 0.515 | n | n | fails |

(era-bad = below that era's book mean R in both eras; net<=0 both = the profit-trap check. A veto must pass BOTH plus n >= 10.)

## 3. Pricing (only VETO-GRADE cells may stack)

| book | n | WR | mean R | net | maxDD |
|---|---|---|---|---|---|
| baseline (cut@09:30) | 144 | 62% | +0.630 | $+21,801 | $1,435 |
| minus V1 score-0 (no conviction condition) | 133 | 64% | +0.680 | $+22,244 | $1,265 |
| minus the full stack | 133 | 64% | +0.680 | $+22,244 | $1,265 |
| one-at-a-time, no vetoes | 118 | 61% | +0.600 | $+16,866 | $1,000 |
| one-at-a-time + veto stack | 110 | 64% | +0.669 | $+17,941 | $958 |

(The last two rows answer the 'second trade' question causally: a veto that kills trade 1 lets serialization admit the trade 2 it was blocking — the only implementable way to prefer the later trade.)

## Read it

- Any VETO-GRADE cell here is still a FIT-SIDE find: it goes to the declared-priors table and is judged on forward data, exactly like S3. The late-bucket lesson stands: mechanism-plausible cells fail worst-of-K nulls all the time.
- The worst-trade table (§1) is for eyeballs, not rules — twelve rows cannot found a rule and are printed so Brake can see each loser's context, per the ask.
