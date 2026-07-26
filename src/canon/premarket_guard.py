"""PremarketGuard — the LIVE twin of arming-reference corrections 2 & 3, fail-closed.

The arming reference (+$55,989.81 / 383, ANGUS 2026-07-26) is built by
`scripts/canon_news_clean.py` as build_canon + THREE corrections: (1) the look-ahead-clean
`conf_PM`, (2) the pre-open news blackout, (3) the 09:55–10:00 dead-zone cut. The live
verdict source (`ScriptVerdictSource` → canon_mechanical.main) produces the UN-corrected
book — corrections 2 & 3 are size->0 vetoes applied after the fact — so the live loop must
apply the same two vetoes to each NY verdict at emit time, or live trades a book that was
never signed off. (Correction 1 lives in the FEEDING of conf_PM, not here.)

Plus the sentinel contract (ANGUS 2026-07-26, news_daily_agent): pre-09:30 entries require
TODAY'S news snapshot to exist. No snapshot -> block every pre-open entry — a missing
board is a red-folder day, never "no news". A stale calendar blocks the same way.

Scope: NY-session verdicts only — the batch applies the news gate to the NY frame only
(London 03:00–08:00 ET carries no covered releases; see canon_news_clean) and the dead
zone is inside the NY morning by construction. Every veto is a REASON string the caller
journals; None means the verdict may proceed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time as dtime

import pandas as pd

from src.canon.news_gate import NewsGate

NY = "America/New_York"
PRE_OPEN_END = dtime(9, 30)
DEAD_ZONES = ((595, 600),)              # ANGUS 2026-07-26: no entries 09:55–10:00


@dataclass
class PremarketGuard:
    gate: NewsGate = field(default_factory=NewsGate.load)
    dead_zones: tuple = DEAD_ZONES
    require_snapshot: bool = True       # live: True. Historical replays may relax it.

    def veto(self, v: dict) -> str | None:
        """Reason this verdict must NOT trade, or None. `v` is a relayed verdict dict
        (session/day/fill...). Unparseable fills fail closed."""
        if v.get("session") != "NY":
            return None
        try:
            et = pd.to_datetime(v["fill"], utc=True).tz_convert(NY)
        except (KeyError, TypeError, ValueError):
            return "unparseable_fill_ts"
        hm = et.hour * 60 + et.minute
        for z0, z1 in self.dead_zones:
            if z0 <= hm < z1:
                return "dead_zone"
        if et.time() < PRE_OPEN_END:
            day = et.date()
            if self.gate.is_stale(day):
                return "news_calendar_stale"
            if self.require_snapshot and not self.gate.snapshot_present(day):
                return "news_snapshot_missing"
            # the calendar stores NAIVE ET stamps; compare like the batch does
            if self.gate.blocks(et.tz_localize(None)):
                return "news_blackout"
        return None
