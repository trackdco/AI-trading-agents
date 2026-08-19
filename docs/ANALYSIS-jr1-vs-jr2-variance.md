# jr1 vs jr2 on the SAME tape: a −5.26R swing, decomposed

Both runs adjudicate session-days 2026-05-31 … 2026-06-04, three windows a day, identical bars.
jr1 scored **+3.0837R** blended (12 trades). jr2 scored **−2.1792R** blended (14 trades).

## Decomposition

| component | R |
|---|---|
| management, on the 5 trades common to BOTH runs | **−0.2250** |
| winners jr1 took that jr2 passed | **−3.2416** |
| trades jr2 took that jr1 passed | **−1.7963** |
| **total swing** | **−5.2629** |

Management is nearly nil. The swing is entirely *which trades were taken*.

### The 5 trades in both runs

| day | cid | jr1 | jr2 | diff |
|---|---|---|---|---|
| 06-01 | A2 | +1.0000 | +1.1086 | +0.1086 |
| 06-01 | P2 | −1.0000 | −1.0000 | 0.0000 |
| 06-02 | L3 | −1.0000 | −1.0000 | 0.0000 |
| 06-02 | L8 | −0.6848 | −0.8333 | −0.1485 |
| 06-03 | A3 | +1.5269 | +1.3418 | −0.1851 |

## The headline: jr1's result WAS two trades

| jr1 trade | R |
|---|---|
| 06-04 L1 | **+2.4680** |
| 06-03 L1 | **+2.1301** |
| | **+4.5981** |

**jr1 without those two: −1.5144R.** Its other ten trades lost money. This was never
"+3 vs −2"; it was "two big LONDON winners vs none".

## Why jr2 passed both — and it is NOT the 0.4.13 change

Both of jr1's winners already carried **2 and 3 target rungs**. They satisfy T78 untouched. The
rung requirement changes how a take is *described*, never whether it is *taken*, and the bounce
fired zero times in 37 emissions. 0.4.13 is exonerated as the cause.

**06-03 L1 — trigger-level divergence on identical evidence.** Both runs cite the *same*
vwap_p2 double rejection (03:08 and 03:15).

- jr1: grade **A**, `take_full`. "Highest-tier anchor, fresh, confluence."
- jr2: grade **C**, `pass`, `constraints_failed: [chop_middle_zone, headroom_defended_level]` —
  entry sat in the chop middle band, and the 15m-proven defended prior-day low was ~14pt below
  entry, inside 0.3R.

**06-04 L1 — THESIS-level divergence. The trigger was obedient.**

- jr1's Tier 1 read the day two-sided-long; the long condition was "fully met" → `take_light`.
- jr2's Tier 1 read it **short**, licensing longs only at 30052–57. Price was 30129.5, ~77pt
  above that zone → `pass` on `direction_mismatch`.

The trigger did the right thing in both runs. It was the *thesis* that differed.

## What the orchestrator's own repair cost

Two of jr2's losers came from mid-run repair work, both contract-correct:

- **06-02 L10 (−1.0000)** — reinstated when the repaired book showed L8 exited 04:28, so L10's
  04:39 fill met a genuinely flat book.
- **06-03 A8 (−1.0000)** — produced by the NY_AM re-adjudication after the escalation flipped
  the thesis long; A8 is a licensed counter-fade under the accommodated read.

**jr2 without those two: −0.1792R.** They were right by the contract and cost 2R.

## The conclusion that matters

Two runs over identical bars disagree by **5.26R**, and jr2's passes are arguably the *more*
disciplined ones — it declined a chop-middle entry with a defended level 14pt away, and honoured
its own thesis direction. The stricter read lost on this sample.

**Neither number estimates edge.** Twelve to fourteen trades, with two of them carrying the whole
result, cannot separate a contract change from luck. The dominant instability is Tier-1 thesis
divergence (06-04 L1), which then propagates deterministically into trigger verdicts — that is
the tractable target, and a thesis-level diff across the five days is the next measurement worth
making.
