#!/usr/bin/env python3
"""CONSTRUCTION validation for the London book feature layer. Not an edge test.

Runs the five-check battery on every VALID feature in `src.engine.book` BEFORE any
question about profitability is asked. That ordering is the point: an edge test on a
badly constructed feature answers a question nobody asked, and answers it convincingly.

Two framing decisions that the first draft of this script got wrong, kept here because
the mistakes are instructive:

**A state feature is not a flow feature, and the contemporaneous check differs.**
Cont-Kukanov-Stoikov's "must relate positively to same-interval return" is a statement
about *flow* -- signed pressure applied DURING an interval moves price during that
interval. Depth imbalance is a *level*, read at one instant. Against the return of the
minute it sits at the end of, it is the post-trade RESIDUAL: what aggressive flow left
behind. A relationship there is memory, not signal, and its size is a measure of
contamination rather than of power. So the contemporaneous check runs on the tape-derived
delta -- a genuine flow measure with exchange aggressor tags -- and the book levels are
read against the first genuinely forward minute.

**Verdicts are calibrated against the shuffle null, never against a constant.** The first
draft called r = -0.0053 a "MAPPING ERROR" when the null's own p95 was 0.0108. A
threshold that fires inside the noise band manufactures findings.

    1. Contemporaneous sign  -- on tape delta (flow, tagged): must be POSITIVE. On book
                                levels: reported as the residual it is.
    2. Shuffle placebo       -- permute the target, keep the feature's marginal
                                distribution, measure apparent power under the null.
                                This sets the bar every other verdict is read against.
    3. Time-shifted placebo  -- the check that matters for snapshot features. The book
                                is a survivor of the flow that just happened.
    4. Parameter ladder      -- imb_L1 .. imb_L10. A real mechanism strengthens smoothly
                                with depth up to the point of decay; knife-edge or
                                sign-flipping behaviour is the signature of noise.
    5. Era stability         -- 2025 vs 2026, coefficient AND the feature's own
                                distribution, on the forward probe. A sign flip is only
                                reported when both eras clear their own null.

NO TRIALS ARE CHARGED. Nothing here proposes a rule, searches a threshold, or measures
P&L. Returns are used only as a construction probe -- the question is always "is this
column measuring what its name says", never "does it pay".

    python -m scripts.book_feature_validation
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine import book  # noqa: E402
from src.engine import footprint as fp  # noqa: E402
from src.validation.window_causality import assert_causal  # noqa: E402

SEED = 20260806
N_SHUFFLE = 1000
OUT = ROOT / "output/london_book_features.parquet"

PROBES = ["imb_L1", "imb_L3", "imb_L10", "press_imb", "wmid_tilt"]


def load_bars() -> pd.DataFrame:
    """Bars indexed by their CLOSE time.

    ``ts_event`` is the bar START -- confirmed on two independent anchors once the depth
    file's floored label is undone (see src/engine/book docstring), so the LDN-ATC-01
    correction and data/reference/parity_slice_feb2026.md both stand. +1min puts the
    index at the close, which is the instant the bar's information exists.
    """
    fr = [pd.read_parquet(ROOT / "data/reference" / f,
                          columns=["ts_event", "open", "high", "low", "close", "volume"])
          for f in ("nq_1m_master.parquet", "nq_1m_feb_jul2026.parquet")]
    b = pd.concat(fr, ignore_index=True)
    b["ts"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(book.LDN) + pd.Timedelta(minutes=1)
    return b.drop_duplicates("ts").sort_values("ts").set_index("ts")[["open", "close"]]


def load_tape_delta() -> pd.Series:
    """Per-minute signed delta (B-A) through the chokepoint. A true FLOW measure."""
    d = fp.load_footprint(fp.fit_span_files(), fp.cached_front_month_bands(), report=False)
    s = fp.signed_delta(d, by=("ts_minute",))
    s.index = s.index.tz_convert(book.LDN) + pd.Timedelta(minutes=1)   # label -> close
    return s.rename("tape_delta")


def corr(x, y) -> tuple[float, int]:
    x, y = pd.Series(x), pd.Series(y)
    m = x.notna() & y.notna()
    if m.sum() < 30 or x[m].std() == 0 or y[m].std() == 0:
        return np.nan, int(m.sum())
    return float(np.corrcoef(x[m], y[m])[0, 1]), int(m.sum())


def null_band(x, y, rng, n=N_SHUFFLE) -> tuple[float, float]:
    """(p95, p) of |r| under target permutation. The bar every verdict is read against."""
    m = pd.Series(x).notna() & pd.Series(y).notna()
    a, b = pd.Series(x)[m].to_numpy(), pd.Series(y)[m].to_numpy()
    if len(a) < 30:
        return np.nan, np.nan
    obs = abs(np.corrcoef(a, b)[0, 1])
    null = np.array([abs(np.corrcoef(a, rng.permutation(b))[0, 1]) for _ in range(n)])
    return float(np.quantile(null, .95)), float((null >= obs).mean())


def main() -> None:
    rng = np.random.default_rng(SEED)
    D = book.load_depth(report=True)

    rule = book.causality_declaration([f"{h:02d}:{m:02d}"
                                       for h in (8, 9) for m in range(0, 60, 15)])
    assert_causal(rule)
    print("[causality] §2.5 window-causality bar PASSES (all windows Rel(0), worst lag 0)")
    print("[causality] NOTE: that bar audits the DECLARED window. It passed this layer on")
    print("            the mislabelled index too — a causality check cannot detect a lying")
    print("            timestamp. The ts_recv assertion in load_depth is what catches it.")

    F = book.features(D).copy()
    F.index = F.index.ceil("min")          # true obs time ~:59.9 -> the minute it ends
    J = F.join(load_bars(), how="inner").join(load_tape_delta(), how="left")
    J["ret"] = (J.close - J.open) / book.TICK
    J["ret_next"] = J.groupby("day")["ret"].shift(-1)
    J["delta_next"] = J.groupby("day")["tape_delta"].shift(-1)
    J["era"] = np.where(J.index.year <= 2025, "2025", "2026")
    print(f"\n[join] {len(J):,} minutes | {J.day.nunique()} sessions | "
          f"eras {J.era.value_counts().to_dict()}")
    print("[join] `ret` is the minute the snapshot sits at the END of — CONTAMINATED by")
    print("       construction (post-trade residual). `ret_next` is the first genuinely")
    print("       forward minute. Only ret_next is a legitimate probe of a book LEVEL.")

    print("\n" + "=" * 78)
    print("0. FEATURE DISTRIBUTIONS (the definition layer, before any outcome)")
    print("=" * 78)
    print(f"{'feature':<16}{'mean':>9}{'sd':>9}{'p5':>9}{'p50':>9}{'p95':>9}{'nan%':>8}")
    for c in PROBES + ["spread", "bid_L10", "ord_sz_bid", "depth_reach_bid", "tape_delta"]:
        s = J[c]
        print(f"{c:<16}{s.mean():>9.3f}{s.std():>9.3f}{s.quantile(.05):>9.3f}"
              f"{s.median():>9.3f}{s.quantile(.95):>9.3f}{s.isna().mean()*100:>7.2f}%")

    print("\n" + "=" * 78)
    print("1. CONTEMPORANEOUS SIGN — on TAPE DELTA, the one true flow measure here")
    print("=" * 78)
    print("   CKS's positive-contemporaneous law is about flow applied DURING an interval.")
    print("   Tape delta is that; book levels are not. This is the positive control that")
    print("   proves the harness can see a correctly-signed relationship at all.")
    r, n = corr(J.tape_delta, J.ret)
    p95, p = null_band(J.tape_delta, J.ret, rng)
    v = "PASS (positive, clears null)" if (r > 0 and p < 0.05) else "FAIL"
    print(f"\n   r(tape_delta_t , ret_t)  = {r:+.4f}   n={n:,}   null p95 {p95:.4f}  p={p:.3f}   {v}")
    print(f"   (footprint B-A convention confirmed independently: the sign is not assumed)")

    print("\n" + "=" * 78)
    print("2. SHUFFLE PLACEBO — sets the noise band every verdict below is read against")
    print("=" * 78)
    print(f"{'feature':<14}{'|r| vs ret_next':>17}{'null p95':>11}{'p':>9}   verdict")
    bands = {}
    for c in PROBES:
        r, _ = corr(J[c], J.ret_next)
        p95, p = null_band(J[c], J.ret_next, rng)
        bands[c] = p95
        print(f"{c:<14}{abs(r):>17.4f}{p95:>11.4f}{p:>9.3f}   "
              f"{'clears the null' if p < 0.05 else 'INSIDE the null'}")

    print("\n" + "=" * 78)
    print("3. TIME-SHIFTED PLACEBO — the post-trade-residual check")
    print("=" * 78)
    print("   r(F_t, ret_t) is the residual: the minute the snapshot sits at the end of.")
    print("   r(F_t, ret_t+1) is the forward probe. If the residual dominates, the feature")
    print("   is memory. Reported as a ratio so the read does not depend on magnitude.")
    print(f"\n{'feature':<14}{'residual r(F,ret_t)':>21}{'forward r(F,ret_t+1)':>22}{'|fwd|/|resid|':>15}   read")
    for c in PROBES:
        r_res, _ = corr(J[c], J.ret)
        r_fwd, _ = corr(J[c], J.ret_next)
        ratio = abs(r_fwd) / max(abs(r_res), 1e-9)
        read = "forward-dominant" if ratio > 1.5 else ("residual-dominant — MEMORY" if ratio < 0.67 else "comparable")
        print(f"{c:<14}{r_res:>+21.4f}{r_fwd:>+22.4f}{ratio:>15.2f}   {read}")

    print("\n" + "=" * 78)
    print("4. PARAMETER LADDER — must strengthen smoothly with depth, not knife-edge")
    print("=" * 78)
    print(f"{'k levels':<10}{'r(imb_Lk, ret_t+1)':>21}{'null p95':>11}{'clears?':>10}{'sd(imb_Lk)':>13}")
    for k in book.LADDER:
        c = f"imb_L{k}"
        r, _ = corr(J[c], J.ret_next)
        p95, p = null_band(J[c], J.ret_next, rng)
        print(f"{k:<10}{r:>+21.4f}{p95:>11.4f}{('yes' if p < .05 else 'no'):>10}{J[c].std():>13.4f}")

    print("\n" + "=" * 78)
    print("5. ERA STABILITY — coefficient and distribution, on the forward probe")
    print("=" * 78)
    print(f"{'feature':<14}{'r 2025':>10}{'r 2026':>10}{'both clear null?':>18}{'sd 2025':>10}{'sd 2026':>10}   verdict")
    for c in PROBES:
        a, b = J[J.era == "2025"], J[J.era == "2026"]
        ra, _ = corr(a[c], a.ret_next)
        rb, _ = corr(b[c], b.ret_next)
        _, pa = null_band(a[c], a.ret_next, rng, n=300)
        _, pb = null_band(b[c], b.ret_next, rng, n=300)
        both = pa < 0.05 and pb < 0.05
        sa, sb = a[c].std(), b[c].std()
        if not both:
            v = "underpowered — no sign claim"
        elif np.sign(ra) != np.sign(rb):
            v = "SIGN FLIP"
        elif abs(sa - sb) / max(sa, sb, 1e-9) > 0.25:
            v = "stable sign, scale drift >25%"
        else:
            v = "stable"
        print(f"{c:<14}{ra:>+10.4f}{rb:>+10.4f}{str(both):>18}{sa:>10.4f}{sb:>10.4f}   {v}")

    print("\n" + "=" * 78)
    print("6. THE GUARDED FEATURE — OFI proxy refuses to build unguarded")
    print("=" * 78)
    try:
        book.ofi_proxy(D)
        print("   *** GUARD FAILED — ofi_proxy built without the flag ***")
    except book.BiasedFeatureError as e:
        print(f"   BiasedFeatureError raised as designed:\n   {str(e)[:170]}...")

    F.to_parquet(OUT)
    print(f"\nfeatures -> {OUT.relative_to(ROOT)}  ({len(F):,} minutes, "
          f"{len([c for c in F.columns if c not in ('day','ts_label')])} feature columns)")
    print("CONSTRUCTION VALIDATION ONLY. No trials charged. No rule proposed. No P&L.")


if __name__ == "__main__":
    main()
