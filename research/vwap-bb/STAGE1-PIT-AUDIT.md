# STAGE 1 — POINT-IN-TIME AUDIT · **CLEAN** · stage 2 permitted

**Every indicator reflects only information available at the signal minute.** No indicator is
contaminated. Stage 2 is unblocked.

Reproduce: `python3 audit_pit.py` and `python3 audit_pit_holes.py` in
`research/star-trading/tools/`. Per-minute detail: `data/audit_pit_detail.json` (280 rows).

N_trials: **0**. Holdout: never addressed — `assert_workbench()` armed on every session read.

---

## 1. Method

A **naive reference implementation**, written independently and recomputed from scratch over
an explicit bar slice at each test minute. Comparing the detector's incremental accumulators
against a second incremental implementation would let a shared bug pass; a plain loop over a
slice cannot share the detector's state bugs.

Three references per indicator per minute:

| | definition | failure mode it catches |
|---|---|---|
| **A** | bars with OPEN ≤ T−1 — everything complete at T | *(this is the only correct value)* |
| **B_full** | the WHOLE session, read at T | compute-once-and-index-back on accumulating indicators |
| **A_plus1** | bars with OPEN ≤ T | the close-label off-by-one, which B_full cannot see |
| **D** | what the detector actually used | — |

**CONTAMINATED** = D matches B_full or A_plus1 where either differs from A.

**20 test minutes**, one per equal-width block of the sample so they span 2023-01-04 →
2024-12-26, and rotated through four intra-session windows (10:00, 10:30, 12:00, 14:00) —
an all-10:05 sample would never discriminate the session-range indicators.

---

## 2. Per-indicator verdict

| indicator | n | discriminating vs full-session | discriminating vs one-bar | D == A | LEAK full | LEAK +1 | neither | verdict |
|---|---|---|---|---|---|---|---|---|
| daily VWAP mid | 20 | 20 | 20 | 20 | 0 | 0 | 0 | **CLEAN** |
| daily VWAP sigma | 20 | 20 | 20 | 20 | 0 | 0 | 0 | **CLEAN** |
| NY VWAP mid | 20 | 20 | 20 | 20 | 0 | 0 | 0 | **CLEAN** |
| NY VWAP sigma | 20 | 20 | 20 | 20 | 0 | 0 | 0 | **CLEAN** |
| **POC / volume profile** | 20 | **16** | 1 | 20 | 0 | 0 | 0 | **CLEAN** |
| session high | 20 | 8 | 0 | 20 | 0 | 0 | 0 | **CLEAN** |
| session low | 20 | 7 | 1 | 20 | 0 | 0 | 0 | **CLEAN** |
| BB basis (entry TF) | 20 | 0 *†* | **12** | 20 | 0 | 0 | 0 | **CLEAN** |
| ATR(20) entry TF | 20 | 0 *†* | **12** | 20 | 0 | 0 | 0 | **CLEAN** |
| HTF classification | 20 | 16 | 0 | 20 | 0 | 0 | 0 | **CLEAN** |
| 4h range high | 20 | 10 | 0 | 20 | 0 | 0 | 0 | **CLEAN** |
| 4h range low | 20 | 9 | 0 | 20 | 0 | 0 | 0 | **CLEAN** |
| prior-day high | 20 | 20 | 0 | 20 | 0 | 0 | 0 | **CLEAN** |
| prior-day low | 20 | 20 | 0 | 20 | 0 | 0 | 0 | **CLEAN** |

*† **Stated rather than reported as a pass.** For a rolling indicator, a full-session array
positionally indexed at T **is** the trailing window — A and B_full agree by construction and
the comparison proves nothing. BB and ATR are therefore tested by the one-bar-ahead column,
which discriminates on 12 of 20 (the other 8 are minutes where the next 1m bar does not close
a new bar on that entry TF, so the window is unchanged either way).*

**POC was the highest-risk item in the brief** — a full-session volume profile computed once
and indexed back. It discriminates on 16 of 20 minutes and the detector matched the
point-in-time value on all 20. The profile is accumulated bar-by-bar inside the forward loop
and the argmax is taken at the signal minute; there is no full-session array anywhere.

**Prior-day levels** were the one indicator the first version of this audit could not test —
I was feeding the same value to both sides, which produced a meaningless UNTESTED. The test now
models the actual failure mode (recomputing the extremes from the **current** session) and
discriminates on 20 of 20.

---

## 3. Structural checks

| check | result |
|---|---|
| **Fractal confirmation** — a swing at 15m bar *j* must not be knowable until *j+2* | **PASS.** A synthetic spike placed on the last bar is not counted as a swing; it is counted only once 2 further bars arrive |
| **Close-label shift** — the last bar consumed must OPEN at T−1 and close at T | **PASS**, 0 failures across 20 minutes |
| **Full-array-then-index** | **None found.** Every accumulator (`dv`, `nv`, `poc`, `bb`, `tfacc`, `b15`, `acc15`, `h4`, `acc4`, `sess_hi/lo`, `tfatr`) is a running value inside one forward pass. No indicator is materialised as an array and indexed |
| **Warm-up seeding** | BB(20) on 5m reaches back to ~07:55 for a 09:36 signal; ATR(20) similarly; `b15` needs 5 bars; `h4` uses only closed 4h periods. **All reach backwards into the same session, none forwards.** The 5m TF's first eligible signal is 09:40, not 09:36, because 09:36 is not a 5m boundary |

---

## 4. The two holes, closed separately

The audit above had two gaps I could not close from inside it. Both are now closed by
`audit_pit_holes.py`.

### Hole 1 — `htf_flag` was its own reference

`audit_pit.py` imports `htf_flag` and uses it as **both** the reference and the detector value,
so it could not detect a bug **inside** `htf_flag` — specifically a wrong loop bound admitting
unconfirmed swings.

Closed with a reference built the opposite way round. `htf_flag` scans a finished array with a
bound of `range(n, len−n)`; the reference **accumulates swings streaming**, recording each only
at the bar where it first becomes confirmable. If the batch bound admitted an unconfirmed
swing, the two would diverge.

| | |
|---|---|
| Comparisons | **5,484** — every 15m boundary across 60 sampled sessions |
| Distinct `b15` prefix lengths | 92 |
| Flag distribution | range 3,017 · uptrend 1,415 · downtrend 1,052 |
| **Disagreements** | **0** |

The flag distribution matters: all three classifications occur in quantity, so the test is
discriminating rather than trivially agreeing on a constant.

### Hole 2 — the one-at-a-time gate uses a forward-looking `hold`

The admission loop sets `open_until = cm + hold`, and `hold` is obtained by walking bars
**after** `cm`. That looks like lookahead.

**It is not, and the argument is worth writing down.** The decision at a later candidate's
minute T2 is `T2 < open_until`. If true, every bar determining "the position is still open"
lies in [cm, T2] — all past at T2. If false, the position closed at or before T2 — also past.
The batch form computes it early, but the *information content* of the decision is causal.

Argument checked rather than trusted: closed with a **strictly causal streaming simulator**
that walks the session bar by bar, resolves an open position only against bars that have
arrived, and consults nothing beyond the bar it is on.

| | |
|---|---|
| Sessions compared | **113** |
| Identical admission sets | **113** |
| Different | **0** |
| Trades admitted, batch / streaming | **324 / 324** |

Identical on every session. The batch form uses no information a live system would lack.

---

## 5. What this audit does *not* establish

Stated so it is not read as broader than it is.

- **It does not verify the indicators are the ones Angus uses.** It verifies they are computed
  point-in-time. Whether the detector's daily VWAP matches his chart's is Stage 3's job, and
  Stage 3 is unanswered.
- **It does not cover the stage-2 entry-fill convention.** §4.2 of the pre-registration fills
  at the next bar's open; the detector audited here prices entry at the BB MA. Stage 2's engine
  changes that, and the changed path needs the same treatment.
- **20 minutes is a sample.** The reference is exact and the detector matched it on every
  discriminating comparison, but 20 is 20. A leak that fires on 0.1% of minutes would likely
  be missed.
- **`h4` is stale by design, not leaking.** The location filter uses only closed 4h periods, so
  it can be up to four hours old. That is point-in-time correct and possibly wrong as a rule —
  a separate question, not this audit's.

---

## VERDICT

**CLEAN — all 14 indicators, on at least one discriminating comparison each. Both structural
checks pass. Both holes closed.**

**Stage 2 is permitted.**
