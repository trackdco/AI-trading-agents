#!/usr/bin/env python3
"""What was the ORDER FLOW doing while we were in the trade? — testing Angus's claim.

ANGUS 2026-07-27, two questions:
  (1) losers that were up >=1R first — "the order flow started going against us, and it
      ended up being a loser". Did it? And did flow turn BEFORE price did?
  (2) winners we exited that then ran much further — "I guarantee the order flow was
      backing that up as well ... in the instance where we exited, the order flow and
      everything was still heavily favouring our trade."

Both are falsifiable, and the tape covers the whole fit window (footprint 2025-06-01 ->
2026-07-19 vs trades 2025-06-02 -> 2026-07-10).

Method. Per-minute signed delta = B(buy aggressor) - A(sell aggressor), the convention
verified in `scripts/champion_journal_cvd.py`. Oriented to the trade: positive = flow WITH
the position. Every in-trade timeline is PATH-CORRECT — it ends the minute the original
stop would have been hit, so a dead position never inherits later flow.

    python -m scripts.intrade_flow_autopsy

Honest limits, stated up front:
  * 1-minute aggregated delta, not the raw tape. Intra-minute sequencing is lost.
  * Aggressor-signed volume only. No book pull/refresh, no absorption at the level, no
    iceberg detection — the things a human reads on a heatmap are NOT all in here.
  * Exit time is INFERRED (first minute price reaches the realized R) because the book
    stores exit_price, not exit_ts. Good enough for "was flow with us around then",
    not for tick-accurate attribution.
  * This is descriptive. A separating statistic here is a hypothesis for the holdout,
    not a rule.
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BARS = ROOT / "data/reference/nq_1m_master.parquet"
BOOK = ROOT / "output/canon_book.parquet"
CVD = ROOT / "data/reference/cvd"
NY = "America/New_York"
SESSION_END = 16 * 60
WIN = 15                      # trailing / forward flow window, minutes


def load_delta() -> pd.Series:
    """Per-minute signed delta (B - A) indexed by ET minute. int64 — uint32 wraps."""
    parts = []
    for f in sorted(glob.glob(str(CVD / "footprint_*.parquet"))):
        d = pd.read_parquet(f, columns=["ts_minute", "side", "volume"])
        d["volume"] = d["volume"].astype("int64")
        d["signed"] = np.where(d["side"] == "B", d["volume"], -d["volume"])
        parts.append(d.groupby("ts_minute")["signed"].sum())
    s = pd.concat(parts).groupby(level=0).sum().sort_index()
    s.index = pd.to_datetime(s.index, utc=True).tz_convert(NY)
    return s


def load_bars() -> pd.DataFrame:
    b = pd.read_parquet(BARS)
    ts = pd.to_datetime(b["ts_event"], utc=True).dt.tz_convert(NY)
    return b.assign(ts=ts, day=ts.dt.strftime("%Y-%m-%d"),
                    mins=ts.dt.hour * 60 + ts.dt.minute).sort_values("ts")


def timelines(book: pd.DataFrame, bars: pd.DataFrame, delta: pd.Series) -> pd.DataFrame:
    """One row per trade: flow measured at the moments that matter."""
    by_day = {d: g for d, g in bars.groupby("day")}
    rows = []
    for t in book.itertuples():
        g = by_day.get(str(t.day))
        if g is None:
            continue
        fill = pd.Timestamp(t.fill)
        fwd = g[(g.ts >= fill) & (g.mins <= SESSION_END)]
        if len(fwd) < 5:
            continue
        sign = 1.0 if t.direction == "long" else -1.0
        risk = float(t.risk)
        if risk <= 0:
            continue

        # path-correct: die on the original stop
        adverse = (fwd.low <= float(t.stop)) if sign > 0 else (fwd.high >= float(t.stop))
        alive = fwd.loc[:adverse.idxmax()] if adverse.any() else fwd
        if len(alive) < 3:
            continue

        # direction-oriented flow, aligned to the alive window
        d = delta.reindex(alive.ts).fillna(0.0).to_numpy() * sign
        favour = sign * (alive.high.to_numpy() - float(t.entry)) / risk   # running best-case R
        n = len(alive)

        # `d=d` binds this trade's flow array explicitly — a late-binding closure over the
        # loop variable would silently read the LAST trade's flow if these were ever called
        # outside the iteration that built them.
        def trail(i, d=d):      # flow over the WIN minutes ending at i
            return float(d[max(0, i - WIN + 1): i + 1].sum())

        def forward(i, d=d):    # flow over the WIN minutes after i
            return float(d[i + 1: i + 1 + WIN].sum())

        peak_i = int(np.argmax(favour))
        rec = {
            "day": t.day, "fill": t.fill, "win_": t.win_, "direction": t.direction,
            "risk": risk, "dollars": t.dollars, "realized_R": float(t.R),
            "mfe_R": float(favour[peak_i]), "peak_min": peak_i,
            "alive_min": n - 1, "stopped": bool(adverse.any()),
            "flow_total": float(d.sum()),
            "flow_at_peak": trail(peak_i),
            "flow_after_peak": forward(peak_i),
        }

        # where did CUMULATIVE flow top out, versus where price topped out?
        cum = np.cumsum(d)
        rec["flow_peak_min"] = int(np.argmax(cum))
        rec["flow_leads_price_min"] = peak_i - rec["flow_peak_min"]

        # THE MATCHED DECISION POINT: the first minute the trade is +1R, measured
        # identically for every trade regardless of outcome. Comparing winners-at-exit
        # with losers-at-peak is NOT apples to apples — those are different kinds of
        # moment, and the peak is only knowable afterwards. This is the moment an agent
        # actually faces, and the only fair place to ask whether flow separates.
        r1 = np.where(favour >= 1.0)[0]
        if len(r1):
            i1 = int(r1[0])
            rec["r1_min"] = i1
            rec["flow_at_r1"] = trail(i1)
            rec["R_after_r1"] = float(favour[i1:].max() - 1.0)   # further run from +1R
        else:
            rec["r1_min"] = np.nan
            rec["flow_at_r1"] = np.nan
            rec["R_after_r1"] = np.nan

        # the exit moment, inferred: first minute the trade reached its realized R
        hit = np.where(favour >= float(t.R) - 1e-9)[0]
        if len(hit):
            e = int(hit[0])
            rec["exit_min"] = e
            rec["flow_at_exit"] = trail(e)
            rec["flow_after_exit"] = forward(e)
            rec["R_after_exit"] = float(favour[e:].max() - t.R)
        else:
            rec["exit_min"] = np.nan
            rec["flow_at_exit"] = np.nan
            rec["flow_after_exit"] = np.nan
            rec["R_after_exit"] = np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def _pct_pos(s):
    s = s.dropna()
    return (s > 0).mean() * 100 if len(s) else np.nan


def main() -> None:
    for p in (BARS, BOOK):
        if not p.exists():
            raise SystemExit(f"missing {p}")
    C = pd.read_parquet(BOOK)
    taken = C[C["size"] > 0].copy()
    print("loading tape ...", flush=True)
    T = timelines(taken, load_bars(), load_delta())
    win, loss = T[T.dollars > 0], T[T.dollars <= 0]
    print(f"{len(T)} trades reconstructed — {len(win)} winners, {len(loss)} losers\n")

    # ---------------------------------------------------------------- Q1
    print("=" * 74)
    print("Q1 — LOSERS THAT WERE UP >=1R FIRST. Did flow turn against us at the peak?")
    print("=" * 74)
    up = loss[loss.mfe_R >= 1.0]
    print(f"n = {len(up)} of {len(loss)} losers ({len(up)/len(loss)*100:.0f}%)\n")
    print(f"{'':<26}{'median':>12}{'mean':>12}{'% positive':>13}")
    print("-" * 63)
    for lbl, s in [("flow INTO the peak (15m)", up.flow_at_peak),
                   ("flow AFTER the peak (15m)", up.flow_after_peak)]:
        print(f"{lbl:<26}{s.median():>12,.0f}{s.mean():>12,.0f}{_pct_pos(s):>12.0f}%")
    flipped = ((up.flow_at_peak > 0) & (up.flow_after_peak < 0)).mean() * 100
    print(f"\n  flow POSITIVE into the peak then NEGATIVE after: {flipped:.0f}% of them")
    lead = up.flow_leads_price_min.dropna()
    print(f"  cumulative flow topped out BEFORE price on {(lead > 0).mean()*100:.0f}% "
          f"(median lead {lead[lead > 0].median():.0f} min)")

    # ---------------------------------------------------------------- Q2
    print("\n" + "=" * 74)
    print("Q2 — WINNERS WE EXITED THAT RAN FURTHER. Was flow still with us at the exit?")
    print("=" * 74)
    ran = win[(win.R_after_exit >= 1.0)].dropna(subset=["flow_at_exit"])
    print(f"n = {len(ran)} winners that ran >=1R past the exit "
          f"(of {win.R_after_exit.notna().sum()} with a locatable exit)\n")
    print(f"{'':<26}{'median':>12}{'mean':>12}{'% positive':>13}")
    print("-" * 63)
    for lbl, s in [("flow AT the exit (15m)", ran.flow_at_exit),
                   ("flow AFTER exit (15m)", ran.flow_after_exit)]:
        print(f"{lbl:<26}{s.median():>12,.0f}{s.mean():>12,.0f}{_pct_pos(s):>12.0f}%")
    both = ((ran.flow_at_exit > 0) & (ran.flow_after_exit > 0)).mean() * 100
    print(f"\n  flow positive AT the exit AND for 15m after: {both:.0f}% "
          f"<- Angus's claim, tested")

    # ------------------------------------------------- the separation test
    print("\n" + "=" * 74)
    print("DOES FLOW SEPARATE THEM? (the only question that matters for a rule)")
    print("=" * 74)
    print("Both groups are in profit at the moment of interest. If flow reads the same in")
    print("both, it cannot tell you to hold one and cut the other.\n")
    a = ran.flow_at_exit.dropna()          # winners, at exit, before running further
    b = up.flow_at_peak.dropna()           # losers, at their peak, before reversing
    print(f"{'group':<34}{'n':>5}{'median 15m flow':>18}{'% positive':>13}")
    print("-" * 70)
    print(f"{'winners at exit (went on to run)':<34}{len(a):>5}{a.median():>18,.0f}{_pct_pos(a):>12.0f}%")
    print(f"{'losers at peak (went on to lose)':<34}{len(b):>5}{b.median():>18,.0f}{_pct_pos(b):>12.0f}%")
    print(f"\n{'forward 15m flow':<34}")
    fa, fb = ran.flow_after_exit.dropna(), up.flow_after_peak.dropna()
    print(f"{'  winners, after exit':<34}{len(fa):>5}{fa.median():>18,.0f}{_pct_pos(fa):>12.0f}%")
    print(f"{'  losers, after peak':<34}{len(fb):>5}{fb.median():>18,.0f}{_pct_pos(fb):>12.0f}%")

    # -------------------------------------------- matched decision point
    print("\n" + "=" * 74)
    print("THE MATCHED TEST — every trade at the moment it first hits +1R")
    print("=" * 74)
    print("The comparison above is unfair: 'winner at exit' and 'loser at peak' are different")
    print("kinds of moment, and the peak is only knowable in hindsight. This asks the question")
    print("an agent actually faces: the trade is +1R right now, hold or cut?\n")

    at1 = T.dropna(subset=["flow_at_r1"]).copy()
    at1["outcome"] = np.where(at1.dollars > 0, "ended up a WINNER", "ended up a LOSER")
    print(f"trades that reached +1R at all: {len(at1)} of {len(T)}\n")
    print(f"{'at the +1R moment':<24}{'n':>5}{'median 15m flow':>18}{'% pos':>8}"
          f"{'median further run':>21}")
    print("-" * 76)
    for lbl in ("ended up a WINNER", "ended up a LOSER"):
        g = at1[at1.outcome == lbl]
        if not len(g):
            continue
        print(f"{lbl:<24}{len(g):>5}{g.flow_at_r1.median():>18,.0f}"
              f"{_pct_pos(g.flow_at_r1):>7.0f}%{g.R_after_r1.median():>20.2f}R")

    w1 = at1[at1.outcome == "ended up a WINNER"].flow_at_r1
    l1 = at1[at1.outcome == "ended up a LOSER"].flow_at_r1
    if len(w1) > 5 and len(l1) > 5:
        gap = w1.median() - l1.median()
        # rank-based separation: P(random winner's flow > random loser's flow)
        allv = pd.concat([w1, l1]).rank()
        auc = (allv[:len(w1)].mean() - (len(w1) + 1) / 2) / len(l1)
        print(f"\n  median flow gap: {gap:,.0f}")
        print(f"  separation (AUC): {auc:.2f}   (0.50 = no signal, 1.00 = perfect)")
        if auc < 0.60:
            print("  => WEAK. Trailing delta alone does not tell hold from cut at +1R.")
        elif auc < 0.70:
            print("  => MODEST. Real but not a rule on its own.")
        else:
            print("  => STRONG for a single feature — worth taking to the holdout.")

    print("\n" + "-" * 74)
    print("READ IT CAREFULLY. FORWARD flow separating the two is nearly tautological — it is")
    print("close to saying price went up when buyers bought. The load-bearing question is")
    print("whether the TRAILING flow, knowable at the moment of decision, separates them.")
    print("If it does not, a flow-only hold/cut rule cannot work and the agent needs more")
    print("than delta (book pull, level structure) to earn its discretion.")


if __name__ == "__main__":
    main()
