# NQ VWAP/BB/Profile Strategy — Definition v1.1

**Status:** LOCKED pending final Angus read-through. Changes from v0.1 sourced from Angus Q&A (17 Jul 2026).
**v1.1 (supersedes v1.0 §4):** the pattern taxonomy is replaced per the **ANGUS 22-Jul-2026
ruling**, documented at `docs/STRATEGY-SETUP-TAXONOMY.md` (which calls itself authoritative
and states "any earlier 'rejection=A, displacement=B' shape-based description is WRONG and
superseded") and implemented in `src/engine/triggers.py`. v1.0's §4 was candle-shape-based;
the ruling makes it context-based. **"Reclaim" is retired as a pattern name.** The ruling
landed five days after v1.0 was locked and this document was never version-bumped — that
gap is what let the code and the constitution disagree for two weeks.
**Source of truth:** 28 hand-backtested trades (Feb 2–27 2026, NQ, NY morning) + journals + charts + Q&A.
**Purpose:** Section 0 context for every spec in the build. Nothing is implemented that isn't written here. Items marked CALIBRATE are numeric parameters the February re-run tunes; items marked TOURNAMENT are rule variants tested head-to-head.

---

## 1. Instrument, Session, Timeframes

- **Instrument:** NQ (CME), sized via MNQ where risk requires.
- **Entry window:** CONFIG, tested as variants — **W1:** 08:00–11:00 ET, pre-market through pre-lunch (primary; matches full sample incl. 8:06 and 10:52 winners; Angus-confirmed intent); **W2:** full trading day with Vault risk parameters unchanged (Angus priority test #2 — where does the edge live across the day?); **W3:** other sessions (London etc.) — Hypothesis H3, after v1 validates. Backtest declares the winner. [TOURNAMENT]
- **End-of-day flatten:** VAULT RULE, not strategy: any open position is flattened before the CME close per the eventual firm's rules (default 15:55 ET). Exists as a backstop; expected to almost never fire (median trade resolves ~30 min).
- **Entry TFs:** 1m, 2m, 3m, 5m. **MTF arbitration:** evaluate all four; if multiple TFs show valid triggers simultaneously, take the highest TF. [CONFIRMED — Angus]
- **Context TFs:** 15m for HTF trend/range flag; 1h/4h for range extremes.

## 2. Indicator Stack (computable only)

| Indicator | Parameters | Role |
|---|---|---|
| Bollinger Bands | 20, SMA, close, 2σ | Basis ("BB MA") = core cluster level |
| NY session VWAP | **Anchored 09:30 ET cash open** — does NOT exist pre-market. ±1σ/±2σ/±3σ | Cluster levels, extension detector, targets |
| Daily VWAP | **CORE — "one of the most important components" (Angus).** Full band set ±1σ/±2σ/±3σ. Anchor: CONFIRMED — standard TradingView VWAP, resets at CME daily session open, 18:00 ET / Asia open | Core cluster level at all times; the ONLY VWAP pre-9:30 |
| Volume profile | Session + daily; **weekly anchor added as tested variant (Angus)**. POC, VAH/VAL, HVN/LVN | POC = core cluster level; profile feeds targets |
| Session boxes | Asia / London / NY | Session extremes for targets/liquidity |
| Data levels | Extremes printed within N min of scheduled releases | Bias + targets. N: CALIBRATE (start 15 min) |

**EXCLUDED: MIG LiquidityEdge.** Closed-source, mutable, replay-inaccurate. MIG targets in journals re-map to nearest computable structural level. A native absorption/exhaustion zone detector is a possible future module, validated separately.

## 3. Core Definitions

- **Confluence cluster:** ≥2 of {BB MA, NY VWAP middle/±1σ (post-9:30 only), daily VWAP middle/±1σ/±2σ/±3σ, daily POC} within proximity tolerance. Pre-9:30, the VWAP family = daily VWAP only. Tolerance: CALIBRATE (start ~10 NQ pts / 0.04%).
- **Confluence count:** distinct level *types* touched (VWAP family ×1, BB ×1, POC ×1, structural ×1).
- **Rejection block:** entry-TF candle that (a) trades into the cluster, (b) CLOSES back on the trade side of all cluster levels, (c) leaves a wick through/into them. **Tradeable zone = the wick: from body edge to wick extreme.** [CONFIRMED — Angus]
- **Displacement (numerical, per Angus "compelling close" requirement):** entry-TF candle whose **body closes through ≥2 cluster levels**, with **body/range ≥ B_min** and **close within the extreme quartile of the candle's range** (top 25% for longs, bottom 25% for shorts — kills the "barely breaks through with a top wick" case). B_min: CALIBRATE (start 0.6). Optional size floor range ≥ k×ATR(20): CALIBRATE (start k=1.0).
- **Over-extension:** touch of NY VWAP ±2σ (extreme ±3σ).

## 4. Pattern Taxonomy (mechanism-based; HTF alignment is a separate flag)

*Context-based, not candle-shape-based. Source: ANGUS 22-Jul-2026, `docs/STRATEGY-SETUP-TAXONOMY.md`.
All three share one entry mechanism — a limit at the retest of the closest structural level
(POC / daily-VWAP ±1/±2 band / BB MA). They differ only in the context of the move before it.*

- **A — Reversal (counter-trend):** a candle **closes through** the cluster, reversing a real
  ±2 daily-VWAP over-extension (the prior `_EXT_LOOKBACK` entry-TF bars must have touched the
  ±2 band) → retest entry. Fades the extension.
- **B — Continuation (with-trend):** a **close-through** with no qualifying prior ±2 extension,
  off a stacked confluence → retest entry. Rides the prevailing trend.
- **B2 — Rejection / fade:** price **wicks into** the level and **closes back** → fade off the
  level at the retest, stop beyond the rejection wick. Works with- or counter-HTF.
- **Retired: "Reclaim."** Not a pattern. The term survives only as the **E3 entry-reference
  level** (§5.3), which is unaffected.
- **HTF flag:** with_trend / counter_trend / range, tagged per trade. Counter-trend raises confluence requirement (§8).

## 5. Entry Rules

1. Detect cluster on each entry TF.
2. Trigger = rejection block (A, B2) or displacement (B). Candle must CLOSE to confirm.
3. **Limit price — TOURNAMENT (replaces "what makes the most sense"):**
   - **E1:** limit at the BB MA (most frequent in journals)
   - **E2:** limit at the 50% level of the trigger candle's wick
   - **E3:** limit at the penetrated cluster level nearest the block's close
4. Stop: beyond the wick extreme of the trigger candle / displacement origin. Structural, never widened (Vault-enforced).
5. No fill → no chase. Order cancels if price runs T_cancel points beyond entry without filling. T_cancel: CALIBRATE.
6. One position at a time. No overlapping trades ever. [CONFIRMED — Angus]

## 6. Targets

**Menu:** VWAP middle; VWAP ±1σ/±2σ; POC; session extremes (Asia/London/pre-market); data extremes; prior-day H/L; weekly H/L; pullback origin (B2); HTF range extremes.

**Selection tree v1:**
1. List opposing structural levels beyond entry, by distance.
2. Defaults: **A** → VWAP middle; **B2** → next structural level in move direction; **B** → opposing liquidity (pre-market/prior-day extreme), preferring ±2σ alignment.
3. **News-day override [CONFIRMED — Angus]:** on high-impact data days, data extremes have elevated sweep probability. If trade direction points at an untaken data extreme beyond the default target, target the data extreme instead. (Fallback variant to test: VWAP −1/+1 as the simpler proxy.)
4. **Fill front-run [CONFIRMED — Angus]:** working target = level ∓ F points (level minus F for longs). F: CALIBRATE (start 2–3 NQ pts). Backtest counts target *touched-minus-F* as filled, mirroring live behavior.
5. **RR floor:** nearest valid target < 1.5R → skip. CALIBRATE floor.
6. Alignment bonus: prefer targets where ≥2 menu levels stack within tolerance.

## 7. Filters & Skip Criteria

- Confluence minimum: 3 counter-trend; 2 with-trend at reduced risk.
- Location: no longs at HTF range top / shorts at range bottom.
- Invalidation-at-entry: trigger candle simultaneously touching the opposing ±1σ → stand down. [Hypothesis — test]
- Volatility stand-down: computable definition TBD (opening range vs ATR). [OPEN]
- News handling: data is bias/target input, not blackout; slippage modeled punitively near releases. "No entry within N min of release" = H4, test.

## 8. Trade Management — TOURNAMENT (split-test, per Angus)

- **V0:** none — set-and-forget (baseline)
- **V1:** BE at +1R. **Definition: TOUCH of +1R (any TF tick), stop to entry exact.** [CONFIRMED — Angus]
- **V2:** BE at first VWAP band milestone touch
- **V3:** BE at 09:30 open if entered pre-open
- **V4:** 50% partial at first structural level, runner to target
Each variant runs over identical data; Monte Carlo compares distributions; winner (or V0) goes live.
**Priority head-to-head (Angus test #1): V1 (BE at +1R touch) vs V0 (none), over the full Jan–Jul period, before the wider tournament.**

## 9. Sizing & Conviction

- Full unit vs half unit per conviction score: full requires 3+ confluences AND (with-trend OR A-at-extension) AND target ≥2R; any of {2 confluences, oversized stop, late-window entry, thin target} → half.
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
3. **Tournaments:** windows W1/W2 × entries E1–E3 × management V0–V4 — run as separate axes, not a combinatorial free-for-all; one axis fixed at a time to avoid overfitting via grid search.
4. **Out-of-sample:** Mar–Jul 2026 untouched until rules lock.
5. **Diagnostics:** per-slice expectancy (pattern × TF × confluence count × HTF flag × time bucket × news flag) so leaks are locatable.
6. **Monte Carlo:** winning config's distribution vs 50K eval (3K target / 2K trailing DD): pass probability, expected attempts/cost, days-to-pass, first-month blowup risk → sizing config → firm selection.
7. Live paper via TradingView; agents grade real-time; human executes.
