set -euo pipefail
cd /tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18
B="--instrument gc --levels all --tf 1 --sar --fill-through --news-gate --max-risk 9 --conviction"
for f in 1.0 1.25 2.0 2.5; do
  python3 -m scripts.pd_va_backtest $B --min-risk $f                 > output/analysis/gcf_${f}.log  2>&1 &
  python3 -m scripts.pd_va_backtest $B --min-risk $f --arm-after 1.0 > output/analysis/gcf_${f}a.log 2>&1 &
done
wait
echo "=== FLOOR SWEEP DONE ==="; ls output/analysis/ | grep "gc_lvall_mr"
