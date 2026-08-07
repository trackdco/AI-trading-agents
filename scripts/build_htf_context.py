#!/usr/bin/env python3
"""HTF context per session — the input the bias agent reads. Step 1 of SPEC-htf-bias-agent.

Pure data. No agent, no model, no judgement. This file only assembles what was knowable before
a session opened, in the vocabulary the agent is taught to reason in (docs/SPEC-htf-bias-agent
§4 and §5).

CAUSALITY IS THE ENTIRE VALUE OF THIS FILE. Every field is built from sessions strictly before
the target day, plus the overnight up to the session open. Nothing from the session being
predicted. This project has produced three separate false findings from causality leaks -- the
depth read one bar late, the +10.57pt "confirmation" head start, and a per-day/full-dataset
indexing bug that voided every number one script produced -- so the rule here is structural:
build the per-session table first, shift once, and never index a full-dataset array with a
per-day counter.

ANONYMISATION IS BUILT IN, NOT BOLTED ON. `--anon` emits the same context with dates stripped,
prices normalised to an index at 100, and the instrument removed. An LLM asked about a dated
NQ session may simply recall the answer; that is the same class of leak as the above, except it
hides inside the model where a diff cannot catch it. The contamination audit in the spec (§7)
runs against this output, and if the agent can identify the period the whole result is void.

WHAT IS DELIBERATELY NOT HERE: any interpretation. No bias, no "bullish", no scoring. The agent
does that. This file would be equally valid if the agent were replaced tomorrow.

    python -m scripts.build_htf_context [--anon] [--sessions AM,PM,E18,E20,LDN]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
BARS = ("data/reference/nq_1m_master.parquet", "data/reference/nq_1m_feb_jul2026.parquet")
RTH = (9 * 60 + 30, 16 * 60)
ASIA = (18 * 60, 3 * 60)          # 18:00 -> 03:00 next day, wraps
LONDON = (3 * 60, 9 * 60 + 30)
SESSION_OPEN = {"AM": 9 * 60 + 30, "PM": 14 * 60, "E18": 18 * 60,
                "E20": 20 * 60, "LDN": 3 * 60}
OUT = ROOT / "output/htf_context.jsonl"


def load() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
                   for p in BARS], ignore_index=True)
    b = b.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    t = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b["ts"] = t
    b["day"] = t.dt.strftime("%Y-%m-%d")
    b["hm"] = t.dt.hour * 60 + t.dt.minute
    iso = t.dt.isocalendar()
    b["wk"] = iso.year.astype(int) * 100 + iso.week.astype(int)
    b["mo"] = t.dt.strftime("%Y-%m")
    return b


def swings(h: np.ndarray, lo: np.ndarray, k: int = 2) -> tuple[list, list]:
    """Fractal pivots, confirmed k bars later so nothing is known early."""
    sh, sl = [], []
    for i in range(k, len(h) - k):
        if (h[i - k:i] < h[i]).all() and (h[i + 1:i + k + 1] < h[i]).all():
            sh.append((i, float(h[i])))
        if (lo[i - k:i] > lo[i]).all() and (lo[i + 1:i + k + 1] > lo[i]).all():
            sl.append((i, float(lo[i])))
    return sh, sl


def fvgs(o: np.ndarray, h: np.ndarray, lo: np.ndarray, c: np.ndarray,
         idx: list) -> list[dict]:
    """Fair value gaps: 3-bar imbalance where bar1 and bar3 do not overlap.
    Returned with the LATER price action checked for fill, so only UNFILLED ones survive."""
    out = []
    for i in range(2, len(h)):
        if lo[i] > h[i - 2]:                                   # bullish FVG
            out.append({"type": "FVG", "dir": "bull", "top": float(lo[i]),
                        "bottom": float(h[i - 2]), "at": idx[i]})
        if h[i] < lo[i - 2]:                                   # bearish FVG
            out.append({"type": "FVG", "dir": "bear", "top": float(lo[i - 2]),
                        "bottom": float(h[i]), "at": idx[i]})
    return out


def unfilled(gaps: list[dict], h: np.ndarray, lo: np.ndarray, upto: int) -> list[dict]:
    live = []
    for g in gaps:
        j = g["_i"] + 1 if "_i" in g else None
        if j is None or j >= upto:
            continue
        seg_h, seg_l = h[j:upto], lo[j:upto]
        if not len(seg_h):
            continue
        # filled once price trades back through the whole gap
        if g["dir"] == "bull" and seg_l.min() <= g["bottom"]:
            continue
        if g["dir"] == "bear" and seg_h.max() >= g["top"]:
            continue
        live.append(g)
    return live


def equal_levels(vals: list[float], tol: float) -> list[float]:
    """Prices revisited within tol — the 'equal highs/lows' that hold resting liquidity."""
    out, used = [], set()
    for i, a in enumerate(vals):
        if i in used:
            continue
        grp = [a]
        for j in range(i + 1, len(vals)):
            if j not in used and abs(vals[j] - a) <= tol:
                grp.append(vals[j])
                used.add(j)
        if len(grp) >= 2:
            out.append(float(np.mean(grp)))
    return out


def build(b: pd.DataFrame, sessions: list[str]) -> list[dict]:
    rth = b[(b.hm >= RTH[0]) & (b.hm < RTH[1])]
    S = rth.groupby("day").agg(o=("open", "first"), h=("high", "max"),
                               l=("low", "min"), c=("close", "last"))
    days = list(S.index)
    di = {d: i for i, d in enumerate(days)}
    # Week/month key PER RTH DAY, aligned to `days` by LABEL. `b` is indexed by the ALL-BARS day
    # list, which is LONGER than the RTH one -- Sunday evenings and holidays carry overnight bars
    # but no RTH. Slicing it positionally with the RTH counter `n` drifts further apart the deeper
    # into the corpus you go, and it returned a previous-week high that was weeks stale on 100% of
    # sessions. Reindex by label; never slice one table with another's counter.
    wk_d = b.groupby("day").wk.first().reindex(days).to_numpy()
    mo_d = b.groupby("day").mo.first().reindex(days).to_numpy()

    dh, dl, dc = S.h.to_numpy(), S.l.to_numpy(), S.c.to_numpy()

    def period_range(keys: np.ndarray, upto: int) -> dict | None:
        """High/low of the most recent COMPLETED period, from the same daily array as everything
        else. Deriving this from a second groupby is what broke it before."""
        prior = keys[:upto][keys[:upto] < keys[upto]]
        if not len(prior):
            return None
        m = keys[:upto] == prior.max()
        return {"high": float(dh[:upto][m].max()), "low": float(dl[:upto][m].min())}

    dgaps = fvgs(S.o.to_numpy(), dh, dl, dc, days)
    for k, g in enumerate(dgaps):
        g["_i"] = di[g["at"]]

    out = []
    for n, day in enumerate(days):
        if n < 65:
            continue
        prev = days[n - 1]
        atr = float(np.mean(dh[n - 14:n] - dl[n - 14:n]))
        # ---- dealing range from recent daily swings (strictly prior) ----
        sh, sl = swings(dh[:n], dl[:n], k=2)
        rng_hi = sh[-1][1] if sh else float(dh[n - 20:n].max())
        rng_lo = sl[-1][1] if sl else float(dl[n - 20:n].min())
        if rng_hi <= rng_lo:
            rng_hi, rng_lo = float(dh[n - 20:n].max()), float(dl[n - 20:n].min())
        eq = (rng_hi + rng_lo) / 2.0

        base = {
            "day": day, "session_atr_20d": round(atr, 2),
            "prev_day": {"high": float(dh[n - 1]), "low": float(dl[n - 1]),
                         "close": float(dc[n - 1]),
                         "close_pos": round(float((dc[n - 1] - dl[n - 1]) /
                                                  max(dh[n - 1] - dl[n - 1], 1e-9)), 3)},
            "prev_week": period_range(wk_d, n),
            "prev_month": period_range(mo_d, n),
            "dealing_range": {"high": round(rng_hi, 2), "low": round(rng_lo, 2),
                              "equilibrium": round(eq, 2)},
            "ipda": {f"{k}d": {"high": float(dh[n - k:n].max()),
                               "low": float(dl[n - k:n].min())} for k in (20, 40, 60)},
            "equal_highs": [round(x, 2) for x in
                            equal_levels([float(v) for _, v in swings(dh[:n], dl[:n])[0][-12:]],
                                         atr * 0.10)],
            "equal_lows": [round(x, 2) for x in
                           equal_levels([float(v) for _, v in swings(dh[:n], dl[:n])[1][-12:]],
                                        atr * 0.10)],
            "unfilled_daily_fvg": [
                {"dir": g["dir"], "top": round(g["top"], 2), "bottom": round(g["bottom"], 2),
                 "age_days": n - g["_i"]}
                for g in unfilled(dgaps, dh, dl, n) if n - g["_i"] <= 60][-6:],
            "daily_ohlc_20": [[round(float(x), 2) for x in
                               (S.o.iloc[i], dh[i], dl[i], dc[i])] for i in range(n - 20, n)],
        }

        gday = b[b.day == day]
        for s in sessions:
            op = SESSION_OPEN[s]
            # Everything strictly before the session opens is fair game. For AM (09:30) and
            # LDN (03:00) that means day n's RTH has NOT happened, so the last completed
            # session is n-1. For the EVENING sessions (18:00, 20:00) day n's RTH is already
            # COMPLETE, so n-1 would be stale by a full day -- the reference shifts forward.
            evening = s in ("E18", "E20")
            row = dict(base)
            if evening:
                row["prev_day"] = {"high": float(dh[n]), "low": float(dl[n]),
                                   "close": float(dc[n]),
                                   "close_pos": round(float((dc[n] - dl[n]) /
                                                            max(dh[n] - dl[n], 1e-9)), 3)}
                row["ipda"] = {f"{k}d": {"high": float(dh[n - k + 1:n + 1].max()),
                                         "low": float(dl[n - k + 1:n + 1].min())}
                               for k in (20, 40, 60)}
                row["daily_ohlc_20"] = [[round(float(x), 2) for x in
                                         (S.o.iloc[i], dh[i], dl[i], dc[i])]
                                        for i in range(n - 19, n + 1)]
            pre = gday[gday.hm < op]
            row["session"] = s
            row["session_open_hm"] = op
            if len(pre):
                row["overnight"] = {
                    "high": float(pre.high.max()), "low": float(pre.low.min()),
                    "last": float(pre.close.iloc[-1]),
                    "swept_prev_high": bool(pre.high.max() > dh[n - 1]),
                    "swept_prev_low": bool(pre.low.min() < dl[n - 1]),
                }
                px = float(pre.close.iloc[-1])
                row["position_in_range"] = round(float((px - rng_lo) /
                                                       max(rng_hi - rng_lo, 1e-9)), 3)
                row["premium_discount"] = ("premium" if px > eq else
                                           "discount" if px < eq else "equilibrium")
            else:
                row["overnight"] = None
                row["position_in_range"] = None
                row["premium_discount"] = None
            out.append(row)
    return out


# Keys whose values are NOT prices and must pass through the index scaling untouched.
# Getting this wrong is silent and destroys the field: position_in_range is a 0-1 ratio, and
# scaling it by 100/price turned 0.53 into 0.0025. age_days is a count of days.
NON_PRICE = {"position_in_range", "close_pos", "age_days", "session", "id", "dir", "type",
             "premium_discount", "swept_prev_high", "swept_prev_low", "session_open_hm"}


def anonymise(rows: list[dict]) -> list[dict]:
    """Strip everything identifying the period or instrument; index PRICES to 100.

    Ratios, counts and labels are passed through unchanged -- see NON_PRICE.

    THE ID IS SHUFFLED, and that is not cosmetic. Rows are built in date order, so a sequential
    id is a monotone proxy for the calendar: W000115 is early in the corpus and W004199 is late.
    That hands back exactly the period signal the rest of this function strips out. Ids are
    therefore drawn from a seeded permutation -- deterministic across rebuilds, but carrying no
    ordering."""
    order = list(range(len(rows)))
    random.Random(20260807).shuffle(order)
    out = []
    for i, r in zip(order, rows):
        ref = r["overnight"]["last"] if r.get("overnight") else r["prev_day"]["close"]
        k = 100.0 / ref

        def sc(v, key=None):
            if key in NON_PRICE or isinstance(v, (bool, str)) or v is None:
                return v
            if isinstance(v, dict):
                return {a: sc(x, a) for a, x in v.items()}
            if isinstance(v, list):
                return [sc(x, key) for x in v]
            return round(v * k, 4)

        a = {kk: sc(vv, kk) for kk, vv in r.items() if kk not in ("day", "session_open_hm")}
        a["id"] = f"W{i:06d}"
        a["session"] = r["session"]          # session identity is legitimate context
        a["_truth_day"] = r["day"]           # underscore = never shown to the agent
        out.append(a)
    return out


def sanity(rows: list[dict]) -> None:
    """Hard invariants, checked on every build. A stale prev_week survived a code review and a
    committed artefact because nothing here asserted that it had to sit inside the price history
    it was drawn from. These are the cheap containment checks that catch that whole family."""
    bad: list[str] = []
    for r in rows:
        d20 = r["daily_ohlc_20"]
        hi20, lo20 = max(x[1] for x in d20), min(x[2] for x in d20)
        hi60, lo60 = r["ipda"]["60d"]["high"], r["ipda"]["60d"]["low"]
        tag = f"{r.get('day', r.get('id'))} {r['session']}"
        # last 20 daily bars END on the reference day, so the prior WEEK is inside them
        pw = r.get("prev_week")
        if pw and not (lo20 - 1e-6 <= pw["low"] and pw["high"] <= hi20 + 1e-6):
            bad.append(f"{tag}: prev_week {pw} outside 20-bar range [{lo20}, {hi20}]")
        # the prior MONTH can predate 20 bars, but never the 60-day lookback
        pm = r.get("prev_month")
        if pm and not (lo60 - 1e-6 <= pm["low"] and pm["high"] <= hi60 + 1e-6):
            bad.append(f"{tag}: prev_month {pm} outside 60d range [{lo60}, {hi60}]")
        # prev_day must BE the last bar of the series handed over -- no off-by-one
        pd_ = r["prev_day"]
        if abs(pd_["high"] - d20[-1][1]) > 1e-6 or abs(pd_["low"] - d20[-1][2]) > 1e-6:
            bad.append(f"{tag}: prev_day does not match the last of daily_ohlc_20")
    if bad:
        for b in bad[:10]:
            print(f"  SANITY FAIL {b}", file=sys.stderr)
        raise SystemExit(f"sanity: {len(bad):,}/{len(rows):,} rows failed containment")
    print(f"sanity: {len(rows):,} rows pass prev_week / prev_month / prev_day containment")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anon", action="store_true")
    ap.add_argument("--sessions", default="AM,PM,E18,E20,LDN")
    a = ap.parse_args()
    b = load()
    rows = build(b, a.sessions.split(","))
    sanity(rows)
    if a.anon:
        rows = anonymise(rows)
    p = OUT if not a.anon else OUT.with_name("htf_context_anon.jsonl")
    with p.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {p.relative_to(ROOT)} — {len(rows):,} session-contexts")
    ex = rows[len(rows) // 2]
    print(f"\nexample ({'anonymised' if a.anon else ex.get('day')}, {ex['session']}):")
    for k in ("dealing_range", "premium_discount", "position_in_range", "overnight",
              "equal_highs", "equal_lows"):
        if k in ex:
            print(f"  {k}: {ex[k]}")
    print(f"  unfilled_daily_fvg: {len(ex.get('unfilled_daily_fvg', []))} live")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
