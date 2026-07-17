#!/usr/bin/env python3
"""ANGUS pass-6 split test: target model {default, vwap_revert, walk_menu} x VWAP-touch {off,on}.
Config-only, on the re-detected triggers (with vwap_touched). Restores config at the end.
touch off = require_bb_vwap:true, require_vwap_touch:false (current composition gate)
touch on  = require_bb_vwap:false, require_vwap_touch:true (price must reach a VWAP band)
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
    ("default", "off"), ("default", "on"),
    ("vwap_revert", "off"), ("vwap_revert", "on"),
    ("walk_menu", "off"), ("walk_menu", "on"),
]


def set_cfg(model, touch):
    txt = ORIG
    txt = re.sub(r"(\n  model: )\w+", r"\g<1>" + model, txt, count=1)
    tv = "true" if touch == "on" else "false"
    bb = "false" if touch == "on" else "true"
    txt = re.sub(r"(\n  require_vwap_touch: )\w+", r"\g<1>" + tv, txt, count=1)
    txt = re.sub(r"(\n  require_bb_vwap: )\w+", r"\g<1>" + bb, txt, count=1)
    CFG.write_text(txt)


def run_once():
    for m in list(sys.modules):
        if m.startswith("src.backtest") or m.startswith("scripts.run_backtest"):
            del sys.modules[m]
    import importlib
    runner = importlib.import_module("scripts.run_backtest_feb")
    buf = io.StringIO()
    with redirect_stdout(buf):
        runner.main()
    return buf.getvalue()


def parse(out):
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
        for model, touch in ARMS:
            set_cfg(model, touch)
            d = parse(run_once())
            d["arm"] = f"{model}/{touch}"
            rows.append(d)
            print(f"done {d['arm']}: {d}", flush=True)
    finally:
        CFG.write_text(ORIG)
        print("config restored", flush=True)

    print("\n===== SPLIT SWEEP (target model x VWAP-touch) =====")
    print(f"{'arm':20s} {'tr':>4s} {'wins':>5s} {'win%':>6s} {'totR':>8s} {'R/tr':>7s} {'MATCH':>6s} {'EXTRA':>6s}")
    for d in rows:
        t, w = d.get("trades", 0), d.get("wins", 0)
        wr = 100 * w / t if t else 0
        rpt = d.get("R", 0) / t if t else 0
        print(f"{d['arm']:20s} {t:>4d} {w:>5d} {wr:>5.1f}% {d.get('R',0):>+8.2f} {rpt:>+7.3f} "
              f"{d.get('matched',0):>6d} {d.get('extra',0):>6d}")


if __name__ == "__main__":
    main()
