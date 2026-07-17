#!/usr/bin/env python3
"""Isolated-arm sweep for the winner-capture diagnosis. Config-only (no new code):
entry variant E1/E2/E3 x rr_floor 2.0/1.5. Restores config at the end.
Reports per arm: trades, win%, total R, and MATCHED/MISSED/EXTRA vs the 28 hand trades.
"""
import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
CFG = Path("config/strategy.yaml")
ORIG = CFG.read_text()

ARMS = [
    ("E1", "2.0"), ("E2", "2.0"), ("E3", "2.0"),
    ("E1", "1.5"), ("E2", "1.5"), ("E3", "1.5"),
]


def set_cfg(variant: str, floor: str):
    txt = ORIG
    # entry.variant is the only 'variant: E?' token; management is 'variant: V0'
    txt = re.sub(r"(\n  variant: )E[123]", r"\g<1>" + variant, txt, count=1)
    txt = re.sub(r"(\n  rr_floor: )[0-9.]+", r"\g<1>" + floor, txt, count=1)
    CFG.write_text(txt)


def run_once():
    # fresh import each arm so load_backtest_config re-reads
    for m in list(sys.modules):
        if m.startswith("src.backtest") or m.startswith("scripts.run_backtest"):
            del sys.modules[m]
    import importlib
    runner = importlib.import_module("scripts.run_backtest_feb")
    buf = io.StringIO()
    with redirect_stdout(buf):
        runner.main()
    return buf.getvalue()


def parse(out: str) -> dict:
    d = {}
    m = re.search(r"trades: (\d+)  wins: (\d+)  losses: (\d+)", out)
    if m:
        d["trades"], d["wins"], d["losses"] = int(m[1]), int(m[2]), int(m[3])
    m = re.search(r"total R: ([+\-0-9.]+)", out)
    if m:
        d["R"] = float(m[1])
    m = re.search(r"MATCHED (\d+) \| MISSED (\d+) \| EXTRA (\d+)", out)
    if m:
        d["matched"], d["missed"], d["extra"] = int(m[1]), int(m[2]), int(m[3])
    return d


def main():
    rows = []
    try:
        for variant, floor in ARMS:
            set_cfg(variant, floor)
            out = run_once()
            d = parse(out)
            d["arm"] = f"{variant}/{floor}"
            rows.append(d)
            print(f"done {d['arm']}: {d}", flush=True)
    finally:
        CFG.write_text(ORIG)  # always restore
        print("config restored", flush=True)

    print("\n\n===== ARM SWEEP RESULTS =====")
    hdr = f"{'arm':10s} {'trades':>6s} {'wins':>5s} {'win%':>6s} {'totR':>8s} {'R/trade':>8s} {'MATCH':>6s} {'MISS':>5s} {'EXTRA':>6s}"
    print(hdr)
    for d in rows:
        t, w = d.get("trades", 0), d.get("wins", 0)
        wr = 100 * w / t if t else 0
        rpt = d.get("R", 0) / t if t else 0
        print(f"{d['arm']:10s} {t:>6d} {w:>5d} {wr:>5.1f}% {d.get('R',0):>+8.2f} {rpt:>+8.3f} "
              f"{d.get('matched',0):>6d} {d.get('missed',0):>5d} {d.get('extra',0):>6d}")


if __name__ == "__main__":
    main()
