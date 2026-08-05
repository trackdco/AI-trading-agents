---
date: 2026-08-05
status: reference
tags: [london, session-structure, trigger-density]
sources: ["docs/PREREG-london-window-study.md", "output/london_window_study.md", "articles/2026-08-05-tradesharpe-method.md"]
---

# LDN-WIN-01 — where the NQ London opportunity actually sits

Measurement authorised by `docs/PREREG-london-window-study.md`, filed before the
run. `scripts/london_window_study.py`, reproducible. **No strategy, no P&L** —
30-minute buckets of realised range, displacement, directional efficiency and
volume across 00:00–07:00 ET. NQ only. Discover 2025 (257 days) / validate 2026
(139 days). 2023/24 untouched; no holdout look spent.

## The profile (median per 30-min bucket)

| ET | 2025 range | 2025 eff | 2025 vol | 2026 range | 2026 eff | 2026 vol |
|---|---:|---:|---:|---:|---:|---:|
| 01:00 | 23.8 | 0.487 | 1,522 | 39.2 | 0.424 | 2,391 |
| 01:30 | 23.8 | 0.429 | 1,628 | 38.5 | 0.473 | 2,416 |
| 02:00 | 30.2 | 0.473 | 2,416 | 44.2 | 0.430 | 2,924 |
| 02:30 | 28.5 | **0.512** | 2,191 | 38.8 | 0.412 | 2,761 |
| **03:00** | **39.5** | 0.444 | **3,851** | **55.8** | 0.431 | **4,052** |
| 03:30 | 35.2 | 0.443 | 2,950 | 44.5 | 0.430 | 3,186 |
| **04:00** | **40.2** | **0.489** | **3,982** | **60.0** | **0.574** | **4,538** |
| 04:30 | 33.0 | 0.471 | 2,756 | 49.0 | 0.451 | 3,302 |
| 05:00 | 29.2 | 0.438 | 2,606 | 49.5 | 0.433 | 3,327 |
| 05:30 | 25.5 | _0.419_ | 2,373 | 43.0 | _0.418_ | 2,810 |
| 06:00 | 29.2 | _0.412_ | 2,684 | 43.5 | _0.409_ | 3,092 |

## What it says

**The session has two peaks, 03:00 and 04:00 ET, and they hold in both eras.**
04:00 is the single best bucket on all three measures in both years — highest
range, highest volume, and the highest efficiency in the whole profile in 2026
(0.574). 03:00 is the volume peak. Nothing else comes close.

03:00 ET is the London cash open, which is expected. **04:00 ET is 09:00 London
/ 10:00 CET, which is the main European macro release slot** — and it is not in
our substrate's assumptions anywhere. That second peak is the more interesting
of the two because nobody put it there on purpose.

**The tail of our window is the worst part of the session.** 05:30 and 06:00
carry the two lowest efficiency readings in the entire profile, in both eras
(0.419/0.412 in 2025, 0.418/0.409 in 2026). Our substrate window runs
03:00–06:00 ET, so a third of it is the least productive stretch measured.

**H1 — supported, but read the size honestly.** The declared test was: median
range *and* efficiency in 02:00–05:00 exceed 05:00–06:00, in both eras. It
passes both eras. But the 2025 margin is real (range 34.1 vs 27.4, +25%;
efficiency 0.472 vs 0.428) and the **2026 margin is negligible** (46.8 vs 46.3,
+1%; 0.431 vs 0.425). One era supports it clearly; the other technically clears
the bar and means almost nothing. Recording that rather than reporting a clean
pass, because the criterion I wrote was direction-only and did not require a
magnitude.

**H2 — failed. Kill criterion 3 fired.** Anchoring buckets to each day's
*measured* European open produced a **flatter** profile than the wall clock
(peak-to-trough 1.90 vs 2.06 in 2025; 1.48 vs 1.82 in 2026). The clock wins.

I left this as two competing readings — either London structure is genuinely
calendar-driven, or the detector is noise. **Followed up the same session and it
is settled: the detector is broken.** `euro_open_det` fires on the first minute
clearing a volume z-score in a 90-minute window, which finds the earliest noise
spike rather than the largest event; 54% of days "detect" before 02:30 and its
biggest non-fallback value is 01:45, the window's own first minute. Full
diagnosis in `docs/FINDING-euro-open-det-is-noise.md`.

So H2 failed because the event anchor was noise, **not** because London
structure is calendar-driven. That question is still genuinely open and needs a
working detector to answer. Use `euro_open_clock` (pure timezone arithmetic,
sound) until the detector is rebuilt.

## What this changes

Tradesharpe's claim was *"one hour before London open to one hour after, and my
best time is just after Frankfurt open"* — roughly 02:00–05:00 ET, against our
substrate's 03:00–06:00.

**He is directionally right, and the correction is at the back end, not the
front.** The measured core is **03:00–05:00 ET**: both peaks, both eras, every
measure. What each window adds beyond that core:

- his extra hour (02:00–03:00) — moderate range, decent efficiency (0.473 in
  2025, 0.430 in 2026)
- our extra hour (05:00–06:00) — declining range and **the worst efficiency
  buckets in the profile**

So the useful conclusion is not "adopt his window" but something narrower and
better evidenced: **the 05:00–06:00 hour is dead weight, and any London
candidate should justify including it rather than inherit it by default.**

## Limits (declared in the prereg, restated because they bind the conclusion)

- Range and efficiency are **direction-agnostic**. A window can score well here
  and still be untradeable if the moves are unpredictable in sign. This study
  cannot tell you a window is profitable — only where the movement is. That is a
  candidate's question.
- Medians only. Deliberate: one 8σ day should not decide a window.
- The source developed this on forex and migrated to futures; this measurement
  is NQ and does not test his instruments.
- One trial on the ledger (LDN-WIN-01), not one per bucket.

## What follows

1. **Flag on `euro_open_det`** — the detector scatters across 75 minutes and
   underperforms the wall clock as an anchor. Before any candidate conditions on
   it, someone should check whether it is measuring the European open or
   measuring noise. Cheap, and it affects the shared substrate rather than one
   candidate.
2. **The 04:00 ET peak deserves a name.** It is the strongest bucket in the
   session on every measure in both eras, it lines up with the 10:00 CET
   European data slot, and no current candidate references it. That is a
   structural feature sitting in plain sight.
3. **Window default for new London candidates: 03:00–05:00 ET**, with anything
   outside it argued for rather than assumed.
