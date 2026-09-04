#!/usr/bin/env python3
"""Quant strategy series, video 2: the strategy (prediction -> orders) on NQ.

Three decisions: (1) entry/exit signal, (2) trade sizing, (3) leverage + liquidation.
Step 0 retrains the video-2 model (12h bars, 3 lag features) since video 1 saved an 8h/1-lag one.

    python -m scripts.quant_v2_strategy
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.quant import research, strategy  # noqa: E402

# ------------------------------------------------------------------ parameters
SYMBOL = "NQ"
DATA = Path("data/reference/nq_1m_master.parquet")
OUT = Path("output/quant_v2")
TIME_INTERVAL = "12h"
NUM_LAGS = 3
FORECAST_HORIZON = 1
TEST_SIZE = 0.25
NUM_EPOCHS = 500
CAPITAL = 10_000.0           # account size in $ (video used $100; NQ notional is big, so $10k reads better)
COMMISSION_PER_SIDE = 2.50
MAKER_SLIPPAGE_TICKS = 0.0
TAKER_SLIPPAGE_TICKS = 1.0
MAINTENANCE_MARGIN = 0.05    # CME NQ maintenance ~ $27.5k on ~$580k notional = ~4.7%
LEVERAGES = [1, 2, 4, 8, 12]

pl.Config.set_tbl_cols(30)
pl.Config.set_tbl_width_chars(230)
pl.Config.set_float_precision(5)
OUT.mkdir(parents=True, exist_ok=True)
target = "close_log_return"
features = [f"{target}_lag_{k}" for k in range(1, NUM_LAGS + 1)]


def section(title: str) -> None:
    print(f"\n{'=' * 90}\n{title}\n{'=' * 90}")


def main() -> None:
    # ------------------------------------------------------------ step 0: video-2 model (12h, 3 lags)
    section("Step 0: train + save the video-2 model: 12h bars, 3 lag features, L1 loss")
    research.set_seed(42)
    ts = research.load_ohlc_time_series(DATA, TIME_INTERVAL)
    ts = research.add_log_return_features(ts, "close", FORECAST_HORIZON, NUM_LAGS)
    ann = research.annualised_rate(ts)
    print(f"rows={len(ts)} range={ts['ts_event'].min()} -> {ts['ts_event'].max()}  sqrt(bars/yr)={ann:.2f}")
    model = research.LinearModel(len(features))
    metrics, _ = research.benchmark_reg_model(ts, features, target, model, ann, NUM_EPOCHS, 0.01, nn.L1Loss(), TEST_SIZE)
    torch.save(model.state_dict(), OUT / "model_weights_12h_3lag.pt")
    print({k: (round(v, 6) if isinstance(v, float) else v) for k, v in metrics.items() if k in ("sharpe", "win_rate", "share_long", "compound_return", "max_drawdown_pct")})

    # ------------------------------------------------------------ load model, interpret
    section("Load the saved model (weights_only=True) and read its parameters")
    model = strategy.load_linear_model(str(OUT / "model_weights_12h_3lag.pt"), len(features))
    print(model)
    params = research.learned_parameters(model)
    print(json.dumps(params, indent=2))
    w = params["linear.weight"]
    print("interpretation: negative weight on a lag = mean reversion (flip the sign of that past move);")
    print("               positive = momentum. Bias > 0 = a standing lean to 'up'.")
    print(f"  lag weights: {[round(x, 5) for x in w]}  bias: {params['linear.bias'][0]:.6f}")

    section("Toy: linear model is readable, a tanh network is not")
    toy_w, toy_b = -0.2, 0.0004
    for x in (-0.01, 0.01, 0.002, 0.0):
        print(f"  linear: x={x:+.3f} -> y_hat = {toy_w}*x + {toy_b} = {toy_w * x + toy_b:+.5f}")
    torch.manual_seed(0)
    net = nn.Sequential(nn.Linear(1, 4), nn.Tanh(), nn.Linear(4, 1))
    for x in (-0.01, 0.01):
        print(f"  tanh net: x={x:+.3f} -> y_hat = {net(torch.tensor([[x]])).item():+.5f}  (why? 13 weights, no story)")

    # ------------------------------------------------------------ test trades
    section("Decision 1: entry/exit = time-based (enter at bar open, exit at bar close)")
    ts_clean = ts.select(["ts_event", "open", "high", "low", "close", target, *features]).drop_nulls()
    split = int(len(ts_clean) * (1 - TEST_SIZE))
    trades = ts_clean[split:]
    print(f"test trades: {len(trades)} bars, {trades['ts_event'].min()} -> {trades['ts_event'].max()}")
    trades = strategy.add_model_predictions(trades, model, features)
    trades = strategy.add_directional_signal(trades, target)
    print(trades.select(["ts_event", "open", "close", target, "y_hat", "directional_signal", "trade_log_return", "cum_trade_log_return"]).head(6))
    share_long = float((trades["directional_signal"] > 0).mean())
    win_rate = float((trades["trade_log_return"] > 0).mean())
    print(f"share long={share_long:.3f}  win rate={win_rate:.3f}  gross total log return={trades['trade_log_return'].sum():.4f}")
    print(f"open-to-close (what a real enter-open/exit-close trade earns) total log return={trades['trade_log_return_open_to_close'].sum():.4f}")
    research.plot_equity_curves(trades, ["cum_trade_log_return"], f"{SYMBOL} {TIME_INTERVAL} equity in log space", OUT / "equity_log_space.png")

    # ------------------------------------------------------------ constant sizing
    section(f"Decision 2a: constant sizing, capital=${CAPITAL:,.0f}, leverage=1")
    const = strategy.add_constant_sizing(trades, CAPITAL, 1, COMMISSION_PER_SIDE, MAKER_SLIPPAGE_TICKS, TAKER_SLIPPAGE_TICKS)
    cols = ["ts_event", "open", "entry_trade_value", "exit_trade_value", "signed_trade_quantity", "nq_contracts", "mnq_contracts", "trade_gross_pnl", "transaction_fee_taker", "trade_net_taker_pnl", "equity_curve_taker"]
    print(const.select(cols).head(5))
    print(f"fees per round trip at ${CAPITAL:,.0f} notional: maker=${const['transaction_fee_maker'].mean():.2f} taker=${const['transaction_fee_taker'].mean():.2f}")
    const_ret = {k: strategy.total_net_return(const, CAPITAL, f"equity_curve_{k}") for k in ("gross", "maker", "taker")}
    print("constant sizing total return:", {k: f"{v:+.2%}" for k, v in const_ret.items()})
    research.plot_equity_curves(const, ["equity_curve_gross", "equity_curve_maker", "equity_curve_taker"], f"{SYMBOL} constant sizing ${CAPITAL:,.0f}, 1x", OUT / "equity_constant_sizing.png")

    # ------------------------------------------------------------ compounding
    section("Decision 2b: compounding sizing (reinvest P&L), leverage=1")
    comp = strategy.add_compounding_trades(trades, CAPITAL, 1, COMMISSION_PER_SIDE, MAKER_SLIPPAGE_TICKS, TAKER_SLIPPAGE_TICKS)
    print(comp.select(["ts_event", "equity_before", "entry_trade_value", "exit_trade_value", "trade_gross_pnl", "trade_net_taker_pnl", "equity_after"]).tail(4))
    comp_ret = strategy.total_net_return(comp, CAPITAL, "equity_after")
    print(f"compounding total net (taker) return: {comp_ret:+.2%}   vs constant: {const_ret['taker']:+.2%}   diff: {comp_ret - const_ret['taker']:+.2%}")

    # ------------------------------------------------------------ leverage
    section("Decision 3: leverage (scales trade SIZE, not the return) + liquidation check")
    print("video's perp formula, price=200, mm=0.5%:")
    for lev in (2, 4, 10, 20):
        print(f"  long  {lev:>2}x -> liquidation {strategy.liquidation_price_perp(200, lev, 0.005, 'long'):.1f}")
    for lev in (2, 4, 10, 50):
        print(f"  short {lev:>2}x -> liquidation {strategy.liquidation_price_perp(200, lev, 0.005, 'short'):.1f}")
    print(f"\nNQ futures margin model, maintenance={MAINTENANCE_MARGIN:.0%} of notional:")
    rows = []
    for lev in LEVERAGES:
        lv = strategy.add_compounding_trades(trades, CAPITAL, lev, COMMISSION_PER_SIDE, MAKER_SLIPPAGE_TICKS, TAKER_SLIPPAGE_TICKS)
        lv = strategy.add_liquidation(lv, lev, MAINTENANCE_MARGIN)
        bh = trades.with_columns(pl.lit(1.0).alias("directional_signal"), pl.col(target).alias("trade_log_return"))
        bh = strategy.add_compounding_trades(bh, CAPITAL, lev, COMMISSION_PER_SIDE, MAKER_SLIPPAGE_TICKS, TAKER_SLIPPAGE_TICKS)
        rows.append({
            "leverage": lev,
            "total_net_return": strategy.total_net_return(lv, CAPITAL, "equity_after"),
            "buy_hold_same_leverage": strategy.total_net_return(bh, CAPITAL, "equity_after"),
            "max_drawdown": strategy.max_drawdown_pct(lv["equity_after"]),
            "min_equity": float(lv["equity_after"].min()),
            "liquidated_bars": int(lv["liquidated"].sum()),
            "worst_room_used": float(lv["room_used"].max()),
            "start_nq_contracts": float(lv["nq_contracts"][0]),
            "start_mnq_contracts": float(lv["mnq_contracts"][0]),
        })
        if lev == 4:
            print(lv.select(["ts_event", "directional_signal", "open", "high", "low", "liquidation_price", "worst_price", "liquidated", "room_used"]).head(4))
            research.plot_equity_curves(lv, ["equity_after"], f"{SYMBOL} compounding 4x, net taker", OUT / "equity_compounding_4x.png")
            lv.write_csv(OUT / "trades_compounding_4x.csv")
    sweep = pl.DataFrame(rows)
    print(sweep)
    sweep.write_csv(OUT / "leverage_sweep.csv")
    safe = strategy.max_safe_leverage(trades, MAINTENANCE_MARGIN)
    print(f"\nmax leverage with zero historical liquidations in this test window: {safe:.1f}x")
    print(f"win rate is still {win_rate:.3f} at every leverage; leverage changes size, not skill.")

    (OUT / "strategy_card.json").write_text(json.dumps({
        "symbol": SYMBOL, "time_interval": TIME_INTERVAL, "features": features, "target": target,
        "model_weights": str(OUT / "model_weights_12h_3lag.pt"), "parameters": params,
        "entry_exit": "time-based: enter at bar open, exit at bar close, direction = sign(y_hat)",
        "sizing": "compounding (equity * leverage)", "capital": CAPITAL,
        "fees": {"commission_per_side": COMMISSION_PER_SIDE, "maker_slippage_ticks": MAKER_SLIPPAGE_TICKS, "taker_slippage_ticks": TAKER_SLIPPAGE_TICKS},
        "maintenance_margin": MAINTENANCE_MARGIN, "share_long": share_long, "win_rate": win_rate,
        "constant_sizing_returns": const_ret, "compounding_1x_return": comp_ret,
        "leverage_sweep": rows, "max_safe_leverage": safe,
    }, indent=2))
    print(f"\nsaved {OUT / 'strategy_card.json'}")


if __name__ == "__main__":
    main()
