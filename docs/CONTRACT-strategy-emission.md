# CONTRACT — per-strategy emission (emission-v0.1-proposed)

**Status: PROPOSED — the agenda for the 30-minute Angus↔Brake conversation (brief §2c),
then frozen.** This is the data contract between **Brake (emitter)** — and any future
emitter of a candidate strategy — and the **correlation/validation infrastructure
(consumer)**: `scripts/correlation_battery.py`, the selector pre-registration's
baselines (`docs/PREREG-selector.md` §2/§6.1), promotion-ladder rung 3
(`docs/VALIDATION-PROCESS.md` §6), and vault `correlation_edge` records
(`docs/VAULT-SCHEMA.md` §3.7). "Get this wrong and every new strategy needs bespoke
glue" (ANGUS brief 2026-08-04 §2c).

Lifecycle on ratification: drop `-proposed`, then the freeze law of
`docs/JOURNAL-SCHEMA-v1.md` applies verbatim — **additions require a version bump
(v0.2+) and never rename or remove v0.1 fields**; reserved names in §2.4, do not
improvise. Markers as in `docs/VALIDATION-PROCESS.md`: [EXISTING] / [PROPOSED — Angus
to ratify] / [OPEN — needs Angus/Pat] / and here **[GAP — needs backfill or waiver]**
for fields an existing book cannot supply today.

**Branch discipline:** drafted on `claude/canon-rebuild-deployment-7m48yv`, off the
live arming branch. Emission artifacts and this doc reach the arming branch only via
the deliberate re-cert flow — a docs commit alone makes the next arm refuse on
provenance (live HANDOFF 2026-08-04 §4). Emissions are research artifacts: **the live
path never reads them** (same isolation law as the vault, `docs/VAULT-SCHEMA.md` §1).

Every number in this document was verified this session against the artifacts named,
at repo state `db97e96` (pandas read of the parquets; `scripts/funded_book.load_book`).

---

## 0. What is emitted, in one sentence

Per strategy, per span: **one parquet of taken trades** (signal timestamps, direction,
risk, per-trade P&L in dollars at the emitted sizing) **plus one small manifest**
(strategy id, mechanism families, input columns, session window, book provenance).
The day-level P&L series the brief names is a **derived view** of the parquet (§3),
not a second artifact — one source of truth, no drift. The brief's field list —
"day-level P&L series, signal timestamps, direction, risk, mechanism tag, input
columns" (§2c) — maps: day P&L → §3 view over `pl`; signal timestamps → `ts` /
`fill_ts` / `exit_ts`; direction → `direction`; risk → `risk_pts` / `risk_dollars`;
mechanism tag + input columns → manifest (§4).

**Files and naming** [EXISTING conventions: parquet books in `output/`, span suffixes
`_fit`/`_holdout`, templated `{span}` — `aikido_{span}.parquet`,
`funded_book_lucid_fit.parquet`]:

```
output/emission_{strategy}_{span}.parquet          # the trades
output/emission_{strategy}_{span}.manifest.yaml    # the manifest
```

- `{strategy}`: filesystem slug of the vault strategy id (`strategy:ny-canon` →
  `ny_canon`; `strategy:london-old-book` → `london_old`). The manifest carries the
  mapping.
- `{span}` ∈ {`fit`, `holdout`}. **One file per strategy per span.** Era splits
  (fit-2025 / fit-2026) are derived by `day` range, never separate files.
- Emitting a `holdout` file for a strategy whose sealed-span book does not yet exist
  **is a holdout look** and requires a declared ledger entry first
  (`docs/VALIDATION-PROCESS.md` §4.1: "Merely building a sealed-span artifact is a
  look"; `docs/REPORT-correlation-2026-08-04.md`). The contract cannot self-authorize
  one.

---

## 1. Emission laws (the semantics, before the columns)

1. **Post-law trades only.** The emission is the strategy's book *after* its ruled
   execution semantics: suppressed trades are never emitted ("Suppressed trades never
   existed" — `scripts/funded_book.py` docstring, rule L), and overlay-modified exits
   (flips, pre-flattens) are emitted as final. Precedent: `funded_book.load_book`
   applies `output/aikido_cr_{span}.parquet` as LAW before anything downstream sees a
   row. A book with **no** ruled semantics (old London) emits as-is with
   `execution_semantics: none` declared in the manifest — consumers can then see the
   difference instead of assuming it.
2. **Taken trades only** (risk actually opened). Unfilled triggers and declined
   candidates are out of scope for v0.1 (reserved: a separate candidates emission,
   §2.4).
3. **Dollars, not R.** `pl` and `risk_dollars` are **US dollars at the emitted
   sizing**; prices and `risk_pts` are **NQ index points**. R is never stored in v0.1
   — derive `pl / risk_dollars`, with the caveat that engine dollars include
   commission ($5 round-turn per 1-lot NQ, `COMMISSION = 5.0` in
   `scripts/capture_replay.py`) so derived R is commission-inclusive.
   **The correlation battery consumes `pl` ($) and nothing else for returns** —
   `groupby('day').pl.sum()`, exactly its current code path
   (`scripts/correlation_battery.py::day_series`).
4. **Timezone: ET, the shop's session language.** All timestamp columns are ISO-8601
   strings at minute resolution in America/New_York wall-clock **with explicit
   offset**, and a single file legitimately mixes `-04:00`/`-05:00` across DST
   (verified: both offsets present in `aikido_fit.parquet` `ts`). Normative parse
   (two sources: burn-list #1, `docs/HANDOFF-london-rebuild.md` §7 prescribes
   `utc=True` + `tz_convert`; `format="mixed"` is from
   `docs/HANDOFF-agents-capture.md` §5):
   `pd.to_datetime(col, format="mixed", utc=True).tz_convert("America/New_York")`.
   Never hardcode London's ET hours — the London window is 08:00–10:00 Europe/London
   converted per-day via `scripts/run_triggers_london.london_window_et`
   (03:00–05:00 or 04:00–06:00 ET; `docs/HANDOFF-london-rebuild.md` §2).
5. **Uniqueness key.** `(strategy, ts, direction)` MUST be unique per file — the NY
   book asserts exactly this (`scripts/apply_close_reverse.build_span`; re-verified
   this session on `aikido_fit.parquet`). An emitter that cannot guarantee it
   (same-minute sibling triggers — burn-list #4) must extend the key with `entry`
   and declare `key:` in the manifest.
6. **Ordering.** Rows stable-sorted by `fill_ts` (mergesort), ties in detection
   order — the tie order is load-bearing (it decided which sibling got the day's
   single elite 2.0× slot; caught by `tests/test_canon_scorer_ny.py`;
   `scripts/funded_book.py::load_book` comment).
7. **Day is the atomic resampling unit.** Budget-governed books are path-dependent
   *within* a day (budget = realized + in-flight + new ≤ base × 16/3 = $853.33 at
   $160; soft de-risk; elite 1/day — `scripts/funded_book.py` docstring), so day P&L
   is not a sum of independent trades. Trade rows exist for joins, timing overlap,
   and shared-budget replay — **never** for sub-day resampling of a governed book.
8. **Minute resolution is the floor.** Both existing books stamp at minute
   resolution; sub-minute is a version-bump question, not an improvisation.
9. **Provenance mandatory.** Every emission carries the manifest's §4 provenance
   block (the `docs/VAULT-SCHEMA.md` §2.2 shape — commit, book identity incl. base
   and overlay, reproduce + expected). A parquet without its manifest is not a valid
   emission.

---

## 2. The emission table

### 2.1 Required columns (v0.1)

| # | column | dtype | units / values | notes |
|---|---|---|---|---|
| 1 | `strategy` | str | slug | = manifest `strategy`; makes concatenated frames self-describing |
| 2 | `day` | str | `YYYY-MM-DD`, ET trading day | matches both existing books (verified: `str` in both parquets) |
| 3 | `ts` | str | ISO-8601, ET offset, minute | **signal identity** — the trigger stamp. Old London lacks one; see §7 waiver |
| 4 | `direction` | str | `long` \| `short` | |
| 5 | `fill_ts` | str | ISO ET | risk opens |
| 6 | `exit_ts` | str | ISO ET | flat (post-law: overlay/flatten exits are final) |
| 7 | `entry` | float64 | NQ points (price) | also the key extension where §1.5 applies |
| 8 | `stop` | float64 | NQ points (price) | |
| 9 | `exit_price` | float64 | NQ points (price) | |
| 10 | `exit_reason` | str | emitter vocab, listed in manifest | measured this session — NY book (`funded_book.load_book("fit")`): `stop`, `target`, `be_stop`, `partial+stop`, `partial+target`, `partial+be_stop`; CR overlay (`output/aikido_cr_fit.parquet` `cr_exit_reason`, sourced per §6 for overlay-hit rows): `flip`, `open_flatten`, `partial+open_flatten` (plus `stop`/`target`/`partial+stop`/`partial+target` on rows outside the funded book); London book (`size > 0`): `stop`, `target`, `partial+stop`, `partial+target`. Full emission union: `stop`, `target`, `be_stop`, `partial+stop`, `partial+target`, `partial+be_stop`, `flip`, `open_flatten`, `partial+open_flatten` |
| 11 | `risk_pts` | float64 | NQ points — the emitting book's own `risk` column, carried verbatim | NY band 7–60pt; London ≥ 9.5pt no cap (`LON_RISK_MIN`, `docs/HANDOFF-london-rebuild.md` §2). Note: NY's `risk` is not always the raw entry−stop arithmetic (verified example: risk 12.75 vs entry−stop 11.25), so consumers treat it as the book's declared risk, never recompute |
| 12 | `qty_mnq` | int64/float64 | MNQ-equivalent contracts, 1 NQ = 10 MNQ | normalizes NY `micros` (already MNQ) vs London `size` (NQ lots → ×10) |
| 13 | `risk_dollars` | float64 | $ at emitted sizing | NY: `risk_d` (= base × tier). London: derivable, `risk_pts × $20 × size` (pre-commission) |
| 14 | `pl` | float64 | **$ at emitted sizing** | **the battery's return column** (§1.3). Commission handling declared in manifest |
| 15 | `sess` | str | vault session vocab: `ny-pre`, `ny-gold`, `london` (`docs/VAULT-SCHEMA.md` §5) | session tag (vault session axis, `docs/VAULT-SCHEMA.md` §5); the brief's "mechanism tag" is manifest `mechanism_families` — see §0 mapping |
| 16 | `conviction` | float64 | sizing multiplier | NY `tier` ∈ {0.5, 1.0, 1.5, 2.0}; London `size` ∈ {0.5, 1.0, 1.5}; emit 1.0 if the strategy has no tiers |

### 2.2 Optional columns (v0.1)

`pattern` (str), `tf` (str) — carried where the source book has them; consumers must
not require them.

### 2.3 Day-level derivation is normative

See §3. No emitter ships a separate day-level file; no consumer computes day P&L any
other way.

### 2.4 Reserved names (do not improvise; version bump to activate)

`r` (per-signal outcome in R at shipped exits — needed only if the selector binds at
per-signal granularity, `docs/PREREG-selector.md` §6.1), `mfe_r`, `status`,
`budget_after`, `account`, `regime_tag`, and a `candidates` emission for
unfilled/declined signals. Mirrors the reserved-names law of
`docs/JOURNAL-SCHEMA-v1.md`.

---

## 3. The day-level view — and the union baseline for free

**Normative derivation** [EXISTING — this is verbatim what the battery already runs]:

```python
pl_day = df.groupby("day").pl.sum()        # $; one value per ACTIVE day
```

Days absent from the index are inactive days. Cross-strategy assembly:

```python
import pandas as pd, glob, yaml
frames = {}
for p in glob.glob("output/emission_*_fit.parquet"):
    m = yaml.safe_load(open(p.replace(".parquet", ".manifest.yaml")))
    frames[m["strategy"]] = pd.read_parquet(p)

pl = pd.DataFrame({s: f.groupby("day").pl.sum() for s, f in frames.items()})
active = pl.notna()               # INTERIM eligibility E(d): >= 1 TAKEN trade that day
b1_separate = pl.fillna(0.0).sum(axis=1)   # B1 "take everything", separate-account arithmetic
```

This yields, with zero bespoke glue:

- **The battery's inputs**: union universe (`fillna(0)`) and both-active universe
  (`dropna()`) for Pearson/Spearman + CIs; worst-decile tail conditioning; the
  combined-ruin day series. `output/correlation_daily_ny_london.parquet` (240 rows ×
  {`ny`,`ldn`}, `day`-indexed, verified this session) is exactly this frame for the
  two current books.
- **The selector prereg's objects** (`docs/PREREG-selector.md` §2.0): `p_s(d)` = the
  columns of `pl`; eligibility `E(d)` = `active` (from row presence, mechanical and
  logged) — the **interim** definition (§2.0 as amended): v0.1 emits taken trades
  only, so E(d) = "≥1 taken trade on day d". Limitation: signalled-but-unfilled days
  are invisible, which is wrong for limit-entry strategies; the v0.2 target is
  activating the reserved `candidates` emission (§2.4) so E(d) derives from signal
  timestamps (§8 gap register); **B1 take-everything = the union sum** —
  "'take everything' is just the union" (brief §4). B2/B3 and the identity shuffle are then pure index arithmetic
  over the same frame.
- **The one-account variant is NOT this arithmetic**: under a shared DLL the union
  book must be replayed in `fill_ts` order with per-signal `risk_dollars` against one
  budget accumulator ($853.33 at $160). The trade-level table is what makes that
  replay possible; whether it is required is blocked on the account-architecture
  ruling (`docs/FOR-ANGUS-rulings-2026-08-04.md` §1;
  `docs/REPORT-correlation-2026-08-04.md`: "Under one shared $853.33 budget the
  answer must be re-run; that is the data contract's first job").

**Timing overlap** consumes `fill_ts`/`exit_ts` directly: per-day in-market minute
sets, intersect across strategies (`scripts/correlation_battery.py::in_market_minutes`
is the reference implementation, including the §1.4 parse).

---

## 4. The manifest

One YAML per emission. Fields:

| field | req | content |
|---|---|---|
| `schema` | yes | `emission-v0.1-proposed` (→ `emission-v0.1` on ratification) |
| `strategy` / `vault_id` | yes | slug + `strategy:<id>` (`docs/VAULT-SCHEMA.md` §3.4) |
| `span` | yes | `fit` \| `holdout` |
| `key` | yes | `[strategy, ts, direction]` or the §1.5 extension |
| `sessions` | yes | vault vocab values (`docs/VAULT-SCHEMA.md` §5) |
| `session_window` | yes | the clock law, incl. the DST rule for London (§1.4) |
| `signal_ts_is_fill` | yes | bool — `true` = `ts` is the fill stamp, not a trigger stamp (§7 waiver) |
| `mechanism_families` | yes | from the 7-family vocabulary of `docs/REPORT-correlation-2026-08-04.md` / battery `FAMILIES` — **this is what the input-family veto reads at prereg time, before any returns exist** (brief §3 item 1) |
| `input_columns` | yes | exact column names the entry/gates read — the prereg template's field (`docs/VALIDATION-PROCESS.md` §1) |
| `sizing_regime` | yes | `funded-governed` (profile + base named) \| `research-native` — the $150-vs-$160-class distinction made structural |
| `execution_semantics` | yes | which flatten / close-reverse / one-per-level rules are baked in (`none` allowed, stated) |
| `commission_included` | yes | bool — whether `pl` includes the engine's $5 round-turn per 1-lot |
| `exit_reason_vocab` | yes | the values this emitter uses |
| `counts` | yes | `rows`, `days`, `span_days`, `net_pl` — **expected values so drift is checkable** (`reproduce` implies `expected`, `docs/VAULT-SCHEMA.md` §2.2) |
| `provenance` | yes | the vault §2.2 block verbatim: `commit`, `book` {generator, artifact, span, profile, base, overlay}, `reproduce`, `expected`, `seed` where stochastic, `holdout_looks_spent` (0 is a statement, not an omission) |

---

## 5. What each consumer reads (so the required set stays honest)

| consumer | columns consumed | manifest fields consumed |
|---|---|---|
| Battery 1 — input-family veto | — | `mechanism_families`, `input_columns` |
| Battery 2 — day P&L Pearson/Spearman | `day`, `pl` | `sizing_regime` (units of $) |
| Battery 3 — tail dependence | `day`, `pl` | — |
| Battery 4 — timing overlap | `day`, `fill_ts`, `exit_ts` | `session_window` |
| Battery 5 — sample adequacy | `day` (row presence) | `counts` |
| Battery 6 — combined ruin | `day`, `pl` (+ `fill_ts`, `risk_dollars` for the one-account replay) | `sizing_regime`, `execution_semantics` |
| Selector B1/B2/B3 + shuffle (`docs/PREREG-selector.md`) | `day`, `pl`, `ts` (eligibility), `fill_ts`, `risk_dollars`, `conviction` | `key`, `sizing_regime` |
| Promotion rung 3 funded MC (`docs/VALIDATION-PROCESS.md` §6) | `day`, `pl` | `provenance` (book identity) |
| Vault `correlation_edge` (`docs/VAULT-SCHEMA.md` §3.7) | — (numbers arrive via battery) | `provenance`, `vault_id`, `mechanism_families` |

Everything in §2.1 is consumed by at least one consumer; nothing a consumer needs is
missing. That closure is the contract's whole point.

---

## 6. Worked example A — the NY canon book, re-expressed

**Source**: `output/funded_book_lucid_fit.parquet` (762 trades, 230 active days, net
+$82,543, span 2025-06-02..2026-07-08 — verified this session; matches the reference
in `scripts/funded_book.py` docstring and live HANDOFF §1) joined on `ts` back to
`funded_book.load_book("fit")` for the columns the funded parquet doesn't carry.
`ts` is unique after rule-L suppression, so the join is exact.

| emission column | source | note |
|---|---|---|
| `strategy` | constant `ny_canon` | |
| `day`, `ts`, `pl` | funded parquet: `day`, `ts`, `pl` | `pl` = micros × dollars_1lot / 10, $ funded-governed, commission-inclusive |
| `sess` | funded parquet `sess`, renamed | `pre` → `ny-pre`, `gold` → `ny-gold` (vault vocab, `docs/VAULT-SCHEMA.md` §5) |
| `conviction` | funded parquet `tier` | |
| `qty_mnq` | funded parquet `micros` | already MNQ |
| `risk_dollars` | funded parquet `risk_d` | = base × tier |
| `direction`, `fill_ts`, `exit_ts`, `entry`, `stop`, `exit_price`, `risk_pts` | `load_book("fit")` via `ts` | **CR overlay already applied as LAW** — rule J/K exits final, rule L rows absent |
| `exit_reason` | overlay-hit rows (`flipped`): `output/aikido_cr_{span}.parquet` `cr_exit_reason`, joined on `ts`+`direction` (the same join `load_book` uses for its overlay merge); untouched rows: `load_book` `exit_reason` | `load_book` merges `cr_dollars_1lot`/`cr_exit_ts`/`cr_exit_price` but **not** `cr_exit_reason` (`scripts/funded_book.py` lines 136–138), so overlay-hit rows keep stale V8 reasons — measured this session: 102 of 762 fit rows |

**Every required column is suppliable today. No gaps.** A real row (trade 1 of the fit
span, read this session):

```
strategy=ny_canon  day=2025-06-02  ts=2025-06-02T08:39:00-04:00  direction=long
fill_ts=2025-06-02T08:40:00-04:00  exit_ts=2025-06-02T08:44:00-04:00
entry=21260.00  stop=21248.75  exit_price=21289.00  exit_reason=partial+target
risk_pts=12.75  qty_mnq=9  risk_dollars=240.00  pl=+435.375  sess=ny-pre  conviction=1.5
```

Manifest:

```yaml
schema: emission-v0.1-proposed
strategy: ny_canon
vault_id: "strategy:ny-canon"
span: fit
key: [strategy, ts, direction]        # asserted unique (apply_close_reverse.build_span)
sessions: [ny-pre, ny-gold]
session_window: "pre 08:00-09:30 ET, gold 09:40-10:30 ET (src/canon/scorer_ny.py PRE_WIN/GOLD_WIN)"
signal_ts_is_fill: false
mechanism_families: [depth-walls, overnight-structure, order-flow, vwap,
                     trigger-density, structural-events]     # 6 of 7; battery FAMILIES
input_columns: [dep_wall_below_d, WALLSZ, on_extreme_age, fill_delta_conf, d15_conf,
                bp5opp, lon_slope_d, ent_vs_vwap_sd_dir, trigdens_30, struct_event]
sizing_regime: "funded-governed (profile lucid, base 160, budget 853.33)"
execution_semantics: {two_sessions: true, close_reverse: true, one_per_level: true}  # J/K/L, LAW
commission_included: true             # $5 round-turn per 1-lot, scripts/capture_replay.py
exit_reason_vocab: [stop, target, be_stop, partial+stop, partial+target, partial+be_stop,
                    flip, open_flatten, partial+open_flatten]   # book reasons on untouched
                                        # rows + cr_exit_reason on the 102 overlay-hit rows
counts: {rows: 762, days: 230, span_days: "2025-06-02..2026-07-08", net_pl: 82543}
provenance:
  commit: "2157069"                   # regenerated at this repo state per
                                      # docs/REPORT-correlation-2026-08-04.md
  book: {generator: scripts/funded_book.py, artifact: output/funded_book_lucid_fit.parquet,
         span: fit, profile: lucid, base: 160, overlay: cr}
  reproduce: "python -m scripts.funded_book --span fit --profile lucid"
  expected: "+$82,543"
  holdout_looks_spent: 0
```

The `holdout` twin is free — `--span holdout` produces the same shape (+$48,211, the
certified holdout reference), and the sealed-span book already exists, so emitting it
spends nothing.

---

## 7. Worked example B — the old London book, re-expressed

**Source**: `output/london_canon_book.parquet`, rows with `size > 0` only (445
candidate rows → 136 taken, 109 active days of 206, net +$35,219; taken-trades span
2025-06-02..2026-07-08, candidate universe runs to 2026-07-10 — verified this
session; 69 columns). Status per
`docs/CANON.md`: BRAKE's reference material, "a *reference to beat*, not a book to
trade".

| emission column | source | note |
|---|---|---|
| `strategy` | constant `london_old` | |
| `day`, `direction`, `entry`, `stop`, `exit_price`, `exit_reason`, `risk_pts` | same-named columns (`risk`) | exit stamps/reasons "unusually complete and useful for gates" (`docs/HANDOFF-london-rebuild.md` §2) |
| `ts` | `fill` | **[GAP — waiver]**: the old book carries no trigger stamp distinct from the fill; `ts := fill_ts` with `signal_ts_is_fill: true` and the 4-part key. Future books emit true L0 trigger stamps |
| `fill_ts`, `exit_ts` | `fill`, `exit` | mixed-offset ISO strings, §1.4 parse |
| `qty_mnq` | `size × 10` | NQ lots → MNQ |
| `risk_dollars` | `risk × 20 × size` | derived, pre-commission — stated in manifest |
| `pl` | `pl` (= `dollars × size`) | **$ at research sizing** — see the sizing GAP below |
| `sess` | constant `london` | |
| `conviction` | `size` | Layer-2 multipliers {0.5, 1.0, 1.5} |
| `pattern`, `tf` (optional) | same-named | |

A real row (first taken trade, read this session):

```
strategy=london_old  day=2025-06-02  ts=2025-06-02T03:03:00-04:00  direction=long
fill_ts=2025-06-02T03:03:00-04:00  exit_ts=2025-06-02T03:25:00-04:00
entry=21245.25  stop=21221.50  exit_price=21221.25  exit_reason=stop
risk_pts=23.75  qty_mnq=10  risk_dollars=475.00  pl=-485.00  sess=london  conviction=1.0
```

**Gaps, honestly:**

- **`pl` at governed sizing — [GAP — needs backfill or waiver].** The old book's `pl`
  is research sizing: NOT budget-governed, NOT funded-accounted
  (`scripts/london_canon.py`; `docs/REPORT-correlation-2026-08-04.md`: "London alone
  at 6.9% P(bust) is NOT a shippable configuration... A funded-profile London book is
  the data contract's first job"). Waiver path: emit as-is with
  `sizing_regime: research-native` — exactly what the battery consumed for the
  2026-08-04 measurement, legal for dependence measurement, **illegal as a promotion
  or shared-budget input**. Backfill path: a funded-profile London book (who builds
  it: §9 item 1).
- **`ts` trigger stamp — [GAP — waiver]** as in the table above.
- **`holdout` span — [GAP — blocked].** `output/london_canon_book_holdout.parquet`
  does not exist and **building it is a holdout look** requiring a declared ledger
  entry (`docs/VALIDATION-PROCESS.md` §4). No `emission_london_old_holdout.parquet`
  until Angus declares.
- **`commission_included` — [OPEN — needs Brake]**: confirm the engine convention
  ($5 round-turn per 1-lot) applies to the old book's `dollars` before the manifest
  states `true`.
- **`execution_semantics: none`** — not a contract gap but a declared fact: the old
  book has no session flatten, no close-reverse, no one-per-level ("NONE — London
  holds to the stop", `scripts/london_canon.py`; measured consequence: 2 of 136 taken
  trades held into NY hours, exits 09:00/09:30 ET — so the battery's 0
  simultaneous-open-risk minutes is a measured fact, not a structural guarantee).
  When Angus's J/K/L-equivalent rulings land (owed — live HANDOFF §8.6), the book
  changes → re-emit, supersede the old manifest with a pointer, never overwrite
  silently (`docs/VAULT-SCHEMA.md` §6).

Manifest (delta from example A):

```yaml
strategy: london_old
vault_id: "strategy:london-old-book"
span: fit
key: [strategy, ts, direction, entry]    # ts is the fill stamp; same-minute siblings possible
sessions: [london]
session_window: "08:00-10:00 Europe/London -> ET per-day via
  scripts.run_triggers_london.london_window_et (03:00-05:00 or 04:00-06:00 ET; never hardcode)"
signal_ts_is_fill: true                  # [GAP — waiver], see contract §7
mechanism_families: [depth-walls, overnight-structure, order-flow, pattern-taxonomy]  # 4 of 7
input_columns: [dep_wall_below_d, dep_wall_above_d, ent_on_pos, on_range, cvd_ASIA,
                pattern, score]          # W/FAR, ROOM, ASIA/opp5 gates — scripts/london_canon.py
sizing_regime: "research-native (Layer-2 size 0.5/1.0/1.5; NOT budget-governed)"  # [GAP]
execution_semantics: none                # rulings owed — live HANDOFF §8.6
commission_included: "[OPEN — needs Brake]"
exit_reason_vocab: [stop, target, partial+stop, partial+target]
counts: {rows: 136, days: 109, span_days: "2025-06-02..2026-07-08", net_pl: 35219}
                                         # span_days = the EMITTED (taken) rows, so a drift
                                         # check recomputes it from the parquet; the 445-row
                                         # candidate universe (206 days) runs to 2026-07-10
provenance:
  commit: "db97e96"                      # artifact verified at this repo state
  book: {generator: scripts/london_canon.py, artifact: output/london_canon_book.parquet,
         span: fit, profile: native, base: n/a, overlay: none}
  reproduce: "python -m scripts.london_canon"
  expected: "136 taken, net +$35,219"
  holdout_looks_spent: 0
```

**Proof the interface works**: the correlation battery's entire 2026-08-04 run —
union/intersection Pearson −0.094/−0.110, tail co-crash 0.10, 0 overlap minutes,
paired-vs-shuffled ruin 0.5%/0.4% (`docs/REPORT-correlation-2026-08-04.md`) — is
computable from these two emissions plus manifests **without touching either
generator script**, and the union column of §3 is byte-for-byte the selector prereg's
B1. Every future candidate that emits this shape gets the full battery and all
selector baselines for the cost of two files.

**Out of scope, permanently**: `output/allyears_daily_books.csv` (the old E3/E4
day-ledger, 783 rows 2023–2026) cannot be expressed in this contract — no
timestamps (day-level only), NY-only (`docs/CANON-QA-LOG.md` entry 25), and
pre-2026-07-28 numbers are VOID as strategy truth (`docs/CANON.md`). It stays a
desk-lane (analog/regime) reference, not an emission.

---

## 8. Gap register — the two existing books against the contract

| contract requirement | NY canon (funded, lucid) | old London book |
|---|---|---|
| all 16 required columns | YES (funded parquet + `load_book` join) | 15 of 16 as-is; `ts` via waiver |
| signal `ts` distinct from fill | YES (trigger stamp) | **[GAP — waiver]** `ts := fill` |
| `pl` at governed sizing | YES ($160 base, J/K/L LAW) | **[GAP — needs backfill or waiver]** research-native only |
| execution semantics baked | YES (overlay is LAW) | none ruled — declared `none`; rulings owed (live HANDOFF §8.6) |
| `holdout` span emission | YES, free (book exists, +$48,211) | **[GAP — blocked]** building it = a declared holdout look |
| commission flag | `true` (engine convention) | **[OPEN — needs Brake]** confirm |
| manifest `input_columns` | YES (`src/canon/scorer_ny.py`) | YES (`scripts/london_canon.py`) |
| manifest provenance block | YES | YES |
| eligibility `E(d)` from signals, not fills | **[GAP — v0.2: `candidates` emission activates so E(d) = signalled days]** — interim E(d) = "≥1 taken trade" (§3) | same gap; worst for limit-entry books, where signalled-but-unfilled days are invisible |

---

## 9. The 30-minute agenda — what genuinely needs live agreement

Everything above is [PROPOSED] mechanics; these seven points are the actual
conversation. Nothing here self-authorizes.

1. **Sizing regime of emissions — the contract's first job.** Is `research-native`
   an acceptable emission (flagged, dependence-measurement-only) or must every
   emission be funded-governed? If the latter: **who builds the funded-profile London
   book** (Brake, as part of his rebuild, vs this chat as battery glue), and does it
   wait for the London execution-semantics rulings? Interacts directly with the
   account-architecture ruling (`docs/FOR-ANGUS-rulings-2026-08-04.md` §1) — under
   one account the shared-budget replay (§3) becomes mandatory, under separate
   accounts the union arithmetic suffices.
2. **The London `ts` waiver.** Accept `ts := fill_ts` + 4-part key for the old book,
   and require true L0 trigger stamps from every future emission (Brake's rebuild
   produces them at L0 by construction)?
3. **Per-signal outcome field now or later.** If the selector binds per-signal, v0.1
   needs `r` (per-signal outcome at shipped exits) — day-level P&L cannot score
   signal-level reassignment (`docs/PREREG-selector.md` §6.1). Default: per-day
   granularity, field stays reserved. Decide with the granularity ruling.
4. **Freeze the vocabularies once**: `sess` values and the mechanism-family list
   (shared with `docs/VAULT-SCHEMA.md` §5's starter lists, themselves
   [OPEN — needs Angus]), plus the `exit_reason` union. And the one quick Brake
   check: `commission_included` for the old London `dollars` (§7).
5. **Holdout emissions and the ledger.** Confirm: `emission_london_old_holdout` (and
   any future candidate's holdout emission whose sealed book doesn't exist) waits for
   a declared ledger look; NY's is free because the sealed book already exists.
   Confirm the ledger entry is the trigger, per `docs/VALIDATION-PROCESS.md` §4.
6. **Where emission commits land.** Emissions are research artifacts that must not
   touch the live arming branch (a docs commit refuses the next arm — live HANDOFF
   §4). Same branch/cadence answer as vault commits
   (`docs/VAULT-SCHEMA.md` §10.7 — [OPEN — needs Angus/Pat]); one ruling can cover
   both.
7. **Interim eligibility.** Ratify E(d) = "≥1 taken trade on day d" as the v0.1
   interim definition (`docs/PREREG-selector.md` §2.0 as amended; §3 here), knowing
   its limitation — signalled-but-unfilled days invisible, wrong for limit-entry
   strategies — and confirm the v0.2 target: activate the reserved `candidates`
   emission (§2.4) so E(d) derives from signal timestamps (§8 gap register).

**Sign-off:**
ANGUS — date: __________ — contract ratified (drop `-proposed`): __________
BRAKE — date: __________ — emitter for London candidates, format confirmed: __________
