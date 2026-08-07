#!/usr/bin/env python3
"""Holdout guard.

The holdout is one measurement and it is spent on first use. This module makes
reading it a deliberate act: every session-selecting call must declare which
partition it wants, and asking for the holdout requires the unseal token from
`config/data_split.yaml`. A careless glob over the archives cannot reach it,
because the archives are never addressed directly — sessions come from here.

    from data_split import sessions

    train = sessions("workbench")                       # fine
    test  = sessions("holdout")                         # raises SealedHoldoutError
    test  = sessions("holdout", unseal="HOLDOUT_...")   # deliberate, and logged
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "config" / "data_split.yaml"


class SealedHoldoutError(RuntimeError):
    """Raised when holdout sessions are requested without the unseal token."""


def _load() -> dict:
    """Minimal reader for the flat subset of YAML this config uses.

    Deliberately not a full YAML parse — no dependency, and the guard should not
    fail open because a library is missing.
    """
    out: dict = {}
    section = None
    for raw in CONFIG.read_text().splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith((" ", "-")) and raw.rstrip().endswith(":"):
            section = raw.rstrip()[:-1]
            out[section] = {}
            continue
        m = re.match(r"^\s+([a-z_]+):\s*(.*)$", raw)
        if m and section:
            k, v = m.group(1), m.group(2).strip().strip('"')
            if v in ("true", "false"):
                v = v == "true"
            elif v.isdigit():
                v = int(v)
            elif v in ("null", ">", ""):
                v = None
            out[section][k] = v
    return out


def bounds(partition: str) -> tuple[date, date]:
    cfg = _load()
    if partition not in ("workbench", "holdout"):
        raise ValueError(f"unknown partition {partition!r}; use 'workbench' or 'holdout'")
    p = cfg[partition]
    return date.fromisoformat(p["start"]), date.fromisoformat(p["end"])


def sessions(partition: str, all_sessions: list[str] | None = None,
             unseal: str | None = None) -> list[str]:
    """Session dates for a partition. Holdout access requires the unseal token."""
    cfg = _load()
    if partition == "holdout":
        expected = cfg["holdout"]["unseal_token"]
        if unseal != expected:
            raise SealedHoldoutError(
                "The holdout is SEALED. It is the only clean out-of-sample measurement "
                "this dataset will produce and it is spent on first use.\n"
                "  workbench: 2023-01-03 .. 2025-01-31 (539 sessions) — use this\n"
                "  holdout:   2025-02-01 .. 2026-01-30 (257 sessions) — one shot\n"
                "Pass unseal=<token from config/data_split.yaml> only after the workbench "
                "result is locked and the pre-registration is signed off."
            )
        if cfg["holdout"].get("spent"):
            raise SealedHoldoutError(
                f"The holdout has already been spent on: {cfg['holdout'].get('spent_on')}. "
                "A second read is no longer out-of-sample."
            )
        print("*** HOLDOUT UNSEALED — record this in config/data_split.yaml (spent: true) ***")

    lo, hi = bounds(partition)
    if all_sessions is None:
        return []
    return [s for s in all_sessions if lo <= date.fromisoformat(s) <= hi]


if __name__ == "__main__":
    cfg = _load()
    for part in ("workbench", "holdout"):
        lo, hi = bounds(part)
        seal = " [SEALED]" if cfg[part].get("sealed") else ""
        print(f"{part:10s} {lo} .. {hi}  {cfg[part]['sessions']} sessions{seal}")
    try:
        sessions("holdout")
    except SealedHoldoutError:
        print("\nguard verified: unauthorised holdout access raises SealedHoldoutError")
