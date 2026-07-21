"""Container entrypoint.

FEED=replay  → run the historical proof harness (scripts.replay).
FEED=live    → GATED. Refuses to start until the Step-4 parity report is signed
               off and the §12 February calibration passes (per user directive:
               no live feed until the validation gate clears).
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    feed = os.environ.get("FEED", "replay").lower()
    if feed == "live":
        sys.stderr.write(
            "REFUSING to start live feed.\n"
            "The live Databento connection is gated behind:\n"
            "  1. Step-4 parity report signed off by Angus (needs Feb 2026 data), and\n"
            "  2. the §12 February calibration passing.\n"
            "Neither has cleared. Set FEED=replay for historical runs.\n")
        return 2
    sys.stderr.write("FEED=replay: use `python -m scripts.replay --data ... "
                     "--start ... --end ...`\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
