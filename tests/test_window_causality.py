"""The §2.5 window-causality bar, and the three defects it exists because of.

Two jobs. First, pin the primitive: `close_time(W) <= T` for every condition of every
rule at every minute it can fire, with `<=` non-strict (a bar that closes AT the decision
minute is settled). Second — and this is the part that stops the check rotting into
decoration — replay the three historical defects and require the check to CATCH them,
and replay LDN-DEF-01 and require it to PASS. A causality check that fires on nothing is
indistinguishable from no check.

The registry below is the programme's causality record. When a new family is prereg'd its
window table lands here too, so the declaration and the audit are the same object.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.validation.window_causality import (
    CausalityViolation, Condition, Rel, Rule, Window, assert_causal, resolve,
    to_minutes, violations, worst_lag)

ROOT = Path(__file__).resolve().parents[1]
PROCESS = ROOT / "docs/VALIDATION-PROCESS.md"


# ------------------------------------------------------------------ primitive
def test_clock_and_relative_edges_resolve():
    assert to_minutes("07:45") == 465
    assert to_minutes(465) == 465
    assert resolve("08:00", "07:30") == 480          # absolute ignores T
    assert resolve(Rel(0), "07:30") == 450           # settles at the decision minute
    assert resolve(Rel(-3), "07:30") == 447
    assert resolve(Rel(15), "07:30") == 465          # 15 minutes of lookahead


def test_a_window_closing_exactly_at_T_is_legal():
    """The inequality is `<=`, not `<`.

    Every census in this repo takes the decision minute's own closed bar. Making this
    strict would condemn the entire fit-span corpus, including the clean one.
    """
    r = Rule.from_table("closes at T", [("c", Rel(-3), Rel(0))], ["08:00", "09:59"])
    assert violations(r) == []
    assert worst_lag(r) == 0
    assert_causal(r)                                  # does not raise


def test_one_minute_of_lookahead_is_caught():
    r = Rule.from_table("one minute late", [("c", "07:00", Rel(1))], ["08:00"])
    assert worst_lag(r) == 1
    with pytest.raises(CausalityViolation):
        assert_causal(r)


def test_a_causal_condition_and_a_leaky_one_in_the_same_rule_are_separated():
    """The check must discriminate WITHIN a rule, not just condemn it wholesale.

    This is LDN-INV-01's shape in miniature: the observable is honest, the cut applied
    to it is not, and the report has to name which is which for the finding to be
    salvageable as descriptive.
    """
    r = Rule.from_table(
        "mixed",
        [("honest", "06:00", "07:00"), ("leaky", "07:00", "09:00")],
        ["08:00"],
    )
    v = violations(r)
    assert [x.condition for x in v] == ["leaky"]
    with pytest.raises(CausalityViolation, match="leaky"):
        assert_causal(r)


def test_violations_are_reported_worst_first_and_name_the_fix_surface():
    r = Rule.from_table("multi", [("a", "07:00", "09:00"), ("b", "07:00", "08:00")],
                        ["07:30"])
    v = violations(r)
    assert [x.lag_minutes for x in v] == [90, 30]     # worst first
    with pytest.raises(CausalityViolation) as e:
        assert_causal(r)
    msg = str(e.value)
    assert "2 window-causality violation(s)" in msg
    assert "07:30" in msg and "09:00" in msg
    # the message has to say what to DO, or it just relocates the argument
    assert "Restrict the decision times, or close the windows earlier" in msg


def test_the_full_admissible_set_of_decision_times_is_what_gets_audited():
    """Auditing only the typical decision time is exactly how LDN-ATC-01 passed."""
    table = [("LTA", "07:00", "08:00")]
    assert violations(Rule.from_table("typical only", table, ["08:00"])) == []
    assert worst_lag(Rule.from_table("full set", table, ["07:30", "08:00"])) == 30


def test_every_decision_time_is_audited_not_just_the_first():
    """The declared set is order-free, so a leak at a LATER entry must still be caught.

    Without this the checker could quietly audit `decision_times[0]` and every other
    test here would still pass — the registry happens to list its leaky minutes first.
    """
    r = Rule.from_table("clean first, leaky second", [("c", "08:00", "10:00")],
                        ["10:00", "09:00"])
    v = violations(r)
    assert [(x.decision_time, x.lag_minutes) for x in v] == [(540, 60)]


def test_a_rule_must_declare_conditions_and_decision_times():
    with pytest.raises(ValueError, match="no conditions"):
        Rule.from_table("empty", [], ["08:00"])
    with pytest.raises(ValueError, match="every minute at which the rule can fire"):
        Rule.from_table("no times", [("c", "07:00", "08:00")], [])


def test_a_bool_edge_is_rejected_rather_than_silently_read_as_a_minute():
    with pytest.raises(TypeError):
        to_minutes(True)


# --------------------------------------------------- the programme's registry
# Each entry is the family's declared window table. `expect` is what the bar must say.

def _def01() -> Rule:
    """LDN-DEF-01 — THE WORKED EXAMPLE (docs/VERDICT-LDN-DEF-01.md §4).

    Footprint minutes read in [t-3, t]; outcome over (t, window close]; the level itself
    is fixed by the prior structure. Asserted in code at the time, on every event.
    """
    return Rule.from_table(
        "LDN-DEF-01 absorption read",
        [("ABSORB / PIN / ICEBERG footprint", Rel(-3), Rel(0),
          "assert max(mins) <= t, fired on every event"),
         ("defended level", "00:00", Rel(0), "prior structure, fixed before the event"),
         ("absorbed side", Rel(0), Rel(0), "fixed BY the event, not chosen")],
        decision_times=["08:00", "08:30", "09:00", "09:30", "10:00"],
    )


def _swp01() -> Rule:
    """LDN-SWP-01 — group-P membership stays open across the outcome window.

    ET minutes. Outcome window 03:00->06:00; the position is taken at 03:00. Group P is
    "Asia extreme breached only AFTER the 03:00 open" — determinable only once the
    window has run. Observed breach lag: median 47 min, 44 of 115 beyond 60 min.
    Group D (breach 00:00-03:00) is clean and is why #3's FAIL is a clean refutation.
    """
    return Rule.from_table(
        "LDN-SWP-01 sweep-timing grouping",
        [("group D — dead-hour breach", "00:00", "03:00", "clean"),
         ("group P — post-open breach", "03:00", "06:00", "THE DEFECT"),
         ("sign of the outcome (which side broke)", "03:00", "06:00", "definitional")],
        decision_times=["03:00"],
    )


def _atc01() -> Rule:
    """LDN-ATC-01 — the LTA window outlives the first trigger minute.

    London minutes. LTA is >=2 consecutive 15m closes inside 07:00-08:00; the trigger
    scan runs 07:00-09:00 and takes the FIRST occurrence, so it can fire at 07:30 on
    the strength of the 07:45 and 08:00 bars. 29 of 108 triggers (27%) are in this class.
    """
    return Rule.from_table(
        "LDN-ATC-01 chain",
        [("bias (03:30-05:15 vs 05:15-07:00)", "03:30", "07:00", "clean"),
         ("reference px (07:00 close)", "07:00", "07:00", "clean"),
         ("pullback beyond ref", "07:00", "08:00", "leaks at 07:30"),
         ("LTA >=2 consecutive 15m closes", "07:00", "08:00", "THE DEFECT"),
         ("trigger 15m+30m aligned close", Rel(-30), Rel(0), "clean at every T")],
        decision_times=["07:30", "08:00", "08:30", "09:00"],
    )


def _inv01() -> Rule:
    """LDN-INV-01 — the quintile boundary is era-local, so the cut sees the future.

    DAY-INDEX units (see window_causality._clock: the check is unit-agnostic). Era 2025
    is days 0..250. `prior_rth_ret` itself is a settled observable; the bottom-quintile
    BOUNDARY applied to it is computed over the whole era, so the cut applied on day 0
    is defined by a distribution that includes day 250.
    """
    return Rule.from_table(
        "LDN-INV-01 bottom-quintile conditioning",
        [("prior_rth_ret (the observable)", -1, -1, "settled the prior RTH close"),
         ("bottom-quintile boundary (era-local)", 0, 250, "THE DEFECT")],
        decision_times=list(range(251)),
    )


REGISTRY = {
    "LDN-DEF-01": (_def01, 0),      # the worked example: causal, worst lag 0
    "LDN-SWP-01": (_swp01, 180),    # group P closes 06:00 ET against a 03:00 decision
    "LDN-ATC-01": (_atc01, 30),     # LTA closes 08:00 against a 07:30 trigger
    "LDN-INV-01": (_inv01, 250),    # era boundary against the first day of the era
}


@pytest.mark.parametrize("fam", sorted(REGISTRY))
def test_registry_matches_the_recorded_verdict(fam):
    build, expected = REGISTRY[fam]
    assert worst_lag(build()) == expected, f"{fam}: window table no longer matches record"


def test_the_worked_example_passes_and_the_three_defects_do_not():
    """A check that fires on nothing is indistinguishable from no check."""
    assert_causal(_def01())                                    # must NOT raise
    for fam in ("LDN-SWP-01", "LDN-ATC-01", "LDN-INV-01"):
        with pytest.raises(CausalityViolation):
            assert_causal(REGISTRY[fam][0]())


def test_atc01_is_clean_from_0800_which_is_why_the_secondary_arm_still_counts():
    """The 08:00+ cohort is causally clean — that is what makes -0.135R at n=65 usable.

    The family closes on a measurement that survives this check, not merely on the
    defective one. Restricting the decision times is the fix the bar points at.
    """
    leaky = _atc01()
    fixed = Rule(leaky.name + " (08:00+)", leaky.conditions,
                 tuple(t for t in leaky.decision_times if to_minutes(t) >= 480))
    assert violations(fixed) == []
    assert_causal(fixed)


def test_swp01_group_D_alone_is_clean_which_is_why_its_FAIL_is_safe():
    """#3 continuation is refuted on group D, and group D never leaked.

    The defect INFLATES the contaminated group's apparent effect; it cannot manufacture
    the near-zero means the FAIL rests on. Direction of the bias is why the verdict
    survives the defect that invalidated the primary statistic.
    """
    swp = _swp01()
    d_only = Rule("LDN-SWP-01 group D", (swp.conditions[0],), swp.decision_times)
    assert violations(d_only) == []


# ------------------------------------------------- the process doc must carry it
def test_validation_process_carries_the_bar_and_the_prereg_fields():
    """The check and the doc are one amendment; neither is any use without the other."""
    t = PROCESS.read_text()
    assert "Window causality — the check is on the (condition, decision-time) pair" in t
    assert "assert max(close_time(Wᵢ)) ≤ T for all i" in t
    assert "Control admissibility" in t
    assert "DISJOINT-GROUP TESTS ONLY" in t
    assert "Condition windows:" in t and "Controls:" in t
    # The data-layer bar, and the reason it is separate: this check is blind to a source
    # whose timestamps lie, and it was blind to exactly that for a year.
    assert "validated against a second, independent clock at load" in t
    assert "Clock provenance:" in t
    assert "cannot catch a source whose timestamps lie" in t
    # the §1 template row must ask for the CLOSE, which is the only edge that binds
    assert re.search(r"\|\s*window CLOSES\s*\|", t)
    assert "LDN-DEF-01" in t, "the worked example is cited in the bar"
