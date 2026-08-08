# CODE PROVENANCE — what changed, and what that voids

**Asked 2026-08-08:** for every indicator, which file and function computes it, and whether any
were modified since the opportunity-set run that produced `candidates.parquet`.

**Answer: no indicator computation has changed. Every core file is byte-identical.** But there
is one real gap in the audit chain, found by this check and closed below.

---

## File-level, by git blob hash

Anchors: opportunity-set run `9449273` → Stage 1 CLEAN `a5862cb` → Stage 2 sealed `6e01386`.

| file | at `9449273` vs now | last commit that modified it | status |
|---|---|---|---|
| `alpha_data.py` | **IDENTICAL** `241d93a` | `f628f4e` (before) | **unchanged** |
| `vwapbb_signals.py` | **IDENTICAL** `3b49add` | `4b271a2` (before) | **unchanged** |
| `vwapbb_opportunity.py` | **IDENTICAL** `70285a3` | `9449273` (the run itself) | **unchanged** |
| `vwapbb_a7_selector.py` | new since | `d7047e0` — **precedes** Stage 1 CLEAN | **new, audited** |
| `stage2_smoke.py` | new since | `6e01386` — **after** Stage 1 CLEAN | **new, NOT audited as a file** |

Everything else added since `9449273` is analysis or measurement tooling that feeds no artefact:
`audit_pit.py`, `audit_pit_holes.py`, `mbp_census.py`, `mbp_feb2026.py`,
`stage4_orderflow.py`, `vwapbb_geometry.py`, `vwapbb_h1_tf.py`, `vwapbb_h1_handlog.py`,
`vwapbb_h2h3_map.py`, `vwapbb_signalcount_amended.py`. **Twelve files added, zero modified.**

---

## Per-indicator

| indicator | computed in | diff since opportunity-set | verdict |
|---|---|---|---|
| Daily VWAP + σ bands | `RunningVWAP` (`vwapbb_signals.py`), accumulated in each detector loop | none | **unchanged** |
| NY VWAP + σ bands | same class, 09:30-anchored | none | **unchanged** |
| Bollinger basis | `bb[tf]` deque, `BB_N` from `vwapbb_signals.py` | none | **unchanged** |
| ATR(20) | `tfatr` deque — **not used by the sealed pipeline** (volatility stand-down DISABLED, A2 #5) | none | **unchanged, unused** |
| Volume profile POC | `poc` defaultdict, `POC_BIN` from `vwapbb_signals.py` | none | **unchanged** |
| Session high / low | `sess_hi`/`sess_lo` in each detector loop | none | **unchanged** |
| HTF classification | `htf_flag()` (`vwapbb_signals.py`) | none | **unchanged** |
| 4h range (location filter) | `h4` deque in each detector loop | none | **unchanged** |
| Prior-day H/L | `prev_hl`, threaded from `main()` | none | **unchanged** |
| Cluster formation | `cluster_levels()` (`vwapbb_signals.py`) | none | **unchanged** |
| Trigger predicate | `trig()` (`vwapbb_opportunity.py`) | none in the function; **call site** now `sorted(trig(...))` in `stage2_smoke.py` only | **unchanged; deterministic ordering added at one call site** |

**No indicator's computation changed. No CLEAN evidence is void on those grounds.**

---

## The real gap this check found

**`stage2_smoke.py` is new since Stage 1 CLEAN, and it carries its own copy of the indicator
accumulation loop (`signal_candidates`). The point-in-time audit validated
`audit_pit.detector_dump`, which mirrors `vwapbb_a7_selector.process`. It never examined
`stage2_smoke`. The sealed result was produced by code the audit had not looked at.**

The Stage 1 report says this itself, under "what this audit does not establish": *"It does not
cover the stage-2 entry-fill convention… the changed path needs the same treatment."* **I wrote
that and then ran Stage 2 without doing it.** Small in consequence — see below — but a process
failure, and it is on record.

### Closed, two ways, both conclusive

**1. Statement-level diff of the indicator block** — 38 indicator-relevant statements in each of
`stage2_smoke.signal_candidates` and `vwapbb_a7_selector.process`. **4 differ**, both known
and neither semantic:

- `to_, th_, tl_, tc_ = …` — line wrapping, identical expression
- `sorted(trig(…))` — the determinism fix that made the sealed hash reproducible

**2. End-to-end equivalence** — `stage2_smoke.signal_candidates` against the audited qualifier,
on the same sessions, comparing the full candidate set `(minute, timeframe, direction, entry)`:

| | |
|---|---|
| sessions compared | **57** |
| identical candidate sets | **57** |
| different | **0** |

Any indicator drift would move a level, move a cluster, and change that set. It does not change.

**3. Indicator values re-derived** against the naive slice reference at the 20 audit minutes,
across all nine indicators:

| | |
|---|---|
| minutes checked | **20** |
| fields disagreeing | **none** |

### Verdict

**The Stage 1 CLEAN evidence transfers to `stage2_smoke.py`.** It now rests on a verification
rather than on an assumption, which is what it should have rested on before the run.

---

## Provenance of the sealed artefact

| | |
|---|---|
| `workbench_results_SEALED.parquet` SHA-256 | `a9ddc2947ca6a5f4c7e453d90427bed91710d1bc94c86de81fa9b381739bd4f0` |
| produced by | `stage2_smoke.py` blob `b515edb89b7ff03620044a0d39dde1bac1532306` |
| indicator inputs from | `vwapbb_signals.py` `3b49add` · `vwapbb_opportunity.py` `70285a3` · `alpha_data.py` `241d93a` |
| selector / geometry from | `vwapbb_a7_selector.py` blob `eeff30ecfd1416de2891982f59b463a4b0314d98` |
| reproduced byte-identical | yes, second independent run |

**Any change to any of those blobs voids the seal and requires a re-run.**

---

## Standing rule, added

**Before any run that produces a sealed or reported artefact, diff the producing code against
the last audited version and record the blob hashes.** A file that is *new* is not thereby
*audited* — this check was prompted from outside, and it should have been automatic.

**N_trials: 0. Sealed result untouched.**
