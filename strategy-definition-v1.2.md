# NQ VWAP/BB/Profile Strategy — Definition v1.2

**Status:** LOCKED. v1.2 amendments instated by Angus (17 Jul 2026, from the Step-8 February calibration review); supersedes v1.1. Full-doc final read-through still owed by Angus (open item in `context/questions-for-angus.md`).

**Changes v1.1 → v1.2** (Angus rulings on the Step-8 calibration report — the first pass of the Phase-2 loop: engine reported divergences, Angus disposed; recorded in `context/progress-tracker.md`):
1. **Confluence minimum 3 → 2 everywhere** (§7): the two types must be **BB + VWAP together**; POC is bonus confluence, never a requirement. The v1.1 "counter-trend demands 3-type alignment" rule is DELETED — it was the nearest gate on 13 of the 24 MISSED February trades, and the diagnostics showed 2-confluence trades outperforming 3-confluence (+0.49 vs −0.21 avg R). Resolves P5.15 as SUPERSEDE.
2. **Full size is the default — counter-trend reversals included** (§9): Angus: "I wasn't doing 50%" in the hand backtest; the v1.1 confluence/type-count sizing tiers and the with-trend-or-A-at-extension conviction test are DELETED. Half size survives ONLY on the two deliberate overrides: oversized stop (>42) and late-window fill (>10:30, session-scoped windows). Reverses the v1.1 counter-trend-half reading (P5.10) at Angus's direction.
3. **Minimum stop NEW** (§5.4): structural stop narrower than **10 pts** → NO TRADE (skip, never widen). Kills the 1–4-pt coin-toss stops behind most February EXTRA losses; Angus's real stops run 10–20 pts.
4. Deliberately NOT changed this pass (one-problem-at-a-time): T_cancel, news/PCE classification (P5.14 still open — rerun "with the news variable after"), halt, RR floor, entry/management variants.
**Source of truth:** 28 hand-backtested trades (Feb 2–27 2026, NQ, NY morning) + journals + charts + Q&A.
**Purpose:** Section 0 context for every spec in the build. Nothing is implemented that isn't written here. Items marked CALIBRATE are numeric parameters the February re-run tunes; items marked TOURNAMENT are rule variants tested head-to-head.

**Changes v1.0 → v1.1** (all sourced from Angus, 17 Jul 2026 — recorded in `context/progress-tracker.md` decision log; these were his operating rules that v1.0 had left blank or under-specified):
1. Session box clock times confirmed (§2): Asia 18:00–03:00, London 03:00–09:30, NY 09:30–16:00 ET.
2. **VWAP warm-up** (§7, NEW): no entries in the first hour after the 18:00 ET daily-VWAP anchor.
3. **T_cancel** start value set (§5.5): 20–25 pts, start 22 (was unset; the 15-pt engineering placeholder was too tight).
4. **RR floor hardened** (§6.5): 2.0R minimum on every trade (was 1.5 CALIBRATE); "thin target → half size" removed from §9 — below 2R is a skip, not a downsize.
5. **Confluence/sizing ladder made type-specific** (§7/§9): FULL-eligible = BB + VWAP + POC aligned (full still additionally requires with-trend OR A-at-extension — §9); HALF = exactly two types and they must include BB + VWAP; BB + VWAP not both present → no trade.
6. **Oversized stop defined** (§9): > 40–45 pts (start 42) → half unit.
7. **Late-window defined** (§9): entries after 10:30 ET → half unit, when testing session-scoped windows (W1 etc.; W2 treatment open — §9).
8. **High-impact pre-open news stand-down** (§7, NEW): a high-impact release scheduled before 09:30 kills all pre-market entries that day; first entries from the 09:30 open.
9. Volume-profile value area confirmed 70% (§2).
10. Post-audit clarifications (same date, adversarial-review findings): §9 default-&-precedence rule (fails-full → half; half triggers demote; no stacking) — the counter-trend-non-A = half completion CONFIRMED by Angus same day; §6.5 reworded from "nearest valid target" to "selected target"; §7 news bullet's "not blackout" reconciled with the new stand-down; §9 oversized-stop wording covers displacement-origin stops. Still-open items routed to `context/questions-for-angus.md`: W2 span + late-window-in-W2, entry-timestamp semantics, R measurement vs front-run.

---

## 1. Instrument, Session, Timeframes

- **Instrument:** NQ (CME), sized via MNQ where risk requires.
- **Entry window:** CONFIG, tested as variants — **W1:** 08:00–11:00 ET, pre-market through pre-lunch (primary; matches full sample incl. 8:06 and 10:52 winners; Angus-confirmed intent; entries after 10:30 → half unit, §9); **W2:** full trading day with Vault risk parameters unchanged (Angus priority test #2 — where does the edge live across the day?; working read: full CME session 18:00 → 15:55 flatten per the config placeholder, under which the §7 VWAP warm-up trims its start to 19:00 — span confirm OPEN, Angus); **W3:** other sessions (London etc.) — Hypothesis H3, after v1 validates. Backtest declares the winner. [TOURNAMENT]
- **End-of-day flatten:** VAULT RULE, not strategy: any open position is flattened before the CME close per the eventual firm's rules (default 15:55 ET). Exists as a backstop; expected to almost never fire (median trade resolves ~30 min).
- **Entry TFs:** 1m, 2m, 3m, 5m. **MTF arbitration:** evaluate all four; if multiple TFs show valid triggers simultaneously, take the highest TF. [CONFIRMED — Angus]
- **Context TFs:** 15m for HTF trend/range flag; 1h/4h for range extremes.

## 2. Indicator Stack (computable only)

| Indicator | Parameters | Role |
|---|---|---|
| Bollinger Bands | 20, SMA, close, 2σ | Basis ("BB MA") = core cluster level |
| NY session VWAP | **Anchored 09:30 ET cash open** — does NOT exist pre-market. ±1σ/±2σ/±3σ | Cluster levels, extension detector, targets |
| Daily VWAP | **CORE — "one of the most important components" (Angus).** Full band set ±1σ/±2σ/±3σ. Anchor: CONFIRMED — standard TradingView VWAP, resets at CME daily session open, 18:00 ET / Asia open | Core cluster level at all times; the ONLY VWAP pre-9:30 |
| Volume profile | Session + daily; **weekly anchor added as tested variant (Angus)**. POC, VAH/VAL (value area **70%** — CONFIRMED, standard session VP), HVN/LVN | POC = core cluster level; profile feeds targets |
| Session boxes | **Asia 18:00–03:00, London 03:00–09:30, NY 09:30–16:00 ET** [CONFIRMED — Angus]. NY pre-market (~08:00–09:30) sits in the London box by convention — Angus: "either/or" (late London vs NY pre-market) | Session extremes for targets/liquidity |
| Data levels | Extremes printed within N min of scheduled releases | Bias + targets. N: CALIBRATE (start 15 min) |

**EXCLUDED: MIG LiquidityEdge.** Closed-source, mutable, replay-inaccurate. MIG targets in journals re-map to nearest computable structural level. A native absorption/exhaustion zone detector is a possible future module, validated separately.

## 3. Core Definitions

- **Confluence cluster:** ≥2 of {BB MA, NY VWAP middle/±1σ (post-9:30 only), daily VWAP middle/±1σ/±2σ/±3σ, daily POC} within proximity tolerance. Pre-9:30, the VWAP family = daily VWAP only. Tolerance: CALIBRATE (start ~10 NQ pts / 0.04%).
- **Confluence count:** distinct level *types* touched (VWAP family ×1, BB ×1, POC ×1, structural ×1). **v1.1:** the entry/sizing ladder (§7/§9) counts only the three CORE types — BB, VWAP family, POC; structural confluence is target/context weight, not entry-minimum credit.
- **Rejection block:** entry-TF candle that (a) trades into the cluster, (b) CLOSES back on the trade side of all cluster levels, (c) leaves a wick through/into them. **Tradeable zone = the wick: from body edge to wick extreme.** [CONFIRMED — Angus]
- **Displacement (numerical, per Angus "compelling close" requirement):** entry-TF candle whose **body closes through ≥2 cluster levels**, with **body/range ≥ B_min** and **close within the extreme quartile of the candle's range** (top 25% for longs, bottom 25% for shorts — kills the "barely breaks through with a top wick" case). B_min: CALIBRATE (start 0.6). Optional size floor range ≥ k×ATR(20): CALIBRATE (start k=1.0).
- **Over-extension:** touch of NY VWAP ±2σ (extreme ±3σ).

## 4. Pattern Taxonomy (mechanism-based; HTF alignment is a separate flag)

- **A — Reversal:** over-extension and/or HTF range extreme → rejection block against prior move → retest entry.
- **B — Reclaim:** price on wrong side of cluster → displacement back through → retest of reclaimed cluster.
- **B2 — Continuation:** established move → pullback to cluster → rejection block with the move → retest entry.
- **HTF flag:** with_trend / counter_trend / range, tagged per trade. Counter-trend raises confluence requirement (§7).

## 5. Entry Rules

1. Detect cluster on each entry TF.
2. Trigger = rejection block (A, B2) or displacement (B). Candle must CLOSE to confirm.
3. **Limit price — TOURNAMENT (replaces "what makes the most sense"):**
   - **E1:** limit at the BB MA (most frequent in journals)
   - **E2:** limit at the 50% level of the trigger candle's wick
   - **E3:** limit at the penetrated cluster level nearest the block's close
4. Stop: beyond the wick extreme of the trigger candle / displacement origin. Structural, never widened (Vault-enforced). **Minimum stop [NEW — Angus, v1.2]: if the structural stop is narrower than 10 pts, SKIP the trade** — never widen to fit ("on NQ we need breathing room"; real stops run 10–20 pts; sub-5-pt wick-stops are coin tosses). CALIBRATE within 10–15 only.
5. No fill → no chase. Order cancels if price runs T_cancel points beyond entry without filling. **T_cancel: 20–25 pts, start 22** [CONFIRMED — Angus, v1.1]. Rationale: a missed limit that runs and later returns to the entry usually fails — price rarely re-chases (same behaviour motivating V1 BE-at-1R, §8) — so the cancel must be loose enough not to kill normal fills, then final. CALIBRATE within the 20–25 band only.
6. One position at a time. No overlapping trades ever. [CONFIRMED — Angus]

## 6. Targets

**Menu:** VWAP middle; VWAP ±1σ/±2σ; POC; session extremes (Asia/London/pre-market); data extremes; prior-day H/L; weekly H/L; pullback origin (B2); HTF range extremes.

**Selection tree v1:**
1. List opposing structural levels beyond entry, by distance.
2. Defaults: **A** → VWAP middle; **B2** → next structural level in move direction; **B** → opposing liquidity (pre-market/prior-day extreme), preferring ±2σ alignment.
3. **News-day override [CONFIRMED — Angus]:** on high-impact data days, data extremes have elevated sweep probability. If trade direction points at an untaken data extreme beyond the default target, target the data extreme instead. (Fallback variant to test: VWAP −1/+1 as the simpler proxy.)
4. **Fill front-run [CONFIRMED — Angus]:** working target = level ∓ F points (level minus F for longs). F: CALIBRATE (start 2–3 NQ pts). Backtest counts target *touched-minus-F* as filled, mirroring live behavior.
5. **RR floor:** the **selected target** (steps 1–4) must offer ≥ **2.0R**; if the tree cannot produce one, skip [CONFIRMED — Angus, v1.1: "still target minimum 2R", hard rule on every trade — a bigger stop must be justified by a proportionally bigger target]. Not a calibration knob. Replaces v1.0's 1.5 CALIBRATE ("nearest valid target" wording dropped — the check applies to the target actually chosen, since the tree deliberately picks non-nearest levels); the old "thin target → half size" (§9) is subsumed — below 2R is a no-trade, not a downsize. [RESOLVED — Angus, 17 Jul 2026: R is measured to the **actual level** — stop 40 pts ⇒ the target level must sit ≥ 80 pts away, and the target must BE a real menu level (§6.1), not an arbitrary 2R price. The front-run F (§6.4) is execution mechanics only and does not enter the R calculation; the backtest still fills at touched-minus-F.]
6. Alignment bonus: prefer targets where ≥2 menu levels stack within tolerance.

## 7. Filters & Skip Criteria

- **Confluence minimum (v1.2 — Angus calibration ruling, 17 Jul 2026):** entry requires **BB MA + VWAP both present** in the cluster — that is the whole gate, for every trade, counter-trend included. Two types not including both = NO TRADE. POC (or anything else) stacking on top = bonus confluence, never a requirement. *(v1.1's "counter-trend demands 3-type alignment" is deleted — it vetoed 13 of Angus's 24 February trades while the 2-confluence trades were the profitable ones; P5.15 ruled SUPERSEDE.)*
- **VWAP warm-up [NEW — Angus, v1.1]:** no entries in the **first hour after the daily-VWAP anchor** (18:00 ET → no entries before 19:00 ET) — the VWAP needs time to form before it means anything. Bites the Asia/overnight (daily-model) variants; W1/NY unaffected.
- Location: no longs at HTF range top / shorts at range bottom.
- Invalidation-at-entry: trigger candle simultaneously touching the opposing ±1σ → stand down. [Hypothesis — test]
- Volatility stand-down: computable definition TBD (opening range vs ATR). [OPEN]
- News handling: data is bias/target input, not a blackout — with ONE v1.1 exception below; slippage modeled punitively near releases. "No entry within N min of release" = H4, test. **High-impact pre-open stand-down [NEW — Angus, v1.1]:** a HIGH-impact release scheduled before 09:30 ET (e.g. CPI 08:30) kills ALL pre-market entries that day — **including entries before the release itself** [CONFIRMED — Angus, 17 Jul: "pre-release entries aren't good"]; first entries from the 09:30 open.
- **"High-impact" defined [CONFIRMED — Angus, 17 Jul]:** Forex Factory **red-folder** releases — the prints that cause giant 1-minute candles: CPI, PPI, Non-Farm Employment/payrolls family, JOLTS, and peers of that magnitude. Orange/medium releases do NOT trigger the stand-down or the §6.3 news-day override ("if it's not that, I don't care about it"). The news_calendar `impact=high` tag must mean exactly this; Feb 2026 rows were seeded best-effort from the hand log and need re-verification against Forex Factory red-folder status [ACTION — Brake]. Edge case pending Angus (see questions-for-angus P5.14): PCE is red-folder on FF but not on Angus's named list — Feb 20 (Core PCE 08:30) decides whether his own 08:06 hand trade survives the rule.

## 8. Trade Management — TOURNAMENT (split-test, per Angus)

- **V0:** none — set-and-forget (baseline)
- **V1:** BE at +1R. **Definition: TOUCH of +1R (any TF tick), stop to entry exact.** [CONFIRMED — Angus]
- **V2:** BE at first VWAP band milestone touch
- **V3:** BE at 09:30 open if entered pre-open
- **V4:** 50% partial at first structural level, runner to target
Each variant runs over identical data; Monte Carlo compares distributions; winner (or V0) goes live.
**Priority head-to-head (Angus test #1): V1 (BE at +1R touch) vs V0 (none), over the full Jan–Jul period, before the wider tournament.**

## 9. Sizing & Conviction

*(v1.2 — Angus calibration ruling, 17 Jul 2026. The v1.1 confluence/type-count sizing tiers and the with-trend-or-A-at-extension conviction test are DELETED: "I wasn't doing 50%… trade counter-trend reversals at full size." History of the superseded v1.1 ladder is in git and the v1.2 changelog.)*

- **Full unit is the default for every entry that passes §7** — counter-trend reversals included. There is no confluence-based or trend-based size reduction.
- **Half unit** only on the two deliberate overrides (either present → half; they do not stack below half):
  - **oversized stop: > 40–45 pts, start 42** [CONFIRMED — Angus, v1.1]. The stop sits at the trigger wick extreme / displacement origin (§5.4), so stop size tracks trigger size; Feb sample median ≈ 30 pts, so 40–45 = "block too big, de-risk". CALIBRATE within the band only. (Floor at the other end: stops < 10 pts are a no-trade — §5.4 v1.2.)
  - **late-window entry: after 10:30 ET** [CONFIRMED — Angus, v1.1], applying ONLY to session-scoped (NY-only) test windows such as W1. [RESOLVED — Angus: **W2 full-day testing has NO time-based half-sizing.**] Context: 09:45–10:15 is peak AM-macro; post-10:30 setups are lower conviction.
- Absolute per-trade risk ceiling comes from Monte Carlo vs eval rules — expected well below the sample's $400.

## 10. Vault (deterministic, no LLM access)

- Max trades/day: **3** (config 2–3; Angus: "no more than 2–3 genuinely high-probability setups exist per day").
- Daily halt: after **2 losses** or **−2R** on the day, whichever first (placeholder; MC calibrates).
- One position at a time; no stop widening; EOD flatten (§1); drawdown kill-switch vs trailing DD buffer; size ceiling from MC.
- All verdicts (taken/skipped/vetoed) logged to strict-schema journal. Nightly stats refresh; weekly Edge-Lab-style review is generated as PROPOSALS ONLY — rule changes require out-of-sample evidence + Angus sign-off + doc version bump. The system never edits its own rules. [CONFIRMED — Angus]

## 11. Architecture Boundary

Agents grade against this doc and propose. Python owns sizing, stops, limits, kill-switch, execution. Telegram alerts fire from the Vault only (post-risk-check), via bot API; inbound /status /pause /flatten commands locked to Angus's chat ID (later phase).

## 12. Data & Validation Plan

1. **Data:** 1-minute NQ, Jan 2026 → present, via Databento (or equivalent cheapest clean source). 2025 pulled later as a regime-robustness check only — not pass/fail. [Angus regime rationale noted; robustness check is the honesty guard.]
2. **Calibration:** February 2026 re-run must approximately reproduce the 28 hand trades; divergences audited one by one (incl. MIG-target remaps). Days Angus skipped: system trades them only if valid triggers exist — gap analysis measures day-selection honestly.
3. **Tournaments:** windows W1/W2 × entries E1–E3 × management V0–V4 — run as separate axes, not a combinatorial free-for-all; one axis fixed at a time to avoid overfitting via grid search. (v1.1 note, resolved by Angus 17 Jul: the late-window half-sizing (§9) exists only in session-scoped windows — W2 has no time-based sizing BY DESIGN, so the W1-vs-W2 arms intentionally differ in sizing as well as window; read that axis knowing both differences are deliberate.)
4. **Out-of-sample:** Mar–Jul 2026 untouched until rules lock.
5. **Diagnostics:** per-slice expectancy (pattern × TF × confluence count × HTF flag × time bucket × news flag) so leaks are locatable.
6. **Monte Carlo:** winning config's distribution vs 50K eval (3K target / 2K trailing DD): pass probability, expected attempts/cost, days-to-pass, first-month blowup risk → sizing config → firm selection.
7. Live paper via TradingView; agents grade real-time; human executes.
