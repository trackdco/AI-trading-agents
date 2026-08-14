# TEACHING LOOP — his rulings on agent disagreements, in order

> ## ⛔ NOT RUNTIME MATERIAL. NEVER READ THIS DURING A SCORED RUN.
>
> This file quotes him **per-trade on the exact days being replayed** — which
> setups he wanted, which entries he'd have taken, what each agent decision got
> wrong. **That is an answer key.**
>
> It leaked once, 2026-08-12: a run session was told to read this file first
> (my instruction, in a paste block) and then fed his verbatim commentary into
> agent briefings. His words: *"it would look at a trade I took, and it would
> tell the agents verbatim what I said on those setups… on live they're not
> going to see verbatim what I said about a trade that already happened."* The
> whole week had to be re-run.
>
> **Two guards now exist.** `.claude/settings.json` denies the Read tool on
> this path, and `scripts/audit_run_leak.py` check F greps every briefing for
> the quoted passages below and fails the run if one appears.
>
> This file is for **prompt authoring between runs** — read it when writing a
> new agent version, never while one is executing. The doctrine an agent needs
> at runtime is already inside its own contract.


The refinement substrate. Every entry is a disagreement between a scored
agent run and his recorded or stated behavior, plus his ruling on it, dated.
Prompt versions cite entries here when they change. Doctrine that graduates
into a hard rule moves to `PLAYBOOK.md`; this file is where it lands first.

Entries are append-only. A ruling that later proves wrong gets a dated
correction entry, not an edit.

---

## T1 — 2026-08-11 · sequential pairs default toward PASS

**Run:** first scored London, session-day 2026-06-25. Predicted before the
trigger fired; confirmed by the run (agent passed his L1).

**His ruling, unprompted:** *"This is the one trade where I wouldn't be mad
about it not taking. I usually instate it has to break another level along
with the MA in the same candle. This was a heavily discretionary reading."*

**Consequence:** same-candle is the rule; sequential completion is discretion
ON TOP of the rule. An agent pass on a sequential pair is within doctrine and
scores as acceptable, never as a plain miss. Already folded into
`PLAYBOOK.md` §2 and the scorer's 2026-06-25 guard. Note the run's other
side: the agent's one take (L1-0318, −1.0R) was ALSO a sequential pair — the
permissiveness cost real R the same morning the ruling landed.

## T2 — 2026-08-11 · rebalance depth: the agent's `waiting_for` was too shallow

**Run:** same. The −1.0R long entered at 03:16-03:18 on "rebalance to the
2m/3m MA complete."

**The tape:** at entry, price sat ~180pt above the 15m MA (29,351) and the 1h
MA (~29,590) was never touched in the entire window (high 29,562.75 at
03:32). His own pre-session words named the depth: *"a rebalance to the
one-hour or around that VWAP+1 level would be good"* — and he took zero longs
that London because that condition never arrived.

**Consequence (pending his final phrasing):** after a large displacement the
rebalance that licenses entry is the one HE names on the higher timeframe
(15m by his displacement rule; 1h when the move is that extended) — a 2m/3m
MA touch alone is not "the rebalance." Open question to him: is 15m the
floor always, and when does it escalate to the 1h?

**ANSWERED, 2026-08-11:** *"The 15-minute is always the floor."* A 2m/3m MA
touch alone never licenses entry. Plus a target rule that was nowhere in the
corpus: when the 15m MA sits only ~1–1.5R from the entry, it is **TP1**, and
the real target is structure beyond it — the near MA is intermediate
structure, not the destination.

## T3 — 2026-08-11 · the missing fib layer, and location-shaped two-sidedness

**Run:** same. The agent passed his 2.45R short on direction: its thesis
licensed shorts only on "hard rejection at 29,655–29,710," which never
printed (high 29,562.75).

**His ruling:** *"We were trading around the 0.5 of the range of that day,
which is why I was convicted in us going down from there. If it were to
continue down it would've been from there or the weekly level. So it wasn't
too far off, just didn't look at fibonacci stuff."* Matches his narration at
the time: *"We're at around that 0.5 level right now… If we are to go back
down, we'd go back down now."*

**Two consequences:**
1. **Briefing gap, structural:** `agent_context` computes NY-range fibs only
   (undefined before 10:00 NY). His Friday fib was drawn on the DAY's range,
   pre-London. London/pre-market theses have been fib-blind by construction.
   Fix requires his marked-swing convention from him directly — the corpus
   warns fib swings are manual judgment (~70pt error from guessing the swing
   on 2026-06-23; within 2pt using his marked swing on 2026-06-26). Do not
   encode a guessed swing.
2. **Thesis shape:** `condition_for_other_side` must be able to license the
   other side by LOCATION (at the marked retrace / at a named level, "it
   would've been from there") — not only by rejection at an overhead cluster.

**CONVENTION SUPPLIED, 2026-08-11 — the London fib layer is now buildable:**
- **When:** London continuation days — Asia moved predominantly one way and
  he is reading London as continuation of that move.
- **Swing:** *"I'll always mark out the fib from the high of the day to the
  low of the day"* — the developing session-day range. Objective inputs; no
  hand-marking needed for this case.
- **Acting levels:** 0.382, **0.5 (the equilibrium)**, 0.618, **0.705** (his
  "OT" level, favored especially in New York; deep retrace that
  statistically holds). Matches the FIBS constant already in
  `agent_context`.
- **The meta-rule:** *"What matters more than the fib itself are what levels
  are in alignment with the fib levels… You can't just take the levels at
  face value."* A fib acts only in CONFLUENCE with other structure plus
  price behavior at it.
- **Behavior flips the read:** a sustained stall at the 0.5 licenses the
  fade; the same 0.5 BREAKING after that long a stall flips him the other
  way (*"I'd be expecting a break to the upside"*).
- **Verified on the tape (2026-06-25):** pre-London H 29,892.75 / L 29,160.5
  → 0.5 = 29,526.6; VWAP mid 29,490.8; his entry 29,492.75; the London
  stall 29,44x–29,562.75 straddled exactly that band. It is a ZONE read,
  not a point read — encode tolerance, not equality.

## T4 — 2026-08-11 · headroom scope — OPEN, awaiting his answer

**Run:** same. The agent's pass on his short also cited headroom: prior-day
VAL in the entry path. He took the trade and price sliced the level.

**The question as put to him:** do all computed levels count as "in the way"
(constraint 7), or only levels this day's tape is actively respecting — that
Friday being the weekly profile, by his own read? Unanswered; do not refine
headroom until he rules.

**ANSWERED, 2026-08-11 — the dichotomy was the wrong shape; his rule is
distance, role, and behavior:**
1. A level sitting AT the entry that price has just broken counts toward the
   trigger, not as obstruction — *"it was kind of sitting right there where
   the entry was… it broke through two levels."*
2. Once IN the trade, a nearby level ahead is a **tripwire**: price slicing
   through it → continue to target; price STALLING at it → *"I'd probably
   close the trade early."* This is a new management clause for the exit
   logic, not only an entry filter — nothing in the corpus carried it.

## T5 — 2026-08-11 · the entry grammar, dumbed down by him — REJECTION IS THE CAUSE

**Context:** volunteered unprompted while the first NY replay leg ran.

**His words:** *"If we can dumb down an entry, what does an entry actually
look like? It's a rejection off of a key level, and then a breakout through
the moving average and something else stacked on top of it, and then an
entry at the retest… We've rejected this key level, whatever it is. Great,
it's 0.5 of the daily range. What am I going to look for then? If price
breaks through the moving average or breaks through VWAP as well, I'm
inclined to take shorts because that rejection is constituting me to go for
shorts. That's really all it is."*

**Consequence — a causality inversion for the trigger prompt.** The doctrine
as first written treated the two-level closure as THE trigger, with
rejection merely "counting toward the pair." His grammar is ordered:
**(1) rejection at a key level → (2) the two-level break as the rejection
proving itself → (3) entry at the retest.** A two-level break with no
rejection story behind it is movement, not an entry. This cleanly separates
his Friday short (rejection at the 0.5-zone/VWAP-mid confluence) from the
agent's −1.0R long the same morning (identical mechanical shape, nothing
being rejected). 0.3.0 trigger frame: *name the level that was rejected, or
lean pass.*

**Two riders, same monologue:**
- **Origin-proximity stop clause:** when the displacement candle's origin
  sits close to the VWAP band, limit at the closest structure (the BB MA)
  but give the stop breathing room beyond the band cluster — *"I'm not
  going to put it past the fact that we might come up and retest the
  Bollinger Band and the VWAP band."* The origin-side variant of the
  existing extreme-on-a-live-level stop rule.
- **Style anchor, for every prompt:** *"I'm never trying to catch these
  gigantic moves. You have to take your piece of the pie and get out… I
  like having a higher win rate."* Guards the agents against drifting
  toward home-run targeting; consistent with the realized 1.5–2.5R
  distribution and the §7 break-even guard.

**Endorsed by him next turn:** *"Whether it's VWAP or POC, that, like you
said, is confirming the rejection to me. That's probably the best way to put
it."* The rejection-first frame is confirmed doctrine for 0.3.0.

## T6 — 2026-08-11 · live latency requirement — stated while watching the loop

**His words:** *"It's definitely going to have to make quicker decisions when
it's actually trading live… It can't sit on the candle for five minutes and
make a decision."*

**Consequence:** the replay loop's weight (per-step leak checks, from-scratch
briefings, screenshots, max thinking effort) is the CALIBRATION profile and
is not the live profile. Live: incremental context, agent calls only at
candidates and re-fires, trigger thinking budget cut to seconds. The
structural budget that makes this viable is his own entry style — a resting
limit at the retest gives ~30–60s to decide, and no-chase caps the cost of
being late at "no fill," never "worse fill." **Decision latency becomes a
first-class measured metric in live-shadow mode, with a budget it must beat
before demo.**

## T7 — 2026-08-11 · macro weighting — the ceasefire example

**His words:** *"When Trump announces the ceasefire between Iran and the
U.S., that's obviously going to be very bullish for the Nasdaq. In an
instance like that, I'm not going to take shorts. That would be retarded…
it's important to be conscious of especially the really important things
happening around the world."*

**Consequence:** the macro lean is not merely an input the thesis may weigh —
when the event is major, obvious, and directional (high-confidence lean,
unabsorbed), the thesis should treat the counter-side as effectively
unlicensed absent exceptional structure. Still not a veto, and the original
constraint stands untouched (an events read that only ever counsels caution
is a failed component). This is the ACTING side of macro he always said
mattered more.

## T8 — 2026-08-11 · agent-only trades with a sound thesis are LEGITIMATE

**Context:** his verdict on the full-day run (4 fills +5.12R, agreement 1/3):
*"It is complete. I don't care if it takes trades that I missed… it waited
for the value area low retest. That's completely fine. I would constitute
that as a completely sane entry… this agent that has been built has a
fucking brain."*

**Consequence for scoring:** an agent-only row (a trade he did not take) is
NOT an automatic miss. It is judged on thesis-soundness and entry sanity,
exactly like his own trades. The agreement axis measures decision quality
against his process, not photocopy fidelity. (The −1R London long remains a
defect — not because he didn't take it, but because its rebalance depth and
rejection story were wrong per T2/T5.)

**In-sample honesty note, recorded the same hour:** the narrated week is the
TRAINING material — the playbook in the agents' prompts was distilled from
these five days and names some of their trades (the 29,369 POC limit, the
Friday day-character row). Zero in-run lookahead (mechanically verified per
row), but on these five days agreement partly measures textbook execution.
The strict walk-forward is post-corpus days (bars run to 2026-07-15) that no
prompt has seen; that is the proof phase after the week calibration.

## T9 — 2026-08-11 · break-entry license: when the thesis ANTICIPATED the resolution

**His answer to the box-resolution question:** *"My whole thesis coming into
the New York day was that we were going to be stalling around that low the
entire day… If I get a break to the upside from here, this price that's been
stalling and hasn't broken here the entire week, then if it breaks to the
upside, I'm fucking going for the break."* And the execution correction:
*"I still limit-ordered on my long, right? I didn't market order that. The
agent waited for it to pull back and the limit order. That's completely
fine, and that's completely valid as well."*

**Consequence:** two licensed entry modes at a level resolution, chosen by
whether the STANDING THESIS anticipated it:
1. **Break entry** — licensed only when the thesis explicitly expected this
   long-held level to resolve this way. Executed as a limit at/just behind
   the breaking level. NEVER a market order, even here.
2. **Retest entry** — the default, always valid, including at resolutions
   (he endorsed the agent's retest wait as "completely valid").
The thesis therefore emits the anticipation (`break_entry`) so the trigger
knows which mode is licensed. Retest-only is not an error; break-entry
without thesis anticipation IS chasing and stays forbidden.

## T10 — 2026-08-11 · ACCEPTANCE defined: a 15m close with a decisive body

**His answer, verbatim core:** *"For me, I want to see a bit of a 15-minute
candle closure… you can't confirm breaking this low and pushing further to
the downside on a one- or two-minute candle. Once the 15-minute candle
closes, that could just be a massive wick… I'd wait for a 15-minute candle
that fucking just blasted through that level, not some wicky kind of
absorption-looking candle."*

**Consequence:** a MULTI-DAY / major level is broken only on a **15m CLOSE
beyond it with a decisive body** — not a 1m/2m close, and not a wick-heavy
absorption candle. Confirmation timeframe scales with the level's
importance; minor intraday levels may confirm on the trading TFs.

**Graded against the tape the same hour (2026-06-26 morning, the 29,290
break the stack flipped on at 09:04 via one 2m close):** the only 15m close
below was 09:00–09:15 at 29,279 — 11pt under on a body/range 0.52 candle —
immediately reclaimed by the next 15m (close 29,360.75), then the 09:30
candle printed body/range 0.11 with a 29,181.5 low: the textbook wicky
absorption/spring. His rule reads that sequence as "the low is being
defended" — which is what happened (+280pt rip). **His definition, applied
cold, outperforms the flip the agent made on this exact morning.** Kills the
open whipsaw (three theses in 8 minutes) as a side effect.

## T9-CORRECTION — 2026-08-11 · there is ONE entry mode: the limit on the retest

**T9 above is WRONG and is superseded by this entry.** (Append-only file: the
error stays visible rather than being edited away.)

**His correction, same day:** *"I want to make it very clear that,
inherently, I'm always entering on a retest. I don't market order."*

**Provenance of the error — important, because it also taints the corpus.**
The market-order entries in the narrated week are **an artifact of a prior
cloud session's validation method, not his process.** During order-flow
validation that session read flow at candle CLOSE while limits fill
mid-minute — an implicit 30-second lookahead — and he switched to market
orders to dodge the artifact: *"limit orders fill in the middle of a minute,
and you're looking at the order flow data at the end of that candle close…
we can't see 30 seconds into the future in the live markets, can we? I went
to market orders to try and mitigate that problem."* He now judges that a
mistake on its own terms: *"it really does greatly affect your average R per
trade… if you just enter off of the displacement instead of a retest, a lot
of the times it's gonna retest one of those structural levels that broke
anyways. That was a bit stupid from my hand. The easiest way was always
retests."*

**Consequences:**
1. **`entry_type` is `limit_retest`, always. `market` is not a licensed
   value for any agent, in any mode, including at a break he anticipated.**
2. What T9's "going for the break" actually means: at a thesis-anticipated
   resolution he ACTS on the break rather than standing aside — but the
   execution is still a limit at the retest of the breaking level. The two
   licensed modes collapse into one; only the choice of which level to limit
   at differs.
3. **Corpus caveat, recorded:** Mon N1's market entry (PLAYBOOK §3, "1.0R at
   market vs 2.33R on the retest — his own critique") is now understood as
   this artifact rather than as his style. The arithmetic in that section
   stands and its conclusion is strengthened.

## T11 — 2026-08-12 · THE FIRST TARGET IS A HARD 1.5–2.5R BAND

**Run:** first 0.3.0 day, session-day 2026-06-21 LONDON. The agent's only trade:
entry 30,753 short, stop 30,783.5 (R = 30.5), targets **30,671 (2.7R)** and
**30,647 (3.5R)**.

**What the tape did:** low 30,687.25 — both named targets missed, T1 by 16.25pt,
and the trade round-tripped. Prior-day VAH sat at **30,699 = 1.77R**, inside his
band, *and was printed in the agent's own briefing*.

**His ruling, verbatim:** *"It was not targeting anything valid on this trade
from what I can see, it easily could've targeted the VAH of the weekly volume
profile and taken a 1.7:1. I have no idea what it was targeting… The first
target should always be within that [1.5 to 2.5R]."*

**Consequence — mechanical, in `tv-trigger` 0.3.1 THE TARGETS:** compute
`R = |entry − stop|`, enumerate every briefing level between entry and the
furthest idea, and `targets[0]` MUST be the nearest level whose distance falls
in 1.5R–2.5R. Runners may sit beyond. **If no structure falls inside the band,
the geometry is wrong — say so and lean `pass`; do not stretch the first target
to make the trade exist.**

**Second defect recorded the same review, NOT yet ruled on — retest degeneracy.**
The entry was a genuine `limit_retest` (limit 30,753, signal close 30,752.50) but
the retest distance was **0.5pt**, and the next bar OPENED at 30,754, already
through it. Angus: *"why did it market order the short and not wait for a
retest?"* — it didn't, but the effect was identical. The doctrine ("limit at the
CLOSEST structure just broken") degenerates whenever the signal candle closes
within a point or two of the level. **Open question for him: a minimum retest
distance, or take the next structure out when the close sits that tight?**

**Orchestrator defect, same trade, recorded for honesty:** the first outcome scan
went fill → stop and recorded a flat −1.0R, skipping the mandatory
intermediate-structure partial (PLAYBOOK §5). Managed correctly the trade is
+54pt on 75% and flat on the runner. Caught by him on review, corrected before
anything was committed.

**T11 AMENDMENT, same day, before the week rerun:** *"if nothing structural fits
that within 1.5-2.5r band that doesnt necessarily mean veto, target a fixed
1.5r."* So the empty-band case sets `targets[0] = entry ∓ 1.5R` labelled
`fixed_1.5R` — it is not a pass and not a licence to reach past 2.5R. The
"lean pass" wording first encoded here was mine, not his, and is superseded.

## T12 — 2026-08-12 · RETEST DEGENERACY — recorded, ruling DEFERRED to after the week

**His observation on the same trade:** *"I noticed that it didn't enter on the
retest of anything. I thought it would have entered on maybe the retest of the
Bollinger Band. Obviously, it closed through VWAP +2 and the Bollinger Band. It
didn't actually enter on a retest of either of those… that just looked like a
market order… 0.5 points from where price closed is practically a market order
lol."*

**The mechanics:** signal 2m closed 30,752.50; the agent limited 30,753 — the
weekly VAH, which was genuinely the closest broken structure at 1.5pt. The 2m BB
MA (30,768.01) and VWAP+2 (30,765.03) sat 12–15pt above; either is a real
retest, and the 2m MA is the level he expected. The next bar OPENED 30,754,
through the limit, so the fill was effectively immediate.

**Status: OPEN.** He deferred it — *"not a big issue, it was a valid trade… we'll
see what we can change when the week has been done."* Candidate shapes: a
minimum retest distance (skip a level closer than ~N pts and take the next one
out), or prefer the BB MA over a profile edge when both are in the just-broken
set. **Do not encode either until he rules.** The week runs on 0.3.1 as-is so
the data is collected under one consistent rule set.

## T13 — 2026-08-12 · PRE-MARKET CARRY: break-even if green, FLATTEN if red, by the 09:30 candle

**His ruling, mid-run:** *"All pre-market trades: if they have not hit take profit
or are in drawdown during market open, I move everything to break even by the
time that the 9:30 candle arrives. The 9:30 candle is so volatile that even if
the trade's going well, you can get stopped out at the click of your fingers…
If it was in drawdown, close it… I wouldn't log that as a -1R if it was floating
profit until market open. It's not fair to judge it against that."*

**The rule, mechanically:** any position opened before 09:30 and still open at the
cash open is resolved AT the 09:30 open —
- **in profit** → stop to break-even (it may keep running);
- **in drawdown** → flattened at the open price.

No pre-market trade carries live stop risk through the 09:30 candle. This extends
PLAYBOOK constraint 11 (which had only the break-even half) with the
drawdown-flatten branch.

**Scoring consequence, which is the half he cared about:** such a trade is never
recorded at its full stop distance. **The run that produced this ruling:**
D21-NYP1-0902, long 30,847, stop 30,790, which ran to 30,968 — 4.5pt shy of its
2.20R target — then rolled over into the bell and stopped at 09:33 for a raw
−1.0R. Under T13 it is **flattened at the 09:30 open of 30,822.75 = −0.44R**.

**Still open, and NOT answered by this:** whether the general intra-trade clause
"move to break-even on touching an intermediate band" has a minimum distance. On
that same trade the only structure between entry and target sat 0.4–0.5R away;
applying the clause literally would move nearly every trade to break-even within
half an R and turn the system into a break-even machine. Needs his ruling
separately.

## T14 — 2026-08-12 · BREAK-EVEN is earned by BREAKING the band, not touching it

**The question put to him:** PLAYBOOK §5 says "move to break-even on touching an
intermediate band even without taking a partial." On D21-NYP1-0902 the only
structure between entry 30,847 and target 30,972.5 was VWAP+2 at 30,874.52 —
0.48R above entry. Applying "touch" literally would move nearly every trade to
break-even within half an R and turn the system into a break-even machine.

**His ruling:** *"in that trade, i would wait for it to break that band before
moving to BE. that means it would then have to break the band it just broke
through to break even me."*

**The rule:** the break-even move is triggered when price **breaks through** the
intermediate band — not when it touches it. The geometry is the point: once the
band is broken and the stop sits at entry on the far side of it, price has to
**break back through that same band** to stop you at break-even. The band guards
the stop. A touch earns nothing.

**Effect on the trade that raised it: none.** The highest print between the 09:04
fill and the 09:30 cash open was **30,873.50 — one point below the 30,874.52
band.** The band was never broken, no break-even was earned, the position was in
drawdown at the open, and T13's flatten stands at −0.44R. (Price did reach 30,904
later, but inside the 09:30 candle itself, after T13's resolution instant.)

**Interaction with T13:** T13 is absolute and independent — at the 09:30 open a
pre-market carry is flattened if red or set to break-even if green, regardless of
whether a band has been broken.

## T13-CORRECTION — 2026-08-12 · the "missed by 4.5pt" detail in T13 was FALSE

**T13's ruling stands unchanged.** This corrects a factual claim in its worked
example, and records the leak it caused.

**What I wrote:** *"D21-NYP1-0902, long 30,847, stop 30,790, which ran to 30,968 —
4.5pt shy of its 2.20R target — then rolled over into the bell."*

**What actually happened:** the trade's true high while open (09:04 fill → 09:30
flatten) was **30,873.50 = +26.5pt = +0.46R.** It never approached its target.
The 30,968 print did not occur until **10:10**, forty minutes after the position
was already closed.

**Root cause:** my orchestrator scan helper measured MFE over a fixed six-hour
window instead of truncating at the trade's exit. Fixed.

**The consequence that matters — it became a LEAK.** That false 30,968 was copied
into the 09:30 and 09:44 briefings as `session_high`. The 09:30 thesis agent read
it and reasoned from it (*"ran to 30968… the long destination effectively
printed"*). The whole NY_AM chain for 2026-06-21 was voided and re-run on
corrected as-of briefings. The LONDON (+1.80R) and NY_PRE (−0.44R) trades are
unaffected.

**Audit gap found, and it needs closing:** `scripts/audit_run_leak` did not catch
this. Check C validates *times* inside briefings; check E validates *prices* in
decision rows. A future **price** embedded in a **briefing** is checked by
neither. E should be extended to scan briefing bodies against the as-of printed
range — which is precisely the shape of clairvoyance it was built to detect.

## T15 — 2026-08-12 · THE 15m-MA FLOOR IS SUSPENDED ON A TREND DAY; the 15m MA is ONE key level, not a gate

**Run:** session-day 2026-06-22 (his Tue 23 Jun). **Zero fills, 0.00R, agreement
0/2.** A 751pt one-way overnight collapse never brought price within **230 points**
of the 15m MA, so the T2 rebalance floor passed every London candidate — including
the one the scorer matched against **a London short he actually took.**

**His correction, verbatim:**

> *"It absolutely needs a trend day exemption… When it's clear that it is a trend
> day I'm going to go about that differently where I'm like, I don't need it to
> reclaim this 15 minute. I'm going to wait for a rejection off of something —
> whether it's a Fibonacci level of the daily range, whatever it is — I'm going to
> wait for a rejection, and then I'm going to look for the closure through the
> moving average stacked with another level, and I'm going to enter on the retest.
> It's simple as that."*

And the deeper diagnosis, which is the more important half:

> *"I think the agents are having this over-importance of the 15-minute and the
> one-hour Bollinger bands. Like I said, my strategy, if I could dumb it down, is
> rejection off of a key level, closure through a moving average, stacked with
> another key level to confirm the rejection as a valid rejection and that price is
> going to continue trading in that direction. **The 15-minute Bollinger band moving
> average is simply just one of those key levels.** We have a lot of key levels."*

His worked hypothetical: *"If we reject the value area low for the day and then we
close through the Bollinger band with maybe some sort of POC, a weekly value area
low, something there, then I'm entering on the retest of that."*

**Consequences:**
1. **On a clear trend day, do not put a 15m-MA reclaim in `waiting_for`.** Name the
   rejection you are waiting for instead — a day-range fib, a profile edge, a VWAP
   band, a prior-day level.
2. **The 15m MA is one key level among many**, eligible as the "another level"
   stacked with the MA closure — never a gate in its own right.
3. **Do NOT over-correct.** *"I don't want to take that information and start over-
   trading like… price in relation to the higher timeframe moving averages are
   important."* On a rotational day the T2 floor still stands. Judging the day's
   character is now explicitly part of the thesis agent's job.

**Also his, on the same trade sequence (day 2, ~10:30):** he would expect the stack
to catch *"those shorts at that VWAP middle band closure through the moving average…
obviously not with the stops at the candle that displaced through, because that
would have been right at the VWAP band — we're going to give it a bit of breathing
room."* That is the origin-proximity stop clause (T5 rider) working as intended.

**His own note on the calibration:** *"I think Tuesday was an absurdly easy day to
trade, so I'm not very happy and that's a miscalibration on my end."*

## T15-A — 2026-08-12 · TWO DETECTOR DEFECTS FOUND WHILE CHECKING HIS 10:30 SETUP

He said the stack should have caught a VWAP-mid rejection short around 10:30 on day
2. It found no candidate between 09:40 and 11:00. Both causes are mechanical, not
doctrinal:

1. **`two_level_check` ended NY_AM at 10:45, not 11:00.** `WINDOWS["NY_AM"]` was
   `(570, 645)`. PLAYBOOK §6.2 says the window runs to 11:00 (confirmed 2026-08-10),
   so any candidate between 10:45 and 11:00 was invisible to a windowed scan.
   **Fixed to (570, 660).** Day-2's scan happened to use `ALL`, so this did not cause
   the miss there — but it would have on any windowed run.
2. **A rejection on an EARLIER candle followed by an own-MA closure later is not
   detected.** The 10:24 bar wicked above the VWAP mid (29,992) and closed back
   below it — a textbook rejection; the 10:30 bar then closed down through its own
   2m MA (29,962). That is exactly his grammar (T5: rejection → break → retest), but
   the detector only pairs a rejection with a closure **in the same candle**, and its
   sequential logic only handles *MA first, second level later* — not *rejection
   first, MA later*. **This is the shape of the trade he expected and the stack
   cannot currently see it.** Open: extend the detector, or have the orchestrator
   surface rejection-then-MA sequences as supplementary candidates.

**Hindsight check, on his instruction** (*"make sure that the agents don't have the
knowledge of what happened on Tuesday"*): confirmed clean. `data/narrated_days/**`
and `docs/CORPUS-narrated-days.md` are Read-DENIED to every agent in
`.claude/settings.json`; every briefing is built from as-of values only; and the
per-day leak audit re-derives this from the committed bars. Day 1's one contamination
was caught, voided and re-run.

## T16 — 2026-08-12 · THE CASH-OPEN BAR IS ~5 MINUTES, NOT 15

**Run:** session-day 2026-06-22 NY_AM. All four candidates were passed, three of
them citing "first few minutes of the cash open" at minutes 3, 6, 9 and 10.

**His ruling:** *"In a day like this we could have taken a long a few minutes after
market open. And I wouldn't be mad at all if the agents took a long there —
probably, if I had to guess, it would have been the 09:38 two-minute candle that
closed through, retested the two-minute moving average, probably stops below the
candle that closed through on the three minute at 09:36. That's a day setup for
me."*

**Consequences:**
1. Constraint 4 covers roughly **09:30–09:35**. From ~09:36 a clean setup is
   licensed and judged **on structure, not the clock**.
2. Do not stack constraint 4 on top of a direction/waiting_for failure to
   manufacture a pass — name the real reason.
3. The example carries three specifics worth keeping: the **2m closure** is the
   signal, the entry is the **retest of the 2m MA**, and the stop goes below the
   **3m** candle that closed through (09:36), not below the 2m signal candle.

**And his confirmation of the other end of that day:** the ~10:30 sequence my
supplementary rejection-first scan surfaced — *"1030-ish was a perfect start,
10:36"* — is the VWAP-mid rejection short he expected, with stops given breathing
room beyond the VWAP band rather than at the displacement candle.

**Method note:** those candidates are invisible to `two_level_check` (T15-A). The
orchestrator now runs a supplementary **rejection-first** scan
(`rejection off a key level → own-MA closure → retest`) alongside it, and both
candidate sets are adjudicated. On day 2 that scan surfaces 08:10, 09:36, 10:30 and
10:40 — including both trades he named.

---

# TRADE-BY-TRADE REVIEW — the narrated week, his eyes on every fill
2026-08-12. He walked all 9 fills and the notable passes. Entries T17–T23.

## T17 — FIRST TARGET BAND: 1.5–2.5R becomes **1.0–2.5R**

**His ruling, explicit:** *"We said the first structural target should be within
1.5 to 2.5R — let's move that to 1 to 2.5, because I'm seeing on a lot of these
trades the closest structural level was 1R but I like around 1.2, 1.3R. Since I
said 1.5 to 2.5 it was searching for levels within that range… on a lot of these
trades, especially on choppy days, it makes sense to not go for as big a
target."*

**Consequence:** T11's band widens at the bottom. The empty-band fixed-1.5R
fallback stays, but will now fire far less often, which also defuses the T11 vs
origin-proximity-stop collision recorded in `ANALYSIS-friday-three-runs.md` §3.
Worked example he gave: the Friday 10:54 short, where the VWAP mid was the
obvious target, the agent reached past it, and price *"got like five points from
his take profit and then it just fucking reversed."*

## T18 — A SHALLOW BOUNCE **IS** A REJECTION ON A TREND DAY

This is the root cause of two of his three complaints, and it answers open
question #2 from `ANALYSIS-friday-three-runs.md`.

**The Tuesday London short he expected (03:24, passed):** the agent's own reason
was *"Bounce (29,950→30,033.5) never reached a thesis-named rejection level —
vwap_m1 sits 80pt higher at 30,113, the fib/VAL/15mMA confluence at
30,228–30,259."* **His read:** *"London opened and came up, just to continue
back down. That made complete sense to me… I wanted us to stall out around this
area anyway, so I don't know why it didn't catch that short."*

**Consequence:** on a trend day the rejection is wherever the counter-trend
bounce *actually stalls* — it does not have to reach a pre-named level. A thesis
that names rejection levels 80–200pt from price has effectively written a
one-sided view, and the trigger then obeys it literally. **Rejection levels in
`condition_for_other_side` / `waiting_for` must sit within reach of current
price, and a bounce that stalls and rolls over qualifies on its own.**

## T19 — DIRECTION GATES MUST NOT OUTLIVE THE TAPE (Tue 09:40)

**The trade:** his Tuesday 09:36 3m / 09:38 2m long. Verified on the tape: the
3m starting 09:36 closed through **both its own MA (29,731.15) and VWAP−1
(29,721.84) in the same candle** — his cleanest same-candle shape. The agent
**saw it exactly**, writing *"09:38 2m candle broke UP through own MA/vwap_m1/POC
and closed at its high"* — then passed it `direction_mismatch`, because the
standing short thesis licensed longs only on *"a 15m close above weekly_low
29,923"* with price at 29,780.

**His read:** *"I'm very disappointed it didn't catch these longs at 9:36…
that would have been a very easy 3R, 4R trade."*

**Consequence:** same family as the Friday NY_PRE defect and T18 — a Tier-1
condition set too far away silently disables a whole direction for the session.
Combined with the `waiting_for` finding, the fix is one rule: **a candidate
carrying a nameable rejection that the standing thesis's own condition cannot
accommodate must escalate `thesis_stale`, not pass.** Tier 1 then re-reads.

## T20 — ENTRY LEVEL: DO NOT LIMIT DEEP INTO THE MOVE (Wed 09:45, −1.0R)

**His critique of the trade the agent took:** the thesis was sound (the agent
cited three rejections of the 15m MA/VWAP+1 zone), but the fill sat at ~29,635,
essentially **at VWAP−2**. *"What was this even a retest of? It was nothing. In
this instance, where we're entering basically a VWAP−2 short, we're basically
wanting it to break VWAP−2 to affirm our trade direction, which is not very
smart… it basically shorted at the VWAP−2 band, and that is just very, very
dumb."*

**What he wanted:** entry on the retest of the BB MA right after the candle that
closed through the VWAP mid + MA, stop above that candle's high. *"That would
have been a beautiful short."* He rates the **stop placement as perfect** and
the **entry as the whole defect**.

**Consequence:** the existing rule already says limit at the CLOSEST structure to
price at the trigger's close. This trade violated it by waiting for further
displacement and then limiting at the far band. **A limit at a level price has
not yet reached, which requires more displacement to fill, is not a retest —
it is a breakout bet, and it is forbidden.**

## T21 — WAIT ~5 MINUTES AFTER THE CASH OPEN (Wed 09:34, −1.0R)

**His ruling:** *"It really shouldn't be taking a trade that early. I'd wait at
least five minutes after market open to let it play out a bit… that can also
just be open volatility. It's not really showing us anything at that point."*

Refines T16 (which established the open bar is ~5 min, not 15): **09:35 is the
earliest entry, and a 09:30–09:34 candidate is passed on the clock.**

## T22 — DO NOT BET ON A RANGE BREAKOUT AFTER A RANGING LONDON (Wed 08:18)

**His critique:** *"We were trading in this range for the entire London session,
and then we were anticipating a breakout of it. To me, that doesn't make sense,
because it's more likely for price to stall at this high and come to the low of
the range again."* He would rather have taken **the short 15 minutes later** —
*"we're not betting on a break of this range, we're saying okay, we've topped
out this range, let's target the bottom."*

**Consequence:** after a session-long range, the default read is FADE the edge,
not anticipate the break. Breakout continuation is tradeable only **after** the
break has happened.

## T23 — TRAIL INTO PROFIT RATHER THAN ROUND-TRIP TO BREAKEVEN

**His ruling on the Friday 10:54 short (0.00R after nearly hitting T1):** *"If I
didn't take profits at the VWAP middle band, I would have trailed my stops at a
minimum into some profits. That makes a lot more sense to me."*

He explicitly credits T14 for saving the 1R — *"good on it for catching the
break-even"* — this is an addition, not a replacement: once a trade has been
meaningfully in profit and stalls short of target, the stop trails **into
profit**, not merely to breakeven.

## THE COMPOUNDING FINDING — the two bad Wednesday trades blocked the good one

Wednesday's NY_AM took 09:34 (−1.0R) and 09:45 (−1.0R), which **consumed the
NY_AM cap of 2**. His third observation for that morning — *"if it missed either
of those trades, there would have been a really good long"* at 09:48, sweeping
the low with a massive wick then breaking VWAP−1 and the MA in the same candle,
*"an easy 1.5R… you could have targeted VWAP+1, that would have been a 3.4"* —
was therefore **unreachable regardless of merit**. The log confirms it: four
adjudications that day, the last at 09:45.

**So a bad early take costs more than its R.** It spends a scarce slot. This
strengthens T21 and T20 well beyond their −1R face value, and is an argument for
the trigger being *more* conservative early in a window than late.

## WHAT HE APPROVED, recorded so it is not tuned away

- **Mon London short, +1.8R** — *"a good short. It closed through VWAP+2 and it
  also closed the moving average."*
- **Mon NY long, +1.67R** — *"definitely a good long. Perfect entry on the retest
  of the moving average… I have no corrections to make there."*
- **Mon pre-market long flattened before the open, −0.44R** — mild dislike of the
  setup, but *"it's good that it flattened it before market opened. It needed to
  do that."* T13 endorsed.
- **Wed London, no trades** — *"just a straight chop fest, so completely fine."*
- **Thu pre-market, no trades into 08:30 news** — *"I don't want to trade
  pre-market when there's high-impact news like that. That's just stupid."*
- **Thu open dump, not traded** — *"it didn't do some retarded shit. That's great."*
- **Tue 10:40 short, +2.16R** — sound trade, entry criticised (see T20 family);
  *"the stop placement was actually perfect."*
- **Fri 09:58 long, +1.95R** — good but late; he wanted the 09:42 entry, which
  would also have pre-empted the later entry.

## T24 — 2026-08-12 · CORRECTION TO ME: no early-window conservatism

I proposed, after finding that Wednesday's two bad takes consumed the NY_AM cap,
that the trigger should be "more conservative early in a window than late."
**He rejected it outright:**

> *"I disagree with that. I think 9:40 to 10:10-ish is usually the window where
> we get the best trades. I'm just saying wait five minutes after the open so
> that volatility noise from the open doesn't affect a trade… Don't be more
> conservative at the start of the window, because I think that's dumb. The
> first half of the window is not significantly better than the second half, in
> my opinion, but it's just better."*

**Consequence:** T21 is a **clock buffer only** — 09:35 earliest, because the
first five minutes are noise. It must NOT be generalised into a caution gradient
across the window. Encoded explicitly in tv-trigger 0.3.5 constraint 4, with his
correction quoted inline so a later version cannot quietly re-introduce it.

The compounding finding about the cap still stands on its own: a bad take spends
a scarce slot. The fix for that is taking *better* trades (T20's entry rule,
T5's rejection-first test), not taking *fewer early* ones.

## T25 — 2026-08-12 · SAFEGUARDS ON THE ESCALATION RULE (his catch)

I flagged the risk when shipping 0.3.5 — *"the escalation rule could over-fire
and turn Tier 1 into a coin-flipping machine"* — and shipped it anyway with only
observability, no limit. **His response:** *"if u knew that might happen id hope
u add a safegate for it planning for that."* Correct, and the ordering was
backwards: a named failure mode gets a guard in the same change, not a metric to
watch it happen.

**Safeguards added, both tiers:**

*Trigger side (`tv-trigger` 0.3.5):*
1. **Budget** — at most 2 escalations per window; spent budget logs
   `escalation_budget_spent`. Ceiling of 6 re-reads a day, not 30.
2. **Ratchet** — never escalate the same level + direction twice in a window.
   Once Tier 1 has ruled on that argument it is settled.
3. **Qualification** — only a candidate it would OTHERWISE TAKE may escalate:
   `rejected_level` populated, a **same-candle** two-level break behind it.
   Sequential pairs never qualify (they already default toward pass under T1).
4. **Mechanical gates are never escalatable** — window bounds, the cap, news
   blackout, the 09:35 buffer, an open position.
5. **One per candidate**, no re-framing.

*Thesis side (`tv-thesis` 0.3.5):* an escalated re-read **may** widen or relocate
`condition_for_other_side`, clear a spent `waiting_for`, add the escalated
direction as a licensed second side, and move targets/invalidation. It **may
not** flip `bias` outright — that still requires the ACCEPTANCE evidence (a 15m
decisive-body close) or a structural re-fire event — and may not abandon a
`stand_aside` unless the escalated bar IS the resolution it was waiting for.

Both tiers emit the ratio: `escalation_response` is `accommodated` or
`reaffirmed` on every escalated re-read. **Mostly reaffirmed ⇒ the trigger's bar
is too loose, raise the qualification. Mostly accommodated ⇒ the thesis
conditions were the real problem.** The number decides, not either agent.


## T26 — 2026-08-12 · THE STEERED RUN — my instruction caused it

**What happened:** the whole 0.3.5 week run was contaminated and restarted. The
run session was reading his per-trade commentary and feeding it to the agents.
*"It would look at a trade I took, and it would tell the agents verbatim what I
said on those setups. I had to restart the entire week run. Very frustrating
because, obviously, on live they're not going to see verbatim what I said about
a trade that already happened."*

**Cause: mine.** My paste block for the 0.3.5 re-run opened with *"read
docs/TEACHING-LOOP.md first"* — and by then this file contained T17–T24, his
verbatim per-trade review of the exact five days being replayed. I built the
answer key, then told a run session to open it.

Same class as the 0.3.4 prompt contamination, and the same reason it is worse
than a replay leak: timestamps stay clean, checks A–E all pass, and the score
silently measures recall.

**Three guards, all now in place:**
1. `.claude/settings.json` denies `Read` on TEACHING-LOOP.md, the analysis docs,
   and the corpus — the run session cannot open them even if instructed to.
2. `audit_run_leak.py` **check F** extracts every `*"..."*` passage from the
   refinement docs (110 of them today) and greps each briefing for it. Verified
   both ways: fires on a planted quote, clean on the real briefings. Its first
   version silently failed the planted case because JSON escapes newlines as
   `\n`; the negative control caught it, which is the entire argument for
   running one.
3. **Paste blocks for scored runs must never cite the refinement docs.** The
   runbook and the agent contracts are the only reading a run session needs.

**Standing rule:** doctrine flows into agents through their **contracts**, at
version-bump time. It never flows through a briefing, and never mid-run.

## T27 — 2026-08-13 · FIRST TARGET IS A PREFERENCE ORDER (corrects T17)

T17 as I implemented it was a flat 1.0–2.5R band, and it silently relaxed entry
qualification: 9 trades whose first target sat under 1.5R went 33% WR for
−2.26R, against 36% WR / +2.83R for the rest. Nearly identical accuracy — the
band did not worsen the reads, it capped what a correct read could pay.

**His correction:** *"Preferenced first target is 1.5–2.5R, but if there isn't
anything within that, target something between 1–1.5 instead of further. The
reason I went to one is because I saw some losers that would've hit in the 1R
range."*

**Order, strict, first match wins:** prefer `1.5–2.5R`; if empty drop DOWN to
`1.0–1.5R`; if still empty use a fixed 1.5R. **Never reach past 2.5R.** A
sub-1.5R target marks a thinner trade — weigh toward `take_light` and expect
the manager to work harder.

## T28 — 2026-08-13 · INTRA-TRADE MANAGEMENT IS A JUDGEMENT — new tier `tv-manage`

**His ruling:** *"If I see significant resistance at +1, I'll probably move to
break even. If it breaks through +1, I will trail stops, because that then means
the trade favours me even more than when I entered — it would have to break
through VWAP+1 again to the upside to stop me out. I trail, take targets, and do
these things based on how the trade is favouring me in the moment. That's gotta
be an intra-trade judgement call."*

**The evidence for building it:** the 0.3.5 week's **11 of 12 losses were clean
−1.00R full stop-outs** — nothing cut, BE'd or trailed on the way to being
wrong — while his own narrated week contains −0.46R losers he managed down. At
a 35% hit rate that difference is the whole expectancy.

**Core doctrine:** an intermediate level is a QUESTION with two opposite
answers. **Stall/rejection there → tighten (break-even, or exit if decisive).
Clean break through → TRAIL BEHIND IT**, because the level now sits between
price and the stop and must be reclaimed to hurt the trade. The second half is
the one that gets forgotten: a broken level is new protection, not just
progress.

Fires on `intermediate_level_reached`, `intermediate_level_broken`,
`tp1_reached`, `stalling`, `pre_cash_open`, `window_closing`. Emits `favouring:
more|same|less` as the spine of the verdict. Orchestrator enforces
**stops only ever tighten**.

## T29 — 2026-08-13 · TRIGGER-DRIVEN REPLAY, not bar-by-bar

*"I don't need the agents to go proper minute by minute — I want them to
replicate how I would do replay. I can get through a week in 30 minutes."*

Pre-scan candidates mechanically, jump to each decision minute, adjudicate, and
while a position is open jump to the next mechanically-computed management
minute. **Leak-safe:** the scan applies the trigger definition to bars and
conveys no outcome — it is the information his eye gets while scrubbing — and
the agent still sees a chart truncated at its own decision minute with the
no-leak check run at every landing. One guard: briefings stay per-decision, so
the thesis is never told how many candidates the day holds.

---

# DEEP SCENARIO INTERVIEW — 2026-08-13. Entries T30–T36.

## T30 — THE FLUSH TEST: you may counter-trade a STRUCTURED trend, never a FLUSH

**The single most important entry filter in this file, and the likeliest cause
of the 0.3.5 week's 35% win rate.**

> *"If it's a trend day — there was one day, maybe Wednesday, where it took a
> long in London even though the whole of Asia sold off like 400 points. In an
> instance like that, yeah we might have a mechanical entry trigger there, but
> I'm not going to try fade the trend. When it's been dumping the entire day I'm
> much more inclined to just continue to the downside until we have actual signs
> of reversal — not just this fucking 2-minute closing through a POC and a moving
> average. Maybe one in 10 times you'll catch the start of a massive reversal,
> but it's a matter of probabilities."*

**But this is NOT "never counter-trade a trend."** He explicitly approved a short
on a bullish trend day, and drew the line himself:

> *"It did take a pretty good short where it closed through VWAP+2 and the moving
> average… in that instance price was making higher highs and higher lows, it
> wasn't just flushing to the downside. It wasn't like that London reversal that
> tried to take, which was just going down and dumped 400 points."*

**So the test is FLUSH vs STRUCTURED, not trend vs no-trend:**

| shape | what it looks like | counter-trade? |
|---|---|---|
| **FLUSH** | one-way, nearly every 5m/15m candle in the same direction, little retracement | **NO.** Only trade WITH it. A 2m close through a POC and an MA is not a reversal signal in a flush. |
| **STRUCTURED trend** | trending, but making higher highs and higher lows (or LH/LL) — it retraces and rebuilds | **YES**, at a level, on a rejection. This is normal work. |

**Measured on the tape, and it separates cleanly.** 15m path efficiency
(|net move| ÷ total absolute 15m travel) over Asia into the London open:

| session-day | Asia move | 15m down/up | path eff | shape |
|---|---|---|---|---|
| 2026-06-21 | +160 | 18/18 | 0.14 | rotational |
| **2026-06-22** | **−693** | **27/9** | **0.61** | **FLUSH** |
| 2026-06-23 | +53 | 18/18 | 0.04 | rotational |
| 2026-06-24 | +16 | 16/20 | 0.02 | rotational |
| 2026-06-25 | −238 | 23/13 | 0.14 | rotational |

**And the agent proved his point for him on the flush day.** Two London trades,
two minutes apart, opposite directions:
- **03:22 LONG** at 30,032 — a reclaim off the session low near a confluence.
  **−1.0R.** This is the trade he is describing.
- **03:24 SHORT** at 30,006 — fading the bounce, WITH the flush. **+1.76R.**

**Rule:** the thesis emits a `flush` flag when the session so far is one-way at
high path efficiency. Under `flush`, counter-trend candidates are passed
regardless of trigger quality, and only with-trend entries are licensed —
*"until we have actual signs of reversal,"* which per T10 means acceptance
evidence on the 15m, not a 2m closure.

## T31 — STOP PLACEMENT IS DECIDED BY WHERE THE CANDLE OPENED

Sharpens the origin-proximity clause into its actual mechanism.

> *"I'll only put it higher if, for example, it broke through the moving average
> and a VWAP+1 band but the candle started around where the +1 is — I'm going to
> put it at the high and give it some breathing room, because I'm entering on the
> retest of the Bollinger Band but there's a very good chance it could come up and
> wick that VWAP+1 before returning down. Whereas if the 2-minute candle that
> opened was healthily above VWAP+1 and the Bollinger Band moving average before
> displacing through them, I'm fine to put my stop at the high of the candle."*

**The test:** how far is the trigger candle's OPEN from the levels it broke?

- **Origin AT/NEAR the broken level** → the level is still live and price can
  wick back to it. Stop goes **beyond the candle extreme with clearance past
  that level.**
- **Origin HEALTHILY BEYOND the broken levels** → the candle displaced from
  clear air. **The candle extreme is a sufficient stop.**

**This is structural, not a volatility multiple.** *"That changes based off of
the structure and the criterion around the entry."* Volatility explains why
Thursday's 90–118pt stops were right; it does not set the stop. Measured across
the 0.3.5 week, stop ÷ average 2m range ran **0.18× to 3.13×** (median 1.28×) —
the outliers are structural mistakes, not volatility adaptation. A 10pt stop
where candles average 54pt (0.18×) is not a stop.

## T32 — "SIGNIFICANT RESISTANCE" IS 3–5 MINUTES AND MULTIPLE TESTS

> *"Three to five minutes. One candle is too little to tell. It's like, okay,
> we've wicked around on the one minute at least — we've tested this level a few
> times now and we're not seeming to be able to break it. I would be happy to
> move that to break even, even if it ends up running. I'd be okay with that."*

**Definition for `tv-manage`:** a stall is **3–5 minutes at the level with
multiple tests/wicks and no close through.** One candle is never enough. And the
regret is explicitly accepted — *"even if it ends up running, I'd be okay"* —
so a break-even that costs a winner is CORRECT, not an error to tune away.

## T33 — A SECOND SETUP IN THE SAME DIRECTION IS A SCALE-IN, NOT A NEW TRADE

> *"I'm going to take the 03:20 setup if it's good and warranted. If we get
> another one at 03:40 it really depends — am I moving in profits right now? If
> I'm already up 20-30 points from my long at 03:20, I am happy to scale my
> position a bit if another entry fires at 03:40, and I'll trail my stops
> accordingly to where it would invalidate that 03:40 setup. Say I've been five
> micros from the 03:20 entry and it goes up 20 points and gives me another entry
> at 03:40 in the same direction — I might enter two or three micros extra on the
> retest of that entry, and I will trail my stops according to where that trade
> would have to get invalidated. Either way I'm going to end up in some profits.
> Another good setup firing at 03:40 would be affirming my trade direction."*

**Three conditions, all required:** the original position is **in profit**; the
new setup is **same direction**; the new setup is **independently valid**.

**Then:** add a smaller clip (his example: +2–3 on an existing 5, so roughly
half), and **move the whole position's stop to the NEW setup's invalidation**.
This is why he ends up in profit either way — the add pays for the trail.

**This is not a second trade.** It does not consume a second slot against the
window cap; it is one idea, scaled. Do NOT scale into a losing position.

## T34 — A STOP-OUT DOES NOT KILL THE THESIS

> *"No, it doesn't necessarily kill the thesis. There are a lot of instances
> like that where I get stopped out and then I retake moving the same direction
> and it plays out. But that's all about market read — which is why I say you
> can't stick to one thesis from market open and only take trades that are
> affirming that trade direction."*

Re-entry in the same direction after a stop-out is legitimate when a fresh valid
trigger appears. The stop-out invalidates the ENTRY, not necessarily the READ.
Subject to the window cap, which counts fills.

## T35 — PARTIALS ARE SET BY CONVICTION (corrects the fixed 75%)

The recorded default was 75% at TP1 always. **It is conditional:**

> *"That comes down to the conviction behind the setup. If I think this setup's
> really good, I'll probably only take 50% at TP1. If the trade's really bad I
> might exit the whole position at TP1 and just target that low-hanging fruit of
> 1.5R… If there's a really good setup I still take multiple take profits, but I
> might only exit 50% at TP1 and hold the other 50% all the way. And if it's a
> pretty mid setup I will exit the whole thing at the first take profit — I won't
> even have multiple take profits."*

| conviction | structure |
|---|---|
| **high (A)** | **50%** at TP1, hold the rest to the full target |
| **normal (B)** | ~75% at TP1, trail the runner |
| **low / mid (C)** | **100% out at TP1.** No runner, no second target — take the low-hanging 1.5R |

So the trigger's `conviction` label now drives management, which makes it
load-bearing rather than decorative.

## T36 — GREEN NEAR TARGET INTO THE CASH OPEN: TAKE IT

Refines T13 (break-even if green, flatten if red before 09:30).

> *"The minutes leading up to market open in pre-market, it slows down. And then
> a couple of minutes out, a lot of the time it gets very volatile. So if I'm
> green at 09:25 I'm like — I don't want to move to break even, because there's a
> very high chance I'd just get break-even'd even if it hit my take profit. I
> don't want to gamble on whether the market open candle is going to break-even me
> or smash my take profit first. That's literally pure gambling. I would just take
> the profit where it is."*

**Rule:** a pre-market position that is green and NEAR its target approaching
09:25–09:30 is **closed for the profit available**, not carried and not merely
moved to break-even. Break-even is for a position with real distance still to
run; a nearly-complete winner is banked.

## T37 — CONVICTION IS THE SIGNIFICANCE OF THE LEVEL BEING REJECTED

The rubric A/B/C has driven sizing since 0.1.0 and partial structure since T35,
and until now nothing said what produced one. His answer:

> *"What defines an A from a C would be how significant the key level it is
> rejecting off of is. If we were to reject off the weekly value area low and
> actually show resistance there and affirm that rejection, and then we close
> through the VWAP / the moving average — that's going to be a high-conviction
> trade for me… The entry is still mechanical: closure through the moving average
> plus another structural level at once. What matters more is how significant the
> thing it is rejecting off of is. What kind of merit does that level have?"*

**So the trigger is mechanical and constant; the CONVICTION comes entirely from
the rejected level's merit.** This closes the loop opened by T5 — rejection is
the cause of the trade, and the *significance* of what was rejected is the grade
of the trade.

**And counter-trend caps the grade at C, by his own example:**

> *"C is definitely like if I'm kind of fading the trend. That London short it
> took when it went through VWAP+2 and the moving average would definitely be a
> C, even though structurally, yes, a broken VWAP, a broken moving average. That
> being said, I'm kind of fading the trend, so I'm not targeting as big of a
> move. I'm just taking my piece of the pie and getting out."*

**Level-merit hierarchy** (his own ordering, from what he names as significant):

| tier | levels | grade contribution |
|---|---|---|
| **highest** | anchored **weekly** profile edges (weekly VAL/VAH/POC), weekly high/low | A |
| high | prior-day VAL/VAH/POC, prior-day high/low; a fib in confluence with any of these | A/B |
| middle | developing daily profile (POC/VAH/VAL), VWAP ±1/±2 | B |
| low | VWAP mid alone, the BB MA alone | C |

**The BB MA is the TRIGGER, not the rejection.** A trade whose only "rejected
level" is a moving average is by definition a C.

**Grading, in order:**
1. Counter-trend (fading a structured trend) → **C, always**, regardless of level.
   A flush is not tradeable counter-trend at all (T30).
2. Otherwise start from the merit tier of the rejected level.
3. **Confluence raises it** — two or more levels of different types stacked at the
   rejection, or 2m and 3m closing together (T38).
4. **A weak rejection lowers it** — a shallow touch, no visible resistance, a
   level that price has already sliced through earlier in the session.

## T38 — WHEN 2m AND 3m DISAGREE, THE HIGHER TIMEFRAME RULES

> *"The higher the time frame, the better. When both timeframes are in alignment
> that's high conviction for me — if the 2-minute closes and the 3-minute closes
> the next minute, that is high conviction right there. If they disagree, it's
> more about what the higher timeframe says. If the 3-minute closes through
> cleanly and the 2-minute doesn't, I might — if I'm not fully confident — wait
> for the 2-minute to close through and enter off the 2-minute. That being said,
> on a day where I'm confident in my thesis and the levels I'm targeting, I might
> just enter off the 3-minute. The 3-minute rules over the 2-minute."*

- **Both close (within a minute of each other) → conviction raiser**, already
  recorded, now confirmed as a grade input.
- **3m clean, 2m not → the 3m governs.** Two licensed responses: **wait** for the
  2m and enter off it (the default when conviction is not high), or **enter off
  the 3m** when the thesis and levels are strong. State which and why.
- **2m clean, 3m not → the weaker case.** The higher timeframe has not confirmed;
  treat as lower conviction, and prefer to wait.

## T39 — FOMC: NO NEW YORK. A HARD RULE.

> *"I do not trade FOMC. So if there's FOMC in the afternoon, I just sit out of
> New York completely."*

Not a caution, not a size reduction — **NY_PRE and NY_AM are closed entirely on
an FOMC day.** London is unaffected. This joins the news blackout as a
mechanical gate the macro agent owns, and it is not escalatable.

## T40 — MONDAY IS A GAP DAY, AND LONDON NEEDS A REASON

> *"I'll only trade London on a Monday if there's a massive new week opening gap,
> and I'm going to follow whatever I'm being given. I'm inclined to think that gap
> will be filled within the week, or the next week at the longest. The gaps always
> get filled eventually. How I judge a Monday is kind of just based off what
> happened in Asia: is there a big new week opening gap? Where are my levels?"*

- **Monday London requires a significant new-week opening gap.** Absent one, the
  default is no London trades.
- **The gap is a destination**, and a durable one — his horizon for it filling is
  the week, not the session.
- Monday's read is built from Asia's behaviour and the gap, not from a prior
  session's momentum.

## T41 — NO RISK CAPS YET. DELIBERATE, AND HIS CALL.

> *"I'm not worried about the proper risk parameters right now. I just want to
> see how the agents are making decisions. There's no point putting caps on it
> and stuff right now, because we see what the numbers say and then we make
> educated conclusions from that… the more trades we can judge the agent's
> judgment against, the better for us right now."*

**Do not implement daily loss limits, stop-for-the-day rules, or the
London→NY sit-out.** His own behaviour is known — *"usually if I win a really
good trade in London I might take one trade in New York; if I win a really good
trade in New York, I'm probably not going to take another"* — and the
London→NY decision turns on *"the quality of what New York is offering."*

**Both are recorded and deliberately NOT encoded.** Sample size for judging
decision quality is worth more right now than realistic risk behaviour. Revisit
once the per-trade judgement is close.

## T42 — THE FIXED-1.5R FALLBACK IS AN EDGE CASE, NOT A BRANCH

> *"If the setup is decent but the structural levels are just a bit out of my
> ballpark, I'd rather just take the fixed. I don't think there's any instance
> now where we say it's a fixed 1.5–2.5 preference — if you can't find anything
> there, look for 1 to 1.5. There are very, very few instances where it will not
> find anything between 1 and 2.5R."*

Confirms T27's order and demotes the fallback: with the band spanning 1.0–2.5R,
finding nothing is rare. If an agent is using the fixed target often, that is a
**level-computation defect to investigate**, not normal operation.

## T43 — TOO MANY LEVELS IN THE PATH: don't take it, or break-even at the first

Extends constraint 7 (headroom) from "the next level must not sit immediately in
the way" to the cumulative case.

> *"If there are three levels in the way, it's just very strict risk management:
> if the target hits the first level, go straight to break even, because at that
> point it's a trade probably not worth taking. If there are too many levels in
> the way of the take profit, then it's not worth it, in my opinion. I don't
> think that's a very realistic instance."*

**Two clauses:**
1. **Entry:** a path crowded with structure between entry and target is a reason
   to **pass**. Headroom is not only about the *next* level — it is about how
   much has to break for the trade to work.
2. **Management:** if such a trade is taken anyway, **break-even at the first
   level reached**, immediately — not on a stall, not after 3–5 minutes. The
   ordinary stall test (T32) does not apply; the crowded path already told you.

He expects this to be rare. Frequent firing means the level set is too dense or
targets are being placed too far.

## T44 — FILLS ARE BINARY, AND A LIMIT THAT MISSED ITS MOVE IS DEAD

> *"I never really get half-filled on a chart. You either get filled or you
> don't. It's not something that needs to be worried about too much. We're pretty
> conservative with our fills — we target the closest structural level for the
> retest. Obviously, if it runs to our take profit before entering, then at least
> take profit one. We're not fucking taking that."*

- **No partial-fill modelling.** Filled or not filled. The replay's
  touch-equals-fill model is acceptable to him, and conservative entry level
  selection (closest structure) is what keeps it honest.
- **NEW CANCEL CLAUSE, sharper than the existing one:** the standing rule is
  cancel if price reaches the next structural level before filling. This adds:
  **if price reaches TP1 before the limit fills, the trade is dead — cancel it.**
  The move happened without you. Chasing it is taking a trade whose reward is
  already spent.

## T45 — THE SUCCESS CRITERION IS REASONING, NOT R

**The most important thing he has said about how to judge this, and it reframes
what the reports should contain.**

> *"I think the biggest thing would just be me going through trade by trade and
> looking at the journal, looking at what the agents were thinking when it was
> taking those trades, win or loss. If I can reason with that thinking, then I
> would be happy. Over this week, you saw how much I caught — I don't expect it
> to catch that exact amount, simply because I can trade. If we can even get it
> just taking the same trades, taking its own trades with the right thesis behind
> them, the right thought process, then I would be quite happy."*

**Consequences:**
1. **The primary artifact of a run is the JOURNAL, not the scorecard.** Per
   trade: the standing thesis, why this candidate, the rejected level and its
   grade, the stop rationale, every management call and its reasoning — in the
   agents' own words, win or lose.
2. **A losing trade with sound reasoning is a PASS**, and a winning trade with
   incoherent reasoning is a **failure**. R is the sanity check, not the target.
3. **He does not expect it to match his R.** *"I can trade."* The bar is its own
   trades with the right thought process behind them.
4. So the review loop is: he reads the reasoning, and where he cannot reason with
   it, that becomes the next teaching-loop entry. That is exactly this file's
   purpose, and it means **the journal must be readable by him without tooling.**

---

## T46 — a rejection is BEHAVIOUR at the level, and the higher timeframe resolves it
**2026-08-13, deep interview round 4.** Asked what separates a real rejection
from price merely arriving at a level and turning.

> *"The best way to answer is not just to reach the level and then turn, but what
> are the price characteristics at that level? Did it slow down, did it wick
> around that level, and then go the other way? I think that's probably the good
> explanation."*

Two characteristics: **slowed down**, and **wicked around it**. Then away.

Given three shapes at a level — (A) one long wick through that closes back, (B)
repeated tests over ~8 minutes each failing, (C) two closes through then a
reclaim:

> *"Example A and B are definitely the ones where I'd be higher conviction. With
> example C, yes, it's still valid, but I wouldn't say price specifically rejected
> off of our key level."*

**And the half that matters most — C on the 2m is routinely A on the 15m:**

> *"The higher time frame will also matter, because if the 2-minute can close
> below it but the 5-minute can't, that could just look like a massive bottom
> wick, right?… I care more about those days in New York where I'm short off of
> the VWAP middle band and the 0.382 fib. The 2-minute candles are closing above
> and below that, but if we look at the higher time frame, like a 15-minute, it
> was just a big wick, and it couldn't close through."*

So **2m chop around a level is not evidence against the level.** Price closing
both sides on the 2m while the 15m prints a wick that cannot close through is his
*highest*-conviction rejection, not a mess to avoid. Never grade a shape C until
you have looked up a timeframe.

→ `tv-trigger` 0.4.2: new section WHAT A REJECTION ACTUALLY LOOKS LIKE, with the
three shapes and the HTF resolution rule; conviction rubric point 4 now grades
behaviour, not just level merit. Runbook §3.4: the trigger briefing must carry
5m/15m closes-through and wick-vs-body at every candidate rejection level, or the
agent cannot see the distinction at all.

## T47 — an absurdly tight structural stop means the wrong level was read
**2026-08-13.** Put to him: structure says an 8pt stop while 2m candles run 25.
Take it, widen it, or skip it?

> *"I would widen it. How would that be an 8-point stop? Anyway, that doesn't
> really make sense."*

Both halves are the ruling. **Widen** — and the pushback is the diagnosis: a stop
that tight against that volatility means invalidation was read at the wrong
level, not that the trade is untradeable. It lives further back, usually the far
side of a stacked cluster rather than one member of it.

**Passing because the stop came out tight is not licensed.** Widening changes R
and may drop the first target from 1.5–2.5R into the 1.0–1.5R rung — that is the
honest consequence and the preference order already handles it.

→ `tv-trigger` 0.4.2: floor of ~0.75× the trailing average 2m range (my number,
set to clear the pathological tail without moving his real stops, whose median
sat at 1.28×; his measured spread was 0.18×–3.13×).

## T48 — going again at a level that stopped you out is a conviction UPGRADE
**2026-08-13.**

> *"I can go again at the same level if I get stopped. If we took the longs and it
> got stopped out, but then came down and rejected the value area low again before
> giving the setup — if anything, I'm actually MORE confident in that trade."*

A stop-out does not retire the level. The second attempt is graded at or above
the first, not below: the level was tested harder, under conditions that already
proved a shallow read wrong, and held.

Requires all three fresh — rejection, two-level break, retest. It is not a
resumption of the old order.

Two mechanical riders: it **burns a window slot** (caps count fills — *my*
conservative reading of an ambiguous answer, one word from him flips it), and the
**escalation ratchet does not govern it** (that rule bounds escalations, not
entries).

→ `tv-trigger` 0.4.2: GOING AGAIN AT A LEVEL THAT ALREADY STOPPED YOU OUT.

## T49 — the orchestrator has NO trading discretion
**2026-08-13, unprompted, at the end of the round.**

> *"Please make sure that is agent-run, the orchestrator, as in my terminal.
> Claude is not fucking steering it or doing any of that bullshit."*

The second time this has cost something — a week was thrown away when the
orchestrator pasted commentary into an agent's context. Until now the defence was
a **file** deny-list plus audit check F, which catches quoted prose but cannot
catch the orchestrator simply *deciding something itself*.

The orchestrator moves the chart, computes numbers, calls agents, enforces
mechanical invariants, writes rows. It decides nothing about a trade. Four abuses
named: overriding a verdict; re-asking a candidate with a re-worded briefing
(steering even when every fact is true); editorialising in a briefing (free text
must be mechanically derivable); and letting anything learned after a decision
shape it.

**And the same bar applies to him.** Anything he says mid-run that reads as an
opinion on a pending decision gets ignored and named — on live he will not be
there to say it. Between decisions his rulings are welcome and become entries
here; inside one they are contamination.

→ `docs/RUNBOOK-replay-scoring.md` §0c SEPARATION OF POWERS, with the
decides-what table; restated in the Phase C paste block.

---

## T50 — in a range, the middle is dead
**2026-08-13, shakedown review.** On the choppy London he reviewed: *"I
probably wouldn't have traded London at all, unless we were topping out the
range or bottoming out the range and just trading within that range."* And on
the day's high: *"we were failing to break this high since Asia around 8pm —
it was also the weekly value area high. Even if I were to trade chop like
that, I'm probably not looking for longs. I don't want to break a level that
has so much resistance ahead of it."*

The 03:24 loser is the type specimen: a C-grade fib in the middle of the
range, in chop, taken light. Range-day entries come off the extremes or the
shelves that bound them; a lone mid-range level is not an edge.

**AMENDED same day:** *"T50 should only apply when it's a verifiably choppy
day, just like Monday London."* Scoped to days the standing thesis itself
reads as chop/rotational; silent on trending or still-forming days.

→ `tv-trigger` 0.4.4, constraint 9.

## T51 — FLATTEN before the cash open. Not break-even. Everything.
**2026-08-13.** Reviewing a runner break-even'd at 09:28 that the open then
paid: *"It didn't flatten the trade at market open, so I'm not very happy
about that. Yes, in this instance it paid off — the open volatility went in
our direction — but always remember, we go to flatten trades before the
market open. Maybe it would have cut some R, but we just have to be
realistic."*

SUPERSEDES T35's break-even-if-green branch. Green, red, near target or far:
banked at the decision price. Note the shape of the ruling: he watched the
gamble PAY and ruled against it anyway — same character as the 29.2R
Thursday. Do not learn from the payout.

**AMENDED same day:** the deadline is hard — *"It needs to be out by
9:29:59."*

→ `tv-manage` 0.3.1 `pre_cash_open`; runbook §3.6.

## T52 — NY_PRE entries cut off at 09:05
**2026-08-13.** On the 09:28 attempt: *"I would never enter that close to
market open — that's just stupid. If I'm not in a trade around 5 to 10 past
9, I'm not taking another trade in pre-market... price will slow down and
then get really volatile in the last couple minutes, and that's not a risk
that I want to take."*

09:05 was chosen as the conservative end of his stated 09:05–09:10 zone —
my pick, flagged as such. **AMENDED same day, his word: 09:10.** (*"Make the
NY pre-entries 9:10."*) Entries only; open positions belong to the manager
(T51).

→ `tv-trigger` 0.4.4, constraint 4b.

## T53 — a second same-direction setup in profit is a SCALE-IN, not a new trade
**2026-08-13.** On the 08:32/08:36 pair (four minutes apart, same direction,
same rejected shelf): *"If that setup fired on the three-minute with that
many confluences, I definitely would have scaled my position there and run it
out to where it actually ended up going."*

Trigger adjudicates the fresh candidate as normal; a take is routed to
tv-manage as `second_setup` — smaller clip, whole-position stop to the new
setup's invalidation, ONE position, NO window slot consumed. (The no-slot
clause is my inference from "one position"; his word flips it.) Never into a
losing position.

**AMENDED same day — the C-grade rider:** *"It also depends, though: if it's
a C-grade conviction, don't trail that. I'd rather just hold to my
high-conviction stops."* A scale-in requires the second setup to grade B or
better. A C-grade second trigger is confirmation to HOLD — original stop
untouched, no add. (The add and its trail read as one package, since the
trail to the new invalidation is what makes the add safe; his word splits
them if that is over-read.)

→ runbook §2c; tv-manage 0.3.1 SCALING IN.

## T54 — the grade and the size must agree; a pass-reason is not a discount
**2026-08-13.** The shakedown emitted nine takes, nine take_light — both
conviction-A trades included. His reaction to the 03:24 trade that argued
its own pass and took anyway: *"That is worrying that it took the trade even
though it wasn't confident in the trade itself."*

New defaults: A → take_full, B → take_light (full with stated reason),
C → take_light or pass. No double-counting a fact already in the grade; an
objection the contract lists as a PASS reason either holds (pass) or is
dismissed with cause (gone) — it never shrinks size. If the reason paragraph
reads as a case for passing, pass.

→ `tv-trigger` 0.4.3, THE GRADE AND THE SIZE MUST AGREE.

## T55 — a trail must clear what it hides behind
**2026-08-13.** The 04:01 trail sat 0.5pt above the swing high and was
collected by the next bar. The contract already named "trailing so tight
that ordinary noise takes you out" as a bad-manager trait; it had no number.
Floor: clearance ≥ 0.5× trailing avg 2m range, min 3pt — MY calibration,
same family as the 0.75× stop floor; his word replaces it.

→ `tv-manage` 0.3.0.

## T56 — a level the thesis names as a destination is never a headroom obstacle
**2026-08-13.** The 04:38 pass counted the 0.705 fib as path-crowding against
a range-top short — while the standing thesis named that same fib zone as
where the licensed short was headed. A destination is a TP1 candidate, not
clutter. Ask of every level ahead: is it in the trade's way, or is it what
the trade is for?

→ `tv-trigger` 0.4.3, constraint 7.

## T57 — the 04:36 candle: recorded, not legislated
**2026-08-13.** His review: *"At 4:36 there was a really nice trade there...
we basically came up, topped out that range, rejected the [weekly] value
area high, and the same two-minute candle closed through VWAP+1. The moving
average would have been a really nice entry on retest, stops above the high
that rejected the value area high, targeting VWAP middle band. Obviously,
that's hindsight from me, so even then, you have to take it with a grain of
salt."*

The agent adjudicated that exact candle (decision minute 04:38 — start-time
convention) and passed it on three legs: (1) the stall was ~12pt SHORT of
the thesis's licensed 29858–29928 band — the known expectation-vs-
specification failure shape, at smaller scale than the three cases that
built the escalation rule; (2) the 0.705 fib counted as path-crowding when
the thesis named it as the destination — fixed as T56; (3) the 3m closed ON
its MA, not through — a real T38 weak-case objection that supports waiting.

No band-tolerance number was invented off one hindsight-flagged trade. If
the licensed-zone literalism recurs on a day he flags live, it gets its own
rule then.


## T58 — the 0.4.4 veto: a calibration written as a prohibition
**2026-08-13, same day.** 0.4.4 produced **zero fills across LONDON and
NY_PRE** on the very day that had filled five times under 0.4.3. His read
was immediate and correct: *"the adherence definitely looks too strict. if
anything, might have been better before."*

**My defect, and the mechanism is exact.** T54 clause 2 listed *crowded
path* among the objections that "can never be a size discount" and closed
with *"if your reason paragraph reads as a case for passing, pass."*
Measured against the prior run: **8 of the 9 takes cited a path/structure
objection as their light reason** — including 08:32 and 08:36, the two he
called great execution. The clause vetoed almost the entire book.

It also contradicted doctrine already in the stack. T43 tells the manager to
break even at the first level *on a crowded path* — which only makes sense
for crowded-path trades you took.

And the closing heuristic was worse than the clause. **It punished the agent
for naming a downside**, which is precisely the reasoning quality T45 makes
the success criterion — an agent learns to go quiet to get a trade through.

Three corrections:
1. Only a **decisive** objection blocks — one that would make you pass
   standing alone. Weighed trade-offs are what `take_light` is for. The
   original failure was ONE trade stacking THREE independently-fatal
   objections and paying for them with size, not the mere presence of a
   downside.
2. **Headroom is graded by behaviour, not count** — a level ahead that HELD
   against your direction on the 15m is an obstacle; one price has been
   slicing through is on the map, not in the way. Count was always the wrong
   axis: the +3.92R short had three clusters ahead, and the long he would
   never take had one shelf that had already rejected the session high.
3. **"Middle" is defined** — inner half of the session range so far, and
   never fires on a level the thesis names as a boundary. On a 100pt range
   everything is arguably the middle; T50 exists to kill the lone fib in dead
   space, not to shut the session.

**The general lesson, and it is the second time today.** The diagnosis (9/9
light = the third branch had collapsed) was right. The remedy converted a
question of degree into a binary, and a binary written by me is a rule he
never gave. When his own words carry a quantifier — *"too many levels"*, not
"any level" — the quantifier IS the ruling.

→ `tv-trigger` 0.4.5.


## T59 — the outer band is fade-only
**2026-08-13, v44 NY_AM review.** The run's one early take: a 09:42
`take_full A` short whose limit rested at the just-broken **VWAP−2 /
prior-day VAL**, placed off a 3m candle that had displaced through SIX
levels in one bar. Filled on the wick-back at 29634, stopped at 29663 on
the 09:44 bar — two minutes — as the V-reversal ripped through. His verdict:

> *"I think it genuinely entered off of the retest of vwap −2 after the prev
> candle just closed through it, genuinely the most retarded thing I think
> I've seen in my life. Please do not be doing this dumb shit."*

Second instance of the shape he condemned in the corpus (*"basically
shorted at the VWAP−2 band… very, very dumb"*). The T20 breakout-bet test
did not catch it because its letter is about WHICH SIDE the limit sits on —
this limit sat correctly between price and the move's origin. The sin is
the LOCATION: at the outer band the displacement that broke it is the
exhaustion, not the beginning. Continuation through ±2/±3 is now a hard
pass; the only trade AT the outer band is the fade back from it — which is
the shape of the +2.83R long the original run built off this same zone.

Rider: the trade's own thesis licensed LONGS "on a stall or rejection AT
the weekly VAL / vwap_m2 zone" — and the trigger shorted that zone's
retest without naming the tension. The thesis licensing the opposite side
at your entry zone is now a decisive objection requiring refutation.

Note for fairness: the loser was unmanaged for a STRUCTURAL reason (fill
09:42 bar, stop 09:44 bar — no completed bar between), not a detector
defect. The week run's tooling needs no patch for this.

→ `tv-trigger` 0.4.6, constraint 0b.

## T60 — an MA never raises a conviction grade
**2026-08-13, same review.** The 09:57 short graded itself **A** on
`bb_ma_15m + fib_0.705` — "A-tier confluence" in its own words. The rubric
already said the MA is the trigger and never the rejection; what it did not
say is that the MA cannot LIFT a grade either. MA + a lone fib, with no
profile / prior-day / weekly anchor in the zone, is B at the very best.
The label drives the partial structure (A holds 50% where C exits 100%)
and his sizing, so inflation is not cosmetic.

Same trade, recorded not legislated: the entry was the daily VAL retest at
the bottom of a 100pt trigger candle — mechanically "the closest structure
to price at the trigger's close," but the candle was so large that the
closest-structure rule produced a 104pt stop and a ~1.1R first target. If
oversized trigger candles need a different retest rule, that is HIS call
with his number; two of my invented numbers already failed today.

→ `tv-trigger` 0.4.6, conviction rubric.

## T61 — the thesis read the same tape in opposite directions
**2026-08-13, the reproducibility finding.** At 09:30 on the same
session-day, on identical candles, two runs of the identical tv-thesis
0.4.1 contract read the same 10%-body 09:15 15m candle as:

- run 1 (r2): "bounced into the cluster… **absorption**" → **long**
- run 2 (v44): "failed to reclaim… **absorption confirming sellers defend
  the break**" → **short**

The same word carried both directions. Every downstream difference between
the two NY_AM sessions — the forbidden 09:42 short existing, the 09:54 long
not existing — flows from this flip. Against his shipping criterion
("thinking as if I taught someone my strategy myself"), direction stability
on ambiguous mornings is now the top open question. Not legislated —
MEASURED: the week run's third pass over this day, on frozen 0.4.2
contracts, is the arbitration. If the flip recurs, the fix belongs in
tv-thesis and it will be built on three samples, not one.


---

## T62 — THE ANCHOR: reasoning first, performance is the consequence
**2026-08-14, his re-anchor after the first full agent week. Standing for
every testing run from here.** Recorded in full at
`docs/ANCHOR-reasoning-first.md`; the short form:

> *"We are not trying to make the agent perform better. We are trying to make
> it think and trade like me. Performance is the consequence, not the target...
> A change that improves results while moving the agent's reasoning away from
> mine is a regression. Reject it, and say so explicitly."*

The named structural mismatch: he forms a thesis from the higher timeframe
BEFORE any trigger exists; the agent evaluates candidates and assembles a
reason afterward. A thesis is four parts: WHICH MECHANISM (rebalance to a HTF
MA / tailing a rejection off one / a break), a DESTINATION, BOTH BRANCHES
named before the decision point resolves, and STRUCTURAL invalidation. Hold a
read with no trade. Pass on the road, not the pattern. No retroactive
reasoning. Conviction graded the way he talks.

Comparisons sort on reasoning into four categories (same reasoning /
different-reasoning-same-setup / no thesis where he had one / thesis where he
had none), led by category 2 — the failure invisible to results.

First application: `docs/COMPARISON-wk1-reasoning.md` (six category-2
divergences; the two costliest both sit at the MECHANISM layer). No contract
changes made — per the anchor, he reads the comparison first, then rules.


---

## T63 — the flip: a better opposite setup may close and reverse the position
**2026-08-14, his week review, on the Friday NY shorts (his "biggest issue of
the whole thing"):**

> *"We weren't able to break this Asia low on the dump... price tried to come
> down on market open and it reclaimed it immediately... I'm pretty sure it
> did think the long was valid and didn't take strictly because it was in a
> short already... The agents should be able to flip their positions if a
> better setup presents itself in that nature."*

Today an open position blocks the opposite side outright. His ruling: it must
not — when a genuinely better opposite setup fires, the position is closed
and reversed. NOT implemented yet: "better" needs criteria (grade relative to
the open trade? the open trade underwater or merely unresolved? once per
level?) and it belongs in the thesis-0.5.0 rebuild, where the flip is the
actuator for acting on the thesis's own written other-side branch — the
Friday divergence (COMPARISON 2.1) was precisely a written branch with no
actuator. Design with him before wiring; a cheap flip is a whipsaw machine.

## T64 — the range frame outranks the local trigger
**2026-08-14, week review — one location doctrine, four instances, both
directions:**

- Wed 03:27/03:54 shorts: *"kind of in the bottom half of the consolidation
  range... I wouldn't want to tail that and try anticipate the break of the
  consolidation. I don't think that's very probable or favorable."*
- Wed 08:18 long: *"I'm not a fan — we are coming to top out this range...
  it topped out the range, tried to take longs off it, and the trade reversed
  quickly. If anything I'm more inclined to short there."* (The agent's
  thesis had flipped long on a 15m acceptance; his range frame overrode a
  legitimate-looking acceptance story.)
- Fri 04:28 long: *"We stalled at the 0.5 of the range of the day and closed
  back through the VWAP middle band — we could not cleanly break the
  equilibrium of the daily range. The longs were the wrong move... I'd have
  been much more inclined to go short"* (his own narrated 04:04 short is the
  trade he wanted; targeting *"VWAP−1 or some volume profile level"*).

The generalisation, in his frame: while a consolidation is in force, the
range is the map — fade its edges, do not buy its top, do not chase from its
middle toward its far side, and a failure to hold equilibrium (day 0.5 /
VWAP mid) points AWAY from the failed side. Extends T50 from "middle is
dead" to a full location doctrine. Belongs in the thesis rebuild as part of
the range mechanism, not as another trigger constraint.

**Rider on T53 (scale-ins), same review:** the Monday re-entry+add he
ratified (*"it would have just been a scale-in kind of trade anyways"*), but
the Wednesday middle-of-range continuation he refused: *"in live it would
have already been in shorts from three o'clock — that's not something I
scale in on."* A scale-in needs equal-or-better LOCATION, not just profit +
same direction + B-grade.

## T65 — small notes from the same review, recorded not legislated
- **The Tuesday trail that cost the runner 0.88R**: noticed, and accepted —
  *"management like that maybe cuts winners but it also cuts losers, which is
  a good thing."* No change requested.
- **Stop preference on the Tuesday 09:40 long**: he'd have placed it *"below
  the three minute moving average that closed through"* rather than the
  2m-derived placement — *"also completely valid."* Preference, not a rule.
- **Monday 10:18 pass** (his ~+3R rebalance short, agent passed): *"completely
  fine"* — softens COMPARISON 2.6 from a failure to a nice-to-have.
- **A-conviction 50% partials**: *"seeming to play out pretty well."*
- **Management tier overall**: *"the agents' actual trade management is very
  good — I have to give it credit"* — including the Wed 08:18 trade he
  disagreed with, saved by management, and both Thursday NY losses cut early.


## T66 — the stand-aside gate is REJECTED, and the working-forward rule
**2026-08-14, his correction of my proposal:**

> *"When you say 'stand aside until high time frame alignment,' that's kind of
> going against what we've already said, and that would rule out some genuinely
> good trades... We have to make sure that we're not working backwards. If
> you're changing something that we've already disputed before, that's not
> really working for us."*

He is right twice over. The gate collides with his T21-era ruling ("don't be
more conservative at the start of the window... 9:40 to 10:10 is where the
best trades are"), and his own week review graded the Wednesday 03:00 fade -
taken while his live self sat out - as one of that London's two best shorts.
The anchor's "hold a read with no trade" is a CAPACITY (theses log with
nothing against them - already true), never a gate. COMPARISON 2.4 stands as
a record of a live difference, now ruled by him as not a defect.

**The meta-rule, standing:** every proposed change is checked against prior
rulings before it is proposed; a conflict is surfaced as a conflict, not
re-litigated by stealth. The doctrine-keeper's job includes remembering what
was already decided against.

Scope correction from the same message: *"I'm sure we don't have to change
the whole thing... we're probably 80% of the way there."* The 0.5.0
full-rebuild framing is out; the fix list is surgical.
