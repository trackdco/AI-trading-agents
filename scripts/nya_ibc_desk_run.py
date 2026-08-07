#!/usr/bin/env python3
"""NYA-IBC-01 agent rung — chained desk run on the frozen IB Shelf Fade
(family-file declaration, Angus 2026-08-05). One CLI conversation per
trade, tools disabled, event-driven turns, guardrails driver-enforced.
Baseline = the frozen mechanical walk (band target + t10 scratch) at
180/360 tier sizing. All R in TRUE risk units (stop = -1R).

    python -m scripts.nya_ibc_desk_run --demo-day 2025-06-04
    python -m scripts.nya_ibc_desk_run
    python -m scripts.nya_ibc_desk_run --status
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

from scripts.nya_ivb_desk_run import build_trades as build_A

NY = "America/New_York"
SPEC = ROOT / ".claude/agents/trade-manager-shelf-v1.md"
RUNS = ROOT / "runs/shelf_desk1"
TICK, SLIP, FR = 0.25, 1, 1.0
FIT0, FIT1 = "2025-06-01", "2026-07-31"
MAX_TURNS = 6
CLI_TIMEOUT = 240

TURN_CONTRACT = (
    'Reply with EXACTLY one JSON object, nothing else: {"action":"hold"|"revise"|'
    '"exit_now","stop_r":<num,optional>,"target_r":<num or null,optional>,'
    '"partial_pct":<0-1,optional>,"note":"<=120 chars"}. R units are TRUE risk '
    '(engine stop = -1R). "hold"=no change (mechanical exits execute when due). '
    '"revise": stop_r only TIGHTENS (0=entry); target_r >= 0.3 replaces the target, '
    'null = ride on the stop (extension mode); partial_pct books that fraction of '
    'what is OPEN at next bar. "exit_now" flattens at next bar. Rule-breaking '
    'fields are ignored by the harness.')


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


def journal_rows() -> list[dict]:
    f = RUNS / "journal.jsonl"
    if not f.exists():
        return []
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()]


def journal_digest(rows: list[dict]) -> str:
    if not rows:
        return "journal: no completed trades yet — judge on the tape alone."
    da = sum(r["agent_dollars"] for r in rows)
    dm = sum(r["mech_dollars"] for r in rows)
    lines = [f"journal: {len(rows)} trades | you ${da:+,.0f} vs mech ${dm:+,.0f} "
             f"(delta ${da - dm:+,.0f})"]
    dying = [r for r in rows if r["mech_R"] < -0.1]
    winning = [r for r in rows if r["mech_R"] > 0.1]
    if dying:
        lines.append(f"  defense (mech losers, n{len(dying)}): "
                     f"${sum(r['agent_dollars'] - r['mech_dollars'] for r in dying):+,.0f}")
    if winning:
        lines.append(f"  offense (mech winners, n{len(winning)}): "
                     f"${sum(r['agent_dollars'] - r['mech_dollars'] for r in winning):+,.0f}")
    ext = [r for r in rows if r.get("extended")]
    if ext:
        lines.append(f"  band-exit refusals: {len(ext)}, net vs mech "
                     f"${sum(r['agent_dollars'] - r['mech_dollars'] for r in ext):+,.0f}")
    lines.append("last trades (you vs mech):")
    for r in rows[-5:]:
        lines.append(f"  {r['day']} {r['direction']} {r['tier']}: {r['agent_R']:+.2f}R vs "
                     f"{r['mech_R']:+.2f}R ({r['exit_reason']}; {r.get('last_note','')[:50]})")
    return "\n".join(lines)


def build_shelf_trades():
    """Frozen spec walk on fit span, with conviction tier + mech outcome."""
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    F = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    F = F.reset_index().set_index(["gday", "clock"]).sort_index()
    days = {d: r.sort_values("ts").reset_index(drop=True) for d, r in R.groupby("gday")}
    out = []
    for t in [x for x in build_A() if FIT0 <= x["day"] <= FIT1]:
        r = days.get(t["day"])
        if r is None:
            continue
        k0 = int((r.ts == t["fill"]).idxmax()) if (r.ts == t["fill"]).any() else None
        if k0 is None:
            continue
        side, e, legacy = t["side"], t["entry"], t["risk"]
        stop_d = 0.5 * legacy
        H, L_, C = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy()
        V = r.volume.clip(lower=0).to_numpy().astype(float)
        tp = (H + L_ + C) / 3
        cv = np.maximum(V.cumsum(), 1)
        vwap = (tp * V).cumsum() / cv
        sd = np.sqrt(np.clip((tp ** 2 * V).cumsum() / cv - vwap ** 2, 0, None))
        clk = r.clock.iloc[k0]
        band0 = vwap[k0] - side * sd[k0]
        try:
            fl = F.loc[(t["day"], clk)]
            edelta, ecvd = float(fl.delta) * side, float(fl.cvd) * side
        except KeyError:
            edelta, ecvd = np.nan, np.nan
        score = (int(clk == "10:00") + (int(ecvd < 0) if ecvd == ecvd else 0)
                 + (int(edelta > 0) if edelta == edelta else 0)
                 + int(side * (e - band0) / stop_d >= -1.7874))
        tier = "CONFIRMED" if score >= 3 else "BASE"
        dollars_risk = 360.0 if tier == "CONFIRMED" else 180.0
        pnl, jx, kind = None, len(r) - 1, "eod"
        for m in range(1, len(r) - k0):
            j = k0 + m
            hi, lo, cl = H[j], L_[j], C[j]
            adv = (hi - e) if side < 0 else (e - lo)
            if adv >= stop_d:
                pnl, jx, kind = -stop_d, j, "stop"; break
            band = vwap[j] - side * sd[j]
            if side * (band - e) >= 0.125 * legacy and \
               ((side < 0 and lo <= band) or (side > 0 and hi >= band)):
                pnl, jx, kind = side * (band - e), j, "band"; break
            r_now = (e - cl) if side < 0 else (cl - e)
            if m == 10 and r_now < 0:
                pnl, jx, kind = r_now, j, "scratch"; break
        if pnl is None:
            pnl = side * (C[-1] - e)
        mech_R = (pnl - FR) / stop_d
        out.append(dict(trade_id=f"shelf_{t['day']}", day=t["day"], side=side,
                        direction="short" if side < 0 else "long",
                        entry=float(e), stop=float(e - side * stop_d),
                        risk=float(stop_d), legacy=float(legacy),
                        fill=t["fill"], tier=tier, score=int(score),
                        dollars_risk=dollars_risk,
                        mech_R=float(mech_R), mech_exit_kind=kind,
                        mech_exit_ts=r.ts.iloc[jx],
                        mech_dollars=float(dollars_risk * mech_R)))
    return out


def manage_trade(t, rday, tape, journal) -> dict:
    side, e, risk = t["side"], t["entry"], t["risk"]
    stop = t["stop"]
    day = t["day"]
    flatten = pd.Timestamp(f"{day} 15:55", tz=NY)
    H, L_, C = rday.high.to_numpy(), rday.low.to_numpy(), rday.close.to_numpy()
    V = rday.volume.clip(lower=0).to_numpy().astype(float)
    tp = (H + L_ + C) / 3
    cv = np.maximum(V.cumsum(), 1)
    vwap = (tp * V).cumsum() / cv
    sd = np.sqrt(np.clip((tp ** 2 * V).cumsum() / cv - vwap ** 2, 0, None))
    k0 = int((rday.ts == t["fill"]).idxmax())

    legs, frac = [], 1.0
    pending: list[tuple] = []
    turns, transcript = 0, []
    partial_done, extended, last_note = False, False, ""
    peak_r, last_turn_min = 0.0, None
    target_mode = "band"          # band | fixed | none
    target_fixed = None
    sid = None
    cvd = 0.0

    def r_of(px):
        return side * (px - e) / risk

    def close(fr, px, reason):
        nonlocal frac
        legs.append((fr, px, reason))
        frac = round(frac - fr, 10)

    def settle(reason, ts_):
        pts = sum(fr * side * (px - e) for fr, px, _ in legs)
        aR = (pts - FR) / risk
        return {"trade_id": t["trade_id"], "day": day, "direction": t["direction"],
                "tier": t["tier"], "risk": risk,
                "agent_R": round(aR, 4), "agent_dollars": round(t["dollars_risk"] * aR, 2),
                "mech_R": round(t["mech_R"], 4), "mech_dollars": round(t["mech_dollars"], 2),
                "exit_reason": reason, "exit_ts": str(ts_), "turns": turns,
                "partials": sum(1 for _, _, rr in legs if rr == "partial"),
                "extended": extended, "mfe_R": round(peak_r, 3),
                "last_note": last_note, "legs": [(f, p, rr) for f, p, rr in legs]}

    def send(minute, why, bar, band_now):
        nonlocal turns, sid, stop, target_mode, target_fixed, pending, partial_done, \
            last_note, last_turn_min
        if turns >= MAX_TURNS or (last_turn_min is not None and minute <= last_turn_min):
            return
        last = float(bar.close)
        state = (f"[{minute.strftime('%H:%M')}] EVENT: {why}\n"
                 f"bar {bar.open:.2f}/{bar.high:.2f}/{bar.low:.2f}/{bar.close:.2f} | "
                 f"R_now {r_of(last):+.2f} peak {peak_r:+.2f} | open {frac:.2f} | "
                 f"stop {r_of(stop):+.2f}R | target "
                 f"{'developing band ' + format(r_of(band_now), '+.2f') + 'R' if target_mode == 'band' else (('fixed ' + format(r_of(target_fixed), '+.2f') + 'R') if target_mode == 'fixed' else 'NONE (riding stop)')} | "
                 f"cvd_since_entry {cvd:+.0f} | "
                 f"mins_to_EOD {int((flatten - minute).total_seconds() // 60)}")
        if turns == 0:
            state = (f"NEW POSITION {t['direction'].upper()} shelf-fade | tier {t['tier']} "
                     f"(${t['dollars_risk']:.0f} risk, fixed) | entry {e} risk {risk:.2f}pt "
                     f"| engine stop {stop} (-1R, INVIOLATE) | mechanical target = the "
                     f"developing near band | mechanical scratch at t+10 if red | "
                     f"session ends 15:55\n{journal_digest(journal)}\n{TURN_CONTRACT}\n\n"
                     + state)
        txt, sid2 = call_claude(state, sid)
        sid = sid2 or sid
        rep = parse_reply(txt)
        turns += 1
        last_turn_min = minute
        transcript.append({"minute": str(minute), "why": why, "sent": state, "reply": txt})
        last_note = str(rep.get("note", ""))[:120]
        if rep["action"] == "exit_now":
            pending.append(("exit", None))
            return
        if rep["action"] != "revise":
            return
        if rep.get("stop_r") is not None:
            try:
                cand = e + side * float(rep["stop_r"]) * risk
                if side * (cand - stop) > 0:
                    stop = round(round(cand / TICK) * TICK, 10)
            except Exception:
                pass
        if "target_r" in rep:
            tr = rep.get("target_r")
            if tr is None:
                target_mode = "none"
            else:
                try:
                    tr = float(tr)
                    if tr >= 0.3:
                        target_mode, target_fixed = "fixed", \
                            round(round((e + side * tr * risk) / TICK) * TICK, 10)
                except Exception:
                    pass
        if rep.get("partial_pct") is not None:
            try:
                p = float(rep["partial_pct"])
                if 0.0 < p < 1.0:
                    pending.append(("partial", p))
            except Exception:
                pass

    for m in range(1, len(rday) - k0):
        j = k0 + m
        minute = rday.ts.iloc[j]
        bar = rday.iloc[j]
        band_now = vwap[j] - side * sd[j]
        if tape is not None:
            try:
                cvd += float(tape.loc[rday.clock.iloc[j], "delta"]) * side
            except KeyError:
                pass
        if minute >= flatten:
            close(frac, float(bar.open) - side * SLIP * TICK, "eod")
            return settle("eod", minute) | {"transcript": transcript}
        for kind, val in pending:
            px = float(bar.open) - side * SLIP * TICK
            if kind == "exit" and frac > 0:
                close(frac, px, "agent_exit")
            elif kind == "partial" and frac > 0:
                close(round(frac * val, 10), px, "partial")
                partial_done = True
        pending = []
        if frac <= 0:
            return settle("agent_exit", minute) | {"transcript": transcript}
        if (side < 0 and bar.high >= stop) or (side > 0 and bar.low <= stop):
            px = (min(stop, float(bar.open)) if side > 0 else max(stop, float(bar.open)))
            close(frac, px - side * SLIP * TICK, "stop")
            return settle("stop", minute) | {"transcript": transcript}
        tgt_now = band_now if target_mode == "band" else target_fixed
        tgt_valid = (target_mode == "band" and side * (band_now - e) >= 0.25 * risk) or \
                    (target_mode == "fixed")
        if target_mode != "none" and tgt_valid and tgt_now is not None and \
           ((side < 0 and bar.low <= tgt_now) or (side > 0 and bar.high >= tgt_now)):
            # mechanical/fixed target touched
            if target_mode == "fixed" or extended:
                close(frac, tgt_now, "target")
                return settle("target", minute) | {"transcript": transcript}
            # band touch = decision point BEFORE executing (one turn), then execute
            why = (f"BAND TOUCH: the mechanical exit is here at {band_now:.2f} "
                   f"({r_of(band_now):+.2f}R). Take it (hold/exit_now) or refuse with a "
                   f"plan (revise: null target to ride, or fixed target + tighter stop).")
            prev_mode = target_mode
            send(minute, why, bar, band_now)
            extended = True
            if target_mode == prev_mode:      # no revision -> mechanical exit executes
                close(frac, tgt_now, "band")
                return settle("band", minute) | {"transcript": transcript}
            continue
        fav = r_of(float(bar.high) if side > 0 else float(bar.low))
        peak_r = max(peak_r, fav)
        why = None
        if turns == 0 and m >= 1:
            why = "position opened — read it and set your plan"
        elif m == 2:
            why = "t+2 check: the decisive minute on this clock"
        elif m == 10:
            r_now = r_of(float(bar.close))
            if r_now < 0:
                why = (f"MECHANICAL SCRATCH NOW: t+10 and red ({r_now:+.2f}R). "
                       f"Take it (hold/exit_now) or refuse with a plan.")
                prev = (stop, target_mode)
                send(minute, why, bar, band_now)
                if (stop, target_mode) == prev:
                    close(frac, float(bar.close), "scratch")
                    return settle("scratch", minute) | {"transcript": transcript}
                extended = True
                continue
        elif extended and (last_turn_min is None or
                           minute - last_turn_min >= pd.Timedelta(minutes=10)):
            why = "extended recheck (10m)"
        if abs(r_of(float(bar.close)) - r_of(stop)) <= 0.3 and m > 2:
            why = why or "price near your stop"
        if why:
            send(minute, why, bar, band_now)
    close(frac, float(rday.close.iloc[-1]), "early_close")
    return settle("early_close", rday.ts.iloc[-1]) | {"transcript": transcript}


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
            da = sum(r["agent_dollars"] for r in rows)
            dm = sum(r["mech_dollars"] for r in rows)
            print(f"agent ${da:+,.0f} vs mech ${dm:+,.0f} (delta ${da - dm:+,.0f})")
        return

    T = build_shelf_trades()
    if a.demo_day:
        T = [t for t in T if t["day"] == a.demo_day]
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    days = {d: r.sort_values("ts").reset_index(drop=True) for d, r in R.groupby("gday")}
    F = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    F = F.reset_index().set_index(["gday", "clock"]).sort_index()

    print(f"sample: {len(T)} trades")
    for t in sorted(T, key=lambda x: x["fill"]):
        if t["trade_id"] in done:
            continue
        rday = days[t["day"]]
        try:
            tape = F.loc[t["day"]]
        except KeyError:
            tape = None
        out = manage_trade(t, rday, tape, journal_rows())
        tr = out.pop("transcript")
        (RUNS / "transcripts" / f"{t['trade_id']}.json").write_text(
            json.dumps({"turns": tr}, indent=1))
        with (RUNS / "journal.jsonl").open("a") as f:
            f.write(json.dumps(out) + "\n")
        done.add(t["trade_id"])
        st.write_text(json.dumps({"done": sorted(done)}))
        print(f"  {t['trade_id']} [{t['tier']}]: agent {out['agent_R']:+.2f}R "
              f"(${out['agent_dollars']:+,.0f}) vs mech {out['mech_R']:+.2f}R "
              f"(${out['mech_dollars']:+,.0f}) | {out['exit_reason']} | turns {out['turns']}",
              flush=True)


if __name__ == "__main__":
    main()
