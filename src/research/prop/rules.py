"""Load config/prop_rules.yaml into account records the simulator can run."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATH = ROOT / "config" / "prop_rules.yaml"


@dataclass(frozen=True)
class AccountRules:
    key: str
    firm: str
    plan: str
    stage: str
    size: float
    start_balance: float
    profit_target: float | None
    mll_amount: float
    mll_mode: str
    lock_floor: float | None
    trail_trigger: float | None
    consistency: float | None
    dll: float | None
    dll_is_breach: bool
    max_minis: int
    max_micros: int
    timezone: str
    reopen: str
    flat_by: str
    holding_past_flat_is_breach: bool
    fees: dict[str, Any]
    payout: dict[str, Any] | None
    news_blackout: bool
    news_blackout_minutes: int
    scaling: str
    sources: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    raw: dict[str, Any] = field(default_factory=dict, compare=False)

    @property
    def fee_unconfirmed(self) -> bool:
        fees = self.fees or {}
        if fees.get("fee_status") == "unconfirmed":
            return True
        if self.stage in {"eval", "funded"} and self.firm == "lucid" and fees.get("onetime") is None:
            return self.stage == "eval" or self.plan == "direct"
        return False


def load_document(path: Path | None = None) -> dict[str, Any]:
    src = path or DEFAULT_PATH
    with src.open() as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict) or "accounts" not in data:
        raise ValueError(f"{src} has no accounts")
    return data


def load_accounts(path: Path | None = None) -> dict[str, AccountRules]:
    data = load_document(path)
    clocks = data["clocks"]
    out: dict[str, AccountRules] = {}
    for key, spec in data["accounts"].items():
        clock_name = spec.get("clock")
        if clock_name not in clocks:
            raise ValueError(f"{key} references unknown clock {clock_name}")
        clock = clocks[clock_name]
        if spec["max_micros"] != spec["max_minis"] * 10:
            raise ValueError(f"{key} micro/mini ratio is not 10:1")
        if spec.get("mll_amount") is None:
            raise ValueError(f"{key} has no confirmed max-loss amount")
        fees = dict(spec.get("fees") or {})
        payout = spec.get("payout")
        out[key] = AccountRules(
            key=key,
            firm=spec["firm"],
            plan=spec["plan"],
            stage=spec["stage"],
            size=float(spec["size"]),
            start_balance=float(spec["start_balance"]),
            profit_target=None if spec.get("profit_target") is None else float(spec["profit_target"]),
            mll_amount=float(spec["mll_amount"]),
            mll_mode=spec["mll_mode"],
            lock_floor=None if spec.get("lock_floor") is None else float(spec["lock_floor"]),
            trail_trigger=None if spec.get("trail_trigger") is None else float(spec["trail_trigger"]),
            consistency=None if spec.get("consistency") is None else float(spec["consistency"]),
            dll=None if spec.get("dll") is None else float(spec["dll"]),
            dll_is_breach=bool(spec.get("dll_is_breach", False)),
            max_minis=int(spec["max_minis"]),
            max_micros=int(spec["max_micros"]),
            timezone=clock["timezone"],
            reopen=clock["reopen"],
            flat_by=clock["flat_by"],
            holding_past_flat_is_breach=bool(clock["holding_past_flat_is_breach"]),
            fees=fees,
            payout=None if not payout else dict(payout),
            news_blackout=bool(spec.get("news_blackout", False)),
            news_blackout_minutes=int(spec.get("news_blackout_minutes", 1)),
            scaling=str(spec.get("scaling") or "none"),
            sources=tuple(spec.get("sources") or ()),
            raw=spec,
        )
    return out


def unconfirmed(path: Path | None = None) -> list[dict[str, Any]]:
    items = load_document(path).get("unconfirmed") or []
    for item in items:
        if "id" not in item or "why" not in item:
            raise ValueError(f"unconfirmed entry missing id or why: {item}")
    return items


def session_open(ts, rules: AccountRules) -> bool:
    """True when a new position is allowed. ts must be timezone-aware."""
    import pandas as pd

    local = pd.Timestamp(ts).tz_convert(rules.timezone)
    minutes = local.hour * 60 + local.minute
    flat_h, flat_m = (int(x) for x in rules.flat_by.split(":"))
    open_h, open_m = (int(x) for x in rules.reopen.split(":"))
    flat = flat_h * 60 + flat_m
    reopen = open_h * 60 + open_m
    weekday = local.weekday()
    if weekday == 5:
        return False
    if weekday == 6 and minutes < reopen:
        return False
    if weekday == 4 and minutes >= flat:
        return False
    return not (weekday != 6 and flat <= minutes < reopen)
