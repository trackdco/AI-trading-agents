set -euo pipefail
cd /tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18
B="--instrument nqlive --levels all --tf 1 --sar --fill-through --news-gate --max-risk 30 --conviction"
python3 -m scripts.pd_va_backtest $B                 > output/analysis/y_lv.log  2>&1
python3 -m scripts.pd_va_backtest $B --arm-after 1.0 > output/analysis/y_lva.log 2>&1
V="--tf 1 --style retest --max-risk 30 --dedupe --conviction --instrument nqlive"
python3 -m scripts.vwap_revolve $V                             > output/analysis/y_vs.log 2>&1 &
python3 -m scripts.vwap_revolve $V --anchor ny                 > output/analysis/y_vn.log 2>&1 &
python3 -m scripts.vwap_revolve $V --arm-after 1.0             > output/analysis/y_as.log 2>&1 &
python3 -m scripts.vwap_revolve $V --anchor ny --arm-after 1.0 > output/analysis/y_an.log 2>&1 &
wait; echo "=== YESTERDAY RUNS DONE ==="
