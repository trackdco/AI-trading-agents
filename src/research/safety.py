"""Research-side halt. Same kill file as the live vault, no broker.

The execution spine in src/canon/spine.py remains the order-time guard for
any future live path. This module only stops research jobs. It does not
flatten, submit, or read credentials.
"""

from __future__ import annotations

from pathlib import Path

KILL_FILE = Path("output/live/KILL")


class ResearchHalted(RuntimeError):
    """The kill file is present. Research refuses to run a path."""


def kill_switch_tripped(path: Path | None = None) -> bool:
    return (path or KILL_FILE).exists()


def require_research_allowed(path: Path | None = None) -> None:
    if kill_switch_tripped(path):
        raise ResearchHalted(
            f"kill file {(path or KILL_FILE)} is present; research path stopped"
        )
