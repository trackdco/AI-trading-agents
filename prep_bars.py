"""Build a continuous front-month NQ 1-minute OHLCV series from the four raw
Databento exports. Data preparation only - the measurement script is untouched.

ROLL ALIGNMENT
--------------
The contract roll is aligned to the SESSION BOUNDARY (18:00 ET), not to a
calendar-date boundary in any timezone.

The first version of this script picked the front month per UTC calendar date.
Because 00:00 UTC is 19:00 ET (EST) or 20:00 ET (EDT), that placed every roll
one to two hours INSIDE the 18:00 -> 16:30 ET profile session. The result was a
121 to 297 point discontinuity in the middle of twelve sessions, which silently
corrupted the volume profile, POC, VAH and VAL for each of them - and, because
each session's levels are read as the next session's "previous day", corrupted
roughly twice that many downstream.

Rolling on ET calendar dates would not fix it either: 00:00 ET is still the
middle of a session that opened at 18:00 the previous evening. The only cut that
leaves every session single-contract is the session open itself, so the front
month is chosen per SESSION and applied to every bar in that session. The roll
step then lands between sessions, where a volume profile never spans it.

Verify with: python prep_bars.py --verify
"""
import argparse
import io
import subprocess
from datetime import time, timedelta

import pandas as pd

ET = "America/New_York"
SESSION_OPEN = time(18, 0)
SESSION_CLOSE = time(16, 30)

FILES = [
    "glbx-mdp3-20230101-20250301.ohlcv-1m.csv.zst",
    "glbx-mdp3-20250101-20250501.ohlcv-1m.csv.zst",
    "glbx-mdp3-20250502-20251001.ohlcv-1m.csv.zst",
    "glbx-mdp3-20251002-20260131.ohlcv-1m.csv.zst",
]

OUT = "nq_1m_frontmonth.csv"


def session_label(ts_et: pd.Series) -> pd.Series:
    """Label every bar with the date its session CLOSES on.

    A session runs 18:00 ET on day X through 16:30 ET on day X+1. Bars in the
    16:30-18:00 maintenance gap are labelled with the upcoming session so that
    every bar in the file carries a label and the contract selection covers the
    full 24 hours - the measurement script excludes the gap itself later.
    """
    d = ts_et.dt.date
    nxt = ts_et.dt.time >= SESSION_CLOSE
    return pd.Series(
        [dd + timedelta(days=1) if n else dd for dd, n in zip(d, nxt)],
        index=ts_et.index,
    )


def load_outrights() -> pd.DataFrame:
    parts = []
    for f in FILES:
        raw = subprocess.run(["zstd", "-dc", f], capture_output=True).stdout
        parts.append(pd.read_csv(io.BytesIO(raw)))
    df = pd.concat(parts, ignore_index=True)
    print(f"raw rows concatenated         : {len(df):,}")

    df["ts"] = pd.to_datetime(df["ts_event"], format="ISO8601", utc=True)

    # calendar spreads are a different instrument at a different price scale
    spreads = df["symbol"].str.contains("-", na=False)
    print(f"calendar-spread rows dropped  : {int(spreads.sum()):,}")
    df = df[~spreads]

    # the four exports overlap (Jan-Feb 2025 is in both file 1 and file 2)
    before = len(df)
    df = df.drop_duplicates(subset=["ts", "symbol"], keep="first")
    print(f"overlap duplicate rows dropped: {before - len(df):,}")

    df["ts_et"] = df["ts"].dt.tz_convert(ET)
    df["session"] = session_label(df["ts_et"])
    return df


def build() -> pd.DataFrame:
    df = load_outrights()

    # front month = highest total volume outright contract in each SESSION
    vol = df.groupby(["session", "symbol"])["volume"].sum()
    front = vol.groupby(level=0).idxmax().apply(lambda x: x[1])
    df["front"] = df["session"].map(front)
    fm = df[df["symbol"] == df["front"]].copy().sort_values("ts")
    print(f"front-month rows              : {len(fm):,}")

    dups = int(fm["ts"].duplicated().sum())
    print(f"duplicate timestamps          : {dups}")
    assert dups == 0, "duplicate timestamps after front-month selection"

    roll = front[front != front.shift(1)].iloc[1:]
    print(f"contract rolls                : {len(roll)}")
    for s, sym in roll.items():
        print(f"    roll into {sym} at session {s}")

    out = fm[["ts", "open", "high", "low", "close", "volume"]].rename(
        columns={"ts": "timestamp"}
    )
    out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out.to_csv(OUT, index=False)

    print()
    print(f"WROTE {OUT}      : {len(out):,} rows")
    print(f"  UTC coverage                : {fm['ts'].min()}  ->  {fm['ts'].max()}")
    print(f"  sessions                    : {fm['session'].nunique()}")
    print(f"  price range                 : {fm['close'].min():.2f} - {fm['close'].max():.2f}")
    print(f"  zero/na volume rows         : {int((fm['volume'].fillna(0) <= 0).sum()):,}")
    return fm


def verify(path: str = OUT) -> None:
    """Confirm the roll step lands BETWEEN sessions, not inside one."""
    df = pd.read_csv(path)
    ts = pd.to_datetime(df["timestamp"], format="ISO8601", utc=True)
    df["ts_et"] = ts.dt.tz_convert(ET)
    df = df.sort_values("ts_et")
    df["session"] = session_label(df["ts_et"])

    # bar-to-bar close jump, and whether each jump straddles a session boundary
    step = df["close"].diff().abs()
    crosses = df["session"] != df["session"].shift(1)

    intra = step[~crosses & step.notna()]
    boundary = step[crosses & step.notna()]

    print(f"VERIFY {path}")
    print(f"  bars                              : {len(df):,}")
    print(f"  sessions                          : {df['session'].nunique():,}")
    print()
    print("  INTRA-session bar-to-bar close jumps (must contain no roll step)")
    print(f"    max                             : {intra.max():.2f} pts")
    print(f"    count >= 100 pts                : {int((intra >= 100).sum())}")
    print()
    print("  SESSION-BOUNDARY jumps (the roll step belongs here)")
    print(f"    max                             : {boundary.max():.2f} pts")
    print(f"    count >= 100 pts                : {int((boundary >= 100).sum())}")
    big = df.loc[boundary[boundary >= 100].index]
    for (_, r), v in zip(big.iterrows(), boundary[boundary >= 100]):
        print(f"      session {r['session']}  step {v:7.2f} pts")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="check an existing file instead of rebuilding")
    ap.add_argument("--path", default=OUT)
    a = ap.parse_args()
    if a.verify:
        verify(a.path)
    else:
        build()
        print()
        verify()
