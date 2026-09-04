#!/usr/bin/env python3
"""Quant strategy series, video 3: put it together (streaming -> model -> orders -> mock exchange).

Ends with a check the video did not do: replay the live code over the video-2 test window and
confirm it reproduces the video-2 backtest equity.

    python -m scripts.quant_v3_system
"""
from __future__ import annotations

import json
import sys
import time
from decimal import Decimal
from pathlib import Path

import numpy as np
import polars as pl
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.quant import research, strategy  # noqa: E402
from src.quant.trading_system import (  # noqa: E402
    ArrayWindow, AutoRegressiveStrategy, DequeWindow, LastValue, LogReturn, LogReturnLags,
    TestAccount, TestExchange, execute,
)

SYMBOL = "NQ"
DATA = Path("data/reference/nq_1m_master.parquet")
OUT = Path("output/quant_v3")
WEIGHTS = Path("output/quant_v2/model_weights_12h_3lag.pt")
TIME_INTERVAL, NUM_LAGS, TEST_SIZE = "12h", 3, 0.25
CAPITAL = Decimal(10_000)
LEVERAGE = Decimal(1)
NQ_POINT_VALUE = Decimal(20)
COMMISSION, TAKER_TICKS = 2.50, 1.0
FEE_PER_CONTRACT_SIDE = Decimal(str(COMMISSION + TAKER_TICKS * 0.25 * 20))
OUT.mkdir(parents=True, exist_ok=True)
target = "close_log_return"
features = [f"{target}_lag_{k}" for k in range(1, NUM_LAGS + 1)]


def section(title: str) -> None:
    print(f"\n{'=' * 90}\n{title}\n{'=' * 90}")


def main() -> None:
    section("Recap: load the video-2 model (12h, 3 lags) with weights_only=True")
    model = strategy.load_linear_model(str(WEIGHTS), NUM_LAGS)
    print(model, research.learned_parameters(model))

    section("Building block 1: sliding window (deque) vs array window")
    w = DequeWindow(3)
    for v in (1, 2, 3):
        w.on_tick(v)
    print(w, "-> push 4 drops", w.on_tick(4), "->", w)
    n = 2_000_000
    for name, win in (("ArrayWindow", ArrayWindow(20)), ("DequeWindow", DequeWindow(20))):
        t0 = time.perf_counter()
        for i in range(n):
            win.on_tick(float(i))
        print(f"  {name}: {n:,} ticks in {time.perf_counter() - t0:.2f}s")

    section("Building block 2: LastValue, LogReturn, LogReturnLags")
    lv = LastValue()
    for i in range(5):
        lv.on_tick(i)
    print("last value:", lv.value)
    lr = LogReturn()
    print("log returns of 100 -> 120 -> 100:", [lr.on_tick(p) for p in (100, 120, 100)], " (they sum to 0)")
    lags = LogReturnLags(NUM_LAGS)
    prices = [90.0, 100.0, 120.0, 100.0, 110.0]
    for p in prices:
        x = lags.on_tick(p)
        print(f"  price {p:6.1f} -> features {None if x is None else x.numpy().round(5).tolist()}")
    manual = [np.log(prices[i] / prices[i - 1]) for i in range(len(prices) - 1, 1, -1)]
    print("  manual [lag_1, lag_2, lag_3]:", np.round(manual, 5).tolist())
    with torch.no_grad():
        print("  model(x) =", float(model(x)[0]))

    section("Building block 3: Decimal for money")
    print("  float: sum of ten 0.1 =", sum(0.1 for _ in range(10)))
    print("  Decimal: sum of ten 0.1 =", sum(Decimal("0.1") for _ in range(10)))

    section("Building block 4: mock account + exchange (open, close, P&L)")
    acct = TestAccount(Decimal(50))
    ex = TestExchange(acct)
    print(" ", ex.market_order("BTCUSD", Decimal(5), Decimal(10)))
    print("  position:", ex.get_position("BTCUSD"), "balance:", ex.balance)
    print(" ", ex.market_order("BTCUSD", Decimal(-5), Decimal(15)))
    print("  position:", ex.get_position("BTCUSD"), "balance:", ex.balance, "trades:", len(acct.trades))

    section("Strategy API: stream prices -> orders -> execute, step by step")
    acct = TestAccount(Decimal(100))
    ex = TestExchange(acct)
    strat = AutoRegressiveStrategy("TOY", model, NUM_LAGS)
    for p in (10, 12, 11, 13, 9, 14):
        orders = strat.on_tick(Decimal(p), ex)
        trades = execute(orders, ex, Decimal(p))
        print(f"  price {p:>3}: y_hat={None if strat.last_y_hat is None else round(strat.last_y_hat, 6)} orders={[str(o.signed_quantity.quantize(Decimal('0.0001'))) for o in (orders or [])]} "
              f"pnl={[str(t.pnl.quantize(Decimal('0.01'))) for t in trades]} balance={ex.balance.quantize(Decimal('0.01'))} pos={None if ex.get_position('TOY') is None else str(ex.get_position('TOY').signed_quantity.quantize(Decimal('0.0001')))}")

    section(f"Parity: replay the live pipeline over the video-2 test window ({SYMBOL} {TIME_INTERVAL})")
    ts = research.load_ohlc_time_series(DATA, TIME_INTERVAL)
    ts = research.add_log_return_features(ts, "close", 1, NUM_LAGS)
    ts_clean = ts.select(["ts_event", "open", "high", "low", "close", target, *features]).drop_nulls()
    split = int(len(ts_clean) * (1 - TEST_SIZE))
    # warm-up: pre-populate the lag window with the bars before the test window (the video's advice)
    warm = ts_clean["close"][split - NUM_LAGS - 1: split].to_list()
    test = ts_clean[split:]
    acct = TestAccount(CAPITAL)
    ex = TestExchange(acct, NQ_POINT_VALUE, FEE_PER_CONTRACT_SIDE)
    strat = AutoRegressiveStrategy(SYMBOL, model, NUM_LAGS, NQ_POINT_VALUE, LEVERAGE)
    for p in warm:
        strat.lags.on_tick(p)  # features only; no orders during warm-up
    rows = []
    prev_close = warm[-1]
    for ts_event, close in zip(test["ts_event"], test["close"]):
        price = Decimal(str(close))
        orders = strat.on_tick(price, ex)
        # the video-2 backtest earns close-to-close on the position opened at the *previous* close,
        # so trade at the new close: close old position (realise P&L), then open the new one.
        trades = execute(orders, ex, price)
        rows.append({"ts_event": ts_event, "prev_close": prev_close, "close": close, "y_hat": strat.last_y_hat,
                     "realised_pnl": float(sum(t.pnl for t in trades)), "fees": float(sum(t.fee for t in trades)),
                     "balance": float(ex.balance), "position": float(ex.get_position(SYMBOL).signed_quantity)})
        prev_close = close
    # close the final position at the last close so balance is fully realised
    last = ex.get_position(SYMBOL)
    final_trade = ex.market_order(SYMBOL, -last.signed_quantity, Decimal(str(test["close"][-1])))
    live = pl.DataFrame(rows)
    live.write_csv(OUT / "replay_trades.csv")
    print(live.select(["ts_event", "close", "y_hat", "realised_pnl", "fees", "balance", "position"]).head(5))
    print(f"live replay: {len(acct.trades)} fills, final balance ${float(ex.balance):,.2f} (last close-out pnl {float(final_trade.pnl):+.2f})")

    # video-2 backtest on the same bars. Its bar i earns close_log_return_i on a position opened at close_{i-1};
    # the live loop above opens at close_{i-1} and realises at close_i, one bar later. Compare equity streams.
    bt = strategy.add_model_predictions(test, model, features)
    bt = strategy.add_directional_signal(bt, target)
    bt = strategy.add_compounding_trades(bt, float(CAPITAL), float(LEVERAGE), COMMISSION, 0.0, TAKER_TICKS)
    bt_final = float(bt["equity_after"][-1])
    # the backtest's first bar uses a position opened before the test window; the live loop opens its first
    # position at the first test close, so live realises bars 2..N. Align: skip the backtest's first bar.
    bt_aligned = float(CAPITAL) * float((bt["equity_after"] / bt["equity_before"])[1:].product())
    # live y_hat at bar i is the forecast FOR bar i+1; the backtest's signal at bar i is the forecast FOR bar i
    same_direction = int((np.sign(live["y_hat"].to_numpy()[:-1]) == bt["directional_signal"].to_numpy()[1:]).sum())
    print(f"signals identical on {same_direction}/{len(bt) - 1} comparable bars")
    bt_gross_aligned = float(CAPITAL) * float((1 + float(LEVERAGE) * (bt["trade_log_return"].exp() - 1))[1:].product())
    print(f"backtest final equity (all {len(bt)} bars): ${bt_final:,.2f}")
    print(f"backtest final equity (bars 2..{len(bt)}, same bars the live loop traded): ${bt_aligned:,.2f}")
    print(f"live replay final balance:                 ${float(ex.balance):,.2f}   diff {float(ex.balance) / bt_aligned - 1:+.4%}")
    # note the backtest prices fees off the bar open; the live loop prices them off the fill (close). Gross check:
    gross_live = float(CAPITAL) + sum(r["realised_pnl"] for r in rows) + float(final_trade.pnl)
    print(f"gross (no fees): live ${gross_live:,.2f}  backtest ${bt_gross_aligned:,.2f}  diff {gross_live / bt_gross_aligned - 1:+.5%}")

    (OUT / "system_card.json").write_text(json.dumps({
        "symbol": SYMBOL, "time_interval": TIME_INTERVAL, "num_lags": NUM_LAGS, "leverage": str(LEVERAGE),
        "capital": str(CAPITAL), "fee_per_contract_side": str(FEE_PER_CONTRACT_SIDE),
        "fills": len(acct.trades), "live_final_balance": float(ex.balance),
        "backtest_final_equity_aligned": bt_aligned, "backtest_final_equity_all_bars": bt_final,
        "signals_identical": f"{same_direction}/{len(bt)}",
    }, indent=2))
    print(f"\nsaved {OUT / 'system_card.json'}")


if __name__ == "__main__":
    main()
