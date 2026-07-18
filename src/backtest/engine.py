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
  * §7/§9 v1.2 (ANGUS calibration ruling 2026-07-17): entry gate = BB+VWAP both present in
    the crossed cluster (POC = bonus, no 3-count minimum anywhere — counter-trend included).
    Size = FULL (1.0) by default for every entry; HALF (0.5) only on oversized stop
    (> sizing.oversized_stop_points) or late-window fill (>= 10:30). Applied to $ only, not R.
  * §5 v1.2 (ANGUS): structural stop < entry.min_stop_points (start 10) -> vetoed_min_stop,
    never widened.
"""
from __future__ import annotations

import re
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
    mgmt_variant: str             # V0..V6 (§8; V5/V6 = ANGUS pass-7 75/25 partials)
    v1_be_at_r: float
    v4_partial_pct: float
    v5_partial_pct: float = 75.0  # ANGUS pass-7: % booked at first structure (V5/V6)
    rr_floor_partial: float = 1.5  # ANGUS pass-7: "RR floor for the first profit target is 1.5"
    v7_partial_r: float = 1.5     # pass-8 MFE-derived TEST arm: V7 books v5_partial_pct at a
                                  # FIXED +kR milestone (not a structure); trade set = V0's
    v8_partial_pct: float = 50.0  # pass-17 V8 (ANGUS March style): % booked at first structure;
                                  # runner TRAILS the prior completed 5m swing; premarket fills
                                  # go BE at 09:29 ("BE before the open for volatility")
    max_trades_per_day: int       # §10
    halt_losses: int
    halt_r: float
    oversized_stop: float         # §9 ANGUS 2026-07-17: stop wider than this -> half size
    late_window_after: dtime      # §9 ANGUS 2026-07-17: entries (fills) after this -> half size
    require_bb_vwap: bool         # §7 v1.2: cluster must hold BB+VWAP (the entry gate; POC = bonus)
    require_vwap_touch: bool = False  # ANGUS pass-6: trade only if price ACTUALLY reached a VWAP band
    target_model: str = "default"     # ANGUS pass-6 split test: "default" | "vwap_revert" | "walk_menu"
    walkout_under_floor: bool = False  # ANGUS pass-9 RULING: when the default target computes < rr_floor,
                                       # walk the menu outward to the FIRST level clearing it (P5.16=yes)
    named_high_impact: list[str] = []  # ANGUS pass-9 RULING (P5.14): high-impact = NAMED LIST only
                                       # (regex, case-insens). Empty = strict red-folder (all "high").
    min_stop_points: float = 10.0     # §5 v1.2 ANGUS: structural stop narrower than this -> no trade
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
        v5_partial_pct=c["management"].get("v5_partial_pct", 75.0),
        rr_floor_partial=c["targets"].get("rr_floor_partial", 1.5),
        v7_partial_r=c["management"].get("v7_partial_r", 1.5),
        v8_partial_pct=c["management"].get("v8_partial_pct", 50.0),
        oversized_stop=c["sizing"]["oversized_stop_points"],
        late_window_after=_hhmm(c["sizing"]["late_window_after"]),
        require_bb_vwap=c["sizing"].get("require_bb_vwap", True),
        require_vwap_touch=c["filters"].get("require_vwap_touch", False),
        target_model=c["targets"].get("model", "default"),
        walkout_under_floor=c["targets"].get("walkout_under_floor", False),
        named_high_impact=c["filters"].get("named_high_impact", []),
        min_stop_points=c["entry"]["min_stop_points"],
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

def _is_market_entry(cfg, trig) -> bool:
    """pass-17 EC (ANGUS's actual execution): market entry for DISPLACEMENT triggers,
    resting limit for rejection blocks. E4 = market for everything (tournament arm).
    pass-22 EC2 = same contextual split, but rejection blocks rest at the ORDER-BLOCK
    50% (E5) instead of the E3 reclaim."""
    return cfg.entry_variant == "E4" or (
        cfg.entry_variant in ("EC", "EC2") and trig.kind == "displacement")


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


def _is_named_high(event: str, patterns: list[str]) -> bool:
    """ANGUS P5.14 ruling: with a named list configured, only listed events count as
    high-impact (PCE et al. excluded). Empty list = strict red-folder (every impact=='high')."""
    if not patterns:
        return True
    ev = str(event).lower()
    return any(re.search(p.lower(), ev) for p in patterns)


def _walk_out(beyond: list, entry: float, stop: float, sign: int,
              rr_floor: float, front_run: float):
    """ANGUS pass-9 ruling (P5.16=yes): first menu level (nearest-out order) whose WORKING
    price clears rr_floor, or None. Pure so tests can drive it without a snapshot."""
    risk = sign * (entry - stop)
    if risk <= 0:
        return None
    for lv in beyond:
        working = lv.price - sign * front_run
        if sign * (working - entry) / risk >= rr_floor:
            return lv
    return None


def default_target_resolver(df_1m: pd.DataFrame, calendar: pd.DataFrame | None,
                            model: str = "default", rr_floor: float = 2.0,
                            front_run: float = 0.0, walkout: bool = False,
                            named_high: list[str] | None = None):
    """§6 target tree against the Step-5 snapshot at trigger time. Returns a callable
    (trig, entry, stop) -> (name, level, aux) or None when no valid opposing level exists.

    ANGUS pass-6 split test — `model`:
      "default"    §6.2 pattern tree (A->VWAP mid, B2->next structural, B->opposing liquidity).
      "vwap_revert" mean-reversion: target the VWAP band 2 sigma toward-and-across the mean from
                    the entry band (enter ~VWAP-1 -> target VWAP+1; enter ~VWAP-2 -> target mid).
      "walk_menu"  walk the distance-ordered menu outward, pick the FIRST level clearing rr_floor
                    (skip only if none does) — the P5.16 idea.
    """
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

        news_ok = True   # news-day override applies to the "default" model only (others self-target)
        if model == "vwap_revert":
            news_ok = False
            # sigma-indexed VWAP bands (prefer NY post-09:30, else daily); target = entry band +/- 2
            bands = {}
            for prefix in ("ny_vwap", "daily_vwap"):
                d = {}
                for lv in snap.target_menu:
                    if lv.type != "vwap" or not lv.name.startswith(prefix + "_"):
                        continue
                    nm = lv.name[len(prefix) + 1:]
                    if nm == "mid":
                        d[0] = lv
                    elif nm.startswith("upper_"):
                        d[int(nm.split("_")[1])] = lv
                    elif nm.startswith("lower_"):
                        d[-int(nm.split("_")[1])] = lv
                if d:
                    bands = d
                    break
            pick = None
            if bands:
                entry_idx = min(bands, key=lambda k: abs(bands[k].price - entry))
                tgt_idx = entry_idx + sign * 2
                if tgt_idx in bands and sign * (bands[tgt_idx].price - entry) > 0:
                    pick = bands[tgt_idx]
                else:                                    # best available VWAP band beyond entry
                    avail = [k for k in bands if sign * (bands[k].price - entry) > 0]
                    if avail:
                        pick = bands[max(avail, key=lambda k: sign * (bands[k].price - entry))]
            pick = pick or nearest(types=("vwap",)) or nearest()
        elif model == "walk_menu":
            news_ok = False
            risk = sign * (entry - stop)
            pick = None
            for lv in beyond:                            # nearest first; first to clear the floor
                working = lv.price - sign * front_run
                reward = sign * (working - entry)
                if risk > 0 and reward / risk >= rr_floor:
                    pick = lv
                    break
            if pick is None:
                return None
        elif trig.pattern == "A":                                  # §6.2 A -> VWAP middle
            pick = nearest(names=("ny_vwap_mid",)) or nearest(names=("daily_vwap_mid",)) \
                or nearest()
        elif trig.pattern == "B2":                                 # §6.2 B2 -> next structural
            pick = nearest(types=_STRUCTURAL) or nearest()
        else:                                                      # B (and unclassified) -> opposing liquidity
            pick = nearest(names=("prior_day_", "asia_session_", "london_session_")) or nearest()

        # §6.3 news-day override: untaken data extreme beyond the default target (default model
        # only). P5.14: with a named list configured, only listed events qualify as high-impact.
        if news_ok and pick is not None and snap.data_levels:
            for r in snap.data_levels:
                lvl = r["data_high"] if trig.direction == "long" else r["data_low"]
                if (sign * (lvl - pick.price) > 0 and r.get("impact") == "high"
                        and _is_named_high(r.get("event", ""), named_high or [])):
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
        # ANGUS pass-9 (P5.16=yes): default target under the floor -> walk outward to the
        # first menu level that clears it, instead of letting order-build veto the trade.
        if walkout and model == "default":
            risk = sign * (entry - stop)
            working = pick_price - sign * front_run
            if risk > 0 and sign * (working - entry) / risk < rr_floor:
                alt = _walk_out(beyond, entry, stop, sign, rr_floor, front_run)
                if alt is not None:
                    pick_name, pick_price = f"walkout_{alt.name}", float(alt.price)
        aux = {}
        sts = [lv for lv in beyond if lv.type in _STRUCTURAL]   # distance-ordered structurals
        if sts:
            aux["partial_level"] = float(sts[0].price)     # V4/V5/V6 first structure (§8)
        if len(sts) > 1:                                   # V5 runner -> NEXT structural (ANGUS)
            aux["structural_2"] = (sts[1].name, float(sts[1].price))
        if len(sts) > 2:                                   # V6 runner -> the one BEYOND (ANGUS)
            aux["structural_3"] = (sts[2].name, float(sts[2].price))
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
    resolve = target_resolver or default_target_resolver(
        df_1m, calendar, cfg.target_model, cfg.rr_floor, cfg.front_run,
        walkout=cfg.walkout_under_floor, named_high=cfg.named_high_impact)
    slip = _Slip(cfg, _news_times(calendar))

    v8_fm = None
    if cfg.mgmt_variant == "V8":                      # prior-5m swing lookup for the V8 trail
        from src.engine.sessions import resample_ohlcv
        _fm = resample_ohlcv(df_1m, "5min")           # close-labeled: bar T completed at T
        v8_fm = (_fm["ts_event"], _fm["high"].to_numpy(), _fm["low"].to_numpy())

    # high-impact releases scheduled before 09:30, keyed by calendar date (Angus news rule).
    # P5.14 (ANGUS): with a named list configured, only listed events trigger the stand-down.
    preopen_news: dict = {}
    if calendar is not None and not calendar.empty:
        hi = calendar[(calendar["impact"] == "high")
                      & (calendar["datetime_ET"].dt.time < dtime(9, 30))]
        if cfg.named_high_impact:
            hi = hi[hi["event"].map(lambda e: _is_named_high(e, cfg.named_high_impact))]
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

    def in_window(tod) -> bool:
        # entry window; supports OVERNIGHT spans (start > end wraps midnight, e.g. 18:00->10:15)
        if cfg.win_start <= cfg.win_end:
            return cfg.win_start <= tod < cfg.win_end
        return tod >= cfg.win_start or tod < cfg.win_end

    def past_eod(tod) -> bool:
        # flatten belt fires ONLY between eod_flatten and the 18:00 session close — an
        # overnight position (e.g. filled 20:00) must not trip yesterday's flatten time
        return cfg.eod_flatten <= tod < dtime(18, 0)

    def halted(ts) -> bool:
        # §10 v1.2 (ANGUS calibration ruling #2, 17 Jul): halt on DAMAGE (-2R day total),
        # not attempt count — two -0.1R scratches must not lock out the day's real setups.
        # halt_losses = 0 disables the loss counter entirely (Angus option (a)).
        st = day(ts)
        return (cfg.halt_losses > 0 and st["losses"] >= cfg.halt_losses) or st["r"] <= cfg.halt_r

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
        if _is_market_entry(cfg, t):
            return t.close                                  # MARKET on the next bar (E4/EC-disp/
                                                            # EC2-disp): build-time reference for
                                                            # the gates; fill = next bar open +/- slip
        if cfg.entry_variant in ("E5", "EC2"):              # ANGUS pass-22 ORDER BLOCK: limit at
                                                            # the two-candle block's 50%; fall back
                                                            # to the E3 reclaim when no OB partner
            return t.ob_mid if t.ob_mid is not None else t.entry_ref
        if cfg.entry_variant == "EC":                       # EC rejection block -> E3 limit
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
        # §9 v1.2 (ANGUS calibration ruling 2026-07-17): FULL size is the default for every
        # entry — counter-trend reversals included ("I wasn't doing 50%"). The v1.1
        # confluence/type-count sizing tiers and the with-trend-or-A conviction test are
        # DELETED. HALF only on the two deliberate overrides: oversized stop / late-window fill.
        size = 1.0
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
            if past_eod(tod):                                # §10 EOD flatten: market at open
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
                    # V4/V5/V6/V7 partial before target (nearer milestone), same trade-through
                    # rule. V4/V5/V6 book at the first STRUCTURE; V7 (pass-8 MFE test arm)
                    # books at a FIXED +kR milestone computed from the fill.
                    if (pos is not None and cfg.mgmt_variant in ("V4", "V5", "V6", "V7", "V8")
                            and not pos.partial_done):
                        if cfg.mgmt_variant == "V7":
                            plvl = pos.entry + sign * cfg.v7_partial_r * pos.risk_pts
                        else:
                            plvl = pos.partial_level
                        if plvl is not None:
                            p_fill = (h >= plvl + through) if sign == 1 else (lo <= plvl - through)
                            if p_fill:
                                pct = (cfg.v4_partial_pct if cfg.mgmt_variant == "V4"
                                       else cfg.v8_partial_pct if cfg.mgmt_variant == "V8"
                                       else cfg.v5_partial_pct)
                                reason = "partial_r_milestone" if cfg.mgmt_variant == "V7" \
                                    else "partial_structural"
                                close_trade(pos, plvl, reason, ts, 0, frac=pct / 100.0)
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
                    # pass-17 V8 (ANGUS March style): premarket fills -> BE at 09:29; once the
                    # partial is booked, TRAIL the runner behind the prior completed 5m swing.
                    if cfg.mgmt_variant == "V8" and pos is not None:
                        if (not pos.be_done and pos.fill_ts.time() < dtime(9, 29)
                                and tod >= dtime(9, 29)):
                            pos.pending_stop, pos.be_done = pos.entry, True
                        if pos.partial_done and v8_fm is not None:
                            j = v8_fm[0].searchsorted(ts, side="right") - 1
                            if j >= 0:
                                cand = float(v8_fm[2][j]) if sign == 1 else float(v8_fm[1][j])
                                cur = pos.pending_stop if pos.pending_stop is not None else pos.stop
                                if (sign == 1 and cand > cur) or (sign == -1 and cand < cur):
                                    pos.pending_stop = cand

        # ---- working order (only when flat) ----
        if pos is None and order is not None:
            t = order.trig
            sign = 1 if t.direction == "long" else -1
            through = cfg.through_ticks * cfg.tick
            if past_eod(tod) or halted(ts):
                veto(t, "cancelled_eod" if past_eod(tod) else "cancelled_halt",
                     "order cancelled before fill")
                order = None
            elif not in_window(tod):
                veto(t, "cancelled_window_end", f"unfilled at {cfg.win_end}")
                order = None
            else:
                if _is_market_entry(cfg, t):
                    # E4/EC-displacement: MARKET entry — fills unconditionally on this (next)
                    # bar at the open with adverse slippage; no resting limit, no T_cancel.
                    ran, fillable = False, True
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
                        if _is_market_entry(cfg, t):
                            # market order crosses the spread: open + adverse slippage; the R
                            # currency is the ACTUAL fill->stop distance (no resting price exists)
                            sl_in = slip.ticks(ts)
                            fill_px = _round_tick(o + sign * sl_in * cfg.tick, cfg.tick)
                        else:
                            fill_px = min(order.limit, o) if sign == 1 else max(order.limit, o)
                        if _is_market_entry(cfg, t) and sign * (fill_px - order.stop) <= 0:
                            # opened at/beyond the stop: a market entry here is instant dead risk
                            st["fills"] -= 1
                            veto(t, "cancelled_gap_through_stop",
                                 f"market fill {fill_px} at/beyond stop {order.stop}")
                            order = None
                            fill_px = None
                        if fill_px is not None:
                            pos = _Pos(order=order, entry=fill_px, fill_ts=ts,
                                       stop=order.stop,
                                       risk_pts=(abs(fill_px - order.stop)
                                                 if _is_market_entry(cfg, t)
                                                 else abs(order.limit - order.stop)))
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
            if not in_window(tod):
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
            # ANGUS pass-6: require price to ACTUALLY have reached a VWAP band ("it rejected VWAP"),
            # not just a VWAP level sitting near a BB level (Brake's Feb-24 find). Supersedes the
            # composition check above when enabled — set require_bb_vwap:false in the touch arm.
            if cfg.require_vwap_touch and not t.vwap_touched:
                veto(t, "vetoed_vwap_touch",
                     "price did not reach a VWAP band (ANGUS pass-6 quality filter)")
                continue
            limit = entry_limit(t)
            if limit is None:
                veto(t, "vetoed_no_entry_ref", f"no {cfg.entry_variant} reference available")
                continue
            limit = _round_tick(limit, cfg.tick)
            # E5/EC2 resting OB entries: stop beyond the two-candle BLOCK (Angus pass-22 —
            # "mark the range of those two", stop past it), not just the trigger wick. The
            # E3 fallback (no OB partner) keeps the wick stop.
            if (cfg.entry_variant in ("E5", "EC2") and not _is_market_entry(cfg, t)
                    and t.ob_mid is not None and t.ob_stop is not None):
                stop = _round_tick(t.ob_stop, cfg.tick)
            else:
                stop = _round_tick(t.stop_ref, cfg.tick)
            sgn = 1 if t.direction == "long" else -1
            risk = sgn * (limit - stop)
            if risk <= 0:
                veto(t, "vetoed_bad_geometry", "stop not beyond entry")
                continue
            # §5 v1.2 (ANGUS calibration ruling 2026-07-17): structural stop must be at least
            # min_stop_points wide — tighter is a SKIP, never widened. Kills the 1-4 pt
            # coin-toss stops behind most of the Feb EXTRA losses ("give NQ breathing room").
            if risk < cfg.min_stop_points:
                veto(t, "vetoed_min_stop",
                     f"stop {risk:.2f} pts < {cfg.min_stop_points:g} minimum (§5 v1.2)")
                continue
            tgt = resolve(t, limit, stop)
            if tgt is None:
                veto(t, "vetoed_no_target", "no opposing level beyond entry (§6)")
                continue
            name, level, aux = (*tgt, {}) if len(tgt) == 2 else tgt
            plvl = aux.get("partial_level")
            if cfg.mgmt_variant in ("V5", "V6") and plvl is not None:
                # ANGUS pass-7 partials: 75% books at the FIRST structure (plvl); the 25%
                # runner targets the NEXT structural (V5) or the one beyond it (V6). Floor:
                # the FIRST profit target must offer >= rr_floor_partial ("RR floor for the
                # first profit target is 1.5"); the runner leg rides free. Missing s2/s3
                # falls back to the model-picked target as the runner.
                runner = aux.get("structural_2") if cfg.mgmt_variant == "V5" else \
                    (aux.get("structural_3") or aux.get("structural_2"))
                if runner is not None:
                    name, level = runner
                first_rr = sgn * (plvl - limit) / risk
                if first_rr < cfg.rr_floor_partial:
                    veto(t, "vetoed_rr_floor",
                         f"first-structure RR {first_rr:.2f} < {cfg.rr_floor_partial} (partial floor)")
                    continue
                working = _round_tick(level - sgn * cfg.front_run, cfg.tick)
            else:
                working = _round_tick(level - sgn * cfg.front_run, cfg.tick)
                reward = sgn * (working - limit)
                if risk > 0 and reward / risk < cfg.rr_floor:
                    veto(t, "vetoed_rr_floor",
                         f"RR {reward / risk:.2f} < {cfg.rr_floor} (target {name})")
                    continue
            order = _Order(trig=t, limit=limit, stop=stop, target_name=name,
                           target_level=level, working_target=working, placed=ts,
                           partial_level=plvl,
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
