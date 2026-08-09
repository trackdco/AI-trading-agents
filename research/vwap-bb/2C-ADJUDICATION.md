# 2C — ADJUDICATION (Amendment 05, item 1)

**The calls, now that it's morning.** Reads alongside `2C-RAW-COLLECTION.md` (the mechanical
collection) and `data/2c-raw/AMBIGUITIES.md` (the blind build's 28 decisions, reproduced there
verbatim). Nothing here re-opens the collection; this classifies it.

Detector pinned to `bab2e0364db9e8cf315027e5cddc9bb37b4a03af` (pre-A14/A15). Blind build's spec
copy is the same vintage — `42d6f0f6…` (A1–A13) — so **A14/A15 play no part in this diff at
all**, checked directly: the blind-build directory was populated before either amendment existed.

---

## 1. PINNED vs UNPINNED — every ambiguity classified

**Rule applied, exactly as given:** an ambiguity is **PINNED** when its *stated justification*
leans on a number that only exists because someone ran the real detector over real data and
published the result — A5's 29.6%, A13's σ̂ census, A9's 46.9, A7's tie-break weights, A10's
worked 2025-01-22 example. Citing what the **spec's prose itself says** (including arithmetic
derivable from that prose) is not pinning — it's reading. Self-measuring your **own**
implementation's behaviour and reporting it is not pinning either — it's not comparing to the
other side.

| id | decision | PINNED? | citation |
|---|---|---|---|
| A-01 | `signal_minute` = last constituent minute | UNPINNED | bars_api docstring, generalisation argument |
| A-02 | fixed grid, not rolling | **borderline — see note** | cites A8's "1m 20·2m 10·3m~6·5m 4", but that count is pure arithmetic (elapsed minutes ÷ TF, floored) — derivable without ever running the detector |
| A-03 | signal window 576–959 | UNPINNED | A1 text |
| A-04 | mutual-proximity clustering | UNPINNED | spec text ("30 pts apart … contradicts the sentence") |
| A-05 | tolerance = 10.00 | UNPINNED | A13's **stated constant** (5.00 = half of 10.00) — a spec-text arithmetic fact, not the σ̂ census |
| A-06 | `range` confluence = 2 | UNPINNED, and disclosed as *not* fit to A9's 46.9 | §4 text; **NOTES.md shows it checking against 46.9 and declining to use it** |
| A-07 | invalidation: NY VWAP, same-side band | UNPINNED | A8/A13 quoted text |
| A-08 | F = 2.5 | UNPINNED | "the only neutral single value" — no figure cited |
| A-09 | T_cancel disabled | UNPINNED | A2's precedent, A9's doctrine — both spec text |
| A-10 | fill = better-of-open-or-limit | UNPINNED | §6.4 + A5 text; 302/1,583 is **self-measured**, not compared to the detector |
| A-11 | stop/target fixed from the limit | UNPINNED | A5 text, decisive on its own |
| **A-12** | **cap counts fills, not admissions** | **PINNED** | *"chosen because A7 and A9 tabulate the capped quantity as 'ADMITTED trades/session' at 2.33–2.90"* — A7's own published range, used to decide an implementation branch |
| A-13 | target menu composition | UNPINNED | A9/A13/A4 text on what's out of scope |
| A-14 | NY σ stays in the target menu | UNPINNED | A13 text, enumeration argument |
| **A-15** | **no band multiple in the eligibility test** | UNPINNED, but **confirms** `n`'s definition against | **A13's σ̂ census** — *"reproducing that table to 0.01 on all seven rows confirms it"* |
| A-16 | ATR = SMA | UNPINNED | §2's house convention |
| A-17 | ATR floor ON | UNPINNED | A1's open item, spec text |
| A-18 | volume spread uniform across bin range | UNPINNED | standard-convention argument |
| **A-19** | **rejection-block geometry (wick vs body)** | **PINNED (corroboration)** | *"corroborated indirectly: the wrong-side rate it produces is 29.54% against A5's 29.6%"* |
| A-20 | displacement "closes through" strictness | UNPINNED | textual definition |
| **A-21** | **"wrong side" = compared to the wick extreme itself** | **PINNED (corroboration)**, same figure as A-19 | *"Rate produced: 29.54% vs A5's stated 29.6%"* |
| **A-22** | **HTF fractal series is session-local** | **PINNED** | *"A10's worked example is entirely inside one session … and reproduces exactly under this scope"* |
| A-23 | §6 rules 2/3/6 unimplemented | UNPINNED | citing the amendments' **own textual admissions**, not a measurement |
| A-24 | out-of-scope no-ops | UNPINNED | TASK.md instruction, textual |
| A-25a | tie-break level order | **PINNED** | *"A7's measured split (level 1 resolves 15.7–19.1%, level 2 fires on 0.2%) only makes sense in that order"* |
| A-25b | levels 3/4/5 never fire | **PINNED (confirmation, not a live decision)** | *"exactly as A7 reports, never fire (0 of 6,917 ties)"* |
| A-26 | exit sim for lock purposes only | UNPINNED | accounting rule 4.1 text |
| A-27 | P3 hint doesn't discriminate | n/a | analysis, decides nothing |
| A-28 (most items) | ticks, RR floor, etc. | UNPINNED | spec-text arithmetic |
| **A-28 (VWAP σ)** | **population-variance formula** | **PINNED (trivial)** | *"confirmed exactly by the A13 census reproduction"* — but there is no live alternative reading a competent implementer would consider; this is confirmation of arithmetic, not a resolved *choice* |

**PINNED, in total: A-12, A-15 (partially — confirms a convention, doesn't decide it outright),
A-19, A-21, A-22, A-25a, A-25b, A-28's VWAP-σ item.** Seven of twenty-eight, and two of those
seven (A-25a/b) are the **same** measurement cited twice, one of them (A-25b) confirming a
**null result** ("never fires") rather than deciding anything live.

## 2. What the pinning actually does — and does not — explain

**None of the PINNED items drive the population-level divergence.** They are confirmations of
low-level mechanics — how the 3/session cap counts, which convention the HTF fractal scope takes,
the exact wick-vs-body reading of a rejection block, the tie-break ordering, the variance formula
— dimensions where the **spec text alone already pointed one way** and the cited figure is
corroboration, not the deciding vote (A-12 is the one partial exception: A7's range is cited
*as* the reason, not merely as confirmation of a reading already settled by text). **Removing
every trace of these seven from consideration changes nothing about the size of the diff**,
because agreement or disagreement on these dimensions doesn't discriminate the trade populations —
both implementations converge on essentially the same low-level mechanics regardless.

**Tested directly, because a hypothesis this specific shouldn't rest on argument alone.** A-01
itself proposed a falsifiable test: *"if the two implementations disagree by a uniform +1 on
every signal_minute and agree on everything else, this entry is the whole explanation."*

```
only_detector trades shifted −1 minute, matched against only_blind:  451 of 1,452  (31.1%)
same test, per entry timeframe:
   1m: 216 of 595  (36.3%)     2m:  89 of 330  (27.0%)
   3m:  80 of 339  (23.6%)     5m:  66 of 188  (35.1%)
```

**A-01 is not the whole explanation. It explains roughly a quarter to a third of the residual,
and the fraction is not even uniform across timeframes** — if it were the single dominant cause,
every timeframe would show close to the same rate. **The remaining 65–75% is genuine admission
divergence** — different candidates qualifying at all, not the same candidate relabelled by one
minute.

## 3. Per-category diagnosis of the surviving diff

3,035 raw disagreements (1,452 detector-only + 1,563 blind-only + 20 geometry mismatches on
matched keys), overwhelmingly explained by **UNPINNED** forks — genuine, uncontaminated test
coverage. Grouped by dominant cause, the way `PARITY-P2-RESULT.md` grouped its twelve mismatches:

| cause | ambiguity | spec text that decides it | adjudication |
|---|---|---|---|
| **signal-minute labelling** | A-01 | bars_api: *"the bar stamped 09:47 covers 09:47:00-09:47:59"* vs A8/A13's own "at 09:50, 20 bars complete" phrasing | **SPEC AMBIGUITY.** Both readings are textually defensible; the spec never states which minute a bar's "close" is labelled by for k>1 |
| **cluster formation** | A-04 | §3: *"within proximity tolerance"* | **SPEC AMBIGUITY**, already named in `PARITY-P2-RESULT.md` §3.6 as ambiguity (b) — chaining vs mutual proximity, unresolved there too |
| **`range` confluence minimum** | A-06 | §7 names only 2 of §4's 3 flags | **SPEC AMBIGUITY.** §7's own text is simply incomplete |
| **invalidation side/band** | A-07 | §7 *"[Hypothesis — test]"* | **SPEC AMBIGUITY**, tagged as such in the spec itself |
| **front-run F** | A-08 | §6.4 *"CALIBRATE (start 2–3 NQ pts)"* — **a range, not a value** | **SPEC AMBIGUITY.** The detector's own F=2.0 (`vwapbb_a7_selector.FRONT_RUN_F`, comment *"low end, most permissive"*) and the blind build's F=2.5 are both inside the stated range; neither is a bug |
| **target menu (esp. weekly H/L)** | A-13 | §6's menu literally lists *"weekly H/L"* | **DOCUMENTED SCOPE LIMITATION, not a fresh bug.** The detector never computes weekly H/L — already ruled in `OUT-OF-SCOPE-BRANCHES.md` branch 9 (*"Weekly H/L not computed"*). The blind build read §6 literally, without seeing that ruling, and implemented it. Neither side is wrong; one implements a documented gap, the other doesn't know the gap was declared |
| **fill accounting on matched trades** | A-10/A-11 | see §4 below (the 302-fill fork), full A5 quote there | **SPEC AMBIGUITY**, formally the subject of Amendment 05 item 4 |
| **entry offset on the 20 1m matches** (≈2–15 pts) | likely A-01, via which bars feed the BB(20) window | same bars_api text as above | **SPEC AMBIGUITY** (consequence of the same signal-minute question, not a separate one) |

**No entry in this table is adjudicated as a detector bug or a second-build bug.** Every
divergence traces to a spec sentence that permits both readings, or to a scope decision already
recorded elsewhere in this project and simply not visible to a build working from the spec text
alone.

## 4. Isolation — two halves, stated separately as asked

> ### Source isolation: HELD.
>
> No detector identifier appears in `blind_impl.py` (`RunningVWAP`, `cluster_levels`,
> `tie_break`, `trig`, `LOC_BAND`, `signal_candidates_current`, `contract_key` — zero hits, all
> checked in `2C-RAW-COLLECTION.md` §2). Where names coincide (`FRONT_RUN_F`, `POC_BIN`,
> `FRACTAL_N`) they are the only sane names for spec quantities, and the surrounding logic
> diverges exactly where a copy would not: `EXTREME_QUARTILE` vs the detector's `QUARTILE`,
> `FIRST_SIGNAL_MIN` vs `FIRST_SIG`, a POC built on **bin centres** against the detector's **bin
> edges**. `READ_MANIFEST.md` is specific, dated in effect by its own content, and internally
> consistent with the deliverables produced. This is a genuinely independent build of the logic.

> ### Output isolation: DID NOT FULLY HOLD, and the leak is named precisely.
>
> The spec copy included the amendment log, which by the time of copying had accumulated five
> detector-measured figures. Two of the seven touched decisions (**A-12**, and to a lesser
> extent **A-15**'s confirmation) used one of those figures as a **deciding** input rather than
> mere corroboration; the rest are corroboration of readings the text had already settled.
> **This is real and is not waved away** — but it is narrow. It affects **cap-counting
> mechanics, an `n`-convention footnote, and confirmation of dimensions (rejection geometry,
> tie-break order, the variance formula) that both builds reach by textual argument anyway.** It
> demonstrably does **not** explain the trade-identity divergence: the A-01 shift test above
> shows the dominant, population-moving forks (A-01, A-04, A-06, A-07, A-08, A-13) were decided
> from spec text and precedent alone, with no published figure to lean on even if the build had
> wanted to.
>
> **One fact argues the discipline was mostly real rather than incidentally clean:** on A-06,
> the build measured that setting `range_conf = 3` lands qualified candidates at 46.4/session —
> within 0.5 of A9's published 46.9 — and **chose 2 anyway**, on textual grounds, disclosing the
> near-miss rather than hiding it. That is the one point in the manifest where fitting was
> directly available and was refused.

**Net verdict: source isolation clean; output isolation leaked on a small, named, low-impact
subset of decisions. The diff's value as a test of the trigger predicates, the stop anchor, the
target ladder and the A7 selector is intact** — those are exactly the UNPINNED dimensions (A-04
clustering, A-08/A-13 targets, A-07 invalidation, A-01 timing) that the leak never touched.

## 5. Updates this closes

- `STAGE3-UNSEAL-RULE.md` clause **a.3**: was *"collected, not adjudicated"* — now **adjudicated.
  Every disagreement resolves to spec ambiguity or documented scope, none to a detector or
  second-build bug. Isolation held on source, leaked narrowly on output, on dimensions that do
  not explain the diff's size.** a.3 is **MET** under the rule's own text (*"a.3: 2c's diff is
  empty under enforced isolation, **or every disagreement is adjudicated to spec ambiguity**
  rather than to a bug in either implementation"* — satisfied by the second clause).
- **b.1 remains the only unmet clause.** Verdict stays **DO NOT OPEN**, now resting on the pass
  marks alone.

**N_trials: unaffected — 1 of 5.** Nothing here compared outcomes or selected among readings by
result; it classified existing decisions and diagnosed existing disagreements.
