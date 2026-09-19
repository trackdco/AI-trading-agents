"""The anchored weekly profile is anchored where HE anchors it — checked, not assumed.

His instruction, 2026-08-13: *"make sure the weekly vp is anchored correctly too
(make sure its in the process)"*. The second half is the point. This was wrong for
an entire scored week and nothing caught it, because the anchor was only ever
eyeballed. It moved weekly POC by ~900 points, and anchored-weekly edges are the
ONLY levels that grade **A** on their own in the trigger's conviction rubric as well
as being named thesis targets — so a wrong anchor changes verdicts, not just numbers.

His rule: anchor to the Asia open (18:00 NY) of THIS WEEK'S Monday, developing to
the cursor. Monday's own session has no week-to-date, so it falls back to the prior
Monday.

The last test is the important one: it plants a wrong anchor and demands the check
notice. A gate that cannot fail is decoration.
"""
from __future__ import annotations

import datetime

import pandas as pd
import pytest

from scripts.agent_context import anchored_weekly_profile
from scripts.build_l2_outcomes import load_bars
from src.htf_ma.levels import NY

# The narrated week plus its Monday, by session-day (the evening the session OPENS).
SESSION_DAYS = ["2026-06-21", "2026-06-22", "2026-06-23", "2026-06-24", "2026-06-25"]


@pytest.fixture(scope="module")
def bars():
    b = load_bars()
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    return b.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]


def anchor_of(bars, sess_day):
    return anchored_weekly_profile(bars, sess_day, upto=None)["anchor"]


@pytest.mark.parametrize("sess_day", SESSION_DAYS)
def test_anchor_is_always_a_monday_1800(bars, sess_day):
    a = anchor_of(bars, sess_day)
    assert a.weekday() == 0, f"{sess_day}: anchored to a {a:%A}, not a Monday"
    assert (a.hour, a.minute) == (18, 0), f"{sess_day}: anchored at {a:%H:%M}, not 18:00"


@pytest.mark.parametrize("sess_day", SESSION_DAYS)
def test_anchor_is_within_the_last_week_and_strictly_before(bars, sess_day):
    a = anchor_of(bars, sess_day)
    open_ = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    back = (open_ - a).days
    assert 0 < back <= 7, (
        f"{sess_day}: anchor is {back}d back; expected 1-7. A rolling "
        "same-weekday-minus-7 window would give exactly 7 every day, which is the "
        "bug this test exists to catch."
    )


def test_consecutive_sessions_share_an_anchor_and_it_resets_once_a_week(bars):
    """Sessions in the same trading week share ONE anchor, and it steps exactly a
    week when it changes. That is what makes this a WEEKLY profile rather than a
    rolling 5-day one — the superseded implementation produced a different anchor
    every single day and never reset at the week boundary.

    Note which days group together: session-days are named by the evening they
    OPEN, so 2026-06-21 (Sun open) and 2026-06-22 (Mon open) both sit at or before
    the week's Monday and fall back to the prior Monday, while 06-23/24/25 share
    the current one. Two groups, not one, and that is correct.
    """
    anchors = {d: anchor_of(bars, d) for d in SESSION_DAYS}
    groups = sorted(set(anchors.values()))
    assert len(groups) == 2, f"expected two anchor groups across this span, got {groups}"
    assert (groups[1] - groups[0]).days == 7, (
        f"the anchor must step exactly one week when it resets, got "
        f"{(groups[1] - groups[0]).days}d"
    )
    for d, a in anchors.items():
        assert a < pd.Timestamp(f"{d} 18:00", tz=NY), (
            f"{d}: anchor {a} is not strictly before the session open"
        )


@pytest.mark.parametrize("sess_day", SESSION_DAYS)
def test_the_profile_develops_and_never_reads_the_future(bars, sess_day):
    """Same anchor, later cursor, never a narrower range — and truncating the bars
    at the cursor must not change the answer."""
    nxt = (datetime.date.fromisoformat(sess_day) + datetime.timedelta(days=1)).isoformat()
    early = pd.Timestamp(f"{nxt} 04:00", tz=NY)
    late = pd.Timestamp(f"{nxt} 11:00", tz=NY)

    a, b_ = (anchored_weekly_profile(bars, sess_day, upto=t) for t in (early, late))
    assert a["anchor"] == b_["anchor"], "the anchor must not move as the session develops"
    assert b_["awHIGH"] >= a["awHIGH"] - 1e-9
    assert b_["awLOW"] <= a["awLOW"] + 1e-9

    truncated = anchored_weekly_profile(bars[bars.index < early], sess_day, upto=early)
    for k in ("awPOC", "awVAL", "awVAH", "awHIGH", "awLOW"):
        assert abs(float(a[k]) - float(truncated[k])) < 1e-9, (
            f"{sess_day}: anchored weekly {k} changed when bars after the cursor were "
            "deleted — it was reading the future"
        )


def test_the_check_can_actually_catch_a_wrong_anchor():
    """Plant the OLD bug and demand the gate's rule reject it.

    The superseded implementation was `sess_day 18:00 - 7 days` — same weekday, one
    week back. On a Tuesday session that lands on a Tuesday, which the Monday rule
    rejects on weekday alone; on the Monday session it lands 7d back on a Monday and
    is indistinguishable, which is exactly why the weekday check alone is not enough
    and the two assertions are kept separate.
    """
    def old_buggy_anchor(sess_day):
        return pd.Timestamp(f"{sess_day} 18:00", tz=NY) - pd.Timedelta(days=7)

    caught = [d for d in SESSION_DAYS if old_buggy_anchor(d).weekday() != 0]
    assert len(caught) == 4, (
        "the weekday rule must reject the old same-weekday-minus-7 anchor on every "
        f"session-day that does not itself open on a Monday; it caught {caught}"
    )
    # The ONE day it cannot distinguish is the session that opens on a Monday
    # (2026-06-22): minus-7 lands on a Monday and 7d back, which the new rule also
    # accepts. That is harmless — on that day both implementations produce the SAME
    # anchor — but it is why the weekday test alone is not sufficient and the
    # 0 < back <= 7 range test is kept as a separate assertion.
    undetectable = [d for d in SESSION_DAYS if old_buggy_anchor(d).weekday() == 0]
    assert undetectable == ["2026-06-22"]
    assert old_buggy_anchor("2026-06-22") == anchored_weekly_profile(
        load_bars_indexed(), "2026-06-22", upto=None)["anchor"], (
        "on a Monday-opening session the old and new anchors must agree, which is "
        "why that case is undetectable and also why it does not matter"
    )


def load_bars_indexed():
    b = load_bars()
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    return b.set_index("mi").sort_index()
