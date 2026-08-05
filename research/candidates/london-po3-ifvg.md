---
date: 2026-08-05
status: thesis-pending
tags: [london, overnight-structure, reversal, pattern-taxonomy]
sources: ["findings/london-nq-what-three-traders-agree-on.md", "findings/london-window-LDN-WIN-01.md", "https://www.youtube.com/watch?v=uGE_GP9-nxU"]
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

## 🔴 The thing I cannot confirm

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

## Skeleton

Accumulation range = high/low of **01:00–02:00 ET** (window declared, not tuned).

Manipulation = a break of that range in **02:30–04:00 ET**, most often ~03:00.

Entry = confirmation that the break failed. Two declared arms:

- **A — IFVG** on 1–3 min, as stated by the source
- **B — close back inside** the accumulation range, which is our existing
  vocabulary and directly comparable to the `open-break` candidate's arm A

Stop beyond the sweep extreme. Target the opposite side of the accumulation
range, with the range midpoint as a declared partial. Flat by 05:00 ET.

## Flags

- **Instrument unresolved — blocks greenlight.** See above.
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
- Data fully in hand: bars plus the 912-day substrate.

## Trial ledger — LDN-PO3-01

_Awaiting Angus greenlight. No trials run. Blocked on the instrument question._
