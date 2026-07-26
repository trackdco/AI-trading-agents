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
| **Day-stop** | **First loss of the day = done trading that day.** No exceptions. |

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
3. On a valid signal: enter next bar open, place stop + 3R target **immediately**, then leave it alone.
4. On a loss: **stop for the day.**
5. 13:00 UK: no new entries. 16:30 UK: flat anything open.
6. Skip DST-transition days entirely (e.g. 2025-11-28, 2026-04-03).

---

## 6. WHAT THIS IS BUILT ON — read before risking money

- **55 trades · 12.5 months (Jul 2025 – Jul 2026) · one favourable regime.**
- Backtest, net of costs: **+$17,763**, max DD **$917**, **56% WR** (31W/24L),
  avg win +2.98R / avg loss −1.02R, every quarter green.
- On the ladder above: **+$36,978**, modelled P(blow) **0.16%**, 5th-percentile **+$22,151**.

**Caveats — these are not optional context:**
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
| flat $250 | 0.00% | 0.06 – 1.4% |
| flat $300 | 0.00 – 0.65% | 2.0 – 3.9% |
| flat $400 | 0.14 – 2.8% | 1.1 – 20% |
| **userB ladder** | **0.03 – 0.64%** | **23 – 75%** |

Ranges bracket the missing-CVD uncertainty (see §8). On the optimistic end of that bracket
the ladder **blew the account on the actual historical 55-trade path** — not a simulated
tail, the real sequence.

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

**Known data gap:** `footprint_q3_2025` / `footprint_q4_2025` are not in the repo, so
Jul–Dec 2025 trades carry no CVD flag and size at the unconfirmed half-rung — **15 confirms
here vs 29 in the original run**. Trade *geometry* is unaffected and reproduces exactly
(55 trades, 31W/24L, 56% WR, +2.98R / −1.02R), because CVD only sets the sizing multiplier.
Every sizing-dependent figure above is therefore given as a **bracket**: lower = as-is,
upper = those days all counted as confirmed. Restore the two parquets to collapse it.
