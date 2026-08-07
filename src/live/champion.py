"""The frozen champion (Blend v1.1) as a LIVE session policy (Phase 4 Stage 2).

The champion is not one book — it is a daily BLEND (docs/CHAMPION-v1.1-FROZEN.md):
every session, the pre-open `imbal_share_20 >= 0.5` switch picks the book:

  E3 book  (balance): entry E3, management V8            — all classified triggers
  E4 book  (war):     entry E4, tight stops              — only triggers with
                                                            |close - stop_ref| <= 15 pts

Config mirrors scripts/score_replay_arms.py `_books` EXACTLY (the harness whose monthly
numbers reproduce the frozen ledger): base = strategy.yaml + win_end 10:15 +
max_trades_per_day 2; the C1-C3 cuts ride in the base config.

`champion_policy(vector_df)` returns the per-session callable the Vault consumes. The
regime vector is precomputed for replay/paper (output/regime_vector.csv); computing it
pre-open from live bars is a Stage-8 deliverable (flagged in the build plan).
"""

from __future__ import annotations

from datetime import time as dtime
from pathlib import Path
from typing import Callable

import pandas as pd

from src.backtest.engine import load_backtest_config

E4_MAX_STOP_PTS = 15.0
VECTOR_CSV = Path("output/regime_vector.csv")


def champion_books(config_path: Path = Path("config/strategy.yaml")) -> dict:
    """The two frozen books, byte-compatible with score_replay_arms._books."""
    base = load_backtest_config(config_path).model_copy(
        update={"win_end": dtime(10, 15), "max_trades_per_day": 2})
    return {"E3": base.model_copy(update={"mgmt_variant": "V8"}),
            "E4": base.model_copy(update={"entry_variant": "E4"})}


def e4_trigger_ok(t) -> bool:
    return abs(float(t.close) - float(t.stop_ref)) <= E4_MAX_STOP_PTS


def _any_trigger(t) -> bool:
    return True


def book_for_day(day: str, vector: pd.DataFrame) -> str:
    """The pre-open switch: imbal_share_20 >= 0.5 -> E4 (war book), else E3. A day with
    no vector row defaults to E3 — identical to the scoring harness."""
    row = vector[vector["day"] == day]
    if row.empty:
        return "E3"
    s = row.iloc[0]["imbal_share_20"]
    return "E4" if (pd.notna(s) and s >= 0.5) else "E3"


def champion_policy(vector: pd.DataFrame | None = None,
                    config_path: Path = Path("config/strategy.yaml"),
                    ) -> Callable[[str], tuple]:
    """Session policy for the Vault: date -> (book_name, cfg, trigger_predicate)."""
    vec = pd.read_csv(VECTOR_CSV) if vector is None else vector
    books = champion_books(config_path)

    def policy(day: str) -> tuple:
        book = book_for_day(day, vec)
        pred = e4_trigger_ok if book == "E4" else _any_trigger
        return book, books[book], pred

    return policy
