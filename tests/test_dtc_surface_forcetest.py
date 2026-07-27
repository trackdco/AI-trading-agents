"""The on-box surface force-test harness, proven against the mock Sierra first.

scripts/dtc_surface_forcetest.py is what Pat runs ON THE BOX for the A7/B7/B8 gate
evidence — so the harness itself must be verified here: every check sequence runs against
MockDTCServer and passes, and the safety refusals (non-SIM account, non-micros symbol)
actually refuse. The mock's positions are canned (always 2), so the one check that needs
a real position ledger — "position reads back FLAT" — is asserted to report that read-back
honestly rather than pass; on the box it must pass.
"""
from __future__ import annotations

import socket

from scripts.dtc_surface_forcetest import main, run_fill, run_resting
from src.desk.dtc_broker import DTCBroker
from src.desk.dtc_client import DTCClient, DTCConfig
from tests.test_dtc_client import MockDTCServer


def _broker(server):
    cfg = DTCConfig(host="127.0.0.1", port=server.port, username="u", password="p",
                    trade_account="Sim1")
    c = DTCClient(cfg=cfg, connector=lambda h, p: socket.create_connection(
        (h, server.port), timeout=2.0))
    assert c.connect()
    return DTCBroker(client=c, symbol="MNQU26-CME", account="Sim1", pump_rounds=4), c


def test_resting_sequence_all_checks_pass_on_the_mock():
    s = MockDTCServer(order_mode="none")               # far-from-market: entry rests
    try:
        b, c = _broker(s)
        rows = run_resting(b, c, account="Sim1", entry=23000.0, stop=22990.0)
        assert [r.label for r in rows if not r.ok] == []
        assert len(rows) == 7                      # 5 checks + 2 raw-state diagnostic rows
        # and the bracket really is dead server-side
        assert len(s.cancelled) >= 1
    finally:
        s.stop()


def test_fill_sequence_all_order_checks_pass_on_the_mock():
    s = MockDTCServer(order_mode="fill_entry")         # entry fills, stop child rests
    try:
        b, c = _broker(s)
        rows = run_fill(b, c, account="Sim1", entry=24870.0, stop=24820.0)
        by = {r.label: r for r in rows}
        flat = by.pop("flatten: position reads back FLAT")
        assert [r.label for r in by.values() if not r.ok] == []
        # the mock's position ledger is canned at 2 — the harness must REPORT that
        # read-back, not paper over it. On the box this row is required to pass.
        assert not flat.ok and "position=2" in flat.detail
    finally:
        s.stop()


def test_refuses_non_sim_account_and_non_micros_symbol(capsys):
    assert main(["--account", "LUCID-EVAL-50K", "--symbol", "MNQU26-CME",
                 "--entry", "1", "--stop", "0.5"]) == 2
    assert "REFUSED" in capsys.readouterr().out
    assert main(["--account", "Sim1", "--symbol", "NQU26-CME",
                 "--entry", "1", "--stop", "0.5"]) == 2
    assert "micros" in capsys.readouterr().out
    assert main(["--account", "Sim1", "--symbol", "MNQU26-CME",
                 "--entry", "1", "--stop", "2"]) == 2   # stop above entry
