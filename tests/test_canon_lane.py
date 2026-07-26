"""Canon-lane verdict source + mappers (src/desk/canon_lane.py).

Offline: the frozen scripts are stubbed by an injected engine_fn returning fixture books, so
these test the size -> level-join -> target -> drop -> relay chain and the verdict->intent
mapping WITHOUT shelling out. The real shell-out (ScriptVerdictSource default engine_fn) is the
on-box path proven separately."""
from __future__ import annotations

import pandas as pd

from src.canon.spine import OrderIntent
from src.desk.canon_lane import (
    ScriptVerdictSource,
    verdict_record,
    verdict_to_intent,
)


def _fixture_engine():
    ny = pd.DataFrame({
        "day": ["2026-03-17", "2026-03-17"],
        "book": ["E3", "E3"],
        "fill": ["2026-03-17 13:00:00+00:00", "2026-03-17 14:00:00+00:00"],
        "direction": ["long", "short"],
        "entry": [18000.0, 18050.0], "stop": [17990.0, 18060.0],
        "size": [1.0, 1.5], "risk": [10.0, 10.0], "dollars": [100.0, -50.0],
        "yr": [2026, 2026],
    })
    lon = pd.DataFrame({
        "day": ["2026-03-17"], "book": ["W1"], "fill": ["2026-03-17 07:30:00+00:00"],
        "direction": ["long"], "entry": [17800.0], "stop": [17790.0],
        "size": [1.0], "risk": [10.0], "dollars": [80.0], "yr": [2026],
    })
    return ny, lon


def test_session_verdicts_size_level_target_and_relay():
    src = ScriptVerdictSource(engine_fn=_fixture_engine)
    vs = src.session_verdicts("2026-03-17")
    assert len(vs) == 3
    # fill-sorted: London 07:30, NY 13:00, NY 14:00
    assert [v["session"] for v in vs] == ["LONDON", "NY", "NY"]
    ny_long = next(v for v in vs if v["fill"].startswith("2026-03-17T13:00"))
    assert ny_long["entry"] == 18000.0 and ny_long["stop"] == 17990.0
    assert ny_long["target"] == 18020.0            # long: entry + 2R*risk (10) = +20
    assert ny_long["micros"] == 10                 # conv 1.0, risk 10 -> 200/20
    ny_short = next(v for v in vs if v["fill"].startswith("2026-03-17T14:00"))
    assert ny_short["target"] == 18030.0           # short: entry - 2R*risk = 18050-20
    assert ny_short["micros"] == 15                # conv 1.5 -> 300/20


def test_session_verdicts_empty_for_other_day():
    src = ScriptVerdictSource(engine_fn=_fixture_engine)
    assert src.session_verdicts("2026-03-18") == []


def test_verdict_to_intent_uses_verdict_micros():
    src = ScriptVerdictSource(engine_fn=_fixture_engine)
    v = next(x for x in src.session_verdicts("2026-03-17") if x["direction"] == "short")
    intent = verdict_to_intent(v, account="FUNDED")
    assert isinstance(intent, OrderIntent)
    assert intent.side == "S" and intent.order_type == "limit"
    assert intent.size == v["micros"] and intent.account == "FUNDED"
    assert intent.entry_ref == v["entry"] and intent.target == v["target"]


def test_verdict_record_carries_roll_ctx():
    v = {"session": "NY", "day": "2026-03-17", "fill": "2026-03-17T13:00:00+00:00",
         "direction": "long", "entry": 18000.0, "stop": 17990.0, "target": 18020.0,
         "conviction": 1.0, "risk_pts": 10.0, "micros": 10, "pl": 100.0}
    rec = verdict_record(v, roll_ctx={"roll": True, "contract": "NQZ26"})
    assert rec["type"] == "verdict" and rec["micros"] == 10
    assert rec["roll"] is True and rec["contract"] == "NQZ26"
