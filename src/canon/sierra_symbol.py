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

Scope: resolver + roll watcher + alert text, all pure/offline-testable. The live feed re-point
and the live roll TAG are wired in the canon-lane loop (src/live/route_b.py, run by
scripts/canon_run.py) — see docs/LIVE-STACK.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

# CME month codes; NQ trades the quarterly cycle only.
_MONTH_CODE = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
               7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"}
_QUARTERLY = (3, 6, 9, 12)          # Mar / Jun / Sep / Dec

# The backtest consumed Databento NQ.v.0 — a VOLUME roll, not a calendar rule. Aligning to it is
# mandatory: a calendar rule rolls up to 6 sessions EARLY, putting live on the back month while
# the backtest still scored the front → gate A1 fails silently (docs/CONTRACT-ROLL-DATES.md).
# OBSERVED volume-roll dates (first day on the new contract), keyed by the OUTGOING contract's
# (year, month) — these are config constants from that table, not a rule:
KNOWN_ROLL_DATES: dict[tuple[int, int], date] = {
    (2025, 6): date(2025, 6, 18),    # NQM25 -> NQU25  (Wed, 2 before expiry)
    (2025, 9): date(2025, 9, 18),    # NQU25 -> NQZ25  (Thu, 1 before — the one exception)
    (2025, 12): date(2025, 12, 17),  # NQZ25 -> NQH26  (Wed, 2 before)
    (2026, 3): date(2026, 3, 18),    # NQH26 -> NQM26  (Wed, 2 before)
    (2026, 6): date(2026, 6, 17),    # NQM26 -> NQU26  (Wed, 2 before)
    (2026, 9): date(2026, 9, 16),    # NQU26 -> NQZ26  (Wed, 2 before) — next roll, paper window
}
# Forward rule for quarters beyond the table: the observed pattern is the WEDNESDAY 2 calendar
# days before the 3rd-Friday expiry (4 of 5 rolls). Pin new observed dates into KNOWN as they land.
VOLUME_ROLL_DAYS_BEFORE = 2


def third_friday(year: int, month: int) -> date:
    """The 3rd Friday of a month — CME equity-index expiry day."""
    first = date(year, month, 1)
    first_friday = 1 + (4 - first.weekday()) % 7      # weekday: Mon=0 .. Fri=4 .. Sun=6
    return date(year, month, first_friday + 14)


def roll_date(year: int, month: int) -> date:
    """The day the front month rolls OUT of the (year, month) quarterly contract — the Databento
    VOLUME roll. Uses the observed date from KNOWN_ROLL_DATES when available, else the forward
    pattern (Wednesday, VOLUME_ROLL_DAYS_BEFORE calendar days before the 3rd-Friday expiry)."""
    known = KNOWN_ROLL_DATES.get((year, month))
    if known is not None:
        return known
    return third_friday(year, month) - timedelta(days=VOLUME_ROLL_DAYS_BEFORE)


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
    """Path to Sierra's market-depth file for the front month on `d`. `.depth` files are
    per-day; `day` defaults to `d`'s date (pass an explicit YYYY-MM-DD for a stored day).

    Sierra's depth-file naming varies BY BOX and does not necessarily match the .scid's
    own naming on the same install — Pat's VPS (SC build 2930, Rithmic) writes
    `NQU26-CME.scid` but `NQU6.CME.2026-07-24.depth` (single-digit year, dot separator;
    found on-box 2026-07-26). So instead of assuming one pattern, build the known naming
    variants and pick by evidence: the day's file that EXISTS wins; failing that, the
    variant with existing sibling days in MarketDepthData (the box's demonstrated
    convention — tonight's file will appear under it); failing that, the default pattern."""
    from pathlib import Path
    day = str(_as_date(day if day is not None else d))
    contract = front_month_symbol(d, root)              # e.g. NQU26
    single = contract[:-2] + contract[-1]               # e.g. NQU6 (single-digit year)
    tag = suffix.lstrip("-.")                           # e.g. CME
    stems = []                                          # ordered, deduped naming variants
    for s in (f"{contract}{suffix}", f"{single}.{tag}", f"{contract}.{tag}",
              f"{single}-{tag}"):
        if s not in stems:
            stems.append(s)
    mdd = Path(data_dir) / "MarketDepthData"
    candidates = [mdd / f"{s}.{day}.depth" for s in stems]
    for c in candidates:
        if c.exists():
            return c
    for s, c in zip(stems, candidates):                 # convention shown by sibling days
        if any(mdd.glob(f"{s}.*.depth")):
            return c
    return candidates[0]


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


@dataclass
class RollTagger:
    """Per-bar contract tag — the LIVE twin of `src/engine/data.tag_rolls`.

    `tag(ts)` returns `{contract, roll}` for a bar at `ts`: `roll=True` on the FIRST bar whose
    front-month contract differs from the previous bar's (the first bar is never a roll, exactly
    like `tag_rolls`). This is diagnostic, NOT corrective: the backtest only TAGS rolls (the tag
    is consumed solely by `diagnostics.py` to partition roll-day trades) and its level/trade
    logic SPANS the gap on the unspliced continuous series — so the live buffers must span too,
    or live diverges from the validated book. The tag lets the journal/gate partition roll-day
    trades the same way and lets §E reset the promotion clock across a roll."""
    root: str = "NQ"
    _last: str | None = None

    def tag(self, ts) -> dict:
        sym = front_month_symbol(ts, self.root)
        roll = self._last is not None and sym != self._last
        self._last = sym
        return {"contract": sym, "roll": roll}
