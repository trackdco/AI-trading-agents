"""Order-time spread / slippage guard (Angus 24 Jul CANON ruling, Q-31 — execution engineering).

The ruling moved spread / fill-quality gating OUT of the judgment desk and INTO Python "at
order time," under one hard constraint: the threshold must be RELATIVE to recent spread
conditions, never a frozen absolute — quote: "Note London 2026 spreads regime-shifted —
make any guard relative, never a frozen absolute."

This is the ONLY new gate the ruling permits, and it is deliberately execution engineering,
not a strategy veto: it never changes what the engine fires or when (that path is FROZEN),
only whether the resulting order is actually PLACED given the spread at the fill. A guard
trip = the order is not placed and the reason is journaled (src/live/journal.on_guard_trip);
nothing else about the loop changes.

Mechanics:
  * baseline  = MEDIAN of the trailing per-bar spread window (median, not mean, so a single
                wide bar cannot inflate the baseline it is being judged against),
  * threshold = mult x baseline,
  * trip      when the fill's spread STRICTLY exceeds the threshold.

Fail-OPEN on absence of evidence, by design. With fewer than `min_obs` baseline bars, or no
measurable fill spread, the guard PASSES. An untested block is exactly the kind of mechanism
the ruling warns degrades a validated book, so the guard only ever trips on a spread that is
wide RELATIVE to a real, sufficiently-sampled local baseline — never on thin data, and never
against a frozen number.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class GuardResult:
    """Outcome of one order-time check. `ok=False` means DO NOT PLACE THE ORDER."""
    ok: bool
    observed: float | None        # spread at the fill (points), or None if unmeasurable
    baseline: float | None        # median trailing spread the threshold derives from
    threshold: float | None       # mult x baseline
    reason: str                   # human/audit string; "ok" | trip detail | fail-open cause


class SpreadGuard:
    """Relative order-time spread guard. Stateless: each `evaluate` is a pure function of the
    fill spread and a caller-supplied trailing-spread baseline (see ambient.recent_spreads),
    so it holds no history that a restart could desync."""

    def __init__(self, mult: float = 3.0, window: int = 30, min_obs: int = 5):
        if mult <= 0:
            raise ValueError("mult must be > 0")
        if min_obs < 1:
            raise ValueError("min_obs must be >= 1")
        self.mult = float(mult)
        self.window = int(window)
        self.min_obs = int(min_obs)

    def evaluate(self, fill_spread, recent_spreads) -> GuardResult:
        if fill_spread is None:
            return GuardResult(True, None, None, None, "pass:no_spread_data")
        fill_spread = float(fill_spread)
        obs = [float(s) for s in (recent_spreads or []) if s is not None]
        if len(obs) < self.min_obs:
            return GuardResult(True, fill_spread, None, None, "pass:insufficient_history")
        baseline = float(median(obs))
        threshold = baseline * self.mult
        if fill_spread > threshold:
            return GuardResult(
                False, fill_spread, baseline, threshold,
                f"spread {fill_spread:.2f}pt > {self.mult:g}x median baseline "
                f"{baseline:.2f}pt (= {threshold:.2f}pt) over {len(obs)} bars")
        return GuardResult(True, fill_spread, baseline, threshold, "ok")
