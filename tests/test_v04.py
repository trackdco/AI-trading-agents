"""Tests for src/desk/v04.py and scripts/run_v04_replay.py — analog block injection,
fresh-eyes derivation, oracle/regret grading, and the chain+panel harness.
"""

import json
import os
import threading
import time as _time

import pandas as pd
import pytest

import scripts.run_v04_replay as v04run
from src.desk import v04
from tests.test_regime_agent import VALID, _calendar, _fixture_frame


# ------------------------------------------------------------------ unit: v04 module

def test_attach_analog_block_present_and_absent():
    b = {"date": "2026-06-08", "playbook_notes": "carry"}
    blk = {"k": 15, "majority_action": "ROTATION"}
    assert v04.attach_analog_block(b, blk)["analog_block"] == blk
    absent = v04.attach_analog_block(b, None)["analog_block"]
    assert isinstance(absent, str) and "no analog block" in absent
    assert "analog_block" not in b            # original untouched (copy semantics)


def test_as_fresh_eyes_strips_notes_only():
    b = {"date": "d", "playbook_notes": "war since Tuesday", "regime_vector": {"x": 1}}
    f = v04.as_fresh_eyes(b)
    assert f["playbook_notes"] == v04.FRESH_NOTES
    assert f["regime_vector"] == b["regime_vector"]      # facts identical
    assert b["playbook_notes"] == "war since Tuesday"    # original untouched


@pytest.mark.parametrize("e3,e4,exp", [
    (-100, -200, "FLAT"),      # both red -> FLAT (Angus rule)
    (0, 0, "FLAT"),            # nothing-day -> FLAT
    (500, 100, "ROTATION"),    # E3 (rotation book) wins
    (100, 900, "MOMENTUM"),    # E4 (momentum book) wins
    (300, 300, "ROTATION"),    # tie -> rotation (>=)
])
def test_oracle_action_angus_rule(e3, e4, exp):
    assert v04.oracle_action(e3, e4) == exp


def test_verdict_action_mapping():
    assert v04.verdict_action("war", False, 1.0) == "MOMENTUM"
    assert v04.verdict_action("balance", False, 0.5) == "ROTATION"
    assert v04.verdict_action("trap", False, 0.5) == "ROTATION"
    assert v04.verdict_action("event_risk", False, 0.5) == "FLAT"   # no committed structure
    assert v04.verdict_action("war", True, 0.0) == "FLAT"       # stand-down overrides
    assert v04.verdict_action("war", False, 0.0) == "FLAT"


def test_verdict_action_v06_event_day_that_trades_maps_to_its_book():
    # v0.6: event_risk no longer auto-FLAT — a traded event day maps to the armed book
    assert v04.verdict_action("event_risk", False, 0.25, ["continuation"]) == "MOMENTUM"
    assert v04.verdict_action("event_risk", False, 0.25, ["reversion"]) == "ROTATION"
    # structure overrides a conflicting regime label (engine gates the book by structure)
    assert v04.verdict_action("war", False, 0.5, ["reversion"]) == "ROTATION"
    # still FLAT when standing down regardless of structure
    assert v04.verdict_action("event_risk", True, 0.0, ["continuation"]) == "FLAT"


def test_v06_size_tiers_schema():
    from src.desk.regime_agent import RegimeVerdict
    base = dict(schema_version="1.0", agent_version="a" * 12, date="2026-03-06",
                regime="event_risk", directional_bias="long",
                permitted_structures=["continuation"], stand_down=False,
                confidence="medium", rationale="reduced-arm event day",
                cited_evidence=["x=1"], playbook_notes="")
    assert RegimeVerdict(**dict(base, size_multiplier=0.25)).size_multiplier == 0.25
    for bad in (0.75, 0.1, 0.3):
        with pytest.raises(Exception):
            RegimeVerdict(**dict(base, size_multiplier=bad))


def test_grade_day_regret_math(tmp_path, monkeypatch):
    books = pd.DataFrame([{"day": "D", "pl_e3": 900.0, "pl_e4": -100.0}]).set_index("day")
    # agent called MOMENTUM (E4=-100); oracle was ROTATION (E3=900)
    g = v04.grade_day("D", "MOMENTUM", books=books)
    assert g["oracle"] == "ROTATION" and not g["hit"]
    assert g["agent_pl"] == -100 and g["oracle_pl"] == 900
    assert g["regret"] == 1000                       # 900 - (-100)
    # a correct rotation call has zero regret
    assert v04.grade_day("D", "ROTATION", books=books)["regret"] == 0
    assert v04.grade_day("UNKNOWN", "FLAT", books=books) is None


def test_divergence_row_flags_disagreement():
    books = pd.DataFrame([{"day": "D", "pl_e3": 900.0, "pl_e4": -100.0}]).set_index("day")
    chained = dict(VALID, regime="war", permitted_structures=["continuation"],
                   stand_down=False, size_multiplier=1.0)                          # MOMENTUM
    fresh = dict(VALID, regime="balance", permitted_structures=["reversion"],
                 stand_down=False, size_multiplier=0.5)                            # ROTATION
    r = v04.divergence_row("D", chained, fresh, books=books)
    assert r["chained_action"] == "MOMENTUM" and r["fresh_action"] == "ROTATION"
    assert r["agree"] is False
    assert r["oracle"] == "ROTATION"
    assert r["fresh_right"] is True and r["chained_right"] is False   # fresh beat the frame


# ------------------------------------------------------------------ harness integration

def _vec_two_days():
    row = {"day_type": "balanced", "imbal_share_20": 0.4, "imbal_share_10": 0.5,
           "trap_rate_10": 0.1, "range_pctl_20": 0.5, "gap_open_pts": 12.0,
           "streak_imbal": 0, "red_folder_today": 1}
    return pd.DataFrame([{"day": "2026-02-11", **row}, {"day": "2026-02-12", **row}])


@pytest.fixture()
def wired(tmp_path, monkeypatch):
    inputs = (_fixture_frame(), _vec_two_days(), _calendar(), None, None)
    monkeypatch.setattr(v04run, "_load_inputs", lambda: inputs)
    # redirect all v04 output under tmp
    monkeypatch.setattr(v04run, "_paths", lambda arm: {
        "blobs": (tmp_path / "b" / arm), "verdicts": tmp_path / f"{arm}_v.csv",
        "gates": tmp_path / f"{arm}_g.csv", "fresh": tmp_path / f"{arm}_f.csv",
        "journal": tmp_path / f"{arm}_j.csv", "divergence": tmp_path / f"{arm}_d.csv",
        "ledger": tmp_path / f"{arm}_l.csv"} | {"_mk": (tmp_path / "b" / arm).mkdir(parents=True, exist_ok=True)})
    # deterministic analog block + known realized books for grading
    monkeypatch.setattr(v04, "load_analog_block",
                        lambda day, csv_path=None: {"k": 3, "majority_action": "ROTATION",
                                                    "mean_pl_if_rotation": 200,
                                                    "mean_pl_if_momentum": -150})
    books = pd.DataFrame([{"day": "2026-02-11", "pl_e3": 200.0, "pl_e4": -150.0},
                          {"day": "2026-02-12", "pl_e3": 200.0, "pl_e4": -150.0}]).set_index("day")
    monkeypatch.setattr(v04, "_load_books", lambda: books)
    return tmp_path


def _run(tmp, blobs, answer_fn, argv):
    stop = threading.Event()

    def responder():
        while not stop.is_set():
            for req in blobs.rglob("*.request.txt"):
                kind = req.name.split(".")[1]                 # chained | fresh
                day = req.name.split(".")[0]
                resp = req.with_name(f"{day}.{kind}.response.txt")
                if not resp.exists() or resp.stat().st_mtime < req.stat().st_mtime:
                    resp.write_text(answer_fn(day, kind, req.read_text()))
                    os.utime(resp, (req.stat().st_mtime + 1,) * 2)
            _time.sleep(0.02)

    t = threading.Thread(target=responder, daemon=True)
    t.start()
    try:
        rc = v04run.main(argv)
    finally:
        stop.set()
        t.join(timeout=2)
    return rc


def test_harness_emits_both_and_chained_carries_notes(wired):
    tmp = wired
    blobs = tmp / "b" / "armX"
    prompts = {}

    def answer(day, kind, prompt):
        prompts[(day, kind)] = prompt
        # fresh reads war/continuation (MOMENTUM, wrong book); chained reads
        # balance/reversion (ROTATION, the correct book for the fixture's books)
        regime, structs = (("war", ["continuation"]) if kind == "fresh"
                           else ("balance", ["reversion"]))
        notes = f"NOTE-{day}-{kind}"
        return json.dumps(dict(VALID, date=day, regime=regime,
                               permitted_structures=structs, size_multiplier=0.5,
                               playbook_notes=notes))

    rc = _run(tmp, blobs, answer, ["--arm", "armX", "--start", "2026-02-11",
                                   "--end", "2026-02-12", "--poll-seconds", "0.02",
                                   "--timeout-minutes", "0.3"])
    assert rc == 0
    # both requests carry the analog block
    assert '"analog_block"' in prompts[("2026-02-11", "chained")]
    assert '"analog_block"' in prompts[("2026-02-11", "fresh")]
    # fresh request has NO inherited notes; chained day-2 carries day-1 chained notes
    assert v04.FRESH_NOTES in prompts[("2026-02-12", "fresh")]
    assert "NOTE-2026-02-11-chained" in prompts[("2026-02-12", "chained")]
    assert "NOTE-2026-02-11-fresh" not in prompts[("2026-02-12", "chained")]
    # divergence detected + graded: fresh (war/MOMENTUM) wrong, chained (ROTATION) right
    D = pd.read_csv(tmp / "armX_d.csv")
    assert (~D.agree).all()
    assert D.chained_right.all() and (~D.fresh_right).all()
    L = pd.read_csv(tmp / "armX_l.csv")
    assert set(L.arm) == {"chained", "fresh"}


def test_harness_chained_failclosed_does_not_advance_notes(wired):
    tmp = wired
    blobs = tmp / "b" / "armY"

    def answer(day, kind, prompt):
        if day == "2026-02-11" and kind == "chained":
            return "garbage not json"
        return json.dumps(dict(VALID, date=day, regime="balance",
                               permitted_structures=["reversion"], size_multiplier=0.5,
                               playbook_notes=f"OK-{day}-{kind}"))

    rc = _run(tmp, blobs, answer, ["--arm", "armY", "--start", "2026-02-11",
                                   "--end", "2026-02-12", "--poll-seconds", "0.02",
                                   "--timeout-minutes", "0.3"])
    assert rc == 0
    v = pd.read_csv(tmp / "armY_v.csv")
    assert list(v.date) == ["2026-02-12"]         # bad chained day not ingested
    j = pd.read_csv(tmp / "armY_j.csv")
    assert (~j.valid.astype(bool)).any()          # failure journaled
