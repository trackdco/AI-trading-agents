# PRE-REGISTRATION — LDN-OBK-01 / LDN-PO3-01 — the London-open break event tree

**Committed BEFORE any data is pulled or scored.** Two candidates that fire on the
same instant and disagree about what to do are registered here as ONE family with
one census, per `research/candidates/london-nq-open-break.md` and
`research/candidates/london-po3-ifvg.md`. The commit that adds this file precedes
the commit that adds `scripts/london_obk_census.py` and any output. If a later
result is reported against different definitions, this file is the evidence.

Greenlit by Brakey 2026-08-05. Sources: Brandan Trades (08:00 UK level break),
EzTrades (03:00 ET PO3 manipulation + IFVG), Tradesharpe (stop geometry), and our
own `LDN-WIN-01` window measurement.

---

## Hypothesis

One falsifiable sentence per branch, same trigger:

- **Continuation branch (LDN-OBK-01):** when NQ breaks its pre-open range after the
  London cash open, the break resolves in the direction of the break often enough,
  and far enough relative to a trigger-candle stop, to pay.
- **Failure branch (LDN-PO3-01):** the first break after the London cash open is
  predominantly a liquidity sweep, so price closes back inside the pre-open range
  and then travels to the far side of it.

The two branches are mutually exclusive resolutions of one event. Testing them
together is one census, not two.

## Mechanism

Before 08:00 London the book is thin and price drifts, leaving a high and a low that
are the only structure anyone can see. At the open, real European size arrives as a
scheduled event. Either that size is behind the first move — in which case whoever
faded it is offside — or it is not, and whoever chased the break is offside and must
cover. **The trapped counterparty is explicit and it is a different set of people in
each branch.** That is the whole trade in both directions.

Supporting measurement, ours, taken before either trader's clock was read:
`LDN-WIN-01` found 03:00 and 04:00 ET (08:00 and 09:00 London) are the two peak
buckets of the session on range, volume and efficiency in both eras, and that
10:00–11:00 London carries the worst efficiency in the profile.

**Mechanism family:** structural events / overnight structure.

## Input columns

`ts_event`, `open`, `high`, `low`, `close`, `volume` from
`data/reference/nq_1m_master.parquet` and `nq_1m_feb_jul2026.parquet`. **Bars only
at census.** No depth, no CVD, no substrate feature columns. This is deliberate: a
bar-only census reaches every era including the 23/24 candle span, and it keeps the
input-family veto trivially clean against the depth-wall and flow candidates.

## Session

`london`. Window declared in **Europe/London local time**, converted to ET per day
via `scripts.run_triggers_london.london_window_et`, so the ~3 weeks/year of UK-US
DST misalignment do not smear the clock. (`LDN-WIN-01` used raw ET buckets and
therefore smeared those weeks; that is a stated limit of that study, corrected here.)

## Entry type

Momentum (E4-style) on the continuation branch; limit/rotation (E3-style) on the
failure branch. Census scores neither — census counts events.

---

## Declared definitions — frozen here, before the run

The one genuinely discretionary joint in this family is **how the level is marked**.
Three options were offered; option 1 is taken because it is closest to as-taught and
requires no tuning:

1. **Pre-open range** = high and low of **06:00–08:00 Europe/London** on the UK
   calendar date. Two hours, single declared window, not searched. It contains
   EzTrades' 01:00–02:00 ET accumulation range and it is the drift Brandan marks
   from at 07:55.
2. **Trigger window** = **08:00–10:00 Europe/London**. Opens at the London cash open;
   closes before the 10:00–11:00 hour that `LDN-WIN-01` measured as the worst in the
   session. Nothing outside this window is a trigger.
3. **Break** = the first 1-minute **close** beyond the pre-open range high (up-break)
   or below its low (down-break) inside the trigger window. First break per side per
   day. A close, not a wick — the failure branch's whole claim is about what the
   break did after it happened, and a wick has no after.
4. **Failure** = a subsequent 1-minute **close back inside** the pre-open range.
   Horizon declared at **30 minutes**, with 60 and 120 also reported. 30 is not
   chosen here — it is inherited from `NYA-FA-01`'s already-frozen fail horizon, so
   the two lanes' numbers are comparable.
5. **Continuation** = no close back inside the range within the horizon.
6. **Excursion** = maximum favourable extension beyond the break level, in points,
   before the first close back inside (or before window end).
7. **Traverse** = after a failure, price reaching the **opposite** edge of the
   pre-open range before 10:00 London. The mid-point is reported separately.

**IFVG is NOT defined here and is not censused.** Per the promotion rule already
declared in `london-po3-ifvg.md`, the default failure-branch spec is arm B (close
back inside), and arm A (IFVG) may not be run until it has a mechanical definition
committed in advance. Writing that definition after seeing this census would be
writing it on the data.

**The SMT-divergence confluence is dropped, not silently folded in.** It needs ES
alongside NQ and we do not hold ES. The verdict will say the spec tested was the
NQ-only leg.

---

## Spans consumed

| span | days | role |
|---|---|---|
| 2025 | full year | **discover** |
| 2026-01-01 → 2026-07-15 | all available | **validate** |
| 2023 / 2024 | — | **NOT TOUCHED** |

**Holdout look: NO.** Fit-only. No 23/24 candle look and no sealed-flow look is
spent by this census. The 128 sealed days of
`docs/HOLDOUT-2023-24-PREREGISTRATION.md` are untouched and their single-look
declaration is unaffected. The 23/24 candle era check is a later rung under §5.9.4
(one corrective iteration, maximum) and will be declared separately when earned.

### Controls — declared, and one of them amended before the run

**AMENDMENT, committed before any data was touched.** The first draft of this file
declared an "inverse pass = the same counts with the branch labels swapped." That is
not a control: continue-rate is exactly `1 − fail-rate`, so swapping the labels
re-prints the same number and tests nothing. Replaced, before running, with two
controls that can actually fail:

1. **Placebo range (the real control).** Rebuild the whole census against a range
   taken from **04:00–06:00 Europe/London** — same two-hour width, same break, fail
   and traverse logic, same 08:00–10:00 trigger window, but a range with no claim on
   the open. If breaks of an arbitrary earlier range fail at the same rate as breaks
   of the pre-open range, then nothing about the *pre-open* range is special and both
   branches are just measuring ordinary mean reversion. **This control is capable of
   killing the family's premise and is the reason it is here.**
2. **Side symmetry.** Up-break and down-break statistics reported separately. A fail
   rate that exists only on one side is a directional drift artifact, not a sweep.

Neither control has a pre-set kill threshold, because neither is the census kill line
of §5.9.1 — they qualify the reading of the fail rate rather than replace it. The
placebo margin is reported with the headline number, always, so the fail rate is
never quoted alone.

## Seed / day list

No sampling. Every day in the spans above with ≥ 60 one-minute bars inside
06:00–10:00 London is included. No seed needed; the universe is exhaustive and
reproducible from the two parquet files.

---

## Acceptance bars

Census is a **counting** stage. It does not accept a strategy; it establishes that
the taught behaviour exists. §2 sleeve bars (era consistency, 1× and 2× cost
realism, PSR(0) ≥ 0.75, book-level deflation) are already pre-registered in the two
candidate files and apply at L1 and beyond, not here.

## Kill criteria — pre-committed, per §5.9.1

A candidate dies at census **only if the claimed behaviour does not happen.** Raw
profitability, ugly win rates and decayed edges do **not** kill at census.

- **LDN-OBK-01 dies** if the pre-open range is broken inside the trigger window on
  **< 30% of days** in either era. There is no level-break trade if there is no
  level break.
- **LDN-PO3-01 dies** if breaks fail (close back inside within 120 min) on
  **< 15% of breaks** in either era. Its claim is that the first move is usually the
  trap; a fail rate near zero refutes that outright.
- **The family dies** if breaks neither fail nor extend — i.e. if excursion beyond
  the level is indistinguishable from zero — because then there is no event to trade
  in either direction.
- **The PO3 strong claim is separately falsifiable and does not kill the branch.**
  EzTrades teaches that the break is *usually* the trap. If the fail rate lands above
  15% but below 50%, the strong form is refuted and recorded as such while the branch
  survives on the weak form.

## Declared secondary question — the NYA-FA-01 transfer

`NYA-FA-01`'s L0 found that **depth of excursion before re-entry** discriminates
traverse odds (23% vs 8% far-edge, deep vs shallow terciles) while **time spent
outside** discriminates nothing (16/19/12%). Both are already frozen results from
the other lane, paid for there. This census recomputes **both** on the London window
at the same tercile construction.

This is declared as a **transfer test of an existing result**, not a new search: no
new variables, no thresholds fitted here, and it costs the family two ledger rows,
not a search. If it replicates, one variable is doing work in two sessions and two
setups, which is worth more than either candidate. If it fails to replicate, that is
a genuine negative about the NY result's generality and is reported as one.

## Known limits, stated up front

- **Bars only.** No absorption, no delta, no depth at census. A break that "should"
  have been read as absorbed is not distinguishable here. That is the point of L3.
- **A census is not a backtest.** Fail rates and excursions are base rates. They do
  not become expectancy until stops, targets and costs are attached at L1, and the
  euro-handoff tombstone (78% WR, +0.02R) is the standing reminder that base rates
  and payment are different questions.
- **First break per side only.** Days that break, fail, and break again are counted
  once per side. Re-break behaviour is a declared future arm, not smuggled in here.
- **The pre-open range is a proxy for "the levels everyone watches".** It is not what
  either trader marks by hand. It is mechanical, declarable and untuned, and those
  three properties are why it was chosen over a better-looking discretionary mark.
- **No instrument transfer claim.** NQ only. Brandan trades MNQ and Brandan's other
  content is CFDs; the structure may transfer, the cost stack does not.

## Artifacts

- `scripts/london_obk_census.py` — the census, committed after this file.
- `output/london_obk_census.parquet` — one row per break event.
- `output/london_obk_census.md` — the printed tables.
- Trials to `output/trial_ledger.parquet` at trial time, per §6.0.2.
- Data card in `research/FUNNEL.md` at the census stage boundary, per §5.10.
