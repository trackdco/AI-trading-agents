#!/usr/bin/env python3
"""Build the combined per-day de-risk schedule from the two agents' gate files.

    python -m scripts.build_gate_schedule

Reads output/regime_gates.csv + output/htf_gates.csv, merges each shared day via
src/desk/combined_gate.combine(), writes output/combined_gate_schedule.csv — the
per-day table the engine's replay consumes (once simulate() exposes the de-risk
hook, engine-lane). Days present in only one file are reported, not merged
(both agents must have ruled).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.desk.combined_gate import combine  # noqa: E402
from src.desk.htf_agent import HTFGate  # noqa: E402
from src.desk.regime_agent import RegimeGate  # noqa: E402

REGIME = Path("output/regime_gates.csv")
HTF = Path("output/htf_gates.csv")
OUT = Path("output/combined_gate_schedule.csv")


def main() -> int:
    if not (REGIME.exists() and HTF.exists()):
        print(f"need both {REGIME} and {HTF}")
        return 1
    rg = pd.read_csv(REGIME).set_index("date")
    hg = pd.read_csv(HTF).set_index("date")
    both = sorted(set(rg.index) & set(hg.index))
    only_r, only_h = sorted(set(rg.index) - set(hg.index)), sorted(set(hg.index) - set(rg.index))
    if only_r:
        print(f"regime-only days (no HTF verdict, not merged): {only_r}")
    if only_h:
        print(f"HTF-only days (no regime verdict, not merged): {only_h}")

    rows = []
    for d in both:
        g = combine(RegimeGate(date=d, **rg.loc[d].to_dict()),
                    HTFGate(date=d, **hg.loc[d].to_dict()))
        rows.append(g.model_dump())
    if not rows:
        print("no shared days to merge")
        return 0
    out = pd.DataFrame(rows)
    out["reasons"] = out["reasons"].apply(lambda r: " | ".join(r))
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(rows)} days)")
    for r in rows:
        print(f"  {r['date']}: rev={r['allow_reversion']} cont={r['allow_continuation']} "
              f"size={r['size_multiplier']} stand_down={r['stand_down']} conflict={r['conflict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
