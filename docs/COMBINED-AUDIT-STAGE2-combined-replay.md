# Combined audit — Stage 2: chronological combined replay, one shared $800 budget

**Fit only. Sealed 2023/24 never loaded.**

Budget rule (NY's existing in-flight-inclusive form): a trade is taken only if `realized losses + in-flight risk + new risk <= $800`. Chronological within each day; no ordering uses information from later in the day.

NY sized on the lucid ladder (base $300: 0.25=$75, 0.5=$150, 0.75=$225, 1.0=$300, 1.5=$450, 2.25 capped at $600). P&L = R x risk_$ because dollar-risk sizing is stop-width-normalised.

**NY alone at the ladder: $+52,143** (264 trades). This is the number every combined figure is measured against.

## London at 1 lot

| priority | NY blocked | LON blocked | combined net | vs NY-alone | worst day | maxDD |
|---|---|---|---|---|---|---|
| NY-first | 1 | 18 | $+71,368 | **$+19,225** | $-763 | $1,882 |
| London-first | 22 | 0 | $+57,916 | **$+5,773** | $-810 | $2,568 |
| higher-conviction-first | 12 | 6 | $+71,988 | **$+19,845** | $-735 | $2,035 |

## London at the lucid ladder

| priority | NY blocked | LON blocked | combined net | vs NY-alone | worst day | maxDD |
|---|---|---|---|---|---|---|
| NY-first | 1 | 17 | $+78,445 | **$+26,302** | $-769 | $2,056 |
| London-first | 16 | 1 | $+71,697 | **$+19,554** | $-769 | $2,056 |
| higher-conviction-first | 8 | 4 | $+82,225 | **$+30,082** | $-785 | $2,056 |

**"vs NY-alone" is London's real contribution** — combined net minus the $+52,143 NY makes by itself under the same budget. A positive figure means London adds money after paying for every NY trade it displaced.
