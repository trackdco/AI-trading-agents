#!/usr/bin/env python3
"""
NQ-bot re-test driver  (research/nq-bot-retest/retest_backtest.py)
==================================================================
Runs the MNQ liquidity-sweep bot's OWN CausalReplayEngine — imported from the bot
repository, not re-implemented — with the three pre-registered changes switchable
by flag. Contract: PREREGISTRATION.md in this directory.

    C1  --stop-floor {none,a5_10pt,a22_2xatr}  floor applied after min(ATR14x2, structural)
                                               and BEFORE the unchanged 30pt cap
    C2  --rth-only                             entry permitted only when the SIGNAL bar's
                                               timestamp satisfies the bot's own is_rth()
    C3  --rr-gate {kept,removed}               the min-R:R gate against the ATR14x1.5 target
                                               the executor never places
        --cap-lifted                           DISCLOSED SENSITIVITY only: skip the 30pt gate
        --slippage-mult X                      abort-condition 2: scale both slippage constants

Untouched configuration == `--stop-floor none --rr-gate kept` with neither flag.

Two NON-behavioural patches are applied in-process (the bot's files are never edited):
  1. the three write-only logging lists (sweep_detector.sweep_log,
     signal_aggregator._signal_history, engine._shadow_signals) are bounded. The backtest
     never reads them; their unbounded growth is what slowed the original 4-year run
     from ~130 bars/s to ~12 bars/s.  `--no-perf-patch` disables this.
  2. trade IDs are sequential instead of uuid4, so a sealed output is byte-reproducible.
Both are gated by the exact-reproduction check recorded in REPRODUCTION.md.

Checkpoints (`--checkpoint PATH --checkpoint-every N`, `--resume`) pickle the whole engine;
a resumed run reproduces a straight run byte-for-byte (tested in REPRODUCTION.md).
`--final-checkpoint PATH` saves the engine state after the last bar; `--continue-from PATH`
loads it and processes only the bars AFTER the saved last bar (same 1m series, HTF files that
are a continuation of the saved run's). The C1/C2/C3 readings must match the saved state;
`--cap-lifted` and `--slippage-mult` may differ (branch point disclosed in meta).
"""
import argparse
import asyncio
import hashlib
import importlib.util
import json
import math
import os
import pickle
import subprocess
import sys
import time as time_module
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RETEST_VERSION = "1.0"
HERE = Path(__file__).resolve().parent
BOT_ROOT = Path(os.environ.get("NQ_BOT_ROOT", "/home/user/prat617/ai-trading-bot/nq_bot_vscode"))
ET = ZoneInfo("America/New_York")


# ── Import the bot's backtest script as a module (its own sys.path setup runs) ──────────
def _load_bot_backtest():
    path = BOT_ROOT / "scripts" / "full_backtest.py"
    if not path.exists():
        sys.exit(f"bot backtest script not found: {path}  (set NQ_BOT_ROOT)")
    spec = importlib.util.spec_from_file_location("full_backtest", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["full_backtest"] = mod
    spec.loader.exec_module(mod)
    return mod, path


fb, FB_PATH = _load_bot_backtest()

# Names the copied decision block refers to — bound from the bot module, never redefined here.
for _name in (
    "np", "is_rth", "SWEEP_MIN_SCORE", "CONTEXT_AGGREGATOR_BOOST", "CONTEXT_OB_BOOST",
    "CONTEXT_FVG_BOOST", "SignalDirection", "HIGH_CONVICTION_MIN_SCORE",
    "HIGH_CONVICTION_MAX_STOP_PTS", "MIN_RR_RATIO", "RiskDecision", "logger",
):
    globals()[_name] = getattr(fb, _name)

import execution.scale_out_executor as _sxe  # noqa: E402  (bot module; for the id patch)


# ── Patch 1: bounded write-only lists ────────────────────────────────────────────────────
class BoundedList(list):
    """list whose append() trims to `maxlen` (amortised O(1)); slicing/len still work."""

    def __init__(self, maxlen: int):
        super().__init__()
        self.maxlen = maxlen

    def append(self, item):
        super().append(item)
        if len(self) > 2 * self.maxlen:
            del self[: len(self) - self.maxlen]


def apply_perf_patch(engine) -> None:
    engine.sweep_detector.sweep_log = BoundedList(1_000)
    engine.signal_aggregator._signal_history = BoundedList(100)
    engine._shadow_signals = BoundedList(1_000)


# ── Patch 2: deterministic trade IDs ─────────────────────────────────────────────────────
class _SequentialUUID:
    """Stands in for the `uuid` module inside the executor: str(uuid4())[:12] -> '000000000001'."""

    def __init__(self):
        self.n = 0

    def uuid4(self):
        self.n += 1
        return f"{self.n:012d}"


def apply_deterministic_ids() -> None:
    _sxe.uuid = _SequentialUUID()


# ── The engine with the three switches ───────────────────────────────────────────────────
STOP_FLOOR_READINGS = ("none", "a5_10pt", "a22_2xatr")
RR_GATE_READINGS = ("kept", "removed")


class RetestEngine(fb.CausalReplayEngine):
    def __init__(self, config, *, stop_floor="none", rr_gate="kept", rth_only=False,
                 cap_lifted=False):
        assert stop_floor in STOP_FLOOR_READINGS and rr_gate in RR_GATE_READINGS
        super().__init__(config)
        self.stop_floor = stop_floor
        self.rr_gate = rr_gate
        self.rth_only = rth_only
        self.cap_lifted = cap_lifted
        self._shadow_count = 0
        self.retest_counters = {
            "c1_floor_applied": 0,            # floor raised the stop
            "c1_floor_then_over_cap": 0,      # ...and the raised stop was then rejected by the 30pt cap
            "c3_rr_gate_rejected": 0,         # gate kept: rejections it produced
            "c3_rr_gate_would_have_rejected": 0,  # gate removed: signals it would have rejected
            "c2_rth_rejected": 0,             # RTH-only rejections (signal bar outside RTH)
            "cap_lifted_admitted_over_30": 0, # sensitivity only: stops > 30pt admitted
            "max_stop_rejected": 0,
        }

    def _record_shadow_signal(self, *a, **k):
        self._shadow_count += 1
        return super()._record_shadow_signal(*a, **k)

    def _stop_floor_value(self, features):
        if self.stop_floor == "a5_10pt":
            return 10.0
        if self.stop_floor == "a22_2xatr":
            return 2.0 * features.atr_14
        return None

    # ---------------------------------------------------------------------------------
    # Copied VERBATIM from CausalReplayEngine._generate_signal (full_backtest.py, commit
    # d1e5ec7) except at the lines marked [RETEST ...]. The untouched configuration must
    # reproduce the original engine exactly — see REPRODUCTION.md.
    # ---------------------------------------------------------------------------------
    async def _generate_signal(self, bar, features, htf_bias, exec_bar) -> None:
        """Run signal pipeline. If signal passes all gates, store as pending."""
        if self.executor.has_active_trade:
            return
        if self._is_warmup():
            return
        if self._check_daily_limits():
            return

        # ── Regime detection ──
        bars_list = self.feature_engine._bars
        avg_vol = (
            np.mean([b.volume for b in bars_list[-20:]])
            if len(bars_list) >= 20
            else bar["volume"]
        )

        self._current_regime = self.regime_detector.classify(
            current_atr=features.atr_14,
            current_vix=features.vix_level or 0,
            trend_direction=features.trend_direction,
            trend_strength=features.trend_strength,
            current_volume=bar["volume"],
            avg_volume=avg_vol,
            is_overnight=not is_rth(bar["timestamp"]),
            near_news_event=False,
        )

        regime_adj = self.regime_detector.get_regime_adjustments(self._current_regime)

        # ── Sweep detector ──
        rth = is_rth(bar["timestamp"])
        sweep_signal = self.sweep_detector.update_bar(
            bar=exec_bar,
            vwap=features.session_vwap,
            htf_bias=htf_bias,
            is_rth=rth,
        )

        # ── Signal aggregation ──
        signal = self.signal_aggregator.aggregate(
            feature_snapshot=features,
            ml_prediction=None,
            htf_bias=htf_bias,
            current_time=bar["timestamp"],
        )

        # ── Determine entry parameters ──
        has_signal = signal and signal.should_trade
        has_sweep = (
            sweep_signal is not None and sweep_signal.score >= SWEEP_MIN_SCORE
        )

        entry_direction = None
        entry_score = 0.0
        entry_source = None
        sweep_stop_override = None

        # PATH C: Sweep-only trigger architecture (mirrors main.py)
        if has_sweep:
            entry_direction = (
                "long" if sweep_signal.direction == "LONG" else "short"
            )
            entry_score = sweep_signal.score
            entry_source = "sweep"
            if sweep_signal.stop_price and sweep_signal.stop_price > 0:
                sweep_stop_override = abs(bar["close"] - sweep_signal.stop_price)
            # Layer 2 context boost from aggregator alignment
            if has_signal:
                signal_dir = (
                    "long" if signal.direction == SignalDirection.LONG
                    else "short"
                )
                if signal_dir == entry_direction:
                    entry_score += CONTEXT_AGGREGATOR_BOOST
            # Layer 2 structural context boosts
            if features:
                if entry_direction == "long":
                    if getattr(features, 'near_bullish_ob', False):
                        entry_score += CONTEXT_OB_BOOST
                    if getattr(features, 'inside_bullish_fvg', False):
                        entry_score += CONTEXT_FVG_BOOST
                elif entry_direction == "short":
                    if getattr(features, 'near_bearish_ob', False):
                        entry_score += CONTEXT_OB_BOOST
                    if getattr(features, 'inside_bearish_fvg', False):
                        entry_score += CONTEXT_FVG_BOOST
        # Aggregator alone cannot trigger (PATH C)

        if entry_direction is None:
            # Capture HTF rejection if aggregator returned a blocked signal
            if (signal is not None and not signal.should_trade
                    and "HTF" in (signal.rejection_reason or "")):
                dir_str = ("LONG" if signal.direction == SignalDirection.LONG
                           else "SHORT")
                self._record_shadow_signal(
                    bar, features, dir_str, signal.combined_score, None,
                    "HTF gate block", 1)
            return

        # Count as a directional signal (regardless of HC outcome)
        self._signals_with_direction += 1

        # ── NaN Guard ──
        if not math.isfinite(entry_score):
            logger.debug("NaN entry_score — blocking")
            self._record_shadow_signal(
                bar, features, entry_direction, entry_score, None,
                "NaN score guard", 2)
            self._rejection_count += 1
            return

        # ── HC Gate 1: Score ──
        if entry_score < HIGH_CONVICTION_MIN_SCORE:
            self._record_shadow_signal(
                bar, features, entry_direction, entry_score, None,
                "HC score below 0.75", 3)
            self._rejection_count += 1
            return

        # ── Risk Assessment ──
        risk_assessment = self.risk_engine.evaluate_trade(
            direction=entry_direction,
            entry_price=bar["close"],
            atr=features.atr_14,
            vix=features.vix_level or 0,
            current_time=bar["timestamp"],
        )

        raw_stop = risk_assessment.suggested_stop_distance
        if sweep_stop_override is not None and sweep_stop_override < raw_stop:
            raw_stop = sweep_stop_override

        # [RETEST C1] stop floor: after min(ATR14x2, structural), before the 30pt cap.
        # A NaN raw_stop compares False and falls through to the original NaN guard.
        _floor = self._stop_floor_value(features)
        _floored = False
        if _floor is not None and raw_stop < _floor:
            raw_stop = _floor
            _floored = True
            self.retest_counters["c1_floor_applied"] += 1

        # ── NaN Guard on stop ──
        if not math.isfinite(raw_stop):
            logger.debug("NaN stop distance — blocking")
            self._record_shadow_signal(
                bar, features, entry_direction, entry_score, None,
                "NaN stop distance", 4)
            self._rejection_count += 1
            return

        # ── HC Gate 2: Stop Distance ──
        # [RETEST sensitivity] --cap-lifted skips this gate; never a candidate reading.
        if raw_stop > HIGH_CONVICTION_MAX_STOP_PTS:
            if not self.cap_lifted:
                self.retest_counters["max_stop_rejected"] += 1
                if _floored:
                    self.retest_counters["c1_floor_then_over_cap"] += 1
                self._record_shadow_signal(
                    bar, features, entry_direction, entry_score, raw_stop,
                    "Max stop exceeded", 5)
                self._rejection_count += 1
                return
            self.retest_counters["cap_lifted_admitted_over_30"] += 1

        # ── Min R:R Check ──
        # [RETEST C3] kept: original behaviour; removed: gate skipped, its would-be rejections counted.
        target_distance = features.atr_14 * self.config.risk.atr_multiplier_target
        if raw_stop > 0 and target_distance / raw_stop < MIN_RR_RATIO:
            if self.rr_gate == "kept":
                self.retest_counters["c3_rr_gate_rejected"] += 1
                self._record_shadow_signal(
                    bar, features, entry_direction, entry_score, raw_stop,
                    "Min R:R failed", 6)
                self._rejection_count += 1
                return
            self.retest_counters["c3_rr_gate_would_have_rejected"] += 1

        # ── Regime gate ──
        if regime_adj["size_multiplier"] == 0:
            self._record_shadow_signal(
                bar, features, entry_direction, entry_score, raw_stop,
                "Regime gate block", 7)
            self._rejection_count += 1
            return

        # ── Risk decision ──
        if risk_assessment.decision not in (
            RiskDecision.APPROVE, RiskDecision.REDUCE_SIZE
        ):
            self._record_shadow_signal(
                bar, features, entry_direction, entry_score, raw_stop,
                "Risk decision rejected", 8)
            self._rejection_count += 1
            return

        # [RETEST C2] RTH-only entry: the SIGNAL bar's timestamp must satisfy the bot's is_rth().
        # Placed last so every existing gate (and any side effect) runs exactly as before.
        if self.rth_only and not rth:
            self.retest_counters["c2_rth_rejected"] += 1
            self._record_shadow_signal(
                bar, features, entry_direction, entry_score, raw_stop,
                "RTH-only (retest C2)", 9)
            self._rejection_count += 1
            return

        # ── All gates passed: store as pending entry ──
        htf_dir = htf_bias.consensus_direction if htf_bias else "n/a"
        htf_str = htf_bias.consensus_strength if htf_bias else 0.0

        self._pending_entry = {
            "direction": entry_direction,
            "score": entry_score,
            "stop_distance": raw_stop,
            "atr": features.atr_14,
            "source": entry_source,
            "regime": self._current_regime,
            "signal_timestamp": bar["timestamp"].isoformat(),
            "htf_direction": htf_dir,
            "htf_strength": round(htf_str, 3),
        }


# ── Data, run loop, output ───────────────────────────────────────────────────────────────
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bot_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(BOT_ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def load_bars(data_paths):
    bars = []
    seen = set()
    for p in data_paths:
        loaded = fb.load_1min_csv(p)
        print(f"  {p}: {len(loaded):,} 1m bars")
        for b in loaded:
            if b["timestamp"] in seen:
                continue
            seen.add(b["timestamp"])
            bars.append(b)
    bars.sort(key=lambda b: b["timestamp"])
    return bars


def et_date(ts: datetime) -> date:
    return ts.astimezone(ET).date()


def summarize(complete, engine) -> dict:
    pnls = [t["adjusted_pnl"] for t in complete]
    n = len(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gp, gl = sum(wins), -sum(losses)
    cum, peak, mdd = 0.0, 0.0, 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        mdd = max(mdd, peak - cum)
    mean = (sum(pnls) / n) if n else 0.0
    sd = (math.sqrt(sum((p - mean) ** 2 for p in pnls) / (n - 1))) if n > 1 else 0.0
    return {
        "trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / n, 2) if n else None,
        "gross_profit": round(gp, 2),
        "gross_loss": round(gl, 2),
        "profit_factor": round(gp / gl, 4) if gl > 0 else None,
        "total_net_pnl": round(sum(pnls), 2),
        "mean_net_per_trade": round(mean, 4),
        "sd_net_per_trade": round(sd, 4),
        "max_drawdown_dollars": round(mdd, 2),
        "rth_entry_share_pct": round(100.0 * sum(1 for t in complete if t.get("is_rth")) / n, 2) if n else None,
        "mean_stop_distance": round(sum(t["stop_distance"] for t in complete) / n, 3) if n else None,
        "signals_with_direction": engine._signals_with_direction,
        "rejections": engine._rejection_count,
        "entries": engine._entry_count,
        "shadow_signals_recorded": engine._shadow_count,
    }


async def run(args) -> dict:
    wall0 = time_module.time()
    if args.slippage_mult != 1.0:
        fb.SLIPPAGE_RTH_PTS = 0.50 * args.slippage_mult
        fb.SLIPPAGE_ETH_PTS = 1.00 * args.slippage_mult
        print(f"  slippage scaled x{args.slippage_mult}: RTH {fb.SLIPPAGE_RTH_PTS} / ETH {fb.SLIPPAGE_ETH_PTS}")

    print("Loading 1-minute data...")
    bars_1m = load_bars(args.data)
    print("Aggregating to 2-minute execution bars (bot's aggregate_to_2m)...")
    bars_2m = fb.aggregate_to_2m(bars_1m)
    del bars_1m
    start = date.fromisoformat(args.start) if args.start else None
    end = date.fromisoformat(args.end) if args.end else None
    if start or end:
        bars_2m = [b for b in bars_2m
                   if (start is None or et_date(b["timestamp"]) >= start)
                   and (end is None or et_date(b["timestamp"]) <= end)]
    base_state = None
    if args.continue_from:
        with open(args.continue_from, "rb") as f:
            base_state = pickle.load(f)
        last_ts = base_state["last_bar_ts"]
        bars_2m = [b for b in bars_2m if b["timestamp"] > last_ts]
        print(f"  continuation: dropping bars <= {last_ts.isoformat()} (saved last bar)")
    if not bars_2m:
        sys.exit("no bars in window")
    print(f"  {len(bars_2m):,} 2m bars: {bars_2m[0]['timestamp']} -> {bars_2m[-1]['timestamp']}")

    print("Loading HTF data...")
    htf_data = fb.load_all_htf(args.htf_dir)

    config_dict = {"stop_floor": args.stop_floor, "rr_gate": args.rr_gate,
                   "rth_only": args.rth_only, "cap_lifted": args.cap_lifted,
                   "slippage_mult": args.slippage_mult,
                   "perf_patch": not args.no_perf_patch,
                   "deterministic_ids": args.deterministic_ids}
    if args.deterministic_ids:
        apply_deterministic_ids()
    config = fb.BotConfig()
    scheduler = fb.HTFScheduler(htf_data)
    start_idx = 0
    rate_log = []
    prior_elapsed = 0.0
    continued_from = None
    ckpt = Path(args.checkpoint) if args.checkpoint else None
    if ckpt and args.resume and ckpt.exists():
        with open(ckpt, "rb") as f:
            st = pickle.load(f)
        if (st["config"] != config_dict or st["first_bar"] != bars_2m[0]["timestamp"].isoformat()
                or st["n_bars"] != len(bars_2m)):
            sys.exit("checkpoint does not match this configuration/window — refusing to resume")
        engine = st["engine"]
        engine._patch_executor()
        scheduler._indices = st["sched_indices"]
        if args.deterministic_ids:
            _sxe.uuid.n = st["ids"]
        start_idx = st["next_bar"]
        rate_log = st["rate_log"]
        prior_elapsed = st["elapsed"]
        print(f"  resumed from {ckpt} at bar {start_idx:,} ({engine._entry_count} entries so far)")
    elif base_state is not None:
        base_cfg = base_state["config"]
        for k in ("stop_floor", "rr_gate", "rth_only"):
            if base_cfg[k] != config_dict[k]:
                sys.exit(f"--continue-from state has {k}={base_cfg[k]!r}; this run asks {config_dict[k]!r}")
        engine = base_state["engine"]
        engine._patch_executor()
        engine.cap_lifted = args.cap_lifted            # may branch here (sensitivity)
        for tf, fed_ts in base_state["sched_last_fed"].items():
            if tf not in scheduler._queues:
                continue
            if fed_ts is None:
                scheduler._indices[tf] = 0
                continue
            q = scheduler._queues[tf]
            pos = next((i for i, b in enumerate(q) if b["timestamp"] == fed_ts), None)
            if pos is None:
                sys.exit(f"HTF {tf}: last fed bar {fed_ts} not found under {args.htf_dir} — "
                         f"HTF files are not a continuation of the saved run")
            scheduler._indices[tf] = pos + 1
        if args.deterministic_ids:
            _sxe.uuid.n = base_state["ids"]
        continued_from = {
            "path": str(args.continue_from), "sha256": sha256_file(Path(args.continue_from)),
            "base_config": base_cfg, "last_bar_ts": base_state["last_bar_ts"].isoformat(),
            "base_trades_sha256": base_state.get("trades_sha256"),
            "base_entry_count": engine._entry_count,
            "records_before_continuation": len(engine.trades),
            "base_lineage": base_state.get("lineage"),
        }
        print(f"  continuing from {args.continue_from}: {engine._entry_count} entries so far, "
              f"last bar {continued_from['last_bar_ts']}")
    else:
        engine = RetestEngine(config, stop_floor=args.stop_floor, rr_gate=args.rr_gate,
                              rth_only=args.rth_only, cap_lifted=args.cap_lifted)
        if not args.no_perf_patch:
            apply_perf_patch(engine)

    def save_checkpoint(next_bar: int, elapsed_so_far: float) -> None:
        paper_enter = engine.executor.__dict__.pop("_paper_enter", None)
        try:
            st = {"config": config_dict, "first_bar": bars_2m[0]["timestamp"].isoformat(),
                  "n_bars": len(bars_2m), "next_bar": next_bar, "engine": engine,
                  "sched_indices": dict(scheduler._indices),
                  "ids": _sxe.uuid.n if args.deterministic_ids else None,
                  "rate_log": rate_log, "elapsed": elapsed_so_far}
            tmp = str(ckpt) + ".tmp"
            with open(tmp, "wb") as f:
                pickle.dump(st, f, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(tmp, ckpt)
        finally:
            if paper_enter is not None:
                engine.executor._paper_enter = paper_enter

    print(f"Replaying: stop_floor={args.stop_floor} rr_gate={args.rr_gate} "
          f"rth_only={args.rth_only} cap_lifted={args.cap_lifted} perf_patch={not args.no_perf_patch}")
    t0 = time_module.time()
    t_int = t0
    total = len(bars_2m)
    for i in range(start_idx, total):
        bar = bars_2m[i]
        await engine.process_bar(bar, scheduler)
        if ckpt and args.checkpoint_every and (i + 1) % args.checkpoint_every == 0 and i + 1 < total:
            save_checkpoint(i + 1, prior_elapsed + (time_module.time() - t0))
            if args.stop_after_bar and i + 1 >= args.stop_after_bar:
                print(f"  --stop-after-bar: checkpoint written at bar {i + 1:,}, exiting for resume test")
                sys.exit(3)
        if (i + 1) % args.progress == 0 or i + 1 == total:
            now = time_module.time()
            rate = args.progress / (now - t_int) if now > t_int else 0.0
            rate_log.append({"bar": i + 1, "ts": bar["timestamp"].isoformat(),
                             "bars_per_sec": round(rate, 1), "entries": engine._entry_count,
                             "cum_pnl": round(engine._cumulative_pnl, 2)})
            print(f"  [{i + 1:>9,}/{total:,}] {bar['timestamp'].strftime('%Y-%m-%d %H:%M')} "
                  f"| {rate:6.1f} bars/s | entries {engine._entry_count} "
                  f"| PnL ${engine._cumulative_pnl:+,.2f}", flush=True)
            t_int = now
    elapsed = prior_elapsed + (time_module.time() - t0)
    if ckpt and ckpt.exists():
        ckpt.unlink()

    trades_sha256 = hashlib.sha256(
        json.dumps(engine.trades, sort_keys=True, default=str).encode()).hexdigest()
    final_ckpt = None
    if args.final_checkpoint:
        fc = Path(args.final_checkpoint)
        fc.parent.mkdir(parents=True, exist_ok=True)
        paper_enter = engine.executor.__dict__.pop("_paper_enter", None)
        try:
            st = {"config": config_dict, "engine": engine,
                  "last_bar_ts": bars_2m[-1]["timestamp"],
                  "sched_last_fed": {tf: (scheduler._queues[tf][idx - 1]["timestamp"] if idx > 0 else None)
                                     for tf, idx in scheduler._indices.items()},
                  "ids": _sxe.uuid.n if args.deterministic_ids else None,
                  "trades_sha256": trades_sha256, "entry_count": engine._entry_count,
                  "retest_version": RETEST_VERSION, "bot_commit": bot_commit(),
                  "lineage": ([continued_from["base_lineage"]] if continued_from and continued_from.get("base_lineage") else []) +
                             [{"window_first_bar": bars_2m[0]["timestamp"].isoformat(),
                               "window_last_bar": bars_2m[-1]["timestamp"].isoformat(),
                               "config": config_dict, "trades_sha256": trades_sha256}]}
            tmp = str(fc) + ".tmp"
            with open(tmp, "wb") as f:
                pickle.dump(st, f, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(tmp, fc)
        finally:
            if paper_enter is not None:
                engine.executor._paper_enter = paper_enter
        final_ckpt = {"path": str(fc), "sha256": sha256_file(fc)}
        print(f"  final state saved: {fc}  sha256={final_ckpt['sha256']}")

    complete = fb.build_complete_trades(engine.trades)
    entries_by_id = {t["trade_id"]: t for t in engine.trades if t["action"] == "entry"}
    for c in complete:  # carry is_rth of the entry bar into the complete record
        c["is_rth"] = entries_by_id[c["trade_id"]]["is_rth"]
    open_at_end = None
    if engine.executor.has_active_trade:
        at = engine.executor._active_trade
        open_at_end = {"trade_id": at.trade_id, "direction": at.direction,
                       "entry_price": at.entry_price,
                       "entry_time": at.entry_time.isoformat() if at.entry_time else None}

    out = {
        "meta": {
            "retest_version": RETEST_VERSION,
            "bot_commit": bot_commit(),
            "bot_full_backtest_sha256": sha256_file(FB_PATH),
            "config": config_dict,
            "data": [str(p) for p in args.data],
            "htf_dir": str(args.htf_dir),
            "window": {"start": args.start, "end": args.end,
                       "first_bar": bars_2m[0]["timestamp"].isoformat(),
                       "last_bar": bars_2m[-1]["timestamp"].isoformat(),
                       "bars_2m": total},
            "elapsed_seconds": round(elapsed, 1),
            "bars_per_second_overall": round(total / elapsed, 1) if elapsed > 0 else None,
            "resumed_from_bar": start_idx or None,
            "trades_sha256": trades_sha256,
            "continued_from": continued_from,
            "final_checkpoint": final_ckpt,
            "rate_log": rate_log,
            "retest_counters": engine.retest_counters,
            "open_at_end_excluded": open_at_end,
            "wall_seconds": round(time_module.time() - wall0, 1),
        },
        "summary": summarize(complete, engine),
        "complete_trades": complete,
        "records": engine.trades,
    }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", nargs="+", required=True, help="combined 1-minute CSV(s), bot format; concatenated, de-duplicated on timestamp")
    ap.add_argument("--htf-dir", required=True, help="directory with htf_{5m,15m,30m,1H,4H,1D}.csv built from the same 1m data")
    ap.add_argument("--out", required=True, help="output JSON path; a .sha256 seal is written beside it")
    ap.add_argument("--start", default=None, help="first ET calendar date to replay (inclusive)")
    ap.add_argument("--end", default=None, help="last ET calendar date to replay (inclusive)")
    ap.add_argument("--stop-floor", choices=STOP_FLOOR_READINGS, default="none")
    ap.add_argument("--rr-gate", choices=RR_GATE_READINGS, default="kept")
    ap.add_argument("--rth-only", action="store_true")
    ap.add_argument("--cap-lifted", action="store_true", help="disclosed sensitivity only")
    ap.add_argument("--slippage-mult", type=float, default=1.0)
    ap.add_argument("--no-perf-patch", action="store_true")
    ap.add_argument("--no-deterministic-ids", dest="deterministic_ids", action="store_false")
    ap.add_argument("--progress", type=int, default=25_000)
    ap.add_argument("--checkpoint", default=None, help="pickle path for exact checkpoints (deleted on completion)")
    ap.add_argument("--checkpoint-every", type=int, default=25_000)
    ap.add_argument("--resume", action="store_true", help="resume from --checkpoint if it exists")
    ap.add_argument("--stop-after-bar", type=int, default=None, help="(test only) exit right after the first checkpoint at/after this bar")
    ap.add_argument("--final-checkpoint", default=None, help="save the engine state after the last bar (for --continue-from)")
    ap.add_argument("--continue-from", default=None, help="engine state saved by --final-checkpoint; only bars after its last bar are processed")
    args = ap.parse_args()

    out = asyncio.run(run(args))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1, default=str)
    digest = sha256_file(out_path)
    with open(str(out_path) + ".sha256", "w") as f:
        f.write(f"{digest}  {out_path.name}\n")
    s = out["summary"]
    print()
    print(f"  trades {s['trades']} | WR {s['win_rate_pct']}% | PF {s['profit_factor']} | "
          f"net ${s['total_net_pnl']:+,.2f} | mean ${s['mean_net_per_trade']:+.2f}/trade | "
          f"maxDD ${s['max_drawdown_dollars']:,.2f}")
    print(f"  counters: {out['meta']['retest_counters']}")
    print(f"  sealed: {out_path}  sha256={digest}")
    print(f"  trades_sha256 (records only, run-time independent): {out['meta']['trades_sha256']}")


if __name__ == "__main__":
    main()
