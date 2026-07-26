"""TradeLifecycle — the armed-path assembly (watch -> fill -> managed exit), fail-closed.

The watch and the executor have their own engine-parity suites (test_order_watch,
test_exit_live); here they are fakes and every ROUTING path is pinned: shadow journaling
with zero broker calls, armed cancels, fill hand-off to the exit factory, the raced fill,
the 3-min cut gate at t+3, and every fail-closed flatten. cut_inputs (the live r_3/fw_3)
is parity-checked against the stored intrade_matrix rows the batch computed."""
from __future__ import annotations

import math

import pandas as pd
import pytest

from src.live.trade_lifecycle import TradeLifecycle, cut_inputs

NY = "America/New_York"


class FakeBroker:
    def __init__(self, position=0):
        self.calls = []
        self._position = position

    def position(self, account):
        return self._position

    def cancel_order(self, ref):
        self.calls.append(("cancel_order", ref))

    def flatten(self, account):
        self.calls.append(("flatten", account))


class FakeExe:
    def __init__(self, cut=False):
        self.bars_seen = []
        self.cuts = []
        self.cut = cut
        self.done = False
        self.halted = False

    def maybe_cut(self, r_3, fw_3):
        self.cuts.append((r_3, fw_3))
        return self.cut

    def on_bar(self, bars_df, ts):
        self.bars_seen.append(ts)
        return []


def _bar(hm, high=100.5, low=99.5, day="2026-03-17"):
    ts = pd.Timestamp(f"{day} {hm}", tz=NY)
    return {"ts_event": ts, "open": 100.0, "high": high, "low": low, "close": 100.0,
            "volume": 10.0}


def _lc(*, armed=False, position=0, exit_factory=None, cut_fn=None):
    broker = FakeBroker(position=position) if armed else None
    rows = []
    lc = TradeLifecycle(broker=broker, account="FUNDED", armed=armed,
                        journal=rows.append, exit_factory=exit_factory,
                        cut_inputs_fn=cut_fn or (lambda *a, **k: (math.nan, math.nan)))
    return lc, broker, rows


def test_shadow_journals_wouldbe_cancel_with_no_broker_at_all():
    lc, _, rows = _lc(armed=False)
    lc.on_placed("shadow:s1", side="B", entry=100.0, stop=99.0, size=3)
    lc.on_bar(_bar("09:00", high=122.0))                     # runs 22 pts: engine cancels
    ow = [r for r in rows if r["event"] == "order_watch"]
    assert ow and ow[0]["reason"] == "cancelled_tcancel" and ow[0]["executed"] is False
    assert not lc.halted                                     # no broker exists to touch


def test_armed_cancel_decision_executes_through_the_broker():
    lc, b, rows = _lc(armed=True)
    lc.on_placed("ref1", side="B", entry=100.0, stop=99.0, size=3)
    lc.on_bar(_bar("09:00", high=122.0))
    assert ("cancel_order", "ref1") in b.calls
    assert [r["event"] for r in rows if r["event"] == "order_watch"] == ["order_watch"]


def test_armed_fill_hands_off_to_the_exit_factory_and_reports_the_race():
    made = []
    lc, b, rows = _lc(armed=True, position=3,
                      exit_factory=lambda *a: made.append(a) or FakeExe())
    lc.on_placed("ref1", side="B", entry=100.0, stop=99.0, size=3)
    lc.on_bar(_bar("09:00", high=122.0))                     # fill read-back AND the bar ran
    assert made == [("ref1", "B", 100.0, 99.0, 3)]           # size from the position read-back
    assert ("cancel_order", "ref1") not in b.calls           # filled entry is never cancelled
    ow = [r for r in rows if r["event"] == "order_watch"]
    assert ow and ow[0]["reason"] == "tcancel_raced_fill"    # the race reaches the journal


def test_armed_fill_with_no_exit_factory_fails_closed():
    lc, b, rows = _lc(armed=True, position=3, exit_factory=None)
    lc.on_placed("ref1", side="B", entry=100.0, stop=99.0, size=3)
    lc.on_bar(_bar("09:00"))
    assert lc.halted and ("flatten", "FUNDED") in b.calls
    assert any(r["event"] == "lifecycle_fail_closed" for r in rows)


def test_cut_gate_fires_once_at_t_plus_3_and_abandons_the_stream():
    exe = FakeExe(cut=True)
    lc, b, rows = _lc(armed=True, position=3, exit_factory=lambda *a: exe,
                      cut_fn=lambda *a, **k: (-0.2, -20.0))
    lc.on_placed("ref1", side="B", entry=100.0, stop=99.0, size=3)
    lc.on_bar(_bar("09:00"))                                 # fill bar
    lc.on_bar(_bar("09:01"))
    lc.on_bar(_bar("09:02"))
    assert exe.cuts == []                                    # before t+3: never asked
    lc.on_bar(_bar("09:03"))                                 # t+3: cut inputs computed once
    assert exe.cuts == [(-0.2, -20.0)]
    lc.on_bar(_bar("09:04"))                                 # stream abandoned after the cut
    assert exe.cuts == [(-0.2, -20.0)]
    assert "09:04" not in [str(t.time())[:5] for t in exe.bars_seen]


def test_cut_gate_healthy_trade_keeps_driving_the_executor():
    exe = FakeExe(cut=False)
    lc, _, _ = _lc(armed=True, position=3, exit_factory=lambda *a: exe,
                   cut_fn=lambda *a, **k: (0.5, 10.0))
    lc.on_placed("ref1", side="B", entry=100.0, stop=99.0, size=3)
    for hm in ("09:00", "09:01", "09:02", "09:03", "09:04"):
        lc.on_bar(_bar(hm))
    assert exe.cuts == [(0.5, 10.0)]                         # checked exactly once
    assert len(exe.bars_seen) == 5                           # driven every bar incl. fill bar


def test_executor_halt_propagates_to_the_lifecycle():
    exe = FakeExe()
    lc, _, rows = _lc(armed=True, position=3, exit_factory=lambda *a: exe)
    lc.on_placed("ref1", side="B", entry=100.0, stop=99.0, size=3)
    lc.on_bar(_bar("09:00"))
    exe.halted = True                                        # the executor flattened (C7)
    lc.on_bar(_bar("09:01"))
    assert lc.halted
    assert any(r["event"] == "lifecycle_halted_by_executor" for r in rows)
    assert lc.on_bar(_bar("09:02")) is None and len(exe.bars_seen) == 2   # frozen


def test_any_exception_in_the_step_flattens_armed():
    class BadBroker(FakeBroker):
        def position(self, account):
            raise RuntimeError("socket died")
    rows = []
    lc = TradeLifecycle(broker=BadBroker(), account="FUNDED", armed=True,
                        journal=rows.append, exit_factory=lambda *a: FakeExe())
    lc.on_placed("ref1", side="B", entry=100.0, stop=99.0, size=3)
    lc.on_bar(_bar("09:00"))
    assert lc.halted and ("flatten", "FUNDED") in lc.broker.calls
    assert any("socket died" in r.get("why", "") for r in rows)


def test_armed_requires_a_broker():
    with pytest.raises(ValueError):
        TradeLifecycle(broker=None, armed=True)


# --------------------------------------------------------------------------- cut_inputs parity
def test_cut_inputs_parity_against_the_stored_intrade_matrix():
    """r_3/fw_3 recomputed live must equal the batch's (scripts/intrade_matrix.py) on real
    trades. A spread sample keeps it fast; the window slice per trade is fair because
    cut_inputs only ever reads [fill, fill+3min]."""
    im = pd.read_parquet("output/intrade_matrix.parquet")
    alive = im[im.r_3.notna()].reset_index(drop=True)
    assert len(alive) > 100
    sample = alive.iloc[:: max(1, len(alive) // 40)]

    M = pd.read_parquet("output/fp_minutes.parquet")
    M.index = pd.DatetimeIndex(M.index)
    M = M.sort_index()
    mb = pd.read_parquet("data/reference/nq_1m_master.parquet")
    fb = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    bars = pd.concat([mb, fb], ignore_index=True).drop_duplicates("ts_event") \
        .sort_values("ts_event").reset_index(drop=True)
    bt = bars.ts_event.dt.tz_convert(NY)

    for t in sample.itertuples():
        f = pd.Timestamp(t.fill).tz_convert(NY).floor("min")
        win = (bt >= f - pd.Timedelta(minutes=1)) & (bt <= f + pd.Timedelta(minutes=4))
        tape = M.loc[f - pd.Timedelta(minutes=1): f + pd.Timedelta(minutes=4)]
        r3, fw3 = cut_inputs(bars[win], tape, entry=t.entry, risk=t.risk,
                             direction=t.direction, fill_ts=t.fill)
        assert fw3 == pytest.approx(t.fw_3, abs=1e-9), (t.day, t.fill, "fw_3")
        assert r3 == pytest.approx(t.r_3, abs=1e-9), (t.day, t.fill, "r_3")


def test_cut_inputs_insufficient_data_is_nan_never_a_guess():
    r3, fw3 = cut_inputs(pd.DataFrame(), pd.DataFrame(), entry=100.0, risk=10.0,
                         direction="long", fill_ts=pd.Timestamp("2026-03-17 09:00", tz=NY))
    assert math.isnan(r3) and math.isnan(fw3)
