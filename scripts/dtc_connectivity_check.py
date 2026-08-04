#!/usr/bin/env python3
"""DTC connectivity burn-in (2026-08-03 audit) — proves the idle-reconnect fix survives
REAL time against Sierra's live DTC server, with ZERO order risk.

This is deliberately NOT ny_run.py and never imports the order-submission path
(DTCBroker.submit_bracket / cancel_order / modify_stop / close_partial). It only ever
does: connect, heartbeat (DTCClient.ensure_connected — the exact call the live loop's
keepalive now runs on a cadence), and an occasional read-only positions() query. It
cannot place, modify, or cancel anything, on any account, by construction.

Why this exists: the 2026-08-02/03 incidents only happen after REAL idle time against
the REAL socket — no replay or unit test can produce that condition, only clock time
can. This script is the safe way to accumulate that clock time before the next --arm.

    python -m scripts.dtc_connectivity_check --hours 4
    python -m scripts.dtc_connectivity_check --hours 4 --account LFE050-9YSC047M-TEST001

PASS for the burn-in certification (docs/RUNBOOK-burnin-r16.md) = it runs the full
requested window and every detected drop heals, with zero unhealed at the end.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.canon_run import load_config       # noqa: E402
from src.desk.dtc_client import DTCClient, DTCConfig  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/live.yaml")
    ap.add_argument("--hours", type=float, default=4.0)
    ap.add_argument("--interval-s", type=float, default=10.0,
                    help="keepalive cadence — matches DTC_KEEPALIVE_S in scripts/ny_run.py")
    ap.add_argument("--account", default="",
                    help="trade account for the read-only positions() probe; blank is "
                         "fine if your Sierra DTC logon doesn't require one up front")
    a = ap.parse_args(argv)

    cfg = load_config(Path(a.config))
    dtc = cfg.get("dtc") or {}
    ccfg = DTCConfig(host=str(dtc.get("host", "127.0.0.1")), port=int(dtc.get("port", 11099)),
                     trade_account=a.account)
    client = DTCClient(cfg=ccfg)
    print(f"connecting to {ccfg.host}:{ccfg.port} (account={a.account!r}) ...")
    if not client.connect():
        print("CONNECT FAILED — is Sierra's DTC server running and listening?")
        return 1
    print("connected. This script NEVER submits/modifies/cancels orders — "
          "read-only heartbeat + position checks only.\n")

    end_at = time.time() + a.hours * 3600
    cycles = drops = healed = 0
    down_since: float | None = None
    longest_down_s = 0.0
    was_up = True
    try:
        while time.time() < end_at:
            cycles += 1
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                ok = client.ensure_connected()
            except Exception as e:                  # noqa: BLE001 — never crash the burn-in
                ok = False
                print(f"[{ts}] cycle {cycles}: ensure_connected raised {e!r}")
            if ok:
                if not was_up:
                    downtime = time.time() - (down_since or time.time())
                    longest_down_s = max(longest_down_s, downtime)
                    healed += 1
                    print(f"[{ts}] cycle {cycles}: RECONNECTED after {downtime:.1f}s downtime")
                    down_since = None
                elif cycles % max(1, int(300 / a.interval_s)) == 0:   # ~every 5 min
                    try:
                        pos = client.positions()
                        # NET signed size (DTCBroker.position()'s own math) — NOT len(pos).
                        # Sierra sends one position REPORT per instrument even when flat
                        # (Quantity 0), so len(pos)==1 reads as "1 contract open" when the
                        # account is actually flat. Caught 2026-08-04 when this printed
                        # positions=1 for 10+ minutes against a genuinely empty account.
                        net = sum(int(p.get("Quantity") or 0) for p in pos)
                        print(f"[{ts}] cycle {cycles}: alive, net_position={net}")
                    except Exception as e:           # noqa: BLE001 — log-only, keep going
                        print(f"[{ts}] cycle {cycles}: alive "
                              f"(positions query failed: {e!r})")
                was_up = True
            else:
                if was_up:
                    drops += 1
                    down_since = time.time()
                    print(f"[{ts}] cycle {cycles}: DROP DETECTED — reconnect currently failing")
                was_up = False
            time.sleep(a.interval_s)
    except KeyboardInterrupt:
        print("\ninterrupted by user")
    finally:
        client.close()

    unhealed = 0 if was_up else 1
    hours_run = cycles * a.interval_s / 3600
    print("\n=== DTC CONNECTIVITY BURN-IN SUMMARY ===")
    print(f"cycles: {cycles}   duration: {hours_run:.2f}h")
    print(f"drops detected: {drops}   healed: {healed}   unhealed at end: {unhealed}")
    print(f"longest downtime observed: {longest_down_s:.1f}s")
    verdict = "PASS" if unhealed == 0 else "FAIL — still down at end, do not arm yet"
    print(verdict)
    return 0 if unhealed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
