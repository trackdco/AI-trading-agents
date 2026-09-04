"""Research helpers mirroring the video's `research` library, adapted to NQ 1-minute bars.

Everything here is pure (no file IO) except `plot_*`, which write PNGs.
"""
from __future__ import annotations

import itertools
import random
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
import polars as pl
import torch
from torch import nn

NQ_POINT_VALUE = 20.0  # $ per index point
NQ_TICK = 0.25         # index points


# ----------------------------------------------------------------------------- setup
def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


# ----------------------------------------------------------------------------- time series
def load_ohlc_time_series(parquet_path: str | Path, time_interval: str) -> pl.DataFrame:
    """Aggregate 1-minute NQ bars into `time_interval` OHLCV bars (polars duration, e.g. '1h')."""
    df = pl.read_parquet(parquet_path).sort("ts_event")
    ts = (
        df.group_by_dynamic("ts_event", every=time_interval, closed="left", label="left")
        .agg(
            pl.col("open").first(),
            pl.col("high").max(),
            pl.col("low").min(),
            pl.col("close").last(),
            pl.col("volume").sum(),
            pl.len().alias("n_minutes"),
        )
    )
    return ts


def add_log_return_features(
    ts: pl.DataFrame, price_col: str, forecast_horizon: int, max_lags: int
) -> pl.DataFrame:
    """Add target `<price>_log_return` (this bar vs `forecast_horizon` bars back) and lags 1..max_lags."""
    target = f"{price_col}_log_return"
    ts = ts.with_columns(
        (pl.col(price_col) / pl.col(price_col).shift(forecast_horizon)).log().alias(target)
    )
    return add_lags(ts, target, max_lags, forecast_horizon)


def add_lags(ts: pl.DataFrame, target: str, max_lags: int, forecast_horizon: int) -> pl.DataFrame:
    """Lag k of the target is the target shifted by k * forecast_horizon rows (always past values)."""
    return ts.with_columns(
        [
            pl.col(target).shift(forecast_horizon * k).alias(f"{target}_lag_{k}")
            for k in range(1, max_lags + 1)
        ]
    )


def autocorrelation_matrix(ts: pl.DataFrame, target: str, max_lags: int) -> pl.DataFrame:
    cols = [target] + [f"{target}_lag_{k}" for k in range(1, max_lags + 1)]
    return ts.select(cols).drop_nulls().corr()


# ----------------------------------------------------------------------------- split
def time_series_split(
    ts: pl.DataFrame, features: Sequence[str], target: str, test_size: float
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Split by time (oldest -> train, newest -> test). No shuffling = no leakage."""
    n = len(ts)
    split_index = int(n * (1 - test_size))
    train, test = ts[:split_index], ts[split_index:]

    def to_x(df: pl.DataFrame) -> torch.Tensor:
        return torch.tensor(df.select(list(features)).to_numpy(), dtype=torch.float32)

    def to_y(df: pl.DataFrame) -> torch.Tensor:
        return torch.tensor(df[target].to_numpy(), dtype=torch.float32).reshape(-1, 1)

    return to_x(train), to_x(test), to_y(train), to_y(test)


# ----------------------------------------------------------------------------- model
class LinearModel(nn.Module):
    """y_hat = w . x + b — two parameters per feature, fully interpretable."""

    def __init__(self, input_features: int) -> None:
        super().__init__()
        self.linear = nn.Linear(input_features, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def total_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def train_model(
    model: nn.Module,
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    num_epochs: int = 200,
    learning_rate: float = 0.01,
    loss_fn: Callable[[torch.Tensor, torch.Tensor], torch.Tensor] | None = None,
    optimizer_cls: type[torch.optim.Optimizer] = torch.optim.Adam,
    log_every: int = 0,
) -> list[float]:
    """Batch gradient descent (whole train set per step). Returns the loss history."""
    criterion = loss_fn or nn.MSELoss()
    optimizer = optimizer_cls(model.parameters(), lr=learning_rate)
    history: list[float] = []
    model.train()
    for epoch in range(num_epochs):
        y_hat = model(x_train)
        loss = criterion(y_hat, y_train)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        history.append(loss.item())
        if log_every and (epoch + 1) % log_every == 0:
            print(f"  epoch {epoch + 1}/{num_epochs} loss={loss.item():.8f}")
    return history


def learned_parameters(model: nn.Module) -> dict[str, list[float]]:
    return {
        name: p.data.numpy().ravel().tolist()
        for name, p in model.named_parameters()
        if p.requires_grad
    }


def predict(model: nn.Module, x: torch.Tensor) -> torch.Tensor:
    model.eval()
    with torch.no_grad():
        return model(x)


# ----------------------------------------------------------------------------- trades
def trade_results(y_hat: torch.Tensor, y: torch.Tensor) -> pl.DataFrame:
    """One row per bar: sign(prediction) is the bet, realised log return * bet is the trade P&L."""
    df = pl.DataFrame({"y_hat": y_hat.squeeze().numpy(), "y": y.squeeze().numpy()})
    return (
        df.with_columns(
            (pl.col("y_hat").sign() == pl.col("y").sign()).alias("is_win"),
            pl.col("y_hat").sign().alias("signal"),
        )
        .with_columns((pl.col("signal") * pl.col("y")).alias("trade_log_return"))
        .with_columns(pl.col("trade_log_return").cum_sum().alias("equity_curve"))
    )


def performance(trades: pl.DataFrame, annualised_rate: float, col: str = "trade_log_return") -> dict:
    eq = trades[col].cum_sum()
    drawdown_log = eq - eq.cum_max()
    max_dd_log = float(drawdown_log.min())
    is_win = trades[col] > 0
    win_rate = float(is_win.mean())
    wins = trades.filter(is_win)[col]
    losses = trades.filter(~is_win)[col]
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0
    ev = win_rate * avg_win + (1 - win_rate) * avg_loss
    std = float(trades[col].std()) if len(trades) > 1 else float("nan")
    total_log = float(trades[col].sum())
    share_long = float((trades["signal"] > 0).mean()) if "signal" in trades.columns else float("nan")
    return {
        "n_trades": len(trades),
        "share_long": share_long,
        "sharpe": (ev / std * annualised_rate) if std and std > 0 else 0.0,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expected_value": ev,
        "total_log_return": total_log,
        "compound_return": float(np.exp(total_log) - 1),
        "max_drawdown_log": max_dd_log,
        "max_drawdown_pct": float(np.exp(max_dd_log) - 1),
        "equity_trough": float(eq.min()),
        "equity_peak": float(eq.max()),
        "std": std,
    }


def nq_round_trip_fee_log(
    price: pl.Expr, commission_per_side: float, slippage_ticks_per_side: float
) -> pl.Expr:
    """Round-trip cost of one NQ contract as a log return of notional (point value * price)."""
    notional = price * NQ_POINT_VALUE
    cost = 2 * (commission_per_side + slippage_ticks_per_side * NQ_TICK * NQ_POINT_VALUE)
    return (1 - cost / notional).log()


def add_transaction_fees(
    trades: pl.DataFrame,
    price: pl.Series,
    commission_per_side: float,
    maker_slippage_ticks: float,
    taker_slippage_ticks: float,
) -> pl.DataFrame:
    """Add net (after-fee) P&L and equity curves for a maker (limit) and taker (market) fill."""
    trades = trades.with_columns(pl.Series("price", price))
    return trades.with_columns(
        nq_round_trip_fee_log(pl.col("price"), commission_per_side, maker_slippage_ticks).alias("fee_maker_log"),
        nq_round_trip_fee_log(pl.col("price"), commission_per_side, taker_slippage_ticks).alias("fee_taker_log"),
    ).with_columns(
        (pl.col("trade_log_return") + pl.col("fee_maker_log")).alias("trade_log_return_net_maker"),
        (pl.col("trade_log_return") + pl.col("fee_taker_log")).alias("trade_log_return_net_taker"),
    ).with_columns(
        pl.col("trade_log_return_net_maker").cum_sum().alias("equity_curve_net_maker"),
        pl.col("trade_log_return_net_taker").cum_sum().alias("equity_curve_net_taker"),
    )


# ----------------------------------------------------------------------------- benchmarking
def benchmark_reg_model(
    ts: pl.DataFrame,
    features: Sequence[str],
    target: str,
    model: nn.Module,
    annualised_rate: float,
    num_epochs: int = 200,
    learning_rate: float = 0.01,
    loss_fn: Callable | None = None,
    test_size: float = 0.25,
) -> tuple[dict, pl.DataFrame]:
    """Train on the old part, trade the new part, return (metrics, trades)."""
    ts = ts.select(["ts_event", "close", target, *features]).drop_nulls()
    x_train, x_test, y_train, y_test = time_series_split(ts, features, target, test_size)
    train_model(model, x_train, y_train, num_epochs, learning_rate, loss_fn)
    criterion = loss_fn or nn.MSELoss()
    y_hat_train = predict(model, x_train)
    y_hat = predict(model, x_test)
    trades = trade_results(y_hat, y_test)
    split_index = len(ts) - len(y_test)
    trades = trades.with_columns(
        ts["ts_event"][split_index:].alias("ts_event"), ts["close"][split_index:].alias("close")
    )
    metrics = {
        "features": "+".join(features),
        "loss": type(criterion).__name__,
        **learned_parameters_flat(model),
        "train_loss": float(criterion(y_hat_train, y_train)),
        "test_loss": float(criterion(y_hat, y_test)),
        **performance(trades, annualised_rate),
    }
    return metrics, trades


def learned_parameters_flat(model: nn.Module) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, vals in learned_parameters(model).items():
        for i, v in enumerate(vals):
            out[f"{name.replace('linear.', '')}_{i}"] = v
    return out


def benchmark_linear_models(
    ts: pl.DataFrame,
    target: str,
    feature_pool: Sequence[str],
    annualised_rate: float,
    combo_sizes: Sequence[int] = (1,),
    num_epochs: int = 200,
    learning_rate: float = 0.01,
    loss_fn: Callable | None = None,
    test_size: float = 0.25,
    seed: int = 42,
) -> pl.DataFrame:
    rows = []
    for k in combo_sizes:
        for combo in itertools.combinations(feature_pool, k):
            set_seed(seed)
            model = LinearModel(len(combo))
            metrics, _ = benchmark_reg_model(
                ts, list(combo), target, model, annualised_rate, num_epochs, learning_rate, loss_fn, test_size
            )
            rows.append(metrics)
    return pl.DataFrame(rows).sort("sharpe", descending=True)


def buy_and_hold(trades: pl.DataFrame, annualised_rate: float) -> dict:
    """Baseline: always long, same bars. `y` is the realised log return per bar."""
    bh = trades.select(pl.col("y").alias("trade_log_return"), pl.lit(1.0).alias("signal"))
    return {"features": "buy_and_hold", "loss": "-", **performance(bh, annualised_rate)}


def annualised_rate(ts: pl.DataFrame) -> float:
    """sqrt(bars per year), measured from the data itself (NQ has session gaps, so don't assume 24x365)."""
    span_days = (ts["ts_event"].max() - ts["ts_event"].min()).total_seconds() / 86400
    per_year = len(ts) / (span_days / 365.25)
    return float(np.sqrt(per_year))


# ----------------------------------------------------------------------------- plotting
def plot_equity_curves(
    trades: pl.DataFrame, columns: Sequence[str], title: str, out_path: str | Path
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 4.5))
    x = trades["ts_event"].to_numpy() if "ts_event" in trades.columns else np.arange(len(trades))
    for c in columns:
        ax.plot(x, trades[c].to_numpy(), label=c, linewidth=1)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_title(title)
    ax.set_ylabel("cumulative log return")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def plot_distribution(values: np.ndarray, title: str, out_path: str | Path, bins: int = 200) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(values[~np.isnan(values)], bins=bins)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
