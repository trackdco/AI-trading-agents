"""Tests for scripts/run_sequential_replay.py — the day-by-day chaining driver.

Mandatory properties: day N+1's briefing carries day N's playbook notes (the
whole point of the driver), stale response files from earlier parallel runs are
rejected by the freshness gate, invalid responses fail closed WITHOUT stopping
the run, and already-ingested days are skipped (resumability).
"""

import json
import os
import threading
import time as _time

import pandas as pd
import pytest

import scripts.run_regime_replay as harness
import scripts.run_sequential_replay as seq
from tests.test_regime_agent import VALID, _calendar, _fixture_frame

NY = "America/New_York"


def _vector_two_days() -> pd.DataFrame:
    row = {"day_type": "balanced", "imbal_share_20": 0.4, "imbal_share_10": 0.5,
           "trap_rate_10": 0.1, "range_pctl_20": 0.5, "gap_open_pts": 12.0,
           "streak_imbal": 0, "red_folder_today": 1}
    return pd.DataFrame([{"day": "2026-02-11", **row}, {"day": "2026-02-12", **row}])


@pytest.fixture()
def wired(tmp_path, monkeypatch):
    """Point every harness path at tmp and feed the two-day fixture inputs."""
    blob = tmp_path / "blobs"
    blob.mkdir()
    for mod in (harness, seq):
        monkeypatch.setattr(mod, "BLOB_DIR", blob)
        monkeypatch.setattr(mod, "VERDICTS", tmp_path / "verdicts.csv")
        monkeypatch.setattr(mod, "GATES", tmp_path / "gates.csv")
        monkeypatch.setattr(mod, "JOURNAL", tmp_path / "journal.csv")
    inputs = (_fixture_frame(), _vector_two_days(), _calendar(), None, None)
    monkeypatch.setattr(seq, "_load_inputs", lambda: inputs)
    return blob, tmp_path


def _respond(day: str, notes: str) -> str:
    v = dict(VALID, date=day, playbook_notes=notes)
    return json.dumps(v)


def _run_with_responder(blob, answer_fn, argv):
    """Run the driver with a background thread playing the transport role."""
    stop = threading.Event()

    def responder():
        while not stop.is_set():
            for req in blob.glob("*.request.txt"):
                day = req.name.split(".")[0]
                resp = blob / f"{day}.response.txt"
                if not resp.exists() or resp.stat().st_mtime < req.stat().st_mtime:
                    resp.write_text(answer_fn(day, req.read_text()))
                    os.utime(resp, (req.stat().st_mtime + 1,) * 2)
            _time.sleep(0.02)

    t = threading.Thread(target=responder, daemon=True)
    t.start()
    try:
        rc = seq.main(argv)
    finally:
        stop.set()
        t.join(timeout=2)
    return rc


def test_notes_chain_day_to_day(wired):
    blob, tmp = wired
    seen_prompts = {}

    def answer(day, prompt):
        seen_prompts[day] = prompt
        return _respond(day, f"NOTES-FROM-{day}")

    rc = _run_with_responder(blob, answer, [
        "--start", "2026-02-11", "--end", "2026-02-12",
        "--poll-seconds", "0.02", "--timeout-minutes", "0.2"])
    assert rc == 0
    # the chaining property: day 2's briefing/prompt embeds day 1's notes
    assert "NOTES-FROM-2026-02-11" in seen_prompts["2026-02-12"]
    assert "NOTES-FROM" not in seen_prompts["2026-02-11"]   # day 1 had no prior notes
    v = pd.read_csv(tmp / "verdicts.csv")
    assert list(v["date"]) == ["2026-02-11", "2026-02-12"]


def test_stale_response_is_not_accepted(wired):
    blob, tmp = wired
    # plant a stale response BEFORE the run (parallel-run leftover), older than any request
    stale = blob / "2026-02-11.response.txt"
    stale.write_text(_respond("2026-02-11", "STALE"))
    old = _time.time() - 3600
    os.utime(stale, (old, old))

    rc = seq.main(["--start", "2026-02-11", "--end", "2026-02-11",
                   "--poll-seconds", "0.02", "--timeout-minutes", "0.002"])
    assert rc == 1                                   # timed out waiting for a FRESH one
    assert not (tmp / "verdicts.csv").exists()       # stale content never ingested


def test_invalid_response_fails_closed_and_run_continues(wired):
    blob, tmp = wired

    def answer(day, prompt):
        return "not json at all" if day == "2026-02-11" else _respond(day, "ok")

    rc = _run_with_responder(blob, answer, [
        "--start", "2026-02-11", "--end", "2026-02-12",
        "--poll-seconds", "0.02", "--timeout-minutes", "0.2"])
    assert rc == 0                                   # bad day did not halt the run
    v = pd.read_csv(tmp / "verdicts.csv")
    assert list(v["date"]) == ["2026-02-12"]         # only the valid day ingested
    j = pd.read_csv(tmp / "journal.csv")
    assert len(j) == 2 and not bool(j.iloc[0]["valid"])   # failure journaled


def test_already_ingested_days_are_skipped(wired):
    blob, tmp = wired
    rc = _run_with_responder(blob, lambda d, p: _respond(d, "n1"), [
        "--start", "2026-02-11", "--end", "2026-02-11",
        "--poll-seconds", "0.02", "--timeout-minutes", "0.2"])
    assert rc == 0
    # second run over the same range: nothing to wait for, returns immediately
    rc2 = seq.main(["--start", "2026-02-11", "--end", "2026-02-11",
                    "--poll-seconds", "0.02", "--timeout-minutes", "0.002"])
    assert rc2 == 0
    assert len(pd.read_csv(tmp / "verdicts.csv")) == 1    # no duplicate ingest
