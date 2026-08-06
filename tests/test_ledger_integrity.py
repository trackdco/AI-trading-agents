"""Guards the trial ledger against the failure that produced four divergent copies.

The ledger forked into 268 / 764 / 255 / 58 rows across branches, with rows unique to
three of them -- including five NYA-IBC-01 sealed-holdout looks present on only one.
A spent holdout look cannot be reconstructed: re-deriving it would be a second look.
These tests exist so a careless merge cannot repeat that silently.
"""
from __future__ import annotations

import json

import pytest

from scripts.ledger_io import KEY, LEDGER, read, sort_key

#: Monotonic floor. The ledger may only grow. RAISE this deliberately when trials are
#: added; a merge that drops rows fails here instead of losing evidence quietly.
#: Any reduction requires an ANGUS ruling recorded in the commit message.
MIN_ROWS = 268


def _rows():
    return [json.loads(ln) for ln in LEDGER.read_text().splitlines() if ln.strip()]


def test_ledger_exists_and_is_jsonl():
    assert LEDGER.exists(), f"{LEDGER} missing -- the ledger is the DSR denominator"
    _rows()  # raises if any line is not valid JSON


def test_keys_unique():
    rows = _rows()
    seen, dupes = set(), []
    for r in rows:
        k = tuple(str(r.get(x, "")) for x in KEY)
        (dupes.append(k) if k in seen else seen.add(k))
    assert not dupes, f"duplicate (family, trial, era) keys -- a union merge collided: {dupes[:5]}"


def test_sorted_by_key():
    rows = _rows()
    assert rows == sorted(rows, key=sort_key), (
        "ledger is not sorted by (family, trial, era). Sorted order is what makes the "
        "union merge driver produce a readable diff -- rewrite via scripts.ledger_io.write")


def test_every_row_has_identity_and_a_declaration():
    missing = [
        (r.get("family"), r.get("trial"), [f for f in ("family", "trial", "era", "prereg")
                                           if not r.get(f)])
        for r in _rows()
        if not all(r.get(f) for f in ("family", "trial", "era", "prereg"))
    ]
    assert not missing, (
        "rows missing family/trial/era/prereg. An unlogged or undeclared trial rigs the "
        f"DSR denominator (BRAKE-HANDOFF §4): {missing[:5]}")


def test_row_count_never_decreases():
    n = len(_rows())
    assert n >= MIN_ROWS, (
        f"ledger has {n} rows, floor is {MIN_ROWS}. Rows were DROPPED. If this is a "
        "take-ours/take-theirs merge resolution, the sealed-holdout rows may be gone -- "
        "resolve by keyed union instead. Lowering MIN_ROWS needs an ANGUS ruling.")


def test_sealed_holdout_rows_are_present():
    """The rows that can never be reconstructed. Named explicitly so a merge cannot
    quietly lose them -- they existed on exactly one of the four forked ledgers."""
    rows = _rows()
    sealed = {(r["family"], r["trial"]) for r in rows
              if r.get("era") and any(t in str(r["era"]).lower()
                                      for t in ("seal", "hold", "23-24"))}
    required = {("NYA-IBC-01", "oof-look-B0_astaught"),
                ("NYA-IBC-01", "oof-look-B1_cap20"),
                ("NYA-IBC-01", "oof-look-B8_full"),
                ("NYA-IBC-01", "oof2-spec-flat"),
                ("NYA-IBC-01", "oof2-ladder")}
    assert required <= sealed, f"SEALED-LOOK ROWS LOST: {sorted(required - sealed)}"


def test_round_trip_is_stable():
    """read -> write must be a no-op, so the file never churns in diffs."""
    before = LEDGER.read_text()
    from scripts.ledger_io import write
    write(read(), derive_parquet=False)
    assert LEDGER.read_text() == before, "write(read(x)) != x -- serialisation is unstable"
