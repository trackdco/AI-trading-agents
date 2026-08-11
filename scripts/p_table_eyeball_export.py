"""REPAIR RUN — Task 4: eyeball export. Highest-value deliverable in the run.

30 qualified events, stratified 10 at 1m / 10 at 3m / 10 at 5m, spread across
both sessions and both directions. One chart per event: candles around the
PXL/PXH, the 0/0.5/1 levels, the displacement candle marked, stop and target
as reference lines. NO outcome/execution path is drawn (no fill marker, no
MFE/MAE trace, no exit) -- this is an object-identification check only, not a
trade replay, consistent with the run's no-outcome discipline.

Deterministic selection (evenly strided within each stratum, sorted by
event_id) -- no randomness.
"""
from __future__ import annotations

import csv
import math
import os
import sys
from datetime import date as Date, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p_table_lib import CONFIG, aggregate_tf, build_session_minutes, session_window_utc
from build_p_table import load_front_minutes, minute_map_for_day_window

CACHE = os.environ.get(
    "P_TABLE_CACHE",
    "/tmp/claude-0/-home-user-AI-trading-agents/a6ad12c8-81a9-57f1-b548-760dc4a1f9f9/scratchpad/cache")
OUT_DIR = "output/eyeball_export"
N_PER_TF = 10
TFS = [1, 3, 5]


def select_events(fit: pd.DataFrame) -> pd.DataFrame:
    q = fit[fit.qualified].copy().sort_values("event_id").reset_index(drop=True)
    picked = []
    for tf in TFS:
        pool = q[q.tf_trigger == tf]
        # spread across session x direction cells, striding within each
        cells = []
        for session in ("ny_am", "london"):
            for direction in (-1, 1):
                sub = pool[(pool.session == session) & (pool.direction == direction)]
                cells.append(sub)
        # round-robin across the 4 cells until N_PER_TF collected
        per_cell_target = [N_PER_TF // 4 + (1 if i < N_PER_TF % 4 else 0)
                           for i in range(4)]
        for cell, k in zip(cells, per_cell_target):
            if not len(cell) or k == 0:
                continue
            step = max(1, len(cell) // k)
            picked.append(cell.iloc[::step].head(k))
    out = pd.concat(picked).drop_duplicates("event_id").reset_index(drop=True)
    return out


def render_event(row, minutes, out_path):
    d = row.direction
    ts_pxl = pd.Timestamp(row.pxl_ts).to_pydatetime()
    ts_trig = pd.Timestamp(row.tf_trigger_ts).to_pydatetime()
    tf = int(row.tf_trigger)
    tf_bars = aggregate_tf(minutes, tf)
    idx_pxl = next((i for i, b in enumerate(tf_bars) if b.close_ts == ts_pxl), None)
    idx_trig = next((i for i, b in enumerate(tf_bars) if b.close_ts == ts_trig), None)
    if idx_pxl is None or idx_trig is None:
        return False
    lo = max(0, idx_pxl - 12)
    hi = min(len(tf_bars), idx_trig + 10)
    window = tf_bars[lo:hi]

    fig, ax = plt.subplots(figsize=(13, 7))
    w = 0.6
    for i, b in enumerate(window):
        color = "#2a9d5c" if b.close >= b.open else "#d1495b"
        ax.plot([i, i], [b.low, b.high], color=color, linewidth=1)
        y0, h = (b.open, b.close - b.open) if b.close >= b.open else (b.close, b.open - b.close)
        h = max(h, (b.high - b.low) * 0.01)
        ax.add_patch(Rectangle((i - w / 2, y0), w, h, facecolor=color,
                               edgecolor=color, alpha=0.85))

    i_pxl = idx_pxl - lo
    i_trig = idx_trig - lo
    # highlight the PXL/PXH candle and the displacement/trigger candle
    ax.add_patch(Rectangle((i_pxl - w / 2 - 0.15, tf_bars[idx_pxl].low),
                           w + 0.3, tf_bars[idx_pxl].high - tf_bars[idx_pxl].low,
                           fill=False, edgecolor="#264653", linewidth=2.2, zorder=5))
    ax.add_patch(Rectangle((i_trig - w / 2 - 0.15, tf_bars[idx_trig].low),
                           w + 0.3, tf_bars[idx_trig].high - tf_bars[idx_trig].low,
                           fill=False, edgecolor="#e76f51", linewidth=2.2, zorder=5))

    x0, x1 = -0.5, len(window) - 0.5
    label = "PXL" if d == -1 else "PXH"
    ax.hlines(row.pxl_level_0, x0, x1, colors="#264653", linestyles="solid", linewidth=1.3)
    ax.text(x1 + 0.1, row.pxl_level_0, f"0  ({label} outer, level_0)", va="center", fontsize=8)
    ax.hlines(row.pxl_level_1, x0, x1, colors="#264653", linestyles="solid", linewidth=1.3)
    ax.text(x1 + 0.1, row.pxl_level_1, "1  (wick inner, level_1, DA-3 body-boundary)",
           va="center", fontsize=8)
    ax.hlines(row.limit_price, x0, x1, colors="#f4a261", linestyles="dashed", linewidth=1.4)
    ax.text(x1 + 0.1, row.limit_price, "0.5  (limit_price = pxl_50)", va="center",
           fontsize=8, color="#a35b1a")
    ax.hlines(row.stop_price_base, x0, x1, colors="#e63946", linestyles="dotted", linewidth=1.4)
    ax.text(x1 + 0.1, row.stop_price_base, "stop_price_base", va="center",
           fontsize=8, color="#e63946")
    if not (isinstance(row.target_price, float) and math.isnan(row.target_price)):
        ax.hlines(row.target_price, x0, x1, colors="#2a9d5c", linestyles="dashdot",
                 linewidth=1.4)
        ax.text(x1 + 0.1, row.target_price, "target_price (nearest draw)",
               va="center", fontsize=8, color="#1b7a3d")

    ax.set_xlim(x0, x1 + 6.5)
    ax.set_xticks([])
    ax.set_title(
        f"{row.event_id}  ·  {row.date} {row.session}  ·  "
        f"{'PXL (short)' if d == -1 else 'PXH (long)'}  ·  tf_trigger={tf}m\n"
        f"wick_width_pts={row.wick_width_pts:.2f}   "
        f"stop_dist_pts={row.stop_dist_pts_base:.2f}   "
        f"r_available={'n/a' if (isinstance(row.r_available, float) and math.isnan(row.r_available)) else f'{row.r_available:.2f}'}",
        fontsize=10)
    ax.set_ylabel("price (pts)")
    legend = [Line2D([0], [0], color="#264653", lw=2.2, label=f"{label} candle (level 0/1 source)"),
             Line2D([0], [0], color="#e76f51", lw=2.2, label="displacement/trigger candle")]
    ax.legend(handles=legend, loc="upper left", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return True


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    fit = pd.read_parquet("output/p_table.parquet")
    picks = select_events(fit)
    df, front = load_front_minutes(CACHE)

    csv_rows = []
    n_ok = n_fail = 0
    for _, row in picks.iterrows():
        d = Date.fromisoformat(row.date)
        w_utc, s_utc, e_utc = session_window_utc(d, row.session)
        mm = minute_map_for_day_window(df, w_utc, e_utc)
        built = build_session_minutes(mm, d, row.session)
        if built is None:
            n_fail += 1
            continue
        minutes, _, _ = built
        fname = f"{row.event_id}.png"
        ok = render_event(row, minutes, os.path.join(OUT_DIR, fname))
        n_ok += ok
        n_fail += not ok
        csv_rows.append(dict(
            event_id=row.event_id, date=row.date, session=row.session,
            direction="short" if row.direction == -1 else "long",
            tf_trigger=row.tf_trigger, wick_width_pts=row.wick_width_pts,
            stop_dist_pts=row.stop_dist_pts_base, r_available=row.r_available,
            pxl_level_0=row.pxl_level_0, pxl_level_1=row.pxl_level_1,
            limit_price=row.limit_price, stop_price=row.stop_price_base,
            target_price=row.target_price, image=fname if ok else ""))

    with open(os.path.join(OUT_DIR, "eyeball_export.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
        w.writeheader()
        w.writerows(csv_rows)

    print(f"selected {len(picks)} events, rendered {n_ok}, failed {n_fail}")
    print(picks.groupby(["tf_trigger", "session", "direction"]).size())


if __name__ == "__main__":
    main()
