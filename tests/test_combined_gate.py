"""Tests for src/desk/combined_gate.py — the regime+HTF merge (conservative AND)."""

import pytest

from src.desk.combined_gate import combine
from src.desk.htf_agent import HTFGate
from src.desk.regime_agent import RegimeGate


def _rg(**kw):
    base = dict(date="2026-02-12", allow_reversion=True, allow_continuation=False,
                size_multiplier=1.0, directional_bias="neutral")
    return RegimeGate(**{**base, **kw})


def _hg(**kw):
    base = dict(date="2026-02-12", fade_permitted=True, continuation_only=False,
                daily_context="range", h4_leg="up")
    return HTFGate(**{**base, **kw})


def test_both_permit_reversion():
    g = combine(_rg(allow_reversion=True), _hg(fade_permitted=True))
    assert g.allow_reversion and not g.stand_down and not g.conflict


def test_htf_blocks_fade_kills_reversion():
    # regime wants reversion but HTF says the leg is a trend segment (no fade)
    g = combine(_rg(allow_reversion=True), _hg(fade_permitted=False))
    assert not g.allow_reversion and g.conflict
    assert any("HTF agent forbids fades" in r for r in g.reasons)


def test_regime_excludes_reversion_even_if_htf_allows():
    g = combine(_rg(allow_reversion=False, allow_continuation=True), _hg(fade_permitted=True))
    assert not g.allow_reversion and g.conflict and g.allow_continuation


def test_continuation_governed_by_regime_only():
    g = combine(_rg(allow_reversion=False, allow_continuation=True),
                _hg(fade_permitted=False, continuation_only=True))
    assert g.allow_continuation and not g.allow_reversion and not g.stand_down


def test_nothing_permitted_forces_stand_down():
    g = combine(_rg(allow_reversion=False, allow_continuation=False, size_multiplier=1.0),
                _hg(fade_permitted=False))
    assert g.stand_down and g.size_multiplier == 0.0


def test_regime_stand_down_propagates():
    g = combine(_rg(allow_reversion=False, allow_continuation=False, size_multiplier=0.0),
                _hg(fade_permitted=True))
    assert g.stand_down and g.size_multiplier == 0.0


def test_size_carries_from_regime():
    g = combine(_rg(allow_reversion=True, size_multiplier=0.5), _hg(fade_permitted=True))
    assert g.size_multiplier == 0.5


def test_date_mismatch_raises():
    with pytest.raises(ValueError, match="date mismatch"):
        combine(_rg(date="2026-02-12"), _hg(date="2026-02-13"))


def test_extra_field_forbidden_on_gate():
    g = combine(_rg(), _hg())
    with pytest.raises(Exception):
        type(g)(**{**g.model_dump(), "surprise": 1})
