#!/usr/bin/env python3
"""LDN-DRIVE-01 — GATED feasibility count for euro-open-drive. NOT A TEST.

WHAT THIS IS. `london_feasibility_scan.py` counted the candidate's FIRST gate only
(the open printing outside the Asia range) and got 67/36 — comfortably over the n>=30
floor. That file warns in its own footer that its numbers are UPPER BOUNDS, because
every candidate layers further gates that only reduce the count. This script applies
euro-open-drive's remaining declared gates and re-counts.

No outcome, no return, no direction, no P&L is computed anywhere in this file. Nothing
is selected on, so no statistical power is spent and this is not a trial. It answers
one question:

    after its OWN gates, can euro-open-drive reach n >= 30 events per era?

THE CANDIDATE'S GATES (research/candidates/london-euro-open-drive.md, "Mechanical
skeleton"), verbatim: "Gates: open prints outside Asia range/value; one-time-framing on
5-min bars; skip if opening range already > threshold (news spent)."

  1. open outside the Asia range
  2. one-time-framing across the London IB on 5-min bars
  3. IB range <= 1.5x the Asia range (the "news not spent" gate)

London IB = the first hour of the session, 08:00-09:00 Europe/London, derived per day
via london_window_et(). ET hours are never hardcoded.

Neither gate 2 nor gate 3 has a single canonical form — the thesis says
"one-time-framing on 5-min bars" and "> threshold" without pinning either. Both are
therefore reported as SENSITIVITY LADDERS, not as point definitions, so that no
definitional choice can be blamed for the answer. Gate 2 is laddered from Dalton's
strict form (zero violations across the IB) out to a form so permissive it is barely a
gate; gate 3 across three thresholds.

SEALED-SPAN GUARD: 2023/24 dropped and asserted gone. No holdout look.

    python -m scripts.ldn_drive01_feasibility
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_inv01_power import fit_only
from scripts.ldn_swp01_london_only import london_window_et

NY = "America/New_York"
FLOOR = 30
IB_MINUTES = 60                      # 08:00-09:00 London = the candidate's IB
IB_RATIOS = (1.5, 2.0, 3.0)          # gate-3 sensitivity ladder
OTF_SLACK = (0, 1, 2, 3)             # gate-2 sensitivity ladder: violations allowed


def otf_violations(ib: pd.DataFrame, side: int) -> int:
    """Count 5-min bars that break one-time-framing in the drive direction.

    Up (side>0): a bar violates by taking out the prior bar's low.  Down: by taking
    out the prior bar's high.  Zero violations is Dalton's strict form; the caller
    ladders the tolerance rather than committing to one reading of the thesis.
    """
    b = ib.set_index("ts").resample("5min").agg(
        {"high": "max", "low": "min"}).dropna()
    if len(b) < 4:                   # need a real IB to frame at all
        return 10**6
    if side > 0:
        return int((b.low.to_numpy()[1:] < b.low.to_numpy()[:-1]).sum())
    return int((b.high.to_numpy()[1:] > b.high.to_numpy()[:-1]).sum())


def holds_the_open(ib: pd.DataFrame, side: int, open_px: float) -> bool:
    """The thesis's other phrasing of the same idea: the drive "never trad[es] back
    through the open". Reported alongside the OTF ladder as an independent reading."""
    return bool(ib.low.min() >= open_px if side > 0 else ib.high.max() <= open_px)


def scan() -> pd.DataFrame:
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY))
    bars["day"] = bars.ts.dt.strftime("%Y-%m-%d")
    by_day = {d: g for d, g in bars.groupby("day", sort=False)}

    rows = []
    for r in sub.itertuples():
        g = by_day.get(r.day)
        if g is None:
            continue
        start, end = london_window_et(r.day)
        w = g[(g.ts >= start) & (g.ts <= end)]
        if len(w) < 30:
            continue
        ib = w[w.ts < start + pd.Timedelta(minutes=IB_MINUTES)]
        if len(ib) < 30:
            continue

        o = float(w.close.iloc[0])
        side = +1 if o > r.asia_hi else -1 if o < r.asia_lo else 0
        if side == 0:
            rows.append({"day": r.day, "era": r.day[:4], "g1": False,
                         "viol": 10**6, "held_open": False,
                         "ib_ratio": float("nan")})
            continue

        ib_rng = float(ib.high.max() - ib.low.min())
        asia_rng = float(r.asia_rng)
        rows.append({
            "day": r.day, "era": r.day[:4], "g1": True,
            "viol": otf_violations(ib, side),
            "held_open": holds_the_open(ib, side, o),
            "ib_ratio": ib_rng / asia_rng if asia_rng > 0 else float("nan"),
        })
    return pd.DataFrame(rows)


def counts(d: pd.DataFrame, mask: pd.Series) -> tuple[int, int]:
    return (int(mask[d.era == "2025"].sum()), int(mask[d.era == "2026"].sum()))


def main() -> None:
    d = scan()
    print("LDN-DRIVE-01 GATED FEASIBILITY — euro-open-drive, counts only, no outcomes")
    print(f"window: 08:00-10:00 Europe/London per day, IB = first {IB_MINUTES} min")
    print(f"days: {len(d)} "
          f"({', '.join(f'{e}: {(d.era == e).sum()}' for e in ('2025', '2026'))})\n")

    g1 = d.g1
    b25, b26 = counts(d, g1)
    print(f"{'gate stack':<52} {'2025':>6} {'2026':>6}  floor n>={FLOOR}")
    print("-" * 82)
    print(f"{'1. open outside Asia range (drive open)':<52} "
          f"{b25:>6} {b26:>6}  OK")

    print("\ngate 2 — one-time-framing across the IB, tolerance laddered:")
    for k in OTF_SLACK:
        m = g1 & (d.viol <= k)
        n25, n26 = counts(d, m)
        lab = ("strict (Dalton: no 5-min bar takes out the prior)" if k == 0
               else f"<= {k} violating 5-min bar{'s' if k > 1 else ''}")
        print(f"  1+2 {lab:<48} {n25:>6} {n26:>6}  "
              f"{'OK' if min(n25, n26) >= FLOOR else 'UNTESTABLE'}")
    m_open = g1 & d.held_open
    n25, n26 = counts(d, m_open)
    print(f"  1+2 {'alt reading: IB never trades back through open':<48} "
          f"{n25:>6} {n26:>6}  "
          f"{'OK' if min(n25, n26) >= FLOOR else 'UNTESTABLE'}")

    # the most permissive gate-2 reading that is still a gate, carried into gate 3
    g2 = g1 & (d.viol <= max(OTF_SLACK))
    print(f"\ngate 3 — on the MOST PERMISSIVE gate 2 above "
          f"(<= {max(OTF_SLACK)} violations):")
    for thr in IB_RATIOS:
        n25, n26 = counts(d, g2 & (d.ib_ratio <= thr))
        print(f"  1+2+3 {f'+ IB range <= {thr}x Asia (news not spent)':<46} "
              f"{n25:>6} {n26:>6}  "
              f"{'OK' if min(n25, n26) >= FLOOR else 'UNTESTABLE'}")

    s25, s26 = counts(d, g1 & (d.viol <= 0))
    print(f"\nsurvival through STRICT gate 2: "
          f"2025 {s25}/{b25} ({100 * s25 / max(1, b25):.0f}%), "
          f"2026 {s26}/{b26} ({100 * s26 / max(1, b26):.0f}%)")

    # How permissive would gate 2 have to be to clear the floor in BOTH eras?
    nbars = 11                       # ~12 five-min bars in a 60-min IB -> 11 transitions
    need = next((k for k in range(nbars + 1)
                 if min(counts(d, g1 & (d.viol <= k))) >= FLOOR), None)
    if need is None:
        print(f"\nNo tolerance reaches n>={FLOOR} in both eras, up to and including a gate")
        print("that admits every drive open.")
    else:
        k25, k26 = counts(d, g1 & (d.viol <= need))
        print(f"\nTolerance required to clear n>={FLOOR} in both eras: <= {need} violating")
        print(f"bars out of ~{nbars} transitions -> {k25}/{b25} and {k26}/{b26} days "
              f"({100 * k26 / max(1, b26):.0f}% of drive opens retained).")
        print("A gate that permits price to take out the prior 5-min bar's extreme on")
        print(f"{need} of {nbars} bars is not one-time-framing. At the point the count "
              "becomes")
        print("testable, the gate is no longer the candidate's gate.")

    print("\nGate 2, not the gate-3 threshold, is what destroys the count: the candidate")
    print("needs a cleanly framing directional IB and London does not supply one often")
    print("enough to test.")

    print("\nTHIS IS NOT A VERDICT. No outcome was measured, so euro-open-drive has not")
    print("been tested and does not enter the DSR trial ledger. It is a determination")
    print("that the candidate as specified cannot be tested on this sample.")


if __name__ == "__main__":
    main()
