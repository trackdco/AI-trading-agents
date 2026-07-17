# AI Workflow Rules — driving Claude Code on this repo

## Session start ritual

Every Claude Code session begins by loading context in this order — and adopting the operating stance defined at the top of project-overview.md (expert quant developer / systematic trader; challenge loudly, change nothing without the gate):
1. `context/project-overview.md`
2. `context/architecture.md`
3. `context/code-standards.md`
4. `strategy-definition-v1.2.md`
5. The active spec (`spec-N-*.md`)
6. `context/progress-tracker.md` (where the last session stopped)

## Spec discipline

- Work is spec-driven only. No freelancing features. If Claude Code proposes something outside the active spec, the answer is "flag it in next-tasks.md and continue the step."
- Claude Code implements ONE step, runs the step's check, shows the result. Human confirms before the next step. This is not optional ceremony — it is the verification mechanism that lets Angus oversee without reading code.
- Clarifying questions come BEFORE implementation, per the standing workflow rule. A spec step that raises questions mid-implementation means stop, ask, resume.

## Auto-accept policy

- **Auto-accept edits: ON** is fine for this repo during build/backtest phases — everything is in git and reversible.
- **Exceptions that keep permission prompts:** any command using API keys or spending money (Databento pulls), anything touching `.env`, `git push --force`, dependency installs beyond the approved list, and file deletion outside `output/`.
- **Hard rule for the future:** when this project reaches live order execution (Phase 5), auto-accept is permanently disabled for the live path. This rule survives all handoffs.

## Anti-tuning guardrail (the one an eager engineer will be most tempted to break)

If a calibration or backtest result looks wrong, the workflow is:
1. Reproduce it, 2. Document it in the relevant `output/` report, 3. Stop.
Never "just adjust the threshold so February matches." Rule/parameter changes require: a written hypothesis → Angus approval → test on data the change has never seen → strategy-doc version bump → then implementation. One hypothesis at a time.

## Agent files (Phase 3 preview)

- Agents live in `.claude/agents/`, one markdown per agent (atlas.md, helios.md, apollo.md, hephaestus.md, hermes.md).
- Each agent file contains: role, its verbatim slice of strategy-definition-v1.2.md, its input (Snapshot fields it may read), and a mandatory JSON output schema. Agents that return anything but valid schema JSON are a bug.
- Agents never receive: account balance, P&L, prior trade outcomes, or each other's verdicts (Hermes aggregates; specialists stay independent).
- Prompt changes to agent files are versioned like code and logged in progress-tracker.md — a prompt edit IS a strategy change.

## Escalation

Anything that smells like a trading-semantics decision → Angus. Anything that smells like an engineering-architecture decision → decide, document in architecture.md, flag in the next update to Angus. When unsure which it is: Angus.
