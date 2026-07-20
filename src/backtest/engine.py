"""First-pass NQ backtester (pre-parity-gate, pre-calibration).

Implements the core of strategy-definition-v1.0.md with DOCUMENTED starting
values only (no tuning). Config: W1 window / E1 entry / V0 management (Step 8
defaults). Simplifications are logged in the final report; this is a smoke test,
NOT a validated result.

No-lookahead: indicators are developing (cumulative from anchor); signals use
CLOSED bars only; entry orders activate on the NEXT 1m bar.
"""
import numpy as np, pandas as pd, yaml
from src.engine.data import load_continuous, NY

CFG = yaml.safe_load(open("config/strategy.yaml"))
TICK = CFG["instrument"]["tick"]
PV = CFG["instrument"]["point_value_nq"]
TOL = CFG["cluster"]["tolerance_pts"]
F = CFG["target"]["front_run_f_pts"]
RRFLOOR = CFG["target"]["rr_floor"]
TCANCEL = CFG["entry"]["t_cancel_pts"]
SLIP = CFG["costs"]["slippage_pts"]
COMM_PTS = 2 * CFG["costs"]["commission_per_side_usd"] / PV
WIN_A, WIN_B = CFG["session"]["w1_start"], CFG["session"]["w1_end"]
MAXTD = CFG["vault"]["max_trades_per_day"]
HALT_L = CFG["vault"]["daily_halt_losses"]
HALT_R = CFG["vault"]["daily_halt_r"]


def session_date(ts):
    # CME session starts 18:00 ET prev day -> shift +6h so a session maps to one date
    return (ts + pd.Timedelta(hours=6)).dt.tz_localize(None).dt.normalize()


def add_vwaps_poc(df):
    df = df.copy()
    df["sd_date"] = session_date(df["ts"])
    df["cal_date"] = df["ts"].dt.tz_localize(None).dt.normalize()
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    v = df["volume"].clip(lower=1e-9)
    # daily VWAP (18:00 anchor) developing bands
    g = df.groupby("sd_date")
    cv = g["volume"].cumsum()
    cvp = (tp * v).groupby(df["sd_date"]).cumsum()
    cvp2 = (tp * tp * v).groupby(df["sd_date"]).cumsum()
    df["dvwap"] = cvp / cv
    var = (cvp2 / cv) - df["dvwap"] ** 2
    df["dvwap_sd"] = np.sqrt(var.clip(lower=0))
    # NY session VWAP (09:30 anchor), NaN before
    cash = df["ts"].dt.strftime("%H:%M") >= "09:30"
    intra = df["ts"].dt.strftime("%H:%M") <= "15:59"
    nymask = cash & intra
    nd = df.where(nymask)
    cvn = (nd["volume"]).groupby(df["cal_date"]).cumsum()
    cvpn = (tp * v).where(nymask).groupby(df["cal_date"]).cumsum()
    cvpn2 = (tp * tp * v).where(nymask).groupby(df["cal_date"]).cumsum()
    df["nyvwap"] = cvpn / cvn
    nvar = (cvpn2 / cvn) - df["nyvwap"] ** 2
    df["nyvwap_sd"] = np.sqrt(nvar.clip(lower=0))
    # developing daily POC (1-pt bins), running argmax per session
    poc = np.full(len(df), np.nan)
    binvol = {}
    cur_sd = None
    best_bin = None
    best_vol = -1.0
    sd = df["sd_date"].values
    price = df["close"].values
    vol = df["volume"].values
    for i in range(len(df)):
        if sd[i] != cur_sd:
            binvol = {}; cur_sd = sd[i]; best_bin = None; best_vol = -1.0
        b = round(price[i])
        nv = binvol.get(b, 0.0) + vol[i]
        binvol[b] = nv
        if nv >= best_vol:
            best_vol = nv; best_bin = b
        poc[i] = best_bin
    df["poc"] = poc
    return df


def prior_levels(df):
    """Prior-day high/low per calendar day (developing = uses only prior days)."""
    day = df["cal_date"]
    hi = df.groupby(day)["high"].max()
    lo = df.groupby(day)["low"].min()
    pdh = hi.shift(1); pdl = lo.shift(1)
    m = pd.DataFrame({"cal_date": hi.index, "pdh": pdh.values, "pdl": pdl.values})
    return df.merge(m, on="cal_date", how="left")


def resample_tf(df1m, tf):
    idx = df1m.set_index("ts")
    o = idx["open"].resample(f"{tf}min", label="right", closed="right").first()
    h = idx["high"].resample(f"{tf}min", label="right", closed="right").max()
    l = idx["low"].resample(f"{tf}min", label="right", closed="right").min()
    c = idx["close"].resample(f"{tf}min", label="right", closed="right").last()
    v = idx["volume"].resample(f"{tf}min", label="right", closed="right").sum()
    r = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}).dropna()
    r["bb_ma"] = r["close"].rolling(20).mean()
    return r.reset_index()


def htf_flag(df1m):
    """15m trend/range: uptrend if close>SMA20 and SMA20 rising; sym for down; else range."""
    r = resample_tf(df1m, 15)
    sma = r["close"].rolling(20).mean()
    slope = sma.diff()
    flag = np.where((r["close"] > sma) & (slope > 0), "uptrend",
            np.where((r["close"] < sma) & (slope < 0), "downtrend", "range"))
    return pd.DataFrame({"ts": r["ts"], "htf": flag})


def find_triggers(tf_df, base, htf, tf):
    """Vectorized level attach + windowed scan for rejection blocks."""
    m = pd.merge_asof(tf_df.sort_values("ts"), base.sort_values("ts"),
                      on="ts", direction="backward")
    m = pd.merge_asof(m, htf.sort_values("ts"), on="ts", direction="backward")
    hhmm = m["ts"].dt.strftime("%H:%M")
    win = (hhmm >= WIN_A) & (hhmm <= WIN_B)
    m = m[win].copy()
    out = []
    for row in m.itertuples(index=False):
        levels = {}
        if not np.isnan(row.bb_ma): levels["BB"] = row.bb_ma
        if not np.isnan(row.dvwap):
            levels["dVWAP"] = row.dvwap
            for n in (1, 2, 3):
                levels[f"dVWAP+{n}"] = row.dvwap + n * row.dvwap_sd
                levels[f"dVWAP-{n}"] = row.dvwap - n * row.dvwap_sd
        if not np.isnan(row.nyvwap):
            levels["nyVWAP"] = row.nyvwap
            levels["nyVWAP+1"] = row.nyvwap + row.nyvwap_sd
            levels["nyVWAP-1"] = row.nyvwap - row.nyvwap_sd
        if not np.isnan(row.poc): levels["POC"] = row.poc
        if len(levels) < 2:
            continue
        lv = sorted(levels.items(), key=lambda x: x[1])
        vals = np.array([x[1] for x in lv])
        # LONG: levels in (low, close), wick pierced from below, closed above
        for direction, cond in (("long", (vals > row.low) & (vals < row.close)),
                                 ("short", (vals < row.high) & (vals > row.close))):
            idx = np.where(cond)[0]
            if len(idx) < 2:
                continue
            sub = vals[idx]
            # tightest window of >=2 levels within tolerance
            best = None
            for a in range(len(sub)):
                b = a
                while b + 1 < len(sub) and sub[b + 1] - sub[a] <= TOL:
                    b += 1
                if b - a + 1 >= 2 and (best is None or (b - a) > (best[1] - best[0])):
                    best = (a, b)
            if best is None:
                continue
            names = [lv[idx[k]][0] for k in range(best[0], best[1] + 1)]
            clv = sub[best[0]:best[1] + 1]
            types = set(n.split("+")[0].split("-")[0].replace("dVWAP", "VWAPfam")
                        .replace("nyVWAP", "VWAPfam") for n in names)
            confl = len(types)
            with_trend = (direction == "long" and row.htf == "uptrend") or \
                         (direction == "short" and row.htf == "downtrend")
            need = CFG["cluster"]["min_confluence_with_trend"] if with_trend \
                else CFG["cluster"]["min_confluence_counter"]
            if confl < need:
                continue
            out.append(dict(ts=row.ts, tf=tf, direction=direction, bb_ma=row.bb_ma,
                            trig_high=row.high, trig_low=row.low, close=row.close,
                            dvwap=row.dvwap, dvwap_sd=row.dvwap_sd, poc=row.poc,
                            pdh=row.pdh, pdl=row.pdl, nyvwap=row.nyvwap,
                            htf=row.htf, confluence=confl, with_trend=with_trend,
                            cluster_lo=float(clv.min()), cluster_hi=float(clv.max())))
            break
    return pd.DataFrame(out)


def pick_target(sig, entry, stop):
    risk = abs(entry - stop)
    menu = [sig["dvwap"], sig["dvwap"] + sig["dvwap_sd"], sig["dvwap"] - sig["dvwap_sd"],
            sig["dvwap"] + 2 * sig["dvwap_sd"], sig["dvwap"] - 2 * sig["dvwap_sd"],
            sig["poc"], sig["pdh"], sig["pdl"], sig["nyvwap"]]
    menu = [x for x in menu if x is not None and not np.isnan(x)]
    if sig["direction"] == "long":
        cands = sorted([x for x in menu if x > entry + risk * RRFLOOR])
        if not cands: return None
        return cands[0] - F
    else:
        cands = sorted([x for x in menu if x < entry - risk * RRFLOOR], reverse=True)
        if not cands: return None
        return cands[0] + F


def backtest(base1m, sigs):
    idx = base1m.set_index("ts")
    path_lo = idx["low"]; path_hi = idx["high"]
    sigs = sigs.sort_values(["ts", "tf"], ascending=[True, False])  # MTF: highest tf first
    trades = []
    day_state = {}  # cal_date -> dict(count, losses, r)
    open_until = pd.Timestamp.min.tz_localize(NY)
    for sig in sigs.to_dict("records"):
        ts = sig["ts"]
        cal = ts.tz_localize(None).normalize()
        st = day_state.setdefault(cal, dict(count=0, losses=0, r=0.0))
        if ts <= open_until:                       # one position at a time
            continue
        if st["count"] >= MAXTD:                    # vault: max trades/day
            continue
        if st["losses"] >= HALT_L or st["r"] <= HALT_R:  # vault: daily halt
            continue
        d = sig["direction"]
        entry = sig["bb_ma"]                        # E1
        if np.isnan(entry):
            continue
        # entry must be reachable in trigger direction (limit is a pullback)
        stop = (sig["trig_low"] - TICK) if d == "long" else (sig["trig_high"] + TICK)
        risk = abs(entry - stop)
        if risk < 2 * TICK:
            continue
        tgt = pick_target(sig, entry, stop)
        if tgt is None:
            continue
        # simulate from next 1m bar to EOD flatten
        day_bars = idx.loc[(idx.index > ts) & (idx.index.normalize() == cal)]
        flat_t = pd.Timestamp(f"{cal.date()} {CFG['session']['eod_flatten']}", tz=NY)
        filled = False; fill_i = None
        exit_px = None; exit_reason = None
        for t, bar in day_bars.iterrows():
            if t > flat_t:
                break
            lo, hi = bar["low"], bar["high"]
            if not filled:
                # limit fill
                if (d == "long" and lo <= entry) or (d == "short" and hi >= entry):
                    filled = True
                    # cancel check happens before fill each bar; fill at limit + slippage
                    entry_fill = entry + (SLIP if d == "long" else -SLIP)
                elif (d == "long" and lo <= entry - TCANCEL) or \
                     (d == "short" and hi >= entry + TCANCEL):
                    exit_reason = "cancelled"; break
                continue
            # in trade (V0: no management). stop-first on same-bar ambiguity.
            if d == "long":
                if lo <= stop:
                    exit_px = stop - SLIP; exit_reason = "stop"; break
                if hi >= tgt:
                    exit_px = tgt - SLIP; exit_reason = "target"; break
            else:
                if hi >= stop:
                    exit_px = stop + SLIP; exit_reason = "stop"; break
                if lo <= tgt:
                    exit_px = tgt + SLIP; exit_reason = "target"; break
        if exit_reason == "cancelled" or not filled:
            continue
        if exit_px is None:  # flattened at EOD
            last = day_bars.loc[day_bars.index <= flat_t]
            if last.empty:
                continue
            exit_px = last["close"].iloc[-1]; exit_reason = "eod"
        pnl_pts = (exit_px - entry_fill) if d == "long" else (entry_fill - exit_px)
        pnl_pts -= COMM_PTS
        r = pnl_pts / risk
        st["count"] += 1; st["r"] += r
        if r < 0: st["losses"] += 1
        # block new entries until this one is closed (approx: rest of considered bar span)
        open_until = ts + pd.Timedelta(minutes=int(sig["tf"]))
        trades.append(dict(ts=ts, date=cal.date(), tf=sig["tf"], direction=d,
                           htf=sig["htf"], with_trend=sig["with_trend"],
                           confluence=sig["confluence"], entry=round(entry_fill, 2),
                           stop=round(stop, 2), target=round(tgt, 2),
                           exit=round(exit_px, 2), reason=exit_reason,
                           risk_pts=round(risk, 2), pnl_pts=round(pnl_pts, 2),
                           r=round(r, 3)))
    return pd.DataFrame(trades)


def run():
    base = load_continuous()
    base = add_vwaps_poc(base)
    base = prior_levels(base)
    htf = htf_flag(base)
    all_sig = []
    for tf in CFG["indicators"]["entry_tfs"]:
        tfd = resample_tf(base, tf)
        s = find_triggers(tfd, base[["ts", "dvwap", "dvwap_sd", "nyvwap", "nyvwap_sd",
                                     "poc", "pdh", "pdl"]], htf, tf)
        if len(s):
            all_sig.append(s)
        print(f"  tf={tf}m: {len(s)} rejection-block triggers")
    sigs = pd.concat(all_sig, ignore_index=True) if all_sig else pd.DataFrame()
    trades = backtest(base, sigs)
    trades.to_csv("output/trades.csv", index=False)
    return trades


if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)
    t = run()
    print(f"\nTOTAL TRADES: {len(t)}")
    print(t.to_string() if len(t) < 40 else t.tail(20).to_string())
