# PHASE 2 — free numbers from the M-TABLE (handoff items 9-11)

Run 2026-08-07 on the fixed fit table (4,716 rows, post entry-price fix).
Declarations were written into `scripts/htf_ma_phase2_free.py` BEFORE the
numbers existed. Full printouts in the script's output; summary + rulings
here. No holdout contact.

## Item 9 — P(retest | break) and the cost of demanding a retest

```
P(ever-retest | break) = 93.5% [92.4, 94.6] pooled; 92.3-94.3% by era x side
non-retested breaks (6.5%, n=95): travel from ma_px median 0.66-0.75W,
  p90 2.3-3.4W, p95 4.2-6.9W
retested breaks, MFE from the retest entry: median 0.21-0.23W
```

DEFINITIONAL NOTE, recorded: BR-7's "80-82% retrace" is a RACE (retest
before the break runs 1W on a close) — Census B's loop stops at 1W. The
93.5% here is EVER-retest before session close — the fill rate for a
resting retest limit. Both stand, they answer different questions. The
6.5% never-retested breaks are the branch's opportunity cost: they escape
(median 0.7W) without offering the entry. The break-retest branch's
"defined entry 80% of the time" claim should be read as: entry offered
93.5% of the time; offered BEFORE the move escapes 1W ~80% of the time.

The ⛔-invalidated "break-and-retest beats immediate rejection" claim
remains VOID — this item prices the branch honestly (existence
unconditional, retest a flag); the re-measured branch comparison belongs
to the cut study's arm-separated books, not to a shared denominator.

## Item 10 — confluence sign by arm (prediction declared in advance: reject +, break −)

```
HIT (censusB target_before_extreme_20, confluence bins 1/2/3+):
  reject: 57->70% (H1-2026), 57->72% (H2-2025)   monotone, +13/+15pp
  break : 70->71% (H1-2026), 65->72% (H2-2025)   flat-to-mildly-positive
R (Spearman confluence_count vs out_ship, entered rows):
  reject: +0.016 [-0.033,+0.067] | -0.010 [-0.066,+0.046]   ~zero
  break : -0.126 [-0.196,-0.049] | -0.058 [-0.139,+0.021]   negative
```

RULING: the prediction is CONFIRMED in the currency where each arm's
mechanism lives, and the dual-currency law was load-bearing: on the reject
arm confluence is a WALL — it predicts ARRIVAL (+13-15pp monotone, both
eras) and nothing in R (congestion caps the tail; Law 5 verbatim). On the
break arm confluence is OBSTACLES — negative in R (CI clear of zero in
H1-2026, same sign in H2-2025), invisible in hit. The pooled +0.06 was two
different diseases averaged. Hit and R disagree on BOTH arms — no
single-currency readout of confluence is a number.

## Item 11 — persistence at n>=5 (the 144 discarded events)

```
continuation_1w (mfe >= 1W from entry) by n_attempts, era:
  H1-2026: 15/14/14/17/14/12%  (n=819/384/166/69/29/17)
  H2-2025: 15/15/14/17/11/28%  (n=921/407/178/75/28/18)
out_ship R by band: +0.17/+0.21/+0.11/+0.17/+0.72/+0.58 (H1)
                    +0.04/+0.09/-0.07/+0.29/+0.27/+0.27 (H2)
```

RULING: BR-5's null EXTENDS through the uncapped range — no monotone rise
in continuation at n>=5, either era. The R-currency shows +0.3..+0.7R at
n>=5 on n=17-29 rows: UNDERPOWERED, recorded as a curiosity, not a claim,
not a cut candidate (no declared mechanism; the n>=5 population is 3% of
the book).

(metric note: continuation_1w here = MFE >= 1W measured FROM ENTRY — at a
0.18W median stop that is ~5.6R, hence ~15% base — not BR-5's
extreme-referenced 55-60%. Definitions stated before reading; both stand.)
