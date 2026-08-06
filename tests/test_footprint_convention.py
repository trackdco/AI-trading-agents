"""Pins the two footprint invariants that drifted, so they cannot drift again.

1. The aggressor-side sign: 'B' is the BUYER-aggressor, so signed delta is B - A.
   Two consumers had this inverted. Settled empirically (see src/engine/footprint):
   over 287 London sessions, B - A scores pearson r = +0.7293 against the realised
   open-to-close move from the independent 1m bar master, rising to +0.7754 on the 138
   sessions with |move| >= 40 pts and +0.7944 on the top 20 by |move|. A - B is the
   exact negative. There is no ambiguity to preserve.

2. No consumer reads data/reference/cvd directly. Every read goes through
   src/engine/footprint so the front-month band-clean and the sealed-holdout guard are
   applied once, not re-implemented eleven times.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pandas as pd
import pytest

from src.engine import footprint as fp

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- 1. the sign

def test_buy_aggressor_is_B():
    """The constant itself, so a flip is a one-line diff that fails here."""
    assert fp.BUY_AGGRESSOR == "B"
    assert fp.SELL_AGGRESSOR == "A"


def test_signed_delta_is_buy_positive():
    """A minute of pure buyer-aggression must produce a POSITIVE delta."""
    df = pd.DataFrame({
        "ts_minute": pd.to_datetime(["2025-06-02 08:00", "2025-06-02 08:00",
                                     "2025-06-02 08:01"], utc=True),
        "price": [21000.0, 21000.25, 21001.0],
        "side": ["B", "A", "B"],
        "volume": [100, 40, 7],
    })
    d = fp.signed_delta(df, by=("ts_minute",))
    assert d.iloc[0] == 60, "B=100 vs A=40 must give +60, not -60"
    assert d.iloc[1] == 7, "a pure-buy minute must be positive"


def test_signed_delta_rejects_hand_rolled_inverse():
    """Guard against the specific defect: A - B is the wrong sign, not a variant."""
    df = pd.DataFrame({
        "ts_minute": pd.to_datetime(["2025-06-02 08:00"] * 2, utc=True),
        "price": [21000.0, 21000.0], "side": ["B", "A"], "volume": [10, 3],
    })
    assert fp.signed_delta(df).iloc[0] > 0


# ------------------------------------------------- 2. the read chokepoint

_ALLOWED = {
    "src/engine/footprint.py",          # the chokepoint itself
    "scripts/sample_holdout_days.py",   # emits the path in generated prose, never reads
    "tests/test_footprint_convention.py",
}
#: The original form. It only sees an INLINE path, which is how this check spent its
#: first day passing vacuously on `scripts/london_obk_flow.py` -- the one file that
#: carried an inverted delta sign AND an unbanded read. That file builds
#: `p = ROOT / "data/reference/cvd" / f` on one line and calls `read_parquet(p)` on the
#: next, so the regex never fired. Six files evaded it the same way. A path-shaped
#: check has to look at the whole module, not at one call expression.
_READ_INLINE = re.compile(r"read_parquet\s*\(\s*[^)]*reference/cvd", re.S)
#: Routing through the chokepoint is what makes naming the directory legitimate --
#: e.g. passing `fp.fit_span_files()` or band-filtering with `fp.cached_front_month_bands()`.
_VIA_CHOKEPOINT = re.compile(r"(from|import)\s+src\.engine\.footprint|"
                             r"from\s+src\.engine\s+import\s+[^\n]*footprint")
_CVD = "reference/cvd"
_READERS = {"read_parquet", "read_csv"}


def _variable_path_reads(src: str) -> list[str]:
    """Modules that READ a cvd path assembled in a variable. AST, not regex.

    A plain "names the directory and calls read_parquet" rule was tried first and flagged
    four files of which three were false positives -- `london_canon.py` and
    `london_matrix.py` declare a holdout tape path in a span dict and never read it, and
    `remaining_family_parity.py` only probes `.exists()`. A check with a 75% false-alarm
    rate gets switched off, so it has to distinguish naming a path from reading one.

    Two taint sources, which between them cover every pattern in this repo:
      - a name bound to an expression mentioning the directory (`p = ROOT / ".../cvd" / f`)
      - a dict KEY whose value mentions it (`{"tape": ".../cvd/footprint_*.parquet"}`),
        so `read_parquet(spec["tape"])` is caught as well

    Known limit, stated rather than hidden: a path that reaches a reader through a
    function return value or an f-string built from fragments is not traced. The
    chokepoint import is the primary control; this is the net beneath it.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        # Some modules use PEP 701 f-strings (nested same-type quotes), which this
        # interpreter's ast cannot parse. Returning [] would let a file escape the check
        # silently, so signal it and let the caller decide.
        return None
    seg = lambda n: ast.get_source_segment(src, n) or ""      # noqa: E731
    tainted_names, tainted_keys = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and _CVD in seg(n.value):
            tainted_names |= {t.id for t in n.targets if isinstance(t, ast.Name)}
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str) and _CVD in seg(v):
                    tainted_keys.add(k.value)
    hits = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and n.args):
            continue
        fn = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
        if fn not in _READERS:
            continue
        a = seg(n.args[0])
        if (_CVD in a
                or (isinstance(n.args[0], ast.Name) and n.args[0].id in tainted_names)
                or any(f'"{k}"' in a or f"'{k}'" in a for k in tainted_keys)):
            hits.append(a)
    return hits


def _sources():
    for base in ("scripts", "src"):
        for p in sorted((ROOT / base).rglob("*.py")):
            rel = p.relative_to(ROOT).as_posix()
            if rel not in _ALLOWED:
                yield rel, p.read_text()


def test_no_direct_footprint_reads():
    """pd.read_parquet on data/reference/cvd outside the chokepoint is a defect."""
    offenders = [rel for rel, src in _sources() if _READ_INLINE.search(src)]
    assert not offenders, (
        "these read the footprint directly instead of via src/engine/footprint, so they "
        "skip the front-month band-clean and the sealed-holdout guard: " + ", ".join(offenders)
    )


def test_no_footprint_reads_via_a_variable_path():
    """The same defect with the path in a variable — the hole the inline check left."""
    offenders, unscannable = {}, []
    for rel, src in _sources():
        if _VIA_CHOKEPOINT.search(src):
            continue
        hits = _variable_path_reads(src)
        if hits is None:                      # unparseable on this interpreter
            if _CVD in src:
                unscannable.append(rel)
            continue
        if hits:
            offenders[rel] = hits
    assert not unscannable, (
        "these name data/reference/cvd but could not be AST-scanned (PEP 701 f-strings "
        "on this interpreter), so the check cannot clear them — review by hand or add to "
        "_ALLOWED with a reason: " + ", ".join(unscannable)
    )
    assert not offenders, (
        "these assemble a data/reference/cvd path and read it without importing "
        "src.engine.footprint, so they get neither the front-month band-clean nor the "
        "sealed-holdout guard: "
        + "; ".join(f"{k} -> {v}" for k, v in offenders.items())
    )


def test_the_variable_path_check_distinguishes_naming_from_reading():
    """Pin the false-positive behaviour that made the first version unusable."""
    reads = 'p = ROOT / "data/reference/cvd" / f\nd = pd.read_parquet(p)\n'
    names = ('S = {"tape": "data/reference/cvd/footprint_holdout_*.parquet",\n'
             '     "m": "output/x.parquet"}\nd = pd.read_parquet(S["m"])\n')
    probes = 'if Path(f"data/reference/cvd/{f}.parquet").exists():\n    pass\n'
    via_key = ('S = {"tape": "data/reference/cvd/f.parquet"}\n'
               'd = pd.read_parquet(S["tape"])\n')
    assert _variable_path_reads(reads), "a variable-path read must be caught"
    assert _variable_path_reads(via_key), "a read through a tainted dict key must be caught"
    assert not _variable_path_reads(names), "declaring a path without reading it is legal"
    assert not _variable_path_reads(probes), "an .exists() probe is not a read"


def test_sealed_holdout_is_guarded():
    """Passing a sealed file without an explicit declaration must raise, not warn."""
    with pytest.raises(PermissionError):
        fp.load_footprint(
            [fp.CVD_DIR / "footprint_holdout_2023-07.parquet"], bands={})


def test_band_clean_requires_price():
    """Dropping the price column is how the contamination became unobservable."""
    with pytest.raises(ValueError):
        fp.load_footprint([fp.CVD_DIR / "footprint_q3_2025.parquet"], bands={},
                          columns=("ts_minute", "side", "volume"))
