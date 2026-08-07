"""OrderWatch (gate B7) — the live cancel decisions must equal the engine's, boundary by
boundary. Conditions are mirrored expression-for-expression from engine.py's working-order
block; these tests pin every boundary at the engine's exact semantics (strict vs inclusive,
window half-open, EOD belt, overnight wrap) plus the fill/cancel race the engine can't have."""
from __future__ import annotations

from datetime import time as dtime

import pandas as pd

from src.canon.order_watch import OrderWatch

NY = "America/New_York"


def _watch(**kw):
    base = {"t_cancel": 22.0, "win_start": dtime(8, 0), "win_end": dtime(10, 15),
            "eod_flatten": dtime(15, 55)}
    base.update(kw)
    return OrderWatch(**base)


def _ts(hm: str):
    return pd.Timestamp(f"2026-03-17 {hm}", tz=NY)


def test_windows_come_from_the_engine_config_not_a_restated_number():
    w = OrderWatch()
    assert w.win_end is not None and w.eod_flatten is not None


def test_rebuilt_canon_has_no_distance_cancel_by_default():
    """ANGUS 2026-07-30: the 22pt cancel measured INVERTED on the rebuilt population — it
    kept -0.180R of trades and killed +0.015R. A resting entry now lives until its own
    session window ends. Defaulting this back to 22.0 trades an unmeasured book."""
    w = OrderWatch()
    assert w.t_cancel is None
    w.register("r1", "B", 100.0)
    assert w.on_bar(_ts("09:00"), high=500.0, low=99.0) == [], "price ran 400pts — must hold"
    assert w.watching == ["r1"]


def test_long_cancels_when_high_runs_t_cancel_beyond_limit_inclusive():
    w = _watch()
    w.register("r1", "B", 100.0)
    assert w.on_bar(_ts("09:00"), high=121.99, low=99.0) == []          # 21.99 < 22: holds
    out = w.on_bar(_ts("09:01"), high=122.0, low=99.0)                  # >= : engine boundary
    assert out and out[0]["reason"] == "cancelled_tcancel" and not out[0]["raced_fill"]
    assert w.watching == []                                             # decided -> dropped


def test_short_mirror_cancels_on_the_low():
    w = _watch()
    w.register("r1", "S", 100.0)
    assert w.on_bar(_ts("09:00"), high=101.0, low=78.01) == []
    out = w.on_bar(_ts("09:01"), high=101.0, low=78.0)
    assert out and out[0]["reason"] == "cancelled_tcancel"


def test_window_end_cancel_is_half_open_at_win_end():
    """Engine: in_window = win_start <= tod < win_end — a bar stamped exactly 10:15 is
    OUTSIDE the window and the unfilled order is cancelled."""
    w = _watch()
    w.register("r1", "B", 100.0)
    assert w.on_bar(_ts("10:14"), high=100.5, low=99.5) == []
    out = w.on_bar(_ts("10:15"), high=100.5, low=99.5)
    assert out and out[0]["reason"] == "cancelled_window_end"


def test_eod_belt_beats_window_reason_and_stops_at_1800():
    """Engine order: past_eod is checked BEFORE in_window, and the belt covers
    [eod_flatten, 18:00) only — an 18:30 bar is next session, not this belt."""
    w = _watch()
    w.register("r1", "B", 100.0)
    out = w.on_bar(_ts("15:55"), high=100.5, low=99.5)
    assert out and out[0]["reason"] == "cancelled_eod"                  # not window_end
    w2 = _watch(win_start=dtime(18, 0), win_end=dtime(10, 15))          # overnight span
    w2.register("r2", "B", 100.0)
    out2 = w2.on_bar(_ts("18:30"), high=100.5, low=99.5)
    assert out2 == [] and w2.watching == ["r2"]                         # in-window overnight


def test_overnight_window_wrap():
    w = _watch(win_start=dtime(18, 0), win_end=dtime(10, 15), eod_flatten=dtime(15, 55))
    w.register("r1", "B", 100.0)
    assert w.on_bar(_ts("02:00"), high=100.5, low=99.5) == []           # wrapped: inside
    out = w.on_bar(_ts("10:15"), high=100.5, low=99.5)
    assert out and out[0]["reason"] == "cancelled_window_end"


def test_utc_stamped_bars_evaluate_against_ny_wall_clock():
    """Live bars arrive UTC-stamped (.scid feed); the engine's windows are NY wall-clock.
    A 09:00 NY bar expressed in UTC (13:00/14:00Z) must NOT read as past the window."""
    w = _watch()
    w.register("r1", "B", 100.0)
    assert w.on_bar(_ts("09:00").tz_convert("UTC"), high=100.5, low=99.5) == []
    out = w.on_bar(_ts("10:15").tz_convert("UTC"), high=100.5, low=99.5)
    assert out and out[0]["reason"] == "cancelled_window_end"


def test_filled_order_is_released_without_cancelling():
    w = _watch()
    w.register("r1", "B", 100.0)
    w.mark_filled("r1")
    assert w.on_bar(_ts("09:00"), high=100.5, low=99.5) == []
    assert w.watching == []


def test_fill_on_a_ran_bar_is_reported_as_the_race_never_silent():
    """The engine resolves a same-bar ran+fill to CANCEL; live, the exchange may fill first.
    That divergence must reach the journal — raced_fill=True — and must not trigger a broker
    cancel of a now-filled entry."""
    w = _watch()
    w.register("r1", "B", 100.0)
    w.mark_filled("r1")
    out = w.on_bar(_ts("09:00"), high=122.0, low=99.5)                  # ran AND filled
    assert out and out[0]["reason"] == "tcancel_raced_fill" and out[0]["raced_fill"]
    assert w.watching == []


def test_mark_gone_removes_without_deciding():
    w = _watch()
    w.register("r1", "B", 100.0)
    w.mark_gone("r1")
    assert w.on_bar(_ts("10:15"), high=200.0, low=99.5) == []


def test_multiple_orders_decided_independently():
    w = _watch()
    w.register("long", "B", 100.0)
    w.register("short", "S", 200.0)
    # high 122 runs the long (>= 100+22); low 180 does NOT run the short (> 200-22=178)
    out = w.on_bar(_ts("09:00"), high=122.0, low=180.0)
    assert [d["ref"] for d in out] == ["long"]
    assert w.watching == ["short"]


# ---- rebuilt canon: per-session expiry and the structural observation ----------------
def test_each_order_expires_on_its_own_session_window():
    """Pre-market orders die at 09:30, golden-window orders at 10:30. One global window
    cannot serve both — an order outliving its session is an unmeasured trade."""
    w = OrderWatch(win_start=dtime(8, 0), win_end=dtime(11, 0), eod_flatten=dtime(15, 55))
    w.register("pre", "B", 100.0, win_end=dtime(9, 30))
    w.register("gold", "B", 100.0, win_end=dtime(10, 30))
    assert w.on_bar(_ts("09:29"), high=101.0, low=99.5) == []
    out = w.on_bar(_ts("09:31"), high=101.0, low=99.5)
    assert [d["ref"] for d in out] == ["pre"] and out[0]["reason"] == "cancelled_window_end"
    assert w.watching == ["gold"], "the gold order must survive its own window"
    out2 = w.on_bar(_ts("10:31"), high=101.0, low=99.5)
    assert [d["ref"] for d in out2] == ["gold"]


def test_struct_event_broke_and_rejected_mirror_the_l1_walk():
    """STRUCT_ACCEPT=5 beyond a touched level is 'broke'; STRUCT_REJECT=8 back off it is
    'rejected'. These feed the elite 2.0x tier, so the thresholds are load-bearing."""
    w = OrderWatch(win_start=dtime(8, 0), win_end=dtime(11, 0), eod_flatten=dtime(15, 55))
    # long entry at 100, away-side level at 110 (above the trigger close)
    w.register("a", "B", 100.0, levels=[("vwap_mid", 110.0, "vwap")], close=105.0)
    w.on_bar(_ts("09:00"), high=110.5, low=104.0)          # touches, only 0.5 beyond
    assert w.struct_event("a") == ""
    w.on_bar(_ts("09:01"), high=115.0, low=109.0)          # 5.0 beyond -> broke
    assert w.struct_event("a") == "broke"

    w.register("b", "B", 100.0, levels=[("vwap_mid", 110.0, "vwap")], close=105.0)
    w.on_bar(_ts("09:02"), high=110.2, low=102.0)          # touched, 8.0 back off -> rejected
    assert w.struct_event("b") == "rejected"


def test_struct_only_considers_away_side_levels():
    """L1 filters the stack to levels at/beyond the trigger close in the run-away direction;
    a level behind the trade can never produce an event."""
    w = OrderWatch(win_start=dtime(8, 0), win_end=dtime(11, 0), eod_flatten=dtime(15, 55))
    w.register("a", "B", 100.0, levels=[("below", 90.0, "sr")], close=105.0)
    w.on_bar(_ts("09:00"), high=106.0, low=80.0)
    assert w.struct_event("a") == ""


def test_first_struct_event_is_final():
    w = OrderWatch(win_start=dtime(8, 0), win_end=dtime(11, 0), eod_flatten=dtime(15, 55))
    w.register("a", "B", 100.0, levels=[("L", 110.0, "sr")], close=105.0)
    w.on_bar(_ts("09:00"), high=116.0, low=109.0)
    assert w.struct_event("a") == "broke"
    w.on_bar(_ts("09:01"), high=110.0, low=100.0)          # would be a rejection
    assert w.struct_event("a") == "broke", "the first event wins and is final"
