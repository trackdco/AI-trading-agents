#!/usr/bin/env python3
"""Does the L0 census contain ANGUS'S OWN TRADES? The detector-vs-trader check.

Parity proved the regenerated stream matches the detector's own history. This checks the
detector against the SPEC — the trades Angus actually took by hand. ANGUS 30-Jul, asked
whether the census would contain them: *"the L0 probably wont"*. This measures that,
trade by trade, so any detector gap is a named finding BEFORE L3 fits checks to the
census and L4 builds a book on it.

Two logs, two matching regimes:

  feb2026_hand_log.csv   exact times. TV labels candles by OPEN; engine bars are
                         CLOSE-labeled, so hand time t on TF maps to the engine bar at the
                         bin close (run_triggers_feb convention). Match window +/-6 min
                         around the mapped bar, direction must agree. TF is NOT required to
                         match: MTF arbitration keeps only the highest TF on a shared close.
  mar2026_hand_log.csv   chart-read times, +/-15-25 min by its own header. Window +/-30 min,
                         direction must agree. A MISS here is weak evidence; a HIT is real.

Only NY-morning trades are checkable (the census band is 07:45-11:00 ET).

    python -m scripts.l0_handlog_check          # uses output/l0_triggers_fit.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"


def load_census() -> pd.DataFrame:
    T = pd.read_parquet(ROOT / "output/l0_triggers_fit.parquet")
    # trigger ts are ET ISO strings whose UTC offset changes across DST — parse via UTC
    ts = pd.to_datetime(T.ts, format="mixed", utc=True).dt.tz_convert(NY)
    return T.assign(ts_et=ts, day=ts.dt.strftime("%Y-%m-%d"))


def _norm(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "")
                  for c in df.columns]
    return df


def feb_trades() -> pd.DataFrame:
    f = _norm(pd.read_csv(ROOT / "data/reference/feb2026_hand_log.csv",
                          encoding="utf-8-sig"))
    return pd.DataFrame([{"day": pd.Timestamp(r.date).strftime("%Y-%m-%d"),
                          "time": str(r.entry_time).strip(),
                          "tf_min": int(str(r.entry_tf).upper().replace("M", "")),
                          "direction": str(r.direction).strip().lower(),
                          "result": str(r.result).strip()}
                         for r in f.itertuples()])


def mar_trades() -> pd.DataFrame:
    f = _norm(pd.read_csv(ROOT / "data/reference/mar2026_hand_log.csv", comment="#"))
    return pd.DataFrame([{"day": str(r.date).strip(), "time": str(r.entry_time).strip(),
                          "tf_min": int(str(r.entry_tf).upper().replace("M", "")),
                          "direction": str(r.direction).strip().lower(),
                          "result": str(r.result).strip()}
                         for r in f.itertuples()])


def check(census: pd.DataFrame, trades: pd.DataFrame, label: str,
          window_min: int, mapped: bool) -> tuple[int, int]:
    hits = 0
    checkable = 0
    print(f"\n{label} — match window +/-{window_min} min"
          f"{', hand time mapped to bin close' if mapped else ''}:")
    for t in trades.itertuples():
        try:
            hand = pd.Timestamp(f"{t.day} {t.time}", tz=NY)
        except Exception:
            print(f"  [SKIP] {t.day} {t.time}: unparseable time")
            continue
        hm = hand.hour * 60 + hand.minute
        if not (7 * 60 + 45 <= hm <= 11 * 60):
            print(f"  [OUT-OF-BAND] {t.day} {t.time} {t.direction} — outside 07:45-11:00")
            continue
        checkable += 1
        ref = hand
        if mapped:                       # TV open-label -> engine bin close
            ref = hand - pd.Timedelta(minutes=hm % t.tf_min) + pd.Timedelta(minutes=t.tf_min)
        d = census[(census.day == t.day) & (census.direction == t.direction)]
        near = d[(d.ts_et - ref).abs() <= pd.Timedelta(minutes=window_min)]
        if len(near):
            hits += 1
            det = ", ".join(f"{r.ts_et:%H:%M} {r.tf} {r.pattern}/{r.kind}"
                            for r in near.itertuples())
            print(f"  [HIT ] {t.day} {t.time} {t.direction:<5} ({t.result:<4}) -> {det}")
        else:
            same_day = census[census.day == t.day]
            alt = ", ".join(f"{r.ts_et:%H:%M}{'L' if r.direction == 'long' else 'S'}"
                            for r in same_day[(same_day.ts_et - ref).abs()
                                              <= pd.Timedelta(minutes=window_min)].itertuples())
            print(f"  [MISS] {t.day} {t.time} {t.direction:<5} ({t.result:<4})"
                  f"{'  nearby opposite/other: ' + alt if alt else '  nothing within window'}")
    print(f"{label}: {hits}/{checkable} checkable trades found in the census")
    return hits, checkable


def main() -> None:
    census = load_census()
    h1, c1 = check(census, feb_trades(), "FEB 2026 (exact hand log)", 6, mapped=True)
    h2, c2 = check(census, mar_trades(), "MAR 2026 (chart-read, approximate)", 30,
                   mapped=False)
    print(f"\nTOTAL: {h1 + h2}/{c1 + c2} of Angus's checkable NY-morning trades appear in L0")
    print("A widespread miss = detector-spec gap -> finding BEFORE L3/L4, which is the point.")


if __name__ == "__main__":
    main()
