"""Feed-robustness tests against synthetic sequences (LIVE-STACK live-path hardening):
dedup, out-of-order/late, gap+backfill, stall, DST boundary, and the serve loop's
CommandListener poll + stale-halt.
"""
from __future__ import annotations

import pandas as pd

from src.canon.feed_guard import FeedGuard, serve, warm_start
from src.canon.ingestor import CanonIngestor

NY = "America/New_York"


def _bar(ts, c=100.0):
    return {"ts_event": ts, "open": c, "high": c + 1, "low": c - 1, "close": c, "volume": 10.0}


def _u(s):
    return pd.Timestamp(s, tz="UTC")


def test_dedup_and_out_of_order():
    g = FeedGuard()
    assert g.accept(_bar(_u("2026-03-17T12:00:00Z"))) != []
    assert g.accept(_bar(_u("2026-03-17T12:00:00Z"))) == [] and g.dupes == 1   # duplicate
    assert g.accept(_bar(_u("2026-03-17T11:59:00Z"))) == [] and g.late == 1    # late/rewind
    assert g.accept(_bar(_u("2026-03-17T12:01:00Z"))) != []                    # normal advance


def test_gap_detected_and_backfilled():
    gaps = []
    g = FeedGuard(on_gap=lambda lo, hi: gaps.append((lo, hi)))
    g.accept(_bar(_u("2026-03-17T12:00:00Z")))
    g.accept(_bar(_u("2026-03-17T12:03:00Z")))                # skipped 12:01, 12:02
    assert gaps == [(_u("2026-03-17T12:01:00Z"), _u("2026-03-17T12:03:00Z"))]
    src = pd.DataFrame([_bar(_u("2026-03-17T12:01:00Z")), _bar(_u("2026-03-17T12:02:00Z")),
                        _bar(_u("2026-03-17T13:00:00Z"))])   # last is outside the gap
    filled = g.backfill(src)
    assert [b["ts_event"] for b in filled] == [_u("2026-03-17T12:01:00Z"),
                                               _u("2026-03-17T12:02:00Z")]
    assert g.gaps == []                                      # cleared


def test_stale_detection_fires_once():
    fired = []
    g = FeedGuard(stale_after_s=180, on_stale=lambda last: fired.append(last))
    g.accept(_bar(_u("2026-03-17T12:00:00Z")))
    assert g.check_stale(_u("2026-03-17T12:02:00Z")) is False      # 120s < 180s
    assert g.check_stale(_u("2026-03-17T12:04:00Z")) is True       # 240s > 180s
    assert g.check_stale(_u("2026-03-17T12:05:00Z")) is True       # still stale
    assert len(fired) == 1                                         # on_stale fired ONCE


def test_tz_naive_rejected():
    g = FeedGuard()
    try:
        g.accept({"ts_event": pd.Timestamp("2026-03-17T12:00:00"), "open": 1, "high": 1,
                  "low": 1, "close": 1, "volume": 1})
        raise AssertionError("expected ValueError on tz-naive bar")
    except ValueError:
        pass


def test_dst_spring_forward_interval_is_utc_safe():
    # US spring-forward 2026-03-08 02:00 ET. Bars straddling it are 60s apart in UTC even
    # though the ET wall clock jumps — no false gap, no false dup.
    g = FeedGuard()
    a = _u("2026-03-08T06:59:00Z")   # 01:59 ET
    b = _u("2026-03-08T07:00:00Z")   # 03:00 ET (02:xx skipped by DST)
    assert g.accept(_bar(a)) != []
    assert g.accept(_bar(b)) != [] and g.gaps == []             # consecutive in UTC


def test_warm_start_primes_state():
    bars = pd.DataFrame([_bar(pd.Timestamp("2026-03-17 08:00", tz=NY).tz_convert("UTC")),
                         _bar(pd.Timestamp("2026-03-17 08:01", tz=NY).tz_convert("UTC"))])
    fp = pd.DataFrame({"delta": [5.0, 3.0], "vol": [50.0, 40.0], "vwp": [100.0, 101.0]},
                      index=pd.DatetimeIndex([b for b in bars.ts_event]))
    ing = CanonIngestor()
    warm_start(ing, bars, fp)
    assert len(ing._bars) == 2 and list(ing.tape.frame().cum) == [5.0, 8.0]


class _FakeListener:
    def __init__(self):
        self.polls = 0

    def poll_once(self, timeout=0):
        self.polls += 1
        return 0


def test_serve_polls_listener_and_halts_on_stale():
    ing = CanonIngestor()
    g = FeedGuard(stale_after_s=180)
    lis = _FakeListener()
    feed = [_bar(_u("2026-03-17T12:00:00Z")), _bar(_u("2026-03-17T12:01:00Z"))]
    # clock jumps far ahead after the 2nd bar -> stale -> loop breaks
    clock = iter([_u("2026-03-17T12:00:30Z"), _u("2026-03-17T12:10:00Z")])
    serve(iter(feed), ing, g, listener=lis, now_fn=lambda: next(clock))
    assert lis.polls >= 1 and g.stalled is True
