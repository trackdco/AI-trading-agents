"""Census math verified on synthetic bars with hand-computed answers."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import pandas as pd
from newslab.census import measure_event, load_bars  # noqa: F401
from newslab.config import TZ_ET


def synth_bars():
    """Flat at 100 until T; release bar jumps; then grinds to 140 by +30m.
    T = 2025-06-12 08:30 ET.  T-1 close = 100 (ref).
    Release bar: o=100 h=130 l=95 c=125.  +5m close 128, +15m 132, +30m 140.
    Drift: closes ramp 99.4 → 100 over the last hour (drift_60m = +0.5)."""
    T = pd.Timestamp("2025-06-12 08:30", tz=TZ_ET)
    idx = pd.date_range(T - pd.Timedelta(minutes=70),
                        T + pd.Timedelta(minutes=125), freq="1min", tz=TZ_ET)
    df = pd.DataFrame(index=idx, columns=["open", "high", "low", "close",
                                          "volume", "symbol"])
    base = 100.0
    for t in idx:
        m = int((t - T).total_seconds() // 60)
        if m < 0:
            c = 100.0 if m == -1 else 99.5
            df.loc[t] = [c, c + .1, c - .1, c, 100, "NQU5"]
        elif m == 0:
            df.loc[t] = [100.0, 130.0, 95.0, 125.0, 5000, "NQU5"]
        else:
            c = min(140.0, 125.0 + 15.0 * m / 30.0)
            df.loc[t] = [c, c + 1.0, c - 1.0, c, 300, "NQU5"]
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df, T


def test_measure_event_exact():
    bars, T = synth_bars()
    m = measure_event(bars, T)
    assert m["coverage_ok"]
    assert m["ref"] == 100.0
    assert abs(m["drift_60m"] - 0.5) < 1e-9
    assert m["rel_high"] == 130.0 and m["rel_low"] == 95.0
    assert m["rel_range"] == 35.0
    assert m["rel_dir"] == 1.0
    assert abs(m["move_30m"] - 40.0) < 1e-9          # 140 − 100
    assert abs(m["move_5m"] - (125 + 15 * 5 / 30 - 100)) < 1e-9
    assert m["max_up"] >= 41.0                        # 140 + 1 high wick
    # gap-fill: long at ref, adverse extreme over bars [T, T+1] = 100−95 = 5
    assert m["stop10_long_stopped"] is False
    # short at ref: adverse = max(high[T:T+1]) − 100 = 30
    assert m["stop20_short_stopped"] is True
    assert abs(m["stop20_short_loss_worst"] - 30.0) < 1e-9  # filled in the hole
    assert m["stop50_short_stopped"] is False


def test_causal_z_no_lookahead():
    from newslab.vintage import causal_z
    ev = pd.DataFrame(dict(
        family=["cpi"] * 12,
        ts_release_et=pd.date_range("2023-01-10", periods=12, freq="ME",
                                    tz=TZ_ET),
        surprise=[0.1, -0.1, 0.0, 0.2, -0.2, 0.1, 0.0, -0.1, 0.3, 0.0, 0.1, -0.3]))
    z = causal_z(ev)
    assert z.iloc[:8].isna().all()          # min-history gate
    # z_8 uses ONLY the first 8 surprises:
    hist = ev["surprise"].iloc[:8]
    expect = (0.3 - hist.mean()) / hist.std(ddof=1)
    assert abs(z.iloc[8] - expect) < 1e-9


def test_wilson_sane():
    from newslab.census import wilson
    lo, hi = wilson(30, 43)                  # 70% on a CPI-sized sample
    assert lo < 0.60 < hi                    # 43 events can't pin 60% vs 70%
    lo2, hi2 = wilson(150, 250)
    assert lo2 > 0.53                        # pooling is what buys certainty
