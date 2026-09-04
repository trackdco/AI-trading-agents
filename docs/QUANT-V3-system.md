# Quant series, video 3: the trading system (NQ)

Puts the model and strategy into a streaming system: prices tick in, features are built live,
the model forecasts, the strategy emits orders, a mock exchange fills them.
Code: `src/quant/trading_system.py`, `scripts/quant_v3_system.py`, tests in `tests/test_quant_trading_system.py`.
Run: `python -m scripts.quant_v3_system` (needs `output/quant_v2/model_weights_12h_3lag.pt` from video 2).

## Building blocks

| Block | What it does |
|---|---|
| `Tick` | generic "handle one new value" interface |
| `DequeWindow` / `ArrayWindow` | fixed-size sliding window. Deque: 2M ticks in 0.31s. Array: 1.45s (every push shifts the buffer). |
| `LogReturn` | two-price window to log(p_t / p_t-1) |
| `LogReturnLags` | prices to the model's feature tensor `[lag_1, lag_2, lag_3]`, most recent first, zero-copy from numpy |
| `Order`, `Trade`, `Position` | Decimal money, signed quantity (+ long, - short), `point_value` for futures ($20 NQ, $2 MNQ) |
| `Account`, `Exchange` | abstract; the strategy only ever sees `Account`, so it cannot place orders itself |
| `TestExchange` | mock fills at the given price, tracks average entry, realised P&L, flips, fees |
| `Strategy` / `AutoRegressiveStrategy` | per bar: close the old position, open the new one, sized from the live balance times a scale factor (leverage). Optional rounding to whole contracts. |

## Parity check (not in the video)

Replayed the live pipeline over the video-2 test window, 502 bars of NQ 12h, $10k, 1x, taker fees.

| | Backtest (video 2 code) | Live replay (video 3 code) |
|---|---|---|
| direction chosen | | identical on 501/501 comparable bars |
| final equity, gross | $13,027 | $13,025 (-0.02%) |
| final equity, net of fees | $12,841 | $12,861 (+0.16%) |

The net gap is fee pricing: the backtest charges fees off the bar open, the live loop off the fill.
So the research code and the streaming code agree. Whatever the backtest says, the live loop would have done.

## Things the video left out that matter for NQ

- **Whole contracts.** The video trades fractional units. NQ trades in whole contracts, so
  `quantity_step=1` rounds down, and a $10k account gets zero NQ contracts at 1x. Use MNQ or leverage.
- **Warm-up.** The strategy needs `num_lags + 1` prices before its first order. The replay pre-feeds
  the bars before the window, as the video recommends for production.
- **No real exchange adapter.** Same choice as the video. The `Exchange` interface is where a
  Rithmic / Sierra / broker adapter would plug in.
- **The model is still the weak part.** See video 1 and 2 notes: it is buy-and-hold with 7 shorts.
  The plumbing is now proven; the next real work is features with information in them.
