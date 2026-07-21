"""Pydantic v2 model for the Engine candidate payload.

This is the ENGINE's output contract: 20 market-observation fields. The four
account/history fields (recent_trade_history, setup_historical_performance,
account_risk_percent_per_trade, proposed_position_size_and_risk) are DELIBERATELY
absent — the Vault injects those downstream, preserving the Engine's
no-account-visibility firewall (architecture.md layer contract).
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

# The Engine's 20-field contract, in order.
ENGINE_FIELDS = [
    "candidate_direction",
    "higher_timeframe_swing_sequence",
    "price_position_in_range",
    "upcoming_news_events",
    "current_session",
    "broad_risk_tone",
    "liquidity_pool_swept",
    "liquidity_draw_target",
    "entry_relative_to_sweep",
    "entry_trigger_type",
    "entry_price",
    "trigger_zone",
    "spread_and_fill_data",
    "current_time_window",
    "recent_volume_and_volatility",
    "setup_timing_alignment",
    "stop_price",
    "invalidation_price",
    "target_price",
    "playbook_match",
]

# Fields the Vault adds later to form the full 24-field Hermes candidate.
VAULT_INJECTED_FIELDS = [
    "recent_trade_history",
    "setup_historical_performance",
    "account_risk_percent_per_trade",
    "proposed_position_size_and_risk",
]


class EngineCandidate(BaseModel):
    """Structural validation only (types kept loose — the values are the
    Engine's honest observation, incl. explicit nulls where a data source such
    as an L1 book or cross-asset feed is not present in 1m OHLCV)."""
    model_config = ConfigDict(extra="forbid")

    candidate_direction: str
    higher_timeframe_swing_sequence: list[dict[str, Any]]
    price_position_in_range: dict[str, Any]
    upcoming_news_events: list[dict[str, Any]]
    current_session: str
    broad_risk_tone: dict[str, Any]
    liquidity_pool_swept: Optional[dict[str, Any]]
    liquidity_draw_target: dict[str, Any]
    entry_relative_to_sweep: Optional[str]
    entry_trigger_type: str
    entry_price: float
    trigger_zone: dict[str, Any]
    spread_and_fill_data: dict[str, Any]
    current_time_window: dict[str, Any]
    recent_volume_and_volatility: dict[str, Any]
    setup_timing_alignment: dict[str, Any]
    stop_price: float
    invalidation_price: float
    target_price: float
    playbook_match: dict[str, Any]
