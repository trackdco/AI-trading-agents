"""Build a continuous front-month NQ 1-minute OHLCV series from the four raw
Databento exports. Data preparation only - the measurement script is untouched."""
import subprocess, io
import pandas as pd

FILES = [
 "glbx-mdp3-20230101-20250301.ohlcv-1m.csv.zst",
 "glbx-mdp3-20250101-20250501.ohlcv-1m.csv.zst",
 "glbx-mdp3-20250502-20251001.ohlcv-1m.csv.zst",
 "glbx-mdp3-20251002-20260131.ohlcv-1m.csv.zst",
]

parts = []
for f in FILES:
    raw = subprocess.run(["zstd", "-dc", f], capture_output=True).stdout
    parts.append(pd.read_csv(io.BytesIO(raw)))
df = pd.concat(parts, ignore_index=True)
print(f"raw rows concatenated      : {len(df):,}")

df["ts"] = pd.to_datetime(df["ts_event"], format="ISO8601", utc=True)

# drop calendar spreads: they are a different instrument at a different price scale
spreads = df["symbol"].str.contains("-", na=False)
print(f"calendar-spread rows dropped: {int(spreads.sum()):,}")
df = df[~spreads]

# the four exports overlap (Jan-Feb 2025 appears in both file 1 and file 2)
before = len(df)
df = df.drop_duplicates(subset=["ts", "symbol"], keep="first")
print(f"overlap duplicate rows dropped: {before - len(df):,}")

# front month = highest total volume outright contract on each calendar date
df["d"] = df["ts"].dt.date
vol = df.groupby(["d", "symbol"])["volume"].sum()
front = vol.groupby(level=0).idxmax().apply(lambda x: x[1])
df["front"] = df["d"].map(front)
fm = df[df["symbol"] == df["front"]].copy()
print(f"front-month rows           : {len(fm):,}")

fm = fm.sort_values("ts")
dups = int(fm["ts"].duplicated().sum())
print(f"duplicate timestamps       : {dups}")
assert dups == 0

# roll dates
roll = front[front != front.shift(1)].iloc[1:]
print(f"contract rolls             : {len(roll)}  -> {[f'{d}:{s}' for d, s in roll.items()]}")

out = fm[["ts", "open", "high", "low", "close", "volume"]].rename(columns={"ts": "timestamp"})
out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
out.to_csv("nq_1m_frontmonth.csv", index=False)

print()
print(f"WROTE nq_1m_frontmonth.csv : {len(out):,} rows")
print(f"  UTC coverage             : {fm['ts'].min()}  ->  {fm['ts'].max()}")
print(f"  distinct calendar dates  : {fm['d'].nunique()}")
print(f"  price range              : {fm['close'].min():.2f} - {fm['close'].max():.2f}")
print(f"  zero/na volume rows      : {int((fm['volume'].fillna(0) <= 0).sum()):,}")
