"""Data ingest: Databento OHLCV-1m .zst -> continuous NQ 1m parquet (NY tz).

First-pass (pre-parity-gate). Roll handling: per NY-session-day we keep only the
single dominant contract (highest daily volume). Because the strategy is strictly
intraday (entry+exit same session), trades never cross a roll, so no price
back-adjustment is needed for R-based accounting.
"""
import glob, io, os
import pandas as pd
import zstandard

RAW_GLOB = "glbx-mdp3-*.ohlcv-1m.csv.zst"
NY = "America/New_York"


def _read_zst(path):
    with open(path, "rb") as fh:
        r = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
        return pd.read_csv(r)


def load_continuous(raw_glob=RAW_GLOB):
    frames = [_read_zst(p) for p in sorted(glob.glob(raw_glob))]
    df = pd.concat(frames, ignore_index=True)
    # keep only NQ outrights (symbol like NQH3, NQM3...), drop spreads/others
    df = df[df["symbol"].str.match(r"^NQ[FGHJKMNQUVXZ]\d+$", na=False)].copy()
    df["ts"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(NY)
    df = df.drop_duplicates(subset=["ts", "symbol"])
    df["day"] = df["ts"].dt.tz_localize(None).dt.normalize()

    # dominant contract per calendar day by total volume
    vol = df.groupby(["day", "symbol"])["volume"].sum().reset_index()
    dom = vol.sort_values("volume").groupby("day").tail(1)[["day", "symbol"]]
    dom = dom.rename(columns={"symbol": "front"})
    df = df.merge(dom, on="day")
    df = df[df["symbol"] == df["front"]].copy()

    df = df.sort_values("ts").reset_index(drop=True)
    out = df[["ts", "open", "high", "low", "close", "volume", "symbol"]].copy()
    return out


def gap_report(df):
    """Missing-minute count per day inside the 09:30-16:00 ET cash session."""
    s = df.set_index("ts")
    rep = []
    for day, g in s.groupby(s.index.tz_localize(None).normalize()):
        cash = g.between_time("09:30", "15:59")
        expected = 390
        rep.append((day.date(), len(cash), expected - len(cash)))
    return pd.DataFrame(rep, columns=["day", "cash_bars", "missing_min"])


if __name__ == "__main__":
    df = load_continuous()
    os.makedirs("data", exist_ok=True)
    df.to_parquet("data/nq_1m.parquet")
    print(f"rows={len(df):,}  {df.ts.min()} -> {df.ts.max()}")
    print(f"contracts stitched: {df.symbol.nunique()}  ({', '.join(sorted(df.symbol.unique())[:6])}...)")
    g = gap_report(df)
    print(f"trading days: {len(g)}")
    print(f"days with >5 missing cash minutes: {(g.missing_min>5).sum()}")
    print(f"median cash bars/day: {g.cash_bars.median():.0f}")
