"""Front-month contract resolution + roll detection for the Route-B file-tail path.

The Route-B data path (src/canon/sierra_files.py) tails ONE Sierra `.scid`/`.depth` file by
path. It has no notion of *which* contract is front — but the front month rolls on the CME
quarterly cycle, and NQU26 (Sep 2026) rolls during the intended paper window. When Sierra
rolls, it starts writing the NEXT contract's file (e.g. `NQZ26-CME.scid`) and stops appending
to the old one; a feed pinned to the old path just goes silently stale. This module resolves
the active front-month symbol/file for a date and detects the roll so the tail loop can
re-point the feed and alert a human.

ROLL RULE (from the box's Rollover Method): **4 calendar days before the 3rd Friday of the
contract month.** NQ trades the quarterly cycle H(Mar)/M(Jun)/U(Sep)/Z(Dec). On the roll day
the front contract becomes the next quarter; prices are NOT back-adjusted, so a gap appears
across the roll (the reason the backtest tags rolls — src/engine/data.tag_rolls).

Scope: resolver + roll watcher + alert text, all pure/offline-testable. Re-pointing the live
feed and adding a live roll TAG to the ingestor's rolling buffers wait on the live file-tail
adapter (scripts/paper_run.stream_live, not yet built) — see docs/LIVE-STACK.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

# CME month codes; NQ trades the quarterly cycle only.
_MONTH_CODE = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
               7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"}
_QUARTERLY = (3, 6, 9, 12)          # Mar / Jun / Sep / Dec
ROLL_DAYS_BEFORE = 4                # "4 calendar days before the 3rd Friday" (box ruling)


def third_friday(year: int, month: int) -> date:
    """The 3rd Friday of a month — CME equity-index expiry day."""
    first = date(year, month, 1)
    first_friday = 1 + (4 - first.weekday()) % 7      # weekday: Mon=0 .. Fri=4 .. Sun=6
    return date(year, month, first_friday + 14)


def roll_date(year: int, month: int) -> date:
    """The day the front month rolls OUT of the (year, month) quarterly contract:
    ROLL_DAYS_BEFORE calendar days before that contract's 3rd-Friday expiry."""
    return third_friday(year, month) - timedelta(days=ROLL_DAYS_BEFORE)


def _as_date(d) -> date:
    if isinstance(d, date) and not isinstance(d, pd.Timestamp):
        return d
    return pd.Timestamp(d).date()


def front_contract(d) -> tuple[int, int]:
    """(year, month) of the front-month quarterly contract active on calendar date `d`.

    A quarterly contract C is front until its roll day; on and after `roll_date(C)` the front
    is the next quarter. So front(d) = the earliest quarterly whose roll day is strictly after
    `d`. On the roll day itself we are already in the NEW contract (strict `>`)."""
    d = _as_date(d)
    for year in (d.year, d.year + 1):                 # +1 covers a Dec-roll into next Mar
        for month in _QUARTERLY:
            if roll_date(year, month) > d:
                return (year, month)
    raise RuntimeError(f"could not resolve front contract for {d}")   # unreachable


def front_month_symbol(d, root: str = "NQ") -> str:
    """Front-month trading symbol on date `d`, e.g. 'NQU26'. Use root 'MNQ' for the micro
    (READ NQ / ROUTE MNQ — the data feed is NQ, orders route MNQ; LIVE-STACK Step 6)."""
    year, month = front_contract(d)
    return f"{root}{_MONTH_CODE[month]}{year % 100:02d}"


def is_roll_day(d, root: str = "NQ") -> bool:
    """True if `d` is a day the front month changes vs the day before (the roll boundary)."""
    d = _as_date(d)
    return front_month_symbol(d, root) != front_month_symbol(d - timedelta(days=1), root)


def next_roll(d) -> tuple[date, str, str]:
    """(roll_day, from_symbol, to_symbol) for the NEXT roll on/after `d`. `from_symbol` is
    today's front; `to_symbol` is what it becomes. Lets an operator see the switch coming."""
    d0 = _as_date(d)
    cur = front_month_symbol(d0)
    probe = d0
    for _ in range(400):                              # < 400 days to the next quarterly roll
        probe += timedelta(days=1)
        if front_month_symbol(probe) != cur:
            return (probe, cur, front_month_symbol(probe))
    raise RuntimeError(f"no roll found within a year of {d0}")   # unreachable


# --------------------------------------------------------------------------- file resolution
def resolve_scid_path(data_dir, d, root: str = "NQ", suffix: str = "-CME"):
    """Path to Sierra's intraday file for the front month on `d`, e.g.
    <data_dir>/NQU26-CME.scid. `suffix` is the exchange/service tag Sierra appends (box: -CME)."""
    from pathlib import Path
    return Path(data_dir) / f"{front_month_symbol(d, root)}{suffix}.scid"


def resolve_depth_path(data_dir, d, day=None, root: str = "NQ", suffix: str = "-CME"):
    """Path to Sierra's market-depth file for the front month on `d`, e.g.
    <data_dir>/MarketDepthData/NQU26-CME.2026-07-27.depth. `.depth` files are per-day; `day`
    defaults to `d`'s date (pass an explicit YYYY-MM-DD to target a stored day)."""
    from pathlib import Path
    day = str(_as_date(day if day is not None else d))
    return Path(data_dir) / "MarketDepthData" / f"{front_month_symbol(d, root)}{suffix}.{day}.depth"


# --------------------------------------------------------------------------- roll watcher
@dataclass
class RollEvent:
    roll_day: str            # the date the roll was observed (YYYY-MM-DD)
    from_symbol: str
    to_symbol: str


class RollWatcher:
    """Detects a front-month roll as the tail loop advances. Call `check(now)` each session
    (or each poll); it returns a RollEvent exactly once, on the first observation that the
    front symbol changed, else None. The live tail wires this to (a) re-point SierraFileFeed
    at the new contract's files and (b) fire `format_roll_alert` over Telegram. Because the
    roll gaps prices, the operator MUST also know the feature buffers span the gap until they
    age out — flagged for the buffer roll-tag deferred to the live-adapter build."""

    def __init__(self, root: str = "NQ", start=None):
        self.root = root
        self.current: str | None = front_month_symbol(start, root) if start is not None else None

    def check(self, now) -> RollEvent | None:
        sym = front_month_symbol(now, self.root)
        if self.current is None:                       # first observation seeds, no event
            self.current = sym
            return None
        if sym == self.current:
            return None
        ev = RollEvent(roll_day=str(_as_date(now)), from_symbol=self.current, to_symbol=sym)
        self.current = sym
        return ev


def format_roll_alert(ev: RollEvent) -> str:
    """Loud, human-facing roll alert for Telegram / the run log."""
    return (f"🔁 CONTRACT ROLL {ev.roll_day}: front month {ev.from_symbol} → {ev.to_symbol}. "
            f"Route-B feed must re-point at the new .scid/.depth files. Prices gap across the "
            f"roll (unspliced) — multi-day levels/warmup buffers span the gap until they age "
            f"out; verify the first post-roll session before trusting cross-roll levels.")
