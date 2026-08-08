# NOTES — blind re-implementation of SPEC.md

## Headline

| | |
|---|---|
| **Sessions processed** | **539** — every `session_end_date <= 2025-01-31` the store holds (2023-01-03 … 2025-01-31). The store holds 796; the 257 after the seal date were never read. |
| **Trades produced** | **1,583** (2.9369 / session) |
| Sessions with ≥1 trade | 537 |
| Direction mix | 839 long / 744 short (53.0 / 47.0) |
| By entry TF | 1m 803 · 2m 337 · 3m 268 · 5m 175 |
| Trades/session distribution | 3 → 515 sessions · 2 → 16 · 1 → 6 · 0 → 2 |
| Output | `blind_trades.json`, sorted by (session_date, signal_minute, entry_tf); byte-identical across reruns; sha256 `8116166a969781893bc9dd…` |

Run: `python3 blind_impl.py`. Pure standard library, ~90 s.

## Independent checks that fell out of the build

These were not targets — they are quantities the spec happens to publish, which the
implementation reproduces without being fitted to them.

| check | spec | mine |
|---|---|---|
| A13 NY σ̂ census, all 7 rows (n = 6/10/20/30/35/50/90) | 9.23 · 11.12 · 16.00 · 19.48 · 20.91 · 24.69 · 30.10 | **identical to 0.01 on every row**, over the same 537 sessions A13 cites |
| A5 "the **29.6%** of triggers whose E1 entry falls on the wrong side of the wick extreme" | 29.6% | **29.54%** |
| A10 fractal example, 2025-01-22 | 08:30 & 08:45 both 21934.25; strict `>` falls back to 21905.00 at 06:15; A10 rule ⇒ **uptrend** | all three reproduced; flag at 09:50 = **uptrend** |
| A7 "levels 3, 4 and 5 **never fire at all**" | 0.0% | 0 of 6,917 ties (6,702 at level 1, 215 stood down at level 2) |
| A7 "blocked — position open" | 15.6–25.9% | 25.5% |
| A9 admitted trades with the location gate OFF | 2.9002 / session | 2.9369 / session |

Where I land outside the spec's published ranges: qualified candidates/session **78.6** (A7's four
readings span 8.87–47.43), 3/day cap binds on **95.5%** of sessions (A7: 63–91%), ties on **23.5%**
of signal minutes (A7: 16.4–22.9%), median hold **3 min** (A7: 5–7). I am more permissive than any
of their four readings. Note those tables predate A13: A12 records that the σ-band eligibility
rule is *"new and unrun"*, and A13 replaced the fixed 10:00 boundary with a live per-instant test
that is satisfied on ~71% of RTH minutes — so the published candidate counts are not measurements
of the specification I implemented.

## The single most important thing for the adjudicator

**Trade count is almost invariant to the ambiguities; trade identity is not.** Sweeping each
genuine fork one at a time (`sensitivity.py`, trade counts only — no outcome computed):

| variant | trades | qual/session | trades also in the baseline set |
|---|---|---|---|
| **baseline (chosen readings)** | **1583** | 78.6 | — |
| cluster = single-linkage chaining | 1561 | 59.0 | **1071 / 1583** |
| §7 invalidation band = other side | 1580 | 89.4 | **879 / 1583** |
| `range` flag needs 3 confluences | 1534 | 46.4 | **990 / 1583** |
| ATR(20) = Wilder instead of SMA | 1584 | 78.9 | 1538 / 1583 |
| target menu without prior-day/week H/L | 1577 | 74.0 | 1389 / 1583 |
| F = 2.0 | 1584 | 78.6 | 1555 / 1583 |
| F = 3.0 | 1584 | 78.5 | 1560 / 1583 |

Every variant lands within ±3% on count — which is §10.1(5) being true (*"the cap, not the
strategy, sets which trades are taken"*) — while as few as **55%** of the individual trades
survive. So: **two implementations agreeing on ~1,500 trades tells you almost nothing, and a
per-trade diff tells you everything.** Adjudicate on the trade sets, not the totals.

## Things to look at first if the two runs disagree

1. **`signal_minute` off by exactly +1 on every trade** → AMBIGUITIES A-01. The three readings of
   "the trigger bar's CLOSE" differ by a uniform constant; this is one decision, not 1,583.
2. **`target` differs but entry/stop match** → A-08 (F = 2.5 vs 2 vs 3) or A-13 (target-menu
   membership: I excluded Asia/London/pre-market boxes, data extremes, pullback origin and
   HTF range extremes, each for a stated reason).
3. **`entry` differs from the BB MA by several points on ~19% of trades** → A-10. TASK.md's
   "not the intended limit" is read as standard limit accounting: a bar that opens through the
   limit fills at the better open. 302 of 1,583 fills do this, median 7.52 pts, all on the very
   next bar, 284 of them because the BB MA already sits on the far side of the trigger close.
   That is A5's *"degenerate at both ends"* showing up in the output.
4. **`|entry − stop|` is not ≥ 10.00 on those same trades** → A-11, and deliberate: A5 says the
   floor *"applies at order placement only"*, so stop and target are fixed from the limit while
   `entry` reports the fill.
5. **Whole trades present in one set and absent from the other** → most likely A-07 (which ±1σ is
   "the opposing" one) or A-04 (cluster linkage), the two forks with the largest identity effect.

## One place I deliberately did not chase a matching number

Setting the `range` HTF flag's confluence minimum to 3 moves qualified candidates from 78.6 to
**46.4/session**, which sits almost exactly on A9's 46.9 and A7 reading A's 47.43. I kept **2**
anyway, because §4 states the rule as *"Counter-trend **raises** confluence requirement"* — which
makes 2 the base and 3 the exception — and because selecting a reading by how close it lands to a
published count is fitting, not reading. Recorded here so the adjudicator can overrule it on the
evidence rather than discover it. It is switchable: `OPT["range_conf"] = 3`.

## Deliberate non-implementations (all justified in AMBIGUITIES.md)

* **T_cancel** (§5.5) — CALIBRATE with *no* start value, so the cancel rule is disabled rather
  than invented, following A2's precedent. Cost: 120 trades (7.6%) fill more than 30 minutes
  after their signal. Any T_cancel removes some of them.
* **Location gate** — A9 demotes it to a recorded covariate; not applied, and TASK.md's schema
  carries no column for it.
* **Volatility stand-down** — A2: DISABLED for v1.
* **§6 rule 2 pattern defaults, rule 3 news override, rule 6 alignment bonus** — A4 records rule 2
  as open, A13 records that no economic calendar exists, and rule 6 is a "prefer" with no rule.
* **§10.2 daily halt (2 losses / −2R)** — cannot be evaluated without computing outcomes, which
  TASK.md forbids. Not applied.
* **§8 management, §9 sizing, A11's `entry_tf_1m` boolean** — no output column; `entry_tf` already
  records which trades are 1m (803 of 1,583, i.e. 50.7%, so A11's hole is live here).

## No outcome was computed

No P&L, no win/loss, no R multiple, no exit reason appears anywhere in the code or the output.
`simulate_exit()` exists solely to decide when the §5.6 / §10.1(2) one-position lock releases, and
its return value is an index — nothing else is derived from it.

## Sealed-data handling

`process_session()` opens with `assert date <= "2025-01-31"`. The date list is filtered before any
session is touched. Sessions before the seal date are additionally read to supply prior-day and
prior-week highs and lows for the §6 target menu; nothing after 2025-01-31 is read at any point.

## Files

* `blind_impl.py` — the implementation (the `OPT` dict at the top holds the switchable forks)
* `blind_trades.json` — 1,583 trades
* `sensitivity.py` — the fork sweep above
* `AMBIGUITIES.md` — 28 entries
* `READ_MANIFEST.md`
