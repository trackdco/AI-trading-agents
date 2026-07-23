# Updated Plan — NQ Trading System (2026-07-23)

Consolidated plan + reconciliation of four open conflicts raised before commit.
Authoritative branch: **`claude/getting-started-6lwnvs`** (see reconciliation §A).
This doc summarizes state and sequencing; the strategy constitution remains
`strategy-definition-v1.2.md` and the live build spec remains
`docs/BUILD-PLAN-bot-phase4-5.md`.

---

## A. Branch reconciliation (RESOLVED)

**`claude/getting-started-6lwnvs` is canonical.** Verified by commit ancestry on
2026-07-23:

| Branch | Commits | Tip | Verdict |
|---|---|---|---|
| **`getting-started-6lwnvs`** | 406 | 2026-07-23 | **CANONICAL** — full engine + live + desk, strategy v1.2 |
| `sample-trade-candidate-json-znauze` | 12 | 2026-07-21 | **Superseded** — 402 commits behind canonical, 8 ahead of the shared fork; still on strategy **v1.0**, uses a stray `market-engine/` layout, has **no `src/live` or `src/desk`**. A stale parallel rebuild of just the Market Engine (the branch-sprawl pattern `context/TEAM.md` warns against). |
| `continue-previous-work-emsc7d` | 379 | 2026-07-22 | **Superseded** — fully contained in canonical (canonical +27 ahead, it 0 ahead). |
| `brake-43x58e` | 52 | 2026-07-22 | **Not canonical, but holds 48 unique data-lane commits** (heatmap / CVD / trend-pullback). Reconcile its DATA into canonical; it does not supersede code. |

**Actions:** treat `znauze` and `continue-previous-work` as closed. Merge Brake's
unique data commits from `brake-43x58e` into canonical (data lane only).

---

## B. Where things stand — three parallel tracks

**Track A — Engine & Backtester (Spec 1).** Steps 1–7 built and tested; strategy
locked at **v1.2**; Step 4 parity gate **PASSED** (Angus, on NQH2026). Remaining:
Step 8 calibration + Step 9 diagnostics. Work has largely moved into *edge
refinement* (see §D).

**Track B — Champion live paper bot (`BUILD-PLAN` Stages 0–9).** Stages 2–7 built;
**Stage 7 parity PASSED** (40 days reconcile to zero diff vs backtest); journaling
done; `src/live/runner.py` fully assembled
(`feed → detector → Vault → risk guard → broker → journal → Telegram`, restart-safe,
kill-switch, strategy-swap seam). **Stage 8 (live paper) in progress, blocked on one
thing: the live data feed** (vendor decision + key — see §C.2).

**Track C — The Desk (third-party Hermes + 4 specialists).** Skill docs for
Atlas/Helios/Apollo/Hephaestus + the Hermes coordinator are written and ready to
paste into the third-party Hermes product. The Python trust boundary
(`src/desk/receiver.py` + `verdict.py`) is built and tested: it re-checks Hermes's
arithmetic, risk-gates via the **same RiskGuard** as the champion, and journals via
the **same LiveJournal**. Blocked on: (1) ~28 Angus rulings (start subset
I-4 → E-3 → E-11; Q-5 already resolved by v1.2), and (2) two engineering gaps
(see §E).

---

## C. The four reconciled conflicts

### C.1 Canonical branch — see §A. RESOLVED: `getting-started-6lwnvs`.

### C.2 Live data feed vendor (Track B)
- The feed is a **swappable adapter** behind a `BarFeed` Protocol (`src/live/feed.py`):
  one `stream()` method yielding closed `Bar`s in the engine's exact OHLCV schema.
  Track B code adapts to any vendor with no Vault change.
- **Databento historical stays** — already purchased and parity-gated; no reversal.
- **TradingView cannot serve as the bot's data feed** — it is a charting platform
  with no licensed programmatic OHLCV stream; its webhooks are event triggers, not a
  continuous bar feed. TradingView's role remains: VWAP/BB *formula reference* and
  *human parity charts*, never the bot's data source.
- **Broker-native feed is viable** — Tradovate or Topstep can provide the live feed
  **and** execution over one connection, which would replace Databento-*live* and
  collapse this decision into the broker choice (§C.4).
- **Hard requirement:** any live vendor must emit bars identical in shape to the
  Databento historical bars (continuous front-month NQ, 18:00-ET session boundary,
  same aggregation). A **feed-parity check** (replay one day from the new vendor vs
  Databento) is mandatory before trusting it.

**Decision:** keep Databento for historical/backtest; for the live feed, go
broker-native (aligns with §C.4) or Databento-live — either is a new `BarFeed`
implementation + parity check. TradingView is not a candidate for this slot.

### C.3 Desk agents — 4 specialists + Hermes coordinator (NOT 7)
- Authoritative Desk = **Atlas / Helios / Apollo / Hephaestus (4 specialists) +
  Hermes (mechanical unanimity coordinator)**. Source of truth:
  `docs/desk-skills/*.md` (adversarially reviewed, 44 findings resolved;
  `<<PLACEHOLDER>>`s mark pending Angus rulings). `docs/agent-blueprint-design/`
  has 5 role JSONs; `coverage.json`/`runtime.json` are specs, not agents.
- The **7-agent marketing-spec build is off-spec** and should be rebuilt to the 4 +
  coordinator. Core rules a marketing build likely violates: each specialist carries
  a **verbatim rulebook slice** (never a paraphrase); Hermes has **zero market
  opinion** — it slices payloads, collects four verdicts, ANDs them, and emits one
  JSON verdict with no outbound actions.
- **Do not confuse tracks:** `.claude/agents/{htf-structure, regime-context-*}` are a
  **separate regime/HTF subsystem** (Pat's regime-context agent), not Desk
  specialists.

**Decision:** rebuild the Hermes skills from `docs/desk-skills/*.md` to the real
4-specialist + coordinator spec. Map any of the 7 that correspond to regime/HTF into
that separate track; drop the rest.

### C.4 Execution broker — Tradovate vs Topstep (OPEN — business decision)
- Not a code decision; it is **prop-eval vs self-funded capital**:
  - **Topstep (TopstepX / ProjectX API)** — prop-firm evaluation → funded account
    (trade their capital). The strategy docs' Monte Carlo plan targets a **prop eval**
    (50K eval, 3K target / 2K trailing DD, "firm selection" as an MC output), which
    aligns with this route.
  - **Tradovate** — retail futures broker, self-funded (own capital), documented API.
- The repo's eval-simulation economics **lean toward prop/Topstep**, but the choice is
  Angus/Pat's. Not needed until go-live (`BUILD-PLAN`: "pick before go-live so the
  paper_broker interface matches it").

**Status:** OPEN. Recorded lean = Topstep (per economics); to be ruled by Angus/Pat
before Stage 9. Whichever is chosen may double as the live feed (§C.2).

---

## D. Strategic reality — the north star

The champion is **2026-calibrated and loses out-of-sample 2023–25**. Angus's reframe:
**optimize for SELECTIVITY (win rate), not total P&L** — the bot takes too many
mediocre trades (32–42% win) vs Angus's live 50%+ on 1–2 trades/night. Proposed edge
closers: **rank-and-take-best-2** (not first-2) and **CVD as a conviction filter**.
Open question that gates any real-money conversation: does the champion have a
cross-regime edge, or is it fundamentally 2026-fit?

---

## E. Key architectural insight — Tracks B and C share one live infrastructure

The Hermes coordinator doc flags two missing Desk pieces; both are ~90% covered by
the champion's already-built live stack:

1. *"Produce a live (snapshot, trigger) pair each candle and hand it to Hermes"* —
   the champion's `src/live/detector.py` already streams the real `detect_triggers`
   per closed bar (Stage 8), and `build_snapshot` exists. Reuse it.
2. *"Manage the approved position fill→exit"* — the champion's `runner.py` +
   `paper_broker.py` already do this. Route `receiver.on_approved` into that broker/
   position manager instead of building a second one.

So the Desk is **the champion live loop with Hermes swapped in at the decision seam**
(`strategy_gate` composes *under* the risk guard in `runner.py`), bridged by the
receiver. **Build Track B first; Track C reuses it.**

---

## F. Recommended sequencing

**Now / unblocked (no Angus dependency):**
1. Track A edge work (from `HANDOFF-next-session.md`, in order): re-detect the trigger
   cache with the E-2 fix → re-grade 2023–2026 (confirm E-2 closes the long/short gap;
   revert cash-open / 10pt-stop if they fail OOS) → run the powered CVD test
   (build-a-real-edge-or-bin-it verdict).
2. Track A finish Spec 1: Step 8 calibration (apply the TV-open-label →
   engine-close-label +TF shift in the matcher) + Step 9 diagnostics.
3. Reconcile Brake's data-lane commits (`brake-43x58e`) into canonical.

**Fast path to a watchable bot (Track B):**
4. Decide the live feed vendor (§C.2 / §C.4) and provide the key; regenerate the
   leaked Telegram token. That single unblock finishes Stage 8 live paper on the
   champion.

**Track C, as rulings land:**
5. Angus works the rulings packet (`docs/FOR-ANGUS-desk-spec-questions.md`); Pat builds
   the agent-file slots now with `<<PLACEHOLDER>>`s, and **rebuilds the Hermes skills to
   the real 4-specialist + coordinator spec** (§C.3).
6. Consolidate the Desk onto the champion's live infra (§E); run the shadow ledger
   (`docs/agent-blueprint.md` §6.6) — Hermes grades live candidates in shadow vs the
   mechanical engine's outcomes, no execution.
7. Fold rulings into a pinned Spec-3, then write the real `.claude/agents/*.md` files
   (verbatim rulebook slices).

**Gated — real money (Stage 9):** only after the strategy shows a cross-regime edge
(not just 2026-fit) AND paper/shadow is clean. Live auto-accept permanently disabled.
Pick the execution broker (§C.4) before go-live so the `paper_broker` interface matches.

---

## G. Open decisions

- **Pat:** live feed vendor + key (§C.2); Telegram token regen. Unblocks Stage 8.
- **Angus:** the ~28 Desk rulings (`FOR-ANGUS-desk-spec-questions.md`); PCE/news P5.14.
- **Angus/Pat:** execution broker — Tradovate vs Topstep (§C.4). Lean = Topstep.
- **Team:** does the champion have a cross-regime edge, or is it 2026-fit? (§D — the
  CVD test + 2023–26 re-grade answer this.)
- **Pat:** rebuild the tonight-built 7-agent Hermes to the real 4 + coordinator (§C.3).
