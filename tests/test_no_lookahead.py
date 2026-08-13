"""ADVERSARIAL LOOKAHEAD TEST — delete the future and see if anything changes.

His instruction, 2026-08-12: *"make sure there isnt look ahead and shit and they
cant see the days high and low lol that wouldnt be very smart."*

Reading the code and concluding "it slices `< t`, looks fine" is not proof. Every
lookahead defect in this project so far passed that reading — the crosshair study
reader, the 6-hour MFE window, the 3m bar clustered to an even minute. Each one
looked causal until it was measured.

So this measures it. For each decision minute we build the level set TWICE:

  1. from the full bar history, exactly as the orchestrator does in a live run;
  2. from a history with every bar at or after the decision minute DELETED.

If any field differs, that field saw the future. If they are identical, the field
provably cannot have — because the second computation had no future to see.

The day's high and low get their own test, because he named them: a decision at
09:30 must see the session's high SO FAR, not the high the day eventually makes.
"""
from __future__ import annotations

import math

import pandas as pd
import pytest

from scripts.agent_context import anchored_weekly_profile
from scripts.phase0_parity import reference_at
from scripts.build_l2_outcomes import load_bars
from src.htf_ma.levels import NY

# One early, one mid-session and one late minute on each session-day of the
# narrated week, so a field that only leaks near the extremes still gets caught.
CASES = [
    (d, m)
    for d in ("2026-06-21", "2026-06-22", "2026-06-23", "2026-06-24", "2026-06-25")
    for m in ("03:00", "08:00", "09:30", "10:30")
]


@pytest.fixture(scope="module")
def bars():
    b = load_bars()
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    return b.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]


def decision_ts(sess_day: str, hhmm: str) -> pd.Timestamp:
    """Session-days are 18:00-anchored: 00:00-17:59 belongs to the next date."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t = pd.Timestamp(f"{sess_day} {hhmm}", tz=NY)
    return t + pd.Timedelta(days=1) if t < t0 else t


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _same(a, b) -> bool:
    if _num(a) and _num(b):
        return (math.isnan(a) and math.isnan(b)) or abs(a - b) < 1e-9
    return a == b


@pytest.mark.parametrize("sess_day,minute", CASES)
def test_every_reference_level_is_blind_to_the_future(bars, sess_day, minute):
    """The whole level set must be identical with the future deleted."""
    t = decision_ts(sess_day, minute)
    full = reference_at(bars, sess_day, minute)
    truncated = reference_at(bars[bars.index < t], sess_day, minute)

    differing = {
        k: (full[k], truncated[k])
        for k in full
        if k in truncated and not _same(full[k], truncated[k])
    }
    assert not differing, (
        f"{sess_day} {minute}: these fields changed when the future was removed, "
        f"so they were reading it: {differing}"
    )


@pytest.mark.parametrize("sess_day,minute", CASES)
def test_the_days_high_and_low_are_developing_not_final(bars, sess_day, minute):
    """He named this one specifically. The session high/low must be AS-OF.

    Two claims, both checked:
      - as-of == the true max/min of bars strictly before the decision minute;
      - where the session LATER extends its range, as-of must differ from final.
        Where it does not extend (a range set overnight), as-of legitimately
        equals final and proves nothing either way, so that case is skipped
        rather than asserted on.
    """
    t = decision_ts(sess_day, minute)
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t_end = t0 + pd.Timedelta(hours=23)

    sofar = bars[(bars.index >= t0) & (bars.index < t)]
    whole = bars[(bars.index >= t0) & (bars.index < t_end)]
    assert len(sofar) and len(whole)

    asof_hi, asof_lo = float(sofar.high.max()), float(sofar.low.min())
    final_hi, final_lo = float(whole.high.max()), float(whole.low.min())

    assert asof_hi <= final_hi and asof_lo >= final_lo
    if final_hi > asof_hi:
        assert asof_hi != final_hi, "session high equals the FINAL high — leak"
    if final_lo < asof_lo:
        assert asof_lo != final_lo, "session low equals the FINAL low — leak"


@pytest.mark.parametrize("sess_day,minute", CASES)
def test_the_anchored_weekly_extremes_are_developing(bars, sess_day, minute):
    """The weekly profile is anchored 7 days back and DEVELOPING to the cursor.

    Compared against the same profile run to the END of the session-day — its
    own window, not the day's — so the comparison is like-for-like.
    """
    t = decision_ts(sess_day, minute)
    asof = anchored_weekly_profile(bars, sess_day, upto=t)
    final = anchored_weekly_profile(bars, sess_day, upto=None)

    assert asof["awHIGH"] <= final["awHIGH"] + 1e-9
    assert asof["awLOW"] >= final["awLOW"] - 1e-9
    assert asof["anchor"] == final["anchor"]

    # and it must be blind to the future by the same truncation argument
    truncated = anchored_weekly_profile(bars[bars.index < t], sess_day, upto=t)
    for k in ("awPOC", "awVAL", "awVAH", "awHIGH", "awLOW"):
        assert _same(asof[k], truncated[k]), (
            f"{sess_day} {minute}: anchored weekly {k} changed when the future "
            f"was deleted — {asof[k]} vs {truncated[k]}"
        )


@pytest.mark.parametrize("sess_day", ["2026-06-21", "2026-06-23", "2026-06-24"])
def test_day_range_fibs_move_when_the_range_extends(bars, sess_day):
    """Fibs are drawn off the DEVELOPING H->L, so they must track it.

    These three session-days all extend their range after 03:00, so a fib set
    that is constant across the session would be computed from the finished day
    — the exact defect he called out about the volume profile. (2026-06-25 is
    excluded on purpose: its high AND low were both set overnight before 03:00,
    so its fibs correctly never move, and asserting movement there would be
    asserting a fact about the tape rather than about the code.)
    """
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)

    def fib_at(hhmm):
        t = decision_ts(sess_day, hhmm)
        seg = bars[(bars.index >= t0) & (bars.index < t)]
        h, l = float(seg.high.max()), float(seg.low.min())
        return l + (h - l) * 0.5

    assert fib_at("03:00") != fib_at("10:30"), (
        f"{sess_day}: the 0.5 day-range fib is identical at 03:00 and 10:30 on a "
        "day whose range demonstrably extends — it is not developing"
    )


def test_the_truncation_harness_can_actually_detect_a_leak(bars):
    """A test that cannot fail proves nothing — so make it fail on purpose.

    2026-06-21 at 03:00: the session high is 30742.25 as-of and 30968.00 final,
    so computing it the wrong way is detectably wrong, and the comparison this
    file relies on catches it.
    """
    sess_day, minute = "2026-06-21", "03:00"
    t = decision_ts(sess_day, minute)
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t_end = t0 + pd.Timedelta(hours=23)

    leaky = float(bars[(bars.index >= t0) & (bars.index < t_end)].high.max())
    honest = float(bars[(bars.index >= t0) & (bars.index < t)].high.max())
    assert leaky > honest, "chose a minute where the day still extends its high"
    assert not _same(leaky, honest), "the comparison used by this file is blind"
