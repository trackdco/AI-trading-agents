#!/usr/bin/env python3
"""Loader for config/live_thresholds.json — the single source of truth for the
canon's frozen thresholds (LIVE-STACK.md punch-list #1).

Usage:
    from scripts.live_thresholds import TH
    TH["derived"]["pre"]["Tp_d15dir_min"]     # -> frozen float
    TH.pre_Tp_d15dir_min                        # convenience attribute

The scorers import this instead of calling `.quantile()` at load time, so the
production thresholds are baked constants, not data-dependent.
"""
from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_CONFIG = _ROOT / "config" / "live_thresholds.json"


class Thresholds(dict):
    """dict with dotted-name attribute access to the frozen scalars used inline."""

    # flat convenience names -> path in the JSON, for the values the scorers read.
    _FLAT = {
        "pre_Tp_d15dir_min": ("derived", "pre", "Tp_d15dir_min"),
        "pre_G_ent_vs_vwap_sd_dir_min": ("derived", "pre", "G_ent_vs_vwap_sd_dir_min"),
        "gold_X_bbw_state_min": ("derived", "gold", "X_bbw_state_min"),
        "gold_AGE_on_extreme_age_min": ("derived", "gold", "AGE_on_extreme_age_min"),
        "gold_PAQ_netpath_30_min": ("derived", "gold", "PAQ_netpath_30_min"),
    }

    def __getattr__(self, name: str):
        if name in self._FLAT:
            node = self
            for k in self._FLAT[name]:
                node = node[k]
            return node
        raise AttributeError(name)


def load() -> Thresholds:
    if not _CONFIG.exists():
        raise FileNotFoundError(
            f"{_CONFIG} not found — run `python -m scripts.freeze_thresholds` to generate it."
        )
    return Thresholds(json.loads(_CONFIG.read_text()))


# module-level singleton, imported by the scorers
TH = load()
