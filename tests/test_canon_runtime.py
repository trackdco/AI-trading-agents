"""Structural proof that canon-relay cannot recompute — it only passes bytes through.

If the relay ever did its own check/score/size, it would "correct" a perturbed verdict.
It does not: relay(perturbed) == perturbed, byte-for-byte. Correctness lives entirely in
the exact Python canon upstream; the relay can preserve or corrupt, never invent.
"""
from __future__ import annotations

import json

from src.desk.canon_runtime import book_for_clock, relay_one


def test_relay_passes_bytes_through_unchanged():
    verdict = {"session": "NY", "day": "2025-06-17", "fill": "2025-06-17T12:01:00+00:00",
               "direction": "long", "conviction": 1.0, "risk_pts": 26.25,
               "micros": 4, "pl": -214.0}
    assert relay_one(json.dumps(verdict)) == verdict


def test_relay_does_not_fix_a_wrong_number():
    # a deliberately corrupted size/pl must flow through UNCHANGED — the relay never
    # recomputes to "correct" it (that is what proves it holds no scoring/sizing logic)
    bad = {"session": "NY", "day": "2025-06-17", "fill": "2025-06-17T12:01:00+00:00",
           "direction": "long", "conviction": 99.0, "risk_pts": 26.25,
           "micros": 999, "pl": -999999.0}
    out = relay_one(json.dumps(bad))
    assert out["micros"] == 999 and out["pl"] == -999999.0 and out["conviction"] == 99.0


def test_router_is_a_clock_lookup():
    import pandas as pd
    # 12:01 UTC = 08:01 ET -> NY (pre); 07:30 UTC = 03:30 ET -> LONDON; 20:00 UTC -> NONE
    assert book_for_clock(pd.Timestamp("2025-06-17T12:01:00Z")) == "NY"
    assert book_for_clock(pd.Timestamp("2025-06-17T07:30:00Z")) == "LONDON"
    assert book_for_clock(pd.Timestamp("2025-06-17T20:00:00Z")) == "NONE"
