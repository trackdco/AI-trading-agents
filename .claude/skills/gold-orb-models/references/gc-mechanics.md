# GC / MGC Mechanics for ORB Implementation (verified against CME materials, Aug 2026)

## Contract math
- **GC** (COMEX Gold): 100 troy oz; quoted USD/oz; **min tick 0.10 = $10/contract; 1.00 point = $100/contract**. A $10 move = $1,000/contract.
- **MGC** (Micro Gold): 1/10th — **$1/tick, $10/point**. Default vehicle for first backtests and small live sizing.
- Money translation for reports: a 3.0-point opening range = $300/contract (GC) of full-range stop before slippage; always print both R and points.

## Sessions (ET primary; AEST = ET +14h during US DST, +15h during US standard time — both listed)
- **Globex week:** Sun 18:00 ET (Mon 08:00 AEST) → Fri 17:00 ET (Sat 07:00 AEST).
- **Daily maintenance halt:** 17:00–18:00 ET Mon–Thu (07:00–08:00 AEST); trading day rolls at the 18:00 ET reset.
- **COMEX pit-legacy / deepest US metals liquidity:** 08:20–13:30 ET (22:20–03:30 AEST next day; +15h: 23:20–04:30).
- **London open:** ~03:00 ET (17:00 AEST; +15h: 18:00 — note London itself shifts with UK DST).
- **NYSE cash open (the anchor all three source models use):** 09:30 ET (23:30 AEST; +15h: 00:30).
- **Daily settlement:** VWAP over 13:29:00–13:30:00 ET for the active month (03:29–03:30 AEST).
- US and Australian DST transitions don't align — recompute the offset for the specific backtest dates rather than hardcoding one.

## The anchor question (gold-specific, highest-impact variable)
9:30 ET has no native meaning for gold — GC has been trading for hours by then. Candidate anchors, ranked by prior: **08:20 ET** (start of deepest US metals liquidity) → **~03:00 ET London** → **09:30 ET** (retail convention only; note it still inherits equity-open volatility spillover, so it is not a null candidate). Sweep all three before tuning any other parameter; report each anchor's result separately in R.

## Rollover & data
- Delivery months: **Feb, Apr, Jun, Aug, Oct, Dec**; physically delivered; exit/roll before First Notice Day (last business day of the month preceding the contract month).
- Backtests: **continuous back-adjusted series, volume-based roll** a few days before First Notice. Never test a single un-rolled contract — range sizes and stops distort near expiry.
- If sourcing MGC data directly, check liquidity depth in earlier years; MGC volume was thin pre-2020 — GC back-adjusted is the safer long-history spine, with MGC used for execution assumptions.

## Cost model (mandatory)
- ≥1 tick/side slippage baseline (GC $10, MGC $1); **2 ticks/side** in the first minute after the range completes and within ±15 min of 8:30 a.m. ET US releases (CPI/PPI/NFP) and FOMC.
- Add round-turn commission per broker (typically ~$2–4 GC, ~$1 MGC retail).
- Robustness check: any edge that dies moving 1→2 ticks was microstructure noise — report the 2-tick result alongside the 1-tick result, always.

## Known behavioural notes
- Spreads tightest and depth greatest during the 08:20–~12:00 ET US/London overlap.
- Independent testing (QuantifiedStrategies) found naive ORB unprofitable on ES and explicitly also on NQ/GC/SI/CL without added filters — hold that prior; the burden of proof is on the filter stack, not on optimism.
