#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.." || exit 1
BR=claude/london-canon-strategy-3p57jk
push() { git add -A docs/ scripts/ >/dev/null 2>&1
  git commit -q -m "$1" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" \
    -m "Claude-Session: https://claude.ai/code/session_01KjCxeeipm4yQ6KrsqKT6wP" >/dev/null 2>&1 || { echo "  (nothing)"; return 0; }
  for d in 2 4 8 16; do git push -u origin "$BR" >/dev/null 2>&1 && { echo "  pushed"; return 0; }; sleep "$d"; done
  echo "  PUSH FAILED"; }
# preflight is a hard gate for stages 2 and 4 (they load the NY book); 0 and 3 are independent
if .venv/bin/python -m scripts.london_combined_job --stage preflight > output/logs/cj_pre.log 2>&1; then
  PRE=ok; else PRE=fail; echo "PREFLIGHT FAILED"; tail -12 output/logs/cj_pre.log; fi
for S in 0 2 3 4; do
  if [ "$PRE" = fail ] && { [ "$S" = 2 ] || [ "$S" = 4 ]; }; then
    echo "=== stage $S SKIPPED (depends on failed preflight) ==="
    printf '# Combined job — Stage %s: SKIPPED\n\nPreflight failed, so the NY book could not be trusted. This stage depends on it and was not run. No numbers.\n' "$S" > "docs/COMBINED-JOB-STAGE${S}-SKIPPED.md"
    push "Combined job stage ${S}: SKIPPED — preflight failed"; continue; fi
  echo "=== stage $S starting $(date -u +%H:%M:%SZ) ==="
  if .venv/bin/python -m scripts.london_combined_job --stage "$S" > "output/logs/cj_${S}.log" 2>&1; then
    tail -2 "output/logs/cj_${S}.log"; push "Combined job stage ${S}: verdict"
  else
    echo "STAGE $S FAILED"; tail -20 "output/logs/cj_${S}.log"
    { echo "# Combined job — Stage ${S}: FAILED"; echo; echo "No verdict should be read from this stage."; echo; echo '```'; tail -40 "output/logs/cj_${S}.log"; echo '```'; } > "docs/COMBINED-JOB-STAGE${S}-FAILED.md"
    push "Combined job stage ${S}: FAILED — no verdict"; fi
done
echo "=== done $(date -u +%H:%M:%SZ) ==="
