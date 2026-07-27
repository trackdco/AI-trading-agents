#!/usr/bin/env python3
"""ON-BOX order-surface FORCE TEST (gates A7 / B7 / B8) — runs the REAL DTCBroker adapter
against a REAL Sierra DTC server and prints PASS/FAIL per check, spine_forcetest-style.

Two modes, both SIM-ACCOUNT-ONLY (the script refuses any account without "sim" in the
name — the funded eval is armed by Angus's token through the spine, never by a test
script):

  RESTING (default)  places ONE far-from-market 1-lot bracket that can never fill,
                     verifies the A7 read-back (two order IDs acknowledged by the server),
                     re-prices the entry in place (CANCEL_REPLACE round-trip), cancels the
                     bracket (B7) and verifies BOTH legs read back dead.
                     Pass --entry far BELOW the market for a buy (e.g. market-500).

  --fill             additionally places a MARKETABLE bracket (qty 2), waits for the fill,
                     then runs the full B8 surface: stop_resting read-back (B4), stop
                     modified IN PLACE, partial close of 1, flatten — and verifies flat +
                     nothing working. Only run this when you mean to: it opens and closes
                     a real SIM position. Pass --entry at/through the market for it.

Any exception in fill mode fail-closes: cancel_all + flatten before exiting.

    python -m scripts.dtc_surface_forcetest --account Sim1 --symbol MNQU26-CME \
        --entry 23000 --stop 22990                      # resting checks only
    python -m scripts.dtc_surface_forcetest --account Sim1 --symbol MNQU26-CME \
        --entry 24870 --stop 24820 --fill               # + the fill-path B8 checks

The same sequences run against the mock Sierra in tests/test_dtc_surface_forcetest.py, so
the harness itself is verified before it ever touches the box.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.desk import dtc_client as D                       # noqa: E402
from src.desk.dtc_broker import DTCBroker                  # noqa: E402
from src.desk.dtc_client import DTCClient, DTCConfig       # noqa: E402

READBACK_KEYS = {"entry", "stop", "size", "side", "account", "stop_resting"}


@dataclass
class _Intent:
    """The slice of OrderIntent that DTCBroker.submit_bracket reads."""
    side: str
    entry_ref: float
    stop: float
    size: int
    account: str


@dataclass
class Row:
    label: str
    ok: bool
    detail: str = ""


def _working(client: DTCClient, oid: str) -> bool:  # alive at the broker, incl. held children
    st = client.order_state.get(oid, {})
    return st.get("OrderStatus") in D.ORDER_ALIVE_STATUSES


def _wait_fill(client: DTCClient, oid: str, rounds: int = 60) -> bool:
    for _ in range(rounds):
        client.pump(timeout=0.5)
        if client.order_state.get(oid, {}).get("FilledQuantity"):
            return True
    return False


def run_resting(broker: DTCBroker, client: DTCClient, *, account: str,
                entry: float, stop: float) -> list[Row]:
    """The no-fill half: A7 read-back, in-place re-price, B7 cancel. The bracket must be
    priced where it CANNOT fill; every order it places is dead by the end."""
    rows = []
    ref = broker.submit_bracket(_Intent("B", entry, stop, 1, account))
    entry_oid, stop_oid = client.last_bracket
    both_acked = ref in client.order_state and stop_oid in client.order_state
    sids = (client.order_state.get(ref, {}).get("ServerOrderID"),
            client.order_state.get(stop_oid, {}).get("ServerOrderID"))
    rows.append(Row("A7 bracket read-back: two order IDs acknowledged", both_acked,
                    f"entry={ref} stop={stop_oid} ServerOrderIDs={sids}"))
    st = broker.order_status(ref)
    rows.append(Row("spine read-back shape (all six keys)", READBACK_KEYS <= set(st),
                    f"{st}"))
    # Diagnostic (always-on): the RAW stored server state for both legs — InfoText carries
    # Sierra's rejection reason verbatim (on-box 2026-07-27: the stop child came back
    # OrderStatus=9 REJECTED and nothing printed why).
    rows.append(Row("raw server state: entry", True, f"{client.order_state.get(ref)}"))
    rows.append(Row("raw server state: stop", True, f"{client.order_state.get(stop_oid)}"))
    # B8's real primitive: move the PROTECTIVE STOP in place (BE move / trail). The live
    # engine never re-prices an entry (cancel-if-runs CANCELS it), so that's what we test —
    # and through the BROKER, which owns the price scaling (the old direct client call
    # bypassed it and sent an unscaled price; found on-box 2026-07-27, read back 286.25).
    new_stop = stop - 1.0                                  # further from market, still safe
    broker.modify_stop(ref, new_stop)
    st2 = broker.order_status(ref)
    rows.append(Row("CANCEL_REPLACE: protective stop re-priced in place",
                    st2.get("stop") == new_stop, f"stop={st2.get('stop')} expected {new_stop}"))
    broker.cancel_order(ref)
    dead_entry = client.order_state.get(ref, {}).get("OrderStatus") == D.ORDER_STATUS_CANCELED
    rows.append(Row("B7 cancel: entry reads back CANCELED", dead_entry,
                    f"OrderStatus={client.order_state.get(ref, {}).get('OrderStatus')}"))
    rows.append(Row("B7 cancel: no leg left working",
                    not _working(client, ref) and not _working(client, stop_oid),
                    f"stop OrderStatus={client.order_state.get(stop_oid, {}).get('OrderStatus')}"))
    return rows


def run_fill(broker: DTCBroker, client: DTCClient, *, account: str,
             entry: float, stop: float) -> list[Row]:
    """The fill half (SIM position opened and closed): B4 stop_resting, B8 stop move,
    B8 partial, kill-path flatten. Fail-closes via the caller's finally-flatten."""
    rows = []
    ref = broker.submit_bracket(_Intent("B", entry, stop, 2, account))
    _, stop_oid = client.last_bracket
    filled = _wait_fill(client, ref)
    rows.append(Row("fill-path: entry filled", filled,
                    f"FilledQuantity={client.order_state.get(ref, {}).get('FilledQuantity')}"))
    st = broker.order_status(ref)
    rows.append(Row("B4/B8: protective stop resting after fill", bool(st.get("stop_resting")),
                    f"{st}"))
    new_stop = stop + 1.0                                  # a BE-style move toward entry
    broker.modify_stop(ref, new_stop)
    got = broker.order_status(ref).get("stop")             # display units (broker unscales)
    rows.append(Row("B8 modify_stop: stop re-priced IN PLACE", got == new_stop,
                    f"stop={got} expected {new_stop}"))
    oid = broker.close_partial(account, 1)
    part_filled = bool(oid) and _wait_fill(client, oid)
    rows.append(Row("B8 close_partial(1): reducing market order filled", part_filled,
                    f"oid={oid!r}"))
    broker.flatten(account)
    rows.append(Row("flatten: no order left working",
                    not _working(client, ref) and not _working(client, stop_oid),
                    f"stop OrderStatus={client.order_state.get(stop_oid, {}).get('OrderStatus')}"))
    pos = broker.position(account)
    rows.append(Row("flatten: position reads back FLAT", pos == 0, f"position={pos}"))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=11099)
    ap.add_argument("--account", required=True, help="SIM trade account (must contain 'sim')")
    ap.add_argument("--symbol", required=True, help="micros order symbol, e.g. MNQU26-CME")
    ap.add_argument("--entry", type=float, required=True)
    ap.add_argument("--stop", type=float, required=True)
    ap.add_argument("--fill", action="store_true", help="also run the fill-path B8 checks")
    ap.add_argument("--price-scale", type=float, default=1.0,
                    help="service price units per display point (Pat's VPS: 100 — the "
                         "Rithmic feed runs 100x display; keep in lockstep with "
                         "config/live.yaml dtc.price_scale)")
    a = ap.parse_args(argv)

    # Non-production naming, either convention: Sierra's internal sim accounts carry "sim";
    # Rithmic's paper environment mirrors the real account id with a -TESTnnn suffix (the
    # box's actual paper account, found 2026-07-27: LFE050-9YSC047M-TEST001). A funded
    # account carries neither.
    if not any(tag in a.account.lower() for tag in ("sim", "test")):
        print(f"REFUSED: account {a.account!r} does not look like a SIM/paper account "
              "(no 'sim' or 'test' in the name). This script only ever runs against "
              "SIM/paper — the funded account is armed through the spine "
              "(docs/PROMOTION-GATE.md), never by a test script.")
        return 2
    if not a.symbol.upper().startswith("MNQ"):
        print(f"REFUSED: symbol {a.symbol!r} is not a micros (MNQ*) contract. "
              "The canon routes micros only (MICRO_CLAMP).")
        return 2
    if a.stop >= a.entry:
        print("REFUSED: --stop must be below --entry (checks run a BUY bracket).")
        return 2

    client = DTCClient(DTCConfig(host=a.host, port=a.port, trade_account=a.account))
    try:
        logged_on = client.connect()
    except Exception as e:  # noqa: BLE001 — dead server raises (ConnectionRefused etc.)
        print(f"LOGON FAILED — {type(e).__name__}: {e}. "
              f"Is Sierra's DTC server up on {a.host}:{a.port}?")
        return 1
    if not logged_on:
        print(f"LOGON FAILED — is Sierra's DTC server up on {a.host}:{a.port}?")
        return 1
    broker = DTCBroker(client=client, symbol=a.symbol, account=a.account,
                       price_scale=a.price_scale)
    rows = [Row("DTC logon", True, f"{a.host}:{a.port} account={a.account}")]
    try:
        rows += run_resting(broker, client, account=a.account, entry=a.entry, stop=a.stop)
        if a.fill:
            rows += run_fill(broker, client, account=a.account, entry=a.entry, stop=a.stop)
    finally:
        if a.fill:                                         # fail-closed: never leave a SIM
            try:                                           # position or working order behind
                broker.flatten(a.account)
            except Exception as e:
                rows.append(Row("fail-closed cleanup flatten", False, f"{e!r}"))
        client.close()

    ok = all(r.ok for r in rows)
    print(f"\n{'check':52s} result")
    for r in rows:
        print(f"{r.label:52s} {'✓' if r.ok else '✗ FAIL'}   {r.detail}")
    print(f"\nDTC SURFACE FORCE TEST: {'✓ all checks passed' if ok else '✗ FAILURES — gate stays RED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
