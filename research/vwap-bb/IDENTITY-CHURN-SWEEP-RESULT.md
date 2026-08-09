# IDENTITY-CHURN SWEEP — RESULT. N_trials 2 of 5. VERDICT: NO EDGE DEMONSTRATED

**2026-08-08.** The pass-mark clause `PASS-MARKS-FOR-SIGNING.md` §10.4a-i, executed: 32
combinations of the five documented fork ambiguities (`FORK-SET-ENUMERATION.md`), each built
under the current A1–A22 base (A16 limit-order entry, A22 2×ATR stop floor), each an actual
outcome computation — the first in this project's Amendment 05 work. **This consumed N_trials
slot 2 of 5.** Full methodology, code, and the bootstrap convention disclosure are in
`run_identity_churn_sweep.py` and `spec_sweep.py`.

## VERDICT: NO EDGE DEMONSTRATED

**Every one of the 32 combinations has a negative mean net R at every one of the three
pre-registered cost bases (0.50 / 0.975 / 1.50 pt).** This is a stronger, cleaner negative than
the pass-mark clause's own text anticipated — (a-i) was written for the case where the result's
*sign* is unstable across ambiguity resolutions ("positive under one resolution and negative
under another"). That did not happen here. There is no sign instability to resolve: the result is
uniformly negative, including at the most lenient cost basis tested (0.50 pt), across all 32
readings of all five ambiguities.

| | |
|---|---|
| Combinations evaluated | 32 / 32 |
| Combinations clearing (positive mean, bootstrap lower bound > 0, no cost-sign-flip) | **0** |
| Mean net R @ 0.50 (lenient), range | −0.016 to −0.091 |
| Mean net R @ 0.975 (base), range | **−0.038 to −0.112** |
| Mean net R @ 1.50 (adverse), range | −0.063 to −0.135 |
| Bootstrap lower bound @ 0.975, range | −0.137 to −0.202 |
| Sign flip (0.50 vs 1.50) in any combination | No — none needed one |
| Trade count, range | 1,111 to 1,384 |

## Full table, all 32 combinations

No combination is more "correct" than another for the purpose of this verdict — the pass mark is
the **minimum**, not a search for the best reading, and no combination should be selected from
this table for any other purpose. It is reported in full for auditability, not to invite a second
look at whichever row happens to be least negative.

| combo | cluster | invalidation | confluence | F | weekly_hl | n | mean R@0.50 | mean R@0.975 | mean R@1.50 | boot LB@0.975 | clears |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 00 | bounded | same | base | 2.0 | absent | 1360 | -0.0680 | -0.0904 | -0.1153 | -0.1800 | no |
| 01 | bounded | same | base | 2.0 | present | 1344 | -0.0271 | -0.0493 | -0.0739 | -0.1420 | no |
| 02 | bounded | same | base | 2.5 | absent | 1360 | -0.0613 | -0.0838 | -0.1087 | -0.1749 | no |
| 03 | bounded | same | base | 2.5 | present | 1344 | -0.0159 | -0.0381 | -0.0626 | -0.1373 | no |
| 04 | bounded | same | counter | 2.0 | absent | 1187 | -0.0639 | -0.0864 | -0.1113 | -0.1791 | no |
| 05 | bounded | same | counter | 2.0 | present | 1184 | -0.0392 | -0.0616 | -0.0863 | -0.1572 | no |
| 06 | bounded | same | counter | 2.5 | absent | 1185 | -0.0677 | -0.0903 | -0.1153 | -0.1828 | no |
| 07 | bounded | same | counter | 2.5 | present | 1183 | -0.0393 | -0.0618 | -0.0865 | -0.1614 | no |
| 08 | bounded | opposite | base | 2.0 | absent | 1384 | -0.0871 | -0.1083 | -0.1317 | -0.1963 | no |
| 09 | bounded | opposite | base | 2.0 | present | 1380 | -0.0820 | -0.1031 | -0.1263 | -0.1952 | no |
| 10 | bounded | opposite | base | 2.5 | absent | 1378 | -0.0907 | -0.1120 | -0.1354 | -0.2017 | no |
| 11 | bounded | opposite | base | 2.5 | present | 1374 | -0.0772 | -0.0982 | -0.1214 | -0.1944 | no |
| 12 | bounded | opposite | counter | 2.0 | absent | 1243 | -0.0868 | -0.1088 | -0.1332 | -0.1963 | no |
| 13 | bounded | opposite | counter | 2.0 | present | 1252 | -0.0762 | -0.0980 | -0.1220 | -0.1902 | no |
| 14 | bounded | opposite | counter | 2.5 | absent | 1239 | -0.0881 | -0.1101 | -0.1345 | -0.1976 | no |
| 15 | bounded | opposite | counter | 2.5 | present | 1247 | -0.0770 | -0.0987 | -0.1227 | -0.1901 | no |
| 16 | chain | same | base | 2.0 | absent | 1316 | -0.0742 | -0.0963 | -0.1209 | -0.1902 | no |
| 17 | chain | same | base | 2.0 | present | 1306 | -0.0593 | -0.0813 | -0.1056 | -0.1776 | no |
| 18 | chain | same | base | 2.5 | absent | 1317 | -0.0632 | -0.0853 | -0.1097 | -0.1772 | no |
| 19 | chain | same | base | 2.5 | present | 1308 | -0.0484 | -0.0703 | -0.0945 | -0.1681 | no |
| 20 | chain | same | counter | 2.0 | absent | 1117 | -0.0552 | -0.0773 | -0.1018 | -0.1736 | no |
| 21 | chain | same | counter | 2.0 | present | 1111 | -0.0494 | -0.0713 | -0.0956 | -0.1729 | no |
| 22 | chain | same | counter | 2.5 | absent | 1114 | -0.0554 | -0.0774 | -0.1017 | -0.1762 | no |
| 23 | chain | same | counter | 2.5 | present | 1111 | -0.0547 | -0.0765 | -0.1007 | -0.1791 | no |
| 24 | chain | opposite | base | 2.0 | absent | 1363 | -0.0428 | -0.0652 | -0.0900 | -0.1625 | no |
| 25 | chain | opposite | base | 2.0 | present | 1367 | -0.0322 | -0.0542 | -0.0785 | -0.1530 | no |
| 26 | chain | opposite | base | 2.5 | absent | 1360 | -0.0437 | -0.0661 | -0.0908 | -0.1635 | no |
| 27 | chain | opposite | base | 2.5 | present | 1364 | -0.0249 | -0.0468 | -0.0711 | -0.1507 | no |
| 28 | chain | opposite | counter | 2.0 | absent | 1227 | -0.0555 | -0.0780 | -0.1029 | -0.1751 | no |
| 29 | chain | opposite | counter | 2.0 | present | 1239 | -0.0370 | -0.0592 | -0.0837 | -0.1608 | no |
| 30 | chain | opposite | counter | 2.5 | absent | 1226 | -0.0580 | -0.0804 | -0.1052 | -0.1778 | no |
| 31 | chain | opposite | counter | 2.5 | present | 1239 | -0.0402 | -0.0622 | -0.0866 | -0.1622 | no |

## Method, stated so the verdict can be audited

- **Fill mechanism**: A16, true single-bar limit-or-better fill.
- **Stop floor**: A22, 2×ATR(20, entry TF), Angus's own decision.
- **Exit resolution**: `resolve_bar_stop_first` — ambiguous bars (both stop and target touched
  in one bar) resolve stop-first, the same convention the discarded run used.
- **Cost accounting**: `stage2_smoke.COSTS` (0.50 / 0.975 / 1.50 pt), net R computed against the
  **realized** R (`|fill_px − stop_px|`), not the intended R at signal time — matching the only
  formula this project has ever used for this quantity.
- **Bootstrap**: session-block (whole sessions resampled with replacement), 10,000 iterations,
  one-sided lower bound at the 1.25th percentile. **This convention (one-sided, 1.25th
  percentile) was never specified in the pre-registration** — only the block design and the
  corrected alpha (0.0125, from the signed ÷4) were. Disclosed as the reading used, not silently
  assumed; if a different percentile convention is wanted, the sealed per-trade data
  (`data/identity_churn_sweep/combo_NN.parquet`, 32 files, each hashed) supports recomputing it
  without a new trial, since the raw trade-level records are what's sealed, not just the summary.

## What this means, stated plainly

**The strategy as currently specified (A1–A22) does not clear its own pre-registered pass mark,
under any of the 32 documented ways its ambiguous rules could reasonably be read, at any of the
three cost assumptions tested.** This is not a borderline or cost-sensitive result — it does not
turn positive even at the most lenient cost basis in any combination. Per Amendment 02's
structure, the pre-registered options from here are a Stage 4 autopsy (≤3 hypotheses about *why*,
not a re-test of *whether*) or accepting the finding as the answer to the question this whole
verification effort was built to ask. **Neither decision is made here.**

## N_trials

**2 of 5.** Stage 3's own allocation under Amendment 02 was ×1; this is its second consumption
(the first, discarded unopened, was not refunded). **3 of 5 remain overall** for whatever comes
next — one fewer than the 4 the original Stage 4 (≤3) + Stage 5 (×1) plan assumed would be
available. The holdout remains sealed and unread; nothing about this result required or used it.
