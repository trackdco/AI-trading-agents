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
MIN_STOP = CFG["entry"]["min_stop_pts"]
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


# level columns -> confluence TYPE group (VWAP family collapses to one type, §3)
LEVEL_COLS = ["bb_ma", "dvwap0", "dvwap+1", "dvwap-1", "dvwap+2", "dvwap-2",
              "dvwap+3", "dvwap-3", "nyvwap0", "nyvwap+1", "nyvwap-1", "poc",
              "pdh", "pdl"]
LEVEL_GROUP = np.array([0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 3])  # BB, VWAPfam, POC, struct
N_GROUPS = 4


def _confluence(Lmat, pierced):
    """Per row: max # distinct TYPE-groups among pierced levels within TOL of an anchor."""
    n, K = Lmat.shape
    Lp = np.where(pierced, Lmat, np.nan)
    best = np.zeros(n, dtype=np.int16)
    for a in range(K):
        La = Lp[:, a]                                   # anchor value (nan if not pierced)
        anchored = ~np.isnan(La)
        if not anchored.any():
            continue
        within = pierced & (Lmat >= La[:, None]) & (Lmat <= (La + TOL)[:, None])
        confl = np.zeros(n, dtype=np.int16)
        for g in range(N_GROUPS):
            cols = np.where(LEVEL_GROUP == g)[0]
            confl += (within[:, cols].any(axis=1)).astype(np.int16)
        confl = np.where(anchored, confl, 0)
        best = np.maximum(best, confl)
    return best


def find_triggers(tf_df, base, htf, tf):
    """Vectorized level attach + rejection-block detection over the entry window."""
    m = pd.merge_asof(tf_df.sort_values("ts"), base.sort_values("ts"),
                      on="ts", direction="backward")
    m = pd.merge_asof(m, htf.sort_values("ts"), on="ts", direction="backward")
    hhmm = m["ts"].dt.strftime("%H:%M")
    m = m[(hhmm >= WIN_A) & (hhmm <= WIN_B)].reset_index(drop=True)
    if m.empty:
        return pd.DataFrame()
    dv, sd = m["dvwap"].values, m["dvwap_sd"].values
    ny, nysd = m["nyvwap"].values, m["nyvwap_sd"].values
    cols = {
        "bb_ma": m["bb_ma"].values,
        "dvwap0": dv, "dvwap+1": dv + sd, "dvwap-1": dv - sd,
        "dvwap+2": dv + 2 * sd, "dvwap-2": dv - 2 * sd,
        "dvwap+3": dv + 3 * sd, "dvwap-3": dv - 3 * sd,
        "nyvwap0": ny, "nyvwap+1": ny + nysd, "nyvwap-1": ny - nysd,
        "poc": m["poc"].values, "pdh": m["pdh"].values, "pdl": m["pdl"].values,
    }
    Lmat = np.column_stack([cols[c] for c in LEVEL_COLS])
    low, high, close = m["low"].values, m["high"].values, m["close"].values
    pierced_long = (Lmat > low[:, None]) & (Lmat < close[:, None])
    pierced_short = (Lmat < high[:, None]) & (Lmat > close[:, None])
    confl_long = _confluence(Lmat, pierced_long)
    confl_short = _confluence(Lmat, pierced_short)
    htf_arr = m["htf"].values
    # need: 2 with-trend, 3 counter-trend (§7)
    wt_long = htf_arr == "uptrend"
    wt_short = htf_arr == "downtrend"
    need_long = np.where(wt_long, 2, 3)
    need_short = np.where(wt_short, 2, 3)
    ok_long = confl_long >= need_long
    ok_short = confl_short >= need_short
    # pick direction with higher confluence when both fire
    direction = np.where(ok_long & (~ok_short | (confl_long >= confl_short)), "long",
                np.where(ok_short, "short", ""))
    valid = (direction != "")
    m = m[valid].copy()
    if m.empty:
        return pd.DataFrame()
    m["tf"] = tf
    m["direction"] = direction[valid]
    m["confluence"] = np.where(direction == "long", confl_long, confl_short)[valid]
    m["with_trend"] = np.where(direction == "long", wt_long, wt_short)[valid]
    m = m.rename(columns={"high": "trig_high", "low": "trig_low"})
    return m[["ts", "tf", "direction", "bb_ma", "trig_high", "trig_low", "close",
              "dvwap", "dvwap_sd", "poc", "pdh", "pdl", "nyvwap", "htf",
              "confluence", "with_trend"]]


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
    if sigs.empty:
        return pd.DataFrame()
    # pre-group 1m bars by calendar day (avoids scanning 1M rows per trigger)
    b = base1m.copy()
    b["cal"] = b["ts"].dt.tz_localize(None).dt.normalize()
    daybars = {}
    for cal, g in b.groupby("cal"):
        daybars[cal] = (g["ts"].values, g["low"].values.astype(float),
                        g["high"].values.astype(float), g["close"].values.astype(float))
    sigs = sigs.sort_values(["ts", "tf"], ascending=[True, False])  # MTF: highest tf first
    trades = []
    day_state = {}
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
        stop = (sig["trig_low"] - TICK) if d == "long" else (sig["trig_high"] + TICK)
        risk = abs(entry - stop)
        if risk < MIN_STOP:                         # realism floor (sub-noise wick stops)
            continue
        tgt = pick_target(sig, entry, stop)
        if tgt is None:
            continue
        if cal not in daybars:
            continue
        tsa, loa, hia, cla = daybars[cal]
        flat_t = np.datetime64(pd.Timestamp(f"{cal.date()} {CFG['session']['eod_flatten']}", tz=NY).tz_convert("UTC").tz_localize(None))
        start = np.searchsorted(tsa, np.datetime64(pd.Timestamp(ts).tz_convert("UTC").tz_localize(None)), side="right")
        filled = False; entry_fill = None
        exit_px = None; exit_reason = None; last_close = None
        for i in range(start, len(tsa)):
            if tsa[i].astype("datetime64[ns]") > flat_t:
                break
            lo, hi = loa[i], hia[i]; last_close = cla[i]
            if not filled:
                # limit entry: fills AT the limit price (no adverse slippage)
                if (d == "long" and lo <= entry) or (d == "short" and hi >= entry):
                    filled = True; entry_fill = entry
                elif (d == "long" and lo <= entry - TCANCEL) or \
                     (d == "short" and hi >= entry + TCANCEL):
                    exit_reason = "cancelled"; break
                continue
            # stop = market order (adverse slip); target = limit (fills at price). stop-first.
            if d == "long":
                if lo <= stop:
                    exit_px = stop - SLIP; exit_reason = "stop"; break
                if hi >= tgt:
                    exit_px = tgt; exit_reason = "target"; break
            else:
                if hi >= stop:
                    exit_px = stop + SLIP; exit_reason = "stop"; break
                if lo <= tgt:
                    exit_px = tgt; exit_reason = "target"; break
        if exit_reason == "cancelled" or not filled:
            continue
        if exit_px is None:  # flattened at EOD
            if last_close is None:
                continue
            exit_px = last_close; exit_reason = "eod"
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
    import os, time
    t0 = time.time()
    if os.path.exists("data/nq_1m.parquet"):
        base = pd.read_parquet("data/nq_1m.parquet")
    else:
        base = load_continuous(); base.to_parquet("data/nq_1m.parquet")
    print(f"  load {time.time()-t0:.0f}s  rows={len(base):,}")
    t0 = time.time()
    base = add_vwaps_poc(base)
    base = prior_levels(base)
    htf = htf_flag(base)
    print(f"  indicators {time.time()-t0:.0f}s")
    t0 = time.time()
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
