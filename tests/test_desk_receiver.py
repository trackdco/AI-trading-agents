"""Tests for src/desk/receiver.py — Hermes verdicts vs. the risk guard + journal."""

import json
import time

from src.desk.receiver import DeskReceiver
from src.desk.verdict import SizingConfig
from src.live.journal import LiveJournal
from src.live.risk import RiskGuard, RiskLimits

CFG = SizingConfig()   # v1.2 defaults


def _write(dir_, name, obj, age_s=3.0):
    p = dir_ / name
    p.write_text(json.dumps(obj))
    old = time.time() - age_s
    import os
    os.utime(p, (old, old))                      # simulate a file past min_age_s
    return p


def _pass_obj(**kw):
    base = {
        "trade": True, "pattern": "A", "direction": "long",
        "entry": 25000.0, "stop": 24980.0,           # 20pt stop -> not oversized
        "target_level": 25045.0,                     # 45/20 = 2.25R -> clears floor
        "target": 25043.0,
        "size": "full", "grade": "A", "thesis": "ok",
        "gates": {"atlas": "pass", "helios": "pass", "apollo": "pass",
                  "hephaestus": "pass"},
        "trigger_ts": "2026-03-17T08:20:00-04:00",
        "snapshot_ts": "2026-03-17T08:20:00-04:00",
        "facts": {"confluence_count": 2, "with_trend": True,
                  "a_at_extension": False, "target_r_multiple": 2.25,
                  "half_trigger_count": 0, "half_trigger_reasons": []},
    }
    base.update(kw)
    return base


def _receiver(tmp_path, on_approved=None, limits=None):
    watch = tmp_path / "inbox"
    watch.mkdir()
    journal = LiveJournal(tmp_path / "journal")
    guard = RiskGuard(limits or RiskLimits(kill_file=tmp_path / "KILL"))
    r = DeskReceiver(watch_dir=watch, sizing_cfg=CFG, journal=journal, guard=guard,
                     on_approved=on_approved, min_age_s=1.0)
    return r, journal, guard, watch


def test_approved_trade_journaled_and_handed_to_callback(tmp_path):
    approved = []
    r, journal, guard, watch = _receiver(tmp_path, on_approved=approved.append)
    _write(watch, "v1.json", _pass_obj())
    out = r.poll_once()
    assert len(out) == 1 and out[0].status == "approved"
    assert len(approved) == 1 and approved[0].entry == 25000.0
    notes = journal.decisions()
    assert any("desk_trade_approved" in d["text"] for d in notes)
    assert (watch / "processed" / "v1.json").exists()
    assert not (watch / "v1.json").exists()


def test_vetoed_verdict_journaled_not_risk_gated(tmp_path):
    r, journal, guard, watch = _receiver(tmp_path)
    obj = _pass_obj(trade=False, entry=None, stop=None, target_level=None,
                    target=None, size=None, grade=None)
    obj["gates"]["apollo"] = "fail"
    _write(watch, "v1.json", obj)
    out = r.poll_once()
    assert out[0].status == "vetoed"
    assert any("desk_verdict_veto" in d["text"] for d in journal.decisions())


def test_invalid_verdict_rejected_and_moved_aside(tmp_path):
    r, journal, guard, watch = _receiver(tmp_path)
    _write(watch, "bad.json", {"garbage": True})
    out = r.poll_once()
    assert out[0].status == "rejected"
    assert (watch / "rejected" / "bad.json").exists()


def test_kill_switch_blocks_approval(tmp_path):
    r, journal, guard, watch = _receiver(tmp_path)
    guard.trip()
    _write(watch, "v1.json", _pass_obj())
    out = r.poll_once()
    assert out[0].status == "risk_gated" and out[0].reason == "kill_switch"
    assert (watch / "processed" / "v1.json").exists()


def test_daily_loss_limit_blocks_approval(tmp_path):
    r, journal, guard, watch = _receiver(
        tmp_path, limits=RiskLimits(kill_file=tmp_path / "KILL",
                                    daily_loss_dollars=100.0))
    from src.live.vault import TradeEvent
    ev = TradeEvent(trade_date="2026-03-17", trigger_ts="x", direction="long",
                    pattern="A", fill_ts="x", entry=1.0, stop_initial=1.0,
                    target_level=1.0, exit_ts="x", exit_price=1.0,
                    exit_reason="stop", points=-5.0, dollars=-200.0,
                    r_multiple=-1.0, size=1.0, book="champion")
    guard.on_trade(ev)                            # champion already blew the daily limit
    _write(watch, "v1.json", _pass_obj())          # Desk trade lands the SAME session
    out = r.poll_once()
    assert out[0].status == "risk_gated" and out[0].reason == "daily_loss_limit"


def test_too_fresh_file_is_left_for_next_poll(tmp_path):
    r, journal, guard, watch = _receiver(tmp_path)
    (watch / "v1.json").write_text(json.dumps(_pass_obj()))   # mtime = now
    out = r.poll_once()
    assert out == [] and (watch / "v1.json").exists()          # untouched, not yet stable


def test_restart_never_reprocesses_a_moved_file(tmp_path):
    approved = []
    r, journal, guard, watch = _receiver(tmp_path, on_approved=approved.append)
    _write(watch, "v1.json", _pass_obj())
    r.poll_once()
    # crash-restart: a brand-new DeskReceiver pointed at the SAME inbox/journal
    r2 = DeskReceiver(watch_dir=watch, sizing_cfg=CFG, journal=journal, guard=guard,
                      on_approved=approved.append, min_age_s=1.0)
    out = r2.poll_once()
    assert out == [] and len(approved) == 1        # file already moved out, nothing to see


def test_on_approved_failure_does_not_block_journaling_or_move(tmp_path):
    def bad(v):
        raise RuntimeError("execution layer down")
    r, journal, guard, watch = _receiver(tmp_path, on_approved=bad)
    _write(watch, "v1.json", _pass_obj())
    out = r.poll_once()
    assert out[0].status == "approved"             # still reported approved
    assert r.failures == 1
    assert (watch / "processed" / "v1.json").exists()   # still moved, not stuck


def test_missing_watch_dir_returns_empty_not_raises(tmp_path):
    journal = LiveJournal(tmp_path / "journal")
    guard = RiskGuard(RiskLimits(kill_file=tmp_path / "KILL"))
    r = DeskReceiver(watch_dir=tmp_path / "does_not_exist", sizing_cfg=CFG,
                     journal=journal, guard=guard)
    assert r.poll_once() == []
