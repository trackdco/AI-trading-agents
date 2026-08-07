# The negative-RR model, as stated on the channel

Reconstructed from the one full transcript captured before YouTube blocked the pull:
**"The LAST Negative RR Strategy You Will Ever Need"** (2026-06-18, 19:01,
[vlKZEA0x2X4](https://www.youtube.com/watch?v=vlKZEA0x2X4)) — a screen-recorded replay
backtest on EUR/USD from 1 April, run in TradeLens.

This is research input only. Nothing here is a proposal to change
`strategy-definition-v1.0.md`; see [Fit against our constitution](#fit-against-our-constitution)
for why one part of it directly contradicts the locked rules.

---

## 1. The rule set as demonstrated

| Element | As stated |
|---|---|
| Market | EUR/USD spot (the channel is forex-first, not futures) |
| Session anchor | The 08:00 candle. Everything keys off it |
| Cut-off | Stop looking at charts around 14:00; if no setup came in the first few hours, the day is done |
| Core object | Imbalance → FVG → **BPR** (opposing FVGs overlapping into one zone) |
| Hard filter | **The BPR must be formed *after* the 08:00 candle.** A pre-08:00 BPR is explicitly passed on, even when it would have won |
| Directional bias | Reversals, not continuations — explicitly *not* trend-following |
| Entry | Market order as price trades back into the BPR |
| Target | 0.5R. The worked example was a **5-pip stop against a 2-pip target** (0.4R in practice) |
| Risk | 1% standard; **0.5% on a merely-A setup** rather than A+ |
| Hold time | Most trades resolve inside 50 minutes |

**Setup grading.** A+ requires stacking: multiple BPRs layered on each other, a liquidity
sweep (relative equal highs/lows taken out) and additional FVG confluence in the same zone.
More overlapping imbalances is read as higher probability of a return to the zone. A "dirty
BPR" — partially filled, some unfilled residue left — still counts, at lower quality.

**The discipline claim.** Much of the video is spent *declining* setups that then went on to
win, on the grounds that they failed the post-08:00 rule. That is the pitch: the rules
matter more than any single outcome.

---

## 2. What the video actually demonstrates

One week of EUR/USD replay, roughly seven trades, ending at a **100% win rate** — which he
flags himself as unrepresentative: keep it realistic, it will not stay at 100%.

Two admissions in that same session matter more than the result:

- **Costs are excluded.** Stated up front: spread and commissions are not in the backtest,
  they get subtracted afterwards. On a 2-pip target that is not a rounding detail — see §3.
- **Discretion is present.** At one entry he says he is not trusting it *out of intuition*
  but takes it because it fits the rules; elsewhere he opens "test positions" after the fact
  to check whether a passed setup would have won. Both are the signature of a
  discretionary method wearing a mechanical costume.

He closes by noting that at 4% risk per trade, a prop firm's phase one would have been
passed inside that single week.

---

## 3. The arithmetic, which is where this lives or dies

Sub-1.0 RR is not inherently unsound — it just relocates the entire edge into the win rate,
where it becomes acutely sensitive to costs. The numbers:

**Gross break-even at 0.5R is a 66.7% win rate.** `0.5p = 1 − p → p = 2/3`. Above it you
make money, below it you do not, and there is no reward multiple to bail you out.

**Costs move that number a very long way.** Take his own 5-pip stop / 2-pip target on a raw
spread account: ~0.1 pip spread plus commission ≈ 0.8 pips round trip. A win nets 1.2 pips,
a loss costs 5.8. Break-even becomes `p = 5.8 / 7.0 = **82.9%**`.

So the honest question is not "is 95% plausible?" but "**is the gap between the claimed 95%
and a realistic 83% real, and does it survive live fills?**" Everything rests there:

| True win rate | Net per trade (5/2 pips, 0.8 cost) | Verdict |
|---|---|---|
| 95% | +0.85 pips | Strong |
| 90% | +0.50 pips | Good |
| 85% | +0.15 pips | Marginal |
| 80% | −0.20 pips | Losing |

A backtest that omits costs cannot distinguish the top row from the bottom one. That is the
single most important thing about this channel's evidence base.

**Slippage is structurally asymmetric here** and replay backtesting cannot see it. You are a
limit-taker on the 2-pip profit and a stop-taker on the 5-pip loss. Stops slip against you;
targets never slip in your favour. Half a pip of stop slippage is 10% of the risk on every
loser.

**The 4% sizing suggestion is the dangerous part.** Losing streaks are ordinary even at high
win rates. At a true 90%, the chance of three consecutive losses somewhere in 100 trades is
about 8%; at a true 80% it is roughly 47%. Three losses at 4% is a 12% drawdown, past the
max drawdown of essentially every prop firm. On a trailing drawdown that is worse again,
because the threshold ratchets up behind every new equity high. Sizing that passes phase one
in a week is the same sizing that ends the account in an afternoon.

**One inconsistency worth resolving from the fuller transcripts.** A 95% win rate makes ten
consecutive losses a `0.05¹⁰` event — about one in ten trillion, i.e. never. Yet
[one video](https://www.youtube.com/watch?v=JF43fif_cPg) is titled *You Will Lose 10 Times in
a Row (And I Can Prove it)*. Ten-in-a-row is only a realistic warning around a ~50% win
rate. Either the title is pure clickbait or the working win rate is far below the headline.
That video and *Why 90% of My Trades Break Even* are the two to read first — break-even
management would also reshuffle the arithmetic above, since a break-even exit is neither a
win nor a full loss and quietly inflates any quoted "win rate".

---

## 4. Fit against our constitution

**Direct conflict.** `strategy-definition-v1.0.md` §6.5 sets an **RR floor: skip when the
nearest valid target is under 1.5R**. A 0.5R model is the precise inverse of that rule. It
cannot be adopted, prototyped into the engine, or slipped in as a tournament variant without
the full gate: written hypothesis → Angus approval → out-of-sample test → version bump.
Flagging it here is the whole of what this document does.

**Structural incompatibility with the Vault, if it ever were proposed.** §10 halts the day
after 2 losses or −2R. At 0.5R those are the same event — two losses *is* −2R — and with a
3-trade daily cap you would need four wins to recover a 2-loss day, which the cap makes
impossible. A low-RR strategy and the current Vault limits cannot both be right; adopting one
would require redesigning the other.

**Instrument translation is not free.** This is EUR/USD spot; we trade NQ. The same
arithmetic on NQ with a 2-tick target ($10) against a 5-tick stop ($25), at ~$4.50 round-turn
commission, gives a break-even win rate of `29.5 / 35 = 84%`. The cost drag is, if anything,
slightly worse than the forex case, and NQ's tick-by-tick noise at that scale is severe.

**What is genuinely portable**, independent of the RR question:

- The post-08:00 formation filter is a clean, fully mechanical time-of-formation rule. Our
  §2 data-levels and session-box machinery could express something equivalent, and the idea
  that a level's *formation time* qualifies it — not just its price — is not currently
  anywhere in our rule set.
- Confluence-by-stacking (more overlapping imbalances = higher grade) is the same shape as
  our §3 confluence count and §9 conviction sizing. Convergent design from an independent
  source is mild evidence the idea is sound.
- Risk-tiering by setup grade (1% vs 0.5%) mirrors our full-unit / half-unit split in §9.

---

## 5. If we ever want to test the RR question properly

Not a proposal — the shape a hypothesis would need if Angus ever wanted one. The honest
version of "does low RR work on NQ" is answerable from data we already have, and does not
require believing anything from this channel:

1. Take the existing detector's entries unchanged. Vary only the target multiple across
   0.5R / 1.0R / 1.5R / 2.0R+ and plot realised expectancy per slice.
2. Model costs punitively — commission plus a full tick of adverse stop slippage — because
   that is exactly the term this channel's evidence omits, and at low RR it dominates.
3. Report the *break-even win rate* alongside every RR bucket, so the required accuracy is
   visible rather than implied.
4. Run the winner through Monte Carlo against the 50K eval's trailing-DD rules before
   anyone forms an opinion. Path dependence, not expectancy, is what kills low-RR sizing.

That test costs little and would settle the question with our own data on our own
instrument, which is worth considerably more than 44 hours of someone else's screen recordings.
