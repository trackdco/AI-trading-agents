"""L3 — the pre-registered test of THE question:

    Does anything knowable BEFORE the print predict the post-print
    direction well enough to beat gap-adjusted losses?

Pooled across families via standardized predictors (per-family n is too
small to say anything alone — 43 CPIs cannot separate 60% from a coin).

Kill rule (frozen in PREREG-L3.md before unsealing):
  NO-TRADE unless BOTH
    (a) pooled directional accuracy Wilson CI-low > 0.50, AND
    (b) gap-adjusted expectancy > 0 using WORST-BOUND stop fills.
Discovery runs on unsealed rows only; the sealed era is scored ONCE, after
the prereg sha is committed, with NEWSLAB_UNSEAL=1.
"""
from __future__ import annotations
import hashlib
import os
import numpy as np
import pandas as pd

from .config import (DEFAULT_STOP_PTS, SURPRISE_TO_NQ_SIGN, unsealed)
from .census import wilson


def prereg_sha(path: str = "PREREG-L3.md") -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:12]


def pooled_direction_test(census: pd.DataFrame, predictor: str,
                          horizon: int = 30, stop: int = DEFAULT_STOP_PTS,
                          entry_tminus: int = 1,
                          score_sealed: bool = False) -> dict:
    """predictor: a signed column (e.g. 'surprise_z' for the ceiling test,
    'nowcast_gap', 'drift_30m', 'kalshi_skew'). Direction traded =
    sign(predictor) mapped through the family's NQ sign convention.

    entry_tminus: entry at close(T − entry_tminus). v1 measures from ref
    (T−1); wire other entry times by re-basing moves in census first.

    Returns verdict dict. Never silently scores sealed rows."""
    df = census[(census["coverage_ok"] == True)].copy()  # noqa: E712
    if score_sealed:
        if not unsealed():
            raise RuntimeError("Sealed scoring requested without "
                               "NEWSLAB_UNSEAL=1. Freeze PREREG-L3.md, "
                               "commit its sha, then unseal.")
        df = df[df["sealed"]]
        era = "SEALED-HOLDOUT"
    else:
        df = df[~df["sealed"]]
        era = "DISCOVERY"
    df = df.dropna(subset=[predictor, f"move_{horizon}m"])
    if df.empty:
        return dict(era=era, n=0, verdict="NO-DATA")

    fam_sign = df["family"].map(SURPRISE_TO_NQ_SIGN)
    direction = np.sign(df[predictor]) * fam_sign          # +1 long / −1 short
    df = df[direction != 0]
    direction = direction[direction != 0]
    move = df[f"move_{horizon}m"]
    hit = np.sign(move) == direction
    k, n = int(hit.sum()), len(hit)
    ci_lo, ci_hi = wilson(k, n)

    # gap-adjusted expectancy in R:
    #   winners: |move| / stop   (conservative: horizon close, no MFE credit)
    #   losers : stopped → WORST-bound fill; not stopped → |move|/stop loss
    side = np.where(direction > 0, "long", "short")
    stopped = np.array([df.iloc[i][f"stop{stop}_{s}_stopped"] is True
                        for i, s in enumerate(side)])
    worst = np.array([df.iloc[i][f"stop{stop}_{s}_loss_worst"] or 0.0
                      for i, s in enumerate(side)])
    r = np.where(hit, move.abs() / stop,
                 np.where(stopped, -worst / stop, -move.abs() / stop))
    ev_r = float(np.mean(r))
    ev_pts = ev_r * stop

    ok = (ci_lo > 0.50) and (ev_r > 0)
    return dict(era=era, predictor=predictor, horizon_min=horizon,
                stop_pts=stop, n=n, hits=k,
                accuracy=round(k / n, 3),
                ci=(round(ci_lo, 3), round(ci_hi, 3)),
                ev_R=round(ev_r, 3), ev_pts=round(ev_pts, 1),
                ev_usd_nq=round(ev_pts * 20, 0),
                verdict="TRADE-CANDIDATE" if ok else "NO-TRADE",
                prereg=os.environ.get("NEWSLAB_PREREG_SHA", "UNSET"))


def report(res: dict) -> str:
    """Angus's units doctrine: R first, points alongside."""
    if res.get("verdict") == "NO-DATA":
        return f"[{res['era']}] no scorable rows."
    return (f"[{res['era']}] {res['predictor']} @ +{res['horizon_min']}m, "
            f"stop {res['stop_pts']}pt: n={res['n']}, "
            f"acc {res['accuracy']:.1%} (CI {res['ci'][0]:.1%}–{res['ci'][1]:.1%}), "
            f"EV {res['ev_R']:+.2f}R ({res['ev_pts']:+.1f} pts, "
            f"~${res['ev_usd_nq']:+.0f}/NQ) → {res['verdict']} "
            f"[prereg {res['prereg']}]")
