"""Per-confluence ablation: which gates, if any, carry the edge.

The deliverable is not a headline number. It is a ranking of each gate's contribution,
plus an honest statement when the answer is "none of it survives". Two views are
produced because they answer different questions:

  leave-one-out  — drop one gate, keep the rest. Measures marginal contribution given
                   everything else, which is what you would actually remove.
  only-this-gate — run the trigger with a single gate. Measures standalone information,
                   which is what the confluence table's "standalone edge" test asks for.

Sample size is reported everywhere and interpretation is refused below a floor: on a
signal count in the low tens, a win-rate difference means nothing, and quoting one would
be the exact failure this whole exercise is built to avoid.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import detector as DT

GATES = ["session", "c1", "c2", "c3", "c4", "c5"]
MIN_N = 30  # below this, report counts only and refuse to interpret


def _stats(trades: pd.DataFrame) -> dict:
    if trades is None or trades.empty:
        return {"n": 0, "win_pct": np.nan, "mean_r": np.nan, "total_r": np.nan,
                "target_pct": np.nan}
    r = trades["pnl_r"]
    return {
        "n": len(trades),
        "win_pct": float((r > 0).mean() * 100),
        "mean_r": float(r.mean()),
        "total_r": float(r.sum()),
        "target_pct": float((trades["exit_reason"] == "target").mean() * 100),
    }


def run_variant(df: pd.DataFrame, ctx: DT.Context, cfg: dict,
                masks: dict[str, np.ndarray], use: list[str]) -> dict:
    sub = {k: (v if k in use else np.ones(len(df), dtype=bool)) for k, v in masks.items()}
    sig = DT.detect(ctx, cfg, sub)
    return _stats(DT.simulate(df, sig, cfg))


def ablation_table(df: pd.DataFrame, ctx: DT.Context, cfg: dict,
                   masks: dict[str, np.ndarray] | None = None) -> pd.DataFrame:
    masks = masks if masks is not None else DT.compute_masks(ctx, cfg)
    rows = []
    base = run_variant(df, ctx, cfg, masks, GATES)
    rows.append({"variant": "all gates (baseline)", "kind": "baseline", **base})
    rows.append({"variant": "no gates (trigger only)", "kind": "trigger",
                 **run_variant(df, ctx, cfg, masks, [])})
    for g in GATES:
        rows.append({"variant": f"drop {g}", "kind": "leave-one-out",
                     **run_variant(df, ctx, cfg, masks, [x for x in GATES if x != g])})
    for g in GATES:
        rows.append({"variant": f"only {g}", "kind": "standalone",
                     **run_variant(df, ctx, cfg, masks, [g])})
    out = pd.DataFrame(rows)
    out["delta_mean_r_vs_base"] = out["mean_r"] - base["mean_r"]
    return out


def clock_profile(df: pd.DataFrame, ctx: DT.Context, cfg: dict,
                  masks: dict[str, np.ndarray] | None = None) -> pd.DataFrame:
    """Outcome by minute-of-hour bucket, to test his claimed 66 / 50 / 75 profile.

    C3 is switched off so every minute is represented; the point is the shape of the
    curve, not whether his chosen window wins.
    """
    masks = masks if masks is not None else DT.compute_masks(ctx, cfg)
    sub = {k: (np.ones(len(df), dtype=bool) if k == "c3" else v) for k, v in masks.items()}
    trades = DT.simulate(df, DT.detect(ctx, cfg, sub), cfg)
    if trades.empty:
        return pd.DataFrame()
    b = pd.cut(trades["minute_of_hour"], [-1, 9, 29, 44, 59],
               labels=["0-9", "10-29", "30-44", "45-59"])
    g = trades.groupby(b, observed=False)["pnl_r"]
    prof = pd.DataFrame({"n": g.size(), "win_pct": g.apply(lambda s: (s > 0).mean() * 100),
                         "mean_r": g.mean()}).reset_index(names="minute_bucket")
    prof["his_claim_pct"] = [66.0, 50.0, 75.0, np.nan]
    return prof


def write_report(path: Path, table: pd.DataFrame, profile: pd.DataFrame,
                 meta: dict) -> None:
    lines = ["# tomtrades CBR — ablation report", ""]
    lines += [f"- {k}: {v}" for k, v in meta.items()]
    lines += ["", "RESEARCH ONLY. Reverse-engineered from public videos and UNVALIDATED.",
              f"Variants with n < {MIN_N} are reported as counts only — a win rate on a",
              "handful of trades is noise, and quoting it would be the failure this",
              "exercise exists to avoid.", "", "## Per-gate ablation", ""]
    show = table.copy()
    for c in ("win_pct", "mean_r", "total_r", "target_pct", "delta_mean_r_vs_base"):
        show[c] = show[c].round(3)
    thin = show["n"] < MIN_N
    for c in ("win_pct", "mean_r", "total_r", "target_pct", "delta_mean_r_vs_base"):
        show.loc[thin, c] = np.nan
    lines.append(show.to_markdown(index=False))
    lines += ["", "## Minute-of-hour profile (C3 disabled)", ""]
    lines.append(profile.round(2).to_markdown(index=False) if not profile.empty
                 else "_no trades_")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
