"""Detector — per-timestamp orchestration with MTF arbitration.

Precomputes anchored VWAP bands (daily + NY) once, resamples entry/context TFs,
finds 15m swings. For a given close timestamp it builds the typed level set,
runs trigger detection on every entry TF whose bar closes then, and applies MTF
arbitration (highest TF wins, §1). Emits a validated 20-field candidate.
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

from . import indicators, structure, clusters, triggers, payload
from .schema import EngineCandidate, ENGINE_FIELDS

_BANDKEYS = {"mid": "vwap", "p1": "vwap_p1", "m1": "vwap_m1", "p2": "vwap_p2",
             "m2": "vwap_m2", "p3": "vwap_p3", "m3": "vwap_m3"}


class Detector:
    def __init__(self, cfg, df1m: pd.DataFrame, news_df: pd.DataFrame | None):
        self.cfg = cfg
        self.df1m = df1m
        self.news = news_df
        bands = cfg["indicators"]["vwap_bands"]

        self.dv = indicators.anchored_vwap(df1m, cfg.t("session", "daily_anchor"), False, bands)
        self.nv = indicators.anchored_vwap(df1m, cfg.t("session", "ny_open"), True, bands)

        self.tf = {}
        self.bb = {}
        from .sessions import resample
        self._resample = resample
        for tf in cfg.entry_tfs:
            f = resample(df1m, tf)
            self.tf[tf] = f
            self.bb[tf] = indicators.bollinger(
                f, cfg["indicators"]["bollinger"]["length"],
                cfg["indicators"]["bollinger"]["stddev"])

        self.ctx15 = resample(df1m, cfg.ctx_tf)
        self.pivots = structure.find_pivots(self.ctx15, cfg["structure"]["swing_pivot_bars"])

        self.daily_anchor = cfg.t("session", "daily_anchor")
        self.ny_open = cfg.t("session", "ny_open")
        self.tol = cfg["clusters"]["tolerance_pts"]
        self.tick = cfg.tick

    # ---- indicator snapshot helpers ----------------------------------------
    def _vwap_dict(self, series_row) -> dict:
        return {k: (float(series_row[col]) if col in series_row and series_row[col] == series_row[col] else None)
                for k, col in _BANDKEYS.items()}

    def _daily_poc(self, asof) -> float:
        day = asof.normalize()
        start = day + pd.Timedelta(hours=self.daily_anchor.hour, minutes=self.daily_anchor.minute)
        if asof.time() < self.daily_anchor:
            start -= pd.Timedelta(days=1)
        win = self.df1m.loc[start:asof]
        vp = indicators.volume_profile(
            win, self.cfg["indicators"]["volume_profile"]["bin_pts"],
            self.cfg["indicators"]["volume_profile"]["value_area_pct"])
        return vp["poc"]

    # ---- main entry point ---------------------------------------------------
    def evaluate(self, asof) -> dict | None:
        cfg = self.cfg
        if asof not in self.dv.index:
            return None
        pre_930 = asof.time() < self.ny_open

        dv_row = self.dv.loc[asof]
        nv_row = self.nv.loc[asof]
        daily_vwap = self._vwap_dict(dv_row)
        ny_vwap = None if pre_930 or nv_row["vwap"] != nv_row["vwap"] else self._vwap_dict(nv_row)
        poc = self._daily_poc(asof)

        # structural extremes
        from .sessions import session_extremes, prior_day_hl, classify_session
        s_hi, s_lo = session_extremes(self.df1m, asof, time(9, 30))
        p_hi, p_lo = prior_day_hl(self.df1m, asof)
        structural = {"session high": s_hi, "session low": s_lo,
                      "prior-day high": p_hi, "prior-day low": p_lo}

        ind = {"daily_vwap": daily_vwap, "ny_vwap": ny_vwap, "daily_poc": poc, "bb_ma": None}

        htf = structure.htf_flag(self.pivots, asof)
        levels_base = clusters.build_levels(ind, structural, pre_930)

        # target menu (§6)
        menu = []
        for src in (daily_vwap, ny_vwap or {}):
            for k in ("mid", "p1", "m1", "p2", "m2"):
                if src.get(k) is not None:
                    menu.append({"label": f"VWAP {k}", "price": src[k]})
        if poc == poc:
            menu.append({"label": "daily POC", "price": poc})
        for lbl, v in structural.items():
            if v == v:
                menu.append({"label": lbl, "price": v})

        overext = {"p2": (ny_vwap or daily_vwap).get("p2"),
                   "m2": (ny_vwap or daily_vwap).get("m2")}

        # evaluate each entry TF whose bar closes at asof; highest TF wins
        best = None
        best_tf = -1
        for tf in sorted(cfg.entry_tfs):
            frame = self.tf[tf]
            if asof not in frame.index:
                continue
            bar = frame.loc[asof]
            bb_ma = self.bb[tf].loc[asof, "bb_ma"] if asof in self.bb[tf].index else np.nan
            levels = list(levels_base)
            if bb_ma == bb_ma:
                levels.append({"type": "bb", "label": "BB basis (MA)", "price": float(bb_ma)})

            tctx = {"tick": self.tick, "tol": self.tol, "htf": htf, "target_menu": menu,
                    "rr_floor": cfg["targets"]["rr_floor"], "front_run": cfg["targets"]["front_run_pts"],
                    "b_min": cfg["triggers"]["displacement_body_min"],
                    "extreme_q": cfg["triggers"]["extreme_quartile"], "overext": overext}
            trig = triggers.evaluate(bar, levels, tctx)
            if trig and tf > best_tf:
                best, best_tf = trig, tf

        if best is None:
            return None

        # ---- context bundle for payload ------------------------------------
        levels_liq = structure.liquidity_levels(self.pivots, asof)
        sweep = structure.detect_sweep(self.df1m, asof, levels_liq, self.tol)

        ctx15_win = self.ctx15.loc[:asof].tail(16)
        range_high = float(ctx15_win["high"].max())
        range_low = float(ctx15_win["low"].min())

        # volume / volatility on the winning TF
        frame = self.tf[best_tf]
        pos = frame.index.get_loc(asof)
        vwin = frame.iloc[max(0, pos - 20):pos + 1]
        vol_avg = float(vwin["volume"].mean())
        vol_ratio = (float(frame.loc[asof, "volume"]) / vol_avg) if vol_avg > 0 else None
        rng = (vwin["high"] - vwin["low"])
        cur_rng = float(frame.loc[asof, "high"] - frame.loc[asof, "low"])
        avg_rng = float(rng.mean())
        chop_flag = bool(cur_rng < 0.6 * avg_rng) if avg_rng > 0 else None
        regime = "directional" if (avg_rng > 0 and cur_rng >= avg_rng) else "chop"

        risk_tone = {"uptrend": "risk-on", "downtrend": "risk-off", "range": "neutral"}[htf]

        ctx = {
            "asof": asof, "tz": cfg.tz, "sweep": sweep,
            "kill_zone": (cfg.t("session", "kill_zone", "start"), cfg.t("session", "kill_zone", "end")),
            "optimal_window": (time(9, 30), time(10, 30)),
            "swing_sequence": structure.swing_sequence(self.pivots, asof),
            "last_close": float(frame.loc[asof, "close"]),
            "range_high": range_high, "range_low": range_low,
            "upcoming_news": payload.upcoming_news(self.news, asof),
            "session": classify_session(asof), "risk_tone": risk_tone,
            "vol_ratio": vol_ratio, "regime": regime, "chop_flag": chop_flag,
            "winning_tf": best_tf,
        }

        p = payload.build(best, ctx)
        # validate structural contract (drops _engine_trigger_detail helper key)
        core = {k: p[k] for k in ENGINE_FIELDS}
        EngineCandidate(**core)
        p["_engine_meta"] = {"winning_tf_min": best_tf, "asof_et": asof.isoformat(),
                             "uncalibrated": True}
        return p
