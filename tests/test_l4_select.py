"""L4 selector — the cap/escalation/causality contract, held as executable assertions.

Every test here encodes a rule whose silent violation cost us the canon:
the shared cap (test_sections_are_independent would have failed for months),
the day-keyed escalation, and best-of-day lookahead.
"""
import pandas as pd
import pytest

from scripts.l4_select import L4Policy, select, summarize


def cands(rows):
    return pd.DataFrame(
        [{"day": d, "session": s, "fill_ts": f"{d} {hm}", "score": sc, "dollars": dol}
         for d, s, hm, sc, dol in rows])


POL = L4Policy()      # 2/session, T=3, escalation bar 4, day stop $400 day-keyed


def test_sections_are_independent():
    """THE canon bug, inverted: 2 pre fills must never starve gold of its slots."""
    b = select(cands([
        ("2025-06-02", "pre", "08:10", 5, 100.0),
        ("2025-06-02", "pre", "08:40", 5, 100.0),
        ("2025-06-02", "gold", "09:45", 5, 100.0),
        ("2025-06-02", "gold", "10:00", 5, 100.0),
    ]), POL)
    assert b.taken.all(), "gold was starved by pre-market fills — the exact shipped defect"
    assert list(b.nth) == [1, 2, 1, 2]


def test_session_cap_is_enforced():
    b = select(cands([
        ("2025-06-02", "pre", "08:10", 5, 100.0),
        ("2025-06-02", "pre", "08:20", 5, 100.0),
        ("2025-06-02", "pre", "08:30", 5, 100.0),
    ]), POL)
    assert list(b.taken) == [True, True, False]
    assert b.kill_reason.iloc[2] == "session_cap"


def test_escalation_second_slot_needs_higher_bar():
    """L2b per session: slot 2 demands score >= escalation_threshold."""
    b = select(cands([
        ("2025-06-02", "gold", "09:45", 3, -50.0),
        ("2025-06-02", "gold", "09:55", 3, 100.0),   # score 3 < bar 4 on slot 2
        ("2025-06-02", "gold", "10:05", 4, 100.0),
    ]), POL)
    assert list(b.taken) == [True, False, True]
    assert b.kill_reason.iloc[1] == "escalation_bar"


def test_escalation_does_not_leak_across_sessions():
    """A pre-market first trade must not force gold's FIRST trade to the escalated bar —
    the live NYScorer._day_taken defect."""
    b = select(cands([
        ("2025-06-02", "pre", "08:10", 5, -100.0),
        ("2025-06-02", "gold", "09:45", 3, 100.0),   # gold's 1st: plain T applies
    ]), POL)
    assert b.taken.iloc[1], "gold's first trade was held to the escalated bar"


def test_escalation_after_loss_only_mode():
    pol = L4Policy(escalation_after_loss_only=True)
    b = select(cands([
        ("2025-06-02", "gold", "09:45", 4, 100.0),   # winner first
        ("2025-06-02", "gold", "09:55", 3, 100.0),   # no loss yet -> plain T
    ]), pol)
    assert list(b.taken) == [True, True]
    b2 = select(cands([
        ("2025-06-02", "gold", "09:45", 4, -100.0),  # loser first
        ("2025-06-02", "gold", "09:55", 3, 100.0),   # after a loss -> escalated bar
    ]), pol)
    assert list(b2.taken) == [True, False]


def test_day_stop_halts_entries():
    b = select(cands([
        ("2025-06-02", "pre", "08:10", 5, -400.0),
        ("2025-06-02", "gold", "09:45", 5, 100.0),
    ]), POL)
    assert not b.taken.iloc[1]
    assert b.kill_reason.iloc[1] == "day_stop"


def test_day_stop_session_key_isolates_sessions():
    pol = L4Policy(day_stop_key="session")
    b = select(cands([
        ("2025-06-02", "pre", "08:10", 5, -400.0),
        ("2025-06-02", "gold", "09:45", 5, 100.0),   # gold's own book is flat
    ]), pol)
    assert b.taken.iloc[1]


def test_causality_no_best_of_day():
    """cap 1: the FIRST candidate clearing T takes the slot, even when a better score
    arrives later. Best-of-day is lookahead and must be structurally impossible."""
    pol = L4Policy(cap_per_session=1)
    b = select(cands([
        ("2025-06-02", "gold", "09:45", 3, -50.0),
        ("2025-06-02", "gold", "10:00", 5, 500.0),
    ]), pol)
    assert list(b.taken) == [True, False]


def test_causality_future_rows_cannot_change_past_decisions():
    base = [("2025-06-02", "gold", "09:45", 3, -50.0),
            ("2025-06-02", "gold", "09:55", 4, 100.0)]
    extra = base + [("2025-06-02", "gold", "10:10", 5, 900.0)]
    a = select(cands(base), POL)
    b = select(cands(extra), POL)
    assert list(a.taken) == list(b.taken.iloc[:2]), "a later candidate altered the past"


def test_days_are_isolated():
    b = select(cands([
        ("2025-06-02", "pre", "08:10", 5, -400.0),
        ("2025-06-03", "pre", "08:10", 5, 100.0),
    ]), POL)
    assert b.taken.iloc[1], "day state leaked across days"


def test_every_untaken_row_has_a_reason():
    b = select(cands([
        ("2025-06-02", "pre", "08:10", 2, 100.0),
        ("2025-06-02", "pre", "08:20", 5, 100.0),
        ("2025-06-02", "pre", "08:30", 5, 100.0),
        ("2025-06-02", "pre", "08:40", 5, 100.0),
    ]), POL)
    assert (b[~b.taken].kill_reason != "").all(), "an untaken candidate has no audit trail"
    assert b.kill_reason.iloc[0] == "threshold"


def test_summarize_shape():
    b = select(cands([
        ("2025-06-02", "pre", "08:10", 5, 100.0),
        ("2025-06-02", "gold", "09:45", 2, 100.0),
    ]), POL)
    s = summarize(b)
    assert set(s.session) == {"pre", "gold", "TOTAL"}
    tot = s[s.session == "TOTAL"].iloc[0]
    assert tot.taken == 1 and tot.dollars == 100.0


def test_missing_columns_fail_loudly():
    with pytest.raises(ValueError, match="missing columns"):
        select(pd.DataFrame({"day": [], "session": []}), POL)
