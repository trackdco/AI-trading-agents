"""The Colab holdout notebook must produce artifacts the repo can actually read.

A format mismatch is only discovered after an expensive MBP-10 pull has already been paid
for, so the condensers are checked here against the REAL committed artifacts their
consumers read:

    condense_ny      -> data/reference/depth_2025/nq_depth_*_ny.csv  (scripts/trade_matrix.py)
    condense_london  -> data/reference/depth_london/*.csv            (scripts/london_depth.py)
    condense_trades  -> data/reference/cvd/footprint_*.parquet       (scripts/champion_journal_cvd.py)

Also pins the DST behaviour: windows are declared in their native timezone, so the weeks
where US and UK daylight-saving disagree must produce different UTC offsets.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks/colab_holdout_pull.ipynb"
NY, LON, UTC = ZoneInfo("America/New_York"), ZoneInfo("Europe/London"), ZoneInfo("UTC")

pytestmark = pytest.mark.skipif(not NB.exists(), reason="notebook not built")


@pytest.fixture(scope="module")
def nbfn():
    """Exec the notebook's pure helper cells; no network, no databento import."""
    import ast

    nb = json.loads(NB.read_text())
    g = {"datetime": datetime, "timedelta": timedelta, "ZoneInfo": ZoneInfo,
         "np": np, "pd": pd, "NY": NY, "LON": LON, "UTC": UTC}
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if "def utc_window" not in src and "def condense_ny" not in src:
            continue
        # Keep ONLY the function definitions. The cells also carry demo/print code that
        # depends on notebook-level config; extracting the defs makes this independent
        # of whatever illustration code sits alongside them.
        tree = ast.parse(src)
        defs = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)],
                          type_ignores=[])
        # S102 is suppressed deliberately: the notebook IS the artifact under test and its
        # helpers exist only as cell source, so exec is the only way to exercise them
        # without duplicating the implementation — which would defeat the test.
        exec(compile(defs, "<notebook>", "exec"), g)  # noqa: S102
    return g


@pytest.fixture(scope="module")
def synthetic_mbp10():
    """600 ten-second MBP-10 snapshots = 100 minutes, starting 12:00Z on 2023-03-15."""
    rng = pd.date_range("2023-03-15T12:00:00Z", periods=600, freq="10s")
    d = pd.DataFrame({"ts_event": rng, "ts_recv": rng, "instrument_id": 42005804,
                      "price": 13000.0, "size": 1, "action": "A", "side": "B", "depth": 0,
                      "rtype": 10, "publisher_id": 1, "flags": 130, "ts_in_delta": 100,
                      "sequence": np.arange(600), "symbol": "NQ.v.0"})
    for i in range(10):
        d[f"bid_px_{i:02d}"] = 13000.0 - i * 0.25
        d[f"ask_px_{i:02d}"] = 13000.25 + i * 0.25
        d[f"bid_sz_{i:02d}"] = 2 + i
        d[f"ask_sz_{i:02d}"] = 3 + i
        d[f"bid_ct_{i:02d}"] = 1
        d[f"ask_ct_{i:02d}"] = 1
    return d.set_index("ts_recv")


@pytest.fixture(scope="module")
def synthetic_trades():
    rng = pd.date_range("2023-03-15T12:00:00Z", periods=1000, freq="1s")
    return pd.DataFrame({
        "ts_event": rng, "ts_recv": rng, "instrument_id": 42005804,
        "price": 13000.0 + np.random.RandomState(0).randint(-8, 8, 1000) * 0.25,
        "size": np.random.RandomState(1).randint(1, 5, 1000),
        "side": np.random.RandomState(2).choice(["B", "A"], 1000)}).set_index("ts_recv")


# --------------------------------------------------------------------- DST ---

def test_sealed_day_list_matches_preregistration(nbfn):
    """The notebook's embedded days must hash to the committed pre-registration."""
    import hashlib
    nb = json.loads(NB.read_text())
    src = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    assert "SEALED_SHA256" in src
    days = pd.read_csv(ROOT / "data/reference/holdout_2023_24_days.csv", dtype=str)["day"].tolist()
    digest = hashlib.sha256("\n".join(days).encode()).hexdigest()
    assert digest in src, "notebook day list is out of sync — re-run scripts/build_colab_notebook"


def test_us_uk_dst_divergence_week(nbfn):
    """2023-03-15: US on EDT, UK still on GMT. Native-tz windows must reflect that."""
    ny_start, _ = nbfn["utc_window"]("2023-03-15", NY, (8, 0), (11, 0))
    lon_start, _ = nbfn["utc_window"]("2023-03-15", LON, (8, 0), (10, 0))
    assert ny_start.endswith("T12:00:00")    # 08:00 EDT
    assert lon_start.endswith("T08:00:00")   # 08:00 GMT
    assert int(ny_start[11:13]) - int(lon_start[11:13]) == 4


@pytest.mark.parametrize("day,tz,hm,expect", [
    ("2023-01-11", NY, (8, 0), "T13:00:00"),    # EST
    ("2023-07-12", NY, (8, 0), "T12:00:00"),    # EDT
    ("2023-01-11", LON, (8, 0), "T08:00:00"),   # GMT
    ("2023-07-12", LON, (8, 0), "T07:00:00"),   # BST
])
def test_window_offsets(nbfn, day, tz, hm, expect):
    start, _ = nbfn["utc_window"](day, tz, hm, (23, 0))
    assert start.endswith(expect)


def test_ny_depth_window_covers_every_canon_fill():
    """The NY depth window was trimmed 11:00 -> 10:30 (Angus, golden = 09:40-10:15).

    Depth is read AT the fill minute, so the window must outlast the latest fill the canon
    has ever taken. Guards against trimming it below a real fill to save data.
    """
    src = "\n".join("".join(c["source"]) for c in json.loads(NB.read_text())["cells"]
                    if c["cell_type"] == "code")
    m = re.search(r'"ny":\s*\(NY,\s*\((\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\)\)', src)
    assert m, "could not find the ny depth window in the notebook"
    start_min = int(m.group(1)) * 60 + int(m.group(2))
    end_min = int(m.group(3)) * 60 + int(m.group(4))

    book = pd.read_parquet(ROOT / "output/canon_book.parquet")
    fills = book.loc[book["size"] > 0, "fillhm"]
    assert start_min <= fills.min(), f"window starts {start_min} after earliest fill {fills.min()}"
    assert end_min >= fills.max(), f"window ends {end_min} before latest fill {fills.max()}"
    # the whole candidate universe, not just what got taken
    assert end_min >= book["fillhm"].max(), "window ends before the latest candidate fill"


def test_trades_window_spans_overnight_without_overlap(nbfn):
    s, e = nbfn["trades_window"]("2023-03-15")
    assert s.startswith("2023-03-14") and e.startswith("2023-03-15")
    _, end_a = nbfn["trades_window"]("2023-03-15")
    start_b, _ = nbfn["trades_window"]("2023-03-16")
    assert end_a <= start_b, "consecutive days overlap — concat would double-count minutes"


# ------------------------------------------------------------- NY depth ---

def test_condense_ny_matches_committed_format(nbfn, synthetic_mbp10):
    real = pd.read_csv(ROOT / "data/reference/depth_2025/nq_depth_2025-06-02_ny.csv")
    out = nbfn["condense_ny"](synthetic_mbp10.copy(), "2023-03-15")
    assert list(out.columns) == list(real.columns)
    assert set(out["side"]) == {"bid", "ask"}
    assert out.ts.nunique() == 100
    assert (out.groupby("ts").size() == 20).all()
    assert out["size"].dtype.kind == "i"
    assert str(out.ts.iloc[0]).startswith("2023-03-15 08:00:00-04:00")


def test_condense_ny_decodes_fixed_point_prices(nbfn, synthetic_mbp10):
    """to_df() may hand back 1e-9 ints depending on databento version."""
    as_float = nbfn["condense_ny"](synthetic_mbp10.copy(), "2023-03-15")
    as_int = synthetic_mbp10.copy()
    for c in [c for c in as_int.columns if "_px_" in c]:
        as_int[c] = (as_int[c] * 1e9).astype("int64")
    out = nbfn["condense_ny"](as_int, "2023-03-15")
    assert np.allclose(sorted(out.price.unique()), sorted(as_float.price.unique()))
    assert out.price.between(1000, 60000).all()


# --------------------------------------------------------- London depth ---

def test_condense_london_matches_committed_format(nbfn, synthetic_mbp10):
    real = pd.read_csv(ROOT / "data/reference/depth_london/glbx-mdp3-20250602.mbp-10_condensed.csv")
    out = nbfn["condense_london"](synthetic_mbp10.copy(), "2023-03-15")
    assert not [c for c in real.columns if c not in out.columns]
    assert list(out.columns)[:len(real.columns)] == list(real.columns), "column order drifted"
    assert len(out) == 100
    ts = pd.to_datetime(out.ts_event, utc=True)
    assert (ts.dt.second == 0).all() and (ts.dt.microsecond == 0).all()


def test_london_depth_loader_reads_our_output(nbfn, synthetic_mbp10):
    """Replicates scripts/london_depth.py load_day() against our artifact."""
    out = nbfn["condense_london"](synthetic_mbp10.copy(), "2023-03-15")
    ts = pd.to_datetime(out.ts_event, utc=True).dt.tz_convert(NY)
    rows = []
    for lvl in range(10):
        for side, px, sz in (("bid", f"bid_px_{lvl:02d}", f"bid_sz_{lvl:02d}"),
                             ("ask", f"ask_px_{lvl:02d}", f"ask_sz_{lvl:02d}")):
            rows.append(pd.DataFrame({"ts": ts, "side": side, "price": out[px], "size": out[sz]}))
    long = pd.concat(rows, ignore_index=True).dropna(subset=["price"])
    long = long[long["size"] > 0]
    assert len(long) == 2000
    assert long.price.between(1000, 60000).all(), "prices left as 1e-9 ints"


# ------------------------------------------------------------ footprint ---

def test_condense_trades_matches_committed_schema(nbfn, synthetic_trades):
    real = pd.read_parquet(ROOT / "data/reference/cvd/footprint_apr2026.parquet")
    fp, _ = nbfn["condense_trades"](synthetic_trades.copy(), "2023-03-15")
    assert list(fp.columns) == list(real.columns)
    assert fp.ts_minute.dtype == real.ts_minute.dtype
    assert set(fp.side.unique()) <= {"B", "A"}
    assert fp.volume.sum() == synthetic_trades["size"].sum()


def test_footprint_volume_is_signed_int64(nbfn, synthetic_trades):
    """uint32 silently wraps on the B-A subtraction — see data/reference/cvd/README.md."""
    tr = synthetic_trades.copy()
    tr["size"] = tr["size"].astype("uint32")
    fp, _ = nbfn["condense_trades"](tr, "2023-03-15")
    assert fp.volume.dtype == np.int64 and fp.trades.dtype == np.int64
    signed = np.where(fp.side == "B", fp.volume, -fp.volume).sum()
    expect = np.where(synthetic_trades.side == "B",
                      synthetic_trades["size"], -synthetic_trades["size"]).sum()
    assert signed == expect


def test_cvd_sign_convention_is_buy_minus_sell(nbfn, synthetic_trades):
    """B = buy aggressor, A = sell aggressor; CVD = B - A (champion_journal_cvd.py)."""
    fp, _ = nbfn["condense_trades"](synthetic_trades.copy(), "2023-03-15")
    signed = np.where(fp.side == "B", fp.volume, -fp.volume).sum()
    raw = np.where(synthetic_trades.side == "B",
                   synthetic_trades["size"], -synthetic_trades["size"]).sum()
    assert signed == raw


def test_band_clean_drops_back_month_prints(nbfn, synthetic_trades):
    tr = synthetic_trades.copy()
    tr.loc[tr.index[0], "price"] = 25000.0        # a calendar-spread / back-month print
    fp, dropped = nbfn["condense_trades"](tr, "2023-03-15")
    assert 25000.0 not in set(fp.price)
    assert dropped > 0
