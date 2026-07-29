#!/usr/bin/env python3
"""DESK EXPORT — emit a single JSON file for the web dashboard (THE DESK).

CONSUMES committed artifacts only and regenerates NOTHING (Angus's rule: consume,
never rebuild). The authoritative trade list, sizing and P&L come from the frozen
`output/baseline_book.parquet` (the 400-trade parity ground truth); entry/exit/
pattern/book are enriched by an exact join into the committed `trade_matrix`
(NY) and `london_matrix` (LONDON). Any field the artifacts genuinely do not carry
is emitted as null (or omitted) and reported in meta.missing_fields — never invented.

    python -m scripts.export_dashboard                       # -> output/desk-export.json
    python -m scripts.export_dashboard --out /tmp/desk.json

Output is deterministic (byte-identical for identical inputs) except meta.generated_at.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output"
SCHEMA = "desk-export/v2"


def git_commit():
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            stderr=subprocess.DEVNULL).decode().strip()
        return sha or None
    except Exception:
        return None


def _lookup(path):
    """Index a candidate matrix by the exact baseline trade key so enrichment is 1:1.

    Key = (day, fill-minute-UTC, direction, risk-pts, 1-lot-dollars). Verified unique
    against baseline_book (264/264 NY, 136/136 LONDON, zero collisions)."""
    mx = pd.read_parquet(path).copy()
    mx["key_ts"] = pd.to_datetime(mx["fill"], utc=True).dt.floor("min")
    d = {}
    for _, r in mx.iterrows():
        k = (str(r["day"]), r["key_ts"], str(r["direction"]),
             round(float(r["risk"]), 2), round(float(r["dollars"]), 1))
        d[k] = r
    return d


def _f(v):
    return None if v is None or pd.isna(v) else round(float(v), 2)


def _s(v):
    return None if v is None or pd.isna(v) else str(v)


def build_export(generated_at=None):
    """Return the desk-export/v2 object built purely from committed artifacts."""
    B = pd.read_parquet(OUT_DIR / "baseline_book.parquet").copy()
    B["key_ts"] = pd.to_datetime(B["fill"], utc=True).dt.floor("min")
    B = B.sort_values(["key_ts", "session", "direction"]).reset_index(drop=True)
    # disambiguate trades that collide on session/day/minute/direction (matches the
    # parity harness's seq), so every id is stable and unique.
    B["seq"] = B.groupby(["session", "day", "key_ts", "direction"]).cumcount()

    ny = _lookup(OUT_DIR / "trade_matrix.parquet")
    lo = _lookup(OUT_DIR / "london_matrix.parquet")

    missing = {"checks"}  # London W/FAR/ROOM/ASIA booleans are not carried by any artifact
    trades = []
    for _, r in B.iterrows():
        session = str(r["session"])
        lk = ny if session == "NY" else lo
        key = (str(r["day"]), r["key_ts"], str(r["direction"]),
               round(float(r["risk_pts"]), 2), round(float(r["dollars_1lot"]), 1))
        m = lk.get(key)
        entry = _f(m["entry"]) if m is not None else None
        exit_ = _f(m["exit_price"]) if m is not None else None
        pattern = _s(m["pattern"]) if m is not None else None
        book = _s(m["book"]) if m is not None else None
        for name, val in (("entry", entry), ("exit", exit_),
                          ("pattern", pattern), ("book", book)):
            if val is None:
                missing.add(name)

        side = str(r["direction"]).upper()
        seq = int(r["seq"])
        risk_pts = round(float(r["risk_pts"]), 2)
        micros = int(r["micros"])
        risk_d = float(r["risk_dollars"])
        pl = float(r["pl"])
        trades.append({
            "id": f"{session}-{r['day']}-{r['key_ts']:%H%M}-{side}-{seq}",
            "ts": r["key_ts"].isoformat(),
            "session": session,
            "book": book,
            "side": side,
            "pattern": pattern,
            "conviction": round(float(r["conviction"]), 4),
            "entry": entry,
            "exit": exit_,
            "risk_pts": risk_pts,
            "stop_pts": risk_pts,          # in this canon the stop distance IS the risk in points
            "micros": micros,
            "contracts": float(micros),    # size is expressed only in MNQ micros; contracts == micros
            "pnl": round(pl, 2),           # gross dollars for the sized micros (no fees modeled)
            "r": round(pl / risk_d, 1) if risk_d else None,
            "_seq": seq,
        })

    trades.sort(key=lambda t: (t["ts"], t["session"], t["side"], t["_seq"]))
    for t in trades:
        del t["_seq"]

    days = B["day"].astype(str)
    meta = {
        "schema": SCHEMA,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "source": "baseline_book",
        "universe": "both books, every day",
        "date_range": {"from": days.min(), "to": days.max()},
        "trade_count": int(len(B)),
        "total_pnl": round(float(B["pl"].sum()), 2),
        "sizing": "frozen dollar-risk schedule",
        "notes": ("2-year canon baseline (combined NY+LONDON books, every day); "
                  "conviction dollar-risk floor schedule at 1-lot; P&L is GROSS in dollars "
                  "for the sized MNQ micros (no commissions/fees); contracts == micros (MNQ); "
                  "r = pnl / dollar-risk."),
        "missing_fields": sorted(missing),
    }
    return {"meta": meta, "trades": trades, "spine_events": []}


def write_export(obj, out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(
        description="Emit desk-export.json for THE DESK from committed artifacts only.")
    ap.add_argument("--out", default=str(OUT_DIR / "desk-export.json"),
                    help="output path (default output/desk-export.json)")
    args = ap.parse_args()

    obj = build_export()
    write_export(obj, args.out)

    m, tr = obj["meta"], obj["trades"]
    ny = sum(t["session"] == "NY" for t in tr)
    lo = sum(t["session"] == "LONDON" for t in tr)
    print(f"wrote {args.out}")
    print(f"  schema {m['schema']}   commit {m['git_commit']}")
    print(f"  trades {m['trade_count']}  (NY {ny} / LONDON {lo})")
    print(f"  range  {m['date_range']['from']} -> {m['date_range']['to']}")
    print(f"  total P&L ${m['total_pnl']:+,.2f}")
    print(f"  missing_fields: {m['missing_fields']}")
    print("  spine_events: " + (f"{len(obj['spine_events'])}" if obj["spine_events"]
                                 else "none (historical artifacts carry no guard trips)"))


if __name__ == "__main__":
    sys.exit(main())
