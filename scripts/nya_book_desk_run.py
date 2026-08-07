#!/usr/bin/env python3
"""NYA-IBC-01 book-selector run — one conversation per day, two engines,
selection decisions only (management mechanical both sides). Baselines B0
(take-all, net) and B1 (canon precedence) computed alongside.

    python -m scripts.nya_book_desk_run --demo-day 2025-06-04
    python -m scripts.nya_book_desk_run
    python -m scripts.nya_book_desk_run --status
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

from scripts.nya_ibc_desk_run import build_shelf_trades

NY = "America/New_York"
SPEC = ROOT / ".claude/agents/book-selector-v1.md"
RUNS = ROOT / "runs/book_desk1"
CLI_TIMEOUT = 240
MAX_TURNS = 10


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


def parse_reply(text: str, allowed: tuple) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"action": allowed[0], "note": "unparseable -> default"}
    try:
        d = json.loads(m.group(0))
    except Exception:
        return {"action": allowed[0], "note": "bad json -> default"}
    if d.get("action") not in allowed:
        d["action"] = allowed[0]
    return d


def journal_rows() -> list[dict]:
    f = RUNS / "journal.jsonl"
    if not f.exists():
        return []
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()]


def digest(rows: list[dict]) -> str:
    if not rows:
        return "journal: day one — no history yet."
    a = sum(r["agent_dollars"] for r in rows)
    b0 = sum(r["b0_dollars"] for r in rows)
    b1 = sum(r["b1_dollars"] for r in rows)
    sk = sum(r["skips"] for r in rows)
    lines = [f"journal: {len(rows)} days | you ${a:+,.0f} vs B0(take-all) ${b0:+,.0f} "
             f"vs B1(canon-precedence) ${b1:+,.0f} | skips {sk}"]
    skipped = [r for r in rows if r["skips"]]
    if skipped:
        d = sum(r["skip_value"] for r in skipped)
        lines.append(f"  your skips forfeited ${-d:+,.0f} of mechanical P&L "
                     f"({'good skips overall' if d < 0 else 'SKIPS ARE COSTING YOU'})")
    for r in rows[-4:]:
        lines.append(f"  {r['day']}: you ${r['agent_dollars']:+,.0f} vs B0 "
                     f"${r['b0_dollars']:+,.0f} ({r['n_events']} signals, {r['skips']} skips)")
    return "\n".join(lines)


def build_days():
    C = pd.read_parquet(ROOT / "output/aikido_cr_fit.parquet")
    if "cr_suppressed" in C.columns:
        C = C[~C.cr_suppressed]
    cts = pd.to_datetime(C.ts, utc=True).dt.tz_convert(NY)
    cex = pd.to_datetime(C.cr_exit_ts, utc=True).dt.tz_convert(NY)
    canon = pd.DataFrame({"fill": cts, "exit": cex,
                          "dir": C.direction.astype(str) if "direction" in C.columns else "?",
                          "dollars": C.cr_dollars_1lot.astype(float)})
    canon["day"] = canon.fill.dt.strftime("%Y-%m-%d")
    shelf = build_shelf_trades()
    days = {}
    for t in shelf:
        d = t["day"]
        tier_dollars = 300.0 if t["tier"] == "CONFIRMED" else 200.0
        ev = dict(engine="SHELF", fill=t["fill"], exit=t["mech_exit_ts"],
                  dir=t["direction"], tier=t["tier"],
                  dollars=tier_dollars * t["mech_R"],
                  desc=f"SHELF {t['direction'].upper()} [{t['tier']}] risk "
                       f"${tier_dollars:.0f} @ {t['fill'].strftime('%H:%M')}")
        days.setdefault(d, []).append(ev)
    for _, r in canon.iterrows():
        if r.day in days:
            days[r.day].append(dict(engine="CANON", fill=r.fill, exit=r.exit,
                                    dir=r["dir"], tier="-", dollars=float(r.dollars),
                                    desc=f"CANON {str(r['dir']).upper()} @ "
                                         f"{r.fill.strftime('%H:%M')}"))
    for d in days:
        days[d].sort(key=lambda e: e["fill"])
    return days


def run_day(d, events, journal):
    sid = None
    turns, transcript = 0, []
    open_pos = []          # (engine, dir, exit_ts, dollars, taken_index)
    agent_events = []      # (event, decision)
    for i, ev in enumerate(events):
        open_pos = [p for p in open_pos if p[2] > ev["fill"]]
        conflict = next((p for p in open_pos if p[1] != ev["dir"]), None)
        if turns >= MAX_TURNS:
            agent_events.append((ev, "take" if conflict is None else "net"))
            open_pos.append((ev["engine"], ev["dir"], ev["exit"], ev["dollars"], i))
            continue
        book = ", ".join(f"{p[0]} {p[1]} (open)" for p in open_pos) or "flat"
        if conflict is None:
            prompt = (f"[{ev['fill'].strftime('%H:%M')}] SIGNAL: {ev['desc']}\n"
                      f"book: {book}\nDecision: take or skip.")
            allowed = ("take", "skip")
        else:
            prompt = (f"[{ev['fill'].strftime('%H:%M')}] CONFLICT: {ev['desc']} fires "
                      f"OPPOSITE to your open {conflict[0]} {conflict[1]}.\n"
                      f"book: {book}\nDecision: net / skip_new / cut_take.")
            allowed = ("net", "skip_new", "cut_take")
        if turns == 0:
            prompt = (f"DESK OPEN {d}. Two engines live; mechanical specs fixed; you "
                      f"choose what the book takes.\n{digest(journal)}\n\n" + prompt)
        txt, sid = call_claude(prompt, sid)
        rep = parse_reply(txt, allowed)
        turns += 1
        transcript.append({"event": ev["desc"], "sent": prompt, "reply": txt})
        act = rep["action"]
        agent_events.append((ev, act))
        if act in ("take", "net", "cut_take"):
            if act == "cut_take" and conflict is not None:
                # cutting early: approximate cut cost as 0 (flat at market ~ entry
                # of new signal); the cut position's remaining P&L is forfeited.
                open_pos = [p for p in open_pos if p is not conflict]
                agent_events.append(({"engine": conflict[0], "desc": "CUT", "dollars":
                                      -conflict[3]}, "cut_adjust"))
            open_pos.append((ev["engine"], ev["dir"], ev["exit"], ev["dollars"], i))

    # settle: agent book = sum of taken events' mechanical dollars, with cut
    # adjustments (a cut forfeits the position's mechanical P&L from that point;
    # conservative approximation: forfeit its ENTIRE mechanical P&L and log it)
    agent_d, skips, skip_value = 0.0, 0, 0.0
    for ev, act in agent_events:
        if act in ("take", "net"):
            agent_d += ev["dollars"]
        elif act == "cut_adjust":
            agent_d += ev["dollars"]        # negative of the cut position's P&L
        elif act in ("skip", "skip_new"):
            skips += 1
            skip_value += ev["dollars"]
    b0 = sum(e["dollars"] for e in events)
    b1 = 0.0
    open_b1 = []
    for e in events:
        open_b1 = [p for p in open_b1 if p[1] > e["fill"]]
        if e["engine"] == "SHELF" and any(pd_ != e["dir"] for pd_, _ in open_b1):
            continue                        # canon precedence: shelf skips
        b1 += e["dollars"]
        open_b1.append((e["dir"], e["exit"]))
    return {"day": d, "n_events": len(events), "turns": turns,
            "agent_dollars": round(agent_d, 2), "b0_dollars": round(b0, 2),
            "b1_dollars": round(b1, 2), "skips": skips,
            "skip_value": round(skip_value, 2),
            "decisions": [(e.get("desc", "?"), a) for e, a in agent_events]}, transcript


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
        print(f"{len(done)} days done")
        if rows:
            print(f"agent ${sum(r['agent_dollars'] for r in rows):+,.0f} vs "
                  f"B0 ${sum(r['b0_dollars'] for r in rows):+,.0f} vs "
                  f"B1 ${sum(r['b1_dollars'] for r in rows):+,.0f}")
        return
    days = build_days()
    sel = sorted(days)
    if a.demo_day:
        sel = [a.demo_day]
    print(f"book run: {len(sel)} days")
    for d in sel:
        if d in done:
            continue
        out, tr = run_day(d, days[d], journal_rows())
        (RUNS / "transcripts" / f"{d}.json").write_text(json.dumps({"turns": tr}, indent=1))
        with (RUNS / "journal.jsonl").open("a") as f:
            f.write(json.dumps(out) + "\n")
        done.add(d)
        st.write_text(json.dumps({"done": sorted(done)}))
        print(f"  {d}: agent ${out['agent_dollars']:+,.0f} vs B0 ${out['b0_dollars']:+,.0f} "
              f"vs B1 ${out['b1_dollars']:+,.0f} ({out['n_events']} signals, "
              f"{out['skips']} skips)", flush=True)


if __name__ == "__main__":
    main()
