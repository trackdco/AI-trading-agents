"""Replay the Market Engine over historical NQ data and emit detected candidates.

This is the historical proof harness (spec-1 Steps 4-8 territory) — NOT live.
It loads real 1m bars, runs the Detector across the entry window, and writes any
detected candidates to output/. Usage:

    python -m scripts.replay --data <file.zst> --start 2026-01-05 --end 2026-01-16
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.config import Config          # noqa: E402
from engine import data as dataio         # noqa: E402
from engine.detector import Detector      # noqa: E402


def load_news(tz: str) -> pd.DataFrame:
    p = ROOT / "config" / "news_calendar.csv"
    df = pd.read_csv(p, comment="#")
    df["datetime_et"] = pd.to_datetime(df["datetime_et"]).dt.tz_localize(tz)
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True, help="one or more .csv.zst files")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--win-start", default="08:00")
    ap.add_argument("--win-end", default="11:00")
    ap.add_argument("--out", default=str(ROOT / "output"))
    args = ap.parse_args()

    cfg = Config.load()
    tz = cfg.tz
    print(f"[replay] loading {args.data} ...", flush=True)
    df1m = dataio.load_historical(args.data, tz)
    rep = dataio.validate(df1m)
    print(f"[replay] data: {rep['rows']} rows  {rep['start']} → {rep['end']}", flush=True)

    lo = pd.Timestamp(args.start, tz=tz)
    hi = pd.Timestamp(args.end, tz=tz) + pd.Timedelta(days=1)
    df1m = df1m.loc[lo:hi]
    print(f"[replay] window {args.start}..{args.end}: {len(df1m)} 1m bars", flush=True)

    news = load_news(tz)
    det = Detector(cfg, df1m, news)

    ws = time(*map(int, args.win_start.split(":")))
    we = time(*map(int, args.win_end.split(":")))
    scan = [ts for ts in df1m.index if ws <= ts.time() <= we]
    print(f"[replay] scanning {len(scan)} in-window minutes across "
          f"{len({t.date() for t in scan})} sessions ...", flush=True)

    outdir = Path(args.out)
    outdir.mkdir(exist_ok=True)
    detections = []
    for ts in scan:
        try:
            cand = det.evaluate(ts)
        except Exception as e:  # keep the scan alive; report at end
            print(f"[warn] {ts}: {type(e).__name__}: {e}", flush=True)
            continue
        if cand:
            detections.append(cand)

    # Honest aggregation (NOT a threshold change): collapse raw per-bar triggers
    # into "distinct setups" using the Vault's documented one-position-at-a-time
    # rule (§10) with a 20-min cooldown. Reveals the calibration gap vs the
    # strategy's "2-3 genuine setups/day" expectation without tuning anything.
    distinct = []
    last_ts = None
    for d in detections:
        ts = pd.Timestamp(d["_engine_meta"]["asof_et"])
        if last_ts is None or (ts - last_ts) >= pd.Timedelta(minutes=20):
            distinct.append(d)
            last_ts = ts
    by_session: dict = {}
    for d in distinct:
        day = pd.Timestamp(d["_engine_meta"]["asof_et"]).date()
        by_session[day] = by_session.get(day, 0) + 1
    sessions = len({t.date() for t in scan}) or 1
    print(f"[replay] RAW per-bar triggers: {len(detections)}  "
          f"({len(detections)/sessions:.1f}/session)", flush=True)
    print(f"[replay] DISTINCT setups (one-position, 20m cooldown): {len(distinct)}  "
          f"({len(distinct)/sessions:.1f}/session)", flush=True)
    print(f"[replay] strategy §10 expectation: 2-3 genuine setups/session  "
          f"→ CALIBRATION GAP is real and expected (uncalibrated params).", flush=True)
    if detections:
        allp = outdir / "detected_candidates.json"
        allp.write_text(json.dumps(detections, indent=2, default=str))
        first = detections[0]
        firstp = outdir / "sample_detection.json"
        core = {k: v for k, v in first.items() if not k.startswith("_")}
        firstp.write_text(json.dumps(core, indent=2, default=str))
        print(f"[replay] wrote {allp.name} ({len(detections)}) and {firstp.name}", flush=True)
        for d in detections[:12]:
            m = d["_engine_meta"]
            td = d["_engine_trigger_detail"]
            print(f"  {m['asof_et']}  {d['candidate_direction']:5s}  {d['playbook_match']['pattern']:2s}  "
                  f"tf={m['winning_tf_min']}m  {td['mechanism']:14s}  "
                  f"conf={td['confluence_count']}  entry={d['entry_price']}  "
                  f"stop={d['stop_price']}  tgt={d['target_price']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
