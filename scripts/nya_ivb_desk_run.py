#!/usr/bin/env python3
"""NYA-IVB-01 agent rung — the fade desk run (PREREG-fab-ivb amendment
2026-08-05d). Adapted from scripts/capture_desk_run.py: one CLI conversation
per trade, tools disabled, event-driven turns, guardrails driver-enforced,
next-bar execution, stop-first, 15:55 flatten. Baseline = the mechanical
default walk. Sample = the six declared tape-rich months.

    python -m scripts.nya_ivb_desk_run --demo-day 2025-06-04
    python -m scripts.nya_ivb_desk_run
    python -m scripts.nya_ivb_desk_run --status
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

NY = "America/New_York"
SPEC = ROOT / ".claude/agents/trade-manager-fade-v1.md"
RUNS = ROOT / "runs/fade_desk1"
MONTHS = ["2025-06", "2025-09", "2025-12", "2026-02", "2026-04", "2026-06"]
TICK, SLIP, FR = 0.25, 1, 1.0
MAX_TURNS = 8
CLI_TIMEOUT = 240

TURN_CONTRACT = (
    'Reply with EXACTLY one JSON object, nothing else: {"action":"hold"|"revise"|'
    '"exit_now","stop_r":<num,optional>,"target_r":<num or null,optional>,'
    '"partial_pct":<0-1,optional>,"note":"<=120 chars"}. "hold"=no change. "revise" '
    'adjusts the standing plan: stop_r only ever TIGHTENS (in R from entry; 0=BE), '
    'target_r replaces the target (null = run on the stop; >=2.0R unless a partial is '
    'already booked), partial_pct books that fraction of what is OPEN at next bar. '
    '"exit_now" flattens at next bar. Rule-breaking fields are ignored by the harness.')


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


def flow_line(tape, minute, s) -> str:
    if tape is None:
        return "flow: no tape this era"
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


def book_line(dep, minute, s) -> str:
    """Per-minute aggregates from output/depth_minutes.parquet — at-price
    reads only (canon 2a9c221); wall_dist valid post decoder fix."""
    if dep is None:
        return "book: n/a"
    snap = dep[dep.index <= minute]
    if not len(snap):
        return "book: n/a"
    r = snap.iloc[-1]
    if (minute - snap.index[-1]) > pd.Timedelta(minutes=3):
        return "book: n/a (stale)"
    imb = (r.imb - 0.5) * 2 * s  # + = book leans with the trade
    opp_ratio = r.ask_wall_ratio if s > 0 else r.bid_wall_ratio
    opp_dist = r.ask_wall_dist if s > 0 else r.bid_wall_dist
    return (f"book: imbalance {imb:+.2f} | wall-ahead ratio {opp_ratio:.1f} "
            f"at {opp_dist:.2f}pt (visible +/-2pt only)")


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
    dm = sum(r["mech_R"] for r in rows)
    lines = [f"journal: {n} trades managed | your total {da:+.1f}R vs mech {dm:+.1f}R "
             f"(delta {da - dm:+.1f}R)"]
    dying = [r for r in rows if r["mech_R"] < -0.1]
    winning = [r for r in rows if r["mech_R"] > 0.1]
    if dying:
        lines.append(f"  defense (mech losers, n{len(dying)}): you "
                     f"{sum(r['agent_R'] - r['mech_R'] for r in dying):+.1f}R vs mech")
    if winning:
        lines.append(f"  offense (mech winners, n{len(winning)}): you "
                     f"{sum(r['agent_R'] - r['mech_R'] for r in winning):+.1f}R vs mech")
    lines.append("last trades (you vs mech):")
    for r in rows[-5:]:
        lines.append(f"  {r['day']} {r['direction']}: {r['agent_R']:+.2f}R vs "
                     f"{r['mech_R']:+.2f}R ({r['exit_reason']}; {r.get('last_note', '')[:60]})")
    return "\n".join(lines)


def build_trades() -> list[dict]:
    """The default-spec fade walk, full detail (mirrors nya_ivb_fade_era.py)."""
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    out = []
    for d, r in R.groupby("gday"):
        r = r.sort_values("ts").reset_index(drop=True)
        ib = r[r.clock < "10:00"]
        if len(ib) < 25 or len(r) < 200:
            continue
        ibh, ibl = ib.high.max(), ib.low.min()
        rng = ibh - ibl
        if rng <= 0:
            continue
        mid = (ibh + ibl) / 2
        win = r[(r.clock >= "10:00") & (r.clock < "10:30")]
        touch = None
        for i, row in win.iterrows():
            if row.close > ibh or row.close < ibl:
                break
            if row.high >= ibh: touch = (-1, i); break
            if row.low <= ibl: touch = (1, i); break
        if touch is None:
            continue
        side, i0 = touch
        entry = ibh if side < 0 else ibl
        stop = entry - side * 0.25 * rng
        risk = abs(entry - stop)
        pts, exit_ts, exit_px = None, None, None
        for j in range(i0 + 1, len(r)):
            hi, lo = r.high.iloc[j], r.low.iloc[j]
            if side < 0:
                if hi >= stop: pts, exit_px = entry - stop, stop
                elif lo <= mid: pts, exit_px = entry - mid, mid
            else:
                if lo <= stop: pts, exit_px = stop - entry, stop
                elif hi >= mid: pts, exit_px = mid - entry, mid
            if pts is not None:
                exit_ts = r.ts.iloc[j]
                break
        if pts is None:
            cl = r.close.iloc[-1]
            pts = (entry - cl) if side < 0 else (cl - entry)
            exit_ts, exit_px = r.ts.iloc[-1], cl
        out.append(dict(trade_id=f"fade_{d}", day=d, side=side,
                        direction="short" if side < 0 else "long",
                        entry=float(entry), stop=float(stop), target=float(mid),
                        risk=float(risk), fill=r.ts.iloc[i0],
                        mech_pts=float(pts), mech_exit_ts=exit_ts,
                        mech_exit_px=float(exit_px),
                        mech_R=float((pts - FR) / risk)))
    return out


def manage_trade(t, bars, tape, dep, journal) -> dict:
    s, entry, risk = t["side"], t["entry"], t["risk"]
    stop, target = t["stop"], t["target"]
    day = t["day"]
    flatten = pd.Timestamp(f"{day} 15:55", tz=NY)
    path = bars.loc[t["fill"]:flatten + pd.Timedelta(minutes=20)]
    path = path[path.index.strftime("%Y-%m-%d") == day]
    cx_min = t["mech_exit_ts"]

    legs, frac = [], 1.0
    pending: list[tuple] = []
    turns, transcript = 0, []
    partial_done, extended, last_note = False, False, ""
    peak_r, seen_r, last_turn_min = 0.0, set(), None
    r3 = None
    sid = None

    def r_of(px):
        return s * (px - entry) / risk

    def close(fr, px, reason):
        nonlocal frac
        legs.append((fr, px, reason))
        frac = round(frac - fr, 10)

    def settle(reason_final, ts):
        pts = sum(fr * s * (px - entry) for fr, px, _ in legs)
        return {"trade_id": t["trade_id"], "day": day, "direction": t["direction"],
                "risk": risk, "agent_R": round((pts - FR) / risk, 4),
                "mech_R": round(t["mech_R"], 4),
                "exit_reason": reason_final, "exit_ts": str(ts), "turns": turns,
                "partials": sum(1 for _, _, rr in legs if rr == "partial"),
                "extended": extended,
                "held_min": int((ts - t["fill"]).total_seconds() // 60),
                "mfe_R": round(peak_r, 3), "last_note": last_note,
                "legs": [(f, p, rr) for f, p, rr in legs]}

    def send(minute, why, bar):
        nonlocal turns, sid, stop, target, pending, partial_done, last_note, last_turn_min
        if turns >= MAX_TURNS or (last_turn_min is not None and minute <= last_turn_min):
            return
        last = float(bar.close)
        press = bool((r3 or 0) >= 0.5 and r_of(last) > 0 and (peak_r - r_of(last)) <= 0.25)
        state = (f"[{minute.strftime('%H:%M')}] EVENT: {why}\n"
                 f"bar {bar.open:.2f}/{bar.high:.2f}/{bar.low:.2f}/{bar.close:.2f} | "
                 f"R_now {r_of(last):+.2f} peak {peak_r:+.2f} | press_state {press} | "
                 f"open {frac:.2f} | stop {r_of(stop):+.2f}R target "
                 f"{'none' if target is None else f'{r_of(target):+.2f}R'} | "
                 f"{flow_line(tape, minute, s)} | {book_line(dep, minute, s)} | "
                 f"mins_to_session_end {int((flatten - minute).total_seconds() // 60)}")
        if turns == 0:
            state = (f"NEW POSITION {t['direction'].upper()} IB-fade | entry {entry} "
                     f"risk {risk:.2f}pt | engine stop {stop} (-1R, INVIOLATE FLOOR) | "
                     f"mechanical target {target} (+2.0R, the IB mid) | session ends 15:55\n"
                     f"{journal_digest(journal)}\n{TURN_CONTRACT}\n\n" + state)
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
        mins_in = int((minute - t["fill"]).total_seconds() // 60)
        if mins_in == 3:
            r3 = r_of(float(bar.close))
            if r3 <= -0.5:
                why = "DYING CHECK: -0.5R by minute 3 — the 19% cohort. Your call."
            else:
                why = "press check (fill+3m)"
        if turns == 0 and mins_in >= 1:
            why = "position opened — read the tape and set your initial plan"
        for k in (1, 2):
            if fav >= k and k not in seen_r:
                seen_r.add(k)
                why = f"touched +{k}R"
        if (peak_r >= 1.0 and peak_r - r_of(float(bar.close)) >= 0.75
                and peak_r - 0.25 > getattr(send, "_gb_peak", 0.0)):
            send._gb_peak = peak_r
            why = why or f"giving back off the +{peak_r:.1f}R peak"
        if tape is not None:
            w = tape.loc[:minute]
            if len(w) >= 5 and r_of(float(bar.close)) >= 0.5:
                c5 = float(w.delta.tail(5).sum()) * s
                opp = int((np.sign(w.delta.tail(5).to_numpy() * s) < 0).sum())
                if (c5 < 0 or opp >= 4) and (last_turn_min is None
                                             or minute - last_turn_min >= pd.Timedelta(minutes=5)):
                    why = why or "flow turning against a green position"
        if abs(r_of(float(bar.close)) - r_of(stop)) <= 0.3 and mins_in > 3:
            why = why or "price near your stop"
        if cx_min is not None and minute >= cx_min and not extended:
            why = (f"MECHANICAL EXIT NOW: the default spec exits here at "
                   f"{t['mech_exit_px']} ({r_of(t['mech_exit_px']):+.2f}R). "
                   f"Take it (exit_now) or refuse it with a plan.")
            extended = True
        elif extended and (last_turn_min is None
                           or minute - last_turn_min >= pd.Timedelta(minutes=10)):
            why = why or "extended recheck (10m)"
        if int((flatten - minute).total_seconds() // 60) == 30:
            why = why or "30 minutes to EOD flatten"
        if why:
            send(minute, why, bar)
    lastbar = path.iloc[-1] if len(path) else None
    px = float(lastbar.close) if lastbar is not None else entry
    close(frac, px, "early_close")
    return settle("early_close", ix[-1] if len(ix) else t["fill"]) | {"transcript": transcript}


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
            dm = sum(r["mech_R"] for r in rows)
            print(f"agent {da:+.1f}R vs mech {dm:+.1f}R (delta {da - dm:+.1f}R)")
        return

    T = build_trades()
    if a.demo_day:
        T = [t for t in T if t["day"] == a.demo_day]
    else:
        T = [t for t in T if t["day"][:7] in MONTHS]
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    bars = B.assign(ts=ts).set_index("ts").sort_index()[["open", "high", "low", "close"]]
    tape_all = pd.read_parquet(ROOT / "output/fp_minutes.parquet").sort_index()
    dep_all = pd.read_parquet(ROOT / "output/depth_minutes.parquet").sort_index()

    print(f"sample: {len(T)} trades over {len({t['day'] for t in T})} days")
    for t in sorted(T, key=lambda x: x["fill"]):
        if t["trade_id"] in done:
            continue
        day = t["day"]
        journal = journal_rows()
        tape = tape_all[tape_all.index.strftime("%Y-%m-%d") == day]
        tape = tape if len(tape) else None
        dep = dep_all[dep_all.index.strftime("%Y-%m-%d") == day]
        dep = dep if len(dep) else None
        out = manage_trade(t, bars, tape, dep, journal)
        tr = out.pop("transcript")
        (RUNS / "transcripts" / f"{t['trade_id']}.json").write_text(
            json.dumps({"turns": tr}, indent=1))
        with (RUNS / "journal.jsonl").open("a") as f:
            f.write(json.dumps(out) + "\n")
        done.add(t["trade_id"])
        st.write_text(json.dumps({"done": sorted(done)}))
        print(f"  {t['trade_id']}: agent {out['agent_R']:+.2f}R vs mech "
              f"{out['mech_R']:+.2f}R | {out['exit_reason']} | turns {out['turns']}",
              flush=True)


if __name__ == "__main__":
    main()
