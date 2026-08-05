---
date: 2026-08-05
kind: rediagnosis (agent, verbatim) — machine-ready as-taught specs
status: SUPERSEDES prior Orochi extraction for spec purposes
---

ORO­CHI RE-EXTRACTION — MACHINE-READY SPECS (as-taught, no simplification)
Sources: /home/user/AI-trading-agents/research/transcripts/orochi/{H01I39z4kcI,0B4uO1ruKoQ,OmzNrWzekwA,qCQQe00oJr8,IMs472GOwnY,WuUeHhB2TMM}.md, EXTRACTION-A/B, research/findings/orochi-diagnosis.md. Timestamps are the transcript 30-second block stamps. "sd1/sd2" = 1st/2nd standard-deviation band of session VWAP. All quotes verbatim (stutters elided with …).

SHARED INSTRUMENT DEFINITION (applies to Specs 1-3, 5). His "DVA" is mechanically pinned in IMs472GOwnY: TradingView standard VWAP, "Anchor period… Session is daily in this case… this is what you want in regards to DVA" [02:03]; "bands calculation you want standard deviation" [02:33]; "bands multiplier one… is what you want to get your actual value area… standard deviation two, which is… your rotational extreme" [03:03]. So: session-anchored VWAP (Globex daily session for NQ), VA = ±1σ, rotational extreme = ±2σ, all bands developing (they move). Warm-up exclusion: "pretty much useless for the first 10 15 minutes" [IMs 04:33]; "the bracket's really small. It's a bit less usable at that point" [H01 04:04].

---

SPEC 1 — VWAP-SD2 ROTATION FADE (regime-gated) — UNTESTED — highest mechanical specificity of the VWAP family

1. THESIS. In a rotational session, price stretched to the ±2σ "rotational extreme" is an over-extension away from a mean the whole session's volume agrees on; whoever chased the stretch is offside against fair value and pays the trip back. The setup exists ONLY because most traders fade sd2 indiscriminately: "a lot of people are always trying to trade off of the second standard deviation. That's just not the case. Only in certain kind of market conditions" [H01 01:00].

2. ENTRY. Trigger: price reaches the ±2σ band of the daily-session VWAP while the session is classified rotational-within-value. His words: "The only time you can kind of get into taking a trade off of these is when the condition is rotational within value… you're playing mean reversion plays back towards the mean… if you're trading up into here… and it's not establishing acceptance above value, then you can… play trades back towards the mean" [H01 03:33]. Note the literal acceptance test sits at the VALUE EDGE (±1σ), not at sd2 — the condition is "not establishing acceptance above value." Entry price: never stated as touch vs close (gap D1). A secondary as-taught reading exists for the sweep case: "you could off of the sweep here… expecting that momentum is slowed down… But just trading off of the condition here, nothing has changed yet until we get back into value" [H01 05:35] — i.e., the sweep-fade only validates on re-entry into the ±1σ band. Session window: any time after VWAP warm-up (skip first 10-15 min / small bracket).

3. STOP. NEVER STATED anywhere in the VWAP videos. Flag: stop is a pure census choice (beyond sd2 extreme / beyond sweep high / fixed-R are all our inventions, must be declared arms, none is "his").

4. TARGETS. Two taught target arms, both his words: "You can target the mean for mean reversion. You can target the other side of value, etc. Those are going to be your contextual targets" [H01 08:09-08:40]. So: (a) mean = developing VWAP; (b) opposite ±1σ band. No partial/trail rule taught for this setup.

5. MANDATORY CONTEXT (hard gate, his central lesson). Condition must be rotational within value. Prohibition stated three ways: "when VWAP starts to trend with price… price being imbalance[d] down against DVA… you're not looking to trade off of the second standard deviation because the condition is bearish" [03:03-03:33]; "We then hold above value area high… So that means that the second standard deviation is not a trade location… Because we're not rotational within value" [05:05-05:35]; "If the market is bullish against value here and you're holding above value, why are you trying to catch a short? You should be trying to catch the pullbacks into value" [09:11]. Mechanically: no acceptance established beyond either ±1σ edge in the current session at trigger time.

6. DISCRETION GAPS → census arms.
- D1 entry price: (a) fade first sd2 touch; (b) require wick beyond sd2 + close back inside sd2; (c) require re-entry into the ±1σ band (his sweep-case literal reading).
- D2 "rotational within value" classifier: (a) price currently inside ±1σ and has traded both sides of VWAP this session; (b) no run of N closes beyond either ±1σ edge so far this session (N = acceptance parameter, see D3); (c) VWAP slope filter (|slope| under threshold) — weakest textual support, he defines imbalance as "VWAP trending with price," so include as an arm, not the default.
- D3 "establishing acceptance": undefined here; borrow his only negative definition (Spec 2, "just barely deviating it") → arms: 1 close beyond edge ≠ acceptance; N=2-3 consecutive closes beyond edge = acceptance (which kills the gate); time-based (≥X minutes beyond edge).
- D4 close/touch timeframe: he trades off 1-min for execution elsewhere [OmzNrWzekwA 04:39] but reads condition on higher TF; arms: 1-min vs 5-min trigger bar.
- D5 target line is developing (moves): (a) fill at level as of entry (frozen); (b) chase the developing line.

7. DATA NEEDS. 1-min candles + volume (VWAP σ bands require volume). No flow, no depth as taught. Minute-delta optional only for our added discriminator arms.

8. FREQUENCY. His walkthrough shows a handful of qualifying touches across ~3 chart days with several disqualified by the gate. Implied cadence: 0-2 triggers/day on rotational days, roughly 2-5/week on NQ; strict D2/D3 gating is expected to remove about half of raw sd2 touches.

---

SPEC 2 — ACCEPTANCE-BACK-INSIDE TRAVERSAL ("80% rule" on VWAP value) — UNTESTED (VWAP expression; profile expression overlaps tested P1)

1. THESIS. Price that was imbalanced outside a value area and then re-accepts inside proves the breakout auction failed; the side positioned outside is now offside and value's gravity carries price across the whole bracket. Named rule: "Did they recently accept back inside? If so… the 80% rule can be applied, and you should expect traversal of value, or… first target is the mean, which is VWAP" [0B4 01:02-01:33].

2. ENTRY. Trigger sequence as taught: (i) price imbalanced against a period value area (rejecting the edge from outside); (ii) prior momentum decays — "momentum starts to round out here and we start to range and then we see a move back into value and that would be where you'd want to get long and target the other side of value" [H01 03:33-04:04]; (iii) entry on the move back inside; a hold of the re-crossed edge upgrades it — "you then see a move back within value holds support… and you expect to target the move through value" [H01 07:07-07:38]. Multi-period stack version: "We shift back inside of developing week value. We shift back inside of developing month value. So, what do you do? Well, you apply that 80% rule… You expect traversal up to value area high" [0B4 04:35-05:05]. Entry price never pinned: "move back into value" (edge cross) vs the held retest are both shown. Window: any session; period VWAPs run continuously.

3. STOP. NEVER STATED. Flag. (Implied invalidation is renewed rejection back outside value — he closes trades when "we shift back into developing value area" against him in the NQ session [OmzNrWzekwA 08:13] — but no stop price is ever taught.)

4. TARGETS. Full traversal to the opposite ±1σ edge; first target the mean. Mandatory interrupt rule (this is a taught exit mechanic, not color): "you can tag the mean, which is the VWAP in this instance, and that can interrupt the move… There's no right or wrong, but nonetheless, the mean, so the POC or the VWAP here, can stop that move" [0B4 05:05-05:35]; independently: "it rotated back to VWAP, which capped price again. Which is one of the things that can stop the move… through value to the other side… a VWAP rejection or POC rejection" [IMs 07:39]. Exit arms must include: (a) all-out at far edge; (b) partial at mean, rest at far edge; (c) scratch on mean rejection.

5. MANDATORY CONTEXT. (i) A prior imbalanced state against that value area (not a from-inside wander); (ii) his acceptance test — the ONLY definition he ever gives is negative: "It hasn't shown any acceptance actually higher… No time and space above this level. Really, it's just slightly chopping, just barely deviating it" [0B4 05:35-06:06] — so a bare wick/1-bar poke back inside is NOT the trigger; (iii) period reliability ranking: "yearly through quarterly is going to be harder to use… less accurate… weekly and monthly are generally very accurate, and you can trade off of them much easier" [0B4 03:04-03:34] — weekly/monthly (and daily-session per H01) are the taught instruments; (iv) multi-period agreement (week+month simultaneously) is the strengthened form.

6. DISCRETION GAPS → census arms.
- D1 "acceptance back inside": (a) 1 close inside; (b) N=2-3 consecutive closes inside; (c) close inside + successful retest of the crossed edge holding. (This is the load-bearing gap; his negative definition kills arm (a)'s wick-only variant but does not choose between the rest.)
- D2 "momentum rounds out" precondition: (a) no new extreme in last N bars before re-entry; (b) a measurable range/balance forms outside value first; (c) omit (re-entry alone). Arm (c) is the strawman risk — his walkthroughs always show decay first.
- D3 period choice: daily-session / weekly / monthly as separate arms; multi-period-agreement as a boost arm.
- D4 mean-interrupt handling: pause vs kill — "no right or wrong" is his literal answer; both are census arms.
- D5 traversal target static-vs-developing (bands move intraday).

7. DATA NEEDS. 1-min candles + volume for daily-session version; for weekly/monthly VWAPs, minute data over the period. No flow as taught.

8. FREQUENCY. Daily-session VWAP version: ~1-2 qualifying re-acceptances/day in his walkthroughs → ~5-10/week. Weekly/monthly version: ~1-4/month per period per instrument. He treats it as his bread-and-butter event ("The number one thing you're going to be doing in AMT framework is looking for… Acceptance back into value" [cccDZfnKXDY 09:42]).

---

SPEC 3 — DVA-SD2 RETEST FADE WITH COMPOUND ADD (the WTI London recap grammar) — UNTESTED — most mechanical single sequence in the corpus

1. THESIS. Same trapped-chaser logic as Spec 1, but with an explicit as-taught entry grammar, add-on rule, sizing, and target: a full rotation harvested in two tranches. (Recap of two real claimed shorts, WTI, April 27, London session — WuUeHhB2TMM.)

2. ENTRY. Setup state: "when session first opens, it stays rotational within the value area. Comes back into the extreme. Retests the extreme here. Accepts back into the value area. So once it does this, we're going to assume it's going to go to the next extreme and stay rotational" [00:00]. Tranche 1: "Hits the inner deviation two on value area high. We get the retest. Enter off the retest" [00:00] — i.e., price hits the sd2 band above VA-high, pulls away, RETESTS, entry on the retest (not the first touch), 1/3 of risk. Tranche 2 (the add): "we accept back into the value area. We get a retest. Slightly comes back out of the value area. Once it comes back into the value area, this is where we enter… So this is where we put the rest of our risk here" [00:32] — re-entry into the ±1σ band after a shallow poke back out = add location for the remaining 2/3. Window: from session open (London for WTI; the analog for NQ is his overnight Globex window).

3. STOP. NEVER STATED. Only forensic evidence: "We almost got wicked out. It survived" [00:32] → a stop existed just beyond the local extreme. Flag: stop distance is a census choice; "just beyond the sd2 retest high" is the most literal reading, declare 2-3 distances.

4. TARGETS. Single, mechanical, stated twice: "Final TP is value area low of DVA" [00:00, 01:02] — the opposite ±1σ band, full exit, no partials ("Full TP on both" [01:02]). Note this target is the developing line.

5. MANDATORY CONTEXT. (i) Session opened and REMAINED rotational within the developing VA before trigger (no acceptance beyond either edge since open); (ii) a completed prior rotation leg (touch extreme → accept back inside) precedes the trade — the entry is the SECOND visit to the extreme zone; (iii) sizing law, his only mechanical risk rule anywhere: "when I get these initial setups on the extreme, on the standard deviation two, I don't go full risk. I like to compound on these… I took third of my risk here" [00:32]; "with each of my scalps at the moment, I do a third of my risk. So this total was 0.66% of my total risk" [01:02] — 1/3 risk at the extreme, remaining 2/3 on the acceptance-back-inside add.

6. DISCRETION GAPS → census arms.
- D1 "retest" of what: (a) second touch of sd2 after a pullback; (b) pullback below VA-high (+1σ) then retest of +1σ from below; (c) any second approach within X ticks of the first rejection high. His phrase "inner deviation two on value area high" is genuinely ambiguous between sd2-band and VAH — declare both.
- D2 add trigger "accept back into the value area… slightly comes back out… once it comes back into the value area": (a) close back inside ±1σ after the poke; (b) touch back inside; (c) N-bar hold inside. The "slightly comes back out" tolerance (how far out still counts as "slightly") needs a declared band, e.g., <0.5σ excursion.
- D3 stop placement (never stated): beyond sd2 extreme / beyond retest wick / σ-multiple.
- D4 "assume it's going to go to the next extreme": target arm (a) opposite ±1σ (his stated TP) vs (b) opposite sd2 ("next extreme" literally) — he SAYS VAL, so (a) is primary, (b) declared secondary.

7. DATA NEEDS. 1-min candles + volume. Nothing else — this recap uses "developing value area… and price action. No fibs, VWAP [stack], or order flow mentioned" (EXTRACTION-B, video 10).

8. FREQUENCY. "with each of my scalps at the moment, I do a third of my risk" implies this is his routine session scalp: 0-1 completed sequences per rotational session, ~2-4/week per instrument.

---

SPEC 4 — IMBALANCE-FILL REBALANCE ENTRY ("LVN rebalance") — UNTESTED — a taught entry-timing mechanism, spec'd as a conditional arm

1. THESIS. When rejection back inside value happens FAST it leaves an imbalance (single-print/LVN/FVG) — a zone with no two-sided business. The auction habitually rebalances it; entering before the fill risks being early into the mandatory retrace, entering after the fill gets the confirmed edge AND the retrace already spent. "a fair value gap is just like a… buying imbalance or a selling imbalance… the market can come back to rebalance that gap. It's not enough to form a trade off of alone" [66sow9MjlSM 00:30].

2. ENTRY. Parent condition: a Spec-2/Spec-6-type rejection back inside value that leaves an imbalance behind. Then, verbatim from the NQ session (trade 3): "when we shift back down into the value area here, we see an imbalance is left behind… I don't want to enter this short until this imbalance is filled here… so I waited until we get a fill of this imbalance… So, we got the fill of the imbalance. It confirmed to me that the two-day value area high is holding in fact as resistance. And then we entered here on the bearish candle that was going back down" [OmzNrWzekwA 07:12-07:43]. So: (i) rejection leaves gap; (ii) WAIT; (iii) price retraces up and fills the gap, tagging the edge; (iv) entry on the first opposing (bearish, for shorts) candle after the fill. Corollary taught in the same trade: an UNFILLED imbalance overhead is a magnet that can interrupt your position ("It just filled some more imbalance up here and continued back down" [08:44]).

3. STOP. NEVER STATED. Flag. Most literal reading: beyond the filled imbalance origin / the confirmed edge.

4. TARGETS. Inherited from the parent setup (traversal targets — in his instance TP1 at composite VAL ~3.3R, final at yearly VWAP ~8.9R [08:13-08:44]). No independent target logic.

5. MANDATORY CONTEXT. (i) A valid parent rejection at a composite/VA edge (this mechanism never fires standalone — "not enough to form a trade off of alone"); (ii) the edge whose confirmation the fill provides must still be intact when filled; (iii) directional hypothesis agreement (he required his bearish session bias for this short, [OmzNrWzekwA 06:11-06:41]).

6. DISCRETION GAPS → census arms.
- D1 imbalance definition: (a) 3-candle FVG (gap between bar1 extreme and bar3 extreme) on the trading TF; (b) TPO single prints / LVN on the 30-min profile; (c) speed-based (move of ≥X ticks in ≤Y minutes). He never names his construction — he points at a chart.
- D2 "filled": (a) 100% traversal of the gap; (b) touch of gap origin; (c) ≥50% fill. His walkthrough looks like full fill; declare all three.
- D3 entry bar: (a) close of first opposing candle after fill (his literal words); (b) limit at the edge level on the fill tag. Timeframe of that candle unstated (1-min vs 5-min arms).
- D4 staleness: how long the gap stays actionable — no words at all; declare a session-bounded arm and an unlimited arm.

7. DATA NEEDS. 1-min candles for FVG/speed constructions; 30-min TPO aggregation for single-print construction. No flow needed as taught.

8. FREQUENCY. Sub-trigger: fired on 1 of his 3 trades on the showcase night. Realistically ~20-40% of parent re-entry signals leave a qualifying gap → roughly 1-3/week on overnight NQ if the parent fires nightly-ish.

---

SPEC 5 — RE-SPEC: NQ OVERNIGHT COMPOSITE ROTATION (tested as P2 "orochi-overnight-rotation") — INCLUDED BECAUSE THE PRIOR SPEC DEVIATES FROM HIS WORDS

DEVIATIONS IDENTIFIED (prior spec per diagnosis: "entries at the composite edge / sd2 of overnight VWAP confirmed by developing-value shift, targets mean → far edge"):
(a) ENTRY LOCATION STRAWMAN — he NEVER enters at the composite-edge/sd2 touch. All three taught entries are post-confirmation DVA events (see below). A touch-fade census tests a trade he explicitly tells beginners not to take.
(b) TARGET TRUNCATION — "mean → far edge" misses that two of three final TPs lie BEYOND the composite: trade 1 finalized at sd2 of the daily VWAP past the composite VAL ("I just took a final TP at the next extreme of standard deviation 2" [02:35]), trade 3 at the yearly VWAP ("~8.869R" [08:44]). Partials at the composite edge / daily VWAP are the taught intermediate.
(c) MISSING MANAGEMENT LAW — the DVA scratch rule: "if we… shift back into developing value area here, I can close the trade" [08:13]; "we failed to shift back into DVA. If this held here, I'm done. I'm closing the trade" [08:44]. An arm without this exit misprices every loser.
(d) MISSING GATES — pre-session directional hypothesis ("you decide if you're neutral, bullish or bearish for that day or for that week"; he skipped longs-above-composite because of it [06:11-06:41]) and the time-and-space breakout veto ("I don't see enough time and space spent above the two-day… composite" [06:11]).
(e) VWAP OBJECT — his DVA is the daily-session VWAP (TradingView session anchor; = Globex 18:00 ET session for NQ). If the tested "overnight VWAP" was anchored elsewhere (midnight, RTH), the confirmation line was wrong. Verify against the prereg.
(f) COMPOSITE SELECTION — age must NOT bound the search: "Doesn't matter if it's 2 days old, 5 days old, 5 months old… If it's the only area that has balance, the only relevant area of balance, then it's going to be a relevant composite" [00:32] (he traded July 28-29 against a May 3 composite). A recency-bounded amt_days balance detector misses his exact showcase condition.

1. THESIS. Overnight NQ rotating inside an old multi-day composite; each extreme traps the breakout-hopeful side, and the DVA (session VWAP value) tells you when their attempt has died; rotation pays edge-to-edge.

2. ENTRY — three taught variants, one grammar (DVA event confirms, composite provides the map):
- V-A (aggressive shift-out): at composite extreme/sd2 → price re-enters DVA → "we see a strong shift in momentum to the bearish side… we fail to make new highs… we failed a push above the daily VWAP. Daily VWOP holds as resistance and then we see a shift out of the developing value area here. I took this trade here without actually waiting for a pullback" [01:33]. Entry = break of developing VAL. His own conservative override: "I recommend waiting for the retest of the value area low of the developing value area… and then taking the trade" [02:04] — BOTH are declared arms, by his instruction.
- V-B (pullback-confirmed re-acceptance): shift back inside composite AND DVA together → "I wanted to see that the two-day value area low would hold… I needed further confirmation which is why I waited for the pullback. And once I saw that our two-day value area low is now support. Developing value area low is now support. I'm comfortable to enter here… on the one minute time frame" [03:36-04:39]. Entry = 1-min pullback hold of the doubled edge.
- V-C (imbalance-fill retest short): Spec 4 verbatim [07:12-07:43].
Window: Globex overnight (his session ran the evening of Jul 28 into Jul 29).

3. STOP. NEVER STATED numerically anywhere in the video. Trade 1 implies a stop above the failed high/VWAP with willingness to scratch early: "I'm comfortable with taking a trade and closing it early before I hit my stop loss or even at break even and looking to re-enter" [02:04]. Flag: stop + re-entry policy are census arms, and the scratch-and-re-enter behavior materially changes the trade's R distribution — a fixed-stop-only census deviates from his management.

4. TARGETS. Partial at first composite edge or daily VWAP; final at: opposite composite edge (safest — "We're rotational within the 2-day… Anything else is kind of just a guess" [05:10-05:41]), or next sd2 extreme, or HTF magnet (yearly VWAP) when hypothesis supports. Plus scratch rule (c) above.

5. MANDATORY CONTEXT. (i) Pre-session classification: rotational within an identified composite ("I could understand here that we were rotational within this two-day composite" [01:03]); (ii) composite = the relevant balance regardless of age, evidenced by live reactions ("look at the reactions we get off this composite" [00:32]); (iii) directional hypothesis gate on breakout-side trades; (iv) DVA agreement — composite signal alone never fires; every entry required the DVA event.

6. DISCRETION GAPS → arms: "strong shift in momentum" (minute-delta flip / N-bar momentum / engulfing close — 3 arms); "fail to make new highs" lookback; pullback depth and "held as support" test on V-B (touch-and-hold vs higher-low close); composite relevance when more than one balance exists (nearest / most-touched / largest-volume — 3 arms); hypothesis gate operationalization (HTF VWAP-stack position as mechanical proxy vs omit).

7. DATA NEEDS. 1-min candles + volume (session VWAP bands, composite VA construction from volume-at-price); minute-delta ONLY for the "momentum shift" arm family. No depth.

8. FREQUENCY. Showcase night = 3 trades in one overnight session, cherry-picked. As-taught cadence: fires only on nights that are rotational inside a relevant composite (roughly half of nights); implied 1-3 triggers per qualifying night, so ~4-8/week ceiling, realistically fewer.

---

SPEC 6 — RE-SPEC: FAILED AUCTION (tested as P1 "orochi-failed-auction") — INCLUDED BECAUSE THE PRIOR SPEC'S DECLARED ARMS OMIT TAUGHT REQUIREMENTS

DEVIATIONS IDENTIFIED (prior spec per diagnosis: arms = "time-outside thresholds, re-entry close counts, delta at the failure point, absorption of the trapped side, depth-wall state"):
(a) TIMESCALE — his failure clock runs HOURS TO A DAY AND A HALF on a 30-minute TPO: "we spent multiple hours or, you know, a day, day and a half, whatever this was, below value area low, and this should have led to a trend, but it didn't" [04:34-05:04]; the weekend example is "multiple days spent above this level" [05:34-06:04]. If the tested time-outside arms were minutes-to-few-bars intraday thresholds, the census measured a different (faster, noisier) trade than the taught one.
(b) STRUCTURE-OUTSIDE REQUIREMENT MISSING — failure is not bare time-plus-reentry; a second balance must FORM outside value with a specific micro-structure: "If it fails to lead to a trend and we start to kind of range here or balance… that's kind of indicative of weakness" [01:01-01:32]; "it starts to round off, then that may lead to a failed auction" [03:33-04:03]; "we're just putting in these kind of weaker, poor highs here. There's a short squeeze above these highs. So, any early sellers here got taken out" [04:34]. None of (range-formation, rounding, poor extremes, counterparty squeeze) is in the prior declared arm list.
(c) ANTI-KNIFE RULE — entries at the outside extreme are forbidden: "do you want to buy the low down here? Probably not… we just shifted bearish against this profile" [01:32-02:02]. If any tested arm entered pre-re-entry, it deviates.
(d) RETEST OPTIONALITY — the taught entry is the trade-back-inside itself; the retest is a bonus, not a requirement: "we didn't get a larger retest, but again, you just kind of have to go with strength at that point" [07:35]. A retest-mandatory arm under-fires vs his cadence; a retest-only census is a strawman.
(e) VALUE OBJECT — merged multi-day TPO composite ("a composite is when value areas overlap between profiles… you can merge these" [02:02-02:32]; his examples are 3-, 4-, 5-day merges on 30-min TPO). If tested against single-session VAs, the bracket is wrong-sized.

1. THESIS. A break from value that builds balance outside instead of trending has trapped everyone who positioned for the trend; when price re-accepts inside, "any buyers that are positioned here… as we trade lower, they're going to be forced to puke their positions, so you're going to see an accelerated move back through value" [06:04-06:34]. His flagship; "it's very repeatable… It's a failed shift, and then you take the preceding kind of shift" [08:36-09:07].

2. ENTRY. Sequence as taught (long form; mirror for shorts): (i) break below composite VA — VAL flips to resistance; (ii) price ranges/balances below for hours-to-1.5 days, with rounding, poor highs, and a squeeze of early trend-side entrants; (iii) trigger = trade back inside value: "it's another failed auction below the same value… we get a move back into value, right? And that's the long you want to take" [08:36-09:07]; (iv) retest of the re-crossed edge is taken when offered, strength is chased when not [07:35]. Chart: 30-min TPO; order flow only as optional LTF execution aid ("if you're reading order flow, which I was for this short" [06:34-07:05]). Window: any (his examples are BTC incl. weekends; transfer to NQ declared by him: "you can apply the same idea to a volume profile, to a VWAP, really any level" [00:00]).

3. STOP. NEVER STATED in the entire video. Flag. Beyond-the-failure-extreme is implied by the trapped-trader logic, never spoken.

4. TARGETS. Traverse the value area: "value area high, which was support, will be lost, it'll become resistance… and then your next target is going to be value low, point of control, so on and so forth" [06:34] (shorts: VAL with POC en route; longs: "we get the move back to value area high" [05:04-05:34]). "So on and so forth" = continuation beyond the far edge is left open — declare far-edge-stop vs runner arms. POC/mean interrupt rule from Spec 2 applies.

5. MANDATORY CONTEXT. (i) Established multi-day composite (overlap-merged); (ii) genuine prior break (edge flipped, retested from outside — "we retested value area low as resistance… and this should lead to lower" [03:33]); (iii) the failure evidence bundle: time outside at HIS scale + balance formed outside + no trend ("the fact that it didn't lead to a trend is just as important as it leading to a trend" [04:34-05:04]); (iv) context veto acknowledged as-taught: "of course, other contexts and other levels can be taken into account" [04:03] — cannot be mechanized, log as unmodeled residual.

6. DISCRETION GAPS → arms. Time-outside threshold at taught scale: (a) ≥4h, (b) ≥12h, (c) ≥1 full day. Balance-outside test: (a) N≥2 touches each side of an outside range, (b) a formed outside VA (mini-profile) whose value does NOT overlap the parent (i.e., true separate balance), (c) rounding proxy = no new extreme for M 30-min bars. "Poor highs/lows": (a) ≥2 equal extremes within X ticks, (b) omit. Squeeze precondition: (a) an outside-range extreme sweep before re-entry, (b) omit. Re-entry: (a) first 30-min close inside, (b) 2 consecutive closes, (c) close inside + edge retest hold. Retest policy: mandatory / optional-take-strength (his words support optional).

7. DATA NEEDS. 30-min candles + daily VA construction (volume-at-price from minute data, or pure TPO from 30-min bars). The failure-point flow discriminator (delta/absorption/depth) remains OUR overlay — as-taught this is candles-only.

8. FREQUENCY. His walkthrough surfaces ~4-5 instances over ~1.5-2 weeks of BTC 30-min chart → implied 2-3/week per instrument at his scale; on NQ with the hours-to-days clock expect nearer 1-2/week. If the prior census fired far more often than this, that alone is evidence the tested clock was faster than the taught one.

---

CROSS-SPEC FLAGS FOR THE PREREGS
- Stops are never taught anywhere in these four videos (the corpus-wide finding in EXTRACTION-B stands). Every stop arm is our invention and must be declared as such — stop-choice cannot be a silent kill vector.
- Every "value" line he trades is DEVELOPING; frozen-level backtests are a systematic deviation. Declare frozen vs developing as paired arms at least once.
- The regime classifier (rotational vs imbalanced-against-value) is the single shared gate across Specs 1, 2, 3, 5 — misclassifying it fails all four at once; its arms should be declared once, centrally, and reused.
- His only taught sizing law (thirds + compound, Spec 3) changes realized R on multi-tranche setups; a single-entry census understates the taught strategy's expectancy shape on Specs 3 and 5.
