"""Tests for src/live/journal.py — the live audit journal (Phase 4 Stage 6)."""

from src.backtest.engine import TradeRecord
from src.desk.journal import from_trade_record
from src.live.journal import LiveJournal, cfg_hash


def _tr(date="2026-03-17", fill="2026-03-17T08:26:00-04:00", points=129.25,
        dollars=2576.0):
    return TradeRecord(
        trade_date=date, trigger_ts="2026-03-17T08:20:00-04:00", tf="2min",
        direction="long", kind="rejection_block", pattern="A", htf_flag="with_trend",
        confluence=2, entry_variant="E4", limit_price=25000.0, fill_ts=fill,
        entry=25000.0, stop_initial=24990.0, target_name="pdh", target_level=25130.0,
        working_target=25129.25, exit_ts="2026-03-17T09:40:00-04:00",
        exit_price=25129.25, exit_reason="target", points=points, r_multiple=2.1,
        size=1.0, dollars=dollars, slippage_ticks=0, mgmt_variant="V0")


class _Cfg:
    """Minimal stand-in with pydantic's hashing surface."""
    def __init__(self, blob='{"win_end":"10:15"}'):
        self._blob = blob

    def model_dump_json(self):
        return self._blob


def test_on_record_writes_full_frozen_schema_row(tmp_path):
    j = LiveJournal(tmp_path)
    cfg = _Cfg()
    j.on_record(_tr(), "E4", cfg)
    rows = j.trades()
    assert len(rows) == 1
    r = rows[0]
    expect = from_trade_record(_tr(), config_hash=cfg_hash(cfg), playbook="E4")
    assert r == expect                                  # full frozen schema, verbatim
    assert r.playbook == "E4" and r.mgmt_variant == "V0" and r.win is True
    assert len(r.config_hash) == 12                     # reproducibility stamp present


def test_dedup_survives_restart(tmp_path):
    j = LiveJournal(tmp_path)
    j.on_record(_tr(), "E4", _Cfg())
    j.on_record(_tr(), "E4", _Cfg())                    # same trade re-delivered
    assert len(j.trades()) == 1
    j2 = LiveJournal(tmp_path)                          # crash-restart
    j2.on_record(_tr(), "E4", _Cfg())
    assert len(j2.trades()) == 1                        # still one row


def test_decisions_trail_sessions_and_halts(tmp_path):
    j = LiveJournal(tmp_path)
    policy = j.wrap_policy(lambda d: ("E3", "cfg", None) if d == "2026-03-17" else None)
    assert policy("2026-03-17")[0] == "E3"              # pick passes through unchanged
    assert policy("2026-03-18") is None                 # stand-down passes through too
    j.on_halt("2026-03-18", "daily_loss_limit")
    j.note("manual restart")
    kinds = [(d["type"], d.get("book", "-")) for d in j.decisions()]
    assert kinds == [("session", "E3"), ("session", None),
                     ("halt", "-"), ("note", "-")]
    assert all("ts" in d for d in j.decisions())


def test_reconcile_row_for_row_vs_batch(tmp_path):
    j = LiveJournal(tmp_path)
    j.on_record(_tr(), "E4", _Cfg())
    ok = j.reconcile([_tr()])
    assert ok["match"] and not ok["missing"] and not ok["unexpected"]
    bad = j.reconcile([_tr(fill="2026-03-17T09:00:00-04:00")])
    assert not bad["match"] and len(bad["missing"]) == 1 and len(bad["unexpected"]) == 1


def test_writes_are_failsoft(tmp_path):
    j = LiveJournal(tmp_path / "blocked")
    (tmp_path / "blocked").write_text("a file, not a dir")   # mkdir will fail
    j.on_record(_tr(), "E4", _Cfg())                    # must not raise
    j.on_halt("2026-03-18", "kill_switch")
    assert j.failures == 2 and j.trades() == []


def test_cfg_hash_stable_and_distinct():
    a, b = _Cfg('{"x":1}'), _Cfg('{"x":1}')
    assert cfg_hash(a) == cfg_hash(b)                   # content-addressed, not identity
    assert cfg_hash(a) != cfg_hash(_Cfg('{"x":2}'))


# ---- Stage-6 review regressions ---------------------------------------------

def test_torn_final_line_survives_restart(tmp_path):
    """Review F1: a crash mid-write leaves a torn last line — restart must not crash,
    intact rows must survive, and dedup must still hold."""
    j = LiveJournal(tmp_path)
    j.on_record(_tr(), "E4", _Cfg())
    with (tmp_path / "journal.jsonl").open("a") as f:
        f.write('{"trade_date": "2026-03-18", "fill_')  # torn mid-write
    j2 = LiveJournal(tmp_path)                          # must construct, not raise
    assert len(j2.trades()) == 1 and j2.corrupt_journal_lines == 1
    j2.on_record(_tr(), "E4", _Cfg())                   # intact row still deduped
    assert len(j2.trades()) == 1


def test_torn_decisions_line_skipped_not_raised(tmp_path):
    j = LiveJournal(tmp_path)
    j.on_halt("2026-03-18", "kill_switch")
    with (tmp_path / "decisions.jsonl").open("a") as f:
        f.write('{"type": "hal')
    assert len(j.decisions()) == 1 and j.corrupt_decision_lines == 1
    LiveJournal(tmp_path)                               # restart seeding tolerant too


def test_schema_drift_row_skipped_and_counted(tmp_path):
    j = LiveJournal(tmp_path)
    j.on_record(_tr(), "E4", _Cfg())
    with (tmp_path / "journal.jsonl").open("a") as f:
        f.write('{"trade_date": "2026-03-18", "not_a_field": 1}\n')  # valid JSON, bad row
    assert len(j.trades()) == 1 and j.corrupt_journal_lines == 1


def test_config_hash_immune_to_id_reuse(tmp_path):
    """Review F2 (proven live): CPython reuses freed object ids — the stamp must be
    content-addressed, never cached by id()."""
    j = LiveJournal(tmp_path)
    cfg_a = _Cfg('{"win_end":"10:15"}')
    j.on_record(_tr(), "E3", cfg_a)
    del cfg_a                                           # free the address
    cfg_b = _Cfg('{"win_end":"11:30"}')                 # often lands on the SAME id
    j.on_record(_tr(fill="2026-03-17T09:00:00-04:00"), "E3", cfg_b)
    assert j.trades()[1].config_hash == cfg_hash(cfg_b)


def test_session_picks_logged_once_across_restarts(tmp_path):
    """Review F3: a restarted Vault re-rolls warmup sessions — the audit trail must
    not re-append the same pick every restart."""
    j = LiveJournal(tmp_path)
    policy = j.wrap_policy(lambda d: ("E3", "cfg", None))
    policy("2026-03-17")
    policy("2026-03-17")                                # same session re-rolled
    assert len(j.decisions()) == 1
    j2 = LiveJournal(tmp_path)                          # crash-restart
    j2.wrap_policy(lambda d: ("E3", "cfg", None))("2026-03-17")
    assert len(j2.decisions()) == 1                     # still once
    j2.wrap_policy(lambda d: ("E4", "cfg", None))("2026-03-17")
    assert len(j2.decisions()) == 2                     # a DIFFERENT pick is news
