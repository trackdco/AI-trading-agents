# VIX daily index (regime feature)

`vix_daily.csv` — daily closing values of the **CBOE Volatility Index (^VIX)**, the
"fear gauge." This is the *index*, not VIX futures.

## File
- `vix_daily.csv` — columns `date` (YYYY-MM-DD), `vix` (index close).
- 9,231 trading days, **1990-01-02 → 2026-07-16**.
- Market-holiday blanks removed (302 dropped).

## Source
FRED series `VIXCLS` (St. Louis Fed), free, public:
`https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS`

## Sanity
- Range 9.14 – 82.69, mean 19.44 (matches history: sub-10 low-vol regimes; 80+ during
  the 2008 and 2020 crashes).
- Feb–Jul 2026 window: 118 days, VIX 15.03 – 31.05 (a stress spike to ~31 inside the
  champion span).

## Intended use
Daily volatility-regime feature — classify each session as low/normal/elevated/high
vol (e.g. via rolling percentile) to gate or contextualize signals. Daily granularity
only (one value per session); it does not resolve intraday.
