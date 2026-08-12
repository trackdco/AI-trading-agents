"""GATE L1 timezone tripwire — the house speciality (3 DST bugs in repo history).

Every result in CEILING-TEST.md and VERDICT.md rests on the release bar being
the bar that actually contains the release. If the ET conversion is wrong by an
hour in one half of the year, every measurement silently shifts and every
verdict is worthless.

These tests assert against the BARS, not against the tz library — a library can
be self-consistently wrong. The check is that the release minute is where the
volume actually lands, in BOTH a January (EST, -05:00) and a July (EDT, -04:00)
event.

Skipped when the bar files are absent, so the suite still runs anywhere.
"""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
import pytest

REPO = os.path.join(os.path.dirname(__file__), "..", "..")
BARS_GLOB = os.path.join(REPO, "glbx-mdp3-*.ohlcv-1m.csv.zst")
EVENTS = os.path.join(os.path.dirname(__file__), "..", "output",
                      "events.parquet")

pytestmark = pytest.mark.skipif(
    not glob.glob(BARS_GLOB) or not os.path.exists(EVENTS),
    reason="bar files or events.parquet not present")


@pytest.fixture(scope="module")
def data():
    from newslab.census import load_bars
    bars = load_bars(BARS_GLOB)
    ev = pd.read_parquet(EVENTS)
    ev = ev[(ev["release_kind"] == "print") & (ev["family"] == "cpi")]
    return bars, ev


def _release_window(bars, ts, before=4, after=3):
    T = ts.floor("min")
    return T, bars.loc[T - pd.Timedelta(minutes=before):
                       T + pd.Timedelta(minutes=after)]


@pytest.mark.parametrize("month,offset", [("01", "-0500"), ("07", "-0400")])
def test_cpi_release_bar_is_0830_et_in_both_dst_halves(data, month, offset):
    bars, ev = data
    row = ev[ev["date"].str[5:7] == month].iloc[0]
    T, win = _release_window(bars, row["ts_release_et"])
    assert T.strftime("%H:%M") == "08:30"
    assert T.strftime("%z") == offset          # EST vs EDT actually differ
    # the release minute must be where the volume lands
    assert win["volume"].idxmax() == T, (
        f"{row['date']}: max volume at {win['volume'].idxmax()}, not {T}")


def test_release_bar_alignment_holds_across_the_whole_table(data):
    """No systematic timestamp offset: the max-volume bar sits on T, and any
    drift is FORWARD (the reaction continuing), never backward."""
    bars, _ = data
    ev = pd.read_parquet(EVENTS)
    ev = ev[(ev["release_kind"] == "print")
            & (ev["family"].isin(["cpi", "nfp", "ppi", "pce", "fomc"]))]
    offs = []
    for _, e in ev.iterrows():
        T = e["ts_release_et"].floor("min")
        if T not in bars.index:
            continue
        _, win = _release_window(bars, e["ts_release_et"], 3, 3)
        if len(win) < 5:
            continue
        offs.append(int((win["volume"].idxmax() - T).total_seconds() // 60))
    s = pd.Series(offs)
    assert len(s) > 100
    assert (s == 0).mean() > 0.80, f"only {(s == 0).mean():.1%} aligned on T"
    # a backward skew would mean the stamps are late — that must stay rare
    assert (s < 0).mean() < 0.02, f"{(s < 0).mean():.1%} peak BEFORE the stamp"
