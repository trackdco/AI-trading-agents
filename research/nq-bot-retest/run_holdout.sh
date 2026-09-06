#!/usr/bin/env bash
# Holdout runs — PREREGISTRATION.md §5-bis, fixed before the holdout export exists.
#
#   usage: run_holdout.sh <holdout_data_dir> [last_ET_date]
#
# <holdout_data_dir> is the output of prepare_holdout_data.py (union combined_1min.csv + htf_*.csv).
# Every run CONTINUES from the sealed 2024-12-31 state of the matching development run
# (data/dev/final/<name>.pkl), replaying 2025-01-01 -> the end of the export in one pass.
#   batch 1: the four pre-registered combinations + the untouched bot (control, reported only)
#   batch 2: 30pt-cap-lifted sensitivity for the four combinations
#   batch 3: 2x-slippage stress (abort condition 2) for the four combinations
# Then the analysis: holdout (entries >= 2025-09-01, verdict), contaminated 2025-01..08 (reported),
# sensitivity and stress tables. One read.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
DATA_DIR=$(cd "$1" && pwd)
END=${2:-}
P=${PYTHON:-/tmp/claude-0/venv_aitb/bin/python}
OUT=$HERE/data/holdout
mkdir -p "$OUT/logs" "$OUT/ckpt"
printf '*.pkl\n*.pkl.tmp\n' > "$OUT/ckpt/.gitignore"
ENDARG=(); [ -n "$END" ] && ENDARG=(--end "$END")

run() {  # run <out_name> <dev_base> <driver flags...>
  local name=$1 base=$2; shift 2
  nohup "$P" "$HERE/retest_backtest.py" --data "$DATA_DIR/combined_1min.csv" --htf-dir "$DATA_DIR" \
    --continue-from "$HERE/data/dev/final/$base.pkl" "${ENDARG[@]}" \
    --out "$OUT/$name.json" --checkpoint "$OUT/ckpt/$name.pkl" --checkpoint-every 25000 --resume \
    --progress 25000 --fast-features "$@" > "$OUT/logs/$name.log" 2>&1 &
  echo "  launched $name (pid $!)"
}

echo "batch 1: combinations + control"
run hold_C1a_C3a   dev_C1a_C3a   --stop-floor a5_10pt   --rr-gate removed --rth-only
run hold_C1a_C3b   dev_C1a_C3b   --stop-floor a5_10pt   --rr-gate kept    --rth-only
run hold_C1b_C3a   dev_C1b_C3a   --stop-floor a22_2xatr --rr-gate removed --rth-only
run hold_C1b_C3b   dev_C1b_C3b   --stop-floor a22_2xatr --rr-gate kept    --rth-only
run hold_untouched dev_untouched --stop-floor none      --rr-gate kept
wait
echo "batch 2: sensitivity — 30pt cap lifted from 2025-01-01"
run sens_C1a_C3a dev_C1a_C3a --stop-floor a5_10pt   --rr-gate removed --rth-only --cap-lifted
run sens_C1a_C3b dev_C1a_C3b --stop-floor a5_10pt   --rr-gate kept    --rth-only --cap-lifted
run sens_C1b_C3a dev_C1b_C3a --stop-floor a22_2xatr --rr-gate removed --rth-only --cap-lifted
run sens_C1b_C3b dev_C1b_C3b --stop-floor a22_2xatr --rr-gate kept    --rth-only --cap-lifted
wait
echo "batch 3: stress — 2x slippage (1.00 RTH / 2.00 ETH) from 2025-01-01"
run stress_C1a_C3a dev_C1a_C3a --stop-floor a5_10pt   --rr-gate removed --rth-only --slippage-mult 2.0
run stress_C1a_C3b dev_C1a_C3b --stop-floor a5_10pt   --rr-gate kept    --rth-only --slippage-mult 2.0
run stress_C1b_C3a dev_C1b_C3a --stop-floor a22_2xatr --rr-gate removed --rth-only --slippage-mult 2.0
run stress_C1b_C3b dev_C1b_C3b --stop-floor a22_2xatr --rr-gate kept    --rth-only --slippage-mult 2.0
wait

echo "analysis"
COMBOS=(C1a_C3a=$OUT/hold_C1a_C3a.json C1a_C3b=$OUT/hold_C1a_C3b.json C1b_C3a=$OUT/hold_C1b_C3a.json C1b_C3b=$OUT/hold_C1b_C3b.json)
STRESS=(C1a_C3a=$OUT/stress_C1a_C3a.json C1a_C3b=$OUT/stress_C1a_C3b.json C1b_C3a=$OUT/stress_C1b_C3a.json C1b_C3b=$OUT/stress_C1b_C3b.json)
SENS=(C1a_C3a=$OUT/sens_C1a_C3a.json C1a_C3b=$OUT/sens_C1a_C3b.json C1b_C3a=$OUT/sens_C1b_C3a.json C1b_C3b=$OUT/sens_C1b_C3b.json)
"$P" "$HERE/analyze_retest.py" "${COMBOS[@]}" --control untouched=$OUT/hold_untouched.json \
  --stress "${STRESS[@]}" --count-from 2025-09-01 --verdict \
  --md "$OUT/HOLDOUT_verdict.md" --json "$OUT/HOLDOUT_verdict.json" | tee "$OUT/logs/analysis_holdout.txt"
"$P" "$HERE/analyze_retest.py" "${COMBOS[@]}" --control untouched=$OUT/hold_untouched.json \
  --count-from 2025-01-01 --count-to 2025-08-31 \
  --md "$OUT/contaminated_2025-01_08.md" --json "$OUT/contaminated_2025-01_08.json" | tee "$OUT/logs/analysis_contaminated.txt"
"$P" "$HERE/analyze_retest.py" "${SENS[@]}" --count-from 2025-09-01 \
  --md "$OUT/sensitivity_cap_lifted_holdout.md" --json "$OUT/sensitivity_cap_lifted_holdout.json" | tee "$OUT/logs/analysis_sensitivity.txt"
"$P" "$HERE/analyze_retest.py" "${STRESS[@]}" --count-from 2025-09-01 \
  --md "$OUT/stress_2x_slippage_holdout.md" --json "$OUT/stress_2x_slippage_holdout.json" | tee "$OUT/logs/analysis_stress.txt"
( cd "$OUT" && sha256sum *.json > SEALS.sha256 )
echo "done — seals in $OUT/SEALS.sha256"
