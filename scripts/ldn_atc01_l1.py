#!/usr/bin/env python3
"""LDN-ATC-01 L1 — first P&L on the pre-London pullback.

AUTHORISED BY docs/PREREG-london-atc-L1.md (committed BEFORE this ran).
STAGE 1 ONLY: fit span 2025-01-01 -> 2026-07-15, bars only, in-sample, can only KILL.

Chain is frozen and inherited verbatim from docs/PREREG-london-atc-census.md.
GATE: the chain must reproduce the published census counts (108 / 69 / 39 and the
terminal-status funnel) BEFORE any P&L is computed. If it does not, this script stops.

    python -m scripts.ldn_atc01_l1
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LDN = "Europe/London"
TICK = 0.25
FIT_START, FIT_END = "2025-01-01", "2026-07-15"
COST_STACKS = (1.0, 2.0)          # points per round turn, prereg §5
HEADLINE_COST = 2.0               # strict stack is the headline


# ------------------------------------------------------------------ bars
def load_bars() -> pd.DataFrame:
    fr = []
    for f in ("nq_1m_master.parquet", "nq_1m_feb_jul2026.parquet"):
        d = pd.read_parquet(ROOT / "data/reference" / f,
                            columns=["ts_event", "open", "high", "low", "close", "volume"])
        fr.append(d)
    b = pd.concat(fr, ignore_index=True)
    # Databento OHLCV-1m `ts_event` is the bar START (left-labelled). Shift +1min so the
    # index is the bar CLOSE time; every window below is then right-closed/right-labelled
    # and "the 07:00 close" means the price AT 07:00. Verified against the L0 census's
    # own ref_px: on 2025-04-11 it is 18695.50, the close of the 06:59-START bar.
    # Getting this wrong puts every boundary one minute late.
    b["ts"] = pd.to_datetime(b["ts_event"], utc=True).dt.tz_convert(LDN) + pd.Timedelta(minutes=1)
    b = b.drop_duplicates(subset="ts").sort_values("ts").set_index("ts")
    b["day"] = b.index.date
    return b[["open", "high", "low", "close", "volume"]].join(b[["day"]])


def win(d: pd.DataFrame, lo: str, hi: str) -> pd.DataFrame:
    """Bars labelled strictly after `lo` and up to and including `hi` (right-closed)."""
    t = d.index.time
    return d[(pd.Index(t) > pd.Timestamp(lo).time()) & (pd.Index(t) <= pd.Timestamp(hi).time())]


def rs(d: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Right-closed, right-labelled resample: a bar labelled T contains only data <= T."""
    return d.resample(rule, label="right", closed="right").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last")).dropna()


# ------------------------------------------------------------------ chain
def classify(d: pd.DataFrame) -> dict:
    """One session -> terminal status + the chain's anchor values. Bars only, causal."""
    out = {"status": None, "bias": None, "ref": np.nan, "trig_ts": None}

    # BIAS: 03:30-07:00 split into halves
    h1, h2 = win(d, "03:30", "05:15"), win(d, "05:15", "07:00")
    if h1.empty or h2.empty:
        out["status"] = "no_bias"
        return out
    if h2.high.max() < h1.high.max() and h2.low.min() < h1.low.min():
        bias = "short"
    elif h2.high.max() > h1.high.max() and h2.low.min() > h1.low.min():
        bias = "long"
    else:
        out["status"] = "no_bias"
        return out
    out["bias"] = bias

    # reference: the close of the bar labelled 07:00
    at7 = d[pd.Index(d.index.time) == pd.Timestamp("07:00").time()]
    if at7.empty:
        out["status"] = "no_bias"
        return out
    ref = float(at7.close.iloc[0])
    out["ref"] = ref

    # PULLBACK: 07:00-08:00, price trades AGAINST the bias beyond the 07:00 close
    pb = win(d, "07:00", "08:00")
    if pb.empty:
        out["status"] = "bias_no_pullback"
        return out
    pulled = (pb.high.max() > ref) if bias == "short" else (pb.low.min() < ref)
    if not pulled:
        out["status"] = "bias_no_pullback"
        return out

    # LTA: >=2 consecutive 15m closes in the PULLBACK direction inside 07:00-08:00
    m15 = rs(d, "15min")
    p15 = win(m15, "07:00", "08:00")
    # Pullback direction is AGAINST the bias. Test each direction EXPLICITLY — `~(close >
    # open)` would count a flat bar (close == open) as directional and extend a run
    # through it. 2026-07-09's 07:45 bar closes exactly at its open and is precisely this
    # case: the negation form gives a run of 2 and a spurious trigger, the explicit form
    # gives 1 and matches the census.
    dirn = (p15.close > p15.open) if bias == "short" else (p15.close < p15.open)
    run = best = 0
    for v in dirn.to_numpy():
        run = run + 1 if v else 0
        best = max(best, run)
    if best < 2:
        out["status"] = "pullback_no_lta"
        return out

    # TRIGGER: 15m close AND its containing 30m close, both bias-aligned, 07:00-09:00.
    # Only realisable on 30m boundaries, where both bars close simultaneously.
    m30 = rs(d, "30min")
    t15, t30 = win(m15, "07:00", "09:00"), win(m30, "07:00", "09:00")
    for ts in t30.index:
        if ts not in t15.index:
            continue
        a, b = t15.loc[ts], t30.loc[ts]
        ok = (a.close < a.open and b.close < b.open) if bias == "short" \
            else (a.close > a.open and b.close > b.open)
        if ok:
            out["status"] = "triggered"
            out["trig_ts"] = ts
            return out
    out["status"] = "lta_no_trigger"
    return out


def sessions(b: pd.DataFrame) -> dict:
    """Qualifying sessions: >=200 one-minute bars in 00:00-10:00 London (census basis)."""
    keep = {}
    for day, d in b.groupby("day"):
        w = d[pd.Index(d.index.time) <= pd.Timestamp("10:00").time()]
        if len(w) >= 200:
            keep[day] = d
    return keep


def main() -> None:
    b = load_bars()
    S = sessions(b)
    S = {d: v for d, v in S.items() if str(FIT_START) <= str(d) <= str(FIT_END)}
    print(f"qualifying sessions in fit span: {len(S)}")

    rows = []
    for day, d in S.items():
        r = classify(d)
        r["day"] = day
        r["era"] = "2025" if str(day) < "2026-01-01" else "2026"
        rows.append(r)
    C = pd.DataFrame(rows)

    print("\n=== CENSUS-REPRODUCTION GATE (must match the published L0 before any P&L) ===")
    funnel = C.status.value_counts()
    published = {"no_bias": 87, "bias_no_pullback": 6, "pullback_no_lta": 160,
                 "lta_no_trigger": 30, "triggered": 108}
    print(f"{'status':<20}{'here':>7}{'published':>11}{'delta':>7}")
    for k, v in published.items():
        h = int(funnel.get(k, 0))
        print(f"{k:<20}{h:>7}{v:>11}{h - v:>+7}")
    print(f"{'fallback_only':<20}{'n/a':>7}{5:>11}{'--':>7}   (fallback arm not in the L1 default)")
    tr = C[C.status == "triggered"]
    e = tr.era.value_counts()
    print(f"\ntriggered by era: 2025={int(e.get('2025',0))} (published 69) | "
          f"2026={int(e.get('2026',0))} (published 39)")
    print("\ntrigger clock:")
    print(tr.trig_ts.map(lambda t: t.strftime('%H:%M')).value_counts().sort_index().to_string())
    C.to_parquet(ROOT / "output/ldn_atc01_l1_chain.parquet")
    print("\nchain written to output/ldn_atc01_l1_chain.parquet")




# =================================================================== L1 P&L
def simulate(d: pd.DataFrame, bias: str, trig_ts, ref: float, cost: float,
             target_mode: str = "structural") -> dict | None:
    """One trade. Stop ENTRY at the trigger candle's extreme; path starts at the FILL
    MINUTE (the NYA-LVL-01 defect); stop-before-target on a same-bar conflict (defect D2);
    both-orderings counted, never guessed. Returns None if the setup is unusable."""
    m15 = rs(d, "15min")
    if trig_ts not in m15.index:
        return None
    tc = m15.loc[trig_ts]
    if bias == "short":
        entry, stop = float(tc.low), float(tc.high)
    else:
        entry, stop = float(tc.high), float(tc.low)
    risk = abs(entry - stop)
    if risk <= 0:
        return None

    if target_mode == "structural":
        target = ref
        beyond = (target < entry - TICK) if bias == "short" else (target > entry + TICK)
        if not beyond:
            return {"skip": "target_not_beyond_entry", "risk": risk}
    else:                                    # fixed 1R secondary
        target = entry - risk if bias == "short" else entry + risk

    k = abs(target - entry) / risk

    fwd = d[(d.index > trig_ts) & (pd.Index(d.index.time) <= pd.Timestamp("10:00").time())]
    if fwd.empty:
        return {"skip": "no_forward_bars", "risk": risk}

    # --- entry fill: trade THROUGH by >= 1 tick, never on a touch
    hit = (fwd.low <= entry - TICK) if bias == "short" else (fwd.high >= entry + TICK)
    if not hit.any():
        return {"skip": "unfilled", "risk": risk, "k": k}
    fill_ts = hit.idxmax()

    path = fwd[fwd.index >= fill_ts]         # path starts AT the fill minute
    mfe = mae = 0.0
    both = False
    for ts, row in path.iterrows():
        adv = (entry - row.low) if bias == "short" else (row.high - entry)
        against = (row.high - entry) if bias == "short" else (entry - row.low)
        mfe, mae = max(mfe, adv), max(mae, against)
        s_hit = (row.high >= stop) if bias == "short" else (row.low <= stop)
        t_hit = (row.low <= target) if bias == "short" else (row.high >= target)
        if s_hit and t_hit:
            both = True
            r_gross, why = -1.0, "stop(bound)"     # conservative: stop first
            break
        if s_hit:
            r_gross, why = -1.0, "stop"
            break
        if t_hit:
            r_gross, why = k, "target"
            break
    else:
        last = float(path.close.iloc[-1])
        r_gross = ((entry - last) if bias == "short" else (last - entry)) / risk
        why = "flat_1000"
    return {"skip": None, "risk": risk, "k": k, "r_gross": r_gross,
            "r_net": r_gross - cost / risk, "exit": why, "both_orderings": both,
            "mfe_r": mfe / risk, "mae_r": mae / risk, "fill_ts": fill_ts}


if __name__ == "__main__":
    main()
