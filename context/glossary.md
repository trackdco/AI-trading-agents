# Glossary — canonical definitions for this repo

Purpose: disambiguation, not education. These are the AUTHORITATIVE definitions of terms as used in this codebase — where industry usage varies (VWAP band math, "displacement," session anchors), this file and the strategy doc win over general convention. Also serves human collaborators new to the domain. Alphabetical.

- **BB / Bollinger Bands (20, SMA, close, 2σ):** 20-period simple moving average of close ("BB MA" / basis) ± 2 standard deviations. The basis line is a core cluster level.
- **BE / break-even:** moving a stop order to the entry price so the worst case becomes $0 on the trade.
- **Cluster / confluence cluster:** ≥2 defined price levels sitting within a tolerance of each other (see strategy doc §3). The strategy only trades where levels stack.
- **Confluence count:** how many distinct level TYPES the trigger candle interacts with. A quality score used for filters and sizing.
- **Contract roll:** futures expire quarterly; the "continuous" price series stitches contracts together. Roll dates are tagged in data, not smoothed over.
- **Data highs/lows:** the price extremes printed within N minutes of a scheduled economic release (from config/news_calendar.csv). Used as bias input and as targets.
- **Displacement:** a candle whose BODY closes through ≥2 cluster levels with body/range and close-location thresholds (doc §3). "Conviction move," numerically defined.
- **Drawdown (trailing):** on funded accounts, a max-loss line that ratchets up with the account's high-water mark. The Vault's kill-switch guards it.
- **Eval / prop firm:** a company that gives traders a funded account after they pass a simulated test with rules (profit target, trailing drawdown, daily limits). The Monte Carlo simulates these rules.
- **HTF:** higher timeframe (15m here). Classified per-moment as uptrend / downtrend / range; stored as a flag on every trade.
- **MAE / MFE:** max adverse / favorable excursion — the worst and best the trade looked between entry and exit, in R.
- **MNQ / NQ:** micro and full-size NASDAQ-100 futures. MNQ = $2/point/contract, NQ = $20/point. Tick size 0.25.
- **POC / VAH / VAL:** volume profile's Point of Control (price with most traded volume) and Value Area High/Low. POC is a core cluster level.
- **R / R-multiple:** profit measured in units of initial risk. Risk $300, make $900 → +3R. The system's universal currency; dollar P&L is derived.
- **Rejection block:** a candle that trades into a cluster, closes back on the trade side of all its levels, and leaves a wick through them. The wick (body edge → wick extreme) is the tradeable zone. THE core entry trigger.
- **Session boxes:** Asia / London / New York time windows; their highs/lows are levels.
- **Stop (stop-loss):** the resting order that exits a losing trade at the invalidation price. Placed structurally (beyond the trigger candle's wick), never widened.
- **Target / TP:** the resting order that exits a winner. Chosen from the target menu via the selection tree (doc §6), front-run by F points so fills aren't missed by a tick.
- **VWAP (+ deviation bands):** volume-weighted average price since an anchor time, with bands at ±1/2/3 volume-weighted standard deviations. TWO instances: daily (anchors 18:00 ET) and NY session (anchors 09:30 ET, doesn't exist before that).
- **Window (W1/W2...):** the time-of-day range during which new entries are allowed. A config axis under test.
