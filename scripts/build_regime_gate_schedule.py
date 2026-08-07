#!/usr/bin/env python3
"""Build a REGIME-ONLY gate schedule for the replay (Pat lane).

The full combined gate (src/desk/combined_gate.py) needs BOTH the regime and HTF
agents. This builder produces the first-cut schedule from the regime agent ALONE,
leaving the HTF layer fully permissive — so the scoreboard measures the regime
agent's effect in isolation before the HTF agent is run over the same days.

It reads the ingested, schema-valid regime gates (output/regime_gates.csv, written
by `run_regime_replay ingest`) and emits output/combined_gate_schedule.csv in the
exact shape simulate(day_gate=...) consumes. Days whose verdict FAILED validation
are absent by construction (fail-closed) and therefore trade as the champion.

    python -m scripts.build_regime_gate_schedule --start 2026-03-01 --end 2026-03-31
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REGIME_GATES = Path("output/regime_gates.csv")
OUT = Path("output/combined_gate_schedule.csv")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="0000")
    ap.add_argument("--end", default="9999")
    args = ap.parse_args(argv)

    if not REGIME_GATES.exists():
        print(f"no {REGIME_GATES} — run `python -m scripts.run_regime_replay ingest` first")
        return 1

    g = pd.read_csv(REGIME_GATES)
    g["date"] = g["date"].astype(str)
    g = g[(g["date"] >= args.start) & (g["date"] <= args.end)].copy()
    if g.empty:
        print("no regime gates in range")
        return 0

    rows = []
    for _, r in g.iterrows():
        allow_rev = bool(r["allow_reversion"])
        allow_cont = bool(r["allow_continuation"])
        size = float(r["size_multiplier"])
        stand_down = (not (allow_rev or allow_cont)) or size == 0.0
        rows.append({
            "date": r["date"],
            "allow_reversion": allow_rev,
            "allow_continuation": allow_cont,
            "size_multiplier": 0.0 if stand_down else size,
            "directional_bias": r["directional_bias"],
            "stand_down": stand_down,
            "reasons": "regime-only (HTF layer permissive)",
            "conflict": False,
        })
    out = pd.DataFrame(rows).sort_values("date")
    OUT.write_text(out.to_csv(index=False))
    print(f"wrote {len(out)} regime-only gate rows -> {OUT}")
    print(out[["date", "allow_reversion", "allow_continuation",
               "size_multiplier", "stand_down"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
