# Quant series, video 2: the strategy (NQ)

Turns the model's prediction into orders. Three decisions: entry/exit signal, trade sizing, leverage.
Code: `src/quant/strategy.py`, `scripts/quant_v2_strategy.py`. Outputs in `output/quant_v2/` (gitignored).
Run: `python -m scripts.quant_v2_strategy`.

## Setup (mirrors the video's switch to 12h bars and 3 features)

| Item | Value |
|---|---|
| Model | linear, 12h bars, features = lags 1..3 of close log return, L1 loss |
| Learned | weights [+0.013, -0.027, +0.004], bias +0.0006 (lag 2 is the mean-reversion term) |
| Test window | 502 bars, 2025-08-27 to 2026-07-15 (newest 25%, never trained on) |
| Entry/exit | time-based: enter at bar open, exit at bar close, direction = sign(y_hat) |
| Capital | $10,000 (video used $100; NQ notional is $20 x price, so $10k reads better) |
| Fees | $2.50/side commission; taker adds 1 tick ($5) slippage per side |
| Margin | maintenance 5% of notional (CME NQ is about 4.7%) |

## Results

| Sizing | Leverage | Net return (taker) | Max drawdown | Liquidated bars |
|---|---|---|---|---|
| constant | 1x | +26.7% | | 0 |
| compounding | 1x | +28.2% | -12.9% | 0 |
| compounding | 2x | +58.4% | -24.8% | 0 |
| compounding | 4x | +116.6% | -45.3% | 0 |
| compounding | 8x | +158.3% | -74.5% | 0 |
| compounding | 12x | +64.1% | -91.6% | 1 (wiped out; the table keeps trading past it) |

Buy-and-hold on the same bars: +24.0% at 1x, +89.6% at 4x. Win rate is 53% at every leverage.
Max leverage with zero historical liquidations in this window: about 10x.
Fees on NQ are small: one $10k round trip costs $0.10 as maker and $0.29 as taker.

## Honest read

- **The model is still 98.6% long.** It shorted 7 of 502 bars, always right after a big up bar
  (the negative lag-2 weight). Those 7 shorts won 5 times and added about 3% over buy-and-hold.
  Seven trades is not evidence of skill.
- **Leverage multiplies size, not edge.** 4x roughly 4x's the return and the drawdown. The
  compounding curve at 8x lost three quarters of the account at its worst and still "won."
  A trader would not have sat through that.
- **NQ lot size sets a floor on leverage.** $10k at 1x is 0.02 NQ or 0.21 MNQ. You cannot trade
  that. One MNQ contract at 23,600 is $47k notional, so the smallest real position on $10k is
  already 4.7x. Fixed 1 MNQ per bar over the window: +126% on $10k, max drawdown -41%.
- **Buy-and-hold is the bar.** At every leverage the model beats it by the same 7 shorts, nothing
  else. The strategy layer is correct and reusable; the model under it still needs real features.

## Differences from the video, on purpose

- Liquidation uses a futures margin model (`liquidation_price_futures`), not the Binance perp
  formula. The video's formula is kept as `liquidation_price_perp` and its toy numbers match.
- Compounding with leverage grows equity by `1 + L * (exp(r) - 1) - fees`, not `exp(L * r)`.
- Trade P&L uses close-to-close like the video (that is what the model predicts). Open-to-close,
  which is what an enter-open/exit-close order actually earns, is one column over and differs by
  0.4% over the window because NQ bars are nearly gap-free except weekends.
