# RESUME HERE — exactly where we are (20 Jul 2026, mid-session usage cap)

Angus's account hit the usage cap mid-analysis. This is the precise pick-up point. Read this, then
continue from "IN FLIGHT" below. **Do NOT restart from scratch and do NOT contrast to the champion**
— the champion is the floor we've moved past. We build from the **chained agent + regime read**.

## The north star (Angus, hardened this session)
**CONSISTENCY — green EVERY month — is the objective function, not total P&L.** A shape carried by
one big month (Feb) is fragile and wrong. Grade every change on months-green + drawdown; reject
anything that turns a green month red even if the total goes up. The core gap is **knowing when NOT
to trade** (and its flip side: not trading when it should). Entry mechanism is NOT the problem.

## The base we build FROM (stop re-deriving these)
- **Chained agent stack (v0.7)**: 2026 = **+$14,465, 5/6 months green, $2.7k max DD** (30% of the
  ~$45-49k SD-oracle). Ledger: `output/v07/chained2026/ledger.csv` (per-day stance/book/pl).
- **SD-oracle** (better book/day or flat) = the benchmark: ~$45k 2026 (6mo), ~$70k/yr 2023-25.
  Built by scratchpad `standdown_all.py`; the ledger HTML = scratchpad `full_history_ledger.html`.
- E-2 fix = correct but INERT (0/5432 relabels). Tier-2 (cash-open cut + 10pt post-open stop) = real
  but modest. Both shipped in config. Don't re-litigate.

## What we PROVED this session (the levers on "when not to trade")
1. **Regime-gated post-open confluence is ADDITIVE to the agent.** The confluence-rejection detector
   (`scripts/cdr_v2.py`), gated by the regime read (**|inventory_pts| <= 20 = rotation days**),
   overlaid on the chained agent → **+$3,306 (+23%), 5/6 green KEPT** (Feb/May added, Mar/Jun stood
   down = no bleed). Ungated it overtrades and is inconsistent — the regime gate is the whole point.
   Fades WIN on rotation days (moderate inventory, 75% win) and DIE on freight-train days (30+ inv,
   16% win). `docs` finding pending; overlay math in this session's transcript.
2. **Don't-trade filter** (`docs/FINDING-dont-trade-filter.md`): cut below-value opens + require CVD
   absorption (cvd<=0) → **132t→78t, +$14,351 (kept the money), 33%→41% win, 5/6 green.** The losers'
   #1 shared signature = **hollow rejections** (no CVD absorption). This is THE leak.
3. **Day-of-week**: Monday is the agent's standout (6/7 months positive) — consistency-worthy sizing
   lever, NOT the Feb-carried total.
4. **July's red is a 4-trade half-month artifact on OLD criteria** — 46 triggers/day exist (same as
   May/Jun), bot took only 4 (2 were junk: 0.5pt & 4pt stops), one bad day (Jul 3) = red stub. NOT a
   leak. It needs a clean re-run under the NEW rules (see task).

## Sign convention (locked, verified)
CVD footprint: **side 'B' = aggressive BUY, 'A' = aggressive SELL** (scratchpad/sign_test.py). `cvd`
is oriented so **negative = flow AGAINST the trade = real absorption** (good). Winners cvd ≈ −74,
losers ≈ −10.

## IN FLIGHT — resume EXACTLY here
**Testing Angus's heatmap-magnet + CVD finding.** Angus: *"a heatmap magnet PLUS CVD — when a trade
had both, we had ~60% win in April, trade frequency down a lot but P&L up a lot."* The give-back/EXIT
use of heatmap tested as noise earlier (`test_cvd_heatmap_givebacks.py`); this is the **ENTRY**
conviction use — a big resting-liquidity wall at the entry level + CVD absorption.

Script is **written and ready**: `scripts/heatmap_magnet_cvd.py` (magnet = size>=15 on the reject
side within 6pt of entry; absorb = cvd<=0; on April champion trades using Brake's `depth_apr2026`).
It was RUNNING when the usage cap hit — the run was cut off by an infra hiccup, NOT a code error.

**FIRST ACTION on resume:** `python -m scripts.heatmap_magnet_cvd` — confirm MAGNET+CVD ≈ 60% win /
fewer trades / higher P&L in April. If it holds, magnet+CVD is a top-tier conviction filter (but
depth is APRIL-ONLY until Brake pulls more — see Brake task).

## TASK LIST (assigned to Angus / next session — mirrored as GitHub issues)
1. **Run `scripts/heatmap_magnet_cvd.py`** — confirm the 60%-April magnet+CVD result. (in-flight)
2. **Clean July re-run** under the FULL current ruleset (E-2 triggers + regime gate + don't-trade
   filter (hollow-CVD + below-value) + confluence). The old July red is stale/4-trade. Angus to send
   specific July setups the bot SHOULD have taken (finds which gate over-restricts).
3. **Fold the gates into the agent's daily read** — regime gate (|inv|<=20) + hollow-CVD + below-value
   + (if it holds) heatmap-magnet — as the "when not to trade" layer, graded on months-green from the
   chained base. This is the "apply the regime context to the fullest extent" work.
4. **Brake**: pull depth/heatmap for Feb, Mar, May, Jun, Jul (only April exists) so magnet+CVD can be
   tested full-year, not just April.

## Key files
- agent ledger `output/v07/chained2026/ledger.csv` · regime `output/regime_vector.csv`
- detectors/tests: `scripts/cdr_v2.py` (confluence-rejection), `scripts/heatmap_magnet_cvd.py`,
  `scripts/postopen_e6.py` (E4+V8+geometry), `scripts/champion_journal_cvd.py`
- journals (scratchpad): `champ_journal_cvd.csv` (per-trade + CVD), `cdr_v2_trades.csv`
- findings: `docs/FINDING-dont-trade-filter.md`, `docs/FINDING-oracle-is-hindsight...md`,
  `docs/SPEC-cash-open-confluence-setup.md` (Angus's 11-trade A+ spec, v2 model)
- depth: `data/reference/depth_apr2026/*_ny.csv` (April only)
