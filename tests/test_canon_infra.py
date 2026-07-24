"""Infra-seam tests (item 6): startup parity gate, heartbeat, spine journal sink, MBO
capture window, B2 offload — all offline with injected transports."""
from __future__ import annotations

import pandas as pd

from src.canon.infra import (
    B2Offload,
    Heartbeat,
    MBOCapture,
    SpineJournalSink,
    StartupParityGate,
)


def test_startup_gate_read_only_until_green():
    g = StartupParityGate(lambda: False)
    assert g.run() is False and g.may_trade is False        # red -> no trading
    g2 = StartupParityGate(lambda: True)
    assert g2.run() is True and g2.may_trade is True
    g3 = StartupParityGate(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert g3.run() is False and g3.may_trade is False      # a throwing gate is NOT green


def test_heartbeat_fires_once_on_loss():
    fired = []
    hb = Heartbeat(miss_after_s=10, on_lost=lambda last: fired.append(last))
    hb.beat(pd.Timestamp("2026-03-17T12:00:00Z"))
    assert hb.check(pd.Timestamp("2026-03-17T12:00:05Z")) is True     # alive
    assert hb.check(pd.Timestamp("2026-03-17T12:00:30Z")) is False    # lost
    assert hb.check(pd.Timestamp("2026-03-17T12:00:40Z")) is False    # still lost
    assert len(fired) == 1
    hb.beat(pd.Timestamp("2026-03-17T12:00:41Z"))                     # recovers
    assert hb.check(pd.Timestamp("2026-03-17T12:00:45Z")) is True and hb.lost is False


def test_spine_journal_sink_roundtrip(tmp_path):
    sink = SpineJournalSink(tmp_path / "spine.jsonl")
    sink({"event": "decision", "rule": "dd_proximity", "action": "halt"})
    sink({"event": "flatten_halt", "rule": "readback_mismatch"})
    evs = sink.events()
    assert len(evs) == 2 and evs[0]["rule"] == "dd_proximity"


def test_mbo_capture_window_and_eviction():
    cap = MBOCapture(window_s=60)
    base = pd.Timestamp("2026-03-17T12:00:00Z")
    for i in range(0, 180, 10):                              # events every 10s over 3 min
        cap.on_event(base + pd.Timedelta(seconds=i), {"action": "A", "i": i})
    # buffer keeps only the last 60s (evicted older)
    assert all(ts >= cap.buf[-1][0] - pd.Timedelta(seconds=60) for ts, _ in cap.buf)
    # window_around a trade returns only events within +/-60s of it
    win = cap.window_around(base + pd.Timedelta(seconds=150))
    assert win and all(90 <= r["i"] <= 210 for r in win)   # 150s +/- 60s = [90,210]


def test_mbo_dump_to_file(tmp_path):
    cap = MBOCapture(window_s=60)
    t = pd.Timestamp("2026-03-17T12:00:00Z")
    cap.on_event(t, {"action": "A", "id": 1})
    n = cap.dump_around(t, tmp_path / "trade_1.jsonl")
    assert n == 1 and (tmp_path / "trade_1.jsonl").exists()


def test_b2_offload_uses_injected_uploader(tmp_path):
    (tmp_path / "a.jsonl").write_text('{"x":1}')
    (tmp_path / "b.jsonl").write_text('{"x":2}')
    uploaded = []
    off = B2Offload("nq-mbo", lambda bucket, key, data: uploaded.append((bucket, key, len(data))))
    keys = off.offload(tmp_path)
    assert keys == ["mbo/a.jsonl", "mbo/b.jsonl"]
    assert [u[0] for u in uploaded] == ["nq-mbo", "nq-mbo"] and all(u[2] > 0 for u in uploaded)
