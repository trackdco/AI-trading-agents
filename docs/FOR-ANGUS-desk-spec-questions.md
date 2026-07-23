# FOR ANGUS — Desk build: rulings needed before any agent file gets written

**Decision needed from you (strategy authority) before Pat/Claude Code write a single
line of the Desk (Atlas/Helios/Apollo/Hephaestus/Hermes).**

**Update (19 Jul, after this packet was first sent):** the Desk skill docs were built
against the original blueprint's v1.0 assumptions, then discovered to be stale — the
LOCKED, current strategy is `strategy-definition-v1.2.md`, which already resolves
several items below via your 17 Jul calibration rulings. Marked ✅ RESOLVED BY v1.2
inline; everything else is still genuinely open.

## Why this exists

Pat wants to start building the Desk. The design (`docs/agent-blueprint.md` +
`docs/agent-blueprint-design/*.json`) is thorough and already survived a 4-lens
adversarial review (44 findings, all resolved) — but it explicitly stops short of
being buildable: it names ~28 trading-rulebook questions only you can answer, and
found 12 places where the engine's actual behavior disagrees with your strategy
doc. Writing an agent file before these are settled means Claude Code guessing at
your rulebook — exactly what this whole design exists to prevent ("when the doc
and the engine disagree, neither is silently fixed — the divergence goes to you").

Full detail on every item below is in `docs/agent-blueprint.md` §8–9. This doc is
the short version so you can rule quickly; ping back if any item needs the longer
context.

## ⛔ Blocking the Hermes rebuild right now — these ten, in one place (23 Jul)

The live Hermes host currently runs an OLDER 7-agent desk (atlas, lumen, hydra,
hermes-execution, apollo, hephaestus, mnemosyne + desk-coordinator). Replacing
it with the v1.2 four-specialist desk is on hold until these ten are ruled on.
Nothing has been deleted or overwritten; the live skills and their content are
backed up.

**Unresolved placeholders sitting in rule logic** (the skill docs literally
contain `<<PLACEHOLDER>>` at these points — they cannot ship as-is):

| # | Where | Question |
|---|---|---|
| Q-7 | `apollo-skill.md:136` | which VWAP is the "opposing ±1σ" |
| Q-9 | `hephaestus-skill.md:81` | stop AT vs. BEYOND the wick extreme |
| Q-11 | `hephaestus-skill.md:104` | correct definition of an "untaken" extreme |
| Q-23 | `apollo-skill.md:105` | is counter-trend alone a valid pattern-A route |
| Q-26 | `atlas-skill.md:125` | does the §7 location veto apply in every regime |

**Coverage gaps from collapsing 7 agents into 4** (new — see section D):

| # | Check being lost | From |
|---|---|---|
| Q-29 | risk-tone vs. direction agreement | `lumen` |
| Q-30 | entry must come AFTER the liquidity sweep | `hydra` |
| Q-31 | spread / fill-quality gating | `hermes-execution` |
| Q-32 | setup must match a documented playbook entry | `mnemosyne` |
| Q-33 | forward-looking news buffer — configured but unenforced | `helios` |

**Why Q-29..Q-33 matter more than "we dropped some checks":** Q-30, Q-31 and
Q-33 are all *vetoes* — they currently STOP trades. Dropping them makes the desk
**looser**, not tighter, and it happens silently. Q-33 is the sharpest: Helios
already accepts `filters.news_entry_buffer_enabled` / `news_entry_buffer_min` in
its config block, so the buffer *looks* implemented, but no check consumes them.

## Recommended starting subset (if you want to unblock the most with the least)

These four block an entire agent's checks from running AT ALL, so ruling these
first lets Pat start on partial agent files while the rest gets worked through:

- **I-4** (§4.2) — the engine must compute a `ProposedConstruction` (entry/stop/
  target/size) BEFORE Hephaestus runs; agents validate prices, they never invent
  them. Nothing about Hephaestus works without this existing. Pure engineering
  ask, but needs your sign-off that "engine proposes, Hephaestus validates" is the
  right shape (vs. some other split).
- **E-3** (§8) — displacement triggers currently get a hard-coded, made-up
  confluence count (`2`) instead of a real one. Feeds sizing AND the location
  checks with a fake number today, in the backtest too, not just the Desk.
- **E-11** (§8) — **still open, but the rule itself is now v1.2's**: the §7
  confluence minimum isn't enforced ANYWHERE in the current engine/backtest path.
  What "isn't enforced" now means the v1.2 BB+VWAP-both-present rule (see Q-2/Q-3
  below), not the old 3-vs-2 split. Still a calibration-validity issue for numbers
  already graded against, not just a Desk blocker.
- ~~**Q-5** (§9) — half-trigger thresholds~~ **✅ RESOLVED BY v1.2**: oversized
  stop > 42 pts, late-window entry after 10:30 ET (session-scoped windows only —
  W2 has no time-based sizing). "Thin target" as a half-trigger no longer exists —
  v1.2 deleted it; below the 2.0R floor is a SKIP, not a half-size trade. See
  `strategy-definition-v1.2.md` §9 and `config/strategy.yaml` `sizing:`.

## A. Engine findings — doc vs. code disagree, which wins? (§8, E-1..E-12)

For each: does the strategy doc win (→ engine gets fixed) or was the engine
behavior intended (→ doc gets amended)? One-line answer is enough per item.

| # | The disagreement |
|---|---|
| E-1 | Engine emits ALL VWAP bands (±1/2/3σ) as candidate levels; doc says mid/±1σ only |
| E-2 | Unknown HTF regime silently defaults shorts to "with_trend" (lenient minimum), longs to "counter_trend" |
| E-3 | Displacement triggers hard-code confluence_count=2, cluster=None — a made-up number feeding §7/§9 |
| E-4 | Displacement entry_ref uses the FIRST level penetrated; doc says nearest-to-close (opposite for longs) |
| E-5 | Over-extension check looks at both sides of a candle, including the side away from the trade |
| E-6 | A range-regime rejection with no over-extension still gets labeled pattern A; doc says A requires it |
| E-7 | Displacement counts penetrations of ANY level; doc requires ≥2 levels that form a real cluster |
| E-8 | Stop placed AT the wick extreme; doc says BEYOND it — needs a ruling + a buffer-ticks config value |
| E-9 | `data_levels` (event-day price extremes) has no retention bound — stale months leak into today's menu |
| E-10 | `cluster.min_level_types` exists in config but the engine hard-codes `2` — changing the config does nothing |
| E-11 | **(urgent, not Desk-only)** The §7 confluence minimum isn't enforced anywhere in engine/backtest |
| E-12 | 1-minute timestamps are labeled inconsistently (start vs close) between two engine modules |

## B. Trading-rulebook questions (§9, Q-1..Q-13, Q-23..Q-28)

- ~~**Q-2:** does a structural level add +1 to confluence count?~~
  **✅ RESOLVED BY v1.2**: no. Structural levels are target/context weight only,
  never entry-minimum credit (§3). The entry gate is just "BB present AND VWAP
  present" — POC and structural are bonus, never required.
- ~~**Q-3:** confluence minimum when HTF regime is "range"?~~ **✅ RESOLVED BY
  v1.2**: moot — the same BB+VWAP-present rule applies to every trade regardless
  of regime, counter-trend included. No regime-based split exists anymore.
- **Q-4:** cluster tolerance — adjacent-gap or full-cluster-span? (still open —
  v1.2 didn't touch this)
- **Q-6:** does a candle closing exactly at a window boundary (e.g. 11:00) count
  as in or out?
- **Q-7:** §7's "opposing ±1σ" invalidation — NY VWAP or daily VWAP?
- **Q-8:** pattern-A default target "VWAP middle" — NY mid when available, else
  daily mid?
- **Q-9:** stop at vs. beyond the wick extreme (pairs with E-8), and which way to
  round to the tick? (v1.2 added a separate NEW rule — minimum stop 10pts, skip
  below it — but did not resolve this at-vs-beyond question)
- ~~**Q-10:** RR-floor basis — raw target level or front-run-adjusted?~~
  **✅ RESOLVED BY v1.2**: the raw `target_level`. Front-run points are execution
  mechanics only for fills and never enter the R calculation. RR floor is also
  now a hard 2.0R, not a CALIBRATE placeholder.
- **Q-11:** "untaken" data extreme — best computable definition (design's proxy
  vs. a proper engine-stamped `swept` flag, I-9)?
- **Q-12:** an unknown news-day status under an active override — note only, size
  downgrade, or veto?
- **Q-13:** ratify or amend the A/B grade mapping (simplified under v1.2 — no
  finer tier below "half" exists anymore, so grade C was dropped), the veto
  field-nullability convention, and "target = working_target" terminology
  (renamed `target_level` vs `target` in the skill docs to avoid the ambiguity
  Q-10's resolution exposed).
- **Q-23:** is counter-trend alone (no over-extension, no range extreme) a valid
  pattern-A route? Doc text says no, engine behavior says yes.
- **Q-24:** no premarket session box currently exists for the §6.2 "pre-market
  extreme" rule — define the clock, or bless a stand-in?
- **Q-25:** which target-menu types count as "structural" for the B2 default —
  structural only, or does POC/VAH/VAL qualify?
- **Q-26:** (flagged as needing your eyes specifically) does the §7 location veto
  apply in every regime or range-only? As designed it systematically vetoes good
  with-trend entries near session/prior-day highs — worth a careful look.
- **Q-27:** is a still-forming event-day price extreme eligible as a target, or
  only once its window closes?
- **Q-28:** on a displacement trade, is "50% of the wick" the trigger candle's
  actual wick, or the origin-to-body-edge zone?

## C. Engineering decisions (§9, Q-14..Q-22) — Pat/Claude Code judgment calls, FYI only

Listed for visibility, not asking for your ruling — these are build-process
choices (retry policy, config file layout, runner concurrency, etc.), except:
**Q-16** (which engine additions land before vs. during the Desk build) and
**Q-20** (should specialists see the engine's computed answers as a cross-check,
or re-derive fully blind) touch strategy intent enough that your preference
would help.

## D. Coverage gaps from the 7→4 desk consolidation (Q-29..Q-33) — NEW, 23 Jul

Context: the live Hermes desk has 7 specialists. The v1.2 design has 4. Reading
the live skills' actual content (not just their names) against the four new
skill docs, most checks do carry over — several more rigorously. These five do
not. **Each needs a ruling: fold it into one of the four, accept the loss
deliberately, or keep it somewhere else.** The default if you say nothing is
that they silently disappear, which is what this section exists to prevent.

For completeness, what DOES carry over cleanly (no ruling needed):
`lumen.RIGHT_SESSION` → Helios 1+2 (wrap-aware, independently recomputed);
`hermes-execution.VALID_TRIGGER` → Apollo 3/4/5; `hermes-execution.ENTRY_IS_EXACT`
→ Apollo 7/8 + Hephaestus's entry construction; `hydra.CLEAR_DRAW_TO_TARGET` →
Atlas 8 + Hephaestus's "nearest opposing-liquidity level" target rule.

And two that are relocated rather than lost — **please confirm this is intended**:
`mnemosyne.HAS_HISTORICAL_EDGE` and `mnemosyne.NOT_REVENGE_OR_FOMO` read
`setup_historical_performance` and `recent_trade_history`, which are exactly two
of the four fields `vault-injector` injects AFTER the Desk runs. All four new
specialists explicitly state "you never see account state, P&L, prior trades,
open positions" — so account-state judgment appears to have moved out of the
Desk and into Python as the trust boundary. That looks deliberate. The open part
is whether the *checks* move with the *fields*, since vault-injector is still a
stub — if nobody implements them downstream, they're gone too.

- **Q-29:** `lumen.RISK_TONE_AGREES` — the live desk fails a trade whose
  direction disagrees with broad risk tone (long needs risk-on/neutral, short
  needs risk-off/neutral). Nothing in the four new docs mentions risk tone at
  all, and Helios structurally cannot own it — it never sees prices by design
  (`data_high`/`data_low` are excluded from its allowlist on purpose). Does
  macro risk tone still gate trades, and if so whose lane is it?
- **Q-30:** `hydra.ENTRY_AFTER_GRAB` + `POOL_SWEPT` — the live desk requires a
  specific identified liquidity pool to have been swept, and requires entry to
  come strictly AFTER the sweep ("entering before or during the sweep fails
  this check regardless of any other factor"). The *target* half of Hydra
  survives via the target menu, but this **sequencing veto has no equivalent**
  anywhere in the new four. Is sweep-then-enter still required?
- **Q-31:** `hermes-execution.SPREAD_FILL_ACCEPTABLE` — the live desk gates on
  spread against a defined maximum plus fill-quality indicators. The word
  "spread" does not appear in any of the five new docs. Does execution-quality
  gating leave the Desk entirely (e.g. become Python's job at fill time), or
  should Hephaestus own it alongside sizing?
- **Q-32:** `mnemosyne.IN_PLAYBOOK` — requires the setup to match a named,
  documented playbook entry, failing novel/improvised setups. Unlike its two
  siblings above, `playbook_match` is NOT among vault-injector's four injected
  fields, so it isn't relocated downstream either — it has no home at all. Is
  "must be in the playbook" still a gate, and if so where does it live?
- **Q-33:** Helios's news buffer is configured but unenforced. Helios's config
  block accepts `filters.news_entry_buffer_enabled` and
  `filters.news_entry_buffer_min`, but **no check consumes them**. Its only
  news vetoes are check 6 (`news_day_classification`) and check 7
  (`high_impact_preopen_standdown`), and check 7 fires only for high-impact
  events scheduled **before 09:30 ET**. So the live desk's forward-looking rule
  — `lumen.NO_IMMINENT_NEWS`, "any high-impact release within the next 60
  minutes fails" — is gone: a 14:00 ET release triggers no stand-down at all
  under the new four. Should the buffer become a real Helios check (and at what
  minutes), or is the pre-09:30 stand-down deliberately the whole news rule now?

## Where the build actually stands now

Pat asked for the build to start in parallel rather than wait — the four
specialist skill docs (`docs/desk-skills/{atlas,helios,apollo,hephaestus}-skill.md`)
and the Hermes coordinator instructions (`docs/desk-skills/hermes-coordinator.md`)
are written, along with the Python receiver (`src/desk/verdict.py`,
`src/desk/receiver.py`, tested) that risk-gates and journals whatever Hermes
decides. Every item this packet marks ✅ RESOLVED is already built into those
docs correctly.

**Updated 23 Jul — they are NOT ready to paste yet, for two different reasons:**

1. Q-7/9/11/23/26 are marked `<<PLACEHOLDER: ...>>` inline in the relevant skill
   doc. Those genuinely are a find-and-replace once you rule — no rebuild needed.
2. Q-29..Q-33 (section D) are NOT placeholders and NOT find-and-replace. They
   are checks the live 7-agent desk enforces today that have no home in the new
   four. Each needs a design decision — fold in, drop deliberately, or house
   elsewhere — before the swap, not after.

Also discovered on 23 Jul: the live Hermes host is **already running a working
7-agent desk** (atlas, lumen, hydra, hermes-execution, apollo, hephaestus,
mnemosyne, plus a `desk-coordinator` that orchestrates them). It predates v1.2 —
none of its skills reference the BB+VWAP confluence rule or the 2.0R floor — but
it is real, used (6–8 invocations each), and carries operational knowledge the
new docs did not: the coordinator's `delegate_task` concurrency-cap batching,
which has since been folded into `hermes-coordinator.md` step 3a so it survives
the swap. Nothing has been deleted or overwritten. When the swap does happen the
plan is update-in-place for atlas/apollo/hephaestus rather than delete-and-
recreate, so usage history is preserved and the desk is never half-built.

## What happens after your rulings land

Per the design doc's own sequence: your answers get folded into a pinned Spec-3,
THEN Pat/Claude Code write the actual `.claude/agents/{atlas,helios,apollo,
hephaestus,hermes}.md` files (each carrying a verbatim slice of your rulebook,
never Claude's paraphrase of it) plus `src/desk/runner.py` and the named test
suite (§6.7). Nothing about the champion bot or your regime-agent work changes —
the Desk is a separate, later live-trading path, not a replacement for either.

## RULING (Angus, 28 Jul — via Claude session; supersedes the frame of this packet)

**META-RULING — read this first, it answers most of the packet.** The v1.2 strategy
definition and the 4-specialist judgment desk it implies are SUPERSEDED. The strategy
is now THE CANON: three mechanically-derived books — pre-market + golden window
(`scripts/canon_mechanical.py`) and London (`scripts/london_canon.py`) — validated at
~+$106k/2yr combined, 12/13 green months. Every check, threshold, score, and size is
frozen deterministic code. **There is no LLM judgment anywhere in the trade path.**
Agent intervention risks degrading performance (proven three times: chop-agent
overdiagnosis, and the veto trap in all three windows). The agents' whole job:

1. **Session routing (Hermes):** know what time it is and which rulebook applies —
   London open → London canon; 04:00 ET → pre-market book; 09:45 ET → golden book.
   That's the "what am I sticking to" question and it's a lookup, not a judgment.
2. **Mechanical execution:** the ENGINE computes the canon verdict (checks, score,
   OF stack, size). Agents relay and execute it. They never validate prices, never
   re-derive setups, never veto beyond the canon's own rules. What validates a trade =
   the canon checks. What dictates size = the canon ladder. Enter or not = score/gates.
3. **JOURNALING (the new mandate — build this properly):** every trade the desk takes
   gets a comprehensive journal record: session/book, every check bit AND its raw
   value, score, OF confirmations, full size-multiplier path, fill/exit/exit_reason,
   MAE/MFE, in-trade marks (r_3/r_5, flow), ambient context (news calendar state,
   DST group, spread at fill, sweep state), engine version + threshold hash. Purpose:
   accumulate live data so recalibration and future upgrades run on evidence. This
   absorbs Mnemosyne. Journal EVERYTHING, gate NOTHING new.

**Engine-vs-doc conflicts (all of section A): the engine as-it-ran WINS, docs amend.**
The canon's +$106k was validated on this engine's actual behavior, warts included.
Changing engine behavior now (E-1, E-4, E-5, E-6, E-7, E-8 stop-AT-wick, E-10)
invalidates the calibration. Freeze behavior; amend docs to match. Exceptions:
E-9 (add a retention bound — pure hygiene), E-12 (fix timestamp labeling — pure
correctness; canon pipelines already normalize). E-3/E-11 are MOOT: the canon's
window-native scores replaced the §7 confluence system entirely.

**Priority three:**
- **Q-30 (sweep-then-enter veto): DROP, deliberately.** Never part of the validated
  canon; every unvalidated veto we tested in three windows was EV-negative inside the
  sized book. Journal sweep state per trade so it can be tested on live data later.
- **Q-31 (spread/fill-quality): moves to Python at order time, not an agent check.**
  A mechanical guard (max spread ticks / slippage cap before placing) is execution
  engineering. Note London 2026 spreads regime-shifted — make any guard relative,
  never a frozen absolute. Journal spread-at-fill on every trade.
- **Q-33 (forward news buffer): DROP the buffer; the pre-09:30 stand-down config dies
  with v1.2 too.** The canons were validated on ALL days — 08:30 CPI/NFP releases are
  inside the profitable sample. An untested news veto is exactly the kind of
  mechanism that degrades a validated book. Journal the news-calendar state on every
  trade; if live data shows a news bleed, we'll rule with evidence. (If a human wants
  a manual FOMC-day stand-down as an operational choice, that's an operator decision
  outside the mechanical spec.)

**Rest of section D:** Q-29 (risk tone): DROP — day-level macro reads tested dead
repeatedly (best AUC 0.58; yday/red-streak nulls in three windows). Q-32 (playbook
match): MOOT — the canon IS the playbook; a trade only exists if the engine fired it
under a canon book, so novel setups cannot occur. Mnemosyne's account-state checks:
account state lives in Python (the funded buffer-scaling plan consumes it
mechanically); no agent gets P&L-based discretion.

**Section B (Q-4..Q-28): all MOOT** — they interpret the superseded v1.2 rulebook.
The placeholders in the four skill docs don't get filled; those docs get rewritten
against the canon (router + executor + journaler, above). I-4: ratified in spirit —
engine proposes everything; nothing invents prices. Q-16/Q-20: specialists never
re-derive blind; the engine's computed answers are the truth, guarded by the
reconciliation-day parity test (live features vs historical pipeline to the decimal).

**Pat's data ask:** Feb–Jul 2026 NQ 1-minute data is ALREADY in the repo on this
branch: `data/reference/nq_1m_feb_jul2026.parquet` (plus `output/fp_minutes.parquet`
for per-minute footprint). No new Databento pull, no platform export needed.

