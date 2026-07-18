"""v0.4 desk mechanics (Angus directive, 18 Jul): analog block + fresh-eyes panel +
mechanical scorecard/regret. Additive to the frozen v0.3 contract — build_briefing,
the verdict schema, and the gate are untouched; this module wraps and measures them.

Three jobs, none of which need an agent turn:
  1. attach_analog_block  — join the precomputed A1 block (output/analog_briefing.csv)
     into a briefing under a new `analog_block` key (the retrieval input that targets
     the book-selection miss). The legacy `analog_days` field is left as-is.
  2. as_fresh_eyes        — derive the no-memory twin of a briefing (playbook_notes
     stripped). Same facts, no inherited frame — the lock-in control.
  3. scorecard/regret     — after the realized day is known, grade an action against
     the oracle (Angus rule: best-book <= 0 counts FLAT) and price the regret.

Desk-contract note: scorecard/regret are MEASUREMENT here (written to a ledger). Feeding
them back into the agent's briefing would show it outcome data, which the v0.3 contract
forbids — that feedback path is deliberately NOT built in this module and is flagged for
Angus before any wiring.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ANALOG_CSV = Path("output/analog_briefing.csv")
BOOKS_2026 = Path("output/l2_analog_routing.csv")     # pl_e3/pl_e4, 2026-02+
BOOKS_HIST = Path("output/allyears_daily_books.csv")  # E3/E4, 2023-01..2026-01

FRESH_NOTES = "(fresh-eyes agent: NO inherited notes — brief from today's facts alone)"


# --------------------------------------------------------------- 1. analog block

def load_analog_block(day: str, csv_path: Path = ANALOG_CSV) -> dict | None:
    """Return the parsed A1 analog block for `day`, or None if absent/empty."""
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path)
    row = df[df["day"] == day]
    if row.empty:
        return None
    raw = row.iloc[0].get("analog_block")
    if not isinstance(raw, str) or not raw.strip():
        return None
    return json.loads(raw)


def attach_analog_block(briefing: dict, block: dict | None) -> dict:
    """Return a copy of `briefing` with the A1 block under `analog_block`. A missing
    block is recorded explicitly (never silently dropped) so the agent knows to fall
    back to tape reasoning rather than assume none existed."""
    out = dict(briefing)
    out["analog_block"] = block if block is not None else "no analog block (insufficient library depth)"
    return out


# --------------------------------------------------------------- 2. fresh-eyes twin

def as_fresh_eyes(briefing: dict) -> dict:
    """The no-memory twin: identical facts, playbook_notes replaced by the fresh-eyes
    marker. Divergence from the chained verdict on the same briefing is the daily
    frame-lock-in signal."""
    out = dict(briefing)
    out["playbook_notes"] = FRESH_NOTES
    return out


# --------------------------------------------------------------- 3. scorecard/regret

def _load_books() -> pd.DataFrame:
    frames = []
    if BOOKS_HIST.exists():
        h = pd.read_csv(BOOKS_HIST)[["day", "E3", "E4"]].rename(
            columns={"E3": "pl_e3", "E4": "pl_e4"})
        frames.append(h)
    if BOOKS_2026.exists():
        frames.append(pd.read_csv(BOOKS_2026)[["day", "pl_e3", "pl_e4"]])
    if not frames:
        return pd.DataFrame(columns=["day", "pl_e3", "pl_e4"]).set_index("day")
    return pd.concat(frames).drop_duplicates("day").set_index("day")


def oracle_action(e3: float, e4: float) -> str:
    """Angus ruling (18 Jul): a best book <= 0 on no trades is FLAT, not a miss."""
    return "FLAT" if max(e3, e4) <= 0 else ("ROTATION" if e3 >= e4 else "MOMENTUM")


def verdict_action(regime: str, stand_down: bool, size_multiplier: float) -> str:
    """Map a verdict to the 3-way action space score_regime_reads.py uses."""
    if stand_down or size_multiplier == 0:
        return "FLAT"
    if regime in ("balance", "trap"):
        return "ROTATION"
    if regime == "war":
        return "MOMENTUM"
    return "FLAT"                       # event_risk with no directional book = FLAT


def grade_day(day: str, action: str, books: pd.DataFrame | None = None) -> dict | None:
    """Score one action against the realized oracle for `day`. None if P&L unknown.
    regret = what perfect selection would have made minus what this action made."""
    books = _load_books() if books is None else books
    if day not in books.index:
        return None
    e3, e4 = float(books.loc[day, "pl_e3"]), float(books.loc[day, "pl_e4"])
    orc = oracle_action(e3, e4)
    agent_pl = 0.0 if action == "FLAT" else (e3 if action == "ROTATION" else e4)
    oracle_pl = max(e3, e4, 0.0)
    return {
        "day": day, "action": action, "oracle": orc, "hit": action == orc,
        "agent_pl": round(agent_pl), "oracle_pl": round(oracle_pl),
        "regret": round(oracle_pl - agent_pl), "e3": round(e3), "e4": round(e4),
    }


def divergence_row(day: str, chained_v: dict, fresh_v: dict,
                   books: pd.DataFrame | None = None) -> dict:
    """One frame-lock-in detector row: chained vs fresh action, agreement, and (if the
    realized day is known) which mind — if either — the oracle vindicated."""
    ca = verdict_action(chained_v["regime"], chained_v["stand_down"],
                        chained_v["size_multiplier"])
    fa = verdict_action(fresh_v["regime"], fresh_v["stand_down"],
                        fresh_v["size_multiplier"])
    books = _load_books() if books is None else books
    orc = None
    if day in books.index:
        orc = oracle_action(float(books.loc[day, "pl_e3"]), float(books.loc[day, "pl_e4"]))
    return {
        "day": day,
        "chained_regime": chained_v["regime"], "chained_action": ca,
        "fresh_regime": fresh_v["regime"], "fresh_action": fa,
        "agree": ca == fa,
        "oracle": orc,
        "chained_right": None if orc is None else ca == orc,
        "fresh_right": None if orc is None else fa == orc,
    }
