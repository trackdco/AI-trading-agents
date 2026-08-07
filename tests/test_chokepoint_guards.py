"""Guard tests for the chokepoint (CLAUDE.md §4, §5).

Every guard here is exercised in BOTH directions: the test that protects
something is shown failing red on a deliberately broken case, in the same run
that shows it green on the real one. A scan that reports zero findings without
a known positive is a suspect scan.

Run: python3 tests/test_chokepoint_guards.py   (no pytest dependency)
"""

import ast
import csv
import json
import os
import sys
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "src"))

import chokepoint  # noqa: E402

# Substring markers identifying raw data files. A path (literal or resolved
# through simple assignment taint) containing any marker is a raw-data access.
RAW_MARKERS = [
    ".csv.zst",
    ".mbp-10_condensed",
    ".mbp-10.csv",
    "condensed_GLBX",
    "feb2026_hand_log",
    "condition.json",
]

CHOKEPOINT_FILE = os.path.join(_REPO, "src", "chokepoint.py")
KNOWN_POSITIVE = os.path.join(_REPO, "tests", "fixtures", "violator_known_positive.py")

FAILURES = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(name)


# ---------------------------------------------------------------- AST scan


class _Taint(ast.NodeVisitor):
    """Collect string constants reachable per-name via simple assignments and
    string concatenation, then flag file-opening calls whose path argument
    contains a raw-data marker."""

    OPENERS = {"open"}
    ATTR_OPENERS = {"read_csv", "open", "ZstdDecompressor", "stream_reader"}

    def __init__(self):
        self.names = {}
        self.hits = []

    def _strings_of(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [node.value]
        if isinstance(node, ast.Name):
            return self.names.get(node.id, [])
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return [
                l + r
                for l in self._strings_of(node.left) or [""]
                for r in self._strings_of(node.right) or [""]
            ]
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    parts.append(v.value)
            return ["".join(parts)]
        if isinstance(node, ast.Call):  # e.g. os.path.join("a", "b")
            out = []
            for a in node.args:
                out.extend(self._strings_of(a) or [])
            return ["/".join(out)] if out else []
        return []

    def visit_Assign(self, node):
        vals = self._strings_of(node.value)
        if vals:
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    self.names.setdefault(tgt.id, []).extend(vals)
        self.generic_visit(node)

    def visit_Call(self, node):
        fname = None
        if isinstance(node.func, ast.Name):
            fname = node.func.id
        elif isinstance(node.func, ast.Attribute):
            fname = node.func.attr
        if fname in self.OPENERS or fname in self.ATTR_OPENERS:
            for arg in node.args:
                for s in self._strings_of(arg):
                    if any(m in s for m in RAW_MARKERS):
                        self.hits.append((node.lineno, fname, s))
        self.generic_visit(node)


def scan_file(path):
    """Returns (hits, parse_error)."""
    try:
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
    except (SyntaxError, UnicodeDecodeError) as e:
        return [], str(e)
    t = _Taint()
    t.visit(tree)
    return t.hits, None


def test_ast_chokepoint():
    py_files = []
    for root, dirs, files in os.walk(_REPO):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
        for fn in files:
            if fn.endswith(".py"):
                py_files.append(os.path.join(root, fn))

    unparseable = []
    violations = []
    known_positive_hits = None
    for path in py_files:
        hits, err = scan_file(path)
        if err:
            unparseable.append((path, err))
            continue
        if os.path.abspath(path) == KNOWN_POSITIVE:
            known_positive_hits = hits
            continue
        if os.path.abspath(path) == os.path.abspath(CHOKEPOINT_FILE):
            continue  # the one module allowed to read raw files
        if hits:
            violations.append((path, hits))

    # Known positive MUST be detected — otherwise the scan itself is broken.
    check(
        "AST scan fires on the known-positive violator (red case)",
        bool(known_positive_hits),
        f"hits={known_positive_hits}",
    )
    # Unparseable files are failures, not skips.
    check(
        "no unparseable python modules",
        not unparseable,
        f"unparseable={[(os.path.relpath(p, _REPO), e) for p, e in unparseable]}",
    )
    check(
        "no module outside src/chokepoint.py reads raw data files",
        not violations,
        f"violations={[(os.path.relpath(p, _REPO), h) for p, h in violations]}",
    )
    check(
        "scan actually covered files",
        len(py_files) >= 3,
        f"scanned {len(py_files)} python files",
    )


# ---------------------------------------------------- sealed-path guard


def test_sealed_guard():
    real_path = chokepoint.SEALED_SPANS_PATH
    a_file = sorted(
        __import__("glob").glob(
            os.path.join(_REPO, chokepoint.BOOK_FAMILIES["ny2025"])
        )
    )[0]
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(
                {
                    "sealed": [
                        {
                            "start": "2025-06-01",
                            "end": "2025-06-30",
                            "reason": "guard red-test",
                        }
                    ]
                },
                tf,
            )
            tmp = tf.name
        chokepoint.SEALED_PATHS_TMP = tmp
        chokepoint.SEALED_SPANS_PATH = tmp

        # RED: sealed load without authorisation must raise.
        raised = False
        try:
            list(chokepoint.load_book_minutes("ny2025", _paths=[a_file]))
        except chokepoint.SealedPathError as e:
            raised = "sealed" in str(e)
        check("sealed load refused without authorisation (red case)", raised)

        # GREEN: explicit authorisation loads.
        rows = list(
            chokepoint.load_book_minutes(
                "ny2025", _paths=[a_file], authorize_sealed=True
            )
        )
        check("sealed load permitted with authorize_sealed=True", len(rows) > 0)
    finally:
        chokepoint.SEALED_SPANS_PATH = real_path
        os.unlink(tmp)

    # GREEN baseline: with the real (empty) sealed list, loads pass.
    rows = list(chokepoint.load_book_minutes("ny2025", _paths=[a_file]))
    check("unsealed load passes with empty sealed list", len(rows) > 0)


# ------------------------------------------------ clock-fingerprint guard


def test_fingerprint_guard():
    # RED: a synthetic book file whose ts_recv == ts_event (no floored lie)
    # must be REFUSED — the correction must not touch data that doesn't need it.
    a_file = sorted(
        __import__("glob").glob(
            os.path.join(_REPO, chokepoint.BOOK_FAMILIES["ny2025"])
        )
    )[0]
    with open(a_file) as f:
        rows = list(csv.DictReader(f))
        fieldnames = rows[0].keys()
    with tempfile.NamedTemporaryFile(
        "w", suffix=".csv", newline="", delete=False
    ) as tf:
        w = csv.DictWriter(tf, fieldnames=fieldnames)
        w.writeheader()
        for r in rows[:20]:
            r2 = dict(r)
            r2["ts_recv"] = r2["ts_event"]  # honest clock — fingerprint absent
            w.writerow(r2)
        tmp = tf.name
    try:
        raised = False
        try:
            list(chokepoint.load_book_minutes("ny2025", _paths=[tmp]))
        except chokepoint.ClockFingerprintError as e:
            raised = "fingerprint" in str(e)
        check("non-floored file refused by fingerprint guard (red case)", raised)
    finally:
        os.unlink(tmp)

    # GREEN: a real floored file loads, and ts_true differs from the floored
    # label by the documented ~60s.
    rows = list(chokepoint.load_book_minutes("ny2025", _paths=[a_file]))
    offs = [r["ts_true"] - r["minute_label_raw"] for r in rows]
    med = sorted(offs)[len(offs) // 2]
    check(
        "floored file loads with corrected clock",
        55.0 <= med <= 61.0,
        f"median offset {med:.2f}s",
    )


if __name__ == "__main__":
    test_ast_chokepoint()
    test_sealed_guard()
    test_fingerprint_guard()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        sys.exit(1)
    print("ALL GUARD CHECKS PASSED (including red cases)")
