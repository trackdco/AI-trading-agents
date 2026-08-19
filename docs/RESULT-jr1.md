# RESULT: jr1 (June walk-forward, session-days 2026-05-31 .. 2026-06-04)

**12 trades · +3.0837R blended (as-run) · +9.0400R full-target · 5 winners (42%)**

Cross-checked two ways that are built to disagree: `score.py` sums `exit` rows, `closeday.py`
sums window closes grouped independently and refuses to write when the two differ. All five
days wrote clean and the sums agree exactly:

```
-1.0000 + 0.5913 - 2.5719 + 3.6570 + 2.4073 = 3.0837
```

## Per day

| session-day | cand | takes | fills | blended | full-target |
|---|---|---|---|---|---|
| 2026-05-31 | 13 | 2 | 1 | -1.0000 | -1.0000 |
| 2026-06-01 | 17 | 3 | 3 | +0.5913 | +2.0444 |
| 2026-06-02 | 19 | 3 | 3 | -2.5719 | -3.0000 |
| 2026-06-03 | 15 | 3 | 2 | **+3.6570** | +4.7600 |
| 2026-06-04 | 13 | 4 | 3 | **+2.4073** | +6.2356 |

The week is carried entirely by the back half, and both of those days are **LONDON-led**
(06-03 L1 +2.13, 06-04 L1 +2.47). That is the opposite of wr2, where NY_AM did the work.

## jr1 vs wr2

| | wr2 | jr1 |
|---|---|---|
| trades | 17 | 12 |
| winners | 14 (82%) | 5 (42%) |
| blended (as-run) | **+16.5304R** | **+3.0837R** |
| full-target | +11.0002R | +9.0400R |
| as-run minus full-target | **+5.5302R** | **-5.9563R** |

The two books are near mirror images on that last line: in wr2 management **added** +5.53R;
in jr1 it **cost** -5.96R. Same contracts, same manager, opposite sign.

### Do not read that as "management failed in jr1"

`full-target` holds the whole position on its original stop to the target, so it gives no
credit to the mandated 50/50 partial. Decomposed:

| bucket | trades | effect |
|---|---|---|
| saves (thesis failed, cut early) | L8, A6, 06-04 P2 | **+1.3995R** |
| cost of the mandated TP1 partial on trades that reached target | 06-03 L1, 06-04 L1 | -2.8812R |
| trailed out of a trade that then worked | 06-01 A2, 06-01 A3, 06-03 A3, 06-04 A5 | -4.4746R |

Only the third bucket is management *losing*, and 06-04 A5 alone is half of it (-2.23R, the
counter-example logged in FINDINGS-wr2-T78.md). The second bucket is the split doing exactly
what it is designed to do.

## The 75/25 question flipped as the sample grew

| sample | as-run | 75/25 | 75/25 ahead by |
|---|---|---|---|
| n=1 | 0.5913 | 0.8534 | +0.2621 |
| n=2 | 2.7214 | 2.8302 | +0.1088 |
| **n=3** | **5.1894** | **5.1387** | **-0.0507** |

Both trades that pull it negative are the two whose runners actually **reached target_2**.
Banking less early is right exactly when TP2 is real - so the split ruling and the T78
two-target mandate are the same question asked twice. A book whose runners reliably reach a
real TP2 should want a *smaller* early partial, not a larger one.

wr2 still favours 75/25 on its own sample (n=4, +0.5397R). Both samples are tiny; this is the
mechanism, not a verdict.

## Open for ruling

Two `harness_finding` rows carry `ruling_needed`; both were decided conservatively in-run and
the superseded verdict retained flagged, per "decide and log, never block":

- **06-02 L10** - trigger returned `take_light` while listing `beyond_written_cap` in its own
  `constraints_failed`. A verdict cannot both fail a mechanical constraint and be a take.
  LONDON cap enforced; take retained flagged `SUPERSEDED_LONDON_CAP`.
- **06-03 A8** - A6 (10:21) and A8 (10:54) were briefed with byte-identical position state and
  read it opposite ways: A6 refused on the already-open gate, A8 took light citing the same
  fact only as a sizing input. Gate enforced to match A6 and the 06-02 L6 precedent; A8's take
  retained flagged. The briefing's `cap_note` ("caps are lifted-with-tags") sits next to the
  open-position line and may be licensing the wrong reading.

Four tooling defects found and fixed during the run are in
`docs/FINDING-jr1-legend-is-not-bar-constant.md`; duplicate `exit` rows in the reference books
are in `docs/FINDING-duplicate-exit-rows.md`.
