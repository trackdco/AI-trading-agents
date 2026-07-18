"""L3 regime-context agent — briefing builder, verdict schema, gate mapping (Pat's lane).

Implements the L3 layer of docs/REGIME-ADAPTATION-DESIGN.md per Angus's pass-29
greenlight (docs/TASK-FOR-PAT-regime-agent.md). The desk contract from
docs/agent-blueprint.md applies: strict JSON (extra='forbid'), fail-closed
validation, deterministic prompts, journaled blobs, no P&L/trade-outcome
visibility, agent file carries zero tools.

Layers consumed:
  L1  output/regime_vector.csv          (mechanical, engine lane — BUILT)
  L2  output/analog_days.csv            (historical analogs, engine lane — OPTIONAL hook;
                                         briefing marks it absent until built)
  news data/reference/news_archive.csv  (Brake's timestamped archive — OPTIONAL hook;
                                         arm C only; items published before the cutoff)

NO-HINDSIGHT (structural): `build_briefing(date)` applies ONE cutoff — 08:00 ET on
`date` — to the 1m bars at the top of the function and derives every price feature
from that truncated frame. Day-`date`'s SCHEDULED calendar rows are included (a
schedule is known ex-ante); nothing else from `date` onward can enter. Mirrors the
engine's zero-lookahead discipline (regime_vector is pre-open by construction).

The verdict gates the ENGINE, not the world: `verdict_to_gate()` emits the
condition-style de-risk dict the replay harness / Vault consumes (design doc:
"the Vault consumes this like the existing condition-based de-risks").
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, time as dtime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from pydantic import BaseModel, field_validator, model_validator

NY = ZoneInfo("America/New_York")
CUTOFF_ET = dtime(8, 0)          # design doc L1: everything strictly pre-open (08:00 ET)
TRAILING_SESSIONS = 10           # completed sessions summarized in the briefing
SHOCK_LOOKBACK_SESSIONS = 5      # sessions scanned for shock bars
SHOCK_MIN_PTS = 40.0             # 1m range >= max(this, SHOCK_MULT x trailing median) = shock
SHOCK_MULT = 6.0                 # pass-14 headline-shock proxy (Mar 23 ceasefire: 408pts/1m)
AGENT_FILE = Path(".claude/agents/regime-context.md")

REGIMES = ("balance", "war", "trap", "event_risk")          # design doc L3 output contract
STRUCTURES = ("reversion", "continuation")


# ------------------------------------------------------------------ verdict schema

class RegimeVerdict(BaseModel, extra="forbid"):
    """Strict-JSON daily verdict. Anything but a valid instance = fail-closed veto
    (the replay treats a failed day as stand_down + an agent_error journal row)."""

    schema_version: str
    agent_version: str                     # sha256[:12] of the agent file that produced it
    date: str                              # YYYY-MM-DD, must echo the briefing date
    regime: str                            # balance | war | trap | event_risk
    directional_bias: str                  # long | short | neutral
    permitted_structures: list[str]        # subset of {reversion, continuation}
    stand_down: bool
    size_multiplier: float                 # 0.0 | 0.5 | 1.0
    confidence: str                        # low | medium | high
    rationale: str                         # <= 600 chars, cites briefing facts only
    cited_evidence: list[str]              # <= 8 briefing-field references
    playbook_notes: str                    # <= 1500 chars — the agent's adaptation memory,
                                           # journaled every day (design doc L3)

    @field_validator("regime")
    @classmethod
    def _regime(cls, v: str) -> str:
        if v not in REGIMES:
            raise ValueError(f"regime must be one of {REGIMES}")
        return v

    @field_validator("directional_bias")
    @classmethod
    def _bias(cls, v: str) -> str:
        if v not in ("long", "short", "neutral"):
            raise ValueError("directional_bias must be long|short|neutral")
        return v

    @field_validator("confidence")
    @classmethod
    def _conf(cls, v: str) -> str:
        if v not in ("low", "medium", "high"):
            raise ValueError("confidence must be low|medium|high")
        return v

    @field_validator("size_multiplier")
    @classmethod
    def _size(cls, v: float) -> float:
        if v not in (0.0, 0.5, 1.0):
            raise ValueError("size_multiplier must be 0.0, 0.5 or 1.0")
        return v

    @field_validator("permitted_structures")
    @classmethod
    def _structs(cls, v: list[str]) -> list[str]:
        bad = [s for s in v if s not in STRUCTURES]
        if bad or len(v) != len(set(v)):
            raise ValueError(f"permitted_structures must be a unique subset of {STRUCTURES}")
        return v

    @field_validator("rationale")
    @classmethod
    def _rat(cls, v: str) -> str:
        if not v or len(v) > 600:
            raise ValueError("rationale must be 1..600 chars")
        return v

    @field_validator("cited_evidence")
    @classmethod
    def _ev(cls, v: list[str]) -> list[str]:
        if not v or len(v) > 8:
            raise ValueError("cited_evidence must have 1..8 items")
        return v

    @field_validator("playbook_notes")
    @classmethod
    def _notes(cls, v: str) -> str:
        if len(v) > 1500:
            raise ValueError("playbook_notes must be <= 1500 chars")
        return v

    @model_validator(mode="after")
    def _stand_down_consistency(self) -> "RegimeVerdict":
        if self.stand_down and (self.permitted_structures or self.size_multiplier != 0.0):
            raise ValueError("stand_down=true requires empty permitted_structures and size 0")
        if not self.stand_down and self.size_multiplier == 0.0:
            raise ValueError("size 0 without stand_down=true is contradictory")
        if not self.stand_down and not self.permitted_structures:
            raise ValueError("not standing down but no permitted structures")
        return self


class RegimeGate(BaseModel, extra="forbid"):
    """Engine-consumable de-risk condition (one per session day)."""

    date: str
    allow_reversion: bool
    allow_continuation: bool
    size_multiplier: float
    directional_bias: str


def verdict_to_gate(v: RegimeVerdict) -> RegimeGate:
    return RegimeGate(
        date=v.date,
        allow_reversion=(not v.stand_down) and "reversion" in v.permitted_structures,
        allow_continuation=(not v.stand_down) and "continuation" in v.permitted_structures,
        size_multiplier=0.0 if v.stand_down else v.size_multiplier,
        directional_bias=v.directional_bias,
    )


# ------------------------------------------------------------------ briefing builder

def _r(x: float | None, nd: int = 2) -> float | None:
    return None if x is None or pd.isna(x) else round(float(x), nd)


def build_briefing(
    date: str,
    df_1m: pd.DataFrame,
    regime_vector: pd.DataFrame,
    calendar: pd.DataFrame,
    analogs: pd.DataFrame | None = None,
    news: pd.DataFrame | None = None,
    playbook_notes: str = "",
) -> dict:
    """Assemble the pre-open briefing for `date`. ONE cutoff, applied here, nowhere else.

    calendar: datetime_ET (tz-aware), event, impact. Day-`date` rows are included in
    full (schedules are ex-ante); rows after `date` never are.
    news (optional, arm C): must carry published_ET; only rows strictly before the
    cutoff are included — the caller does NOT pre-filter, we enforce it here.
    """
    cutoff = pd.Timestamp(datetime.combine(pd.Timestamp(date).date(), CUTOFF_ET), tz=NY)
    past = df_1m[df_1m["ts_event"] < cutoff]
    if past.empty:
        raise ValueError(f"no bars before cutoff {cutoff} — cannot brief")

    # --- completed prior sessions (CME date = 18:00 boundary), most recent last
    sd = past["ts_event"].dt.tz_convert(NY)
    sess_date = (sd + pd.Timedelta(hours=6)).dt.date          # 18:00 -> next calendar day
    frame = past.assign(_sd=sess_date)
    today_sd = pd.Timestamp(date).date()
    prior = frame[frame["_sd"] < today_sd]
    g = prior.groupby("_sd", sort=True)
    sessions = pd.DataFrame({
        "open": g["open"].first(), "close": g["close"].last(),
        "high": g["high"].max(), "low": g["low"].min(),
    }).tail(TRAILING_SESSIONS)
    sessions["net_pts"] = sessions["close"] - sessions["open"]
    trailing = [
        {"date": str(d), "net_pts": _r(row.net_pts), "range_pts": _r(row.high - row.low),
         "close": _r(row.close)}
        for d, row in sessions.iterrows()
    ]

    # directional persistence + location vs the trailing window
    nets = sessions["net_pts"].to_numpy()
    streak = 0
    for x in nets[::-1]:
        if streak == 0:
            sign = 1 if x > 0 else -1 if x < 0 else 0
        if sign == 0 or (x > 0) != (sign > 0) or x == 0:
            break
        streak += 1
    last_px = float(past["close"].iloc[-1])
    win_hi, win_lo = float(sessions["high"].max()), float(sessions["low"].min())

    # --- today's overnight (18:00 prev -> cutoff)
    on = frame[frame["_sd"] == today_sd]
    overnight = None
    if not on.empty:
        prior_close = float(sessions["close"].iloc[-1]) if len(sessions) else None
        overnight = {
            "net_pts": _r(on["close"].iloc[-1] - on["open"].iloc[0]),
            "range_pts": _r(on["high"].max() - on["low"].min()),
            "gap_vs_prior_close_pts": _r(last_px - prior_close) if prior_close else None,
        }

    # --- shock bars (headline proxy, pass 14): trailing sessions incl. overnight
    recent_sds = sorted(set(frame["_sd"]))[-SHOCK_LOOKBACK_SESSIONS:]
    recent = frame[frame["_sd"].isin(recent_sds)]
    rng = recent["high"] - recent["low"]
    thr = max(SHOCK_MIN_PTS, SHOCK_MULT * float(rng.median()))
    shocks = recent[rng >= thr]
    shock_summary = {
        "threshold_pts": _r(thr), "count": int(len(shocks)),
        "largest": None if shocks.empty else {
            "ts": str(shocks.loc[(shocks["high"] - shocks["low"]).idxmax(), "ts_event"]),
            "range_pts": _r(float((shocks["high"] - shocks["low"]).max())),
        },
    }

    # --- L1 vector row (already strictly pre-open by construction)
    row = regime_vector[regime_vector["day"] == date]
    if row.empty:
        raise ValueError(f"regime_vector has no row for {date}")
    l1 = {k: (None if pd.isna(v) else (float(v) if isinstance(v, (int, float)) else v))
          for k, v in row.iloc[0].items()}

    # --- calendar: today's schedule (ex-ante) + prior 3 days, never beyond today
    cal = calendar.copy()
    cal["_d"] = cal["datetime_ET"].dt.tz_convert(NY).dt.date
    lo = today_sd - timedelta(days=3)
    sel = cal[(cal["_d"] >= lo) & (cal["_d"] <= today_sd)]
    cal_rows = [
        {"when": r["datetime_ET"].isoformat(), "event": r["event"], "impact": r["impact"],
         "today": r["_d"] == today_sd}
        for _, r in sel.sort_values("datetime_ET").iterrows()
    ]

    # --- optional layers
    analog_block: list[dict] | str = "L2 analog module not available"
    if analogs is not None and not analogs.empty:
        analog_block = analogs.head(10).to_dict("records")
    news_block: list[dict] | str = "news archive not available (arm B)"
    if news is not None and not news.empty:
        nn = news[news["published_ET"] < cutoff].sort_values("published_ET").tail(40)
        news_block = [{"published": r["published_ET"].isoformat(), "headline": r["headline"]}
                      for _, r in nn.iterrows()]

    return {
        "schema_version": "1.0",
        "date": date,
        "weekday": pd.Timestamp(date).strftime("%A"),
        "cutoff_et": cutoff.isoformat(),
        "regime_vector": l1,
        "trailing_sessions": trailing,
        "trailing_stats": {
            "net_5d_pts": _r(float(nets[-5:].sum())) if len(nets) >= 1 else None,
            "net_10d_pts": _r(float(nets.sum())),
            "directional_streak_days": int(streak),
            "pct_off_window_high": _r(100.0 * (win_hi - last_px) / win_hi, 3),
            "pct_off_window_low": _r(100.0 * (last_px - win_lo) / win_lo, 3),
        },
        "overnight": overnight,
        "shock_bars": shock_summary,
        "calendar": cal_rows,
        "analog_days": analog_block,
        "news": news_block,
        "playbook_notes": playbook_notes or "(none yet)",
    }


# ------------------------------------------------------------------ prompt + transport

def agent_version(agent_file: Path = AGENT_FILE) -> str:
    return hashlib.sha256(agent_file.read_bytes()).hexdigest()[:12]


def render_prompt(briefing: dict, agent_file: Path = AGENT_FILE) -> str:
    """Deterministic request: agent definition + canonical-JSON briefing. No wall
    clock, no ids — byte-identical for identical inputs (blueprint §6.3 tier 1)."""
    body = agent_file.read_text()
    payload = json.dumps(briefing, sort_keys=True, ensure_ascii=False, default=str)
    return (
        f"{body}\n\n---\n\nBRIEFING (JSON, your ONLY source of facts):\n{payload}\n\n"
        f"Respond with EXACTLY one JSON object matching the verdict schema. "
        f'Set "agent_version" to "{agent_version(agent_file)}" and "date" to '
        f'"{briefing["date"]}". No prose outside the JSON.'
    )


def parse_verdict(raw: str, expect_date: str) -> RegimeVerdict:
    """Strict parse — fail-closed. Accepts a bare JSON object or one inside a fence."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text[4:] if text.startswith("json") else text
    v = RegimeVerdict.model_validate(json.loads(text))
    if v.date != expect_date:
        raise ValueError(f"verdict date {v.date} != briefing date {expect_date}")
    return v


def blob_ref(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def journal_row(briefing: dict, prompt: str, raw_response: str,
                verdict: BaseModel | None, error: str | None = None,
                agent_file: Path = AGENT_FILE) -> dict:
    """One append-only journal record per grading (desk contract: every verdict —
    valid or failed — is journaled with blob refs). Shared by all desk agents:
    pass the agent's own file so the version stamp is correct."""
    return {
        "date": briefing["date"],
        "agent_version": agent_version(agent_file),
        "briefing_sha": blob_ref(json.dumps(briefing, sort_keys=True, default=str)),
        "prompt_sha": blob_ref(prompt),
        "response_sha": blob_ref(raw_response),
        "valid": verdict is not None,
        "error": error or "",
        **({} if verdict is None else verdict.model_dump()),
    }
