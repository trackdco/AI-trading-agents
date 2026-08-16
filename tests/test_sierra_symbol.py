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


def test_resolve_paths(tmp_path):
    """HERMETIC on purpose: this used to point at the literal C:/SierraChart/Data, which
    EXISTS on the box and holds both naming variants — the most-recently-written file won
    (by design) and the hardcoded assertion failed there while passing everywhere the
    path is absent (found during the 2026-08-01 R13 certification). An empty tmp dir
    pins the DEFAULT-pattern fallback deterministically on every machine; the by-evidence
    behavior is pinned separately by test_resolve_depth_path_detects_the_box_naming."""
    scid = resolve_scid_path(tmp_path, date(2026, 9, 15))
    assert scid.name == "NQU26-CME.scid"
    dep = resolve_depth_path(tmp_path, date(2026, 9, 16), day="2026-09-16")
    assert dep.name == "NQZ26-CME.2026-09-16.depth" and dep.parent.name == "MarketDepthData"


def test_resolve_depth_path_detects_the_box_naming(tmp_path):
    """Pat's VPS names depth files NQU6.CME.<date>.depth (single-digit year, dot separator)
    while the .scid on the SAME box is NQU26-CME.scid (on-box finding 2026-07-26). The
    resolver must pick by evidence: exact existing file first; else the variant with
    existing sibling days (tonight's file will appear under the box's convention); else
    the default pattern."""
    mdd = tmp_path / "MarketDepthData"
    mdd.mkdir()
    # 1) exact file for the day exists under the box convention -> picked
    (mdd / "NQU6.CME.2026-07-24.depth").write_bytes(b"")
    got = resolve_depth_path(tmp_path, date(2026, 7, 24), day="2026-07-24")
    assert got.name == "NQU6.CME.2026-07-24.depth"
    # 2) day's file absent, but a sibling day shows the convention -> same stem, new day
    got = resolve_depth_path(tmp_path, date(2026, 7, 26), day="2026-07-26")
    assert got.name == "NQU6.CME.2026-07-26.depth"
    # 3) empty dir -> the default pattern
    for f in mdd.iterdir():
        f.unlink()
    got = resolve_depth_path(tmp_path, date(2026, 7, 26), day="2026-07-26")
    assert got.name == "NQU26-CME.2026-07-26.depth"


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


def test_resolve_scid_path_prefers_the_freshest_existing_variant(tmp_path):
    """The box's FOURTH naming casualty (2026-07-27 pre-London): a re-opened chart started
    writing NQU6.CME.scid while the resolver pointed at the months-old NQU26-CME.scid,
    frozen at Friday. The LIVE file is whichever Sierra is writing NOW — pick the freshest
    existing variant, never let a stale twin shadow it."""
    import os
    import time
    old = tmp_path / "NQU26-CME.scid"
    new = tmp_path / "NQU6.CME.scid"
    old.write_bytes(b"x" * 10)
    new.write_bytes(b"y" * 10)
    past = time.time() - 3 * 86400
    os.utime(old, (past, past))                          # old naming: last written Friday
    got = resolve_scid_path(tmp_path, date(2026, 7, 27))
    assert got.name == "NQU6.CME.scid"

    os.utime(old, None)                                  # old naming freshens again -> wins
    os.utime(new, (past, past))
    assert resolve_scid_path(tmp_path, date(2026, 7, 27)).name == "NQU26-CME.scid"

    # nothing exists (fresh box): fall back to the default pattern
    empty = tmp_path / "empty"
    empty.mkdir()
    assert resolve_scid_path(empty, date(2026, 7, 27)).name == "NQU26-CME.scid"
