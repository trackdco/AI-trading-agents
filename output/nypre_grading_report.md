# NY pre-market survivors — grading pack (DSR / PBO / funded-shell MC / correlation)

Universe: 268 flow-span sessions 2025-06-02 .. 2026-07-15. Sizing: research-native $160-risk per trade. Canon restricted to the same days (fit-span funded accounting, 762 trades).

## 1. DSR (Brake's grader, src/validation/dsr.py)

### nypre_gap  (daily SR +0.0455, n=268 days, skew -0.16, kurt 5.8)
  a) rebuilt exit arms             SR0 +0.0603  PSR(0) 0.770  DSR 0.405  below .95
  b) family ledger (7 arms)        SR0 +0.0794  PSR(0) 0.770  DSR 0.291  below .95
  c) whole program (34 arms)       SR0 +0.1217  PSR(0) 0.770  DSR 0.108  below .95

### nypre_inv  (daily SR +0.0652, n=268 days, skew +7.29, kurt 68.8)
  a) rebuilt exit arms             SR0 +0.0224  PSR(0) 0.916  DSR 0.818  below .95
  b) family ledger (8 arms)        SR0 +0.0274  PSR(0) 0.916  DSR 0.788  below .95
  c) whole program (34 arms)       SR0 +0.0399  PSR(0) 0.916  DSR 0.704  below .95

## 2. PBO (Brake's grader, src/validation/pbo.py — CSCV on the exit-arm choice)

  nypre_gap: PBO 0.02 over 12870 splits (4 arms, 256 days used) — selection beats noise; IS->OOS slope -0.95, P(OOS loss) 0.22
  nypre_inv: PBO 0.57 over 12870 splits (5 arms, 256 days used) — OVERFIT >= .50; IS->OOS slope -1.17, P(OOS loss) 0.22

## 3. Funded-shell MC (comparative; 50k start, $2k EOD trailing, lock at 50k)

  nypre_gap alone              6mo: P(bust) 0.3%  median $+410  p05 $-844 | 12mo: P(bust) 3.2%  median $+810
  nypre_inv alone              6mo: P(bust) 0.6%  median $+900  p05 $-1,076 | 12mo: P(bust) 3.6%  median $+2,175
  gap + inv (paired days)      6mo: P(bust) 2.6%  median $+1,411  p05 $-1,017 | 12mo: P(bust) 9.8%  median $+2,815
  ny_canon alone (same span)   6mo: P(bust) 0.1%  median $+38,810  p05 $+28,518 | 12mo: P(bust) 0.2%  median $+77,258
  canon + both (paired days)   6mo: P(bust) 0.1%  median $+40,071  p05 $+29,148 | 12mo: P(bust) 0.2%  median $+80,381
  pairing cost (canon+both):  paired P(bust) 0.3% vs shuffled 0.4% — the gap is what same-day dependence costs

## 4. Correlation battery, scored against the five [PROPOSED] thresholds

### nypre_gap vs nypre_inv  (active 51/22 days, both-active 4)
  union (inactive=$0):  Pearson +0.006  Spearman +0.002
  both-active:          Pearson +0.334  Spearman +0.258
  T3 min-60-both-active: NOT MET — return estimates untrusted; structural veto + timing rule
  T5 shared families 1/3 (order-flow): no veto

### nypre_gap vs ny_canon  (active 51/230 days, both-active 47)
  union (inactive=$0):  Pearson -0.001  Spearman +0.037
  both-active:          Pearson -0.020  Spearman +0.063
  T3 min-60-both-active: NOT MET — return estimates untrusted; structural veto + timing rule
  T5 shared families 1/3 (order-flow): no veto

### nypre_inv vs ny_canon  (active 22/230 days, both-active 20)
  union (inactive=$0):  Pearson -0.012  Spearman -0.028
  both-active:          Pearson +0.054  Spearman -0.072
  T3 min-60-both-active: NOT MET — return estimates untrusted; structural veto + timing rule
  T5 shared families 2/3 (order-flow, overnight-structure): no veto

### In-market minute overlap (simultaneous open risk, same account)
  nypre_gap vs nypre_inv: 4 shared days, 52 simultaneous minutes (15% of nypre_gap's 338 in-market minutes)
  nypre_gap vs ny_canon: 47 shared days, 55 simultaneous minutes (16% of nypre_gap's 338 in-market minutes)
  nypre_inv vs ny_canon: 20 shared days, 40 simultaneous minutes (15% of nypre_inv's 267 in-market minutes)

T4 combined P(bust) <= 1.0%: see section 3 — the paired canon+both 12mo number is the input.
