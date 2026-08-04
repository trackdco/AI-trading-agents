# REPORT — Correlation battery: NY canon ↔ old London book (2026-08-04)

The first actual measurement of the NY↔London relationship — both books have been
leaning on assumptions about it (ANGUS brief 2026-08-04 §3). Six measurements, run
as a battery; correlation is not one number.

**Provenance.** Script `scripts/correlation_battery.py` (this commit), seed 7,
10k-resample bootstrap CIs, 2,000-sim ruin MC. Inputs:
`output/funded_book_lucid_fit.parquet` — the shipped NY funded accounting (rules
J/K/L, $160 base, regenerated at repo state `2157069` via
`python -m scripts.funded_book --span fit --profile lucid`, printing the reference
+$82,543) — and `output/london_canon_book.parquet` (old London book, native research
sizing, `scripts/london_canon.py`, rows with `size > 0` only). Raw run output:
`output/correlation_battery_report.md`; joined day series:
`output/correlation_daily_ny_london.parquet`. Common span 2025-06-02..2026-07-08;
NY active 230 days, London active 109, both-active 99.

## Headline

| Measurement | Result |
|---|---|
| Day-level Pearson, union universe (n=240) | **−0.094** [95% CI −0.185 .. +0.003] |
| Day-level Spearman, union (n=240) | −0.096 [−0.216 .. +0.026] |
| Day-level Pearson, both-active only (n=99) | −0.110 [−0.265 .. +0.065] |
| Day-level Spearman, both-active (n=99) | −0.086 [−0.273 .. +0.104] |
| Tail co-crash P(LDN worst decile \| NY worst decile) | 0.10 — exactly the independence floor |
| Both-red-decile days | 1 observed vs 1.0 expected under independence |
| Simultaneous open-risk minutes | **0** across all 240 days |
| Combined ruin: paired vs pairing-shuffled P(bust) | 0.5% vs 0.4% — dependence costs ≈ nothing |
| Input families shared | **3 of 7** — depth walls, overnight structure, order flow |

Reading: on returns, the two books are indistinguishable from independent — slightly
negative point estimates, CIs spanning zero, tail behaviour exactly at the
independence floor, zero clock overlap (the only contention channel is the shared
budget, confirming the HANDOFF's zero-overlap claim; measured clocks below).
On **inputs**, they are cousins: both gate on depth walls, overnight structure, and
order-flow families. The brief's own warning applies verbatim — structural overlap is
the leading indicator; return correlation is the lagging one. Today's clean return
numbers do not retire the structural caution.

Fill clocks, measured from the taken trades this session (these supersede the
HANDOFF/brief's quoted 08:02–10:20 / 03:02–05:54 ranges, which were approximate):
NY 08:00–10:29 ET (762 trades, funded lucid fit book); London 03:01–05:50 ET
(136 taken trades, `output/london_canon_book.parquet`). Zero overlap either way.

**Supersedes:** the `day-corr +0.11` figure in the `scripts/london_canon.py`
docstring (measured pre-rules, against a pre-J/K/L NY accounting). Against the
shipped funded book the sign flips: −0.09/−0.11. Per the stale-figure rule, quote
this report, not the docstring.

## Tail detail (small-n, direction not precision)

Worst-decile cuts: NY −$296/day (10 days), London −$487/day (10 days). One common
both-red-decile day. Pearson conditioned on either-book-in-worst-decile (n=19):
−0.451 — on the days that matter most, the point estimate is *hedging*, not
stacking; at n=19 treat as direction only.

## Combined ruin (funded shell: 50k start, $2k EOD trailing, lock at 50k, 252-day year)

| Book | P(bust) | median net/yr | maxDD med / p95 | median worst day |
|---|---|---|---|---|
| NY alone (funded lucid) | 0.4% | +$86,165 | $1,267 / $1,954 | −$690 |
| London alone (native sizing) | 6.9% | +$36,046 | $2,115 / $3,803 | −$1,292 |
| Combined, as paired | 0.5% | +$123,458 | $1,694 / $2,697 | −$1,266 |
| Combined, pairing shuffled | 0.4% | +$122,734 | $1,631 / $2,683 | −$1,080 |

- This MC deliberately excludes payout withdrawals (that knob lives in
  `scripts/mc_funded_lab.py`) and runs the *mechanical* NY book, so its absolute
  P(bust) is a comparison statistic between rows, not a funding forecast; the
  mc_funded_lab agent-book figure (P(bust) 0.1%) is a different instrument.
- **The promotion criterion the brief names** — marginal portfolio contribution —
  reads: adding London to NY at native sizing raises median net/yr +$86k → +$123k
  (+43%) while P(bust) moves 0.4% → 0.5% and p95 maxDD $1,954 → $2,697. On these
  numbers, keeping both beats keeping the better one — *at separate-account or
  ungoverned sizing*. Under one shared $853.33 budget the answer must be re-run;
  that is the data contract's first job.
- London alone at 6.9% P(bust) is NOT a shippable configuration — the old book is
  un-governed research sizing with a −$1,292 median worst day against an $853
  budget. It is included as a dependence measurement, not a candidate.

## Proposed thresholds — every number [PROPOSED — Angus to ratify]

The brief demands numbers, not principles. Proposals, anchored to what was measured:

1. **Max pairwise |ρ|** (day-level, Pearson AND Spearman, both-active universe):
   **0.30** for two strategies to co-ship on one account. Both must clear; where
   they disagree materially (>0.15 apart), investigate before ruling. Measured
   NY↔London: −0.09/−0.11 — clears.
2. **Max tail dependence:** conditional co-crash probability at decile conditioning
   ≤ **0.25** (2.5× the 0.10 independence floor), on a minimum of 60 both-active
   days. Measured: 0.10 — clears.
3. **Minimum common days** before any return-based estimate is trusted: **60
   both-active days**; below that, only the structural (input-family) veto and
   timing overlap apply. Measured: 99 — estimates count.
4. **Max combined P(bust)** at shipped sizing under the funded shell: **1.0%**
   (payout-free comparative MC; re-derive with mc_funded_lab before any live scale
   decision). Measured combined-as-paired: 0.5% — clears at native sizing;
   NOT yet measured under a shared budget.
5. **Input-family rule (the veto):** two strategies sharing **≥3** gating families
   require an explicit Angus waiver to co-ship on the same account, regardless of
   measured return correlation. NY↔London currently trips this (3/7 shared) — the
   waiver decision is Angus's, with the mitigating evidence being zero clock
   overlap, tail independence, and negative point correlation. A portfolio should
   also carry **≥2** families that only one strategy reads (currently true: VWAP +
   trigger density + structural events are NY-only; pattern taxonomy is
   London-only).

## What this battery does not yet know

- **Shared-budget accounting.** Everything above treats the books as separately
  capitalized. One account = one budget accumulator = a contention channel that
  exists even at zero return correlation. Blocked on the account-architecture
  ruling (FOR-ANGUS-rulings-2026-08-04.md §1) and the emission contract.
- **Holdout replication.** A 2023/24 NY↔London correlation would double the
  evidence — but the London holdout book does not exist yet
  (`output/london_canon_book_holdout.parquet` is unbuilt) and computing on the
  sealed span **is a holdout look**: it does not run until Angus declares it in
  the ledger. Deliberately not run today.
- **Regime conditioning.** 13 months, one regime. The structural-cousin warning
  (shared families re-correlating when a regime ends) is untestable on this span —
  which is exactly why the input-family veto stays load-bearing.
