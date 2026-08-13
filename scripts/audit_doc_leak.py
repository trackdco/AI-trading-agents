#!/usr/bin/env python3
"""AUDIT — is the do-not-read list actually enforced, and what is still burned?

    python -m scripts.audit_doc_leak            # exits 1 on any FAIL

`scripts/audit_run_leak.py` audits a RUN: did a decision see the future. This
audits the REPO: can an agent still reach a file that would tell it the answer.

It exists because a gap was caught by eye, not by tooling. `docs/DIAGNOSIS-
0.3.5-week.md` was named in the operator's do-not-read instructions but was
absent from the settings deny-list, so the guardrail did not cover it — and
tracing that turned up a second file, `docs/ANALYSIS-clean-week-0.3.5.md`, a
full per-day R scoreboard for the corpus week that no list mentioned at all.

Prose and policy drift apart silently. This makes them fail loudly.

THREE CHECKS
  A  every path named in a do-not-read instruction EXISTS on disk
     (a typo'd path is a rule that protects nothing, and reads as protection)
  B  every path named in a do-not-read instruction is covered by a deny rule
     (this is the bug that was caught by hand)
  C  every file an agent can still READ is scanned for session-day dates sitting
     next to outcome language — the burn list. Not a failure by itself: some of
     it is load-bearing doctrine that cannot be written without its example. It
     is reported so the burn is a decision rather than a surprise.

Check C's output is the input to one standing rule: **the narrated week is a
rehearsal corpus, not a measurement set.** Days that carry day-tagged outcome
commentary in readable docs can teach, but they can never score. Walk-forward
days must stay off this list to stay measurable.
"""
from __future__ import annotations

import fnmatch
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / ".claude" / "settings.json"

# Files that TELL someone not to read something. Scanned for named paths.
INSTRUCTION_SOURCES = [
    ".claude/agents/tv-thesis.md",
    ".claude/agents/tv-trigger.md",
    ".claude/agents/tv-manage.md",
    ".claude/agents/tv-macro-events.md",
    "docs/RUNBOOK-replay-scoring.md",
    "docs/KICKOFF-local-session.md",
]

# A path token: docs/x.md, data/narrated_days/*, output/agent_runs/...
PATH_TOKEN = re.compile(
    r"(?<![\w/.])((?:docs|data|output|scripts)/[A-Za-z0-9_./*-]+)")

# Phrases that mark a passage as a prohibition. Checked against the containing
# paragraph, because these lists are written as prose, not as config.
FORBID = re.compile(
    r"do not (?:read|open|touch)|never\s+(?:read|open|`)|"
    r"files you do not open|named poison|denied at the tool level|"
    r"are denied in|do not work around the denial|above all \*\*never",
    re.I)

# Outcome language — what a decision PRODUCED, which is the thing a replaying
# agent must not be able to look up.
OUTCOME = re.compile(
    r"[+\-−]\s?\d+(?:\.\d+)?\s*R\b|\b\d+(?:\.\d+)?R\b|"
    r"\bstopped out\b|\bleft on the table\b|\bwin rate\b|\bhit rate\b|"
    r"\bbreak-?even hit\b|\brealised R\b|\bfull stop-?outs?\b|"
    r"\bexpectancy\b|\bscoreboard\b|\bP&L\b", re.I)

SESSION_DAY = re.compile(r"\b20\d{2}-[01]\d-[0-3]\d\b")

# Dates that are provably not session-days: ruling stamps, "confirmed <date>".
STAMP = re.compile(
    r"(?:confirmed|measured|closed|ruling|his ruling|corrected by him|"
    r"added|probed|on|updated|interview)[^.\n]{0,40}$", re.I)

# Check C only cares about days the tv-* stack could actually REPLAY: the
# narrated corpus week and the Feb-July walk-forward. This repo also carries
# years of mechanical-canon research whose dates are build stamps and closed-
# lane session-days — flagging those buries the signal in history.
REPLAY_FROM, REPLAY_TO = "2026-02-01", "2026-07-15"

# A prohibition is a SENTENCE, not a paragraph. Agent frontmatter is one
# unbroken comment block carrying both "never read X" and "doctrine in Y" —
# paragraph-level matching reads the second as the first and flags the
# stack's own required reading as poison.
SENTENCE = re.compile(r"(?<=[.!?;])\s+|\n\s*[-*]\s+|\n(?=\s*\d+\.\s)")


def denied_globs() -> list[str]:
    raw = json.loads(SETTINGS.read_text())
    out = []
    for rule in raw.get("permissions", {}).get("deny", []):
        m = re.match(r"\s*Read\((.+)\)\s*$", rule)
        if m:
            out.append(m.group(1).lstrip("./"))
    return out


def is_denied(rel: str, globs: list[str]) -> bool:
    for g in globs:
        if fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(rel, g.rstrip("*") + "*"):
            return True
    return False


def named_paths() -> dict[str, list[str]]:
    """path -> which instruction files name it as forbidden."""
    found: dict[str, list[str]] = {}
    for src in INSTRUCTION_SOURCES:
        p = ROOT / src
        if not p.is_file():
            continue
        for para in re.split(r"\n\s*\n", p.read_text()):
            if not FORBID.search(para):
                continue
            for sent in SENTENCE.split(para):
                if not FORBID.search(sent):
                    continue          # doctrine reference, not a prohibition
                for tok in PATH_TOKEN.findall(sent):
                    tok = tok.rstrip(".,;:`)")
                    # scripts/ paths here are tooling, not poison
                    if tok.startswith("scripts/"):
                        continue
                    found.setdefault(tok, []).append(src)
    return found


def readable_md(globs: list[str]) -> list[Path]:
    out = []
    for p in sorted(ROOT.glob("docs/*.md")):
        if not is_denied(p.relative_to(ROOT).as_posix(), globs):
            out.append(p)
    return out


def main() -> int:
    globs = denied_globs()
    named = named_paths()
    fails = 0

    print("=" * 78)
    print("  DOC LEAK AUDIT — is the do-not-read list actually enforced?")
    print("=" * 78)

    # ---- A: named paths exist
    print("\nA. paths named as forbidden actually exist")
    missing = []
    for path in sorted(named):
        probe = path.replace("*", "")
        hit = (ROOT / probe).exists() or bool(list(ROOT.glob(path)))
        if not hit:
            missing.append(path)
    if missing:
        fails += 1
        print("   FAIL — named but not on disk (a rule protecting nothing):")
        for m in missing:
            print(f"     {m}   (named in {', '.join(sorted(set(named[m])))})")
    else:
        print(f"   pass — all {len(named)} named paths exist")

    # ---- B: named paths are denied
    print("\nB. paths named as forbidden are covered by a settings deny rule")
    uncovered = [p for p in sorted(named)
                 if p not in missing and not is_denied(p.lstrip("./"), globs)]
    if uncovered:
        fails += 1
        print("   FAIL — instruction-only, no guardrail:")
        for u in uncovered:
            print(f"     {u}   (named in {', '.join(sorted(set(named[u])))})")
        print("   → add   \"Read(./%s)\"   to .claude/settings.json deny"
              % uncovered[0])
    else:
        print(f"   pass — {len(named) - len(missing)} named paths all denied")

    # ---- C: what is still readable and still burned
    print(f"\nC. burn list — readable docs tying a REPLAYABLE session-day "
          f"({REPLAY_FROM}..{REPLAY_TO}) to an outcome")
    burn: dict[str, set[str]] = {}
    for p in readable_md(globs):
        lines = p.read_text().splitlines()
        for i, line in enumerate(lines):
            window = " ".join(lines[max(0, i - 1):i + 2])
            for d in SESSION_DAY.findall(line):
                if not (REPLAY_FROM <= d <= REPLAY_TO):
                    continue          # research history, closed lane
                before = line[:line.index(d)]
                if STAMP.search(before):
                    continue
                if OUTCOME.search(window):
                    burn.setdefault(d, set()).add(
                        f"{p.relative_to(ROOT).as_posix()}:{i + 1}")
    if burn:
        for d in sorted(burn):
            print(f"   {d}  burned by:")
            for site in sorted(burn[d]):
                print(f"       {site}")
        print("\n   Not a failure. These days can TEACH but must never SCORE.")
        print("   A walk-forward day appearing here has lost its measurability —")
        print("   move the passage into a denied file or de-identify it.")
    else:
        print("   none — no readable doc ties a session-day to an outcome")

    print("\n" + "=" * 78)
    print("  FAIL" if fails else "  PASS", f"— {fails} check(s) failed")
    print("=" * 78)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
