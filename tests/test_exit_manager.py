"""Managed-exit decision tests (src/canon/exit_manager.py) — V8 partial/trail/BE + 3-min cut + EOD.

Unit-level, deterministic. These prove the RULES fire correctly; byte-exact fidelity to
engine.py's exit prices on the clean book is the separate A-section reconciliation (per the
module doc), not asserted here."""
from __future__ import annotations

import pandas as pd

from src.canon.exit_manager import ExitConfig, ManagedExit, ManagedPosition

NY = "America/New_York"


def _ts(hm, day="2026-03-17"):
    return pd.Timestamp(f"{day} {hm}", tz=NY)


def _pos(**kw):
    base = dict(direction="long", entry=18000.0, stop=17990.0, size=4,
                fill_time=_ts("08:30"), first_structure=18020.0)
    base.update(kw)
    return ManagedPosition(**base)


def test_be_move_for_premarket_fill_at_be_time():
    m, pos = ManagedExit(), _pos()
    # before be_time: no BE
    assert not any(a.kind == "move_be" for a in m.on_bar(pos, high=18005, low=17995, now=_ts("09:00")))
    a = m.on_bar(pos, high=18005, low=17995, now=_ts("09:29"))
    be = next(x for x in a if x.kind == "move_be")
    assert be.price == 18000.0 and pos.stop == 18000.0 and pos.be_done


def test_partial_at_first_structure_via_trade_through():
    m, pos = ManagedExit(), _pos()
    assert not any(a.kind == "partial" for a in m.on_bar(pos, high=18010, low=17995, now=_ts("08:35")))
    a = m.on_bar(pos, high=18021, low=18000, now=_ts("08:40"))   # trades through 18020
    p = next(x for x in a if x.kind == "partial")
    assert p.price == 18020.0 and p.pct == 0.5 and pos.partial_done


def test_trail_ratchets_only_favourably_after_partial():
    m = ManagedExit()
    pos = _pos()
    pos.partial_done = True                                       # runner phase
    a = m.on_bar(pos, high=18030, low=18010, now=_ts("08:45"), prior_5m_swing_low=18005.0)
    tr = next(x for x in a if x.kind == "trail_stop")
    assert tr.price == 18005.0 and pos.stop == 18005.0
    # a LOWER swing must NOT loosen the stop
    m.on_bar(pos, high=18030, low=18010, now=_ts("08:46"), prior_5m_swing_low=17999.0)
    assert pos.stop == 18005.0


def test_3min_cut_exits_at_market():
    m, pos = ManagedExit(), _pos(fill_time=_ts("08:30"))
    # 3 min in, adverse r_3 & fw_3 -> cut (marketable)
    a = m.on_bar(pos, high=18001, low=17995, now=_ts("08:33"), r_3=-0.2, fw_3=-14.0)
    cut = next(x for x in a if x.kind == "cut")
    assert cut.market is True and pos.closed


def test_3min_cut_not_triggered_when_not_adverse():
    m, pos = ManagedExit(), _pos()
    a = m.on_bar(pos, high=18010, low=17998, now=_ts("08:33"), r_3=0.1, fw_3=5.0)
    assert not any(x.kind == "cut" for x in a) and not pos.closed


def test_eod_flatten():
    m, pos = ManagedExit(), _pos(first_structure=None)
    a = m.on_bar(pos, high=18010, low=17990, now=_ts("15:59"))
    flat = next(x for x in a if x.kind == "flatten")
    assert flat.market is True and flat.reason == "eod" and pos.closed


def test_short_direction_partial_and_trail():
    m = ManagedExit()
    pos = _pos(direction="short", entry=18000.0, stop=18010.0, first_structure=17980.0)
    a = m.on_bar(pos, high=18000, low=17979, now=_ts("08:40"))    # trades down through 17980
    assert any(x.kind == "partial" for x in a) and pos.partial_done
    a2 = m.on_bar(pos, high=17990, low=17975, now=_ts("08:45"), prior_5m_swing_high=17995.0)
    tr = next(x for x in a2 if x.kind == "trail_stop")
    assert tr.price == 17995.0 and pos.stop == 17995.0           # short trails DOWN to swing high
