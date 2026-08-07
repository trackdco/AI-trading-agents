"""Synthetic-message tests for MBO order-book reconstruction + MBP-10 aggregation
(LIVE-STACK Step 2/4). No feed/transport — pure event application, so this validates the
book math the reconciliation gate will later assert against Databento MBP-10.
"""
from __future__ import annotations

from src.canon.book import Level, OrderBook


def _add(oid, side, price, size):
    return {"action": "A", "order_id": oid, "side": side, "price": price, "size": size}


def test_add_aggregates_size_and_count():
    b = OrderBook()
    # one 40-lot order vs four 10-lot orders at the SAME price -> same size, different count
    b.apply(_add(1, "B", 100.0, 40))
    b.apply(_add(2, "A", 101.0, 10))
    b.apply(_add(3, "A", 101.0, 10))
    b.apply(_add(4, "A", 101.0, 10))
    b.apply(_add(5, "A", 101.0, 10))
    snap = b.mbp10()
    assert snap["bids"] == [Level(100.0, 40, 1)]
    assert snap["asks"] == [Level(101.0, 40, 4)]     # size 40 but FOUR orders (MBO-only signal)
    assert b.best_bid() == 100.0 and b.best_ask() == 101.0


def test_cancel_decrements_then_drops_empty_level():
    b = OrderBook()
    b.apply(_add(1, "B", 100.0, 10))
    b.apply(_add(2, "B", 100.0, 15))
    b.apply({"action": "C", "order_id": 1, "side": "B", "price": 100.0, "size": 10})
    assert b.mbp10()["bids"] == [Level(100.0, 15, 1)]
    b.apply({"action": "C", "order_id": 2, "side": "B", "price": 100.0, "size": 15})
    assert b.mbp10()["bids"] == []                    # level emptied -> removed
    # cancel of an unknown id is a no-op, never a negative level
    b.apply({"action": "C", "order_id": 99, "side": "B", "price": 100.0, "size": 5})
    assert b.mbp10()["bids"] == []


def test_modify_moves_price_and_size():
    b = OrderBook()
    b.apply(_add(1, "A", 101.0, 10))
    b.apply(_add(2, "A", 102.0, 5))
    # modify order 1 up to 102.0 with size 8: leaves 101 empty, 102 becomes 5+8=13 over 2 orders
    b.apply({"action": "M", "order_id": 1, "side": "A", "price": 102.0, "size": 8})
    snap = b.mbp10()
    assert snap["asks"] == [Level(102.0, 13, 2)]


def test_mbp10_ordering_and_depth_cap():
    b = OrderBook()
    for i, p in enumerate([100.0, 99.0, 101.0, 98.0]):      # unsorted adds
        b.apply(_add(10 + i, "B", p, 1))
    for i, p in enumerate([105.0, 103.0, 104.0]):
        b.apply(_add(20 + i, "A", p, 1))
    snap = b.mbp10(depth=2)
    assert [lv.price for lv in snap["bids"]] == [101.0, 100.0]   # bids high->low, top 2
    assert [lv.price for lv in snap["asks"]] == [103.0, 104.0]   # asks low->high, top 2


def test_clear_wipes_book():
    b = OrderBook()
    b.apply(_add(1, "B", 100.0, 10))
    b.apply(_add(2, "A", 101.0, 10))
    b.apply({"action": "R"})
    assert b.mbp10() == {"bids": [], "asks": []}
    assert b.best_bid() is None and b.best_ask() is None


def test_long_form_matches_depth_feature_input_shape():
    b = OrderBook()
    b.apply(_add(1, "B", 100.0, 10))
    b.apply(_add(2, "A", 101.0, 7))
    rows = b.long_form()
    assert {"side": "bid", "price": 100.0, "size": 10, "ct": 1} in rows
    assert {"side": "ask", "price": 101.0, "size": 7, "ct": 1} in rows
