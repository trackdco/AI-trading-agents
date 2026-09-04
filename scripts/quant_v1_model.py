#!/usr/bin/env python3
"""Quant strategy series, video 1: build the model (auto-regressive log-return, linear, PyTorch).

Follows the video's walkthrough but on NQ 1-minute bars from data/reference/nq_1m_master.parquet.
Writes tables, plots, and the chosen model weights to output/quant_v1/.

    python -m scripts.quant_v1_model
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.quant import research  # noqa: E402

# ------------------------------------------------------------------ research parameters
SYMBOL = "NQ"
DATA = Path("data/reference/nq_1m_master.parquet")
OUT = Path("output/quant_v1")
TIME_INTERVAL = "1h"
MAX_LAGS = 4
FORECAST_HORIZON = 1
TEST_SIZE = 0.25
NUM_EPOCHS = 500
LEARNING_RATE = 0.01
# NQ costs: ~$2.50/side all-in commission; a market order pays ~1 tick of spread per side.
COMMISSION_PER_SIDE = 2.50
MAKER_SLIPPAGE_TICKS = 0.0
TAKER_SLIPPAGE_TICKS = 1.0

SHOW_COLS = ["features", "loss", "weight_0", "bias_0", "share_long", "sharpe", "win_rate", "expected_value", "compound_return", "max_drawdown_pct", "equity_trough", "equity_peak", "n_trades"]
pl.Config.set_tbl_cols(30)
pl.Config.set_tbl_width_chars(220)
pl.Config.set_float_precision(6)
OUT.mkdir(parents=True, exist_ok=True)
research.set_seed(42)


def section(title: str) -> None:
    print(f"\n{'=' * 90}\n{title}\n{'=' * 90}")


def run_interval(time_interval: str, max_lags: int, num_epochs: int) -> tuple[pl.DataFrame, float]:
    section(f"{SYMBOL} {time_interval} bars: build time series + features")
    ts = research.load_ohlc_time_series(DATA, time_interval)
    print(f"rows={len(ts)}  range={ts['ts_event'].min()} -> {ts['ts_event'].max()}")
    ts = research.add_log_return_features(ts, "close", FORECAST_HORIZON, max_lags)
    print(ts.head(max_lags + 3))
    ann = research.annualised_rate(ts)
    print(f"annualisation factor sqrt(bars/year) = {ann:.2f}")
    return ts, ann


def main() -> None:
    target = "close_log_return"

    # ---------------------------------------------------------------- 1h: follow the video
    ts, ann = run_interval(TIME_INTERVAL, MAX_LAGS, NUM_EPOCHS)
    ts_clean = ts.drop_nulls()
    research.plot_distribution(ts_clean[target].to_numpy(), f"{SYMBOL} {TIME_INTERVAL} log returns", OUT / "dist_log_returns_1h.png")
    research.plot_distribution(ts_clean["close"].to_numpy(), f"{SYMBOL} close price (multimodal)", OUT / "dist_price_1h.png")

    section("Step 1: AR(1) linear model, MSE loss (the video's first model)")
    features = [f"{target}_lag_1"]
    x_train, x_test, y_train, y_test = research.time_series_split(ts_clean, features, target, TEST_SIZE)
    print(f"train rows={len(x_train)} test rows={len(x_test)}  shapes x={tuple(x_train.shape)} y={tuple(y_train.shape)}")
    model = research.LinearModel(len(features))
    print(model, "| total parameters:", research.total_parameters(model))
    research.train_model(model, x_train, y_train, NUM_EPOCHS, LEARNING_RATE, nn.MSELoss(), log_every=100)
    print("learned:", research.learned_parameters(model))
    # closed-form OLS sanity check so we know gradient descent converged
    x_np, y_np = x_train.numpy().ravel(), y_train.numpy().ravel()
    w_ols, b_ols = np.polyfit(x_np, y_np, 1)
    print(f"OLS check: weight={w_ols:.6f} bias={b_ols:.8f}")
    y_hat = research.predict(model, x_test)
    print(f"train loss={nn.MSELoss()(research.predict(model, x_train), y_train):.10f}  test loss={nn.MSELoss()(y_hat, y_test):.10f}")

    trades = research.trade_results(y_hat, y_test)
    split_index = len(ts_clean) - len(y_test)
    trades = trades.with_columns(ts_clean["ts_event"][split_index:].alias("ts_event"), ts_clean["close"][split_index:].alias("close"))
    print(trades.head(8))
    perf = research.performance(trades, ann)
    print(json.dumps(perf, indent=2))
    print("buy-and-hold baseline on the same test bars:")
    print(json.dumps(research.buy_and_hold(trades, ann), indent=2))
    research.plot_equity_curves(trades, ["equity_curve"], f"{SYMBOL} {TIME_INTERVAL} AR(1) MSE gross equity", OUT / "equity_1h_ar1_mse.png")

    section("Step 2: benchmark lags 1..4 (single-feature models), L1 loss")
    pool = [f"{target}_lag_{k}" for k in range(1, MAX_LAGS + 1)]
    bench_1h = research.benchmark_linear_models(ts, target, pool, ann, num_epochs=NUM_EPOCHS, loss_fn=nn.L1Loss(), test_size=TEST_SIZE)
    bh_1h = pl.DataFrame([research.buy_and_hold(trades, ann)])
    print(pl.concat([bench_1h, bh_1h], how="diagonal").select(SHOW_COLS))
    bench_1h.write_csv(OUT / "benchmark_1h_l1.csv")
    print("\nautocorrelation matrix:")
    print(research.autocorrelation_matrix(ts, target, MAX_LAGS))

    section("Step 3: best 1h model with transaction fees")
    best = bench_1h.row(0, named=True)
    best_feats = best["features"].split("+")
    research.set_seed(42)
    model = research.LinearModel(len(best_feats))
    _, trades = research.benchmark_reg_model(ts, best_feats, target, model, ann, NUM_EPOCHS, LEARNING_RATE, nn.L1Loss(), TEST_SIZE)
    trades = research.add_transaction_fees(trades, trades["close"], COMMISSION_PER_SIDE, MAKER_SLIPPAGE_TICKS, TAKER_SLIPPAGE_TICKS)
    print(f"best 1h feature: {best_feats}  weight={best.get('weight_0'):.5f} bias={best.get('bias_0'):.7f}")
    print(f"avg round-trip fee (log): maker={trades['fee_maker_log'].mean():.7f} taker={trades['fee_taker_log'].mean():.7f}")
    for col in ["trade_log_return", "trade_log_return_net_maker", "trade_log_return_net_taker"]:
        p = research.performance(trades, ann, col)
        print(f"{col:30s} sharpe={p['sharpe']:7.2f} compound={p['compound_return']:8.4f} EV={p['expected_value']:.7f} win={p['win_rate']:.3f} maxDD={p['max_drawdown_pct']:.4f} trough={p['equity_trough']:.4f}")
    research.plot_equity_curves(trades, ["equity_curve", "equity_curve_net_maker", "equity_curve_net_taker"], f"{SYMBOL} {TIME_INTERVAL} best lag, gross vs net of fees", OUT / "equity_1h_best_fees.png")

    # ---------------------------------------------------------------- 8h: longer horizon
    ts8, ann8 = run_interval("8h", 3, NUM_EPOCHS)
    pool8 = [f"{target}_lag_{k}" for k in range(1, 4)]
    all_bench = []
    for loss in [nn.HuberLoss(), nn.MSELoss(), nn.L1Loss()]:
        section(f"8h benchmark, loss={type(loss).__name__}")
        b = research.benchmark_linear_models(ts8, target, pool8, ann8, num_epochs=NUM_EPOCHS, loss_fn=loss, test_size=TEST_SIZE)
        print(b.select(SHOW_COLS))
        all_bench.append(b)
    bench_8h = pl.concat(all_bench).sort("sharpe", descending=True)
    bench_8h.write_csv(OUT / "benchmark_8h_all_losses.csv")
    print("\n8h ranking across all losses, plus buy-and-hold on the same test bars:")
    _, t_tmp = research.benchmark_reg_model(ts8, pool8[:1], target, research.LinearModel(1), ann8, 1, LEARNING_RATE, None, TEST_SIZE)
    print(pl.concat([bench_8h, pl.DataFrame([research.buy_and_hold(t_tmp, ann8)])], how="diagonal").select(SHOW_COLS))
    print("\nautocorrelation matrix (8h):")
    print(research.autocorrelation_matrix(ts8, target, 3))

    section("8h: best model, gross vs net of fees, save weights")
    best8 = bench_8h.row(0, named=True)
    feats8 = best8["features"].split("+")
    loss8 = {"HuberLoss": nn.HuberLoss(), "MSELoss": nn.MSELoss(), "L1Loss": nn.L1Loss()}[best8["loss"]]
    research.set_seed(42)
    model8 = research.LinearModel(len(feats8))
    _, trades8 = research.benchmark_reg_model(ts8, feats8, target, model8, ann8, NUM_EPOCHS, LEARNING_RATE, loss8, TEST_SIZE)
    trades8 = research.add_transaction_fees(trades8, trades8["close"], COMMISSION_PER_SIDE, MAKER_SLIPPAGE_TICKS, TAKER_SLIPPAGE_TICKS)
    print(f"best 8h: features={feats8} loss={best8['loss']} params={research.learned_parameters(model8)}")
    summary = {}
    for col in ["trade_log_return", "trade_log_return_net_maker", "trade_log_return_net_taker"]:
        p = research.performance(trades8, ann8, col)
        summary[col] = p
        print(f"{col:30s} sharpe={p['sharpe']:7.2f} compound={p['compound_return']:8.4f} EV={p['expected_value']:.7f} win={p['win_rate']:.3f} maxDD={p['max_drawdown_pct']:.4f} trough={p['equity_trough']:.4f} n={p['n_trades']}")
    research.plot_equity_curves(trades8, ["equity_curve", "equity_curve_net_maker", "equity_curve_net_taker"], f"{SYMBOL} 8h {'+'.join(feats8)} {best8['loss']}: gross vs net", OUT / "equity_8h_best_fees.png")
    trades8.write_csv(OUT / "trades_8h_best.csv")

    torch.save(model8.state_dict(), OUT / "model_weights.pt")
    (OUT / "model_card.json").write_text(json.dumps({
        "symbol": SYMBOL, "time_interval": "8h", "forecast_horizon": FORECAST_HORIZON,
        "features": feats8, "target": target, "loss": best8["loss"],
        "parameters": research.learned_parameters(model8),
        "test_size": TEST_SIZE, "test_range": [str(trades8["ts_event"].min()), str(trades8["ts_event"].max())],
        "fees": {"commission_per_side": COMMISSION_PER_SIDE, "maker_slippage_ticks": MAKER_SLIPPAGE_TICKS, "taker_slippage_ticks": TAKER_SLIPPAGE_TICKS},
        "performance": summary,
    }, indent=2))
    print(f"\nsaved {OUT/'model_weights.pt'} and {OUT/'model_card.json'}")


if __name__ == "__main__":
    main()
