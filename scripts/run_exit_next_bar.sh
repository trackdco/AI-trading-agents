#!/bin/bash
# corrected-exit runs: 3 tapes x 3 books x {armed, flat}
cd /tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad/ql18
mkdir -p output/analysis/xnlogs
jobs=()
for inst in nq nq20a nq17a; do
  if [ "$inst" = "nq" ]; then I=""; NG="--news-gate"; VNG=""; else I="--instrument $inst"; NG=""; VNG="--no-news-gate"; fi
  for arm in "--arm-after 1.0" ""; do
    tag=$( [ -n "$arm" ] && echo arm || echo flat )
    jobs+=("python3 -m scripts.pd_va_backtest $I --levels all --tf 1 --sar --fill-through $NG --max-risk 30 --conviction $arm --exit-next-bar > output/analysis/xnlogs/lv_${inst}_${tag}.log 2>&1")
    jobs+=("python3 -m scripts.vwap_revolve --tf 1 --style retest --max-risk 30 --dedupe --conviction $I $VNG $arm --exit-next-bar > output/analysis/xnlogs/vs_${inst}_${tag}.log 2>&1")
    jobs+=("python3 -m scripts.vwap_revolve --tf 1 --style retest --max-risk 30 --dedupe --conviction --anchor ny $I $VNG $arm --exit-next-bar > output/analysis/xnlogs/vn_${inst}_${tag}.log 2>&1")
  done
done
printf '%s\n' "${jobs[@]}" | xargs -P 4 -I{} bash -c "{}"
echo "=== XN RUNS DONE ==="

# reality gate: results are not quoted until this passes for every tape
for inst in nq nq20a nq17a; do
  i=""; ng="_ng"; ng0=""; [ "$inst" != "nq" ] && { i="_$inst"; ng=""; ng0="_ng0"; }
  python3 /home/user/AI-trading-agents/scripts/reality_gate.py \
    output/analysis/pd_va_trades${i}_lvall_xr30_sar_through_tf1${ng}_arm1_xn.jsonl.gz \
    output/analysis/vwap_rev_tf1_retest${i}${ng0}_xr30_dd_arm1_xn.jsonl.gz \
    output/analysis/vwap_rev_tf1_retest${i}${ng0}_xr30_nyanc_dd_arm1_xn.jsonl.gz --depth 3.0 --target 1.0
done
