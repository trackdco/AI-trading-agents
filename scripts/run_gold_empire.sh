set -euo pipefail
cd /tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18
# Gold constants at the NQ certification ratios (S22 validated the ratio method
# natively): floor 1.5 / depth 0.9 / bin 0.3 from INSTRUMENTS["gc"]; stop cap
# = 6x floor = 9.0pt (NQ 30/5). News gate ON - the calendar is US high-impact
# pre-market prints, which move gold as much as NQ, and it covers 2023-26.
echo "=== gold level book, flat + armed ==="
B="--instrument gc --levels all --tf 1 --sar --fill-through --news-gate --max-risk 9 --conviction"
python3 -m scripts.pd_va_backtest $B                 > output/analysis/gc_lv.log  2>&1
python3 -m scripts.pd_va_backtest $B --arm-after 1.0 > output/analysis/gc_lva.log 2>&1
echo "=== gold vwap books x4 ==="
V="--tf 1 --style retest --max-risk 9 --dedupe --conviction --instrument gc"
python3 -m scripts.vwap_revolve $V                             > output/analysis/gc_vs.log 2>&1 &
python3 -m scripts.vwap_revolve $V --anchor ny                 > output/analysis/gc_vn.log 2>&1 &
python3 -m scripts.vwap_revolve $V --arm-after 1.0             > output/analysis/gc_as.log 2>&1 &
python3 -m scripts.vwap_revolve $V --anchor ny --arm-after 1.0 > output/analysis/gc_an.log 2>&1 &
wait
echo "=== GOLD RUNS DONE ==="; ls output/analysis/ | grep -E "_gc_|gc_xr"
