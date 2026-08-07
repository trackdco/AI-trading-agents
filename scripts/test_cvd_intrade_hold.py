#!/usr/bin/env python3
"""CVD as a PROSPECTIVE in-trade hold/bail signal (April 2026), addressing the
adversarial review's key critique of the first pass: H1 was concurrent (measured AT
the eventual MFE peak, unknowable in real time) rather than predictive.

The actionable reframe: at the moment a trade FIRST reaches +1R, you don't yet know
whether it will hold (winner) or reverse to a loss (giveback). If CVD flow measured
in the window ENDING at that +1R crossing separates the two populations, that's a
real, live-usable exit/trail decision rule -- "I'm up 1R, is the flow still with me?"

Replays every April trade minute-by-minute vs the 1m master to find each trade's
first +1R crossing, measures trailing signed CVD delta at that instant, and tests
whether it distinguishes trades that go on to win vs those that reverse to a loss.
Reports full sample AND a risk_pts>=5 floor (drops the stop-tick-noise crossings the
reviewers flagged), plus a day-blocked permutation test (the reviewers noted day-level
clustering shrinks effective n below the trade count).

    python -m scripts.test_cvd_intrade_hold
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MASTER = "data/reference/nq_1m_master.parquet"
TZ = "America/New_York"
RNG_SEED = 42
N_PERM = 20000


def perm_test(a, b, n=N_PERM):
    obs = a.mean() - b.mean()
    pool = np.concatenate([a, b]); n_a = len(a)
    rng = np.random.default_rng(RNG_SEED)
    diffs = np.array([(lambda p: p[:n_a].mean() - p[n_a:].mean())(rng.permutation(pool))
                       for _ in range(n)])
    return obs, (np.abs(diffs) >= np.abs(obs)).mean()


def day_blocked_perm(df, val, grp, n=N_PERM):
    """Permute the win/reverse LABEL at the day level (all trades on a day keep their
    day, labels shuffle across days) -- respects within-day clustering."""
    days = df.day.unique()
    obs = df[df[grp]].value_mean(val) if False else (df[df[grp] == 'winner'][val].mean()
                                                     - df[df[grp] == 'giveback'][val].mean())
    day_label = df.groupby("day")[grp].first()  # a day is winner-day if its first trade is; coarse
    rng = np.random.default_rng(RNG_SEED)
    cnt = 0
    for _ in range(n):
        perm_map = dict(zip(days, rng.permutation(day_label.values)))
        lab = df.day.map(perm_map)
        diff = df[lab == 'winner'][val].mean() - df[lab == 'giveback'][val].mean()
        if abs(diff) >= abs(obs):
            cnt += 1
    return obs, cnt / n


def main():
    t = pd.read_csv("output/april_trade_timestamps.csv",
                     parse_dates=["entry_ts", "exit_ts"])
    cvd = pd.read_csv("output/cvd_minute_apr2026.csv", index_col=0, parse_dates=True)
    bars = pd.read_parquet(MASTER).set_index("ts_event").sort_index()

    rows = []
    for _, r in t.iterrows():
        window = bars.loc[r.entry_ts:r.exit_ts]
        if window.empty:
            continue
        if r.dir == "long":
            exc = (window.high - r.entry) / r.risk_pts
        else:
            exc = (r.entry - window.low) / r.risk_pts
        crossed = exc[exc >= 1.0]
        if crossed.empty:
            continue                                  # never reached +1R (entry_miss-ish)
        cross_ts = crossed.index[0]
        sign = 1 if r.dir == "long" else -1
        # CVD flow in the 3 and 5 min ENDING at the crossing (info available at decision time)
        w3 = cvd.loc[cross_ts - pd.Timedelta(minutes=2):cross_ts]
        w5 = cvd.loc[cross_ts - pd.Timedelta(minutes=4):cross_ts]
        outcome = "winner" if r.win else "giveback"   # among +1R trades, loss == giveback by defn
        rows.append(dict(day=r.day, fill=r.fill, dir=r.dir, risk_pts=r.risk_pts,
                          cross_ts=cross_ts, outcome=outcome,
                          cvd_3m=(w3.delta * sign).sum(), cvd_5m=(w5.delta * sign).sum(),
                          dollars=r.dollars))
    df = pd.DataFrame(rows)
    print(f"{len(df)} April trades reached +1R "
          f"({(df.outcome=='winner').sum()} held to win, {(df.outcome=='giveback').sum()} reversed)")

    for floor, sub in [("FULL sample", df), ("risk_pts>=5 (drops stop-tick noise)",
                                              df[df.risk_pts >= 5])]:
        print(f"\n=== {floor}: n={len(sub)} "
              f"({(sub.outcome=='winner').sum()}W / {(sub.outcome=='giveback').sum()}GB) ===")
        for col in ["cvd_3m", "cvd_5m"]:
            w = sub[sub.outcome == "winner"][col].values
            g = sub[sub.outcome == "giveback"][col].values
            if len(w) < 2 or len(g) < 2:
                continue
            obs, p = perm_test(w, g)
            print(f"  {col}: winner mean {w.mean():+.0f} (med {np.median(w):+.0f}) | "
                  f"giveback mean {g.mean():+.0f} (med {np.median(g):+.0f}) | "
                  f"diff {obs:+.0f}, trade-perm p={p:.3f}")

    # day-blocked check on the full sample, cvd_5m
    if df.day.nunique() > 2:
        obs, p = day_blocked_perm(df, "cvd_5m", "outcome")
        print(f"\nday-blocked permutation (cvd_5m, full): diff {obs:+.0f}, p={p:.3f} "
              f"({df.day.nunique()} distinct trading days)")

    df.to_csv("output/cvd_intrade_1R.csv", index=False)

    # ---- DIVERGENCE framing (the read a pro reaches for first): over the entry->+1R
    # leg, did confirming flow BUILD with price, or lag (divergence)? Only trades with a
    # multi-bar leg (crossed +1R after >=2 min, not a single-bar stop-tick spike).
    tzc = cvd.index.tz
    t2 = t.copy()
    t2["entry_ts"] = t2.entry_ts.dt.tz_convert(tzc)
    t2["exit_ts"] = t2.exit_ts.dt.tz_convert(tzc)
    drows = []
    for _, r in t2.iterrows():
        w = bars.loc[r.entry_ts:r.exit_ts]
        if w.empty:
            continue
        exc = (w.high - r.entry) / r.risk_pts if r.dir == "long" else (r.entry - w.low) / r.risk_pts
        cr = exc[exc >= 1.0]
        if cr.empty:
            continue
        cross = cr.index[0].tz_convert(tzc)
        leg = cvd.loc[r.entry_ts:cross]
        if len(leg) < 2:
            continue
        sign = 1 if r.dir == "long" else -1
        signed = leg.delta * sign
        drows.append(dict(outcome="winner" if r.win else "giveback",
                           conf_flow_over_leg=signed.sum(),          # confirming flow, entry->+1R
                           fade_into_1R=signed.iloc[-1] - signed.max()))  # flow fading at the top?
    dd = pd.DataFrame(drows)
    print(f"\n=== DIVERGENCE framing (multi-bar legs only): n={len(dd)} "
          f"({(dd.outcome=='winner').sum()}W / {(dd.outcome=='giveback').sum()}GB) ===")
    for col in ["conf_flow_over_leg", "fade_into_1R"]:
        w = dd[dd.outcome == "winner"][col].values
        g = dd[dd.outcome == "giveback"][col].values
        if len(w) < 2 or len(g) < 2:
            continue
        obs, p = perm_test(w, g)
        print(f"  {col}: winner {w.mean():+.0f} (med {np.median(w):+.0f}) | "
              f"giveback {g.mean():+.0f} (med {np.median(g):+.0f}) | diff {obs:+.0f}, p={p:.3f}")


if __name__ == "__main__":
    main()
