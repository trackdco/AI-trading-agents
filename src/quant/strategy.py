"""Quant series video 2: turn model predictions into orders (entry/exit, sizing, leverage, liquidation).

NQ notes vs the video's Bitcoin example:
- Notional is in dollars = price * $20 (one NQ contract). Micro NQ (MNQ) is $2 per point.
- Fees are per contract-equivalent: commission per side + slippage ticks per side (taker only),
  expressed as a fraction of notional so the video's dollar arithmetic still works.
- Futures have no fixed "liquidation price" like a crypto perp: the broker closes you when equity
  drops below maintenance margin. `liquidation_price_futures` models that; `liquidation_price_perp`
  is the video's (Binance-style) formula, kept so the toy numbers match the video.
"""
from __future__ import annotations

import numpy as np
import polars as pl
import torch
from torch import nn

from src.quant.research import NQ_POINT_VALUE, NQ_TICK

MNQ_POINT_VALUE = 2.0


# ----------------------------------------------------------------------------- model loading
def load_linear_model(weights_path: str, input_features: int) -> nn.Module:
    from src.quant.research import LinearModel

    model = LinearModel(input_features)
    model.load_state_dict(torch.load(weights_path, weights_only=True))  # weights_only: no arbitrary code
    model.eval()
    return model


def add_model_predictions(trades: pl.DataFrame, model: nn.Module, features: list[str]) -> pl.DataFrame:
    x = torch.tensor(trades.select(features).to_numpy(), dtype=torch.float32)
    with torch.no_grad():
        y_hat = model(x).squeeze(1).numpy()
    return trades.with_columns(pl.Series("y_hat", y_hat))


# ----------------------------------------------------------------------------- decision 1: signal
def add_directional_signal(trades: pl.DataFrame, target: str) -> pl.DataFrame:
    """Time-based entry/exit: enter at the bar open, exit at the bar close. Direction = sign(y_hat)."""
    return (
        trades.with_columns(pl.col("y_hat").sign().alias("directional_signal"))
        .with_columns(
            (pl.col(target) * pl.col("directional_signal")).alias("trade_log_return"),
            ((pl.col("close") / pl.col("open")).log() * pl.col("directional_signal")).alias("trade_log_return_open_to_close"),
        )
        .with_columns(pl.col("trade_log_return").cum_sum().alias("cum_trade_log_return"))
    )


# ----------------------------------------------------------------------------- fees
def nq_fee_rate_per_side(price: pl.Expr, commission_per_side: float, slippage_ticks: float) -> pl.Expr:
    """Cost of one side, as a fraction of notional, for one NQ contract at `price`."""
    return (commission_per_side + slippage_ticks * NQ_TICK * NQ_POINT_VALUE) / (price * NQ_POINT_VALUE)


# ----------------------------------------------------------------------------- decision 2: sizing
def add_constant_sizing(
    trades: pl.DataFrame,
    capital: float,
    leverage: float,
    commission_per_side: float,
    maker_slippage_ticks: float,
    taker_slippage_ticks: float,
    ratio: float = 1.0,
) -> pl.DataFrame:
    """Same notional every trade: capital * ratio * leverage. P&L is not reinvested."""
    trade_value = capital * ratio * leverage
    return _finish_sizing(
        trades.with_columns(
            pl.lit(trade_value).alias("entry_trade_value"),
            (pl.lit(trade_value) * pl.col("trade_log_return").exp()).alias("exit_trade_value"),
        ),
        capital, commission_per_side, maker_slippage_ticks, taker_slippage_ticks,
    )


def add_compounding_trades(
    trades: pl.DataFrame,
    capital: float,
    leverage: float,
    commission_per_side: float,
    maker_slippage_ticks: float,
    taker_slippage_ticks: float,
    fee_side: str = "taker",
) -> pl.DataFrame:
    """Reinvest: notional = equity * leverage each bar. Equity compounds on the *levered* simple return
    net of fees (equity is not exp(leverage * log_return) — leverage scales the trade size, not the return).
    """
    slip = taker_slippage_ticks if fee_side == "taker" else maker_slippage_ticks
    fee_rate = nq_fee_rate_per_side(pl.col("open"), commission_per_side, slip)
    simple = pl.col("trade_log_return").exp() - 1
    # per-bar growth factor of equity: 1 + L*r - fees on entry (L) and exit (L*(1+r)) notional
    growth = 1 + leverage * simple - fee_rate * leverage * (2 + simple)
    trades = trades.with_columns(growth.alias("_growth")).with_columns(
        (pl.lit(capital) * pl.col("_growth").cum_prod()).alias("equity_after"),
    ).with_columns(
        pl.col("equity_after").shift(1).fill_null(capital).alias("equity_before"),
    ).with_columns(
        (pl.col("equity_before") * leverage).alias("entry_trade_value"),
    ).with_columns(
        (pl.col("entry_trade_value") * pl.col("trade_log_return").exp()).alias("exit_trade_value"),
    ).drop("_growth")
    return _finish_sizing(trades, capital, commission_per_side, maker_slippage_ticks, taker_slippage_ticks)


def _finish_sizing(
    trades: pl.DataFrame, capital: float, commission: float, maker_ticks: float, taker_ticks: float
) -> pl.DataFrame:
    maker_rate = nq_fee_rate_per_side(pl.col("open"), commission, maker_ticks)
    taker_rate = nq_fee_rate_per_side(pl.col("open"), commission, taker_ticks)
    return (
        trades.with_columns(
            (pl.col("entry_trade_value") / pl.col("open")).alias("trade_quantity"),
            (pl.col("exit_trade_value") - pl.col("entry_trade_value")).alias("trade_gross_pnl"),
            ((pl.col("entry_trade_value") + pl.col("exit_trade_value")) * maker_rate).alias("transaction_fee_maker"),
            ((pl.col("entry_trade_value") + pl.col("exit_trade_value")) * taker_rate).alias("transaction_fee_taker"),
        )
        .with_columns(
            (pl.col("trade_quantity") * pl.col("directional_signal")).alias("signed_trade_quantity"),
            (pl.col("entry_trade_value") / (pl.col("open") * NQ_POINT_VALUE)).alias("nq_contracts"),
            (pl.col("entry_trade_value") / (pl.col("open") * MNQ_POINT_VALUE)).alias("mnq_contracts"),
            (pl.col("trade_gross_pnl") - pl.col("transaction_fee_maker")).alias("trade_net_maker_pnl"),
            (pl.col("trade_gross_pnl") - pl.col("transaction_fee_taker")).alias("trade_net_taker_pnl"),
        )
        .with_columns(
            (capital + pl.col("trade_gross_pnl").cum_sum()).alias("equity_curve_gross"),
            (capital + pl.col("trade_net_maker_pnl").cum_sum()).alias("equity_curve_maker"),
            (capital + pl.col("trade_net_taker_pnl").cum_sum()).alias("equity_curve_taker"),
        )
    )


def total_net_return(trades: pl.DataFrame, capital: float, col: str = "equity_curve_taker") -> float:
    return float(trades[col][-1] / capital - 1)


def max_drawdown_pct(equity: pl.Series) -> float:
    return float((equity / equity.cum_max() - 1).min())


# ----------------------------------------------------------------------------- decision 3: leverage
def liquidation_price_perp(price: float, leverage: float, maintenance_margin: float, side: str) -> float:
    """The video's (Binance-style) isolated-margin formula."""
    if side == "long":
        return price * leverage / (leverage + 1 - maintenance_margin * leverage)
    return price * leverage / (leverage - 1 + maintenance_margin * leverage)


def liquidation_price_futures(price: pl.Expr, leverage: float, maintenance_margin: float, signal: pl.Expr) -> pl.Expr:
    """Futures margin: equity/notional = 1/L. Closed out when the adverse move eats equity down to
    the maintenance margin (a fraction of notional). Long: P*(1 - 1/L + mm). Short: P*(1 + 1/L - mm)."""
    loss_room = 1 / leverage - maintenance_margin
    return pl.when(signal == 1).then(price * (1 - loss_room)).otherwise(price * (1 + loss_room))


def add_liquidation(trades: pl.DataFrame, leverage: float, maintenance_margin: float) -> pl.DataFrame:
    sig = pl.col("directional_signal")
    return trades.with_columns(
        liquidation_price_futures(pl.col("open"), leverage, maintenance_margin, sig).alias("liquidation_price"),
        pl.when(sig == 1).then(pl.col("low")).otherwise(pl.col("high")).alias("worst_price"),
    ).with_columns(
        pl.when((sig == 1) & (pl.col("low") <= pl.col("liquidation_price")))
        .then(True)
        .when((sig == -1) & (pl.col("high") >= pl.col("liquidation_price")))
        .then(True)
        .otherwise(False)
        .alias("liquidated"),
        # how close did the worst price come, as a fraction of the room we had
        (((pl.col("open") - pl.when(sig == 1).then(pl.col("low")).otherwise(pl.col("high"))).abs() / pl.col("open"))
         / (1 / leverage - maintenance_margin)).alias("room_used"),
    )


def max_safe_leverage(trades: pl.DataFrame, maintenance_margin: float) -> float:
    """Largest L such that no historical bar's worst adverse move would have liquidated us."""
    sig = trades["directional_signal"]
    adverse = np.where(sig.to_numpy() == 1,
                       (trades["open"] - trades["low"]).to_numpy(),
                       (trades["high"] - trades["open"]).to_numpy()) / trades["open"].to_numpy()
    worst = float(np.nanmax(adverse))
    return 1 / (worst + maintenance_margin)
