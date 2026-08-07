#!/usr/bin/env python3
"""NY PRE-MARKET SURVIVOR BOOKS — the two frozen specs, as committed reproducible code.

The 2026-08-04 pre-market funnel (research/candidates/nypre-*.md) ended with two
survivors whose specs froze in their trial ledgers but whose sims lived only in
session-inline python. This script is the permanent home: it rebuilds both books
from raw data, emits them through the strategy-emission contract
(docs/CONTRACT-strategy-emission.md), and checks itself against the ledgered
numbers — any drift from the frozen spec fails loudly.

  nypre_gap  NYP-GAP-01 trial-7 freeze: inside-prior-range small-gap fade
             (|gap| <= 0.35% of open, open inside prior RTH range), d5-gated
             (09:25-09:29 pre-open delta leaning toward the fill), short/long at
             the 09:30 open toward prior close, stop 1x gap beyond entry, target
             prior close, time-stop 10:00, no BE. Skip if risk < 2 pts.
  nypre_inv  NYP-INV-01 trial-7 arm A1: overnight-inventory fade. Gate: >= 90% of
             04:00-09:30 pre-market 1-min closes above prior RTH close AND net
             selling delta on 08:00-09:29 minutes whose bar high tags the
             overnight high (within 0.1%) AND ONH at least 2 pts above the open.
             Short the 09:30 open, stop entry+20, exit 10:00 close, no BE.

Both books live on the flow span only (fp_minutes: 2025-06 .. 2026-07) because
both gates read the footprint tape. Accounting: 1 pt base friction, $160 risked
per trade (qty = 160 / (2 * risk_pts) MNQ), pl = 160 * net_pts / risk_pts.
Intrabar tie-break is CONSERVATIVE: the stop is checked before the target inside
a bar (ledger note, NYP-INV-01 trial 7).

    python -m scripts.nypre_book           # build, emit, self-check
    python -m scripts.nypre_book --arms    # also write the exit-arm day-level
                                           # return matrices PBO grades against
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCHEMA = "emission-v0.1-proposed"
FRICTION_PTS = 1.0
RISK_DOLLARS = 160.0
MNQ_PT = 2.0

# Trial-7 tournament reference lines (research/candidates/nypre-*.md) — the
# frozen-spec numbers under the STANDARDIZED conservative tie-break. The gap
# fade's trial-6 headline (PF 1.80, $+1,797) predates the standardization and is
# NOT the reference; the restatement is ledgered as trial 8 in the candidate
# file. pf here is the tournament convention: gross-win/gross-loss on net POINTS.
EXPECT = {
    "nypre_gap": dict(n=51, net_pts=406, dollars=837, pf_pts=1.61),
    "nypre_inv": dict(n=22, net_pts=295, dollars=2362, pf_pts=1.94),
}


def build_setups() -> list[dict]:
    """One row per flow-span session: everything both gates and both entries read."""
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["cal"] = B.ts.dt.date.astype(str)
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    rth = R.groupby("cal").agg(close=("close", "last"), hi=("high", "max"), lo=("low", "min"))

    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    fp = fp.assign(clock=fp.index.strftime("%H:%M"), gday=(fp.index + pd.Timedelta(hours=6)).date)
    fp["gday"] = fp["gday"].astype(str)

    days = sorted(set(B[B.gday >= "2025-06-02"].gday.unique()) & set(fp.gday.unique()))
    setups = []
    for d in days:
        g = B[B.gday == d]
        r = g[(g.clock >= "09:30") & (g.clock < "16:00")].sort_values("ts")
        pm = g[(g.clock >= "04:00") & (g.clock < "09:30")]
        f = fp[fp.gday == d]
        if len(r) < 100 or len(pm) < 100 or len(f) < 200:
            continue
        pcals = rth.index[rth.index < d]
        if not len(pcals):
            continue
        p = rth.loc[pcals[-1]]
        op = r.open.iloc[0]
        half = d[:4] + ("H1" if d[5:7] < "07" else "H2")
        d5 = f[(f.clock >= "09:25") & (f.clock < "09:30")].delta.sum()
        onh = g[(g.clock >= "18:00") | (g.clock < "09:30")].high.max()
        fw = f[(f.clock >= "08:00") & (f.clock < "09:30")]
        gm = g.set_index(g.ts.dt.floor("min"))[["high"]]
        near = fw.join(gm, how="inner")
        near = near[near.high >= onh - 0.001 * onh]
        absorb = near.delta.sum() if len(near) else np.nan
        sk = (pm.close > p.close).mean()
        w10 = r[r.clock < "10:00"]
        setups.append(dict(
            day=d, half=half, op=op, onh=onh, pclose=p.close, plo=p.lo, phi=p.hi,
            sk=sk, d5=d5, absorb=absorb,
            bar_ts=w10.ts.to_numpy(), bars=w10[["high", "low", "close"]].to_numpy(),
        ))
    return setups


def sim(direction: int, op: float, stp: float, bar_ts, bars,
        be_at: float | None = None, tgt: float | None = None):
    """March the 09:30-09:59 bars; stop before target inside a bar (conservative).

    Returns (net_pts_after_friction, risk_pts, exit_ts, exit_price, exit_reason).
    """
    cur_stp = stp
    risk = (stp - op) if direction < 0 else (op - stp)
    for t, (hi, lo, cl) in zip(bar_ts, bars):
        if direction < 0:
            if hi >= cur_stp:
                return op - cur_stp - FRICTION_PTS, risk, t, cur_stp, "stop"
            if tgt is not None and lo <= tgt:
                return op - tgt - FRICTION_PTS, risk, t, tgt, "target"
            if be_at and (op - lo) >= be_at:
                cur_stp = min(cur_stp, op)
        else:
            if lo <= cur_stp:
                return cur_stp - op - FRICTION_PTS, risk, t, cur_stp, "stop"
            if tgt is not None and hi >= tgt:
                return tgt - op - FRICTION_PTS, risk, t, tgt, "target"
            if be_at and (hi - op) >= be_at:
                cur_stp = max(cur_stp, op)
    t, cl = bar_ts[-1], bars[-1][2]
    pts = (op - cl) if direction < 0 else (cl - op)
    return pts - FRICTION_PTS, risk, t, cl, "time_1000"


def gap_gate(s: dict):
    """(direction, stop, target) if the day passes the frozen gap-fade gate, else None."""
    gap = s["op"] - s["pclose"]
    if not (s["plo"] <= s["op"] <= s["phi"] and 0 < abs(gap) <= s["op"] * 0.0035):
        return None
    direction = -1 if gap > 0 else 1
    confirmed = (direction == 1 and s["d5"] >= 0) or (direction == -1 and s["d5"] <= 0)
    if not confirmed:
        return None
    stp = s["op"] + abs(gap) * (1 if gap > 0 else -1)
    if abs(s["op"] - stp) < 2:
        return None
    return direction, stp, s["pclose"]


def inv_gate(s: dict) -> bool:
    """The frozen inventory-fade gate (long-side only; short side died at census)."""
    return bool(s["sk"] >= 0.9 and s["absorb"] == s["absorb"] and s["absorb"] < 0
                and (s["onh"] - s["op"]) >= 2)


def build_books(setups: list[dict]) -> dict[str, pd.DataFrame]:
    rows = {"nypre_gap": [], "nypre_inv": []}
    for s in setups:
        entry_ts = s["bar_ts"][0]
        g = gap_gate(s)
        if g is not None:
            direction, stp, tgt = g
            net, risk, xts, xpx, why = sim(direction, s["op"], stp, s["bar_ts"], s["bars"], tgt=tgt)
            rows["nypre_gap"].append(dict(
                strategy="nypre_gap", day=s["day"], half=s["half"], ts=entry_ts,
                direction="long" if direction > 0 else "short",
                fill_ts=entry_ts, exit_ts=xts, entry=s["op"], stop=stp,
                exit_price=xpx, exit_reason=why, risk_pts=risk,
                qty_mnq=RISK_DOLLARS / (MNQ_PT * risk), risk_dollars=RISK_DOLLARS,
                net_pts=net, pl=RISK_DOLLARS * net / risk,
                sess="ny-pre-open", conviction=1.0,
            ))
        if inv_gate(s):
            stp = s["op"] + 20.0
            net, risk, xts, xpx, why = sim(-1, s["op"], stp, s["bar_ts"], s["bars"])
            rows["nypre_inv"].append(dict(
                strategy="nypre_inv", day=s["day"], half=s["half"], ts=entry_ts,
                direction="short",
                fill_ts=entry_ts, exit_ts=xts, entry=s["op"], stop=stp,
                exit_price=xpx, exit_reason=why, risk_pts=risk,
                qty_mnq=RISK_DOLLARS / (MNQ_PT * risk), risk_dollars=RISK_DOLLARS,
                net_pts=net, pl=RISK_DOLLARS * net / risk,
                sess="ny-pre-open", conviction=1.0,
            ))
    return {k: pd.DataFrame(v) for k, v in rows.items()}


def _head_commit() -> str:
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                       text=True, cwd=ROOT)
    return r.stdout.strip() or "unknown"


def manifest(name: str, E: pd.DataFrame) -> dict:
    spec = {
        "nypre_gap": dict(
            vault_id="strategy:nypre-gap-engine",
            mechanism_families=["session-structure", "order-flow"],
            input_columns=["gap_pts", "prior_rth_range", "d5_preopen_delta"],
            ledger="research/candidates/nypre-gap-engine.md",
        ),
        "nypre_inv": dict(
            vault_id="strategy:nypre-inventory-correction",
            mechanism_families=["overnight-structure", "order-flow"],
            input_columns=["pm_close_share_vs_prior_close", "onh", "absorb_delta_at_onh"],
            ledger="research/candidates/nypre-inventory-correction.md",
        ),
    }[name]
    return {
        "schema": SCHEMA, "strategy": name, "vault_id": spec["vault_id"],
        "span": "flow-fit", "key": ["strategy", "ts", "direction"],
        "sessions": ["ny-pre-open"],
        "session_window": "entry 09:30 open, hard exit 10:00 (holds through the bell "
                          "by design — semantics ruling logged in the candidate file)",
        "signal_ts_is_fill": True,
        "mechanism_families": spec["mechanism_families"],
        "input_columns": spec["input_columns"],
        "sizing_regime": f"research-native fixed-${int(RISK_DOLLARS)}-risk "
                         "(1/risk MNQ sizing; NOT funded-governed)",
        "execution_semantics": {"two_sessions": False, "close_reverse": False,
                                "one_per_level": False},
        "commission_included": True,   # 1 pt base friction folded into net_pts/pl
        "exit_reason_vocab": sorted(set(E.exit_reason)),
        "counts": {"rows": int(len(E)), "days": int(E.day.nunique()),
                   "span_days": f"{E.day.min()}..{E.day.max()}",
                   "net_pl": int(round(E.pl.sum()))},
        "provenance": {
            "commit": _head_commit(),
            "book": {"generator": "scripts/nypre_book.py", "spec_frozen_in": spec["ledger"]},
            "reproduce": "python -m scripts.nypre_book",
            "holdout_looks_spent": 0,
            "gaps": ["research-native sizing (contract §7 class)",
                     "flow span only — both gates read the footprint tape",
                     "small n: the ledgered §2.2 warning applies to every statistic"],
        },
    }


INV_ARMS = {
    "A0_onh": (lambda s: s["onh"], None),
    "A1_20": (lambda s: s["op"] + 20, None),
    "A2_30": (lambda s: s["op"] + 30, None),
    "A3_onh_be15": (lambda s: s["onh"], 15),
    "A4_20_be15": (lambda s: s["op"] + 20, 15),
}
GAP_ARMS = {"G0_1x": (1.0, None), "G1_half": (0.5, None),
            "G2_1x_be10": (1.0, 10), "G3_half_be10": (0.5, 10)}


def arm_matrices(setups: list[dict]) -> dict[str, pd.DataFrame]:
    """Day-level P&L per exit arm — the T x N matrices PBO's CSCV consumes.

    Rows are ALL flow-span sessions (no-trade days = 0), columns the declared arms
    from the trial-7 tournaments. Day-level rows per the pbo.py leakage note.
    """
    all_days = [s["day"] for s in setups]
    out = {}
    inv = pd.DataFrame(0.0, index=all_days, columns=list(INV_ARMS))
    for s in setups:
        if not inv_gate(s):
            continue
        for arm, (stp_f, be) in INV_ARMS.items():
            net, risk, *_ = sim(-1, s["op"], stp_f(s), s["bar_ts"], s["bars"], be_at=be)
            inv.loc[s["day"], arm] = RISK_DOLLARS * net / risk
    out["nypre_inv"] = inv
    gap = pd.DataFrame(0.0, index=all_days, columns=list(GAP_ARMS))
    for s in setups:
        g = gap_gate(s)
        if g is None:
            continue
        direction, _, tgt = g
        gp = s["op"] - s["pclose"]
        for arm, (k, be) in GAP_ARMS.items():
            stp = s["op"] + abs(gp) * k * (1 if gp > 0 else -1)
            if abs(s["op"] - stp) < 2:
                continue
            net, risk, *_ = sim(direction, s["op"], stp, s["bar_ts"], s["bars"],
                                be_at=be, tgt=tgt)
            gap.loc[s["day"], arm] = RISK_DOLLARS * net / risk
    out["nypre_gap"] = gap
    return out


def summarize(E: pd.DataFrame, name: str) -> dict:
    net = E.net_pts
    gwp, glp = net[net > 0].sum(), -net[net <= 0].sum()
    gwd, gld = E.pl[E.pl > 0].sum(), -E.pl[E.pl <= 0].sum()
    cum = E.pl.cumsum()
    halves = {h: round(float(x.sum())) for h, x in net.groupby(E.half)}
    return dict(n=len(E), wr=float((net > 0).mean()), net_pts=float(net.sum()),
                dollars=float(E.pl.sum()), pf_pts=float(gwp / max(glp, 1e-9)),
                pf_usd=float(gwd / max(gld, 1e-9)),
                dd=float((cum.cummax() - cum).max()), halves=halves)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", action="store_true", help="also write exit-arm matrices")
    a = ap.parse_args()

    setups = build_setups()
    books = build_books(setups)
    ok = True
    for name, E in books.items():
        s = summarize(E, name)
        exp = EXPECT[name]
        checks = [("n", s["n"], exp["n"], 0),
                  ("dollars", round(s["dollars"]), exp["dollars"], 5),
                  ("pf_pts", round(s["pf_pts"], 2), exp["pf_pts"], 0.011),
                  ("net_pts", round(s["net_pts"]), exp["net_pts"], 5)]
        bad = [f"{k}: got {g} want {w}" for k, g, w, tol in checks if abs(g - w) > tol]
        status = "MATCHES LEDGER" if not bad else "DRIFT: " + "; ".join(bad)
        print(f"{name}: n={s['n']} WR {s['wr']:.0%} {s['net_pts']:+.0f}pts "
              f"${s['dollars']:+,.0f} PF(pts) {s['pf_pts']:.2f} PF($) {s['pf_usd']:.2f} "
              f"DD ${s['dd']:,.0f} halves={s['halves']}  [{status}]")
        ok &= not bad
        E.to_parquet(ROOT / f"output/emission_{name}_fit.parquet", index=False)
        with open(ROOT / f"output/emission_{name}_fit.manifest.yaml", "w") as f:
            yaml.safe_dump(manifest(name, E), f, sort_keys=False)
    if a.arms:
        for name, M in arm_matrices(setups).items():
            M.to_parquet(ROOT / f"output/nypre_arms_{name}.parquet")
            print(f"arms {name}: {M.shape[0]} days x {list(M.columns)}")
    if not ok:
        print("SELF-CHECK FAILED — the rebuilt books do not match the frozen ledgers")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
