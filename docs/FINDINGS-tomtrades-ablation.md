# FINDINGS — tomtrades CBR, first mechanical test

Run: GC front month, 1,276,717 one-minute bars, 2023-01-02 → 2026-08-11. Correlates DX
and 6J. Detector `src/research/tomtrades/`, evidence v2, config defaults — **one
parameter point, not the sweep the confluence table specifies.**

**Headline: negative expectancy in every configuration but one, and the exception is
inside the noise. No transaction costs are modelled, so the real numbers are worse.**

## The table

| variant | kind | n | win % | mean R | total R |
|---|---|---|---|---|---|
| all gates | baseline | 42 | 52.4 | **-0.220** | -9.2 |
| no gates (trigger only) | trigger | 1964 | 67.6 | -0.031 | -61.6 |
| drop session | leave-one-out | 132 | 68.9 | **+0.038** | +5.0 |
| drop c1 | leave-one-out | 103 | 63.1 | -0.039 | -4.0 |
| drop c2 | leave-one-out | 42 | 52.4 | -0.220 | -9.2 |
| drop c3 | leave-one-out | 139 | 57.6 | -0.101 | -14.0 |
| drop c4 | leave-one-out | 43 | 51.2 | -0.238 | -10.2 |
| drop c5 | leave-one-out | 117 | 60.7 | -0.128 | -15.0 |
| only session | standalone | 883 | 66.9 | -0.050 | -44.3 |
| only c1 | standalone | 1052 | 67.6 | -0.027 | -28.5 |
| only c2 | standalone | 1769 | 65.9 | -0.024 | -42.0 |
| only c3 | standalone | 779 | 68.4 | -0.013 | -10.3 |
| only c4 | standalone | 1958 | 67.6 | -0.032 | -62.2 |
| only c5 | standalone | 836 | 66.3 | **-0.007** | -6.2 |

## 1. His win rate is roughly right. It is not the problem.

The trigger alone hits **67.6%** across 1,964 trades. He claims 76–88%; on the same
pattern we measure not far off, and 68.4% inside his clock window. The hit rate is the
one part of his story the data broadly supports.

It loses anyway, because the reward:risk is upside down. A 67.6% win rate at
-0.031R/trade implies an average win near **0.43R against near-1R losses** — roughly
1:2.3 against. Break-even at that hit rate needs about 0.48R per win.

That is structural, not a tuning miss. The target is 50% of the hourly extension while
the stop sits beyond the pattern extreme, so the stop is systematically wider than the
target. **The method's arithmetic does not close, and no threshold in the config fixes
that** — only a different target or a tighter stop would, and both are departures from
what he says.

## 2. Every gate subtracts. The full stack is the worst configuration tested.

Trigger only is -0.031R. All gates on is **-0.220R**, seven times worse, on 42 trades in
three and a half years. Every `only X` row beats the baseline. The confluences, as
specified and at these defaults, destroy value rather than add it.

Two caveats before this is read as a verdict on his confluences:
- n=42 is far too thin to characterise the full stack. The signal is that the stack is
  *restrictive*, not that it is *proven bad*.
- These are default parameters. The table prescribes sweeps and none were run.

**`drop session` (+0.038R, n=132) is the only positive cell in fourteen.** With fourteen
variants tested, one crossing zero is what multiplicity predicts. It is a hypothesis to
test on a sealed holdout, nothing more.

**C2 is exactly redundant.** `drop c2` reproduces the baseline to the trade (n=42,
identical statistics), so wherever the other gates allow, the overextension gate also
allows. His central concept adds nothing here once the others are applied.

## 3. The clock claim is contradicted in shape

| minute of hour | n | measured win % | his claim |
|---|---|---|---|
| 0-9 | **0** | — | 66% |
| 10-29 | 21 | 61.9 | 50% |
| 30-44 | 45 | 57.8 | **75%** |
| 45-59 | 73 | 56.2 | — |

He claims a peak at the halfway mark. We measure a monotonic **decline**, and his
favourite bucket has the worst mean R of the three (-0.169). Two buckets are under the
n=30 floor, so this refutes the *shape*, not the levels.

**The 0-9 bucket is structurally empty, and that is the sharper point.** C2 requires a
20-minute one-way run before a signal can exist, so a trade before minute 20 is
impossible under his own overextension rule. His claimed 66% win rate at 0-10 minutes
cannot be produced by the method he describes. Those two statements cannot both be true.

## 4. On 1-minute data the entry is systematically late

**6,046 signals were skipped because the 50% target had already been reached before the
next-bar fill** — three times the number of trades actually taken. By the time a shift
confirms on a 1-minute close, the move it was meant to fade is frequently over.

This is the strongest evidence yet for taking his 5-second chart literally. It is not a
stylistic preference; on 1-minute bars the entry arrives after the opportunity. Any
verdict on this method from 1-minute data is a verdict on a slower approximation of it.

## What this does and does not establish

Does: at default parameters, on GC, with a 1-minute trigger and no costs, the method as
specified loses, the confluences subtract, and the clock premise is contradicted in
shape.

Does not: falsify the method. Not swept, not cost-modelled, on a futures proxy rather
than his instrument, at a timeframe the skipped-signal count shows is too coarse.

Next, in order of expected information: (1) re-run on 5-second GC data — the skip count
says this is the binding constraint, not parameter choice; (2) sweep the C3 window and
C1 threshold, which is what the table asks for; (3) test the target/stop geometry
directly, since §1 says that is where the arithmetic fails.

Per the repo's non-negotiables, these divergences are reported, not fixed. No parameter
was adjusted to improve any number above.
