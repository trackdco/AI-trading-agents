# Multi-firm farm

Retrieved 3 Nov 2026 from each firm's help centre. Apex is not in this file. Nothing here places an order. Costs are TopstepX's MNQ $1.22 round turn plus one tick each side, scaled to a 16-point stop. Lucid's fee is not printed. Where the table uses Lucid, the fee in the path is an assumed $100.

## Who qualifies

A firm is in the simulator only if a bot is allowed and the funded plan has no consistency rule, an end-of-day trail that locks, and a small payout day. The others were read and left out.

| firm | in the sim | why |
|---|---|---|
| LucidFlex | yes | Bot allowed. Funded consistency none. Stated breach: eod. |
| Topstep | yes | Bot allowed. Funded consistency none. Stated breach: intraday. |
| Tradeify Select Flex | yes | Bot allowed. Funded consistency none. Stated breach: intraday. |
| MyFundedFutures Rapid EOD | yes | Bot allowed. Funded consistency none. Stated breach: eod. |
| FundedNext Futures Flex | yes | Bot allowed. Funded consistency none. Stated breach: eod. |
| take_profit_trader | no | Bots and algorithmic execution are prohibited on every account. |
| alpha_futures | no | Full automation is prohibited, and account rolling is named as a banned practice. |
| elite_trader_funding | no | A bot needs written authorization. The only tools they currently authorize are listed trade copiers. |
| bulenox | no | The Master account pays only if the best day is at most 40% of profit. That is a funded consistency rule, so the one-big-day recipe is blocked. |
| earn2trade | no | The prohibited-conduct page bars software and AI used for an unfair advantage, and the programs are a progression evaluation rather than a Flex-style funded account. |
| tradeday | no | Third-party bots are forbidden and the Tradovate API is not exposed. That is not a platform you can hang an unattended farm on. |
| lucid_pro | no | Eval can be passed in one day and has no consistency rule, but the funded payout table did not extract into clean cells. Inventing the caps would overstate the firm. |
| lucid_direct | no | Straight to funded, with a 20% consistency rule. That is not a no-consistency funded account. |
| fundednext_rapid_pro | no | Bots are allowed, but the funded account has a 40% consistency rule, so the one-big-day payout is blocked. |
| tradeify_growth | no | Bots are allowed under the same exclusive-use rule, but Growth sim-funded payouts have a 35% consistency rule. |

## Quotes

### LucidFlex

- https://support.lucidtrading.com/en/articles/11404728-other-trading-activities: "Bots and trade copiers are allowed on Lucid. LucidFlex news trading is allowed and is not a breach."
- https://support.lucidtrading.com/en/articles/12945805-lucidflex-consistency-percentage: "Consistency Percentage must be 40% or less, or 50% or less with the add-on. It applies only during the evaluation."
- https://lucidtrading.com/general-faq/: "Up to 10 active evaluation accounts per household/family. Up to 5 active funded accounts per household/family. Total combined limit across eval + funded is 10. Automated strategies and in-platform/third party trade copiers are permitted. Hedging is prohibited. LucidFlex payouts need 5 profitable trading days plus positive net profit. Accounts are one-time fees."

### Topstep

- https://help.topstep.com/en/articles/11187768-topstepx-api-access, 2026-09-17: "Bots are allowed. Orders must come from the trader's own device. VPS and VPN use for orders is banned."
- https://help.topstep.com/en/articles/8284215-express-funded-account-parameters: "You can hold up to 5 active XFAs at a time. Balance starts at $0."
- https://help.topstep.com/en/articles/8284197-trading-combine-parameters: "Can I have more than one Trading Combine? Yes. There's no limit to the number of Trading Combines you can have."

### Tradeify Select Flex

- https://help.tradeify.co/en/articles/10468318-guidelines-for-traders: "You must prove you are the sole owner. Using the bot across multiple firms is against Tradeify's policy. No high-frequency bots."
- https://help.tradeify.co/en/articles/10495897-rules-trailing-max-drawdowns: "The limit only updates at the end of the day, but it is enforced in real time. Touching it fails the account immediately."
- https://help.tradeify.co/en/articles/10468320-rules-consistency-rule: "Select evaluation is 40%. There is no consistency rule for Select accounts in funded mode."
- https://help.tradeify.co/en/articles/14369021-tradeify-pricing-reference: "Select 50K with 40% consistency costs $165. With the 50% add-on it costs $205."
- https://help.tradeify.co/en/articles/12853966-select-flex-and-select-daily-payout-policies: "Select Flex, accounts bought on or after 1 Sep 2026: 50K cap is 50% of total profits, capped at $2,500. Winning day is $150. Split is 90/10."
- https://help.tradeify.co/en/articles/10468251-how-many-simulated-funded-accounts-can-i-have-at-once: "Up to 5 simulated funded accounts per person and per household. Up to 15 Select evaluations per 30 days."

### MyFundedFutures Rapid EOD

- https://help.myfundedfutures.com/en/articles/8444599-fair-play-and-prohibited-trading-practices: "Traders may use automated strategies tailored to their own settings so long as they do not exploit the favorable fills of the simulated environment. High-frequency trading is not allowed."
- https://help.myfundedfutures.com/en/articles/16158363-rapid-eod-50k-a-comprehensive-look, 2026-08-24: "Evaluation consistency is 30%, minimum 4 days, EOD max loss $2,000, target $3,000. Sim funded consistency is none. Buffer $2,100, then $500 since the last payout. No cap. Minimum request $500. Split 90/10. Trail locks at $100. No activation fee. Tier-1 news is banned once funded."
- https://help.myfundedfutures.com/en/articles/16498635-moving-from-evaluation-to-sim-funded-account: "Up to 10 active evaluations. Rapid EOD 50K is capped at 3 sim-funded accounts."
- https://myfundedfutures.com/blog/myfundedfutures-rapid-eod-plan: "The blog states both a $135 one-time fee and a $157 one-time fee for the 50K. The help centre does not print either number."

### FundedNext Futures Flex

- https://helpfutures.fundednext.com/en/articles/14298560-is-the-usage-of-automated-trading-systems-eas-and-bots-allowed-in-fundednext-futures, 2026-04-09: "FundedNext Futures allows EAs and trading bots during the Challenge and on FundedNext Accounts. Latency abuse and order flooding are prohibited."
- https://helpfutures.fundednext.com/en/articles/17229807-what-is-fundednext-futures-flex-challenge, 2026-10-29: "Flex 50K target $2,500, maximum loss $1,500, locks at $50,100. Price $141.99, third purchase onward $84.99. Consistency 40% in the challenge only."
- https://helpfutures.fundednext.com/en/articles/17229848-fundednext-futures-flex-fundednext-account-all-rules: "No consistency rule once funded. Five benchmark days of $200, $500 cycle profit, minimum withdrawal $250, maximum 50% up to $1,500, 95% reward share, account ends after 5 rewards."
- https://helpfutures.fundednext.com/en/articles/17225812-how-many-accounts-can-i-hold-with-fundednext-futures-and-what-is-the-maximum-allocation-available: "Challenges up to $750,000 combined. Up to 5 active funded accounts per user and per household, and 10 issued per calendar month."

### take_profit_trader

- https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/34431153546397-TakeProfitTrader-Universal-Trading-Policies-UTP: "No Trading Bots or Algos. Automated trading systems, bots, or algorithmic execution tools are not permitted."
- https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15171769361053-PRO-Account-Rules: "We do not allow any automated or bot trading of any kind. All trades must be manually executed by the trader."

### alpha_futures

- https://help.alpha-futures.com/en/articles/9508585-prohibited-trading-practices: "The use of AI, bots, and other automated trading mechanisms is strictly prohibited. Hands-off full automation is forbidden. Account rolling, max leverage into the max loss and then buying another account, is not tolerated. VPS is permitted. VPN to hide an IP is not."

### elite_trader_funding

- https://elitetraderfunding.app/help/trade-copier-disclaimer: "You may not use AI, bots, automated trading systems, or other automated trading strategies unless expressly authorized in writing by ETF. The only automated tools currently authorized are the approved trade copiers."

### bulenox

- https://bulenox.com/index.php/help/master-account/: "The 40% Consistency rule states that upon submitting a withdrawal request, the balance must not consist of more than 40% of the total profit balance from a single trading day. Minimum withdrawal $1,000 after 10 trading days."
- https://bulenox.com/help/qualification-account/, 2023-08-14: "Connecting to Rithmic through a third-party API or trader composite software costs $100 a month. The page does not say a self-written bot is banned."

### earn2trade

- https://help.earn2trade.com/en/articles/9286647-prohibited-conduct-in-earn2trade-evaluations-and-in-the-livesim-live-trading-environment: "Utilizing software, artificial intelligence, or ultra-fast data entry techniques that could manipulate the trading environment or provide an unfair advantage is prohibited conduct."

### tradeday

- https://tradeday.freshdesk.com/en/support/solutions/articles/103000085101-automated-algo-and-bot-trading: "We do not make platform APIs available to traders. Algos and bots purchased from a third party are forbidden. If multiple users are making the same trades, the accounts will be shut down."
- https://tradeday.freshdesk.com/en/support/solutions/articles/103000121031-prohibited-trade-practices: "Using a VPN or VPS to mask the location of the trading is prohibited. Hedging across accounts is prohibited. More than 200 trades in a day is prohibited."

### lucid_pro

- https://support.lucidtrading.com/en/articles/12890029-lucidpro-evaluation-account, 2026-08-26: "Pass the evaluation in one trading day."

### lucid_direct

- https://support.lucidtrading.com/en/articles/12890178-luciddirect-consistency-percentage: "LucidDirect uses a 20% consistency rule."

### fundednext_rapid_pro

- https://helpfutures.fundednext.com/en/articles/17230245-is-there-any-consistency-rule-to-be-followed-in-the-fundednext-futures-challenge-fundednext-account: "On the FundedNext Account, 40% consistency applies only to Rapid Pro. Legacy and Flex have no consistency rule once funded. Direct is 20% perpetual. Rapid Daily has none at either stage and uses a buffer."

### tradeify_growth

- https://help.tradeify.co/en/articles/10468320-rules-consistency-rule: "Growth Sim Funded Accounts must follow a 35% Consistency Rule."

## The recipe

Eval days are the fewest equal winning days that fit the consistency rule. Two equal days are 50%, so they pass Topstep's 55% and a 50% add-on, and they fail a 40% rule. A 30% rule needs four. A red day risks the whole max-loss line. The funded day in the recipe is sized so that one large day plus the minimum winning days fills the payout cap. That large day can pay more than the stop, so a 50% hit rate on it is not a zero-expectancy coin. The symmetric column is the zero-expectancy coin: the winning day equals the stop, and costs make it slightly negative before the firm takes a fee.

| firm | stated grade | eval days | recipe day | recipe EV | symmetric coin EV | payouts / 100 (recipe) | recipe hit rate that clears zero |
|---|---|---:|---:|---|---|---:|---|
| Topstep | intraday | 2 | $3,400 | $107 ($83 to $132) | $5 ($-4 to $14) | 12.1 | 45.0% |
| LucidFlex | eod | 3 | $3,400 | $42 ($16 to $69) | $2 ($-16 to $20) | 9.0 | 55.0% |
| FundedNext Futures Flex | eod | 3 | $2,200 | $27 ($6 to $47) | $2 ($-13 to $16) | 10.0 | 55.0% |
| Tradeify Select Flex | intraday | 3 | $4,400 | $10 ($-24 to $45) | $-114 ($-122 to $-106) | 8.3 | 55.0% |
| MyFundedFutures Rapid EOD | eod | 4 | $2,100 | $-82 ($-96 to $-68) | $-157 ($-157 to $-157) | 4.2 | 60.0% |

### Same book, other grade, and the opening-range holdout

The 5-minute rule is the one from the earlier note: first 5 minutes set the direction and the stop, flat before 15:55. Holdout is July 2025 through July 2026, n=266, mean net R 0.094. That interval included zero when it was measured. It is the least-bad holdout in this repo, not a proven edge. Sized here to the day's stop.

| firm | grade | recipe EV | signal EV | signal payouts / 100 |
|---|---|---:|---:|---:|
| LucidFlex | stated | $42 ($16 to $69) | $-97 ($-100 to $-94) | 0.2 |
| LucidFlex | intraday | $-12 ($-26 to $2) | $-97 ($-101 to $-94) | 0.2 |
| Topstep | stated | $107 ($83 to $132) | $-54 ($-57 to $-52) | 0.1 |
| Topstep | eod | $194 ($158 to $231) | $-52 ($-55 to $-49) | 0.3 |
| Tradeify Select Flex | stated | $10 ($-24 to $45) | $-164 ($-166 to $-162) | 0.0 |
| Tradeify Select Flex | eod | $16 ($-21 to $53) | $-165 ($-165 to $-165) | 0.0 |
| MyFundedFutures Rapid EOD | stated | $-82 ($-96 to $-68) | $-155 ($-158 to $-153) | 0.1 |
| MyFundedFutures Rapid EOD | intraday | $-96 ($-109 to $-83) | $-152 ($-162 to $-142) | 0.0 |
| FundedNext Futures Flex | stated | $27 ($6 to $47) | $-85 ($-85 to $-85) | 0.0 |
| FundedNext Futures Flex | intraday | $-30 ($-39 to $-20) | $-84 ($-86 to $-83) | 0.0 |

### Fee assumptions

- LucidFlex: $80 → $62, $100 → $42, $150 → $-8. Help centre describes a one-time fee and does not print it. Rank uses an assumed $100. The table also runs $80 and $150.
- FundedNext Futures Flex: $85 → $27, $142 → $-30. List price on the Flex challenge page is $141.99. The same page says the third purchase onward is $84.99, and the first two are $74.99. A farm's next eval is the repeat price. The list price is in the sensitivity. No activation fee.
- MyFundedFutures Rapid EOD: $135 → $-60, $157 → $-82. The help article does not print the price. The firm's own blog says $135 in one paragraph and $157 in another. The rank uses $157, the higher figure. $135 is in the sensitivity.

## Do the sims charge commission?

Yes on the four firms that print a rate. The path still uses one cost model for every firm. Case (b) is TopstepX's MNQ $1.22 round turn plus one tick each side, which is what the rest of this file has been using. It is not each firm's own card. One tick each side on MNQ is $1.00 a round turn (0.50 points at $2 a point). A full-size stop is 16 points, $32 of risk per contract, so the cost is that many dollars times the contracts needed to risk the max-loss line.

- **Topstep.** [TopstepX commissions](https://help.topstep.com/en/articles/8284213-topstepx-commissions-and-fees), 30 Sep 2026: "These fees apply when trading the Trading Combine, Express Funded Account, and Live Funded Account. Commissions and fees are automatically deducted from each trade." Micro E-mini NASDAQ 100 (MNQ) total is $1.22 round turn: exchange $0.70, NFA $0.02, commission $0.50. The live-account costs page also says the Combine charges "a $3.70/lot simulated fee" and lists NQ and ES near $3.80. That sentence is the mini, not the micro. The product table is the MNQ number.
- **LucidFlex.** [Approved products and commissions](https://support.lucidtrading.com/en/articles/11508978-approved-products-and-commissions), 26 Aug 2026. The column is "Commission (Per Side)." MNQ is 0.50, so $1.00 round turn. NQ is 1.75 per side. The article says the table is "what it costs." It does not use the words "deducted from your balance."
- **Tradeify.** [Trading commission fees](https://help.tradeify.co/en/articles/10468315-trading-commission-fees), updated in the last two weeks: "Total Round Trip Cost includes Exchange fees, NFA fees, Clearing fees, and Commissions." MNQ is $1.82 round turn. The pricing page says "All trades incur commission fees." It does not separately say the sim balance is where they come out.
- **MyFundedFutures.** [Futures instrument list](https://help.myfundedfutures.com/en/articles/9735811-futures-instrument-list), 24 Aug 2026, column "Total Cost Round Trip." MNQ is 0.25 tick, $0.50 tick value, **$1.90** round trip. NQ is **$4.68**. The [live account page](https://help.myfundedfutures.com/en/articles/10101257-understanding-live-funded-account-at-myfunded-futures) says "Round-Trip Commissions and Fees" "will be deducted directly from your Live Funded Account balance." The evaluation articles do not repeat that sentence. The instrument list is the schedule for the products the sim trades.
- **FundedNext Flex.** [How commissions work](https://helpfutures.fundednext.com/en/articles/14298151-how-do-commissions-work-in-futures-trading), 22 Aug 2026: the all-in rate "includes broker commissions, exchange and NFA fees, and clearing fees," and "the commission and fees are charged twice, once for opening and once for closing." The only number on the page is an NQ example, $2.88 per side, $5.76 round turn, described as NinjaTrader's rate. The page does not print an MNQ figure.

Same book as the table above, stated breach, 2,500 paths, its own sample. The commission-plus-slippage point will not match the earlier row to the dollar. Compare the intervals. Slippage only drops the $1.22 and keeps the tick. Zero cost drops both.

| firm | cost | symmetric EV | symmetric payouts / 100 | recipe EV | recipe payouts / 100 |
|---|---|---|---:|---|---:|
| LucidFlex | slippage only | $19 ($-0 to $38) | 12.6 | $39 ($12 to $65) | 8.7 |
| LucidFlex | commission plus slippage | $4 ($-14 to $23) | 11.8 | $21 ($-4 to $46) | 7.6 |
| LucidFlex | zero cost | $18 ($-2 to $39) | 12.2 | $50 ($23 to $77) | 9.4 |
| Topstep | slippage only | $17 ($7 to $27) | 11.2 | $81 ($61 to $101) | 10.5 |
| Topstep | commission plus slippage | $2 ($-7 to $12) | 9.8 | $87 ($65 to $109) | 10.8 |
| Topstep | zero cost | $19 ($8 to $30) | 11.0 | $83 ($64 to $102) | 10.5 |
| Tradeify Select Flex | slippage only | $-113 ($-122 to $-105) | 5.5 | $45 ($5 to $85) | 9.9 |
| Tradeify Select Flex | commission plus slippage | $-117 ($-125 to $-109) | 5.3 | $-16 ($-50 to $18) | 7.1 |
| Tradeify Select Flex | zero cost | $-116 ($-124 to $-107) | 5.0 | $26 ($-11 to $63) | 9.0 |
| MyFundedFutures Rapid EOD | slippage only | $-157 ($-157 to $-157) | 0.0 | $-87 ($-101 to $-74) | 3.9 |
| MyFundedFutures Rapid EOD | commission plus slippage | $-157 ($-157 to $-157) | 0.0 | $-82 ($-96 to $-68) | 4.2 |
| MyFundedFutures Rapid EOD | zero cost | $-157 ($-157 to $-157) | 0.0 | $-94 ($-107 to $-81) | 3.5 |
| FundedNext Futures Flex | slippage only | $10 ($-5 to $25) | 12.4 | $31 ($10 to $52) | 10.4 |
| FundedNext Futures Flex | commission plus slippage | $6 ($-9 to $21) | 12.5 | $10 ($-9 to $28) | 8.4 |
| FundedNext Futures Flex | zero cost | $11 ($-5 to $27) | 12.0 | $20 ($0 to $40) | 9.4 |

## A month at the cap

Each firm is run at its published funded cap. The month is the symmetric coin, so a winning day pays the same dollars as the stop. Tradeify's rule says the bot may not be used at another firm, so the combined book is also shown without Tradeify.

| firm | funded cap | mean month | 95% CI | P(month negative) |
|---|---:|---:|---|---:|
| Topstep | 5 | $90 | $16 to $165 | 45.0% |
| LucidFlex | 5 | $-81 | $-213 to $50 | 68.2% |
| FundedNext Futures Flex | 5 | $41 | $-78 to $159 | 63.5% |
| Tradeify Select Flex | 5 | $-1,216 | $-1,277 to $-1,155 | 94.2% |
| MyFundedFutures Rapid EOD | 3 | $-942 | $-942 to $-942 | 100.0% |

All five firms, coin, each at its cap: mean $-2,109 ($-2,321 to $-1,897), P(month negative) 84.5%, 10th percentile $-4,560.

Combined book without Tradeify: mean $-893 ($-1,090 to $-696), P(month negative) 72.0%, 10th percentile $-3,055.

## Rank

Ranked by the symmetric coin, at the breach the firm states. The recipe column above is a 50% hit on a larger target than the stop. That is a different question. The opening range does not get to overrule either number.

1. **Topstep.** Symmetric coin $5 ($-4 to $14) per eval. Recipe, 50% on the larger day, $107 ($83 to $132). Stated grade: intraday.
2. **LucidFlex.** Symmetric coin $2 ($-16 to $20) per eval. Recipe, 50% on the larger day, $42 ($16 to $69). Stated grade: eod.
3. **FundedNext Futures Flex.** Symmetric coin $2 ($-13 to $16) per eval. Recipe, 50% on the larger day, $27 ($6 to $47). Stated grade: eod.
4. **Tradeify Select Flex.** Symmetric coin $-114 ($-122 to $-106) per eval. Recipe, 50% on the larger day, $10 ($-24 to $45). Stated grade: intraday.
5. **MyFundedFutures Rapid EOD.** Symmetric coin $-157 ($-157 to $-157) per eval. Recipe, 50% on the larger day, $-82 ($-96 to $-68). Stated grade: eod.

## Verdict

A symmetric 50/50 coin, after the scaled MNQ cost, is not a positive-EV purchase at any of these firms under the stated breach rule. The intervals that sit entirely below zero are Tradeify Select Flex, MyFundedFutures Rapid EOD. Where an interval covers zero, a coin has not been shown to work. The recipe, which wins a larger dollar amount than it risks and hits that outcome half the time, is above zero for Topstep, LucidFlex, FundedNext Futures Flex. That recipe is not a coin. It is a 50% chance to bank the payout-sized day. The 5-minute holdout does not supply that hit rate. Its mean R is about a tenth of an R and the confidence interval includes zero, and sized to the stop it loses the fee. Tradeify's symmetric coin is $-114 ($-122 to $-106). Their rule also forbids running the same bot at another firm, so it cannot be one leg of a shared farm. MyFundedFutures' help article does not print the Rapid EOD fee, and the firm's blog names both $135 and $157. The rank uses $157. Lucid's fee is still not on the help page. FundedNext's list price is $141.99 and the repeat price is $84.99. The rank uses the repeat price. Topstep has no cap on Combines and a hard cap of 5 XFAs, and the max-loss line is watched intraday. Take Profit Trader, Alpha Futures, and Elite Trader Funding are out because the bot is banned or needs written permission they have not given. Bulenox, Tradeify Growth, FundedNext Rapid Pro, and LucidDirect are out because the funded account still has a consistency rule. Start with the three firms whose symmetric coin is least bad and whose rules actually allow the bot. Do not start a five-firm copy of one strategy. Tradeify's exclusive-use rule forbids it, and a coin does not pay for the fees.

## Recipes for the top of the list

These are the parameters the simulator used. They are not an instruction to buy the eval.

### Topstep

- Account: 50K. Fee in the rank: $49. Activation $149.
- Eval: 2 equal days of $1,500 net, so the best day is 50.0% of the target. Consistency cap is 55.0%. A red day risks the $2,000 line.
- Funded: one day aimed at $3,400 net, then 4 days at the $150 minimum. Payout 50.0% of balance, cap $2,000, trader keeps 90.0%.
- Grade the max loss the way the page states: intraday. Stop at 5 funded accounts.
- Monthly Trading Combine subscription. A failed attempt still pays the month. There is no published cap on how many Combines you can hold. The month below starts at most 15, so it can be compared with firms that do cap evals. Only the 5 XFA limit is a Topstep rule.

### LucidFlex

- Account: 50K. Fee in the rank: unconfirmed, assumed $100. Activation $0.
- Eval: 3 equal days of $1,000 net, so the best day is 33.3% of the target. Consistency cap is 40.0%. A red day risks the $2,000 line.
- Funded: one day aimed at $3,400 net, then 4 days at the $150 minimum. Payout 50.0% of cycle, cap $2,000, trader keeps 90.0%.
- Grade the max loss the way the page states: eod. Stop at 5 funded accounts.
- Help centre describes a one-time fee and does not print it. Rank uses an assumed $100. The table also runs $80 and $150.

### FundedNext Futures Flex

- Account: 50K. Fee in the rank: $85. Activation $0.
- Eval: 3 equal days of $833 net, so the best day is 33.3% of the target. Consistency cap is 40.0%. A red day risks the $1,500 line.
- Funded: one day aimed at $2,200 net, then 4 days at the $200 minimum. Payout 50.0% of cycle, cap $1,500, trader keeps 95.0%.
- Grade the max loss the way the page states: eod. Stop at 5 funded accounts.
- List price on the Flex challenge page is $141.99. The same page says the third purchase onward is $84.99, and the first two are $74.99. A farm's next eval is the repeat price. The list price is in the sensitivity. No activation fee.

