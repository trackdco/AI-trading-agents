"""Prop rules, causal features, and the empty setup slot. No broker, no network."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from src.research import DISARMED, ORDER_ROUTING
from src.research.features.book import (
    MINUTE_LABEL_END_STATE,
    BookSnapshot,
    asof_book,
    naive_label_asof,
)
from src.research.features.footprint import absorption_at, stacked_imbalances
from src.research.features.store import features_at
from src.research.features.tape import (
    BUY,
    SELL,
    bar_vwap,
    cvd,
    footprint_minutes_to_trades,
    session_vwap_trades,
)
from src.research.news import in_news_blackout
from src.research.prop.account import PropAccount
from src.research.prop.montecarlo import (
    TradeDistribution,
    run_paths,
    static_floor_pass_rate,
)
from src.research.prop.rules import (
    load_accounts,
    load_document,
    session_open,
    unconfirmed,
)
from src.research.safety import ResearchHalted
from src.research.setup.card import SetupNotDeclared, load_card
from src.research.setup.harness import Fold, run_declared

UTC = timezone.utc
CT = ZoneInfo("America/Chicago")
ROOT = Path(__file__).resolve().parents[1]


def _ts(year, month, day, hour, minute, tz=UTC):
    return datetime(year, month, day, hour, minute, tzinfo=tz)


def test_package_is_disarmed_and_has_no_order_route():
    assert DISARMED is True
    assert ORDER_ROUTING is False
    banned = ("submit_bracket", "SubmitNewSingleOrder", "dtc_client", "api_key", "DATABENTO_API_KEY")
    text = "\n".join(path.read_text() for path in (ROOT / "src" / "research").rglob("*.py"))
    for token in banned:
        assert token not in text
    assert "INVALID" in (ROOT / "docs" / "CANON.md").read_text()
    assert "INVALID DOLLAR RESULTS" in (ROOT / "scripts" / "funded_book.py").read_text()


def test_rules_load_from_official_sources_and_exclude_apex():
    doc = load_document()
    assert doc["retrieved"] == "2026-11-03"
    assert "apex" not in doc["accounts"]
    accounts = load_accounts()
    combine = accounts["topstep_combine_50k"]
    assert combine.profit_target == 3000
    assert combine.mll_amount == 2000
    assert combine.mll_mode == "eod_trail_lock_at_start"
    assert combine.consistency == 0.55
    assert combine.max_minis == 5
    assert combine.dll is None
    assert combine.fees["monthly"] == 49
    assert combine.fees["activation_if_pass"] == 149
    assert combine.sources
    assert all(item["url"].startswith("https://") for item in combine.sources)
    flex = accounts["lucidflex_eval_50k"]
    assert flex.consistency == 0.40
    assert flex.trail_trigger == 52100
    assert flex.lock_floor == 50100
    assert flex.fees["onetime"] is None
    pro = accounts["lucidpro_eval_50k"]
    assert pro.dll == 1200
    assert pro.consistency is None
    direct = accounts["luciddirect_50k"]
    assert direct.payout["consistency"] == 0.20
    assert direct.payout["min_cycle_profit"] == 3000
    daily = accounts["luciddaily_50k"]
    assert daily.mll_mode == "intraday_trail"
    assert daily.news_blackout is True
    flags = unconfirmed()
    ids = {item["id"] for item in flags}
    assert "lucidflex_dll_dollars" in ids
    assert "topstep_xfa_scaling_dollar_tiers" in ids
    assert "luciddaily_100k" not in accounts
    assert accounts["topstep_xfa_50k_standard"].scaling == "unconfirmed"
    assert accounts["topstep_xfa_50k_standard"].payout["cap"] == 2000


def test_session_clock_topstep_and_lucid():
    rules = load_accounts()
    # Tuesday 6 Jan 2026, 15:09 CT is inside the session, 15:10 is flat.
    assert session_open(datetime(2026, 1, 6, 15, 9, tzinfo=CT), rules["topstep_combine_50k"])
    assert not session_open(datetime(2026, 1, 6, 15, 10, tzinfo=CT), rules["topstep_combine_50k"])
    assert session_open(datetime(2026, 1, 6, 17, 0, tzinfo=CT), rules["topstep_combine_50k"])
    assert not session_open(datetime(2026, 1, 10, 12, 0, tzinfo=CT), rules["topstep_combine_50k"])  # Saturday
    ny = ZoneInfo("America/New_York")
    lucid = rules["lucidflex_eval_50k"]
    assert session_open(datetime(2026, 1, 6, 16, 44, tzinfo=ny), lucid)
    assert not session_open(datetime(2026, 1, 6, 16, 45, tzinfo=ny), lucid)
    assert session_open(datetime(2026, 1, 6, 18, 0, tzinfo=ny), lucid)


def test_topstep_eod_trail_does_not_follow_an_intraday_spike():
    account = PropAccount(load_accounts()["topstep_combine_50k"])
    assert account.apply(3000, ts=_ts(2026, 1, 6, 16, 0)).action == "accepted"
    assert account.apply(-3000, ts=_ts(2026, 1, 6, 16, 5)).action == "accepted"
    account.end_day()
    assert account.floor == 48000
    assert account.balance == 50000
    assert not account.passed


def test_topstep_trail_ratchets_up_and_locks_and_consistency_blocks_a_spike_day():
    rules = load_accounts()["topstep_combine_50k"]
    account = PropAccount(rules)
    account.apply(500, ts=_ts(2026, 1, 6, 16, 0))
    account.end_day()
    assert account.floor == 48500
    account.apply(-400, ts=_ts(2026, 1, 7, 16, 0))
    account.end_day()
    assert account.floor == 48500
    assert account.balance == 50100

    spike = PropAccount(rules)
    spike.apply(3000, ts=_ts(2026, 1, 6, 16, 0))
    spike.end_day()
    assert not spike.passed
    assert spike.required_profit() == pytest.approx(3000 / 0.55)

    steady = PropAccount(rules)
    steady.apply(1500, ts=_ts(2026, 1, 6, 16, 0))
    steady.end_day()
    assert not steady.passed
    steady.apply(1500, ts=_ts(2026, 1, 7, 16, 0))
    steady.end_day()
    assert steady.passed
    assert steady.balance == 53000


def test_touching_the_max_loss_fails_and_dll_only_blocks_the_day():
    rules = load_accounts()["topstep_combine_50k"]
    bust = PropAccount(rules)
    assert bust.apply(-2000, ts=_ts(2026, 1, 6, 16, 0)).action == "bust"
    assert bust.failed and bust.fail_reason == "mll"
    alive = PropAccount(rules)
    assert alive.apply(-1999, ts=_ts(2026, 1, 6, 16, 0)).action == "accepted"

    from dataclasses import replace

    limited = PropAccount(replace(rules, dll=1000.0))
    assert limited.apply(-400, ts=_ts(2026, 1, 6, 16, 0)).action == "accepted"
    assert limited.apply(-400, ts=_ts(2026, 1, 6, 16, 1)).action == "accepted"
    assert limited.apply(-400, ts=_ts(2026, 1, 6, 16, 2)).action == "dll"
    assert not limited.failed
    assert limited.apply(-50, ts=_ts(2026, 1, 6, 16, 3)).action == "rejected"
    limited.end_day()
    assert limited.apply(-50, ts=_ts(2026, 1, 7, 16, 0)).action == "accepted"


def test_contract_cap_and_lucid_lock_and_xfa_payout():
    combine = load_accounts()["topstep_combine_50k"]
    account = PropAccount(combine)
    assert account.apply(10, ts=_ts(2026, 1, 6, 16, 0), minis=6).reason == "contracts"
    assert account.apply(10, ts=_ts(2026, 1, 6, 16, 0), micros=50).action == "accepted"
    assert account.apply(10, ts=_ts(2026, 1, 6, 16, 1), minis=1, micros=40).action == "accepted"
    assert account.apply(10, ts=_ts(2026, 1, 6, 16, 2), minis=1, micros=41).reason == "contracts"

    flex = PropAccount(load_accounts()["lucidflex_eval_50k"])
    flex.apply(2100, ts=_ts(2026, 1, 6, 16, 0))
    flex.end_day()
    assert flex.locked
    assert flex.floor == 50100
    flex.apply(5000, ts=_ts(2026, 1, 7, 16, 0))
    flex.end_day()
    assert flex.floor == 50100

    xfa = PropAccount(load_accounts()["topstep_xfa_50k_standard"])
    assert xfa.floor == -2000
    for day in range(5):
        # Monday 5 Jan through Friday 9 Jan, 10:00 CT, inside the session.
        xfa.apply(400, ts=_ts(2026, 1, 5 + day, 16, 0))
        xfa.end_day()
    assert xfa.payout_count == 1
    assert xfa.gross_payouts == 1000
    assert xfa.trader_cash == 900
    assert xfa.balance == 1000
    assert xfa.floor == 0


def test_news_blackout_rejects_luciddaily_only_inside_the_window():
    event = pd.Timestamp("2026-01-06 15:00", tz="UTC")
    events = pd.DatetimeIndex([event])
    assert in_news_blackout(datetime(2026, 1, 6, 15, 0, 30, tzinfo=UTC), events, 1)
    assert not in_news_blackout(datetime(2026, 1, 6, 15, 2, tzinfo=UTC), events, 1)
    daily = PropAccount(load_accounts()["luciddaily_50k"])
    daily.news_events = events
    assert daily.apply(-10, ts=datetime(2026, 1, 6, 15, 0, 30, tzinfo=UTC)).reason == "news"
    assert daily.apply(-10, ts=datetime(2026, 1, 6, 16, 0, tzinfo=UTC)).action == "accepted"


def test_static_floor_zero_edge_stays_near_the_closed_form():
    # D/(D+T) = 2000/5000 = 0.40. Risk is $250 so the barriers are 8 and 12
    # steps and a few hundred days is enough for almost every path to finish.
    rate = static_floor_pass_rate(
        2000, 3000, TradeDistribution.no_edge(250), n_sims=600, max_days=400, seed=11
    )
    assert 0.32 <= rate <= 0.48


def test_trailing_zero_edge_pass_rate_is_below_the_static_ceiling():
    rules = load_accounts()["topstep_combine_50k"]
    result = run_paths(
        rules,
        TradeDistribution.no_edge(400),
        n_sims=400,
        max_days=60,
        seed=3,
        funded=load_accounts()["topstep_xfa_50k_standard"],
        funded_days=20,
    )
    assert result.pass_rate < 0.40
    assert result.expected_fees > 0
    assert result.fee_unconfirmed is False
    lucid = run_paths(
        load_accounts()["lucidflex_eval_50k"],
        TradeDistribution.no_edge(400),
        n_sims=300,
        max_days=60,
        seed=4,
    )
    assert lucid.fee_unconfirmed is True
    assert lucid.expected_fees == 0


def test_end_of_minute_book_is_not_visible_at_the_minute_label():
    early = BookSnapshot(
        pd.Timestamp("2026-01-06 15:59", tz="UTC"),
        bids=((21000.0, 10),),
        asks=((21000.25, 10),),
    )
    leaked = BookSnapshot(
        pd.Timestamp("2026-01-06 16:00", tz="UTC"),
        bids=((21000.0, 500),),
        asks=((21000.25, 1),),
    )
    decision = datetime(2026, 1, 6, 16, 0, tzinfo=UTC)
    snaps = [early, leaked]
    assert naive_label_asof(snaps, decision) is leaked
    causal = asof_book(snaps, decision, convention=MINUTE_LABEL_END_STATE)
    assert causal is early
    assert asof_book([leaked], decision, convention=MINUTE_LABEL_END_STATE) is None


def _tape(rows):
    return pd.DataFrame(rows)


def test_cvd_sign_session_vwap_and_no_future_trades():
    decision = datetime(2026, 1, 6, 23, 30, tzinfo=UTC)  # 18:30 NY, after the anchor
    trades = _tape(
        [
            {"ts": "2026-01-06 22:30:00+00:00", "price": 100, "size": 10, "side": BUY},  # 17:30 NY
            {"ts": "2026-01-06 23:30:00+00:00", "price": 200, "size": 10, "side": BUY},
            {"ts": "2026-01-06 23:31:00+00:00", "price": 900, "size": 100, "side": SELL},
        ]
    )
    assert cvd(trades, decision) == 10
    assert session_vwap_trades(trades, decision) == pytest.approx(200)
    later = datetime(2026, 1, 6, 23, 31, tzinfo=UTC)
    assert cvd(trades, later) == 10 - 100


def test_bar_vwap_uses_open_and_waits_for_the_close():
    bars = pd.DataFrame(
        [
            {"ts": "2026-01-06 23:00:00+00:00", "open": 10, "high": 50, "low": 10, "close": 40, "volume": 1},
            {"ts": "2026-01-06 23:01:00+00:00", "open": 30, "high": 30, "low": 30, "close": 30, "volume": 1},
        ]
    )
    # 23:00 bar closes at 23:01. A decision at 23:00:30 cannot see it.
    mid = datetime(2026, 1, 6, 23, 0, 30, tzinfo=UTC)
    assert pd.isna(bar_vwap(bars, mid))
    after = datetime(2026, 1, 6, 23, 1, tzinfo=UTC)
    assert bar_vwap(bars, after) == pytest.approx(10)
    # hlc3 of that bar would be (50+10+40)/3 = 33.3, which this function must not return
    assert bar_vwap(bars, after) != pytest.approx(33.333, abs=0.1)


def test_stacked_imbalance_waits_for_the_minute_close_and_absorption_needs_the_book():
    start = pd.Timestamp("2026-01-06 16:00", tz="UTC")
    rows = []
    for i, price in enumerate((100.0, 100.25, 100.5)):
        rows.append({"ts": start + pd.Timedelta(seconds=5 + i), "price": price, "size": 20, "side": BUY})
    trades = _tape(rows)
    during = datetime(2026, 1, 6, 16, 0, 30, tzinfo=UTC)
    after = datetime(2026, 1, 6, 16, 1, tzinfo=UTC)
    assert stacked_imbalances(trades, during) == []
    stacks = stacked_imbalances(trades, after)
    assert len(stacks) == 1 and stacks[0].side == BUY

    level_rows = []
    base = pd.Timestamp("2026-01-06 16:10", tz="UTC")
    for i in range(10):
        level_rows.append(
            {"ts": base + pd.Timedelta(seconds=i), "price": 100.0, "size": 10, "side": SELL}
        )
    tape = _tape(level_rows)
    decision = datetime(2026, 1, 6, 16, 10, 20, tzinfo=UTC)
    proxy = absorption_at(tape, decision, 100.0, attacking="bid", book=None)
    assert proxy.proxy and not proxy.confirmed
    book = [
        BookSnapshot(base, bids=((100.0, 40),), asks=((100.25, 5),)),
        BookSnapshot(base + pd.Timedelta(seconds=20), bids=((100.0, 35),), asks=((100.25, 5),)),
        BookSnapshot(base + pd.Timedelta(seconds=40), bids=((100.0, 1),), asks=((100.25, 5),)),
    ]
    held = absorption_at(tape, decision, 100.0, attacking="bid", book=book)
    assert held.confirmed
    future = tape.copy()
    future.loc[len(future)] = {
        "ts": "2026-01-06 16:10:50+00:00",
        "price": 80,
        "size": 500,
        "side": BUY,
    }
    again = absorption_at(future, decision, 100.0, attacking="bid", book=book)
    assert again == held
    row = features_at(tape, decision, book=book)
    row_future = features_at(future, decision, book=book)
    assert row.cvd == row_future.cvd
    assert row.book_imbalance == row_future.book_imbalance


def test_footprint_minutes_become_visible_at_the_close():
    minutes = pd.DataFrame(
        [
            {"ts_minute": "2026-01-06 16:00:00+00:00", "price": 100, "volume": 5, "side": BUY},
        ]
    )
    trades = footprint_minutes_to_trades(minutes)
    during = datetime(2026, 1, 6, 16, 0, 30, tzinfo=UTC)
    after = datetime(2026, 1, 6, 16, 1, tzinfo=UTC)
    assert cvd(trades, during) == 0
    assert cvd(trades, after) == 5


def test_setup_card_is_empty_and_walk_forward_scores_only_later_folds(tmp_path):
    card = load_card()
    assert card.status == "awaiting_angus"
    with pytest.raises(SetupNotDeclared):
        run_declared(
            card,
            pd.DataFrame({"ts": [], "pnl": []}),
            load_accounts()["topstep_combine_50k"],
            [Fold(_ts(2026, 1, 5, 0, 0), _ts(2026, 1, 6, 0, 0)), Fold(_ts(2026, 1, 6, 0, 0), _ts(2026, 1, 8, 0, 0))],
        )
    declared = load_card()
    declared.status = "declared"
    declared.name = "TEST_FIXTURE_NOT_A_STRATEGY"
    rows = [{"ts": "2026-01-05 16:00:00+00:00", "pnl": 100000.0}]
    for day in (6, 7, 8, 9):
        for minute in (0, 5, 10):
            rows.append({"ts": f"2026-01-{day:02d} 16:{minute:02d}:00+00:00", "pnl": 100.0})
    trades = pd.DataFrame(rows)
    folds = [
        Fold(_ts(2026, 1, 5, 0, 0), _ts(2026, 1, 6, 0, 0)),
        Fold(_ts(2026, 1, 6, 0, 0), _ts(2026, 1, 10, 0, 0)),
    ]
    kill = tmp_path / "KILL"
    result = run_declared(
        declared,
        trades,
        load_accounts()["topstep_combine_50k"],
        folds,
        n_shuffles=300,
        seed=1,
        kill_path=kill,
    )
    assert result.n_trades == 12
    assert result.mean_pnl == pytest.approx(100)
    assert result.null_p < 0.05
    assert result.end_balance == 51200
    kill.write_text("stop")
    with pytest.raises(ResearchHalted):
        run_declared(
            declared,
            trades,
            load_accounts()["topstep_combine_50k"],
            folds,
            kill_path=kill,
        )
