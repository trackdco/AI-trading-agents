"""Event-driven backtester core (Spec 1, Step 7).

`simulate(df_1m, triggers, cfg)` replays closed 1m bars against a precomputed list of
Step-6 `Trigger`s and produces trades / verdicts / equity per the mechanical rules of
strategy-definition-v1.0.md §5-§10. Trigger *detection* is not run here (it is expensive
and belongs to the runner); the simulator is a pure, causal function of (bars ≤ t).

Timing model (no lookahead, structurally):
  * 1m bars are START-labeled: the bar stamped t covers [t, t+1min) and is CLOSED when
    iterated. A trigger's ts is its candle CLOSE — its working order becomes active for
    1m bars stamped ≥ ts (all strictly after the trigger's data).
  * Management state changes (BE moves) detected on bar b take effect from the NEXT bar
    (intrabar paths are unknowable; conservative).
  * Recorded event ts = the 1m bar's start label.

Fill realism (spec-1 §3):
  * A resting limit fills only when price trades STRICTLY THROUGH it by
    ≥ fills.trade_through_ticks × tick (touch ≠ fill); fill price = the limit.
  * Stops fill at worse-of(stop, bar open) ∓ slippage ticks (adverse). Slippage is
    fills.slippage_ticks_news within ±fills.news_slippage_window_min minutes of any
    non-holiday calendar release, else fills.slippage_ticks_normal.
  * Same-bar stop+target resolves to STOP (conservative). A fill bar is immediately
    evaluated for exits (stop first).
  * EOD flatten (session.eod_flatten): market-out at the flatten bar's OPEN ∓ slippage.

Documented conventions (flagged in progress-tracker for Angus):
  * If one bar satisfies both T_cancel and the entry fill, CANCEL wins (no-chase priority).
  * Unfilled orders cancel at the entry-window end and at EOD.
  * htf_flag == "range" (and "unclassified" pattern) use the COUNTER-TREND confluence
    minimum (§7 names only counter/with-trend; stricter reading chosen).
  * Daily halt blocks NEW orders; an already-open position rides to its exit.
  * Pattern-A default target: NY VWAP mid when it exists at trigger time, else daily
    VWAP mid (§3 over-extension is vs NY VWAP → reversion targets the NY mid post-9:30).
  * BE stop (V1/V2/V3) is a stop at entry EXACT (§8); its fill suffers slippage like any
    stop. V4 partial exits at the first structural menu level via trade-through; R is the
    leg-weighted sum. Commission charged as 2 sides per trade regardless of legs (flag).
  * $ P&L reported at 1 NQ contract (R is the calibration currency; Angus sized variably).
  * §9 conviction sizing: size=1.0 (full) needs conviction (3+ confluence AND (with-trend
    OR pattern A) AND target ≥ 2R), else 0.5; applied to $ only, not R.
  * §9 v1.1 cluster-TYPE ladder (ANGUS): NO TRADE unless BB+VWAP both in the crossed cluster;
    FULL additionally needs POC (BB+VWAP+POC) plus the conviction test above; exactly-2 -> HALF.
    Also HALF on oversized stop (> sizing.oversized_stop_points) or late-window fill (>= 10:30).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time as dtime
from pathlib import Path

import pandas as pd
import yaml
from pydantic import BaseModel

from src.engine.data import _session_date
from src.engine.sessions import load_news_calendar
from src.engine.triggers import Trigger

_STRUCTURAL = ("structural",)


# ---------------------------------------------------------------- config

class BacktestConfig(BaseModel):
    timezone: str
    win_start: dtime
    win_end: dtime
    eod_flatten: dtime
    entry_variant: str            # E1 | E2 | E3 (§5.3)
    t_cancel: float               # §5.5
    front_run: float              # §6.4 F
    rr_floor: float               # §6.5
    news_override: bool           # §6.3
    min_conf_counter: int         # §7
    min_conf_with: int            # §7
    mgmt_variant: str             # V0..V4 (§8)
    v1_be_at_r: float
    v4_partial_pct: float
    max_trades_per_day: int       # §10
    halt_losses: int
    halt_r: float
    oversized_stop: float         # §9 ANGUS 2026-07-17: stop wider than this -> half size
    late_window_after: dtime      # §9 ANGUS 2026-07-17: entries (fills) after this -> half size
    require_bb_vwap: bool         # §9 v1.1: cluster must hold BB+VWAP (no-trade gate); full=BB+VWAP+POC
    vwap_warmup_min: int          # ANGUS 2026-07-17: no entries within N min of the 18:00 anchor
    no_premarket_high_impact: bool  # ANGUS 2026-07-17 (TIGHTENED): on a high-impact pre-open
                                    # release day the ENTIRE pre-market is blocked; entries from 09:30
    tick: float
    through_ticks: int
    slip_normal: int
    slip_news: int
    news_window_min: int
    commission_side: float
    point_value: float

    model_config = {"arbitrary_types_allowed": True}


def _hhmm(s: str) -> dtime:
    h, m = s.split(":")
    return dtime(int(h), int(m))


def load_backtest_config(config_path: Path = Path("config/strategy.yaml")) -> BacktestConfig:
    c = yaml.safe_load(open(config_path))
    win = c["session"]["entry_windows"][c["session"]["entry_window"]]
    return BacktestConfig(
        timezone=c["session"]["timezone"],
        win_start=_hhmm(win["start"]), win_end=_hhmm(win["end"]),
        eod_flatten=_hhmm(c["session"]["eod_flatten"]),
        entry_variant=c["entry"]["variant"], t_cancel=c["entry"]["cancel_if_runs_points"],
        front_run=c["targets"]["front_run_points"], rr_floor=c["targets"]["rr_floor"],
        news_override=c["targets"]["news_day_override"],
        min_conf_counter=c["filters"]["min_confluence_counter_trend"],
        min_conf_with=c["filters"]["min_confluence_with_trend"],
        mgmt_variant=c["management"]["variant"], v1_be_at_r=c["management"]["v1_be_at_r"],
        v4_partial_pct=c["management"]["v4_partial_pct"],
        oversized_stop=c["sizing"]["oversized_stop_points"],
        late_window_after=_hhmm(c["sizing"]["late_window_after"]),
        require_bb_vwap=c["sizing"].get("require_bb_vwap", True),
        vwap_warmup_min=c["filters"]["vwap_warmup_min"],
        no_premarket_high_impact=c["filters"]["no_premarket_entry_on_high_impact"],
        max_trades_per_day=c["vault"]["max_trades_per_day"],
        halt_losses=c["vault"]["daily_halt_losses"], halt_r=c["vault"]["daily_halt_r"],
        tick=c["instrument"]["tick_size"], through_ticks=c["fills"]["trade_through_ticks"],
        slip_normal=c["fills"]["slippage_ticks_normal"], slip_news=c["fills"]["slippage_ticks_news"],
        news_window_min=c["fills"]["news_slippage_window_min"],
        commission_side=c["fills"]["commission_per_contract_side"],
        point_value=c["instrument"]["point_value_nq"],
    )


# ---------------------------------------------------------------- records

class TradeRecord(BaseModel):
    trade_date: str
    trigger_ts: str
    tf: str
    direction: str
    kind: str
    pattern: str
    htf_flag: str
    confluence: int
    entry_variant: str
    limit_price: float
    fill_ts: str
    entry: float
    stop_initial: float
    target_name: str
    target_level: float
    working_target: float
    exit_ts: str
    exit_price: float
    exit_reason: str              # target | stop | be_stop | eod | partial+<reason>
    points: float
    r_multiple: float
    size: float                   # §9 conviction: 1.0 full / 0.5 half ($ scaling only)
    dollars: float                # at 1 NQ contract x size, net of commissions
    slippage_ticks: int
    mgmt_variant: str


class Verdict(BaseModel):
    ts: str
    tf: str
    direction: str
    pattern: str
    status: str                   # taken | skipped_* | vetoed_* | cancelled_*
    reason: str


@dataclass
class _Order:
    trig: Trigger
    limit: float
    stop: float
    target_name: str
    target_level: float
    working_target: float
    placed: pd.Timestamp
    partial_level: float | None = None    # V4: first structural menu level beyond entry (§8)
    v2_band: float | None = None          # V2: first VWAP band level beyond entry (§8)


@dataclass
class _Pos:
    order: _Order
    entry: float
    fill_ts: pd.Timestamp
    stop: float
    risk_pts: float
    be_done: bool = False
    pending_stop: float | None = None
    legs: list = field(default_factory=list)   # closed legs: (fraction, exit_price, reason, ts)
    frac_open: float = 1.0
    partial_done: bool = False
    partial_level: float | None = None
    v2_band: float | None = None


# ---------------------------------------------------------------- helpers

def _round_tick(p: float, tick: float) -> float:
    return round(round(p / tick) * tick, 10)


def _news_times(calendar: pd.DataFrame | None) -> list[pd.Timestamp]:
    if calendar is None or calendar.empty:
        return []
    cal = calendar[calendar["impact"].isin(["high", "medium"])]
    return list(cal["datetime_ET"])


class _Slip:
    def __init__(self, cfg: BacktestConfig, news: list[pd.Timestamp]):
        self.cfg, self.news = cfg, sorted(news)

    def ticks(self, ts: pd.Timestamp) -> int:
        w = pd.Timedelta(minutes=self.cfg.news_window_min)
        for n in self.news:                       # list is small (a few hundred)
            if abs(ts - n) <= w:
                return self.cfg.slip_news
        return self.cfg.slip_normal


def default_target_resolver(df_1m: pd.DataFrame, calendar: pd.DataFrame | None):
    """§6 target tree against the Step-5 snapshot at trigger time. Returns a callable
    (trig, entry, stop) -> (name, level) or None when no valid opposing level exists."""
    from src.engine.snapshot import build_snapshot

    def resolve(trig: Trigger, entry: float, stop: float):
        ts = pd.Timestamp(trig.ts)
        snap = build_snapshot(df_1m, ts, calendar=calendar if calendar is not None else None)
        sign = 1 if trig.direction == "long" else -1
        beyond = [lv for lv in snap.target_menu if sign * (lv.price - entry) > 0]
        if not beyond:
            return None
        beyond.sort(key=lambda lv: sign * (lv.price - entry))     # nearest first

        def nearest(types=None, names=None):
            for lv in beyond:
                if types and lv.type not in types:
                    continue
                if names and not any(lv.name.startswith(n) for n in names):
                    continue
                return lv
            return None

        if trig.pattern == "A":                                    # §6.2 A -> VWAP middle
            pick = nearest(names=("ny_vwap_mid",)) or nearest(names=("daily_vwap_mid",)) \
                or nearest()
        elif trig.pattern == "B2":                                 # §6.2 B2 -> next structural
            pick = nearest(types=_STRUCTURAL) or nearest()
        else:                                                      # B (and unclassified) -> opposing liquidity
            pick = nearest(names=("prior_day_", "asia_session_", "london_session_")) or nearest()

        # §6.3 news-day override: untaken data extreme beyond the default target
        if pick is not None and snap.data_levels:
            for r in snap.data_levels:
                lvl = r["data_high"] if trig.direction == "long" else r["data_low"]
                if sign * (lvl - pick.price) > 0 and r.get("impact") == "high":
                    ev = pd.Timestamp(r["event_time"])
                    seg = df_1m[(df_1m["ts_event"] > ev) & (df_1m["ts_event"] < ts)]
                    taken = (not seg.empty and
                             ((seg["high"].max() >= lvl) if trig.direction == "long"
                              else (seg["low"].min() <= lvl)))
                    if not taken:
                        pick_name, pick_price = f"data_extreme_{r['event'][:16]}", float(lvl)
                        break
            else:
                pick_name, pick_price = pick.name, float(pick.price)
        elif pick is None:
            return None
        else:
            pick_name, pick_price = pick.name, float(pick.price)
        aux = {}
        st = nearest(types=_STRUCTURAL)
        if st is not None:
            aux["partial_level"] = float(st.price)         # V4 milestone (§8)
        vw = nearest(types=("vwap",))
        if vw is not None:
            aux["v2_band"] = float(vw.price)               # V2 milestone (§8)
        return (pick_name, pick_price, aux)

    return resolve


# ---------------------------------------------------------------- simulator

def simulate(df_1m: pd.DataFrame, triggers: list[Trigger], cfg: BacktestConfig,
             target_resolver=None, entry_price_fn=None,
             calendar: pd.DataFrame | None = None):
    """Replay closed 1m bars against triggers. Returns (trades, verdicts, equity_df)."""
    if calendar is None:
        try:
            calendar = load_news_calendar()
        except Exception:
            calendar = pd.DataFrame(columns=["datetime_ET", "event", "impact"])
    resolve = target_resolver or default_target_resolver(df_1m, calendar)
    slip = _Slip(cfg, _news_times(calendar))

    # high-impact releases scheduled before 09:30, keyed by calendar date (Angus news rule)
    preopen_news: dict = {}
    if calendar is not None and not calendar.empty:
        hi = calendar[(calendar["impact"] == "high")
                      & (calendar["datetime_ET"].dt.time < dtime(9, 30))]
        for _, ev in hi.iterrows():
            d0 = ev["datetime_ET"].date()
            cur = preopen_news.get(d0)
            if cur is None or ev["datetime_ET"] < cur:
                preopen_news[d0] = ev["datetime_ET"]

    trig_by_ts: dict[pd.Timestamp, list[Trigger]] = {}
    for t in triggers:
        trig_by_ts.setdefault(pd.Timestamp(t.ts), []).append(t)

    trades: list[TradeRecord] = []
    verdicts: list[Verdict] = []
    order: _Order | None = None
    pos: _Pos | None = None
    day_stats: dict = {}          # session_date -> {"fills": n, "losses": n, "r": x}

    bars = df_1m.sort_values("ts_event").reset_index(drop=True)

    def day(ts) -> dict:
        d = _session_date(pd.Series([ts]), dtime(18, 0)).iloc[0]
        return day_stats.setdefault(d, {"fills": 0, "losses": 0, "r": 0.0})

    def halted(ts) -> bool:
        st = day(ts)
        return st["losses"] >= cfg.halt_losses or st["r"] <= cfg.halt_r

    def veto(t: Trigger, status: str, reason: str):
        verdicts.append(Verdict(ts=t.ts, tf=t.tf, direction=t.direction,
                                pattern=t.pattern, status=status, reason=reason))

    def entry_limit(t: Trigger) -> float | None:
        if entry_price_fn is not None:
            return entry_price_fn(t)
        if cfg.entry_variant == "E2":                       # §5.3 E2: wick midpoint
            return (t.wick_low + t.wick_high) / 2
        if cfg.entry_variant == "E3":                       # §5.3 E3: penetrated level nearest close
            return t.entry_ref
        # E1: BB basis of the trigger TF at trigger time (§5.3)
        from src.engine.indicators import indicators_asof, load_indicators_config
        ind = indicators_asof(df_1m, pd.Timestamp(t.ts), load_indicators_config())
        return ind["tfs"].get(t.tf, {}).get("bb_basis")

    def close_trade(p: _Pos, exit_price: float, reason: str, ts: pd.Timestamp,
                    slip_ticks: int, frac: float | None = None):
        nonlocal pos
        f = p.frac_open if frac is None else frac
        p.legs.append((f, exit_price, reason, ts))
        p.frac_open = round(p.frac_open - f, 10)
        if p.frac_open > 0:
            return                                           # partial leg booked; runner continues
        sign = 1 if p.order.trig.direction == "long" else -1
        pts = sum(fr * sign * (px - p.entry) for fr, px, _, _ in p.legs)
        r = pts / p.risk_pts if p.risk_pts > 0 else 0.0
        conviction = (p.order.trig.confluence_count >= 3
                      and (p.order.trig.htf_flag == "with_trend" or p.order.trig.pattern == "A")
                      and sign * (p.order.working_target - p.entry) / p.risk_pts >= 2.0)
        # §9 v1.1 cluster-TYPE ladder (ANGUS): FULL needs BB+VWAP+POC all present AND conviction;
        # exactly-2 (incl BB+VWAP, already gated at entry) -> HALF. Legacy typeless -> conviction only.
        ctypes = set(p.order.trig.cluster_types)
        if cfg.require_bb_vwap and ctypes:
            full = {"bb", "vwap", "poc"}.issubset(ctypes) and conviction
        else:
            full = conviction
        size = 1.0 if full else 0.5                           # §9 ($ scaling only)
        # ANGUS 2026-07-17 half-size overrides: oversized stop / late-window entry
        if p.risk_pts > cfg.oversized_stop or p.fill_ts.time() >= cfg.late_window_after:
            size = 0.5
        dollars = pts * cfg.point_value * size - 2 * cfg.commission_side
        last = p.legs[-1]
        trades.append(TradeRecord(
            trade_date=str(_session_date(pd.Series([p.fill_ts]), dtime(18, 0)).iloc[0]),
            trigger_ts=p.order.trig.ts, tf=p.order.trig.tf, direction=p.order.trig.direction,
            kind=p.order.trig.kind, pattern=p.order.trig.pattern, htf_flag=p.order.trig.htf_flag,
            confluence=p.order.trig.confluence_count, entry_variant=cfg.entry_variant,
            limit_price=p.order.limit, fill_ts=p.fill_ts.isoformat(), entry=p.entry,
            stop_initial=p.order.stop, target_name=p.order.target_name,
            target_level=p.order.target_level, working_target=p.order.working_target,
            exit_ts=ts.isoformat(), exit_price=last[1],
            exit_reason=(reason if len(p.legs) == 1 else "partial+" + reason),
            points=round(pts, 4), r_multiple=round(r, 4), size=size,
            dollars=round(dollars, 2), slippage_ticks=slip_ticks, mgmt_variant=cfg.mgmt_variant))
        st = day(p.fill_ts)
        st["r"] += r
        if r < 0:
            st["losses"] += 1
        pos = None

    for i in range(len(bars)):
        b = bars.iloc[i]
        ts, o, h, lo = b["ts_event"], b["open"], b["high"], b["low"]
        tod = ts.time()
        sign = None

        # ---- open position management (evaluated on every closed bar) ----
        if pos is not None:
            sign = 1 if pos.order.trig.direction == "long" else -1
            if pos.pending_stop is not None:                 # BE move applies from this bar on
                pos.stop = pos.pending_stop
                pos.pending_stop = None
            if tod >= cfg.eod_flatten:                       # §10 EOD flatten: market at open
                sl = slip.ticks(ts)
                px = o - sign * sl * cfg.tick
                close_trade(pos, px, "eod", ts, sl)
            else:
                through = cfg.through_ticks * cfg.tick
                stop_hit = (lo <= pos.stop) if sign == 1 else (h >= pos.stop)
                if stop_hit:                                 # stop first (conservative)
                    sl = slip.ticks(ts)
                    worse = min(pos.stop, o) if sign == 1 else max(pos.stop, o)
                    px = worse - sign * sl * cfg.tick
                    reason = "be_stop" if pos.be_done and pos.stop == pos.entry else "stop"
                    close_trade(pos, px, reason, ts, sl)
                else:
                    tgt = pos.order.working_target
                    tgt_fill = (h >= tgt + through) if sign == 1 else (lo <= tgt - through)
                    # V4 partial before target (nearer level), same trade-through rule
                    if (pos is not None and cfg.mgmt_variant == "V4" and not pos.partial_done):
                        plvl = pos.partial_level
                        if plvl is not None:
                            p_fill = (h >= plvl + through) if sign == 1 else (lo <= plvl - through)
                            if p_fill:
                                frac = cfg.v4_partial_pct / 100.0
                                close_trade(pos, plvl, "partial_structural", ts, 0, frac=frac)
                                if pos is not None:
                                    pos.partial_done = True
                    if pos is not None and tgt_fill:
                        close_trade(pos, tgt, "target", ts, 0)
                    elif pos is not None and not pos.be_done:
                        # management arm checks -> stop move takes effect NEXT bar
                        v = cfg.mgmt_variant
                        if v == "V1":
                            arm = pos.entry + sign * cfg.v1_be_at_r * pos.risk_pts
                            if (h >= arm) if sign == 1 else (lo <= arm):
                                pos.pending_stop, pos.be_done = pos.entry, True
                        elif v == "V2":
                            band = pos.v2_band
                            if band is not None and ((h >= band) if sign == 1 else (lo <= band)):
                                pos.pending_stop, pos.be_done = pos.entry, True
                        elif v == "V3" and pos.fill_ts.time() < dtime(9, 30) and tod >= dtime(9, 30):
                            pos.pending_stop, pos.be_done = pos.entry, True

        # ---- working order (only when flat) ----
        if pos is None and order is not None:
            t = order.trig
            sign = 1 if t.direction == "long" else -1
            through = cfg.through_ticks * cfg.tick
            if tod >= cfg.eod_flatten or halted(ts):
                veto(t, "cancelled_eod" if tod >= cfg.eod_flatten else "cancelled_halt",
                     "order cancelled before fill")
                order = None
            elif tod >= cfg.win_end:
                veto(t, "cancelled_window_end", f"unfilled at {cfg.win_end}")
                order = None
            else:
                ran = (h >= order.limit + cfg.t_cancel) if sign == 1 else \
                      (lo <= order.limit - cfg.t_cancel)
                fillable = (lo <= order.limit - through) if sign == 1 else \
                           (h >= order.limit + through)
                if ran:                                       # cancel wins over same-bar fill
                    veto(t, "cancelled_tcancel",
                         f"price ran {cfg.t_cancel} pts beyond limit unfilled")
                    order = None
                elif fillable:
                    st = day(ts)
                    if st["fills"] >= cfg.max_trades_per_day:
                        veto(t, "vetoed_vault_max", "max trades/day reached at fill time")
                        order = None
                    else:
                        st["fills"] += 1
                        # gap-through entry: a resting limit cannot fill better than the bar's
                        # first traded price. If the bar OPENED beyond the limit, the fill is the
                        # open (favourable), not the limit — otherwise a same-bar gap past the stop
                        # books a phantom loss (entry at limit, exit at open). risk_pts stays the
                        # INTENDED risk (limit->stop, the R currency); actual P&L uses the real fill.
                        fill_px = min(order.limit, o) if sign == 1 else max(order.limit, o)
                        pos = _Pos(order=order, entry=fill_px, fill_ts=ts,
                                   stop=order.stop,
                                   risk_pts=abs(order.limit - order.stop))
                        pos.partial_level = order.partial_level
                        pos.v2_band = order.v2_band
                        verdicts.append(Verdict(ts=t.ts, tf=t.tf, direction=t.direction,
                                                pattern=t.pattern, status="taken",
                                                reason=f"filled {fill_px}"))
                        order = None
                        # evaluate exits on the fill bar itself (stop first, conservative)
                        p = pos
                        stop_hit = (lo <= p.stop) if sign == 1 else (h >= p.stop)
                        if stop_hit:
                            sl = slip.ticks(ts)
                            worse = min(p.stop, o) if sign == 1 else max(p.stop, o)
                            close_trade(p, worse - sign * sl * cfg.tick, "stop", ts, sl)
                        else:
                            tgt = p.order.working_target
                            if (h >= tgt + through) if sign == 1 else (lo <= tgt - through):
                                close_trade(p, tgt, "target", ts, 0)

        # ---- new triggers closing at this bar's label ----
        for t in trig_by_ts.get(ts, []):
            if pos is not None:
                veto(t, "skipped_position_open", "one position at a time (§5.6)")
                continue
            if order is not None:
                veto(t, "skipped_order_working", "an order is already working")
                continue
            if not (cfg.win_start <= tod < cfg.win_end):
                veto(t, "vetoed_window", f"outside entry window {cfg.win_start}-{cfg.win_end}")
                continue
            if halted(ts):
                veto(t, "vetoed_halt", "daily halt active (§10)")
                continue
            if day(ts)["fills"] >= cfg.max_trades_per_day:
                veto(t, "vetoed_vault_max", "max trades/day reached (§10)")
                continue
            # ANGUS 2026-07-17: daily VWAP warm-up — no entries within N min of the 18:00 anchor
            mins_since_anchor = (tod.hour * 60 + tod.minute) - 18 * 60
            if 0 <= mins_since_anchor < cfg.vwap_warmup_min:
                veto(t, "vetoed_vwap_warmup",
                     f"within {cfg.vwap_warmup_min}min of the 18:00 daily-VWAP anchor")
                continue
            # ANGUS 2026-07-17 (TIGHTENED): on a high-impact pre-open release day the ENTIRE
            # pre-market is blocked -> no entries until 09:30 (doc wins; pre-release entries gone)
            if cfg.no_premarket_high_impact and tod < dtime(9, 30):
                rel = preopen_news.get(ts.date())
                if rel is not None:
                    veto(t, "vetoed_news_preopen",
                         f"high-impact day (release {rel.time()}) -> whole pre-market blocked until 09:30")
                    continue
            need = cfg.min_conf_with if t.htf_flag == "with_trend" else cfg.min_conf_counter
            if t.confluence_count < need:
                veto(t, "vetoed_confluence", f"confluence {t.confluence_count} < {need} "
                     f"({t.htf_flag})")
                continue
            # §9 v1.1 (ANGUS): NO TRADE unless BOTH BB and VWAP are in the crossed cluster.
            # Guarded on non-empty cluster_types so legacy triggers without type data pass through.
            if cfg.require_bb_vwap and t.cluster_types and not {"bb", "vwap"}.issubset(t.cluster_types):
                veto(t, "vetoed_bb_vwap",
                     f"cluster {sorted(t.cluster_types)} lacks BB+VWAP (§9 v1.1 no-trade)")
                continue
            limit = entry_limit(t)
            if limit is None:
                veto(t, "vetoed_no_entry_ref", f"no {cfg.entry_variant} reference available")
                continue
            limit = _round_tick(limit, cfg.tick)
            stop = _round_tick(t.stop_ref, cfg.tick)
            sgn = 1 if t.direction == "long" else -1
            risk = sgn * (limit - stop)
            if risk <= 0:
                veto(t, "vetoed_bad_geometry", "stop not beyond entry")
                continue
            tgt = resolve(t, limit, stop)
            if tgt is None:
                veto(t, "vetoed_no_target", "no opposing level beyond entry (§6)")
                continue
            name, level, aux = (*tgt, {}) if len(tgt) == 2 else tgt
            working = _round_tick(level - sgn * cfg.front_run, cfg.tick)
            reward = sgn * (working - limit)
            if risk > 0 and reward / risk < cfg.rr_floor:
                veto(t, "vetoed_rr_floor",
                     f"RR {reward / risk:.2f} < {cfg.rr_floor} (target {name})")
                continue
            order = _Order(trig=t, limit=limit, stop=stop, target_name=name,
                           target_level=level, working_target=working, placed=ts,
                           partial_level=aux.get("partial_level"),
                           v2_band=aux.get("v2_band"))

    # equity
    closed = sorted(trades, key=lambda tr: tr.exit_ts)
    eq_rows, cr, cd = [], 0.0, 0.0
    for tr in closed:
        cr += tr.r_multiple
        cd += tr.dollars
        eq_rows.append({"exit_ts": tr.exit_ts, "r_multiple": tr.r_multiple,
                        "cum_r": round(cr, 4), "cum_dollars": round(cd, 2)})
    equity = pd.DataFrame(eq_rows, columns=["exit_ts", "r_multiple", "cum_r", "cum_dollars"])
    return trades, verdicts, equity


def write_outputs(trades, verdicts, equity, outdir: Path = Path("output")):
    outdir.mkdir(exist_ok=True)
    pd.DataFrame([t.model_dump() for t in trades]).to_csv(outdir / "trades.csv", index=False)
    pd.DataFrame([v.model_dump() for v in verdicts]).to_csv(outdir / "verdicts.csv", index=False)
    equity.to_csv(outdir / "equity.csv", index=False)
