"""The escalation gate must REFUSE, not merely advise. One test per safeguard.

Each test states the failure it prevents, because the whole point of this module
is that the equivalent instruction already exists in the tv-trigger prompt and
prompt text is not enforcement.
"""
import pytest

from scripts.escalation_gate import EscalationGate, normalise_level


def stale(level="daily_poc", price=29369.0, constraints=None):
    return {
        "decision": "pass",
        "thesis_stale": True,
        "rejected_level": {"level": level, "price": price},
        "constraints_failed": constraints or ["waiting_for_unmet"],
    }


def gate(**kw):
    g = EscalationGate(**kw)
    g.open_window("NY_AM")
    return g


# -- 1. per-window budget --------------------------------------------------

def test_budget_grants_two_then_refuses():
    """Without a budget, a thesis the tape outran escalates on every candidate."""
    g = gate()
    assert g.request("c1", stale("daily_poc", 29369)).granted
    assert g.request("c2", stale("prior_day_vah", 29884)).granted
    third = g.request("c3", stale("weekly_val", 29290))
    assert not third.granted
    assert third.reason.startswith("escalation_budget_exhausted")
    assert third.downgraded_to == "pass"


def test_budget_resets_per_window():
    g = gate()
    g.request("c1", stale("daily_poc", 29369))
    g.request("c2", stale("prior_day_vah", 29884))
    assert not g.request("c3", stale("weekly_val", 29290)).granted
    g.open_window("NY_PRE")
    assert g.request("c4", stale("weekly_val", 29290)).granted


def test_budget_is_configurable():
    g = gate(budget=1)
    assert g.request("c1", stale()).granted
    assert not g.request("c2", stale("vwap_p1", 30649)).granted


# -- 2. same-level ratchet -------------------------------------------------

def test_ratchet_blocks_same_level_by_name():
    """Prevents one disagreement being re-litigated across every candidate."""
    g = gate()
    assert g.request("c1", stale("daily_poc", 29369)).granted
    second = g.request("c2", stale("daily_poc", 29369))
    assert not second.granted and second.reason == "same_level_ratchet"


def test_ratchet_blocks_same_level_by_price_within_tolerance():
    """A renamed level at the same price is the same level."""
    g = gate(price_tol=5.0)
    g.request("c1", stale("daily_poc", 29369.0))
    r = g.request("c2", stale("session_poc_developing", 29371.5))
    assert not r.granted and r.reason == "same_level_ratchet"


def test_ratchet_allows_a_genuinely_different_level():
    g = gate()
    g.request("c1", stale("daily_poc", 29369.0))
    assert g.request("c2", stale("prior_day_vah", 29884.0)).granted


def test_ratchet_is_order_free_on_compound_level_names():
    """'a + b' and 'b + a' name one level, not two."""
    g = gate()
    g.request("c1", stale("bb_ma_15m + daily_poc", 29370.0))
    r = g.request("c2", stale("daily_poc + bb_ma_15m", 29999.0))
    assert not r.granted and r.reason == "same_level_ratchet"


def test_normalise_level_is_order_and_punctuation_free():
    assert normalise_level("bb_ma_15m + daily_poc") == normalise_level("daily POC / bb-ma-15m")


# -- 3. mechanical gates never re-fire -------------------------------------

@pytest.mark.parametrize("g_name", [
    "window_cap", "window_closed", "news_blackout",
    "cash_open_buffer", "position_already_open",
])
def test_mechanical_gate_argument_always_refuses(g_name):
    """Tier 1 cannot un-exhaust a cap or un-print a news release."""
    g = gate()
    r = g.request("c1", stale(), mechanical_gate=g_name)
    assert not r.granted
    assert r.reason == f"mechanical_gate:{g_name}"


def test_mechanical_gate_detected_in_the_verdicts_own_constraints():
    """Even if the orchestrator does not flag it, the verdict betrays itself."""
    g = gate()
    r = g.request("c1", stale(constraints=["window_cap"]))
    assert not r.granted and r.reason == "mechanical_gate:window_cap"


def test_mechanical_gate_does_not_consume_budget():
    """A refused mechanical escalation must not spend a thesis escalation."""
    g = gate()
    g.request("c1", stale(), mechanical_gate="window_cap")
    g.request("c2", stale(), mechanical_gate="news_blackout")
    assert g.request("c3", stale("daily_poc", 29369)).granted
    assert g.request("c4", stale("vwap_p1", 30649)).granted
    assert not g.request("c5", stale("weekly_low", 29160)).granted


def test_unrecognised_gate_name_is_treated_as_mechanical():
    """Fail closed: an unknown gate refuses rather than silently re-firing."""
    g = gate()
    r = g.request("c1", stale(), mechanical_gate="some_new_gate")
    assert not r.granted and r.reason.startswith("mechanical_gate:some_new_gate")


# -- 4 & 5. contract conditions --------------------------------------------

def test_once_per_candidate():
    g = gate()
    g.request("c1", stale("daily_poc", 29369))
    r = g.request("c1", stale("prior_day_vah", 29884))
    assert not r.granted and r.reason == "already_escalated_this_candidate"


def test_escalation_without_a_named_rejection_is_refused():
    """The contract licenses escalation only when a rejection can be NAMED."""
    g = gate()
    v = {"thesis_stale": True, "rejected_level": None, "constraints_failed": ["waiting_for_unmet"]}
    r = g.request("c1", v)
    assert not r.granted and r.reason == "no_rejection_named"


def test_a_refused_level_does_not_enter_the_ratchet():
    """A level refused on budget was never escalated, so it stays escalatable."""
    g = gate(budget=1)
    assert g.request("c1", stale("prior_day_vah", 29884)).granted   # spends the budget
    refused = g.request("c2", stale("daily_poc", 29369))
    assert not refused.granted and refused.reason.startswith("escalation_budget_exhausted")
    g.open_window("NY_AM_2")
    assert g.request("c3", stale("daily_poc", 29369)).granted


# -- reporting -------------------------------------------------------------

def test_report_counts_and_reaffirm_rate():
    g = gate()
    g.request("c1", stale("daily_poc", 29369))
    g.request("c2", stale("prior_day_vah", 29884))
    g.request("c3", stale("weekly_val", 29290))          # budget refusal
    g.record_outcome("c1", "accommodated")
    g.record_outcome("c2", "reaffirmed")
    rep = g.report()
    assert rep["requested"] == 3
    assert rep["granted"] == 2
    assert rep["refused"] == 1
    assert rep["accommodated"] == 1 and rep["reaffirmed"] == 1
    assert rep["reaffirm_rate"] == 0.5
    assert rep["refused_by_reason"]["escalation_budget_exhausted"] == 1


def test_record_outcome_rejects_unknown_values_and_unknown_candidates():
    g = gate()
    g.request("c1", stale())
    with pytest.raises(ValueError):
        g.record_outcome("c1", "maybe")
    with pytest.raises(KeyError):
        g.record_outcome("nope", "accommodated")


# -- the inverse: escalations the trigger should have raised ----------------

def test_detects_a_pass_that_named_a_rejection_on_a_thesis_gate():
    """The expensive failure is the MISSING escalation, not the excess one."""
    v = {"decision": "pass", "thesis_stale": False,
         "constraints_failed": ["direction_mismatch"],
         "rejected_level": {"level": "session_high + vwap_p2", "price": 30869.75}}
    should, why = EscalationGate.should_have_escalated(v)
    assert should and "direction_mismatch" in why


@pytest.mark.parametrize("gate_name", ["waiting_for_unmet", "waiting_for_not_satisfied", "waiting_for"])
def test_detects_every_spelling_of_the_waiting_for_gate(gate_name):
    v = {"decision": "pass", "thesis_stale": False,
         "constraints_failed": [gate_name],
         "rejected_level": {"level": "daily_poc", "price": 29369.0}}
    assert EscalationGate.should_have_escalated(v)[0]


def test_no_rejection_named_means_the_pass_was_correct():
    v = {"decision": "pass", "thesis_stale": False,
         "constraints_failed": ["waiting_for_unmet"], "rejected_level": None}
    should, why = EscalationGate.should_have_escalated(v)
    assert not should and "no rejection named" in why


def test_a_mechanical_gate_alongside_a_thesis_gate_excuses_the_pass():
    """Tier 1 cannot fix a spent cap, so withholding the escalation is right."""
    v = {"decision": "pass", "thesis_stale": False,
         "constraints_failed": ["waiting_for_unmet", "window_cap"],
         "rejected_level": {"level": "daily_poc", "price": 29369.0}}
    assert not EscalationGate.should_have_escalated(v)[0]


def test_a_take_is_never_a_missed_escalation():
    v = {"decision": "take_full", "thesis_stale": False, "constraints_failed": [],
         "rejected_level": {"level": "daily_poc", "price": 29369.0}}
    assert not EscalationGate.should_have_escalated(v)[0]


def test_an_actual_escalation_is_not_also_a_missed_one():
    v = {"decision": "pass", "thesis_stale": True,
         "constraints_failed": ["waiting_for_unmet"],
         "rejected_level": {"level": "daily_poc", "price": 29369.0}}
    assert not EscalationGate.should_have_escalated(v)[0]


def test_a_non_thesis_pass_reason_is_not_a_missed_escalation():
    v = {"decision": "pass", "thesis_stale": False,
         "constraints_failed": ["headroom", "chop"],
         "rejected_level": {"level": "daily_poc", "price": 29369.0}}
    assert not EscalationGate.should_have_escalated(v)[0]


# -- T25 qualification: only a candidate it would OTHERWISE TAKE may escalate

def test_T25_sequential_pair_cannot_escalate():
    """Sequential pairs default toward pass under T1, so escalating one asks
    Tier 1 to re-read on evidence the trigger would not have traded anyway."""
    g = gate()
    v = dict(stale("session_high", 30869.75), pair_shape="sequential")
    r = g.request("c1", v)
    assert not r.granted and r.reason.startswith("T25_not_same_candle")


def test_T25_sequential_refusal_does_not_spend_budget():
    g = gate()
    # prices kept far apart so the ratchet does not fire and mask the budget
    g.request("c1", dict(stale("alpha", 29000.0), pair_shape="sequential"))
    g.request("c2", dict(stale("beta", 29500.0), pair_shape="sequential"))
    assert g.request("c3", dict(stale("gamma", 30000.0), pair_shape="same_candle")).granted
    assert g.request("c4", dict(stale("delta", 30500.0), pair_shape="same_candle")).granted
    fifth = g.request("c5", dict(stale("epsilon", 31000.0), pair_shape="same_candle"))
    assert not fifth.granted and fifth.reason.startswith("escalation_budget_exhausted")


def test_T25_same_candle_still_qualifies():
    g = gate()
    assert g.request("c1", dict(stale(), pair_shape="same_candle")).granted


def test_T25_mixed_shape_string_counts_as_same_candle():
    """'same_candle (3m) / sequential (2m)' has a same-candle leg — it qualifies."""
    g = gate()
    v = dict(stale(), pair_shape="same_candle (3m) / sequential (2m)")
    assert g.request("c1", v).granted


def test_T25_applies_to_the_missed_escalation_detector_too():
    seq = {"decision": "pass", "thesis_stale": False, "pair_shape": "sequential",
           "constraints_failed": ["direction_mismatch"],
           "rejected_level": {"level": "session_high", "price": 30869.75}}
    should, why = EscalationGate.should_have_escalated(seq)
    assert not should and "T25" in why

    same = dict(seq, pair_shape="same_candle")
    assert EscalationGate.should_have_escalated(same)[0]
