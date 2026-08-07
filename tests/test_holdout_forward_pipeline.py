"""The forward holdout pipeline must not quietly diverge from the canon it claims to test.

The failure mode this guards is not a crash — it is a run that completes, prints a plausible
number, and answers a different question than the one asked. Three ways that happens here:

  1. the scorer gets called with a gate the production canon does not use (a dead zone, a
     different Layer-0 floor), so the "holdout" is a different rulebook;
  2. the fit and holdout spans go through subtly different code, so the two columns are not
     comparable and the whole fit-vs-holdout design collapses;
  3. a feature is assembled with the wrong function — the AGE bug, where London's per-trade
     `on_extreme_age_trade` was used for gold's per-day check and dropped its fire rate from
     47% to 14% while every number downstream still looked reasonable.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pandas as pd
import pytest

from scripts import build_ny_substrate, london_canon, london_depth, london_matrix
from scripts import london_substrate, score_canon_span

ROOT = Path(__file__).resolve().parents[1]
SPANNED = (score_canon_span, london_substrate, london_matrix, london_depth, london_canon)
# build_ny_substrate keys its spans by segment list rather than a path dict, so it is checked
# separately below rather than bent into the same shape.
ALL_SPANNED = SPANNED + (build_ny_substrate,)


def test_every_span_aware_script_offers_both_spans():
    """A script that only knows one span cannot produce the comparison."""
    for mod in ALL_SPANNED:
        spans = getattr(mod, "SPANS", None) or mod.SEGMENTS
        assert set(spans) == {"fit", "holdout"}, f"{mod.__name__}: {sorted(spans)}"


def test_fit_and_holdout_specs_have_identical_shape():
    """Same keys on both sides — a key present in one span only is a silent behaviour fork."""
    for mod in SPANNED:
        f, h = mod.SPANS["fit"], mod.SPANS["holdout"]
        assert set(f) == set(h), f"{mod.__name__}: fit {sorted(f)} vs holdout {sorted(h)}"


def test_no_span_writes_over_another_spans_artifact():
    """Every output path must be unique across spans, or one run clobbers the other."""
    for mod in SPANNED:
        outs = [str(s.get("out") or s.get("matrix") or "") for s in mod.SPANS.values()]
        outs = [o for o in outs if o]
        assert len(set(outs)) == len(outs), f"{mod.__name__}: colliding outputs {outs}"


def test_scorer_is_called_without_a_dead_zone():
    """canon_mechanical.main() calls build_canon(T) with no gates, and the armed
    +$55,989.81 came from that call. Passing dead_zones here would score a different book."""
    src = inspect.getsource(score_canon_span.score)
    calls = [n for n in ast.walk(ast.parse(src.lstrip()))
             if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "build_canon"]
    assert calls, "score() no longer calls build_canon"
    for c in calls:
        assert not c.keywords, f"build_canon called with {[k.arg for k in c.keywords]}"


def test_engine_stop_floor_is_off_by_default():
    """Layer 0 gates 7-60pt downstream. An engine-level floor vetoes at FILL time, and since
    max_trades_per_day is enforced there, each veto hands the cap slot to a trade the
    rulebook never saw — which is exactly what broke the first holdout run."""
    cfg = build_ny_substrate.canon_config(stop_gate=False)
    assert cfg.min_stop_points == 0.0
    assert cfg.post_open_min_stop == 0.0
    assert cfg.max_trades_per_day == 2          # PER BOOK
    assert (cfg.win_start.hour, cfg.win_end.hour, cfg.win_end.minute) == (8, 10, 15)

    gated = build_ny_substrate.canon_config(stop_gate=True)
    assert gated.min_stop_points > 0, "stop-gate=on must restore the live floor"


def test_gold_age_uses_the_per_day_form_not_the_per_trade_one():
    """src/canon/features.py warns the two disagree on 60/60 days. Gold's scorer was fit
    against the per-day form; calling the other one is undetectable downstream."""
    src = inspect.getsource(score_canon_span.build_features)
    assert "on_extreme_age_day(" in src
    # matched on the parsed tree, not the text — the comment above the call names the wrong
    # function precisely so the next reader knows which one is the trap.
    names = {n.id for n in ast.walk(ast.parse(inspect.getsource(score_canon_span)))
             if isinstance(n, ast.Name)}
    assert "on_extreme_age_day" in names
    assert "on_extreme_age_trade" not in names


def test_holdout_london_triggers_reuse_the_production_window_rule():
    """Three of the six sealed months straddle a UK/US clock changeover. A forked window
    helper would shift those weeks by an hour and quietly mis-window the session."""
    from scripts import holdout_london_triggers as hlt

    assert hlt.london_window_et.__module__ == "scripts.run_triggers_london"
    normal = hlt.london_window_et("2023-07-05")
    shifted = hlt.london_window_et("2024-03-20")      # UK on BST, US already on EDT
    assert normal[0].hour == 3 and normal[1].hour == 5
    assert shifted[0].hour in (3, 4)


@pytest.mark.parametrize("span", ["fit", "holdout"])
def test_declared_inputs_that_exist_are_readable(span):
    """Catches a path typo before a two-hour run consumes it."""
    for key in ("bars", "trigs", "depth"):
        for entry in score_canon_span.SPANS[span].get(key, []):
            p = ROOT / (entry[0] if isinstance(entry, tuple) else entry)
            if p.exists() and p.is_file() and p.suffix in (".parquet", ".csv"):
                reader = pd.read_parquet if p.suffix == ".parquet" else pd.read_csv
                assert len(reader(p, **({} if p.suffix == ".parquet" else {"nrows": 5}))) > 0
