# Handoff brief — Star Trading corpus analysis

Everything another chat needs to process the full 117-video corpus and come back with
something usable. Self-contained on purpose: it restates the constraints rather than
pointing at repo files, so it works in a chat with no access to this repository.

**How to use it.** Get the transcripts first (§6), then paste §1 into the new chat as its
opening message, attach transcripts in batches, and have it emit the §2 record for each
video. §3–§5 are the reference material that keeps the analysis honest; paste them in
alongside §1 if the chat has room, or feed them when it starts drawing conclusions.

---

## 1. The primer — paste this first

> You are acting as an expert quantitative developer and systematic futures trader. I am
> going to feed you transcripts from a YouTube trading channel (Star Trading / @StarTrading-n8t,
> a trader called Erik). There are 117 videos, ~45 hours. The channel teaches one idea:
> **negative risk-to-reward** — targets smaller than the stop, roughly 0.5R, carried by a
> claimed 90–95% win rate.
>
> **My goal.** I run a mechanical NQ futures system. I want to know whether there is a real,
> mechanisable edge in this material, and if so what exactly the rules are. I do not want a
> summary of his marketing. I want the rule set extracted, the claims tested against
> arithmetic, and the discretionary gaps named.
>
> **Critical context about my system, which constrains what is useful to me:**
> - I trade **NQ futures**, not EUR/USD spot. He is forex-first. Translation is not free —
>   tick size, commission and noise all differ.
> - My strategy document is **locked** and carries a **1.5R minimum target floor**. A 0.5R
>   model is the direct inverse of my current rules. So I am not looking for something to
>   adopt — I am looking for a clearly-stated hypothesis I could take through a formal
>   approval and out-of-sample testing gate.
> - My risk layer halts the day after 2 losses or −2R, with a 3-trade daily cap. At 0.5R
>   those two halt conditions collapse into one event and a 2-loss day is mathematically
>   unrecoverable. Any low-RR proposal has to address this.
> - Everything must end up **fully mechanical** — no "use your judgement", no "you'll feel
>   it". Where he is being discretionary, I need that flagged, not smoothed over.
>
> **How to treat the source.** He is selling a program, a journal product and a Discord. Win
> rates and account figures are marketing until corroborated. Extract mechanics faithfully;
> treat every performance claim as an unverified assertion and say so. If two videos
> contradict each other, surface the contradiction rather than picking one.
>
> **What I want back**, in this order:
> 1. A single consolidated rule set — the strategy as precisely as it can be stated, with
>    every parameter he gives a number for.
> 2. A list of the places the rules are ambiguous or discretionary, ranked by how much they
>    would change results.
> 3. Every performance claim, with its stated sample size and what was excluded from it.
> 4. Contradictions between videos.
> 5. Your verdict on whether a testable hypothesis exists here, stated in one paragraph I
>    could hand to a strategy owner for sign-off.
>
> Acknowledge, and I will start sending transcripts.

---

## 2. Extraction schema — one record per video

Ask the chat to emit this for each transcript, then consolidate at the end. Keeping it
structured is what makes 117 videos aggregate instead of blur.

```yaml
video_id:
title:
date:
type: method | backtest | live-recap | psychology | prop-firm | promo
rules_stated:        # only rules given explicitly, verbatim intent preserved
  - rule:
    parameter:       # any number he attaches to it
    conditional:     # when it applies / when it doesn't
claims:
  - claim:           # e.g. "95% win rate"
    sample_size:     # trades / days / weeks, or "none given"
    period:
    instrument:
    costs_included:  # yes | no | not stated  <-- the single most important field
    verifiable:      # is there anything auditable, or is it an assertion
discretion:          # points where he defers to intuition, feel, or "you'll know"
contradictions:      # anything conflicting with an earlier video
new_vs_known:        # does this add to the rule set or restate it
```

The `costs_included` field is the one that decides everything. In the transcript already
captured he states plainly that spread and commissions are excluded. If that holds across
the corpus, every headline number on the channel is a gross figure, and §4 shows what that
does to them.

---

## 3. What is already established

From the one full transcript captured before the block —
[The LAST Negative RR Strategy You Will Ever Need](https://www.youtube.com/watch?v=vlKZEA0x2X4)
(2026-06-18, 19:01), a worked replay backtest on EUR/USD from 1 April in TradeLens.

**The rule set as demonstrated:**

| Element | As stated |
|---|---|
| Session anchor | The 08:00 candle — everything keys off it |
| Cut-off | Around 14:00; if no setup came early, the day is done |
| Core object | Imbalance → FVG → **BPR** (opposing FVGs overlapping into one zone) |
| Hard filter | **The BPR must form *after* the 08:00 candle.** Pre-08:00 zones are passed on, even when they would have won |
| Direction | Reversals — explicitly not continuation |
| Entry | Market order as price trades back into the BPR |
| Target | 0.5R; the worked example was a **5-pip stop against a 2-pip target** |
| Risk | 1% standard, **0.5% on an A rather than A+ setup** |
| Hold time | Most trades resolve inside 50 minutes |

**Grading.** A+ = multiple BPRs stacked, plus a liquidity sweep (relative equal highs/lows
taken), plus additional FVG confluence in the same zone. A partially-filled zone — his
"dirty BPR" — still counts at lower quality.

**Two admissions in that session matter more than the 100% weekly win rate it produced:**
costs are excluded by his own statement, and discretion is present — at one entry he says he
does not trust it on intuition but takes it because it fits the rules, and elsewhere he opens
"test positions" after the fact to check whether a passed setup would have won.

He also notes that at 4% risk per trade, a prop firm's phase one would have cleared inside
that one week.

---

## 4. The arithmetic — give this to the chat before it forms a verdict

Sub-1.0 RR is not unsound in principle. It relocates the whole edge into the win rate, where
costs bite hardest. These numbers are verified:

- **Gross break-even at 0.5R is a 66.7% win rate.** `0.5p = 1 − p → p = 2/3`. No reward
  multiple exists to rescue you below it.
- **Costs move that a very long way.** His own 5-pip stop / 2-pip target, with ~0.8 pips
  round-trip cost: a win nets 1.2, a loss costs 5.8, so break-even becomes **82.9%**.
- Therefore the real question is not "is 95% plausible" but **"is the gap between a claimed
  95% and a required 83% real, and does it survive live fills?"**

| True win rate | Net per trade | Verdict |
|---|---|---|
| 95% | +0.85 pips | Strong |
| 90% | +0.50 pips | Good |
| 85% | +0.15 pips | Marginal |
| 80% | −0.20 pips | Losing |

A cost-free backtest cannot separate the top row from the bottom one. That is the corpus's
central evidential weakness and the chat should keep returning to it.

**Slippage is structurally asymmetric and replay backtesting cannot see it.** You are a
limit-taker on a 2-pip profit and a stop-taker on a 5-pip loss. Stops slip against you;
targets never slip in your favour. Half a pip of stop slippage is 10% of the risk on every
loser.

**Streak risk is what kills the sizing.** At a true 90% win rate, three consecutive losses
somewhere in 100 trades runs ~8%; at a true 80% it is ~47%. Three losses at his suggested 4%
is a 12% drawdown — past the max drawdown at essentially every prop firm, and worse on a
trailing drawdown that ratchets up behind each equity high.

**On NQ the picture is slightly worse than forex.** A 2-tick target ($10) against a 5-tick
stop ($25) at ~$4.50 round-turn commission gives a break-even win rate of **84%**.

**A contradiction worth resolving.** At 95%, ten consecutive losses is a `0.05¹⁰` event —
about one in ten trillion. Yet one video is titled *You Will Lose 10 Times in a Row (And I
Can Prove it)*. Ten-in-a-row is only a realistic warning near a 50% win rate. Either the
title is clickbait or the working win rate is far below the headline.

---

## 5. Open questions, ranked

The chat should treat these as its actual job. In rough order of how much each would change
the verdict:

1. **Does he ever state results net of spread and commission?** If never, every number on
   the channel is gross and the corpus cannot support its own headline claims.
2. **What is the real win rate on the largest sample he shows?** The 1000-trade videos and
   the 7.5-hour 30-day "full movie" are the places to look. Get the denominator.
3. **How are break-evens counted?** *Why 90% of My Trades Break Even* suggests break-even
   exits are common. If those are excluded from the denominator, a "95% win rate" may be
   95% of a much smaller set of resolved trades. This alone could explain the entire gap
   between his claims and the arithmetic.
4. **What is the exact BPR definition?** Tick tolerances, how much fill makes a zone "dirty"
   and still valid, minimum size, how many can stack. This is the difference between a
   mechanisable rule and a vibe.
5. **What is the stop rule, precisely?** The 5-pip stop in the captured video looked fixed
   rather than structural. Fixed-distance and beyond-the-zone are very different strategies.
6. **Is the 08:00 anchor a fixed clock time or a session open?** And in which timezone —
   this determines whether it maps to anything on NQ at all.
7. **What is the actual drawdown history?** Worst streak, worst day, worst month. He must
   have it; the question is whether he shows it.
8. **Does the model change over time?** He says "my new model" in the June 2026 video.
   Chronology matters — later videos may supersede earlier ones rather than corroborate them.

---

## 6. The corpus and how to work through it

**Getting the transcripts.** Run from a home connection — cloud IPs get blocked by
YouTube's bot check, which is what stopped this session's pull:

```bash
cd research/star-trading
./tools/pull_channel.sh captions
python3 tools/vtt_to_text.py captions transcripts
```

Add `YTDLP_EXTRA="--cookies-from-browser chrome"` if the bot check fires anyway. Requires
`yt-dlp` (`pipx install yt-dlp` or `brew install yt-dlp`).

**Tier 1 — 20 videos, ~18h 45m. Process these first; they should yield ~90% of the rule set.**
The masterclasses state rules explicitly, the backtests carry the samples, and the streak and
break-even videos hold the arithmetic that decides everything.

| Video | Length |
|---|---|
| [After 30 Days I Doubled My Money With Negative RR (Full Movie)](https://www.youtube.com/watch?v=O5NBF8Jg5vU) | 7:32:16 |
| [I Quadrupled The Account With Negative RR](https://www.youtube.com/watch?v=UX-7OcxqdZw) | 1:38:55 |
| [The Ultimate Negative RR Masterclass — Full 2026 Blueprint](https://www.youtube.com/watch?v=DvlS4m3qNV0) | 1:24:23 |
| [Full Negative Risk to Reward Masterclass](https://www.youtube.com/watch?v=2fj3r7jgsA4) | 1:18:54 |
| [You're Unprofitable Because You're Trading When You Shouldn't](https://www.youtube.com/watch?v=n6tdQXCM52Y) | 58:45 |
| [The Full Breakdown On How I Win 20 Times in a Row](https://www.youtube.com/watch?v=GRgI67UwkHY) | 34:48 |
| [I Backtested My ICT Scalping Model Live (86% Winrate)](https://www.youtube.com/watch?v=xbh3qNNgRWE) | 33:59 |
| [Backtesting The Negative RR Strategy That Got Me Interviewed by FundingPips](https://www.youtube.com/watch?v=d2PHNIV6rmA) | 31:12 |
| [6 Years of Multi Timeframe Price Action Mastery in 30 Minutes](https://www.youtube.com/watch?v=mAyb9k-fsWw) | 27:49 |
| [Steal This Scalping Strategy to Get Funded FAST (1000 Trades Backtested)](https://www.youtube.com/watch?v=wj_ySYkAR1I) | 25:32 |
| [The Checklist That Guarantees a 90% Win Rate](https://www.youtube.com/watch?v=ReDMfMM9bKQ) | 25:24 |
| [Full Liquidity Masterclass For Negative RR Traders](https://www.youtube.com/watch?v=QC7m_0eZCAc) | 25:20 |
| [Backtesting My Negative RR Strategy to Proof You Wrong](https://www.youtube.com/watch?v=MgcxuVd6jx0) | 23:44 |
| [Negative Risk to Reward Strategy Backtest (95% Winrate)](https://www.youtube.com/watch?v=oHZCMvO0JlA) | 21:50 |
| [My Take Loss Stop Profit Strategy Has a 95% Win Rate](https://www.youtube.com/watch?v=J8LCSx5mrYI) | 21:07 |
| [Why 90% of My Trades Break Even (And I Still Profit)](https://www.youtube.com/watch?v=n5TBiz17eA4) | 20:49 |
| [The LAST Negative RR Strategy You Will Ever Need](https://www.youtube.com/watch?v=vlKZEA0x2X4) | 19:01 | ✅ already extracted |
| [You Will Lose 10 Times in a Row (And I Can Prove it)](https://www.youtube.com/watch?v=JF43fif_cPg) | 18:41 |
| [The Easiest Forex Strategy Known To Man (1000 Trades Backtested)](https://www.youtube.com/watch?v=c6WUKYFo0hI) | 14:21 |
| [What 1000 Backtested Trades Reveal About My Negative RR Strategy](https://www.youtube.com/watch?v=9JGlNWEdOnk) | 7:05 |

**Tier 2 — the remaining 97 videos, ~25h 54m.** Full list with links, lengths and view counts
in [`channel-index.md`](channel-index.md). Mostly restatement, live recaps and psychology.
Worth a fast pass for contradictions and stray parameters rather than a close read — and the
live recaps are the only place an unedited losing streak might show up.

**Batching.** Feed Tier 1 in groups of 3–4 transcripts, asking for the §2 record on each and
nothing else, then request the consolidated rule set once Tier 1 is done. Asking for
synthesis too early produces confident summaries of an incomplete rule set.

---

## 7. What a good answer looks like

The deliverable that would actually be worth something back here:

- **A rule set precise enough to code**, with every ambiguity flagged as an open decision
  rather than quietly resolved.
- **A claims table** with sample sizes and cost treatment, so the evidence can be weighed
  instead of believed.
- **A single-paragraph hypothesis** suitable for a formal sign-off gate — or an honest
  finding that no testable hypothesis survived contact with the arithmetic. That second
  outcome is a perfectly good result and should not be talked around.

Worth keeping in view throughout: the underlying question — *does low RR work on NQ* — is
answerable from our own data without believing anything from this channel. Take the existing
detector's entries unchanged, vary only the target multiple across 0.5R / 1.0R / 1.5R / 2.0R,
model costs punitively, and report the required break-even win rate beside every bucket. The
corpus is worth mining for the *ideas* it might contribute — the post-08:00 formation filter
is a genuinely novel, cleanly mechanical qualifier that our rules do not currently have — but
not for its evidence.
