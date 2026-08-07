"""Gold + London feature parity — the live library must reproduce the stored matrices.

P2 (live feature-matrix assembly) is only worth anything if a feature computed live equals
the value the frozen thresholds were fit against. So these are not unit tests against
hand-made frames: each one recomputes a column with `src/canon/features.py` and asserts it
equals the STORED research artifact, to the decimal, on real trades.

Covered here (the columns the gold + London scorers read that the pre-existing depth /
tape / VWAP families did not):

  gold   bp5opp, lon_slope_d          vs output/canon_book.parquet / gold_quality.parquet
         netpath_30, bbw_state,       vs output/badpa_matrix.parquet
         churn_flow_30
         on_extreme_age (day form)    vs output/canon_book.parquet
  London opp5, on_extreme_age (trade  vs output/london_canon_features.parquet
         form), cvd_ASIA, on_range,   vs output/london_matrix.parquet
         ent_on_pos

NOT covered, and deliberately not faked: `trigdens_30` needs the v2 trigger caches
(output/triggers_*_ob_v2.csv), which are regenerated artifacts absent from the repo. The
port is a straight count over trigger timestamps; it stays unverified until those caches
exist on the machine running this, and that gap is stated rather than papered over.

Everything skips (never silently passes) when its artifact is missing.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.canon.features import (
    badpa_features,
    bp5opp,
    london_session_features,
    lon_slope_d,
    on_extreme_age_day,
    on_extreme_age_trade,
    opp5,
)

NY = "America/New_York"
SAMPLE = 120                      # real rows per column — enough to catch a definition drift
MASTER = "data/reference/nq_1m_master.parquet"
FEB_JUL = "data/reference/nq_1m_feb_jul2026.parquet"


def _need(*paths: str):
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        pytest.skip(f"artifact(s) absent, parity runs where the data lives: {missing}")


def _same(a, b, tol: float = 1e-9) -> bool:
    """NaN==NaN counts as equal; otherwise compare to `tol`."""
    a_nan, b_nan = a != a, b != b
    if a_nan or b_nan:
        return a_nan and b_nan
    return abs(float(a) - float(b)) <= tol


@pytest.fixture(scope="module")
def fp() -> pd.DataFrame:
    _need("output/fp_minutes.parquet")
    m = pd.read_parquet("output/fp_minutes.parquet")
    m.index = pd.DatetimeIndex(m.index)
    return m.sort_index()


@pytest.fixture(scope="module")
def bars() -> pd.DataFrame:
    _need(MASTER, FEB_JUL)
    mb = pd.read_parquet(MASTER)
    fb = pd.read_parquet(FEB_JUL)
    b = (pd.concat([mb, fb], ignore_index=True).drop_duplicates("ts_event")
         .sort_values("ts_event").reset_index(drop=True))
    return b.assign(mi=b.ts_event.dt.tz_convert(NY)).set_index("mi").sort_index()


def _report(name: str, checked: int, bad: list) -> None:
    assert checked, f"{name}: nothing checked — sample selection is broken, not passing"
    assert not bad, f"{name}: {len(bad)}/{checked} mismatch, first 3: {bad[:3]}"


# ---- gold quality --------------------------------------------------------------------

def test_bp5opp_and_lon_slope_match_the_gold_quality_matrix(fp):
    """Both gold-quality inputs (T2's absorption bit and LONSLOPE) on real gold trades.

    Sourced from gold_quality.parquet, which IS the artifact that defines these columns —
    canon_book carries them too but only populates them on gold-window rows, so checking
    against it would compare a real value to a merge-artifact NaN on every pre trade."""
    _need("output/gold_quality.parquet", "output/trade_matrix.parquet")
    gq = pd.read_parquet("output/gold_quality.parquet")
    tm = pd.read_parquet("output/trade_matrix.parquet")[["day", "book", "fill", "direction"]]
    rows = gq.merge(tm, on=["day", "book", "fill"], how="left")
    rows = rows.dropna(subset=["direction"]).head(SAMPLE)
    bad_b, bad_l, n = [], [], 0
    for t in rows.itertuples():
        f = pd.Timestamp(t.fill).tz_convert(NY)
        n += 1
        if not _same(bp5opp(fp, t.direction, f), t.bp5opp):
            bad_b.append((t.day, bp5opp(fp, t.direction, f), t.bp5opp))
        sess = fp[fp.sday == t.day]
        if not _same(lon_slope_d(sess, t.direction), t.lon_slope_d):
            bad_l.append((t.day, lon_slope_d(sess, t.direction), t.lon_slope_d))
    _report("bp5opp", n, bad_b)
    _report("lon_slope_d", n, bad_l)


def test_bp5opp_is_the_thresholded_form_of_opp5(fp):
    """The two 5-minute-opposition columns come from ONE primitive on purpose — this pins
    the relationship so a future edit can't drift them apart (bp5opp == opp5 >= 3)."""
    _need("output/london_canon_features.parquet")
    lf = pd.read_parquet("output/london_canon_features.parquet")
    checked = 0
    for t in lf.dropna(subset=["opp5"]).head(60).itertuples():
        f = pd.Timestamp(t.fill).tz_convert(NY)
        raw, flag = opp5(fp, t.direction, f), bp5opp(fp, t.direction, f)
        if raw == raw and flag == flag:
            assert flag == float(raw >= 3), (t.fill, raw, flag)
            checked += 1
    assert checked, "no comparable rows"


# ---- badpa ---------------------------------------------------------------------------

def test_badpa_columns_match_the_stored_matrix(fp, bars):
    """netpath_30 / bbw_state / churn_flow_30 — the gold PAQ and X inputs, plus the
    Layer-2e cold-grind input — against badpa_matrix.parquet."""
    _need("output/badpa_matrix.parquet")
    bp = pd.read_parquet("output/badpa_matrix.parquet")
    cols = ["netpath_30", "bbw_state", "churn_flow_30"]
    bad: dict[str, list] = {c: [] for c in cols}
    n = 0
    for t in bp.head(SAMPLE).itertuples():
        f = pd.Timestamp(t.fill).tz_convert(NY)
        mine = badpa_features(bars, fp, np.nan, f)
        n += 1
        for c in cols:
            if not _same(mine.get(c, np.nan), getattr(t, c)):
                bad[c].append((t.day, mine.get(c, np.nan), getattr(t, c)))
    for c in cols:
        _report(c, n, bad[c])


# ---- the two on_extreme_age definitions ----------------------------------------------

def test_gold_on_extreme_age_is_the_completed_overnight_day_form(fp):
    _need("output/canon_book.parquet")
    cb = pd.read_parquet("output/canon_book.parquet")
    if "on_extreme_age" not in cb.columns:
        pytest.skip("canon_book lacks on_extreme_age")
    hm = fp.index.hour * 60 + fp.index.minute
    on = fp[(hm >= 1080) | (hm < 480)]                    # 18:00-08:00 ET
    bad, n = [], 0
    for t in cb.dropna(subset=["on_extreme_age"]).drop_duplicates("day").head(80).itertuples():
        mine = on_extreme_age_day(on[on.sday == t.day])
        n += 1
        if not _same(mine, t.on_extreme_age):
            bad.append((t.day, mine, t.on_extreme_age))
    _report("on_extreme_age_day", n, bad)


def test_london_on_extreme_age_is_the_per_trade_minutes_form(bars):
    _need("output/london_canon_features.parquet")
    lf = pd.read_parquet("output/london_canon_features.parquet")
    bad, n = [], 0
    for t in lf.dropna(subset=["on_extreme_age", "entry"]).head(SAMPLE).itertuples():
        f = pd.Timestamp(t.fill).tz_convert(NY)
        sess0 = (f - pd.Timedelta(hours=18)).normalize() + pd.Timedelta(hours=18)
        w = bars.loc[sess0: f - pd.Timedelta(minutes=1)]
        mine = on_extreme_age_trade(w, t.entry, f)
        n += 1
        if not _same(mine, t.on_extreme_age):
            bad.append((str(t.fill)[:16], mine, t.on_extreme_age))
    _report("on_extreme_age_trade", n, bad)


def test_the_two_on_extreme_age_forms_really_are_different(fp, bars):
    """Guard the naming split: if these ever coincide, someone has quietly unified two
    definitions that the two scorers do NOT share, and one lane is then being fed the
    other's number."""
    _need("output/london_canon_features.parquet")
    lf = pd.read_parquet("output/london_canon_features.parquet")
    hm = fp.index.hour * 60 + fp.index.minute
    on = fp[(hm >= 1080) | (hm < 480)]
    differ = compared = 0
    for t in lf.dropna(subset=["on_extreme_age", "entry"]).head(40).itertuples():
        f = pd.Timestamp(t.fill).tz_convert(NY)
        sess0 = (f - pd.Timedelta(hours=18)).normalize() + pd.Timedelta(hours=18)
        day_form = on_extreme_age_day(on[on.sday == t.day])
        trade_form = on_extreme_age_trade(bars.loc[sess0: f - pd.Timedelta(minutes=1)],
                                          t.entry, f)
        if day_form == day_form and trade_form == trade_form:
            compared += 1
            differ += int(abs(day_form - trade_form) > 1e-9)
    assert compared, "no comparable rows"
    assert differ > compared * 0.5, (
        f"the two on_extreme_age forms agreed on {compared - differ}/{compared} rows — "
        "they are supposed to be different features sharing a name")


# ---- London session ------------------------------------------------------------------

def test_london_session_features_match_the_stored_matrix(fp, bars):
    """cvd_ASIA / on_range / ent_on_pos — London's ASIA and ROOM inputs. Note cvd_ASIA is
    the FIRST 8 HOURS from the 18:00 anchor (18:00-02:00), NOT the 18:00-03:00 window used
    elsewhere; getting that wrong is exactly what this asserts against."""
    _need("output/london_matrix.parquet")
    lm = pd.read_parquet("output/london_matrix.parquet")
    cols = ["cvd_ASIA", "on_range", "ent_on_pos"]
    if not set(cols) <= set(lm.columns):
        pytest.skip("london_matrix lacks the session columns")
    bad: dict[str, list] = {c: [] for c in cols}
    n = 0
    for t in lm.dropna(subset=["entry"]).head(SAMPLE).itertuples():
        f = pd.Timestamp(t.fill).tz_convert(NY)
        sess0 = (f - pd.Timedelta(hours=18)).normalize() + pd.Timedelta(hours=18)
        mine = london_session_features(fp.loc[sess0: f - pd.Timedelta(minutes=1)],
                                       bars.loc[sess0: f - pd.Timedelta(minutes=1)],
                                       t.entry, sess0)
        n += 1
        for c in cols:
            if not _same(mine.get(c, np.nan), getattr(t, c)):
                bad[c].append((str(t.fill)[:16], mine.get(c, np.nan), getattr(t, c)))
    for c in cols:
        _report(c, n, bad[c])


def test_london_opp5_matches_the_stored_features(fp):
    _need("output/london_canon_features.parquet")
    lf = pd.read_parquet("output/london_canon_features.parquet")
    bad, n = [], 0
    for t in lf.dropna(subset=["opp5"]).head(SAMPLE).itertuples():
        f = pd.Timestamp(t.fill).tz_convert(NY)
        mine = opp5(fp, t.direction, f)
        n += 1
        if not _same(mine, t.opp5):
            bad.append((str(t.fill)[:16], mine, t.opp5))
    _report("opp5", n, bad)


# ---- no-lookahead guards --------------------------------------------------------------

def test_windows_never_read_the_fill_minute_or_later(fp, bars):
    """Every window here must end at fill-1min. Feed a tape/bars frame that continues well
    past the fill and assert the answers are unchanged — the cheapest possible standing
    check that a future edit hasn't widened a slice into the future."""
    _need("output/london_matrix.parquet")
    lm = pd.read_parquet("output/london_matrix.parquet")
    row = lm.dropna(subset=["entry"]).iloc[0]
    f = pd.Timestamp(row.fill).tz_convert(NY)
    sess0 = (f - pd.Timedelta(hours=18)).normalize() + pd.Timedelta(hours=18)

    truncated_fp = fp.loc[: f - pd.Timedelta(minutes=1)]
    truncated_bars = bars.loc[sess0: f - pd.Timedelta(minutes=1)]
    full_bars = bars.loc[sess0: f + pd.Timedelta(hours=6)]        # deliberately post-fill

    assert _same(opp5(truncated_fp, "long", f), opp5(fp, "long", f))
    assert _same(bp5opp(truncated_fp, "long", f), bp5opp(fp, "long", f))
    a = badpa_features(truncated_bars, truncated_fp, float(row.entry), f)
    b = badpa_features(full_bars, fp, float(row.entry), f)
    for k in set(a) | set(b):
        assert _same(a.get(k, np.nan), b.get(k, np.nan)), k
    assert _same(on_extreme_age_trade(truncated_bars, float(row.entry), f),
                 on_extreme_age_trade(full_bars.loc[: f - pd.Timedelta(minutes=1)],
                                      float(row.entry), f))
