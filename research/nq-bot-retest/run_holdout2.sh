#!/usr/bin/env bash
# Holdout-2 runs — PREREGISTRATION-2.md §5, fixed before the data is touched.
#
#   usage: run_holdout2.sh <prepared_data_dir>
#
# <prepared_data_dir>: output of prepare_holdout_data.py on the 2018-08-01 .. 2021-09-30 tape
# (combined_1min.csv + htf_*.csv). Every run starts COLD on the first bar (2018-08-01), as the
# bot's own backtests do, and replays to 2021-08-31. The verdict counts entries 2018-09-01 ..
# 2021-08-31 (August 2018 warms the engine).
#   batch 1: the three cap-free cells (V2-1 C1a×C3a, V2-2 C1a×C3b, V2-3 C1b×C3a) + untouched control
#   batch 2: the three capped controls + 2x-slippage stress for the three cells (abort condition)
#   batch 3: the intrabar counterfactual for the three cells (disclosed, never a candidate)
# Then the analysis: alpha 0.025, seed 20260907, verdict = minimum across the three cells.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
DATA_DIR=$(cd "$1" && pwd)
P=${PYTHON:-/tmp/claude-0/venv_aitb/bin/python}
OUT=$HERE/data/holdout2
mkdir -p "$OUT/logs" "$OUT/ckpt"
printf 'logs/\nckpt/\n*.json\n!HOLDOUT2_verdict.json\n!controls_capped.json\n!stress_2x_slippage.json\n!intrabar_counterfactual.json\n' > "$OUT/.gitignore"
printf '*.pkl\n*.pkl.tmp\n' > "$OUT/ckpt/.gitignore"

run() {  # run <out_name> <driver flags...>
  local name=$1; shift
  nohup "$P" "$HERE/retest_backtest.py" --data "$DATA_DIR/combined_1min.csv" --htf-dir "$DATA_DIR" \
    --start 2018-08-01 --end 2021-08-31 \
    --out "$OUT/$name.json" --checkpoint "$OUT/ckpt/$name.pkl" --checkpoint-every 25000 --resume \
    --progress 25000 --fast-features --record-levels "$@" > "$OUT/logs/$name.log" 2>&1 &
  echo "  launched $name (pid $!)"
}

echo "batch 1: cap-free cells + untouched control"
run h2_V21_C1a_C3a_capfree --stop-floor a5_10pt   --rr-gate removed --rth-only --cap-lifted
run h2_V22_C1a_C3b_capfree --stop-floor a5_10pt   --rr-gate kept    --rth-only --cap-lifted
run h2_V23_C1b_C3a_capfree --stop-floor a22_2xatr --rr-gate removed --rth-only --cap-lifted
run h2_untouched           --stop-floor none      --rr-gate kept
wait
echo "batch 2: capped controls + 2x slippage stress"
run h2_ctl_C1a_C3a_capped  --stop-floor a5_10pt   --rr-gate removed --rth-only
run h2_ctl_C1a_C3b_capped  --stop-floor a5_10pt   --rr-gate kept    --rth-only
run h2_ctl_C1b_C3a_capped  --stop-floor a22_2xatr --rr-gate removed --rth-only
run h2_stress_V21          --stop-floor a5_10pt   --rr-gate removed --rth-only --cap-lifted --slippage-mult 2.0
wait
run h2_stress_V22          --stop-floor a5_10pt   --rr-gate kept    --rth-only --cap-lifted --slippage-mult 2.0
run h2_stress_V23          --stop-floor a22_2xatr --rr-gate removed --rth-only --cap-lifted --slippage-mult 2.0
echo "batch 3: intrabar counterfactual (kill switch off, per PREREGISTRATION-2 §3)"
run h2_intrabar_V21        --stop-floor a5_10pt   --rr-gate removed --rth-only --cap-lifted --intrabar-stops --no-kill-switch
run h2_intrabar_V22        --stop-floor a5_10pt   --rr-gate kept    --rth-only --cap-lifted --intrabar-stops --no-kill-switch
wait
run h2_intrabar_V23        --stop-floor a22_2xatr --rr-gate removed --rth-only --cap-lifted --intrabar-stops --no-kill-switch
wait

echo "analysis (PREREGISTRATION-2 §4: alpha 0.025, seed 20260907, entries 2018-09-01 .. 2021-08-31)"
A=(--count-from 2018-09-01 --count-to 2021-08-31 --alpha 0.025 --seed 20260907)
CELLS=(V2-1_C1a_C3a=$OUT/h2_V21_C1a_C3a_capfree.json V2-2_C1a_C3b=$OUT/h2_V22_C1a_C3b_capfree.json V2-3_C1b_C3a=$OUT/h2_V23_C1b_C3a_capfree.json)
STRESS=(V2-1_C1a_C3a=$OUT/h2_stress_V21.json V2-2_C1a_C3b=$OUT/h2_stress_V22.json V2-3_C1b_C3a=$OUT/h2_stress_V23.json)
"$P" "$HERE/analyze_retest.py" "${CELLS[@]}" --control untouched=$OUT/h2_untouched.json --stress "${STRESS[@]}" "${A[@]}" --verdict \
  --md "$OUT/HOLDOUT2_verdict.md" --json "$OUT/HOLDOUT2_verdict.json" | tee "$OUT/logs/analysis_verdict.txt"
"$P" "$HERE/analyze_retest.py" capped_C1a_C3a=$OUT/h2_ctl_C1a_C3a_capped.json capped_C1a_C3b=$OUT/h2_ctl_C1a_C3b_capped.json capped_C1b_C3a=$OUT/h2_ctl_C1b_C3a_capped.json \
  --control untouched=$OUT/h2_untouched.json "${A[@]}" --md "$OUT/controls_capped.md" --json "$OUT/controls_capped.json" | tee "$OUT/logs/analysis_controls.txt"
"$P" "$HERE/analyze_retest.py" "${STRESS[@]}" "${A[@]}" --md "$OUT/stress_2x_slippage.md" --json "$OUT/stress_2x_slippage.json" | tee "$OUT/logs/analysis_stress.txt"
"$P" "$HERE/analyze_retest.py" V2-1=$OUT/h2_intrabar_V21.json V2-2=$OUT/h2_intrabar_V22.json V2-3=$OUT/h2_intrabar_V23.json "${A[@]}" \
  --md "$OUT/intrabar_counterfactual.md" --json "$OUT/intrabar_counterfactual.json" | tee "$OUT/logs/analysis_intrabar.txt"
( cd "$OUT" && sha256sum *.json > SEALS.sha256 )
echo "done — seals in $OUT/SEALS.sha256"
