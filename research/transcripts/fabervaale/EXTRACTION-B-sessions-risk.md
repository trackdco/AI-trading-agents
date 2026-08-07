---
date: 2026-08-05
kind: extraction (agent, verbatim)
covers: LQvv5xgy_ik, 8CWKfoSJu3c, fZlNGWvd2Ko, jasv3L-d8ZE, 0jM5Y31YJak, 0KyIEdvVKMQ
---

# Fabervaale extraction — batch B (risk protocol, sessions, mental game)

VIDEO 1 — "Exposing my Risk Management Protocol" (LQvv5xgy_ik)

File: /home/user/AI-trading-agents/research/transcripts/fabervaale/LQvv5xgy_ik.md

Structure: he walks five risk environments — hedge fund, prop firm, CME Group cup, World Trading Cup, personal account — each with its own risk geometry. His thesis: "while retail only focus on technical analysis and strategies... professional only holy grail is risk management" [00:30]. "The prop firm risk geometry, it's different from what they sell on social media... It's not about sniper entry, it's not about high risk to reward low win rate. This is the blueprint for failure in a prop environment" [00:00].

1. HEDGE FUND FRAME (context, not his day-trading rules)
- Goal: "maximize sustainable risk adjust compounding over time... highest possible long-term return for a given level of acceptable risk and survivability" [01:01].
- Start from the risk protocol, not the raw-return protocol [01:33-02:03]. Optimize for risk-adjusted return, not raw return: "the goal of the hedge fund is not to optimize for maximum return. The goal of the hedge fund is to optimize for maximum risk... they want to take the minimum possible amount of risk, and they put a maximum on it" [04:04-04:34].
- Medallion 1988-89 example (15%, 1%) used to argue raw return is meaningless without risk [05:05-06:05]. "in trading you can have a negative week, you can have a negative month, and in the worst case you can also have a negative full year" [05:35-06:05].
- Liquidity capacity: "every model have a maximum liquidity capability... You cannot put billions in a scalping model... you will take too much slippage" [08:08].
- He runs "Edge Forge in mainland Abu Dhabi that I'm using to provide research to the hedge fund... I'm in this side here... Not operational" [07:36]; wants his own fund "in 2027... 2028" [03:04-03:34].

2. PROP FIRM PROTOCOL (mechanically explicit)
- Goal: "high pass rate and high probability of payout" [08:08-08:39].
- Core rule: LOW-VARIANCE, HIGH-WIN-RATE geometry. "going on models that have win rate above 60-70% and are capable of getting you a higher probability of pass rate, a lower risk of ruin, and a lower max drawdown" [09:41].
- Exact risk-reward band: "having high win rate, okay? Moderate risk per trade and going for moderate risk reward, one to one, even one to 0.75, maximum one to 1.5. This is the best for prop firm survival" [10:43-11:14].
- Anti-sniper argument: chasing the 1:10 sniper "that happens one times every week" risks losing the account in the attempt [09:41-10:11]. "Remember that is not a personal account. You cannot manage as a personal account" [09:41-10:11].
- Phases: "on the evaluation phase, the best one is the low variance zone... on the funded phase, you need to optimize for high outcome, because you want to get a payout" [11:44-12:15]. Also "some prop have consistency rules" limiting aggressive optimization [13:48].
- Counterparty risk rule: a Canadian CFD prop flagged a >$50,000 payout during regulator trouble, therefore: "compounding on the prop and keeping all the money on the prop is not the best option... The best option is to withdraw as much as you can and put in your personal account" [12:15-12:48].
- Validation anecdote: traded The Trading Pit live with community using the order flow approach, "high win rate model with low variance and with low risk to reward is the best one probability of passing it" [12:48-13:48].
- Meta-frame: "prop firm trading is way different from real trading... you are not trading the real market, you are trading the rules that another entity put on you. So, you are trading a synthetic market" [11:14-11:44].

3. CME GROUP EQUITY CUP PROTOCOL
- Rules: "single account, so you cannot test on sequential real account, no test... extremely limited time" [13:48-14:18]. CME runs it once per year [14:18-14:49].
- His deployment: "I used the best model that I have and the best model that I have is... the order flow high win rate scalping low variance, the one that you saw me using in all the podcast in the world where I traded live" [14:49].
- Mechanism: "the goal here is to unlock margin to go heavier... keep the drawdown as low as possible because the time is limited, so if you go in drawdown, you have even less margin" [14:49-15:19].
- Result: "I was positioned in the top 0.7, 0.6%... you did 50, 60 execution, you had a net profit of 54.6%, a maximum drawdown 0.42" [15:19-15:51].
- Compounding rule inside the cup: "you have the execution compounding on the heavy side when I release margin... The more I was releasing margin, the more I was getting aggressive" [16:21-16:53]. He flags the protocol as aggressive and drift-dependent: "If you continue with this risk, when you take the negative... maybe you will approach a drawdown that is 10 times this" [15:51-16:21].
- Leaderboard shows both max profit and max drawdown, so you optimize both [16:53].

4. WORLD TRADING CUP (Robbins) PROTOCOL — game theory
- Goal: "terminal rank position, convex upside... limited time... the final goal is the percentage" [17:24-17:55]. "The goal of the competition is not optimized for risk of ruin. It's not optimized for maximum drawdown. It's optimized... for terminal rank positioning" [17:55-18:26].
- Rules he exploits: sequential accounts allowed (multiple model tests); no simultaneous hedged accounts [18:26-18:56].
- Nash-equilibrium point: "Most participants deploy aggression too early. If you open the leaderboard in the beginning is 200% 100% and then they disappear... because they optimize for immediate ranking instead of long-term positioning" [19:26-19:56]. To beat e.g. "my friend Nazri Khan that did that 120%, you cannot use a conservative approach... you need to input the maximum amount of aggression in the late stage" [19:56-20:26].
- Cost realism: models must survive "the markup on execution... and the slippage"; automated quant models "are making profit but never enough to win this kind of competition" [20:26-20:58].
- 3-month blueprint [20:58-23:31]:
  - Phase 1 (month 1): regime detection out of sample. "One account that trend following strategy I tested. One account that has the mean reverting and one account I tested the volatility breakout" [21:29]. Discard whatever the regime is not rewarding [21:29-22:00].
  - Phase 2 (month 2): "validation and moderate risk... you deploy risk on the mean reverting strategy [the winner]... you start to scale" [22:00-23:01]. Testing must be on real account: "for models that have, like the one that I use, 500-600 execution per quarter, the slippage and commission are a huge part of it" [22:31-23:01].
  - Phase 3 (month 3): "convexity exploitation... first slot, second slot, third slot. Usually, they are above 50 to 150%... you need to deploy maximum aggression... In the second half of the middle month and the third month is where I make 3-400 trades. I stay there 6 hours per day scalping with the model that I choose" [23:01-23:31].
- If a 1-year competition: use the first quarter for testing three models, then "approach extreme risk... I will make probably more than 2,000 execution" [23:31-24:03].
- Podium account reconstruction: "The cumulative month is the 68 and 22%... maximum drawdown. We had 89.5%, 158% cumulative... I was in drawdown for the first week and I recovered for the second... And then I deployed aggression in the late phase. Was not enough to win" [24:34-25:04].
- Style/size discards: swing trading is too slow — "for the quarterly competition, you don't have enough sample... winning a World Cup with three, four, five position, it's not a sample validation... It can also be luck" [25:04-25:34]. Small accounts discarded: "if you enter with 2,500, you pay more commission... you need to open micro... it will not survive the execution of 300, 400, 500 trades" [25:34-26:05].
- Actual comp execution: regime test showed directional market; mean reverting bad, trend following amazing; "I open the account that... will go to podium... on this one, I go aggressively trend following scalping... 500, 600... if I'm not wrong, 650 execution" in one quarter [26:05-26:36].

5. PERSONAL ACCOUNT PROTOCOL
- Goal: "Risk adjust return, psychological stability, and long-term compounding" [26:36-27:06].
- Compounding rule: "Only if moderate risk tolerance, you can compound profit... you have a month where you make an exceptional performance, I don't know, six figures in profit, you could use part of this profit to input additional risk in the next sample" [26:36-27:06].
- Per-trade risk: "if you want to be really conservative, it should be 1.25%, 0.5% per trade... I know I'm moderate" [29:08-29:39] (so his own risk is above the conservative 0.5-1.25% band, unspecified exactly). Hard warning: "I saw some people risking 5%... If you incur in a streak of a drawdown, you will destroy" [30:09].
- Capital-size realism: "The problem is the conception in the industry where you can live out of trading with $500, $1,000... If this was possible... I will be billionaire with the amount that I trade" [29:39-30:09].
- Broker diversification (FTX trauma — he was an active crypto scalper on the FTX leaderboard when it shut down): "if I do futures, I have four, five, six broker... they needs to have insurance. You need to isolate tail risk" [27:37-28:08]. "diversification is not with only models and account, but it's also with multiple brokerage and models... Discretionary, algo, short-term, long-term" [28:08-28:38].
- Model diversification: an options algo portfolio run by a paid manager; his discretionary models; an algo model (IVB) "that Luca validated on the multi-charts and also we receive an audit from a market maker that generated 30 million in profit, Matteo" [28:38-29:08].
- Risk pyramid, personal account: "First point is the ability... Second point is risk management, risk adjusted return, and in the end the real return" — inverted vs competition [30:09-30:40].
- Automation + tracking rule: "You need to have an execution model that should be also automated in terms of blocking the maximum risk per day, the maximum risk per week, and you need to track. If there is no measurement, there is no improvement in trading" [31:10-31:40].
- IVB model (opening model — NY AM relevant): "the IVB, that is based on the fact that the nature of the US equities have predictable behavior during the opening... and that the bottom of the first 30 minutes is giving a lot of value in the direction of the day... can be improved with option flow, and this is the study that I'm doing" [31:40-32:11]. Logic shown free on YouTube [28:38-29:08].
- Investment models (not scalping): post-earnings-announcement drift portfolio [32:11]; "blockchain intelligence" BTC accumulation model accounting for miners [32:11-32:43]; holder/13F/congressman-tracking stock research from public government data [32:43-33:13].

VIDEO 2 — "How I did 20R in one NQ Session" (8CWKfoSJu3c)

File: /home/user/AI-trading-agents/research/transcripts/fabervaale/8CWKfoSJu3c.md

SESSION RECONSTRUCTION — Best session of December, NASDAQ (NQ) futures, New York session, Interactive Brokers personal account.
- Self-ID and clock: "I scalp the NASDAQ during the New York session and managed to close the session at $50,000 profit. And I did this while I was also live with my community" [00:00-00:31]. No intraday clock times stated; NQ prices ~25,550-25,760 locate it, and "New York session" is explicit.
- Prior trades: "$27,500 in profit on the first trades of the day" [01:03] (those trades not broken down).
- Featured trade: SHORT NQ, 10 contracts.
  - Risk: "we are risking a small amount of profit, only 3,150 to make an additional 23,000 of profit on the short position here" [01:03-01:35]. On 10 contracts that is a ~15.75-pt initial stop. Later: "we started with a small stop-loss for 3,500 and then we completed the session with a 10x risk-to-reward multiplier" [08:50] (per-position RR quoted up to 1:19).
  - Read/trigger: "the path of least resistance of the buyers getting completely absorbed. You can see the punch to the wall I marked for you and you can see the rewarded effort of the sellers... we have complete control on the auction of the sellers. We are really high in the curve" [01:35].
  - Add rule (negative): "I was considering increasing additional position to contract on the way down. But the price was so aggressive that I could only position myself in discount and is not the best idea when you are already loaded with 10 contracts here to raise the exposure low in the curve" [01:35-02:05]. So: adds only high in the curve (premium), never adds low in the curve when already fully loaded.
  - Management sequence: "the first step that I will do, I will lower my risk to be above the eye [high] or a stop to zero and run this train on the way down trailing aggressively my stop loss when I see that buyers might take back control" [02:05-02:36].
  - Levels read: sellers' control level 25,650; 25,630 (buyer reload level); aggressive sell order + "another punch to the wall" [02:36]; break of 25,584.3 = sellers take control [05:44]; "squeeze" level 25,570 — "if the market managed to break this low at 25,570 this small range... you can expect volatility on the way down... to reach really fast the yellow level" [06:14-06:45]; 25,550 = "also a psychological level we are low in the curve we are in the last point of absorption" [07:15]; 25,534 break [07:47].
  - Target math: "if they break the low the total risk-to-reward to get to the low of the curve is like 1 to 16 1 to 19 on the final target... Final target is 27,600 for 1 to 19 risk-to-reward. This is not common. You need volatility to do these kind of trades. And unfortunately, volatility is not there every day" [03:08-03:40].
  - Trailing-stop ladder (all stops IN PROFIT, dollar-quoted): +$2,550 [03:40] -> +$9,600 ("worst case scenario, we close 36 $37,000" for the day) [06:45] -> partial cover for $20,000 on the single position at the squeeze catalyst [07:15-07:47] -> +$21,000 after 25,534 break [07:47-08:18] -> final exit +$23,000: "I close my stop loss in profit for 23,000 because if these buyers, aggressive buyers take back control, I want to be out of the market" [08:18].
  - Exit trigger for the trail: appearance/recovery of aggressive traders on the opposite side; he waits for an absorbed aggressive seller at a low "to be recovered and break on the way down to cover myself above the last point of break" [07:47].
- Conditional profit-taking rule (drawdown context): "if you were in loss for the day, for example, let's say minus 5,000, it will be smart to take profit and to bring your balance back to break even so you can take a next trade in a calm way. In this case, considering that we have $27,000 profit plus $12,000 profit floating... Doesn't make sense to be super conservative on the profit taking" [04:42-05:13]. I.e., profit-taking aggressiveness scales with day P&L cushion.
- Volatility caveat: "if you want a smoother profit, you can decide to take profit more often than I do when we are in a consolidation phase" [03:40].
- Account proof: "this one it's my interactive broker account... the incredible skew between the maximum draw down on the single position and profit... This is what you can do when the market is really directional. If you know how to trail your stop-loss" [08:18-08:50].
- Marketing/context: appearances on "chart fanatic channel or word of wisdom podcast... or in the channel of Andre"; private charting room "live twice a week" [00:31-01:03].

VIDEO 3 — "My Best Trading Session of the Month" (fZlNGWvd2Ko)

File: /home/user/AI-trading-agents/research/transcripts/fabervaale/fZlNGWvd2Ko.md

SESSION RECONSTRUCTION — Best session of October, NQ (implied; his standard instrument), following directly after a London session.
- Clock: "we came from a London session where we did pretty good amount of profit. That was around $10,000 and we start the session getting caught by a little bit of choppiness here. So we give back $5,000 to the market, around 4,500" [00:30-01:01]. So: he traded London that day (+~$10k), then the New York session opened choppy (-$4.5-5k on two failed continuation shorts).
- Losing trades: "The first trades that we took was a continuation short and we gave back two trades inside here. We tried this continuation and we failed" [00:30-01:01].
- HARD SESSION-STOP RULE (the key protocol quote): "we continue to take with a maximum drawdown that is break even. So if we go back to break even, we stop the session" [01:01-01:33]. Note the reference point is the day's running P&L including the London profit — he's risking only the day's open profit.
- Setup that made the day — failed-auction reversal LONG:
  - Context/trigger: "this consolidation area got completely wrecked by buyers that took control. The sellers got absorbed here. So what I'm trying to do is capitalize on the failed auction of the seller and then aggression of the level of the buyers" [01:01-01:33].
  - Invalidations: "I will be really fast in putting my position to break even if this level failed... because if this level failed, this one become the new pivot" [01:33-02:05].
  - Target frame: "I will try uh good risk to reward trades and amazing risk to reward trades to take the top of the day" [01:33-02:05].
- Scaling/risk mechanics: "I'm loading and scaling in position trying to get my losses smaller and smaller. As you can see, I'm only risking the profit of the day, okay? I'm not risking more. We are up a gain 9,000 for the day, around 10,000 now for the day. And I will continue to scale my position as we go" [02:05-02:37]. Entries: "we loaded the first one here, then we reloaded here, then we reloaded here and this one was our protection level. So we took all the bottom of the up session of the day" [05:44-06:14].
- Risk compression: "the market gives a really solid aggression. My risk goes really low and now I'm risking $980 to make potential $25,000" [02:37-03:10].
- Expectancy frame (worst-day vs best-day sizing): "in the worst session that I can make, I lose around 5,000, 10,000. If we can manage to make more than 25 session, it means that the best session of the month it's two times and a half bigger than the worst session of the month. So this is a pretty good maximum risk to reward balance for the day" [03:10].
- Mid-trade management reads: cover candidates behind defended levels; "if this big trade sell gets stopped out, I don't want to be in the position because we will have a really fast snapback" [02:37-03:10]; buyers wall + absorbed sellers consolidation: "if we break down this level, I want to be risk free or with a really tight stop loss because... we will probably revisit this level here" [03:40-04:11]; stop to zero once "sellers got stopped again in the movement and buyers are starting to continue up. As you can see, big trades in the body of the candle" [04:11-04:42].
- Locked-profit ladder: "covered below this low... worst case scenario, I close $10,000. The best case scenario, I close above $25,000 for the day" [04:42-05:14] -> "Now the worst case scenario, we close $15,000 for the day. This is a really good process that you need to memorize because this is a way to get back your profit from the market as soon as possible and not give back the profit that you make to the market" [05:14-05:44].
- Exit: "the market explode from this level. You see all these aggression and a failed auction and this is the reason I closed my trade... I could have made 40, 50,000 dollar session but I prefer to be conservative when I have a really good sniper trades" [05:44]. After close "the market just skyrocket up. This could have been also 50 to 60,000 dollar day but uh I decided to close" [06:14].
- Summary rule: "We risk a really small amount of money to make a really banger day" [06:14].
- Platform note: "the platform that I'm using it's a professional order flow platform and it will be released on the 9th of November" [00:00-00:30].

VIDEO 4 — "Watch me Manage a -10.000$ trading Session" (jasv3L-d8ZE)

File: /home/user/AI-trading-agents/research/transcripts/fabervaale/jasv3L-d8ZE.md

SESSION RECONSTRUCTION — Worst session of the month, NQ (price level 24,932 quoted), live-recorded drawdown day. Dated internally as "the precession of the 23" [01:32] (the session preceding the 23rd — consistent with pre-holiday compression).
- Clock: "Every movement got absorbed in the first two hours" [00:00] — he is trading from the session open onward; later "Now we are in a super consolidating area in the last two hours" [01:32]; he refuses to extend into the evening (below).
- Condition: "we got the most consolidation session of the month... It got consolidating for all the session... This is the worst market condition you can get for my strategy. Like up, you try the breakout da da da da da. You can take 10 stop loss" [00:00, 01:32].
- Damage: "my trend following model took a straight [streak of] stop loss. We are at $9,000 in draw down for the day" [01:32-02:02]. Elsewhere: "I went in deep draw down. I took a streak of stop-loss and I manage risk without overexposing my account" [00:31-01:02].
- The losing-day protocol as actually practiced:
  1. "What we can do is manage risk correctly, accept a day of draw down if the condition don't get better and also decide to take some profit to reduce the amount of draw down if necessary" [02:02-02:32]. Acceptance of a red day is an explicit option — no revenge sizing.
  2. Keep position risk near zero before adding: "with this movement, I can put risk to almost zero. If it accept and scale inside other two contract... We can scale other two contract here on the way down... Set up here the stop loss $600 and profit target... and also put stop loss to zero. So we don't risk" [03:32-04:04]. Note the add is 2 contracts with a $600 stop, i.e., small clip and tiny dollar risk while in drawdown — he sizes DOWN in drawdown.
  3. Hold one high-RR position and endure: "one short that is floating $3,500 in profit with the potential to make $15,000" [01:32-02:02]; "your only role is to endure during all these moments and get the movement that create a new range. This is the only way to... have a huge amount of probability that you will be profitable with control loss and amazing profit" [10:51].
  4. Wait for the catalyst level: "We will see if the market does a good breakdown on the level 24,932 for a capitulation down" [02:02-02:32]; "if we can break this low, this horizontal level, probability that we go down it's exponential" [05:06].
- Orderflow/positioning reads used: "Big buyers getting absorbed on the top. Today there is a lot of volume. So I need to bigger filter" [01:02-01:32] (he raises the big-trades filter threshold on high-volume days); wall metaphor "If you use the maze 10 times here, every time you hit it gets weaker" [06:09]; short positioning "they have 4.7 billion almost $5 billion short" -> "the market maker and the hedge fund are really aggressive on the downside" [06:09-06:39, 08:18]; tape acceleration signature: "When they decide to approach the level... you will see so fast that this number scales by 1,000 multiple... from 6,000 you see 7,000 like this" [06:39-07:15]; a highlighted trade "18 contract from the top with risk-to-reward 1 to 20... the sniper" [08:49]; gamma regime: "the market maker are long gamma. So they will try to compress volatility. I expect a good explosion down" [09:19] and "when you are positive gamma, they are going to compress every movement" [11:21-11:52].
- Recovery: breakdown finally comes; floating +$7,000 [00:00], +$9,000 [00:00], +$10,000 [08:49-09:19], "I can also close the day with $12,000 in profit, but I expect breakdown. Maybe I put stop in profit to recover all the draw down" [09:19-09:50]; +$13,000 floating [09:50-10:21]; exit: "Sellers entering aggressive. We are going to protect ourself soon here. Okay, we locked in $12,000 and we are out of the position. So, a day that was in negative 9,000 is going to be closing 2,330. Done. Okay, we saved everything and we still made 10,000 for the day" [10:21-10:51] (the two closing figures conflict in the transcript; direction is clear: roughly -9k recovered to a green close).
- END-OF-DAY STOP RULE (operational, stated as principle): "we could have made $7,000 of profit more... But when the day starts really bad and the compression it's so bad, even if the option is confirming, if even if you have order flow confirming down, it's always [not] bad to cut in profit and stop the day because as soon as you go to the evening, your focus lowers because you are sitting on 20 execution and the market finally is trending... So take what the markets gives you" [10:51-11:52]. Two hard facts inside: he had ~20 executions that day, and he treats the evening as a no-trade fatigue zone.
- Regime lesson: "is not the day to trade trend following. And even in the worst session of the month, we made money" [11:52].
- Loss tolerance stated: "Imagine if you can lose $10,000 in one day. You can you can handle it" [05:06] — consistent with the worst-session band of -$5k to -$10k in fZlNGWvd2Ko [03:10].

VIDEO 5 — "My Top 3 Trades from the Competition" (0jM5Y31YJak)

File: /home/user/AI-trading-agents/research/transcripts/fabervaale/0jM5Y31YJak.md

Credentials: "I was ranked three times in the world trading championship day trading division and I was vice champion for two times with a total performance of 350% over 9 months" [00:00]. Competition = "the quarterly world cup of robins [Robbins]" [01:00]. Date of featured session: "this was 30 of December. So, we were on the final days of the competition. We were head-to-head with Nazaran" [04:08].

SESSION RECONSTRUCTION — NQ short day, Dec 30, Robbins Cup.
- Clock: "before the starting of the session it was almost uh 12 uh central central European time we had some kind of balance" [00:00]. 12:00 CET = 06:00 ET — the balance built in the NY pre-market; his "starting of the session" is after that. He "closed the session around four" [06:12] — if CET, 16:00 CET = 10:00 ET, which would put the entire traded sequence inside roughly 06:00-10:00 ET (pre-market into NY AM); ambiguity flag: "four" could also be 4 PM local of another reference, but the CET framing at [00:00] makes 16:00 CET the natural reading. He explicitly "didn't continue to load my position during the evening" [07:48].
- Context: price-action-only view was balanced/confusing; "volume was telling us something different" [00:30-01:00]. "one of my most profitable trading session... a super directional session and I just capitalize on the market collapsing on NASDAQ" [01:00-01:31].
- Tool stack demonstrated: cumulative volume delta (CVD) as leading indicator [01:31-02:03]; volume spread analysis [00:30-01:00, 07:17]; "big trades it's an indicator that we are developing in our proprietary platform... giving us an edge in understanding where the big players are pushing the price" [02:35-03:05]; "delta profile footprint" [06:44-07:17]; auction market theory day types [05:41-06:12].
- Regime call: "the market was balanced at this time but... the direction from the pressure of the market and cumulative volume delta is pretty huge even before the breakout. So the market is clearly building pressure down... this is a distribution" [02:03-02:35]. Rule: "the volume is leading the price" [02:35].
- Trade 1 (short): "the first moment that we had some kind of follow up on volume and confirmation from price was exactly this candle. This was my first position because the market told me Fabio we are going down the volume pressure is down and we have the price action that is following up" [03:05-03:37].
  - Management: "The first position went to break even immediately. So, the market exploded in my direction and I put my stop loss to break even" [04:08-04:39]. Result "almost 1 to three even more 1:5 risk-to-reward ratio" [04:39].
  - His stated day-management model: "my way of trading is keeping draw down really low, building uh the profit for the day and then risking again the profit. So what I'm seeking... is explosion in market movement" [03:37-04:08].
  - Sizing rule: "when the market is giving me another confirmation that the sellers are pushing the price down. I put my first stop loss to break even and I can consider to close the first trade and open a second one with the profit of the first one or just continue to add to my position in direction of the trend" [04:39-05:09].
- Trades 2-3 (adds): "This was the first position. This was the second position. This was the third position. And then I closed all these trades here in the second accumulation phase. Why? Because I start to see that the big trades are not pushing anymore the price down. We are in a redistribution phase" [05:09-05:41]. Exit trigger = big-trades participation dying, not price.
- Re-entry with house money: "From this moment I waited and I took some profit and I use half of this profit to risk again... You see again the price action breaking down. You see again big trades in the direction of the trend because we studied auction market theory and we know that this is a sell model day and we continue to sell and this was another huge takeprofit" [05:41-06:12]. Five different positions trailed in total by that point [06:12].
- Final trade (VSA punch-the-wall short): "the market is breaking down... the price is trying to retrace the buyers are trying to take control... but the results is almost zero. So to do this kind of analysis I usually use the delta profile footprint... the result of the price for a pressure in by delta was almost zero. So this is a confirmation that the buyers are punching a wall and I want to be short" [06:12-07:17].
  - Management: "as soon as the market approach the all-time low for the day you see big traders sell continuing to push down. This is your opportunity to put the risk to zero... and again the market collapse. I took profit for this position at this level. That was the low of the day" [07:17-07:48].
- Stop-for-the-day: "I was sitting at a huge profit for the day. So I didn't continue to load my position during the evening" [07:48].

VIDEO 6 — "Winning the Mental Game of Trading" (0KyIEdvVKMQ)

File: /home/user/AI-trading-agents/research/transcripts/fabervaale/0KyIEdvVKMQ.md

Credential: "I was able to achieve 500% return during 12 months in the world most famous trading competition also known as the robit [Robbins] cup" [00:00-00:31], "with the pressure of the world looking at me" [00:31-01:03].

OPERATIONAL rules (actionable, not just psychology):
- Psychological circuit breaker = hard daily stop, platform-enforced: "you need to have a psychological circuit breaker... a way to interrupt the emotional escalation... So quit breaker. It can be a maximum draw down per day. It can be done directly from the platform. If I reach 1% of draw down, I stop for the day. It can also be [that] the best opportunity the next one on the planet. I will not take it because I'm not in a mental state that let me trade successfully" [17:36-18:07]. Escalation example it prevents: near prop max-drawdown, losing one trade, doubling risk to recover [17:05-17:36].
- Flat per-trade risk: "make sure that every execution have the same amount of money of risk. Don't put more risk only because you think this... will be a good trade because I already took a three stop loss. The next one will be a good trade. This is the best way to go bankrupt" [19:40-20:10]. Cross-reference: "I took 2,000 execution all with the same risk" [16:33].
- Journal fields that feed filters: "You need to have a detailed record to evaluate performance. What time of the day trade? What trigger you use. Why? Because in the long term you can filter... you know that London session is not worth to trade for me. My profit factor is really low. I pay a lot of commission but profit factor is really low... I get half of the day for free" [20:10-20:41]. (Directly supports dropping non-core sessions — a session-selection rule derived from journaling.)
- Scaling rule: "have a gradual position scaling... You made a lot of profit for the week, for the month. You can increase the risk if you want accordingly to the amount of profit. Don't risk all your profit because otherwise you are just putting at risk everything you already made" [21:44-22:14].
- Pre-session regime classification: "my trend following strategy don't perform really good in consolidation market. That's the reason I need to understand before how the market will behave in the session. You can do this with multiple parameters like ATR or open session behavior to understand how much the session will have in average movement" [22:14-22:44].
- Trading plan must contain: "entry and exit rules... risk parameters... favorable market condition. And you need the procedure to handle various trading scenarios" [21:44-22:44].
- Beginner throttle: "We have a limited psychological capital account... don't take if you are a beginner 10 execution per day. Start with short execution and low number of execution. Don't try to take 20 execution per day" [18:38-19:08]. (Implies his own 20/day cadence is expert-level.)
- Habit threshold: "How much time it requires for the mental brain to build an habit. It's around 66 days. If you can achieve 66 days of discipline, journaling, visualization, pre-planning of the session, respecting your plan, you can be a trader" [09:47-10:19].
- Morning ritual: "For me in this case is meditation... 20 minutes... get in a mental state where you are calm before going on charts" [08:15-08:46].
- Cost-of-impulse calculator: "How much does it cost to me an error?... Three losses out of the plan, maybe with one hour of €1,000 or €3,000... Understand that every time you want to untick this part of the checklist of the plan, you are taking this risk" [10:19-10:50]. (Confirms a written checklist exists per plan.)
- System over willpower: "It's really difficult to be disciplined if you don't have rules" [21:12-21:44].

PURE psychology (non-operational): acceptance/awareness/responsibility/practice/patience five-step [04:08-04:39]; probability-vs-prediction reframe [01:34-02:37, 14:28-14:59]; acceptance paradox (expect a loss daily so you don't overreact) [07:44-08:15]; kintsugi metaphor [11:22-11:54]; strategy-hopper journey [15:31-16:02]; "100 people same strategy performed differently... You are yourself the strategy" [13:58-14:28]; definition "profitable trading is consistent execution of positive expectancy" [14:28-14:59]; overtrading example (30/100 trades in plan) [02:37-03:37]; spillover effect [12:56].

RISK PROTOCOL — CONSOLIDATED

Per-trade risk
- Personal account conservative benchmark: 0.5-1.25% per trade; he self-describes as "moderate", i.e., above that, never quantified exactly [LQ 29:08-29:39]. 5%/trade called account destruction [LQ 30:09].
- Every execution carries the same dollar risk; no martingale after losses [0K 19:40-20:10, 16:33].
- Observed dollar stops on NQ: $3,150-$3,500 initial on a 10-contract clip (~16-17.5 pts) [8C 01:03, 08:50]; $600 on a 2-contract add (~15 pts) [ja 04:04]; $980 total open risk mid-scale [fZ 02:37].
- Prop accounts: moderate risk per trade, target RR 1:0.75 to 1:1, max 1:1.5, win rate >60-70% — low-variance geometry [LQ 10:43-11:14].

Daily loss limits / session stops
- Platform-enforced daily circuit breaker; example threshold "If I reach 1% of drawdown, I stop for the day" [0K 17:36-18:07]. Execution model "automated in terms of blocking the maximum risk per day, the maximum risk per week" [LQ 31:10].
- Session stop when green cushion is consumed: "if we go back to break even, we stop the session" [fZ 01:01-01:33].
- Realized worst-day band: -$5,000 to -$10,000 [fZ 03:10]; -$9,000 intraday drawdown tolerated on the recorded worst day [ja 01:32-02:02]; "you can lose $10,000 in one day. You can handle it" [ja 05:06].
- Best-day target ~2.5x worst-day loss ($25k+ vs $5-10k) as the day-level risk-reward balance [fZ 03:10].
- Stop trading into the evening regardless of confirmation once execution count is high (~20) and the day started badly — fatigue rule [ja 10:51-11:52]; same behavior at huge profit ("didn't continue to load my position during the evening") [0j 07:48].

Scaling up / down
- Core intraday engine: keep drawdown near zero, build day profit, then risk ONLY the day's profit on subsequent trades ("I'm only risking the profit of the day... I'm not risking more" [fZ 02:05-02:37]; "keeping draw down really low, building the profit for the day and then risking again the profit" [0j 03:37-04:08]; "use half of this profit to risk again" [0j 05:41]).
- Add-on rules: add on fresh confirmation in trend direction after moving stop to break even [0j 04:39-05:09]; add only high in the curve (premium), never raise exposure low in the curve when fully loaded [8C 01:35-02:05]; don't add while a big opposing trade is at risk of being stopped (snapback risk) [fZ 02:37-03:10].
- In drawdown he sizes DOWN (2-contract adds, $600 stop, stop-to-zero) and accepts the red day rather than pressing [ja 02:02-04:04].
- Weekly/monthly scaling: increase risk in proportion to banked profit; never risk all accumulated profit [0K 21:44-22:14]; exceptional month (six figures) -> deploy part of the profit as extra risk next period [LQ 26:36-27:06].
- Competition scaling: aggression proportional to released margin (CME cup) [LQ 16:21] and back-loaded to the final phase (Robbins) [LQ 23:01-23:31].

Trailing / trade management
- Sequence on every winner: stop to break even on first confirmation -> stop to zero/risk-free -> ladder stop-in-profit at orderflow events (level breaks, absorbed aggressors recovered) -> exit when aggressive opposite-side traders take back control [8C 02:05-08:18; fZ 04:11-05:44; 0j 04:08-07:48].
- Partial covers to lock worst-case day P&L in steps ($10k -> $15k... ) — "get back your profit from the market as soon as possible and not give back the profit" [fZ 04:42-05:44].
- Profit-taking aggressiveness scales with cushion: red or flat day -> take profit early to restore break even; big green day -> let the 1:16-1:19 runner work [8C 04:42-05:13].

R accounting
- He accounts in dollars per position and per day, with RR quoted per position (1:3-1:5 typical managed winner [0j 04:39]; 1:16-1:20 on volatile runner days [8C 03:08-03:40; ja 08:49]) and a session-level multiple (initial $3,500 stop -> $50k day = "10x risk-to-reward multiplier" for the session — the "20R" of the title is day P&L over initial stop, ~$50k/$3,150) [8C 08:50].
- Expectancy accounting always includes commission and slippage; a profitable model becomes unprofitable without them, especially at 500-650 executions/quarter [LQ 20:26-24:03].

Compounding / withdrawals / structural risk
- Withdraw from props aggressively; keep money in personal accounts [LQ 12:15-12:48].
- 4-6 futures brokers, insured, multiple platforms/models to isolate tail risk (FTX lesson) [LQ 27:37-28:38].
- Diversify discretionary + algo + managed options book [LQ 28:38-29:08].
- Measurement mandate: "If there is no measurement, there is no improvement in trading" [LQ 31:10]; journal time-of-day and trigger per trade, filter sessions by profit factor [0K 20:10-20:41].

SETUPS / MODELS

1. ORDER FLOW HIGH-WIN-RATE SCALPING, LOW VARIANCE (the core model; used in CME cup, podcasts, all live sessions)
- TRIGGER: aggression + confirmation — big trades hitting in the direction of pressure with price following (effort WITH result), after CVD shows building pressure/distribution [0j 02:03-03:37]; or absorption failure of the opposing side ("punch to the wall", "path of least resistance... completely absorbed") [8C 01:35].
- CONTEXT: needs a directional/expanding regime; classified pre-session via ATR/open-session behavior [0K 22:14-22:44]; auction position matters (high/low in the curve, premium/discount) [8C 01:35-02:05]; gamma regime filter — long/positive gamma = compression, movements get compressed, trend trades off [ja 09:19, 11:21-11:52].
- STOP & TARGET: small fixed dollar stop (observed ~15-17 NQ pts on the clip), instant break-even on confirmation, stop-to-zero, then trailed on orderflow; targets are auction extremes (low of the curve/top of day), 1:1-1:1.5 in prop mode, up to 1:16-1:20 with volatility [8C 03:08-03:40; LQ 10:43].
- TOOLS READ: CVD, volume spread analysis (effort vs result / "punching a wall"), proprietary big-trades indicator (threshold raised on high-volume days [ja 01:02-01:32]), delta profile footprint, volume profile / value area, marked absorption and squeeze levels, psychological round levels, options positioning (billions short) and gamma [0j 01:31-07:17; 8C 02:36-07:15; ja 06:09-09:19].
- DISCRETION GAPS: what counts as "aggressive"; big-trades filter size; where exactly stops trail ("I'm playing with the stopping profit because I was not sure where to put it" [8C 07:15-07:47]); when regime is "directional enough"; his actual per-trade % risk.
- QUANT CLAIMS: win rate >60-70% [LQ 09:41]; CME cup 54.6% net, 0.42% max DD, 50-60 executions, top ~0.6% [LQ 15:19-15:51]; 500-650 executions/quarter [LQ 22:31, 26:05].

2. FAILED-AUCTION REVERSAL (October best session)
- TRIGGER: consolidation "completely wrecked" by one side; opposite side absorbed; enter with the aggressor at the reclaimed level after the failed auction [fZ 01:01-01:33].
- CONTEXT: post-shakeout at a session extreme; taken to "take the top of the day" [fZ 01:33-02:05].
- STOP & TARGET: below the failure pivot; break even "really fast" if the level fails (level failure redefines the pivot); scale-in on aggression; target session extreme, day RR risking-$980-for-$25k class [fZ 01:33-03:10].
- TOOLS READ: big trades, absorption, buyer/seller walls, protected levels [fZ 02:05-04:11].
- DISCRETION GAPS: which consolidations qualify; reload spots; when "conservative" close beats holding the runner (he left $25-35k twice) [fZ 05:44-06:14].
- QUANT CLAIMS: none beyond the session P&L.

3. TREND FOLLOWING / CONTINUATION MODEL (his stated competition podium model, "trend following scalping" [LQ 26:05-26:36])
- TRIGGER: breakout/continuation with volume; explicitly breaks down in consolidation ("you try the breakout da da da da. You can take 10 stop loss" [ja 00:00]; "my trend following strategy don't perform really good in consolidation market" [0K 22:14]).
- CONTEXT: directional regime only; discarded when regime compresses [LQ 21:29-22:00].
- QUANT CLAIMS: 650 executions in the podium quarter, 68%/89.5%/158% cumulative legs, 22% max DD [LQ 24:34-26:36].

4. SELL-MODEL DAY / DISTRIBUTION SHORT (competition Dec 30) — CVD distribution + first volume-with-price candle = entry; add on each fresh seller confirmation; exit adds when big trades stop participating (redistribution); re-enter with half of booked profit; final punch-the-wall short via footprint delta-vs-price divergence at retrace [0j 02:03-07:48]. Discretion gaps: distribution-vs-accumulation call is tool-assisted judgment; "almost zero result" threshold unquantified.

5. IVB OPENING MODEL (algorithmic, disclosed free on YouTube)
- TRIGGER/CONTEXT: "the nature of the US equities have predictable behavior during the opening... the bottom of the first 30 minutes is giving a lot of value in the direction of the day" [LQ 31:40-32:11]. Being enhanced with option flow.
- QUANT CLAIMS: validated by Luca on MultiCharts; independently audited by "Matteo," a market maker with $30M profit, who confirmed the volume component adds value [LQ 28:38-29:08].
- This is the single most directly NY-AM-codable model mentioned: first-30-minutes low as day-direction signal.

6. MEAN REVERSION and VOLATILITY BREAKOUT models — named only as competition test accounts, no mechanics given [LQ 21:29].

7. Investment models (out of scope for scalping): post-earnings drift portfolio [LQ 32:11], blockchain-intelligence BTC accumulation [LQ 32:11-32:43], holder/congressman-tracking stock research [LQ 32:43-33:13], options algo portfolio (outsourced) [LQ 28:38].

TRADER PROFILE — FACTS

- Name: Fabio ("the market told me Fabio" [0j 03:05-03:37]); handle Fabervaale. Discretionary orderflow scalper.
- Instrument: NASDAQ futures (NQ) — every reconstructed session; prices 24,932-25,760 (NQ full contract); Interactive Brokers shown for the personal account [8C 08:18]; 4-6 futures brokers total [LQ 27:37].
- Size: 10 NQ contracts full clip [8C 01:35]; 2-contract adds in drawdown [ja 03:32]; an "18 contract from the top" trade referenced [ja 08:49]; six-figure profit months referenced [LQ 27:06].
- Day P&L range: best sessions +$25k to +$50k; worst sessions -$5k to -$10k [fZ 03:10; 8C 00:00].
- Frequency/hold times: ~20 executions on a heavy day [ja 11:21]; 300-400 trades in the last 6 weeks of a competition quarter, 6 h/day in that phase [LQ 23:31]; 500-650 executions/quarter; ~2,000 executions cited for 12 months [0K 16:33]. Hold times: minutes to a couple of hours (scalps trailed through a session leg).
- Competitions: Robbins World Cup Trading Championship, day trading division — ranked (podium) 3 times, vice champion twice, 350% total over 9 months [0j 00:00]; also "500% return during 12 months" [0K 00:31]; quarterly format, sequential accounts legal, hedged simultaneous accounts and arbitrage illegal [LQ 18:26-18:56]; rival: Nasri/Nazri Khan, footprint scalper, ~120% [LQ 19:56, 30:40], head-to-head "Nazaran" on Dec 30 [0j 04:08]. CME Group Equity Cup (annual, single account, no testing): 54.6% net, 0.42% max DD, top ~0.6-0.7%, 50-60 executions [LQ 14:18-15:51].
- Prop history: The Trading Pit traded live with community [LQ 12:48]; unnamed Canadian CFD prop, >$50k payout flagged [LQ 12:15]. Ex-FTX crypto scalper (leaderboard) [LQ 27:37].
- Business: Edge Forge (B2B research to hedge funds, mainland Abu Dhabi) [LQ 07:36]; building a proprietary professional orderflow platform (big-trades indicator; launch Nov 9) [fZ 00:00; 0j 02:35]; private charting room, live twice a week [8C 00:31-01:03]; business partner Luca (algo validation, live commentary) [LQ 28:38; 0j 05:09]; podcast appearances: Chart Fanatic, Word of Wisdom, Andre's channel [8C 00:31].
- Sessions traded: New York session primary (explicit); London occasionally (one +$10k London morning [fZ 00:30]); avoids the evening.

MENTAL-GAME: OPERATIONAL vs TALK

Operational (enforceable): platform-enforced daily max-drawdown circuit breaker (e.g. 1%/day) [0K 17:36-18:07]; automated max risk per day AND per week [LQ 31:10]; back-to-break-even session stop [fZ 01:01]; flat dollar risk per execution, no post-loss size increase [0K 19:40-20:10]; journal time-of-day + trigger per trade, prune sessions by profit factor [0K 20:10-20:41]; profit-proportional scaling, never risking the full banked profit [0K 21:44-22:14]; pre-session regime check (ATR / open behavior) gating which model is allowed [0K 22:14-22:44]; execution-count/evening fatigue stop [ja 10:51-11:52]; beginner execution throttle [0K 18:38-19:08]; written plan checklist with cost-of-deviation calculation [0K 10:19-10:50]; 20-minute pre-market meditation [0K 08:15-08:46]; 66-day discipline streak as a go/no-go trader test [0K 09:47-10:19].
Talk (mindset only): five-step inner journey, acceptance paradox, probability-vs-prediction, kintsugi, mirror/responsibility, strategy-hopper, spillover effect [0K throughout].

SESSION-CLOCK EVIDENCE (everything about WHEN he trades)

- "I scalp the NASDAQ during the New York session" [8C 00:00] — primary declaration.
- Robbins Dec 30 session: pre-session balance "was almost uh 12 uh central central European time" [0j 00:00] = 06:00 ET (NY pre-market); breakout traded after that; "I closed the session around four" [0j 06:12] — read as 16:00 CET = 10:00 ET given the CET framing (flag: unit not restated); "I didn't continue to load my position during the evening" [0j 07:48]. Net: the whole documented competition winner ran roughly 06:00-10:00 ET.
- October best session: "we came from a London session where we did pretty good amount of profit... around $10,000 and we start the session getting caught by a little bit of choppiness" [fZ 00:30] — London AM traded, then the NY open chop, then the NY-session reversal leg. NY open chop cost him $4.5-5k before the day-making trade.
- Worst session: "Every movement got absorbed in the first two hours" [ja 00:00] — he was executing from the first two hours of the session; "we are in a super consolidating area in the last two hours" [ja 01:32]; evening explicitly avoided: "as soon as you go to the evening, your focus lowers because you are sitting on 20 execution" [ja 11:21-11:52].
- Journal-driven session pruning: "you know that London session is not worth to trade for me. My profit factor is really low... I get half of the day for free" [0K 20:10-20:41] — time-of-day is a first-class journal field and filter.
- Competition phase-3 workload: "I stay there 6 hours per day scalping" [LQ 23:31].
- IVB model anchor: "US equities have predictable behavior during the opening... the bottom of the first 30 minutes is giving a lot of value in the direction of the day" [LQ 31:40-32:11] — i.e., 09:30-10:00 ET structurally significant in his own research.

NY-AM / PRE-MARKET RELEVANCE (08:00-10:30 ET NQ)

Directly transferable to the 08:00-10:30 ET window:
1. The Dec 30 competition session is the best time-stamped evidence: pressure built in pre-market balance (~06:00 ET, CVD distribution while price balanced), the tradeable breakout came at/after the open, and the session was done by ~10:00 ET. The pattern — pre-market CVD/delta divergence against a balanced profile, first volume-confirmed candle out of balance as entry — is an open-window play [0j 00:00-07:48].
2. IVB: low of the first 30 minutes (09:30-10:00 ET) predicts day direction; he considers this validated and audited, and is extending it with option flow [LQ 28:38-32:11]. This is the most quant-ready NY-AM claim in the corpus.
3. First-two-hours diagnostic: on the worst day, wall-to-wall absorption in the first two hours told him the day was untradeable for trend-following [ja 00:00]; conversely, NY-open choppiness on the October day cost a known, bounded amount ($4.5-5k) before the regime resolved [fZ 00:30-01:01]. Consumer implication: the open (09:30-10:30) is where he pays regime-discovery tuition, with a hard floor (break-even/day stop) under it.
4. His day-P&L engine fits a short window: small fixed initial risk at the open -> break even fast -> risk only accumulated day profit on adds -> trail on orderflow -> stop when aggressive opposite flow appears or profit is "huge". Nothing in the mechanics needs the afternoon; his best documented sessions concentrate execution early and he affirmatively refuses evening trading twice [0j 07:48; ja 11:21-11:52].
5. Caveats for the window: the 1:16-1:20 runners require volatility that "is not there every day" [8C 03:40]; long/positive-gamma days compress every movement and invalidate breakout/trend entries [ja 09:19, 11:21] — a pre-08:00 gamma-positioning check is part of his actual context stack; on high-volume days he raises the big-trades filter threshold before the open [ja 01:02-01:32].
6. Unstated gap: no transcript pins an exact entry clock time in the 08:00-09:30 ET pre-market other than the 06:00 ET balance observation; his "New York session" wording plus the ~10:00 ET close on the flagship comp day support NY-AM concentration but do not prove he trades 08:00-09:30 specifically.
