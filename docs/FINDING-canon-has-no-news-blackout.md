# FINDING — the news blackout exists in the CHAMPION, not in the CANON

**STATUS: OPEN — a rulebook call for Angus/Pat, not an engineering fix.**
Raised by Angus, 2026-07-26: *"we need an agent in our system that is up to date on news events,
for example i dont want the agent to be entering a trade 2 minutes before CPI. forex factory red
folder news was backlogged since 2023 for all of our tests so it knew this but i dont know if the
agents will."*

**The backfill is real and the rule is real — but they are wired into the champion engine, and
the canon never sees either.** The +$52,522.81 arming book was scored news-blind.

---

## 1. Where the rule actually lives

`src/backtest/engine.py:846` — the champion path:

```python
# ANGUS 2026-07-17 (TIGHTENED): on a high-impact pre-open release day the ENTIRE
# pre-market is blocked -> no entries until 09:30
if cfg.no_premarket_high_impact and tod < dtime(9, 30):
    rel = preopen_news.get(ts.date())
    if rel is not None:
        veto(t, "vetoed_news_preopen", ...)
```

plus news-aware slippage (`slippage_ticks_news: 4` within `news_slippage_window_min: 15`) and the
§6.3 `news_day_override` target rule. Driven by `config/strategy.yaml: named_high_impact`, the
NAMED-LIST ruling from pass-9 (P5.14).

## 2. Where it does not live — the entire canon chain

`grep -c news` across every script the canon book is built from:

| stage | file | news references |
|---|---|---|
| NY candidates | `scripts/trade_angles.py` | **0** |
| NY matrix | `scripts/trade_matrix.py` | **0** |
| NY scorer | `scripts/canon_mechanical.py` | **0** |
| London candidates | `scripts/london_substrate.py` | **0** |
| London matrix | `scripts/london_matrix.py` | **0** |
| London scorer | `scripts/london_canon.py` | **0** |
| live runtime | `src/desk/canon_runtime.py` | **0** |
| live lane | `src/desk/canon_lane.py` | **0** |
| Route B feed | `src/live/route_b.py` | **0** |
| safety spine | `src/canon/spine.py` | **0** |

(The single hit in `scripts/dayflow_v2.py` is a docstring listing `red_folder_today` as a *regime
feature* — descriptive context for the regime vector, not a gate on any trade.)

The canon does not inherit the veto upstream either: its candidate set comes from
`trade_angles`/`london_substrate`, which read the bar and orderflow substrates directly. They
never pass through `engine.simulate()`, so no trade is ever vetoed for news anywhere in the chain.

**Consequence: live, the canon will place an entry two minutes before CPI, because nothing in the
path knows CPI exists.**

## 3. What it is costing, measured on the clean book

404 trades, 214 high-impact releases inside the span, distance from fill to nearest release:

| window around a red-folder release | trades | P&L | win rate | avg |
|---|---|---|---|---|
| within ±2 min | 4 (1.0%) | +$506 | 75% | +$127 |
| within ±5 min | 6 (1.5%) | +$157 | 50% | +$26 |
| within ±15 min | 12 (3.0%) | −$1,058 | 33% | −$88 |
| within ±30 min | 25 (6.2%) | −$2,080 | 28% | −$83 |
| within ±60 min | 31 (7.7%) | −$1,709 | 32% | −$55 |
| **more than 60 min away** | **373 (92.3%)** | **+$54,231** | **51%** | **+$145** |

Filled *before* a release — the case Angus named — is worse than the symmetric window:

| filled BEFORE a release by | trades | P&L | win rate |
|---|---|---|---|
| ≤5 min | 2 | −$349 | 0% |
| ≤15 min | 6 | −$977 | 17% |
| ≤30 min | 19 | −$1,998 | 21% |

Worst five in the 30-minute pre-release window:

```
2025-07-31  NY  08:13 ET   17 min before   -$335.00
2025-10-01  NY  09:46 ET   14 min before   -$231.00
2026-03-05  NY  08:25 ET    5 min before   -$227.50
2025-07-17  NY  08:01 ET   29 min before   -$220.50
2026-05-14  NY  08:01 ET   29 min before   -$216.00
```

**Read this as direction, not as a licence to fit.** 31 trades is a small sample and −$1,709 is
3% of the book; a filter tuned on it would be exactly the −2R mistake again (in-sample, flipped
sign on a substrate change). What makes this different from a discovered edge is that **the rule
already exists as an Angus ruling** — 17 July, whole-premarket blackout on named high-impact days.
This is not a new filter to justify. It is an existing one that did not get carried across.

The mechanism is also unsurprising: the canon's NY pre window is 08:00–09:30 with a **median fill
of 08:01**, and CPI/NFP/PPI all print at **08:30 ET**. The book is structurally sitting in
positions across the release.

## 4. The calendar is stale, and cannot be refreshed from here

| file | span | impact levels |
|---|---|---|
| `config/news_calendar_hist.csv` | 2023-01-04 → 2026-01-28 (529 rows) | high only |
| `config/news_calendar.csv` | 2026-02-02 → **2026-07-16** (236 rows) | high + medium + holiday |

**Today is 2026-07-26. The calendar ran out ten days ago, and it holds no future events at all.**
A blackout rule needs *forward-dated* releases; a historical backfill cannot provide them.

`scripts/scrape_ff_calendar.py` exists but its own docstring says it **cannot run in this
container** — Forex Factory's Cloudflare blocks datacenter IPs. Same doctrine as the depth
condensers: the fetch happens on Angus's or Brake's machine, the small CSV travels.

## 5. Design ruling this needs — and one thing it must NOT be

**It must not be an agent, in the trade path.** "Zero LLM/discretion in the trade path" is the
standing doctrine. A blackout is a **deterministic table lookup on a frozen calendar** — timestamp
in, veto out, byte-reproducible in backtest and live. An LLM deciding at 08:28 whether a release
counts is precisely the thing the doctrine forbids, and it would void the A3 relay guarantee.

An agent is the right tool for **maintaining** the calendar — fetching weekly, diffing against the
committed CSV, flagging schedule changes and surprise pressers, alerting when it goes stale. That
sits entirely outside the trade path and never touches a decision.

**Adding the veto changes the canon, so it needs re-validation, not a bolt-on.** If the rule goes
into the live path only, live stops matching the book and **A1/A2 fail on the first blackout day**.
It has to be re-derived in `canon_mechanical`/`london_canon`, producing a new signed-off number —
the same class of change as the `conf_PM` lookahead fix.

Open questions for Angus:

1. **Scope** — the champion's rule blocks the *entire pre-market* on a named-high-impact day. Is
   that the canon's rule too, or a tighter ±N-minute window around each release? The champion's
   version is much broader, and the canon's pre window is where most of the NY book lives.
2. **Named list vs all-high-impact** — reuse `named_high_impact` from `config/strategy.yaml`, or
   score every red folder?
3. **London** — the London book runs 03:00–08:00 ET, which contains UK/EU releases. The hist
   backfill is US-centric. Does London need its own calendar, or is it out of scope?
4. **Open positions** — block new entries only, or also flatten an open position before a release?
   The champion rule only gates entries.
5. **Fail-closed** — if the calendar is stale on the day, does the desk stand down or trade on?
   Recommendation: **stand down.** A missing calendar is a missing required context, which is
   already Tier-2 rule 5 behaviour ("missing data → skip the trade, never guess").

---

## 6. THE RULE ANGUS SPECIFIED, MEASURED (2026-07-26)

> *"If a high-conviction trade fires at 8:00 to 8:28, when it's two minutes away from NFP, I
> don't really want it to be in that trade. I'm not gonna bet on the high-impact news event
> going in favor of our trade."*

**128 of the 214 high-impact releases in the book's span print at 08:30 ET.** 135 land before
09:30, on 68 calendar days; **40 of the book's 224 trading days (18%) carry one.**

Applied to the clean book, NY-scoped:

| rule | trades blocked | book after | vs canon | win rate of what it blocked | months green |
|---|---|---|---|---|---|
| block NY entries ≤15 min before the release | 4 | $53,299 | **+$776** | **0%** | 13/13 |
| block NY entries ≤30 min before | 15 | $54,730 | **+$2,208** | **7%** | 13/13 |
| block NY entries ≤45 min before | 15 | $54,730 | +$2,208 | 7% | 13/13 |
| **block ALL NY entries before the release** | **16** | **$54,845** | **+$2,322** | **6%** | 13/13 |
| *champion rule: block whole pre-market to 09:30* | *26* | *$54,475* | *+$1,952* | *23%* | *13/13* |

**Every trade the 30-minute rule blocks:**

```
2025-06-17  08:01   29 min before 08:30   -$212.50
2025-07-17  08:01   29 min                -$220.50
2025-07-31  08:13   17 min                -$335.00
2025-08-15  08:06   24 min                -$111.00
2025-08-29  08:05   25 min                -$155.00
2025-09-26  08:13   17 min                 -$51.00
2025-11-25  08:04   26 min                -$202.50
2026-02-10  08:18   12 min                -$212.00
2026-03-05  08:25    5 min                -$227.50
2026-03-12  08:26    4 min                -$121.50
2026-03-19  08:01   29 min                +$178.00   <- the only winner
2026-03-19  08:03   27 min                 -$98.00
2026-05-14  08:01   29 min                -$216.00
2026-05-28  08:21    9 min                -$215.00
2026-06-25  08:07   23 min                  -$8.00
                                   1 winner of 15, -$2,208
```

### Three things this settles

**1. It is not a tuned window.** "Block all NY entries before the release" and "block within
30–60 min before" select **the same trades**, because the NY pre window opens at 08:00 and the
prints land at 08:30. There is no parameter to fit. The rule is simply **"do not be in a position
going into the print"** and the session structure bounds it automatically. That is the version to
adopt — the one with no free parameter.

**2. The champion's rule is too broad, and measurably worse.** Blocking the *whole* pre-market to
09:30 blocks 26 trades for **+$1,952**, against **+$2,322** for blocking only pre-release. The
difference is the **10 trades entered AFTER the print but before 09:30: +$370, 50% win.** Trading
the post-release move is fine; being in the position across it is what kills. That also matches
what Angus actually said, which was about betting on the outcome, not about the morning being bad.

**3. London needs a different calendar, not this one.** The window 03:00–08:00 ET contains
**zero** high-impact releases in our files — not because London is safe, but because the backfill
is **USD-only**. UK CPI (02:00 ET), BOE (07:00 ET) and ECB (08:15 ET) are simply not in the data.
**London is currently unprotected and we cannot even see the exposure.**

### Coverage gap: Unemployment Claims

Angus named claims as high-impact. The calendar barely has them:

| file | Unemployment Claims rows | impact tagging |
|---|---|---|
| `news_calendar_hist.csv` (2023-01→2026-01) | **0** | — |
| `news_calendar.csv` (2026-02→07) | 24 | **19 medium, 5 high** |

Claims print 08:30 ET every Thursday; **43 of the book's 224 days are Thursdays**, so ~43 days
should carry one and almost none do. **The +$2,322 above is therefore a floor** — measured against
a calendar blind to most Thursdays.

But the counter-datapoint is worth recording, because it argues against over-reacting:

| NY pre-window trades | count | P&L | win |
|---|---|---|---|
| on a Thursday (claims day) | 49 | **+$2,387** | 43% |
| every other day | 167 | +$15,989 | 40% |

**Thursday pre-window trades outperform.** So weekly claims do not look like the thing doing the
damage — the tier-1 prints do (CPI, PPI, NFP, PCE, retail sales). That is an argument for the
**named list** (question 2 in §5) rather than blacking out every red folder, and against paying
to close the claims gap first.

---

## 7. FOMC DAYS — Angus's instinct, measured (n=10, and that is the headline)

Angus, 2026-07-26: *"i dont usually trade at all on fomc days because price is comically bad."*

The book stops at **10:12 ET** and the decision prints at **14:00**, so every trade on these days
happens 4+ hours *before* the announcement — this is the pre-announcement drift, not the reaction.

| | days | total | mean/day | **median/day** | green |
|---|---|---|---|---|---|
| FOMC decision days | 10 | **+$4,897** | **+$490** | **−$99** | **4/10 (40%)** |
| every other day | 214 | +$47,625 | +$223 | +$70 | 118/214 (55%) |

**The mean and the median disagree, and the median is the honest one.** Every FOMC decision day:

```
2025-06-18   -$192      2026-03-17  +$4,318   <- carries the entire result
2025-07-30   +$381      2026-03-18    -$232
2025-09-17   -$382      2026-04-28    +$151
2025-10-29   -$114      2026-06-16  +$1,482
2025-12-10   -$430      2026-06-17     -$84
```

- drop the single best day: 9 days, **+$580**, median −$114, 3/9 green
- drop the best two: 8 days, **−$902**, 2/8 green

So the +$4,897 is **one session**. Six of ten days are red and the median day loses money, against
a +$70 median elsewhere. That is consistent with what Angus describes — chop, thin, everyone
waiting — punctuated by the occasional session where something actually breaks.

**But it is not significant and must not be traded as a finding.** Bootstrapping 10-day samples
from the other 214 days: **7.1%** beat the FOMC mean and **10.3%** have a median at least as low.
At n=10 neither tail clears anything. A filter built on this is the −2R mistake again — an
in-sample number that flipped sign the moment the substrate changed.

*Curiosity, explicitly not a claim:* both two-day meetings split the same way — day 1 the big
winner (+$4,318, +$1,482), day 2 negative (−$232, −$84). n=2 pairs. Worth watching live, worth
nothing today.

**Recommendation: do not code an FOMC filter.** If Angus wants to stand down on decision days as
a doctrinal choice — same class as "no PM session" — that is his call and entirely reasonable;
the in-sample cost is ~$4,897, which is really one lucky day. But it should be recorded as a
preference, not justified as an edge.

## 8. WHY A STATIC CALENDAR CANNOT WORK — the daily-refresh requirement

Angus, 2026-07-26: *"why we cannot have a static news forecast. something needs to check whats on
the board THAT DAY, but only take note of it, not let it actually act upon. if i were to upload
the forecasted 6 months, the actual days would be different because events shift, like cpi has
multiple times this year, and also things pop up, such as trump speaking."*

Correct, and it changes the design. Two distinct failure modes a static dump cannot cover:

1. **Scheduled events move.** A release date/time set six months out is a forecast, not a fact.
2. **Unscheduled events appear.** Pressers, emergency statements, Fed speakers added days ahead.
   These have no forward-dated row to load at all.

### The architecture that follows

**Refresh daily, freeze before the session, journal what was frozen.**

```
  pre-session job  ->  fetch today's board  ->  output/news/YYYY-MM-DD.csv  (immutable)
                                                        |
                                                        v
                              NewsGate.load(snapshot)  ->  deterministic lookup at trade time
```

The split Angus described — *"only take note of it, not let it actually act upon"* — is exactly
the right boundary, and it is also what makes the thing reproducible:

- the **fetcher** observes and records. It never decides. It may be an agent.
- the **gate** acts, on a frozen file, by table lookup. Never an agent.

**The snapshot must be frozen before the session opens and journaled with the trades.** If the
calendar can change mid-session, the same day replays differently and **A1/A2 parity is
unreproducible** — you could never prove after the fact which board the bot was looking at. Dated
immutable snapshots make a live day replayable to the byte, which is the whole point of A2.

### Open operational question — where does the fetch run?

`scripts/scrape_ff_calendar.py` cannot run in this container: Forex Factory's Cloudflare blocks
datacenter IPs. **The VPS running Sierra is also a datacenter IP**, so it will very likely be
blocked too — this needs testing on the box before anyone designs around it. If it is blocked,
the options are:

1. fetch on Angus's or Brake's machine, push the dated CSV to the repo, VPS pulls it — reliable
   but needs a human every trading day, which is a daily single point of failure;
2. an economic-calendar API that permits datacenter access (Trading Economics, Finnhub, FMP) —
   costs money, needs a name-mapping layer to our `event` strings so the promotion rule still works;
3. a scheduled job on a residential-IP box that pushes to the repo.

**Whatever the source, the fail-closed rule stands:** no fresh snapshot for today -> the desk
stands down. `NewsGate.is_stale()` exists for exactly this. A calendar that has run out cannot
clear a day, and "no news found" must never be inferred from "no data fetched."
