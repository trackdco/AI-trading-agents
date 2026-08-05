---
id: zxck-news-draw
name: News (data) high/low opposing draw
trader: Powell
prefix: zxck-
sessions: [08:30 ET on CPI / PPI / NFP only]
instruments: [NQ]
GAP_ENTRY: PARTIAL — inverse FVGs named as one of the two entries after the sweep
NY_SESSION: YES
sources: [c15YLeAKc2A, WEeXKMzaJjY, Y-oqSZmNo4U, 55KRVFLqzwA]
components: zxck-COMPONENTS.md
verdict: PARTIAL
---

# `zxck-news-draw` — the news high/low opposing draw

## Confirmation

### 1 · TEACH-BACK

On a release day the news candle prints a high and a low — the data high and the data low — and
his claim is simple: **whichever one gets taken first, the other becomes the draw**. That gives
me a directional target for free, which is why he likes trading news days at all. So at 08:30 on
a CPI, PPI or NFP day I mark both extremes, wait for one side to be swept, and then look to enter
in the direction of the untouched side. The entry is a low-timeframe trigger after the sweep —
he names the **first 30-second CISD** with a 10-point stop targeting the opposite extreme for
about 1:4, and says inverse FVGs work equally well there. He also uses the two levels a second
way: once price closes strongly through a data high or low, that level starts behaving like a key
open and can be traded as one, and if the news candle left a decent wick on the 15-minute, its
50% is a wick-CE entry — but **only** if engineered liquidity is present, because entering every
50% of every wick gets you killed. Two things temper this. He shows a **counter-example where the
first entry after the data high was swept would have lost**, on a CPI day he calls atrocious. And
he has a separate, event-specific prior: **NFP makes a move that reverses at the market open,
while CPI makes a move that continues all day** — which cuts against a pure "take the opposing
side" read and I do not know how the two rules interact.

### 2 · SEVEN-PART COMPLETENESS CHECK

| part | tag | evidence |
|---|---|---|
| **bias source** | **[stated]** | *"whichever side we take first, we're going to go for that other opposing liquidity pool"* `[c15YLeAKc2A @ 00:00]`; *"the draw on liquidity is pretty much free"* `[@ 03:11]` |
| **setup conditions** | **[stated]** | one side of the news range swept; only CPI/PPI/NFP `[@ 05:36]` |
| **entry trigger** | **[stated]** | *"the first 30 second change in state of delivery"* `[@ 02:47]`; or an inverse FVG `[@ 03:11]` |
| **stop / invalidation** | **[stated]** | *"10 point stop"* `[@ 02:47]` |
| **targets** | **[stated]** | the opposite data extreme; *"target data low for a one to four, 40 points"* `[@ 02:47]` |
| **risk / sizing** | **[inferred]** | `COMPONENTS` §D/§E |
| **avoid-filters** | **[inferred]** | Only by demonstration — the CPI day that failed `[@ 01:10]` and *"price action was cancer"* `[@ 03:11]`. **No rule for when to skip** |

### 3 · ASK ME

**Q-H1 · How do the opposing-draw rule and the NFP/CPI priors interact?**
- *Best guess:* **the NFP/CPI prior sets the day's direction and the data high/low gives the
  levels.** So on NFP: the release move runs to one extreme, reverses at 09:30, and the opposing
  extreme is the draw — the two agree. On CPI: the move *continues*, which would mean the first
  extreme keeps extending and the opposing draw is **wrong**. That reading makes CPI days a skip
  for this model, and I am not confident in it.
- *Why it matters:* CPI is one of the three days the model is allowed to trade. If the two rules
  conflict there, we are either dropping a third of the sample or trading against his own prior.
- *Answerable from method?* **Yes** — this is the one I'd most want your read on.
  Sources: `[c15YLeAKc2A @ 00:00]` vs `[WEeXKMzaJjY @ 03:58]`.

**Q-H2 · What exactly is the "data high/low" — the 08:30 one-minute candle's range, or the whole reaction?**
- *Best guess:* **the extremes of the initial reaction**, not a fixed candle. He points at wicks
  and describes them as *"like news wicks"* `[55KRVFLqzwA @ 02:44]` and refers to *"a decent sized
  wick on the 15 minute"* `[c15YLeAKc2A @ 06:45]`, which implies a wider window than one minute.
- *Why it matters:* it is the level definition. One-minute range and five-minute range give
  materially different levels and therefore different sweeps and different targets.
- *Answerable from method?* **Yes**, or re-watch `c15YLeAKc2A @ 02:01–02:24`.

**Q-H3 · Is the 30-second trigger essential, or will a 1-minute trigger do?**
- *Best guess:* **1-minute is acceptable but worse.** He recommends 15s/30s because *"price action
  is really really fast"* `[c15YLeAKc2A @ 02:24]`, and separately argues 5-minute triggers beat
  1-minute in normal conditions `[WEeXKMzaJjY @ 03:10]` — the opposite direction. News is his
  stated exception.
- *Why it matters:* **we hold 1-minute data and nothing finer.** If 30 seconds is essential, this
  card is untestable with what we have and should be marked blocked rather than tested badly.
- *Answerable from method?* **Yes.**

**Q-H4 · Does he skip the session when price action is "atrocious", and if so on what signal?**
- *Best guess:* **yes, discretionarily, with no stated signal.** He calls the failing CPI day
  *"absolutely atrocious"* `[c15YLeAKc2A @ 00:00]` and elsewhere describes chop as an
  invalidation `[xae9AiV5Ps4 @ 09:16]`.
- *Why it matters:* a mechanical backtest takes every day including the ones he would have sat
  out, which **understates** his results in a way we should state rather than discover.
- *Answerable from method?* **Yes** — and if there's no rule, I'll record that as a known bias in
  the backtest rather than invent a chop filter.

### ⬛ SELF-RESOLVED 2026-08-07 — Q21 closed
Full evidence: `SELF-RESOLVED-2026-08-07.md`.
- **Q21 → the sub-minute trigger is OPTIONAL and the trigger is open-ended**: *"you can use the
  30-second or even the 15-second, whatever you feel like doing"* `[c15YLeAKc2A @ 02:24]`;
  *"you can use inverse fair value gaps whatever you want"* `[@ 03:11]` `[stated]`
  **The card is NOT blocked on our 1-minute data.**

**Still open: Q20 (the CPI conflict).**

### ⬛ FOLDED IN 2026-08-07 — Brake's answers

**Q20 · the CPI conflict — `[stated-by-user]`: CPI IS A SKIP.**
> *"accept the agent's reading that CPI is a skip. It's internally consistent: he says CPI keeps
> extending all day, so the opposing-draw rule genuinely conflicts on CPI, and trading against his
> own stated prior would be the incoherent choice. Yes it drops a third of the sample, but the
> logic is clean. Tag inferred, medium priority."*

**LOCKED RULE:** the model trades **PPI and NFP only**. CPI days are skipped, because
> *"CPI usually makes a move and it usually just keeps making that move for the entire day"*
> `[WEeXKMzaJjY @ 03:58]`
directly contradicts
> *"whichever side we take first, we're going to go for that other opposing liquidity pool"*
> `[c15YLeAKc2A @ 00:00]`.
Tagged `[inferred]` — **he never says to skip CPI.** This is the coherent reading of two of his
statements, ratified by Brake, not a rule he stated.

**Cost of the rule, stated up front:** roughly a third of eligible days removed. Given ~12 releases
each of CPI/PPI/NFP a year, the eligible universe drops from ~36 to ~24 days — before any setup
filter. **This model may not clear the n≥30 floor.** That is a foreseeable outcome, not a surprise.

**⚠️ BOOKKEEPING CORRECTION.** Two questions from this card's original set — **Q-H2** (what
exactly constitutes the data high/low) and **Q-H4** (does he skip on unreadable price action) —
were dropped from the shrunk list I presented **without being marked resolved**. That was my
error. Applying the stated protocol now:
- **Q-H2 `[inferred]`, assumption stated:** the data high/low are the extremes of the release
  reaction. **He never gives a window length.** The only timeframe he attaches to them is a
  15-minute wick `[c15YLeAKc2A @ 06:45]`. **Any window we pick is OURS**, and it defines the level,
  so it materially changes the trade. **This is why the card stays Partial.**
- **Q-H4 `[inferred]`:** he skips discretionarily on *"atrocious"* price action `[@ 00:00]` with
  **no stated signal**. A mechanical backtest will take days he would have sat out and therefore
  **understates** him. Recorded as a known bias; no chop filter invented.

### 4 · VERDICT — **PARTIAL**

Unusually complete for this corpus — bias, entry, stop and target are all [stated] with numbers,
and we hold the news calendar. Partial because **Q-H1 is a possible internal contradiction** on
one of its three eligible days, and **Q-H3 may make it untestable on our data**.

---

## Edge thesis
> *"that's why I like trading news days because the draw on liquidity is pretty much free."*
> `[c15YLeAKc2A @ 03:11]`
He offers no mechanism: *"they're like news wicks. I don't even know why they're special. They
just work."* `[55KRVFLqzwA @ 02:44]` — `[inferred by him]`, honestly flagged as such by him.

## The second use — data extremes as key opens
> *"if you get a strong close above, you can basically use it as like a key open."* `[c15YLeAKc2A @ 04:45]`
And the wick version: *"if they leave a decent sized wick on the 15 minute, you can use the 50%
mark of that for an entry"* — **but only with engineered liquidity**, *"if you just try to enter
on every 50% of every wick, you're going to get merked"* `[@ 06:45]`.

## Which releases — `[stated]`
> *"only use 08:30 if there's news days, some decent news, CPI, PPI, NFP."* `[c15YLeAKc2A @ 05:36]`
Corroborated `[Y-oqSZmNo4U @ 18:12]`. **We hold `config/news_calendar_hist.csv` and
`config/news_calendar.csv`, and all three are US releases — so the calendar side is implementable.**

## The counter-example he shows himself
> *"if you tried taking the first entry after data high got swept yesterday you would have gotten
> [wrecked] because of this price action."* `[c15YLeAKc2A @ 01:10]`

## Revision log
- **2026-08-07 rev a** — PARTIAL. Q-H1 possible internal conflict; Q-H3 may block on data.

### 2026-08-07 rev b — self-resolution, Brake's answers, exit lock
Prior rev-a numbers and tags are **retained above, not overwritten**. This revision adds:
the Step-1 self-resolution block, Brake's `[stated-by-user]` answers where given, the locked exit
convention (`EXIT-CONVENTION-LOCKED.md`), and a re-issued verdict.
