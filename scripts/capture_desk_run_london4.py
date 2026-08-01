#!/usr/bin/env python3
"""RUN 4 — surgical fix, not a redesign (see the correction below; the first draft of
this file over-generalized and was caught by its own required single-day validation).

v2/v3 gave the agent a peak-R-based lockout (no protective actions past +2R peak,
target EXTENSION still allowed) and asked it to voluntarily accept or refuse V1's own
mechanical exit when offered. Run 3's graded result: agent +80.58R vs V1 +99.01R
(delta -18.43R, 129 paired trades). Decomposing WHERE that came from (replaying run
3's own actual per-trade decisions, not a new run):
  mirrored V1 (no material deviation, n=70): agent +80.53R vs V1 +81.64R (delta -1.11R)
  exited EARLY, before V1's own exit (n=5):  agent  -0.45R vs V1  -1.68R (delta +1.23R)
  held PAST / refused V1's offered exit (n=54): agent +0.50R vs V1 +19.05R (delta -18.55R)
100% of the deficit is the third bucket, and it traces to the ASK-A-CHOICE event
specifically -- the +2R lockout itself was never implicated (defense stayed
+17.8R-shaped across every prior run, untouched by this decomposition).

FIRST DRAFT'S MISTAKE (kept here rather than silently corrected, matching this
project's retraction convention): it over-generalized "remove the choice" into
"remove the lockout too, give full authority throughout." Validated on demo day
2026-03-31 before launching the full chain, per this branch's own discipline --
and failed immediately: with the lockout removed, the agent rode a trade to +3.35R
peak, then proactively tightened its stop "to lock in the gain," got stopped at +2R,
and missed V1's real +10.37R target entirely -- reproducing, exactly, the mechanism
run 1 originally showed cost -27.8R concentrated in big winners (why the lockout was
built in the first place). The replay above only licenses removing the ASK; it never
licensed removing the LOCK, and conflating the two was wrong.

v4, corrected: the +2R peak lockout is UNCHANGED from v3 -- same threshold, same
protective-actions-disabled-above-it, same target-extension-only allowance while
locked. It is not touched because it was never broken. The ONLY change from v3: the
"MECHANICAL EXIT NOW: take it or refuse it" turn is replaced by a silent,
HARNESS-ENFORCED mirror-close -- once V1's own realized exit moment
(t["v1_exit_ts"]) arrives, whatever fraction is still open closes right there, at a
price that reconstructs V1's own realized R exactly (no LLM call, no choice, nothing
to refuse, regardless of lock state). This is the single surgical fix the replay
evidence actually supports; conviction context (A+/mid/neither) is unchanged from
run 3.

Population, execution semantics, guardrails, causality discipline -- ALL unchanged
from run 3 / docs/PLAN-agents-capture-london.md. See scripts/capture_desk_run_london3.py
for the shared design notes (dynamic one-at-a-time re-walk, PLAN §4b, etc.) — not
repeated here.

    python -m scripts.capture_desk_run_london4 --demo-day 2025-06-02   # one day, stop
    python -m scripts.capture_desk_run_london4                        # the full chain
    python -m scripts.capture_desk_run_london4 --status
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
SPEC = ROOT / ".claude/agents/trade-manager-london-v4.md"
RUNS = ROOT / "runs/desk_london4"
TICK, SLIP, COMMISSION, PV = 0.25, 1, 5.0, 20.0
MAX_TURNS = 10
CLI_TIMEOUT = 240
MASTER = "data/reference/nq_1m_master.parquet"
# UNCHANGED from v2/v3 (docs/REPORT-desk-london-1.md finding): once a trade's peak
# reaches this many R, no more tightening, partials, or exit_now -- only hold, or a
# target_r that EXTENDS the current target. Never implicated in run 3's -18.43R
# deficit (see module docstring); kept exactly as-is.
LOCKOUT_PEAK_R = 2.0

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
    mirrored = sum(1 for r in rows if r.get("exit_reason") == "mech_exit_mirror")
    parts = sum(1 for r in rows if r.get("partials"))
    lines = [f"journal: {n} trades managed ({len(paired)} paired vs V1) | your total "
             f"{da:+.1f}R vs V1 {dv:+.1f}R on paired trades (delta "
             f"{sum(r['agent_R'] - r['v1_R'] for r in paired):+.1f}R) | mechanically "
             f"mirrored to V1's own exit (you hadn't fully cut yet) {mirrored}x | "
             f"partials {parts}x"]
    for era in ("2025", "2026"):
        g = [r for r in rows if r["day"].startswith(era)]
        if g:
            gp = [r for r in g if r.get("v1_R") is not None]
            lines.append(f"  {era}: n{len(g)} you {sum(r['agent_R'] for r in g):+.1f}R"
                         + (f" vs V1 {sum(r['v1_R'] for r in gp):+.1f}R" if gp else ""))
    for grade in ("A+", "mid", "neither"):
        g = [r for r in paired if r.get("grade") == grade]
        if g:
            lines.append(f"  {grade} (n{len(g)}, size {g[0].get('weight', 1.0):.1f}x): "
                         f"you {sum(r['agent_R'] for r in g):+.1f}R vs V1 "
                         f"{sum(r['v1_R'] for r in g):+.1f}R (delta "
                         f"{sum(r['agent_R'] - r['v1_R'] for r in g):+.1f}R)")
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
    not re-derived here. IDENTICAL to run 3's population/grade logic."""
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

    # conviction grade -- IDENTICAL definition to the validated V1 conviction ladder
    # (A+ 2.0x / mid 1.0x / neither 0.5x), computed here so the agent's briefing can
    # show it. Purely informational for the agent; the walk mechanics (R produced) are
    # unaffected -- dollar conversion at grading time applies the weight.
    b_aplus = (b.pattern == "B2") & (b.W == 1) & (b.FAR == 1)
    b_neither = (b.pattern != "B2") & ~((b.W == 1) & (b.FAR == 1))
    grade = np.where(b_aplus, "A+", np.where(b_neither, "neither", "mid"))
    weight = np.where(b_aplus, 2.0, np.where(b_neither, 0.5, 1.0))

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
            v1_exit_reason=str(t.exit_reason),
            grade=str(grade[i]), weight=float(weight[i])))
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
    partial_done, last_note = False, ""
    peak_r, seen_r, last_turn_min = 0.0, set(), None
    r3 = None
    sid = None
    cx_min = t["v1_exit_ts"]

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
                "grade": t["grade"], "weight": t["weight"],
                "agent_R": round(net / (risk_pts * PV), 4), "agent_dollars": round(net, 2),
                "v1_R": t["v1_R"], "v1_dollars": t["v1_dollars"],
                "exit_reason": reason_final, "exit_ts": str(ts), "turns": turns,
                "partials": sum(1 for _, _, r in legs if r == "partial"),
                "held_min": int((ts - t["fill_ts"]).total_seconds() // 60),
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
        locked = peak_r >= LOCKOUT_PEAK_R
        state = (f"[{minute.strftime('%H:%M')}] EVENT: {why}\n"
                 f"bar {bar.open:.2f}/{bar.high:.2f}/{bar.low:.2f}/{bar.close:.2f} | "
                 f"R_now {r_of(last):+.2f} peak {peak_r:+.2f} | pressing {press} | "
                 f"open {frac:.2f} | stop {r_of(stop):+.2f}R target "
                 f"{'none' if target is None else f'{r_of(target):+.2f}R'} | "
                 f"{flow_line(tape, minute, s)} | {book_line(dep, minute, last, s)} | "
                 f"mins_to_session_end {int((flatten - minute).total_seconds() // 60)}"
                 + (f"\nLOCKED: peak has reached +{peak_r:.1f}R (>= {LOCKOUT_PEAK_R:.0f}R). "
                    "Protective actions (stop tighten, partial, exit_now) are DISABLED by "
                    "the harness for this trade from here on -- your reply may only hold "
                    "or extend target_r further. Don't propose protection; it will be "
                    "silently ignored." if locked else ""))
        if turns == 0:
            state = (f"NEW POSITION {t['direction'].upper()} | entry {entry} "
                     f"risk {risk_pts:.2f}pt | engine stop {stop} (-1R, INVIOLATE FLOOR) | "
                     f"structural target {target} "
                     f"({'n/a' if target is None else f'{r_of(target):+.1f}R'}) | "
                     f"pattern {t.get('pattern', '?')} | bucket {t['bucket']} | "
                     f"CONVICTION GRADE {t['grade']} (size {t['weight']:.2f}x base) | "
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
            if locked:
                last_note = (last_note + " [HARNESS: exit_now blocked, locked >=2R]")[:160]
            else:
                pending.append(("exit", None))
            return
        if act != "revise":
            return
        if rep.get("stop_r") is not None and not locked:
            try:
                cand = entry + s * float(rep["stop_r"]) * risk_pts
                if s * (cand - stop) > 0:            # tighten-only, always
                    stop = round(round(cand / TICK) * TICK, 10)
            except Exception:
                pass
        if "target_r" in rep:
            tr = rep.get("target_r")
            if tr is None:
                if not locked:
                    target = None
            else:
                try:
                    tr = float(tr)
                    floor = 0.1 if partial_done else 2.0
                    # cur_r = inf when target is already None: a target_r=null trap
                    # existed here in v2 (documented, never fixed in code) because no
                    # finite tr could ever "extend" past infinity, permanently
                    # stranding the trade without a target. In v4 this is structurally
                    # moot: the mirror-close below is a hard backstop regardless of
                    # target state, so a stranded-without-a-target trade still closes
                    # correctly at V1's own exit moment either way.
                    cur_r = r_of(target) if target is not None else float("inf")
                    if locked:
                        if tr > cur_r:          # only a genuine EXTENSION passes while locked
                            target = round(round((entry + s * tr * risk_pts) / TICK) * TICK, 10)
                    elif tr >= floor:
                        target = round(round((entry + s * tr * risk_pts) / TICK) * TICK, 10)
                except Exception:
                    pass
        if rep.get("partial_pct") is not None and not locked:
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
        # HARNESS-ENFORCED (run 4's core change, not spec-guided, see module
        # docstring): once V1's own realized exit moment arrives, whatever fraction
        # is still open closes HERE, at V1's own realized price -- no hold, no
        # refusal, no target-extension channel past this line. The mirror price is
        # solved so that, when frac is still 1.0 (no earlier partial/tighten leg),
        # the resulting agent_R is EXACTLY t["v1_R"] (commission included once, not
        # double-counted): pts = v1_R*risk_pts + COMMISSION/PV  =>  net = pts*PV -
        # COMMISSION = v1_R*risk_pts*PV.
        if cx_min is not None and minute >= cx_min:
            v1_price = entry + s * (t["v1_R"] * risk_pts + COMMISSION / PV)
            close(frac, v1_price, "mech_exit_mirror")
            return settle("mech_exit_mirror", minute) | {"transcript": transcript}
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
        if cx_min is not None:
            mins_to_cx = int((cx_min - minute).total_seconds() // 60)
            if mins_to_cx == 10:
                why = why or ("10 minutes to the mechanical exit point -- last call "
                              "for early defense, this position auto-closes to V1's "
                              "own result once that moment arrives")
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
