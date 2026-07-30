"""The live NY lane — feature mapping, fail-closed refusals, and budget bookkeeping.

The scorer itself is proven against the shipped book in test_canon_scorer_ny.py. What this
file pins is the LANE: that an ingestor feature row is mapped onto the scorer's inputs
correctly (including the on_extreme_age trap that silently changes a score component), that a
missing feature refuses rather than fabricates, and that the fill/exit bookkeeping actually
moves the budget.
"""
from __future__ import annotations

import math

import pandas as pd
import pytest

from src.canon.ny_lane import NYLane, WINDOW_END, in_canon_window, scorer_row, session_day
from src.canon.scorer_ny import LUCID, SCALED600

NY = "America/New_York"


def _ts(hm: str, day: str = "2026-04-20"):
    return pd.Timestamp(f"{day} {hm}", tz=NY).tz_convert("UTC")


def _feats(**over) -> dict:
    """A gold-qualifying feature row as the ingestor would emit it (note: on_extreme_age_day
    and on_extreme_age_trade, NOT on_extreme_age)."""
    f = {"dep_thick": 5.0, "dep_wall_below_d": 8.0, "dep_wall_above_d": 6.0,
         "dep_wall_below_sz": 9.0, "dep_wall_above_sz": 9.0,
         "ent_vs_vwap_sd_dir": 0.5, "fill_delta_conf": 1, "d15_conf": 1,
         "trigdens_30": 20.0, "bp5opp": 0, "lon_slope_d": 0.0,
         "on_extreme_age_day": 500.0,        # gold's form: well past the 136.5 threshold
         "on_extreme_age_trade": 2.0}        # London's form: would fail the threshold
    f.update(over)
    return f


class FakeIngestor:
    """Returns a prepared feature row; records what the lane asked for."""
    def __init__(self, feats):
        self.feats = feats
        self.asked = []

    def feature_row(self, fill_ts, entry, direction, trigger_times=None):
        self.asked.append({"fill_ts": fill_ts, "entry": entry, "direction": direction,
                           "trigger_times": trigger_times})
        return dict(self.feats)


def _lane(feats=None, profile=LUCID, buffer=5_000.0, day="2026-04-20") -> NYLane:
    lane = NYLane(ingestor=FakeIngestor(feats if feats is not None else _feats()),
                  profile=profile)
    lane.start_day(day, buffer=buffer)
    return lane


def _cand(lane, hm="09:50", **kw):
    args = {"fill_ts": _ts(hm), "entry": 18_000.0, "stop": 17_990.0, "direction": "long",
            "trigger_times": [], "struct_event": ""}
    args.update(kw)
    return lane.on_candidate(**args)


# ---------------------------------------------------------------- the mapping
def test_gold_age_maps_the_DAY_form_not_the_trade_form():
    """scripts/score_canon_span.py:164 — gold's AGE input is on_extreme_age_DAY over the
    completed overnight tape; on_extreme_age_trade is London's per-trade wall-clock form.
    Mapping the wrong one silently changes a score component, so it is pinned here."""
    row = scorer_row(_feats(), fill_ts=_ts("09:50"), entry=18_000.0, stop=17_990.0,
                     direction="long")
    assert row["on_extreme_age"] == 500.0            # the DAY form
    # and when the day form is absent the component stands down rather than borrowing London's
    row2 = scorer_row(_feats(on_extreme_age_day=None) | {"on_extreme_age_trade": 2.0},
                      fill_ts=_ts("09:50"), entry=18_000.0, stop=17_990.0, direction="long")
    row2.pop("on_extreme_age")
    bare = {k: v for k, v in _feats().items() if k != "on_extreme_age_day"}
    row3 = scorer_row(bare, fill_ts=_ts("09:50"), entry=18_000.0, stop=17_990.0,
                      direction="long")
    assert math.isnan(row3["on_extreme_age"])


def test_row_carries_trade_geometry_and_clock():
    row = scorer_row(_feats(), fill_ts=_ts("09:50"), entry=18_000.0, stop=17_985.5,
                     direction="short")
    assert row["risk"] == pytest.approx(14.5)
    assert row["fill_hm"] == 590                     # 09:50 ET
    assert row["day"] == "2026-04-20" and row["direction"] == "short"


def test_session_day_uses_the_1800_boundary():
    assert session_day(_ts("09:50", "2026-04-20")) == "2026-04-20"
    # an 18:30 fill belongs to the NEXT session day, as the batch computes it
    assert session_day(_ts("18:30", "2026-04-20")) == "2026-04-21"


def test_in_canon_window_prefilter():
    assert in_canon_window(_ts("08:30")) and in_canon_window(_ts("10:29"))
    assert not in_canon_window(_ts("09:35")) and not in_canon_window(_ts("10:31"))


# ---------------------------------------------------------------- fail-closed
def test_missing_depth_refuses_instead_of_fabricating():
    """No depth book -> the ingestor omits the keys -> W and D read NaN -> the gate cannot be
    satisfied. An absent feature must never let a trade through."""
    bare = {k: v for k, v in _feats().items()
            if not k.startswith("dep_")}
    out = _cand(_lane(bare))
    assert out["take"] is False and out["micros"] == 0
    assert out["reasons"] == ["gold_no_wall_ahead"]


def test_out_of_window_candidate_is_refused():
    out = _cand(_lane(), hm="09:35")                 # between the two windows
    assert out["take"] is False and out["reasons"] == ["outside_window"]
    assert out["window_end"] is None


def test_wall_quality_cut_refuses_with_its_own_reason():
    out = _cand(_lane(_feats(dep_wall_below_d=2.0)))
    assert out["take"] is False and out["reasons"] == ["gold_wall_quality"]


# ---------------------------------------------------------------- verdict shape
def test_verdict_carries_what_the_relay_and_spine_need():
    out = _cand(_lane())
    for k in ("session", "day", "fill", "direction", "entry", "stop", "target",
              "conviction", "risk_pts", "micros"):
        assert k in out, f"the relay/spine consume {k}"
    assert out["session"] == "NY" and out["window"] == "gold"
    assert out["target"] is None, "the canon has no fixed target — the exit is managed"
    assert out["take"] and out["micros"] >= 1
    assert out["window_end"] == WINDOW_END["gold"].isoformat()


def test_elite_is_reported_and_capped_per_day():
    lane = _lane()
    a = _cand(lane, struct_event="broke")
    assert a["conviction"] == 2.0 and a["elite"] is True
    lane.confirm(a)
    b = _cand(lane, hm="09:51", struct_event="broke")
    assert b["conviction"] < 2.0 and "elite_used_today" in b["reasons"]


def test_absent_struct_event_never_escalates():
    out = _cand(_lane(), struct_event="")
    assert out["conviction"] < 2.0


# ---------------------------------------------------------------- bookkeeping
def test_confirm_consumes_budget_and_exit_frees_it():
    lane = _lane(profile=SCALED600, buffer=3_000.0)   # base 150 -> budget 800
    before = lane.status()["room"]
    v = _cand(lane, struct_event="broke")             # elite: $300 of risk
    lane.confirm(v)
    assert lane.status()["inflight_risk"] == pytest.approx(v["risk_dollars"])
    assert lane.status()["room"] == pytest.approx(before - v["risk_dollars"])
    lane.on_exit(v, pl=-v["risk_dollars"])
    st = lane.status()
    assert st["inflight_risk"] == 0.0
    assert st["realized"] == pytest.approx(-v["risk_dollars"])
    assert v["pl"] == pytest.approx(-v["risk_dollars"])


def test_budget_refuses_once_room_is_gone():
    lane = _lane()
    taken = []
    for i in range(30):
        v = _cand(lane, hm=f"09:{50 + i % 9}", struct_event="")
        if not v["take"]:
            assert "budget_exhausted" in v["reasons"]
            break
        lane.confirm(v)
        taken.append(v)
    else:
        pytest.fail("the budget never refused — capacity is unbounded")
    assert sum(v["risk_dollars"] for v in taken) <= lane.status()["budget"] + 1e-9


def test_confirm_and_exit_reject_unknown_verdicts():
    lane = _lane()
    refused = _cand(lane, hm="09:35")
    with pytest.raises(RuntimeError):
        lane.confirm(refused)
    with pytest.raises(RuntimeError):
        lane.on_exit(refused, pl=0.0)


def test_lane_passes_trigger_times_through_for_trigdens():
    """TRIG is a score component; the ingestor cannot own trigger detection, so the lane must
    forward the day's stamps or TRIG silently stands down."""
    lane = _lane()
    stamps = [_ts("09:41"), _ts("09:45")]
    _cand(lane, trigger_times=stamps)
    got = lane.ingestor.asked[-1]["trigger_times"]
    assert got is not None and len(got) == 2
    assert got.dtype.kind == "M" and got.dtype.name.startswith("datetime64"), \
        "badpa_features needs numpy datetime64"
    assert getattr(got.dtype, "tz", None) is None, "must be NAIVE utc, not tz-aware"


def test_trigger_times_are_normalised_to_naive_utc():
    """badpa_features compares the stamps against fill.to_datetime64() (naive UTC). Handing
    it tz-aware stamps raises, or silently miscounts — and trigdens_30 is a score component."""
    from src.canon.ny_lane import normalize_trigger_times
    arr = normalize_trigger_times([_ts("09:41"), _ts("09:45")])
    assert arr.dtype.kind == "M" and getattr(arr.dtype, "tz", None) is None
    # 09:41 ET on 2026-04-20 is 13:41Z — the offset must be applied, not dropped
    assert str(arr[0]).startswith("2026-04-20T13:41:00")


def test_empty_trigger_times_stand_TRIG_down_rather_than_scoring_zero():
    """An absent census must leave trigdens_30 missing (TRIG stands down), not assert a
    density of zero — which would be a fabricated feature value."""
    from src.canon.ny_lane import normalize_trigger_times
    assert normalize_trigger_times([]) is None
    assert normalize_trigger_times(None) is None


def test_sibling_triggers_in_the_same_minute_and_direction_are_tracked_separately():
    """Triggers off one cluster share a fill minute AND a direction routinely. Keying verdicts
    on (fill, direction) silently dropped the first of a colliding pair, so its risk never
    left the budget — a leak that grows all session."""
    lane = _lane()
    a = _cand(lane, hm="09:50")
    b = _cand(lane, hm="09:50")
    assert a["vid"] != b["vid"]
    lane.confirm(a)
    lane.confirm(b)
    assert lane.status()["open_positions"] == 2
    lane.on_exit(a, pl=-10.0)
    lane.on_exit(b, pl=-20.0)                      # must not raise
    st = lane.status()
    assert st["open_positions"] == 0 and st["inflight_risk"] == 0.0
    assert st["realized"] == pytest.approx(-30.0)


def test_explicit_risk_pts_overrides_the_bracket_distance():
    """`entry`/`stop` are trigger references and disagree with the canon's realized risk on
    28% of validated trades. Risk drives BOTH the 7-60pt gate and micros."""
    lane = _lane()
    inferred = _cand(lane, entry=18_000.0, stop=17_990.0)          # 10pt
    explicit = _cand(lane, entry=18_000.0, stop=17_990.0, risk_pts=17.75)
    assert inferred["risk_pts"] == pytest.approx(10.0)
    assert inferred["risk_source"] == "bracket"
    assert explicit["risk_pts"] == pytest.approx(17.75)
    assert explicit["risk_source"] == "explicit"
    assert explicit["micros"] < inferred["micros"], "a wider stop must buy fewer contracts"


def test_explicit_risk_can_refuse_a_trade_the_bracket_would_admit():
    """The 7-60pt gate reads the same risk the sizing does, so a reference-level stop that
    looks in-band while the real bracket is out of band must not slip through."""
    lane = _lane()
    assert _cand(lane, entry=18_000.0, stop=17_990.0)["take"] is True
    out = _cand(lane, entry=18_000.0, stop=17_990.0, risk_pts=61.0)
    assert out["take"] is False and out["reasons"] == ["hard_gate_risk"]
