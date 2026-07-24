"""Frozen trade-journal schema (Pat's lane — Hermes reporting duty, pass-24 directive).

docs/TASK-FOR-PAT-trade-journal-agent.md assigned the executed-trade journaling
duty to Hermes. This module is the FROZEN schema that duty writes to — the
single contract shared by (a) the backtester's per-trade output, (b) the
walk-forward replay's memory, and (c) the live execution feed later. Per the
task doc it EXTENDS the engine's `TradeRecord` rather than duplicating it.

STATUS: SUPERSEDED FOR THE CORE by the engine lane's frozen v1.0
(docs/JOURNAL-SCHEMA-v1.md, pass 30) — THAT is the authoritative journal
(producer = engine lane). This module is now REFRAMED as the **v1.1 extension
proposal**: the executed-trade superset + the agent-output / review fields the
engine v1.0 explicitly RESERVED ("regime_call / regime_conf / playbook",
"analog_k_winrate", "news_ids"). It does not compete with v1.0; it proposes the
next version's additions using the reserved names. Ratification = engine lane +
Angus, as a v1.1 bump. See docs/journal-schema-freeze.md for the mapping.

The freeze reconciles two emitters that have already drifted: the engine's
`TradeRecord` (src/backtest/engine.py) and the condensed `output/journal_*.csv`
(which carries `align_votes`, `pre930`, `risk_pts`, `hold_min`, `win` that
`TradeRecord` lacks). `coverage_report()` lists exactly what each is missing so
the engine lane knows what to add.

Desk context (regime/HTF verdicts + the gates that admitted the trade) is part
of the record: the adaptation experiment's memory needs to know WHY a trade was
allowed, not just what happened. These fields are OPTIONAL — a pre-agent
backtest row leaves them null; an agent-gated row fills them.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = "0.1.0-proposed"

Direction = Literal["long", "short"]
ClusterType = Literal["bb", "vwap", "poc", "ote", "structural"]


class JournalRecord(BaseModel, extra="forbid"):
    """One executed trade, every criterion from the task doc. extra='forbid' so a
    stray column is a loud error, not silent drift (the whole point of freezing)."""

    schema_version: str = SCHEMA_VERSION

    # --- identity -----------------------------------------------------------
    trade_date: str                       # session date YYYY-MM-DD (18:00 CME boundary)
    trigger_ts: str                       # ISO ET candle-close time of the trigger
    tf: str                               # entry timeframe (1min|2min|3min|5min)
    direction: Direction
    entry_variant: str                    # E1|E2|E3 (§5.3) — champion journal calls it "branch"
    mgmt_variant: str                     # V0..V9 (§8)
    config_hash: str                      # reproducibility stamp of the config that ran it

    # --- setup --------------------------------------------------------------
    kind: str                             # rejection_block | displacement (§3)
    pattern: str                          # A | B | B2 (§4)
    htf_flag: str                         # with_trend | counter_trend | range (§4)
    confluence_count: int                 # distinct level types (§3/§7)
    cluster_types: list[ClusterType] = Field(default_factory=list)
    cluster_center: float | None = None
    vwap_touched: bool | None = None
    align_votes: int | None = None        # champion-journal HTF-alignment vote count
    day_type: str | None = None           # balanced | imbalanced | unknown (AMT layer)
    session: str | None = None            # premarket | ny | ...
    pre_930: bool | None = None           # entered before the 09:30 open
    news_context: str | None = None       # e.g. "high_impact:CPI" | "none"

    # --- execution ----------------------------------------------------------
    limit_price: float | None = None
    fill_ts: str | None = None
    entry: float
    slippage_ticks: int | None = None
    stop_initial: float
    risk_pts: float | None = None         # |entry - stop_initial| (champion journal carries it)
    target_name: str | None = None
    target_level: float | None = None
    working_target: float | None = None   # target ∓ front-run F (§6.4)
    rr_at_entry: float | None = None
    size: float                           # §9 unit: 1.0 full | 0.5 half

    # --- path ---------------------------------------------------------------
    mfe_r: float | None = None
    mae_r: float | None = None
    time_to_mfe_min: float | None = None
    hold_min: float | None = None
    partial_fills: int | None = None
    trail_moves: int | None = None
    be_armed: bool | None = None

    # --- outcome ------------------------------------------------------------
    exit_ts: str
    exit_price: float
    exit_reason: str                      # target | stop | be_stop | eod | partial+<reason>
    points: float
    r_multiple: float
    dollars: float                        # net of commissions, at size
    win: bool | None = None

    # --- desk context (optional — v1.1 additions, using engine v1.0's RESERVED names) ---
    regime_call: str | None = None        # reserved v1.0 name; e.g. "balance" (regime agent)
    regime_conf: str | None = None        # reserved v1.0 name; low|medium|high
    playbook: str | None = None           # reserved v1.0 name; the permitted-structure/book choice
    htf_verdict: str | None = None        # HTF agent: e.g. "range/rotation/fade_ok"
    analog_k_winrate: float | None = None # reserved v1.0 name; L2 lookup empirical win rate
    news_ids: list[str] = Field(default_factory=list)       # reserved v1.0 name; briefing item ids
    gates_applied: list[str] = Field(default_factory=list)  # which de-risks were live
    size_multiplier_applied: float | None = None            # agent size mult that scaled this

    # --- ambient context (Angus 24 Jul CANON ruling — journal-only, gate NOTHING new) ---
    # The ruling RETIRED three live-desk vetoes and mandated journaling the state each one
    # read, on every trade, so they can be re-evaluated on live evidence. All optional
    # (None) so pre-ruling rows still validate and the Stage-7 reconcile keys are untouched.
    # See src/live/ambient.py and docs/ambient-instrumentation-choices.md.
    sweep_state: str | None = None          # Q-30 (veto DROPPED): swept_before_entry |
                                            #   swept_after_entry | no_sweep | unknown
    spread_at_fill: float | None = None     # Q-31: execution spread at the fill, in points
                                            #   (range proxy until a quote feed lands)
    news_calendar_state: str | None = None  # Q-33 (buffer DROPPED): "{event}:T{+/-}{min}"
                                            #   signed minutes to the nearest high-impact
                                            #   release, or "none"

    # --- review (Angus-filled later) ----------------------------------------
    angus_verdict: str | None = None      # free text: "valid I'd take" | "wouldn't" | "missed context"
    would_angus_take: bool | None = None  # prefilled by the capture-matcher on a hand-log match

    @field_validator("cluster_types")
    @classmethod
    def _unique(cls, v: list[str]) -> list[str]:
        if len(v) != len(set(v)):
            raise ValueError("cluster_types must be unique")
        return v

    @field_validator("win")
    @classmethod
    def _win_consistent(cls, v, info):
        # win, when present, must agree with the sign of r_multiple
        r = info.data.get("r_multiple")
        if v is not None and r is not None and v != (r > 0):
            raise ValueError(f"win={v} disagrees with r_multiple={r}")
        return v


# ------------------------------------------------------------------ adapters

# engine TradeRecord field -> frozen field (rename map; everything else is 1:1)
_TR_RENAME = {
    "confluence": "confluence_count",
    "exit_price": "exit_price",
}


def from_trade_record(tr: BaseModel, config_hash: str, **desk_context) -> JournalRecord:
    """Lift an engine `TradeRecord` into the frozen schema, deriving what it omits.

    desk_context accepts any optional desk/review field (regime_call, etc.).
    """
    d = tr.model_dump()
    data = {
        "trade_date": d["trade_date"], "trigger_ts": d["trigger_ts"], "tf": d["tf"],
        "direction": d["direction"], "entry_variant": d["entry_variant"],
        "mgmt_variant": d["mgmt_variant"], "config_hash": config_hash,
        "kind": d["kind"], "pattern": d["pattern"], "htf_flag": d["htf_flag"],
        "confluence_count": d["confluence"],
        "limit_price": d["limit_price"], "fill_ts": d["fill_ts"], "entry": d["entry"],
        "slippage_ticks": d["slippage_ticks"], "stop_initial": d["stop_initial"],
        "risk_pts": round(abs(d["entry"] - d["stop_initial"]), 2),
        "target_name": d["target_name"], "target_level": d["target_level"],
        "working_target": d["working_target"], "size": d["size"],
        "exit_ts": d["exit_ts"], "exit_price": d["exit_price"],
        "exit_reason": d["exit_reason"], "points": d["points"],
        "r_multiple": d["r_multiple"], "dollars": d["dollars"],
        "win": d["r_multiple"] > 0,
        **desk_context,
    }
    return JournalRecord(**data)


# ------------------------------------------------------------------ coverage / freeze aid

# task-doc "relevant criteria" grouped — the target the freeze must cover
REQUIRED_SECTIONS = {
    "identity": ["trade_date", "trigger_ts", "tf", "direction", "entry_variant",
                 "mgmt_variant", "config_hash"],
    "setup": ["kind", "pattern", "htf_flag", "confluence_count", "cluster_types",
              "cluster_center", "vwap_touched", "day_type", "session", "news_context"],
    "execution": ["limit_price", "fill_ts", "entry", "slippage_ticks", "stop_initial",
                  "target_name", "target_level", "working_target", "rr_at_entry", "size"],
    "path": ["mfe_r", "mae_r", "time_to_mfe_min", "partial_fills", "trail_moves", "be_armed"],
    "outcome": ["exit_ts", "exit_price", "exit_reason", "points", "r_multiple", "dollars"],
    "review": ["angus_verdict", "would_angus_take"],
}


def coverage_report(emitted_columns: list[str]) -> dict:
    """What a current emitter (engine TradeRecord fields, or a journal CSV header)
    is MISSING vs the frozen schema — the actionable freeze checklist."""
    frozen = set(JournalRecord.model_fields)
    emitted = set(emitted_columns)
    # apply known renames so TradeRecord's "confluence" counts as covered
    normalized = {(_TR_RENAME.get(c, c)) for c in emitted}
    per_section = {
        sec: [f for f in fields if f not in normalized]
        for sec, fields in REQUIRED_SECTIONS.items()
    }
    return {
        "frozen_field_count": len(frozen),
        "emitted_field_count": len(emitted),
        "missing_by_section": {k: v for k, v in per_section.items() if v},
        "unknown_emitted": sorted(normalized - frozen),   # columns not in the frozen schema
    }
