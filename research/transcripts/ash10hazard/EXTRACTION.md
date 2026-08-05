# ash10hazard — channel survey and extraction

Source: `https://www.youtube.com/@ash10hazard/videos`, 50 most recent enumerated 2026-08-05.
3 tutorial transcripts pulled and cleaned here. No trial spent, nothing tested.

**This is the opposite kind of source from ATAS.** ATAS was a vendor teaching its product.
This is a retail day-trader selling a Discord, mentorship and a prop-firm affiliate code.
Read the evidence and the method separately — they deserve different verdicts.

---

## The channel as evidence: worthless, and it is important to say why

Of ~50 videos, roughly 40 are P&L headlines: `+$3.6K`, `+$4K`, `+$5K`, `+$7.5K`, `+$12K`,
`+$5,663`, `+$10K in 3 minutes`.

**Losses in the entire visible history: one.** *"How I Was UP +$6K & 1 Point from TP & it
reversed"*, plus two "breakeven trades" videos.

That distribution is not achievable by any real trader. It is selective reporting, and it
is the single clearest signal in the survey. A channel showing ~40 wins and 1 loss is not
publishing a track record; it is publishing a marketing funnel.

The funnel is explicit in the tutorial's own close: Discord monthly or lifetime purchase,
one-to-one mentorship, *"use code Ash10 at Alpha Futures"* (prop-firm affiliate), and
recurring giveaways. **The strategy content is the lead magnet.** Revenue plausibly comes
from signups rather than from trading.

View counts are 46–1,500. This is a small channel, not an established source.

**None of that makes the method wrong.** It means the channel supplies zero evidence either
way, and the method has to be judged entirely on its own mechanics.

## The method — ICT "unicorn model" / Silver Bullet

Session: **09:30 → 14:15 ET**. Macro windows (09:45–10:15, 10:45–11:15, 11:45–12:15,
13:45–14:15) are named as highest-probability, but he explicitly trades the full session:
*"just trading the full session completely eliminates the fact that you missed those
trades."*

Sequence:

| # | step | specifiable? |
|---|---|---|
| 1 | **Liquidity sweep** — a 15-min swing high/low taken out, or session liquidity (London highs, Asia highs, NY lows, lunch highs/lows) | **yes** |
| 2 | **Shift in market structure** — price takes out the most recent short-term high/low against the sweep | **yes**, given a swing definition |
| 3 | **Entry at a fair value gap**, paired with an inverted order block | FVG **yes** (3-candle pattern); order block **no** |
| 4 | **ES/NQ dual confirmation** — the model must appear on both; if ES has not shifted, enter but exit if it fails to shift on the next candle | **yes — but we hold no ES data** |
| 5 | **Stop** at the recent swing, "or two previous swing highs if the RR is good enough" | partly — the alternative is discretionary |
| 6 | **Target 2R**, at "the opposing draw on liquidity" | **yes** |
| 7 | **Trail** by R-multiple *or* by judgement | **no** |

### The author states the core is unteachable

> *"You're probably wondering, well, how do I know? … if you understand price action, then
> you'll know. But it's kind of hard to teach it to you unless you've been in the Discord
> watching me trade every day."*

That is simultaneously a sales pitch and an admission that the specification is incomplete.
Steps 3 (order block), 5 (stop variant) and 7 (trailing) are discretionary, and step 7 is
explicitly so: *"I don't like to be so systematic anymore… I look at the scenario."*

**A strategy whose entry, stop and management each contain a judgement call cannot be
tested as stated.** It can only be tested in a mechanised form, and any mechanisation is
our specification choice, not his — which must be declared as such.

### Evidence offered: four trades over two days

The tutorial's entire empirical content is 4 executions on 21–22 May, all winners.

---

## Data blocker

**We hold no ES data.** `data/reference/` contains NQ only. Step 4 — the ES/NQ dual
confirmation, which the author treats as a core filter and has clearly refined over time —
**cannot be evaluated at all**. Any test we run would be of a strictly weaker model than
the one taught.

That is disclosable up front, not after a null.

---

## The one clean, cheap, high-value test

Strip the discretion and one claim underpins the entire framework — his and every other
ICT channel's:

> **Price behaves differently inside the fixed macro windows (09:45–10:15, 10:45–11:15,
> 11:45–12:15, 13:45–14:15 ET) than outside them.**

Why this is the right thing to measure first:

- **Completely non-circular.** The clock times are fixed in advance by the framework, not
  chosen from the data. This is exactly the distinction drawn in
  `FINDING-LDN-MACRO-01-blocked-on-data.md`: inferring event windows from volatility is
  circular; testing *pre-declared* clock windows is not.
- **No strategy required.** Just realised range, volume, and directional persistence per
  clock minute against the rest of the session.
- **Cheap and decisive.** If those windows are not distinguishable, a large part of the ICT
  edifice loses its stated foundation — and that finding transfers to every ICT-derived
  candidate anyone brings us, forever.
- **It is a NY-session test**, which is now in scope.
- We have 3.5 years of 1-minute NQ bars, so it is well powered.

**Recommendation: measure the macro windows before anything else from this channel.** It is
one measurement, it is not a trial in the ledger sense (no strategy, no outcome selection),
and it gates whether the rest is worth specifying.

If the windows *are* special, the FVG-after-sweep model becomes worth a proper prereg in a
declared mechanised form. If they are not, this channel and every ICT variant of it can be
closed with one number.

## Standing note

The ATAS four-condition conjunction feasibility count (`research/transcripts/atas/
EXTRACTION.md`) is still **outstanding** and was not superseded by this channel.
