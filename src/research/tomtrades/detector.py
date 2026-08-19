"""The CBR detector: context gates -> shift trigger -> signals -> simulated trades.

Signal timing is deliberately conservative and is the thing ``test_no_lookahead`` pins:
a shift is confirmed on the CLOSE of the break bar, and the position opens at the OPEN
of the following bar. Nothing consults a bar that has not finished.

A note on C7 that the numbers depend on. His nested "fractal shift" is a shift on a
timeframe FINER than the trigger — he describes it on a 5-second chart. With 1-minute
data there is no finer timeframe, so ``c7`` here is an APPROXIMATION: a tighter-pivot
sub-shift inside the retrace zone of the outer 1m shift. His claimed 70% -> 88% uplift
cannot be honestly tested without sub-minute bars, and any C7 result must be reported
with that caveat attached.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import gates as G
from . import indicators as ind


@dataclass
class Context:
    """Everything the gates need, precomputed once per run."""

    df: pd.DataFrame
    state: pd.DataFrame
    atr_1h_min: pd.Series
    corr_ret: pd.Series | None = None
    yen_ret: pd.Series | None = None
    masks: dict[str, np.ndarray] = field(default_factory=dict)


def build_context(df: pd.DataFrame, cfg: dict,
                  dxy: pd.DataFrame | None = None,
                  yen: pd.DataFrame | None = None) -> Context:
    state = ind.hourly_run_state(df, cfg.get("tz_anchor", "UTC"))
    hourly = ind.resample_ohlcv(df, "1h")
    a = ind.atr(hourly, 24)
    atr_min = pd.Series(a.to_numpy(), index=hourly["ts_event"]).reindex(
        df["ts_event"], method="ffill")

    def aligned_return(other: pd.DataFrame | None, bars: int) -> pd.Series | None:
        if other is None:
            return None
        r = ind.rolling_return(other.set_index("ts_event")["close"], bars)
        return r.reindex(df["ts_event"], method="ffill")

    look = int(cfg["c4_correlation"]["lookback_min"])
    return Context(
        df=df, state=state, atr_1h_min=atr_min,
        corr_ret=aligned_return(dxy, look), yen_ret=aligned_return(yen, look),
    )


def compute_masks(ctx: Context, cfg: dict) -> dict[str, np.ndarray]:
    """Each gate as its own boolean array, so ablation is a dict lookup."""
    return {
        "session": G.session_mask(ctx.df, cfg["sessions"]),
        "c1": G.c1_range(ctx.df, cfg["c1_range"]),
        "c2": G.c2_overextension(ctx.state, ctx.atr_1h_min, cfg["c2_overextension"]),
        "c3": G.c3_clock(ctx.state, cfg["c3_clock"]),
        "c4": G.c4_correlation(ctx.state, ctx.corr_ret, ctx.yen_ret, cfg["c4_correlation"]),
        "c5": G.c5_aoi(ctx.df, ctx.state, ctx.atr_1h_min, cfg["c5_aoi"]),
    }


def _swing_tracks(df: pd.DataFrame, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Last confirmed swing high / low as of each bar (NaN until one exists)."""
    ph, pl = ind.pivot_flags(df["high"], df["low"], k)
    hv, lv = df["high"].to_numpy(), df["low"].to_numpy()
    n = len(df)
    last_h = np.full(n, np.nan)
    last_l = np.full(n, np.nan)
    ch = cl = np.nan
    ph_a, pl_a = ph.to_numpy(), pl.to_numpy()
    for i in range(n):
        if ph_a[i] and i - k >= 0:
            ch = hv[i - k]
        if pl_a[i] and i - k >= 0:
            cl = lv[i - k]
        last_h[i], last_l[i] = ch, cl
    return last_h, last_l


def detect(ctx: Context, cfg: dict, masks: dict[str, np.ndarray] | None = None) -> pd.DataFrame:
    """Scan for shifts where every enabled gate allows, and emit signal rows."""
    df, state = ctx.df, ctx.state
    masks = masks if masks is not None else compute_masks(ctx, cfg)
    allow = np.ones(len(df), dtype=bool)
    for m in masks.values():
        allow &= m

    c6 = cfg["c6_shift"]
    tick = float(cfg["instrument"]["tick_size"])
    k = int(c6["pivot_k"])
    win = int(c6["window_bars"])
    sweep_pad = int(c6["sweep_min_ticks"]) * tick
    w_required = c6["shape"] == "W_required"
    nested_mode = cfg["c7_nested"]["mode"]
    ex = cfg["execution"]
    retr_frac = float(ex["entry_retrace_frac"])
    buf = int(ex["stop_buffer_ticks"]) * tick
    stop_atr_max = float(c6["stop_atr_max"])

    last_h, last_l = _swing_tracks(df, k)
    h, low_, c = (df[x].to_numpy() for x in ("high", "low", "close"))
    ts = df["ts_event"].to_numpy()
    rd = state["run_dir"].to_numpy()
    disp = state["displacement"].to_numpy()
    hour_id = state["hour_id"].to_numpy()
    atr_a = np.nan_to_num(ctx.atr_1h_min.to_numpy(), nan=0.0)

    rows: list[dict] = []
    armed_dir = 0
    armed_i = -1
    armed_ext = np.nan
    armed_level = np.nan   # the swing level the sweep took out, for the autopsy
    pull = np.nan          # pullback extreme after the sweep (the W's middle)
    saw_lower_high = False

    for i in range(len(df)):
        # --- arm on a sweep of the last confirmed swing in the run direction ------
        if rd[i] == 1 and not np.isnan(last_h[i]) and h[i] > last_h[i] + sweep_pad:
            armed_dir, armed_i, armed_ext = -1, i, h[i]      # fade up-run => short
            armed_level = last_h[i]
            pull, saw_lower_high = np.nan, False
        elif rd[i] == -1 and not np.isnan(last_l[i]) and low_[i] < last_l[i] - sweep_pad:
            armed_dir, armed_i, armed_ext = 1, i, low_[i]    # fade down-run => long
            armed_level = last_l[i]
            pull, saw_lower_high = np.nan, False

        if armed_dir == 0 or i <= armed_i:
            continue
        if i - armed_i > win:                                 # sweep went stale
            armed_dir = 0
            continue

        # --- the W's middle leg --------------------------------------------------
        # Order matters: the break is tested against the pullback level established by
        # bars STRICTLY BEFORE i, then bar i updates that level. Testing against a level
        # that already includes bar i's own low can never fire, since close >= low.
        # The shape is: swept extreme -> pullback -> bounce (freezing the pullback) ->
        # break of the frozen level. Without the freeze the level keeps running away and
        # the pattern never completes.
        prior_pull = pull
        if armed_dir == -1:
            broke = saw_lower_high and not np.isnan(prior_pull) and c[i] < prior_pull
            if not w_required:
                broke = not np.isnan(last_l[i]) and c[i] < last_l[i]
            if not saw_lower_high:
                pull = low_[i] if np.isnan(pull) else min(pull, low_[i])
                if not np.isnan(pull) and h[i] > pull + sweep_pad and h[i] < armed_ext:
                    saw_lower_high = True          # bounce confirmed; pull is now frozen
            armed_ext = max(armed_ext, h[i])
        else:
            broke = saw_lower_high and not np.isnan(prior_pull) and c[i] > prior_pull
            if not w_required:
                broke = not np.isnan(last_h[i]) and c[i] > last_h[i]
            if not saw_lower_high:
                pull = h[i] if np.isnan(pull) else max(pull, h[i])
                if not np.isnan(pull) and low_[i] < pull - sweep_pad and low_[i] > armed_ext:
                    saw_lower_high = True
            armed_ext = min(armed_ext, low_[i])

        if not broke:
            continue
        if not allow[i] or disp[i] <= 0:
            armed_dir = 0
            continue

        # --- his own "it would be a pretty big stop loss" tell -------------------
        stop = armed_ext + buf * (1 if armed_dir == -1 else -1)
        entry_ref = c[i]
        risk = abs(stop - entry_ref)
        if risk <= 0 or (atr_a[i] > 0 and risk > stop_atr_max * atr_a[i]):
            armed_dir = 0
            continue

        # --- C7 approximation: a tighter sub-shift inside the retrace zone -------
        nested = False
        if nested_mode != "off":
            lo_i = max(armed_i, i - win)
            seg = slice(lo_i, i + 1)
            sub_h, sub_l = ind.pivot_flags(df["high"].iloc[seg], df["low"].iloc[seg], 1)
            nested = bool(sub_h.sum() >= 1 and sub_l.sum() >= 1)
            if nested_mode == "gate" and not nested:
                armed_dir = 0
                continue

        # Shape descriptors, recorded for the autopsy. These are annotations only —
        # nothing above reads them, so adding a field can never move a signal.
        break_level = prior_pull if w_required else (
            last_l[i] if armed_dir == -1 else last_h[i])
        rows.append(
            {
                "signal_ts": ts[i],
                "direction": armed_dir,
                "entry_ts": ts[i + 1] if i + 1 < len(df) else pd.NaT,
                "entry_idx": i + 1,
                "signal_idx": i,
                "entry_ref_close": entry_ref,
                "stop": stop,
                "risk": risk,
                "hour_id": hour_id[i],
                "minute_of_hour": state["minute_of_hour"].to_numpy()[i],
                "run_displacement": disp[i],
                "nested": nested,
                "retrace_target_frac": retr_frac,
                "armed_idx": armed_i,
                "bars_since_arm": i - armed_i,
                "sweep_depth": abs(armed_ext - armed_level),
                "break_level": break_level,
                "break_dist": abs(entry_ref - break_level),
                "pattern_ext": armed_ext,
            }
        )
        armed_dir = 0

    sig = pd.DataFrame(rows)
    if sig.empty:
        return sig
    return sig[sig["entry_idx"] < len(df)].reset_index(drop=True)


def simulate(df: pd.DataFrame, signals: pd.DataFrame, cfg: dict,
             be_trigger_r: float | None = None) -> pd.DataFrame:
    """Fill at next-bar open, then walk forward to stop or target.

    When a bar's range contains both the stop and the target, the stop is assumed to
    have been hit first. That is the pessimistic reading and the only defensible one
    without sub-minute data — the alternative flatters every result.

    ``be_trigger_r`` moves the stop to the entry price once the trade has been that far
    in profit. It defaults to off, so the baseline is untouched; the autopsy uses it to
    price one specific exit-geometry change rather than guess at it from excursions.
    Arming happens at the END of the bar that reaches the trigger, so a bar that both
    reaches the trigger and returns to the old stop is still a full loss.
    """
    if signals.empty:
        return signals
    ex = cfg["execution"]
    o, h, low_, c = (df[x].to_numpy() for x in ("open", "high", "low", "close"))
    ts = df["ts_event"].to_numpy()
    state = ind.hourly_run_state(df, cfg.get("tz_anchor", "UTC"))
    hour_open_px = pd.Series(o).groupby(state["hour_id"].to_numpy()).transform("first").to_numpy()
    max_hold = 240
    out = []
    skipped_target_passed = 0
    for r in signals.itertuples(index=False):
        i0 = int(r.entry_idx)
        entry = o[i0]
        d = int(r.direction)
        stop = float(r.stop)
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        if ex["target_mode"] == "fixed_rr":
            target = entry + d * float(ex["fixed_rr"]) * risk
        else:
            # "50% of the hourly candle extension" — the impulse runs hour_open ->
            # run EXTREME, not hour_open -> entry. Measuring it from entry puts the
            # target on the losing side whenever price has already retraced past the
            # hour open before the fill, which silently books losses as "target" exits.
            ho = hour_open_px[i0]
            run_dir = -d                                   # the trade fades the run
            extreme = ho + run_dir * float(r.run_displacement)
            target = extreme - run_dir * float(ex["target_impulse_frac"]) * abs(extreme - ho)
            # if price already reached the 50% level before the fill there is nothing
            # left to capture; taking the trade would be a lookahead-flavoured freebie
            if (d < 0 and target >= entry) or (d > 0 and target <= entry):
                skipped_target_passed += 1
                continue
        exit_px, exit_ts, reason = np.nan, pd.NaT, "timeout"
        mfe = mae = 0.0                        # excursions in R, post-entry anatomy
        live_stop = stop
        for j in range(i0, min(i0 + max_hold, len(df))):
            fav = (entry - low_[j]) if d < 0 else (h[j] - entry)
            adv = (h[j] - entry) if d < 0 else (entry - low_[j])
            mfe, mae = max(mfe, fav / risk), max(mae, adv / risk)
            hit_stop = (h[j] >= live_stop) if d < 0 else (low_[j] <= live_stop)
            hit_tgt = (low_[j] <= target) if d < 0 else (h[j] >= target)
            if hit_stop:                       # pessimistic tie-break
                exit_px, exit_ts = live_stop, ts[j]
                reason = "stop" if live_stop == stop else "breakeven"
                break
            if hit_tgt:
                exit_px, exit_ts, reason = target, ts[j], "target"
                break
            if be_trigger_r is not None and fav / risk >= be_trigger_r:
                live_stop = entry              # armed only for SUBSEQUENT bars
        else:
            j = min(i0 + max_hold, len(df)) - 1
            exit_px, exit_ts = c[j], ts[j]
        pnl_r = d * (exit_px - entry) / risk
        out.append({**r._asdict(), "entry": entry, "target": target, "exit_px": exit_px,
                    "exit_ts": exit_ts, "exit_reason": reason, "pnl_r": pnl_r,
                    "hold_bars": j - i0 + 1, "mfe_r": mfe, "mae_r": mae,
                    "rr_at_entry": abs(target - entry) / risk})
    if skipped_target_passed:
        # surfaced rather than silently dropped: a large count means the entry
        # is arriving after the move it was meant to fade
        print(f"[simulate] skipped {skipped_target_passed} signals whose 50% "
              f"target was already reached before the fill", flush=True)
    trades = pd.DataFrame(out)
    if trades.empty:
        return trades
    cap = int(cfg["risk"]["max_trades_per_day"])       # [A] "max 2-3 trades per day"
    if cap:
        day = pd.to_datetime(trades["entry_ts"]).dt.tz_convert("America/New_York").dt.date
        trades = trades.assign(_d=day)
        trades = trades.groupby("_d", group_keys=False).head(cap).drop(columns="_d")
    return trades.reset_index(drop=True)
