"""Construction guards for the London book feature layer.

The three things that can silently destroy this layer, each pinned by a test that fails
on its own failure mode:

1. **The floored timestamp.** ``ts_event`` sits exactly on the minute, which reads as a
   clean per-minute sample; the row is actually the book ~59.9s later. Indexing by the
   label is a 60-second lookahead in every consumer, and nothing downstream can see it.
2. **Snapshot-differenced "flow".** OFI over ~23,654 unobserved events is not OFI; the
   guard has to refuse rather than warn, because a warning gets read once and a returned
   Series gets used forever.
3. **The sealed span.** ``depth_london_2023_24`` must be unreachable without an explicit
   declared-look flag, asserted at the chokepoint rather than in each consumer.

Plus the sign convention on the cross-weighted mid, which is the classic microprice bug
and is invisible to goodness-of-fit.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.engine import book

ROOT = Path(__file__).resolve().parents[1]
LIVE = (ROOT / "data/reference/depth_london").is_dir()
live_only = pytest.mark.skipif(not LIVE, reason="London depth archive not present")


def _row(bid_px, bid_sz, ask_px, ask_sz, bid_ct=None, ask_ct=None, label="2026-04-15 08:15",
         recv_offset_s=59.889):
    """One synthetic snapshot, in the wide on-disk layout including both clocks."""
    n = book.LEVELS
    bid_ct = bid_ct or [1] * n
    ask_ct = ask_ct or [1] * n
    lab = pd.Timestamp(label, tz=book.LDN)
    d = {"ts_event": [lab], "ts_recv": [lab + pd.Timedelta(seconds=recv_offset_s)],
         "ts_in_delta": [12698], "sequence": [1]}
    for i in range(n):
        d[f"bid_px_{i:02d}"] = [bid_px[i]]
        d[f"ask_px_{i:02d}"] = [ask_px[i]]
        d[f"bid_sz_{i:02d}"] = [bid_sz[i]]
        d[f"ask_sz_{i:02d}"] = [ask_sz[i]]
        d[f"bid_ct_{i:02d}"] = [bid_ct[i]]
        d[f"ask_ct_{i:02d}"] = [ask_ct[i]]
    f = pd.DataFrame(d)
    f["ts"] = f.ts_recv
    f["ts_label"] = f.ts_event
    f["day"] = f.ts_event.dt.date
    return f.set_index("ts")


def _book(bid_heavy: bool):
    b = [100.0 - 0.25 * i for i in range(book.LEVELS)]
    a = [100.5 + 0.25 * i for i in range(book.LEVELS)]
    big, small = [10] * book.LEVELS, [2] * book.LEVELS
    return _row(b, big if bid_heavy else small, a, small if bid_heavy else big)


# ------------------------------------------------------------------ the clock
@live_only
def test_ts_event_is_floored_and_the_loader_undoes_it():
    """The whole layer rests on this. If the extraction ever changes, fail loudly."""
    f = book.depth_files()[0]
    raw = pd.read_csv(f, usecols=["ts_event", "ts_recv"])
    te = pd.to_datetime(raw.ts_event, utc=True, format="mixed")
    tr = pd.to_datetime(raw.ts_recv, utc=True, format="mixed")
    assert (te.dt.second == 0).all(), "ts_event no longer floored — re-derive the offset"
    lag = (tr - te).dt.total_seconds()
    assert 55 < lag.median() < 60.5, f"floor offset moved to {lag.median():.1f}s"

    d = book.load_depth([f])
    # The index must be the TRUE time, not the label — off by ~a minute from ts_event.
    assert (d.index - d["ts_label"]).median() > pd.Timedelta(seconds=55)


def test_loader_refuses_an_extraction_whose_lag_is_not_the_floor(tmp_path):
    """A genuine per-instant sample would have millisecond lag; the correction would
    then be a 60-second ERROR rather than a fix. Refuse rather than silently shift."""
    r = _row([100 - .25 * i for i in range(10)], [5] * 10,
             [100.5 + .25 * i for i in range(10)], [5] * 10, recv_offset_s=0.002)
    csv = tmp_path / "glbx-mdp3-20260415.mbp-10_condensed.csv"
    r.reset_index(drop=True).drop(columns=["ts_label"]).to_csv(csv, index=False)
    with pytest.raises(ValueError, match="floored-label assumption"):
        book.load_depth([csv])


def test_features_at_refuses_a_row_labelled_at_or_after_the_decision():
    """Reading row M for a decision at M is the 60-second lookahead, and it is the
    natural thing to write. It has to raise, not return."""
    F = book.features(_book(True))
    decision = pd.Timestamp("2026-04-15 08:15", tz=book.LDN)
    # index is ts_recv (08:15:59.9), so a decision at 08:16 legitimately sees it
    assert book.features_at(F, decision + pd.Timedelta(minutes=1)) is not None
    # but a frame mis-indexed on the LABEL must be caught
    G = F.copy()
    G.index = pd.DatetimeIndex(G["ts_label"])
    with pytest.raises(ValueError, match="lookahead"):
        book.features_at(G, decision)


def test_features_at_returns_none_before_any_snapshot():
    F = book.features(_book(True))
    assert book.features_at(F, pd.Timestamp("2026-04-15 07:00", tz=book.LDN)) is None


# ------------------------------------------------------------------ the signs
def test_depth_imbalance_is_buy_side_positive():
    """Matches footprint delta's B-A convention so the two layers can be read together."""
    assert book.features(_book(True))["imb_L10"].iloc[0] > 0
    assert book.features(_book(False))["imb_L10"].iloc[0] < 0


def test_weighted_mid_is_cross_weighted_not_same_side_weighted():
    """A LARGE BID pulls the weighted mid toward the ASK.

    Size is what must be consumed before price can travel that way, so the price leans
    away from the thick side. Weighting each price by its own size inverts this, fits
    exactly as well, and is backwards — the classic microprice bug.
    """
    f = book.features(_book(True)).iloc[0]
    assert f["wmid"] > f["mid"], "large bid must tilt the weighted mid UP toward the ask"
    assert f["wmid_tilt"] > 0
    g = book.features(_book(False)).iloc[0]
    assert g["wmid"] < g["mid"] and g["wmid_tilt"] < 0


def test_book_pressure_weights_near_size_more_than_far_size():
    n = book.LEVELS
    b = [100.0 - 0.25 * i for i in range(n)]
    a = [100.5 + 0.25 * i for i in range(n)]
    near = _row(b, [20] + [1] * (n - 1), a, [1] * n)
    far = _row(b, [1] * (n - 1) + [20], a, [1] * n)
    assert book.features(near)["press_bid"].iloc[0] > book.features(far)["press_bid"].iloc[0]


def test_imbalance_is_bounded_and_the_ladder_is_ordered():
    F = book.features(_book(True))
    for k in book.LADDER:
        v = F[f"imb_L{k}"].iloc[0]
        assert -1.0 <= v <= 1.0
    assert F["bid_L1"].iloc[0] <= F["bid_L3"].iloc[0] <= F["bid_L10"].iloc[0]


def test_average_order_size_uses_the_count_fields():
    """bid_ct_*/ask_ct_* are on all 295 days and were unused before this layer."""
    n = book.LEVELS
    r = _row([100 - .25 * i for i in range(n)], [12] + [1] * (n - 1),
             [100.5 + .25 * i for i in range(n)], [1] * n,
             bid_ct=[4] + [1] * (n - 1))
    assert book.features(r)["ord_sz_bid"].iloc[0] == pytest.approx(3.0)


# ------------------------------------------------------------ the guarded one
def test_ofi_proxy_refuses_without_the_flag():
    d = pd.concat([_book(True), _book(False)])
    with pytest.raises(book.BiasedFeatureError, match="BIASED"):
        book.ofi_proxy(d)


def test_ofi_proxy_names_itself_a_proxy_when_forced():
    """If someone insists, the column name must carry the warning into every artifact."""
    d = pd.concat([_book(True), _book(False)])
    s = book.ofi_proxy(d, i_know_this_is_biased=True)
    assert s.name == "ofi_PROXY"


def test_the_biased_error_says_what_would_make_it_valid():
    """A refusal that does not name the fix just relocates the argument."""
    with pytest.raises(book.BiasedFeatureError) as e:
        book.ofi_proxy(_book(True))
    m = str(e.value)
    assert "event-level MBP-10" in m and "wrong sign" in m.lower()


# ------------------------------------------------------------------ the seal
def test_sealed_span_is_guarded():
    p = Path("data/reference/depth_london_2023_24/glbx-mdp3-20230703.mbp-10_condensed.csv")
    with pytest.raises(PermissionError, match="SEALED"):
        book.load_depth([p])
    with pytest.raises(PermissionError):
        book.load_depth([Path("data/reference/depth_london/x_holdout_y.csv")])


@live_only
def test_default_file_list_excludes_the_sealed_span():
    assert all("2023_24" not in p.as_posix() and "holdout" not in p.name.lower()
               for p in book.depth_files())


# ------------------------------------------------------- causality declaration
def test_causality_declaration_passes_and_is_not_vacuous():
    from src.validation.window_causality import assert_causal, violations

    r = book.causality_declaration(["08:00", "09:30"])
    assert violations(r) == []
    assert_causal(r)
    assert len(r.conditions) >= 2, "a declaration with no conditions certifies nothing"
