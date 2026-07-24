#!/usr/bin/env python3
"""Agent-replay producer (PARITY-CHECK.md Step 1).

Produces `agent_replay.parquet` for `scripts/parity_harness.py`: the taken-trade book the
mechanical canon "agents" generate over the committed candidate universe, sized under the
frozen dollar-risk floor schedule.

The agents here are the deterministic canon scorers:
  * NY pre+gold -> scripts/canon_mechanical.py  (reads output/trade_matrix.parquet ...)
  * London      -> scripts/london_canon.py      (reads output/london_matrix.parquet ...)

This RE-RUNS both scorers fresh (so a fresh run must reproduce the committed decisions —
that is the drift check; sizing the already-committed books would be circular), then sizes
their `size>0` trades with baseline_dollar_risk.size_book VERBATIM, so any parity mismatch
can only be a DECISION difference, never a sizing-definition artifact.

    python -m scripts.agent_replay                 # -> agent_replay.parquet
    python -m scripts.agent_replay out.parquet     # custom output path
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.baseline_dollar_risk import size_book


def _run_scorer(module: str) -> None:
    r = subprocess.run([sys.executable, "-m", module], cwd=ROOT,
                       capture_output=True, text=True, check=False)
    if r.returncode != 0:
        sys.stderr.write(r.stdout[-2000:] + r.stderr[-2000:])
        raise SystemExit(f"scorer {module} failed (exit {r.returncode})")


def main(out: str = "agent_replay.parquet") -> None:
    print("running NY canon scorer (canon_mechanical) ...", flush=True)
    _run_scorer("scripts.canon_mechanical")
    print("running London canon scorer (london_canon) ...", flush=True)
    _run_scorer("scripts.london_canon")

    ny = pd.read_parquet("output/canon_book.parquet")
    lo = pd.read_parquet("output/london_canon_book.parquet")
    ny_sized = size_book(ny, "NY")
    lo_sized = size_book(lo, "LONDON")
    book = pd.concat([ny_sized, lo_sized], ignore_index=True).sort_values("fill")
    book = book.reset_index(drop=True)
    book.to_parquet(out)
    print(f"wrote {out}: {len(book)} taken trades "
          f"(NY {len(ny_sized)}, London {len(lo_sized)}); P&L ${book.pl.sum():+,.2f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "agent_replay.parquet")
