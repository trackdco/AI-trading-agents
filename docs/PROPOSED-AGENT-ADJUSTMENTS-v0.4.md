# Proposed adjustments for regime agent v0.4 — for Angus review, then Pat

Target metric: regime-read accuracy (scripts/score_regime_reads.py). Baseline v0.x on
March 2026: 43% reads, 17% read-quality capture, −$1,715 P&L (v0.3.0). Dominant miss:
event_risk over-call — 12 FLAT calls where the oracle wanted 8, seven misses on
tradeable days. At 60–70% reads the same architecture plausibly outperforms the
champion (rough March math: capture scales ~linearly with reads → ~45–55% capture ≈
+$5–6k vs champion's +$4.3k, and the insurance pays extra in red months).

## A. What the agent SEES (engine lane — buildable now)

A1. ANALOG BLOCK in the briefing. For today's regime vector: the K=15 nearest days from
    the 850-day library, each with its realized best action (rotation/momentum/flat) and
    both books' P&L. Regime reading becomes retrieval-plus-judgment instead of inference
    from one morning. THIS is "understanding the historical data" made literal.

A2. AMT FEATURE UPGRADE. The current day-type input is one overlap ratio. Add (all
    pre-open computable): overnight value position vs prior day's VA (above/inside/below
    — the 80%-rule setup), open-vs-value location, prior close location in prior VA,
    overnight inventory direction + size, overnight range vs 20d norm. These are the
    auction-theory reads that actually distinguish rotation from migration mornings.

A3. EVENT ANALOGS. Calendar says "CPI today"; it should also say: "last 6 CPI days:
    median morning range X, champion made money on 4, the release resolved directional
    by 09:15 in 5 of 6." Retrieval kills the boy-who-cried-wolf pattern behind 7 of the
    12 March misses.

## B. How VERDICTS work (Pat lane)

B1. 09:30 SECOND LOOK, release-only authority: may lift an 08:00 brake, never add one
    mid-session. Directly targets the 03-17 class (reasonable caution, disproven by the
    open, unrevisable all day).

B2. EVENT-RISK EXPIRES. Pre-release stand-down auto-expires once the release resolves
    (e.g. CPI 08:30 → verdict void at 09:00, agent re-reads the post-release tape).
    03-10/11/17 were post-release trend days lost to all-day event flats.

B3. SPLIT THE TAXONOMY. {balance, war, trap, event_risk} conflates tape-state with
    calendar-state. Two axes: tape ∈ {rotation, momentum, trap, unclear} × event-flag ∈
    {none, pre-release, post-shock}. Event becomes a timing MODIFIER, not a regime —
    an event morning can still be a momentum day after 09:00.

B4. HEALTH-CONDITIONED DEFAULT (Angus ruling, filed): unsure → follow baseline only
    where baseline's trailing expectancy is positive; else unsure → defend.

## C. How it LEARNS

C1. Scorecard feedback: each morning's briefing includes the agent's own running
    read-accuracy BY MISS CLASS ("your event_risk calls: 2/9 correct") from the ledger.
C2. Regret lines: every intervention's counterfactual cost (both arms run daily) goes
    into the playbook notes — the agent confronts the price of each brake it pulled.
C3. Confidence calibration tracked: if 'high' confidence doesn't outperform 'medium',
    confidence loses authority (ties into library-depth gating, finding #6).

## D. Process guard

D1. All of A+B+C land as ONE version bump (v0.4). Fair exam = months the agent was not
    iterated on: May 2026 + one 2025 quarter. Score reads first, P&L second. No further
    March retests count for anything.

Engine lane commits to A1–A3 (data plumbing) immediately on Angus's go.
