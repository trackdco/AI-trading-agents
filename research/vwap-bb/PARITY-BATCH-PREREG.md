# PARITY BATCH P4–P9 — PRE-REGISTRATION — **WITHDRAWN 2026-08-08**

> ## WITHDRAWN. NO INSTANT IN THIS DOCUMENT WILL BE READ BY ANYONE.
>
> **Reason:** the Code-Path Verification Suite closed the parity gate at P2 (`STATE.md`,
> `PARITY-P2-RESULT.md`) and replaced hand-reading with machine verification — 2a's
> spec-derived unit tests, 2b's full-workbench invariants, and 2c's differential
> implementation. P3 was cancelled the same day, for the same reason: Amendment 03 §7
> published its own selection criterion and thereby told the reader a trigger existed at
> the released instant before any chart was opened, which no date-and-time-only discipline
> can repair. This batch inherits the identical structural problem one level up — it is a
> *pre-registered plan* for more hand readings, and no further hand readings will be
> performed.
>
> **A committed pre-registration nobody will execute must be closed deliberately, not left
> to go stale.** This document, including its already-executed draw in §7, is retained in
> full below for the historical record — the seed derivation, the pool construction, and
> the six drawn instants are exactly as committed at `92e2857`, unmodified. **Nothing below
> this notice is in force. Reading it as a live instruction is an error.**
>
> The class-membership file it produced, `PARITY-BATCH-SEALED.md` /
> `data/PARITY-BATCH-SEALED.json`, is likewise withdrawn and stays sealed permanently — not
> because opening it would compromise a blind that will ever be used, but because there is
> no remaining reason to open it at all.

---

# PARITY BATCH P4–P9 — PRE-REGISTRATION

**Written 2026-08-08, BEFORE P3's result is known and BEFORE any instant is drawn.**
Spec `42d6f0f68ed35bef0280be782c58f72059333222047841473ab74d5b9fbd83bf` (A1–A13).
N_trials: 0. Holdout sealed. The archived pre-A8 result stays unopened.

> **This document is committed in TWO parts.** Part 1 — everything down to §6 — fixes the seed
> rule, the draw method, the redraw rule and the scoring rule, and is committed **with no
> instants in it**. Part 2 — §7 — is appended afterwards and contains the draw. The git history
> is the proof that the method preceded the result; if §7 and §1–§6 were ever committed
> together, this pre-registration is void.

---

## 1. Why this exists: Amendment 03 §7's control failed

The P3 control released only a date and a time. It was not enough.

**Amendment 03 §7 published the selection criterion** — *"P3 must be chosen where a trigger
survives past the confluence gate. On 2m, 3m or 5m."* That sentence, written by Angus in his own
runbook, tells the reader **that a trigger exists at the released instant and that it is not on
1m**, before he opens a chart.

**The leak is in the criterion, not in the release.** No date-and-time-only discipline can
repair it, because the criterion had to be published to justify the instant.

### What this costs, stated exactly

| P3 field | still blind? |
|---|---|
| §7 "is there a valid trigger at 10:20?" | **NO — pre-answered by the published criterion** |
| §7 "which timeframes did you check" | not blind — 1m is excluded by A11 and he was told so |
| which timeframe it fires on, and whether more than one does | **blind** |
| direction | **blind** |
| trigger kind — rejection block or displacement | **blind** |
| every level in §1a, §1b, §1c, §1d | **blind** |
| §2 Bollinger values, §3 candles | **blind** |
| §5 HTF classification | **blind** |
| §8 entry, stop, target, and what anchors them | **blind** |

> ### RULING, recorded before P3 is compared
>
> **P3's §7 binary — "does a trigger fire" — is NOT SCORED.** It contributes no MATCH and no
> MISMATCH, and it may not be cited as agreement.
>
> **Everything else in P3 IS scored**: the timeframe, the count of firing timeframes, the
> direction, the trigger kind, every level, and the entry/stop/target geometry. Those were never
> disclosed and remain a genuine test.

**This ruling is fixed now, before the comparison, so it cannot be adjusted to suit the result.**

---

## 2. What P4–P9 fix

A single mixed, unlabelled batch. **Angus is told six dates and times. He is not told which class
any instant belongs to, and the classes are not distinguishable from the release.** The
criterion can therefore be published in full — knowing that *three of six* fire tells him
nothing about *this* one.

| class | n | drawn from |
|---|---|---|
| **F — detector-fires** | **3** | admitted trades under the current spec |
| **R — uniform random** | **3** | all (session, minute) pairs in the workbench, minute ∈ 09:36–15:59 |

**Class F exists** because a random instant almost never reaches the deep code paths — P2 was
random-ish in effect and its only trigger died at the first gate, leaving the trigger predicates,
the RR floor, the stop anchor, the target ladder and the A7 selector untested.

**Class R exists** because class F is a biased sample of the detector's own opinion. Class R is
the only part of this batch that can surface a **false positive** — an instant where Angus sees a
setup and the detector does not — and false positives are invisible to a fires-only design.

---

## 3. Draw method — fixed before drawing

### 3.1 The seed

> **`seed = int(the first 16 hex characters of the git commit SHA of the commit that adds this
> document in its PART-1 form, base 16)`.**

That commit's SHA is not knowable while this text is being written and cannot be steered, so the
seed cannot be shopped. It is recoverable by anyone from `git log`. **The SHA and the resulting
integer are recorded verbatim in §7 when the draw is made.**

### 3.2 The generator

`random.Random(seed)` from the Python standard library — Mersenne Twister, deterministic and
reproducible across machines. **One stream, drawn in the fixed order below.** No second
generator, no reseeding, no `random.shuffle` on a separate instance.

### 3.3 Order of operations, fixed

1. Build **pool R** — every `(session_date, minute)` pair with `session_date` in the workbench
   (2023-01-03 … 2025-01-31), the session **not** excluded by accounting rule §4.3 (roll, session
   after roll, mixed contract, holiday/short), and `minute ∈ [09:36, 15:59]` inclusive.
   Sorted ascending. **No filtering on anything the detector thinks.**
2. Build **pool F** — every trade admitted under the current spec (`spec_current.py`, A8+A9+A10+A13)
   over the same sessions, with `entry_tf ∈ {2, 3, 5}`. Sorted by (date, minute, tf).
   **No scoring, no ranking, no test-design preference — that was the P3 method and it is
   abandoned.**
3. Draw **3 from F** with `rng.sample(F, 3)`.
4. Draw **3 from R** with `rng.sample(R, 3)`, rejecting any that collides with a drawn F instant
   on `(date, minute)`.
5. Apply the redraw rule (§3.4) to all six.
6. `rng.shuffle` the six, then number them **P4 … P9** in shuffled order.
7. Release **dates and times only**.

### 3.4 Redraw rule — fixed now, because redrawing is otherwise a free parameter

An instant may be replaced **only** for a reason that is knowable without looking at the
detector's output for it:

| reason | action |
|---|---|
| Angus reports the platform cannot render 2m/3m/5m at that date | mark **UNREADABLE**, log it, draw the next from the same stream |
| the session is excluded by §4.3 | cannot occur — pools exclude them |
| any other reason | **no redraw** |

**Every discarded draw is logged in §7 with its reason.** A batch with silent replacements is a
batch that was chosen.

### 3.5 Class membership is sealed

Written to `research/vwap-bb/PARITY-BATCH-SEALED.md` at draw time, alongside each instant's
expected detector state. **Not opened until all six readings are submitted.** The release carries
six date-time pairs in shuffled order and nothing else.

---

## 4. Scoring — fixed before any reading

**Field-by-field at 1.00 point tolerance**, MATCH or MISMATCH with both values shown, exactly as
P2 and P3. Every mismatch diagnosed as exactly one of **spec ambiguity · implementation bug ·
charting difference · reading error**. No fifth category. Nothing softened into "close enough".

**Known-unverifiable fields are excluded from scoring, not counted as passes:** the NY VWAP σ
bands (A8 fixes the feed at 1-minute; the platform cannot render it for the workbench window) and
the entire 1m row (A11).

**For class R instants, the §7 binary IS scored** — that is the whole point of the class, and
nothing about those instants was disclosed. **For class F instants it is scored too**, because
the mixed release means the reader cannot know which class he is looking at.

---

## 5. SIX INSTANTS DO NOT SUPPORT AN AGREEMENT RATE

> **No agreement rate will be computed, quoted, or implied from this batch — not "5 of 6", not
> "83%", not "mostly agrees".**

Three reasons, each sufficient on its own:

1. **n = 6.** A Wilson 95% interval on 5/6 runs from roughly 42% to 99%. An interval that wide is
   compatible with a detector that agrees nearly always and one that agrees half the time. It
   distinguishes nothing.
2. **The sample is stratified by design and is not representative.** Half the batch is drawn from
   the detector's own admitted trades — a population defined by the thing being tested. Any rate
   computed over the mix describes the mix, not the detector.
3. **Fields within an instant are not independent.** P2 showed one root cause — the VWAP input
   feed — producing nine mismatched fields. Counting those as nine failures, or as one, are both
   wrong, and no weighting fixes it.

### What the output IS

> **A list of divergences. Each one is a finding on its own terms, and stands or falls on its own
> diagnosis.**

That is what P2 produced and it was worth the exercise: it found four specification gaps that a
pass/fail ratio would have compressed into a single uninformative number.

**A batch in which all six agree on every scored field is reported as "no divergence found in six
instants", never as "the detector is correct".**

---

## 6. What would make this batch void

- §7 committed in the same commit as §1–§6, or the seed not recoverable from `git log`
- an instant replaced for any reason not in §3.4, or replaced without being logged
- class membership disclosed before all six readings are in
- `PARITY-BATCH-SEALED.md` opened early
- any agreement rate reported
- the scoring rule in §4 changed after a reading is seen

---

## 7. THE DRAW

**Executed 2026-08-08, in a commit separate from §1–§6.** Script:
`research/star-trading/tools/parity_batch_draw.py`.

### 7.1 Seed, recoverable by anyone

| | |
|---|---|
| PART-1 commit SHA | **`4014d2e5c31fbeeefe579d35d19558a2850afe87`** |
| first 16 hex | `4014d2e5c31fbeee` |
| **seed** | **`4617547402224582382`** |
| generator | `random.Random(seed)` — CPython Mersenne Twister |

Verify: `git log` → find the commit that added this file without §7 → take its SHA → the seed is
`int(sha[:16], 16)`. **The SHA could not be known while §1–§6 were being written, so the seed
could not be shopped.**

### 7.2 Pools, built per §3.3

| | |
|---|---|
| **pool R** | **192,384** (session, minute) pairs — 501 sessions × 384 minutes (09:36–15:59 inclusive) |
| sessions excluded (§4.3) | holiday/short 22 · roll 8 · session after roll 8 = **38 of 539** |
| **pool F** | **857** admitted trades on 2m/3m/5m under spec `42d6f0f6` (A8+A9+A10+A13) |

**Pool F was NOT scored or ranked.** `rng.sample` over the whole pool. The test-design scoring
used for P3 is abandoned — it is what made P3's selection criterion publishable-and-leaky.

### 7.3 Discarded draws

**None.** No collision, no exclusion, no redraw. Every drawn instant has a bar present.
*(A silent replacement would void this batch — §6.)*

### 7.4 THE RELEASE — dates and times only

Shuffled with the same stream, then numbered. **Class membership is not shown here and is not
inferable from the ordering.**

| | date | time (ET) |
|---|---|---|
| **P4** | **2024-10-30** | **10:15** |
| **P5** | **2024-05-02** | **11:51** |
| **P6** | **2023-08-30** | **09:42** |
| **P7** | **2023-02-17** | **09:39** |
| **P8** | **2023-12-14** | **11:51** |
| **P9** | **2024-01-04** | **09:47** |

Each is read exactly as P2 and P3 were: **Bar Replay to that minute, do not scroll forward.**
"At `hh:mm`" means the bar covering `hh:(mm−1):00 – hh:(mm−1):59` has just closed. Chart labels
by open time, so on 2m/3m/5m step to the last bar that closed **at or before** the stated minute.

Class membership and the detector's expected state for all six are in
[`PARITY-BATCH-SEALED.md`](PARITY-BATCH-SEALED.md) and
`data/PARITY-BATCH-SEALED.json`. **Not opened until all six readings are submitted.**

### 7.5 Two things the release itself makes obvious, stated so they are not mistaken for leaks

**Readability is the live risk.** The draw ran over the whole workbench and landed on
**2023-02 to 2024-10** — every instant is older than the January 2025 window Angus has already
proven he can render. **If the platform cannot show 2m/3m/5m at one of these dates, §3.4 applies:
mark it UNREADABLE, log it, draw the next from the same stream.** That is the only permitted
replacement and it must be logged in this section.

**Three instants sit before 10:00 ET.** At 09:39, 09:42 and 09:47 the NY VWAP has 9, 12 and 17
bars behind it, so under **A13** its σ bands will usually be ineligible and the cluster set will
carry the NY **mid** only. This follows from the released times and A13's published rule — it is
derivable by anyone and reveals nothing about any instant's class or outcome. It does mean those
three instants exercise the **A13 eligibility path**, which no parity instant has tested.
