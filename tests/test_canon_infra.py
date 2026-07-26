"""Infra-seam tests (item 6): startup parity gate, heartbeat, spine journal sink, MBO
capture window, B2 offload — all offline with injected transports."""
from __future__ import annotations

import pandas as pd

import importlib.util
from pathlib import Path

from src.canon.infra import (
    B2Offload,
    Heartbeat,
    MBOCapture,
    SierraArchiver,
    SpineJournalSink,
    StartupParityGate,
)

NY = "America/New_York"


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
    assert keys == ["sierra/a.jsonl", "sierra/b.jsonl"]     # prefix repointed mbo -> sierra
    assert [u[0] for u in uploaded] == ["nq-mbo", "nq-mbo"] and all(u[2] > 0 for u in uploaded)


def test_b2_upload_path_single_file(tmp_path):
    f = tmp_path / "x.scid"
    f.write_bytes(b"abc")
    up = []
    off = B2Offload("bkt", lambda b, k, d: up.append((b, k, len(d))), prefix="sierra")
    key = off.upload_path(f, "sierra/scid/x.scid")
    assert key == "sierra/scid/x.scid" and up == [("bkt", "sierra/scid/x.scid", 3)]


# --------------------------------------------------------------------------- Sierra archiver
def _sierra_dir(tmp_path):
    data = tmp_path / "Data"
    (data / "MarketDepthData").mkdir(parents=True)
    (data / "NQU26-CME.scid").write_bytes(b"scid-day1")
    (data / "MarketDepthData" / "NQU26-CME.2026-09-10.depth").write_bytes(b"depth10")
    return data


def test_sierra_archiver_uploads_depth_and_scid_idempotently(tmp_path):
    data = _sierra_dir(tmp_path)
    uploaded = []
    off = B2Offload("nq-sierra-book", lambda b, k, d: uploaded.append(k), prefix="sierra")
    arch = SierraArchiver(data, off, tmp_path / "manifest.json")
    now = pd.Timestamp("2026-09-10 12:00", tz=NY)
    keys = arch.archive(now=now)
    assert "sierra/depth/NQU26-CME.2026-09-10.depth" in keys       # per-day depth (immutable)
    assert "sierra/scid/2026-09-10/NQU26-CME.scid" in keys         # nightly date-stamped .scid
    # idempotent: a second run sends nothing
    assert arch.archive(now=now) == []
    # .scid grows -> re-archived; the depth is unchanged so it is NOT re-sent
    (data / "NQU26-CME.scid").write_bytes(b"scid-day1-grown")
    keys2 = arch.archive(now=now)
    assert keys2 == ["sierra/scid/2026-09-10/NQU26-CME.scid"]


def test_sierra_archiver_catches_the_box_depth_naming(tmp_path):
    """Pat's VPS writes NQU6.CME.<date>.depth (dot separator, single-digit year) next to
    NQU26-CME.scid — the old root+suffix glob silently skipped every depth file, the one
    class that cannot be re-downloaded (found via dry-run on-box 2026-07-26). The archiver
    must match depth files on ROOT alone."""
    data = _sierra_dir(tmp_path)
    (data / "MarketDepthData" / "NQU6.CME.2026-07-24.depth").write_bytes(b"depth-box")
    uploaded = []
    off = B2Offload("nq-mbo-archive", lambda b, k, d: uploaded.append(k), prefix="sierra")
    keys = SierraArchiver(data, off, tmp_path / "m.json").archive(
        now=pd.Timestamp("2026-07-26 12:00", tz=NY))
    assert "sierra/depth/NQU6.CME.2026-07-24.depth" in keys
    assert "sierra/depth/NQU26-CME.2026-09-10.depth" in keys       # default naming still works


def test_sierra_archiver_pending_is_read_only(tmp_path):
    data = _sierra_dir(tmp_path)
    off = B2Offload("b", lambda *a: None)
    arch = SierraArchiver(data, off, tmp_path / "m.json")
    p = arch.pending(now=pd.Timestamp("2026-09-10 12:00", tz=NY))
    assert len(p) == 2 and not (tmp_path / "m.json").exists()      # no upload, no manifest write


def test_sierra_archiver_catches_up_multiple_depth_days(tmp_path):
    data = _sierra_dir(tmp_path)
    # a second (older, un-archived) depth day still present in Sierra's ~30-day window
    (data / "MarketDepthData" / "NQU26-CME.2026-09-09.depth").write_bytes(b"depth09")
    off = B2Offload("b", lambda *a: None, prefix="sierra")
    arch = SierraArchiver(data, off, tmp_path / "m.json")
    keys = arch.archive(now=pd.Timestamp("2026-09-10 12:00", tz=NY))
    assert "sierra/depth/NQU26-CME.2026-09-09.depth" in keys       # caught up before ageout
    assert "sierra/depth/NQU26-CME.2026-09-10.depth" in keys


def test_archive_sierra_register_command():
    spec = importlib.util.spec_from_file_location(
        "archive_sierra", Path(__file__).resolve().parents[1] / "scripts" / "archive_sierra.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cmd = mod.register_command("config/live.yaml", time_ct="17:30", task="SierraArchive")
    assert cmd.startswith("schtasks /Create /SC DAILY") and "SierraArchive" in cmd
    assert "/ST 17:30" in cmd and "archive_sierra.py" in cmd
