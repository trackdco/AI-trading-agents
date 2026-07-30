#!/usr/bin/env python3
"""Causal capture replay on the REBUILT canon — the harness the chained-agents test runs in.

HANDOFF-agents-capture rule 1: build the causal harness FIRST, then let agents play inside
it. This is `run_intrade_replay.py`'s settlement engine re-pointed from the dead 383-trade
book to the aikido canon (`funded_book.load_book`), with the same non-negotiables:

  * an exit decision at minute t sees only bars <= t (the decide callback gets the current
    bar and state; nothing later exists yet)
  * stop checks run BEFORE the decision each minute — no arm rescues a dead position
  * stops are inviolate: a plan's stop only ever TIGHTENS (rule 6)
  * P&L is ANCHORED ON THE BOOK'S OWN DOLLARS: the canon's realised `dollars_1lot` is ground
    truth up to the canon exit; only the DEVIATION is simulated. No second implementation of
    V8 (the champion-vs-canon lesson). The V8 half-off leg's price is recovered by inverting
    the book's own arithmetic (`implied_partial`), never re-resolved.

`check` must pass before any arm is graded: every trade's exit stamp must lie on its path,
single-leg trades must reconcile dollars to the cent, partial trades must recover a partial
price that actually traded before the exit.

    python -m scripts.capture_replay check --span fit
    python -m scripts.capture_replay grade --span fit     # mechanical control arms only
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars  # noqa: E402
from scripts import funded_book as fb  # noqa: E402

NY = "America/New_York"
COMMISSION = 5.0            # 2 x commission_side, engine config
STOP_SLIP = 5.0             # 1 tick slip_normal on stop exits, engine config
PARTIAL_PCT = 0.50          # shipped v8_partial_pct
EOD_HM = "15:55"


def sgn(direction: str) -> float:
    return 1.0 if direction == "long" else -1.0


def load_trades(span: str) -> list[dict]:
    V = fb.load_book(span)
    # load_book parses stamps as UTC; the path walk anchors EOD at 15:55 NEW YORK, so
    # convert here or day_path truncates every path at 10:55 ET (caught by check mode).
    rows = []
    for i, r in enumerate(V.itertuples()):
        fill_ny = r.fill.tz_convert(NY)
        rows.append({
            "trade_id": f"{r.day}_{fill_ny.strftime('%H%M')}_{r.direction[0]}_{i}",
            "day": r.day, "ts": r.ts, "sess": r.sess, "direction": r.direction,
            "fill": fill_ny, "exit": r.exit.tz_convert(NY), "entry": float(r.entry),
            "stop": float(r.stop), "risk": float(r.risk),
            "exit_price": float(r.exit_price), "exit_reason": str(r.exit_reason),
            "dollars": float(r.dollars_1lot), "size": float(r.size_engine),
            "tier": float(r.tier), "elite": bool(r.elite), "era": str(r.era)})
    return rows


def load_bars_ny() -> pd.DataFrame:
    b = load_bars()
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    return b.set_index("mi").sort_index()


def day_path(trade: dict, bars: pd.DataFrame) -> pd.DataFrame:
    end = trade["fill"].normalize() + pd.Timedelta(
        hours=int(EOD_HM[:2]), minutes=int(EOD_HM[3:]))
    return bars.loc[trade["fill"]:end]


def canon_exit_of(trade: dict, path: pd.DataFrame):
    """(exit_minute, exit_price) from the book's own stamp, snapped onto the path index."""
    ix = path.index
    if not len(ix):
        return trade["fill"], trade["exit_price"]
    j = int(np.searchsorted(ix, trade["exit"], side="left"))
    m = ix[min(j, len(ix) - 1)]
    return m, float(trade["exit_price"])


def implied_partial(trade: dict) -> float | None:
    """The V8 half-off price, inverted from the book's realised dollars (never re-resolved).

    dollars = 20*size*[0.5*s*(pp-e) + 0.5*s*(xp-e)] - COMMISSION  ->  solve pp.
    Slippage on the final leg is already inside exit_price; the partial leg books at its
    level exactly (engine convention, slip=0 on partials)."""
    if not trade["exit_reason"].startswith("partial"):
        return None
    s, e, xp = sgn(trade["direction"]), trade["entry"], trade["exit_price"]
    pts = (trade["dollars"] + COMMISSION) / (20.0 * trade["size"])
    lead = (pts - (1 - PARTIAL_PCT) * s * (xp - e)) / PARTIAL_PCT
    return e + s * lead


def _apply_plan(state, act, s, stop, px):
    """Fold a ("plan", target_px, stop_px, partial_pct) decision in at price px. Stops only
    tighten; a partial books that fraction of what is STILL OPEN (compounding)."""
    if not (isinstance(act, tuple) and act):
        return
    if act[0] == "stop":
        tgt, new_stop, pct = None, act[1], None
    elif act[0] == "plan":
        _, tgt, new_stop, pct = act
    else:
        return
    if new_stop is not None:
        state["stop"] = max(stop, new_stop) if s > 0 else min(stop, new_stop)
    if tgt is not None:
        state["target"] = tgt
    if pct:
        closed = state["runner"] * float(pct)
        state["agent_booked"] += closed * s * (px - state["anchor_px"]) * 20.0
        state["runner"] -= closed
        state["partials"].append(round(float(pct), 3))


def simulate(trade: dict, path: pd.DataFrame, decide, canon_exit) -> dict:
    """Walk the path minute by minute. decide(minute, state, bar) -> None | "take_canon" |
    "exit_now" | ("stop", px) | ("plan", tgt, stop, pct)."""
    s, entry = sgn(trade["direction"]), trade["entry"]
    cx_min, cx_px = canon_exit
    pp = implied_partial(trade)
    state = {"stop": trade["stop"], "extended": False, "peak": entry,
             "canon_exit_here": False, "reason": "start",
             "booked": 0.0, "part_px": None, "canon_exit": canon_exit,
             "has_partial": pp is not None, "target": None,
             "runner": 1.0 - (PARTIAL_PCT if pp is not None else 0.0),
             "anchor_px": entry, "agent_booked": 0.0, "partials": []}
    for minute, bar in path.iterrows():
        hi, lo = float(bar.high), float(bar.low)
        stop = state["stop"]
        state["canon_exit_here"] = minute == cx_min
        if state["canon_exit_here"]:
            act = decide(minute, state, bar)
            if act == "take_canon":
                return _out(trade, state, minute, cx_px, "canon")
            if act == "exit_now":
                return _out(trade, state, minute, float(bar.close), "agent_exit")
            state["anchor_px"] = cx_px
            _apply_plan(state, act, s, stop, cx_px)
            state["extended"] = True
            state["peak"] = max(state["peak"], hi) if s > 0 else min(state["peak"], lo)
            continue
        if (s > 0 and lo <= stop) or (s < 0 and hi >= stop):
            return _out(trade, state, minute, stop, "stop")
        if pp is not None and state["part_px"] is None and lo - 1e-9 <= pp <= hi + 1e-9:
            state["part_px"] = pp
            state["booked"] = PARTIAL_PCT * s * (pp - entry) * 20.0
        state["peak"] = max(state["peak"], hi) if s > 0 else min(state["peak"], lo)
        act = decide(minute, state, bar)
        if act == "exit_now":
            return _out(trade, state, minute, float(bar.close), "agent_exit")
        _apply_plan(state, act, s, stop, float(bar.close))
        tgt = state.get("target")
        if tgt is not None and ((s > 0 and hi >= tgt) or (s < 0 and lo <= tgt)):
            return _out(trade, state, minute, tgt, "agent_target")
    last = path.index[-1] if len(path) else trade["fill"]
    px = float(path.close.iloc[-1]) if len(path) else entry
    return _out(trade, state, last, px, "eod")


def _out(trade: dict, state: dict, minute, px: float, reason: str) -> dict:
    """Canon-anchored settlement (see run_intrade_replay._out for the full argument).
    At/after the canon exit: book dollars + the runner carried from the canon exit price.
    Before it: simulated from the fill, flagged early_deviation."""
    s_, entry, risk = sgn(trade["direction"]), trade["entry"], trade["risk"]
    size = trade["size"]
    cx_min, cx_px = state["canon_exit"]
    book = trade["dollars"]
    early = minute < cx_min

    open_frac = state["runner"]
    agent_booked = state["agent_booked"]
    if early:
        gross = (state["booked"] + agent_booked
                 + open_frac * s_ * (px - entry) * 20.0) * size
        net = gross - COMMISSION - (STOP_SLIP if reason == "stop" else 0.0)
    else:
        carry = (agent_booked + open_frac * s_ * (px - cx_px) * 20.0) * size
        net = book + carry - (STOP_SLIP if (reason == "stop" and minute > cx_min) else 0.0)

    return {"exit_minute": minute, "exit_price": px, "exit_reason": reason,
            "R": net / (risk * 20.0), "dollars": net,
            "canon_dollars": book, "delta_vs_canon": net - book,
            "partials_taken": list(state["partials"]),
            "early_deviation": bool(early), "partial_booked": state["has_partial"],
            "extended": bool(state["extended"]),
            "held_minutes": int((minute - trade["fill"]).total_seconds() // 60)}


# ------------------------------------------------------------------ mechanical arms

def arm_canon(trade, canon_exit):
    return lambda m, st, bar: "take_canon" if st["canon_exit_here"] else None


def arm_be1r(trade, canon_exit):
    s, entry, risk = sgn(trade["direction"]), trade["entry"], trade["risk"]

    def decide(m, st, bar):
        if s * (st["peak"] - entry) >= risk:
            return ("stop", entry)
        return "take_canon" if st["canon_exit_here"] else None
    return decide


def arm_lock1r_2r(trade, canon_exit):
    s, entry, risk = sgn(trade["direction"]), trade["entry"], trade["risk"]

    def decide(m, st, bar):
        if s * (st["peak"] - entry) >= 2 * risk:
            return ("stop", entry + s * risk)
        return "take_canon" if st["canon_exit_here"] else None
    return decide


def arm_trail1r(trade, canon_exit):
    s, entry, risk = sgn(trade["direction"]), trade["entry"], trade["risk"]

    def decide(m, st, bar):
        if s * (st["peak"] - entry) >= risk:
            return ("stop", st["peak"] - s * risk)
        return "take_canon" if st["canon_exit_here"] else None
    return decide


MECH_ARMS = {"canon": arm_canon, "be1r": arm_be1r,
             "lock1r_2r": arm_lock1r_2r, "trail_1r": arm_trail1r}


# ------------------------------------------------------------------ modes

def cmd_check(trades, bars) -> int:
    """Three reconciliations per trade before any arm may be graded:
      1. the book's exit stamp lies on the trade's path (canon arm settles on a real minute)
      2. single-leg trades: dollars == s*(exit-entry)*20*size - commission, to the cent
      3. partial trades: the inverted partial price traded strictly before the exit minute
    """
    bad, n = [], 0
    for t in trades:
        path = day_path(t, bars)
        if not len(path):
            bad.append((t["trade_id"], "no path"))
            continue
        n += 1
        cx_min, _ = canon_exit_of(t, path)
        if abs((cx_min - t["exit"]).total_seconds()) > 60:
            bad.append((t["trade_id"], f"exit stamp off-path: {t['exit']} vs {cx_min}"))
            continue
        s = sgn(t["direction"])
        if t["exit_reason"].startswith("partial"):
            pp = implied_partial(t)
            seg = path.loc[:cx_min]
            traded = bool(len(seg)) and bool(
                ((seg.low - 1e-9 <= pp) & (pp <= seg.high + 1e-9)).any())
            if not traded:
                bad.append((t["trade_id"],
                            f"implied partial {pp:.2f} never traded before exit"))
        else:
            want = s * (t["exit_price"] - t["entry"]) * 20.0 * t["size"] - COMMISSION
            if not np.isclose(want, t["dollars"], atol=0.02):
                bad.append((t["trade_id"],
                            f"single-leg ${t['dollars']:+,.2f} vs derived ${want:+,.2f}"))
        res = simulate(t, path, arm_canon(t, canon_exit_of(t, path)),
                       canon_exit_of(t, path))
        if not np.isclose(res["dollars"], t["dollars"], atol=0.01):
            bad.append((t["trade_id"], "canon arm does not reproduce book dollars"))
    print(f"checked {n} canon trades")
    print(f"  reconciled: {n - len(bad)}  ({(n - len(bad)) / max(n, 1) * 100:.1f}%)")
    for tid, why in bad[:15]:
        print(f"    {tid}: {why}")
    ok = len(bad) / max(n, 1) <= 0.02
    print(f"  {'PASS' if ok else 'FAIL'} — "
          f"{'harness anchored to the canon' if ok else 'DO NOT GRADE ANY ARM ON THIS'}")
    return 0 if ok else 1


def cmd_grade(trades, bars, span: str) -> int:
    rows = []
    for t in trades:
        path = day_path(t, bars)
        if not len(path):
            continue
        cx = canon_exit_of(t, path)
        base = {"trade_id": t["trade_id"], "day": t["day"], "ts": t["ts"],
                "sess": t["sess"], "era": t["era"], "tier": t["tier"],
                "elite": t["elite"], "risk": t["risk"], "size": t["size"],
                "direction": t["direction"]}
        for name, mk in MECH_ARMS.items():
            r = simulate(t, path, mk(t, cx), cx)
            rows.append({**base, "arm": name, **r})
    D = pd.DataFrame(rows).drop(columns=["partials_taken"])
    out = ROOT / f"output/capture_replay_mech_{span}.parquet"
    D.to_parquet(out, index=False)
    print(f"{'arm':<11}{'1-lot $':>12}{'mean R':>9}{'median R':>10}{'WR':>6}{'held':>7}")
    for name in MECH_ARMS:
        d = D[D.arm == name]
        print(f"{name:<11}${d.dollars.sum():>+11,.0f}{d.R.mean():>9.3f}"
              f"{d.R.median():>10.3f}{(d.dollars > 0).mean() * 100:>5.0f}%"
              f"{d.held_minutes.median():>7.0f}")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["check", "grade"])
    ap.add_argument("--span", default="fit", choices=["fit", "holdout"])
    a = ap.parse_args()
    trades = load_trades(a.span)
    bars = load_bars_ny()
    print(f"canon [{a.span}]: {len(trades)} trades, "
          f"1-lot ${sum(t['dollars'] for t in trades):+,.0f}\n")
    if a.mode == "check":
        raise SystemExit(cmd_check(trades, bars))
    raise SystemExit(cmd_grade(trades, bars, a.span))


if __name__ == "__main__":
    main()
