"""Tests for the two hardened assertions in scripts/sierra_pin_check.py (Angus checks #1/#2).

Offline against SYNTHETIC .scid/.depth. These prove the loud FAILs fire when order flow is
blind or the ladder is short, and that a healthy sample still PASSes — they do NOT stand in
for the on-box run against real Sierra bytes (that is the pin gate itself)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

import pandas as pd

from src.canon.sierra_files import (
    DCMD_CLEAR,
    DCMD_SET_ASK,
    DCMD_SET_BID,
    write_depth,
    write_scid,
)

# load the script module by path (scripts/ is not a package)
_SPEC = importlib.util.spec_from_file_location(
    "sierra_pin_check", Path(__file__).resolve().parents[1] / "scripts" / "sierra_pin_check.py")
pin = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pin)

NY = "America/New_York"


def _ts(hms):
    return pd.Timestamp(f"2026-03-17 {hms}", tz=NY).tz_convert("UTC")


# --------------------------------------------------------------------------- check #1 (.scid CVD)
def test_scid_all_zero_orderflow_fails_check1(tmp_path):
    p = tmp_path / "blind.scid"
    write_scid(p, [{"ts": _ts("08:00"), "close": 100.0, "total_volume": 500,
                    "bid_volume": 0, "ask_volume": 0},
                   {"ts": _ts("08:01"), "close": 100.5, "total_volume": 400,
                    "bid_volume": 0, "ask_volume": 0}])
    with pytest.raises(pin.OrderFlowFail) as ei:
        pin.check_scid(p)
    assert "CHECK #1" in str(ei.value) and "CVD" in str(ei.value)


def test_scid_one_sided_orderflow_fails_check1(tmp_path):
    p = tmp_path / "half.scid"
    write_scid(p, [{"ts": _ts("08:00"), "close": 100.0, "total_volume": 500,
                    "bid_volume": 0, "ask_volume": 500}])         # ask only, bid all-zero
    with pytest.raises(pin.OrderFlowFail):
        pin.check_scid(p)


def test_scid_healthy_orderflow_passes(tmp_path):
    p = tmp_path / "ok.scid"
    write_scid(p, [{"ts": _ts("08:00"), "close": 100.0, "total_volume": 500,
                    "bid_volume": 200, "ask_volume": 300},
                   {"ts": _ts("08:01"), "close": 100.5, "total_volume": 400,
                    "bid_volume": 250, "ask_volume": 150}])
    assert pin.check_scid(p) is True


# --------------------------------------------------------------------------- check #2 (.depth 10)
def _depth_ladder(path, levels: int):
    recs = [{"ts": _ts("08:00"), "command": DCMD_CLEAR}]
    for i in range(levels):
        recs.append({"ts": _ts("08:00"), "command": DCMD_SET_BID,
                     "price": 100.0 - 0.25 * i, "qty": 50 + i, "num_orders": 3})
        recs.append({"ts": _ts("08:00"), "command": DCMD_SET_ASK,
                     "price": 100.25 + 0.25 * i, "qty": 60 + i, "num_orders": 4})
    write_depth(path, recs)


def test_depth_five_levels_fails_check2_names_denali(tmp_path):
    p = tmp_path / "thin.depth"
    _depth_ladder(p, 5)
    with pytest.raises(pin.OrderFlowFail) as ei:
        pin.check_depth(p)
    msg = str(ei.value)
    assert "CHECK #2" in msg and "DENALI" in msg.upper()


def test_depth_ten_levels_passes(tmp_path):
    p = tmp_path / "full.depth"
    _depth_ladder(p, 10)
    assert pin.check_depth(p) is True


def test_depth_empty_book_fails_check2(tmp_path):
    p = tmp_path / "empty.depth"
    write_depth(p, [{"ts": _ts("08:00"), "command": DCMD_CLEAR}])
    with pytest.raises(pin.OrderFlowFail) as ei:
        pin.check_depth(p)
    assert "not subscribed" in str(ei.value)


# --------------------------------------------------------------------------- main() exit codes
def test_main_returns_1_on_orderflow_fail(tmp_path, capsys):
    p = tmp_path / "blind.scid"
    write_scid(p, [{"ts": _ts("08:00"), "close": 100.0, "total_volume": 500,
                    "bid_volume": 0, "ask_volume": 0}])
    rc = pin.main(["sierra_pin_check.py", str(p)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "order-flow / depth blind" in out          # NOT the layout-mismatch banner
