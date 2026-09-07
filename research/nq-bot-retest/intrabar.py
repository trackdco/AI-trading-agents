"""
intrabar.py — a realistic stop model for the bot's executor (driver flag --intrabar-stops).

The bot evaluates every exit on the 2-minute bar CLOSE and fills the initial hard stop AT that
close, however far through the level it is (RESULT.md §B.10.3). Live, a stop is a resting order:
it triggers when price touches the level and fills at the level, or at the next print if price
gaps through. This mixin does exactly that for the three resting orders — the initial hard stop
(both contracts), the C1 trailing stop once it is active, and the C2 breakeven/trailing stop —
using the 1-minute bars inside each 2-minute bar: trigger on the minute's low/high, fill at the
level, or at the minute's open when the open is already beyond it. Everything else — trail
activation and high-water marks from 2-minute closes, the 12-bar fallback, the 150pt target, the
120-minute time stop, bar counting — is untouched and still runs on the 2-minute close through the
bot's own `update()`.

Counters in meta.intrabar_counters say how often each intrabar path fired.
"""
import math

from execution.scale_out_executor import ScaleOutPhase


class IntrabarMixin:
    sub_bars = {}   # class attribute, set by the driver: 2m bucket ts -> [(ts, o, h, l, c), ...]; never pickled

    def _ensure_intrabar(self):
        if not hasattr(self, "intrabar_counters"):
            self.intrabar_counters = {"hard_stop_intrabar": 0, "hard_stop_gap_fill": 0,
                                      "c1_trail_intrabar": 0, "c2_stop_intrabar": 0,
                                      "closed_on_2m_close": 0}

    async def _manage_active_position(self, bar):
        self._ensure_intrabar()
        ex = self.executor
        if not ex.has_active_trade:
            return None
        subs = self.sub_bars.get(bar["timestamp"]) or [
            (bar["timestamp"], bar["open"], bar["high"], bar["low"], bar["close"])]
        for ts, o, h, l, c in subs:
            trade = ex._active_trade
            if trade is None:
                break
            long = trade.direction == "long"

            def touched(level):
                return (l <= level) if long else (h >= level)

            def fill_at(level):
                gapped = (o <= level) if long else (o >= level)
                return (o if gapped else level), gapped

            if trade.phase == ScaleOutPhase.PHASE_1:
                s = trade.initial_stop
                if touched(s):
                    fill, gapped = fill_at(s)
                    self.intrabar_counters["hard_stop_intrabar"] += 1
                    self.intrabar_counters["hard_stop_gap_fill"] += int(gapped)
                    result = await ex._close_all(trade, fill, ts, "stop")
                    return self._finalize_exit(result, bar)
                if trade.c1_trailing_active:
                    d = ex.scale_config.c1_trail_distance_pts
                    trail = trade.c1_best_price - d if long else trade.c1_best_price + d
                    if touched(trail):
                        fill, _ = fill_at(trail)
                        self.intrabar_counters["c1_trail_intrabar"] += 1
                        await ex._close_c1_to_runner(trade, round(fill, 2), ts, "c1_trail_from_profit")
            trade = ex._active_trade
            if trade is not None and trade.phase in (ScaleOutPhase.C1_HIT, ScaleOutPhase.RUNNING):
                s2 = trade.c2.stop_price
                if touched(s2):
                    fill, _ = fill_at(s2)
                    reason = "trailing" if trade.c2_trailing_stop > 0 else "breakeven"
                    self.intrabar_counters["c2_stop_intrabar"] += 1
                    result = await ex._close_c2(trade, fill, ts, reason)
                    return self._finalize_exit(result, bar)
        if not ex.has_active_trade:
            return None
        result = await ex.update(bar["close"], bar["timestamp"])
        if result and result.get("action") == "trade_closed":
            self.intrabar_counters["closed_on_2m_close"] += 1
            return self._finalize_exit(result, bar)
        return result

    def _finalize_exit(self, result, bar):
        """The bot's own post-close bookkeeping (CausalReplayEngine._manage_active_position), verbatim."""
        import full_backtest as fb
        closed_trade = self.executor._trade_history[-1]
        c1_exit_slip = (fb.get_slippage(closed_trade.c1.exit_time)
                        if closed_trade.c1.exit_time else fb.SLIPPAGE_RTH_PTS)
        c2_exit_slip = (fb.get_slippage(closed_trade.c2.exit_time)
                        if closed_trade.c2.exit_time else fb.SLIPPAGE_RTH_PTS)
        exit_slippage_cost = (c1_exit_slip + c2_exit_slip) * fb.POINT_VALUE
        raw_pnl = result.get("total_pnl", 0.0)
        adjusted_pnl = raw_pnl - exit_slippage_cost
        if not math.isfinite(adjusted_pnl):
            adjusted_pnl = 0.0
        self._daily_pnl += adjusted_pnl
        self._cumulative_pnl += adjusted_pnl
        self.risk_engine.record_trade_result(adjusted_pnl, result["direction"])
        exit_record = {
            "action": "exit",
            "trade_id": result.get("trade_id", ""),
            "bar_index": self._bars_processed,
            "timestamp": bar["timestamp"].isoformat(),
            "direction": result["direction"],
            "entry_price": result.get("entry_price", 0),
            "c1_exit_price": result.get("c1_exit_price", 0),
            "c2_exit_price": result.get("c2_exit_price", 0),
            "raw_pnl": raw_pnl,
            "exit_slippage_cost": exit_slippage_cost,
            "c1_exit_slippage": c1_exit_slip,
            "c2_exit_slippage": c2_exit_slip,
            "adjusted_pnl": adjusted_pnl,
            "daily_pnl": self._daily_pnl,
            "cumulative_pnl": self._cumulative_pnl,
            "c1_pnl": result.get("c1_pnl", 0),
            "c2_pnl": result.get("c2_pnl", 0),
            "c1_exit_reason": result.get("c1_exit_reason", ""),
            "c2_exit_reason": result.get("c2_exit_reason", ""),
            "commission_total": closed_trade.total_commission,
            "c1_exit_time": closed_trade.c1.exit_time.isoformat() if closed_trade.c1.exit_time else None,
            "c2_exit_time": closed_trade.c2.exit_time.isoformat() if closed_trade.c2.exit_time else None,
        }
        self.trades.append(exit_record)
        return exit_record
