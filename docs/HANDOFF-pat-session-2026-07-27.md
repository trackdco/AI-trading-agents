# HANDOFF — Pat's session, 2026-07-27 (read this first, then work)

**Who you are working with:** Pat — builds the engine/agents and runs the VPS/Sierra box.
Angus is strategy authority (rulings only he can make); Brake handles data. This file was
written by the prior session mid-launch so a fresh chat can continue without losing state.

**Your immediate task (Angus's words):** "run the 2023/2024 out of regime random days test
thing" — an out-of-regime robustness check of the canon on 2023/2024 days. Details in §3.

---

## 1. WHERE THE LAUNCH STANDS (do not disturb this from a research session)

The system goes LIVE on the funded account at the NY session TODAY (pre-market 08:00 ET)
if the remaining human steps land. As of commit `7a0b6b7`:

- **Arming reference:** `output/baseline_book_news.parquet` = **+$55,989.81 / 383 trades**
  (leakage-clean + news blackout + 09:55–10:00 dead zone). Certified on the box twice
  tonight: 383/383 exact, P&L to the cent. London +$21,506/136 inside it.
- **Gates GREEN, all verified on-box tonight:** A7/B7/B8 (order surface vs live Rithmic
  paper — "✓ all checks passed"), C4 (both operators' /kill), C5 (spine forcetest 11/11),
  B6 (feed lag median 2.79s), cert (A1/A2). Runner is up DISARMED shadowing London
  (03:00–05:50 ET); kill listener runs as its own process.
- **Remaining before arming:** C2/C3 drills after the London window (~05:50 ET), final
  cert re-run at the FINAL commit, Pat's written confirmation (gates checked against
  artifacts, 383 number + commit SHA named), Angus's passphrase → `canon_run --arm`.
- **Arming mechanics:** `src/live/arming.py` + `canon_run --arm`. Angus sends the phrase
  to HIS Claude session, which commits `config/arming.yaml` (phrase HASH + certified SHA +
  funded account). The provenance check refuses to arm if ANY file other than arming.yaml
  differs from the certified commit — **so do not push code tonight unless it is meant to
  force a re-certification.** Research outputs/docs are fine; trade-path code is not.

**Eight real bugs were found and fixed on the box tonight** (each has a commit + test):
wrong DTC OrderStatus enum; Sierra's present-but-null fields; order prices needing the
box's 100× service scale (`dtc.price_scale`); Sierra attach semantics unusable → bracket
contract v4 (independent pair, geometric safety + reject pairing); scid resolver following
the freshest naming variant (`NQU6.CME.scid`); kill-listener long-poll timeout; stale-
verdict guard (boot catch-up would have re-emitted months-old signals — ARMED, those reach
the broker; now anything older than 120s vs wall clock is journaled and skipped); Windows
console emoji logging. **Read these diffs before writing the confirmation:** `ec31848`,
`c938b10`, `7fb2304`, `245dc06`, `6e264c5`, `3300270`, `7a0b6b7`.

## 2. STANDING RULES (non-negotiable, from Angus)

- **Mechanical only** (docs/RULING-mechanical-only.md): no agent discretion in the trade
  path, no LLM verdicts. Frozen constants change only via freeze → two-way OOS → Angus
  sign-off → new certified book.
- **Branch discipline:** develop/commit/push ONLY `claude/getting-started-6lwnvs`. No PRs.
- **Raw market data never goes to GitHub** — condensed artifacts only.
- **§E (PROMOTION-GATE):** any change to canon/sizer/spine/relay = stop-and-review + full
  re-certification. Applies from tonight onward with real money attached.
- Angus's standing preferences: consistency (months green) over total P&L; findings must
  survive adversarial verification on disjoint substrates before he sees them as verdicts
  (the rr-1.5 retraction is the cautionary tale — docs/FINDING-rr-floor-study.md).

## 3. THE TASK: 2023/2024 OUT-OF-REGIME RANDOM-DAYS TEST

**Goal:** measure whether the canon's mechanical rulebook holds up on days OUTSIDE the
2025–2026 regime it was built in — random-sampled days from 2023/2024, scored exactly as
live would score them, no refits, no new knobs.

**What already exists (start here, don't rebuild):**
- `docs/LONG-WALK-2023-2026.md` — the full-history run: champion v1.1 OOS by year,
  analog rerun, oracle by year. Its conclusion frames expectations for regime drift.
- Trigger caches for 2023–2026 were re-detected with the E-2 fix (see the re-grade in
  `docs/REVIEW-stage2-vault.md` / `ENGINE-RESPONSE-*` and the long-walk doc).
- `scripts/canon_mechanical.py` — THE canon scorer (`build_canon(T, news_gate=None,
  dead_zones=None)`); `scripts/canon_news_clean.py` shows the full corrected construction.
  The scorer consumes the engine's trade_matrix (candidate fills + features), so the
  2023/24 days must run through the same detection → candidate pipeline first.
- `scripts/golden_deep_oos.py` — the two-way OOS harness pattern (derive/apply, per-fold),
  useful as the template for honest sampling and reporting.
- News gate: `config/news_calendar_hist.csv` starts later than 2023 — check coverage for
  sampled days; a day without calendar coverage must FAIL CLOSED for pre-9:30 NY entries
  (NewsGate.is_stale semantics), or be reported as uncovered. Do not silently assume
  "no news" in 2023/24.

**Design guardrails:**
- Random days, pre-registered before scoring (journal the sampled dates first, then run) —
  no peeking, no resampling until the story looks good.
- Report per-year and per-book (NY windows / London), floor-R units ($200 = 1R), months-
  green framing alongside totals — Angus reads consistency first.
- Expect and REPORT degradation honestly if it's there. The long-walk already showed the
  oracle doesn't generalize (docs/FINDING-oracle-is-hindsight-books-dont-generalize.md);
  the question is whether the CANON RULEBOOK (not the oracle) carries.
- Nothing from this test changes live behavior without the full §2 pipeline.

## 4. KEY FILES MAP

- `docs/PROMOTION-GATE.md` — the arming gate (authoritative). `docs/STATUS-go-live-
  checklist.md` — plain-language state. `docs/GO-NOGO-2026-07-27.md` — tonight's order.
- `docs/CANON-MECHANICAL.md`, `docs/GOLDEN-WINDOW-DISSECTION.md`, `docs/HEADLINE-NUMBERS.md`
- Live stack: `scripts/canon_run.py` (runner; `--arm` path), `src/live/route_b.py` (loop;
  stale-verdict guard), `src/canon/spine.py` (Tier-1 pins: −4R daily indexed, DD ramp
  $1,500→$0 at $100 with $100 hard halt, clamp 40 micros), `src/desk/dtc_broker.py`
  (price_scale, bracket v4, pairing), `src/canon/premarket_guard.py` (corrections 2+3
  live), `scripts/kill_listener.py` (own process, always running).
- Box facts: symbol `NQU6.CME` (data) / `MNQU6.CME` (orders), price_scale 100, paper
  account `LFE050-9YSC047M-TEST001`, DTC 127.0.0.1:11099 (Allow Trading = Yes, Trade
  Simulation Mode = OFF), forcetest needs `--price-scale 100`.

## 5. HOW THIS TEAM WORKS WITH CLAUDE

Screenshots of the box/terminal drive the loop; Claude reads them, fixes, pushes; the box
pulls. Every fix ships with a test and lands as its own commit with the on-box finding in
the message. Full suite green (656 as of `7a0b6b7`) before every push. When something
looks wrong on the box, get the RAW evidence (Trade Service Log, Message Log, raw server
state) before theorizing — tonight's bugs were all solved by reading what the server
actually said.
