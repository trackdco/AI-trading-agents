#!/usr/bin/env python3
"""Live CANON runner — the operational entry point for the canon-scripts decision lane.

There is NO paper stage. The account is the FUNDED one; the sequence is:

    gates -> shadow run (zero orders) -> gate_report PASS -> arming token -> live on funded

This runs the AUTHORITATIVE canon lane (shape i, src/live/route_b.RouteBLive): the frozen canon
scripts (canon_mechanical.py + london_canon.py) shelled out via canon_runtime, sized by the
dollar-risk sizer, dropped atomically, and relayed byte-for-byte — the lane that produced the
signed-off baseline. ARMING REFERENCE = leakage-clean + pre-open news blackout, +$55,617.56/386
(output/baseline_book_news.parquet, ANGUS 2026-07-26; docs/PROMOTION-GATE.md is authoritative).
Superseded steps kept as history only: +$52,522.81/404 (leakage-fix only, baseline_book_clean)
and +$56,065.18/400 (pre-lookahead-fix). No champion in the trade path, no LLM verdicts.

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
from src.canon.premarket_guard import PremarketGuard
from src.canon.sierra_files import SierraFileFeed
from src.canon.sierra_symbol import resolve_depth_path, resolve_scid_path
from src.canon.spine import load_spine_config
from src.desk.canon_lane import ScriptVerdictSource
from src.live.route_b import (
    JsonlSink,
    RollState,
    RouteBLive,
    build_shadow_instrument,
)
from src.canon.book import DepthBook
from src.canon.ingestor import CanonIngestor
from src.live.trade_lifecycle import build_lifecycle
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
def _git_sha() -> str:
    """The commit this process runs, for the boot journal. Fail-soft: a box without git
    context still boots — 'unknown' is itself a journaled fact."""
    import subprocess
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                           cwd=Path(__file__).resolve().parents[1], timeout=10)
        return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def load_config(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def setup_logging(run_log: Path) -> logging.Logger:
    run_log.parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("canon_run")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    # Windows consoles default to cp1252, which cannot encode the alert emoji — every
    # Telegram alert then dumps a UnicodeEncodeError traceback into the console (cosmetic
    # but deafening; on-box 2026-07-27). Log the FILE as UTF-8 and let the console replace
    # what it can't draw.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — a non-reconfigurable stream keeps the old behavior
        pass
    fh = logging.FileHandler(run_log, encoding="utf-8")
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


# --------------------------------------------------------------------------- arming (opt-in)
def build_armed_broker(cfg: dict, auth, log: logging.Logger):
    """Connect the real DTC order route for an ARMED run. Every precondition is a hard exit —
    a refused arm must never degrade into a run the operator believes is armed."""
    from src.desk.dtc_broker import DTCBroker
    from src.desk.dtc_client import DTCClient, DTCConfig
    dtc = cfg.get("dtc") or {}
    symbol = str(dtc.get("order_symbol", "")).strip()
    if not symbol.upper().startswith("MNQ"):
        raise SystemExit(f"ARM REFUSED: dtc.order_symbol {symbol!r} is not a micros (MNQ*) "
                         "contract — the canon routes micros only")
    client = DTCClient(DTCConfig(host=str(dtc.get("host", "127.0.0.1")),
                                 port=int(dtc.get("port", 11099)),
                                 trade_account=auth.account))
    try:
        logged_on = client.connect()
    except Exception as e:  # noqa: BLE001 — dead server raises (ConnectionRefused etc.)
        raise SystemExit(f"ARM REFUSED: DTC logon failed on {dtc.get('host', '127.0.0.1')}:"
                         f"{dtc.get('port', 11099)} ({type(e).__name__}: {e}) — is Sierra's "
                         f"DTC server up?") from e
    if not logged_on:
        raise SystemExit(f"ARM REFUSED: DTC logon failed on {dtc.get('host', '127.0.0.1')}:"
                         f"{dtc.get('port', 11099)} — is Sierra's DTC server up?")
    scale = float(dtc.get("price_scale", 1.0))
    log.info("DTC order route up | %s:%s | account=%s | symbol=%s | price_scale=%g",
             dtc.get("host", "127.0.0.1"), dtc.get("port", 11099), auth.account, symbol, scale)
    return DTCBroker(client=client, symbol=symbol, account=auth.account,
                     price_scale=scale), client


def _collect_arm_token() -> str:
    """The phrase Angus issued: ARM_TOKEN env var, else an interactive prompt (never argv —
    a secret on the command line outlives the process in shell history)."""
    import getpass
    import os
    return os.environ.get("ARM_TOKEN") or getpass.getpass("arming token: ")


# --------------------------------------------------------------------------- the canon lane
def build_canon_live(cfg: dict, alerts: LaunchAlerts, log: logging.Logger,
                     arm: bool = False) -> RouteBLive:
    """Assemble the authoritative canon-lane loop from config. Spine DISARMED (_NoBroker)
    unless `arm=True` AND every check in src/live/arming.py passes (Angus's committed token
    hash, the certified-commit provenance rule, DTC logon) — then, and only then, the spine
    is armed with the real order route."""
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
    # Tier-1 limits come from config and are asserted against the signed-off set BEFORE the
    # spine is built (§D2 blocker 3). Fails closed: a drifted or missing limit raises here
    # rather than reaching an order. Previously these rode on dataclass defaults.
    spine_cfg = load_spine_config()
    log.info("spine Tier-1 pinned | clamp=%d micros | daily halt=%.1fR | dd buffer=$%.0f",
             spine_cfg.max_contracts, spine_cfg.daily_loss_halt_r, spine_cfg.dd_halt_buffer)

    broker = client = None
    token = ""
    account = sc.get("account", "FUNDED")
    if arm:
        from src.live.arming import ArmingError, verify_for_arming
        token = _collect_arm_token()
        try:
            auth = verify_for_arming(token)
        except ArmingError as e:
            raise SystemExit(f"ARM REFUSED: {e}") from e
        broker, client = build_armed_broker(cfg, auth, log)
        account = auth.account

    instrument = build_shadow_instrument(out_dir, account=account, cfg=spine_cfg,
                                         kill_file=kill_file, broker=broker,
                                         arm_token=(token if arm else None))
    if arm:
        if not instrument.spine.arm(token):
            raise SystemExit("ARM REFUSED: spine rejected the token at arm() — "
                             "this should be impossible after verify_for_arming; investigate")
        log.info("SPINE ARMED | account=%s", account)
    # lifecycle via the SAME assembly both modes use (build_lifecycle): disarmed it journals
    # would-be actions with executed=False and is broker-less — §D evidence, zero broker
    # calls possible; armed it drives the managed exit through the real order route.
    ingestor = CanonIngestor(book=DepthBook())
    lifecycle = build_lifecycle(broker, account, ingestor, out_dir, armed=arm)
    # corrections 2+3 live: news blackout + 09:55-10:00 dead zone + the sentinel's
    # fail-closed snapshot requirement (no board today -> no pre-open entries).
    guard = PremarketGuard()
    log.info("premarket guard | %d blackout days on calendar | snapshot required: %s",
             len(guard.gate.releases), guard.require_snapshot)
    live = RouteBLive(
        feed=feed, data_dir=data_dir, root=root, suffix=suffix, alerts=alerts,
        verdict_source=ScriptVerdictSource(),
        verdict_sink=JsonlSink(out_dir / "verdicts.jsonl"),
        decision_sink=SpineJournalSink(out_dir / "decisions.jsonl"),
        instrument=instrument, ingestor=ingestor, lifecycle=lifecycle,
        premarket_guard=guard, roll_state=RollState(root=root),
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
    ap.add_argument("--arm", action="store_true",
                    help="ARM the spine: requires Angus's committed authorization "
                         "(config/arming.yaml), the token phrase (ARM_TOKEN env or prompt), "
                         "HEAD == the certified commit, and a live DTC logon. Any failed "
                         "check is a hard exit — no silent fallback to shadow")
    args = ap.parse_args(argv)

    cfg = load_config(Path(args.config))
    log = setup_logging(Path(cfg["paths"]["run_log"]))
    log.info("=" * 70)
    log.info("canon_run START | config=%s (canon lane, %s)", args.config,
             "ARM REQUESTED — verifying authorization" if args.arm
             else "DISARMED — zero orders")
    # Boot provenance (Angus 2026-07-26): journal the exact commit this run executes, so
    # the arming token can NAME the commit it arms and any journal row is attributable.
    sha = _git_sha()
    log.info("boot | git=%s", sha)
    SpineJournalSink(Path(cfg["paths"]["journal_dir"]) / "decisions.jsonl")(
        {"type": "boot", "git_sha": sha, "config": str(args.config)})

    kill = Path(cfg["paths"]["kill_file"])
    if kill.exists():
        log.warning("KILL FILE PRESENT (%s) — the spine will halt until a human removes it", kill)

    alerts = build_alerts(cfg, log, force_off=(args.telegram == "off"))
    live = build_canon_live(cfg, alerts, log, arm=args.arm)

    state = {"stop": False}

    def _handle(signum, _frame):
        log.warning("signal %s received — requesting clean stop", signum)
        state["stop"] = True

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)

    sc = cfg.get("feed", {}).get("sierra", {})
    alerts.say(f"🔴 canon runner up — ARMED, live orders enabled (commit {sha[:12]})"
               if args.arm else
               "▶️ canon runner up (DISARMED — zero orders until the arming token)")
    live.serve(sleep_fn=time.sleep, stop_fn=lambda: state["stop"],
               poll_interval_s=float(sc.get("poll_interval_s", 1.0)))
    alerts.say("⏹️ canon runner STOPPED")
    log.info("canon_run STOP")
    log.info("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
