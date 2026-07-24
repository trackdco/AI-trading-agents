"""Order-book reconstruction + MBO->MBP-10 aggregation (LIVE-STACK Step 2/4).

The live feed is **MBO** (Market By Order): every add / modify / cancel of an individual
resting order, keyed by order id. The canon was validated on **MBP-10** (10 price levels
per side, each with total size AND order count). This module reconstructs the book from
the MBO stream and aggregates it to MBP-10 — the single deterministic implementation the
live ingestor and the reconciliation gate both use, so "our MBO->MBP-10 == Databento
MBP-10" can be proven on a historical day (LIVE-STACK cross-cutting A).

Deterministic and transport-agnostic: a live DTC source and a historical `.scid`/`.depth`
or Databento source all feed the SAME `apply()`. Event schema (one dict per event):

    {"action": "A"|"M"|"C"|"R", "order_id": int, "side": "B"|"A",
     "price": int|float, "size": int}

  A add     — a new resting order at (side, price, size)
  M modify  — order_id changes price and/or size (net queue effect = remove old, add new)
  C cancel  — remove order_id
  R clear   — wipe the whole book (session reset / snapshot boundary)

Prices are kept as given (CME integer 1e-9 fixed-point or float — the book never does
price math, only equality/sort), so it is exact for either.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Level:
    price: float
    size: int
    ct: int                       # order count at this price (the MBO-only signal)


class OrderBook:
    """Resting book reconstructed from MBO events; aggregate view via `mbp10()`."""

    def __init__(self) -> None:
        self._orders: dict[int, tuple[str, float, int]] = {}      # id -> (side, price, size)
        self._bid_sz: dict[float, int] = defaultdict(int)
        self._ask_sz: dict[float, int] = defaultdict(int)
        self._bid_ct: dict[float, int] = defaultdict(int)
        self._ask_ct: dict[float, int] = defaultdict(int)

    # ---- mutation ----------------------------------------------------------
    def apply(self, ev: dict) -> None:
        a = ev["action"]
        if a == "R":
            self.__init__()
            return
        if a == "A":
            self._add(ev["order_id"], ev["side"], float(ev["price"]), int(ev["size"]))
        elif a == "C":
            self._remove(ev["order_id"])
        elif a == "M":
            # modify = remove the old resting order, add the new one (queue-priority reset).
            self._remove(ev["order_id"])
            self._add(ev["order_id"], ev["side"], float(ev["price"]), int(ev["size"]))
        else:
            raise ValueError(f"unknown book action {a!r}")

    def _add(self, oid: int, side: str, price: float, size: int) -> None:
        if oid in self._orders:                # defensive: a re-add of a live id is a modify
            self._remove(oid)
        self._orders[oid] = (side, price, size)
        sz, ct = (self._bid_sz, self._bid_ct) if side == "B" else (self._ask_sz, self._ask_ct)
        sz[price] += size
        ct[price] += 1

    def _remove(self, oid: int) -> None:
        prev = self._orders.pop(oid, None)
        if prev is None:
            return                              # cancel of an unknown id: no-op, never negative
        side, price, size = prev
        sz, ct = (self._bid_sz, self._bid_ct) if side == "B" else (self._ask_sz, self._ask_ct)
        sz[price] -= size
        ct[price] -= 1
        if sz[price] <= 0:                       # level emptied -> drop it (no zero-size levels)
            sz.pop(price, None)
            ct.pop(price, None)

    # ---- aggregate view ----------------------------------------------------
    def mbp10(self, depth: int = 10) -> dict[str, list[Level]]:
        """Top-`depth` levels per side: bids high->low, asks low->high, each carrying
        aggregated size and order count. Fewer than `depth` levels if the book is thin."""
        bids = [Level(p, self._bid_sz[p], self._bid_ct[p])
                for p in sorted(self._bid_sz, reverse=True)[:depth]]
        asks = [Level(p, self._ask_sz[p], self._ask_ct[p])
                for p in sorted(self._ask_sz)[:depth]]
        return {"bids": bids, "asks": asks}

    def long_form(self, depth: int = 10) -> list[dict]:
        """MBP-10 as the long-form rows the depth feature code consumes (one row per
        level per side): {side: 'bid'|'ask', price, size}. `ct` is carried too so the
        journal/research layer keeps the MBO-only order-count signal."""
        snap = self.mbp10(depth)
        rows = [{"side": "bid", "price": lv.price, "size": lv.size, "ct": lv.ct}
                for lv in snap["bids"]]
        rows += [{"side": "ask", "price": lv.price, "size": lv.size, "ct": lv.ct}
                 for lv in snap["asks"]]
        return rows

    def best_bid(self) -> float | None:
        return max(self._bid_sz) if self._bid_sz else None

    def best_ask(self) -> float | None:
        return min(self._ask_sz) if self._ask_sz else None
