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

## Where the build actually stands now

Pat asked for the build to start in parallel rather than wait — the four
specialist skill docs (`docs/desk-skills/{atlas,helios,apollo,hephaestus}-skill.md`)
and the Hermes coordinator instructions (`docs/desk-skills/hermes-coordinator.md`)
are written and ready for Pat to paste into the third-party Hermes product, along
with the Python receiver (`src/desk/verdict.py`, `src/desk/receiver.py`, tested)
that risk-gates and journals whatever Hermes decides. Every item this packet marks
✅ RESOLVED is already built into those docs correctly. Every item still open is
marked `<<PLACEHOLDER: ...>>` inline in the relevant skill doc — a plain
find-and-replace once you rule, no rebuild needed.

## What happens after your rulings land

Per the design doc's own sequence: your answers get folded into a pinned Spec-3,
THEN Pat/Claude Code write the actual `.claude/agents/{atlas,helios,apollo,
hephaestus,hermes}.md` files (each carrying a verbatim slice of your rulebook,
never Claude's paraphrase of it) plus `src/desk/runner.py` and the named test
suite (§6.7). Nothing about the champion bot or your regime-agent work changes —
the Desk is a separate, later live-trading path, not a replacement for either.

## RULING (Angus): _pending_
