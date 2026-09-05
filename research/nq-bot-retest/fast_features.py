"""
fast_features.py — exact-equivalence fast paths for the bot's NQFeatureEngine zone bookkeeping.

Installed by `install()`, which monkeypatches five methods on the bot's `NQFeatureEngine` class
(the bot's files are never edited). Each replacement computes the same values — float64
arithmetic is bit-identical in numpy and Python — mutates the same object attributes in the same
order, and produces the same snapshot fields as the original. Nothing behavioural is dropped:

  _ob_exists            original scans every order block ever detected (12k at bar 150k) with the
                        predicate  same direction & |Δzone_high|<2 & |Δzone_low|<2.  Replacement:
                        a bucket index on (direction, floor(zone_high/2), floor(zone_low/2)); any
                        match lies in the 3x3 neighbourhood, where the identical predicate is applied.
  _fvg_exists           same predicate with threshold 1.0, evaluated on numpy arrays over all gaps.
  _check_ifvg           the inversion test vectorised; hits processed in list order, as the loop did.
  _update_zone_validity order blocks: once the 500-bar buffer is full (`len(_bars) == 500`), the
                        age threshold is constant, so a valid+mitigated block can never change state
                        again and revisiting it is a no-op; only valid+unmitigated blocks are visited.
                        Before that point the original loop runs verbatim. Gaps: the fill update is
                        vectorised (same expressions), changed values written back to the objects.
  _compute_proximity_signals  active lists taken from the maintained structures (same order);
                        the `recent_sweeps` comprehension — assigned and never read, and the source
                        of ~13% of run time via list.index — is omitted.

Equivalence evidence: REPRODUCTION.md §6.
"""
import math

import numpy as np

from features.engine import NQFeatureEngine, FairValueGap  # bot modules (sys.path set by the driver)

CAP = 500  # NQFeatureEngine keeps the last 500 bars


# ── order blocks ────────────────────────────────────────────────────────────────────────
def _ob_key(direction, hi, lo):
    return (direction, math.floor(hi / 2.0), math.floor(lo / 2.0))


class OBList(list):
    """The bot's `_order_blocks` list plus: a bucket index, the active (valid & unmitigated)
    sub-list in list order, and the steady-state flag."""

    def __init__(self, items=()):
        super().__init__()
        self.buckets = {}
        self.active = []
        self.steady = False
        for ob in items:
            self.append(ob)

    def append(self, ob):
        super().append(ob)
        self.buckets.setdefault(_ob_key(ob.direction, ob.zone_high, ob.zone_low), []).append(ob)
        if ob.is_valid and not ob.mitigated:
            self.active.append(ob)

    def exists(self, new_ob) -> bool:
        d, hi, lo = new_ob.direction, new_ob.zone_high, new_ob.zone_low
        bh, bl = math.floor(hi / 2.0), math.floor(lo / 2.0)
        for dh in (-1, 0, 1):
            for dl in (-1, 0, 1):
                for ob in self.buckets.get((d, bh + dh, bl + dl), ()):
                    if abs(ob.zone_high - hi) < 2.0 and abs(ob.zone_low - lo) < 2.0:
                        return True
        return False

    def rebuild_active(self):
        self.active = [ob for ob in self if ob.is_valid and not ob.mitigated]

    def __reduce__(self):
        return (_restore_oblist, (list(self), self.steady))


def _restore_oblist(items, steady):
    o = OBList(items)
    o.steady = steady
    return o


# ── fair value gaps ─────────────────────────────────────────────────────────────────────
class FVGList(list):
    """The bot's `_fvgs` list plus parallel numpy arrays (kept in sync on every change)."""

    def __init__(self, items=()):
        super().__init__()
        self.n = 0
        cap = 1024
        self.H = np.empty(cap)
        self.L = np.empty(cap)
        self.S = np.empty(cap)
        self.F = np.empty(cap)
        self.bull = np.empty(cap, dtype=bool)
        self.bear = np.empty(cap, dtype=bool)
        self.valid = np.empty(cap, dtype=bool)
        self.inv = np.empty(cap, dtype=bool)
        for f in items:
            self.append(f)

    def _grow(self):
        for name in ("H", "L", "S", "F", "bull", "bear", "valid", "inv"):
            a = getattr(self, name)
            b = np.empty(len(a) * 2, dtype=a.dtype)
            b[: self.n] = a[: self.n]
            setattr(self, name, b)

    def append(self, f):
        super().append(f)
        i = self.n
        if i == len(self.H):
            self._grow()
        self.H[i] = f.gap_high
        self.L[i] = f.gap_low
        self.S[i] = f.gap_size
        self.F[i] = f.filled_pct
        self.bull[i] = (f.gap_type == "bullish")
        self.bear[i] = (f.gap_type == "bearish")
        self.valid[i] = f.is_valid
        self.inv[i] = f.is_inverse
        self.n = i + 1

    def exists(self, gap_type, hi, lo) -> bool:
        n = self.n
        if n == 0:
            return False
        same_type = self.bull[:n] if gap_type == "bullish" else (self.bear[:n] if gap_type == "bearish" else np.zeros(n, bool))
        return bool(np.any(same_type & (np.abs(self.H[:n] - hi) < 1.0) & (np.abs(self.L[:n] - lo) < 1.0)))

    def compress(self, keep):
        idx = np.flatnonzero(keep)
        new = FVGList()
        for i in idx:
            new.append(self[i])
        return new

    def __reduce__(self):
        return (_restore_fvglist, (list(self),))


def _restore_fvglist(items):
    return FVGList(items)


# ── patched methods ─────────────────────────────────────────────────────────────────────
def _ensure_fast(self):
    if not isinstance(self._order_blocks, OBList):
        self._order_blocks = OBList(self._order_blocks)
        # a converted (unpickled, slow-engine) state past the buffer fill has already had the
        # original loop run at len == 500; fresh engines start with steady = False
        self._order_blocks.steady = len(self._bars) >= CAP
    if not isinstance(self._fvgs, FVGList):
        self._fvgs = FVGList(self._fvgs)


def _ob_exists(self, new_ob) -> bool:
    _ensure_fast(self)
    return self._order_blocks.exists(new_ob)


def _fvg_exists(self, new_fvg) -> bool:
    _ensure_fast(self)
    return self._fvgs.exists(new_fvg.gap_type, new_fvg.gap_high, new_fvg.gap_low)


def _check_ifvg(self, current_bar) -> None:
    _ensure_fast(self)
    fv = self._fvgs
    n = fv.n
    if n == 0:
        return
    close = current_bar.close
    hit = fv.valid[:n] & ~fv.inv[:n] & (
        (fv.bull[:n] & (close < fv.L[:n])) | (fv.bear[:n] & (close > fv.H[:n]))
    )
    for i in np.flatnonzero(hit):          # ascending == the original's list order
        f = fv[i]
        ifvg = FairValueGap(
            detected_at=current_bar.timestamp,
            gap_type="bearish" if f.gap_type == "bullish" else "bullish",
            gap_high=f.gap_high,
            gap_low=f.gap_low,
            gap_size=f.gap_size,
            is_inverse=True,
        )
        f.is_valid = False
        fv.valid[i] = False
        fv.append(ifvg)


def _update_zone_validity(self, current_bar) -> None:
    _ensure_fast(self)
    obl = self._order_blocks
    max_age = self.config.ob_max_age_bars
    nb = len(self._bars)

    if not obl.steady:
        # ---- original loop, verbatim ----
        for ob in obl:
            if not ob.is_valid:
                continue
            bars_since = nb - ob.bar_index
            if bars_since > max_age:
                ob.is_valid = False
                continue
            if ob.direction == "bullish":
                if current_bar.low <= ob.zone_high:
                    ob.mitigated = True
            elif ob.direction == "bearish":
                if current_bar.high >= ob.zone_low:
                    ob.mitigated = True
        obl.rebuild_active()
        if nb >= CAP:
            obl.steady = True
    else:
        keep = []
        for ob in obl.active:               # valid & unmitigated, list order
            bars_since = nb - ob.bar_index
            if bars_since > max_age:
                ob.is_valid = False
                continue
            if ob.direction == "bullish":
                if current_bar.low <= ob.zone_high:
                    ob.mitigated = True
            elif ob.direction == "bearish":
                if current_bar.high >= ob.zone_low:
                    ob.mitigated = True
            if not ob.mitigated:
                keep.append(ob)
        obl.active = keep

    fv = self._fvgs
    n = fv.n
    if n:
        H, L, S, F = fv.H[:n], fv.L[:n], fv.S[:n], fv.F[:n]
        valid, bull, bear = fv.valid[:n], fv.bull[:n], fv.bear[:n]
        lo, hi = current_bar.low, current_bar.high
        F_old = F.copy()
        with np.errstate(divide="ignore", invalid="ignore"):
            mb = valid & bull & (lo <= H)
            fd = H - np.maximum(lo, L)
            newb = np.where(S > 0, np.minimum(fd / S, 1.0), 1.0)
            F[mb] = newb[mb]
            mr = valid & bear & (hi >= L)
            fd2 = np.minimum(hi, H) - L
            newr = np.where(S > 0, np.minimum(fd2 / S, 1.0), 1.0)
            F[mr] = newr[mr]
        for i in np.flatnonzero(F != F_old):
            fv[i].filled_pct = float(F[i])
        keep = valid | (F < 1.0)
        if not keep.all():
            self._fvgs = fv.compress(keep)

    if len(self._sweeps) > 50:
        self._sweeps = self._sweeps[-50:]


def _compute_proximity_signals(self, snapshot, bar) -> None:
    _ensure_fast(self)
    proximity_points = 5.0

    active_obs = list(self._order_blocks.active)
    snapshot.active_order_blocks = active_obs
    for ob in active_obs:
        if ob.direction == "bullish":
            if ob.zone_low - proximity_points <= bar.close <= ob.zone_high + proximity_points:
                snapshot.near_bullish_ob = True
        elif ob.direction == "bearish":
            if ob.zone_low - proximity_points <= bar.close <= ob.zone_high + proximity_points:
                snapshot.near_bearish_ob = True

    fv = self._fvgs
    n = fv.n
    if n:
        idx = np.flatnonzero(fv.valid[:n] & (fv.F[:n] < 0.8))
    else:
        idx = np.zeros(0, dtype=int)
    active_fvgs = [fv[i] for i in idx]
    snapshot.active_fvgs = active_fvgs
    if len(idx):
        H, L = fv.H[:n][idx], fv.L[:n][idx]
        bull, bear = fv.bull[:n][idx], fv.bear[:n][idx]
        inside = (L <= bar.close) & (bar.close <= H)
        if np.any(inside & bull):
            snapshot.inside_bullish_fvg = True
        if np.any(inside & bear):
            snapshot.inside_bearish_fvg = True

    snapshot.recent_sweeps = self._sweeps[-5:] if self._sweeps else []
    for sweep in self._sweeps[-5:]:
        if sweep.confirmed:
            if sweep.sweep_type == "buy_side":
                snapshot.recent_buy_sweep = True
            elif sweep.sweep_type == "sell_side":
                snapshot.recent_sell_sweep = True

    long_structural_stops = []
    short_structural_stops = []
    for ob in active_obs:
        if ob.direction == "bullish" and snapshot.near_bullish_ob:
            long_structural_stops.append(ob.zone_low - 3.0)
        elif ob.direction == "bearish" and snapshot.near_bearish_ob:
            short_structural_stops.append(ob.zone_high + 3.0)
    if len(idx):
        if snapshot.inside_bullish_fvg and bull.any():
            long_structural_stops.append(float((L[bull] - 3.0).max()))
        if snapshot.inside_bearish_fvg and bear.any():
            short_structural_stops.append(float((H[bear] + 3.0).min()))
    for sweep in self._sweeps[-5:]:
        if sweep.confirmed:
            if sweep.sweep_type == "sell_side":
                long_structural_stops.append(sweep.sweep_price - 5.0)
            elif sweep.sweep_type == "buy_side":
                short_structural_stops.append(sweep.sweep_price + 5.0)

    if long_structural_stops:
        snapshot.structural_stop_long = round(max(long_structural_stops), 2)
    if short_structural_stops:
        snapshot.structural_stop_short = round(min(short_structural_stops), 2)


_ORIGINALS = {}


def install() -> None:
    """Monkeypatch NQFeatureEngine in-process. Idempotent."""
    if _ORIGINALS:
        return
    for name, fn in (("_ob_exists", _ob_exists), ("_fvg_exists", _fvg_exists),
                     ("_check_ifvg", _check_ifvg), ("_update_zone_validity", _update_zone_validity),
                     ("_compute_proximity_signals", _compute_proximity_signals)):
        _ORIGINALS[name] = getattr(NQFeatureEngine, name)
        setattr(NQFeatureEngine, name, fn)


def uninstall() -> None:
    for name, fn in _ORIGINALS.items():
        setattr(NQFeatureEngine, name, fn)
    _ORIGINALS.clear()
