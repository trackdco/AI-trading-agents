# NQ VWAP/BB/Profile Strategy — Definition v1.0

**Status:** LOCKED pending final Angus read-through. Changes from v0.1 sourced from Angus Q&A (17 Jul 2026).
**Source of truth:** 28 hand-backtested trades (Feb 2–27 2026, NQ, NY morning) + journals + charts + Q&A.
**Purpose:** Section 0 context for every spec in the build. Nothing is implemented that isn't written here. Items marked CALIBRATE are numeric parameters the February re-run tunes; items marked TOURNAMENT are rule variants tested head-to-head.

---

## 1. Instrument, Session, Timeframes

- **Instrument:** NQ (CME), sized via MNQ where risk requires.
- **Entry window: RTH 09:31–16:00 ET, entry blackout 09:31–09:35, first tradeable signal bar 09:36.** [AMENDED 2026-08-07 — see Amendment Log A1]
  - Tournament variants retained for later testing, all now *inside* the RTH boundary: **W2:** full RTH day with Vault risk parameters unchanged (Angus priority test #2 — where does the edge live across the day?); **W3:** other sessions (London etc.) — Hypothesis H3, after v1 validates. Backtest declares the winner. [TOURNAMENT]
  - **Superseded:** W1 08:00–11:00 ET, pre-market through pre-lunch. Retained here for traceability only; it is no longer the primary window. Nine of the 28 hand-log trades fall before 09:36 and are consequently OUT OF SCOPE — see `data/reference/hand_log_scope.md`.
- **End-of-day flatten:** VAULT RULE, not strategy: any open position is flattened before the CME close per the eventual firm's rules (default 15:55 ET). Exists as a backstop; expected to almost never fire (median trade resolves ~30 min).
- **Entry TFs:** 1m, 2m, 3m, 5m. **MTF arbitration:** evaluate all four; if multiple TFs show valid triggers simultaneously, take the highest TF. [CONFIRMED — Angus]
  - **1m is RETAINED as an entry timeframe and every 1m trade is FLAGGED in Stage 3 output** (boolean `entry_tf_1m`). [AMENDED 2026-08-08 — see Amendment Log A11] Parity on 1m is **structurally unverifiable on the workbench window** — the reference platform's 1-minute history does not reach back to January 2025, and the recent window where it does is the sealed holdout. The flag preserves the ability to answer the question retrospectively rather than scoping 1m out to avoid a measurement problem.
- **Context TFs:** 15m for HTF trend/range flag; 1h/4h for range extremes. **The 4h/1h range is RECORDED, NOT GATED ON** — see §7 and Amendment Log A9.

## 2. Indicator Stack (computable only)

| Indicator | Parameters | Role |
|---|---|---|
| Bollinger Bands | 20, SMA, close, 2σ | Basis ("BB MA") = core cluster level |
| NY session VWAP | **Anchored 09:30 ET cash open** — does NOT exist pre-market. ±1σ/±2σ/±3σ. **Computed from 1-minute bars (A8). σ bands are INELIGIBLE below the minimum-observation threshold of §2.1 (A8).** | Cluster levels, extension detector, targets |
| Daily VWAP | **CORE — "one of the most important components" (Angus).** Full band set ±1σ/±2σ/±3σ. Anchor: CONFIRMED — standard TradingView VWAP, resets at CME daily session open, 18:00 ET / Asia open. **Computed from 1-minute bars (A8).** | Core cluster level at all times; the ONLY VWAP pre-9:30 |
| Volume profile | Session + daily; **weekly anchor added as tested variant (Angus)**. POC, VAH/VAL, HVN/LVN | POC = core cluster level; profile feeds targets |
| Session boxes | Asia / London / NY | Session extremes for targets/liquidity |
| Data levels | Extremes printed within N min of scheduled releases | Bias + targets. N: CALIBRATE (start 15 min) |

### 2.1 Indicator input feed [ADDED 2026-08-08 — see Amendment Log A8]

**Both VWAP anchors are computed from 1-minute bars — ONE canonical series, shared by every
entry timeframe.** Reason: VWAP estimates a single underlying quantity (the volume-weighted mean
price since the anchor); bar size is only the resolution at which that integral is approximated,
and finer is strictly better. **Bollinger Bands remain per-entry-timeframe**, because a 20-bar
SMA of 5m bars is *definitionally* a different object from a 20-bar SMA of 2m bars — there is no
single underlying quantity being approximated. The volume profile likewise uses 1-minute bars.

~~**Minimum observations before NY VWAP σ bands are eligible: 30 completed 1-minute bars since
the 09:30 anchor, i.e. from 10:00 ET.**~~ **SUPERSEDED BY A13 — the fixed-n form is the wrong
shape. 30 does not satisfy the tightened criterion (5.01 pt against a 5.00 pt bound) and no n
does at the p75 σ̂, because the CI half-width is nearly flat in n.**

**IN FORCE (A13): a NY VWAP σ band is cluster-eligible when the 95% CI on its distance from the
mid is ≤ HALF the §3 cluster tolerance —** `1.95996 · σ̂ / √(2(n−1)) ≤ 5.00 points` — **evaluated
live, per instant, from that session's own σ̂.** Below that the NY **mid** is usable and the **σ
bands are not**: they may not enter a cluster (§3) and may not serve as the §7 invalidation
reference. **No waiting period, no clock time, no fitted constant.** Derivation in A13.
**Pre-registered, not tuned: no value was tried against outcomes.**

**EXCLUDED: MIG LiquidityEdge.** Closed-source, mutable, replay-inaccurate. MIG targets in journals re-map to nearest computable structural level. A native absorption/exhaustion zone detector is a possible future module, validated separately.

## 3. Core Definitions

- **Confluence cluster:** ≥2 of {BB MA, NY VWAP middle/±1σ (post-9:30 only), daily VWAP middle/±1σ/±2σ/±3σ, daily POC} within proximity tolerance. Pre-9:30, the VWAP family = daily VWAP only. Tolerance: CALIBRATE (start ~10 NQ pts / 0.04%).
- **Confluence count:** distinct level *types* touched (VWAP family ×1, BB ×1, POC ×1, structural ×1).
- **Rejection block:** entry-TF candle that (a) trades into the cluster, (b) CLOSES back on the trade side of all cluster levels, (c) leaves a wick through/into them. **Tradeable zone = the wick: from body edge to wick extreme.** [CONFIRMED — Angus]
- **Displacement (numerical, per Angus "compelling close" requirement):** entry-TF candle whose **body closes through ≥2 cluster levels**, with **body/range ≥ B_min** and **close within the extreme quartile of the candle's range** (top 25% for longs, bottom 25% for shorts — kills the "barely breaks through with a top wick" case). B_min: CALIBRATE (start 0.6). Optional size floor range ≥ k×ATR(20): CALIBRATE (start k=1.0).
- **Over-extension:** touch of NY VWAP ±2σ (extreme ±3σ).

## 4. Pattern Taxonomy (mechanism-based; HTF alignment is a separate flag)

- **A — Reversal:** over-extension and/or HTF range extreme → rejection block against prior move → retest entry.
- **B — Reclaim:** price on wrong side of cluster → displacement back through → retest of reclaimed cluster.
- **B2 — Continuation:** established move → pullback to cluster → rejection block with the move → retest entry.
- **HTF flag:** with_trend / counter_trend / range, tagged per trade. Counter-trend raises confluence requirement (§8).

## 5. Entry Rules

1. Detect cluster on each entry TF.
2. Trigger = rejection block (A, B2) or displacement (B). Candle must CLOSE to confirm.
3. **Limit price — TOURNAMENT (replaces "what makes the most sense"):**
   - **E1:** limit at the BB MA (most frequent in journals)
   - **E2:** limit at the 50% level of the trigger candle's wick
   - **E3:** limit at the penetrated cluster level nearest the block's close
4. Stop: beyond the wick extreme of the trigger candle / displacement origin. Structural, never widened (Vault-enforced). **Minimum stop distance: 10.00 points (40 ticks). Effective stop = max(structural stop, 10.00 pt).** The floor applies at order placement only; once placed the stop is never widened, and a structural stop already beyond 10.00 pt is used unchanged. A trigger whose E1 entry falls on the wrong side of the wick extreme remains invalid — the floor does not rescue it. [AMENDED 2026-08-08 — see Amendment Log A5]
5. No fill → no chase. Order cancels if price runs T_cancel points beyond entry without filling. T_cancel: CALIBRATE.
6. One position at a time. No overlapping trades ever. [CONFIRMED — Angus]

## 6. Targets

**Menu:** VWAP middle; VWAP ±1σ/±2σ; POC; session extremes (Asia/London/pre-market); data extremes; prior-day H/L; weekly H/L; pullback origin (B2); HTF range extremes.

**Selection tree v1:**
1. List opposing structural levels beyond entry, by distance.
2. Defaults: **A** → VWAP middle; **B2** → next structural level in move direction; **B** → opposing liquidity (pre-market/prior-day extreme), preferring ±2σ alignment.
3. **News-day override [CONFIRMED — Angus]:** on high-impact data days, data extremes have elevated sweep probability. If trade direction points at an untaken data extreme beyond the default target, target the data extreme instead. (Fallback variant to test: VWAP −1/+1 as the simpler proxy.)
4. **Fill front-run [CONFIRMED — Angus]:** working target = level ∓ F points (level minus F for longs). F: CALIBRATE (start 2–3 NQ pts). Backtest counts target *touched-minus-F* as filled, mirroring live behavior.
5. **RR floor — target is the nearest *valid* target, and "valid" means it clears the floor.** Walk the ladder of opposing menu levels outward from entry. The working target is the **first level whose front-run-adjusted distance is ≥ 1.5R**. Skip only if **no** level in the menu clears the floor. RR floor: CALIBRATE. [AMENDED 2026-08-08 — see Amendment Log A4]
   - **Superseded reading:** "test rung 1; if it is under 1.5R, skip." Retained here for traceability. It measured the floor against a level a median 7.95 pts from entry and discarded setups the menu already carried a valid target for.
   - Consequence, recorded: realised RR will sit near the floor by construction. That is lower than the hand log's realised 3.68R and is deliberate — this rule completes a specification, it does not attempt to reproduce the human's payoff.
6. Alignment bonus: prefer targets where ≥2 menu levels stack within tolerance.

## 7. Filters & Skip Criteria

- Confluence minimum: 3 counter-trend; 2 with-trend at reduced risk.
- ~~Location: no longs at HTF range top / shorts at range bottom.~~ **DEMOTED FROM GATE TO
  RECORDED COVARIATE 2026-08-08 (A9).** Range position is **recorded, not gated on**. Stage 3
  output carries **both** definitions as columns — `range_pos_swing` (swing highs/lows, the
  reference definition) and `range_pos_blocks` (session-local 240-min clock blocks, the former
  implementation) — and **neither removes a candidate.** Reason: the threshold was never written
  down, the two definitions differ by a factor of 11 on the same instant and land on opposite
  sides of any plausible threshold, and the runbook prefers continuous covariates to binary
  gates. Whether location predicts outcome becomes a pre-registered question, not an assumption.
- Invalidation-at-entry: trigger candle simultaneously touching the opposing ±1σ → stand down. [Hypothesis — test]
- Volatility stand-down: computable definition TBD (opening range vs ATR). [OPEN]
- News handling: data is bias/target input, not blackout; slippage modeled punitively near releases. "No entry within N min of release" = H4, test.

## 8. Trade Management — TOURNAMENT (split-test, per Angus)

- **V0:** none — set-and-forget (baseline)
- **V1:** BE at +1R. **Definition: TOUCH of +1R (any TF tick), stop to entry exact.** [CONFIRMED — Angus]
- **V2:** BE at first VWAP band milestone touch
- ~~**V3:** BE at 09:30 open if entered pre-open~~ — **STRUCK 2026-08-08 (A6).** Unreachable: A1 sets the first tradeable signal bar at 09:36, so no trade can be entered pre-open and the variant can never fire. Retained struck-through for traceability.
- **V4:** 50% partial at first structural level, runner to target

**Management axis = 4 variants (V0, V1, V2, V4).** Tournament configuration space 90 → **72**.
Each variant runs over identical data; Monte Carlo compares distributions; winner (or V0) goes live.
**Priority head-to-head (Angus test #1): V1 (BE at +1R touch) vs V0 (none), over the full Jan–Jul period, before the wider tournament.**

## 9. Sizing & Conviction

- Full unit vs half unit per conviction score: full requires 3+ confluences AND (with-trend OR A-at-extension) AND target ≥2R; any of {2 confluences, oversized stop, late-window entry, thin target} → half.
- Absolute per-trade risk ceiling comes from Monte Carlo vs eval rules — expected well below the sample's $400.

## 10. Vault (deterministic, no LLM access)

### 10.1 Selector — FIRST-COME [AMENDED 2026-08-08 — see Amendment Log A7]

The Vault admits **at most one candidate at a time, in signal-time order**. Stated in full:

1. **Admission order.** Qualified candidates (those surviving §5, §6 and §7) are admitted in
   ascending order of **signal minute** — the close minute of the trigger candle. No candidate
   is compared against any later candidate. Nothing about the session's future is consulted.
2. **One position at a time.** While a position is open, later candidates are **NOT admitted
   and are NOT queued**. A candidate that fires during an open position is **DISCARDED**. It is
   not reconsidered when the position resolves. Re-entry requires a **fresh trigger** meeting
   §5 in full.
   - *Why discarded rather than queued:* a trigger's validity is tied to its trigger candle
     (§5.2, "candle must CLOSE to confirm") and its entry is a limit at the BB MA (E1). By the
     time an earlier position resolves the BB MA has moved, the cluster may have dissolved and
     the trigger candle is stale. Filling a stale trigger at a price that no longer sits on the
     level is precisely the behaviour §5.5 forbids — *"No fill → no chase."* Queueing would
     reintroduce chasing under another name.
3. **Session cap.** At most **3** candidates are admitted per session (§10 as written). Once 3
   are admitted, all further candidates are discarded regardless of quality.
4. **Tie-break — candidates sharing a signal minute.** Applied in order; the first level that
   separates them decides.

   | # | rule | grounds |
   |---|---|---|
   | 1 | **Highest entry TF** | §1 MTF arbitration — *"if multiple TFs show valid triggers simultaneously, take the highest TF"* **[SPEC, CONFIRMED — Angus]** |
   | 2 | **Long and short on the same bar → stand down, take neither** | This is a confluence strategy. Contradictory confluence is not confluence, and there is no basis in the spec for preferring one side |
   | 3 | **Larger cluster (more distinct level types)** | §3 defines confluence count as the quality measure and §7 already gates on it. Using the spec's own measure to break a tie is consistent |
   | 4 | **Cluster nearest the entry price** | The cluster actually being traded against |
   | 5 | **Lowest cluster low** | Pure determinism backstop. Arbitrary, and stated as arbitrary, so that runs reproduce |

   **Before tie-breaking, collapse duplicate records of the same trade.** One cluster can emit
   both a rejection and a displacement trigger on the same bar; those share entry, stop and
   target and are **one trade, not two**.

   **Measured weight of each level** (workbench, 509 sessions — see `research/STATE.md`):
   ties occur on **16.4–22.9%** of signal minutes; level 1 resolves **15.7–19.1%** of
   admissions; level 2 fires on **0.2%** under reading A and never otherwise; **levels 3, 4 and
   5 never fire at all.** The tie-break is therefore carried entirely by a rule Angus already
   confirmed, and the arbitrary backstop is dead weight retained only for determinism.

5. **Consequence, stated plainly.** The 3/day cap discards **41–58%** of qualified candidates
   and binds on **63–91%** of sessions. **Admission order materially determines the traded
   population — the cap, not the strategy, sets which trades are taken.** This is a **known
   property of the design, not an oversight.** Any future change to trigger sensitivity changes
   the traded population through the cap before it changes anything else, and must be assessed
   on that basis.

### 10.2 Remaining Vault rules

- Max trades/day: **3** (config 2–3; Angus: "no more than 2–3 genuinely high-probability setups exist per day").
- Daily halt: after **2 losses** or **−2R** on the day, whichever first (placeholder; MC calibrates).
- One position at a time; no stop widening; EOD flatten (§1); drawdown kill-switch vs trailing DD buffer; size ceiling from MC.
- All verdicts (taken/skipped/vetoed) logged to strict-schema journal. Nightly stats refresh; weekly Edge-Lab-style review is generated as PROPOSALS ONLY — rule changes require out-of-sample evidence + Angus sign-off + doc version bump. The system never edits its own rules. [CONFIRMED — Angus]

## 11. Architecture Boundary

Agents grade against this doc and propose. Python owns sizing, stops, limits, kill-switch, execution. Telegram alerts fire from the Vault only (post-risk-check), via bot API; inbound /status /pause /flatten commands locked to Angus's chat ID (later phase).

## 12. Data & Validation Plan

1. **Data:** 1-minute NQ, Jan 2026 → present, via Databento (or equivalent cheapest clean source). 2025 pulled later as a regime-robustness check only — not pass/fail. [Angus regime rationale noted; robustness check is the honesty guard.]
2. **Calibration — DOWNGRADED, not relocatable. [AMENDED 2026-08-08 — A6]** The original gate ("February 2026 re-run must approximately reproduce the 28 hand trades") **cannot be run.** The held bar archives end 2026-01-30 and contain no February 2026. The repo does hold MBP-10 book snapshots for all 19 hand-log dates, but at one snapshot per minute with no intra-minute high/low and no volume — so no OHLC bars, no VWAP, no volume profile. Three of the detector's four inputs are absent, and the calibration cannot be reconstructed from that schema either. **Replacement:** a behavioural sanity report over 2025-01-06 → 2025-01-31 (spec-1 Step 8), which checks that the system behaves plausibly but does **not** check it against Angus's trades. The two are not equivalent and the substitution is not a pass. Trade-by-trade divergence auditing and the skipped-day gap analysis are **irrecoverable** unless February 2026 bars are acquired.
   - **Superseded:** the February 2026 reproduction gate. Retained for traceability. See Amendment Log A3, `research/vwap-bb/preflight.md` gate 5, and `research/STATE.md`.
3. **Tournaments:** windows W1/W2 × entries E1–E3 × management V0/V1/V2/V4 — run as separate axes, not a combinatorial free-for-all; one axis fixed at a time to avoid overfitting via grid search. (V3 struck — A6.)
4. **Out-of-sample:** Mar–Jul 2026 untouched until rules lock.
5. **Diagnostics:** per-slice expectancy (pattern × TF × confluence count × HTF flag × time bucket × news flag) so leaks are locatable.
6. **Monte Carlo:** winning config's distribution vs 50K eval (3K target / 2K trailing DD): pass probability, expected attempts/cost, days-to-pass, first-month blowup risk → sizing config → firm selection.
7. Live paper via TradingView; agents grade real-time; human executes.

---

## Amendment Log

Append-only. Each entry records a ruling, its date, its reason, and the settled decision it
defers to — so a future reader sees a decision, not a silent edit.

### A1 — 2026-08-07 — Entry window changed from W1 08:00–11:00 ET to RTH 09:31–16:00 ET

**Change.** §1 entry window is now RTH 09:31–16:00 ET, with an entry blackout 09:31–09:35 and
the first tradeable signal bar at 09:36. W1 (08:00–11:00) is superseded and retained in §1 for
traceability only.

**Reason.** The doc's W1 window conflicted with the project's settled session convention. The
conflict was surfaced by PRE-FLIGHT gate 2 (`research/vwap-bb/preflight.md`), which found that
nine of the 28 hand-log trades — 32% of the sample, including its single largest winner at
+12.98R — fall before 09:36 and are therefore untradeable under the settled convention. Two
documents were describing two different strategies.

**Settled decision deferred to.** RTH 09:31–16:00, entry blackout 09:31–09:35, first tradeable
signal bar 09:36. Settled decisions take precedence over the strategy doc where the two
conflict; this amendment brings the doc into line rather than the reverse.

**Consequences, recorded so they are not rediscovered later:**
- Nine hand-log trades are OUT OF SCOPE. They are not deleted — see
  `data/reference/hand_log_scope.md` for the list and the reason.
- The in-scope hand-log evidence is **19 trades, 13 wins (68.4%), Wilson 95% [46.0%, 84.6%]**,
  against a cost-adjusted breakeven of 40.6% at the §6.5 1.5R floor with c/s = 1.53%.
  One-sided binomial p = 0.0133 — it clears breakeven at the lower bound.
- **Open item, NOT resolved by this amendment:** BB(20) and ATR(20) evaluated at 09:36 reach
  back into pre-open bars whose median 1-minute range is 5.75 pts against 9.50 in RTH. Every
  band width and ATR threshold on the first tradeable bars is therefore computed from a regime
  1.65× quieter than the one being traded, biasing toward admitting trades the rule intends to
  exclude. Adopting RTH does not fix this. It is logged for the study design.

### A2 — 2026-08-07 — Five previously unstated parameters frozen

Recorded in full in `research/vwap-bb/preflight.md` gate 4. VWAP typical price = HLC/3
[SPEC, per "standard TradingView VWAP"]; volume-profile bin = 1.00 pt [FIAT]; HTF
classification = 15m fractal swings N=2, HH+HL ⇒ uptrend / LH+LL ⇒ downtrend / else range
[FIAT]; stop buffer = 1 tick beyond the wick extreme [FIAT, per §5.4 "never widened"];
volatility stand-down = DISABLED for v1 [FIAT, §7 was marked OPEN with no definition].
Zero parameters were set by examining outcomes. N_trials remains 0.

**The fractal item is EXTENDED by A10 (2026-08-08):** A2 fixed N=2 but never stated how equal
extremes are treated, and a strict `>` on both sides admits neither bar of a plateau. A10 states
the comparison explicitly. **N=2 and the HH+HL/LH+LL classification are unchanged.**

### A3 — 2026-08-07 — Parity and calibration targets relocated into available coverage

§12.2's February 2026 calibration month does not exist in the held bar data, which ends
2026-01-30. Parity dates relocated; the calibration gate is **downgraded**, not relocated —
see `research/vwap-bb/preflight.md` gate 5 and spec-1 Step 4 / Step 8 for the substitution and
why the two are not equivalent.

### A4 — 2026-08-08 — §6 rule 5: "nearest valid target" disambiguated to "nearest target that clears the floor"

**Change.** §6 rule 5 previously read *"nearest valid target < 1.5R → skip."* It is now: walk
the ladder of opposing menu levels outward from entry and take the **first level whose
front-run-adjusted distance is ≥ 1.5R**; skip only if **no** level in the menu clears the floor.

**Reason.** The word *"valid"* was never defined, and the implementation read it as vacuous —
rung 1 was tested and, if it failed, the setup was discarded even when the menu already carried
a level that cleared the floor. Measured over 33,993 pre-floor candidates
(`research/vwap-bb/target-stop-reconciliation.md` §3):

| ladder rung | median distance from entry |
|---|---|
| nearest — what the old rule tested | **7.95 pts** |
| 2nd nearest | 20.88 pts |
| 3rd nearest | 37.36 pts |
| nearest liquidity extreme (§6 rule 2's default for B) | 75.76 pts |
| deepest rung the menu offers | 192.36 pts |

**63.3% of candidates have a level ≥155.2 pts available** — the hand log's median winner
distance — and 91.8% have one ≥84.2 pts, its smallest. The menu is not short of targets. The
old reading of rule 5 discarded them, and in doing so turned the RR floor into a filter that
*preferentially admitted the tightest stops in the population* (median stop 5.62 pt pre-floor,
3.12 pt post-floor). The floor was screening on stop size, not target quality.

Reading "valid" as "clears the floor" is the only reading under which rule 5 is not
self-defeating, and it is consistent with rule 1 ("list opposing structural levels beyond
entry, **by distance**") — a list ordered by distance implies walking it.

**Grounds.** Selected **structurally**: the menu holds these levels and the nearest-rule
discards them. **No outcome was computed, no P&L, no configuration compared, nothing ranked.**
The feasibility map that surfaced the defect reports constraints satisfied, not performance.

**Tag: [FIAT].** The spec states no disambiguation; this supplies one.

**Consequences, recorded so they are not rediscovered later:**
- Realised RR now sits **near the floor by construction** — the rule takes the first
  qualifying level, not the best one. That is *below* the hand log's realised 3.68R. This is a
  specification completion, not an attempt to reproduce the human's payoff, and the gap is
  expected.
- §6 rule 2's pattern-conditioned defaults (**A** → VWAP middle, **B2** → next structural
  level, **B** → opposing liquidity) remain **unimplemented and ambiguous**. Pattern A's
  default names a target that 85.4% of the time sits *inside* the firing cluster, i.e. at the
  entry. A4 does not fix rule 2. **Open, needs Angus.**
- The A/B/B2 taxonomy of §4 is not implemented in the detector at all.

### A5 — 2026-08-08 — §5.4: minimum stop distance of 10.00 points

**Change.** §5.4 now carries a floor: effective stop = **max(structural stop, 10.00 pt)**. The
floor applies at placement only; the "never widened" rule is unchanged, and a structural stop
already beyond 10.00 pt is used as-is.

**Reason — fill realism and measured spread, not performance.**

1. **The measured spread makes tighter stops meaningless.** Top-of-book spread over 5,781 RTH
   snapshots on 99 sessions is **0.75 pt median (3 ticks), 1.50 pt at p90**
   (`research/STATE.md` COSTS). A 10.00 pt stop is **40 ticks — 13.3× the median spread and
   6.7× the p90.** Below roughly that scale the stop is not measuring structure, it is
   measuring the width of the book.
2. **It bounds cost as a fraction of risk.** At the measured base stop-exit cost of 0.975 pt,
   a 10 pt stop puts costs at **9.75% of risk**. The frozen geometry's 3.12 pt median put them
   at **31.2%**, which moved cost-adjusted breakeven from 40.6% to 46.4% on its own.
3. **It never excludes behaviour the author demonstrated.** The hand log's smallest in-scope
   stop is **11.00 pts**; the floor sits below it. Every trade Angus actually took under the
   settled session convention is admissible under A5. This uses the author's recorded stop
   *distances*, not his P&L.
4. **It sits inside the feasible region**, jointly with A4 — the two are coupled, since a floor
   on R raises the distance a target must reach to clear 1.5R
   (`target-stop-reconciliation.md` §5).

**Grounds.** **No outcome was computed, no P&L, no configuration compared, nothing ranked.**

**Tag: [FIAT].** §5.4 stated no minimum.

**Consequences, recorded so they are not rediscovered later:**
- A5 is a **floor, not a repair.** The 29.6% of triggers whose E1 entry falls on the wrong side
  of the wick extreme remain invalid and are still skipped. The E1-plus-wick pairing is
  degenerate at both ends and that is **still an open gate-4 item**.
- With A4, the minimum target distance becomes 15.00 pts (10.00 × 1.5).
- The §1 note that "median trade resolves ~30 min" was derived under the old geometry. Wider
  stops lengthen holds, so the 30-minute one-position lockout used in the signal count is a
  **declared placeholder that A5 makes more approximate, not less**.

### A6 — 2026-08-08 — Housekeeping: V3 struck; §12.2 corrected

**V3 struck from the management axis.** *"BE at 09:30 open if entered pre-open"* cannot fire:
A1 sets the first tradeable signal bar at 09:36, so no trade is ever entered pre-open. The
management axis is **4 variants (V0, V1, V2, V4)** and the tournament configuration space is
**90 → 72**. Retained struck-through in §8 for traceability.

**§12.2 corrected.** It still described the February 2026 calibration as a live gate after A3
had downgraded it. The corrected text records that the gate cannot be run, why the MBP-10 book
snapshots do not rescue it (one snapshot per minute; no intra-minute high/low, no volume, so no
OHLC, no VWAP, no volume profile — three of the detector's four inputs absent), and that the
behavioural sanity report substituted in its place is **not equivalent and is not a pass**.

**Grounds.** Both are corrections of internal inconsistency. No outcome was computed.

### A7 — 2026-08-08 — §10: the Vault selector is FIRST-COME, stated in full

**Change.** §10 gains 10.1, which states the admission rule the spec never contained: candidates
admitted in signal-time order, one position at a time, later candidates during an open position
**discarded not queued**, max 3 per session, with a five-level tie-break for candidates sharing
a signal minute. Full text in §10.1.

**Reason — first-come by ELIMINATION, not by comparison.**

1. **A ranking selector is not tradeable.** "Take the highest-conviction candidate of the
   session" requires knowing every candidate before choosing one. That is lookahead. It cannot
   be executed in real time and no backtest of it would mean anything.
2. **A threshold selector needs a score with resolution, and §9's has none.** The conviction
   score is **3-valued** (confluence ≥3, with-trend, target ≥2R) and **~two-thirds of
   candidates sit on a single value** — 65.7% on score 2 under reading A. Any threshold either
   admits two-thirds of the pool or, among whatever clears it, collapses to first-come anyway.
   The score cannot separate the population it would be asked to rank.
3. **Therefore first-come is the only implementable selector the spec supports.**

**This is a specification completion by elimination, NOT a performance comparison. No outcome
was examined.** No selector was backtested, no P&L computed, no alternative scored. The two
rejected forms were rejected on *implementability* and *resolution* — properties of the rule
and the score, not of any result they produce. **N_trials remains 0.**

**Tag: [FIAT]** for the admission rule, the discard-not-queue ruling and tie-break levels 2–5.
**Tie-break level 1 is [SPEC]** — it is §1's MTF arbitration, already confirmed by Angus, and
it turns out to carry the entire tie-break in practice.

**Measured under A4 + A5 + A7** (workbench, 509 sessions, `vwapbb_a7_selector.py`):

| | A | B | C | D |
|---|---|---|---|---|
| qualified candidates / session | 47.43 | 27.44 | 13.76 | 8.87 |
| **ADMITTED trades / session** | **2.849** | **2.782** | **2.699** | **2.328** |
| blocked — position open | 15.6% | 17.0% | 22.3% | 25.9% |
| blocked — 3/day cap | 57.7% | 45.5% | 51.5% | 41.3% |
| sessions where the cap binds | 91.0% | 86.8% | 81.5% | 63.1% |
| signal minutes with a tie | 22.9% | 19.9% | 16.4% | 18.1% |
| median hold, minutes | 5 | 6 | 6 | 7 |

**All four readings clear the gate-6 tripwire of 0.4862 trades/session, by 4.8× to 5.9×.**

**Consequences, recorded so they are not rediscovered later:**
- **The cap is the dominant filter.** It discards 41–58% of qualified candidates and binds on
  63–91% of sessions. Admission order determines the traded population. Recorded in §10.1(5) as
  a known property.
- **The arbitrary tie-break backstop is never used.** Levels 3, 4 and 5 fire on 0.0% of
  admissions. §1's MTF arbitration resolves everything that is not already unique. The [FIAT]
  content of the tie-break is, in practice, zero.
- **A measurement-hygiene finding.** Before duplicate records were collapsed, level 5 appeared
  to decide **36.1%** of admissions and ties appeared to occur on **39.3%** of signal minutes.
  Both were artefacts: `trig()` emits a rejection and a displacement for the same cluster, and
  those duplicates were tying with themselves. Every level-5 invocation was between two records
  of an **identical** trade — same entry, same stop, same target — so the choice was immaterial.
  The admitted counts are unchanged by the fix; only the tie statistics were wrong. **An
  arbitrary rule that looks load-bearing may just be counting one thing twice.**
- **Median hold is 5–7 minutes against the hand log's ~30.** Stops under A5 are still ~3.5×
  tighter than the human's 35-point median, so positions resolve faster and the
  one-position rule blocks less than it would under his geometry. **Residual, not new** — it
  follows from A5 being a floor rather than the anchor, which remains unresolved.

---

**N_trials after A4, A5, A6 and A7: 0.** None of these amendments was selected by comparing
outcomes, computing P&L, ranking configurations, or reading the holdout. A4, A5 and A7 are
**specification completions** — they supply values, disambiguations and rules the spec never
stated, on structural, execution-realism and implementability grounds. A6 is a correction of
internal inconsistency.
The first decision made by comparing outcomes will increment N_trials, and must be recorded
here at the moment it is made.

---

## Amendments A8–A11 — 2026-08-08 — the four gaps parity P2 surfaced

**Source: `research/vwap-bb/PARITY-P2-RESULT.md` (PARITY FAIL, 12 of 48 numeric fields, all
twelve diagnosed as specification gaps) and Runbook Amendment 03. No implementation bug was
found. None of these four is selected because it makes the detector agree with the reference
chart; where a resolution also happens to resolve a mismatch, that is recorded as a CHECK, not
as the justification. N_trials remains 0.**

### A8 — 2026-08-08 — §2.1: the VWAP input feed is 1-minute, and NY σ bands get a minimum-observation rule

**Change.** New §2.1. Both VWAP anchors are computed from **1-minute bars, one canonical series**
shared by all four entry timeframes. Bollinger Bands stay **per-entry-timeframe**. NY VWAP σ
bands are **ineligible for cluster membership (§3) and for the §7 invalidation reference until
30 completed 1-minute bars have elapsed since the 09:30 anchor** — i.e. from **10:00 ET**. Below
that the NY **mid** remains usable.

**Reason for the feed — arithmetic, not aesthetic.** §2 said *"standard TradingView VWAP"*, an
indicator whose value depends on the chart's timeframe, and never named the feed. VWAP estimates
**one underlying quantity** — the volume-weighted mean price since the anchor — and bar size is
only the resolution at which that integral is approximated. Finer is strictly better, so 1m wins
on the merits. A Bollinger basis is not like this: a 20-bar SMA of 5m closes is a *different
object* from a 20-bar SMA of 2m closes, not a coarser estimate of the same one, so
per-timeframe is the only coherent reading there. **The split is principled.**

Per-entry-timeframe VWAP was the tempting alternative and fails hardest where the indicator is
already weakest. Completed bars behind the NY anchor at 09:50: **1m 20 · 2m 10 · 3m ~6 · 5m 4.**
A standard deviation from four observations, used to place a level that decides cluster
membership and invalidation, is indefensible.

**Reason for the minimum-observation rule — the estimator, not the data.** The relative standard
error of a standard deviation estimated from *n* observations is approximately
**1/√(2(n−1))**. That is a property of the estimator; it needs no data to evaluate and **no value
was tried against the trade list**.

| n bars since 09:30 | ET | RSE of σ̂ | 95% CI on the band's distance from the mid |
|---|---|---|---|
| 6 | 09:36 | **31.6%** | ±62% — the ±1σ band could be anywhere from 0.38σ to 1.62σ |
| 10 | 09:40 | 23.6% | ±46% |
| 20 | 09:50 | 16.2% | ±32% |
| **30** | **10:00** | **13.1%** | **±26%** |
| 60 | 10:30 | 9.2% | ±18% |

**30 is chosen because it is the point at which the σ estimate's own 95% interval is narrower
than the cluster tolerance it feeds.** At the workbench's typical early-session NY σ of roughly
15–20 points, a ±26% interval on σ is ±4–5 points — inside the ~10-point cluster tolerance of
§3, so the band's *membership* decision is no longer dominated by estimation error. At n=6 the
same interval is ±9–12 points, wider than the tolerance itself: the level is noise with a line
drawn through it. 30 is also the conventional small-sample boundary, which is a weak reason on
its own and is not the operative one.

**Stated as a cost, not hidden.** This makes the first tradeable signal bar (09:36) fall inside
the ineligible window. Between 09:36 and 09:59 the NY VWAP contributes its **mid only**. Fewer
clusters will form and the §7 invalidation will fire less in that window. **That is the intended
consequence** — a level that cannot be estimated should not be allowed to decide trades — and it
is a spec change whose effect on trade counts is unmeasured at the time of writing.

**Cost to parity, recorded as a limitation and not as a pass.** NY VWAP band parity against the
reference chart is now **unverifiable**: Angus cannot render a 1-minute VWAP for January 2025.
The daily VWAP agreement at 0.002 across feeds is genuine reassurance about the implementation;
the NY bands get none.

**Tag: [SPEC]** for the 1m feed (it resolves what *"standard TradingView VWAP"* left open on
structural grounds). **[FIAT]** for the 30-bar threshold. **Free-parameter count +1.**

**Check, not justification:** the detector already computed from 1m bars, so A8 codifies existing
behaviour on the feed and does **not** move the detector toward the reference chart. It moves the
*specification* to where the detector already was, for an independent reason.

### A9 — 2026-08-08 — §7: the location filter is DEMOTED from gate to recorded covariate

**Change.** §7's *"no longs at HTF range top / shorts at range bottom"* no longer removes a
candidate. Stage 3 records **two** columns — `range_pos_swing` (swing highs/lows, the reference
definition set by the P2 reading) and `range_pos_blocks` (session-local 240-minute clock blocks,
≤6, session-reset, current partial block excluded — the former implementation). **Gate on
neither.**

**Reason 1 — the threshold was never written down.** §7 states a direction, not a number. The
implementation invented `LOC_BAND = 0.20`. Asked to make the call by eye at P2, the reference
trader answered *"not really sure."* **A rule nobody can state is not a filter; it is a free
parameter with a gate's authority.**

**Reason 2 — the two definitions are not two readings of one thing.** At 2025-01-22 09:50 the
swing range is **1733.25** points wide and the clock-block range **151.75** — a factor of
**eleven** — putting price at **74.50%** and **143.99%** respectively, on opposite sides of any
plausible threshold. Neither candidate is clearly right, which is the strongest argument that
neither should be load-bearing.

**Reason 3 — house style.** Amendment 01's Stage 5 doctrine prefers continuous covariates to
binary gates: a gate splits the trade budget, a covariate keeps every trade in the fit. Range
position is natively continuous. Recording is free; testing is what costs α.

**Measured before the change, as required by Amendment 03 §8.1** — descriptive count, full
workbench, 501 processed sessions, `research/star-trading/tools/loc_gate_measure.py`:

| | |
|---|---|
| Otherwise-valid candidates (every gate except location) | **23,490** — 12,042 long / 11,448 short |
| **Blocked by the location gate** | **4,346 = 18.50%** — long **19.55%**, short **17.40%** |
| Range position **outside [0, 1]** | **21.07%** — 11.34% above 1.00, 9.79% below 0.00 |
| Admitted trades, gate **ON** | **1,423** (655 long / 768 short), 2.8403/session |
| Admitted trades, gate **OFF** | **1,453** (719 long / 734 short), 2.9002/session |
| Delta | **+30 trades, +2.11%** |
| Amendment 02 floor n ≥ 661 | ON **2.15×** · OFF **2.20×** — both CLEAR |

**The feared failure mode did NOT materialise, and this is recorded as a negative result.**
Amendment 03 §4 warned the gate might be suppressing longs systematically in an up-drifting
market and pushing the realised count under the runnable floor. It blocks **19.55% of longs
against 17.40% of shorts** — near-symmetric, not a systematic long suppression — and the sample
budget is never at risk. **Decision 2 is a footnote on sample size.** The demotion stands on
reasons 1–3, which are about specification quality, not about trade counts.

**Two findings the count did produce, neither of which was the one being looked for:**

1. **The range fails to contain price 21.07% of the time.** A "range" price sits above or below
   is not a range under any reading of §7, and 4,346 gate decisions were taken on it.
2. **The cap absorbs the gate.** 4,346 blocked candidates yield only **+30** admitted trades when
   the gate is removed, because the 3/session cap and one-at-a-time occupancy substitute one
   trade for another. But the *composition* moves: **655→719 long, 768→734 short**, i.e. 46.0/54.0
   becomes 49.5/50.5. **The gate's effect on which trades are taken is an order of magnitude
   larger than its effect on how many.** Consistent with §10.1(5): the cap, not the filter, sets
   the population.

**Tag: [SPEC]** — this removes an invented parameter rather than adding one. **Free-parameter
count −1** (`LOC_BAND` retired).

**Consequence for the sealed result, stated plainly:** the sealed run **applied** this gate. It
is therefore a result on the pre-A9 specification. See A12 note below.

### A10 — 2026-08-08 — A2's 15m fractal: equal extremes, stated

**Change.** A swing high at bar *i* requires **`H[i] > H[i−1 … i−N]` AND `H[i] ≥ H[i+1 … i+N]`**.
Mirrored for lows: **`L[i] < L[i−1 … i−N]` AND `L[i] ≤ L[i+1 … i+N]`**. **The first bar of a
plateau is the swing.** N=2 and the HH+HL / LH+LL classification are unchanged.

**Reason 1 — the level was established by the bar that created it.** A2's fractal is a
formalisation of chart reading, and a chart reader attributes structure to the bar that made the
high, not the one that revisited it.

**Reason 2 — it confirms earlier, for free.** Under N=2 a swing at bar *i* is confirmed once
*i+1* and *i+2* complete. Admitting the first bar of a plateau rather than the last confirms one
plateau-length sooner. **Confirmation lag is pure cost** in a model whose first tradeable bar is
09:36, and a rule that reduces it at no cost should.

**Why it was needed.** A strict `>` on both sides admits **neither** bar of a plateau. On
2025-01-22 the 08:30 and 08:45 fifteen-minute bars both printed **21934.25 to the tick**; the
detector admitted neither, fell back to 21905.00 at 06:15, and read **range** where the reference
read **uptrend**. Three of the four swings matched to ≤0.25 at identical timestamps. **The entire
trend flag turned on a tie the spec never anticipated.**

**Check, not justification.** Applied to that instant, 08:30 is admitted at 21934.25 against
21905.00 at 06:15 — a higher high, the lows already agreed — and the flag becomes **uptrend**,
matching the reference. **The rule was chosen on the two reasons above and would stand if it had
produced the opposite flag.** Recorded this way so it is never read as fitted.

**Tag: [FIAT]** — a tie-breaking convention. It replaces silence rather than adding a knob, so
the free-parameter count is unchanged.

**Consequence for the sealed result:** the sealed run used strict `>`, so its HTF flags differ
wherever a 15m plateau occurs. See A12 note below.

### A11 — 2026-08-08 — §1: 1m retained, and flagged

**Change.** 1m remains an entry timeframe. Stage 3 output carries a boolean **`entry_tf_1m`** on
every trade.

**Reason — the alternatives are worse, and the hole is permanent.** The reference platform's
1-minute history does not reach nineteen months back, so **there is no instant inside the
workbench where a 1m reference reading can be taken**, and the recent window where 1m *is*
renderable is the sealed holdout. Scoping 1m out would discard the hand log's four 1M entries —
two of them in scope — and would change the strategy to avoid a *measurement* problem, which is
backwards. Ignoring it means not knowing whether the result rests on an unverified path.

**Flagging costs one boolean and buys a retrospective answer:** if Stage 3's expectancy survives
with 1m trades excluded, the hole never mattered; if it does not, **the finding is that the edge
lives in the least-verified code path**, which is worth knowing before it trades money.

**Why the hole is live and not academic.** At P2 it was moot — no 1m trigger at the instant. But
across **09:36–09:44 the detector fired eleven raw 1m triggers, three carrying two cluster
types**, at minutes that cannot be rendered. **A parity instant chosen one minute earlier would
have been silently incomplete.**

**Named and not quietly dropped:** one recent session of 1-minute OHLCV, pulled solely to run a
parity instant and never used for performance measurement, would close the hole for a trivial
sum. A unit test is not a sample and it contaminates nothing. **Angus's standing no on further
data purchases holds; this is recorded as available, not recommended.**

**Tag: [SPEC]** — an output field, no rule change, no new parameter.

### A12 — 2026-08-08 — note: what A8–A11 do to the sealed workbench result

**A9 and A10 change the admitted population; A8 and A11 do not.**

| amendment | changes the population? | why |
|---|---|---|
| A8 feed | **No** on the feed — the detector already used 1m. **Yes** on the σ-band eligibility rule, which is new and unrun | codifies existing behaviour, then adds a restriction |
| A9 location | **Yes** | the sealed run applied the gate; the amended spec does not. Measured: 1,423 → 1,453 admitted, and the direction mix moves 46.0/54.0 → 49.5/50.5 |
| A10 fractal | **Yes** | HTF flags differ wherever a 15m plateau occurs, which changes counter-trend status and hence the confluence minimum |
| A11 1m flag | **No** | output-only |

**Therefore `workbench_results_SEALED.parquet` is a result on the PRE-A8 specification.** It is
not invalidated and it is not re-sealed here — that is a decision for Angus, not a side effect of
an amendment. What is recorded is that **the spec hash it was produced under is superseded**, and
that any Stage 3 run under A8–A11 is a *different* run and must be sealed separately rather than
compared against it. **Two results and a choice made afterwards is the thing the seal exists to
prevent.**

**N_trials after A8, A9, A10, A11 and A12: 0.** Nothing here was selected by comparing outcomes,
computing P&L, ranking configurations or reading the holdout. The location-gate figures in A9 are
a **descriptive count of a filter's block rate**, not a test of whether removing it helps — that
question remains unasked and unanswered.

### A13 — 2026-08-08 — A8's σ threshold RESTATED, and the fixed-n form ABANDONED

**A8's feed decision stands unchanged.** Only its threshold clause is superseded.

**The criterion, restated as asked.** A NY VWAP σ band is cluster-eligible when the **95%
confidence interval on its distance from the mid is ≤ HALF the §3 cluster tolerance**:

> **z · σ̂ / √(2(n−1)) ≤ tol / 2**  —  i.e. **1.95996 · σ̂ / √(2(n−1)) ≤ 5.00 points**

This is tighter than A8's original wording (*"inside the 10-pt cluster tolerance"*), which
licensed n=20 and arguably n=10 and was therefore not a criterion at all.

**n = 30 DOES NOT FALL OUT OF IT.** Measured descriptively over 537 workbench sessions —
`research/star-trading/tools/` NY-σ census, no outcome touched:

| n | ET | median σ̂ | CI half-width at median σ̂ | ≤ 5.00? |
|---|---|---|---|---|
| 6 | 09:36 | 9.23 | **5.72** | no |
| 10 | 09:40 | 11.12 | 5.14 | no |
| 20 | 09:50 | 16.00 | 5.09 | no |
| **30** | **10:00** | **19.48** | **5.01** | **no — by 0.01** |
| **35** | **10:05** | 20.91 | **4.97** | **yes** |
| 50 | 10:20 | 24.69 | 4.89 | yes |
| 90 | 11:00 | 30.10 | 4.42 | yes |

**Recorded without softening: 30 fails, by 0.01 of a point.** The smallest n that satisfies the
criterion at the median is **35**. At the **p75** σ̂ it is **never satisfied** — not at n=90, not
anywhere in the measured range.

**And the fixed-n form is not merely mis-set. It is the wrong shape.**

> **The CI half-width is essentially FLAT in n: 5.72 at n=6, 5.01 at n=30, 4.42 at n=90.**
> It falls by 23% while n grows fifteen-fold.

The reason is structural. NY VWAP dispersion **grows through the session at almost exactly the
rate √(2(n−1)) shrinks the estimator's error**, because each new bar both adds an observation
and widens the price range the VWAP is dispersed over. **Waiting for more bars does not buy a
materially better band estimate in absolute points, so no waiting period fixes the problem A8
was written to fix.** A8's premise — that the band becomes trustworthy after enough
observations — is false as stated.

**Resolution: the criterion is evaluated LIVE, per instant, from that session's own σ̂.**

```
eligible(σ̂, n)  ⟺  1.95996 · σ̂ / √(2(n−1))  ≤  5.00
```

No waiting period, no clock time, **no fitted constant**: z is the 95% normal quantile and 5.00
is half of §3's stated tolerance. **On a quiet session the bands qualify early; on a violent one
they never qualify, which is the correct behaviour and is what a fixed n cannot express.**

**Free parameters: A8 added one (the 30). A13 removes it. Net effect of A8+A13 on the count:
zero.**

**Named honestly — the rule is mildly circular.** σ̂ appears on both sides: the estimate gates its
own admissibility. This is the same circularity as a t-statistic using the sample SD and is
accepted for the same reason, but it is a real property and is recorded rather than glossed.

**Why the fixed-30 form would have been actively harmful — the 10:00 ET coincidence.**
30 bars past the 09:30 anchor lands **exactly at 10:00 ET**, which is the conventional slot for a
cluster of US releases — ISM Manufacturing and Services PMI, JOLTS, Conference Board Consumer
Confidence, Michigan sentiment (prelim and final), new and existing home sales, factory orders.
*(The project holds no economic calendar — see out-of-scope branch 3 — so this is the
conventional schedule, not a verified list for any given date.)*

A fixed boundary at 10:00 would therefore have switched σ-band eligibility on **at the same
minute that realised volatility jumps on a large minority of sessions**, and:

1. **It confounds the Stage 5 release layer.** That layer asks whether release proximity predicts
   outcome. A rule that changes the *level set itself* at the modal release minute puts a
   detector-side discontinuity at exactly the covariate's discontinuity. Any release effect
   would be partly the eligibility switch, and the two are not separable after the fact.
2. **It makes σ̂ least reliable precisely where the rule declared it reliable.** The estimate is
   taken over 09:30–10:00, the pre-release drift window; the level it places is then used from
   10:00, into the release. **The estimation window and the application window sit on opposite
   sides of the volatility break.**

**The live rule removes both problems** — eligibility becomes a function of the session's own
dispersion rather than of the clock, so there is no fixed minute for a release to coincide with.

**Recorded for the Stage 5 pre-registration regardless:** if any future rule reintroduces a fixed
clock boundary, it must not be at 10:00, 08:30 or 14:00 ET, and the release layer must control
for it.

**P3 re-verified under both forms.** `2025-01-29 10:20` remains an admitted trade on 2m/3m/5m
under the fixed-30 rule and under the live rule, so the released instant is unaffected by this
amendment. Verified with `research/star-trading/tools/spec_current.py`; no outcome computed.

**Tag: [SPEC]** — the criterion is derived from §3's stated tolerance and a standard interval, not
chosen. **Supersedes A8's threshold clause only; A8's 1-minute feed decision is unchanged.**

**N_trials after A13: 0.** The σ̂ census is a descriptive measurement of an indicator's dispersion.
No trade outcome was examined and no value was selected by comparing results.

### A14 — 2026-08-08 — order-price tick rounding, direction fixed BEFORE any recompute

**Finding that forced this.** Invariant 9 of the Code-Path Verification Suite (`STATE.md`,
2026-08-08): of 1,472 admitted trades, **1,401 intended entries, 824 stops and 1,134 targets sit
off the 0.25 tick grid.** §5.3 makes the entry a 20-bar mean and no clause anywhere rounds a
price to a tradeable increment. Live, a stop or target at a non-existent price is rounded by the
broker in a direction nobody chose — an uncontrolled source of slippage this project has
otherwise gone to some length to make explicit (§4.2's next-bar-open fill, the front-run in
§6.4).

**Rule, stated once and applied uniformly — round every transmitted order price to the 0.25 grid
in the direction that makes the trade worse:**

| price | reference | direction | reason |
|---|---|---|---|
| **Stop** | entry | **away from entry** (long: floor down; short: ceil up) | widens the realised risk R for the same structural stop — conservative, since a wider R dilutes every R-multiple computed against it |
| **Target** | entry | **away from entry** (long: ceil up; short: floor down) | requires a larger favourable move to be counted as reached — conservative about what a live system would actually capture |
| **Entry** (E1, the resting limit) | — | **against the trader** (long: ceil up, i.e. pay more; short: floor down, i.e. receive less) | a resting limit order that cannot sit exactly on the level fills at the nearest price that is *no better* than intended, never at one that is better. This extends the same stated principle to the one price A2's rounding text does not name outright, and is flagged here as an extension rather than a literal quote |

**The direction was fixed and committed before any trade was recomputed.** Choosing it after
seeing its effect on the trade count or the R distribution would be choosing a number that
flatters the result, which is exactly the failure this amendment exists to close.

**The opposite convention — round toward entry / round in the trader's favour — is recorded as an
untested branch**, not evaluated, in `OUT-OF-SCOPE-BRANCHES.md`.

**Boundary case, stated so it is not left implicit:** a price already exactly on the 0.25 grid is
not moved. "Away from entry" and "against the trader" are directions applied only when rounding
is necessary; they are not a mandate to always move the price.

**Tag: [SPEC]** — closes a gap invariant 9 found; it is a completion, not a fix to code that
contradicted an existing clause. **Free-parameter count unchanged** — no threshold is introduced,
only a rounding convention with no tunable value.

**N_trials after A14: 0.** No value here was chosen by comparing outcomes; the direction is fixed
by a stated conservatism principle applied identically to every price, before computation.

### A15 — 2026-08-08 — §6.5, the ladder collapses rungs within one tick, formalising existing behaviour

**Finding that forced this.** 2a's test D5 (Code-Path Verification Suite, `STATE.md`,
2026-08-08) asserted that two menu levels 0.25 pt apart should walk the ladder as two distinct
rungs. It failed: `ladder()` collapses any level within one tick of the previously kept rung and
keeps the nearer one, and **no clause in §6.5 or A4 authorises that** — the text says only *"Walk
the ladder of opposing menu levels outward from entry."* D5's expectation had no spec clause
behind it and was reclassified `UNSPECIFIED IN SPEC`, along with D4, whose pass on the same
undocumented behaviour was equally uninformative.

**Rule, formalising what the code already does — when two menu levels fall within one tick of
each other, they collapse to a single rung, and the rung nearer to entry is kept.**

**Why "within one tick" and not some other bound.** Two menu levels 0.25 apart are not two
distinct order prices — NQ trades in 0.25 increments, so they are, for execution purposes, the
same level. Treating them as separate rungs would let the RR-floor walk (§6.5) count a
near-duplicate as a second, independent opportunity to clear the floor, which is not what
"outward from entry" describes.

**Why the nearer rung, not the further one.** The nearer rung is the one actually being traded
against — the same principle §10.1(4) level 4 already uses to break a tie between candidate
clusters ("Cluster nearest the entry price"). Keeping the further rung would let the ladder claim
a target beyond what the local cluster of levels actually justifies.

**The boundary, stated precisely, and CORRECTED — see the errata note below: "within" means a gap
of ≤ 1 tick (0.25 pt), inclusive, collapses to a single rung. Only a gap strictly greater than
one tick (> 0.25 pt) keeps two rungs separate.** Two levels **exactly** one tick apart therefore
**collapse to one rung**, the nearer of the two — verified directly against the code:
`ladder([120.0, 120.25], entry=105.0, "long", f=2.0)` returns `[118.0]`, a single rung, because
the existing `abs(x - out[-1]) > TICK` test is `>`, strict, and `0.25 > 0.25` is false. A gap of
0.275 (`ladder([120.0, 120.275], ...)`) does return two rungs, `[118.0, 118.275]`, confirming the
boundary sits exactly at one tick, inclusive.

**The alternative — never collapse, and walk every raw menu level as its own rung — is recorded
as an untested branch** in `OUT-OF-SCOPE-BRANCHES.md`, not run: it is a behaviour change to a
component (the target ladder) that a live trade record already depends on, and evaluating it now
would be comparing outcomes to choose a ladder rule.

**No code changes.** `ladder()` in `vwapbb_a7_selector.py` already implements this rule exactly;
A15 states in the specification what the implementation was silently already doing. **Tests D4
and D5 are rewritten under item 6** to assert this rule directly, rather than asserting nothing.

**Tag: [FIAT]** — a de-duplication convention with one bound (1 tick), which was already implicit
in the code and is not newly invented. **Free-parameter count unchanged.**

**N_trials after A15: 0.** No behaviour changed; a description was added for a rule that already
governed every admitted trade.

**ERRATA, 2026-08-08, disclosed rather than silently corrected.** A15 as first written contained
a sentence directly contradicting itself and the code: it stated the ≤1-tick rule as the operative
one and, one sentence later, claimed "two levels exactly one tick apart remain **two** distinct
rungs" — which is the *opposite* of ≤1-tick-inclusive and does not match `ladder()`'s actual
output. Caught while writing item 6's new test cases for the boundary, before any test was
written against the wrong version. **Corrected above; nothing about the rule itself changed, only
the sentence describing it.** No trade was ever computed under the wrong reading — no code
implements the erroneous sentence, only the spec's prose stated it backwards for a few hours.

### A16 — 2026-08-08 — §5.3/§5.5 operationalised: entry fills as a true limit order; PREREGISTRATION 4.2's next-open convention becomes a disclosed sensitivity, not a candidate

**Change.** The entry order described in §5.3 ("limit at [level]") and §5.5 ("No fill → no
chase... order cancels if price runs T_cancel points beyond entry without filling") is now
operationalised exactly as those clauses name it: a resting LIMIT order. **Fill rule:** the order
fills at the limit price, or better, if the one bar immediately following the signal bar's close
reaches it; if that bar's range never reaches the limit, there is no trade. `PREREGISTRATION.md`
4.2's "fills unconditionally at the next bar's open" convention — used throughout Stage 2 and the
discarded Stage 3 run — is retained **only** as a disclosed sensitivity: computed and reported
alongside the limit-order population for comparison, **never as a second candidate the pass marks
could select between.**

**Reason — pre-committed on the evidence already in the text, not on any result.**
1. §5.3's own words are the order type. Every one of the three tournament variants (E1/E2/E3)
   reads "limit at [level]" under a section header that is literally "Limit price." A price whose
   defining property is that it is a limit is, by construction, a limit order.
2. §5.5 corroborates it and only makes sense under it. "No fill → no chase. Order cancels if price
   runs T_cancel points beyond entry without filling" describes a resting order that CAN fail to
   fill — a market order cannot fail to fill, so a no-chase-cancel clause is meaningless unless
   the order it describes is a limit order. This is textual corroboration, not an inference from
   any measured behaviour.
3. The single-bar window is the only reading that does not invent a parameter. T_cancel has no
   stated value and is disabled everywhere in this project (`FILL-MECHANICS-QUOTES.md` §2). A
   limit order resting across more than one bar needs some stated duration; since none exists,
   the only window available without fabricating a number is the one bar the signal already
   designates as the earliest actionable bar (4.2's own bar, reused for its timing only, not its
   unconditional-fill rule).
4. Grounds are structural, not statistical. Nothing above cites a P&L, a win rate, or a comparison
   between the limit and market-at-open populations. The basis is what the spec's own words say an
   order IS, not which reading produces more, fewer, better, or worse trades.

**What changes operationally.**
- Fill: long fills iff the fill-window bar's low ≤ limit; short iff its high ≥ limit. Fill price =
  the limit, or the bar's open if the open itself already cleared the limit favourably
  (`min(open, limit)` long / `max(open, limit)` short).
- No fill → no trade. The signal is not retried on a later bar — §5.5's own no-chase clause
  already says the order cancels rather than persisting, and no later window is stated anywhere
  the spec could supply one from.
- Exit resolution (stop-vs-target) is unchanged. This amendment touches only how a trade enters,
  not how it is managed once filled.

**Market-at-open — retained, never a competing candidate.** `PREREGISTRATION.md` 4.2 already
discloses that its convention "departs from E1's stated limit-at-the-BB-MA" and is "worse than a
filled limit and better than nothing." That self-disclosed departure is preserved as a
documented, always-computed SENSITIVITY figure — reported next to the limit-order population in
every future report so the size of the divergence stays visible — but it is retired as a thing
the pass marks, or any future selection, could choose INSTEAD of the limit mechanism. Limit is
the pre-registered mechanism. Market-at-open is a disclosed comparison point, not an alternative
on the table.

**Grounds.** No outcome was computed, no P&L, no configuration compared by result. The decision
rests on what §5.3 and §5.5 already say an order is, and on which fill window can be built
without inventing an unstated parameter.

**Tag: [FIAT]**, resting on the order-type finding already made in `FILL-MECHANICS-QUOTES.md` and
the single-bar-window finding already used in `MINIMAL-FROZEN-SPEC-BUILD.md` /
`IMPLEMENTED-LEVELS-LIMIT-FILL-BUILD.md`. §5.3 and §5.5 stated no minimum rest duration and no
operationalised fill test; A16 supplies both, from the text alone.

**Consequences, recorded so they are not rediscovered later:**
- The discarded Stage 3 run (`STAGE3-DISCARDED.md`) was built under the market-at-open convention
  this amendment now demotes to a sensitivity. Its 65.2%-below-1.5R finding was the evidence that
  forced this amendment; A16 does not retroactively validate that run, which stays discarded and
  unopened.
- This is a change to the trader, not a patch: `admit_current` (`spec_current.py`) and
  `invariants_2b._admit` are both superseded by a new admission function under this amendment.
- Every admission list built from this point forward carries BOTH figures — limit-fill
  (canonical) and market-at-open (disclosed sensitivity) — as a matter of course.

**N_trials after A16: 1 of 5, unchanged.** No outcome was computed to arrive at this amendment.
