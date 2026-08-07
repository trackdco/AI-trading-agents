"""Canonical loader and instantaneous feature layer for the London MBP-10 book.

THE ONLY SUPPORTED PATH TO ``data/reference/depth_london/*.csv``.

Companion to :mod:`src.engine.footprint`. That module owns the aggressor-tagged tape
(what traded); this one owns the resting book (what was showing). Between them they are
the whole London flow substrate.

What this data is, measured rather than assumed
-----------------------------------------------
295 sessions, 2025-06-02 -> 2026-07-22. **Exactly 120 rows per session** -- one per
minute, 08:00-09:59 *London local* on every day, so DST is already handled at extraction
(verified on both BST and GMT days). Ten levels, populated 100% of the time, never
crossed. Prices are already decimal here; ``data/depth/`` is a mixed archive that needs a
per-file 1e-9 detection, and this one does not.

**``ts_event`` IS FLOORED TO THE MINUTE. THE ROW LABELLED T IS THE BOOK AT ~T+59.9s.**
This is the single most consequential fact in this module and it is not visible from
``ts_event`` alone -- every value sits exactly on a minute boundary, which reads as a
clean per-minute sample. ``ts_recv`` carries the truth:

    ts_recv - ts_event : median 59.889s, p1 58.193s, 95.9% inside [59s, 60s)
    ts_in_delta (matching-engine -> capture latency) : ~13 microseconds, negligible

So the row labelled 08:15 is the book at 08:15:59.9 -- the END of minute 08:15, not its
start. **A decision taken at minute M must read the row labelled M-1**; reading row M is
a ~60-second lookahead. :func:`load_depth` indexes by ``ts_recv`` so this cannot be got
wrong by accident, and :func:`features_at` enforces it.

This also settles an apparent conflict with the bar master. Measured against the *label*,
``close(ts_event=T) ~ mid(label T)`` at median 0.375 pts, which reads as the bars being
END-labelled and contradicts ``data/reference/parity_slice_feb2026.md`` and the
LDN-ATC-01 bar-label correction. Against the *true* time the contradiction dissolves:
label T is the book at the close of the bar covering [T, T+1), so the bars are
START-labelled exactly as documented. **The prose was right; the depth timestamp was the
liar.** Two independent checks agree once the floor is undone -- footprint trades stamped
``ts_minute=T`` fall inside bar ``ts_event=T`` on 98.1% of 42,230 minutes (17.5% for the
alternative), and ``open(T) ~ mid(label T-1)``.

The number that decides everything downstream:

    consecutive rows are a median of **23,654 sequence numbers apart**
    (p25 15,576 | p75 33,606 | max 135,458)

Roughly 23,654 book events happen and are discarded between one row and the next.

What follows from that
----------------------
**Instantaneous features survive; differenced ones do not.** A function of the book at
one instant degrades gracefully as sampling coarsens -- noisier, sparser, still unbiased.
A quantity defined on *successive updates* does not degrade, it becomes a different
quantity. So this module computes levels and refuses differences.

**Order flow imbalance is BIASED here, not merely noisy.** Cont, Kukanov & Stoikov (2014)
define OFI as a sum of per-event contributions from successive best-quote changes, and
their own identity is that *a market sell and a cancelled buy of the same size are
equivalent to OFI* -- same effect on the bid queue. Differencing two snapshots recovers
only the NET change across ~23,654 netted events, so a reconstruction

  - understates gross flow (only the residual survives),
  - conflates cancellation with execution -- economically opposite events,
  - can carry the OPPOSITE SIGN to true integrated OFI.

A sign flip leaves R-squared unchanged, so nothing downstream will catch it. CKS operate
at 10-second resolution and report contemporaneous R^2 ~ 65%; FX order-book work at 0.1s
notes reconstruction is sound there only because "in most cases nothing happens within a
time-slice", which fails completely at 60 seconds. :func:`ofi_proxy` therefore exists but
refuses to run unless the caller passes ``i_know_this_is_biased=True``, and it returns a
column named ``ofi_PROXY``. **What would move OFI to VALID: event-level MBP-10 for this
window** -- the same Databento schema unsampled. A purchase, not a code change.

**The book only reaches +/-2.25 points.** Ten levels span a median 2.25 pts per side
(p90 2.75) -- about nine ticks. These are at-price reads and nothing else; they cannot
speak to structure at a level 20 points away. This reproduces canon finding 2a9c221
independently.

**NQ's book is thin.** Touch size median 1 contract in 1 order; 29-30 contracts across
all ten levels. Level-1 imbalance therefore has a tiny denominator and is close to a coin
flip minute to minute. Prefer the multi-level forms, and normalise before comparing
across time -- raw contract counts load on the activity regime, not on imbalance.

Causality
---------
Once indexed by ``ts_recv``, a snapshot observed at time t is settled at t, and a feature
read at decision minute M uses the last snapshot with ``ts_recv <= M`` -- see
:func:`causality_declaration`, which is the window table a prereg transcribes.

**A warning the §2.5 bar cannot give you.** That check audits *declared* windows. It
takes ``close_time(W)`` from the declaration, so it certifies a rule whose window table
says "book snapshot closes at Rel(0)" even when the underlying timestamp is floored and
the true close is Rel(+1). It passed this layer on the mislabelled index. **A causality
bar cannot detect a lying timestamp** -- that needs a data-layer assertion against a
second clock, which is what ``ts_recv`` provides here and what :func:`load_depth`
asserts.

Two further hazards remain, and neither is fixed by the timestamp being legal:

  - **The post-trade residual.** The book at T is a *survivor* -- what aggressive flow
    left behind. Depth replenishes fast relative to a minute (Large 2007: ~20s half-life
    where replenishment occurs at all), so the observed book has usually re-equilibrated
    and correlates mechanically with the move that just finished. Joined to a *past*
    return that reads as prediction and is memory. The time-shifted placebo is the check.
  - **At-fill reads.** A book read taken at the moment a limit order fills contains the
    answer: the fill required price to travel to the order. Anchor reads at the DECISION
    instant. :func:`features_at` takes the decision minute for exactly this reason.

Sealed-span safety
------------------
:func:`load_depth` refuses any path under ``depth_london_2023_24`` unless the caller
passes ``allow_holdout=True``, which only a declared look may do. The assertion lives
here, at the chokepoint, rather than being restated in every consumer.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

DEPTH_LONDON = Path("data/reference/depth_london")
DEPTH_SEALED = Path("data/reference/depth_london_2023_24")
LDN = "Europe/London"
TICK = 0.25
LEVELS = 10

BID_PX = [f"bid_px_{i:02d}" for i in range(LEVELS)]
ASK_PX = [f"ask_px_{i:02d}" for i in range(LEVELS)]
BID_SZ = [f"bid_sz_{i:02d}" for i in range(LEVELS)]
ASK_SZ = [f"ask_sz_{i:02d}" for i in range(LEVELS)]
BID_CT = [f"bid_ct_{i:02d}" for i in range(LEVELS)]
ASK_CT = [f"ask_ct_{i:02d}" for i in range(LEVELS)]

#: Levels at which the multi-level ladder is reported. The ladder IS the parameter test:
#: a real book mechanism strengthens smoothly as depth is added up to the point of decay,
#: and behaves erratically or knife-edge when it is noise.
LADDER = (1, 2, 3, 5, 10)

__all__ = [
    "BiasedFeatureError",
    "causality_declaration",
    "depth_files",
    "features",
    "features_at",
    "load_depth",
    "ofi_proxy",
    "session_features",
]

_DATE = re.compile(r"(\d{8})")


class BiasedFeatureError(RuntimeError):
    """Raised when a snapshot-differenced 'flow' feature is requested unguarded."""


# ------------------------------------------------------------------ loading
def depth_files(depth_dir: Path | str = DEPTH_LONDON) -> list[Path]:
    """Every non-sealed daily depth CSV, sorted."""
    return sorted(Path(depth_dir).glob("*.mbp-10_condensed.csv"))


def _guard(path: Path, allow_holdout: bool) -> None:
    if allow_holdout:
        return
    parts = {p.lower() for p in path.parts}
    if DEPTH_SEALED.name in parts or "holdout" in path.name.lower():
        raise PermissionError(
            f"{path} is in the SEALED 2023/24 span. Reading it spends a holdout look. "
            f"Pass allow_holdout=True only from a declared look with the declaration "
            f"already committed."
        )


def load_depth(
    paths=None,
    *,
    depth_dir: Path | str = DEPTH_LONDON,
    allow_holdout: bool = False,
    tz: str = LDN,
    report: bool = False,
) -> pd.DataFrame:
    """Load raw wide MBP-10 snapshots. One row per minute, indexed by London time.

    Returns the wide frame untouched apart from the index -- feature construction is
    :func:`features`, kept separate so a caller can audit the raw book.
    """
    paths = [Path(p) for p in (paths if paths is not None else depth_files(depth_dir))]
    if not paths:
        raise FileNotFoundError(f"no depth CSVs under {depth_dir}")
    frames = []
    cols = (["ts_event", "ts_recv", "ts_in_delta", "sequence"]
            + BID_PX + ASK_PX + BID_SZ + ASK_SZ + BID_CT + ASK_CT)
    for p in paths:
        _guard(p, allow_holdout)
        frames.append(pd.read_csv(p, usecols=cols))
    d = pd.concat(frames, ignore_index=True)

    # TRUE observation time. ts_event is floored to the minute at extraction; ts_recv is
    # the capture-server receive time and ts_in_delta the matching-engine->capture lag
    # (~13us, kept for exactness rather than because it matters). Indexing by the label
    # would put every read ~60s in the future -- see the module docstring.
    label = pd.to_datetime(d.ts_event, utc=True, format="mixed")
    recv = pd.to_datetime(d.ts_recv, utc=True, format="mixed")
    d["ts"] = (recv - pd.to_timedelta(d.ts_in_delta, unit="ns")).dt.tz_convert(tz)
    d["ts_label"] = label.dt.tz_convert(tz)

    lag = (recv - label).dt.total_seconds()
    if lag.median() < 30:
        raise ValueError(
            f"depth ts_event/ts_recv lag has median {lag.median():.1f}s, expected ~59.9s. "
            f"The floored-label assumption this loader corrects for may not hold on this "
            f"extraction. Re-verify before using — an unchecked minute here is a "
            f"60-second lookahead in every consumer."
        )

    d = d.drop_duplicates(subset="ts").sort_values("ts").set_index("ts")
    d["day"] = d["ts_label"].dt.date          # session = the LABEL's date, unchanged
    if report:
        gap = d.sequence.diff()
        print(f"[book] {len(d):,} snapshot minutes | {d.day.nunique()} sessions | "
              f"{d.index.min().date()} -> {d.index.max().date()}")
        print(f"[book] events discarded between snapshots: median {gap.median():,.0f} "
              f"(p75 {gap.quantile(.75):,.0f}) -- differencing these is BIASED, see module docstring")
        print(f"[book] ts_event is FLOORED: true time runs {lag.median():.1f}s after the "
              f"label. Indexed by ts_recv; a decision at minute M reads the row LABELLED M-1.")
    return d


# ------------------------------------------------- instantaneous features
def features(d: pd.DataFrame, *, ladder=LADDER, pressure_alpha: float = 1.0) -> pd.DataFrame:
    """Every VALID feature: a pure function of the book at the snapshot instant.

    Nothing here differences across rows, so nothing here can be reordered, resampled or
    subset into a different quantity. That is the property the coarse sampling costs us
    everywhere else, and the reason this layer is the one worth having.

    Columns
    -------
    ``mid``, ``spread``            best prices; spread in points
    ``imb_L{k}``                   (Qb-Qa)/(Qb+Qa) over the first k levels, in [-1, 1].
                                   Buy-side-positive, matching footprint delta's B-A.
    ``bid_L{k}``/``ask_L{k}``      resting size over the first k levels
    ``wmid``                       size-weighted mid (Qa*Pb + Qb*Pa)/(Qa+Qb). Note the
                                   CROSS weighting: a large bid pulls the price toward
                                   the ask, because size is the thing that must be
                                   consumed before price can move that way. Getting this
                                   backwards is the classic microprice bug and it is
                                   invisible to R^2.
    ``wmid_tilt``                  wmid - mid, in ticks. The imbalance-driven lean.
                                   Stoikov's full microprice adds a martingale correction
                                   G(imbalance, spread) that must be FITTED; fit it on an
                                   expanding window or it is the LDN-INV-01 defect.
    ``press_bid``/``press_ask``    distance-weighted depth, sum(Q_i / dist_i^alpha),
                                   distance in ticks from mid. Near size counts more.
    ``press_imb``                  (press_bid - press_ask)/(press_bid + press_ask)
    ``ord_sz_bid``/``ord_sz_ask``  mean order size at the touch (sz/ct). The ct_* fields
                                   are present on all 295 days and were previously unused.
    ``depth_reach_bid``/_ask       points from best to the 10th level -- the honest
                                   statement of how far these reads can see (~2.25 pts).
    """
    bpx, apx = d[BID_PX].to_numpy(float), d[ASK_PX].to_numpy(float)
    bsz, asz = d[BID_SZ].to_numpy(float), d[ASK_SZ].to_numpy(float)
    bct, act = d[BID_CT].to_numpy(float), d[ASK_CT].to_numpy(float)

    out = pd.DataFrame(index=d.index)
    out["best_bid"], out["best_ask"] = bpx[:, 0], apx[:, 0]
    out["mid"] = (bpx[:, 0] + apx[:, 0]) / 2.0
    out["spread"] = apx[:, 0] - bpx[:, 0]

    for k in ladder:
        b, a = bsz[:, :k].sum(1), asz[:, :k].sum(1)
        out[f"bid_L{k}"], out[f"ask_L{k}"] = b, a
        out[f"imb_L{k}"] = (b - a) / np.where(b + a > 0, b + a, np.nan)

    q_b, q_a = bsz[:, 0], asz[:, 0]
    tot = q_b + q_a
    # CROSS weighting -- larger bid => price leans toward the ask.
    out["wmid"] = np.where(tot > 0, (q_a * bpx[:, 0] + q_b * apx[:, 0]) / np.where(tot > 0, tot, 1),
                           out["mid"])
    out["wmid_tilt"] = (out["wmid"] - out["mid"]) / TICK

    mid = out["mid"].to_numpy()[:, None]
    d_b = np.maximum((mid - bpx) / TICK, 0.5)      # >= half a tick, never divide by zero
    d_a = np.maximum((apx - mid) / TICK, 0.5)
    pb = (bsz / d_b ** pressure_alpha).sum(1)
    pa = (asz / d_a ** pressure_alpha).sum(1)
    out["press_bid"], out["press_ask"] = pb, pa
    out["press_imb"] = (pb - pa) / np.where(pb + pa > 0, pb + pa, np.nan)

    out["ord_sz_bid"] = q_b / np.where(bct[:, 0] > 0, bct[:, 0], np.nan)
    out["ord_sz_ask"] = q_a / np.where(act[:, 0] > 0, act[:, 0], np.nan)
    out["depth_reach_bid"] = bpx[:, 0] - bpx[:, LEVELS - 1]
    out["depth_reach_ask"] = apx[:, LEVELS - 1] - apx[:, 0]
    out["day"] = d["day"].to_numpy()
    out["ts_label"] = d["ts_label"].to_numpy()
    return out


def features_at(F: pd.DataFrame, decision_ts) -> pd.Series | None:
    """The book state as of a DECISION minute: the last snapshot OBSERVED at or before it.

    ``F`` must be indexed by true observation time -- i.e. built from :func:`load_depth`,
    which indexes by ``ts_recv``. On the raw label this would silently return the book as
    of ``decision_ts + 59.9s``.

    Never call this with a fill timestamp. A limit fill requires price to have travelled
    to the order, so a book read anchored at the fill contains the outcome. The signature
    takes ``decision_ts`` rather than a generic ``ts`` to make that hard to get wrong.
    """
    t = pd.Timestamp(decision_ts)
    sub = F[F.index <= t]
    if sub.empty:
        return None
    row = sub.iloc[-1]
    if "ts_label" in F.columns and pd.Timestamp(row["ts_label"]) >= t:
        raise ValueError(
            f"book row labelled {row['ts_label']} would be used for a decision at {t}; "
            f"its true observation time is ~60s after its label, so this is a lookahead. "
            f"Build F from load_depth() so the index is ts_recv."
        )
    return row


def session_features(F: pd.DataFrame, *, agg=("mean", "std")) -> pd.DataFrame:
    """Per-session summary of the instantaneous features. Aggregation, not differencing."""
    num = F.select_dtypes(include=[np.number])
    return num.groupby(F["day"]).agg(list(agg))


# ------------------------------------------------------------ the guarded one
def ofi_proxy(d: pd.DataFrame, *, i_know_this_is_biased: bool = False) -> pd.Series:
    """Snapshot-differenced best-quote change. **This is NOT OFI.**

    Kept in the codebase so that anyone who reaches for OFI finds this docstring instead
    of writing the naive version in a scratchpad. It returns a column named ``ofi_PROXY``
    and refuses to run unguarded, because the failure mode is a feature that looks
    perfectly reasonable and measures the residual of ~23,654 netted events.

    Cont-Kukanov-Stoikov's identity -- a market sell and a cancelled buy of the same size
    are equivalent to OFI -- is why: differencing conflates them. The proxy understates
    gross flow, mixes cancellation with execution, and can carry the opposite sign to
    true integrated OFI, which R^2 will not reveal.

    If you use it anyway: label it a proxy in the prereg, state the bias direction, and
    clear the time-shifted placebo first. To get the real thing, buy event-level MBP-10
    for this window.
    """
    if not i_know_this_is_biased:
        raise BiasedFeatureError(
            "OFI from 1-per-minute snapshots is BIASED, not merely noisy: consecutive "
            "rows are ~23,654 book events apart, and CKS's own identity makes a "
            "cancelled buy indistinguishable from a market sell in the net change. It "
            "understates gross flow, conflates cancellation with execution, and can "
            "carry the WRONG SIGN -- which R^2 cannot detect. Pass "
            "i_know_this_is_biased=True to build it as a declared proxy, or buy "
            "event-level MBP-10 to make it VALID."
        )
    bp, bs = d[BID_PX[0]].to_numpy(float), d[BID_SZ[0]].to_numpy(float)
    ap, asz = d[ASK_PX[0]].to_numpy(float), d[ASK_SZ[0]].to_numpy(float)
    pb, pa = np.r_[np.nan, bp[:-1]], np.r_[np.nan, ap[:-1]]
    sb, sa = np.r_[np.nan, bs[:-1]], np.r_[np.nan, asz[:-1]]
    e_b = np.where(bp > pb, bs, np.where(bp < pb, -sb, bs - sb))
    e_a = np.where(ap < pa, -asz, np.where(ap > pa, sa, -(asz - sa)))
    return pd.Series(e_b + e_a, index=d.index, name="ofi_PROXY")


# ------------------------------------------------------------ causality table
def causality_declaration(decision_times):
    """The §2.5 per-condition window table for any rule reading this layer.

    Every feature here closes at the decision minute -- ``Rel(0)`` -- because a snapshot
    stamped T is the state at T. Transcribe this into the prereg and assert it; the
    result is a rule that is causal by construction rather than by assurance.
    """
    from src.validation.window_causality import Rel, Rule

    return Rule.from_table(
        "book instantaneous features",
        [("book snapshot (all imb/wmid/press/ord_sz)", Rel(0), Rel(0),
          "state AT the decision minute; no differencing anywhere in this layer"),
         ("spread / mid / best prices", Rel(0), Rel(0), "same snapshot")],
        decision_times=decision_times,
        note="Causal by construction. The residual hazards are behavioural, not "
             "temporal: the post-trade residual (join to a FUTURE outcome, never a past "
             "move) and at-fill reads (anchor at the decision, not the fill).",
    )
