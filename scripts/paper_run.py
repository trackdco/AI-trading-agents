#!/usr/bin/env python3
"""Paper-trading launcher (Phase 4 Stage 8) — assemble and RUN the LiveRunner for real.

This is the operational entrypoint the desk starts to paper-trade the frozen champion.
It wires the exact stack the validated full-stack drill uses (scripts/runner_drill.py),
adds real Telegram alerting + file logging, and is driven entirely by config/live.yaml.

What it guarantees
------------------
* Restart-safe   — LiveRunner restores the ledger, re-seeds the risk guard, and
                   re-fires nothing (no duplicate alerts / journal rows) on a re-launch.
* KILL-aware      — the RiskGuard reads paths.kill_file on every gate; present => no new
                   trades, every session, until a human deletes it. Logged loudly at start.
* Alerting        — Telegram (from .env) on START / STOP / TRADE / HALT / DAILY SUMMARY,
                   and every one of those is also written to paths.run_log.
* Live regime     — the runner defaults to LiveVectorPolicy (src/live/vector.py): the
                   E3/E4 book is computed from live bars, NOT the precomputed CSV.
* Pluggable feed  — feed.type selects the bar source. `replay` streams parquet (today,
                   validated). `live` is the Stage-8 seam, marked <<LIVE FEED ADAPTER>>.

Usage
-----
    python -m scripts.paper_run                     # uses config/live.yaml
    python -m scripts.paper_run --config config/live.yaml --session 2026-03-17
    python -m scripts.paper_run --telegram off      # run silent (log only, no network)

Clean shutdown: on SIGINT/SIGTERM the current bar finishes, the session is finalized
(daily summary flushed), a STOP alert fires, and the process exits 0.
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.live.feed import BAR_COLS, Bar, ReplayFeed
from src.live.risk import RiskLimits
from src.live.runner import LiveRunner
from src.live.telegram import (
    TelegramAlerts,
    TelegramConfig,
    fmt_daily,
    fmt_halt,
    fmt_trade,
    kill_switch_redundancy_warning,
)

NY = "America/New_York"


# --------------------------------------------------------------------------- alerts
class LaunchAlerts:
    """The single alert surface the runner calls (say / on_trade / on_halt /
    daily_summary). Every message is LOGGED to the run log; when a Telegram client is
    wired it is also sent. Fail-soft: the underlying TelegramAlerts already isolates
    network errors, and logging never raises into the loop."""

    def __init__(self, log: logging.Logger, tg: TelegramAlerts | None = None):
        self._log = log
        self._tg = tg

    def say(self, text: str) -> None:
        self._log.info("ALERT | %s", text.replace("\n", " | "))
        if self._tg is not None:
            self._tg.say(text)

    def on_trade(self, ev) -> None:
        self._log.info("TRADE | %s", fmt_trade(ev).replace("\n", " | "))
        if self._tg is not None:
            self._tg.on_trade(ev)

    def on_halt(self, date: str, reason: str) -> None:
        self._log.warning("HALT  | %s", fmt_halt(date, reason))
        if self._tg is not None:
            self._tg.on_halt(date, reason)

    def daily_summary(self, broker, date: str) -> None:
        d = broker.day_summary(date)
        self._log.info("DAILY | %s", fmt_daily(date, d.trades, d.wins, d.losses,
                                               d.points, d.dollars,
                                               broker.equity()).replace("\n", " | "))
        if self._tg is not None:
            self._tg.daily_summary(broker, date)


# --------------------------------------------------------------------------- config
def load_config(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def setup_logging(run_log: Path) -> logging.Logger:
    run_log.parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("paper_run")
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
    except Exception as e:  # noqa: BLE001 — missing .env creds etc.: degrade to log-only, never crash
        log.warning("telegram requested but unavailable (%s: %s) — running silent",
                    type(e).__name__, e)
        return LaunchAlerts(log, tg=None)


def _check_kill_switch_redundancy(tgcfg: TelegramConfig, log: logging.Logger,
                                  tg: TelegramAlerts) -> None:
    """Warn (loudly, and over Telegram) if fewer than 2 humans can reach the /kill switch.
    A 24/5 autonomous system with one reachable operator is a design fault. WARN, never
    block startup (Angus ruling)."""
    warn = kill_switch_redundancy_warning(tgcfg)
    if warn is None:
        log.info("kill-switch reachability OK — %d authorized Telegram operators",
                 len(tgcfg.allowed_user_ids))
        return
    log.warning("=" * 70)
    log.warning("%s", warn)
    log.warning("=" * 70)
    tg.say(warn)                                        # broadcast to the group on launch


def build_runner(cfg: dict, alerts: LaunchAlerts, ambient_extra=None) -> LiveRunner:
    paths = cfg["paths"]
    risk = cfg.get("risk", {})
    runner_cfg = cfg.get("runner", {})
    limits = RiskLimits(
        daily_loss_dollars=float(risk.get("daily_loss_dollars", 1500.0)),
        max_trades_per_day=int(risk.get("max_trades_per_day", 3)),
        equity_floor_dollars=(None if risk.get("equity_floor_dollars") is None
                              else float(risk["equity_floor_dollars"])),
        kill_file=Path(paths["kill_file"]),
    )
    return LiveRunner(
        ledger_path=Path(paths["ledger"]),
        journal_dir=Path(paths["journal_dir"]),
        starting_equity=float(cfg["account"]["starting_equity"]),
        limits=limits,
        alerts=alerts,
        history_days=int(runner_cfg.get("history_days", 20)),
        ambient=bool(runner_cfg.get("ambient", True)),
        ambient_extra=ambient_extra,   # roll/contract stamp on the champion journal (sierra path)
        # spread_guard stays None unless a real guard is constructed; config flag is
        # advisory only here (arming it changes fills — deliberately opt-in).
    )


# ------------------------------------------------------------------------- feed seam
def stream_replay(runner: LiveRunner, feed_cfg: dict, log: logging.Logger,
                  should_stop) -> None:
    """Drive the runner over one paper session from historical bars.

    Mirrors the validated drill: warmup bars are fed with detection OFF (and alerts
    suppressed, so the 16-18 warmup days do not emit bogus 0-trade summaries), then the
    session window streams with detection ON. The runner's LiveVectorPolicy classifies
    the day's E3/E4 book from the SAME accumulated history — no precomputed CSV."""
    rc = feed_cfg["replay"]
    parquet = rc["parquet"]
    session = str(rc["session"])
    warmup_days = int(rc.get("warmup_days", 18))

    df = pd.read_parquet(parquet)
    if "ts_event" not in df.columns:
        raise ValueError(f"{parquet} missing ts_event")
    win_lo = pd.Timestamp(session, tz=NY)
    warm_lo = win_lo - pd.Timedelta(days=warmup_days)
    warmup = df[(df.ts_event >= warm_lo) & (df.ts_event < win_lo)]
    window = ReplayFeed(df, start=session, end=session)
    log.info("replay feed | session=%s warmup_days=%d warmup_bars=%d session_bars=%d",
             session, warmup_days, len(warmup), len(window))

    # --- warmup: Vault + detector + vector policy see history; no trades, no alerts ---
    saved, runner.alerts = runner.alerts, None
    runner.detect_enabled = False
    for row in warmup[list(BAR_COLS)].sort_values("ts_event").itertuples(index=False):
        runner.on_bar(Bar.from_row({c: getattr(row, c) for c in BAR_COLS}))
    runner.alerts = saved
    runner.detect_enabled = True
    log.info("warmup complete — going live on the session window")

    # --- session window: detection on, alerts live ---
    runner.alerts.say(f"▶️ NQ paper bot UP (replay {session}) — equity "
                      f"${runner.broker.equity():,.0f}, "
                      f"{len(runner.broker.trades)} trades restored")
    for bar in window.stream():
        if should_stop():
            log.warning("stop requested — halting stream after current bar")
            break
        runner.on_bar(bar)
    runner.finalize()


def stream_live(runner: LiveRunner, feed_cfg: dict, log: logging.Logger,
                should_stop, roll_state=None) -> None:
    """Route-B live tail: drive the paper desk off Sierra's own .scid/.depth files.

    Fans each closed minute to the champion (journal.jsonl) AND a shadow canon/spine that
    emits the promotion-gate evidence (spine.jsonl / rejects.jsonl / sizing.jsonl). The spine
    is DISARMED (no broker call possible); the champion uses the PaperBroker. See
    src/live/route_b.py. Config block `feed.sierra`:
        data_dir       Sierra Data dir (e.g. C:/SierraChart/Data)   [required]
        scid           explicit .scid path override                 [optional]
        root/suffix    symbol root / exchange tag (NQ / -CME)        [default NQ / -CME]
        trailing_floor EOD drawdown line for AccountState            [default account floor]
        flush_ms       configured Sierra flush (report baseline)     [default 1000]
        poll_interval_s / warmup.{parquet,session,warmup_days}
    """
    import time

    from src.canon.sierra_files import SierraFileFeed
    from src.canon.sierra_symbol import resolve_depth_path, resolve_scid_path
    from src.live.route_b import RouteBLive, build_shadow_instrument

    sc = feed_cfg.get("sierra", {})
    data_dir = sc.get("data_dir")
    if not data_dir:
        raise NotImplementedError("feed.sierra.data_dir not set — point it at Sierra's Data dir")
    root, suffix = sc.get("root", "NQ"), sc.get("suffix", "-CME")
    now = pd.Timestamp.now(tz="UTC")
    today = str(now.tz_convert(NY).date())
    scid = Path(sc["scid"]) if sc.get("scid") else resolve_scid_path(data_dir, now, root, suffix)
    depth = resolve_depth_path(data_dir, now, day=today, root=root, suffix=suffix)
    log.info("Route-B live | scid=%s depth=%s", scid, depth)

    out_dir = Path(runner.journal.dir)
    feed = SierraFileFeed(scid, depth if depth.exists() else None,
                          flush_ms=int(sc.get("flush_ms", 1000)),
                          on_lag=lambda r: None)
    # AUTHORITATIVE lane = the canon scripts (shape i). The champion is STRUCTURALLY ABSENT from
    # the live path here — it is NOT wired as the comparator, because its LiveRunner journals to
    # the same dir and would collide with the canon verdict journal. The comparator canary (with
    # an ISOLATED journal dir) is wired in the dedicated canon entry point (P3), not paper_run
    # (which is itself being retired — no paper stage; the funded account is the target).
    from src.canon.infra import SpineJournalSink
    from src.desk.canon_lane import ScriptVerdictSource
    from src.live.route_b import JsonlSink
    instrument = build_shadow_instrument(out_dir, account=sc.get("account", "FUNDED"))
    live = RouteBLive(
        feed=feed, data_dir=data_dir, root=root, suffix=suffix, roll_state=roll_state,
        verdict_source=ScriptVerdictSource(),
        verdict_sink=JsonlSink(out_dir / "verdicts.jsonl"),
        decision_sink=SpineJournalSink(out_dir / "decisions.jsonl"),
        instrument=instrument, alerts=runner.alerts)

    # warm start from recent history (bars only; footprint optional via warmup.footprint)
    warm = sc.get("warmup", {})
    if warm.get("parquet"):
        df = pd.read_parquet(warm["parquet"])
        session = str(warm.get("session", today))
        wlo = pd.Timestamp(session, tz=NY) - pd.Timedelta(days=int(warm.get("warmup_days", 20)))
        hist = df[(df.ts_event >= wlo) & (df.ts_event < pd.Timestamp(session, tz=NY))]
        fp = pd.read_parquet(warm["footprint"]) if warm.get("footprint") else None
        live.warm(hist, fp)
        log.info("warm start | %d history bars", len(hist))

    log.info("Route-B live tail serving (poll every %ss) — Ctrl-C / /kill to stop",
             sc.get("poll_interval_s", 1.0))
    live.serve(sleep_fn=time.sleep, stop_fn=should_stop,
               poll_interval_s=float(sc.get("poll_interval_s", 1.0)))


# ------------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config/live.yaml")
    ap.add_argument("--session", default=None, help="override feed.replay.session")
    ap.add_argument("--telegram", choices=["on", "off"], default="on",
                    help="off => force silent (log only), overrides config")
    args = ap.parse_args(argv)

    cfg = load_config(Path(args.config))
    if args.session:
        cfg.setdefault("feed", {}).setdefault("replay", {})["session"] = args.session

    log = setup_logging(Path(cfg["paths"]["run_log"]))
    log.info("=" * 70)
    log.info("paper_run START | config=%s feed=%s", args.config, cfg["feed"]["type"])

    kill = Path(cfg["paths"]["kill_file"])
    if kill.exists():
        log.warning("KILL FILE PRESENT (%s) — no new trades will be admitted this run "
                    "until a human removes it", kill)

    alerts = build_alerts(cfg, log, force_off=(args.telegram == "off"))
    # Route-B paths get a shared live roll tag (RollState): the runner's ambient stamps
    # roll/contract on the champion journal, the loop tags bars + journals roll events.
    ftype = cfg["feed"]["type"]
    roll_state = None
    if ftype in ("live", "sierra"):
        from src.live.route_b import RollState
        roll_state = RollState(root=cfg["feed"].get("sierra", {}).get("root", "NQ"))
    runner = build_runner(cfg, alerts,
                          ambient_extra=(roll_state.context if roll_state is not None else None))
    log.info("runner assembled | equity=$%.0f ledger=%s journal=%s",
             runner.broker.equity(), cfg["paths"]["ledger"], cfg["paths"]["journal_dir"])

    # --- clean shutdown plumbing ---
    state = {"stop": False}

    def _handle(signum, _frame):
        log.warning("signal %s received — requesting clean stop", signum)
        state["stop"] = True

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)

    try:
        if ftype == "replay":
            stream_replay(runner, cfg["feed"], log, lambda: state["stop"])
        elif ftype in ("live", "sierra"):
            stream_live(runner, cfg["feed"], log, lambda: state["stop"], roll_state)
        else:
            raise ValueError(f"unknown feed.type {ftype!r} (expected replay|sierra|live)")
    except NotImplementedError as e:
        log.error("%s", e)
        return 2

    alerts.say(f"⏹️ NQ paper bot STOPPED — equity ${runner.broker.equity():,.0f}, "
               f"{len(runner.broker.trades)} trades total")
    log.info("paper_run STOP | equity=$%.0f trades=%d",
             runner.broker.equity(), len(runner.broker.trades))
    log.info("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
