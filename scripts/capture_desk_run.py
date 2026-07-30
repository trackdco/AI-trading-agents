#!/usr/bin/env python3
"""The desk-live chained-agents run — ANGUS's mandate, 2026-07-30 (this session):

  "i want it to literally be like me sitting at a desk live watching the order flow,
   adapting as things change... entry mechanism mechanical for now, trade management the
   agents have all the discretion, with hard guard rails set of course."

One CONVERSATION per trade (Claude CLI, spec as system prompt, ALL TOOLS DISABLED —
bounded context enforced at the harness level). The agent inherits the mechanical plan
(engine stop + structural working target) at fill and owns it to flat. Turns are
EVENT-DRIVEN (budget ruling: ~8h / ~500 trades): press check at fill+3m, each whole-R
touch, flow flips against a green position, stop/target proximity, the canon-exit minute
(take it or refuse it), 10-min rechecks while extended, EOD warning. Between turns the
standing plan executes mechanically minute-by-minute, driver-side.

Sample (ANGUS): 3 months per era, declared rule first/middle/last-full —
2025-06, 2025-09, 2025-12, 2026-02, 2026-04, 2026-06. Full days, fill order, day thesis
at 07:45 + re-read at 09:40 (gold fills carry both; pre fills only the 07:45 read).

GUARDRAILS (driver-enforced; a malformed or rule-breaking reply degrades to "no change"):
stops only tighten; targets >= 2.0R until a partial is booked (then the runner rides
free, >= 0.1R sanity only); partials strictly 0-1 of what is open; no re-entries, no
size or direction changes; EOD flatten absolute (15:55, or last-bar on early closes);
max 10 turns per trade.

CAUSALITY: every prompt is built from bars/tape/depth strictly <= the turn's minute; the
per-trade transcript (runs/desk/transcripts/) is the audit trail. Executions are next-bar
(market actions at next open +/- 1 tick slip; stops resting, stop-first; targets
trade-through), the engine's own conventions.

    python -m scripts.capture_desk_run --demo-day 2025-06-02   # one day, then stop
    python -m scripts.capture_desk_run                          # the sampled chain
    python -m scripts.capture_desk_run --status
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.capture_replay import load_trades, load_bars_ny, sgn  # noqa: E402

NY = "America/New_York"
SPEC = ROOT / ".claude/agents/trade-manager-v3.md"
RUNS = ROOT / "runs/desk2"
# Phase 1 (ANGUS: "im happy to run a bigger chained run"): the ENTIRE fit span,
# chronological. Phase 2 = the sealed 2023/24 holdout, full-tier, policy frozen — LAST,
# so the untouched span stays the proof.
MONTHS = [f"2025-{m:02d}" for m in range(6, 13)] + [f"2026-{m:02d}" for m in range(2, 8)]
TICK, SLIP, COMMISSION, PV = 0.25, 1, 5.0, 20.0
MAX_TURNS = 10
CLI_TIMEOUT = 240

DEPTH_DIRS = ["data/reference/depth_2025", "data/reference/depth_2026",
              "data/reference/depth_apr2026", "data/reference/depth_2023_24"]

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


def load_depth(day: str, cache: dict):
    if day in cache:
        return cache[day]
    cache[day] = None
    for d in DEPTH_DIRS:
        f = ROOT / d / f"nq_depth_{day}_ny.csv"
        if f.exists():
            dd = pd.read_csv(f)
            dd["ts"] = pd.to_datetime(dd.ts)
            cache[day] = dd
            break
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
    da = sum(r["agent_R"] for r in rows)
    dv = sum(r["v8_R"] for r in rows)
    ext = sum(1 for r in rows if r.get("extended"))
    parts = sum(1 for r in rows if r.get("partials"))
    lines = [f"journal: {n} trades managed | your total {da:+.1f}R vs V8 {dv:+.1f}R "
             f"(delta {da - dv:+.1f}R) | held past mechanical exit {ext}x | partials {parts}x"]
    for sess in ("pre", "gold"):
        g = [r for r in rows if r["sess"] == sess]
        if g:
            lines.append(f"  {sess}: n{len(g)} you {sum(r['agent_R'] for r in g):+.1f}R "
                         f"vs V8 {sum(r['v8_R'] for r in g):+.1f}R")
    # the gauges: dying vs winning trades, and the cutting-early scorecard
    dying = [r for r in rows if r["v8_R"] < -0.1]
    winning = [r for r in rows if r["v8_R"] > 0.1]
    if dying:
        lines.append(f"  defense (mech losers, n{len(dying)}): you "
                     f"{sum(r['agent_R'] - r['v8_R'] for r in dying):+.1f}R vs mech")
    if winning:
        lines.append(f"  offense (mech winners, n{len(winning)}): you "
                     f"{sum(r['agent_R'] - r['v8_R'] for r in winning):+.1f}R vs mech")
    cuts = [r for r in rows if r["exit_reason"] == "agent_exit"
            and r.get("left_peak_R") is not None]
    if cuts:
        # CONDITIONED on the state at exit — so the read is "when it looks like THIS,
        # it usually runs X more" rather than one blended number (ANGUS).
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
    lines.append("last trades (you vs V8):")
    for r in rows[-5:]:
        lines.append(f"  {r['day']} {r['sess']} {r['direction']}: {r['agent_R']:+.2f}R vs "
                     f"{r['v8_R']:+.2f}R ({r['exit_reason']}; {r.get('last_note', '')[:60]})")
    return "\n".join(lines)


# ------------------------------------------------------------------ day reads

def day_reads(day, bars, journal, state) -> tuple[str, str | None, str | None]:
    """07:45 thesis (one session) and the 09:40 open re-read (same session, resumed)."""
    d0 = pd.Timestamp(f"{day} 07:40", tz=NY)
    prior = bars.loc[:d0 - pd.Timedelta(hours=16)]
    on = bars.loc[d0 - pd.Timedelta(hours=13, minutes=40):d0]      # 18:00 -> 07:40
    if not len(on):
        return "no overnight data", None, None
    pd_day = (prior[prior.index >= prior.index[-1] - pd.Timedelta("24h")]
              if len(prior) else on)
    last = float(on.close.iloc[-1])
    gap_note = ""
    if journal:
        last_day = max(r["day"] for r in journal)
        gap = (pd.Timestamp(day) - pd.Timestamp(last_day)).days
        if gap > 4:
            gap_note = (f"NOTE: {gap} calendar days since your last journaled day "
                        f"({last_day}) — a sample/time gap. The regime may have shifted; "
                        f"weight your older journal entries accordingly.\n")
    ctx = (f"PRE-MARKET READ, {day} 07:45 ET. You trade NQ pullback rejections: pre "
           f"08:00-09:30 (ALL pre positions flattened at 09:30 — two sessions), gold "
           f"09:40-10:30, mechanical entries, you manage them.\n{gap_note}"
           f"prior day: O {pd_day.open.iloc[0]:.0f} H {pd_day.high.max():.0f} "
           f"L {pd_day.low.min():.0f} C {pd_day.close.iloc[-1]:.0f}\n"
           f"overnight (18:00->07:40): H {on.high.max():.0f} L {on.low.min():.0f} "
           f"last {last:.0f} (gap {last - float(pd_day.close.iloc[-1]):+.0f} vs prior close)\n"
           f"last 5 bars (t,h,l,c): "
           + "; ".join(f"{t.strftime('%H:%M')} {r.high:.0f}/{r.low:.0f}/{r.close:.0f}"
                       for t, r in on.tail(5).iterrows())
           + f"\n{journal_digest(journal)}\n"
           'Reply EXACTLY one JSON: {"bias":"long|short|neutral","day_type":"<=30 chars",'
           '"thesis":"<=200 chars","invalidates":"<=120 chars"}')
    txt, sid = call_claude(ctx, None)
    thesis = txt.strip()
    reread = None
    if sid:
        o = bars.loc[pd.Timestamp(f"{day} 09:30", tz=NY):pd.Timestamp(f"{day} 09:39", tz=NY)]
        if len(o):
            rr = (f"09:40 RE-READ. The cash open printed: 09:30-09:39 "
                  f"O {o.open.iloc[0]:.0f} H {o.high.max():.0f} L {o.low.min():.0f} "
                  f"C {o.close.iloc[-1]:.0f}. Update or confirm your read. "
                  'Reply EXACTLY one JSON: {"bias":"long|short|neutral",'
                  '"note":"<=150 chars"}')
            txt2, _ = call_claude(rr, sid)
            reread = txt2.strip()
    return thesis, reread, sid


# ------------------------------------------------------------------ the trade loop

def manage_trade(t, bars, tape, dep, thesis, reread, journal, log) -> dict:
    s, entry, risk, size = sgn(t["direction"]), t["entry"], t["risk"], t["size"]
    stop = t["stop"]
    target = t.get("working_target")
    day = t["day"]
    path = bars.loc[t["fill"]:t["fill"].normalize() + pd.Timedelta(hours=16, minutes=10)]
    path = path[path.index.strftime("%Y-%m-%d") == day]
    # TWO-SESSION LAW: pre positions die at 09:30; everything at 15:55.
    flatten = pd.Timestamp(f"{day} 09:30" if t["sess"] == "pre" else f"{day} 15:55", tz=NY)
    flip_at, flip_px, flip_by = t.get("flip_at"), t.get("flip_px"), t.get("flip_by")
    cx_min = t["exit"]

    legs, frac = [], 1.0
    pending: list[tuple] = []            # market actions executing at next bar open
    turns, transcript = 0, []
    partial_done, extended, last_note = False, False, ""
    peak_r, seen_r, last_turn_min = 0.0, set(), None
    r3, r5 = None, None                  # minute-close R at fill+3 / fill+5 (press state)
    sid = None

    def r_of(px):
        return s * (px - entry) / risk

    def close(fr, px, reason):
        nonlocal frac
        legs.append((fr, px, reason))
        frac = round(frac - fr, 10)

    def settle(reason_final, ts):
        pts = sum(fr * s * (px - entry) for fr, px, _ in legs)
        net = pts * PV * size - COMMISSION
        # WHAT THE TRADE DID AFTER THE EXIT — the cutting-early detector (ANGUS: "so it
        # knows after a while if its likely its cutting trades early"). Post-exit path on
        # the ORIGINAL stop to the session boundary, stop-first. Computed at close, read
        # only by LATER trades — causal by the journal cutoff.
        after = path.loc[ts:]
        after = after[after.index > ts]
        bound = flatten
        left_peak, would_stop, end_after = 0.0, False, 0.0
        for mi2, b2 in after.iterrows():
            if mi2 >= bound:
                break
            if (s > 0 and b2.low <= t["stop"]) or (s < 0 and b2.high >= t["stop"]):
                would_stop = True
                end_after = r_of(t["stop"])
                break
            fav2 = (b2.high - float(legs[-1][1])) if s > 0 else (float(legs[-1][1]) - b2.low)
            left_peak = max(left_peak, float(fav2) / risk)
            end_after = r_of(float(b2.close))
        w = tape.loc[:ts]
        fx = {}
        if len(w) >= 5:
            fx = {"cvd5_at_exit": round(float(w.delta.tail(5).sum()) * s, 0),
                  "cvd15_at_exit": round(float(w.delta.tail(15).sum()) * s, 0),
                  "opposed_at_exit": int((np.sign(w.delta.tail(5).to_numpy() * s) < 0).sum())}
        return {"trade_id": t["trade_id"], "day": day, "sess": t["sess"],
                "direction": t["direction"], "risk": risk,
                "agent_R": round(net / (risk * PV), 4), "agent_dollars": round(net, 2),
                "v8_R": round(t["dollars"] / (risk * PV), 4), "v8_dollars": t["dollars"],
                "exit_reason": reason_final, "exit_ts": str(ts), "turns": turns,
                "partials": sum(1 for _, _, r in legs if r == "partial"),
                "extended": extended, "held_min": int((ts - t["fill"]).total_seconds() // 60),
                "mfe_R": round(peak_r, 3),
                "capture": round(net / (risk * PV) / peak_r, 3) if peak_r > 0.5 else None,
                "left_peak_R": round(left_peak, 3), "would_have_stopped": bool(would_stop),
                "settle_after_R": round(end_after, 3), **fx,
                "last_note": last_note, "legs": [(f, p, r) for f, p, r in legs]}

    def send(minute, why, bar):
        nonlocal turns, sid, stop, target, pending, partial_done, last_note, last_turn_min
        if turns >= MAX_TURNS or (last_turn_min is not None and minute <= last_turn_min):
            return
        last = float(bar.close)
        press = bool((((r3 or 0) >= 0.5) or ((r5 or 0) >= 0.5))
                     and r_of(last) > 0 and (peak_r - r_of(last)) <= 0.25)
        state = (f"[{minute.strftime('%H:%M')}] EVENT: {why}\n"
                 f"bar {bar.open:.2f}/{bar.high:.2f}/{bar.low:.2f}/{bar.close:.2f} | "
                 f"R_now {r_of(last):+.2f} peak {peak_r:+.2f} | press_state {press} | "
                 f"open {frac:.2f} | stop {r_of(stop):+.2f}R target "
                 f"{'none' if target is None else f'{r_of(target):+.2f}R'} | "
                 f"{flow_line(tape, minute, s)} | {book_line(dep, minute, last, s)} | "
                 f"mins_to_session_end {int((flatten - minute).total_seconds() // 60)}")
        if turns == 0:
            state = (f"NEW POSITION {t['direction'].upper()} {t['sess']} | entry {entry} "
                     f"risk {risk}pt | engine stop {stop} (-1R, INVIOLATE FLOOR) | "
                     f"structural target {target} "
                     f"({'n/a' if target is None else f'{r_of(target):+.1f}R'}) | "
                     f"pattern {t.get('pattern', '?')} | session ends "
                     f"{'09:30 HARD (pre)' if t['sess'] == 'pre' else '15:55'}\n"
                     + ("reversal context: this entry CLOSED an opposing position — you "
                        "are trading the book's strongest signal\n"
                        if t.get("is_reversal") else "")
                     + f"day thesis: {thesis}\n"
                     + (f"open re-read: {reread}\n" if reread and t["sess"] == "gold" else "")
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
                cand = entry + s * float(rep["stop_r"]) * risk
                if s * (cand - stop) > 0:                       # tighten only
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
                        target = round(round((entry + s * tr * risk) / TICK) * TICK, 10)
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
    start = ix.searchsorted(t["fill"], side="right")
    for i in range(start, len(ix)):
        minute, bar = ix[i], path.iloc[i]
        # 1. session flatten at the bar's open (09:30 for pre — two-session law; else 15:55)
        if minute >= flatten:
            reason = "open_flatten" if t["sess"] == "pre" else "eod"
            close(frac, float(bar.open) - s * SLIP * TICK, reason)
            return settle(reason, minute) | {"transcript": transcript}
        # 1b. CLOSE-AND-REVERSE LAW: an opposing canon fill this minute closes the position
        # at that fill. Stop still checks first on this bar (conservative), then the flip.
        if flip_at is not None and minute >= flip_at and frac > 0:
            if (s > 0 and bar.low <= stop) or (s < 0 and bar.high >= stop):
                px = (min(stop, float(bar.open)) if s > 0 else max(stop, float(bar.open)))
                close(frac, px - s * SLIP * TICK, "stop")
                return settle("stop", minute) | {"transcript": transcript}
            close(frac, float(flip_px), "flip")
            transcript.append({"minute": str(minute), "why": "OPPOSING SIGNAL FILLED",
                               "sent": f"harness: opposing canon signal ({flip_by}) filled "
                                       f"at {flip_px} — position closed and reversed (law)",
                               "reply": "(no reply — mechanical)"})
            return settle("flip", minute) | {"transcript": transcript}
        # 2. pending market actions at this bar's open
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
        # 3. stop, stop-first
        if (s > 0 and bar.low <= stop) or (s < 0 and bar.high >= stop):
            px = (min(stop, float(bar.open)) if s > 0 else max(stop, float(bar.open)))
            close(frac, px - s * SLIP * TICK, "stop")
            return settle("stop", minute) | {"transcript": transcript}
        # 4. target, trade-through
        if target is not None and ((s > 0 and bar.high >= target + TICK)
                                   or (s < 0 and bar.low <= target - TICK)):
            close(frac, target, "target")
            return settle("target", minute) | {"transcript": transcript}
        # 5. state + events
        fav = r_of(float(bar.high) if s > 0 else float(bar.low))
        peak_r = max(peak_r, fav)
        why = None
        mins_in = int((minute - t["fill"]).total_seconds() // 60)
        if mins_in == 3:
            r3 = r_of(float(bar.close))
        elif mins_in == 5:
            r5 = r_of(float(bar.close))
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
        if minute == cx_min or (minute > cx_min and not extended):
            why = f"MECHANICAL EXIT NOW: V8 exits this position here at {t['exit_price']}" \
                  f" ({r_of(t['exit_price']):+.2f}R). Take it (exit_now) or refuse it with a plan."
            extended = True
        elif extended and minute > cx_min and (last_turn_min is None or
                                               minute - last_turn_min >= pd.Timedelta(minutes=10)):
            why = why or "extended recheck (10m)"
        if int((flatten - minute).total_seconds() // 60) == 30:
            why = why or "30 minutes to EOD flatten"
        if why:
            send(minute, why, bar)
    # bars ran out (early close): flatten at last close
    lastbar = path.iloc[-1] if len(path) else None
    px = float(lastbar.close) if lastbar is not None else entry
    close(frac, px, "early_close")
    return settle("early_close", ix[-1] if len(ix) else t["fill"]) | {"transcript": transcript}


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
        print(f"{len(done)} trades done | journal {len(rows)} rows")
        if rows:
            da = sum(r["agent_R"] for r in rows)
            dv = sum(r["v8_R"] for r in rows)
            print(f"agent {da:+.1f}R vs V8 {dv:+.1f}R (delta {da - dv:+.1f}R)")
        return

    T = load_trades("fit")
    # base_v8 arm carries working_target for every canon trade (the rescued l2_outcomes
    # predates that column)
    L2 = pd.read_parquet(ROOT / "output/fixedr_fit_base_v8.parquet")
    wt = {(r.ts, r.direction): float(r.working_target) for r in L2.itertuples()}
    for t in T:
        t["working_target"] = wt.get((t["ts"], t["direction"]))
    # THE MECHANICAL BASELINE IS THE TWO-RULE CANON: overlay exits/dollars replace the raw
    # V8 walk for flipped/pre-flattened trades — the agent is measured against the book as
    # it would actually execute, and the "mechanical exit" marker is the real one.
    O = pd.read_parquet(ROOT / "output/aikido_cr_fit.parquet").set_index(["ts", "direction"])
    if "cr_suppressed" in O.columns:      # rule 3: one-per-level — these trades don't exist
        sup = set(O[O.cr_suppressed].index)
        T = [t for t in T if (t["ts"], t["direction"]) not in sup]
        O = O[~O.cr_suppressed]
    for t in T:
        k = (t["ts"], t["direction"])
        if k in O.index:
            r = O.loc[k]
            t["dollars"] = float(r.cr_dollars_1lot)
            t["exit_price"] = float(r.cr_exit_price)
            t["exit"] = pd.to_datetime(r.cr_exit_ts).tz_convert(NY)
    # CLOSE-AND-REVERSE boundaries from the FIXED entry stream: a trade's first opposing
    # fill (same day, after its own fill) is its hard horizon if still open there.
    by_day: dict[str, list[dict]] = {}
    for t in T:
        by_day.setdefault(t["day"], []).append(t)
    for day_, g in by_day.items():
        g.sort(key=lambda x: x["fill"])
        for i, ta in enumerate(g):
            ta["flip_at"] = ta["flip_px"] = ta["flip_by"] = None
            for b in g[i + 1:]:
                if b["direction"] != ta["direction"]:
                    ta["flip_at"], ta["flip_px"] = b["fill"], float(b["entry"])
                    ta["flip_by"] = b["trade_id"]
                    break
    if a.demo_day:
        days = [a.demo_day]
    else:
        days = sorted({t["day"] for t in T if t["day"][:7] in MONTHS})
    bars = load_bars_ny()
    tape = pd.read_parquet(ROOT / "output/fp_minutes.parquet").sort_index()
    dcache: dict = {}

    for day in days:
        todays = [t for t in T if t["day"] == day and t["trade_id"] not in done]
        if not todays:
            continue
        journal = journal_rows()
        thesis, reread, _ = day_reads(day, bars, journal, None)
        print(f"== {day}: {len(todays)} trades", flush=True)
        flipped_by_agent: set = set()
        for t in sorted(todays, key=lambda x: x["fill"]):
            t["is_reversal"] = t["trade_id"] in flipped_by_agent
            journal = journal_rows()
            dep = load_depth(day, dcache)
            out = manage_trade(t, bars, tape, dep, thesis, reread, journal, None)
            if out["exit_reason"] == "flip" and t.get("flip_by"):
                flipped_by_agent.add(t["flip_by"])
            tr = out.pop("transcript")
            (RUNS / "transcripts" / f"{t['trade_id']}.json").write_text(
                json.dumps({"thesis": thesis, "reread": reread, "turns": tr}, indent=1))
            with (RUNS / "journal.jsonl").open("a") as f:
                f.write(json.dumps(out) + "\n")
            done.add(t["trade_id"])
            st.write_text(json.dumps({"done": sorted(done)}))
            print(f"  {t['trade_id']}: agent {out['agent_R']:+.2f}R vs V8 "
                  f"{out['v8_R']:+.2f}R | {out['exit_reason']} | turns {out['turns']}",
                  flush=True)


if __name__ == "__main__":
    main()
