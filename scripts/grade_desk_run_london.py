#!/usr/bin/env python3
"""Grade the London desk run against docs/PLAN-agents-capture-london.md §6-9.

Port of scripts/grade_desk_run2.py (claude/agents-capture-handoff-26rnvp), adapted:
baseline is V1 (not V8/three-rule canon), no session (pre/gold) split -- era is the
only stable stratifier at this n -- and the mechanical control (lock1r_2r) and oracle
ceiling are computed only on PAIRED trades (those where V1 had an exit moment to
anchor on; agent-only trades admitted by the dynamic one-at-a-time re-walk have no
V1 reference point, per PLAN §4b, and are reported separately, never silently folded
in or dropped).

    python -m scripts.grade_desk_run_london
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.capture_desk_run_london import (COMMISSION, PV, RUNS, SLIP, TICK,  # noqa: E402
                                             load_bars, load_candidates, sgn)
from scripts.london_combined_job import maxdd  # noqa: E402
from scripts.london_funded_test import fund  # noqa: E402

N_SHUFFLES = 1000
RNG = np.random.default_rng(20260731)


def walk(t: dict, bars: pd.DataFrame) -> dict | None:
    """One pass over a PAIRED trade's law path (V1's own exit moment as the anchor).
    Returns per-bar offset/open-R arrays (for the shuffle's realize()), the oracle
    ceiling, and the lock1r_2r control R. None for agent-only trades (no V1 anchor)."""
    if t["v1_exit_ts"] is None:
        return None
    s, entry, risk_pts = sgn(t["direction"]), t["entry"], t["risk"] / PV
    stop = t["stop"]
    flatten = pd.Timestamp(f"{t['day']} 15:55", tz="America/New_York")
    path = bars.loc[t["fill_ts"]:flatten]
    cx, cx_R = t["v1_exit_ts"], t["v1_R"]

    def r_of(px):
        return s * (px - entry) / risk_pts

    ix = path.index
    start = ix.searchsorted(t["fill_ts"], side="right")
    offs, openR = [], []
    peak = 0.0
    ctl_R, ctl_stop, ctl_lock, ctl_ts = None, stop, False, None
    for i in range(start, len(ix)):
        minute, bar = ix[i], path.iloc[i]
        off = int((minute - t["fill_ts"]).total_seconds() // 60)
        if minute >= flatten:
            break
        offs.append(off)
        openR.append(r_of(float(bar.open) - s * SLIP * TICK))
        stopped = (s > 0 and bar.low <= stop) or (s < 0 and bar.high >= stop)
        if ctl_R is None:
            if (s > 0 and bar.low <= ctl_stop) or (s < 0 and bar.high >= ctl_stop):
                px = (min(ctl_stop, float(bar.open)) if s > 0
                      else max(ctl_stop, float(bar.open)))
                ctl_R, ctl_ts = r_of(px - s * SLIP * TICK), minute
            elif not ctl_lock and minute >= cx:
                if peak >= 2.0:
                    ctl_lock = True
                    ctl_stop = entry + s * 1.0 * risk_pts
                else:
                    ctl_R, ctl_ts = cx_R, minute
        fav = r_of(float(bar.high) if s > 0 else float(bar.low))
        peak = max(peak, fav)
        if stopped:
            break
    if ctl_R is None:
        ctl_R, ctl_ts = cx_R, cx
    oracle = max(peak, cx_R) if peak > 0 else cx_R
    return {"offs": np.array(offs), "openR": np.array(openR), "oracle_R": oracle,
           "ctl_R": ctl_R, "ctl_locked": ctl_lock, "ctl_ts": ctl_ts}


def realize(w: dict, m: int, fallback_R: float) -> float:
    j = int(np.searchsorted(w["offs"], m, side="right"))
    if j >= len(w["offs"]):
        return fallback_R
    return float(w["openR"][j])


def main() -> None:
    rows = [json.loads(l) for l in open(RUNS / "journal.jsonl")]
    T = {t["trade_id"]: t for t in load_candidates()}
    bars = load_bars()

    all_rows = rows
    paired = [r for r in rows if r.get("v1_R") is not None]
    agent_only = [r for r in rows if r.get("v1_R") is None]
    print(f"== POPULATION == {len(all_rows)} managed trades ({len(paired)} paired vs "
          f"V1, {len(agent_only)} agent-only -- admitted only under the agent's own "
          f"timing, no V1 anchor)")

    d = np.array([r["agent_R"] - r["v1_R"] for r in paired])
    aR = np.array([r["agent_R"] for r in paired])
    vR = np.array([r["v1_R"] for r in paired])
    n = len(d)
    print(f"\n== PAIRED STATS (n={n}) ==")
    print(f"agent {aR.sum():+.2f}R vs V1 {vR.sum():+.2f}R | delta {d.sum():+.2f}R "
          f"(mean {d.mean():+.4f}, median {np.median(d):+.4f}, sd {d.std(ddof=1):.3f})")
    tstat = d.mean() / (d.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    flips = RNG.choice([-1.0, 1.0], size=(100_000, n))
    p_sign = float((np.abs((flips * d).sum(axis=1)) >= abs(d.sum())).mean())
    print(f"t = {tstat:.2f} | sign-flip permutation p = {p_sign:.5f} (100k, two-sided)")
    k = min(3, n)
    topk = np.sort(d)[-k:]
    print(f"fragility: top-{k} deltas {np.round(topk, 2)} | delta without them "
          f"{d.sum() - topk.sum():+.2f}R "
          f"({'PASS' if d.sum() - topk.sum() > 0 else 'FAIL'})")
    print(f"win rate: agent {(aR > 0).mean() * 100:.1f}% vs V1 {(vR > 0).mean() * 100:.1f}%")
    if agent_only:
        aoR = np.array([r["agent_R"] for r in agent_only])
        print(f"\nagent-only trades (no V1 baseline, n={len(agent_only)}): "
              f"agent {aoR.sum():+.2f}R, WR {(aoR > 0).mean() * 100:.0f}% -- reported, "
              "not part of the paired delta above")

    print("\n== ERA SPLIT (kill: sign flip) ==")
    for era in ("2025", "2026"):
        m = np.array([r["day"].startswith(era) for r in paired])
        if m.sum():
            print(f"  fit-{era}: n={m.sum()} delta {d[m].sum():+.2f}R "
                  f"(mean {d[m].mean():+.4f})")
    print("== BUCKET SPLIT ==")
    for bucket in sorted({t["bucket"] for t in T.values()}):
        m = np.array([r.get("bucket") == bucket for r in paired])
        if m.sum():
            print(f"  {bucket}: n={m.sum()} delta {d[m].sum():+.2f}R "
                  f"(mean {d[m].mean():+.4f})")

    walks = {}
    for r in paired:
        t = T.get(r["trade_id"])
        if t is None:
            continue
        w = walk(t, bars)
        if w is not None:
            walks[r["trade_id"]] = w
    have = [r for r in paired if r["trade_id"] in walks]
    comm_r = np.array([COMMISSION / r["risk"] for r in have])  # risk already $-denominated
    ctl = np.array([walks[r["trade_id"]]["ctl_R"] for r in have]) - comm_r
    aR2 = np.array([r["agent_R"] for r in have])
    vR2 = np.array([r["v1_R"] for r in have])
    nlock = sum(walks[r["trade_id"]]["ctl_locked"] for r in have)
    print(f"\n== MECHANICAL CONTROL lock1r_2r (paired trades only, n={len(have)}, "
          f"commission-netted) ==")
    print(f"control {ctl.sum():+.2f}R (locked on {nlock} trades) | V1 {vR2.sum():+.2f}R | "
          f"agent {aR2.sum():+.2f}R")
    verdict = "agent BEATS best mechanical control" if aR2.sum() > ctl.sum() else "control wins — KILL"
    print(f"agent - control = {aR2.sum() - ctl.sum():+.2f}R ({verdict})")

    orc = np.array([walks[r["trade_id"]]["oracle_R"] for r in have])
    print(f"\n== ORACLE CEILING (report-only, paired trades) ==")
    if orc.sum() != 0:
        print(f"hindsight-optimal {orc.sum():+.2f}R | agent captures "
              f"{aR2.sum() / orc.sum() * 100:.1f}% of ceiling "
              f"(V1 {vR2.sum() / orc.sum() * 100:.1f}%)")

    held = np.array([r["held_min"] for r in have])
    replay_real = np.array([realize(walks[r["trade_id"]], int(held[i]), aR2[i])
                            for i, r in enumerate(have)])
    strata: dict = {}
    for i, r in enumerate(have):
        strata.setdefault((r["day"][:4], vR2[i] >= 0), []).append(i)
    nulls = np.empty(N_SHUFFLES)
    for kk in range(N_SHUFFLES):
        tot = 0.0
        for _, idxs in strata.items():
            perm = RNG.permutation(idxs)
            for i, j in zip(idxs, perm):
                tot += realize(walks[have[i]["trade_id"]], int(held[j]), aR2[i])
        nulls[kk] = tot
    p_null = float((nulls >= replay_real.sum()).mean())
    print(f"\n== CONVICTION SHUFFLE (timing reassigned within era x V1-sign strata, "
          f"{N_SHUFFLES} draws) ==")
    print(f"timing-only replay of agent exits: {replay_real.sum():+.2f}R "
          f"(actual agent {aR2.sum():+.2f}R adds partials/targets on top)")
    print(f"null: mean {nulls.mean():+.2f}R sd {nulls.std():.2f} "
          f"max {nulls.max():+.2f}R | p(null >= real) = {p_null:.4f} "
          f"({'PASS' if p_null < 0.05 else 'FAIL — coin with commentary'})")

    print("\n== FUNDED (flat $250 risk/trade, MNQ micros -- london_funded_test.py "
          "convention, paired trades) ==")
    for name, Rarr in (("V1", vR2), ("agent", aR2), ("lock1r_2r", ctl)):
        stop_pts = np.array([T[r["trade_id"]]["risk"] / PV for r in have])
        dollars = Rarr * stop_pts * PV
        frame = pd.DataFrame({"day": [r["day"] for r in have],
                              "fill_ts": [r["exit_ts"] for r in have],
                              "risk": stop_pts * PV, "dollars": dollars,
                              "era": [r["day"][:4] for r in have]})
        f = fund(frame, np.ones(len(frame)))
        dd = f.groupby("day").pl.sum()
        eq = dd.cumsum()
        print(f"  {name:10s}: net ${f.pl.sum():+,.0f} | worst day ${dd.min():+,.0f} | "
              f"maxDD ${(eq.cummax() - eq).max():,.0f}")


if __name__ == "__main__":
    main()
