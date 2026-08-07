"""Tests for src/live/vector.py — the live E3/E4 book switch (Phase 4 Stage 8).

Focus: the note_bar() O(1) readiness hook and its perf contract (bars_provider must
be called at most once per day, never while merely checking PENDING). Decision
correctness against the frozen reference is scripts/vector_parity.py (all 113 days).
"""

import pandas as pd

from src.live.vault import PENDING
from src.live.vector import LiveVectorPolicy

NY = "America/New_York"


def _bars(day, times, price=25000.0):
    """A minimal frame: `day`'s pre-open bars run 00:00->07:59, `today` from 08:00 on."""
    rows = []
    for h, m in times:
        rows.append({"ts_event": pd.Timestamp(f"{day} {h:02d}:{m:02d}", tz=NY),
                     "open": price, "high": price + 1, "low": price - 1,
                     "close": price, "volume": 10.0})
    return pd.DataFrame(rows)


class _CountingProvider:
    """Wraps a DataFrame and counts how many times it's actually materialized."""
    def __init__(self, df):
        self.df = df
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.df


def test_pending_before_any_bar_seen_never_touches_bars_provider_WHEN_tracked():
    """With note_bar tracking (the runner's real usage), PENDING costs zero calls."""
    df = _bars("2026-03-17", [(h, 0) for h in range(0, 8)])
    prov = _CountingProvider(df)
    policy = LiveVectorPolicy(prov, daytypes_csv="does/not/exist.csv")
    policy.note_bar(pd.Timestamp("2026-03-17 07:00", tz=NY))
    assert policy("2026-03-17") == PENDING
    assert prov.calls == 0                          # PENDING answered without materializing


def test_pending_without_note_bar_falls_back_to_one_call():
    """Without note_bar (a caller that never tracks), PENDING still costs exactly ONE
    call — not the zero of the fast path, but not repeated either."""
    df = _bars("2026-03-17", [(h, 0) for h in range(0, 8)])
    prov = _CountingProvider(df)
    policy = LiveVectorPolicy(prov, daytypes_csv="does/not/exist.csv")
    assert policy("2026-03-17") == PENDING
    assert prov.calls == 1


def test_note_bar_tracked_pending_stays_cheap_across_many_retries():
    """The actual perf contract: retrying __call__ many times (the Vault's per-bar
    PENDING retry) must cost O(1) each — bars_provider() untouched until 08:00."""
    df = _bars("2026-03-17", [(h, 0) for h in range(0, 8)])
    prov = _CountingProvider(df)
    policy = LiveVectorPolicy(prov, daytypes_csv="does/not/exist.csv")
    for h in range(0, 8):                            # 8 "PENDING retry" bars, pre-open
        policy.note_bar(pd.Timestamp(f"2026-03-17 {h:02d}:00", tz=NY))
        assert policy("2026-03-17") == PENDING
    assert prov.calls == 0                           # still zero — no frame ever pulled


def test_note_bar_ready_at_first_bar_at_or_after_open_materializes_once():
    df = _bars("2026-03-17", [(h, 0) for h in range(0, 9)])   # includes 08:00
    prov = _CountingProvider(df)
    policy = LiveVectorPolicy(prov, daytypes_csv="does/not/exist.csv")
    for h in range(0, 8):
        policy.note_bar(pd.Timestamp(f"2026-03-17 {h:02d}:00", tz=NY))
        policy("2026-03-17")
    policy.note_bar(pd.Timestamp("2026-03-17 08:00", tz=NY))
    pick = policy("2026-03-17")
    assert pick != PENDING and prov.calls == 1        # exactly one materialization
    policy("2026-03-17")                              # cached: no further calls
    assert prov.calls == 1


def test_evening_bar_of_next_session_does_not_falsely_resolve_prior_day():
    """An 18:00+ bar rolls into the NEXT session day (per _session_date) — note_bar
    for that bar must not be mistaken for the day it nominally shares a calendar
    date with."""
    df = _bars("2026-03-17", [(7, 0)])
    prov = _CountingProvider(df)
    policy = LiveVectorPolicy(prov, daytypes_csv="does/not/exist.csv")
    policy.note_bar(pd.Timestamp("2026-03-16 18:30", tz=NY))   # rolls to 2026-03-17 session
    # tracked under 2026-03-17 (the session day), but it's an EVENING bar, not 08:00+
    assert policy("2026-03-17") == PENDING
    assert prov.calls == 0


def test_fallback_without_note_bar_still_correct_and_single_fetch():
    """A caller that never invokes note_bar (e.g. the parity script) still gets a
    correct answer, and — since the readiness check and the decision reuse the SAME
    fetched frame — still only ONE bars_provider() call, not two."""
    df = _bars("2026-03-17", [(h, 0) for h in range(0, 9)])
    prov = _CountingProvider(df)
    policy = LiveVectorPolicy(prov, daytypes_csv="does/not/exist.csv")
    pick = policy("2026-03-17")
    assert pick != PENDING and prov.calls == 1


def test_no_bars_for_day_is_pending_via_fallback_too():
    df = _bars("2026-03-16", [(h, 0) for h in range(0, 9)])   # a different day entirely
    prov = _CountingProvider(df)
    policy = LiveVectorPolicy(prov, daytypes_csv="does/not/exist.csv")
    assert policy("2026-03-17") == PENDING
