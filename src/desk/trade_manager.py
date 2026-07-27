"""Intra-trade management agent — briefing builder, verdict schema, replay mechanics.

ANGUS (28-Jul): *"the agent would take the same trades regardless using the mechanical
baseline, its just about how much longer they hold it for with their discretion."*

So ENTRIES ARE FROZEN. Every arm of the replay takes the identical canon fills at the
identical entries on the identical original stops. The only thing that varies is what happens
after the fill. This is not a selection test and it must never become one — the agent is never
asked whether to take a trade, only what to do with one it is already in.

The prize is sized in docs/FINDING-exit-discretion-headroom.md: winners realize mean 2.14R
against a mean 7.28R available while alive. But the same file kills the naive version —
78% of winners eventually stop out if simply held to 16:00 on the original stop, so "hold
longer" is only worth anything if it is conditional on something. Flow is the candidate.

NO-HINDSIGHT (structural, not promised). `build_briefing()` truncates bars, tape and depth to
strictly BEFORE the decision minute in its first three statements, then derives every feature
from those truncated frames. Nothing downstream can see forward because nothing downstream
holds a frame that extends forward. Same discipline as `regime_agent.build_briefing`'s 08:00
cutoff. The one deliberate exception is `canon_exit_here`, a boolean saying the mechanical
plan closes at this minute — that is the agent's own plan, not the future, and withholding it
would make the take-or-hold question unaskable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel, field_validator

NY = "America/New_York"
SCHEMA_VERSION = "intrade-1.0"
AGENT_FILE = Path(".claude/agents/trade-manager.md")

EOD_FLATTEN_HM = 15 * 60 + 55        # engine's eod_flatten, the hard backstop for every arm
RECHECK_MIN = 20                     # re-evaluate this often once the agent has extended
MAX_DECISIONS = 6                    # per trade, so one runner cannot eat the whole budget
RATIONALE_MAX = 300

ACTIONS = ("hold", "exit_now", "stop_to_be", "stop_lock")


# ------------------------------------------------------------------ verdict schema

class IntradeVerdict(BaseModel, extra="forbid"):
    """Strict-JSON per-decision verdict. Anything else = fail-closed, and fail-closed here
    means FALL BACK TO CANON — a broken agent must never be able to invent a position."""

    schema_version: str
    agent_version: str                  # sha256[:12] of the agent file that produced it
    trade_id: str                       # must echo the briefing
    decision_minute: str                # must echo the briefing, ISO with ET offset
    action: str
    lock_r: float | None = None         # required for stop_lock, ignored otherwise
    conviction: float                   # 0.0-1.0, journaled for the learning curve
    flow_read: str                      # what the tape is saying, in the agent's words
    rationale: str

    @field_validator("action")
    @classmethod
    def _known_action(cls, v: str) -> str:
        if v not in ACTIONS:
            raise ValueError(f"action must be one of {ACTIONS}, got {v!r}")
        return v

    @field_validator("conviction")
    @classmethod
    def _unit_interval(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"conviction must be in [0,1], got {v}")
        return v

    @field_validator("rationale", "flow_read")
    @classmethod
    def _capped(cls, v: str) -> str:
        if len(v) > RATIONALE_MAX:
            raise ValueError(f"text over {RATIONALE_MAX} chars ({len(v)})")
        return v


def agent_version() -> str:
    if not AGENT_FILE.exists():
        return "missing"
    return hashlib.sha256(AGENT_FILE.read_bytes()).hexdigest()[:12]


# ------------------------------------------------------------------ briefing

def _sgn(direction: str) -> float:
    return 1.0 if direction == "long" else -1.0


def build_briefing(trade: dict, minute: pd.Timestamp, state: dict,
                   bars: pd.DataFrame, tape: pd.DataFrame,
                   depth: pd.DataFrame | None, journal: dict | None = None) -> dict:
    """One decision point. `bars`/`tape` are indexed on ET minute; `state` carries the
    management so far (current stop, whether the agent has already extended).

    Everything the agent sees is derived from the three truncated frames below. `journal`, if
    given, is the digest of decisions on trades that CLOSED before this one opened — the
    agent's own memory, never anything concurrent.
    """
    journal = journal or {"decisions_recorded": 0}
    bars = bars.loc[bars.index < minute]
    tape = tape.loc[tape.index < minute]
    depth = depth[depth.ts < minute] if depth is not None and len(depth) else None

    sgn = _sgn(trade["direction"])
    entry, risk = float(trade["entry"]), float(trade["risk"])
    fill = pd.Timestamp(trade["fill"])
    live = bars.loc[bars.index >= fill]
    last = float(bars.close.iloc[-1])

    # excursion so far, path-correct: only while the position has been alive
    if len(live):
        mfe = sgn * (live.high.max() - entry) if sgn > 0 else sgn * (live.low.min() - entry)
        mae = sgn * (live.low.min() - entry) if sgn > 0 else sgn * (live.high.max() - entry)
    else:
        mfe = mae = 0.0

    def d(k: int) -> float:
        w = tape.tail(k)
        return float(w.delta.sum()) * sgn if len(w) else float("nan")

    opp5 = int((np.sign(tape.delta.tail(5).to_numpy() * sgn) < 0).sum()) if len(tape) >= 5 else None
    vol5 = float(tape.vol.tail(5).mean()) if len(tape) >= 5 else float("nan")
    volmed = float(tape.vol.median()) if len(tape) else float("nan")

    b = {
        "schema_version": SCHEMA_VERSION,
        "trade_id": trade["trade_id"],
        "decision_minute": minute.isoformat(),
        "reason_for_decision": state["reason"],
        "trade": {
            "direction": trade["direction"],
            "session": trade["win_"],
            "pattern": trade["pattern"],
            "entry": round(entry, 2),
            "original_stop": round(float(trade["stop"]), 2),
            "current_stop": round(float(state["stop"]), 2),
            "risk_points": round(risk, 2),
            "minutes_in_trade": int((minute - fill).total_seconds() // 60),
            "last_price": round(last, 2),
            "R_now": round(sgn * (last - entry) / risk, 2),
            "R_best_so_far": round(mfe / risk, 2),
            "R_worst_so_far": round(mae / risk, 2),
            "R_locked_if_stopped_now": round(sgn * (float(state["stop"]) - entry) / risk, 2),
            "already_extended": bool(state["extended"]),
        },
        "mechanical_plan": {
            "canon_exits_at_this_minute": bool(state["canon_exit_here"]),
            "canon_exit_price": (round(float(trade["exit_price"]), 2)
                                 if state["canon_exit_here"] else None),
        },
        "flow": {
            "cvd_5m_signed": round(d(5), 1),
            "cvd_15m_signed": round(d(15), 1),
            "cvd_30m_signed": round(d(30), 1),
            "opposed_of_last_5_minutes": opp5,
            "volume_last_5m_vs_day_median": (round(vol5 / volmed, 2)
                                             if volmed and volmed == volmed else None),
        },
        "journal": journal,
        "recent_bars_oldest_first": [
            {"t": t.strftime("%H:%M"), "o": round(r.open, 2), "h": round(r.high, 2),
             "l": round(r.low, 2), "c": round(r.close, 2)}
            for t, r in bars.tail(10).iterrows()],
    }

    if depth is not None and len(depth):
        snap = depth[depth.ts == depth.ts.max()]
        bid, ask = snap[snap.side == "bid"], snap[snap.side == "ask"]
        if len(bid) and len(ask):
            tb, ta = float(bid["size"].sum()), float(ask["size"].sum())
            ahead, behind = (ask, bid) if sgn > 0 else (bid, ask)
            wa = ahead.loc[ahead["size"].idxmax()] if len(ahead) else None
            wb = behind.loc[behind["size"].idxmax()] if len(behind) else None
            b["book"] = {
                "thickness": round(tb + ta, 1),
                "imbalance_signed": round(((tb - ta) / max(tb + ta, 1)) * sgn, 3),
                "wall_ahead_points_away": (round(abs(float(wa.price) - last), 2)
                                           if wa is not None else None),
                "wall_ahead_size": float(wa["size"]) if wa is not None else None,
                "wall_behind_points_away": (round(abs(float(wb.price) - last), 2)
                                            if wb is not None else None),
                "wall_behind_size": float(wb["size"]) if wb is not None else None,
                "note": "MBP-10 aggregated levels, median 5.25pt of book — NOT order-by-order",
            }
    return b


def briefing_prompt(b: dict) -> str:
    """Deterministic prompt. Identical briefing -> identical bytes, so the blob sha is a
    real audit key rather than a timestamp."""
    return (
        "Manage this open position. You did NOT choose this trade and you cannot change its "
        "entry or its direction — the mechanical canon took it. Your only question is what to "
        "do with it now.\n\n"
        "Everything below is strictly what was knowable at the decision minute. There is no "
        "information about what happens next, and guessing is not rewarded.\n\n"
        f"{json.dumps(b, indent=1, sort_keys=True)}\n\n"
        "Reply with ONE JSON object and nothing else:\n"
        '{"schema_version": "%s", "agent_version": "<given to you>", "trade_id": "%s", '
        '"decision_minute": "%s", "action": "hold|exit_now|stop_to_be|stop_lock", '
        '"lock_r": <float, only for stop_lock>, "conviction": <0.0-1.0>, '
        '"flow_read": "<what the tape is saying, <=%d chars>", '
        '"rationale": "<why this action, <=%d chars>"}'
        % (SCHEMA_VERSION, b["trade_id"], b["decision_minute"], RATIONALE_MAX, RATIONALE_MAX)
    )


# ------------------------------------------------------------------ replay mechanics

def apply_action(state: dict, v: IntradeVerdict, trade: dict) -> dict:
    """Fold one verdict into the management state. Every path is monotone in the trader's
    favour: a stop may only move toward profit, never away, and `hold` past a canon exit is
    the only way a position outlives its mechanical plan."""
    sgn = _sgn(trade["direction"])
    entry, risk = float(trade["entry"]), float(trade["risk"])
    st = dict(state)
    if v.action == "exit_now":
        st["force_exit"] = True
        return st
    if v.action == "stop_to_be":
        st["stop"] = _tighten(st["stop"], entry, sgn)
    elif v.action == "stop_lock":
        r = 0.0 if v.lock_r is None else float(v.lock_r)
        st["stop"] = _tighten(st["stop"], entry + sgn * r * risk, sgn)
    if st["canon_exit_here"]:
        st["extended"] = True          # held through the mechanical close
    return st


def _tighten(cur: float, proposed: float, sgn: float) -> float:
    """A stop only ever moves toward price."""
    return max(cur, proposed) if sgn > 0 else min(cur, proposed)


# ------------------------------------------------------------------ journal

# The flow variables carried on every journal row. These are the columns the digest buckets
# on, so adding one here makes it queryable; describing it in prose does not.
FLOW_KEYS = ("cvd_5m_signed", "cvd_15m_signed", "cvd_30m_signed",
             "opposed_of_last_5_minutes", "volume_last_5m_vs_day_median")
BOOK_KEYS = ("imbalance_signed", "wall_ahead_points_away", "wall_ahead_size",
             "wall_behind_points_away")


def journal_row(briefing: dict, verdict: "IntradeVerdict | None", outcome: dict) -> dict:
    """One decision, its flow state, and WHAT THE TRADE DID AFTERWARDS.

    ANGUS: *"so for example it can look back and be like okay the last 3 times the delta has
    been this positive the trade ran another 2r+ minimum so i can hold it for longer."*

    That question is only answerable if the forward outcome is stored next to the flow
    reading that preceded it — which is why `r_ran_further` (MFE from THIS minute onward,
    minus where the trade already was) sits on the same row as `cvd_15m_signed`. A row is
    only ever written after the trade has closed, so nothing here can leak into a live
    decision; the digest then filters to trades closed before the current week.
    """
    t = briefing["trade"]
    row = {
        "trade_id": briefing["trade_id"],
        "decision_minute": briefing["decision_minute"],
        "session": t["session"],
        "reason": briefing["reason_for_decision"],
        "direction": t["direction"],
        "pattern": t["pattern"],
        "r_now": t["R_now"],
        "r_best_so_far": t["R_best_so_far"],
        "minutes_in_trade": t["minutes_in_trade"],
        "canon_exits_here": briefing["mechanical_plan"]["canon_exits_at_this_minute"],
        "action": verdict.action if verdict else "unanswered",
        "lock_r": verdict.lock_r if verdict else None,
        "conviction": verdict.conviction if verdict else None,
        "flow_read": verdict.flow_read if verdict else "",
    }
    row |= {k: briefing["flow"].get(k) for k in FLOW_KEYS}
    row |= {f"book_{k}": briefing.get("book", {}).get(k) for k in BOOK_KEYS}
    # forward outcome, in R, measured from THIS decision onward
    row |= {
        "r_ran_further": outcome.get("r_peak_after") is not None
        and round(outcome["r_peak_after"] - t["R_now"], 2) or None,
        "r_at_exit": round(outcome["R"], 2),
        "r_given_back": (round(outcome["r_peak_after"] - outcome["R"], 2)
                         if outcome.get("r_peak_after") is not None else None),
        "delta_vs_canon": round(outcome.get("delta_vs_canon", 0.0), 2),
        "held_minutes_total": outcome.get("held_minutes"),
        "exit_reason": outcome.get("exit_reason"),
    }
    return row


def _bucket(rows: list[dict], key: str, edges: list[float], labels: list[str]) -> list[dict]:
    """Base rates for the forward run, split on one flow variable."""
    out = []
    for i, lab in enumerate(labels):
        lo = edges[i - 1] if i else -float("inf")
        hi = edges[i] if i < len(edges) else float("inf")
        sel = [r for r in rows
               if r.get(key) is not None and r.get("r_ran_further") is not None
               and lo <= r[key] < hi]
        if len(sel) < 3:                     # below this a "base rate" is an anecdote
            continue
        fwd = sorted(r["r_ran_further"] for r in sel)
        out.append({
            key: lab, "n": len(sel),
            "ran_further_median_R": round(fwd[len(fwd) // 2], 2),
            "ran_a_further_2R_or_more": f"{sum(f >= 2 for f in fwd)}/{len(sel)}",
            "went_nowhere_under_0.5R": f"{sum(f < 0.5 for f in fwd)}/{len(sel)}",
        })
    return out


def journal_digest(rows: list[dict], recent: int = 6) -> dict:
    """What the agent gets to carry forward: its own record, plus forward-run base rates
    bucketed on the flow variables it will see again."""
    if not rows:
        return {"decisions_recorded": 0,
                "note": "no completed decisions yet — judge on the tape alone"}
    holds = [r for r in rows if r["action"] == "hold" and r["canon_exits_here"]]
    takes = [r for r in rows if r["action"] == "exit_now" and r["canon_exits_here"]]
    gained = [r for r in holds if r["delta_vs_canon"] > 0]
    left = [r["r_given_back"] for r in takes if r.get("r_given_back") is not None]
    d = {
        "decisions_recorded": len(rows),
        "your_record_at_the_mechanical_exit": {
            "held": len(holds),
            "holds_that_beat_the_mechanical_exit": f"{len(gained)}/{len(holds)}" if holds else "0/0",
            "mean_dollars_per_hold": (round(sum(r["delta_vs_canon"] for r in holds) / len(holds), 2)
                                      if holds else None),
            "took_the_exit": len(takes),
            "median_R_left_behind_when_taking": (round(sorted(left)[len(left) // 2], 2)
                                                 if left else None),
        },
        "forward_run_by_15m_delta": _bucket(
            rows, "cvd_15m_signed", [0, 250],
            ["negative (flow against)", "0 to +250", ">= +250 (flow strongly with)"]),
        "forward_run_by_opposed_minutes": _bucket(
            rows, "opposed_of_last_5_minutes", [2, 4],
            ["0-1 of 5 opposed (clean)", "2-3 of 5", "4-5 of 5 (tape turned)"]),
        "most_recent": [
            {k: r[k] for k in ("decision_minute", "reason", "r_now", "cvd_15m_signed",
                               "opposed_of_last_5_minutes", "action", "r_ran_further",
                               "delta_vs_canon")}
            for r in rows[-recent:]],
    }
    return d
