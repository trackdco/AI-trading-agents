# NQ VWAP/BB/Profile Strategy — Definition v1.1

**Status:** LOCKED. v1.1 amendments instated by Angus (17 Jul 2026); supersedes v1.0. Full-doc final read-through still owed by Angus (open item in `context/questions-for-angus.md`).
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
4. Stop: beyond the wick extreme of the trigger candle / displacement origin. Structural, never widened (Vault-enforced).
5. No fill → no chase. Order cancels if price runs T_cancel points beyond entry without filling. **T_cancel: 20–25 pts, start 22** [CONFIRMED — Angus, v1.1]. Rationale: a missed limit that runs and later returns to the entry usually fails — price rarely re-chases (same behaviour motivating V1 BE-at-1R, §8) — so the cancel must be loose enough not to kill normal fills, then final. CALIBRATE within the 20–25 band only.
6. One position at a time. No overlapping trades ever. [CONFIRMED — Angus]

## 6. Targets

**Menu:** VWAP middle; VWAP ±1σ/±2σ; POC; session extremes (Asia/London/pre-market); data extremes; prior-day H/L; weekly H/L; pullback origin (B2); HTF range extremes.

**Selection tree v1:**
1. List opposing structural levels beyond entry, by distance.
2. Defaults: **A** → VWAP middle; **B2** → next structural level in move direction; **B** → opposing liquidity (pre-market/prior-day extreme), preferring ±2σ alignment.
3. **News-day override [CONFIRMED — Angus]:** on high-impact data days, data extremes have elevated sweep probability. If trade direction points at an untaken data extreme beyond the default target, target the data extreme instead. (Fallback variant to test: VWAP −1/+1 as the simpler proxy.)
4. **Fill front-run [CONFIRMED — Angus]:** working target = level ∓ F points (level minus F for longs). F: CALIBRATE (start 2–3 NQ pts). Backtest counts target *touched-minus-F* as filled, mirroring live behavior.
5. **RR floor:** the **selected target** (steps 1–4) must offer ≥ **2.0R**; if the tree cannot produce one, skip [CONFIRMED — Angus, v1.1: "still target minimum 2R", hard rule on every trade — a bigger stop must be justified by a proportionally bigger target]. Not a calibration knob. Replaces v1.0's 1.5 CALIBRATE ("nearest valid target" wording dropped — the check applies to the target actually chosen, since the tree deliberately picks non-nearest levels); the old "thin target → half size" (§9) is subsumed — below 2R is a no-trade, not a downsize. [Measure R to the raw level or the front-run working target (§6.4)? OPEN — Angus/Brake; backtest fills at touched-minus-F.]
6. Alignment bonus: prefer targets where ≥2 menu levels stack within tolerance.

## 7. Filters & Skip Criteria

- **Confluence minimum (v1.1, type-specific):** entry requires **BB MA + VWAP both present** in the cluster — two types that don't include both = NO TRADE. Exactly two types (BB + VWAP) = tradeable at half unit (§9). All three core types (BB + VWAP + POC) = full-unit eligible (§9). Trend overlay unchanged from v1.0: counter-trend demands the full 3-type alignment; with-trend may trade the 2-type (BB+VWAP) case at reduced risk.
- **VWAP warm-up [NEW — Angus, v1.1]:** no entries in the **first hour after the daily-VWAP anchor** (18:00 ET → no entries before 19:00 ET) — the VWAP needs time to form before it means anything. Bites the Asia/overnight (daily-model) variants; W1/NY unaffected.
- Location: no longs at HTF range top / shorts at range bottom.
- Invalidation-at-entry: trigger candle simultaneously touching the opposing ±1σ → stand down. [Hypothesis — test]
- Volatility stand-down: computable definition TBD (opening range vs ATR). [OPEN]
- News handling: data is bias/target input, not a blackout — with ONE v1.1 exception below; slippage modeled punitively near releases. "No entry within N min of release" = H4, test. **High-impact pre-open stand-down [NEW — Angus, v1.1]:** a HIGH-impact release scheduled before 09:30 ET (e.g. CPI 08:30) kills all pre-market entries that day — let price play out post-news; first entries from the 09:30 open.

## 8. Trade Management — TOURNAMENT (split-test, per Angus)

- **V0:** none — set-and-forget (baseline)
- **V1:** BE at +1R. **Definition: TOUCH of +1R (any TF tick), stop to entry exact.** [CONFIRMED — Angus]
- **V2:** BE at first VWAP band milestone touch
- **V3:** BE at 09:30 open if entered pre-open
- **V4:** 50% partial at first structural level, runner to target
Each variant runs over identical data; Monte Carlo compares distributions; winner (or V0) goes live.
**Priority head-to-head (Angus test #1): V1 (BE at +1R touch) vs V0 (none), over the full Jan–Jul period, before the wider tournament.**

## 9. Sizing & Conviction

- **Full unit** requires **all three core types aligned — BB + VWAP + POC** (§7) AND (with-trend OR A-at-extension) AND target ≥ 2R (automatic in v1.1 — §6.5 makes 2R the floor on every trade).
- **Half unit** on any of:
  - exactly **two** confluence types (which must include BB + VWAP — §7; anything less is a no-trade; §7's trend gate applies FIRST, so the 2-type case is with-trend only — counter-trend already requires all three types to enter at all);
  - **oversized stop: > 40–45 pts, start 42** [CONFIRMED — Angus, v1.1]. The stop sits at the trigger wick extreme / displacement origin (§5.4), so stop size tracks trigger size; Feb sample median ≈ 30 pts, so 40–45 = "block too big, de-risk". CALIBRATE within the band only;
  - **late-window entry: after 10:30 ET** [CONFIRMED — Angus, v1.1] when testing session-scoped windows (W1 etc.; W2 full-day treatment: OPEN — Angus). Context: 09:45–10:15 is peak AM-macro (most volatile/probable); post-10:30 setups are lower conviction. (v1.0's "thin target" trigger is removed — §6.5.)
- **Default & precedence (v1.1 clarification of v1.0's two-bucket intent):** §7 gates entry first; among trades that enter, only two sizes exist. A trade that fails ANY full-unit condition trades at **half** — half is the default, not an exception list (this covers the 3-type counter-trend trade that is not A-at-extension: it enters per §7, sized half). Any half-unit trigger present demotes an otherwise-full trade to half; multiple triggers do not stack below half. [CONFIRMED — Angus, 17 Jul 2026: counter-trend-non-A with full 3-type alignment = half.]
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
3. **Tournaments:** windows W1/W2 × entries E1–E3 × management V0–V4 — run as separate axes, not a combinatorial free-for-all; one axis fixed at a time to avoid overfitting via grid search. (v1.1 note: the late-window half-sizing (§9) is scoped to session windows, so the W1-vs-W2 arms may differ in sizing as well as window — read that axis accordingly, or resolve the W2-treatment OPEN item first.)
4. **Out-of-sample:** Mar–Jul 2026 untouched until rules lock.
5. **Diagnostics:** per-slice expectancy (pattern × TF × confluence count × HTF flag × time bucket × news flag) so leaks are locatable.
6. **Monte Carlo:** winning config's distribution vs 50K eval (3K target / 2K trailing DD): pass probability, expected attempts/cost, days-to-pass, first-month blowup risk → sizing config → firm selection.
7. Live paper via TradingView; agents grade real-time; human executes.
