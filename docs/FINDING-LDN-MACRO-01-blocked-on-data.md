# FINDING — LDN-MACRO-01 (eu-macro-windows): **BLOCKED ON DATA ACQUISITION**

**Drafted for Brake's signature.** Routes to Angus.
Reproduce: `python -m scripts.ldn_remaining_feasibility` (section 2).

**Not a verdict.** No outcome was measured, no trial recorded, ledger unchanged. This is a
determination that the candidate cannot be tested *in this container* for want of an input,
and a statement of exactly what would unblock it.

---

## The finding

The candidate needs European scheduled releases: *"German prints and UK data around 02:00
ET, flash PMIs 03:15–04:00 ET, Eurozone aggregates around 05:00 ET."*

We hold **no European release calendar.** What we hold is `config/news_calendar.csv` and
`config/news_calendar_hist.csv` — 765 rows spanning 2023-01 → 2026-07, and they are
**entirely US red-folder**: ISM, Non-Farm Payrolls, CPI, Retail Sales, PCE, FOMC,
Unemployment Claims.

The release times settle it. Converted to London clock:

| London time | releases | what it is |
|---|---|---|
| 13:30 | 401 | 08:30 ET — US data |
| 15:00 | 131 | 10:00 ET — US data |
| 12:30 | 42 | 07:30 ET — US data |
| **08:00–10:00** | **0** | **our window** |

**Zero of 765 calendar entries land inside the London session.** The nine "Flash PMI" rows
are S&P Global *US* flash PMIs, not European ones — the London-clock distribution confirms
it.

The window arithmetic itself is fine: the thesis's own clock times were checked against
`london_window_et()`, and flash PMIs at 08:15 and 09:00 London do fall inside the session on
all 396 days. There is simply no data saying *which days* those releases occurred.

## Why I did not reconstruct one

Two routes were available and both are wrong:

1. **Scrape Forex Factory.** `scripts/news_daily_agent.py` documents why this cannot happen
   here: *"Cloudflare blocks datacenter IPs — this container cannot run it."* That is a
   pre-existing, documented constraint, not a new discovery.
2. **Infer releases from the tape** — find recurring clock minutes with volatility spikes
   and call them releases. **This is circular** and would repeat the LDN-SWP-01 defect: the
   event would be defined by a property of the very window whose outcome is being measured.
   A "release" identified because the tape moved, then used to predict that the tape moves,
   proves nothing.

Fabricating release dates from general knowledge of when flash PMIs usually land (around
the 22nd–24th) would be inventing data. It is not an option.

## What unblocks it — concretely

The transport already exists and is already in use for the news sentinel:

1. Run the FF scrape on a machine Forex Factory allows — Brake's or Angus's box, not this
   container (`scripts/scrape_ff_calendar.py`, `scripts/extract_news_calendar.py`).
2. Filter to **EUR and GBP** currencies, high impact, 2025-01 → 2026-07.
3. Commit as `config/news_calendar_eu.csv` with the same `datetime_ET,event,impact` schema
   the existing files use, and push.

Once that file exists this candidate is immediately testable and the feasibility count can
be re-run without further build work.

## Worth noting for the programme

The thesis argues this candidate pays even on a null: *"clean event dummies upgrade every
other London candidate."* That is correct, and it is now the **main** reason to get the
calendar rather than a side benefit — every London candidate tested so far has been run
**without any news conditioning at all**. Whether the nulls we have found are partly news
contamination is currently unknown and unknowable.

It is also the only remaining candidate whose NY-canon input-family overlap is rated **LOW**
(news/time is a genuinely new input family), which the portfolio diversity criterion wants.

**Recommendation to Angus: this is the cheapest high-value unblock on the board.** It needs
one scrape on a permitted machine and a committed CSV — no modelling, no build.

## Programme state

**8 of 9 candidates resolved or determined.** London trial ledger: **24**, unchanged by this
finding. No holdout looks spent.
