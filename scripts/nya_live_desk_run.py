#!/usr/bin/env python3
"""THE LIVE-SIM DESK RUN — ANGUS's mandate, 2026-08-05 (family-file declaration):

  "i want to run the agents from the beginning and simulate as if they were trading
   live with the knowledge of the 2 strategies. they dont have any hindsight, they
   are placed there and make their own decisions etc etc."

One CONVERSATION per session day, chronological from 2025-06-02, ALL fit-span days
with a canon or shelf signal. The agent's knowledge = the two shipped specs (in the
system prompt) and its own journal — NO fit-span diagnostic briefings (that material
is the hindsight being removed). It decides participation (take/pass at every fill),
management of every taken position (event-driven turns, guardrails driver-enforced),
and cross-engine conflicts (pass / net / close_other). Canon-vs-canon
close-and-reverse stays engine law. Defaults are the machine: malformed replies,
turn-cap overflow, and unrefused mechanical-exit events execute the mechanical book —
a fully passive agent reproduces B0.

BASELINES: B0 = both books fully mechanical, net conflicts (canon two-rule dollars,
shelf frozen walk at 200/300). B1 = canon precedence (shelf stands aside while an
opposite canon position is open). Passes are logged with forfeited mechanical P&L
and fed back through the journal digest AFTER resolution (causal).

CAUSALITY: every prompt is built from bars/tape/depth strictly <= the turn's minute;
per-day transcripts are the audit trail. Executions next-bar, engine conventions.

    python -m scripts.nya_live_desk_run --demo-day 2025-06-04
    python -m scripts.nya_live_desk_run
    python -m scripts.nya_live_desk_run --status
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

from scripts.capture_replay import (load_trades, load_bars_ny, sgn,  # noqa: E402
                                    implied_partial)
from scripts.nya_ibc_desk_run import build_shelf_trades  # noqa: E402

NY = "America/New_York"
SPEC = ROOT / ".claude/agents/live-desk-v1.md"
RUNS = ROOT / "runs/live_desk1"
TICK, SLIP, PV, COMMISSION, SFR = 0.25, 1, 20.0, 5.0, 1.0
SHELF_TIER = {"CONFIRMED": 300.0, "BASE": 200.0}
# CADENCE (Angus, two rulings): minute-by-minute intraday adaptation WHERE THE
# MONEY IS — one call EVERY MINUTE a position is open; while flat in the entry
# window (08:00-10:30, the only window either engine can enter) a 5-minute pulse
# plus every signal minute; flat after 10:30 = off the desk.
#
# CHAINING (Angus: "what if we did every 2 trading weeks for higher frequency...
# the closer we can get to a day the better, just dont want to wait a million
# years"): days inside a BATCH run concurrently and the journal chains
# batch-to-batch, so batch size IS the learning granularity. Wall clock is
# 254/min(BATCH, WORKERS) waves — so a finer batch only costs time if it drops
# below the worker count. BATCH 10 with WORKERS 10 gives fortnightly learning at
# 26 waves (~8h), FASTER than the old 21-day/6-worker setup (43 waves, ~14h).
# Going below 10 does cost: 5-day batches cap parallelism at 5 (~16h), daily
# chaining is fully sequential (~80h).
BATCH_DAYS = 10
# Angus: "it takes what a dozen trades and draws the conclusion, thats way too
# inconclusive... it should be trading like that for the first couple months
# minimum and using the journal as documentation rather than ruling, just like i
# wouldnt take 5 trades, see one part underperform and just burn it."
SAMPLE_FLOOR = 40
MAX_TURNS_DAY = 600
CLI_TIMEOUT = 240
WORKERS = 10
MODEL = "sonnet"        # Angus: the desk runs on Sonnet — don't burn the plan

DEPTH_DIRS = ["data/reference/depth_2025", "data/reference/depth_2026",
              "data/reference/depth_apr2026", "data/reference/depth_2023_24"]

TURN_CONTRACT = (
    'Reply with EXACTLY one JSON object, nothing else. Signal events: {"action":'
    '"take"|"pass","close_other":"<pos_id>,optional","note":"<=120"}. Every other '
    'minute: {"action":"hold"|"revise"|"exit_now","pos":"<pos_id, required if more '
    'than one position open>","stop_r":<num,opt>,"target_r":<num or null,opt>,'
    '"partial_pct":<0-1,opt>,"close_other":"<pos_id>,opt","note":"<=120"}. R = TRUE '
    'risk (engine stop = -1R, 0 = entry). stop_r only TIGHTENS. canon target_r >= '
    '2.0 until a partial then >= 0.1; shelf target_r >= 0.3; null = ride on the '
    'stop. MECHANICAL EXIT events: "hold" TAKES the exit; refusing = "revise" with '
    'a plan. Rule-breaking fields are ignored; malformed replies = the mechanical '
    'book. Keep notes terse; silence-equivalent is {"action":"hold"}.')


# ------------------------------------------------------------------ CLI conversation

def call_claude(prompt: str, session: str | None) -> tuple[str, str | None]:
    cmd = ["claude", "-p", "--model", MODEL, "--system-prompt-file", str(SPEC),
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


def parse_reply(text: str, signal: bool) -> dict:
    default = {"action": "take" if signal else "hold", "note": "malformed -> machine"}
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return default
    try:
        d = json.loads(m.group(0))
    except Exception:
        return default
    ok = ("take", "pass") if signal else ("hold", "revise", "exit_now")
    if d.get("action") not in ok:
        d["action"] = default["action"]
    return d


# ------------------------------------------------------------------ market views

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
    rows = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    return sorted(rows, key=lambda r: r["day"])   # parallel writes land out of order


def journal_digest(rows: list[dict]) -> str:
    if not rows:
        return ("journal: DAY ONE. You have never traded these strategies live — "
                "only the rulebooks and validation numbers you were hired with.")
    a = sum(r["agent_dollars"] for r in rows)
    b0 = sum(r["b0_dollars"] for r in rows)
    b1 = sum(r["b1_dollars"] for r in rows)
    lines = [f"journal: {len(rows)} days | you ${a:+,.0f} vs B0(machine) ${b0:+,.0f} "
             f"vs B1(canon-precedence) ${b1:+,.0f}"]
    for eng in ("CANON", "SHELF"):
        tr = [t for r in rows for t in r["trades"] if t["engine"] == eng]
        ps = [p for r in rows for p in r["passes"] if p["engine"] == eng]
        if not tr and not ps:
            continue
        da = sum(t["agent_dollars"] for t in tr)
        dm = sum(t["mech_dollars"] for t in tr)
        fired = len(tr) + len(ps)
        lines.append(
            f"  {eng}: {fired} signals, you took {len(tr)} / passed {len(ps)} "
            f"({len(ps) / fired:.0%})")
        lines.append(f"    the ENGINE earned ${dm:+,.0f} on the ones you took — that is "
                     f"the strategy's own record, and it is not in question")
        verdict = ("LOGBOOK ONLY — n is far too small to mean anything yet"
                   if len(tr) < SAMPLE_FLOOR else "sample is getting usable")
        lines.append(f"    YOUR HANDLING of them: ${da:+,.0f} (${da - dm:+,.0f} vs the "
                     f"engine) on n={len(tr)} — {verdict}")
    lines.append(f"  SAMPLE DISCIPLINE: both engines were certified on hundreds of "
                 f"trades. Under ~{SAMPLE_FLOOR} of your own trades on an engine you "
                 f"have NO basis to judge it — that is a logbook entry, not a verdict. "
                 f"A run of bad handling means manage differently; it never means stop "
                 f"taking that engine's signals. Pass a signal only for what the TAPE "
                 f"and your BOOK say right now (flow against it, a conflicting "
                 f"position), never because your record on that engine looks thin.")
    ps = [p for r in rows for p in r["passes"]]
    if ps:
        forf = sum(p["mech_dollars"] for p in ps)
        lines.append(f"  passes: {len(ps)}, forfeited mechanical P&L ${forf:+,.0f} "
                     f"({'your passes are SAVING money' if forf < 0 else 'your passes are COSTING money'})")
    cf = [c for r in rows for c in r.get("conflicts", [])]
    if cf:
        lines.append(f"  conflicts faced: {len(cf)} | " +
                     "; ".join(f"{c['day']}:{c['choice']}" for c in cf[-3:]))
    # conditioned learning gauges (canon run-1 convention): when you cut early
    # in state X, what usually happened next — read by LATER months only.
    tr_all = [t for r in rows for t in r["trades"]]
    cuts = [t for t in tr_all if t["exit_reason"] == "agent_exit"
            and t.get("left_peak_R") is not None]
    if cuts:
        for label, sel in (
                ("flow WITH you", [t for t in cuts if t.get("cvd5_at_exit", 0) > 0]),
                ("flow AGAINST you", [t for t in cuts if t.get("cvd5_at_exit", 0) <= 0])):
            if not sel:
                continue
            died = sum(1 for t in sel if t.get("would_have_stopped"))
            lp = sorted(t["left_peak_R"] for t in sel)
            lines.append(f"  your early cuts with {label} (n{len(sel)}): {died} would "
                         f"have stopped anyway; median run after you left "
                         f"{lp[len(lp) // 2]:+.2f}R")
    # THE TRAIL GAUGE. The dominant discretionary behaviour on this desk is
    # tightening a stop until it catches the trade — invisible to the cut gauge
    # above (those are 'agent_exit'; these die as 'stop' above -1R). Split by the
    # flow you tightened into, so the lesson is "when it looked like THIS",
    # not a blanket "stop trailing".
    trail = [t for t in tr_all if t.get("touched") and t["exit_reason"] == "stop"
             and t.get("agent_R", -1) > -0.95]
    if trail:
        d = sum(t["agent_dollars"] - t["mech_dollars"] for t in trail)
        lines.append(f"  YOUR TRAILED STOPS caught {len(trail)} trades, net "
                     f"${d:+,.0f} vs letting the engine run them")
        for label, sel in (
                ("flow still WITH you", [t for t in trail
                                         if t.get("cvd5_at_exit", 0) > 0]),
                ("flow AGAINST you", [t for t in trail
                                      if t.get("cvd5_at_exit", 0) <= 0])):
            if not sel:
                continue
            lp = sorted(t.get("left_peak_R") or 0.0 for t in sel)
            dd = sum(t["agent_dollars"] - t["mech_dollars"] for t in sel)
            lines.append(f"    tightened with {label} (n{len(sel)}): ${dd:+,.0f}; "
                         f"median {lp[len(lp) // 2]:+.2f}R ran on AFTER your stop hit")
    caps = sorted(t["capture"] for t in tr_all if t.get("capture") is not None)
    if caps:
        lines.append(f"  capture (realized/peak, trades that reached +0.5R): "
                     f"median {caps[len(caps) // 2]:+.2f}")
    debs = [(t["day"], t["debrief"]) for r in rows for t in r["trades"]
            if t.get("debrief")]
    if debs:
        lines.append("your recent trade-journal entries:")
        for d, note in debs[-2:]:
            lines.append(f'  {d}: "{note[:110]}"')
    lines.append("last days (you vs B0):")
    for r in rows[-3:]:
        lines.append(f"  {r['day']}: you ${r['agent_dollars']:+,.0f} vs "
                     f"${r['b0_dollars']:+,.0f} ({r['n_signals']} signals, "
                     f"{len(r['passes'])} passes)")
    return "\n".join(lines)


# ------------------------------------------------------------------ signal building

def build_signals():
    """Per-day chronological signal lists, both engines, mech anchors attached."""
    T = load_trades("fit")
    L2 = pd.read_parquet(ROOT / "output/fixedr_fit_base_v8.parquet")
    wt = {(r.ts, r.direction): float(r.working_target) for r in L2.itertuples()}
    O = pd.read_parquet(ROOT / "output/aikido_cr_fit.parquet").set_index(["ts", "direction"])
    if "cr_suppressed" in O.columns:
        sup = set(O[O.cr_suppressed].index)
        T = [t for t in T if (t["ts"], t["direction"]) not in sup]
        O = O[~O.cr_suppressed]
    days: dict[str, list[dict]] = {}
    for t in T:
        # the overlay parquet only carries trades the two-rule walk CHANGED;
        # everything else keeps the engine's own exit/dollars (run-1 convention)
        k = (t["ts"], t["direction"])
        mech_exit, mech_px, mech_d = t["exit"], t["exit_price"], t["dollars"]
        if k in O.index:
            r = O.loc[k]
            mech_exit = pd.to_datetime(r.cr_exit_ts).tz_convert(NY)
            mech_px, mech_d = float(r.cr_exit_price), float(r.cr_dollars_1lot)
        # AUDIT FIX 2: the book's `stop` column is not reliably the INITIAL stop
        # (28% disagree with `risk`; 51 trades sit ~BE and exit 'stop' for ~$15 —
        # a MOVED stop, i.e. post-hoc information). Reconstruct the engine's own
        # -1R stop from risk so R units are honest and no hindsight leaks in.
        s_ = sgn(t["direction"])
        init_stop = round(round((t["entry"] - s_ * t["risk"]) / TICK) * TICK, 10)
        # AUDIT FIX 1: 43.8% of canon trades bank a 50% partial in their shipped
        # management. Recover its price (capture_replay's own inversion of the
        # engine arithmetic) so a TOUCHED position keeps the shipped partial
        # instead of silently becoming a naked position.
        ppx = implied_partial(t)
        days.setdefault(t["day"], []).append(dict(
            engine="CANON", day=t["day"], sess=t["sess"], direction=t["direction"],
            s=s_, fill=t["fill"], entry=float(t["entry"]),
            stop=init_stop, risk=float(t["risk"]), size=float(t["size"]),
            partial_px=(float(ppx) if ppx is not None else None),
            pattern=t.get("pattern", "?"), target=wt.get((t["ts"], t["direction"])),
            mech_exit=mech_exit, mech_exit_px=mech_px, mech_dollars=mech_d))
    for t in build_shelf_trades():
        td = SHELF_TIER[t["tier"]]
        days.setdefault(t["day"], []).append(dict(
            engine="SHELF", day=t["day"], sess="shelf", direction=t["direction"],
            s=float(t["side"]), fill=t["fill"], entry=float(t["entry"]),
            stop=float(t["stop"]), risk=float(t["risk"]), legacy=float(t["legacy"]),
            tier=t["tier"], score=int(t["score"]), dollars_risk=td,
            mech_exit=t["mech_exit_ts"], mech_exit_kind=t["mech_exit_kind"],
            mech_dollars=float(td * t["mech_R"]), mech_R=float(t["mech_R"])))
    for d in days:
        days[d].sort(key=lambda x: x["fill"])
        for i, sig in enumerate(days[d]):
            sig["sid"] = f"{'C' if sig['engine'] == 'CANON' else 'S'}{i + 1}"
    return days


def b1_dollars(sigs: list[dict]) -> float:
    """Canon precedence: shelf entry skipped while an opposite canon position is open."""
    tot, open_canon = 0.0, []
    for g in sigs:
        open_canon = [(s_, x_) for s_, x_ in open_canon if x_ > g["fill"]]
        if g["engine"] == "CANON":
            tot += g["mech_dollars"]
            open_canon.append((g["s"], g["mech_exit"]))
        elif not any(s_ != g["s"] for s_, _ in open_canon):
            tot += g["mech_dollars"]
    return tot


# ------------------------------------------------------------------ the day loop

def sig_desc(g: dict) -> str:
    if g["engine"] == "CANON":
        tgt = "none" if g["target"] is None else f"{g['target']:.2f} ({g['s'] * (g['target'] - g['entry']) / g['risk']:+.1f}R)"
        pt = (f", engine banks HALF at {g['partial_px']:.2f} "
              f"({g['s'] * (g['partial_px'] - g['entry']) / g['risk']:+.1f}R) then runs "
              f"the rest" if g.get("partial_px") is not None else "")
        return (f"CANON {g['direction'].upper()} [{g['sess']}] fills {g['entry']:.2f}, "
                f"stop {g['stop']:.2f} (-1R = {g['risk']:.2f}pt), working target {tgt}"
                f"{pt}, pattern {g['pattern']}")
    return (f"SHELF {g['direction'].upper()} [{g['tier']}, ${g['dollars_risk']:.0f} risk] "
            f"fills {g['entry']:.2f}, stop {g['stop']:.2f} (-1R = {g['risk']:.2f}pt), "
            f"target = developing near VWAP band, scratch t+10 if red")


def run_day(day: str, sigs: list[dict], bars, tape_day, dep, journal) -> tuple[dict, list]:
    daybars = bars.loc[pd.Timestamp(f"{day} 07:00", tz=NY):
                       pd.Timestamp(f"{day} 16:05", tz=NY)]
    rth = daybars.loc[pd.Timestamp(f"{day} 09:30", tz=NY):
                      pd.Timestamp(f"{day} 15:59", tz=NY)]
    V = rth.volume.clip(lower=0).to_numpy().astype(float)
    tp = ((rth.high + rth.low + rth.close) / 3).to_numpy()
    cv = np.maximum(V.cumsum(), 1)
    vwap = (tp * V).cumsum() / cv
    sd = np.sqrt(np.clip((tp ** 2 * V).cumsum() / cv - vwap ** 2, 0, None))
    rix = rth.index

    def band_at(minute, s):
        j = rix.searchsorted(minute, side="right") - 1
        if j < 0:
            return None
        return float(vwap[j] - s * sd[j])

    sid = None
    turns, transcript = 0, []
    book: list[dict] = []
    done_trades: list[dict] = []
    passes: list[dict] = []
    conflicts: list[dict] = []
    just_closed: list[dict] = []
    last_turn_min = None
    thesis = ""

    def r_of(p, px):
        return p["s"] * (px - p["entry"]) / p["risk"]

    def entry_state(minute, s, entry, risk):
        """All variables you know at the fill, recorded mechanically (archive)."""
        st = {}
        try:
            w = tape_day.loc[:minute]
            if len(w):
                st["delta1m"] = round(float(w.delta.iloc[-1]) * s, 0)
                st["cvd5m"] = round(float(w.delta.tail(5).sum()) * s, 0)
                st["cvd15m"] = round(float(w.delta.tail(15).sum()) * s, 0)
                st["opposed5"] = int((np.sign(w.delta.tail(5).to_numpy() * s) < 0).sum())
                vmed = float(w.vol.tail(60).median()) or 1.0
                st["volx"] = round(float(w.vol.iloc[-1]) / vmed, 2)
        except Exception:
            pass
        try:
            if dep is not None and len(dep):
                snap = dep[dep.ts < minute]
                if len(snap):
                    snap = snap[snap.ts == snap.ts.max()]
                    bid, ask = snap[snap.side == "bid"], snap[snap.side == "ask"]
                    if len(bid) and len(ask):
                        tb, ta = float(bid["size"].sum()), float(ask["size"].sum())
                        st["imb"] = round((tb - ta) / max(tb + ta, 1) * s, 3)
                        ahead = ask if s > 0 else bid
                        wa = ahead.loc[ahead["size"].idxmax()]
                        st["wall_pt"] = round(abs(float(wa.price) - entry), 2)
                        st["wall_sz"] = float(wa["size"])
        except Exception:
            pass
        j = rix.searchsorted(minute, side="right") - 1
        if j >= 0:
            st["vwap_dist_r"] = round(s * (float(vwap[j]) - entry) / risk, 2)
            st["band_dist_r"] = round(s * ((float(vwap[j]) - s * float(sd[j])) - entry)
                                      / risk, 2)
            if j >= 5:
                st["vwap_slope5"] = round(float(vwap[j] - vwap[j - 5]), 2)
            seen = rth.loc[:minute]
            if len(seen):
                st["rth_range_pt"] = round(float(seen.high.max() - seen.low.min()), 2)
        return st

    def post_exit_walk(p, ts_):
        """What the trade did AFTER the exit, on the ORIGINAL engine stop — the
        could-have-captured-more / would-have-died-anyway record."""
        seg = daybars.loc[ts_:]
        seg = seg[seg.index > ts_]
        xpx = float(p["legs"][-1][1]) if p["legs"] else p["entry"]
        left_peak, would_stop, end_r = 0.0, False, None
        for mi2, b2 in seg.iterrows():
            if mi2 >= p["flatten"]:
                break
            if (p["s"] > 0 and b2.low <= p["sig"]["stop"]) or \
               (p["s"] < 0 and b2.high >= p["sig"]["stop"]):
                would_stop = True
                end_r = r_of(p, p["sig"]["stop"])
                break
            fav2 = (float(b2.high) - xpx) if p["s"] > 0 else (xpx - float(b2.low))
            left_peak = max(left_peak, fav2 / p["risk"])
            end_r = r_of(p, float(b2.close))
        return (round(left_peak, 3), bool(would_stop),
                round(end_r, 3) if end_r is not None else None)

    def close_pos(p, fr, px, reason):
        p["legs"].append((fr, px, reason))
        p["frac"] = round(p["frac"] - fr, 10)

    def settle(p, reason, ts_, anchor=False):
        # ANCHORING LAW (capture_replay): an untouched position settles at the
        # engine's own realised dollars — only agent DEVIATIONS are simulated.
        if anchor:
            net = p["sig"]["mech_dollars"]
            aR = net / (p["risk"] * PV * p["sig"]["size"]) if p["engine"] == "CANON" \
                else net / p["sig"]["dollars_risk"]
        else:
            pts = sum(fr * p["s"] * (px - p["entry"]) for fr, px, _ in p["legs"])
            if p["engine"] == "CANON":
                net = pts * PV * p["sig"]["size"] - COMMISSION
                aR = net / (p["risk"] * PV * p["sig"]["size"])
            else:
                aR = (pts - SFR) / p["risk"]
                net = p["sig"]["dollars_risk"] * aR
        book.remove(p)
        done_trades.append({
            "pid": p["pid"], "engine": p["engine"], "day": day,
            "direction": p["sig"]["direction"],
            "sess": p["sig"]["sess"], "tier": p["sig"].get("tier", "-"),
            "taken_by": p["taken_by"], "agent_R": round(aR, 4),
            "agent_dollars": round(net, 2),
            "mech_dollars": round(p["sig"]["mech_dollars"], 2),
            "exit_reason": reason, "exit_ts": str(ts_), "turns": p["turns"],
            "extended": p["extended"], "touched": p["touched"],
            "partials": sum(1 for _, _, rr in p["legs"] if rr == "partial"),
            "mfe_R": round(p["peak_r"], 3), "mae_R": round(p["trough_r"], 3),
            "mfe_min": p["mfe_min"], "mae_min": p["mae_min"],
            "first_red_min": p["first_red_min"], "cvd5_at_first_red": p["red_cvd5"],
            "capture": round(aR / p["peak_r"], 3) if p["peak_r"] > 0.5 else None,
            "held_min": int((ts_ - p["sig"]["fill"]).total_seconds() // 60),
            "last_note": p["last_note"],
            "score": p["sig"].get("score"), "entry_state": p.get("entry_state"),
            "day_ctx": day_ctx, "debrief": "",
            "legs": [(f, px, rr) for f, px, rr in p["legs"]]})
        row = done_trades[-1]
        try:
            w = tape_day.loc[:ts_]
            if len(w) >= 5:
                row["cvd5_at_exit"] = round(float(w.delta.tail(5).sum()) * p["s"], 0)
                row["opposed_at_exit"] = int(
                    (np.sign(w.delta.tail(5).to_numpy() * p["s"]) < 0).sum())
        except Exception:
            pass
        lp, ws, sr = post_exit_walk(p, ts_)
        row["left_peak_R"], row["would_have_stopped"], row["settle_after_R"] = lp, ws, sr
        just_closed.append(row)

    def apply_mgmt(p, rep):
        p["touched"] = True
        if rep.get("stop_r") is not None:
            try:
                cand = p["entry"] + p["s"] * float(rep["stop_r"]) * p["risk"]
                if p["s"] * (cand - p["stop"]) > 0:
                    p["stop"] = round(round(cand / TICK) * TICK, 10)
            except Exception:
                pass
        if "target_r" in rep:
            tr = rep.get("target_r")
            if tr is None:
                p["target_mode"], p["target_px"] = "none", None
            else:
                try:
                    tr = float(tr)
                    floor = (0.1 if p["partial_done"] else 2.0) \
                        if p["engine"] == "CANON" else 0.3
                    if tr >= floor:
                        p["target_mode"] = "fixed"
                        p["target_px"] = round(
                            round((p["entry"] + p["s"] * tr * p["risk"]) / TICK) * TICK, 10)
                except Exception:
                    pass
        if rep.get("partial_pct") is not None:
            try:
                v = float(rep["partial_pct"])
                if 0.0 < v < 1.0:
                    p["pending"].append(("partial", v))
            except Exception:
                pass

    def handle_close_other(rep):
        pid = rep.get("close_other")
        if pid:
            for q in book:
                if q["pid"] == pid:
                    q["touched"] = True
                    q["pending"].append(("exit", None))

    def pos_state(p, minute, bar):
        last = float(bar.close)
        tgt = ("developing band" if p["target_mode"] == "band" else
               ("none (riding stop)" if p["target_mode"] == "none" else
                f"{r_of(p, p['target_px']):+.2f}R"))
        ap = (f" | engine partial pending {r_of(p, p['auto_partial_px']):+.2f}R"
              if p.get("auto_partial_px") is not None else "")
        return (f"pos {p['pid']} {p['engine']} {p['sig']['direction']} | "
                f"R_now {r_of(p, last):+.2f} peak {p['peak_r']:+.2f} | "
                f"open {p['frac']:.2f} | stop {r_of(p, p['stop']):+.2f}R | "
                f"target {tgt}{ap}")

    def book_state(minute, bar):
        if not book:
            return "book: flat"
        return "book: " + " || ".join(pos_state(p, minute, bar) for p in book)

    def send(minute, bar, why, p=None, signal=None):
        """One turn. p = management target position; signal = signal dict."""
        nonlocal turns, sid, last_turn_min
        is_sig = signal is not None
        s_ctx = signal["s"] if is_sig else (p["s"] if p is not None else 1.0)
        state = (f"[{minute.strftime('%H:%M')}] EVENT: {why}\n"
                 f"bar {bar.open:.2f}/{bar.high:.2f}/{bar.low:.2f}/{bar.close:.2f} | "
                 f"{flow_line(tape_day, minute, s_ctx)} | "
                 f"{book_line(dep, minute, float(bar.close), s_ctx)}\n"
                 f"{book_state(minute, bar)}\n"
                 f"mins_to_EOD {int((pd.Timestamp(f'{day} 15:55', tz=NY) - minute).total_seconds() // 60)}")
        if p is not None:
            state += f"\nthis event is about: {pos_state(p, minute, bar)}"
        txt, sid2 = call_claude(state, sid)
        sid = sid2 or sid
        rep = parse_reply(txt, is_sig)
        turns += 1
        last_turn_min = minute
        transcript.append({"minute": str(minute), "why": why, "sent": state, "reply": txt})
        if p is not None:
            p["last_note"] = str(rep.get("note", ""))[:120]
            p["turns"] += 1
        handle_close_other(rep)
        return rep

    def open_pos(g, taken_by):
        mode = "band" if g["engine"] == "SHELF" else \
            ("fixed" if g.get("target") is not None else "none")
        book.append(dict(
            pid=g["sid"], engine=g["engine"], sig=g, s=g["s"], entry=g["entry"],
            entry_state=entry_state(g["fill"], g["s"], g["entry"], g["risk"]),
            trough_r=0.0, mfe_min=0, mae_min=0, first_red_min=None, red_cvd5=None,
            risk=g["risk"], stop=g["stop"], frac=1.0, legs=[], pending=[],
            target_mode=mode, target_px=g.get("target"),
            auto_partial_px=g.get("partial_px"),
            extended=False, partial_done=False, peak_r=0.0, seen_r=set(),
            turns=0, last_note="", taken_by=taken_by, gb_peak=0.0,
            flatten=pd.Timestamp(f"{day} 09:30" if g["sess"] == "pre" else f"{day} 15:55",
                                 tz=NY),
            mech_exit_done=False, scratch_done=False, touched=False))

    # ---- 07:45 morning read (+ the day's market-condition record)
    day_ctx: dict = {}
    d0 = pd.Timestamp(f"{day} 07:40", tz=NY)
    prior = bars.loc[:d0 - pd.Timedelta(hours=16)]
    on = bars.loc[d0 - pd.Timedelta(hours=13, minutes=40):d0]
    if len(on):
        pd_day = (prior[prior.index >= prior.index[-1] - pd.Timedelta("24h")]
                  if len(prior) else on)
        last = float(on.close.iloc[-1])
        day_ctx = {"gap_pt": round(last - float(pd_day.close.iloc[-1]), 2),
                   "on_range_pt": round(float(on.high.max() - on.low.min()), 2),
                   "prior_range_pt": round(float(pd_day.high.max() - pd_day.low.min()), 2)}
        gap_note = ""
        if journal:
            gap = (pd.Timestamp(day) - pd.Timestamp(max(r["day"] for r in journal))).days
            if gap > 4:
                gap_note = f"NOTE: {gap} calendar days since your last journaled day.\n"
        ctx = (f"MORNING READ, {day} 07:45 ET. Your desk, your day. Both engines live.\n"
               f"{gap_note}"
               f"prior day: O {pd_day.open.iloc[0]:.0f} H {pd_day.high.max():.0f} "
               f"L {pd_day.low.min():.0f} C {pd_day.close.iloc[-1]:.0f}\n"
               f"overnight (18:00->07:40): H {on.high.max():.0f} L {on.low.min():.0f} "
               f"last {last:.0f} (gap {last - float(pd_day.close.iloc[-1]):+.0f})\n"
               f"{journal_digest(journal)}\n{TURN_CONTRACT}\n"
               'Reply EXACTLY one JSON: {"bias":"long|short|neutral",'
               '"day_type":"<=30 chars","thesis":"<=200 chars"}')
        txt, sid = call_claude(ctx, None)
        thesis = txt.strip()[:300]
        turns += 1
        transcript.append({"minute": "07:45", "why": "morning read", "sent": ctx,
                           "reply": txt})

    ix = daybars.index
    start = ix.searchsorted(pd.Timestamp(f"{day} 07:46", tz=NY))
    fills_by_min: dict = {}
    for g in sigs:                      # snap each fill onto the first bar >= fill
        j = ix.searchsorted(g["fill"])
        if j < len(ix):
            fills_by_min.setdefault(ix[j], []).append(g)

    for i in range(start, len(ix)):
        minute, bar = ix[i], daybars.iloc[i]
        fills_now = fills_by_min.get(minute, [])
        # 1. session flattens at the bar open
        for p in list(book):
            if minute >= p["flatten"]:
                reason = "open_flatten" if p["sig"]["sess"] == "pre" else "eod"
                close_pos(p, p["frac"], float(bar.open) - p["s"] * SLIP * TICK, reason)
                settle(p, reason, minute, anchor=not p["touched"])
        # 2. canon close-and-reverse LAW — live only for TOUCHED positions (an
        # untouched canon pos already carries the flip inside its anchored exit)
        for g in fills_now:
            if g["engine"] != "CANON":
                continue
            for p in [q for q in book if q["engine"] == "CANON" and q["s"] != g["s"]
                      and q["touched"]]:
                if (p["s"] > 0 and bar.low <= p["stop"]) or \
                   (p["s"] < 0 and bar.high >= p["stop"]):
                    px = (min(p["stop"], float(bar.open)) if p["s"] > 0
                          else max(p["stop"], float(bar.open)))
                    close_pos(p, p["frac"], px - p["s"] * SLIP * TICK, "stop")
                    settle(p, "stop", minute)
                else:
                    close_pos(p, p["frac"], g["entry"], "flip")
                    settle(p, "flip", minute)
                    transcript.append({"minute": str(minute), "why": "close-and-reverse",
                                       "sent": f"harness: opposing canon fill closed "
                                               f"{p['pid']} at {g['entry']} (law)",
                                       "reply": "(mechanical)"})
        # 3. pending market actions at this bar's open
        for p in list(book):
            for kind, val in p["pending"]:
                px = float(bar.open) - p["s"] * SLIP * TICK
                if kind == "exit" and p["frac"] > 0:
                    close_pos(p, p["frac"], px, "agent_exit")
                elif kind == "partial" and p["frac"] > 0:
                    close_pos(p, round(p["frac"] * val, 10), px, "partial")
                    p["partial_done"] = True
            p["pending"] = []
            if p["frac"] <= 0:
                settle(p, "agent_exit", minute)
        # 4. stops, stop-first (untouched CANON is path-anchored to its exit stamp —
        # its stop outcome, if any, is already inside the engine's own dollars)
        for p in list(book):
            if p["engine"] == "CANON" and not p["touched"]:
                continue
            if (p["s"] > 0 and bar.low <= p["stop"]) or \
               (p["s"] < 0 and bar.high >= p["stop"]):
                px = (min(p["stop"], float(bar.open)) if p["s"] > 0
                      else max(p["stop"], float(bar.open)))
                close_pos(p, p["frac"], px - p["s"] * SLIP * TICK, "stop")
                settle(p, "stop", minute, anchor=not p["touched"])
        # 4b. the SHIPPED partial (canon): a standing order the agent inherits.
        # Fires once, at its price, unless the agent already booked a partial.
        for p in list(book):
            ap = p.get("auto_partial_px")
            if ap is None or p["partial_done"] or p["frac"] <= 0:
                continue
            if (p["s"] > 0 and bar.high >= ap) or (p["s"] < 0 and bar.low <= ap):
                close_pos(p, round(p["frac"] * 0.5, 10), ap, "partial")
                p["partial_done"] = True
                p["auto_partial_px"] = None
        # 5. targets + mechanical-exit decision events
        for p in list(book):
            mins_in = int((minute - p["sig"]["fill"]).total_seconds() // 60)
            if p["engine"] == "SHELF":
                bnow = band_at(minute, p["s"]) if p["target_mode"] == "band" else None
                tgt = bnow if p["target_mode"] == "band" else p["target_px"]
                valid = (p["target_mode"] == "fixed") or \
                    (p["target_mode"] == "band" and bnow is not None and
                     p["s"] * (bnow - p["entry"]) >= 0.25 * p["risk"])
                touched = tgt is not None and valid and \
                    ((p["s"] < 0 and bar.low <= tgt) or (p["s"] > 0 and bar.high >= tgt))
                if touched and (p["target_mode"] == "fixed" or p["extended"]):
                    close_pos(p, p["frac"], tgt, "target")
                    settle(p, "target", minute)
                    continue
                if touched and turns < MAX_TURNS_DAY:
                    prev_mode = p["target_mode"]
                    rep = send(minute, bar,
                               f"MECHANICAL EXIT ({p['pid']}): shelf band is here at "
                               f"{tgt:.2f} ({r_of(p, tgt):+.2f}R). hold TAKES it; refuse "
                               f"= revise with a plan.", p=p)
                    p["extended"] = True
                    if rep["action"] == "revise":
                        apply_mgmt(p, rep)
                    if p["target_mode"] == prev_mode:
                        close_pos(p, p["frac"], tgt, "band")
                        settle(p, "band", minute, anchor=not p["touched"])
                    continue
                elif touched:
                    close_pos(p, p["frac"], tgt, "band")
                    settle(p, "band", minute, anchor=not p["touched"])
                    continue
                if mins_in >= 10 and not p["scratch_done"]:
                    p["scratch_done"] = True
                    if r_of(p, float(bar.close)) >= 0:
                        continue
                    if turns < MAX_TURNS_DAY and p["frac"] > 0:
                        prev = (p["target_mode"], p["stop"])
                        rep = send(minute, bar,
                                   f"MECHANICAL EXIT ({p['pid']}): shelf t+10 scratch, "
                                   f"red {r_of(p, float(bar.close)):+.2f}R. hold TAKES "
                                   f"it; refuse = revise with a plan.", p=p)
                        if rep["action"] == "revise":
                            apply_mgmt(p, rep)
                            p["extended"] = True
                            continue
                    close_pos(p, p["frac"], float(bar.close), "scratch")
                    settle(p, "scratch", minute, anchor=not p["touched"])
            else:  # CANON
                if p["touched"] and p["target_mode"] == "fixed" and \
                   p["target_px"] is not None and \
                   ((p["s"] > 0 and bar.high >= p["target_px"] + TICK) or
                        (p["s"] < 0 and bar.low <= p["target_px"] - TICK)):
                    close_pos(p, p["frac"], p["target_px"], "target")
                    settle(p, "target", minute)
                    continue
                if not p["mech_exit_done"] and minute >= p["sig"]["mech_exit"]:
                    p["mech_exit_done"] = True
                    xpx = p["sig"]["mech_exit_px"]
                    if turns < MAX_TURNS_DAY:
                        rep = send(minute, bar,
                                   f"MECHANICAL EXIT ({p['pid']}): canon exits here at "
                                   f"{xpx:.2f} ({r_of(p, xpx):+.2f}R). hold TAKES it; "
                                   f"refuse = revise with a plan.", p=p)
                        if rep["action"] == "revise":
                            apply_mgmt(p, rep)
                            p["extended"] = True
                            continue
                    close_pos(p, p["frac"], xpx, "canon_exit")
                    settle(p, "canon_exit", minute, anchor=not p["touched"])
        # 6. signal fills -> take/pass turns
        for g in fills_now:
            opposing = [q for q in book if q["s"] != g["s"]]
            if turns >= MAX_TURNS_DAY:
                open_pos(g, "auto_cap")
                continue
            if opposing:
                why = (f"SIGNAL + CONFLICT: {sig_desc(g)} — fires OPPOSITE to your open "
                       f"{', '.join(q['pid'] + ' ' + q['engine'] for q in opposing)}. "
                       f"pass / take (net the hedge) / take + close_other.")
            else:
                why = f"SIGNAL: {sig_desc(g)} — take or pass."
            rep = send(minute, bar, why, signal=g)
            if rep["action"] == "take":
                open_pos(g, "agent")
                if opposing:
                    conflicts.append({"day": day, "sid": g["sid"],
                                      "choice": "cut+take" if rep.get("close_other")
                                      else "net"})
            else:
                passes.append({"sid": g["sid"], "engine": g["engine"],
                               "desc": sig_desc(g),
                               "mech_dollars": round(g["mech_dollars"], 2),
                               "note": str(rep.get("note", ""))[:120]})
                if opposing:
                    conflicts.append({"day": day, "sid": g["sid"], "choice": "pass"})
        # 7. peak tracking + THE MINUTE PULSE. The desk is at the chart every
        # minute of 08:00-10:30 (the only entry window either engine has) and
        # every minute it holds a position after that. One call per minute;
        # signal/mechanical-exit turns already count as that minute's call.
        for p in book:
            mins_in_p = int((minute - p["sig"]["fill"]).total_seconds() // 60)
            fav = r_of(p, float(bar.high) if p["s"] > 0 else float(bar.low))
            if fav > p["peak_r"]:
                p["peak_r"], p["mfe_min"] = fav, mins_in_p
            worst = r_of(p, float(bar.low) if p["s"] > 0 else float(bar.high))
            if worst < p["trough_r"]:
                p["trough_r"], p["mae_min"] = worst, mins_in_p
            if p["first_red_min"] is None and r_of(p, float(bar.close)) <= -0.25:
                p["first_red_min"] = mins_in_p
                try:
                    w = tape_day.loc[:minute]
                    p["red_cvd5"] = round(float(w.delta.tail(5).sum()) * p["s"], 0)
                except Exception:
                    pass
        hhmm = minute.strftime("%H:%M")
        at_chart = bool(book) or (("08:00" <= hhmm <= "10:30")
                                  and minute.minute % 5 == 0)
        if at_chart and last_turn_min != minute and turns < MAX_TURNS_DAY:
            fresh = next((p for p in book if p["turns"] == 0), None)
            focus = fresh or (book[0] if len(book) == 1 else None)
            why = (f"position {fresh['pid']} opened — read it and set your plan"
                   if fresh else "minute pulse — adapt or hold")
            rep = send(minute, bar, why, p=focus)
            tgt = focus
            if rep.get("pos"):
                tgt = next((q for q in book if q["pid"] == rep["pos"]), tgt)
            if tgt is not None:
                if rep["action"] == "exit_now":
                    tgt["touched"] = True
                    tgt["pending"].append(("exit", None))
                elif rep["action"] == "revise":
                    apply_mgmt(tgt, rep)
        # 8. trade-journal debriefs — one deep note per closed trade (Angus:
        # "make sure the agent is taking deep notes on every trade it takes")
        if just_closed:
            for row_ in just_closed:
                if row_["taken_by"] == "agent" and turns < MAX_TURNS_DAY:
                    red = (f"first went red t+{row_['first_red_min']}m"
                           + (f" (cvd5 {row_['cvd5_at_first_red']:+.0f})"
                              if row_.get("cvd5_at_first_red") is not None else "")
                           if row_["first_red_min"] is not None else "never went red")
                    after = ("it would have hit the stop anyway"
                             if row_.get("would_have_stopped") else
                             (f"it ran {row_['left_peak_R']:+.2f}R further after you left"
                              if row_.get("left_peak_R") is not None else ""))
                    sett = (f"; session settled {row_['settle_after_R']:+.2f}R"
                            if row_.get("settle_after_R") is not None else "")
                    dwhy = (f"[{minute.strftime('%H:%M')}] TRADE CLOSED {row_['pid']}: "
                            f"{row_['engine']} {row_['direction']} "
                            f"({row_['sess']}/{row_['tier']}), exited "
                            f"'{row_['exit_reason']}' at {row_['agent_R']:+.2f}R "
                            f"(${row_['agent_dollars']:+,.0f}). Pure-machine outcome on "
                            f"this trade: ${row_['mech_dollars']:+,.0f}.\n"
                            f"THE PATH: held {row_['held_min']}m | MFE "
                            f"{row_['mfe_R']:+.2f}R at t+{row_['mfe_min']}m | MAE "
                            f"{row_['mae_R']:+.2f}R at t+{row_['mae_min']}m | {red} | "
                            f"flow at exit cvd5 {row_.get('cvd5_at_exit', 0):+.0f}, "
                            f"opposed {row_.get('opposed_at_exit', '?')}/5 | {after}{sett}."
                            f"\nWrite your trade journal entry — deep note: your entry "
                            f"read (tape/book/context), where it turned for or against "
                            f"you and what the flow said there, what you captured vs what "
                            f"was there, and the lesson your future self should find. "
                            f'Reply EXACTLY one JSON: {{"note":"<=500 chars"}}')
                    txt, sid2 = call_claude(dwhy, sid)
                    sid = sid2 or sid
                    turns += 1
                    transcript.append({"minute": str(minute),
                                       "why": f"debrief {row_['pid']}",
                                       "sent": dwhy, "reply": txt})
                    m = re.search(r"\{.*\}", txt, re.DOTALL)
                    if m:
                        try:
                            row_["debrief"] = str(json.loads(m.group(0))
                                                  .get("note", ""))[:500]
                        except Exception:
                            pass
            just_closed.clear()
    # any survivors (data ended early): flatten at last close
    for p in list(book):
        close_pos(p, p["frac"], float(daybars.close.iloc[-1]), "early_close")
        settle(p, "early_close", ix[-1], anchor=not p["touched"])

    b0 = sum(g["mech_dollars"] for g in sigs)
    row = {"day": day, "n_signals": len(sigs), "turns": turns,
           "agent_dollars": round(sum(t["agent_dollars"] for t in done_trades), 2),
           "b0_dollars": round(b0, 2), "b1_dollars": round(b1_dollars(sigs), 2),
           "trades": done_trades, "passes": passes, "conflicts": conflicts,
           "thesis": thesis}
    return row, transcript


# ------------------------------------------------------------------ chain driver

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo-day", default=None)
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "transcripts").mkdir(exist_ok=True)
    if not a.status:                      # single-instance lock: no double desks
        import fcntl
        lockf = open(RUNS / ".lock", "w")
        try:
            fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("another desk run holds the lock — refusing to double-launch")
            return
        main._lock = lockf               # keep the fd alive for the process life
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
                  f"B1 ${sum(r['b1_dollars'] for r in rows):+,.0f} | "
                  f"passes {sum(len(r['passes']) for r in rows)}")
        return
    days = build_signals()
    sel = [d for d in sorted(days) if d not in done]
    if a.demo_day:
        sel = [a.demo_day]
    bars = load_bars_ny()
    tape = pd.read_parquet(ROOT / "output/fp_minutes.parquet").sort_index()
    dcache: dict = {}
    print(f"live-sim desk: {len(sel)} days, {sum(len(days[d]) for d in sel)} "
          f"signals | {WORKERS} workers, {BATCH_DAYS}-day batches, journal chains "
          f"every {BATCH_DAYS} trading days", flush=True)

    def one(d, journal):
        t0 = pd.Timestamp(f"{d} 00:00", tz=NY)
        return d, run_day(d, days[d], bars, tape.loc[t0:t0 + pd.Timedelta(hours=24)],
                          dcache.get(d), journal)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    batches = [sel[i:i + BATCH_DAYS] for i in range(0, len(sel), BATCH_DAYS)]
    for batch in batches:
        for d in batch:                       # depth pre-loaded serially; workers read only
            dcache[d] = load_depth(d, {})
        journal = journal_rows()              # frozen at batch start = the chained memory
        print(f"== {batch[0]}..{batch[-1]}: {len(batch)} days | "
              f"journal {len(journal)} days", flush=True)
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = [ex.submit(one, d, journal) for d in batch]
            for fut in as_completed(futs):
                try:
                    d, (row, tr) = fut.result()
                except Exception as e:
                    print(f"  DAY FAILED (will resume): {e}", flush=True)
                    continue
                (RUNS / "transcripts" / f"{d}.json").write_text(
                    json.dumps({"turns": tr}, indent=1))
                with (RUNS / "journal.jsonl").open("a") as f:
                    f.write(json.dumps(row) + "\n")
                done.add(d)
                st.write_text(json.dumps({"done": sorted(done)}))
                print(f"  {d}: you ${row['agent_dollars']:+,.0f} vs B0 "
                      f"${row['b0_dollars']:+,.0f} vs B1 ${row['b1_dollars']:+,.0f} "
                      f"({row['n_signals']} signals, {len(row['passes'])} passes, "
                      f"{row['turns']} turns)", flush=True)


if __name__ == "__main__":
    main()
