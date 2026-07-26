"""The sequential live scorer must reproduce the batch books ROW-FOR-ROW (item 4 core).

The stored artifacts are the truth: output/canon_book.parquet is build_canon's own output
(the NY canon, pre/gold, all layers incl. governor + cold trail + day ladder) and
output/london_canon_book.parquet is build_london's. Every row is replayed through
NYScorer/LondonScorer in fill order and score/size/governor/nth/pl must match exactly.
A third test rebuilds the news-gated book (the arming-reference construction from
scripts/canon_news_clean.py) and replays it with the same gate wired into the scorer.
"""
from __future__ import annotations

import math

import pandas as pd
import pytest

from src.canon.scorer import LondonScorer, NYScorer, eff_dollars, ny_checks

CHECK_COLS_NY = ["W", "F", "Tp", "G", "C", "D", "Tc", "X", "AGE", "PAQ",
                 "WALLSZ", "BIGFD", "T2", "TRIG", "VWAPD", "LONSLOPE"]


@pytest.fixture(scope="module")
def book():
    return pd.read_parquet("output/canon_book.parquet")


@pytest.fixture(scope="module")
def lonbook():
    return pd.read_parquet("output/london_canon_book.parquet")


def _same(a: float, b: float) -> bool:
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    return a == b


def _replay_ny(book: pd.DataFrame, news_gate=None) -> list:
    s = NYScorer(news_gate=news_gate)
    out = []
    for row in book.to_dict("records"):
        v = s.decide(row)
        pl = s.settle(v, r_3=row["r_3"], fw_3=row["fw_3"], dollars=row["dollars"])
        out.append((v, pl))
    return out


def test_ny_checks_match_the_stored_book_bit_for_bit(book):
    for i, row in enumerate(book.to_dict("records")):
        c = ny_checks(row)
        for k in CHECK_COLS_NY:
            assert _same(c[k], float(row[k])), (i, k, c[k], row[k])


def test_ny_full_stack_parity_every_row(book):
    """score, size, governor, nth, Q, struct and pl — the ENTIRE stack, sequentially."""
    for i, ((v, pl), row) in enumerate(zip(_replay_ny(book), book.to_dict("records"))):
        assert v.score == row["score"], (i, "score", v.score, row["score"])
        assert v.size == row["size"], (i, "size", v.size, row["size"], v.vetoes)
        assert v.governor == row["governor"], (i, "governor", v.governor, row["governor"])
        assert _same(v.Q, float(row["Q"])), (i, "Q", v.Q, row["Q"])
        assert _same(v.struct, float(row["struct"])), (i, "struct")
        nth = float("nan") if v.nth is None else float(v.nth)
        assert _same(nth, float(row["nth"])), (i, "nth", v.nth, row["nth"])
        assert pl == pytest.approx(row["pl"], abs=1e-9), (i, "pl", pl, row["pl"])


def test_ny_eff_dollars_and_cut3_parity(book):
    for i, row in enumerate(book.to_dict("records")):
        cut, eff = eff_dollars(r_3=row["r_3"], fw_3=row["fw_3"],
                               risk=row["risk"], dollars=row["dollars"])
        assert cut == bool(row["cut3"]), (i, "cut3")
        assert eff == pytest.approx(row["eff_dollars"], abs=1e-9), (i, "eff")


def test_ny_book_covers_both_windows_and_all_layers(book):
    """The parity above is only meaningful if the replayed sample actually exercises the
    stack: both windows, sized and vetoed rows, a fired governor is NOT guaranteed — but
    escalations, quality zeroes and the day ladder must all appear in 713 rows."""
    assert set(book.win_) == {"pre", "gold"}
    assert (book["size"] == 0).any() and (book["size"] > 0).any()
    assert (book.Q <= 1).any() and (book.Q >= 3).any()
    assert book.cut3.any()
    assert (book.nth >= 2).any()


def test_ny_news_gated_rebuild_parity():
    """The arming-reference construction: conf_PM <- pm_sofar_conf, news gate wired in.
    Rebuild via the batch (scripts/canon_mechanical.build_canon) and replay sequentially
    with the SAME gate object — every output must match again."""
    from scripts.canon_mechanical import build_canon
    from src.canon.news_gate import NewsGate

    T = pd.read_parquet("output/trade_matrix.parquet")
    T["conf_PM"] = T["pm_sofar_conf"]
    gate = NewsGate.load()
    C = build_canon(T, news_gate=gate)
    for i, ((v, pl), row) in enumerate(zip(_replay_ny(C, news_gate=gate),
                                           C.to_dict("records"))):
        assert v.score == row["score"] and v.size == row["size"], (i, v.vetoes)
        assert v.governor == row["governor"], (i, "governor")
        assert pl == pytest.approx(row["pl"], abs=1e-9), (i, "pl")
    # and the gate actually vetoed something in this sample, or the test proves nothing
    n_vetoed = sum("news_blackout" in v.vetoes for v, _ in _replay_ny(C, news_gate=gate))
    assert n_vetoed > 0


def test_london_full_stack_parity_every_row(lonbook):
    s = LondonScorer()
    for i, row in enumerate(lonbook.to_dict("records")):
        v = s.decide(row)
        assert v.score == row["score"], (i, "score", v.score, row["score"])
        assert v.size == row["size"], (i, "size", v.size, row["size"], v.vetoes)
        nth = float("nan") if v.nth is None else float(v.nth)
        assert _same(nth, float(row["nth"])), (i, "nth", v.nth, row["nth"])
        assert row["dollars"] * v.size == pytest.approx(row["pl"], abs=1e-9), (i, "pl")
        for k in ("W", "FAR", "ROOM", "ASIA"):
            assert v.checks[k] == float(row[k]), (i, k)
        assert v.checks["room_R"] == pytest.approx(row["room_R"], nan_ok=True), (i, "room_R")


def test_london_book_exercises_the_stack(lonbook):
    assert (lonbook["size"] == 0).any() and (lonbook["size"] == 1.5).any()
    assert (lonbook["size"] == 0.25).any() or (lonbook["size"] == 0.5).any()
    assert (lonbook.nth >= 2).any()
    assert (lonbook.pattern == "B").any()


def test_settle_discipline_is_enforced():
    """decide() before settling the prior verdict must raise — the trails would be stale.
    A hard-gated verdict owes no settle."""
    book = pd.read_parquet("output/canon_book.parquet")
    row = book.to_dict("records")[0]
    s = NYScorer()
    v = s.decide(row)
    with pytest.raises(RuntimeError):
        s.decide(row)
    s.settle(v, r_3=row["r_3"], fw_3=row["fw_3"], dollars=row["dollars"])
    gated = dict(row, risk=3.0)                       # below the 7pt hard gate
    g = s.decide(gated)
    assert g.hard_gated and g.size == 0.0
    s.decide(row)                                     # no settle owed after a hard gate
