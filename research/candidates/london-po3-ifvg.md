---
date: 2026-08-05
status: L1 done — raw negative, conditioning search earned
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

### Trial 1 — L0 census (2026-08-05) — **PASSED on premise, claim narrowed sharply**

Same prereg, same census, same event tree as `LDN-OBK-01` — one trigger, two
branches. `docs/PREREG-london-open-break-tree.md`, `scripts/london_obk_census.py`.
396 sessions, 2025/2026, **2023/24 untouched.**

**1. Breaks fail, and even the strong form survives.** Of 425 breaks:

| era | fail ≤30m | fail ≤60m | fail ≤120m |
|---|---:|---:|---:|
| 2025 | 79% | 83% | **85%** |
| 2026 | 77% | 81% | **84%** |

The declared census floor was 15%. EzTrades' strong claim — that the first move after
the open is *usually* the trap, not the real move — needed >50% and got 84–85%. **On
its own terms, as taught, the claim is correct.**

**2. And now the number that stops this being a good day.** The declared placebo — a
04:00–06:00 London range, same two-hour width, same logic, but with no claim on the
open — fails at **73% (2025) / 70% (2026)**.

So most of that spectacular 85% is not the London open sweeping anybody. It is what
any range boundary does: price poked it and came back. **The edge is the margin, not
the level:**

| era | pre-open | placebo | margin | z |
|---|---:|---:|---:|---:|
| 2025 | 85% (276) | 73% (305) | **+12 pp** | +3.43 |
| 2026 | 84% (149) | 70% (151) | **+14 pp** | +2.94 |

Era-consistent, in the same direction, at a respectable z in both. **There is
something specific about the pre-open range. It is about a seventh of what the raw
number advertises.** From here on this candidate quotes the margin and never the 85%
alone — and this is precisely why the placebo was added to the prereg before the run
instead of after. Without it the honest read and the flattering read are
indistinguishable, and I would have reported the flattering one.

**3. No side asymmetry.** Up-break fail 78% (2025) / 74% (2026); down-break 80% /
81%. The effect is not a directional drift artifact dressed up as a sweep.

**4. Traverse is the weak link, and it is the same lesson NY learned.** After a
failure, price reaches the **far edge** of the range only **~20%** of the time inside
the window; the midpoint about **46%**. That is the same shape as
`NYA-FA-01`'s finding that the "80% rule" is folklore (far edge 12–21% there). **The
declared target for arm B is therefore the midpoint, not the far edge** — the far-edge
version of this trade is not supported by its own base rate in either session.

**5. The declared transfer test FAILED.** `NYA-FA-01`'s excursion-depth discriminator
(23% vs 8% far-edge traverse) does not replicate here: in points rho **−0.105**
(inverted), normalised by range width rho **−0.017** (flat). Time-outside
discriminates nothing here either — that half *does* replicate NY. Full write-up and
the geometric explanation, addressed to the NY lane, in
`research/findings/nyfa-discriminator-does-not-transfer.md`. **London does not inherit
a discriminator; it has to find its own.**

**Recorded:** 4 rows under `LDN-PO3-01` in `output/trial_ledger.parquet` — the two
placebo-margin trials and both transfer-test constructions. The normalised transfer
test was a second look and is charged as one.

**Next rung — L1, on arm B only.** Close-back-inside entry (arm A/IFVG stays barred
until a mechanical definition is committed in advance), stop beyond the sweep
extreme, **target the midpoint** per finding 4, flat by 10:00 London. Costs at 1× and
2×. The SMT-divergence confluence remains dropped for want of ES data and the verdict
will say so.

### Trial 2 — L1 mechanics (2026-08-05) — **ugly raw, and the target question reopens**

`docs/PREREG-london-open-break-L1.md`, same run as `LDN-OBK-01`.

**F1 — the declared default (entry at the fail-bar close, stop beyond the sweep
extreme, target the range midpoint):**

| era | n | WR | net pts | $ @160 risk | PF | R/trade |
|---|---:|---:|---:|---:|---:|---:|
| 2025 | 234 | 34% | −149 | −$7,099 | 0.93 | −0.190 |
| 2026 | 125 | 33% | +8 | +$42 | 1.01 | +0.002 |

Strict cost: both negative. Ugly raw is expected and does not kill (§5.9.2).

**F2 — the as-taught far-edge target — is the interesting result, and I am not
promoting it.**

| era | R/trade (base) | PF | $ |
|---|---:|---:|---:|
| 2025 | −0.202 | 0.96 | −$7,556 |
| 2026 | **+0.302** | **1.20** | **+$6,031** |

It reaches its target only 13% of the time against F1's 29%, but when it pays it pays
much more. **It is much better in 2026 and no better in 2025 — era inconsistent**, so
under §6.0.1 it does not displace the declared default on in-sample rank. Ledgered as
a declared negative.

**This forces a correction to my own census read.** Trial 1 concluded from the ~20%
far-edge traverse rate that "the far-edge version of this trade is not supported by
its own base rate" and moved the declared target to the midpoint. **That inference was
too quick.** A low hit rate on a distant target is not the same as a bad target — the
payoff per hit is what settles it, and base rates alone cannot see that. The right
statement is that **the target question is open**, not that the midpoint won. It is a
declared exit-arm question for a later rung, with both arms already on the ledger.

**Cost sensitivity is the real story on this branch.** Average risk is small — roughly
5 points, because the sweep extreme sits close to the fail-bar close — so a 1–2 point
cost is 20–40% of the stop. Fabio named NQ slippage as the one thing that breaks his
version of this trade. That is now measured rather than quoted.

**Declared variable — minimum displacement — did not lift.** ≥0.10× range width:
2025 −0.255R, 2026 −0.200R, worse than unfiltered in both eras.

**Recorded:** 4 arm×era trials in `output/trial_ledger.parquet`.

**Next rung.** Conditioning search (earned — the premise passed census and the +12/+14
pp placebo margin is a real, era-consistent signal that something specific happens at
this range). Arm A (IFVG) remains barred pending a mechanical definition committed in
advance. SMT confluence remains dropped for want of ES data.
