#!/usr/bin/env python3
"""Chained-agents capture test on the rebuilt canon — the plan/ingest/grade loop.

docs/PLAN-agents-capture-run.md is the pre-registered protocol; this file is its machinery.
Settlement comes from scripts/capture_replay.py (100% canon reconciliation, both spans).
Briefings, verdict schema, and the journal come from src/desk/trade_manager.py — the kept
desk infra — re-pointed at the aikido canon.

Two input tiers (§4 of the plan — the fp_minutes tape is fit-only):
  full   flow (fp CVD) + book (MBP-10) + geometry + bars       fit-only evidence
  bar    book + geometry + bars, NO flow block                 holdout-confirmable

Chronological chain: `plan --week` builds the journal ONLY from trades that closed before
that week under the tier's own verdicts, then emits the current frontier's briefings (one
file per decision; decision N+1 of a trade exists only after N is answered). One briefing
per agent call — no multi-briefing prompts, so no same-day lookahead is even possible.
Verdicts are fail-closed through IntradeVerdict: malformed -> the trade falls back to canon.

    python -m scripts.capture_agents weeks  --tier bar
    python -m scripts.capture_agents plan   --tier bar --week 2025-06-02
    python -m scripts.capture_agents ingest --tier bar --file <candidates.jsonl>
    python -m scripts.capture_agents grade  --tier bar
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.capture_replay import (  # noqa: E402
    MECH_ARMS, arm_canon, canon_exit_of, day_path, load_bars_ny, load_trades, sgn, simulate)
from src.desk.trade_manager import (  # noqa: E402
    EOD_FLATTEN_HM, MAX_DECISIONS, RATIONALE_MAX, RECHECK_MIN, SCHEMA_VERSION,
    IntradeVerdict, build_briefing, journal_digest, journal_row)

NY = "America/New_York"
TAPE = ROOT / "output/fp_minutes.parquet"
DEPTH_DIRS = ["data/reference/depth_2025", "data/reference/depth_2026",
              "data/reference/depth_apr2026", "data/reference/depth_2023_24"]
SPEC = ROOT / ".claude/agents/trade-manager-v2.md"
TIERS = ("full", "bar")


def spec_version() -> str:
    return hashlib.sha256(SPEC.read_bytes()).hexdigest()[:12] if SPEC.exists() else "missing"


def blobs_dir(tier: str) -> Path:
    return ROOT / f"output/desk_blobs/capture/{tier}"


def verdicts_path(tier: str) -> Path:
    return ROOT / f"output/capture_verdicts_{tier}.jsonl"


# ------------------------------------------------------------------ inputs

def add_vwap(bars: pd.DataFrame) -> pd.DataFrame:
    """Daily-anchored (18:00 ET) running VWAP + 1σ band, causal by construction (cumulative
    sums only). Feeds build_briefing's vwap_distance_sd_signed."""
    b = bars.copy()
    typ = (b.high + b.low + b.close) / 3.0
    anchor = (b.index - pd.Timedelta(hours=18)).date
    g = pd.Series(anchor, index=b.index)
    v = b.volume.astype(float).clip(lower=1.0)
    cv = v.groupby(g).cumsum()
    cvt = (v * typ).groupby(g).cumsum()
    cvt2 = (v * typ * typ).groupby(g).cumsum()
    vw = cvt / cv
    var = (cvt2 / cv - vw * vw).clip(lower=0.0)
    b["vw"], b["up1"] = vw, vw + np.sqrt(var)
    return b


def load_tape(tier: str) -> pd.DataFrame:
    if tier == "bar":
        return pd.DataFrame(columns=["delta", "vol"],
                            index=pd.DatetimeIndex([], tz=NY))
    t = pd.read_parquet(TAPE).sort_index()
    return t


def load_depth(day: str, cache: dict) -> pd.DataFrame | None:
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


def briefing_trade(t: dict) -> dict:
    """The trade dict shaped the way build_briefing expects (old-book field names)."""
    return {**t, "win_": t["sess"], "pattern": t.get("pattern", "?")}


def path_states(t: dict, bars: pd.DataFrame, minute: pd.Timestamp) -> dict | None:
    """The triple-era press signal, as PAST facts only: minute-close R at fill+3m / fill+5m,
    reported only for checkpoints strictly before the decision minute."""
    s, entry, risk = sgn(t["direction"]), t["entry"], t["risk"]
    out = {}
    for k in (3, 5):
        cp = t["fill"] + pd.Timedelta(minutes=k)
        if cp >= minute:
            continue
        seg = bars.loc[:cp]
        if len(seg):
            out[f"r_at_fill_plus_{k}m"] = round(s * (float(seg.close.iloc[-1]) - entry) / risk, 2)
    if not out:
        return None
    best = max(out.values())
    out["at_or_above_half_R_by_t5"] = bool(best >= 0.5)
    out["note"] = ("trades at +0.5R or better by minute 3-5 won 79-88% in every era "
                   "(fit-2025, fit-2026, sealed holdout) — the strongest known state")
    return out


# ------------------------------------------------------------------ decision points

def decision_points(trade: dict, path: pd.DataFrame, canon_exit) -> list[tuple]:
    """Anchors are self-consistent with the strict `< minute` briefing truncation: the
    reached_+1R decision sits on the bar AFTER the bar that touched +1R, so the event is
    visible DATA at decision time and the action executes one bar later (reaction latency;
    the stop is still checked first on the reaction bar). Detection starts after the fill
    bar — the fill bar's extremes straddle the fill and would overstate the excursion. The
    canon-exit decision stays ON the exit bar (the settlement anchors there); its briefing
    carries the exit price explicitly and data through the prior completed bar. On a minute
    collision the canon-exit decision wins."""
    s, entry, risk = sgn(trade["direction"]), trade["entry"], trade["risk"]
    cx_min, _ = canon_exit
    pts = []
    if len(path) > 2 and risk > 0:
        after = path.iloc[1:]
        fav = after.high if s > 0 else after.low
        hit = after.index[(s * (fav - entry) >= risk).to_numpy()]
        if len(hit):
            j = int(np.searchsorted(path.index, hit[0], side="right"))
            if j < len(path) and path.index[j] < cx_min:
                pts.append((path.index[j], "reached_+1R"))
    pts.append((cx_min, "canon_would_exit_here"))
    m = cx_min + pd.Timedelta(minutes=RECHECK_MIN)
    while len(path) and m <= path.index[-1] and len(pts) < MAX_DECISIONS:
        nxt = path.index[path.index >= m]
        if not len(nxt):
            break
        pts.append((nxt[0], "recheck_while_extended"))
        m = nxt[0] + pd.Timedelta(minutes=RECHECK_MIN)
    seen, out = set(), []
    for mi, why in sorted(pts, key=lambda p: (p[0], p[1] != "canon_would_exit_here")):
        if mi not in seen:
            seen.add(mi)
            out.append((mi, why))
    return out[:MAX_DECISIONS]


def _plan_from(v: IntradeVerdict, trade: dict):
    if v.action == "exit_now":
        return "exit_now"
    s_, e, risk = sgn(trade["direction"]), trade["entry"], trade["risk"]
    tgt = e + s_ * float(v.target_r) * risk if v.target_r is not None else None
    stp = e + s_ * float(v.stop_r) * risk if v.stop_r is not None else None
    return ("plan", tgt, stp, v.partial_pct)


def reachable_points(trade, path, cx, verdicts) -> list[tuple]:
    """Decision points the position actually reaches under the answered verdicts so far.
    Stops at the first unanswered one — that is the frontier."""
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
                    done["stop"] = True
                    return "take_canon" if st["canon_exit_here"] else "exit_now"
                return _plan_from(v, trade)
        return "take_canon" if st["canon_exit_here"] else None

    simulate(trade, path, probe, cx)
    return reached


def replay_with_verdicts(t, path, cx, verdicts):
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


def read_verdicts(tier: str) -> dict:
    out, bad = {}, 0
    p = verdicts_path(tier)
    if not p.exists():
        return out
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            v = IntradeVerdict(**json.loads(line))
            out[(v.trade_id, v.decision_minute)] = v
        except Exception:
            bad += 1
    if bad:
        print(f"  {bad} malformed verdicts dropped (fail-closed -> canon)")
    return out


# ------------------------------------------------------------------ journal chain

def build_journal(trades, bars, tape, verdicts, before, dcache) -> list[dict]:
    """Journal rows for every trade CLOSED (under the tier's verdicts) strictly before
    `before` — the agent's own past, never anything concurrent."""
    rows = []
    for t in trades:
        if t["fill"] >= before:
            continue
        path = day_path(t, bars)
        if not len(path):
            continue
        cx = canon_exit_of(t, path)
        out, seen = replay_with_verdicts(t, path, cx, verdicts)
        if out["exit_minute"] >= before:
            continue
        s_, entry, risk = sgn(t["direction"]), t["entry"], t["risk"]
        dep = load_depth(t["day"], dcache)
        st = {"stop": t["stop"], "extended": False, "peak": entry,
              "canon_exit_here": False, "reason": ""}
        for minute, why in seen:
            st["reason"], st["canon_exit_here"] = why, minute == cx[0]
            b = build_briefing(briefing_trade(t), minute, st, bars, tape, dep)
            seg = path.loc[minute:out["exit_minute"]]
            if len(seg):
                fav = (seg.high - entry) if s_ > 0 else (entry - seg.low)
                peak = float(fav.max())
                ipk = int(np.argmax(fav.to_numpy()))
            else:
                peak, ipk = 0.0, 0
            rows.append(journal_row(
                b, verdicts.get((t["trade_id"], minute.isoformat())),
                {**out, "r_peak_after": peak / risk, "minutes_to_peak_after": ipk,
                 "r_banked": None, "r_runner": None}))
    return rows


# ------------------------------------------------------------------ modes

def cmd_weeks(trades, tier: str) -> int:
    verdicts = read_verdicts(tier)
    by_week: dict[str, list] = {}
    for t in trades:
        wk = (t["fill"] - pd.Timedelta(days=int(t["fill"].dayofweek))).strftime("%Y-%m-%d")
        by_week.setdefault(wk, []).append(t)
    print(f"{len(by_week)} weeks | {len(verdicts)} verdicts answered [{tier}]")
    for wk in sorted(by_week):
        n = len(by_week[wk])
        answered = sum(1 for t in by_week[wk] for k in verdicts if k[0] == t["trade_id"])
        print(f"  {wk}: {n} trades, {answered} verdicts")
    return 0


def cmd_plan(trades, bars, tier: str, week: str) -> int:
    verdicts = read_verdicts(tier)
    tape = load_tape(tier)
    out_dir = blobs_dir(tier)
    out_dir.mkdir(parents=True, exist_ok=True)
    dcache: dict = {}
    wk_start = pd.Timestamp(week, tz=NY)
    wk_end = wk_start + pd.Timedelta(days=7)

    jrows = build_journal(trades, bars, tape, verdicts, wk_start, dcache)
    week_trades = [t for t in trades if wk_start <= t["fill"] < wk_end]
    ver = spec_version()
    manifest = []
    for t in week_trades:
        path = day_path(t, bars)
        if not len(path):
            continue
        cx = canon_exit_of(t, path)
        state = {"stop": t["stop"], "extended": False, "reason": "",
                 "peak": t["entry"], "canon_exit_here": False}
        for minute, why in reachable_points(t, path, cx, verdicts):
            if (t["trade_id"], minute.isoformat()) in verdicts:
                continue
            state["reason"] = why
            state["canon_exit_here"] = minute == cx[0]
            b = build_briefing(briefing_trade(t), minute, state, bars, tape,
                               load_depth(t["day"], dcache))
            if tier == "bar":
                b.pop("flow", None)
            ps = path_states(t, bars.loc[bars.index < minute], minute)
            if ps:
                b["path_states"] = ps
            b["journal"] = journal_digest(jrows, like=b)
            b["agent_version"] = ver
            stem = f"{t['trade_id']}__{minute.strftime('%H%M')}"
            (out_dir / f"{stem}.briefing.json").write_text(
                json.dumps(b, sort_keys=True, separators=(",", ":"), default=str))
            manifest.append({"trade_id": t["trade_id"], "day": t["day"],
                             "decision_minute": minute.isoformat(), "reason": why,
                             "stem": stem})
    mpath = out_dir / f"round_{week}.json"
    mpath.write_text(json.dumps(manifest, indent=1))
    print(f"[{tier}] week {week}: {len(week_trades)} trades -> {len(manifest)} new "
          f"briefings | journal {len(jrows)} rows | spec {ver}")
    print(f"manifest: {mpath.relative_to(ROOT)}")
    return 0


def cmd_ingest(tier: str, file: str) -> int:
    src = Path(file)
    ok, bad = [], 0
    for line in src.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            v = IntradeVerdict(**json.loads(line))
            ok.append(json.dumps(v.model_dump(), default=str))
        except Exception as e:
            bad += 1
            print(f"  DROPPED: {str(e)[:160]}")
    with verdicts_path(tier).open("a") as f:
        for line in ok:
            f.write(line + "\n")
    print(f"[{tier}] ingested {len(ok)} verdicts, dropped {bad} (fail-closed)")
    return 0


def cmd_grade(trades, bars, tier: str) -> int:
    verdicts = read_verdicts(tier)
    print(f"[{tier}] {len(verdicts)} valid verdicts\n")
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
            rows.append({**base, "arm": name, **{k: v for k, v in r.items()
                                                if k != "partials_taken"}})
        r, _ = replay_with_verdicts(t, path, cx, verdicts)
        rows.append({**base, "arm": "agent",
                     **{k: v for k, v in r.items() if k != "partials_taken"}})
    D = pd.DataFrame(rows)
    out = ROOT / f"output/capture_agents_{tier}.parquet"
    D.to_parquet(out, index=False)

    M = pd.read_parquet(ROOT / "output/capture_mfe_fit.parquet")[["ts", "direction", "mfe_R"]]
    print(f"{'arm':<11}{'1-lot $':>12}{'meanR':>8}{'medR':>8}{'WR':>5}{'capture':>9}")
    for name in list(MECH_ARMS) + ["agent"]:
        d = D[D.arm == name].merge(M, on=["ts", "direction"], how="left")
        pos = d[d.mfe_R > 0.1]
        cap = (pos.R / pos.mfe_R).clip(-1, 1).mean()
        print(f"{name:<11}${d.dollars.sum():>+11,.0f}{d.R.mean():>8.3f}"
              f"{d.R.median():>8.3f}{(d.dollars > 0).mean() * 100:>4.0f}%{cap:>9.3f}")
    a = D[D.arm == "agent"].set_index("trade_id")
    c = D[D.arm == "canon"].set_index("trade_id")
    diff = a.dollars - c.dollars
    print(f"\nagent vs canon: ${diff.sum():+,.0f} | better {int((diff > 0).sum())} "
          f"worse {int((diff < 0).sum())} unchanged {int((diff == 0).sum())}")
    for (era, sess), g in a.groupby(["era", "sess"]):
        gd = (g.dollars - c.loc[g.index].dollars)
        print(f"  {era}·{sess}: Δ${gd.sum():+,.0f} on {len(g)}")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["weeks", "plan", "ingest", "grade"])
    ap.add_argument("--tier", required=True, choices=TIERS)
    ap.add_argument("--week", default=None)
    ap.add_argument("--file", default=None)
    ap.add_argument("--span", default="fit", choices=["fit", "holdout"])
    a = ap.parse_args()
    if a.mode == "ingest":
        raise SystemExit(cmd_ingest(a.tier, a.file))
    trades = load_trades(a.span)
    if a.mode == "weeks":
        raise SystemExit(cmd_weeks(trades, a.tier))
    bars = add_vwap(load_bars_ny())
    if a.mode == "plan":
        if not a.week:
            raise SystemExit("--week required")
        raise SystemExit(cmd_plan(trades, bars, a.tier, a.week))
    raise SystemExit(cmd_grade(trades, bars, a.tier))


if __name__ == "__main__":
    main()
