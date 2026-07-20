# ROADMAP — next session (highest expectancy across the full NY session)

**Frame (non-negotiable):** optimize **expectancy**, not win rate. WR rises as a *byproduct* of cutting
bad trades; chasing WR by shrinking targets halves the money (tail law — Angus proved it). Every item
below is a **hypothesis** → validate on Feb–May in-sample → confirm on **Jun/Jul held-out** → Angus
sign-off → strategy-doc version bump. Add ONE lever at a time; never stack filters in-sample (that's
how the magnet+5-filters went negative, and how the magnet 60% turned out to be one trade).

Grounding numbers are from the full Feb–Jul champion journal (n=146), this session.

---

## P0 — ENGINE AUDIT FIRST (does the code grade trades correctly?)
If the grader is wrong, every expectancy number is wrong. Do this before more signal-hunting.
- [ ] Port the crash fix in `selection_signal_test.py` (`if d == "miss"` on a cached DataFrame →
      `isinstance(d, str)`). The magnet headline came from code that didn't run.
- [ ] **Fill realism** in `src/backtest/engine.py`: limit entry/target must fill AT price (no adverse
      slip); only the stop (market) eats slippage. Same-bar stop+target → resolve stop-first (honest).
      Tiny-wick stops (<~3pt) blow R up via fixed costs — add/verify a min-stop floor.
- [ ] **No-lookahead audit:** developing indicators only; signals on closed bars; entry activates next
      bar; MTF arbitration doesn't peek. Add a test if missing.
- [ ] **TZ/DST + session boxes:** config flags that `sessions.resample_ohlcv` bins from midnight
      (`origin='start_day'`) — verify session-box/HTF alignment is correct, not off by the session anchor.
- [ ] **Parity gate (Step 4, still ungated):** run `detector_parity.py` / `make_parity_report.py`
      against Angus's Feb 11 09:48 & Feb 17 09:50 chart values — prove BB/VWAP/POC are within 1 pt.
- [ ] Reproduce champion 146t/+$14k from the canonical script to confirm no drift.
- **Deliverable:** audit report — confirmed bugs + P&L impact of each.

## P1 — SESSION EXPECTANCY MAP + TIME GATING (trade the whole session, not just premarket)
The champion caps entries at 10:15. The 10:00 bucket is +0.68R — there's likely edge past the cap.
- [ ] Grade triggers across the FULL day (extend past 10:15 → 11:00, 12:00, and afternoon) and build a
      15/30-min expectancy map, month-by-month (Feb–May scored; Jun/Jul held out).
- [ ] **Kill the money pit:** 09:15–09:45 is −0.81R / −0.33R. Propose a stand-down there (extends the
      existing 09:30–09:40 rule). Measure P&L recovered.
- [ ] **Extend into NY:** test 10:15→11:00 (and later) as added windows; keep only buckets with edge
      that holds across months. 09:45–10:15 is +0.48R overall but NEG in May & Jul — trade, don't
      over-weight; re-check once bugs are fixed.
- **Deliverable:** a "when to trade" schedule in config (trade 08:15–09:00, stand down 09:15–09:45,
      trade 10:00–?, proven NY windows), each bucket expectancy-validated OOS.

## P2 — LOCK THE DEPTH-FREE SELECTION SIGNALS (validate, then gate)
Reproducible now, no data buy. Validate each with the CI + permutation rigor used on the magnet.
- [ ] CVD-confirm (+0.39R lift), ≥6pt real-stop (+0.47R), combo (+0.65R, n=73) — confirm significance,
      then bake in as champion gates.
- [ ] Exhaustion (CVD divergence) — looked great at n=4; needs real n before trusting.
- [ ] Regime / day-type gating (chop stand-down) and HTF-location filter (no longs at range top, §7).
- One axis at a time; report marginal expectancy per lever.

## P3 — ORDER-FLOW CONCEPTS (once Angus's Feb–Jul depth lands)
- [ ] Absorption (large wall on the REJECTION side + opposing CVD, holding) and magnet (target-side
      wall) — re-run on the real Feb–Jul sample; same CI/permutation gate. April n=5 was untestable.
- [ ] Only if absorption survives: book imbalance, iceberg/refill.
- Depth carries spoofing/replay risk — treat as confirmation, never a sole trigger.

## P4 — NEW CONFIRMATION AXIS (later): market internals $TICK / breadth
Classic index-futures fade confirm; could push past ~45% WR. New data pull; only after P0–P3.

---

## Concepts to add — by data availability
- **Now (depth-free):** time-of-day gating, CVD-confirm, CVD-divergence exhaustion, real-stop floor,
  regime/day-type stand-down, VWAP-band location, ATR/vol regime, news-proximity buffer.
- **After depth:** absorption, magnet, book imbalance, iceberg/refill.
- **New pull:** $TICK / breadth internals.

## Cutting unnecessary trades — the levers (each OOS-validated, added one at a time)
1. **Time gating** — kill 09:15–09:45 (biggest single bleed).
2. **≥6pt real-stop floor** — removes junk instant-stop-outs.
3. **CVD-confirm gate** — flow must agree with direction.
4. **Counter-trend confluence bump** (§7: 3 vs 2).
5. **Regime stand-down** on chop days.
6. **Location filter** — no longs at HTF range top / shorts at bottom.
7. Keep max-3/day + first-2-by-time (already champion).
Discipline: measure the *marginal* expectancy of each; if a lever doesn't lift OOS, drop it.
