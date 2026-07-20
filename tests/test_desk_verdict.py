"""Tests for src/desk/verdict.py — the Python trust boundary on Hermes's output.

Rules match strategy-definition-v1.2.md (the LOCKED strategy, Angus 17 Jul 2026):
full size is the default; half ONLY on an oversized stop (>42pts) or a late-window
fill (>10:30 ET, session-scoped windows only); a stop <10pts should never have been
proposed; the RR floor (2.0R) is measured to the raw target_level, never the
front-run-adjusted target.
"""

import json

from src.desk.verdict import SizingConfig, validate_verdict

CFG = SizingConfig()   # v1.2 defaults: min_stop=10, rr_floor=2.0, oversized=42,
                       # late_window_after="10:30", session_scoped=True


def _gates(all_pass=True):
    v = "pass" if all_pass else "fail"
    return {"atlas": v, "helios": v, "apollo": v, "hephaestus": v}


def _pass_verdict(**overrides):
    """A normal-conviction long: 20pt stop, 2R+ target, filled well before 10:30."""
    base = {
        "trade": True, "pattern": "A", "direction": "long",
        "entry": 25000.0, "stop": 24980.0,          # 20pt stop -> not oversized
        "target_level": 25045.0,                    # 45/20 = 2.25R -> clears 2.0R floor
        "target": 25043.0,                          # front-run-adjusted fill price
        "size": "full", "grade": "A", "thesis": "ok",
        "gates": _gates(True), "trigger_ts": "2026-03-17T08:20:00-04:00",
        "snapshot_ts": "2026-03-17T08:20:00-04:00",
        "facts": {"confluence_count": 2, "with_trend": True,
                  "a_at_extension": False, "target_r_multiple": 2.25,
                  "half_trigger_count": 0, "half_trigger_reasons": []},
    }
    base.update(overrides)
    return json.dumps(base)


def test_valid_full_size_verdict_passes():
    r = validate_verdict(_pass_verdict(), CFG)
    assert r.ok and r.verdict.trade and r.verdict.size == "full" and r.verdict.grade == "A"


def test_invalid_json_rejected():
    r = validate_verdict("{not json", CFG)
    assert not r.ok and "invalid_json" in r.veto_reason


def test_schema_violation_extra_field_rejected():
    obj = json.loads(_pass_verdict())
    obj["not_a_real_field"] = 1
    r = validate_verdict(json.dumps(obj), CFG)
    assert not r.ok and "schema_violation" in r.veto_reason


def test_trade_true_with_a_failed_gate_is_rejected():
    obj = json.loads(_pass_verdict())
    obj["gates"]["apollo"] = "fail"
    r = validate_verdict(json.dumps(obj), CFG)
    assert not r.ok and "hermes_arithmetic_mismatch" in r.veto_reason


def test_missing_gate_key_rejected():
    obj = json.loads(_pass_verdict())
    del obj["gates"]["apollo"]
    r = validate_verdict(json.dumps(obj), CFG)
    assert not r.ok and "schema_violation" in r.veto_reason


def test_well_formed_veto_is_a_valid_result():
    obj = json.loads(_pass_verdict())
    obj["trade"] = False
    obj["gates"]["apollo"] = "fail"
    obj["entry"] = obj["stop"] = obj["target_level"] = obj["target"] = None
    obj["size"] = obj["grade"] = None
    r = validate_verdict(json.dumps(obj), CFG)
    assert r.ok and r.verdict.trade is False


def test_trade_true_missing_construction_fields_rejected():
    obj = json.loads(_pass_verdict())
    obj["entry"] = None
    r = validate_verdict(json.dumps(obj), CFG)
    assert not r.ok and "schema_violation" in r.veto_reason


def test_stop_narrower_than_v12_floor_rejected():
    """§5.4 v1.2: a structural stop <10pts should never have been proposed at all."""
    obj = json.loads(_pass_verdict(entry=25000.0, stop=24994.0,   # 6pt stop
                                   target_level=25020.0, target=25018.0))
    r = validate_verdict(json.dumps(obj), CFG)
    assert not r.ok and "min_stop_violation" in r.veto_reason


def test_target_below_rr_floor_measured_to_raw_level_rejected():
    """§6.5 v1.2: R is measured to target_level, and must be >= 2.0."""
    obj = json.loads(_pass_verdict(entry=25000.0, stop=24980.0,   # 20pt stop
                                   target_level=25030.0,           # 30/20 = 1.5R < 2.0
                                   target=25028.0))
    r = validate_verdict(json.dumps(obj), CFG)
    assert not r.ok and "rr_floor_violation" in r.veto_reason


def test_frontrun_price_never_used_for_rr_floor():
    """The working (front-run) target must NOT rescue a trade that misses the floor
    on the raw target_level, and must not sink one that clears it on target_level."""
    obj = json.loads(_pass_verdict(entry=25000.0, stop=24980.0,
                                   target_level=25045.0,   # 2.25R -> clears floor
                                   target=25010.0))         # working price is much closer
    r = validate_verdict(json.dumps(obj), CFG)              # must still PASS: uses target_level
    assert r.ok


def test_oversized_stop_forces_half_size():
    obj = json.loads(_pass_verdict(entry=25000.0, stop=24950.0,   # 50pt stop > 42
                                   target_level=25150.0, target=25145.0,
                                   size="half", grade="B"))
    r = validate_verdict(json.dumps(obj), CFG)
    assert r.ok and r.verdict.size == "half" and r.verdict.grade == "B"


def test_claiming_full_size_despite_oversized_stop_rejected():
    obj = json.loads(_pass_verdict(entry=25000.0, stop=24950.0,   # 50pt stop > 42
                                   target_level=25150.0, target=25145.0))
    # size/grade left at "full"/"A" from _pass_verdict -> should be rejected
    r = validate_verdict(json.dumps(obj), CFG)
    assert not r.ok and "hermes_arithmetic_mismatch" in r.veto_reason


def test_late_window_fill_forces_half_size_in_session_scoped_window():
    obj = json.loads(_pass_verdict(trigger_ts="2026-03-17T10:45:00-04:00",
                                   size="half", grade="B"))
    r = validate_verdict(json.dumps(obj), CFG)
    assert r.ok and r.verdict.size == "half"


def test_late_window_has_no_effect_in_w2_full_day_window():
    """Angus, 17 Jul: W2 (full-day) testing has NO time-based half-sizing at all."""
    cfg = SizingConfig(window_session_scoped=False)
    obj = json.loads(_pass_verdict(trigger_ts="2026-03-17T14:45:00-04:00"))
    # size/grade stay "full"/"A" -> must PASS despite the late hour, since W2 is exempt
    r = validate_verdict(json.dumps(obj), cfg)
    assert r.ok and r.verdict.size == "full"


def test_confluence_count_and_target_r_facts_are_informational_only():
    """§9 v1.2 explicitly deleted the confluence/target-R sizing ladder — these
    facts must NOT affect the size/grade recompute, only ride along for the audit
    trail (informational facts, never load-bearing)."""
    obj = json.loads(_pass_verdict())
    obj["facts"]["confluence_count"] = 0
    obj["facts"]["with_trend"] = False
    obj["facts"]["a_at_extension"] = False
    r = validate_verdict(json.dumps(obj), CFG)
    assert r.ok and r.verdict.size == "full"          # still full: no ladder anymore


def test_incoherent_long_construction_rejected():
    obj = json.loads(_pass_verdict())
    obj["stop"] = 25010.0                        # stop above entry on a long: wrong
    r = validate_verdict(json.dumps(obj), CFG)
    assert not r.ok and "incoherent_construction" in r.veto_reason


def test_incoherent_short_construction_rejected():
    # short requires target < entry < stop; putting the stop BELOW entry breaks it
    obj = json.loads(_pass_verdict(direction="short", entry=25000.0,
                                   stop=24980.0, target_level=24950.0,
                                   target=24952.0))
    r = validate_verdict(json.dumps(obj), CFG)
    assert not r.ok and "incoherent_construction" in r.veto_reason


def test_none_input_rejected_not_raised():
    r = validate_verdict(None, CFG)
    assert not r.ok and "invalid_json" in r.veto_reason
