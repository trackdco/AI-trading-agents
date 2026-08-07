#!/usr/bin/env python3
"""Kill-switch listener — the canon stack's /kill consumer, as its OWN process.

The canon spine halts on a KILL FILE (config/live.yaml paths.kill_file). This process is
the thing that writes it when Pat or Angus sends /kill on Telegram. It is deliberately
SEPARATE from canon_run: a kill switch inside the process you may need to kill is a single
point of failure — this listener keeps working even if the runner is wedged, and the
runner keeps trading (until told otherwise) even if this listener dies. Run BOTH.

Commands (locked to TELEGRAM_ALLOWED_USER_IDS; strangers are silently ignored):
    /kill    -> write the KILL file. The spine halts on its next check and STAYS halted;
                there is no /reset — removing the file requires a human at the box.
    /status  -> kill state + how fresh the runner's log is (stale = runner not writing).

Run on the box (keep it running alongside canon_run, e.g. its own console or a service):
    python -m scripts.kill_listener                 # uses config/live.yaml + .env

C4 drill: with this running, BOTH operators send /kill from their own phones (one at a
time, deleting the file at the box in between) and confirm the file appears and the
runner's spine journals the halt. That — not the alert test — is the kill-switch gate.
"""
from __future__ import annotations

import signal
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.live.telegram import KillFileListener, TelegramAlerts, TelegramConfig  # noqa: E402


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="config/live.yaml")
    args = ap.parse_args(argv)

    cfg = yaml.safe_load(Path(args.config).read_text())
    kill_file = Path(cfg["paths"]["kill_file"])
    run_log = Path(cfg["paths"]["run_log"])
    tg = TelegramConfig.from_env()
    listener = KillFileListener(tg, kill_file, run_log)

    state = {"stop": False}

    def _handle(signum, _frame):
        state["stop"] = True

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)

    TelegramAlerts(tg).say("🛡 kill listener up (independent of the runner) — "
                           "/kill and /status are live")
    print(f"kill listener | file={kill_file} | operators={len(tg.allowed_user_ids)}")
    while not state["stop"]:
        listener.poll_once(timeout=25)          # long-poll; returns on traffic or timeout
        time.sleep(0.5)
    print("kill listener stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
