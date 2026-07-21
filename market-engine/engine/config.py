"""Config loading. Every strategy number comes from config/strategy.yaml."""
from __future__ import annotations

import os
from pathlib import Path
from datetime import time

import yaml

_DEF = Path(__file__).resolve().parent.parent / "config" / "strategy.yaml"


def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


class Config:
    def __init__(self, data: dict):
        self._d = data

    @classmethod
    def load(cls, path: str | os.PathLike | None = None) -> "Config":
        p = Path(path) if path else _DEF
        with open(p) as f:
            return cls(yaml.safe_load(f))

    def __getitem__(self, k):
        return self._d[k]

    def get(self, k, default=None):
        return self._d.get(k, default)

    # convenience typed accessors used in hot paths
    @property
    def tz(self) -> str:
        return self._d["session"]["tz"]

    @property
    def tick(self) -> float:
        return float(self._d["instrument"]["tick_size"])

    @property
    def entry_tfs(self) -> list[int]:
        return list(self._d["entry_timeframes"])

    @property
    def ctx_tf(self) -> int:
        return int(self._d["context_timeframe"])

    def t(self, *keys) -> time:
        cur = self._d
        for k in keys:
            cur = cur[k]
        return _parse_hhmm(cur)
