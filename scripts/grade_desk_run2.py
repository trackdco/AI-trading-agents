"""Grade desk run 2 (phase 1, fit span) against the pre-registered protocol.

docs/PLAN-agents-capture-run.md §6-§9: per-trade paired stats with fragility,
era split (fit-2025 vs fit-2026 must not flip sign), conviction-shuffle null,
funded comparison (lucid + scaled600), best-mechanical-control comparison
(lock1r_2r re-run on the three-rule canon horizons), oracle ceiling.

All walks replicate manage_trade's bar mechanics exactly: session flatten at
bar open (09:30 pre / 15:55), close-and-reverse law with stop-first on the flip
bar, stop-first at min(stop, open) with slip, next-bar-open execution for
discretionary exits.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from scripts.capture_desk_run import COMMISSION, MONTHS, NY, PV, ROOT, RUNS, SLIP, TICK
from scripts.capture_replay import load_bars_ny, load_trades, sgn
import scripts.funded_book as fb

N_SHUFFLES = 1000
RNG = np.random.default_rng(20260730)


def build_trades() -> list[dict]:
    T = load_trades("fit")
    O = pd.read_parquet(ROOT / "output/aikido_cr_fit.parquet").set_index(["ts", "direction"])
    if "cr_suppressed" in O.columns:
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
    by_day: dict[str, list[dict]] = {}
    for t in T:
        by_day.setdefault(t["day"], []).append(t)
    for _, g in by_day.items():
        g.sort(key=lambda x: x["fill"])
        for i, ta in enumerate(g):
            ta["flip_at"] = ta["flip_px"] = None
            for b in g[i + 1:]:
                if b["direction"] != ta["direction"]:
                    ta["flip_at"], ta["flip_px"] = b["fill"], float(b["entry"])
                    break
    return [t for t in T if t["day"][:7] in MONTHS]


def walk(t: dict, bars: pd.DataFrame) -> dict:
    """One pass over the trade's law path. Returns the law-terminal event, the
    oracle ceiling, the lock1r_2r control R, and the arrays the shuffle needs."""
    s, entry, risk = sgn(t["direction"]), t["entry"], t["risk"]
    stop = t["stop"]
    day = t["day"]
    path = bars.loc[t["fill"]:t["fill"].normalize() + pd.Timedelta(hours=16, minutes=10)]
    path = path[path.index.strftime("%Y-%m-%d") == day]
    flatten = pd.Timestamp(f"{day} 09:30" if t["sess"] == "pre" else f"{day} 15:55", tz=NY)
    flip_at, flip_px = t.get("flip_at"), t.get("flip_px")
    cx, cx_px = t["exit"], t["exit_price"]

    def r_of(px):
        return s * (px - entry) / risk

    ix = path.index
    start = ix.searchsorted(t["fill"], side="right")
    offs, openR = [], []          # per-bar: minutes since fill, R if exiting at this open
    law_off, law_R = None, None   # law-terminal event (flatten / flip / stop)
    peak = 0.0                    # favorable-extreme R, bar-inclusive (oracle ceiling)
    peak_pre_stop = 0.0           # favorable-extreme R seen strictly before the stop bar
    # lock1r_2r control state
    ctl_R, ctl_stop, ctl_lock, ctl_ts = None, stop, False, None
    for i in range(start, len(ix)):
        minute, bar = ix[i], path.iloc[i]
        off = int((minute - t["fill"]).total_seconds() // 60)
        if minute >= flatten:
            law_off, law_R = off, r_of(float(bar.open) - s * SLIP * TICK)
            if ctl_R is None:
                ctl_R, ctl_ts = law_R, minute
            break
        if flip_at is not None and minute >= flip_at:
            if (s > 0 and bar.low <= stop) or (s < 0 and bar.high >= stop):
                px = (min(stop, float(bar.open)) if s > 0 else max(stop, float(bar.open)))
                law_off, law_R = off, r_of(px - s * SLIP * TICK)
            else:
                law_off, law_R = off, r_of(flip_px)
            if ctl_R is None:
                ctl_ts = minute
                if (s > 0 and bar.low <= ctl_stop) or (s < 0 and bar.high >= ctl_stop):
                    px = (min(ctl_stop, float(bar.open)) if s > 0
                          else max(ctl_stop, float(bar.open)))
                    ctl_R = r_of(px - s * SLIP * TICK)
                else:
                    ctl_R = r_of(flip_px)
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
                if peak >= 2.0:   # +2R printed: refuse the canon exit, lock stop at +1R
                    ctl_lock = True
                    ctl_stop = entry + s * 1.0 * risk
                else:
                    ctl_R, ctl_ts = r_of(cx_px), minute
        fav = r_of(float(bar.high) if s > 0 else float(bar.low))
        if not stopped:
            peak_pre_stop = max(peak_pre_stop, fav)
        peak = max(peak, fav)
        if stopped:
            px = (min(stop, float(bar.open)) if s > 0 else max(stop, float(bar.open)))
            law_off, law_R = off, r_of(px - s * SLIP * TICK)
            break
    if law_R is None:             # bars ran out (early close) — settle at last close
        law_off = offs[-1] + 1 if offs else 0
        law_R = r_of(float(path.iloc[-1].close)) if len(path) else 0.0
    if ctl_R is None:
        ctl_R = law_R
    if ctl_ts is None:
        ctl_ts = ix[-1] if len(ix) else t["fill"]
    oracle = max(peak, law_R) if peak > 0 else law_R
    return {"offs": np.array(offs), "openR": np.array(openR),
            "law_off": law_off, "law_R": law_R,
            "oracle_R": oracle, "ctl_R": ctl_R, "ctl_locked": ctl_lock, "ctl_ts": ctl_ts}


def realize(w: dict, m: int) -> float:
    """R realized by the plan 'exit at offset m minutes' under the law walk:
    the decision executes at the next bar's open unless a law event lands first."""
    j = int(np.searchsorted(w["offs"], m, side="right"))
    if j >= len(w["offs"]):
        return w["law_R"]
    return float(w["openR"][j])


def main() -> None:
    rows = [json.loads(l) for l in open(RUNS / "journal.jsonl")]
    jmap = {r["trade_id"]: r for r in rows}
    T = build_trades()
    T = [t for t in T if t["trade_id"] in jmap]
    bars = load_bars_ny()
    walks = {t["trade_id"]: walk(t, bars) for t in T}

    d = np.array([jmap[t["trade_id"]]["agent_R"] - jmap[t["trade_id"]]["v8_R"] for t in T])
    aR = np.array([jmap[t["trade_id"]]["agent_R"] for t in T])
    vR = np.array([jmap[t["trade_id"]]["v8_R"] for t in T])
    n = len(d)
    print(f"== PAIRED STATS (n={n}) ==")
    print(f"agent {aR.sum():+.1f}R vs mech {vR.sum():+.1f}R | delta {d.sum():+.1f}R "
          f"(mean {d.mean():+.4f}, median {np.median(d):+.4f}, sd {d.std(ddof=1):.3f})")
    tstat = d.mean() / (d.std(ddof=1) / np.sqrt(n))
    flips = RNG.choice([-1.0, 1.0], size=(100_000, n))
    p_sign = float((np.abs((flips * d).sum(axis=1)) >= abs(d.sum())).mean())
    print(f"t = {tstat:.2f} | sign-flip permutation p = {p_sign:.5f} (100k, two-sided)")
    top3 = np.sort(d)[-3:]
    print(f"fragility: top-3 deltas {np.round(top3, 2)} | delta without them "
          f"{d.sum() - top3.sum():+.1f}R "
          f"({'PASS' if d.sum() - top3.sum() > 0 else 'FAIL'})")
    print(f"win rate: agent {(aR > 0).mean() * 100:.1f}% vs mech {(vR > 0).mean() * 100:.1f}%")

    print("\n== ERA SPLIT (kill: sign flip) ==")
    for era in ("2025", "2026"):
        m = np.array([t["day"].startswith(era) for t in T])
        print(f"  fit-{era}: n={m.sum()} delta {d[m].sum():+.1f}R (mean {d[m].mean():+.4f})")
    print("== SESSION SPLIT ==")
    for ss in ("pre", "gold"):
        m = np.array([t["sess"] == ss for t in T])
        print(f"  {ss}: n={m.sum()} delta {d[m].sum():+.1f}R (mean {d[m].mean():+.4f})")

    # ctl_R comes straight off prices; mech/agent R are commission-netted — net it too.
    comm_r = np.array([COMMISSION / (t["risk"] * PV) for t in T])
    ctl = np.array([walks[t["trade_id"]]["ctl_R"] for t in T]) - comm_r
    nlock = sum(walks[t["trade_id"]]["ctl_locked"] for t in T)
    print(f"\n== MECHANICAL CONTROL lock1r_2r (three-rule horizons, commission-netted) ==")
    print(f"control {ctl.sum():+.1f}R (locked on {nlock} trades) | mech {vR.sum():+.1f}R | "
          f"agent {aR.sum():+.1f}R")
    print(f"agent - control = {aR.sum() - ctl.sum():+.1f}R "
          f"({'agent BEATS best mech control' if aR.sum() > ctl.sum() else 'control wins — KILL'})")

    orc = np.array([walks[t["trade_id"]]["oracle_R"] for t in T])
    print(f"\n== ORACLE CEILING (report-only) ==")
    print(f"hindsight-optimal {orc.sum():+.1f}R | agent captures "
          f"{aR.sum() / orc.sum() * 100:.1f}% of ceiling (mech {vR.sum() / orc.sum() * 100:.1f}%)")

    held = np.array([jmap[t["trade_id"]]["held_min"] for t in T])
    replay_real = np.array([realize(walks[t["trade_id"]], int(held[i]))
                            for i, t in enumerate(T)])
    strata = {}
    for i, t in enumerate(T):
        strata.setdefault((t["sess"], vR[i] >= 0), []).append(i)
    nulls = np.empty(N_SHUFFLES)
    for k in range(N_SHUFFLES):
        tot = 0.0
        for _, idxs in strata.items():
            perm = RNG.permutation(idxs)
            for i, j in zip(idxs, perm):
                tot += realize(walks[T[i]["trade_id"]], int(held[j]))
        nulls[k] = tot
    p_null = float((nulls >= replay_real.sum()).mean())
    print(f"\n== CONVICTION SHUFFLE (timing reassigned within sess x mech-sign, "
          f"{N_SHUFFLES} draws) ==")
    print(f"timing-only replay of agent exits: {replay_real.sum():+.1f}R "
          f"(actual agent {aR.sum():+.1f}R adds partials/targets on top)")
    print(f"null: mean {nulls.mean():+.1f}R sd {nulls.std():.1f} "
          f"max {nulls.max():+.1f}R | p(null >= real) = {p_null:.4f} "
          f"({'PASS' if p_null < 0.05 else 'FAIL — coin with commentary'})")

    print("\n== FUNDED (static sizing, full span) ==")
    V = pd.DataFrame([{"trade_id": t["trade_id"], "day": t["day"], "ts": t["ts"],
                       "month": t["day"][:7], "fill": t["fill"], "exit": t["exit"],
                       "risk": t["risk"], "tier": t["tier"], "elite": t["elite"],
                       "dollars_1lot": t["dollars"], "sess": t["sess"]} for t in T])
    Va = V.copy()
    Va["dollars_1lot"] = [jmap[t]["agent_dollars"] for t in Va.trade_id]
    Va["exit"] = pd.to_datetime([jmap[t]["exit_ts"] for t in Va.trade_id], utc=True)
    Vc = V.copy()
    Vc["dollars_1lot"] = [walks[t]["ctl_R"] * r * PV - COMMISSION
                          for t, r in zip(Vc.trade_id, Vc.risk)]
    Vc["exit"] = pd.to_datetime([walks[t]["ctl_ts"] for t in Vc.trade_id], utc=True)
    for prof in ("lucid", "scaled600"):
        for name, frame in (("mech", V), ("agent", Va), ("lock1r_2r", Vc)):
            B = fb.run(frame.sort_values("fill", kind="mergesort"), prof)
            dd = B.groupby("day").pl.sum()
            eq = dd.cumsum()
            maxdd = float((eq.cummax() - eq).max())
            mg = dd.groupby(dd.index.str[:7]).sum()
            print(f"  {prof:9s} {name:5s}: net ${dd.sum():+,.0f} | worst day "
                  f"${dd.min():+,.0f} | maxDD ${maxdd:,.0f} | months green "
                  f"{(mg > 0).sum()}/{len(mg)}")


if __name__ == "__main__":
    main()
