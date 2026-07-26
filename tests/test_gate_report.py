"""Tests for scripts/gate_report.py — the A/B/C/D PASS/FAIL emitter (docs/PROMOTION-GATE.md).

Evaluators are pure (take loaded artifacts), so most tests pass lightweight namespaces; one
end-to-end test writes real journal/spine artifacts and asserts the rendered verdict."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

_SPEC = importlib.util.spec_from_file_location(
    "gate_report", Path(__file__).resolve().parents[1] / "scripts" / "gate_report.py")
gr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gr)

from src.desk.journal import JournalRecord  # noqa: E402


def _trade(session="ny", playbook="E4", slippage=1, entry_variant="E1",
           trade_date="2026-03-06", fill_ts="2026-03-06T09:30:00-05:00"):
    return SimpleNamespace(session=session, playbook=playbook, slippage_ticks=slippage,
                           entry_variant=entry_variant, trade_date=trade_date, fill_ts=fill_ts)


def _by_id(gates):
    return {g.id: g for g in gates}


# --------------------------------------------------------------------------- A
def test_A_both_books_and_completeness():
    a = {"trades": [_trade(session="ny"), _trade(session="london", playbook="london_canon")],
         "corrupt_journal_lines": 0}
    g = _by_id(gr.eval_A(a, expected=None))
    assert g["A5"].status == gr.PASS                 # both books fired
    assert g["A6"].status == gr.PASS                 # zero malformed
    assert g["A4"].status == gr.INCONCLUSIVE         # no --expected reference
    assert g["A1"].status == gr.INCONCLUSIVE         # needs parity artifact


def test_A5_fails_when_one_book_missing_and_A6_on_corruption():
    a = {"trades": [_trade(session="ny")], "corrupt_journal_lines": 2}
    g = _by_id(gr.eval_A(a, expected=None))
    assert g["A5"].status == gr.FAIL
    assert g["A6"].status == gr.FAIL


def test_A4_missed_trade_fails():
    a = {"trades": [_trade(trade_date="2026-03-06", fill_ts="t1")], "corrupt_journal_lines": 0}
    expected = [("2026-03-06", "t1"), ("2026-03-06", "t2")]      # t2 never taken
    g = _by_id(gr.eval_A(a, expected))
    assert g["A4"].status == gr.FAIL and "1 missed" in g["A4"].detail


# --------------------------------------------------------------------------- B
def _base_b(**over):
    a = {"trades": [_trade()], "spine": [], "sizing": [], "feed_lag": []}
    a.update(over)
    return a


def test_B2_market_order_disqualifies():
    a = _base_b(trades=[_trade(entry_variant="market")])
    assert _by_id(gr.eval_B(a))["B2"].status == gr.FAIL


def test_B4_naked_position_fails_else_pass():
    fail = gr.eval_B(_base_b(spine=[{"event": "naked_position", "account": "ACC"}]))
    assert _by_id(fail)["B4"].status == gr.FAIL
    ok = gr.eval_B(_base_b(spine=[{"event": "placed", "setup": "s1"}]))
    assert _by_id(ok)["B4"].status == gr.PASS
    none = gr.eval_B(_base_b(spine=[]))
    assert _by_id(none)["B4"].status == gr.INCONCLUSIVE


def test_B5_sizing_pass_and_fail():
    ok = gr.eval_B(_base_b(sizing=[{"conviction": 1.0, "stop_pts": 10.0, "micros": 10}]))
    assert _by_id(ok)["B5"].status == gr.PASS
    bad = gr.eval_B(_base_b(sizing=[{"conviction": 1.0, "stop_pts": 10.0, "micros": 15}]))
    assert _by_id(bad)["B5"].status == gr.FAIL


def test_B6_feed_lag_and_B1_unset():
    g = _by_id(gr.eval_B(_base_b(feed_lag=[{"lag_s": 1.2}, {"lag_s": 0.8}])))
    assert g["B6"].status == gr.PASS
    assert g["B1"].status == gr.UNSET                # slippage measured, threshold [SET]


# --------------------------------------------------------------------------- C
def test_C5_spine_rule_coverage():
    spine = [{"event": "decision", "action": "reject", "rule": r} for r in gr.REQUIRED_SPINE_RULES]
    full = _by_id(gr.eval_C({"decisions": [], "spine": spine}))
    assert full["C5"].status == gr.PASS
    partial = _by_id(gr.eval_C({"decisions": [], "spine": spine[:3]}))
    assert partial["C5"].status == gr.FAIL and "missing" in partial["C5"].detail


def test_C4_kill_needs_two_operators():
    dec2 = [{"type": "halt", "reason": "kill_switch", "operator": "pat"},
            {"type": "halt", "reason": "kill_switch", "operator": "angus"}]
    assert _by_id(gr.eval_C({"decisions": dec2, "spine": []}))["C4"].status == gr.PASS
    dec1 = [{"type": "halt", "reason": "kill_switch", "operator": "pat"}]
    assert _by_id(gr.eval_C({"decisions": dec1, "spine": []}))["C4"].status == gr.FAIL
    assert _by_id(gr.eval_C({"decisions": [], "spine": []}))["C4"].status == gr.INCONCLUSIVE


# --------------------------------------------------------------------------- D
def test_D_dst_and_weekend_and_counts():
    # window 2026-03-06 (Fri) .. 2026-03-09 (Mon) spans the Mar-8 DST change AND a weekend
    trades = [_trade(trade_date="2026-03-06"), _trade(trade_date="2026-03-09", session="london",
                                                      playbook="london")]
    g = _by_id(gr.eval_D({"trades": trades}))
    assert g["D3"].status == gr.PASS                 # covers Mar 8 DST
    assert g["D4"].status == gr.PASS                 # spans Sun Mar 8
    assert g["D1"].status == gr.UNSET and g["D2"].status == gr.UNSET


def test_D3_fails_without_dst():
    trades = [_trade(trade_date="2026-06-01"), _trade(trade_date="2026-06-02")]
    g = _by_id(gr.eval_D({"trades": trades}))
    assert g["D3"].status == gr.FAIL


# --------------------------------------------------------------------------- end-to-end
def _make_record(session, playbook):
    return JournalRecord(
        trade_date="2026-03-06", trigger_ts="2026-03-06T09:20:00-05:00", tf="1min",
        direction="long", entry_variant="E1", mgmt_variant="V0", config_hash="abc123",
        kind="rejection_block", pattern="A", htf_flag="with_trend", confluence_count=2,
        entry=18000.0, stop_initial=17990.0, size=1.0, exit_ts="2026-03-06T10:00:00-05:00",
        exit_price=18050.0, exit_reason="target", points=50.0, r_multiple=2.0, dollars=100.0,
        slippage_ticks=1, session=session, playbook=playbook)


def test_build_report_end_to_end(tmp_path):
    (tmp_path / "journal.jsonl").write_text(
        _make_record("ny", "E4").model_dump_json() + "\n"
        + _make_record("london", "london_canon").model_dump_json() + "\n")
    (tmp_path / "feed_lag.jsonl").write_text('{"lag_s": 1.1}\n{"lag_s": 0.9}\n')
    (tmp_path / "spine.jsonl").write_text('{"event": "placed", "setup": "s1"}\n')

    report, all_pass = gr.build_report(tmp_path, expected_path=None)
    assert "A. Correctness" in report and "D. Sample" in report
    assert "Both books exercised" in report
    # A1-A3 are INCONCLUSIVE without parity artifacts, so overall must NOT promote.
    assert all_pass is False
    assert "DO NOT PROMOTE" in report
