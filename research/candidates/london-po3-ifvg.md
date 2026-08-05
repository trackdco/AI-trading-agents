---
date: 2026-08-05
status: thesis-pending
tags: [london, overnight-structure, reversal, pattern-taxonomy]
sources: ["findings/london-nq-what-three-traders-agree-on.md", "findings/london-window-LDN-WIN-01.md", "https://www.youtube.com/watch?v=uGE_GP9-nxU", "https://www.youtube.com/watch?v=v7tdhjW84Ho", "https://www.youtube.com/watch?v=RJXe1rF9kXM"]
---

# london-po3-ifvg — the 03:00 sweep of the London accumulation range

## Thesis (for Angus)

Between roughly 01:00 and 02:00 ET, London builds a range. It is a genuinely
quiet stretch — the Asian session is finishing, Europe has not properly started,
and price mostly just accumulates. That range is visible to everyone and the
orders pile up on both sides of it.

Then at about 03:00 ET the European open arrives and the first thing it does is
take one side of that range. The claim is that this first move is usually **not**
the real move — it is the sweep that collects the stops, and the actual
direction is the one that follows once those orders are consumed.

The wrong side is whoever treated the 03:00 break as the signal. They are the
liquidity.

EzTrades states it as three components: **time** (only the 03:00 manipulation),
**PO3** (accumulation → manipulation → distribution), and an **inverse fair
value gap on a 1–3 minute chart** as the entry trigger — *"ideally a V-shaped
inverse within a few candles."*

**What makes this worth a look is the clock, not the framing.** PO3 and IFVG are
ICT vocabulary and the mechanism is old. But he pins it to a specific minute, and
that minute is the one our own measurement independently found: `LDN-WIN-01` put
**03:00 ET as the volume peak of the whole session in both eras**. Brandan's
08:00 UK is the same instant from a different direction. Three sources, one
clock, one of them our own data.

**How it differs from `london-nq-open-break`, and why both are worth having.**
They fire at the same time and disagree about what to do:

- open-break trades the resolution of a level test — it can go **with** the break
- this one says the 03:00 break is a trap and trades **against** it, after
  confirmation

That is an event-tree pair on one trigger, not two independent ideas, and it
should share a ledger the way the prior programme paired sweep-reversal with
sweep-continuation. Testing them as one family is much cheaper than two.

## ~~The thing I cannot confirm~~ — RESOLVED, see Update 2

**I do not know what instrument this is.** The transcript never says — no
"nasdaq", no "NQ", no "gold", no "futures". He demonstrates it on a chart and
captions do not carry chart content. His channel is gold-heavy. Attempts to pull
the video description for a hint hit YouTube's bot-check on every client.

So the honest position is: **the model is fully specified, the instrument is
not.** It may be a gold strategy. If it is, the clock still holds (03:00 ET is
03:00 ET) but the evidence for applying it to NQ is one unverified assumption,
and this candidate is much weaker than it reads.

Settling it needs either his second London video (`v7tdhjW84Ho`, queued) or
someone watching two minutes of the chart. **I would not greenlight this ahead of
`london-nq-open-break` until that is resolved**, and I am filing it as
thesis-pending rather than quietly assuming NQ because it would be convenient.

**Update 1 — a second EzTrades video landed naming no instrument either.**
`RJXe1rF9kXM` contains zero mentions of nasdaq, NQ, ES, gold, US30, DAX or
futures. On that basis I concluded transcripts could not settle this for this
source, and that waiting for `v7tdhjW84Ho` was unlikely to help.

**Update 2 — that was wrong. `v7tdhjW84Ho` settles it.** Two mentions, both
load-bearing:

> *"if you're **trading Nasdaq**, you would use **ES as your correlated asset**
> that you're looking for SMT divergences."* [@ 2:09 — stated while describing
> this London setup's confluence requirement]

> *"we **live trade NQ** every single morning at **9:30 a.m. Eastern** using this
> framework. **Same PO3, different time.**"* [@ 5:02]

So: **NQ is explicitly in scope for the framework**, and Nasdaq is named inside
the London setup's own rules. The instrument blocker is lifted.

**But read the second quote carefully, because it cuts both ways.** His *live*
NQ trading is the **New York** open at 09:30 ET — "same PO3, different time".
That means the framework is proven on NQ at 09:30 and the London 03:00 version is
the transfer, not the other way round. It is no longer an unknown instrument; it
is a known instrument at an unproven hour. Better, and still not free.

**A prediction of mine failed here and the failure is the useful part.** I
generalised from two videos to "this source never names instruments" and
recommended not waiting. One more video disproved it. Two data points were not
enough to declare a pattern about a 406-video channel — the corpus was there and
I called it early.

### New rule detail this video adds

A confluence requirement absent from `uGE_GP9-nxU`: the setup *"needs to be
rejecting from a **15-minute or 1-hour fair value gap**, or it needs to have an
**SMT divergence**"* (NQ vs ES non-confirmation).

That is a real addition to the spec and it carries a **data dependency**: SMT
divergence needs ES alongside NQ, which we do not hold. Either buy ES bars, or
declare the HTF-FVG-rejection leg alone and record that the SMT arm was dropped
for data reasons rather than silently testing a weaker spec.

## Skeleton

Accumulation range = high/low of **01:00–02:00 ET** (window declared, not tuned).

Manipulation = a break of that range in **02:30–04:00 ET**, most often ~03:00.

Entry = confirmation that the break failed. Two declared arms:

- **A — IFVG** on 1–3 min, as stated by the source
- **B — close back inside** the accumulation range, which is our existing
  vocabulary and directly comparable to the `open-break` candidate's arm A

Stop beyond the sweep extreme. Target the opposite side of the accumulation
range, with the range midpoint as a declared partial. Flat by 05:00 ET.

## Promotion rule — declared BEFORE any tournament (§6.0.1)

**Default spec = arm B, close back inside the accumulation range.** Chosen on
mechanism and on testability, not on expected performance: the thesis is that the
03:00 break *fails*, and a close back inside the range is the minimal
unambiguous statement of failure. Arm A (IFVG) is the source's own trigger but
*"a V-shaped inverse within a few candles"* is not yet a mechanical definition,
and an arm whose definition is still being written cannot be the default —
whoever writes it would be writing it after seeing the data.

**Arm A (IFVG) may displace B only if ALL THREE hold:**
1. IFVG is given a mechanical definition **committed before** the arm is run,
2. PBO on the arm matrix is **< 0.5**, and
3. the holdout adjudicates in A's favour under the single corrective iteration.

**The SMT-divergence confluence is not an arm at all** until ES data exists. If
we run without it, the verdict records that the spec tested was the
HTF-FVG-rejection leg only, and the SMT leg was dropped for data reasons — not
quietly folded in as "the strategy".

**In-sample rank never promotes anything here.**

## Bars — pre-registered per §5.9.3 and §5.9.5

- **Census kill line (§5.9.1):** dies only if the claimed behaviour does not
  occur — i.e. if the 01:00–02:00 range is not swept in 02:30–04:00, or sweeps
  never fail. Tested **as taught**, with the confluence requirement included as
  a mandatory trigger, per §5.9.1.
- Sleeve bars as for `london-nq-open-break`: era consistency plus inverse pass,
  costs at 1× and 2×, PSR(0) ≥ 0.75.
- Deflation charged at book level; every trial to the machine ledger at trial
  time.

## Flags

- **Instrument RESOLVED** — NQ is named explicitly. What remains is that his
  *live* NQ application is the 09:30 ET New York open; the London 03:00 version
  is a transfer of a proven framework to an unproven hour.
- **SMT-divergence confluence needs ES data**, which we do not hold. Declare the
  HTF-FVG leg alone and record the dropped arm, or buy ES bars.
- **Family overlap.** Accumulation → manipulation → distribution is the same
  object as the previously greenlit `london-asia-sweep-reversal`. If that
  candidate is genuinely scrapped, this replaces it; if not, this joins its
  ledger rather than opening a new family. **Angus's call**, and it changes the
  arm count.
- **Event-tree pair with `london-nq-open-break`** — same trigger, opposite
  prediction. One family, one ledger.
- IFVG needs a mechanical definition before it can be censused; "V-shaped inverse
  within a few candles" is not one. Arm B exists so the candidate is testable
  even if arm A's definition proves too loose.
- Data: the core spec is fully covered by bars plus the 912-day substrate.
  **The SMT-divergence arm is the one exception** — it needs ES, which we do not
  hold, so that arm is either bought or explicitly dropped.

## Trial ledger — LDN-PO3-01

_Awaiting Angus greenlight. No trials run. Instrument blocker lifted; the open
question is now the clock (03:00 London vs his proven 09:30 NY), not the market._
