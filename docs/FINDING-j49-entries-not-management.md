# j49 vs w49: the difference is at ENTRY, not management or trend alignment

Measured on every fill in both runs, from bars between fill and exit. MFE = maximum
FAVOURABLE excursion in R (how far the trade ever went the right way before it ended);
MAE = maximum ADVERSE excursion in R.

|            | mean MFE | mean MAE | reached +1R unrealised | never got past +0.75R |
|------------|---------:|---------:|-----------------------:|----------------------:|
| **w49**    | **2.45R** | 0.60R   | **15 of 19**           | 3 of 19               |
| **j49**    | **0.97R** | 1.06R   | **6 of 16**            | **9 of 16**           |

## What this rules OUT

- **It is not management.** You cannot trail a stop on a trade that never goes your way.
  The two j49 fills that DID reach +1R unrealised (d1 P2 at 1.60R, d3 L10 at 1.07R) are
  exactly the two that got trailed and exactly the two that finished green. Management
  converted every trade it was given something to work with.
- **It is not fade-vs-follow.** Two horizons were tested and both failed to separate the
  weeks. On a 2-hour 15m slope, AGAINST-trend was w49's BEST bucket (+11.9R over 11
  fills) - the opposite of the hypothesis. On session drift from the 18:00 open, j49's
  two WITH-trend fills (d5 L2 and L4, shorts into a -292pt session) lost 1.0000R each.

## What it points AT

The entry criteria selected setups with no follow-through in this regime. Seven of ten
j49 fills never got even three-quarters of one R in profit at any point between fill and
stop - they went against the position essentially from the first bar. Mean MAE (1.11R)
EXCEEDS mean MFE (0.57R): the average j49 trade spent more of its life beyond its own
stop distance than it ever spent in profit.

The trend idea may still be the right explanation for WHY those setups had no
follow-through - a "rejection" at a band edge in a market that keeps going is not a
rejection. But the measurement locates the failure at entry selection, and any fix
belongs in the trigger's criteria for what counts as a rejection worth taking, not in
the manager's rules.

## Final numbers — both runs complete

Recomputed on the closed run: j49 finished 16 fills / **-4.1589R** blended, w49 22 fills /
**+14.7758R**. (The MFE table counts 19 w49 fills and 16 j49 fills - the ones whose exit row
carries a usable exit minute; a handful of w49 multi-leg exits record their minutes per leg in
a shape this particular script does not parse, which shifts the counts but not the picture.)

Two further facts from the closed run point the same way:

- **Twelve of j49's sixteen fills were shorts**, against a roughly even split in w49. The
  triggers kept finding the same shape and it kept not working.
- **Management was worth +0.4507R in j49 against +1.7360R in w49** - still positive, but there
  was far less to work with. The two j49 trades that reached +1R unrealised are the two that
  got trailed and the two that finished best.

Sample sizes are small - sixteen fills and twenty-two. Treat the direction as real and the
decimals as indicative.

Nothing here fed either run. Every verdict was made before this analysis existed.
