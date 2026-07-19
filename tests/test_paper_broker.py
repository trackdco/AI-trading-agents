"""Tests for src/live/paper_broker.py — the simulated account (Phase 4 Stage 3)."""

from src.live.paper_broker import PaperBroker
from src.live.vault import TradeEvent


def _ev(date="2026-02-10", fill="2026-02-10T09:35:00-05:00", points=10.0, dollars=200.0,
        book="E3"):
    return TradeEvent(trade_date=date, trigger_ts=fill, direction="long", pattern="A",
                      fill_ts=fill, entry=25000.0, stop_initial=24990.0, target_level=25020.0,
                      exit_ts=fill, exit_price=25010.0, exit_reason="target", points=points,
                      dollars=dollars, r_multiple=1.0, size=1.0, book=book)


def test_books_trades_and_totals_points_dollars_separate():
    b = PaperBroker(starting_equity=10_000.0)
    b.on_trade(_ev(points=10.0, dollars=200.0))
    b.on_trade(_ev(fill="2026-02-10T10:00:00-05:00", points=-5.25, dollars=-105.0))
    assert b.total_points() == 4.75              # points stay points
    assert b.total_dollars() == 95.0             # dollars stay dollars
    assert b.equity() == 10_095.0


def test_duplicate_event_not_double_booked():
    b = PaperBroker()
    ev = _ev()
    b.on_trade(ev)
    b.on_trade(ev)                               # replay/restart duplicate
    assert len(b.trades) == 1 and b.total_dollars() == 200.0


def test_day_summary_rollup():
    b = PaperBroker()
    b.on_trade(_ev(dollars=200.0))
    b.on_trade(_ev(fill="2026-02-10T10:00:00-05:00", dollars=-50.0))
    b.on_trade(_ev(date="2026-02-11", fill="2026-02-11T09:30:00-05:00", dollars=300.0))
    d = b.day_summary("2026-02-10")
    assert (d.trades, d.wins, d.losses, d.dollars) == (2, 1, 1, 150.0)
    assert [x.date for x in b.daily()] == ["2026-02-10", "2026-02-11"]


def test_ledger_persistence_and_restore(tmp_path):
    path = tmp_path / "ledger.csv"
    b = PaperBroker(ledger_path=path, starting_equity=1_000.0)
    b.on_trade(_ev(dollars=200.0))
    b.on_trade(_ev(fill="2026-02-10T10:00:00-05:00", dollars=-50.0))
    assert path.exists()
    # restart: restore from disk, totals identical, dedup intact
    r = PaperBroker.restore(path, starting_equity=1_000.0)
    assert r.total_dollars() == 150.0 and r.equity() == 1_150.0
    r.on_trade(_ev(dollars=999.0))               # same (date, fill) → still deduped
    assert r.total_dollars() == 150.0


def test_reconcile_against_batch():
    b = PaperBroker()
    b.on_trade(_ev(dollars=200.0))
    b.on_trade(_ev(fill="2026-02-10T10:00:00-05:00", dollars=-50.0))
    ok = b.reconcile([("2026-02-10", "2026-02-10T09:35:00-05:00", 200),
                      ("2026-02-10", "2026-02-10T10:00:00-05:00", -50)])
    assert ok["match"] and not ok["missing"] and not ok["unexpected"]
    bad = b.reconcile([("2026-02-10", "2026-02-10T09:35:00-05:00", 200),
                       ("2026-02-10", "2026-02-10T11:00:00-05:00", 75)])
    assert not bad["match"]
    assert bad["missing"] == [("2026-02-10", "2026-02-10T11:00:00-05:00", 75)]
    assert bad["unexpected"] == [("2026-02-10", "2026-02-10T10:00:00-05:00", -50)]


def test_ledger_persists_full_trade_and_restore_is_verbatim(tmp_path):
    path = tmp_path / "ledger.csv"
    b = PaperBroker(ledger_path=path)
    ev = _ev(dollars=200.0)
    b.on_trade(ev)
    r = PaperBroker.restore(path).trades[0]
    # nothing fabricated on restore: audit-critical fields come back verbatim
    assert (r.trigger_ts, r.stop_initial, r.target_level) == \
           (ev.trigger_ts, ev.stop_initial, ev.target_level)
    assert (r.entry, r.exit_price, r.dollars, r.book) == \
           (ev.entry, ev.exit_price, ev.dollars, ev.book)


def test_restore_handles_missing_target_level(tmp_path):
    path = tmp_path / "ledger.csv"
    b = PaperBroker(ledger_path=path)
    ev = _ev(dollars=50.0)
    b.on_trade(TradeEvent(**{**ev.__dict__, "target_level": None}))
    assert PaperBroker.restore(path).trades[0].target_level is None
