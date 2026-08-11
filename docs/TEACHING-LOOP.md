# TEACHING LOOP — his rulings on agent disagreements, in order

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
