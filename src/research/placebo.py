"""Reusable level-placebo harness. Born in Job 2 (VP breakout arm),
built because Job 1's placebos were not proximity-matched and the
reopening burden demanded the fix as a standard module.

Interface (all functions are pure; none touch disk):

    anchor_prices(bars) -> pd.Series
        session_date -> 09:30 anchor price (first RTH bar's open).

    proximity_matched(profiles, anchors, rng) -> pd.DataFrame
        ONE placebo draw. For every OK session D, a donor session E
        (derangement: E != D) lends its ENTIRE level geometry —
        vah/val/poc as SIGNED DISTANCES from E's own 09:30 anchor —
        which is translated onto D's anchor and snapped to tick.
        By construction the placebo's joint distribution of
        (distance-from-price, VA width W, internal geometry) IS the
        empirical distribution — the strongest form of proximity
        matching. Call N times with one rng for N draws.

    stale(profiles, shift=5) -> pd.DataFrame
        Levels from `shift` sessions earlier applied to today.
        Retained as a comparator so the Job 1 confound stays
        documented: stale levels are NOT proximity-matched (price
        drifts), and their inflated lifts demonstrate exactly the
        artifact proximity matching removes.

Rows whose donor/self levels are unavailable get profile_status
'NO_DONOR' / 'NO_ANCHOR' so downstream census code (which keeps only
'OK') drops them explicitly, never silently.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TICK = 0.25
ET = "America/New_York"


def anchor_prices(bars: pd.DataFrame) -> pd.Series:
    rth = bars[(bars["ts_event"].dt.hour * 60 + bars["ts_event"].dt.minute)
               .between(9 * 60 + 30, 15 * 60 + 59)]
    first = (rth.sort_values("ts_event", kind="mergesort")
                .groupby("session")["open"].first())
    first.index.name = "session_date"
    return first


def _snap(x: np.ndarray) -> np.ndarray:
    return np.round(np.asarray(x, dtype=float) / TICK) * TICK


def proximity_matched(profiles: pd.DataFrame, anchors: pd.Series,
                      rng: np.random.Generator) -> pd.DataFrame:
    p = profiles.sort_values("session_date", kind="mergesort").reset_index(drop=True)
    out = p.copy()
    ok_mask = (p.profile_status == "OK") & p.session_date.isin(anchors.index)
    out.loc[(p.profile_status == "OK") & ~p.session_date.isin(anchors.index),
            "profile_status"] = "NO_ANCHOR"
    ok = p[ok_mask].reset_index()
    n = len(ok)
    if n < 2:
        return out
    perm = rng.permutation(n)
    for i in np.where(perm == np.arange(n))[0]:   # forbid self-donation
        j = (i + 1) % n
        perm[i], perm[j] = perm[j], perm[i]
    a_self = anchors.loc[ok.session_date].to_numpy(float)
    a_donor = anchors.loc[ok.session_date.iloc[perm]].to_numpy(float)
    for col in ("vah", "val", "poc"):
        donor_lv = ok[col].to_numpy(float)[perm]
        out.loc[ok["index"], col] = _snap(a_self + (donor_lv - a_donor))
    return out


def stale(profiles: pd.DataFrame, shift: int = 5) -> pd.DataFrame:
    p = profiles.sort_values("session_date", kind="mergesort").reset_index(drop=True)
    out = p.copy()
    out[["vah", "val", "poc"]] = p[["vah", "val", "poc"]].shift(shift)
    out.loc[out[["vah", "val", "poc"]].isna().any(axis=1),
            "profile_status"] = "NO_DONOR"
    return out
