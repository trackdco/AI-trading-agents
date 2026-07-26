"""Tests for src/live/telegram.py — alerts + locked commands (Phase 4 Stage 5)."""


import pytest

from src.live.paper_broker import PaperBroker
from src.live.risk import RiskGuard, RiskLimits
from src.live.telegram import (
    MIN_KILL_OPERATORS,
    CommandListener,
    TelegramAlerts,
    TelegramConfig,
    fmt_trade,
    kill_switch_redundancy_warning,
    whoami,
)
from src.live.vault import TradeEvent


def _cfg(allowed=(111,)):
    return TelegramConfig(token="tok", chat_id="-500", allowed_user_ids=allowed)


def test_kill_switch_redundancy_warns_below_two_operators():
    assert kill_switch_redundancy_warning(_cfg(allowed=())) is not None       # zero operators
    one = kill_switch_redundancy_warning(_cfg(allowed=(111,)))
    assert one is not None and "SINGLE POINT OF FAILURE" in one               # one operator
    assert kill_switch_redundancy_warning(_cfg(allowed=(111, 222))) is None   # two -> ok
    assert MIN_KILL_OPERATORS == 2


def _ev(dollars=250.0):
    return TradeEvent(trade_date="2026-03-17", trigger_ts="2026-03-17T08:20:00-04:00",
                      direction="long", pattern="A", fill_ts="2026-03-17T08:26:00-04:00",
                      entry=25000.0, stop_initial=24990.0, target_level=25050.0,
                      exit_ts="2026-03-17T09:40:00-04:00", exit_price=25129.25,
                      exit_reason="target", points=129.25, dollars=dollars,
                      r_multiple=2.1, size=1.0, book="E4")


class FakeTransport:
    def __init__(self, updates=None, ok=True, raise_on=None):
        self.calls = []
        self.updates = updates or []
        self.ok = ok
        self.raise_on = raise_on

    def __call__(self, method, params, token, timeout=10.0):
        self.calls.append((method, params))
        if self.raise_on == method:
            raise ConnectionError("network down")
        if method == "getUpdates":
            return {"ok": True, "result": self.updates}
        return {"ok": self.ok}


def test_trade_alert_formats_points_and_dollars_separately():
    text = fmt_trade(_ev())
    assert "+129.25 pts" in text and "$+250" in text          # units rule holds
    assert "E4" in text and "target" in text and "08:26" in text


def test_on_trade_sends_and_reports_ok():
    tr = FakeTransport()
    tg = TelegramAlerts(_cfg(), transport=tr)
    assert tg.on_trade(_ev()) is True
    method, params = tr.calls[0]
    assert method == "sendMessage" and params["chat_id"] == "-500"
    assert "TRADE 2026-03-17" in params["text"]


def test_send_is_failsoft_on_exception_and_counts_failures():
    tg = TelegramAlerts(_cfg(), transport=FakeTransport(raise_on="sendMessage"))
    assert tg.on_halt("2026-03-18", "daily_loss_limit") is False   # no raise
    assert tg.failures == 1


def test_daily_summary_uses_broker_rollup():
    tr = FakeTransport()
    broker = PaperBroker(starting_equity=25_000.0)
    broker.on_trade(_ev(dollars=250.0))
    tg = TelegramAlerts(_cfg(), transport=tr)
    tg.daily_summary(broker, "2026-03-17")
    assert "1 trades (1W/0L)" in tr.calls[0][1]["text"]
    assert "$25,250" in tr.calls[0][1]["text"]


def _upd(uid, text, update_id=1):
    return {"update_id": update_id, "message": {"from": {"id": uid}, "text": text}}


def test_commands_locked_to_allowed_users(tmp_path):
    guard = RiskGuard(RiskLimits(kill_file=tmp_path / "KILL"))
    tr = FakeTransport(updates=[_upd(999, "/kill", 1), _upd(999, "/status", 2)])
    lis = CommandListener(_cfg(allowed=(111,)), guard, PaperBroker(), transport=tr)
    handled = lis.poll_once()
    assert handled == 0 and lis.ignored == 2
    assert not (tmp_path / "KILL").exists()                    # stranger can't kill
    assert all(m != "sendMessage" for m, _ in tr.calls)        # and gets NO reply


def test_kill_command_arms_the_switch_for_allowed_user(tmp_path):
    guard = RiskGuard(RiskLimits(kill_file=tmp_path / "KILL"))
    tr = FakeTransport(updates=[_upd(111, "/kill", 7)])
    lis = CommandListener(_cfg(allowed=(111,)), guard, PaperBroker(), transport=tr)
    assert lis.poll_once() == 1
    assert (tmp_path / "KILL").exists()                        # gate now stands down
    assert guard.gate("2026-03-18")["risk_reason"] == "kill_switch"
    assert any("ARMED" in p.get("text", "") for m, p in tr.calls if m == "sendMessage")


def test_status_command_replies_with_snapshot(tmp_path):
    guard = RiskGuard(RiskLimits(kill_file=tmp_path / "KILL"))
    broker = PaperBroker(starting_equity=25_000.0)
    ev = _ev()
    guard.on_trade(ev)
    broker.on_trade(ev)
    tr = FakeTransport(updates=[_upd(111, "/status", 3)])
    lis = CommandListener(_cfg(allowed=(111,)), guard, broker, transport=tr)
    assert lis.poll_once() == 1
    reply = [p["text"] for m, p in tr.calls if m == "sendMessage"][0]
    assert "killed=False" in reply and "$25,250" in reply and "2026-03-17" in reply


def test_poll_offset_advances_and_poll_is_failsoft(tmp_path):
    guard = RiskGuard(RiskLimits(kill_file=tmp_path / "KILL"))
    tr = FakeTransport(updates=[_upd(111, "/status", 41)])
    lis = CommandListener(_cfg(), guard, PaperBroker(), transport=tr)
    lis.poll_once()
    assert lis._offset == 42                                   # acked; not re-processed
    lis2 = CommandListener(_cfg(), guard, PaperBroker(),
                           transport=FakeTransport(raise_on="getUpdates"))
    assert lis2.poll_once() == 0                               # network down: no raise


def test_whoami_lists_unique_senders_with_ids():
    updates = [
        {"update_id": 1, "message": {"from": {"id": 7732530108, "first_name": "Pat",
                                              "username": "pat_t"},
                                     "chat": {"id": 7732530108}, "text": "hello"}},
        {"update_id": 2, "message": {"from": {"id": 7732530108, "first_name": "Pat",
                                              "username": "pat_t"},
                                     "chat": {"id": 7732530108}, "text": "again"}},
        {"update_id": 3, "message": {"from": {"id": 4242, "first_name": "Angus"},
                                     "chat": {"id": -5356314891}, "text": "/status"}},
        {"update_id": 4, "message": {}},                       # no sender: skipped
    ]
    rows = whoami(_cfg(), transport=FakeTransport(updates=updates))
    assert [r["user_id"] for r in rows] == [7732530108, 4242]  # deduped, in order
    assert rows[0]["username"] == "pat_t"
    assert rows[1] == {"user_id": 4242, "name": "Angus", "username": None,
                       "chat_id": -5356314891}


def test_config_from_env_requires_token(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)                                # no .env here
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with pytest.raises(ValueError):
        TelegramConfig.from_env()
    (tmp_path / ".env").write_text(
        "TELEGRAM_BOT_TOKEN=abc\nTELEGRAM_CHAT_ID=-5356314891\n"
        "TELEGRAM_ALLOWED_USER_IDS=111, 222\n")
    cfg = TelegramConfig.from_env()
    assert cfg.chat_id == "-5356314891" and cfg.allowed_user_ids == (111, 222)


# ------------------------------------------------------------------ KillFileListener (canon)
def test_killfile_listener_kill_writes_the_spine_kill_file(tmp_path):
    from src.live.telegram import KillFileListener
    kf = tmp_path / "KILL"
    tr = FakeTransport(updates=[_upd(111, "/kill", 5)])
    lis = KillFileListener(_cfg(allowed=(111,)), kf, transport=tr, clock=lambda: 1_000.0)
    assert lis.poll_once() == 1
    assert kf.exists() and "user 111" in kf.read_text()        # who + when journaled inside
    assert any("KILL file set" in p.get("text", "") for m, p in tr.calls if m == "sendMessage")


def test_killfile_listener_locked_to_operators(tmp_path):
    from src.live.telegram import KillFileListener
    kf = tmp_path / "KILL"
    tr = FakeTransport(updates=[_upd(999, "/kill", 1), _upd(999, "/status", 2)])
    lis = KillFileListener(_cfg(allowed=(111,)), kf, transport=tr)
    assert lis.poll_once() == 0 and lis.ignored == 2
    assert not kf.exists()                                     # stranger can't kill
    assert all(m != "sendMessage" for m, _ in tr.calls)        # and gets NO reply


def test_killfile_listener_status_reports_kill_state_and_runner_freshness(tmp_path):
    from src.live.telegram import KillFileListener
    kf, log = tmp_path / "KILL", tmp_path / "run.log"
    log.write_text("boot\n")
    fresh = log.stat().st_mtime + 10.0                         # clock 10s after last write
    tr = FakeTransport(updates=[_upd(111, "/status", 3)])
    lis = KillFileListener(_cfg(allowed=(111,)), kf, run_log=log, transport=tr,
                           clock=lambda: fresh)
    assert lis.poll_once() == 1
    reply = [p["text"] for m, p in tr.calls if m == "sendMessage"][0]
    assert "not killed" in reply and "10s ago" in reply and "STALE" not in reply

    kf.write_text("x")                                         # killed + stale runner
    tr2 = FakeTransport(updates=[_upd(111, "/status", 4)])
    lis2 = KillFileListener(_cfg(allowed=(111,)), kf, run_log=log, transport=tr2,
                            clock=lambda: fresh + 3600)
    assert lis2.poll_once() == 1
    reply2 = [p["text"] for m, p in tr2.calls if m == "sendMessage"][0]
    assert "KILLED" in reply2 and "STALE" in reply2


def test_killfile_listener_poll_is_failsoft(tmp_path):
    from src.live.telegram import KillFileListener
    lis = KillFileListener(_cfg(), tmp_path / "KILL",
                           transport=FakeTransport(raise_on="getUpdates"))
    assert lis.poll_once() == 0                                # network down: no raise
