# FINDING: duplicate `exit` rows in the reference books, and what they do to the trail ledger

Found while assembling the jr1-vs-wr2 comparison. Scope note: **wr2 and jr1 are clean** (one
wr2 case found and removed, below). The rest is in w49/j49, which are outside the
"wr2 then jr1 then STOP" scope - **logged, not re-worked.**

## 1. The wr2 case (fixed)

`wr2 2026-06-23 P2` carried two exit rows:

| | `original_r_pts` | `r_blended` |
|---|---|---|
| stale | **3.0** | +1.0000 |
| live | **34.25** | +0.0876 |

Entry 29843.25 against an original stop of 29809.00 is 34.25pt of risk, not 3.0. That wrong
denominator turned a 3.00pt scratch into a full +1.0000R. The corrected re-resolution was
appended and the bad row left in place.

`score.py` was already taking the later row, so **wr2's headline never moved**: 16.5304R
blended / 11.0002R full-target before and after removal, and 06-23's day_summary
(1.8882R) sums from the correct rows. The stale row was only a landmine for any consumer
that sums exit rows naively - which is exactly how it was caught: a naive sum read wr2 as
+17.5304R, exactly 1.0000R high.

Removed. wr2 and jr1 now have exactly one exit row per fill.

## 2. The reference books are not clean

| book | trades with duplicate exit rows | naive sum | last-wins dedup | a naive read is off by |
|---|---|---|---|---|
| w49 | **10** | +24.9696R | +16.2789R | **+8.6907R** |
| j49 | 1 | -1.9834R | -4.1589R | +2.1755R |

`score.py`'s `DAYS` only covers wr2 and jr1, so it cannot be pointed at these books to
arbitrate them.

## 3. What that does to the dead-zone-trail ledger

`docs/RECEIPT-deadzone-trail.md` is a per-trade counterfactual list, not a naive book sum, so
the duplicates do not corrupt it wholesale. But four of its eleven rows are duplicated
trades, and **three quote the stale row**:

| ledger row | ledger "as-run" | authoritative | ledger used |
|---|---|---|---|
| w49 06-23 L1 | +1.145 | **+1.5684** | stale |
| w49 06-23 L5 | +0.483 | **+0.3879** | stale |
| w49 06-23 P3 | +1.825 | +1.8309 | authoritative (ok) |
| w49 06-25 A2 | +2.740 | **+4.8648** | stale |

Recomputing the rule's-effect column against the ledger's own HOLD counterfactuals:

| | ledger effect | corrected effect | delta |
|---|---|---|---|
| L1 | +0.53 | +0.11 | -0.42 |
| L5 | -1.48 | -1.39 | +0.09 |
| A2 | -0.88 | -3.00 | -2.12 |
| | | **net** | **-2.45R** |

## 4. The ruling is unchanged - and strengthened

The ledger's headline was **as-run +10.27R · rule-applied +8.48R · the ban costs ≈ -1.8R**.
Every correction pushes the as-run column *up* (~+2.45R net), leaving the HOLD counterfactuals
untouched, so the ban gets **more** expensive, not less: roughly **-4.2R** instead of -1.8R.

So the ruling - dead-zone trail nets positive, manage 0.3.4 stands as written - is not in
doubt. The errors ran in the direction that reinforces it. **No manage change is proposed and
0.3.4 remains untouched.**

Caveat on precision: the corrected effects above reuse the ledger's HOLD counterfactuals,
which have not been re-derived, and w49 06-25 A2 is already marked in the receipt as a
convention artefact (its dead-zone stop was never actually hit). Treat -4.2R as
direction-and-order-of-magnitude, not a new headline.

## 5. Recommendation

Deduplicate w49/j49 (last-wins) and re-issue the receipt before the trail question is opened
again, so the ledger quotes authoritative rows. Not done here: out of scope for this run, and
nothing about it changes the standing ruling.
