# LONDON REV-3 BUNDLE — the complete decision package for ANGUS

**One read, one signature. Everything below is committed on
`claude/london-canon-strategy-3p57jk`-lineage (session-3 branch); every number traces
to a named verdict doc. Nothing in this bundle has touched the sealed 2023/24 span.
Until signed, prereg rev 2a (window 08:00–10:00, V8, 187-trade book) remains the
strategy of record; both configurations are rehearsed and the sealed run is one
command under either.**

---

## 1. The decision: sign ONE configuration

| | **rev 2a** (as pre-registered) | **rev 3** (this bundle) |
|---|---|---|
| window | 08:00–10:00 London | 08:00–**09:45** |
| gate | wall = (W or FAR), floor 9.5pt | same, **plus score-0 veto** |
| concurrency | none enforced | **one position at a time** |
| management | V8 (partial 50% + trail) | **V1 (BE on touch of +1R, run to structure target)** |
| fit book | 187 tr / +$22,795 / 57% WR / +0.513R / maxDD $2,550 | 130 tr / **+$22,665** / 29% WR* / **+0.758R** / **maxDD $1,310** |
| era split (net) | +$8,178 / +$14,618 | +$7,965 / +$14,700 (mean R +0.578 / +0.898) |
| holdout projection | ~84 trades, 78% power | ~59 trades, ~85% power if effect persists |

\* rev 3's WR optic is structural: V1 scratches ~40% of trades at breakeven; mean R
and net are the health metrics (`docs/LONDON-MGMT-TOURNAMENT.md`).

**Declared forward expectation stays ≈ +0.48 mean R under EITHER config** — the rev-3
improvements are rulings and a tournament result; the guard-failed window cut may not
inherit into the prior.

## 2. The rev-3 elements, each with its honest evidence status

1. **Window 08:00–09:45** — RULING (Brake), evidence-informed but guard-failed
   (late-bucket permutation p=0.076). Disclosed: the boundary was examined three
   times on fit data and is now CLOSED to fit-side moves
   (`docs/LONDON-REV3-BASELINE.md`). At 09:45 the plain-book cut is better than
   free: +$270 net AND −39% maxDD; the removed 15 minutes were net-negative alone.
2. **Score-0 veto** — the one loss-filter that survived all three bars
   (era-bad + removes-negative-money + n≥10) out of 13 candidates tested across two
   scans (`docs/LONDON-VETO-SCAN.md`, `docs/LONDON-LIQUIDITY-SCAN.md`). Mechanism:
   W/FAR agree r=0.834; score-0 = the only wall check disagrees with its twin AND
   thin book AND quiet level. 11 trades, 36% WR, net negative in both eras.
   Thresholds FROZEN as literals: dep_thick > 57, dep_resist > 29, trigdens_30 > 8
   (`src/canon/scorer.py`; ±10% perturbation flat).
3. **One position at a time** — CONSTITUTION ENFORCEMENT (strategy-doc §5, your
   NY-confirmed rule, never implemented for London). Costs fit net vs the
   overlapping book; per-trade quality unchanged; combined with the veto it admits
   better second trades (`docs/LONDON-TF-CONVICTION.md`, `docs/LONDON-VETO-SCAN.md`).
4. **V1 management (BE at +1R)** — YOUR declared priority tournament
   (decision log 2026-07-17: "BE-at-1R vs none"), finally run through the real
   engine: V1 +$22,360 vs V8 +$17,941 vs V0 +$14,850 at 09:30, era-consistent, and
   the February hand log already traded BE. Mechanism: scratches 17 near-miss full
   losers AND stops paying the partial haircut (winners reach full structure targets
   36 times vs V8's 5) (`docs/LONDON-MGMT-TOURNAMENT.md`).

## 3. Three engine rulings needed REGARDLESS of which config is signed

1. **Same-order twins.** TF grids detect one level 1–4 min apart and converge on
   identical orders; the backtest double-counts the fill (329 population groups; 9
   doubled positions in the rev-2a book). Live cannot double-fill one limit. Rule:
   enforce first-order-wins dedup (rev 3 serialization subsumes it), or record the
   frozen book as a deliberate exception. ALSO: 46 twin groups got different
   simulated exits from the identical order — V8 management context leaks from the
   trigger candle; engine fix in Pat's lane (`docs/LONDON-TF-CONVICTION.md` §0).
2. **Day-stop units.** The $400 stop was applied to 1-LOT dollars in every backtest;
   a funded account's Vault counts FUNDED dollars, and the books differ (144 vs 155
   trades at $250 sizing — `docs/LONDON-FUNDED-TEST.md`). Rule which unit binds
   before any funded deployment.
3. **No-realistic-target trades.** When no §6 menu level sits within reach, the
   engine posts a far level (8–36R) — functionally "no TP, managed by stop." On fit
   these uncapped runners PAID (+10.4R and +8.2R trades). Rule: leave as runner /
   cap / time-exit — an explicit rule either way
   (chat-documented; priced in `docs/LONDON-EXIT-LAB.md`).

## 4. Post-holdout menu (declared now, decided AFTER validation — sizing stays flat
1 lot per your standing ruling)

- **Sizing ladders** (`docs/LONDON-LADDER-945.md`, `docs/LONDON-LADDER-LAB.md`):
  lead candidate = $200 base, 1.5× on Mon/Fri A+ (B2 & both-wall), 0.5× on
  no-conviction: +$23,222 funded, net/DD 27.6, ~94% of the gain is outcome-aligned.
  Calendar tier is TODAY-MINED (weakest evidence layer). Alternatives: wall-only
  1.5/0.5 (tier-test validated), flat.
- **Grade-scaled exits** (`docs/LONDON-EXIT-LAB.md`): A+ runs to 4–5R/menu, mid
  takes 1.5R — bar-walk +$23,328, needs an engine variant + forward data.
- **Eval math** (`docs/LONDON-MC-LADDER.md`): full edge P(bust) 0.2%, pass in ~32
  days; HALF edge P(bust) ~20%; zero edge ~73%. Ladder = faster, flat = safer at
  half-edge. The holdout picks the row.

## 5. Robustness, verified (`docs/LONDON-ROBUSTNESS.md`)

Costs: +4 ticks/side still nets +$17.9k (V1). Perturbation: plateaus on floor and
veto thresholds; the window's early side is the one soft edge (09:15 costs −31%) —
consistent with the guard, disclosed. P(bust) full-edge 0.2%.

## 6. The sign-off table

| item | who | action |
|---|---|---|
| Prereg rev 2a draft (§2/§3/§4 changes) | **Brake** | re-confirm (rev-1 signature does not carry) |
| Config: rev 2a as written OR this rev 3 | **ANGUS** | sign ONE; §1/§3/§4 + the rev-3 elements if rev 3 |
| Engine rulings 1–3 (§3 above) | **ANGUS** | rule each, either direction |
| Sealed-span session ranges (context metric, not outcomes) | **ANGUS** | optional yes/no (era-diagnosis flag) |
| Spot-check sheet (`docs/FOR-ANGUS-spot-check-sheet.md`) | **ANGUS** | 22 trades, a/b/c each — the human calibration pass |

## 7. What happens mechanically after signature

1. Build the sealed span's artifacts: `build_l0/l1/l2/l3 --span holdout` (+
   `--mgmt V1` L2 arm if rev 3). Mechanical, same code the fit rebuild verified.
2. One command: `london_holdout_report --span holdout --config <signed>
   --authorized-by "ANGUS, <date>"`. Both configs' rehearsals PASS and are
   byte-deterministic; the sealed report writes once and the runner refuses a
   second opening.
3. Read at the declared resolution: **a near-miss on +0.48 is not decay; a sign
   flip is.**
