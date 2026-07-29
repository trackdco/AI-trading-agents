"""Tests for scripts/export_dashboard.py — THE DESK export.

The export is a faithful, deterministic view of the committed baseline_book: same
trade count and total P&L to the cent (the parity anchor), enriched from the trade/
london matrices, inventing nothing. Run from the repo root:
`python -m pytest tests/test_export_dashboard.py`
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from scripts.export_dashboard import SCHEMA, build_export  # noqa: E402

FIXED = "2026-07-24T00:00:00+00:00"
REQUIRED = {"id", "ts", "session", "book", "side", "pattern", "conviction",
            "entry", "exit", "risk_pts", "stop_pts", "micros", "contracts", "pnl", "r"}


def _baseline():
    return pd.read_parquet(ROOT / "output" / "baseline_book.parquet")


def test_total_pnl_matches_baseline_to_the_cent():
    obj = build_export(generated_at=FIXED)
    assert abs(obj["meta"]["total_pnl"] - float(_baseline()["pl"].sum())) < 0.01


def test_trade_count_matches_baseline():
    obj = build_export(generated_at=FIXED)
    assert obj["meta"]["trade_count"] == len(_baseline()) == len(obj["trades"])


def test_session_split_matches_baseline():
    obj = build_export(generated_at=FIXED)
    B = _baseline()
    ny = sum(t["session"] == "NY" for t in obj["trades"])
    lo = sum(t["session"] == "LONDON" for t in obj["trades"])
    assert ny == int((B.session == "NY").sum())
    assert lo == int((B.session == "LONDON").sum())


def test_schema_and_top_level_shape():
    obj = build_export(generated_at=FIXED)
    assert obj["meta"]["schema"] == SCHEMA == "desk-export/v2"
    assert set(obj) == {"meta", "trades", "spine_events"}
    assert obj["meta"]["source"] == "baseline_book"


def test_spine_events_empty_not_synthesised():
    assert build_export(generated_at=FIXED)["spine_events"] == []


def test_deterministic_byte_identical():
    a = json.dumps(build_export(generated_at=FIXED), sort_keys=True)
    b = json.dumps(build_export(generated_at=FIXED), sort_keys=True)
    assert a == b


def test_ids_unique():
    ids = [t["id"] for t in build_export(generated_at=FIXED)["trades"]]
    assert len(ids) == len(set(ids))


def test_required_fields_and_enums():
    for t in build_export(generated_at=FIXED)["trades"]:
        assert REQUIRED <= set(t), f"missing {REQUIRED - set(t)}"
        assert t["side"] in ("LONG", "SHORT")
        assert t["session"] in ("NY", "LONDON")


def test_checks_reported_missing_and_omitted():
    obj = build_export(generated_at=FIXED)
    assert "checks" in obj["meta"]["missing_fields"]
    assert all("checks" not in t for t in obj["trades"])


def test_conviction_and_micros_totals_match_baseline():
    obj = build_export(generated_at=FIXED)
    B = _baseline()
    assert round(sum(t["conviction"] for t in obj["trades"]), 4) == round(float(B["conviction"].sum()), 4)
    assert sum(t["micros"] for t in obj["trades"]) == int(B["micros"].sum())


def test_enrichment_present_for_every_trade():
    # the join is exact, so entry/exit/pattern/book must be populated for all 400
    obj = build_export(generated_at=FIXED)
    for t in obj["trades"]:
        assert t["entry"] is not None and t["exit"] is not None
        assert t["pattern"] is not None and t["book"] is not None
    assert obj["meta"]["missing_fields"] == ["checks"]
