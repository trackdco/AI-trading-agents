"""Step-4 parity harness (spec-1 §4).

Computes the indicator snapshot (BB basis, daily VWAP ±1σ, NY VWAP, daily POC)
at the reference timestamps so Angus can compare each to the values visible on
the reference charts (must agree within 1.0 NQ pt before Steps 5-9 are trusted).

NOTE: the reference dates are in Feb 2026, which is NOT in the repo's historical
data (coverage ends 2026-01-31). Those rows will report NO DATA until the Feb
2026 1m NQ is pulled from Databento historical. An in-coverage date is included
purely to prove the report FORMAT and the computation, not as the parity check.
"""
from __future__ import annotations

import sys
from datetime import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.config import Config          # noqa: E402
from engine import data as dataio, indicators, structure  # noqa: E402

REF = [
    ("2026-02-11T09:48", "PARITY reference (Feb NFP short) — needs Feb data"),
    ("2026-02-17T09:50", "PARITY reference — needs Feb data"),
    ("2026-01-13T09:50", "IN-COVERAGE illustration (format/computation proof only)"),
]


def snapshot(df1m, cfg, ts):
    bands = cfg["indicators"]["vwap_bands"]
    dv = indicators.anchored_vwap(df1m, cfg.t("session", "daily_anchor"), False, bands)
    nv = indicators.anchored_vwap(df1m, cfg.t("session", "ny_open"), True, bands)
    f5 = __import__("engine.sessions", fromlist=["resample"]).resample(df1m, 5)
    bb = indicators.bollinger(f5, cfg["indicators"]["bollinger"]["length"],
                              cfg["indicators"]["bollinger"]["stddev"])
    day = ts.normalize()
    start = day + pd.Timedelta(hours=18)
    if ts.time() < time(18, 0):
        start -= pd.Timedelta(days=1)
    poc = indicators.volume_profile(df1m.loc[start:ts],
                                    cfg["indicators"]["volume_profile"]["bin_pts"],
                                    cfg["indicators"]["volume_profile"]["value_area_pct"])["poc"]
    bb_ts = f5.index.asof(ts)
    return {
        "bb_basis": round(float(bb.loc[bb_ts, "bb_ma"]), 2) if bb_ts is not None else None,
        "daily_vwap": round(float(dv.loc[ts, "vwap"]), 2) if ts in dv.index else None,
        "daily_vwap_p1": round(float(dv.loc[ts, "vwap_p1"]), 2) if ts in dv.index else None,
        "daily_vwap_m1": round(float(dv.loc[ts, "vwap_m1"]), 2) if ts in dv.index else None,
        "ny_vwap": (round(float(nv.loc[ts, "vwap"]), 2)
                    if ts in nv.index and nv.loc[ts, "vwap"] == nv.loc[ts, "vwap"] else None),
        "daily_poc": round(float(poc), 2) if poc == poc else None,
    }


def main():
    cfg = Config.load(); tz = cfg.tz
    files = [str(p) for p in sorted(ROOT.parent.glob("glbx-mdp3-*.csv.zst"))]
    df = dataio.load_historical(files, tz)
    cov0, cov1 = df.index.min(), df.index.max()

    lines = ["# Parity Report (spec-1 Step 4)", "",
             f"Data coverage: **{cov0} → {cov1}**", "",
             "Angus: compare each COMPUTED value below to the reference-chart value; "
             "each must agree within **1.0 NQ pt**. Do not sign off on rows marked NO DATA.", "",
             "| Timestamp (ET) | Note | BB basis | daily VWAP | +1σ | −1σ | NY VWAP | daily POC | chart value | Δ | ✓ |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s, note in REF:
        ts = pd.Timestamp(s, tz=tz)
        if ts < cov0 or ts > cov1:
            lines.append(f"| {s} | {note} | — | — | — | — | — | — | _fill_ | _fill_ | ❌ NO DATA |")
            continue
        snap = snapshot(df, cfg, ts)
        lines.append(
            f"| {s} | {note} | {snap['bb_basis']} | {snap['daily_vwap']} | "
            f"{snap['daily_vwap_p1']} | {snap['daily_vwap_m1']} | {snap['ny_vwap']} | "
            f"{snap['daily_poc']} | _fill_ | _fill_ | ⬜ |")

    lines += ["", "## Gate status",
              "- ❌ **BLOCKED — parity cannot be signed off.** The two required reference "
              "dates (Feb 11 & Feb 17 2026) are outside data coverage.",
              "- **Unblock:** pull Feb 2026 (ideally Feb–Jul for out-of-sample) 1m NQ "
              "GLBX.MDP3 from Databento **historical**, then re-run `python -m scripts.parity`.",
              "- Steps 5-9 detection is built but must be treated as UNCALIBRATED until this "
              "gate and the §12 February calibration pass."]
    out = ROOT / "output" / "parity_report.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"wrote {out}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
