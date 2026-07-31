#!/usr/bin/env python3
"""The London desk-live chained-agents run. Port of the NY design
(`scripts/capture_desk_run.py`, `claude/agents-capture-handoff-26rnvp`) — see
`docs/PLAN-agents-capture-london.md` for the full design and every place London's
execution semantics differ from NY's (no two-session law, no close-and-reverse, a
dynamic one-at-a-time re-walk instead).

One CONVERSATION per trade (Claude CLI, spec as system prompt, ALL TOOLS DISABLED).
The agent inherits the mechanical V1 plan (engine stop + real structural target) at
fill and owns it to flat. Turns are EVENT-DRIVEN: press check at fill+3m, each
whole-R touch, flow flips against a green position, stop/target proximity, the V1
mechanical-exit minute (take it or refuse it), 10-min rechecks while extended, EOD
warning. Between turns the standing plan executes mechanically minute-by-minute,
driver-side.

Population: the PRE-SERIALIZATION rev-3 candidates (window 08:00-09:45 London + floor
9.5pt + score-0 veto, 161 candidates / 93 days / 39 days with >=2 same-day candidates) —
NOT the frozen 130-trade V1 book. One-at-a-time admission is re-derived LIVE per arm
(mechanical V1 vs agent), from each arm's own REAL realized exit times, because letting
the agent exit earlier or later than V1 changes which candidates are reachable. See
PLAN §4b.

GUARDRAILS (driver-enforced; a malformed or rule-breaking reply degrades to "no
change"): stops only tighten; targets >= 2.0R until a partial is booked (then the
runner rides free, >= 0.1R sanity only); partials strictly 0-1 of what is open; no
re-entries, no size or direction changes; EOD flatten absolute (15:55 ET, or last-bar
on early closes); max 10 turns per trade.

CAUSALITY: every prompt is built from bars/tape/depth strictly <= the turn's minute;
the per-trade transcript (runs/desk_london/transcripts/) is the audit trail.
Executions are next-bar (market actions at next open +/- 1 tick slip; stops resting,
stop-first; targets trade-through) — the engine's own conventions.

    python -m scripts.capture_desk_run_london --demo-day 2025-06-02   # one day, stop
    python -m scripts.capture_desk_run_london                        # the full chain
    python -m scripts.capture_desk_run_london --status
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l0_triggers_london import window_et  # noqa: E402
from scripts.london_combined_job import lon_book  # noqa: E402
from scripts.london_depth import load_day as load_depth_day  # noqa: E402
from scripts.london_holdout_report import CONFIGS, load_pop  # noqa: E402
from scripts.research.v9_tournament import swap_arm  # noqa: E402
from src.canon.scorer import LON_VETO_RESIST, LON_VETO_THICK, LON_VETO_TRIGDENS  # noqa: E402
from src.research.holdout_guard import assert_path_fit_only  # noqa: E402

NY = "America/New_York"
LON = "Europe/London"
SPEC = ROOT / ".claude/agents/trade-manager-london.md"
RUNS = ROOT / "runs/desk_london"
TICK, SLIP, COMMISSION, PV = 0.25, 1, 5.0, 20.0
MAX_TURNS = 10
CLI_TIMEOUT = 240
MASTER = "data/reference/nq_1m_master.parquet"

BUCKETS = [(480, 510, "08:00-08:30"), (510, 540, "08:30-09:00"),
           (540, 570, "09:00-09:30"), (570, 585, "09:30-09:45")]

TURN_CONTRACT = (
    'Reply with EXACTLY one JSON object, nothing else: {"action":"hold"|"revise"|'
    '"exit_now","stop_r":<num,optional>,"target_r":<num or null,optional>,'
    '"partial_pct":<0-1,optional>,"note":"<=120 chars"}. "hold"=no change. "revise" '
    'adjusts the standing plan: stop_r only ever TIGHTENS (in R from entry; 0=BE), '
    'target_r replaces the target (null = run on the stop; >=2.0R unless a partial is '
    'already booked), partial_pct books that fraction of what is OPEN at next bar. '
    '"exit_now" flattens at next bar. Rule-breaking fields are ignored by the harness.')


# ------------------------------------------------------------------ CLI conversations

def call_claude(prompt: str, session: str | None) -> tuple[str, str | None]:
    cmd = ["claude", "-p", "--system-prompt-file", str(SPEC),
           "--disallowedTools", "*", "--output-format", "json"]
    if session:
        cmd += ["--resume", session]
    cmd.append(prompt)
    for attempt in (1, 2):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT,
                               cwd=str(RUNS))
            out = json.loads(r.stdout.strip().splitlines()[-1])
            return out.get("result", ""), out.get("session_id") or session
        except Exception as e:
            if attempt == 2:
                return f"__ERROR__ {e}", session
    return "__ERROR__", session


def parse_reply(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"action": "hold", "note": "unparseable -> no change"}
    try:
        d = json.loads(m.group(0))
    except Exception:
        return {"action": "hold", "note": "bad json -> no change"}
    if d.get("action") not in ("hold", "revise", "exit_now"):
        d["action"] = "hold"
    return d


# ------------------------------------------------------------------ market data views

def flow_line(tape, minute, s) -> str:
    w = tape.loc[:minute]
    if not len(w):
        return "flow: no tape"
    d1 = float(w.delta.iloc[-1]) * s
    c5 = float(w.delta.tail(5).sum()) * s
    c15 = float(w.delta.tail(15).sum()) * s
    opp = int((np.sign(w.delta.tail(5).to_numpy() * s) < 0).sum())
    v = float(w.vol.iloc[-1])
    vmed = float(w.vol.tail(60).median()) or 1.0
    return (f"flow(signed to trade): delta1m {d1:+.0f} cvd5m {c5:+.0f} cvd15m {c15:+.0f} "
            f"opposed {opp}/5 vol {v / vmed:.1f}x")


def book_line(dep, minute, last, s) -> str:
    if dep is None or not len(dep):
        return "book: n/a"
    snap = dep[dep.ts < minute]
    if not len(snap):
        return "book: n/a"
    snap = snap[snap.ts == snap.ts.max()]
    bid, ask = snap[snap.side == "bid"], snap[snap.side == "ask"]
    if not len(bid) or not len(ask):
        return "book: n/a"
    tb, ta = float(bid["size"].sum()), float(ask["size"].sum())
    ahead = ask if s > 0 else bid
    wa = ahead.loc[ahead["size"].idxmax()]
    return (f"book: imbalance {((tb - ta) / max(tb + ta, 1)) * s:+.2f} "
            f"wall-ahead {abs(float(wa.price) - last):.2f}pt x{float(wa['size']):.0f}")


DEPTH_DIR = ROOT / "data/reference/depth_london"


def load_depth(day: str, cache: dict):
    if day in cache:
        return cache[day]
    cache[day] = load_depth_day(day, DEPTH_DIR)
    return cache[day]


# ------------------------------------------------------------------ journal

def journal_rows() -> list[dict]:
    f = RUNS / "journal.jsonl"
    if not f.exists():
        return []
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()]


def journal_digest(rows: list[dict]) -> str:
    if not rows:
        return "journal: no completed trades yet — judge on the tape alone."
    n = len(rows)
    paired = [r for r in rows if r.get("v1_R") is not None]
    da = sum(r["agent_R"] for r in rows)
    dv = sum(r["v1_R"] for r in paired) if paired else 0.0
    ext = sum(1 for r in rows if r.get("extended"))
    parts = sum(1 for r in rows if r.get("partials"))
    lines = [f"journal: {n} trades managed ({len(paired)} paired vs V1) | your total "
             f"{da:+.1f}R vs V1 {dv:+.1f}R on paired trades (delta "
             f"{sum(r['agent_R'] - r['v1_R'] for r in paired):+.1f}R) | held past "
             f"mechanical exit {ext}x | partials {parts}x"]
    for era in ("2025", "2026"):
        g = [r for r in rows if r["day"].startswith(era)]
        if g:
            gp = [r for r in g if r.get("v1_R") is not None]
            lines.append(f"  {era}: n{len(g)} you {sum(r['agent_R'] for r in g):+.1f}R"
                         + (f" vs V1 {sum(r['v1_R'] for r in gp):+.1f}R" if gp else ""))
    dying = [r for r in paired if r["v1_R"] < -0.1]
    winning = [r for r in paired if r["v1_R"] > 0.1]
    if dying:
        lines.append(f"  defense (V1 losers/scratches, n{len(dying)}): you "
                     f"{sum(r['agent_R'] - r['v1_R'] for r in dying):+.1f}R vs V1")
    if winning:
        lines.append(f"  offense (V1 winners, n{len(winning)}): you "
                     f"{sum(r['agent_R'] - r['v1_R'] for r in winning):+.1f}R vs V1")
    cuts = [r for r in rows if r["exit_reason"] == "agent_exit"
            and r.get("left_peak_R") is not None]
    if cuts:
        for label, sel in (
                ("flow still WITH you", [r for r in cuts if r.get("cvd5_at_exit", 0) > 0]),
                ("flow AGAINST you", [r for r in cuts if r.get("cvd5_at_exit", 0) <= 0])):
            if not sel:
                continue
            lp = sorted(r["left_peak_R"] for r in sel)
            died = sum(1 for r in sel if r["would_have_stopped"])
            lines.append(
                f"  your exits with {label} (n{len(sel)}): {died} would have hit the "
                f"stop anyway; median run AFTER you left: {lp[len(lp) // 2]:+.1f}R")
    caps = [r["capture"] for r in rows if r.get("capture") is not None]
    if caps:
        caps.sort()
        lines.append(f"  capture (realized/peak, trades that reached +0.5R): median "
                     f"{caps[len(caps) // 2]:+.2f}")
    lines.append("last trades (you vs V1):")
    for r in rows[-5:]:
        v1s = f"{r['v1_R']:+.2f}R" if r.get("v1_R") is not None else "n/a (agent-only)"
        lines.append(f"  {r['day']} {r['direction']}: {r['agent_R']:+.2f}R vs "
                     f"{v1s} ({r['exit_reason']}; {r.get('last_note', '')[:60]})")
    return "\n".join(lines)


# ------------------------------------------------------------------ candidate population

def bucket_of(minute_of_day: int) -> str:
    for lo, hi, name in BUCKETS:
        if lo <= minute_of_day < hi:
            return name
    return "?"


def load_candidates() -> list[dict]:
    """The 161 pre-serialization rev-3 candidates: window 08:00-09:45 London + floor
    9.5pt + score-0 veto, WITHOUT the one-at-a-time serial_walk step -- that admission
    is re-derived dynamically in main() instead (PLAN §4b). V1's own mechanical
    outcome for each candidate IN ISOLATION (dollars/R/exit_ts/exit_reason/target)
    comes straight from the already-computed L2 V1 arm -- authoritative engine output,
    not re-derived here."""
    P = load_pop("fit")
    P = swap_arm(P, "output/l2_outcomes_london_fit_v1.parquet")
    c = CONFIGS["rev3"]
    lonmins = ((pd.to_datetime(P.fill, format="mixed", utc=True).dt.tz_convert(LON).dt.hour * 60
                + pd.to_datetime(P.fill, format="mixed", utc=True).dt.tz_convert(LON).dt.minute))
    P = P[lonmins < c["cut_min"]]
    b = lon_book(P, floor=9.5, lifetime=math.inf, cap=999).reset_index(drop=True)
    conv = ((b.W == 1) & (b.FAR == 1)).astype(int)
    for f, t in (("dep_thick", LON_VETO_THICK), ("dep_resist", LON_VETO_RESIST),
                 ("trigdens_30", LON_VETO_TRIGDENS)):
        conv = conv + (b[f].astype(float) > t).astype(int)
    b = b[conv.values > 0].reset_index(drop=True)

    A = pd.read_parquet(ROOT / "output/l2_outcomes_london_fit_v1.parquet")
    A = A[["ts", "tf", "direction", "working_target"]].drop_duplicates(
        ["ts", "tf", "direction"])
    b = b.merge(A, on=["ts", "tf", "direction"], how="left", validate="1:1")

    out = []
    for i, t in enumerate(b.itertuples()):
        fill_ts = pd.to_datetime(t.fill_ts, utc=True).tz_convert(NY)
        exit_ts = pd.to_datetime(t.exit_ts, utc=True).tz_convert(NY) if pd.notna(t.exit_ts) \
            else None
        mod = int(pd.Timestamp(t.fill).tz_convert(LON).hour * 60
                  + pd.Timestamp(t.fill).tz_convert(LON).minute)
        tid = f"{t.day}_{fill_ts.strftime('%H%M')}_{t.direction[0]}_{i}"
        out.append(dict(
            trade_id=tid, day=t.day, direction=t.direction, entry=float(t.entry),
            stop=float(t.stop), risk=float(t.risk), fill_ts=fill_ts, pattern=t.pattern,
            era=t.era, tf=t.tf, ts=t.ts, bucket=bucket_of(mod),
            working_target=(float(t.working_target) if pd.notna(t.working_target)
                            else None),
            v1_dollars=float(t.dollars), v1_R=float(t.R), v1_exit_ts=exit_ts,
            v1_exit_reason=str(t.exit_reason)))
    return out


# ------------------------------------------------------------------ bars / tape

def load_bars() -> pd.DataFrame:
    from src.research.holdout_guard import filter_to_fit_years
    assert_path_fit_only(MASTER)
    bars = (pd.read_parquet(ROOT / MASTER).drop(columns=["roll"], errors="ignore")
            .sort_values("ts_event").reset_index(drop=True))
    bars["ts_event"] = pd.to_datetime(bars.ts_event, utc=True)
    bars = filter_to_fit_years(bars, "ts_event", MASTER)
    bars = bars.set_index("ts_event").sort_index().tz_convert(NY)
    return bars


def sgn(direction: str) -> float:
    return 1.0 if direction == "long" else -1.0


# ------------------------------------------------------------------ day reads

def day_reads(day, bars, journal) -> tuple[str, str | None]:
    """Single pre-window thesis read (no cash-open re-read -- London has one
    continuous window, no NY-style session transition to re-read at; PLAN §4)."""
    win_start, _ = window_et(day)
    d0 = win_start - pd.Timedelta(minutes=15)
    prior = bars.loc[:d0 - pd.Timedelta(hours=16)]
    on = bars.loc[d0 - pd.Timedelta(hours=13, minutes=45):d0]
    if not len(on):
        return "no pre-window data", None
    pd_day = (prior[prior.index >= prior.index[-1] - pd.Timedelta("24h")]
              if len(prior) else on)
    last = float(on.close.iloc[-1])
    gap_note = ""
    if journal:
        last_day = max(r["day"] for r in journal)
        gap = (pd.Timestamp(day) - pd.Timestamp(last_day)).days
        if gap > 4:
            gap_note = (f"NOTE: {gap} calendar days since your last journaled day "
                        f"({last_day}) — a sample/time gap. Weight older journal "
                        f"entries accordingly.\n")
    ctx = (f"PRE-WINDOW READ, {day} {d0.strftime('%H:%M')} ET "
           f"(London window opens {win_start.strftime('%H:%M')} ET, 08:00 London "
           f"time, closes 09:45 London). Mechanical entries, you manage them.\n"
           f"{gap_note}"
           f"prior day: O {pd_day.open.iloc[0]:.0f} H {pd_day.high.max():.0f} "
           f"L {pd_day.low.min():.0f} C {pd_day.close.iloc[-1]:.0f}\n"
           f"overnight->pre-window: H {on.high.max():.0f} L {on.low.min():.0f} "
           f"last {last:.0f} (gap {last - float(pd_day.close.iloc[-1]):+.0f} vs prior close)\n"
           f"last 5 bars (t,h,l,c): "
           + "; ".join(f"{t.strftime('%H:%M')} {r.high:.0f}/{r.low:.0f}/{r.close:.0f}"
                       for t, r in on.tail(5).iterrows())
           + f"\n{journal_digest(journal)}\n"
           'Reply EXACTLY one JSON: {"bias":"long|short|neutral","day_type":"<=30 chars",'
           '"thesis":"<=200 chars","invalidates":"<=120 chars"}')
    txt, _ = call_claude(ctx, None)
    return txt.strip(), None


# ------------------------------------------------------------------ the trade loop

def manage_trade(t, bars, tape, dep, thesis, journal) -> dict:
    s, entry, risk_pts = sgn(t["direction"]), t["entry"], t["risk"] / PV
    stop = t["stop"]
    target = t["working_target"]
    day = t["day"]
    flatten = pd.Timestamp(f"{day} 15:55", tz=NY)
    path = bars.loc[t["fill_ts"]:flatten + pd.Timedelta(minutes=5)]
    path = path[path.index <= flatten]

    legs, frac = [], 1.0
    pending: list[tuple] = []
    turns, transcript = 0, []
    partial_done, extended, last_note = False, False, ""
    peak_r, seen_r, last_turn_min = 0.0, set(), None
    r3 = None
    sid = None

    def r_of(px):
        return s * (px - entry) / risk_pts

    def close(fr, px, reason):
        nonlocal frac
        legs.append((fr, px, reason))
        frac = round(frac - fr, 10)

    def settle(reason_final, ts):
        pts = sum(fr * s * (px - entry) for fr, px, _ in legs)
        net = pts * PV - COMMISSION
        after = path.loc[ts:]
        after = after[after.index > ts]
        left_peak, would_stop, end_after = 0.0, False, 0.0
        for mi2, b2 in after.iterrows():
            if mi2 >= flatten:
                break
            if (s > 0 and b2.low <= t["stop"]) or (s < 0 and b2.high >= t["stop"]):
                would_stop = True
                end_after = r_of(t["stop"])
                break
            fav2 = (b2.high - float(legs[-1][1])) if s > 0 else (float(legs[-1][1]) - b2.low)
            left_peak = max(left_peak, float(fav2) / risk_pts)
            end_after = r_of(float(b2.close))
        w = tape.loc[:ts]
        fx = {}
        if len(w) >= 5:
            fx = {"cvd5_at_exit": round(float(w.delta.tail(5).sum()) * s, 0),
                  "cvd15_at_exit": round(float(w.delta.tail(15).sum()) * s, 0),
                  "opposed_at_exit": int((np.sign(w.delta.tail(5).to_numpy() * s) < 0).sum())}
        return {"trade_id": t["trade_id"], "day": day, "direction": t["direction"],
                "bucket": t["bucket"], "era": t["era"], "risk": t["risk"],
                "agent_R": round(net / (risk_pts * PV), 4), "agent_dollars": round(net, 2),
                "v1_R": t["v1_R"], "v1_dollars": t["v1_dollars"],
                "exit_reason": reason_final, "exit_ts": str(ts), "turns": turns,
                "partials": sum(1 for _, _, r in legs if r == "partial"),
                "extended": extended, "held_min": int((ts - t["fill_ts"]).total_seconds() // 60),
                "mfe_R": round(peak_r, 3),
                "capture": round(net / (risk_pts * PV) / peak_r, 3) if peak_r > 0.5 else None,
                "left_peak_R": round(left_peak, 3), "would_have_stopped": bool(would_stop),
                "settle_after_R": round(end_after, 3), **fx,
                "last_note": last_note, "legs": [(f, p, r) for f, p, r in legs]}

    def send(minute, why, bar):
        nonlocal turns, sid, stop, target, pending, partial_done, last_note, last_turn_min
        if turns >= MAX_TURNS or (last_turn_min is not None and minute <= last_turn_min):
            return
        last = float(bar.close)
        press = bool((r3 or 0) >= 0.5 and r_of(last) > 0 and (peak_r - r_of(last)) <= 0.25)
        state = (f"[{minute.strftime('%H:%M')}] EVENT: {why}\n"
                 f"bar {bar.open:.2f}/{bar.high:.2f}/{bar.low:.2f}/{bar.close:.2f} | "
                 f"R_now {r_of(last):+.2f} peak {peak_r:+.2f} | pressing {press} | "
                 f"open {frac:.2f} | stop {r_of(stop):+.2f}R target "
                 f"{'none' if target is None else f'{r_of(target):+.2f}R'} | "
                 f"{flow_line(tape, minute, s)} | {book_line(dep, minute, last, s)} | "
                 f"mins_to_session_end {int((flatten - minute).total_seconds() // 60)}")
        if turns == 0:
            state = (f"NEW POSITION {t['direction'].upper()} | entry {entry} "
                     f"risk {risk_pts:.2f}pt | engine stop {stop} (-1R, INVIOLATE FLOOR) | "
                     f"structural target {target} "
                     f"({'n/a' if target is None else f'{r_of(target):+.1f}R'}) | "
                     f"pattern {t.get('pattern', '?')} | bucket {t['bucket']} | "
                     f"session ends 15:55 ET\n"
                     f"day thesis: {thesis}\n"
                     + f"{journal_digest(journal)}\n{TURN_CONTRACT}\n\n" + state)
        txt, sid2 = call_claude(state, sid)
        sid = sid2 or sid
        rep = parse_reply(txt)
        turns += 1
        last_turn_min = minute
        transcript.append({"minute": str(minute), "why": why, "sent": state, "reply": txt})
        last_note = str(rep.get("note", ""))[:120]
        act = rep["action"]
        if act == "exit_now":
            pending.append(("exit", None))
            return
        if act != "revise":
            return
        if rep.get("stop_r") is not None:
            try:
                cand = entry + s * float(rep["stop_r"]) * risk_pts
                if s * (cand - stop) > 0:
                    stop = round(round(cand / TICK) * TICK, 10)
            except Exception:
                pass
        if "target_r" in rep:
            tr = rep.get("target_r")
            if tr is None:
                target = None
            else:
                try:
                    tr = float(tr)
                    floor = 0.1 if partial_done else 2.0
                    if tr >= floor:
                        target = round(round((entry + s * tr * risk_pts) / TICK) * TICK, 10)
                except Exception:
                    pass
        if rep.get("partial_pct") is not None:
            try:
                p = float(rep["partial_pct"])
                if 0.0 < p < 1.0:
                    pending.append(("partial", p))
            except Exception:
                pass

    ix = path.index
    start = ix.searchsorted(t["fill_ts"], side="right")
    for i in range(start, len(ix)):
        minute, bar = ix[i], path.iloc[i]
        if minute >= flatten:
            close(frac, float(bar.open) - s * SLIP * TICK, "eod")
            return settle("eod", minute) | {"transcript": transcript}
        for kind, val in pending:
            px = float(bar.open) - s * SLIP * TICK
            if kind == "exit" and frac > 0:
                close(frac, px, "agent_exit")
            elif kind == "partial" and frac > 0:
                close(round(frac * val, 10), px, "partial")
                partial_done = True
        pending = []
        if frac <= 0:
            return settle("agent_exit", minute) | {"transcript": transcript}
        if (s > 0 and bar.low <= stop) or (s < 0 and bar.high >= stop):
            px = (min(stop, float(bar.open)) if s > 0 else max(stop, float(bar.open)))
            close(frac, px - s * SLIP * TICK, "stop")
            return settle("stop", minute) | {"transcript": transcript}
        if target is not None and ((s > 0 and bar.high >= target + TICK)
                                   or (s < 0 and bar.low <= target - TICK)):
            close(frac, target, "target")
            return settle("target", minute) | {"transcript": transcript}
        fav = r_of(float(bar.high) if s > 0 else float(bar.low))
        peak_r = max(peak_r, fav)
        why = None
        mins_in = int((minute - t["fill_ts"]).total_seconds() // 60)
        if mins_in == 3:
            r3 = r_of(float(bar.close))
        if turns == 0 and mins_in >= 1:
            why = "position opened — read the tape and set your initial plan"
        elif mins_in == 3:
            why = "press check (fill+3m)"
        for k in range(1, 20):
            if fav >= k and k not in seen_r:
                seen_r.add(k)
                why = f"touched +{k}R"
        if (peak_r >= 1.0 and peak_r - r_of(float(bar.close)) >= 0.75
                and peak_r - 0.25 > getattr(send, "_gb_peak", 0.0)):
            send._gb_peak = peak_r
            why = why or f"giving back off the +{peak_r:.1f}R peak"
        w = tape.loc[:minute]
        if len(w) >= 5 and r_of(float(bar.close)) >= 0.5:
            c5 = float(w.delta.tail(5).sum()) * s
            opp = int((np.sign(w.delta.tail(5).to_numpy() * s) < 0).sum())
            if (c5 < 0 or opp >= 4) and (last_turn_min is None
                                         or minute - last_turn_min >= pd.Timedelta(minutes=5)):
                why = why or "flow turning against a green position"
        if abs(r_of(float(bar.close)) - r_of(stop)) <= 0.3 and mins_in > 3:
            why = why or "price near your stop"
        cx_min = t["v1_exit_ts"]
        if cx_min is not None:
            if minute == cx_min or (minute > cx_min and not extended):
                why = (f"MECHANICAL EXIT NOW: V1 exits this position here "
                       f"({t['v1_exit_reason']}, {t['v1_R']:+.2f}R). Take it (exit_now) "
                       "or refuse it with a plan.")
                extended = True
            elif extended and minute > cx_min and (last_turn_min is None or
                                                   minute - last_turn_min >= pd.Timedelta(minutes=10)):
                why = why or "extended recheck (10m)"
        if int((flatten - minute).total_seconds() // 60) == 30:
            why = why or "30 minutes to EOD flatten"
        if why:
            send(minute, why, bar)
    lastbar = path.iloc[-1] if len(path) else None
    px = float(lastbar.close) if lastbar is not None else entry
    close(frac, px, "early_close")
    return settle("early_close", ix[-1] if len(ix) else t["fill_ts"]) | {"transcript": transcript}


# ------------------------------------------------------------------ chain driver

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo-day", default=None)
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "transcripts").mkdir(exist_ok=True)

    done = set()
    st = RUNS / "state.json"
    if st.exists():
        done = set(json.loads(st.read_text())["done"])
    if a.status:
        rows = journal_rows()
        paired = [r for r in rows if r.get("v1_R") is not None]
        print(f"{len(done)} trades done | journal {len(rows)} rows "
              f"({len(paired)} paired vs V1)")
        if paired:
            da = sum(r["agent_R"] for r in paired)
            dv = sum(r["v1_R"] for r in paired)
            print(f"agent {da:+.1f}R vs V1 {dv:+.1f}R (delta {da - dv:+.1f}R, paired only)")
        return

    T = load_candidates()
    by_day: dict[str, list[dict]] = {}
    for t in T:
        by_day.setdefault(t["day"], []).append(t)
    days = [a.demo_day] if a.demo_day else sorted(by_day)
    bars = load_bars()
    tape = pd.read_parquet(ROOT / "output/fp_minutes.parquet").sort_index()
    dcache: dict = {}

    for day in days:
        if day not in by_day:
            continue
        todays = sorted(by_day[day], key=lambda x: x["fill_ts"])
        journal = journal_rows()
        thesis, _ = day_reads(day, bars, journal)
        print(f"== {day}: {len(todays)} candidates", flush=True)
        v1_open_until = pd.Timestamp("1970-01-01", tz=NY)
        agent_open_until = pd.Timestamp("1970-01-01", tz=NY)
        dep = load_depth(day, dcache)
        for t in todays:
            if t["trade_id"] in done:
                # advance both trackers past this already-processed trade's own record
                jr = next((r for r in journal_rows() if r["trade_id"] == t["trade_id"]), None)
                if jr:
                    agent_open_until = max(agent_open_until, pd.Timestamp(jr["exit_ts"]))
                if t["v1_exit_ts"] is not None and t["fill_ts"] >= v1_open_until:
                    v1_open_until = max(v1_open_until, t["v1_exit_ts"])
                continue
            v1_eligible = t["fill_ts"] >= v1_open_until
            agent_eligible = t["fill_ts"] >= agent_open_until
            if not agent_eligible:
                print(f"  {t['trade_id']}: SKIPPED (agent still in a position until "
                      f"{agent_open_until})", flush=True)
                done.add(t["trade_id"])
                st.write_text(json.dumps({"done": sorted(done)}))
                continue
            tt = dict(t)
            if not v1_eligible:
                tt["v1_R"], tt["v1_dollars"] = None, None
                tt["v1_exit_ts"], tt["v1_exit_reason"] = None, "agent_only"
            journal = journal_rows()
            out = manage_trade(tt, bars, tape, dep, thesis, journal)
            tr = out.pop("transcript")
            (RUNS / "transcripts" / f"{t['trade_id']}.json").write_text(
                json.dumps({"thesis": thesis, "turns": tr}, indent=1))
            with (RUNS / "journal.jsonl").open("a") as f:
                f.write(json.dumps(out) + "\n")
            done.add(t["trade_id"])
            st.write_text(json.dumps({"done": sorted(done)}))
            agent_open_until = pd.Timestamp(out["exit_ts"])
            if v1_eligible and t["v1_exit_ts"] is not None:
                v1_open_until = t["v1_exit_ts"]
            v1s = f"{out['v1_R']:+.2f}R" if out["v1_R"] is not None else "n/a"
            print(f"  {t['trade_id']}: agent {out['agent_R']:+.2f}R vs V1 {v1s} | "
                  f"{out['exit_reason']} | turns {out['turns']}", flush=True)


if __name__ == "__main__":
    main()
