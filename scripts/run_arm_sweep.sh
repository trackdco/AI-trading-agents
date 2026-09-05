set -euo pipefail
cd /tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18
B="--levels all --tf 1 --sar --fill-through --news-gate --max-risk 30 --conviction"
V="--tf 1 --style retest --max-risk 30 --dedupe --conviction"
echo "=== level book at 0.75 and 1.25 (vwap dedupe needs these first) ==="
python3 -m scripts.pd_va_backtest $B --arm-after 0.75 > output/analysis/as_lv075.log 2>&1 &
python3 -m scripts.pd_va_backtest $B --arm-after 1.25 > output/analysis/as_lv125.log 2>&1 &
python3 -m scripts.vwap_revolve $V --arm-after 0.5              > output/analysis/as_vs05.log 2>&1 &
python3 -m scripts.vwap_revolve $V --anchor ny --arm-after 0.5  > output/analysis/as_vn05.log 2>&1 &
python3 -m scripts.vwap_revolve $V --arm-after 2.0              > output/analysis/as_vs20.log 2>&1 &
python3 -m scripts.vwap_revolve $V --anchor ny --arm-after 2.0  > output/analysis/as_vn20.log 2>&1 &
wait
echo "=== vwap at 0.75 and 1.25 ==="
python3 -m scripts.vwap_revolve $V --arm-after 0.75              > output/analysis/as_vs075.log 2>&1 &
python3 -m scripts.vwap_revolve $V --anchor ny --arm-after 0.75  > output/analysis/as_vn075.log 2>&1 &
python3 -m scripts.vwap_revolve $V --arm-after 1.25              > output/analysis/as_vs125.log 2>&1 &
python3 -m scripts.vwap_revolve $V --anchor ny --arm-after 1.25  > output/analysis/as_vn125.log 2>&1 &
wait
echo "=== ARM SWEEP DONE ==="
