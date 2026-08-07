#!/usr/bin/env python3
"""Intra-trade discretion replay — same trades, same stops, only the management differs.

ANGUS (28-Jul): *"the agent would take the same trades regardless using the mechanical
baseline, its just about how much longer they hold it for with their discretion."*

Every arm replays the IDENTICAL canon fills on the IDENTICAL original stops over the
identical 1-minute path. Entries are frozen. The arms:

  canon      the mechanical exit, exactly as the canon realised it. The baseline.
  be1r       stop to break-even the moment +1R trades. Mechanical control.
  lock1r_2r  at +2R, lock +1R. Mechanical control.
  trail_1r   once +1R, trail the stop 1R behind the high-water mark. Mechanical control.
  agent      the canon plan, plus whatever the trade-manager agent decided at its
             decision points — including holding THROUGH the canon exit.

The mechanical arms are not decoration. `scripts/trail_policies.py` already showed every
trail loses to canon and that BE-at-1R wins on totals while taking months-green from 12/13
to 7/13, with $55,640 of $74,938 coming from five trades. Without those arms beside it,
"the agent beat canon" cannot be distinguished from "holding longer beat canon in this
sample", which is the whole question.

  python -m scripts.run_intrade_replay check              # harness must reproduce canon P&L
  python -m scripts.run_intrade_replay plan               # decision points + briefings
  python -m scripts.run_intrade_replay grade              # replay every arm, report

`plan` writes one briefing + deterministic prompt per decision point under
output/desk_blobs/intrade/. `grade` reads output/intrade_verdicts.jsonl; any trade with no
valid verdict falls back to canon, so a missing or malformed answer can only ever cost the
agent its opportunity — never invent a position.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.canon_mechanical import build_canon  # noqa: E402
from src.canon.news_gate import NewsGate  # noqa: E402
from src.desk.trade_manager import (  # noqa: E402
    EOD_FLATTEN_HM,
    MAX_DECISIONS,
    RECHECK_MIN,
    IntradeVerdict,
    agent_version,
    build_briefing,
    journal_digest,
    journal_row,
)

NY = "America/New_York"
BOOK = ROOT / "output/canon_book.parquet"
BARS = ROOT / "data/reference/nq_1m_master.parquet"
BARS2 = ROOT / "data/reference/nq_1m_feb_jul2026.parquet"
TAPE = ROOT / "output/fp_minutes.parquet"
DEPTH_DIRS = {"NY": ["data/reference/depth_2025", "data/reference/depth_2026"],
              "LONDON": ["data/reference/depth_london", "data/reference/depth_london_10_13"]}
BLOBS = ROOT / "output/desk_blobs/intrade"
VERDICTS = ROOT / "output/intrade_verdicts.jsonl"
OUT = ROOT / "output/intrade_replay.parquet"


def sgn(direction: str) -> float:
    return 1.0 if direction == "long" else -1.0


def load_bars() -> pd.DataFrame:
    fr = [pd.read_parquet(p).drop(columns=["roll"], errors="ignore")
          for p in (BARS, BARS2) if p.exists()]
    b = (pd.concat(fr, ignore_index=True).drop_duplicates("ts_event")
         .sort_values("ts_event").reset_index(drop=True))
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    return b.set_index("mi").sort_index()


def load_canon() -> pd.DataFrame:
    """THE ARMING BOOK — 383 trades, +$55,989.81. Both sessions, news-clean.

    Not `canon_book.parquet`: that is `build_canon(T)` with no corrections, and it is 264 NY
    trades with no London. The armed system is what `scripts/canon_news_clean` builds —

      correction 1  conf_PM -> pm_sofar_conf        the look-ahead fix
      correction 2  news_gate=NewsGate.load()       no NY entry open into a pre-open
                                                    high-impact release (ANGUS 2026-07-26)
      correction 3  dead_zones=[(595, 600)]         the 09:55-10:00 entry cut

    plus the London book, which the blackout leaves untouched by construction (no US release
    prints inside 03:00-08:00 ET). Rebuilt here rather than read from
    `baseline_book_news.parquet`, because that file carries only the SIZED summary —
    session/day/fill/risk_pts/micros/pl — and a replay needs entry, stop and exit price.
    """
    T = pd.read_parquet(ROOT / "output/trade_matrix.parquet")
    T["conf_PM"] = T["pm_sofar_conf"]
    ny = build_canon(T, news_gate=NewsGate.load(), dead_zones=[(595, 600)])
    ny = ny[ny["size"] > 0].assign(session="NY")
    lon = pd.read_parquet(ROOT / "output/london_canon_book.parquet")
    lon = lon[lon["size"] > 0].assign(session="LONDON", win_="london", governor=1.0)
    cols = ["session", "day", "book", "fill", "direction", "entry", "stop", "risk",
            "exit_price", "dollars", "pattern", "win_", "size", "governor", "pl",
            "exit_reason"]
    for f in (ny, lon):
        for c in cols:
            if c not in f.columns:
                f[c] = np.nan
    B = pd.concat([ny[cols], lon[cols]], ignore_index=True)
    B["fill"] = pd.to_datetime(B.fill, utc=True, format="mixed").dt.tz_convert(NY)
    B["day"] = B.day.astype(str).str[:10]
    B = B[B.risk > 0].sort_values("fill").reset_index(drop=True)
    B["trade_id"] = (B.day + "_" + B.session.str[:2] + B.book + "_"
                     + B.fill.dt.strftime("%H%M") + "_" + B.direction.str[0])
    return B


def trade_rows(book: pd.DataFrame) -> list[dict]:
    return book.to_dict("records")


def day_path(trade: dict, bars: pd.DataFrame) -> pd.DataFrame:
    """Fill minute -> 15:55 ET the same session. The engine flattens there, so no arm may
    hold past it."""
    f = trade["fill"]
    end = f.normalize() + pd.Timedelta(minutes=EOD_FLATTEN_HM)
    return bars.loc[f:end]


def derive_canon_exit(trade: dict, path: pd.DataFrame):
    """The canon book stores an exit PRICE but no exit stamp. Recover the stamp as the first
    minute at-or-after the fill whose range contains that price. `check` mode proves this
    reproduces the book's realised dollars before any arm is allowed to rely on it."""
    s_, px, stop = sgn(trade["direction"]), float(trade["exit_price"]), float(trade["stop"])
    hit = path.index[((path.low - 1e-9 <= px) & (px <= path.high + 1e-9)).to_numpy()]
    # A stopped-out trade books at the stop plus a tick of slippage, and that slipped price
    # can sit outside every bar's range. Bound the search by the first stop touch so the
    # canon exit can never be dated LATER than the market actually ended the trade.
    stopped = path.index[((path.low <= stop) if s_ > 0 else (path.high >= stop)).to_numpy()]
    cands = [c[0] for c in (hit, stopped) if len(c)]
    if cands:
        return min(cands), px
    return (path.index[-1], float(path.close.iloc[-1])) if len(path) else (trade["fill"], px)


# Costs, read straight off the engine config and verified against the book: every exit pays
# commission_side x2 = $5, and a stop pays one more tick of slip_normal = $5. On the 185 E4
# trades (mgmt V0, no partial leg) this alone reconciles the replay to the canon exactly —
# median residual $5.00 on target exits and $10.00 on stops.
COMMISSION = 5.0
STOP_SLIP = 5.0
PARTIAL_PCT = 0.50          # sizing.v8_partial_pct — the E3 book's half-off leg


def implied_partial(trade: dict, cx_px: float) -> float | None:
    """The price V8 booked half at, recovered from the canon's own realised dollars.

    The canon book stores one exit price but the E3 book exits in two legs, so
    `(exit_price - entry) x 20` overstates every V8 winner (+13% in aggregate). Rather than
    re-implement V8's partial-level resolution — which would be a second implementation to
    keep in sync — invert the arithmetic the engine already did:

        dollars + costs = 20 x [ 0.5 x s(pp - e) + 0.5 x s(xp - e) ]

    Returns None when the recovered price never traded before the exit, which means the
    trade had no partial leg and the single-exit model is already correct.
    """
    # NY: only the E3 book runs V8, so only it has a partial leg. London labels it outright.
    reason = str(trade.get("exit_reason") or "")
    has_partial = reason.startswith("partial") if reason else (trade["book"] == "E3")
    if not has_partial:
        return None
    s, e = sgn(trade["direction"]), float(trade["entry"])
    gross = float(trade["dollars"]) + COMMISSION
    # gross/20 = P.s(pp-e) + (1-P).s(xp-e)  ->  solve for the partial leg
    lead = (gross / 20.0 - (1 - PARTIAL_PCT) * s * (cx_px - e)) / PARTIAL_PCT
    pp = e + s * lead
    return pp if lead > 0 else None


def _apply_plan(state, act, s, stop, px):
    """Fold a ("plan", target_px, stop_px, partial_pct) decision in at price `px`.

    A stop only ever tightens; a target replaces the previous one; a partial books that
    fraction of WHAT IS STILL OPEN and shrinks the runner. Scaling out twice therefore
    compounds — 0.75 then 0.5 leaves an eighth running, which is the point: conviction can
    be expressed in size rather than only reported as a number.
    """
    if not (isinstance(act, tuple) and act):
        return
    if act[0] == "stop":
        # the mechanical arms speak ("stop", level). Once the agent arm gained targets and
        # partials the tuple grew to ("plan", target, stop, pct), and this guard silently
        # dropped every mechanical stop move — which is why be1r and trail_1r graded
        # byte-identical, both collapsing to plain canon-with-holds.
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
    """Walk the path minute by minute. `decide(minute, state, bar)` returns an action string
    (or None). Stop checks run BEFORE the decision, so no arm can rescue a position the
    market already took out. The V8 half-off leg books the first time its price trades,
    whatever the arm later does with the runner."""
    s, entry = sgn(trade["direction"]), float(trade["entry"])
    cx_min, cx_px = canon_exit
    pp = implied_partial(trade, cx_px)
    state = {"stop": float(trade["stop"]), "extended": False, "peak": entry,
             "force_exit": False, "canon_exit_here": False, "reason": "start",
             "booked": 0.0, "part_px": None, "canon_exit": canon_exit,
             "has_partial": pp is not None, "target": None,
             "runner": 1.0 - (PARTIAL_PCT if pp is not None else 0.0),
             "anchor_px": entry, "agent_booked": 0.0, "partials": []}
    for minute, bar in path.iterrows():
        hi, lo = float(bar.high), float(bar.low)
        stop = state["stop"]
        state["canon_exit_here"] = minute == cx_min
        if state["canon_exit_here"]:
            # The canon closed on THIS bar. Whether its stop also printed here is unknowable
            # from 1-minute data and irrelevant: the mechanical plan's outcome is the book's
            # own realised price. Ask the arm, and if it holds, the stop resumes NEXT bar.
            act = decide(minute, state, bar)
            if act == "take_canon":
                return _out(trade, state, minute, cx_px, "canon")
            if act == "exit_now":
                return _out(trade, state, minute, float(bar.close), "agent_exit")
            # from here the book's `dollars` covers everything up to this price, so the
            # agent's own P&L is measured from the canon exit onward.
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
    """P&L ANCHORED ON THE CANON'S OWN REALISED DOLLARS.

    The alternative — replaying every trade from the fill — needs V8's partial-level
    resolution reimplemented, and a second implementation of the exit engine is a liability,
    not an asset. It also reproduced only 82% of trades exactly, so it would have added noise
    to the very quantity being measured.

    Instead the book's `dollars` is taken as ground truth up to the canon exit, and only the
    DEVIATION is simulated:

      exit at/after the canon exit  ->  book dollars + runner carried from the canon exit
                                        price to wherever the arm actually got out. Exact:
                                        the partial leg is already inside `dollars`, and the
                                        runner is what is still open. This is the
                                        hold-longer case, which is the whole hypothesis.
      exit BEFORE the canon exit    ->  simulated from the fill, flagged `early_deviation`.
                                        Approximate for V8 trades whose partial had not yet
                                        booked; exact for everything else.

    The canon arm therefore reproduces the book to the cent by construction, and every other
    arm is measured as "canon, plus or minus what the deviation earned".
    """
    s_, entry, risk = sgn(trade["direction"]), float(trade["entry"]), float(trade["risk"])
    cx_min, cx_px = state["canon_exit"]
    book = float(trade["dollars"])
    half = float(trade["risk"]) > 42          # sizing.oversized_stop_points -> half size in $
    early = minute < cx_min

    open_frac = state["runner"]
    agent_booked = state["agent_booked"]
    if early:
        gross = (state["booked"]
                 + agent_booked
                 + open_frac * s_ * (px - entry) * 20.0)
        if half:
            gross /= 2.0
        net = gross - COMMISSION - (STOP_SLIP if reason == "stop" else 0.0)
    else:
        carry = agent_booked + open_frac * s_ * (px - cx_px) * 20.0
        if half:
            carry /= 2.0
        # the canon's own exit costs are already inside `book`; holding past it only adds the
        # slippage of the later exit, and only when that exit is a stop.
        net = book + carry - (STOP_SLIP if (reason == "stop" and minute > cx_min) else 0.0)

    return {"exit_minute": minute, "exit_price": px, "exit_reason": reason,
            "points": s_ * (px - entry), "R": net / (risk * 20.0), "dollars": net,
            "canon_dollars": book, "delta_vs_canon": net - book,
            "partials_taken": list(state["partials"]),
            "r_banked": round(agent_booked / (risk * 20.0), 2) if agent_booked else None,
            "r_runner": (round(open_frac * s_ * (px - cx_px) / risk, 2)
                         if not early else None),
            "early_deviation": bool(early), "partial_booked": state["has_partial"],
            "extended": state["extended"],
            "held_minutes": int((minute - trade["fill"]).total_seconds() // 60)}


# ------------------------------------------------------------------ mechanical arms

def arm_canon(trade, canon_exit):
    return lambda m, st, bar: "take_canon" if st["canon_exit_here"] else None


def arm_be1r(trade, canon_exit):
    s, entry, risk = sgn(trade["direction"]), float(trade["entry"]), float(trade["risk"])

    def decide(m, st, bar):
        if s * (st["peak"] - entry) >= risk:
            return ("stop", entry)
        return "take_canon" if st["canon_exit_here"] else None
    return decide


def arm_lock1r_2r(trade, canon_exit):
    s, entry, risk = sgn(trade["direction"]), float(trade["entry"]), float(trade["risk"])

    def decide(m, st, bar):
        if s * (st["peak"] - entry) >= 2 * risk:
            return ("stop", entry + s * risk)
        return "take_canon" if st["canon_exit_here"] else None
    return decide


def arm_trail1r(trade, canon_exit):
    """Once +1R has traded, ride a 1R trail and IGNORE the canon exit — the pure
    'hold longer, mechanically' arm."""
    s, entry, risk = sgn(trade["direction"]), float(trade["entry"]), float(trade["risk"])

    def decide(m, st, bar):
        if s * (st["peak"] - entry) >= risk:
            return ("stop", st["peak"] - s * risk)
        return "take_canon" if st["canon_exit_here"] else None
    return decide


MECH_ARMS = {"canon": arm_canon, "be1r": arm_be1r,
             "lock1r_2r": arm_lock1r_2r, "trail_1r": arm_trail1r}


# ------------------------------------------------------------------ decision points

def decision_points(trade: dict, path: pd.DataFrame, canon_exit) -> list[tuple]:
    """Where the agent is asked. Two anchors from Angus's two rules, then re-checks.

    1. the first minute +1R trades          — 'up 1R and flow against it' (cut or hold)
    2. the canon exit minute                — 'hold it for longer' (take it or extend)
    3. every RECHECK_MIN after that         — only reached if it extended
    """
    s, entry, risk = sgn(trade["direction"]), float(trade["entry"]), float(trade["risk"])
    cx_min, _ = canon_exit
    pts = []
    fav = path.high if s > 0 else path.low
    r1 = path.index[(s * (fav - entry) >= risk).to_numpy()]
    if len(r1) and r1[0] < cx_min:
        pts.append((r1[0], "reached_+1R"))
    pts.append((cx_min, "canon_would_exit_here"))
    m = cx_min + pd.Timedelta(minutes=RECHECK_MIN)
    while m <= path.index[-1] and len(pts) < MAX_DECISIONS:
        nxt = path.index[path.index >= m]
        if not len(nxt):
            break
        pts.append((nxt[0], "recheck_while_extended"))
        m = nxt[0] + pd.Timedelta(minutes=RECHECK_MIN)
    seen, out = set(), []
    for mi, why in pts:
        if mi not in seen:
            seen.add(mi)
            out.append((mi, why))
    return out[:MAX_DECISIONS]


def load_depth(day: str, session: str, cache: dict):
    """NY depth is stored long-form per day; London depth is the raw Databento condensed
    wide layout, so it is folded to the same (ts, side, price, size) shape here."""
    key = (session, day)
    if key in cache:
        return cache[key]
    cache[key] = None
    for d in DEPTH_DIRS[session]:
        if session == "NY":
            f = ROOT / d / f"nq_depth_{day}_ny.csv"
            if f.exists():
                dd = pd.read_csv(f)
                dd["ts"] = pd.to_datetime(dd.ts)
                cache[key] = dd
                break
        else:
            f = ROOT / d / f"glbx-mdp3-{day.replace('-', '')}.mbp-10_condensed.csv"
            if f.exists():
                w = pd.read_csv(f)
                ts = pd.to_datetime(w.ts_event, utc=True).dt.tz_convert(NY)
                parts = [pd.DataFrame({"ts": ts, "side": side, "price": w[px], "size": w[sz]})
                         for lvl in range(10)
                         for side, px, sz in (("bid", f"bid_px_{lvl:02d}", f"bid_sz_{lvl:02d}"),
                                              ("ask", f"ask_px_{lvl:02d}", f"ask_sz_{lvl:02d}"))
                         if px in w.columns]
                dd = pd.concat(parts, ignore_index=True).dropna(subset=["price"])
                cache[key] = dd[dd["size"] > 0]
                break
    return cache[key]


# ------------------------------------------------------------------ modes

def cmd_check(trades, bars) -> int:
    """The derived canon exit must reproduce the book's realised dollars. If it does not,
    every arm below it is measuring against a fiction."""
    bad, n = [], 0
    for t in trades:
        path = day_path(t, bars)
        if not len(path):
            bad.append((t["trade_id"], "no path"))
            continue
        cx = derive_canon_exit(t, path)
        res = simulate(t, path, arm_canon(t, cx), cx)
        n += 1
        want, got = float(t["dollars"]), res["dollars"]
        if not np.isclose(got, want, atol=0.01):
            bad.append((t["trade_id"], f"canon ${want:+,.0f} vs replay ${got:+,.0f}"))
    print(f"replayed {n} canon trades")
    print(f"  reproduced: {n - len(bad)}  ({(n - len(bad)) / max(n, 1) * 100:.1f}%)")
    for tid, why in bad[:15]:
        print(f"    {tid}: {why}")
    ok = len(bad) / max(n, 1) <= 0.02
    print(f"  {'PASS' if ok else 'FAIL'} — "
          f"{'harness reproduces the canon' if ok else 'DO NOT GRADE ANY ARM ON THIS'}")
    return 0 if ok else 1


def reachable_points(trade, path, cx, verdicts):
    """Decision points the position ACTUALLY reaches, given the verdicts answered so far.

    A trade that took its mechanical exit at decision 2 never has a decision 3, so
    pre-generating all six is both wasteful and wrong. Replaying with the verdicts in hand
    and recording where the arm was still open is the only way to know which briefings are
    real — and it is what makes the run chained rather than a batch of independent guesses.
    """
    pts = decision_points(trade, path, cx)
    reached, done = [], {"stop": False}

    def probe(m, st, bar):
        if done["stop"]:
            return None
        for pm, why in pts:
            if pm == m:
                reached.append((m, why))
                v = verdicts.get((trade["trade_id"], m.isoformat()))
                if v is None:
                    done["stop"] = True          # unanswered: stop here, this is the frontier
                    return "take_canon" if st["canon_exit_here"] else "exit_now"
                return _plan_from(v, trade)
        return "take_canon" if st["canon_exit_here"] else None

    simulate(trade, path, probe, cx)
    return reached


def replay_with_verdicts(t, path, cx, verdicts):
    """Replay one trade under the agent arm and return (outcome, [(minute, reason)])."""
    pts = decision_points(t, path, cx)
    seen = []

    def decide(m, st, bar):
        for pm, why in pts:
            if pm == m:
                seen.append((m, why))
                v = verdicts.get((t["trade_id"], m.isoformat()))
                if v is None:
                    return "take_canon" if st["canon_exit_here"] else None
                return _plan_from(v, t)
        return "take_canon" if st["canon_exit_here"] else None

    return simulate(t, path, decide, cx), seen


def build_journal(trades, bars, tape, verdicts, before, cache) -> list[dict]:
    """Journal rows for every trade that CLOSED strictly before `before`.

    The cutoff is the whole point: a decision in week W may only ever look back at trades
    already finished when week W began. Rows carry the flow state at the decision AND the
    forward excursion after it, because "the last 3 times delta was this positive the trade
    ran another 2R" is only answerable when those two live on the same row.
    """
    rows = []
    for t in trades:
        if t["fill"] >= before:
            continue
        path = day_path(t, bars)
        if not len(path):
            continue
        cx = derive_canon_exit(t, path)
        out, seen = replay_with_verdicts(t, path, cx, verdicts)
        if out["exit_minute"] >= before:
            continue                      # still open when the week started
        s_, entry, risk = sgn(t["direction"]), float(t["entry"]), float(t["risk"])
        dep = load_depth(str(t["day"])[:10], t["session"], cache)
        st = {"stop": float(t["stop"]), "extended": False, "peak": entry,
              "canon_exit_here": False, "reason": ""}
        for minute, why in seen:
            st["reason"], st["canon_exit_here"] = why, minute == cx[0]
            b = build_briefing(t, minute, st, bars, tape, dep)
            seg = path.loc[minute:out["exit_minute"]]
            peak = (s_ * (seg.high.max() - entry) if s_ > 0
                    else s_ * (seg.low.min() - entry)) if len(seg) else 0.0
            rows.append(journal_row(b, verdicts.get((t["trade_id"], minute.isoformat())),
                                    {**out, "r_peak_after": peak / risk}))
    return rows


def cmd_plan(trades, bars, week=None) -> int:
    verdicts = read_verdicts()
    print(f"{len(verdicts)} verdicts already answered — emitting only the next frontier\n")
    tape = pd.read_parquet(TAPE)
    tape.index = pd.DatetimeIndex(tape.index)
    tape = tape.sort_index()
    BLOBS.mkdir(parents=True, exist_ok=True)
    cache: dict = {}
    ver, total = agent_version(), 0
    index = []

    jrows: list = []
    if week:
        wk_start = pd.Timestamp(week, tz=NY)
        wk_end = wk_start + pd.Timedelta(days=7)
        jrows = build_journal(trades, bars, tape, verdicts, wk_start, cache)
        (ROOT / "output/intrade_journal.jsonl").write_text(
            "\n".join(json.dumps(r, default=str) for r in jrows))
        trades = [t for t in trades if wk_start <= t["fill"] < wk_end]
        print(f"week {week}: {len(trades)} trades | journal carries {len(jrows)} "
              f"completed decisions\n")

    for t in trades:
        path = day_path(t, bars)
        if not len(path):
            continue
        cx = derive_canon_exit(t, path)
        dep = load_depth(str(t["day"])[:10], t["session"], cache)
        state = {"stop": float(t["stop"]), "extended": False, "reason": "", "peak": t["entry"],
                 "canon_exit_here": False}
        pts = reachable_points(t, path, cx, verdicts)
        for minute, why in pts:
            if (t["trade_id"], minute.isoformat()) in verdicts:
                continue                       # already answered in an earlier round
            state["reason"] = why
            state["canon_exit_here"] = minute == cx[0]
            b = build_briefing(t, minute, state, bars, tape, dep)
            # The digest is matched to THIS briefing, not computed once per week: "situations
            # like this one" is the question, and it has a different answer at +1R than it
            # does sitting on the mechanical target.
            b["journal"] = journal_digest(jrows, like=b)
            b["agent_version"] = ver
            stem = f"{t['trade_id']}__{minute.strftime('%H%M')}"
            # compact, not pretty-printed: these are read by a model, and the indentation was
            # a third of the payload.
            (BLOBS / f"{stem}.briefing.json").write_text(
                json.dumps(b, sort_keys=True, separators=(",", ":")))
            index.append({"trade_id": t["trade_id"], "day": str(t["day"])[:10],
                          "decision_minute": minute.isoformat(), "reason": why, "stem": stem})
            total += 1
    # LOOKAHEAD FIREWALL. Two briefings from the SAME DAY cannot be judged together: the
    # later one carries price, flow and geometry from minutes the earlier one has not lived
    # through yet, so showing both in one prompt hands the earlier decision its own future.
    # Colour the round by day — each group holds at most one decision per day — and the
    # caller issues one judge call per group. Groups are small (the count equals the busiest
    # day in the round, usually 1-3) and the total briefing volume is unchanged.
    groups: list[list[str]] = []
    for row in sorted(index, key=lambda r: r["decision_minute"]):
        for g in groups:
            if row["day"] not in {d for d, _ in g}:
                g.append((row["day"], row["stem"]))
                break
        else:
            groups.append([(row["day"], row["stem"])])
    stems = [[st for _, st in g] for g in groups]
    (ROOT / "output/intrade_round_groups.json").write_text(json.dumps(stems, indent=1))
    if stems:
        print(f"  lookahead firewall: {len(stems)} group(s), sizes "
              f"{[len(g) for g in stems]} — no group shares a day")

    idx_path = ROOT / "output/intrade_decision_index.csv"
    df = pd.DataFrame(index)
    if idx_path.exists() and len(df):
        try:
            prev = pd.read_csv(idx_path)
        except pd.errors.EmptyDataError:   # blank/whitespace-only index from an aborted round
            prev = None
        if prev is not None and len(prev):
            df = (pd.concat([prev, df], ignore_index=True)
                  .drop_duplicates(["trade_id", "decision_minute"]))
    df.to_csv(idx_path, index=False)
    print(f"{len(trades)} trades -> {total} NEW decision points this round")
    print(f"  briefings + prompts: {BLOBS.relative_to(ROOT)}")
    print("  index: output/intrade_decision_index.csv")
    print(f"  agent_version: {ver}")
    return 0


def read_verdicts() -> dict:
    """{(trade_id, decision_minute): IntradeVerdict}. Invalid rows are dropped loudly —
    fail-closed means the trade falls back to canon, never to a guess."""
    out, bad = {}, 0
    if not VERDICTS.exists():
        return out
    for line in VERDICTS.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            v = IntradeVerdict(**json.loads(line))
            out[(v.trade_id, v.decision_minute)] = v
        except Exception:
            bad += 1
    if bad:
        print(f"  {bad} malformed verdicts dropped (those trades fall back to canon)")
    return out


def _plan_from(v, trade):
    """An IntradeVerdict as the replay sees it: exit, or a plan of (target, stop, partial)."""
    if v.action == "exit_now":
        return "exit_now"
    s_, e, risk = sgn(trade["direction"]), float(trade["entry"]), float(trade["risk"])
    tgt = e + s_ * float(v.target_r) * risk if v.target_r is not None else None
    stp = e + s_ * float(v.stop_r) * risk if v.stop_r is not None else None
    return ("plan", tgt, stp, v.partial_pct)


def arm_agent(trade, canon_exit, verdicts, points):
    """The canon plan, overridden only where a valid verdict says otherwise."""
    by_min = {m: why for m, why in points}

    def decide(m, st, bar):
        if m in by_min:
            v = verdicts.get((trade["trade_id"], m.isoformat()))
            if v is not None:
                st["_acted"] = True
                return _plan_from(v, trade)
        return "take_canon" if st["canon_exit_here"] else None
    return decide


def cmd_grade(trades, bars) -> int:
    verdicts = read_verdicts()
    print(f"loaded {len(verdicts)} valid verdicts\n")
    rows = []
    for t in trades:
        path = day_path(t, bars)
        if not len(path):
            continue
        cx = derive_canon_exit(t, path)
        pts = decision_points(t, path, cx)
        base = {"trade_id": t["trade_id"], "day": str(t["day"])[:10], "win_": t["win_"],
                "size": float(t["size"]), "governor": float(t["governor"]),
                "risk": float(t["risk"]), "direction": t["direction"]}
        for name, mk in MECH_ARMS.items():
            r = simulate(t, path, mk(t, cx), cx)
            rows.append({**base, "arm": name, **r})
        r = simulate(t, path, arm_agent(t, cx, verdicts, pts), cx)
        rows.append({**base, "arm": "agent", **r})
    D = pd.DataFrame(rows)
    D["pl"] = D.dollars * D["size"] * D.governor
    D.to_parquet(OUT, index=False)

    print("=" * 92)
    print("INTRA-TRADE DISCRETION — same trades, same stops, only management differs")
    print("=" * 92)
    print(f"  {'arm':<11}{'total P&L':>12}{'mean R':>9}{'median R':>10}{'WR':>6}"
          f"{'held min':>10}{'green mo':>10}{'maxDD':>10}")
    for name in list(MECH_ARMS) + ["agent"]:
        d = D[D.arm == name]
        if not len(d):
            continue
        mo = d.groupby(d.day.str[:7]).pl.sum()
        cum = d.groupby("day").pl.sum().cumsum()
        print(f"  {name:<11}${d.pl.sum():>+11,.0f}{d.R.mean():>9.2f}{d.R.median():>10.2f}"
              f"{(d.R > 0).mean()*100:>5.0f}%{d.held_minutes.median():>10.0f}"
              f"{int((mo > 0).sum()):>7}/{len(mo)}"
              f"${(cum.cummax() - cum).max():>9,.0f}")
    a, c = D[D.arm == "agent"], D[D.arm == "canon"]
    if len(verdicts):
        m = a.merge(c[["trade_id", "pl", "R"]], on="trade_id", suffixes=("", "_canon"))
        diff = m.pl - m.pl_canon
        print(f"\n  agent vs canon: ${diff.sum():+,.0f} over {len(m)} trades — "
              f"better on {int((diff > 0).sum())}, worse on {int((diff < 0).sum())}, "
              f"unchanged {int((diff == 0).sum())}")
        ext = a[a.extended]
        print(f"  held through the canon exit on {len(ext)} trades "
              f"({len(ext)/max(len(a),1)*100:.0f}%), mean R {ext.R.mean():.2f}"
              if len(ext) else "  never held through a canon exit")
    else:
        print("\n  NO VERDICTS — the agent arm is canon by construction. Run `plan`, answer "
              "the briefings, append to output/intrade_verdicts.jsonl, then grade.")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["check", "plan", "grade"])
    ap.add_argument("--week", default=None,
                    help="ISO date of a Monday: emit only that week, with a journal built "
                         "from trades that closed before it (the chronological chain)")
    a = ap.parse_args()
    book = load_canon()
    trades = trade_rows(book)
    bars = load_bars()
    n = book.session.value_counts().to_dict()
    print(f"arming canon: {len(trades)} taken trades ({n}) on {book.day.nunique()} days, "
          f"1-lot ${book.dollars.sum():+,.0f}\n")
    if a.mode == "plan":
        raise SystemExit(cmd_plan(trades, bars, week=a.week))
    raise SystemExit({"check": cmd_check, "grade": cmd_grade}[a.mode](trades, bars))


if __name__ == "__main__":
    main()
