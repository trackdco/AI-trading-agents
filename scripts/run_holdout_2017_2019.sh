#!/usr/bin/env bash
# THE 2017-2019 HOLDOUT — one command, mechanical, in the order the pre-reg declares.
#   bash scripts/run_holdout_2017_2019.sh <glbx-mdp3-20170101-20200102.ohlcv-1m.csv.zst>
# Runs from the engine worktree (ql18). Stops at the first failed integrity gate.
# Nothing here may be re-chosen after the data exists: docs/PREREG-holdout-2017-2019.md
set -euo pipefail
RAW="${1:?path to the Databento .csv.zst}"
QL="${QL:-/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$QL"
mkdir -p output/analysis

echo "=== 1. build the continuous tape (integrity gates enforced inside) ==="
python3 "$REPO/scripts/build_nq_2017_2019.py" "$RAW" data/reference

echo "=== 2. boundary continuity with nq_2020_2022 + roll-month check ==="
python3 - <<'PY'
import json, pandas as pd
a = pd.read_parquet("data/reference/nq_2017_2019_1m.parquet")
b = pd.read_parquet("data/reference/nq_2020_2022_1m.parquet")
ta = pd.to_datetime(a.ts_event, utc=True); tb = pd.to_datetime(b.ts_event, utc=True)
ov = set(ta) & set(tb)
if ov:
    ma = a.set_index(ta).loc[sorted(ov)]; mb = b.set_index(tb).loc[sorted(ov)]
    diff = int((ma[["open","high","low","close"]].values != mb[["open","high","low","close"]].values).any(axis=1).sum())
    print(f"overlap {len(ov):,} minutes, {diff} price-differing bars")
    assert diff <= max(2, len(ov)//1000), "overlap does not match nq_2020_2022 - STOP"
else:
    gap = (tb.min() - ta.max()).total_seconds()/3600
    print(f"no shared minutes; boundary gap {gap:.1f}h (Amendment-1 substitute: must be < 96h)")
    assert gap < 96, "boundary gap too large - STOP"
rolls = json.load(open("data/reference/nq_2017_2019_roll_days.json"))
months = sorted({int(r[5:7]) for r in rolls})
print(f"{len(rolls)} rolls in months {months}")
assert set(months) <= {3,6,9,12}, "roll outside Mar/Jun/Sep/Dec - STOP"
print("GATES OK")
PY

echo "=== 3. Gate 0: tick screen per year, and k for Run B ==="
python3 "$REPO/scripts/score_holdout_2017_2019.py" --gate0

echo "=== 4. Run A: value-area book (Test A) ==="
python3 -m scripts.pd_va_backtest --instrument nq17a --tf 1 --sar --fill-through --max-risk 30 \
    > output/analysis/h17_va.log 2>&1
echo "=== 5. Run B: value-area book, era constants (nq17b written by formula in step 3) ==="
python3 -m scripts.pd_va_backtest --instrument nq17b --tf 1 --sar --fill-through \
    --max-risk "$(python3 -c 'import json;print(json.load(open("output/analysis/holdout17_constants.json"))["cap"])')" \
    > output/analysis/h17_vb.log 2>&1
echo "=== 6. the empire: level book flat + armed ==="
B="--instrument nq17a --levels all --tf 1 --sar --fill-through --max-risk 30 --conviction"
python3 -m scripts.pd_va_backtest $B                 > output/analysis/h17_lv.log  2>&1
python3 -m scripts.pd_va_backtest $B --arm-after 1.0 > output/analysis/h17_lva.log 2>&1
echo "=== 7. the empire: four vwap books in parallel ==="
V="--tf 1 --style retest --max-risk 30 --dedupe --conviction --instrument nq17a --no-news-gate"
python3 -m scripts.vwap_revolve $V                             > output/analysis/h17_vs.log 2>&1 &
python3 -m scripts.vwap_revolve $V --anchor ny                 > output/analysis/h17_vn.log 2>&1 &
python3 -m scripts.vwap_revolve $V --arm-after 1.0             > output/analysis/h17_as.log 2>&1 &
python3 -m scripts.vwap_revolve $V --anchor ny --arm-after 1.0 > output/analysis/h17_an.log 2>&1 &
wait
echo "=== 8. VERDICTS (Tests A-E, predictions P1-P6) ==="
python3 "$REPO/scripts/score_holdout_2017_2019.py" | tee output/analysis/holdout17_verdict.txt
echo "=== DONE — record output/analysis/holdout17_verdict.txt verbatim in the findings doc ==="
