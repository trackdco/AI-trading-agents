# TRADE PLAN — NQ London Pullback (10:00–13:00 UK) · Funded $50k

Mechanical. If a rule needs judgement, the answer is **no trade**.
Baseline "Scheme A". All times **Europe/London**.

---

## 1. THE SETUP (M15 bars only)

Trade **only** 10:00–13:00 UK. Outside the window: no entries, ever.

**LONG** — all four must be true on one closed M15 bar:
1. **Stack:** 20-MA > 50-MA > 200-MA, and price above all three.
2. **Wick:** bar low ≤ 50-MA (it touches/pierces).
3. **Close back:** bar closes above the 50-MA.
4. **Fading volume:** bar volume < mean volume of the prior 10 bars.

**SHORT** — exact mirror (20 < 50 < 200, price below all; bar high ≥ 50-MA; closes below; fading volume).

## 2. EXECUTION

| | Rule |
|---|---|
| **Entry** | Open of the **next** M15 bar. Market. |
| **Stop** | `min(swing-low-5, 50-MA) − 1 tick` (long; mirror short), **clamped 5–70 pt**. |
| **Target** | **3R**, fixed at entry. **Never move it. Never cap it.** |
| **Time exit** | Flat at **16:30 UK** if neither hit. |
| **One at a time** | **Never hold two positions at once.** No new entry while a trade is open. |
| **Day-stop** | **First *closed* loss of the day = done trading that day.** No exceptions. |

**DO NOT:** move to breakeven · trail the stop · tighten the stop · take partials ·
exit early on a "weak" wall. Every one of these was tested and every one **lost money**
(−$1.2k to −$13k). The wide stop and the uncapped 3R tail *are* the edge.

Expect to sit through heat: the median winner goes **0.42R against you** before paying,
and 2 of 33 winners went to ~0.95R (nearly the stop) and still hit 3R.

## 3. SIZING — buffer ladder

**Buffer = account balance − $50,000.** Recheck the rung *before every trade*.
**Confirm** = 3-min CVD delta at entry agrees with trade direction. No CVD data → treat as **unconfirmed**.

| Buffer | Confirmed risk | Unconfirmed risk |
|---|---|---|
| < $750 (eval / pre-lock) | $250 | $125 |
| $750 – $2,000 | $350 | $175 |
| $2,000 – $4,000 | $500 | $250 |
| ≥ $4,000 | $700 | $350 |

**Start on the bottom rung.** The buffer is the protection, not the win rate.

## 4. SIZE TABLE — MNQ micros ($2/pt)

`contracts = risk$ ÷ (stop_pt × $2)`, **rounded DOWN**.

| Buffer rung | | 15pt | 25pt | 36pt* | 50pt | 70pt |
|---|---|---|---|---|---|---|
| **< $750** | confirm $250 | 8 | 5 | 3 | 2 | 1 |
| | unconf $125 | 4 | 2 | 1 | 1 | **—** |
| **$750–2k** | confirm $350 | 11 | 7 | 4 | 3 | 2 |
| | unconf $175 | 5 | 3 | 2 | 1 | 1 |
| **$2k–4k** | confirm $500 | 16 | 10 | 6 | 5 | 3 |
| | unconf $250 | 8 | 5 | 3 | 2 | 1 |
| **≥ $4k** | confirm $700 | 23 | 14 | 9 | 7 | 5 |
| | unconf $350 | 11 | 7 | 4 | 3 | 2 |

\* 36pt ≈ the median stop. **—** = 1 MNQ ($140) exceeds the $125 allowance → **skip the trade**.

> **Correction vs the handoff:** it listed 70pt → **2** MNQ on the $250 rung. Exact is
> 1.79; 2 contracts risks **$280**, i.e. **12% over-risk** on the tightest rung.
> Rounded down = 1. On a funded account the whole plan rests on the buffer — take the
> under-risk, not the over-risk.

## 5. DAILY ROUTINE

1. Pre-open: note balance → compute buffer → fix today's rung.
2. 10:00 UK: start watching M15 closes. No entries before 10:00.
3. On a valid signal: **only if flat** — enter next bar open, place stop + 3R target
   **immediately**, then leave it alone. If a position is already open, **skip the signal.**
4. On a **closed** loss: **stop for the day.**
5. 13:00 UK: no new entries. 16:30 UK: flat anything open.
6. Skip DST-transition days entirely (e.g. 2025-11-28, 2026-04-03).

---

## 6. WHAT THIS IS BUILT ON — read before risking money

- **55 trades · 12.5 months (Jul 2025 – Jul 2026) · one favourable regime.**
- Reproduced bit-exactly from the repo on 2026-07-26 with the full CVD set (29/55 confirmed).
- Backtest, net of costs: **+$17,763**, max DD **$917**, **56% WR** (31W/24L),
  avg win +2.98R / avg loss −1.02R, every quarter green.
- On the ladder above: **+$36,978**, modelled P(blow) **0.16%**, 5th-percentile **+$22,151**.

> ### ⚠ CORRECTION (2026-07-26) — the 55-trade book above contains LOOKAHEAD
>
> The day-stop was implemented as *"walk the day's signals in order, stop once a trade's
> **final net** is negative."* Signals fire every 15 min but trades take a **median ~2 h** to
> resolve, so when a second signal fired while the first was **still open**, the backtest
> declined it using a result that did not exist yet. `scripts/london_daystop_lookahead.py`
> rebuilds all three readings at flat $300/R:
>
> | Day-stop rule | trades | netR | P&L | max DD |
> |---|---|---|---|---|
> | **A** as-written (the 55-trade book) | 55 | +67.95 | +$20,384 | $1,256 |
> | **B** realtime, stacking allowed — *what the old §2 wording actually produced* | 65 | +57.77 | +$17,330 | **$2,152 — BREACHES** |
> | **C** realtime **+ one position at a time** — *the rule now in §2* | 41 | +38.15 | +$11,445 | $1,256 |
>
> The 10 trades A hides are **all losers** (−10.18R) — same-day, same-direction signals firing
> into the adverse move that is busy stopping out the first trade.
>
> **B also stacks up to 5 positions at once** (15 of 41 days stack) and contains **7 correlated
> multi-stop clusters**; the worst is **−4.10R in a single bar** (2025-10-20 12:00) = **$2,052
> at the $500 rung, $2,873 at the $700 rung** — account-ending in one minute against a $2,000
> trailing DD. Book A contains **zero** such clusters *by construction*, which is why none of
> the §6/§7 drawdown or P(blow) figures see them.
>
> **Treat §6 and §7 numbers below, and the whole of §3/§4, as computed on book A.** The honest
> expectation under the corrected rules is **book C: 41 trades, +38.15R** — roughly **56% of the
> headline P&L** for the same drawdown. Everything downstream needs re-deriving on C.

**Caveats — these are not optional context:**
- **The figures in this section are book A (lookahead).** See the correction box. Re-derive on C.
- **No 2023–24 holdout. Out-of-sample is UNPROVEN.** Thresholds were frozen on 2025 and the
  book was sliced many ways; treat any future tweak as a holdout candidate, not a ship.
- The $917 DD, 3.06R worst streak and 0.16% blow-probability are **in-sample / Monte-Carlo**,
  not live results.
- 55 trades is a **small sample** — roughly 4–5 trades a month. Expect long quiet stretches.
- **NO-LOCK firms: the ladder is ruinous — TESTED, see §7.** This plan is validated only for
  trailing DD that **locks at $50k**.

**If live results diverge, the answer is to size down or stop — not to re-tune the geometry.**


---

## 7. NO-LOCK FIRMS — do not use the ladder

`scripts/funded_nolock.py` re-runs the plan under a trailing drawdown that **never locks**
(the floor follows the equity peak forever, so a drawdown can end you at *any* balance —
not just inside the first $2k). Same 55-trade book, 8,000 Monte-Carlo paths each.

| Sizing | LOCK P(blow) | **NO-LOCK P(blow)** |
|---|---|---|
| flat $150 | 0.00% | 0.00% |
| flat $250 | 0.00 – 0.07% | 0.05 – 0.40% |
| flat $300 | 0.05 – 0.24% | 0.44 – 1.05% |
| flat $400 | 0.59 – 1.04% | **5.6 – 8.6%** |
| **userB ladder** | **0.03 – 0.15%** | **49.9%** |

Ranges are shuffle→bootstrap Monte-Carlo (8,000 paths each). Under NO-LOCK the ladder is a
**coin flip — 49.9% — and it blew the account on the actual historical 55-trade path**
(+$8,888 instead of +$36,978). That is not a simulated tail; it is what the real sequence did.
5th-percentile outcome collapses from +$35,868 (lock) to +$5,035 (no-lock).

**Why:** the ladder scales risk *up* with the buffer. Under a lock, that buffer is banked
safety. Without a lock the floor keeps rising with your peak, so you are taking $700 risk
in a regime where a normal losing streak still reaches the floor. The buffer never becomes safe.

**Rule:** confirm your firm's drawdown type before sizing.
- **Locks at start** → ladder as written in §3.
- **Trails forever (no lock)** → **ladder is off the table.** Flat **$150–$250**, no scaling.

## 8. REPRODUCING THIS

```bash
export LONDON_SCRATCH=/path/to/workdir
git worktree add --detach $LONDON_SCRATCH/canon_wt origin/claude/getting-started-6lwnvs  # bars + CVD
python3 scripts/london_conviction.py    # -> london_conviction_book.csv (55 trades)
python3 scripts/funded_sim.py           # LOCK model + ladders
python3 scripts/funded_nolock.py        # LOCK vs NO-LOCK
```

**Verified reproduction (2026-07-26).** With all five CVD footprints present the pipeline
reproduces the original run **bit-exactly**: 55 trades, 31W/24L, 56% WR, +2.98R/−1.02R,
**29/55 confirmed**, fixed-contract V1 **+$75,668**, funded base-$300 **+$17,763 / DD $917**,
ladder **+$36,978 / DD $2,139**. Every figure matches the handoff.

**Remaining data notes:**
- `nq_1m_master.parquet` (bars) is on the **canon** branch only, not brake — point `LONDON_WT`
  at a canon worktree (as above) or copy the file. Brake is self-contained for CVD, not bars.
- **Jan 2026** is the one genuine CVD hole (2 trades); they size at the unconfirmed half-rung.

## 9. SCALE-OUT — tested, FAILS (do not use)

`scripts/london_scaleout.py`. Bank a fraction at +XR, let the rest run to 3R, stop unchanged.
Nine variants (25/50/75% banked at +1R/+1.5R/+2R). **Every one loses:**

| banked at | 25% | 50% | 75% |
|---|---|---|---|
| +1.0R | −12.2R | −24.2R | −36.2R |
| +1.5R | −8.7R | −17.2R | −25.7R |
| +2.0R | **−4.9R** | −9.7R | −14.4R |

vs a **+67.95R** baseline. Best case still sheds 4.9R.

**Mechanism — the ratio is fatal:** **31 of 31 winners** touch +1R, so every winner pays the
tax. Only **7 of 24 losers** touch +1R, so only 7 get rescued. You are trading 31 taxes for
7 rescues. Win rate *rises* (56% → 69%) while money *falls* — the exact vanity-metric trap the
tail law predicts.

**Why it is structural, not a close call.** At the *best* cell (bank 25% at +2R) the deficit
decomposes exactly: 31 winners each taxed 0.25R = **−7.75R**, against 4 rescued losers each
gaining 0.75R = **+3.00R**, less ~0.15R commission → **−4.90R**. To reach breakeven you would
need roughly **11 of 24 losers** to touch +2R instead of 4 — and the nearest additional
candidate misses by **67 ticks**. This is not a rounding error away from working.

**Independently audited** (three adversarial lenses, 2026-07-26): trade set token-identical to
the book builder; per-trade touch flags re-derived by a from-scratch walk sharing no code
(identical counts, zero conservative/optimistic divergences); every cost assumption stacked in
scale-out's favour — including a physically impossible one — moves the best cell only
−4.90R → −4.60R. All nine still lose.

**Two disclosed simplifications** (neither reverses it): the day-stop is frozen from the
baseline book rather than re-derived on scaled P&L (bound: ≤ +0.87R, and 0.00R at the best
cell); and the 16:30 / next-day fallback branches are untested here because this book has
**zero time exits** — the exit mix is 37 stop / 33 target.

**Scale-out now joins the tested-and-failed list** (tighter stop, breakeven, armed trail, entry
filters, ROOM-target). Six interventions tested, six losses. The uncapped 3R tail is the edge.
