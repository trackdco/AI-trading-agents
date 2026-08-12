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
