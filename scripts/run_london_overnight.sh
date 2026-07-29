#!/usr/bin/env bash
# Overnight driver: run each audit stage, then commit AND PUSH its verdict before starting the
# next. The commits are the deliverable — the session that launched this will compact, so
# nothing may depend on results being held in context.
#
# A stage that fails does not silently skip: it writes a FAILED marker, commits that, and the
# driver stops. Half a result reported as a whole result is worse than no result.
set -u
cd "$(dirname "$0")/.." || exit 1
BR=claude/london-canon-strategy-3p57jk
PY=.venv/bin/python
mkdir -p output/logs docs

push() {   # $1 = message
  git add -A docs/ scripts/ >/dev/null 2>&1
  git commit -q -m "$1" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" \
                        -m "Claude-Session: https://claude.ai/code/session_01KjCxeeipm4yQ6KrsqKT6wP" \
    >/dev/null 2>&1 || { echo "  (nothing to commit)"; return 0; }
  for d in 2 4 8 16; do
    git push -u origin "$BR" >/dev/null 2>&1 && { echo "  pushed"; return 0; }
    echo "  push failed, retry in ${d}s"; sleep "$d"
  done
  echo "  PUSH FAILED after retries"; return 1
}

for S in 1 2 3; do
  echo "=== stage $S starting $(date -u +%H:%M:%SZ) ==="
  if $PY -m scripts.london_overnight_audit --stage "$S" > "output/logs/audit_stage${S}.log" 2>&1; then
    tail -3 "output/logs/audit_stage${S}.log"
    push "London overnight audit stage ${S}: verdict"
  else
    echo "STAGE $S FAILED"; tail -20 "output/logs/audit_stage${S}.log"
    { echo "# London overnight audit — Stage ${S}: FAILED"; echo
      echo "The stage did not complete. No verdict should be read from it."; echo
      echo '```'; tail -40 "output/logs/audit_stage${S}.log"; echo '```'; } \
      > "docs/LONDON-AUDIT-STAGE${S}-FAILED.md"
    push "London overnight audit stage ${S}: FAILED — no verdict"
    exit 1
  fi
done
echo "=== all stages complete $(date -u +%H:%M:%SZ) ==="
