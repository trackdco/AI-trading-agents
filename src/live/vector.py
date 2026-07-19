"""Live pre-open regime switch (Phase 4 Stage 8) — the champion's E3/E4 pick from bars.

Batch reference: scripts/build_daytypes.py classifies each day pre-open (overnight
developing value area vs the prior day's completed value area), and
scripts/build_regime_vector.py rolls `imbal_share_20` over the last 20 classified days
INCLUDING the day itself — verified empirically (908/912 rows) and decision-relevant
(the E3/E4 switch flips on 71/912 days if the day's own overnight is excluded).

That timing fact shapes this module: the day's own classification needs its overnight
(18:00 -> 08:00 ET), which completes 14 hours AFTER the Vault's session roll. So the
policy answers `PENDING` (src.live.vault) until the first bar at/after 08:00, then
classifies the day from the SAME bar history the Vault trades on, updates the rolling
imbal series, and picks the book exactly like `book_for_day`:
imbal_share_20 >= 0.5 -> E4 (war book + tight-trigger filter), else E3. A day that
cannot be classified (no prior day in the buffer / short overnight) mirrors the batch
"unknown" handling: it gets no vector row, joins no rolling window, and trades E3 (the
same default `book_for_day` applies to a missing row).

The rolling window is seeded from output/amt_daytypes.csv (the committed history), and
the seed is trimmed to strictly-before the first live day so a replayed historical day
can never read its own batch answer — it must recompute it from bars.

Verification: scripts/vector_parity.py replays historical days and asserts this
policy's picks equal `book_for_day` on the frozen output/regime_vector.csv.
"""

from __future__ import annotations

from datetime import time as dtime
from pathlib import Path
from typing import Callable

import pandas as pd

from src.engine.data import _session_date
from src.engine.indicators import volume_profile
from src.live.champion import champion_books, e4_trigger_ok
from src.live.vault import PENDING

DAYTYPES_CSV = Path("output/amt_daytypes.csv")
_OPEN = dtime(8, 0)
_BOUNDARY = dtime(18, 0)
_MIN_ON_BARS = 60                      # same floor as build_daytypes
_PROFILE_ARGS = (0.25, 70)             # tick size, value-area percent — same as batch


def _any_trigger(t) -> bool:
    return True


class LiveVectorPolicy:
    """Session policy computing the champion's daily book switch from streamed bars.

    bars_provider: () -> DataFrame with BAR_COLS (the runner's accumulated history,
    warmup included). Called only when a decision is attempted, so the frame reflects
    everything up to the current bar.
    """

    def __init__(self, bars_provider: Callable[[], pd.DataFrame],
                 daytypes_csv: Path = DAYTYPES_CSV):
        self._bars = bars_provider
        self._books = champion_books()
        self._picks: dict[str, tuple | None] = {}      # day -> finalized pick
        self.shares: dict[str, float | None] = {}      # day -> imbal_share_20 (audit)
        self._imbal: list[tuple[str, float]] = []      # (day, 0/1) classified days
        self._seed_trimmed = False
        if Path(daytypes_csv).exists():
            dt = pd.read_csv(daytypes_csv)
            self._imbal = [(str(r.day), float(r.type == "imbalanced"))
                           for r in dt.itertuples() if r.type != "unknown"]

    def __call__(self, day: str):
        if not self._seed_trimmed:                     # a replayed day must never read
            self._imbal = [x for x in self._imbal if x[0] < day]   # its own batch row
            self._seed_trimmed = True
        if day in self._picks:
            return self._picks[day]
        bars = self._bars()
        sd = _session_date(bars["ts_event"], _BOUNDARY).astype(str)
        today = bars[sd == day]
        # ready only when the latest bar sits on the session's MORNING side at/after
        # 08:00 — evening bars (18:00+, prior calendar date) must stay PENDING, else
        # the day would be "classified" at 18:01 with zero overnight bars.
        if today.empty:
            return PENDING
        last = today["ts_event"].iloc[-1]
        if not (str(last.date()) == day and last.time() >= _OPEN):
            return PENDING                             # overnight not complete yet
        pick = self._decide(day, bars, sd, today)
        self._picks[day] = pick
        return pick

    # ---- internals ----------------------------------------------------------
    def _decide(self, day: str, bars: pd.DataFrame, sd: pd.Series,
                today: pd.DataFrame) -> tuple:
        imbal = self._classify(day, bars, sd, today)
        if imbal is not None:
            self._imbal.append((day, imbal))
        share = self._share20()
        self.shares[day] = share
        if imbal is not None and share is not None and share >= 0.5:
            return ("E4", self._books["E4"], e4_trigger_ok)
        return ("E3", self._books["E3"], _any_trigger)  # incl. unknown-day default

    def _classify(self, day: str, bars, sd, today) -> float | None:
        """balanced/imbalanced/None(unknown) — mirrors build_daytypes exactly."""
        prior_days = sorted(set(sd[sd < day]))
        if not prior_days:
            return None
        prior_bars = bars[sd == prior_days[-1]]
        on_bars = today[today["ts_event"].dt.time < _OPEN]
        if prior_bars.empty or len(on_bars) < _MIN_ON_BARS:
            return None
        pv = volume_profile(prior_bars, *_PROFILE_ARGS)
        ov = volume_profile(on_bars, *_PROFILE_ARGS)
        inter = max(0.0, min(ov.vah, pv.vah) - max(ov.val, pv.val))
        width = max(ov.vah - ov.val, _PROFILE_ARGS[0])
        return float(inter / width < 0.5)              # 1.0 imbalanced, 0.0 balanced

    def _share20(self) -> float | None:
        tail = self._imbal[-20:]
        if len(tail) < 5:                              # rolling min_periods=5
            return None
        return sum(v for _, v in tail) / len(tail)
