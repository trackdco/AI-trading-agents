#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.." || exit 1
BR=claude/london-canon-strategy-3p57jk
push() {
  git add -A docs/ scripts/ >/dev/null 2>&1
  git commit -q -m "$1" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" \
    -m "Claude-Session: https://claude.ai/code/session_01KjCxeeipm4yQ6KrsqKT6wP" >/dev/null 2>&1 \
    || { echo "  (nothing to commit)"; return 0; }
  for d in 2 4 8 16; do
    git push -u origin "$BR" >/dev/null 2>&1 && { echo "  pushed"; return 0; }
    sleep "$d"
  done
  echo "  PUSH FAILED"; return 1
}
for S in 1 2 3; do
  echo "=== stage $S starting $(date -u +%H:%M:%SZ) ==="
  if .venv/bin/python -m scripts.combined_book_audit --stage "$S" > "output/logs/combined_s${S}.log" 2>&1; then
    tail -2 "output/logs/combined_s${S}.log"; push "Combined NY+London audit stage ${S}: verdict"
  else
    echo "STAGE $S FAILED"; tail -20 "output/logs/combined_s${S}.log"
    { echo "# Combined audit — Stage ${S}: FAILED"; echo; echo "No verdict should be read from this stage."; echo; echo '```'; tail -40 "output/logs/combined_s${S}.log"; echo '```'; } > "docs/COMBINED-AUDIT-STAGE${S}-FAILED.md"
    push "Combined audit stage ${S}: FAILED — no verdict"; exit 1
  fi
done
echo "=== all stages complete $(date -u +%H:%M:%SZ) ==="
