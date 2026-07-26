"""Tests for the Route-B front-month resolver + roll watcher (src/canon/sierra_symbol.py).

Pins the CME quarterly roll rule ("4 calendar days before the 3rd Friday") against the
NQU26→NQZ26 roll that lands in the Sep-2026 paper window."""
from __future__ import annotations

from datetime import date

import pandas as pd

from src.canon.sierra_symbol import (
    RollTagger,
    RollWatcher,
    format_roll_alert,
    front_contract,
    front_month_symbol,
    is_roll_day,
    next_roll,
    resolve_depth_path,
    resolve_scid_path,
    roll_date,
    third_friday,
)


def test_roll_date_sep_2026_is_the_volume_roll():
    assert third_friday(2026, 9) == date(2026, 9, 18)      # 3rd Friday of Sep 2026
    assert roll_date(2026, 9) == date(2026, 9, 16)         # Databento VOLUME roll (Wed, -2), from table


def test_front_month_around_the_sep_roll():
    # before the roll → still NQU26; on/after Sep 16 (the volume roll) → NQZ26
    assert front_month_symbol(date(2026, 9, 15)) == "NQU26"
    assert front_month_symbol(date(2026, 9, 16)) == "NQZ26"   # roll day is already the new one
    assert front_month_symbol(date(2026, 9, 18)) == "NQZ26"
    assert front_contract(date(2026, 9, 15)) == (2026, 9)
    assert front_contract(date(2026, 9, 16)) == (2026, 12)


def test_front_month_dec_roll_crosses_year():
    # Dec 2026 (Z26) not in the table -> forward rule: 3rd Fri Dec 18 2026, Wed -2 = Dec 16 -> H27
    assert roll_date(2026, 12) == date(2026, 12, 16)
    assert front_month_symbol(date(2026, 12, 15)) == "NQZ26"
    assert front_month_symbol(date(2026, 12, 16)) == "NQH27"


def test_micro_root_and_is_roll_day():
    assert front_month_symbol(date(2026, 9, 16), root="MNQ") == "MNQZ26"
    assert is_roll_day(date(2026, 9, 16)) is True
    assert is_roll_day(date(2026, 9, 17)) is False


def test_next_roll_from_paper_window():
    roll_day, frm, to = next_roll(date(2026, 7, 25))
    assert roll_day == date(2026, 9, 16) and frm == "NQU26" and to == "NQZ26"


def test_resolve_paths():
    scid = resolve_scid_path("C:/SierraChart/Data", date(2026, 9, 15))
    assert scid.name == "NQU26-CME.scid"
    dep = resolve_depth_path("C:/SierraChart/Data", date(2026, 9, 16), day="2026-09-16")
    assert dep.name == "NQZ26-CME.2026-09-16.depth" and dep.parent.name == "MarketDepthData"


def test_roll_watcher_fires_once_on_roll():
    w = RollWatcher(start=date(2026, 9, 15))
    assert w.check(date(2026, 9, 15)) is None              # same day, no event
    ev = w.check(date(2026, 9, 16))                        # crosses the roll
    assert ev is not None and ev.from_symbol == "NQU26" and ev.to_symbol == "NQZ26"
    assert w.check(date(2026, 9, 17)) is None              # already switched — no re-fire
    assert "NQU26 → NQZ26" in format_roll_alert(ev)


def test_roll_watcher_seeds_without_event():
    w = RollWatcher()                                      # no start → first check seeds
    assert w.check(pd.Timestamp("2026-09-13", tz="UTC")) is None
    assert w.current == "NQU26"


def test_roll_tagger_marks_first_post_roll_bar():
    """The live twin of tag_rolls: first bar is never a roll; roll=True once, on the first bar
    whose front-month contract differs from the previous bar's."""
    tg = RollTagger()
    d15 = pd.Timestamp("2026-09-15 12:00", tz="America/New_York")
    d16 = pd.Timestamp("2026-09-16 12:00", tz="America/New_York")
    a = tg.tag(d15)
    assert a == {"contract": "NQU26", "roll": False}       # first bar, never a roll
    assert tg.tag(d15) == {"contract": "NQU26", "roll": False}   # same contract, no roll
    b = tg.tag(d16)
    assert b == {"contract": "NQZ26", "roll": True}         # crossed the roll -> tagged once
    assert tg.tag(d16) == {"contract": "NQZ26", "roll": False}   # already rolled, no re-tag
