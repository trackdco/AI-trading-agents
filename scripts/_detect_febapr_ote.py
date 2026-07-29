#!/usr/bin/env python3
"""Pass 22: checkpointed morning-band (07:45-11:00) re-detection over Feb 2 - Apr 30 2026
with OTE fib cluster levels FORCED ON (the split-test arms need triggers detected against
the ote-augmented cluster set; the committed config default stays OFF so the standard
caches remain valid). Re-running skips done days.

    python -m scripts._detect_febapr_ote
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import src.engine.snapshot as _snap                     # noqa: E402
import src.engine.triggers as _trg                      # noqa: E402
from src.engine.triggers import detect_triggers        # noqa: E402

# force the pass-22 flag ON for this detection run only (both modules bind the name)
_snap._include_ote = lambda: True
_trg._include_ote = lambda: True

NY = "America/New_York"
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
CKPT = Path("output/triggers_febapr_ote_checkpoint.csv")
FINAL = Path("output/triggers_febapr_ote.csv")


def main():
    df = pd.read_parquet(DATA)
    done: set[str] = set()
    if CKPT.exists():
        prev = pd.read_csv(CKPT)
        done = set(pd.to_datetime(prev["ts"], utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d"))
        print(f"checkpoint: {len(prev)} triggers over {len(done)} days", flush=True)

    for d in pd.date_range("2026-02-02", "2026-04-30", freq="D"):
        day = f"{d:%Y-%m-%d}"
        if d.weekday() >= 5 or day in done:
            continue
        start = pd.Timestamp(f"{day} 07:45", tz=NY)
        end = pd.Timestamp(f"{day} 11:00", tz=NY)
        if df[(df["ts_event"] >= start) & (df["ts_event"] <= end)].empty:
            continue                                   # holiday / missing session
        trigs = detect_triggers(df, start=start, end=end)
        rows = pd.DataFrame([t.model_dump() for t in trigs])
        if not rows.empty:
            rows.to_csv(CKPT, mode="a", header=not CKPT.exists(), index=False)
        print(f"  {day}: {len(trigs)} triggers", flush=True)

    out = pd.read_csv(CKPT).sort_values("ts").reset_index(drop=True)
    out.to_csv(FINAL, index=False)
    print(f"wrote {FINAL} ({len(out)} triggers)", flush=True)


if __name__ == "__main__":
    main()
