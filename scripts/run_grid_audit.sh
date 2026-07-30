#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.." || exit 1
BR=claude/london-canon-strategy-3p57jk
push() { git add -A docs/ scripts/ >/dev/null 2>&1
  git commit -q -m "$1" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" \
    -m "Claude-Session: https://claude.ai/code/session_01KjCxeeipm4yQ6KrsqKT6wP" >/dev/null 2>&1 || { echo "  (nothing)"; return 0; }
  for d in 2 4 8 16; do git push -u origin "$BR" >/dev/null 2>&1 && { echo "  pushed"; return 0; }; sleep "$d"; done
  echo "  PUSH FAILED"; }
for S in A B C; do
  echo "=== stage $S $(date -u +%H:%M:%SZ) ==="
  if .venv/bin/python -m scripts.london_grid_audit --stage "$S" > "output/logs/grid_${S}.log" 2>&1; then
    tail -2 "output/logs/grid_${S}.log"; push "London grid audit stage ${S}: verdict"
  else
    echo "STAGE $S FAILED"; tail -25 "output/logs/grid_${S}.log"
    { echo "# London grid audit — Stage ${S}: FAILED"; echo; echo "No verdict should be read from this stage."; echo; echo '```'; tail -40 "output/logs/grid_${S}.log"; echo '```'; } > "docs/LONDON-GRID-STAGE${S}-FAILED.md"
    push "London grid audit stage ${S}: FAILED"; exit 1
  fi
done
echo "=== done $(date -u +%H:%M:%SZ) ==="
