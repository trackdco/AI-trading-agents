"""CONFORMANCE: the live decision core must reproduce the shipped book exactly.

`scripts/funded_book.py` is the canon spec; `src/canon/scorer_ny.py` is what will actually
run against a broker. If they disagree by one trade, the thing we validated is not the thing
we would trade. So this replays every row of output/aikido_{fit,holdout}.parquet through the
live scorer — driven through the real live protocol (start_day / evaluate / commit / on_exit),
never by peeking at the book — and requires an exact match on both spans, for both shipped
profiles: same trades, same tier, same risk dollars, same micros, same P&L.

The check is strong because the scorer RE-DERIVES the gates from raw depth/flow columns
rather than reading the parquet's precomputed `valid` / `gold_score` / `pre_score`. Agreement
therefore also proves the live re-derivation of W, D, the wall-quality cut, the scores and the
tiers matches the batch — not just that the arithmetic downstream of them lines up.

The unit tests below pin the behaviours that have no second source: the elite slot's
refusal semantics, budget accounting under OVERLAPPING positions (the failure mode that
killed realized-loss day-halts), and the two half-size rules.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from scripts import funded_book as fb
from src.canon.scorer_ny import (
    LUCID,
    PROFILES,
    SCALED600,
    NYScorerV2,
    session_of,
)

ROOT = Path(__file__).resolve().parents[1]
SPANS = ["fit", "holdout"]


def _row(r) -> dict:
    """The live feed's view of a signal — raw feature fields only, never a book column."""
    return {"day": r.day, "fill": r.fill, "fill_hm": r.fill_hm, "direction": r.direction,
            "risk": r.risk, "dep_thick": r.dep_thick,
            "dep_wall_below_d": r.dep_wall_below_d, "dep_wall_above_d": r.dep_wall_above_d,
            "dep_wall_below_sz": r.dep_wall_below_sz, "dep_wall_above_sz": r.dep_wall_above_sz,
            "ent_vs_vwap_sd_dir": r.ent_vs_vwap_sd_dir, "fill_delta_conf": r.fill_delta_conf,
            "d15_conf": r.d15_conf, "on_extreme_age": r.on_extreme_age,
            "trigdens_30": r.trigdens_30, "bp5opp": r.bp5opp, "lon_slope_d": r.lon_slope_d,
            "struct_event": r.struct_event}


def replay(span: str, profile) -> pd.DataFrame:
    """Drive the live scorer over a span through the real protocol and return its book."""
    S = pd.read_parquet(ROOT / f"output/aikido_{span}.parquet").copy()
    S["fill"] = pd.to_datetime(S.fill_ts, format="mixed", utc=True)
    S["exit"] = pd.to_datetime(S.exit_ts, format="mixed", utc=True)
    S = S.sort_values("fill", kind="mergesort")   # stable: ties resolve to detection order

    s = NYScorerV2(profile=profile)
    bal, line = fb.START, fb.START - fb.TRAIL
    out = []
    for day, g in S.groupby("day", sort=True):
        s.start_day(day, buffer=bal - line)
        live: list[tuple] = []                      # (exit_ts, verdict, pl) still open
        day_pl = 0.0
        for r in g.itertuples():
            for item in [x for x in live if x[0] <= r.fill]:      # settle what has closed
                s.on_exit(item[1], pl=item[2])
                live.remove(item)
            v = s.evaluate(_row(r))
            if not v.taken:
                continue
            s.commit(v)
            pl = v.micros * r.dollars_1lot / 10.0
            live.append((r.exit, v, pl))
            day_pl += pl
            out.append({"day": day, "fill": r.fill, "sess": v.session, "tier": v.tier,
                        "risk_d": v.risk_dollars, "micros": v.micros, "pl": pl})
        for item in live:                                          # close out the day
            s.on_exit(item[1], pl=item[2])
        bal += day_pl
        line = min(fb.START, max(line, bal - fb.TRAIL))
    return pd.DataFrame(out)


@pytest.mark.parametrize("span", SPANS)
@pytest.mark.parametrize("profile_name", ["lucid", "scaled600"])
def test_live_scorer_reproduces_the_shipped_book(span, profile_name):
    profile = PROFILES[profile_name]
    got = replay(span, profile)
    want = fb.run(fb.load_book(span), profile_name).sort_values("day").reset_index(drop=True)
    got = got.sort_values(["day", "fill"]).reset_index(drop=True)

    assert len(got) == len(want), (
        f"{span}/{profile_name}: live took {len(got)} trades, the book took {len(want)}")
    for col in ("tier", "risk_d", "micros", "pl"):
        diff = (got[col].to_numpy() - want[col].to_numpy())
        assert abs(diff).max() < 1e-9, f"{span}/{profile_name}: {col} diverges"
    assert (got.sess.to_numpy() == want.sess.to_numpy()).all()
    assert abs(got.pl.sum() - want.pl.sum()) < 1e-6


@pytest.mark.parametrize("span", SPANS)
def test_reference_net_is_reproduced(span):
    """The headline numbers in the funded_book docstring, from the LIVE path."""
    expect = {"fit": 90_015, "holdout": 56_409}[span]
    assert round(replay(span, LUCID).pl.sum()) == pytest.approx(expect, abs=1)


# ---------------------------------------------------------------- windows and gates
def test_session_windows_are_the_shipped_ones():
    assert session_of(480) == "pre" and session_of(569) == "pre"
    assert session_of(570) == "other" and session_of(579) == "other"
    assert session_of(580) == "gold" and session_of(629) == "gold"
    assert session_of(630) == "other", "gold ends at 10:30 — 09:55-10:00 is NOT a dead zone"


def _gold(**over) -> dict:
    row = {"day": "2026-01-05", "fill": pd.Timestamp("2026-01-05 14:50", tz="UTC"),
           "fill_hm": 590, "direction": "long", "risk": 10.0, "dep_thick": 5.0,
           "dep_wall_below_d": 8.0, "dep_wall_above_d": 6.0,
           "dep_wall_below_sz": 9.0, "dep_wall_above_sz": 9.0,
           "ent_vs_vwap_sd_dir": 0.5, "fill_delta_conf": 1, "d15_conf": 1,
           "on_extreme_age": 5.0, "trigdens_30": 20.0, "bp5opp": 0, "lon_slope_d": 0.0,
           "struct_event": "broke"}
    row.update(over)
    return row


def _fresh(profile=LUCID, buffer=5_000.0) -> NYScorerV2:
    s = NYScorerV2(profile=profile)
    s.start_day("2026-01-05", buffer=buffer)
    return s


def test_risk_band_and_gates_refuse():
    s = _fresh()
    assert s.evaluate(_gold(risk=6.9)).reasons == ["hard_gate_risk"]
    assert s.evaluate(_gold(risk=60.1)).reasons == ["hard_gate_risk"]
    assert s.evaluate(_gold(dep_wall_above_d=float("nan"))).reasons == ["gold_no_wall_ahead"]
    # the aikido wall-quality cut, both limbs
    assert s.evaluate(_gold(dep_wall_below_d=2.0)).reasons == ["gold_wall_quality"]
    assert s.evaluate(_gold(dep_wall_above_sz=1.0)).reasons == ["gold_wall_quality"]
    # pre-market: a wall BEHIND the trade voids it
    pre = _gold(fill_hm=520, dep_wall_below_d=8.0)
    assert s.evaluate(pre).reasons == ["pre_wall_behind"]


def test_elite_slot_is_spent_on_fills_not_on_refusals():
    """A budget-refused elite candidate must NOT burn the day's 2.0x slot — the backtest
    sets elite_used only after the budget check passes."""
    s = _fresh()
    v1 = s.evaluate(_gold())
    assert v1.tier == 2.0 and v1.taken
    s.commit(v1)
    v2 = s.evaluate(_gold())                       # second elite of the day
    assert v2.tier != 2.0 and "elite_used_today" in v2.reasons

    s2 = _fresh()
    while True:                                    # fill the budget with non-elite risk
        v = s2.evaluate(_gold(trigdens_30=1.0))    # TRIG=0 -> not elite
        if not v.taken:
            break
        s2.commit(v)
    refused = s2.evaluate(_gold())
    assert not refused.taken and "budget_exhausted" in refused.reasons
    assert refused.tier == 2.0, "it was elite-eligible; the budget is what refused it"
    s2._open.clear()                               # positions close, budget frees up
    still_elite = s2.evaluate(_gold())
    assert still_elite.tier == 2.0, "a refused elite must leave the slot available"


def test_budget_counts_inflight_risk_not_just_realized_losses():
    """The failure mode that killed realized-loss day halts: 4-8 OVERLAPPING losers whose
    losses are not realized when the later entries fire."""
    s = _fresh()
    taken = []
    for _ in range(20):
        v = s.evaluate(_gold(trigdens_30=1.0))
        if not v.taken:
            break
        s.commit(v)
        taken.append(v)
    assert taken, "at least one trade must be admitted"
    inflight = sum(v.risk_dollars for v in taken)
    assert inflight <= s._budget + 1e-9, "in-flight risk may never exceed the day's budget"
    assert not s.evaluate(_gold(trigdens_30=1.0)).taken


def test_soft_derisk_and_dd_ramp_each_halve_size():
    s = _fresh()
    full = s.evaluate(_gold(trigdens_30=1.0)).risk_dollars
    s.commit(s.evaluate(_gold(trigdens_30=1.0)))
    s._open.clear()
    s._realized = -s._soft                          # exactly at the trigger
    soft = s.evaluate(_gold(trigdens_30=1.0))
    assert soft.risk_dollars == pytest.approx(full * 0.5)
    assert "soft_derisk_half" in soft.reasons

    r = NYScorerV2(profile=LUCID)
    r.start_day("2026-01-05", buffer=999.0)         # under the $1k ramp
    assert "dd_ramp_half" in r.evaluate(_gold(trigdens_30=1.0)).reasons


def test_scaled_profile_base_steps_with_buffer_and_caps():
    assert LUCID.base_for(50_000.0) == 150.0, "lucid never scales"
    assert SCALED600.base_for(3_000.0) == 150.0
    assert SCALED600.base_for(4_999.0) == 150.0, "first step lands at +$5k, not +$3k"
    assert SCALED600.base_for(5_000.0) == 225.0
    assert SCALED600.base_for(7_000.0) == 300.0
    assert SCALED600.base_for(99_000.0) == 600.0, "hard cap"


def test_budget_and_soft_scale_with_the_base():
    """ANGUS 2026-07-29: 'with more buffer, we have more of a daily budget.' A fixed budget
    against a scaled base strangles the book — that version lost 20% of holdout net."""
    small = NYScorerV2(profile=SCALED600)
    small.start_day("2026-01-05", buffer=3_000.0)
    big = NYScorerV2(profile=SCALED600)
    big.start_day("2026-01-05", buffer=30_000.0)
    assert big._base == 4 * small._base
    assert big._budget == pytest.approx(4 * small._budget)
    assert big._soft == pytest.approx(4 * small._soft)


def test_evaluate_is_pure():
    """The execution layer re-asks on every bar while an order rests; that must not mutate."""
    s = _fresh()
    before = s.status()
    for _ in range(5):
        s.evaluate(_gold())
    assert s.status() == before


def test_commit_requires_a_taken_verdict_and_is_single_use():
    s = _fresh()
    v = s.evaluate(_gold())
    s.commit(v)
    with pytest.raises(RuntimeError):
        s.commit(v)
    refused = s.evaluate(_gold(risk=999.0))
    with pytest.raises(RuntimeError):
        s.commit(refused)


def test_absent_struct_event_never_escalates_size():
    """If the execution layer cannot observe the structural event, the trade sizes at its own
    tier. Missing evidence must never buy 2.0x."""
    s = _fresh()
    assert s.evaluate(_gold(struct_event="")).tier < 2.0
    assert s.evaluate(_gold(struct_event="rejected")).tier < 2.0
    assert s.evaluate(_gold(struct_event=None)).tier < 2.0


def test_day_boundary_must_be_declared():
    s = _fresh()
    with pytest.raises(RuntimeError):
        s.evaluate(_gold(day="2026-01-06"))


def test_no_trade_count_cap_exists():
    """Entries are UNCAPPED — capacity is the budget, not a slot count. A day of small-risk
    trades must be able to exceed the old 2/session and 3/day backstops."""
    s = _fresh(profile=SCALED600, buffer=30_000.0)
    n = 0
    while n < 50:
        v = s.evaluate(_gold(trigdens_30=1.0, risk=40.0))
        if not v.taken:
            break
        s.commit(v)
        s.on_exit(v, pl=1.0)                 # closes immediately: no in-flight risk
        n += 1
    assert n > 3, f"only {n} trades admitted — a trade-count cap is still in force"
