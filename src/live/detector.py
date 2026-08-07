"""Live trigger detection (Phase 4 Stage 8) — the real detector, streamed.

Wraps the REAL `detect_triggers` (src/engine/triggers.py) for per-bar use — never a
re-implementation, so live detection is the backtest detector by construction. The
underlying detector is already prefix-safe (a forming candle is never evaluated as
closed — spec-1 §3), and MTF arbitration is per shared close-time, so a later trigger
can never change an earlier one. That makes incremental detection sound: on each closed
bar, re-detect only a short TAIL window (long enough to cover every entry timeframe's
newly-closed candle) and let the Vault's identity dedup absorb the overlap between
consecutive calls.

Band: detection runs only inside DETECT_BAND (07:45-11:00 ET) — the SAME band the
frozen trigger caches were built with (scripts/_detect_marjul.py) — so streamed
detection is comparable to the cached reference row-for-row. `unclassified` patterns
are dropped exactly like the parity harness does.

Cost (measured on real data): ~0.8s per tail call vs ~9.4s for a full-window re-scan —
comfortably inside the 60s/bar live budget.

Verification: scripts/detector_parity.py streams real sessions bar-by-bar and asserts
the union of per-bar detections equals the frozen cache for those days.
"""

from __future__ import annotations

from datetime import time as dtime

import pandas as pd

from src.engine.triggers import Trigger, detect_triggers
from src.live.feed import Bar

DETECT_BAND = (dtime(7, 45), dtime(11, 0))   # == the frozen caches' band
TAIL_MINUTES = 10                            # covers the largest entry TF's candle (5m)
                                             # with slack for either labeling convention


class LiveDetector:
    """Per-bar trigger detection over a streamed 1m frame.

    Usage in the live loop (runner owns the bar history):
        det = LiveDetector()
        for bar in feed.stream():
            events = vault.on_bar(bar)            # vault buffers the bar
            new = det.on_bar(df_so_far, bar)      # detect on the same history
            if new:
                vault.add_triggers(new)
    """

    def __init__(self, band: tuple[dtime, dtime] = DETECT_BAND,
                 tail_minutes: int = TAIL_MINUTES, cfg=None,
                 detect_fn=detect_triggers):
        self.band = band
        self.tail = pd.Timedelta(minutes=tail_minutes)
        self.cfg = cfg                        # None -> detector loads its own config
        self._detect = detect_fn
        self.calls = 0

    def wants(self, ts: pd.Timestamp) -> bool:
        """Is this bar inside (or trailing-close to) the detection band?"""
        tod = ts.time()
        if tod < self.band[0]:
            return False
        return (ts - self.tail).time() <= self.band[1] or tod <= self.band[1]

    def on_bar(self, df_1m: pd.DataFrame, bar: Bar) -> list[Trigger]:
        """Detect triggers newly decidable at this closed bar. Returns possibly-
        overlapping results across consecutive calls — feed them to
        `vault.add_triggers`, whose identity dedup makes the overlap harmless."""
        ts = pd.Timestamp(bar.ts_event)
        if not self.wants(ts):
            return []
        day = ts.strftime("%Y-%m-%d")
        lo = max(pd.Timestamp(f"{day} {self.band[0]}", tz=ts.tz), ts - self.tail)
        hi = min(pd.Timestamp(f"{day} {self.band[1]}", tz=ts.tz), ts)
        if lo > hi:
            return []
        self.calls += 1
        trigs = (self._detect(df_1m, start=lo, end=hi) if self.cfg is None
                 else self._detect(df_1m, self.cfg, start=lo, end=hi))
        return [t for t in trigs if t.pattern != "unclassified"]
