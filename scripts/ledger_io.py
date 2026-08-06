#!/usr/bin/env python3
"""The trial ledger's only read/write path.

WHY JSONL AND NOT PARQUET
-------------------------
The ledger forked into four divergent copies (268 / 764 / 255 / 58 rows) with rows
unique to three of them, including five NYA-IBC-01 sealed-holdout looks that exist
nowhere else. That was not a discipline failure -- it was inevitable. Parquet is a binary
blob, git cannot merge it, so every branch that writes it resolves take-ours or
take-theirs and silently drops the other side. A spent holdout look is the one row that
can never be reconstructed, because re-deriving it would be a second look.

Sorted JSONL merges line-by-line. Two branches appending different trials union cleanly
with no adjudication (see .gitattributes: merge=union).

KEY = (family, trial, era)
Unique in all four historical ledgers with zero duplicates, and it is the unit preregs
declare trials in ("3 measures x 2 era directions = 6 trials"). Stable under re-runs: a
re-run of a declared arm overwrites rather than accumulating.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "output/trial_ledger.jsonl"
DERIVED = ROOT / "output/trial_ledger.parquet"      # build artifact, gitignored
KEY = ("family", "trial", "era")
COLUMNS = ["family", "trial", "era", "prereg", "stat_type", "estimate", "n", "t_stat",
           "effect", "verdict", "programme", "researcher", "cluster", "series_path"]


def _norm(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    return v


def sort_key(row: dict) -> tuple:
    return tuple(str(row.get(k, "")) for k in KEY)


def read() -> pd.DataFrame:
    if not LEDGER.exists():
        return pd.DataFrame(columns=COLUMNS)
    rows = [json.loads(ln) for ln in LEDGER.read_text().splitlines() if ln.strip()]
    return pd.DataFrame(rows, columns=COLUMNS)


def write(df: pd.DataFrame, *, derive_parquet: bool = True) -> int:
    """Sorted, deterministic, one JSON object per line with sorted keys."""
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = None
    rows = [{k: _norm(v) for k, v in r.items() if k in COLUMNS}
            for r in df[COLUMNS].to_dict("records")]
    rows.sort(key=sort_key)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
                              for r in rows))
    if derive_parquet:
        pd.DataFrame(rows, columns=COLUMNS).to_parquet(DERIVED)
    return len(rows)


def append(new_rows: list[dict]) -> int:
    """Add trials. Existing keys are OVERWRITTEN, never duplicated."""
    cur = read()
    add = pd.DataFrame(new_rows)
    both = pd.concat([cur, add], ignore_index=True)
    both["_k"] = both[list(KEY)].astype(str).apply(tuple, axis=1)
    both = both.drop_duplicates("_k", keep="last").drop(columns="_k")
    return write(both)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--from-parquet":
        n = write(pd.read_parquet(DERIVED))
        print(f"converted {DERIVED.name} -> {LEDGER.name}: {n} rows")
    else:
        print(f"{LEDGER.name}: {len(read())} rows")
