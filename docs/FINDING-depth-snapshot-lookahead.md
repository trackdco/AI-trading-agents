# FINDING — condensed depth snapshots carry ~59 seconds of look-ahead

**Drafted for Brake's signature. Routes to Angus. Flagged BLOCKING for any depth-feature
deployment, including the NY canon.**

Reproduce: `python -m scripts.verify_depth_lookahead` (read-only, changes nothing).

**Surfaced by** the LDN order-flow literature sweep (workflow `wf_974dbf55-a24`) and then
**independently verified here before being reported**. Nothing in this document is taken on
an agent's word.

---

## The defect

Every condensed depth snapshot is **stamped with the start of the minute but contains the
book state from the end of that minute**.

`scripts/condense_depth.py`:

```
39   df["minute"] = df["ts"].dt.floor("1min")
46   last = g.sort_values("ts").groupby("minute").tail(1)     # LAST message of the minute
54   rows.append(dict(ts=r["minute"], ...))                   # stamped with the FLOOR
```

`tail(1)` takes the final book message of the minute; the row is then labelled with the
floored minute. `src/canon/features.py::depth_at` then selects `dep.ts <= minute`.

**`depth_at` is not the bug.** Its semantics are correct. The data underneath it is
mislabelled, so correct code returns a snapshot from up to 59 seconds *after* the moment it
was asked about.

## Verification — two independent tests

**Test 1 — raw receive time.** Only possible where `ts_recv` survived the condense:

| | London depth |
|---|---|
| `ts_recv − ts_event` | median **59.82s** (p10 59.16, p90 59.98) |
| rows >30s into the labelled minute | **100.0%** |

**Test 2 — snapshot mid vs bar (decisive, works even where provenance was stripped).** A
true start-of-minute snapshot tracks the bar's OPEN; an end-of-minute snapshot tracks its
CLOSE:

| dataset | joined minutes | \|mid − OPEN\| | \|mid − CLOSE\| | ratio |
|---|---|---|---|---|
| **London** (`depth_london`) | 7,200 | 9.00 ticks | **1.00 tick** | 9.0× |
| **NY canon** (`depth_2025`) | 8,946 | 15.50 ticks | **1.00 tick** | 15.5× |

Both datasets are unambiguously end-of-minute state. **The NY canon — the book that ships
first — has the same defect.**

## Scope: what this is, and what it is not

**It is a backtest and calibration bias. It is not a live execution bug.**

A live feed delivers the book as it actually is; there is no future in it. `src/live/` and
`src/desk/` do not call `depth_at` at all today.

**What it does mean:** every historical depth feature was *measured*, and every depth
threshold *calibrated*, on snapshots carrying ~59 seconds of foresight. A feature that
looked informative in replay has strictly less to work with live.

There is a sharp irony worth putting in front of Angus. `src/canon/features.py:68` reads:

> *"the live ingestor MUST call this exact function"*

— written precisely so live and backtest cannot drift. The function **is** shared, so the
intent holds in code. But replay feeds it mislabelled snapshots while live feeds it true
state, so **they drift anyway — through the data, not the code.** The guard was placed one
layer above where the defect lives.

## Affected

`depth_at` is imported by `src/canon/book.py`, `src/canon/features.py`,
`src/canon/ingestor.py` (line 153), `scripts/sierra_parity_replay.py`,
`scripts/london_canon.py`, `scripts/score_canon_span.py`,
`scripts/capture_desk_run_london{,3,4}.py`.

Every `dep_*` number produced by those paths carries the bias — including, per the sweep,
`LONDON-CONVICTION-SWEEP`, `LONDON-LOSER-STATS` and `LONDON-VETO-SCAN`.

**One consolation, and it is real:** those London depth results were **null**. They were
null *with the bias helping them*. A look-ahead advantage that still produces nothing is a
stronger null, not a weaker one. This finding does not overturn any London verdict — it
strengthens them.

**The NY canon is the exposure.** Its depth features were not null, and they were measured
on 15.5×-biased snapshots.

## What I did NOT do

**I have not changed any code.** This touches `src/canon/`, and the standing instruction for
unsupervised work is that live and canon code are not modified without sign-off. The
verification script is read-only and additive.

## Recommended remediation, in order

1. **Do not ship any depth-gated behaviour until this is resolved.** That includes the NY
   canon's depth features.
2. **Re-stamp the condense.** Either label each snapshot with the *end* of its minute
   (`minute + 1min`, honest about what it holds), or take the *first* message of the minute
   rather than the last. Re-stamping is cheaper and loses no data; `head(1)` is truer to
   "state at the start of the minute" but discards most of the minute's information.
3. **Re-derive every `dep_*` feature and every depth threshold** on the corrected data, then
   re-measure whatever the canon claims from them.
4. **Add a regression test** asserting `|mid − bar_open| < |mid − bar_close|` for any
   snapshot labelled at a minute boundary. That single assertion would have caught this at
   the point the condenser was written.
5. **Restore provenance.** The NY files (`ts,side,price,size`) dropped `ts_recv`, which is
   why test 1 is unavailable for them. Keeping it makes this class of defect trivially
   auditable.

## Why this matters beyond the immediate fix

This is the **third** causality-class defect found in this programme, after LDN-SWP-01's
circular direction variable and my own broken placebo in LDN-VT-01. All three were invisible
to the fragility gate, because a look-ahead bias is perfectly robust to trimming — it is a
*correct* signal about the wrong interval.

It is the strongest possible argument for the amendment already proposed in
`LONDON-PROGRAMME-CLOSEOUT.md`: **the causality audit must be executable assertions, not a
prose section a reviewer reads.** A prose audit of `depth_at` would have passed — the
function is correct. Only a test comparing the data against a bar would have caught it.
