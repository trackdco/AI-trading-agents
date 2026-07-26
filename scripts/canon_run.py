#!/usr/bin/env python3
"""Live CANON runner — the operational entry point for the canon-scripts decision lane.

There is NO paper stage. The account is the FUNDED one; the sequence is:

    gates -> shadow run (zero orders) -> gate_report PASS -> arming token -> live on funded

This runs the AUTHORITATIVE canon lane (shape i, src/live/route_b.RouteBLive): the frozen canon
scripts (canon_mechanical.py + london_canon.py) shelled out via canon_runtime, sized by the
dollar-risk sizer, dropped atomically, and relayed byte-for-byte — the lane that produced the
signed-off baseline_book (400/400, +$56,065.18). No champion in the trade path, no LLM verdicts.

Until the arming token is presented, the spine is DISARMED (`_NoBroker`): it evaluates and
journals every decision but CANNOT route an order — the shadow run emits zero orders. Each
session's canon verdicts drive the verdict journal (verdicts.jsonl) + the disarmed spine
(spine.jsonl / sizing.jsonl / rejects.jsonl); roll events go to decisions.jsonl.

What it guarantees
------------------
* Disarmed by default — zero orders until Angus's arming token (a deliberate later step).
* KILL-aware        — the spine reads paths.kill_file; present => the spine halts.
* Alerting          — Telegram (from .env) on START / STOP / ROLL, also written to the run log.
* Route-B live data — tails Sierra's own .scid/.depth files (DTC won't serve data); FeedGuard
                      (stall/gap), warm start, contract-roll re-point all carry over.

Usage
-----
    python -m scripts.canon_run                      # uses config/live.yaml
    python -m scripts.canon_run --telegram off       # run silent (log only, no network)

Clean shutdown: on SIGINT/SIGTERM the current poll finishes, a STOP alert fires, exit 0.
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.canon.infra import SpineJournalSink
from src.canon.sierra_files import SierraFileFeed
from src.canon.sierra_symbol import resolve_depth_path, resolve_scid_path
from src.desk.canon_lane import ScriptVerdictSource
from src.live.route_b import (
    JsonlSink,
    RollState,
    RouteBLive,
    build_shadow_instrument,
)
from src.live.telegram import (
    TelegramAlerts,
    TelegramConfig,
    kill_switch_redundancy_warning,
)

NY = "America/New_York"


# --------------------------------------------------------------------------- alerts
class LaunchAlerts:
    """The single alert surface the runner calls. Every message is LOGGED; when a Telegram
    client is wired it is also sent. Fail-soft: TelegramAlerts isolates network errors, and
    logging never raises into the loop."""

    def __init__(self, log: logging.Logger, tg: TelegramAlerts | None = None):
        self._log = log
        self._tg = tg

    def say(self, text: str) -> None:
        self._log.info("ALERT | %s", text.replace("\n", " | "))
        if self._tg is not None:
            self._tg.say(text)


# --------------------------------------------------------------------------- config / logging
def load_config(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def setup_logging(run_log: Path) -> logging.Logger:
    run_log.parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("canon_run")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(run_log)
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    log.addHandler(fh)
    log.addHandler(sh)
    return log


def build_alerts(cfg: dict, log: logging.Logger, force_off: bool) -> LaunchAlerts:
    enabled = bool(cfg.get("telegram", {}).get("enabled", False)) and not force_off
    if not enabled:
        log.info("telegram DISABLED — running silent (alerts are logged only)")
        return LaunchAlerts(log, tg=None)
    try:
        tgcfg = TelegramConfig.from_env()
        tg = TelegramAlerts(tgcfg)
        log.info("telegram ENABLED — alerts will broadcast to the group")
        alerts = LaunchAlerts(log, tg=tg)
        _check_kill_switch_redundancy(tgcfg, log, tg)
        return alerts
    except Exception as e:  # noqa: BLE001 — missing .env creds etc.: degrade to log-only
        log.warning("telegram requested but unavailable (%s: %s) — running silent",
                    type(e).__name__, e)
        return LaunchAlerts(log, tg=None)


def _check_kill_switch_redundancy(tgcfg: TelegramConfig, log: logging.Logger,
                                  tg: TelegramAlerts) -> None:
    """Warn (loudly, and over Telegram) if fewer than 2 humans can reach the /kill switch. A
    24/5 autonomous desk with one reachable operator is a design fault. WARN, never block."""
    warn = kill_switch_redundancy_warning(tgcfg)
    if warn is None:
        log.info("kill-switch reachability OK — %d authorized Telegram operators",
                 len(tgcfg.allowed_user_ids))
        return
    log.warning("=" * 70)
    log.warning("%s", warn)
    log.warning("=" * 70)
    tg.say(warn)


# --------------------------------------------------------------------------- the canon lane
def build_canon_live(cfg: dict, alerts: LaunchAlerts, log: logging.Logger) -> RouteBLive:
    """Assemble the authoritative canon-lane loop from config. Spine DISARMED (_NoBroker)."""
    paths = cfg["paths"]
    out_dir = Path(paths["journal_dir"])
    kill_file = Path(paths["kill_file"])
    sc = cfg.get("feed", {}).get("sierra", {})
    data_dir = sc.get("data_dir")
    if not data_dir:
        raise SystemExit("feed.sierra.data_dir not set — point it at Sierra's Data dir")
    root, suffix = sc.get("root", "NQ"), sc.get("suffix", "-CME")

    now = pd.Timestamp.now(tz="UTC")
    today = str(now.tz_convert(NY).date())
    scid = Path(sc["scid"]) if sc.get("scid") else resolve_scid_path(data_dir, now, root, suffix)
    depth = resolve_depth_path(data_dir, now, day=today, root=root, suffix=suffix)
    log.info("canon lane | scid=%s depth=%s", scid, depth)

    feed = SierraFileFeed(scid, depth if depth.exists() else None,
                          flush_ms=int(sc.get("flush_ms", 1000)), on_lag=lambda r: None)
    acct = cfg.get("account", {})
    instrument = build_shadow_instrument(out_dir, account=sc.get("account", "FUNDED"),
                                         kill_file=kill_file)
    live = RouteBLive(
        feed=feed, data_dir=data_dir, root=root, suffix=suffix, alerts=alerts,
        verdict_source=ScriptVerdictSource(),
        verdict_sink=JsonlSink(out_dir / "verdicts.jsonl"),
        decision_sink=SpineJournalSink(out_dir / "decisions.jsonl"),
        instrument=instrument, roll_state=RollState(root=root),
        account_equity=float(acct.get("equity", 50_000.0)))

    # warm start from recent history so day-one levels/tape are correct
    warm = sc.get("warmup", {})
    if warm.get("parquet"):
        df = pd.read_parquet(warm["parquet"])
        session = str(warm.get("session", today))
        wlo = pd.Timestamp(session, tz=NY) - pd.Timedelta(days=int(warm.get("warmup_days", 20)))
        hist = df[(df.ts_event >= wlo) & (df.ts_event < pd.Timestamp(session, tz=NY))]
        fp = pd.read_parquet(warm["footprint"]) if warm.get("footprint") else None
        live.warm(hist, fp)
        log.info("warm start | %d history bars", len(hist))
    return live


# ------------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config/live.yaml")
    ap.add_argument("--telegram", choices=["on", "off"], default="on",
                    help="off => force silent (log only), overrides config")
    args = ap.parse_args(argv)

    cfg = load_config(Path(args.config))
    log = setup_logging(Path(cfg["paths"]["run_log"]))
    log.info("=" * 70)
    log.info("canon_run START | config=%s (canon lane, DISARMED — zero orders)", args.config)

    kill = Path(cfg["paths"]["kill_file"])
    if kill.exists():
        log.warning("KILL FILE PRESENT (%s) — the spine will halt until a human removes it", kill)

    alerts = build_alerts(cfg, log, force_off=(args.telegram == "off"))
    live = build_canon_live(cfg, alerts, log)

    state = {"stop": False}

    def _handle(signum, _frame):
        log.warning("signal %s received — requesting clean stop", signum)
        state["stop"] = True

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)

    sc = cfg.get("feed", {}).get("sierra", {})
    alerts.say("▶️ canon runner up (DISARMED — zero orders until the arming token)")
    live.serve(sleep_fn=time.sleep, stop_fn=lambda: state["stop"],
               poll_interval_s=float(sc.get("poll_interval_s", 1.0)))
    alerts.say("⏹️ canon runner STOPPED")
    log.info("canon_run STOP")
    log.info("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
