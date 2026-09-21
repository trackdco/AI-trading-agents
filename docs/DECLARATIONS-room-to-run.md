# DECLARATION — ROOM-TO-RUN AS A STANDALONE GATE (3m and 5m)

Written 2026-08-07, **before this gate has been run in the form specified
below**. Read the integrity note in §0 first — it states exactly which
parts of this are genuinely unread and which are a restatement of numbers
already on the record. Holdout look #1 remains **HALTED**; no sealed row
has been read.

---

## §0 — INTEGRITY NOTE: what is already known, stated before the design

A declaration that pretends to be blind when it is not is worse than no
declaration. The honest accounting:

**ALREADY READ on fit** (FINDINGS-ltf-trigger-recensus, BR-32/33/34) — the
pooled marginal lift of the room gate with a 2pt risk floor:
`TF=2 +0.185`, `TF=3 +0.212`, `TF=5 +0.214`, all three with both-era
day-boot CIs on the lift clear of zero; `TF=1` and `TF=15` clear H2 only.
**Re-running that on fit is a RESTATEMENT, NOT A TEST**, and it will be
labelled as such in the output. It cannot confirm anything.

**GENUINELY UNREAD, and therefore the actual content of this pass:**
1. The **per-session** split at 3m and 5m. Only the pooled-over-sessions
   number has been read, and the programme's standing rule is that sessions
   are never pooled (BR-23/26).
2. The **per-arm** split at 3m and 5m.
3. The **natural frequency** of the gated book. Every number read so far
   came from a *frequency-matched* construction that forced a target rate
   using flow concordance. This pass forbids that (§3).
4. The **threshold sensitivity** — 3R was taken from the shipped partial,
   never swept.
5. **The entire account layer**: daily-R distribution, worst-day R,
   max non-breaching size, P(graduate), P(death). None of it exists for
   this book at any timeframe.

**THE REAL CONFIRMATION VENUE.** `next_lvl_R` is pure bar geometry — level
distances over risk, no tape — so this is a **bar-only claim** and belongs
to the **bar-only holdout venue** (23 months, 2023-01..2025-05, Blocks A
and B, *both* must pass) under DECLARATIONS-holdout-partition D1/D2. It
does **not** touch the flow venue, which stays unspent.

Per the standing one-look-per-family rule, this claim **joins holdout look
#1's frozen claim list** rather than opening a second bar-only look. That
is the operational reason look #1 stays halted: **the claim list is not
finished.** Look #1 fires when it is.

---

## §1 — THE GATE, specified exactly

Two constructions, **both declared now** so neither is a post-hoc choice:

> **PRIMARY (isolates the variable).**
> Population: first-of-fight rows with **`risk ≥ 2.0 pt`**.
> Gate: **`next_lvl_R ≥ 3.0` OR no level ahead** (open space).
> The risk floor is applied to the baseline *and* the gated set, so the
> measured lift is room-to-run alone and not the floor's contribution.
>
> **AS-TRADED (what the book would actually be).**
> Population: all first-of-fight rows.
> Gate: **`risk ≥ 2.0 pt` AND (`next_lvl_R ≥ 3.0` OR open space)**.
> Reported alongside; the floor's own contribution is therefore visible as
> the difference between the two.

`next_lvl_R` is the census column already built: distance from entry to the
**nearest other locus ahead in the trade direction**, in R, as-of the
decision bar. "No level ahead" is a category, not missing data.

**Why 3R, and why it is not a tuned number.** The shipped exit takes 75%
off at 3R. A target closer than 3R means the partial cannot be reached at
the level that defines the trade. The threshold is read off the exit
grammar, not swept for fit. **A full sweep over {2, 3, 4, 5}R is reported
as sensitivity and is NEVER selected on** — same discipline as X.

**Why a 2pt floor.** BR-29: below ~2pt the stop is inside the noise and
`cost_R = 0.5/risk` explodes; those rows return −0.667R at 1m. The floor is
a stop-quality precondition, not a performance filter. It is fixed at 2.0pt
and not swept.

---

## §2 — SCOPE

- **Timeframes: 3m and 5m only.** 1m is closed (BR-33: worst at every
  matched rung, only TF failing the both-era check). 2m and 15m run as
  **reported control columns**, never as candidates.
- **Sessions: LONDON, NY_PRE, NY_AM scored and reported SEPARATELY. Never
  pooled, never averaged.**
- **Both arms**, reported separately and combined.
- **X = 0.5W15** declared; full {0.25, 0.5, 1.0, 2.0}W sensitivity reported.
- **Costs** at 0.5 / 1.0 / 1.5pt per round trip, as D6.

**Cell count, stated up front: 2 candidate TF × 3 sessions × 2 arms = 12
cells**, plus 6 combined-arm cells and 12 control-column cells. Bonferroni
α on the candidate family = 0.05/12 = 0.0042.

---

## §3 — WHAT IS FORBIDDEN IN THIS PASS

- **No CONCORD. No flow features of any kind.** Concordance has now failed
  its own declared bar twice — BR-19 at 15m (max lift +0.046R, below the
  bar, every half-1 survivor dead on half 2) and BR-31 at LTF (96 cut cells
  searched, 0 clearing in both eras). It does not get a third appearance as
  a convenience knob.
- **No frequency matching.** The earlier matched-selectivity table used
  concordance to hit a target rate. That construction is not repeated.
  **Whatever frequency the gate produces is the frequency, and it is
  reported as a result** — including if it is too low to build a book on.
- **No threshold selection.** The sweep is reported; 3R is the declared
  operating point regardless of which sweep value looks best.
- **No holdout contact.**

---

## §4 — THE DECLARED BARS

**Bar 1 — the gate itself (Law 7).** Per session, per TF, per arm:

> marginal lift = q·(EV_all − μ_cut)/(1 − q) ≡ EV_kept − EV_all
> **≥ +0.05R**, with the **paired** day-boot CI on the **lift** clear of
> zero in **BOTH eras** (H2-2025 and H1-2026), at X = 0.5W.

Dual currency reported alongside (Law 3): win rate of kept vs cut. A gate
that buys hit rate and sells expectancy is refuted, as BR-20 was.

**Bar 2 — the account layer, declared before the numbers exist.** The gated
book is compared against its OWN ungated baseline (same session, same TF,
same risk floor) on two axes:

> (a) **P(graduate) at matched contract size**, and
> (b) **max non-breaching size** — the largest size at which the worst fit
> day's total R does not breach the $2,000 EOD trailing drawdown.
>
> **The gate PASSES the account layer only if it does not lose on either
> axis.** A gate that raises EV while concentrating losses into worse days
> can *reduce* P(graduate) at the size you can actually run — that is the
> failure mode this bar exists to catch, and it is the Law-3 dual-currency
> idea applied to the account rather than to the trade.

**Bar 3 — frequency admissibility.** A book below **0.5 fights/day in its
own session** is recorded as **too thin to run standalone**, whatever its
EV, and is not carried forward alone.

---

## §5 — THE PREDICTION, DECLARED BEFORE THE RUN

1. The per-session split will be **uneven**, and LONDON will not
   automatically be best — the pooled +0.212/+0.214 could be carried by
   NY_AM, which has the most rows.
2. Natural frequency will land near **5/day pooled across 7 loci and both
   arms**, i.e. well under 1/day per session per arm — thin.
3. The gate will look **better on the break arm**, because a break already
   has direction and room is what it needs; a reject is trading against the
   nearer level by construction.
4. **The account layer is where this is most likely to fail.** Room-rich
   trades run further, so their losers run further too before the trail
   catches them; worst-day R may worsen and shrink the max size.

If (4) happens, **that is the finding** and it is reported as the headline,
not as a footnote — the same clause D6 carried, for the same reason.

---

## §6 — WITHDRAWN: the D1a reject-arm follow-up

FINDINGS-ltf-trigger-recensus proposed "a fresh blind declaration on the
15m reject book, where n_keep would be ~7× larger." **That proposal is
withdrawn. It does not survive specification, on three counts:**

1. **The population was mis-stated.** Condition (B) is 0% on 15m rejects at
   `bbma15` only — there the locus *is* the 15m BB MA, so a reject cannot
   close through it. At the other six loci (B) is a genuine confluence
   condition (reject a non-MA locus *and* reclaim the mean) running
   **9.8–11.2%** of rejects. So "the 15m reject book" was never the right
   name for the object; the object is *non-bbma15 15m rejects*.
2. **The justification was arithmetically wrong.** n_keep at 15m reject is
   **325** against 1m's **225** — a ratio of **1.44×, not ~7×**. The claim
   that motivated the follow-up was false.
3. **The population has already been read.** The D1a table in that same
   document reports the lift on exactly this set: LONDON **+0.060**,
   NY_PRE **−0.057**, NY_AM **+0.116**. Two positive, one negative, none
   clearing. There is nothing left to declare blind.

Recorded as a **specification failure caught before it consumed a
declaration**, not as a result.
