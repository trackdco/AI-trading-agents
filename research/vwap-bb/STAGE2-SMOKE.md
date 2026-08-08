# STAGE 2 — SMOKE TEST · **COMPLETED AND SEALED**

**The result exists, hashed and immutable, before the pass marks are finalised.** That property
is the point of this stage, and it holds only if nobody looks. **Nobody has.**

No outcome column has been read, printed, summed, averaged, counted or branched on. The script
carries a self-check that scans everything it prints for outcome tokens and aborts if any
appears; it passed.

---

## Result

| | |
|---|---|
| **Completed** | **YES** |
| Workbench sessions | **539** (2023-01-03 → 2025-01-31) |
| **Sessions PROCESSED** | **501** |
| Sessions EXCLUDED | **38** |
| Errors | **0** |
| **ADMITTED TRADES** | **1,423** |
| **Trades / session** | **2.8403** |
| Runtime | 1.1 min |
| Output | `research/vwap-bb/data/workbench_results_SEALED.parquet` |
| Rows × columns | 1,423 × 35 |
| **SHA-256** | **`a9ddc2947ca6a5f4c7e453d90427bed91710d1bc94c86de81fa9b381739bd4f0`** |

### Exclusions

| reason | sessions |
|---|---|
| holiday / short session | 22 |
| roll session (4.3) | 8 |
| session after roll (4.3) | 8 |

Reconciliation: **501 + 38 + 0 = 539 ✓**

### Frequency against the pre-registered tripwires

The axis structure is **OPEN** (pre-registration §10.3), so no single tripwire is hardcoded.
Measured **2.8403 trades/session** against every divisor in §6:

| divisor | tripwire | verdict |
|---|---|---|
| /1 | 0.7631 | **CLEARS** |
| /4 | 1.1720 | **CLEARS** |
| /5 | 1.2373 | **CLEARS** |
| /8 | 1.3745 | **CLEARS** |
| /16 | 1.5758 | **CLEARS** |
| /72 | 2.0091 | **CLEARS** |

**Gate 6 does not reopen at any axis structure under consideration.**

### Candidate audit — entry logic only, no outcomes

| | count |
|---|---|
| dropped: E1 entry beyond the wick extreme | 10,202 |
| dropped: no menu level clears the RR floor | 456 |
| dropped: fill would land at or after EOD flatten | 25 |
| stand-down: long and short on one bar (tie-break level 2) | 3 |

### Determinism

The sealed artefact was **reproduced byte-identical on a second independent run**. For a file
whose entire value is its hash, that is not a nicety — a non-reproducible seal proves nothing.

---

## The engine was rewritten before it ran, and that was not optional

A pre-run adversarial review — five independent reviewers, each on a different dimension, all
returning high confidence — found defects that would have been baked into the seal. **A bug
found after sealing is expensive precisely because the seal's value is that the result predates
the pass marks; re-running destroys that.** Every finding below was confirmed against the code
before being fixed.

| # | defect | severity | why it mattered | fix |
|---|---|---|---|---|
| 1 | **EOD flatten was tested BEFORE stop/target on the same bar** | material | 4.5 silently overrode 4.1. A 15:55 bar that traded through the stop and recovered was recorded as a flatten, not a stop. Worse, because every stop is forced to exactly −R, the flatten branch was the *only* exit that could lose more than one unit of risk — on precisely the bar where the stop check had been suppressed | Flatten now exits at the **OPEN** of the first bar ≥ 15:55, so none of that bar's range is used either way |
| 2 | **`open_until` off-by-one in the one-at-a-time gate** | fatal | A new position could fill at the OPEN of the very bar on which the previous position exited. It also mixed a signal-anchored base with a fill-anchored duration, so missing minutes loosened the gate | Replaced the whole batch gate with the **strictly causal streaming loop** already verified equivalent in `STAGE1-PIT-AUDIT.md` §4 |
| 3 | **A4 target feasibility ran AFTER `tie_break`** | material | An infeasible winner silently killed the entire signal minute instead of yielding to a feasible runner-up | Stop and target are now decided **at signal time** as absolute prices, per candidate, **before** the tie-break |
| 4 | **Hardcoded tripwire 0.4862** | material | That is the superseded gate-4 signal-count figure, below every value in the pre-registration's §6 table. A frequency of 0.9 would have printed "CLEARS" while actually reopening gate 6 | Reports against the **whole §6 table**; presumes no axis decision |
| 5 | **`trig()` returns a set; iterated unsorted** | minor→serious | Hash randomisation made candidate order vary between runs, so `trigger_kind` varied, so **the sealed SHA-256 was not reproducible.** For this artefact that is close to fatal | `sorted(trig(...))` |
| 6 | **Roll detection used `sorted(sym_of[d])[0]` — alphabetical, not chronological** | minor | `NQH4` sorts before `NQZ3`. **Confirmed: 6 of 8 roll dates were one session late** | Chronological `contract_key()` on (year digit, month code) |
| 7 | `for k in rows[0]` raised IndexError on an empty result set | operational | Would have destroyed the run *and* the error list after full runtime | Guarded |
| 8 | Docstring advertised a self-check that did not exist | minor | A false claim about the safeguards in my own file | **Implemented it** rather than deleting the claim |
| 9 | `minutes_held` was a bar count | minor | Understates the hold across missing minutes | Both `minutes_held` and `bars_held` recorded |

Roll dates, before and after fix #6:

| | dates |
|---|---|
| alphabetical (wrong) | 2023-03-14, 06-13, 09-12, 12-11; 2024-03-12, 06-18, 09-17, 12-17 |
| **chronological (used)** | 2023-03-**13**, 06-**12**, 09-**11**, 12-11; 2024-03-**11**, 06-**17**, 09-**16**, 12-17 |

Six moved by one session. Because 4.3 also excludes the session *after* each roll, the wrong
dates would have excluded the wrong pair each quarter — trading a genuine roll session and
discarding a clean one.

---

## Design decisions the review forced, recorded because they are choices

**Order placement.** Stop and target are absolute **prices fixed at signal time** from the
intended E1 entry (the BB MA), exactly as a live order would be. The fill then happens at the
next bar's open per §4.2, and realised risk is `|fill − stop_price|` — the risk actually taken,
not the risk intended. Both are recorded (`stop_distance_points`, `intended_stop_distance`),
along with `slippage_vs_intended`.

This resolves defect #3 cleanly: A4 feasibility is a **signal-time** decision, so it can be
evaluated per candidate before the tie-break, and it uses only information a live trader has
when submitting the order.

**A gap through the stop before filling** is recorded as a drop, not a trade — if the market has
already traded through the stop when the fill would occur, the E1 limit would not have filled at
a sane price anyway. Counted in the audit.

---

## What this stage did NOT do

- **Nothing was read from the parquet.** `read_results()` raises `SealedResultsError` without
  the token. That guard is not a security boundary — it is a file, and anyone can open it — it
  is a **speed bump against absent-mindedness**, and it is honest to say so.
- **No expectancy, win rate, P&L, equity curve or drawdown was computed** at any point.
- **The holdout was never addressed.** `assert_workbench()` armed on every session.
- **Nothing was tuned.** The engine implements the frozen spec plus A1/A4/A5/A7 and the §4
  accounting rules, and nothing else.

**N_trials remains 0.** Reading this file will be the first act that spends it, and it must not
happen until PREREGISTRATION.md §10.4 is signed.
