# Canon rebuild — full Q&A log

Every question Angus asked in the rebuild session, and the answer given. Chronological,
grouped by phase. This is the "why" behind `docs/CANON.md` and the `scripts/funded_book.py`
spec — the reasoning record, not the spec itself.

**Provenance note:** the session ran long enough that its early portion was context-compacted.
Entries 1–51 are reconstructed from the running summary and the committed artifacts they
produced; the wording of questions is preserved as asked, and answers are condensed to their
substance and the numbers actually measured. Entries 52–56 are verbatim-fresh. Where an
answer's number appears here, it reproduces from committed code on committed data.

---

## Phase 1 — Discovering the old canon was broken

**1. "fuck. this is deployed live now too, fuck."**
Confirmed the concern was real but the exposure was not: the live stack was structurally
disarmed (`_NoBroker`), so nothing could reach a broker. Identified the four places the cap
defect actually lived: the substrate via `ScriptVerdictSource`, `NYScorer._day_taken` and
`_day_pl` (both day-wide rather than per-session), and the `RiskLimits` backstop of 3.

**2. "my point is that we have launched something that is broken lol"**
Agreed without hedging. The defect: the 2-trade cap was shared across pre-market and the
golden window instead of being 2 per session, which starved gold of candidates on 56% of
day-books. Every downstream number built on that substrate was contaminated.

**3. "what do we do from here then, we probably need to re measure from the beginning"**
Proposed exactly that — rebuild from raw triggers rather than patch the cap, because the
selection defect had polluted the population every later stage learned from.

**4. "we need to re run triggers from the beginning... the base strategy before order flow,
and make order flow confirm without any trade caps or anything. we work from there, and build
the trade caps after. what do you propose we do?"**
Proposed the L0–L4 layered architecture that became the rebuild:
L0 census (every trigger, no selection) → L1 fills (cancel rules as derived columns, one walk
serving all arms) → L2 outcomes (a real `simulate()` per trigger) → L3 features + check trial
→ L4 post-hoc causal policy. Governing invariant: layers above L0 may only *remove or weight*,
never add, and every kill must be attributable. Caps get imposed last, at L4, where they can be
measured rather than assumed.

**5. "the limit has a 22 point cancel not a 22 minute cancel, although for golden window that
limit should be extended and based off a structural level it hits. if our entry is a limit of
bb MA stacked on vwap −1 and it touches the vwap band and rejects hard, we shouldnt be entering
that. if it runs 30 points without touching a structural level and revisits entry, it should
enter that."**
Recorded as a ruling and built it into L1 as a derived column rather than a filter, so all
three arms (`arm_none`, `arm_dist22`, `arm_struct`) could be measured from one walk. Later
measurement proved the 22pt cancel *inverted*: it kept −0.180R of trades and killed +0.015R.
It was replaced by session-window-end expiry — the order lives until its window closes.

**6. "i meant if it touches the vwap middle band and rejects hard before coming back down, not
if it revisits the vwap −1."**
Corrected the implementation: the structural event is a touch-and-reject of the level *ahead*,
recorded as `struct_event` ∈ {broke, rejected} with `STRUCT_ACCEPT=5` / `STRUCT_REJECT=8`.

## Phase 2 — L0 and L1

**7. "alright, lets get onto L0"** → Started the census build.

**8. "just to confirm so we dont do this shit again, what is L0 measuring"**
L0 is the population, not a strategy: every trigger the production detector fires in the
07:45–11:00 band, with no selection, no cap, no gate. Its only job is to be *complete* — if a
trade never appears at L0 it can never be evaluated anywhere above. Gated by parity against the
cached stream (identity columns must be identical).

**9. "and what does L1 measure before u move to it."**
L1 answers "would this trigger have filled, and under what order-lifetime rule?" One walk per
trigger recording `max_away_before_fill`, `struct_event`, and `mins_to_fill`; the cancel arms
are *derived* from those columns rather than simulated separately. Gated by reproducing engine
fills to the tick.

**10. "yeah okay, get onto it."** → Ran it.

**11. "give me the verdict after each step so we can make sure we are tracking on the right
path instead of coming to the end to see something fucked up"**
Adopted as standing procedure: a verdict at every layer boundary, plus an explicit gate that
must pass before the next layer starts. This is what caught the L1 fill-mechanics bug and the
L3 join bug before either could reach a conclusion.

**12. "can L0 be done more efficiently?"**
Yes — added day-level parallelism (`--procs`) with bit-identical output, since each day's
detection is independent.

**13. "run as many parallel things as u need but make sure we are not sacrificing any quality,
always be on the lookout for bugs and diagnose before we see the problems downstream like we
did with canon."**
Ran parallel builds with per-layer gates as the quality guarantee, and used Sonnet for
data-grinding agents while keeping decisions on the main model.

**14. "im lowkey a bit confused on what we are actually doing... dumb it down a bit"**
Plain version given: L0 = write down every setup that appeared. L1 = which of those you'd
actually have gotten filled on. L2 = what happened to those fills. L3 = which order-flow checks
actually predict the good ones. L4 = how many to take and how big. The old canon did steps 4
and 5 *before* step 1 was honest, which is how it broke.

**15. "awesome, where are we up to now?"** / **18. "let me know when done, how far through is
L0?"** / **23. "how is it going claude>"**
Progress reports at each point.

**16. "so this might be a while, anything that can be done in the meantime?"** and
**20. "anything i can do in the meantime, or do i let you cook"**
Suggested the useful parallel work (hand-log validation material, ruling confirmations) and
otherwise: let it cook.

**17. "realistically once fully refined, i expect it to be taking a minimum of 3 or so trades a
day on average. there is no day realistically where it should trade no session at all... that
being said we dont want to just fill the volume with junk"**
Recorded as a design target and checked it at the end: the shipped book takes ~4/day, gold ≥1
every month, and **zero** zero-trade days across all 352 days.

**19. "it is a good sign that gold had a lot more valid trade entries that were just dismissed
by the trade cap"**
Confirmed — that was the smoking gun for the defect, and it's why gold ended up the larger book
once the cap was removed.

**21. "these are all valid, but the key is that they have to touch that level, and reject" /
"theres plenty of my trade data from february and april in the main github terminal"**
Built the hand-log check against the February log (exact, ±6min mapping TV-open → bin-close)
and March (±30min): **43 of 45** matched.

**22. "remember that i really trade the displacement through on any timeframe as well... 1, 2,
3 and 5 are all valid"**
Folded into the trigger definition — displacement-through on any of those timeframes counts.

## Phase 3 — Results, and separating the two sessions

**24. "im reading all of this and a bit confused. can u give me the key finds"**
The decomposition: structure alone is ≈ breakeven (−0.01R) inside the 7–60pt band; order-flow
selection adds +0.36R; V8 exits do the rest. Rejected sides are −0.44 to −0.61R — unrescuable.
Sub-7pt stops are 14% WR and carry three-quarters of all raw loss, which vindicated the 7pt
floor. The 22pt distance cancel is inverted and should go.

**25. "is this just for pre market and gold window, no london?"**
Correct — NY only. London was a separate book and became Brake's rebuild.

**26. "lets separate pre market from golden window and dissect them before we decide what to
ship, give me a comprehensive breakdown, and what you would suggest"**
Delivered the split. Surviving gates: **gold D** (wall ahead) and **pre W** (no wall behind) —
all pre edge lives inside W. Dead on trial: C (fed a provenance-broken cached column), PAQ, X,
LONSLOPE as a standalone, and G as an adder (failed holdout).

**27. "whats the difference between fit and holdout, is fit 2025-2026 and holdout 2023/2024?"**
Yes. Fit = 2025-06 → 2026-07 (230 days), with *discovery restricted to 2025 only* so 2026 acts
as an out-of-era check. Holdout = six sealed months of 2023/24 (Jul/Sep/Nov 23, Mar/Apr/Oct 24;
122 days) that no discovery step ever saw.

**28. "this is a big find... my main goals are to maintain high win rate, eliminate as much max
DD as we can (optimised for fundeds). do some aikido, look at the losers, find traits they have
that winners dont... trade frequency looking good for gold, as long as the ones we are cutting
are predominantly losers"**
Ran the loser autopsy. It produced the **wall-quality cut**: skip gold when
`dep_wall_below_d < 2.75` or `WALLSZ == 0`. The cut set runs 37–41% WR in *all three* eras —
i.e. predominantly losers, exactly the bar set. Book WR +7pp, maxDD −37%/−45%.

**29. "pre is already goated, no need. whats our stats look like now. why is there a red month"**
Gave the updated stats and traced the red month to capped slot competition, which the uncapped
test then resolved.

## Phase 4 — Sizing

**30. "i think we need to build some conviction based sizing. what is the best setup? what is
the second best? whats an average? what do we de risk on?... it's interesting that uncapped, it
was profitable. what does our overall book look like uncapped?"**
Built the score tiers from era-consistent cells (`gold_score = 2D+Tc+AGE+TRIG+T2`,
`pre_score = 2W+G+F`), and showed uncapped is *better* than capped once the wall cut exists —
the cap was pure cost.

**31. "ladder should be shipped, but i want to see how uncapped shapes up with conviction based
sizing too. it seems like it makes sense to go uncapped"** → Ran and confirmed.

**32. "im happy with uncapped, purely because under funded sizing itll shape up better with the
dd figures... $100 at 0.5, $200 at 1.0, $300 at 1.5"** → Ran that ladder.

**33. "i dont like that worst day figure at all... we're gonna have a max $800 dll configured
for sanity... so either we de risk per trade or cap the frequency, or we look at what trades
are losing"**
Diagnosed *why* naive day-halts fail here: the worst days are 4–8 **overlapping** losers, and
the losses aren't realized yet when the later entries fire. Invented the in-flight-inclusive
budget — `realized losses + in-flight risk + new risk ≤ budget` — which bounds the worst day
structurally rather than reactively.

**35. "i want to test different risk management systems. hypothesize on some things you think
could work, and test them out"**
Ran the risk lab. Result: once the budget exists, overlays add ≈ nothing — which is *healthy*,
because it means the edge is entry-driven, not management-driven. Only the soft de-risk
survived (half size once realized day P&L ≤ −$280). Buffer-scaled risk was rejected for
era-flipping. Post-loss cooldown looked excellent leaky and **collapsed when tested causally**
— rejected and explained rather than shipped.

**36. "what are the win rates for each conviction size? dont ship anything yet, still sussing"**
Gave per-tier win rates across all three eras.

**37. "are there any trades that have lower frequency but performed significantly better, like
the order flow combinations... I like 0.5, 1, 1.5 and 2. but wouldnt want to do double sizing
on anything less than 70-75%"**
Searched 339 combinations under a triple-era filter. One survived the bar:
**gold & TRIG & LONSLOPE & struct_event=='broke'** — 70% / 79% / 70% across the three eras,
pooled 72%, Wilson lower bound 64%, roughly 2 per week.

**38. "lets do a 2.0, and give it $800 dll budget. 2.0x should definitely be capped at one per
day"** → Shipped exactly that; the elite tier is capped at one per day.

**39. "that max dd still scaring me a lil. you got any ideas?"**
Honest answer: maxDD here is *sequences of ordinary red days*, not disasters — so the only real
levers are scale and a start ramp. No clever overlay fixes it, and I said so rather than
inventing one.

**40. "one thing i want to build is a scale down ramp when we have 1k available dd... how does
it look at $75, $150, $225, $300"**
Built the ramp (buffer < $1k → half size) and ran that ladder. Noted the ramp is **dormant
across all 19 months of history** — it never fires on this data, so it costs nothing and exists
purely as insurance for a worse-than-history future.

**41. "lol funny that holdout is more profitable. lets do $80, $160, $240, $320, so long as we
have a ramp configured for live trading"** → Shipped that as the first Lucid config (later
superseded, entry 54).

## Phase 5 — Monte Carlo

**42. "run a monte carlo over the entire 19 months. eval + funded. 2k trailing EOD dd that
locks at 2k balance... 53k target... 54k for a full 2k payout because you can only withdraw
50%. give me a dynamic thing where i can change base sizing, profit targets etc"**
Built the interactive MC lab: day-level bootstrap resampling **whole days with intraday order
preserved** (so overlap and sequencing survive), seeded RNG, and modes for eval / funded year /
full cycle.

**43. "make it more detailed — full equity curve, pass probability, max payout probability"**
Added the spaghetti fan with median and 5–95% band, the P&L distribution, P(finish by day N),
and payout-count distributions.

**44. "idk what u did to it"** / **45. "let me play around with the different sizing... i dont
have that option here"** / **46. "can you refer to the other monte carlos we've ran because
this one is a bit confusing"**
Three layout failures on my side, fixed by rebuilding it in the house style of the existing
simulator verbatim — same palette, same tile grammar, same controls-above-charts layout. The
lesson recorded: match the established form rather than inventing a new one.

## Phase 6 — Scaling rule

**47. "i want a scaling rule for an account like alpha futures or my funded futures pro
accounts. for every 1k available dd after $3k profit, add $50 onto the base sizing, but i want
to change it dynamically"** → Built it as live controls.

**48. "$150 base, +$75 per extra 1k, base cap $450 for now. happy to ship if it shapes up"**
Ran it — and reported it **failed**: holdout net *down* 20% and a red month returned. Diagnosed
the cause: a $450 cap against a *fixed* $800 budget strangles itself, because an elite trade at
$900 no longer fits and even two 1.0x trades exceed the budget.

**49. "the thing is, with more buffer, we have more of a daily budget. max DLL should scale
with the increased cap. +$75 for every 2k after 3k, capped at 600, but the daily loss should
scale with the increased sizing"**
Your fix, and it was the right one. With the budget scaling proportionally
(`budget = base × 16/3`, soft = 35% of it), **every month goes green in both spans** —
including September, the one stress month, at +$3,903 — because size is only ever large when
the cushion is large. Fit +$320,150, holdout +$188,324, MC P(bust) 1.0%.

**50. "re run without the cap at all, just static sizing at 75, 150, 225 and 300, so i can see
the raw pnl without scaling"**
Ran it: fit +$89,925 (maxDD $1,603), holdout +$56,408 (maxDD $1,503), 13/13 and 6/6 green.

## Phase 7 — Ship

**51. "this is the new canon. before we ship officially, break down the month by month, day of
week pnl and frequency, split between pre market and golden window, in fit and holdout"**
Delivered the full split. The four honest reads:
- **Gold is the engine in both eras** — fit $62.2k vs pre $27.8k; holdout $45.9k vs $10.5k at
  2.2× the trade count. Exactly the inverse of the broken canon, which starved it.
- **Every month green in both spans (19/19).** Pre goes red three times in fit (Aug/Sep/Dec 25);
  gold covers all three and has no red month in either span.
- **Weekday effects era-flip, so no calendar rules ship.** Fit's "worst" Thursday pre (29% WR)
  runs 59% in holdout; Wednesday pre flips 39% → 67%; Friday goes from worst fit day to
  second-best holdout day. Cutting on fit weekdays would have burned real holdout money.
- **Pre wins differently per era** — 42% WR in fit (paid by R-multiple) vs 61% in holdout.
  Streaky pre is expected behavior, not breakage.

**52. "pull it up in local host for me please, im more than ready to ship this. please be clear
with me on what we are shipping before we do."**
Published the ship-review page (entry rules, ladder, risk spine, profile comparison, both
breakdown tables, and an explicit "not in this ship" section), and **held** — no commits until
confirmation. Stated plainly: the live re-arm is *not* in this ship; NYScorer still runs the old
architecture and stays disarmed until rewritten.

**53. "static 150 is now the lucid by the way. not 160"**
Applied it everywhere. The Lucid ladder is **$75 / $150 / $225 / $300**; the $80/160/240/320
ladder is retired and marked superseded in the docstring. That collapsed the menu from three
profiles to two: `lucid` (default) and `scaled600`. Committed as `ea20116` after verifying both
reproduce on both spans.

**54. "delete all of the previous canon shit so the other chats dont get conflicted. this IS
the new canon. everything needed is here."**
Deleted 248 files / 48,377 lines — 138 old-canon scripts, 44 docs, 9 dashboards, 5 orphaned
tests, and the stale tracked outputs. Reference-checked every deletion first. Deliberately kept,
with reasons written into `docs/CANON.md`: the deployed (disarmed) live stack, since deleting it
breaks the VPS before the re-arm replaces it; the legacy import dependencies the new L3 builder
actually imports; and the London artifacts, which are Brake's reference-to-beat. Added
`docs/CANON.md` as the orientation law, and committed the canon datasets — they had *never* been
tracked, so the shipped numbers previously existed only in this container. Verified after the
cut: no dangling imports, 708 tests still collect, L4 tripwires 13/13, `funded_book` reproduces
+$89,925 to the dollar. Committed as `d420b10`.

**55. "can you make a file of every single question I have asked and what you answered?"**
This file.

---

## The corrections I had to make along the way

Recorded because they're the reason to trust the result, not a reason to doubt it:

| What broke | How it was caught | Fix |
|---|---|---|
| Mixed-DST timestamps (3×) | Crash on spans crossing DST | Always `utc=True` then `tz_convert` |
| L1 filled a minute early at sub-tick prices | The L1 engine-parity gate | Tick-round at placement; evaluate from the bar *after* the trigger |
| L3 gate showed 95 false diffs | Investigating rather than accepting | Join must include entry price — sibling triggers share fill minutes |
| Cached `pm_sofar_conf` was provenance-broken | Agreed with neither clean nor leaky definition | Excluded; the old C check had been fed a coin flip |
| Realized-loss day halts didn't bound worst day | Worst days are overlapping losers | Budget counts realized + in-flight + new |
| Post-loss cooldown looked great | Re-tested causally | Collapsed — rejected, not shipped |
| First scaling attempt (cap $450, fixed budget) | Holdout net down 20% | Angus's proportional-budget fix |
| Reported a workflow as running after it was killed | Read event counts, not timestamps | Check last-event *timestamps*; verify liveness after interrupts |
