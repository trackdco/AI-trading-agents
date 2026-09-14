"""Mechanical trade-outcome scan on committed bars. Orchestrator tool, not an agent tool."""
import sys, json
sys.path.insert(0, "/Users/barbelldaddy/AI-trading-agents")
import pandas as pd
from scripts.build_l2_outcomes import load_bars
from src.htf_ma.levels import NY

def scan(sess_day_next, start_et, side, entry, stop, targets, limit_price=None, cancel_at=None, expiry_min=10,
         cash_open_flatten=False, trail_r_after_t1=0.5):
    """T13: a pre-market fill is resolved AT the 09:30 open when cash_open_flatten
    is set - flattened if red, breakeven if green - and can never run past it.
    He caught this missing on 2026-06-21.

    T23: once targets[0] prints, the 25% runner's stop moves into profit by
    trail_r_after_t1 R. This defaults ON because it is a standing rule, not a
    per-trade choice - it was silently absent for the first three days of the
    clean run and inflated every runner that would have been trailed out before
    targets[1]. A rule that has to be remembered per call is a rule that gets
    forgotten. The trail arms on the bar AFTER the T1 bar, since intrabar order
    is unknowable and arming it on the same bar would let a single candle both
    bank the target and stop the runner.
    """
    b = load_bars()
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b = b.set_index("mi").sort_index()[["open","high","low","close","volume"]]
    t0 = pd.Timestamp(f"{sess_day_next} {start_et}", tz=NY)
    w = b[(b.index >= t0) & (b.index <= t0 + pd.Timedelta(hours=6))]
    out = {"side": side, "entry": entry, "stop": stop, "targets": targets}
    # limit lifecycle
    if limit_price is not None:
        fill_t = None
        for t, r in w.iterrows():
            if t > t0 + pd.Timedelta(minutes=expiry_min):
                out["limit"] = "no_fill_expired"; break
            if cancel_at is not None:
                # cancel triggers on whichever side of the entry the level sits
                ran = (r.high >= cancel_at) if cancel_at > limit_price else (r.low <= cancel_at)
                hit = (r.high >= limit_price) if side == "short" else (r.low <= limit_price)
                if ran and not hit:
                    out["limit"] = f"no_fill_ran @{t.strftime('%H:%M')}"; break
            hit = (r.high >= limit_price) if side == "short" else (r.low <= limit_price)
            if hit:
                fill_t = t; out["limit"] = f"filled {limit_price} @{t.strftime('%H:%M')}"; break
        if fill_t is None and "limit" not in out: out["limit"] = "no_fill_expired"
        if fill_t is None: return out
        w = w[w.index >= fill_t]
    if cash_open_flatten:
        o = b[b.index == pd.Timestamp(f"{sess_day_next} 09:30", tz=NY)]
        if len(o):
            px = float(o.iloc[0].open)
            red = (px < entry) if side == "long" else (px > entry)
            out["T13"] = {"open_0930": px, "state": "red" if red else "green",
                          "action": "flatten" if red else "breakeven",
                          "exit": px if red else entry,
                          "r": round(((px - entry) / abs(entry - stop)) * (1 if side == "long" else -1), 3) if red else 0.0}
            w = w[w.index < pd.Timestamp(f"{sess_day_next} 09:30", tz=NY)]
    ev = []
    live_stop = stop
    t1_bar = None
    R = abs(entry - stop)
    for t, r in w.iterrows():
        # T23: arm the runner's trail from the bar after targets[0] printed
        if t1_bar is not None and t > t1_bar and trail_r_after_t1 is not None:
            live_stop = (entry - trail_r_after_t1 * R) if side == "short" else (entry + trail_r_after_t1 * R)
        if side == "short":
            if r.high >= live_stop:
                ev.append(("TRAIL" if live_stop != stop else "STOP", live_stop, t.strftime("%H:%M"))); break
            for i, tg in enumerate(targets):
                if r.low <= tg and not any(e[0]==f"T{i+1}" for e in ev):
                    ev.append((f"T{i+1}", tg, t.strftime("%H:%M")))
                    if i == 0: t1_bar = t
        else:
            if r.low <= live_stop:
                ev.append(("TRAIL" if live_stop != stop else "STOP", live_stop, t.strftime("%H:%M"))); break
            for i, tg in enumerate(targets):
                if r.high >= tg and not any(e[0]==f"T{i+1}" for e in ev):
                    ev.append((f"T{i+1}", tg, t.strftime("%H:%M")))
                    if i == 0: t1_bar = t
        if len(ev) and ev[-1][0] == f"T{len(targets)}": break
    out["events"] = ev
    # T13 describes what happens to a position STILL OPEN at 09:30. If the trade
    # already closed - stopped, trailed out, or finished its last target - the block
    # is not merely unused, it is misleading: it reports a breakeven or a flatten for
    # a position that no longer existed. Mark it so it cannot be read as the outcome.
    if "T13" in out and ev and ev[-1][0] in ("STOP", "TRAIL", f"T{len(targets)}"):
        out["T13"]["applied"] = False
        out["T13"]["why_not"] = (f"position already closed by {ev[-1][0]} at {ev[-1][2]}, "
                                 "before the 09:30 cash open - the trade never reached it")
    elif "T13" in out:
        out["T13"]["applied"] = True
    # MFE/MAE must be measured over the TRADE'S LIFE, not the whole scan window
    end_t = None
    if ev:
        last_lbl = ev[-1][2]
        for t in w.index:
            if t.strftime("%H:%M") == last_lbl:
                end_t = t
                break
    life = w if end_t is None else w[w.index <= end_t]
    out["life_end"] = (end_t.strftime("%H:%M") if end_t is not None else "window_end")
    out["mfe"] = round(float(entry - life.low.min()) if side=="short" else float(life.high.max() - entry), 2)
    out["mae"] = round(float(life.high.max() - entry) if side=="short" else float(entry - life.low.min()), 2)
    return out

if __name__ == "__main__":
    a = json.loads(sys.argv[1])
    print(json.dumps(scan(**a), indent=1))
