"""Feed-lag measurement + forcetest account guard — both found live on the box, pre-London.

1. measure_feed_lag against a freshly BACKFILLED file reported a months-long 'median': the
   first poll ingests the whole file and every backlog bar is timed against the wall clock.
   The fix primes that catch-up read OUTSIDE the measured window; only appends observed
   after priming are live samples.
2. The box's paper account is Rithmic-style (LFE050-9YSC047M-TEST001) — 'test', not 'sim'.
   The forcetest guard accepts either non-production tag and still refuses a funded-looking
   name.
"""
from __future__ import annotations

import pandas as pd

from scripts.dtc_surface_forcetest import main as forcetest_main
from scripts.sierra_parity_replay import measure_feed_lag
from src.canon.sierra_files import write_scid


def _hist_bars(n=5, day="2026-07-24"):
    return [{"ts": pd.Timestamp(f"{day} 14:{30 + i:02d}:00", tz="UTC"), "close": 100.0 + i,
             "total_volume": 10, "bid_volume": 4, "ask_volume": 6} for i in range(n)]


def test_backlog_bars_are_primed_out_of_the_lag_stats(tmp_path):
    scid = tmp_path / "NQU6.CME.scid"
    write_scid(scid, _hist_bars())
    s = measure_feed_lag(scid, None, seconds=1, flush_ms=1000,
                         journal=tmp_path / "lag.jsonl")
    # all bars are historical backlog -> primed out; nothing appended live during the window
    assert s["n"] == 0
    # and the journal holds no backlog rows either (sink attached only after priming)
    j = tmp_path / "lag.jsonl"
    assert not j.exists() or j.read_text().strip() == ""


def test_forcetest_guard_accepts_test_naming_refuses_funded_looking(capsys):
    # funded-looking name (no sim/test): refused before any network is touched
    rc = forcetest_main(["--account", "LFE050-9YSC047M", "--symbol", "MNQU6.CME",
                         "--entry", "28400", "--stop", "28380"])
    assert rc == 2 and "REFUSED" in capsys.readouterr().out
    # the box's real paper account passes the guard; the next stop is the DTC logon,
    # which fails fast here (nothing listens) — rc 1, NOT the guard's rc 2
    rc = forcetest_main(["--account", "LFE050-9YSC047M-TEST001", "--symbol", "MNQU6.CME",
                         "--entry", "28400", "--stop", "28380",
                         "--host", "127.0.0.1", "--port", "1"])
    assert rc == 1 and "LOGON FAILED" in capsys.readouterr().out
