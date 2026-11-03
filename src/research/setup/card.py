"""The slot for one pre-declared setup. This file does not contain one.

A setup card names the entry, the stop, the target, the filters, and the
size tiers before any result is computed. The harness refuses to run a card
whose status is still `awaiting_angus`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CARD = ROOT / "config" / "setup_card.yaml"


class SetupNotDeclared(RuntimeError):
    """Angus has not supplied the setup. The harness will not invent one."""


@dataclass
class SetupCard:
    name: str | None
    status: str
    entry: dict[str, Any] = field(default_factory=dict)
    stop: dict[str, Any] = field(default_factory=dict)
    target: dict[str, Any] = field(default_factory=dict)
    filters: list[Any] = field(default_factory=list)
    size_tiers: list[Any] = field(default_factory=list)
    notes: str = ""

    def require_declared(self) -> None:
        if self.status != "declared" or not self.name:
            raise SetupNotDeclared(
                "No setup is declared. config/setup_card.yaml is waiting for Angus. "
                "The research stack will not invent an entry, stop, or target."
            )


def load_card(path: Path | None = None) -> SetupCard:
    src = path or DEFAULT_CARD
    with src.open() as handle:
        raw = yaml.safe_load(handle) or {}
    return SetupCard(
        name=raw.get("name"),
        status=raw.get("status") or "awaiting_angus",
        entry=dict(raw.get("entry") or {}),
        stop=dict(raw.get("stop") or {}),
        target=dict(raw.get("target") or {}),
        filters=list(raw.get("filters") or []),
        size_tiers=list(raw.get("size_tiers") or []),
        notes=str(raw.get("notes") or ""),
    )
