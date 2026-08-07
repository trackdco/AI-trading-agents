#!/usr/bin/env python3
"""L4 — the selection policy, applied POST-HOC to scored candidates. The last layer.

WHY IT IS A SEPARATE LAYER (the whole point of the rebuild): the old cap lived inside
simulate() at fill time, where it silently decided which candidates every other layer ever
saw — 2 slots shared across pre+gold meant gold got ZERO candidates on 56% of day-books,
and nobody could see it because the starved pool WAS the substrate. Here the policy walks a
complete, already-scored population, so changing any knob is a re-run, never a rebuild, and
every kill is attributable.

THE POLICY (ANGUS 28/29-Jul rulings, parameterized so each is measurable):

  caps per SESSION, not per day     2 London / 2 pre-market / 2 gold ("2 trades in london,
                                    2 in pre market, 2 in golden window")
  escalation within the session     "if it lost the first, the second needed extra
                                    conviction" — the 2nd+ slot demands a higher bar
  day stop                          cumulative realized P&L at/below -day_stop halts
                                    further entries (keyable per day or per session)
  per-session threshold T           a candidate must clear its session's bar to take a
                                    slot — the honest lever for gold frequency

CAUSALITY, NON-NEGOTIABLE: the walk is chronological within each day. A candidate is taken
iff, AT ITS FILL TIME, it clears the bar and a slot remains. "Best 2 of the day" is not
implementable live (you cannot skip a 09:45 trade hoping for a better 10:05) and is
structurally excluded here: no ordering, ranking, or selection uses any information from
later in the day. The unit tests assert this.

This module is pure logic over a DataFrame and is fully unit-tested on synthetic data
(tests/test_l4_select.py) — it can be trusted before L2/L3 artifacts exist.

Input schema (one row per candidate): day, session, fill_ts, score, realized dollars (or R).
Output: the input plus taken/nth/kill_reason columns — the complete audit trail.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class L4Policy:
    cap_per_session: int = 2
    threshold: dict = field(default_factory=lambda: {"pre": 3.0, "gold": 3.0, "london": 3.0})
    escalation_threshold: dict = field(default_factory=lambda: {"pre": 4.0, "gold": 4.0,
                                                                "london": 3.0})
    escalation_after_loss_only: bool = False   # False = 2nd+ slot always needs the higher
                                               # bar (the shipped L2b shape); True = only
                                               # after a realized loss in the session
                                               # (Angus's literal wording — measurable)
    day_stop_dollars: float = 400.0            # halt at/below -this
    day_stop_key: str = "day"                  # "day" | "session" — both measurable


def select(cands: pd.DataFrame, pol: L4Policy,
           dollars_col: str = "dollars") -> pd.DataFrame:
    """Chronological causal walk. Returns cands + [taken, nth, kill_reason].

    Requires columns: day, session, fill_ts, score, and `dollars_col` (the candidate's
    realized outcome, used ONLY after the take decision — for the day-stop accumulator).
    Rows must represent FILLED candidates; unfilled ones cannot consume slots (the engine
    consumed cap slots at fill time; so does this walk).
    """
    need = {"day", "session", "fill_ts", "score", dollars_col}
    if missing := need - set(cands.columns):
        raise ValueError(f"missing columns: {sorted(missing)}")
    out = cands.sort_values(["day", "fill_ts"], kind="stable").copy()
    out["taken"] = False
    out["nth"] = 0
    out["kill_reason"] = ""

    for day, g in out.groupby("day", sort=False):
        slots: dict[str, int] = {}
        losses: dict[str, bool] = {}
        pl: dict[str, float] = {}
        for i in g.index:
            sess = out.at[i, "session"]
            score = out.at[i, "score"]
            stop_key = day if pol.day_stop_key == "day" else sess
            if pl.get(stop_key, 0.0) <= -pol.day_stop_dollars:
                out.at[i, "kill_reason"] = "day_stop"
                continue
            used = slots.get(sess, 0)
            if used >= pol.cap_per_session:
                out.at[i, "kill_reason"] = "session_cap"
                continue
            bar = pol.threshold.get(sess, float("inf"))
            esc = (used >= 1 and (losses.get(sess, False)
                                  or not pol.escalation_after_loss_only))
            if esc:
                bar = max(bar, pol.escalation_threshold.get(sess, bar))
            if score < bar:
                out.at[i, "kill_reason"] = "escalation_bar" if esc else "threshold"
                continue
            # taken: consume the slot, then (and only then) settle its outcome forward
            slots[sess] = used + 1
            out.at[i, "taken"] = True
            out.at[i, "nth"] = slots[sess]
            d = float(out.at[i, dollars_col])
            pl[stop_key] = pl.get(stop_key, 0.0) + d
            if d < 0:
                losses[sess] = True
    return out


def summarize(book: pd.DataFrame, dollars_col: str = "dollars") -> pd.DataFrame:
    """Per-session verdict table: takes, take-rate, WR, P&L, trades/week."""
    t = book[book.taken]
    weeks = book.day.nunique() / 5.0
    rows = []
    for sess, g in book.groupby("session"):
        tg = g[g.taken]
        rows.append({
            "session": sess, "candidates": len(g), "taken": len(tg),
            "per_week": round(len(tg) / weeks, 2) if weeks else 0.0,
            "WR": round((tg[dollars_col] > 0).mean(), 3) if len(tg) else float("nan"),
            "dollars": round(tg[dollars_col].sum(), 2),
            "kills": g[~g.taken].kill_reason.value_counts().to_dict()})
    rows.append({"session": "TOTAL", "candidates": len(book), "taken": len(t),
                 "per_week": round(len(t) / weeks, 2) if weeks else 0.0,
                 "WR": round((t[dollars_col] > 0).mean(), 3) if len(t) else float("nan"),
                 "dollars": round(t[dollars_col].sum(), 2), "kills": {}})
    return pd.DataFrame(rows)
