# FINDING — `euro_open_det` does not detect the European open

**Severity: shared substrate. Caught before anything depended on it.**
Found while interpreting LDN-WIN-01 (`research/findings/london-window-LDN-WIN-01.md`),
where anchoring to `euro_open_det` produced a *flatter* profile than the plain
wall clock — the opposite of what a real event anchor should do.

## The column

`scripts/london_day_features.py`, documented as:

> `euro_open_det` — detected European open: first minute 01:45–03:15 ET with
> volume z ≥ 3 vs same-clock-minute trailing 20-day stats; fallback 03:00

## What it actually produces

Distribution across all 912 substrate days:

| Value | Days | What it is |
|---|---:|---|
| **01:45** | 27 | the **first minute of the search window** |
| 01:46–01:59 | 219 | decaying tail from the window boundary |
| 02:00–02:59 | 419 | scattered, no mode |
| **03:00** | **247 (27%)** | **the fallback value — indistinguishable from "no detection"** |
| 03:01–03:15 | 38 | |

- **54% of days detect before 02:30** — more than an hour before the London cash
  open.
- The single largest non-fallback value is **01:45, the window's first minute**,
  with a smooth geometric decay after it. That shape is the signature of a
  first-crossing rule on a noisy series: it fires at the earliest opportunity,
  not at the largest event.
- The 03:00 mode is **not a detection**. It is the fallback firing when no
  minute in the 90-minute window clears z ≥ 3. Reported as if it were a
  measurement, it flatters the column badly — a reader sees "27% detect at 03:00,
  which is the London open" when the correct reading is "27% failed to detect".
- On DST-mismatch days it should concentrate near the shifted open. It does not:
  27 land on the 03:00 fallback, the rest scatter (01:47, 02:08, 02:28, 02:30,
  02:53 …).

## Diagnosis

A "first minute where volume z ≥ 3" rule over a 90-minute window does not find
the biggest volume event in that window — it finds **the earliest minute that
happens to clear a threshold**. Pre-open volume is thin, so its trailing-20-day
standard deviation is small, so a z-score of 3 is easy to hit on very little
activity. The genuine European-open surge at 03:00 is far larger, but by then
the detector has already fired on noise and stopped looking.

The build's own verification gate did not catch it because the gate checks that
the *mode* is 03:00 — which it is, purely because the fallback is 03:00.
**The gate passes on the failure mode.**

## Impact

- **`euro_open_clock` is sound.** It is pure timezone arithmetic —
  `pd.Timestamp(f"{day} 08:00", tz=UK).tz_convert(ET)` — and is the correct
  column to use. The DST-mismatch handling built on it (mismatch weeks opening
  at 04:00 ET) is unaffected.
- **`euro_open_det` should not be used for conditioning or anchoring.**
- **Nothing currently depends on it.** A grep across the repo finds it only in
  the builder that creates it and in my own article from earlier today (now
  corrected). No candidate, prereg or emission reads it. This is the cheap case:
  found before it cost anything.
- It also **explains the H2 failure in LDN-WIN-01**, which I had left as two
  competing readings. It is now settled: event-anchoring lost to the wall clock
  because the "event" was noise, not because London structure is calendar-driven.
  That question remains genuinely open and needs a working detector to answer.

## Recommended fix (not applied — substrate change, Brake's call)

Replace first-crossing with **argmax over the window**: the minute in
02:30–03:30 ET with the highest volume z-score, rather than the first to cross a
threshold. Report *no detection* explicitly rather than silently substituting
03:00, so a failed detection is visible instead of masquerading as a successful
one. Then change the verification gate to check the detected value against
`euro_open_clock` on mismatch weeks — a gate that can actually fail.

Not applying it here: it changes a shared substrate column that the London
program builds on, and the substrate has a named owner. Flagged rather than
fixed.

## Reproduce

```bash
.venv/bin/python -c "
import pandas as pd
df = pd.read_parquet('output/london_day_features.parquet')
print(df.euro_open_det.value_counts().sort_index().to_string())
print('fallback 03:00:', (df.euro_open_det=='03:00').mean())
print('before 02:30  :', (df.euro_open_det<'02:30').mean())
"
```
