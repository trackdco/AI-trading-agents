# PREREG — j49 post-mortem

**Registered 2026-08-18, MID-RUN, before the completed book exists.** His
report from the floor: *"J49 is currently running -6R, so we have brutally
fucked something here, but we will wait till it's finished and see what we've
messed up."* That instruction governs: the run finishes clean on the exact
contracts it started with (trigger 0.4.10 / thesis 0.4.2 / manage 0.3.2 /
macro 0.2.0), and nothing in doctrine changes until he has read the book
trade by trade. This document exists so the post-mortem cannot fit its story
to the data afterwards — every prediction below is dated before the evidence
that will test it.

The instrument this week uniquely provides: **the same tape has been run
twice.** `jn1` (June week 1, 0.4.7-era stack) finished **+7.69R on 22
fills** on these exact bars. j49 is the re-run under the new contracts. The
minute-level diff between the two books is the spine of the post-mortem;
every hypothesis states what it predicts for that diff.

---

## 1. What the mid-run evidence already says (his Mac session's table)

Tagged at 10 fills, two chains still live — recompute at close:

|     | mean MFE | mean MAE | reached +1R unrealised | never past +0.75R |
|-----|---------:|---------:|-----------------------:|------------------:|
| w49 |    2.37R |    0.57R |               19 of 23 |           3 of 23 |
| j49 |    0.57R |    1.11R |                2 of 10 |           7 of 10 |

Accepted from that analysis, and it is good work:

- **Management is exonerated.** The only two j49 fills that reached +1R
  unrealised (d1 P2 → +1.60R, d3 L10 → +1.07R) were trailed and finished
  green. The manager converted everything it was given — consistent with
  every w49-era measurement (manager beats all fixed brackets).
- **A bolt-on trend filter is dead.** Tested at two horizons; against-trend
  was w49's BEST bucket (+11.9R / 11 fills) and j49's two with-trend fills
  both lost. Do not resurrect this idea later.
- **The failure localises to entry selection** — fills with no
  follow-through.

One units check before leaning on the table: **mean MAE 1.11R exceeds the
1R stop distance.** Confirm the ruler — bar-extreme beyond the stop print,
blended-entry chains, or a position actually held past stop distance. It
changes no conclusion above, but "spent more of its life past its own stop"
should not be quoted until the ruler is confirmed.

## 2. The baseline, extracted (jn1 ledger — verified +7.69R)

From `output/agent_runs/*_jn1.jsonl` via `scripts/leak_report.py`'s loader:

| day | cid | window | side | R | note |
|-----|-----|--------|------|---:|------|
| 05-31 | L1 | LONDON | short | **+6.57** | the week's engine; trailed out on the 03:51 bounce |
| 05-31 | L2 | LONDON | short | — | second leg of the chain, no exit row |
| 05-31 | P2 | NY_PRE | long | +0.50 | |
| 06-01 | P2 | NY_PRE | short | +0.00 | breakeven |
| 06-01 | A2 | NY_AM | long | +2.12 | final target |
| 06-01 | A5 | NY_AM | long | +0.14 | |
| 06-02 | L6 | LONDON | short | −1.00 | same-edge churn |
| 06-02 | L8 | LONDON | short | −1.00 | same-edge churn |
| 06-02 | L10 | LONDON | short | +0.00 | third try, breakeven |
| 06-02 | A1 | NY_AM | short | +1.73 | |
| 06-02 | A4 | NY_AM | short | −0.28 | |
| 06-02 | A6 | NY_AM | short | −1.00 | |
| 06-03 | L1 | LONDON | short | **+1.78** | |
| 06-03 | P1 | NY_PRE | short | −0.92 | |
| 06-03 | P3 | NY_PRE | short | −1.00 | |
| 06-03 | A3 | NY_AM | short | +2.26 | |
| 06-03 | A6 | NY_AM | short | −1.00 | |
| 06-03 | A8 | NY_AM | short | −1.00 | |
| 06-04 | L2 | LONDON | short | −1.00 | |
| 06-04 | P2 | NY_PRE | long | −0.43 | flipped |
| 06-04 | P3 | NY_PRE | short | +2.23 | |
| 06-04 | A6 | NY_AM | long | −1.00 | |

Facts about the baseline that reframe "what did we break":

- **The money was three trades.** +6.57 +2.26 +2.23 = **+11.06R** of the
  +7.69R total. Nine of 22 fills lost. Miss the runners and the same week
  is negative even with identical churn.
- **The churn is not new.** 06-02 London put three shorts into the same
  failing edge (−2.00R net) in the BASELINE week too. j49's repeated
  no-follow-through entries have precedent on this tape; jn1 survived them
  because the runners paid for the churn.

## 3. The registered fact: the 0.4.9 map, applied to the baseline's minutes

`scripts/chop_state.py` (causality-gated, as-of) evaluated at jn1's entry
minutes, against the contract text now in force (`tv-trigger.md` §TRADING A
RANGE: *"the middle stays dead — no entries from the middle toward either
side"*; *"trigger in the LOW edge zone → long… HIGH edge zone → short"*):

| jn1 entry | jn1 result | chop_state at that minute | 0.4.9/0.4.10 map says |
|-----------|-----------:|---------------------------|------------------------|
| 05-31 03:12 short (L1) | **+6.57R** | **CHOP** (43pt/3h), zone **middle** | **barred** — middle is dead |
| 05-31 03:18 short (L2) | chain leg | **CHOP**, zone **low** | **barred** — low edge licenses LONG only |
| 06-03 03:22 short (L1) | **+1.78R** | **CHOP** (94pt/3h), zone **middle** | **barred** — middle is dead |
| 06-02 04:03 short (L6) | −1.00R | CHOP (72pt), zone middle | barred — map correctly kills it |
| 06-02 04:24 short (L8) | −1.00R | CHOP (81pt), zone middle | barred — map correctly kills it |
| 06-02 04:39 short (L10) | +0.00R | CHOP (81pt), zone middle | barred |
| 06-01 09:46 long (A2) | +2.12R | TRENDING | map silent |
| 06-02 09:36 short (A1) | +1.73R | TRENDING | map silent |
| 06-03 09:42 short | +2.26R region | TRENDING | map silent |
| 06-04 08:52 short (P3) | +2.23R | TRENDING | map silent |

The arithmetic this registers: **on this tape the map bars ≈ +8.35R of
winners and ≈ −2.00R of churn — a ≈ −6.3R swing versus the baseline from
London CHOP minutes alone**, before a single new losing fill is counted.
The map cuts both the poison and the medicine; on a week where the ranges
BROKE, the medicine was bigger.

Two supporting facts, also established pre-book:

- **The candidates were presented.** `scripts/offline_scan.py 2026-05-31`
  emits 03:12 DOWN and 03:18 DOWN (and 06-03 03:22 is jn1's own take
  minute). So the j49 book must contain explicit adjudication rows at those
  minutes — this is checkable as PASS-with-reason, not an absence.
- **The runners were not captured — already known.** His session reports
  j49's only green fills are d1 P2 and d3 L10. A same-minute take of 05-31
  03:12 or 06-03 03:22 on identical tape reaches ≥ +1R unrealised and the
  manager "converted everything it was given" — so a green London fill
  would exist on d1 or d4 if either runner had been taken. None does.

**The mechanism, stated precisely.** Middle-is-dead is not new — T50 had
it — but T50 was scoped to *"a VERIFIABLY choppy day — the standing
thesis's own chop read — not on any day with a range."* 0.4.9 replaced that
day-level scoping with a mechanical trailing-3h flag delivered in every
briefing. A 43pt pre-London coil on what became the best trend day of the
month now arrives pre-labelled CHOP+middle, and the contract's plain text
bars the entry. `chop_state.py`'s own docstring warned it cannot tell
05-31 from 06-02 through London (*"Both mornings were ranges. One held and
paid; the other kept failing at the same edge"*) — it was built as a state
detector, and the contract wired it into a veto. **The map also has no
break-of-range clause**: when a range resolves by breakout, the licensed
trade under the map still points back inside. His session's independent
finding — *"a 'rejection' at a band edge in a market that keeps going isn't
a rejection"* — is the same hole seen from the losing side.

## 4. Predictions (falsifiable when the book lands)

- **P1** — the j49 05-31 book contains PASS rows at ~03:12/03:18 whose
  `reason` cites chop / middle / the range map (not freshness, not thesis
  disagreement).
- **P2** — same at ~03:22 on 06-03.
- **P3** — j49 avoided most of jn1's −2.00R 06-02 London churn (the map
  working as designed on a range that held).
- **P4** — a plurality of j49's red fills are edge-zone entries under CHOP
  citing the map licence, overrun when the range broke.
- **P5** — NY-window selection under TRENDING is broadly unchanged vs jn1
  (map silent there), so the delta concentrates in London/pre.

If P1/P2 FAIL — j49 took those minutes and still bled, or passed them for
non-map reasons — the map is exonerated for the missed-runner half and
H1/H4/H5 take the weight.

## 5. Hypothesis set (standing updated 2026-08-18, pre-book)

| # | hypothesis | standing now | decisive test |
|---|-----------|--------------|---------------|
| H1 | mid-run machinery change (the "efficiency" speed-up; w49 never ran the fast path) corrupted briefings/fills | **must be excluded FIRST** — a defect voids the measurement | certify j49 briefings against offline regeneration on landing; ask the Mac session what changed and which days ran under it |
| H2 | 0.4.9 chop map redirected selection (bars middle/breakout entries, licenses edge fades into breaks) | **prime suspect** — §3 | P1–P5 on the book; per-fill chop_state + cited licence |
| H3 | wider take licence changed composition | early read against volume (10 fills by d3–4 vs jn1's 22/wk is not inflation); composition diff still open | minute-level take/pass diff vs §2 ledger |
| H4 | inflated baseline — jn1 carried the §10h stale-chart defect (days 2–3), a +0.50R tripwire miss, mid-week contract edits | real but partial: it shrinks the delta, it cannot make −6R a good week | re-score jn1 excluding tainted rows; honest baseline band |
| H5 | variance/regime at ~10–20 fills | residual only | reached only after H1–H4; never first |

## 6. Order of operations when the book lands

1. **Certify** (H1): j49 briefings vs offline regeneration; row-schema diff
   between slow-path and fast-path days.
2. **Diff** (H2/H3): j49 takes/passes vs the §2 ledger, minute by minute.
3. **Tag** (P1–P5): every j49 fill and every jn1-winner minute with
   chop_state, zone, and the licence/veto the agent actually cited.
4. **Re-baseline** (H4): honest jn1 band with defect rows excluded.
5. **Only then** doctrine — with him, trade by trade, per the ANCHOR. The
   fix shape if H2 confirms is NOT deleting the map: it is scoping it (what
   counts as a rejection worth taking; a break-of-range clause; whether
   middle-dead needs its day-level scoping back). Not one word of contract
   changes before his read.

## 7. Standing constraints until then

- **No contract edits mid-run.** jn1's mid-week edits are exactly why its
  own baseline needs re-scoring (H4). Do not manufacture the same confound
  twice.
- The run finishes on 0.4.10 whatever the tape does.
- Asks of the Mac session, with the book: (a) what exactly the efficiency
  change altered and which days ran under it; (b) confirmation that zero
  contract edits happened mid-run; (c) the MAE ruler (§1); (d) push
  `output/books/j49/` and `tmp/FINDING-entries-not-management.md` on
  completion — nothing j49 exists on any remote as of this registration.
