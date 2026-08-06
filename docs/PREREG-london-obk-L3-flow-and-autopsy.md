# PRE-REGISTRATION — LDN-PO3-01 / LDN-OBK-01 — L3 flow pass + mandatory loser autopsy

**Committed BEFORE any flow data is joined or any winner/loser split is inspected.**
This is the stage §3.2 makes mandatory and §5.9.2 makes decisive: *"An expectancy kill
that predates the flow cross-check is PREMATURE and gets vacated on review."* Neither
branch may be killed or shipped until this runs.

Order of operations is fixed and declared: **flow confirmation on RAW triggers first,
autopsy second.** The raw pass has to stand on its own before any winner/loser
comparison is allowed to shape it — otherwise the flow features get selected by the
autopsy and then "confirmed" on the same data.

## Data and its limits, stated before use

| source | span | note |
|---|---|---|
| `data/reference/cvd/footprint_*.parquet` (non-holdout) | 2025-06-01 → 2026-07-19 | full contiguous tape |
| `data/reference/depth_london/*.csv` | 295 days, 07:00–08:59 **UTC** | MBP-10 condensed |

**Depth coverage is asymmetric and it matters.** The depth files are fixed to
07:00–08:59 UTC. Under BST that is 08:00–09:59 London — the whole trigger window.
Under GMT it is 07:00–08:59 London, so only the **open hour** (08:00–08:59 London) is
covered. Consequence: depth features are complete for the open hour on every day, and
present for the macro hour only on BST days. Since the fade branch's confirmed
condition (V1) is the open hour, this is adequate — but the macro-hour depth reads are
seasonally incomplete and **any macro-hour depth result is barred from being a gate.**

**Flow span is shorter than the bar span.** Bars run from 2025-01-01; flow starts
2025-06-01. So the flow pass sees **2025 H2 only** for the discover era. Stated up
front so nobody later reads "2025" in a flow table as the full year.

**2023/24 untouched.** `footprint_holdout_*.parquet` and `depth_london_2023_24/` are
not read by this run. **Holdout look: NO.**

---

## Step 1 — flow confirmation on RAW triggers

Applied to the **unconditioned** default arms (F1 and A/S1), on every raw trigger in
the flow span. No conditioning, no cuts, no filters. The question is only: **does
at-entry flow state separate outcomes at all?**

### The feature set — SMALL, and declared here before looking

Six features. Four from tape, two from book. Chosen on mechanism; the list does not
grow after the first table is printed.

**Tape (footprint delta; `side` A = buy-aggressor, B = sell-aggressor):**

1. `delta_entry` — signed delta on the entry minute.
2. `delta_pre5` — cumulative delta over the 5 minutes before entry.
3. **`delta_sweep`** — cumulative delta from the break bar through the fail bar. **This
   is the mechanism variable, not a filter.** The fade branch's whole thesis is that
   the break traps aggressive participants; the delta printed during the sweep *is*
   that trapped size. If the trapped-counterparty story is true anywhere, it is here.
   Bars could not see it, which is why V3 half-failed on candles.
4. `absorb_extreme` — volume on the sweep-extreme minute ÷ median minute volume in
   that day's pre-open window. High volume at the extreme with price failing to
   progress is the absorption signature.

**Book (MBP-10, at-price reads ONLY — per the canon finding at commit `2a9c221`, the
book sees roughly ±5 NQ points and distant-level structure is not real):**

5. `wall_ratio_opp` — largest resting level ÷ median level size on the side the trade
   must trade *into*.
6. `book_imb` — `bid_total / (bid_total + ask_total)` at the entry minute.

### Declared predictions

- **`delta_sweep` is the one I expect to work.** A fade should pay best when the sweep
  printed *large* aggressive delta in the break direction — that is a big trapped
  cohort — and should pay worst when the sweep printed little delta, because then
  nobody was trapped and the move was just drift.
- `absorb_extreme` high should favour the fade (size absorbed at the extreme).
- `wall_ratio_opp` high should *hurt* (a wall in the path is an obstacle to the target).
- `delta_entry` / `delta_pre5` / `book_imb` are included as controls with no strong
  prior. If they outperform `delta_sweep`, that is a warning that the result is
  generic flow-momentum rather than this candidate's mechanism, and it will be
  recorded in those words.

### Reporting

Terciles per feature per era, R/trade and PF at both cost levels, n≥15 per cell or
suppressed. Every feature ledgered whether it works or not.

---

## Step 2 — the mandatory loser autopsy (§3.2)

Runs only after step 1 is printed. Procedure fixed by §3.2 and followed literally:

1. **Feature set declared before looking** — the six flow features above plus the four
   candle features already in hand (range width, break hour, drift alignment,
   excursion). No new features are introduced at autopsy time.
2. **Loser vs winner distributions, per era**, for every one of the ten.
3. **Half-year decomposition is mandatory**, not optional — the trigger event for this
   rule was the H2-2025 losing stretch both pre-market winners shared, invisible at
   calendar-year granularity. Finest available split on the flow span: **2025H2,
   2026H1, 2026H2**.
4. **Every candidate cut-set is a ledgered arm.**
5. **A cut is only legal if the cut cohort is bad in EVERY era** — the wall-quality-cut
   precedent. A cut that only works in the discovery era is a declared negative.
6. **De-risk (half size) is tested alongside every hard cut.** Sometimes the answer is
   smaller, not none.

### What the autopsy may and may not conclude

- It may identify cut-sets and de-risk arms. It may **not** promote them: the frozen
  default spec stays unconditioned F1 / A-S1 per §6.0.1.
- **An expectancy kill becomes legal for the first time here**, because the declared
  search — candle features, then flow-at-entry — is complete at the end of this run.
  If both branches are negative in every era at strict cost after the full search,
  that verdict is earned and will be written.
- If flow *does* lift, the next rung is grading (MC / DSR / PBO / correlation
  battery), not shipping.

## Artifacts

`scripts/london_obk_flow.py`, `scripts/london_obk_autopsy.py`,
`output/london_obk_flow.md`, `output/london_obk_autopsy.md`, trials to
`output/trial_ledger.parquet`, `research/FUNNEL.md` cards refreshed per §5.10.
