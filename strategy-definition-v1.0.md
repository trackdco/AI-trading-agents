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
- Location: no longs at HTF range top / shorts at range bottom.
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
