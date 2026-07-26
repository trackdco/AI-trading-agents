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
