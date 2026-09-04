# Quant series, video 1: the model (NQ)

Follows the "build a quant strategy from scratch" video 1 (auto-regressive log-return model,
linear, trained with PyTorch) but on our own NQ data instead of Bitcoin.

| Item | Value |
|---|---|
| Data | `data/reference/nq_1m_master.parquet`, 1-min NQ, 2023-01-02 to 2026-07-15 |
| Bars | 1h (20,865 rows) and 8h (2,805 rows), resampled with polars |
| Target | next-bar log return of close |
| Features | lags 1..4 (1h) / 1..3 (8h) of the target |
| Model | `y_hat = w * lag + b` (2 parameters), batch gradient descent, Adam |
| Split | by time, oldest 75% train, newest 25% test (Aug 2025 to Jul 2026). No shuffle. |
| Fees | $2.50/side commission; taker pays 1 tick/side slippage, maker 0 |

Code: `src/quant/research.py` (helpers), `scripts/quant_v1_model.py` (walkthrough).
Run: `pip install -r requirements-quant.txt && python -m scripts.quant_v1_model`.
Outputs land in `output/quant_v1/` (gitignored): benchmark CSVs, equity PNGs, `model_weights.pt`, `model_card.json`.

## What happened

- **Gold data is not in the repo.** Only NQ. The "gold" files here mean the "golden window" trade idea.
- **The pipeline works end to end** and reproduces every step of the video: log returns, lags,
  time split, linear model, trade results, metrics, fee curves, loss-function sweep, saved weights.
- **Gradient descent barely moves the weight.** Log returns are tiny (~0.001), so the loss surface
  is almost flat in `w`. Adam lands near zero with a different sign than exact least squares.
  Loss is the same to 8 decimals either way. The sign of the prediction is decided by the bias.

## The honest result

The "best" models are buy-and-hold in disguise.

| Model | share of bets long | Sharpe | compound return | max DD |
|---|---|---|---|---|
| 1h lag 4, L1 loss | 100% | 1.30 | +25.8% | -12.6% |
| buy-and-hold, same 1h bars | 100% | 1.30 | +25.8% | -12.6% |
| 8h lag 1, L1 loss | 100% | 1.28 | +26.0% | -12.1% |
| buy-and-hold, same 8h bars | 100% | 1.28 | +26.0% | -12.1% |
| 8h lag 2, Huber/MSE (actually flips sign) | 82% | 1.06 | +21.1% | -14.1% |

Every model that actually changes its mind based on the lag does worse than just being long.
NQ 1h autocorrelation is about 0.01 (nothing). At 8h, lags 2 and 3 show -0.07 (a whisper of
mean reversion), not enough to beat the drift in this test year.

Fees matter less on NQ than on Bitcoin: one round trip costs about 0.003% of notional at taker
and 0.001% at maker, so the 8h taker curve keeps ~90% of gross. The video's "fees kill the 1h
edge" lesson still shows up at 1h: taker Sharpe drops from 1.30 to 0.45.

## Takeaways for video 2

- The video's plain lag model has no edge on NQ beyond "NQ went up in the test year." Do not
  build the strategy on the saved weights and expect the 1.3 Sharpe to be model skill.
- Next things to try before video 2: remove the bias (forbid "always long"), add features with
  real information (session, VWAP distance, order-book depth from the MBP-10 CSVs, CVD),
  test on more than one 25% window (walk-forward).
- Multiple-testing caution: ranking 4 lags x 3 losses and picking the top row is cheap
  overfitting; the buy-and-hold row is the fair bar.
