"""Pre-open news blackout — a deterministic table lookup, not a judgement.

ANGUS RULING 2026-07-26:
  * "it should not be trading from 8-8:30 when there is high impact news at 8:30."
    -> block NY entries that would be OPEN GOING INTO a pre-open release. Entries AFTER
       the print are fine (measured: +$370 / 50% win on the 10 such trades — trading the
       reaction is not the problem, betting on the outcome is).
  * "anything that is considered high/medium should also be considered high, the mediums
    can stay as they are."
    -> an event NAME that carries impact=high ANYWHERE in the calendar is high EVERYWHERE.
       Names that are only ever medium stay medium and never trigger a blackout. This
       resolves the calendar's inconsistent tagging (Unemployment Claims is tagged medium
       on 19 of its 24 rows and high on 5) without hand-maintaining a regex list.
  * "lets focus on pre market for now" -> pre-09:30 releases only. Post-open (10:00 ISM /
    JOLTS, 14:00 FOMC) is a separate ruling, deliberately out of scope here.

NO LLM, no discretion, no free parameter. The blackout window is not tuned: it runs from
the session open to the release, and the session structure bounds it (the NY pre window
opens at 08:00, the prints land at 08:30). "Before the release" and "within 30-60 min
before" select the identical trade set — see docs/FINDING-canon-has-no-news-blackout.md §6.

    from src.canon.news_gate import NewsGate
    gate = NewsGate.load()
    gate.blackout_until(date(2026, 3, 5))       # -> Timestamp('2026-03-05 08:30') or None
    gate.blocks(ts_et)                          # -> bool, the trade-time question
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from datetime import time as _time
from pathlib import Path

import pandas as pd

CALENDARS = ("config/news_calendar_hist.csv", "config/news_calendar.csv")
DAILY_DIR = Path("data/reference/news_daily")   # sentinel snapshots (scripts/news_daily_agent.py)
PRE_OPEN_CUTOFF = _time(9, 30)      # "pre-market" = anything printing before the cash open
DAY_MARKER = _time(0, 0)            # 00:00 rows are all-day markers (holidays, OPEC), not prints


def _load_raw(paths=CALENDARS) -> pd.DataFrame:
    frames = []
    daily = sorted(DAILY_DIR.glob("news_*.csv")) if DAILY_DIR.exists() else []
    for p in list(paths) + daily:
        if not Path(p).exists():
            continue
        d = pd.read_csv(p, comment="#")
        d.columns = [c.strip() for c in d.columns]
        frames.append(d)
    if not frames:
        raise FileNotFoundError(f"no calendar found among {paths}")
    c = pd.concat(frames, ignore_index=True)
    c["ts"] = pd.to_datetime(c["datetime_ET"], errors="coerce")
    c["event"] = c["event"].astype(str).str.strip()
    c["impact"] = c["impact"].astype(str).str.strip().str.lower()
    # daily sentinel rows are appended last -> keep the FRESHEST row per (minute, event)
    c = c.dropna(subset=["ts"]).drop_duplicates(subset=["ts", "event"], keep="last")
    return c.sort_values("ts").reset_index(drop=True)


def ever_high(cal: pd.DataFrame) -> set[str]:
    """The Angus promotion rule: a NAME tagged high anywhere is high everywhere."""
    return set(cal.loc[cal["impact"] == "high", "event"].unique())


@dataclass(frozen=True)
class NewsGate:
    #: date -> earliest promoted-high release before 09:30 ET that day
    releases: dict
    #: names promoted to high, for journalling and audit
    promoted: frozenset
    #: last calendar date present — past this the gate is BLIND, see `stale_after`
    stale_after: pd.Timestamp

    @classmethod
    def load(cls, paths=CALENDARS) -> "NewsGate":
        cal = _load_raw(paths)
        names = ever_high(cal)
        hi = cal[cal["event"].isin(names)
                 & (cal["ts"].dt.time < PRE_OPEN_CUTOFF)
                 & (cal["ts"].dt.time != DAY_MARKER)]
        first = hi.groupby(hi["ts"].dt.date)["ts"].min()
        return cls(releases=dict(first), promoted=frozenset(names),
                   stale_after=cal["ts"].max())

    # ---- the two questions the trade path asks -------------------------------
    def blackout_until(self, day: _date) -> pd.Timestamp | None:
        """The timestamp entries are blocked up to on `day`, or None if the day is clear."""
        return self.releases.get(day)

    def blocks(self, ts_et: pd.Timestamp) -> bool:
        """True if an entry at this ET timestamp would be open going into a pre-open release.

        Blocks strictly BEFORE the release. An entry at or after the print is allowed —
        that is the measured refinement over the champion's whole-pre-market rule.
        """
        rel = self.releases.get(ts_et.date())
        return rel is not None and ts_et < rel

    def snapshot_present(self, day: _date) -> bool:
        """True if the sentinel wrote a snapshot for `day`. FAIL-CLOSED CONTRACT (Angus
        2026-07-26): no snapshot for today -> block ALL pre-09:30 entries. A missing board
        is a red-folder day, never "no news"."""
        return (DAILY_DIR / f"news_{day}.csv").exists()

    def is_stale(self, day: _date) -> bool:
        """A calendar that has run out cannot clear a day. Callers must FAIL CLOSED:
        missing required context -> stand down (Tier-2 rule 5), never assume 'no news'."""
        return pd.Timestamp(day) > self.stale_after.normalize()


if __name__ == "__main__":                                   # quick audit
    g = NewsGate.load()
    med = sorted(set(_load_raw()["event"]) - g.promoted)
    print(f"promoted to HIGH ({len(g.promoted)} names, blackout triggers):")
    for n in sorted(g.promoted):
        print(f"   {n}")
    print(f"\nleft as MEDIUM ({len(med)} names, never trigger):")
    for n in med:
        print(f"   {n}")
    print(f"\nblackout days on file: {len(g.releases)}")
    print(f"calendar runs to {g.stale_after}  ->  STALE for anything after this")
