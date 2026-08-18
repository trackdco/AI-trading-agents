# j49 pre-registration, scored against the landed book

`docs/PREREG-j49-postmortem.md` registered five falsifiable predictions before the j49 book
existed. The book is now complete — 77/77 candidates, all five days reconciled, **−4.1589R
blended / −4.6096R full-target**. Here is each prediction against it, scored the way it was
written rather than the way it would be convenient to read.

**Three of the five failed. One is half-confirmed. One failed in the specific way the
pre-registration itself nominated as exonerating the chop map.**

---

## P1 — half confirmed

> the j49 05-31 book contains PASS rows at ~03:12/03:18 whose `reason` cites chop / middle /
> the range map (not freshness, not thesis disagreement).

Both minutes are PASS rows, so the verdicts and the timing land. The *reasons* only half land:

| cid | min | verdict | cites the map? | what it actually cites |
|---|---|---|---|---|
| L1 | 03:12 | pass | **no** | the Monday no-gap rule and the thesis's stand_aside. It then escalated, and the thesis REAFFIRMED. |
| L2 | 03:18 | pass | **yes** | `constraints_failed: [direction_mismatch, chop_edge_mismatch, sequential_pair_no_override_reason]` |

One of the two passed for a map reason and one passed for thesis reasons. **Half confirmed.**

## P2 — FAILED

> same at ~03:22 on 06-03.

06-03 at 03:22 is **not a pass**. It is `L1`, `take_light`, conviction A, filled at 30493.00
and stopped at 30523.00 at 03:30 for **−1.0000R**. The map did not bar that minute; the trigger
took it on the thesis's own other-side clause and lost.

The pre-registration named this exact outcome and named its consequence:

> If P1/P2 FAIL — j49 took those minutes and still bled, or passed them for non-map reasons —
> the map is exonerated for the missed-runner half and H1/H4/H5 take the weight.

P2 failed in precisely that manner. **By the pre-registration's own rule, the chop map is
exonerated for that half.**

## P3 — FAILED, decisively

> j49 avoided most of jn1's −2.00R 06-02 London churn (the map working as designed on a range
> that held).

It did not avoid it. It reproduced it. j49's 06-02 LONDON took **three fills for −1.7000R**,
fading the *same* weekly-VAH / daily-VAH / VWAP+1 cluster at ~30723–30729 three separate times:

| cid | in | out | R |
|---|---|---|---|
| L6 | 30713.00 @ 04:03 | stopped 30728.00 @ 04:05 | −1.0000 |
| L8 | 30711.00 @ 04:25 | stopped 30735.00 @ 04:28 | −1.0000 |
| L10 | 30723.00 @ 04:48 | trailed out 30718.50 @ 05:00 | **+0.3000** |

L10 was the third attempt and the only one whose stop ever moved. It was also **beyond the
written cap of 2**, taken only because caps are lifted for this run.

In the agents' favour: they were not blind to the repetition. L8 cited L6's stop-out as grounds
to place its stop above it; L10 graded itself down from the flat-book `take_full` to
`take_light` explicitly because it was "the 3rd test of this zone this window after 2
stop-outs". They saw it and took it anyway.

## P4 — FAILED as stated

> a plurality of j49's red fills are edge-zone entries under CHOP citing the map licence,
> overrun when the range broke.

Of the ten red fills:

- **3 of 10** cite chop / range / edge in the take reason — not a plurality.
- **10 of 10** sit at `zone_now: middle`. **Not one** was an edge-zone entry.
- **7 of 10** were under `TRENDING`, not `CHOP`.

The prediction described losses at the range edge overrun by a break. The book says the losses
were in the *middle*, mostly in sessions the map had already labelled TRENDING.

## P5 — FAILED as stated

> NY-window selection under TRENDING is broadly unchanged vs jn1 (map silent there), so the
> delta concentrates in London/pre.

The delta does not concentrate in London/pre. NY_AM holds j49's **largest winner** (06-03 A3,
+2.7247R blended including an accepted T53 clip) *and* three of the ten red fills. Across the
week NY_AM is **+2.0611R** and LONDON is **−5.7000R**. London is worse, but NY is not "broadly
unchanged" — it is carrying the week.

---

## What the book DOES say — the one clean structural difference

Splitting every fill in both runs by the `chop_state` recorded on its own trigger row at its
own decision minute:

| | fills | R | avg |
|---|---:|---:|---:|
| **w49 — CHOP** | **0** | — | — |
| w49 — TRENDING | 23 | +14.7758R | +0.6424R |
| **j49 — CHOP** | **5** | **−2.5088R** | −0.5018R |
| j49 — TRENDING | 11 | −1.6501R | −0.1500R |

**w49 never took a single fill in a CHOP session. j49 took five, every one of them in LONDON,
and they lost 2.51R between them.** That is the cleanest structural difference between the two
weeks and it is a *selection* fact, not a management one.

It is not the whole story, and the second row matters: j49's TRENDING fills also lost (−1.65R
over 11) where w49's won (+14.78R over 23). Zone does not separate them either — w49's
middle-zone fills made **+8.82R** over 14 while j49's made **−2.15R** over 10, on the same map
and the same labels.

## Where that leaves the hypothesis set

- **H2 (chop map redirected selection)** — partly implicated, partly exonerated. Implicated:
  the only CHOP fills in either run are j49's, and they lost. Exonerated: by the
  pre-registration's own P2 rule, and because the red fills are middle-zone under TRENDING,
  not the edge-zone-under-CHOP shape H2 predicted.
- **H5 (variance/regime)** — cannot stay "residual only". The independent measurement in
  `docs/FINDING-j49-entries-not-management.md` shows mean maximum favourable excursion of
  **0.97R** in j49 against **2.45R** in w49, with **9 of 16** j49 fills never reaching even
  +0.75R at any point between fill and stop. The trades did not go wrong late; most never
  worked at all. That is the largest single effect measured here.
- **H1 (machinery defect)** — still to be excluded, and it should be. This run cannot certify
  itself. Every j49 briefing passed the tightened leak guard (751 checked, zero real leaks) and
  every capture cursor was verified against independently-computed arithmetic — which caught
  two genuine `replay_status` drift incidents — but offline regeneration against a second
  implementation is a different test and has not been run.

## Caveats, stated rather than buried

Sixteen fills and twenty-two. Every effect above is measured on samples that small. The
direction of the CHOP result is clean because the count is zero on one side, but zero out of 23
is still only 23 observations. Treat the shape as real and the decimals as indicative.

Nothing in this document fed either run. Every verdict was made before any of it was computed.
