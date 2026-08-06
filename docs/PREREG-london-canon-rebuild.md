# PREREG — LDN-CAN-01, the London canon rebuild (L0 census)

**Committed BEFORE the census is analysed. The parity gate ran first and passed;
nothing below was written after seeing a trigger count.**

Date: 2026-08-05
Family: `LDN-CAN-01` — Angus's canon geometry (BB / daily-VWAP bands / POC confluence)
applied to the London window
Authorises: `scripts/build_l0_triggers_london.py`
Method of record: `docs/HANDOFF-london-rebuild.md` (written 2026-07-28→31, never run)

---

## 0. What Angus asked for, and what it turns out to be

> *"what if we build a london strategy around my canon strategy. vwap, bollinger bands,
> etc you should know. start top down. raw triggers, etc etc."*

This is not a new family to invent. **It is the London canon rebuild, which is fully
specified in `docs/HANDOFF-london-rebuild.md` and has never been run.** The machinery
already exists — the detector, the substrate builders, the depth loader, the span
switches. What does not exist is an honest trial of any of it.

## 0.1 The strategy in plain terms (so the object being tested is unambiguous)

**Levels.** Three kinds, and only three: **Bollinger Band** levels on the entry
timeframe, **daily-VWAP deviation bands**, and the **volume-profile POC**. Where two or
more of them stack close together, that is a *confluence cluster*.

**Triggers.** Two mechanical shapes against a cluster:
- **rejection block** — a candle wicks into the cluster and closes back out beyond all of
  it, leaving the wick through
- **displacement** — a candle's *body* closes through ≥2 levels of one cluster, with
  body/range above a floor and the close in the extreme quartile of the range

**Pattern tag** — context of the close-through, not candle shape:
- **A** = reversal (reverses a recent ±2 daily-VWAP over-extension, counter-trend)
- **B** = continuation (with-trend, off a stacked confluence)
- **B2** = rejection / fade (wick into a level, close back, fade off it)

**Entry.** A limit on the **retest** of the closest structural level (POC / VWAP band /
BB MA). Not a market order at the trigger.

**Stop.** Beyond the wick extreme or the displacement origin.

**Angus's own sizing ladder (v1.1 §9), which is a rule and not a finding:** FULL =
BB+VWAP+POC; HALF = two levels including BB+VWAP; **NO TRADE without both BB and VWAP.**

**Window.** 08:00–10:00 Europe/London, converted per-day to ET — 03:00–05:00 normally,
04:00–06:00 on DST-misaligned weeks. Never hardcoded ET hours (handoff burn-list item 1).

## 0.2 The old London book is NOT the baseline

`output/london_canon_book.parquet` exists and `scripts/london_canon.py` advertises 2025
+$22,219 / 2026 +$13,000, WR ~60/56%, PF 3.3/2.4. **Those numbers are treated as history,
not as truth, and this rebuild does not start from them.** They come from un-governed
research sizing on checks that, in the handoff's own words, *"were never honestly trialed."*
`docs/CANON.md` already calls that book "a reference to beat, not a book to trade."

Nothing in this family inherits a threshold from that book. Every check it used
(`W`, `FAR`, `ROOM`, `ASIA`) is re-derived and re-trialled from scratch at L3, or it does
not ship. The NY rebuild killed `C`, `PAQ`, `X` and `LONSLOPE` and demoted five more; the
prior here is that London loses checks too.

---

## 1. Span, and what stays sealed

- **Primary build span (§5.11.9a): 2025-06 → 2026-07**, the 13 months with candles + flow
  + depth all present. **Discover on 2025 months, validate on 2026.**
- **SEALED, untouched by this rung and every rung before L4 signs off:** the 2023/24
  sealed days (`data/reference/holdout_2023_24_days.csv`),
  `data/reference/depth_london_2023_24` (128 days), and the sealed flow months. **One
  look, at the very end, declared in the §4 ledger first.**
- L0 uses **bars only**. No depth, no tape, no order flow. Those enter at L3.

## 2. What L0 does, and its gate

Regenerate every trigger the production detector fires in the London window, from bars,
with **no selection of any kind** — no caps, no stop gate, no score, no pattern filter, no
order flow. L0 answers one question: *what does the canon's own geometry fire on in
London?*

**GATE — parity against the cached London stream.** On three overlap days spread across
the span, one of them deliberately DST-misaligned, the regenerated stream must match
`output/triggers_london.csv` on the identity columns (`ts`, `tf`, `direction`, `kind`,
`entry_ref`, `stop_ref`).

**STATUS: RAN BEFORE THIS PREREG WAS COMMITTED, AND PASSED.** 2025-06-10 39 vs 39,
2025-11-05 53 vs 53, 2026-05-13 16 vs 16 — IDENTICAL in every case. Recorded here rather
than claimed later.

## 3. Event-universe sensitivity is built in from stage one (§5.11.2)

`--band wide` detects over **07:30–10:30 Europe/London** against the standard
08:00–10:00. Both are built at L0 and both are reported on the data card.

This is deliberate and it is the direct lesson from `LDN-PO3-01`, which was killed twice
before anyone asked what widening the window did — and when it was finally asked, the
answer changed the trade count by 13%. The question is answerable here without a re-run,
at stage one, for free.

### AMENDMENT (ANGUS 2026-08-05, mid-run — recorded, not silently applied)

> *"dont worry about 7:30 to 10:30, im only interested in 8-10"*

**The wide band is CANCELLED.** The `--band wide` run was killed before it produced a
parquet and **no wide-band number was ever computed, seen, or reported.** The window for
this family is 08:00–10:00 Europe/London, full stop.

Consequences, stated so nothing is quietly lost:

- The §5.11.2 event-universe item is **NOT closed at L0**. It moves to L1, where the
  honest universe questions on this family are different and cheaper anyway: **which
  timeframes are in scope** (the detector fires on 1/2/3/5-minute), **whether both
  patterns trade**, and **the order-cancel policy** (orders die at the window end per the
  standing ruling, versus a distance cancel). Those are re-entry and universe questions
  that live inside the declared window.
- The rung table in §5 is updated accordingly: L0 closes item 5 only; item 2 is owed at L1.
- `scripts/build_l0_triggers_london.py` keeps the `--band` switch. It is not deleted,
  because deleting it would hide that the question was asked. It is simply not run.

## 3.1 AMENDMENT — the position is the SETUP, not the trigger (ANGUS 2026-08-05, at L1)

> *"big thing is overlapping entries. for example if it broke the 1 minute bb ma, and then
> 3 minute as well after the 1 minute filled, it should not double up on the same trade...
> i dont scale my entry just because it broke the MA on multiple time frames
> sequentially."*

**This is a defect in the L1 population, not a refinement.** L1 walks every trigger
independently so execution capacity cannot shape the population — correct — but one move
through a BB basis trips the 1-minute, then the 2-minute, then the 3-minute, and L1
counted that as three trades. The detector has always resolved **simultaneous** multi-TF
collisions ("highest TF wins", §1 MTF arbitration). **Nothing ever resolved sequential
ones.**

Measured on the fit span before any rule was written:

| same-direction fill following an earlier one | share |
|---|---:|
| within 5 min and 2 pts | 52.1% |
| within 15 min and 5 pts | 73.9% |
| **sharing an actual cluster LEVEL, within 15 min** | **97.7%** |

They are structurally the same setup, not merely adjacent in price.

**THE RULE, declared — a fill joins an OPEN setup when, in the same day and direction, it
lands within 15 minutes of that setup's FIRST fill AND either shares a cluster level name
with it, or fills within 5 points of it.** Window runs from the setup's first fill, never
its latest, so a chain cannot extend a setup indefinitely. Thresholds: 15 min because the
entry timeframes span 1–5 minutes and a cluster re-trips within a few bars; 5 points
because that is about one median intended stop (4.00 pt).

**Effect: 7,239 fills → 1,804 setups, 6.8 per session. 75% of the fill population was the
same trade counted again.** Only 20.5% of setups are singletons; the median setup collapses
3 triggers, the largest 18.

**Tie-break — which member of the setup is actually traded. Two arms, both recorded,
neither enforced here:**

- **`setup_first` — the earliest fill. DEFAULT, on causality.** At the moment the 1-minute
  fills you do not yet know a 3-minute is coming, so taking it needs no foreknowledge and
  no waiting. Same principle as the L4 burn-list rule *"first-N-clearing, never
  best-of-day"*.
- **`setup_htf` — the highest timeframe in the setup. DECLARED CHALLENGER.** Live it
  requires standing aside for an arbitration window and may select a fill that has already
  happened. **Its causality must be proven before it can be traded**, and it does not
  displace the default on in-sample rank (§6.0.1).

The two arms trade the **same setups** and differ only in which entry is used:

| arm | n | /session | timeframe mix | median risk |
|---|---:|---:|---|---:|
| as walked (no dedup) | 7,239 | 27.4 | 1m 22% · 2m 25% · 3m 28% · 5m 25% | 4.00 pt |
| **`setup_first`** (default) | 1,804 | 6.8 | 1m 31% · 2m 29% · 3m 22% · 5m 19% | 4.75 pt |
| `setup_htf` (challenger) | 1,804 | 6.8 | 1m 7% · 2m 9% · 3m 19% · **5m 65%** | 6.00 pt |

Pattern mix is unchanged between them (B2 59–60%, B 33–34%, A 7–8%), so the tie-break is a
pure entry-quality question for L2 and not a different strategy.

**Consequence for §5.11.2:** the event-universe item is closed at L1 by this plus the
timeframe/pattern/cancel tables on the L1 card. The population definition is now the setup.

Implementation: `scripts/l1_london_dedup.py` → `output/l1_fills_london_fit_dedup.parquet`.
Nothing is enforced in that file; both tie-breaks are boolean columns beside the untouched
population, exactly as the cancel policies are.

## 4. Census kill line — declared before the numbers are read (§5.9.1)

L0 is a census. **It can only kill on the premise, never on expectancy.** This family
dies at L0 if and only if:

- the detector fires **fewer than 2 triggers per session on average** in the standard
  band — too thin to build a session book on; or
- **fewer than 60% of triggers carry both BB and VWAP in the cluster**, because Angus's
  own ladder says no-BB-or-no-VWAP is NO TRADE, and a substrate that is mostly untradeable
  under the strategy's own rule is not this strategy.

Anything else — ugly distributions, pattern skew, hour clustering — is reported and
carried forward. **No expectancy claim is made or implied at this rung, in either
direction** (§5.9.2).

## 5. The declared ladder, with the §5.11 checklist mapped in ADVANCE

The failure that killed `LDN-PO3-01` twice was declaring a search complete that had
cleared 2 of 9 checklist items. So the checklist is assigned to rungs here, before the
first number, rather than audited at the end:

| rung | what runs | §5.11 items closed | gate |
|---|---|---|---|
| **L0** census | every trigger, no selection, 08:00–10:00 London | 5 (year/half reporting) | parity vs cached stream — **PASSED** |
| **L1** fills | E3 limits walked once each, no cancels enforced; cancel policies as derived columns | 7 (lookahead audit), 2 (event universe — timeframe scope, pattern scope, cancel policy) | engine fill reproduction to the tick |
| **L2** outcomes | every fill through the REAL engine, V8 management, rr_floor 2.0 | 3 (stop/risk arm class), 1 (MFE/MAE pack) | lookback invariance 7d vs 30d |
| **L3** features + trial | depth, tape, VWAP geometry; every old check re-trialled at re-derived thresholds | 4 (state-conditional), 6 (canon variable map), 9c (in-trade flow) | reproduce old matrix values to 1e-6; family-wise permutation null |
| **L4** policy | caps, sizing, risk as POST-HOC causal walks; 1-lot first | 9b (conviction sizing), 8 (mechanical baseline) | causal unit tests, PBO, DSR |

**Objective at every rung: profit factor at strict cost, era- and half-consistent, with
trade-sequence max drawdown in dollars reported beside it** (Angus 2026-08-05 — the funded
shell's trailing line is a hard constraint PF cannot see). Win rate is a reported column.

## 6. Promotion rule — declared before any tournament (§6.0.1)

**The default spec is the as-taught geometry at Angus's own ladder: cluster must contain
BB and VWAP, limit on the retest, stop beyond the wick extreme / displacement origin.**
Nothing displaces it on in-sample rank. Any alternative needs PBO < 0.5 on the arm matrix
**and** holdout adjudication under the single corrective iteration (§5.9.4).

Every trial, winners and losers alike, to `output/trial_ledger.parquet` at trial time.

## 7. Standing rulings carried in, not re-litigated

From `docs/HANDOFF-london-rebuild.md` §5: rr_floor 2.0 hard on every trade; no distance
cancel, orders die at the session-window end; V8 exits; 1-lot before any sizing; the $700
daily risk budget is account-level and shared with NY, so London does not get its own.

The London risk gate (`risk >= 9.5pt`, no upper cap) is **carried in as a hypothesis to
re-test at L2, not as a rule** — the handoff is explicit that it must be tested on the
honest population the way NY's 7–60 band was.
