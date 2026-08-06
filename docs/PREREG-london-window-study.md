# PRE-REGISTRATION — London session window study

Filed per `docs/VALIDATION-PROCESS.md` §1, BEFORE the measurement is run. The git
timestamp of this commit is the declaration. Trial family: **LDN-WIN-01**.

**This is a measurement, not a strategy.** No entries, no stops, no P&L. It
answers one structural question that sits underneath every London candidate we
might build, so getting it wrong is expensive and getting it right is cheap.

## Claim (falsifiable)

Source: Tradesharpe, who streams the London session live and has done for three
years (`research/articles/2026-08-05-tradesharpe-method.md` §1):

> *"Many people think London open is the best time to trade. **It's actually
> false. I like to trade 1 hour before London open and during London open and
> only an hour after.**"* [`7jCUl1Bh89Q` @ 16:00]
> *"My best time for London is probably **just after Frankfurt open**."*
> [`e6TIug9jQQs` @ 1:23:56]

Rendered as a testable claim on NQ:

**H1.** Directional opportunity — measured as realised range and absolute
displacement per unit time — is **concentrated in the window from one hour
before the European open to one hour after**, i.e. roughly 02:00–05:00 ET, and
is materially lower in 05:00–06:00 ET.

**H2.** The concentration is tighter when anchored to the **measured** European
open (`euro_open_det`) than to the 03:00 ET clock — i.e. the effect follows the
event, not the wall clock.

**Why it matters regardless of the answer.** Our London substrate window is
03:00–06:00 ET. His is 02:00–05:00. They overlap by two hours and disagree at
both ends. If H1 holds, every candidate built on the current window is fishing
in the wrong last hour and missing the first.

## Instrument and session

- **NQ only** (Angus 2026-08-05: the focus is Nasdaq futures). Gold and DAX are
  out of scope for this study even though the source trades them.
- Bars: `data/reference/nq_1m_master.parquet`, the verified candle store.
- Session features: `output/london_day_features.parquet`
  (`scripts/london_day_features.py`), which already carries `euro_open_det`,
  `euro_open_clock` (03:00 on 843 days, 04:00 on the 69 DST-mismatch days) and
  `dst_mismatch`.

## Eras

- **Discover: 2025** (calendar year). **Validate: 2026-01..2026-07.**
- **Inverse pass required** (§2.1): discover-2026 / validate-2025 must agree in
  direction. Era-flips kill.
- **2023/24 is NOT touched.** Not in any form, including descriptively. The
  sealed holdout is untouched and this study does not spend a look.

## What exactly gets computed (this document authorises exactly this)

Per trading day, over **00:00–07:00 ET**, in 30-minute buckets:

1. **Realised range** — (high − low) of the bucket, in NQ points.
2. **Absolute displacement** — |close − open| of the bucket, in points.
3. **Directional efficiency** — |close − open| ÷ (high − low), i.e. how much of
   the movement went somewhere. A liquidity-event window should show high range
   *and* high efficiency; chop shows high range and low efficiency.
4. **Volume** — contracts traded in the bucket.

Each computed twice:
- **clock-anchored** — fixed 30-min buckets from 00:00 ET
- **event-anchored** — buckets relative to that day's `euro_open_det`,
  from −120 min to +180 min

Reported as medians (not means — a single 8σ day should not decide this) by era,
with the DST-mismatch days broken out separately since their European open is a
measured 04:00 ET.

## Acceptance bars

This is descriptive, so there is no expectancy bar. The claim is judged on:

- **H1 supported** iff median range-per-30min and median efficiency in
  02:00–05:00 ET both exceed 05:00–06:00 ET, **in both eras**.
- **H2 supported** iff event-anchored bucketing shows a tighter peak (higher
  peak-to-trough ratio across buckets) than clock-anchored, **in both eras**.
- Minimum n: every reported bucket cell must have ≥ 100 days per era. With ~250
  trading days a year this is satisfied by construction; the check exists to
  catch data gaps rather than to gate the result.

## Kill criteria (the claim dies if ANY)

1. **No concentration.** Median range/efficiency in 02:00–05:00 is not above
   05:00–06:00 in both eras → the window claim is not true on NQ and we keep our
   existing window.
2. **Era flip.** The profile's shape disagrees between 2025 and 2026 → it is a
   regime artifact, not session structure.
3. **Clock beats event.** If clock-anchored is tighter than event-anchored, then
   `euro_open_det` is not adding anything and the DST handling is noise.

## What this study explicitly does NOT do

- It does not test a strategy, an entry, or an exit.
- It does not authorise a candidate. A window result feeds the *design* of
  later candidates; it is not itself tradeable.
- It does not touch 2023/24 or spend a holdout look.
- It adds **one** trial to the ledger (LDN-WIN-01), not one per bucket — the
  buckets are a single declared computation, not independent discoveries.

## Known limits

- Realised range and efficiency are proxies for "opportunity". They are agnostic
  to direction, so a window can score well and still be untradeable if moves are
  unpredictable in sign. That is a separate question and belongs to a candidate,
  not here.
- The source developed this on forex (GBPJPY/gold) and migrated to futures. The
  claim may hold on his instruments and fail on NQ; that is a legitimate outcome
  and would be recorded as such rather than as a failure of the study.
- Contract roll days are in the sample. Ranges spanning a roll are noted but not
  excluded, since we are measuring intraday buckets rather than close-to-close.
