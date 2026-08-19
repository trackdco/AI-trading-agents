"""Opening-range-breakout engine for GC, v3 parity.

Implements the M3-base skeleton (close-outside entry, next-candle-open fill,
opposite-side stop, R-multiple target, forced flat, one trade/day) plus every v3
mechanism from `references/tv-findings.md`. All v3 additions default OFF so that
`Config()` is the v1-exact configuration the calibration diff needs.

Conventions, stated because they decide the numbers:

* **Intrabar resolution is 1-minute.** Entry-timeframe candles decide the *signal*;
  the exit walk always runs on 1m bars. Where a single 1m bar could have hit both the
  stop and the target, the stop wins (`optimistic=False`). TradingView's emulator does
  the opposite on 15m bars, which is the single largest expected divergence class.
* **Everything armed on a touch arms for SUBSEQUENT bars only.** The ratchet cannot
  fill inside the bar that triggered it, because 1m OHLC does not order its own extremes.
* **Daily context is prior-day-shifted.** ATR and the prior-day close are computed from
  sessions strictly before the one being traded; `assert` guards this rather than trusting it.
* **R is measured on realised risk** — entry to stop *after* any cap, so a capped trade's
  -1R is a smaller dollar loss, which is the entire point of the cap.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

NY = "America/New_York"
POINT_USD = 100.0     # GC: 1.00 point = $100/contract
TICK = 0.10           # GC min tick = $10
TICK_USD = 10.0


@dataclass(frozen=True)
class Config:
    """v1-exact by default. Every v3 mechanism is opt-in."""
    # --- v1 core -----------------------------------------------------------
    anchor: str = "09:30"          # ET; sweep {08:20, 09:30, 03:00}
    or_minutes: int = 15
    entry_tf: int = 15             # minutes per entry candle
    target_r: float = 1.5
    flat_minutes: int = 240
    flat_from_anchor: bool = False  # True = flat at anchor+N (Pine v3.1), False = entry+N
    max_trades_per_day: int = 1
    cutoff: str | None = None      # e.g. "12:00" — no ENTRY after this candle opens
    slip_ticks: float = 0.0        # per side
    commission_usd: float = 0.0    # round turn
    optimistic: bool = False       # True = target wins a both-touched bar (TV-like)
    exit_tf: int = 1               # minutes per EXIT-walk bar; 15 emulates a TV 15m chart

    # --- v3 (a) hard risk cap ---------------------------------------------
    risk_mode: str = "off"         # off | cap | skip
    # Point caps are NOT comparable across eras: gold's opening range quadrupled between
    # 2023 and 2026, so a 30-pt cap binds 0.6% of 2023-25 trades and 18.5% of 2026 days.
    # The ATR and %-of-price forms are scale-free and fire at a stable rate in both.
    # Whichever of the three are set, the tightest binds.
    max_risk_pts: float | None = None
    max_risk_atr: float | None = None    # x prior-day ATR14
    max_risk_pct: float | None = None    # % of entry price

    # --- v3 (b) profit ratchet --------------------------------------------
    ratchet: bool = False
    ratchet_trigger_r: float = 1.0
    ratchet_lock_r: float = 0.25

    # --- v3 (c) time stop --------------------------------------------------
    time_stop_min: int | None = None   # e.g. 90
    time_stop_r: float = 0.5           # scratch if below this R at the deadline

    # --- v3 (d)(e)(f) gates -------------------------------------------------
    vwap_gate: bool = False        # long only above session VWAP, short only below
    pdc_gate: bool = False         # long only above prior-day close, short only below
    skip_weekdays: tuple = ()      # e.g. (0,) to skip Monday

    # --- v3 (g) breakers ----------------------------------------------------
    daily_stop_r: float | None = None    # e.g. -2.0
    weekly_stop_r: float | None = None   # e.g. -4.0
    consec_loss_halt: int | None = None  # e.g. 3; counter resets WEEKLY

    # --- range filter (M3-base), already ATR-relative -------------------------
    atr_lo: float | None = None    # min OR width as a multiple of prior-day ATR
    atr_hi: float | None = None
    atr_days: int = 14

    # --- Crabel contraction gate (the original ORB precondition) --------------
    crabel: str | None = None      # nr4 | nr7 | inside | idnr4 — read on the PRIOR day

    # --- participation on the breakout bar ------------------------------------
    min_relvol: float | None = None    # breakout-bar volume / slot-matched 14-day mean
    min_bar_atr: float | None = None   # breakout-bar range / ATR14 of the entry TF

    def label(self) -> str:
        bits = [f"{self.anchor}", f"OR{self.or_minutes}", f"tf{self.entry_tf}",
                f"{self.target_r}R", f"flat{self.flat_minutes}"]
        if self.risk_mode != "off":
            bits.append(f"{self.risk_mode}{self.max_risk_pts:g}")
        if self.ratchet:
            bits.append(f"ratchet{self.ratchet_trigger_r:g}->{self.ratchet_lock_r:g}")
        if self.time_stop_min:
            bits.append(f"ts{self.time_stop_min}@{self.time_stop_r:g}")
        for f_, n in ((self.vwap_gate, "vwap"), (self.pdc_gate, "pdc")):
            if f_:
                bits.append(n)
        if self.skip_weekdays:
            bits.append("skip" + "".join("MTWRF"[d] for d in self.skip_weekdays))
        if self.consec_loss_halt:
            bits.append(f"cons{self.consec_loss_halt}")
        if self.slip_ticks:
            bits.append(f"slip{self.slip_ticks:g}t")
        return " · ".join(bits)


# ---------------------------------------------------------------------------
# data prep
# ---------------------------------------------------------------------------

def load_gc(path: str = "data/gc_1m.parquet") -> pd.DataFrame:
    b = pd.read_parquet(path)
    b = b[["ts_event", "open", "high", "low", "close", "volume"]].copy()
    b["ts_event"] = pd.to_datetime(b.ts_event)
    if b.ts_event.dt.tz is None:
        b["ts_event"] = b.ts_event.dt.tz_localize("UTC")
    b["ts_event"] = b.ts_event.dt.tz_convert(NY)
    return prep(b.sort_values("ts_event").reset_index(drop=True))


def prep(b: pd.DataFrame) -> pd.DataFrame:
    """Attach calendar date, minute-of-day, CME session id and session VWAP."""
    ts = b.ts_event
    b = b.copy()
    b["cal"] = ts.dt.normalize()
    b["tmin"] = ts.dt.hour * 60 + ts.dt.minute
    b["dow"] = ts.dt.dayofweek
    # CME session: rolls at 18:00 ET, so an evening bar belongs to the NEXT calendar day
    b["sess"] = (ts + pd.Timedelta(hours=6)).dt.normalize()
    tp = (b.high + b.low + b.close) / 3.0
    g = b.groupby("sess", sort=False)
    pv = (tp * b.volume).groupby(b.sess).cumsum()
    vv = b.volume.groupby(b.sess).cumsum()
    b["vwap"] = np.where(vv > 0, pv / vv.replace(0, np.nan), tp)
    return b


def daily_context(b: pd.DataFrame, atr_days: int) -> pd.DataFrame:
    """Prior-day-shifted daily stats. Row `cal` carries values known BEFORE that day."""
    d = (b.groupby("cal")
           .agg(hi=("high", "max"), lo=("low", "min"), close=("close", "last"))
           .sort_index())
    tr = pd.concat([d.hi - d.lo,
                    (d.hi - d.close.shift()).abs(),
                    (d.lo - d.close.shift()).abs()], axis=1).max(axis=1)
    out = pd.DataFrame(index=d.index)
    out["pdc"] = d.close.shift(1)                       # prior day's close
    out["atr"] = tr.rolling(atr_days).mean().shift(1)   # ATR through YESTERDAY

    # Crabel contraction, all read on the PRIOR day so they are known at today's open.
    rng = d.hi - d.lo
    nr4 = rng == rng.rolling(4).min()
    nr7 = rng == rng.rolling(7).min()
    ins = (d.hi < d.hi.shift(1)) & (d.lo > d.lo.shift(1))
    out["nr4"] = nr4.shift(1).fillna(False)
    out["nr7"] = nr7.shift(1).fillna(False)
    out["inside"] = ins.shift(1).fillna(False)
    out["idnr4"] = (ins & nr4).shift(1).fillna(False)
    return out


# ---------------------------------------------------------------------------
# the signal interface
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Candidate:
    """One trade candidate. This is the ONLY thing a replacement signal must produce.

    Everything downstream — fills, the risk cap, the ratchet, the time stop, the forced
    flat, the breakers and the cost model — is signal-agnostic and works unchanged.

    signal_tmin  minute-of-day of the bar whose CLOSE produced the signal
    fill_tmin    minute-of-day of the bar whose OPEN fills it (no same-bar fills)
    direction    +1 long, -1 short
    stop_ref     price the protective stop sits at BEFORE any cap is applied
    meta         free-form, copied onto the trade row for later analysis
    """
    signal_tmin: int
    fill_tmin: int
    direction: int
    stop_ref: float
    meta: dict = field(default_factory=dict)


def orb_candidates(day: pd.DataFrame, cfg: Config, row, feat, anchor: int,
                   or_end: int) -> list[Candidate]:
    """The opening-range-breakout generator. RETIRED as an edge (see the skill's
    references/null-result.md); kept as the reference implementation of the interface."""
    o = day[(day.tmin >= anchor) & (day.tmin < or_end)]
    if len(o) < cfg.or_minutes:
        return []                                     # incomplete opening range
    or_hi, or_lo = float(o.high.max()), float(o.low.min())
    width = or_hi - or_lo
    if width <= 0:
        return []

    atr = None if row is None else row.atr
    if cfg.atr_lo is not None or cfg.atr_hi is not None:
        if atr is None or not np.isfinite(atr):
            return []
        if cfg.atr_lo is not None and width < cfg.atr_lo * atr:
            return []
        if cfg.atr_hi is not None and width > cfg.atr_hi * atr:
            return []

    out = []
    for _, c in _tf_candles(day, or_end, cfg.entry_tf).iterrows():
        if c.close > or_hi:
            d_ = 1
        elif c.close < or_lo:
            d_ = -1
        else:
            continue
        if feat is not None and (cfg.min_relvol is not None or cfg.min_bar_atr is not None):
            f = feat.get(int(c.tmin))
            if f is None:
                continue
            rv, ra = f
            if cfg.min_relvol is not None and not (rv >= cfg.min_relvol):
                continue
            if cfg.min_bar_atr is not None and not (ra >= cfg.min_bar_atr):
                continue
        out.append(Candidate(int(c.tmin), int(c.tmin) + cfg.entry_tf, d_,
                             or_lo if d_ > 0 else or_hi,
                             {"or_hi": or_hi, "or_lo": or_lo, "or_width": width}))
    return out


# ---------------------------------------------------------------------------
# the backtest
# ---------------------------------------------------------------------------

def entry_frame(bars: pd.DataFrame, anchor: int, tf: int) -> pd.DataFrame:
    """Every entry-timeframe candle in the sample, with participation features.

    Both features are strictly backward-looking: the ATR and the volume baseline are
    shifted so the bar being judged is never part of its own benchmark. The volume
    baseline is SLOT-MATCHED — the 10:00 bar is compared with the last 14 10:00 bars, not
    with the session average — because intraday volume has a shape and comparing a bar to
    a flat mean would just rediscover the time of day.
    """
    d = bars[bars.tmin >= anchor].copy()
    d["slot"] = (d.tmin - anchor) // tf
    c = (d.groupby(["cal", "slot"], sort=True)
           .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                close=("close", "last"), vol=("volume", "sum"), tmin=("tmin", "first"))
           .reset_index().sort_values(["cal", "slot"]).reset_index(drop=True))
    pc = c.close.shift()
    tr = pd.concat([c.high - c.low, (c.high - pc).abs(), (c.low - pc).abs()],
                   axis=1).max(axis=1)
    c["atr_tf"] = tr.rolling(14).mean().shift(1)
    c["rng_atr"] = (c.high - c.low) / c.atr_tf
    base = c.groupby("slot").vol.transform(lambda s: s.rolling(14).mean().shift(1))
    c["relvol"] = c.vol / base.replace(0, np.nan)
    return c


def _tf_candles(day: pd.DataFrame, start_mod: int, tf: int) -> pd.DataFrame:
    """Aggregate 1m bars into entry-timeframe candles aligned to the anchor."""
    d = day[day.tmin >= start_mod].copy()
    if d.empty:
        return d
    d["slot"] = (d.tmin - start_mod) // tf
    g = d.groupby("slot")
    out = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                close=("close", "last"), tmin=("tmin", "first"))
    return out


def run(bars: pd.DataFrame, cfg: Config, ctx: pd.DataFrame | None = None,
        signal_fn=orb_candidates) -> pd.DataFrame:
    if ctx is None:
        ctx = daily_context(bars, cfg.atr_days)
    a_h, a_m = (int(x) for x in cfg.anchor.split(":"))
    anchor = a_h * 60 + a_m
    or_end = anchor + cfg.or_minutes
    cut = None
    if cfg.cutoff:
        c_h, c_m = (int(x) for x in cfg.cutoff.split(":"))
        cut = c_h * 60 + c_m
    slip = cfg.slip_ticks * TICK

    EF = None
    if cfg.min_relvol is not None or cfg.min_bar_atr is not None:
        ef = entry_frame(bars, or_end, cfg.entry_tf)
        EF = {k: dict(zip(g.tmin.astype(int), zip(g.relvol, g.rng_atr)))
              for k, g in ef.groupby("cal", sort=False)}

    trades: list[dict] = []
    week_r, week_id, consec = 0.0, None, 0

    for cal, day in bars.groupby("cal", sort=True):
        wk = cal.isocalendar()[:2]
        if wk != week_id:
            week_id, week_r, consec = wk, 0.0, 0     # consec resets WEEKLY (v2 bug)
        if cfg.weekly_stop_r is not None and week_r <= cfg.weekly_stop_r:
            continue
        if cfg.consec_loss_halt is not None and consec >= cfg.consec_loss_halt:
            continue
        if day.dow.iloc[0] in cfg.skip_weekdays:
            continue

        row = ctx.loc[cal] if cal in ctx.index else None
        atr = None if row is None else row.atr

        if cfg.crabel is not None:
            if row is None or not bool(row[cfg.crabel]):
                continue

        feat = EF.get(cal) if EF is not None else None
        cands = signal_fn(day, cfg, row, feat, anchor, or_end)
        if not cands:
            continue
        if cfg.exit_tf > 1:
            one = _tf_candles(day, anchor, cfg.exit_tf).set_index("tmin")
        else:
            one = day.set_index("tmin")
        day_r, taken = 0.0, 0

        for cd in cands:
            if taken >= cfg.max_trades_per_day:
                break
            if cfg.daily_stop_r is not None and day_r <= cfg.daily_stop_r:
                break
            d_, fill_mod = cd.direction, cd.fill_tmin
            if cut is not None and fill_mod > cut:
                break
            nxt = day[day.tmin == fill_mod]
            if nxt.empty:
                break
            entry = float(nxt.open.iloc[0]) + d_ * slip

            # Directional bias gates. These CONTINUE rather than break: a later candidate
            # on the same day can still qualify, which is what the Pine reference does.
            # They used to break, which silently under-traded every gated day.
            if cfg.pdc_gate:
                if row is None or not np.isfinite(row.pdc) or (entry - row.pdc) * d_ <= 0:
                    continue
            if cfg.vwap_gate:
                if (entry - float(nxt.vwap.iloc[0])) * d_ <= 0:
                    continue

            stop = cd.stop_ref
            capped = False
            if cfg.risk_mode != "off":
                caps = []
                if cfg.max_risk_pts is not None:
                    caps.append(cfg.max_risk_pts)
                if cfg.max_risk_atr is not None and atr is not None and np.isfinite(atr):
                    caps.append(cfg.max_risk_atr * atr)
                if cfg.max_risk_pct is not None:
                    caps.append(cfg.max_risk_pct / 100.0 * entry)
                if caps and abs(entry - stop) > min(caps):
                    if cfg.risk_mode == "skip":
                        continue
                    stop = entry - d_ * min(caps)
                    capped = True
            # The stop must sit on the PROTECTIVE side of the entry -- below for a long,
            # above for a short. ORB's stop (the opposite OR boundary) satisfies this by
            # construction and this never fires for it. A signal whose stop reference is
            # computed from bars strictly before the fill bar (any reversal/turn signal)
            # can have price run past that reference before the fill actually happens; take
            # that trade and _walk() would exit on its very first bar at a price ON THE
            # WRONG SIDE of entry, recording a "stop" that is arithmetically a WIN. Caught by
            # test_a_stop_on_the_wrong_side_of_entry_is_rejected_not_mispriced.
            if (entry - stop) * d_ <= 0:
                continue
            risk = abs(entry - stop)
            if risk < TICK:
                continue

            t = _walk(one, fill_mod, d_, entry, stop, risk, cfg, anchor)
            gross = d_ * (t["exit_px"] - entry) - slip
            pnl_usd = gross * POINT_USD - cfg.commission_usd
            r = pnl_usd / (risk * POINT_USD)
            trades.append({
                "cal": cal, "dow": day.dow.iloc[0], "dir": d_,
                **cd.meta,
                "entry_min": fill_mod, "entry": entry, "stop": stop,
                "risk_pts": risk, "capped": capped, "atr": atr,
                "exit_min": t["exit_min"], "exit_px": t["exit_px"],
                "reason": t["reason"], "mfe_r": t["mfe_r"], "mae_r": t["mae_r"],
                "bars_held": t["bars"], "pnl_pts": gross, "pnl_usd": pnl_usd, "r": r,
            })
            day_r += r
            week_r += r
            consec = consec + 1 if r < 0 else 0
            taken += 1

    return pd.DataFrame(trades)


def _walk(one: pd.DataFrame, fill_mod: int, d_: int, entry: float, stop: float,
          risk: float, cfg: Config, anchor: int) -> dict:
    """Minute-by-minute exit walk. Returns the first exit that triggers."""
    target = entry + d_ * cfg.target_r * risk
    live_stop = stop
    mfe = mae = 0.0
    ratchet_on = False
    deadline = (anchor if cfg.flat_from_anchor else fill_mod) + cfg.flat_minutes
    ts_at = fill_mod + cfg.time_stop_min if cfg.time_stop_min else None

    mods = one.index.to_numpy()
    sel = mods[(mods >= fill_mod) & (mods <= deadline)]
    if len(sel) == 0:
        return _ex(entry, fill_mod, 'no_bars', 0.0, 0.0, 0)
    hi = one.high.to_numpy(); lo = one.low.to_numpy(); cl = one.close.to_numpy()
    pos = {m: i for i, m in enumerate(mods)}
    last_px, last_mod, n = entry, fill_mod, 0

    for m in sel:
        i = pos[m]
        n += 1
        fav = d_ * ((hi[i] if d_ > 0 else lo[i]) - entry) / risk
        adv = d_ * ((lo[i] if d_ > 0 else hi[i]) - entry) / risk
        mfe, mae = max(mfe, fav), min(mae, adv)
        hit_stop = (lo[i] <= live_stop) if d_ > 0 else (hi[i] >= live_stop)
        hit_tgt = (hi[i] >= target) if d_ > 0 else (lo[i] <= target)
        if hit_stop and hit_tgt:
            if cfg.optimistic:
                return _ex(target, m, "target", mfe, mae, n)
            return _ex(live_stop, m, "ratchet" if ratchet_on else "stop", mfe, mae, n)
        if hit_stop:
            return _ex(live_stop, m, "ratchet" if ratchet_on else "stop", mfe, mae, n)
        if hit_tgt:
            return _ex(target, m, "target", mfe, mae, n)
        # --- armed for SUBSEQUENT bars only ---------------------------------
        if ts_at is not None and m >= ts_at:
            cur = d_ * (cl[i] - entry) / risk
            if cur < cfg.time_stop_r:
                return _ex(cl[i], m, "time_stop", mfe, mae, n)
        if cfg.ratchet and not ratchet_on and fav >= cfg.ratchet_trigger_r:
            ratchet_on = True
            live_stop = entry + d_ * cfg.ratchet_lock_r * risk
        last_px, last_mod = cl[i], m
    return _ex(last_px, last_mod, "flat", mfe, mae, n)


def _ex(px, mod, reason, mfe, mae, bars) -> dict:
    return {"exit_px": float(px), "exit_min": int(mod), "reason": reason,
            "mfe_r": float(mfe), "mae_r": float(mae), "bars": int(bars)}


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------

def summarise(t: pd.DataFrame, label: str = "") -> dict:
    if t is None or t.empty:
        return {"label": label, "n": 0}
    w = t[t.r > 0]; l = t[t.r <= 0]
    gp, gl = w.pnl_usd.sum(), -l.pnl_usd.sum()
    return {
        "label": label, "n": len(t),
        "win_pct": 100 * len(w) / len(t),
        "ev_r": t.r.mean(),
        "total_r": t.r.sum(),
        "pts": t.pnl_pts.sum(),
        "usd": t.pnl_usd.sum(),
        "pf": (gp / gl) if gl > 0 else np.inf,
        "med_risk_pts": t.risk_pts.median(),
        "max_dd_r": _max_dd(t.r.to_numpy()),
        "tgt_pct": 100 * (t.reason == "target").mean(),
        "stop_pct": 100 * t.reason.isin(["stop", "ratchet"]).mean(),
        "flat_pct": 100 * (t.reason == "flat").mean(),
    }


def _max_dd(r: np.ndarray) -> float:
    eq = np.cumsum(r)
    return float((eq - np.maximum.accumulate(np.r_[0, eq])[1:]).min()) if len(eq) else 0.0
