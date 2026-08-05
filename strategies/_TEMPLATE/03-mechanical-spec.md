# <Strategy Name> — Mechanical Specification v0.1

**Stage 3.** Precise enough that someone could code this without asking a single
question. Every ambiguity left here becomes a guess made by whoever implements
it — and trading semantics guessed by an engineer is the most expensive mistake
available in this repo.

---

## Plain English

_Restate the whole thing in five sentences: when it fires, where you get in,
where you're wrong, where you're out. Angus must be able to read only this
section and recognise the trade._

---

## 1. Scope

| Field | Value |
|---|---|
| Instrument | |
| Session window (local, with tz) | |
| Entry timeframe(s) | |
| Context timeframe(s) | |
| Max concurrent positions | 1 (repo invariant) |

## 2. Trigger

Conditions, all of which must hold on a **closed** candle:

1. 
2. 
3. 

Multi-timeframe arbitration if several fire at once: 

## 3. Entry

| Field | Rule |
|---|---|
| Order type | |
| Price | |
| Fill requirement | price must trade fully through the limit |
| Cancel condition | |

## 4. Stop

| Field | Rule |
|---|---|
| Placement | |
| Never widened | yes (Vault-enforced) |
| Tick rounding | round to 0.25 at the order boundary |

## 5. Target

| Field | Rule |
|---|---|
| Selection | |
| Front-run | level ∓ F points, F = |
| Minimum RR to take the trade | |

## 6. Trade management

| Field | Rule |
|---|---|
| Baseline (V0) | set and forget |
| Variant under test | |

## 7. Invented parameters

Everything here was a discretionary point in the source that we chose a number
for. **These are the only things Stage 5 is allowed to tune** — anything tuned
that isn't on this list is undeclared curve-fitting.

| # | Parameter | Default | Where it came from | Tunable range |
|---|---|---|---|---|
| 1 | | | dossier discretion #_ | |

## 8. Context tags to record on every trigger

Needed for the Stage 5 slice analysis. Recording them costs nothing at run time
and not having them means re-running everything.

- [ ] session, time bucket (30-min)
- [ ] HTF trend flag (up / down / range)
- [ ] ATR tercile
- [ ] day of week
- [ ] minutes to/from nearest scheduled release
- [ ] confluence count
- [ ] book imbalance at entry *(where MBP-10 exists)*
- [ ] resting size within N ticks of entry *(where MBP-10 exists)*
- [ ] CVD slope over the prior K minutes *(blocked — see data-inventory §3)*
- [ ] MAE, MFE in R

## 9. Known data limitations

_From `context/data-inventory.md`. State the fallback chosen for any missing
input, and the consequence for the OOS test._

## Version log

| Version | Date | Change | Reason |
|---|---|---|---|
| v0.1 | | initial | from 02-hypothesis.md |
