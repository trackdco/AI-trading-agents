#!/usr/bin/env python3
"""Step 0 — determine the bar-label convention of the Databento OHLCV-1m files.

Nothing downstream is valid until this is settled (ict-nq-backtest skill,
workflow step 0). Two candidate conventions:

    open-labeled    a bar stamped 08:30:00 covers  [08:30:00, 08:31:00)
    close-labeled   a bar stamped 08:30:00 covers  (08:29:00, 08:30:00]

Three independent probes. None of them needs indicator code.

    A  econ release   An 08:30:00 ET print dumps volume into the minute that
                      STARTS at 08:30. Open-labeled  -> spike on the 08:30 stamp.
                      Close-labeled -> spike on the 08:31 stamp.

    B  cash open      Same logic at the 09:30:00 ET NY equity open.

    C  session break  CME NQ halts 17:00 ET and reopens 18:00 ET.
                      Open-labeled  -> last bar before the halt is stamped 16:59
                                       (17:00 absent), first bar back is 18:00.
                      Close-labeled -> last bar before the halt is stamped 17:00
                                       (16:59 also present), first bar back 18:01
                                       (18:00 absent).
                      Deterministic: no spike, no threshold, no econ calendar.

Probe C is the tiebreaker; A and B corroborate it.

Release days are located EMPIRICALLY (--scan) rather than from a hardcoded BLS
calendar, so the result does not depend on anyone remembering the right dates.
Explicit dates can still be forced with --dates.

Usage:
    python3 scripts/check_bar_label.py                      # auto: scan + probe
    python3 scripts/check_bar_label.py --dates 2026-01-13 2026-01-09
    python3 scripts/check_bar_label.py --scan-only --top 15
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

import pandas as pd
import zstandard as zstd

REPO = Path(__file__).resolve().parent.parent
NY = "America/New_York"

# Raw source columns we need. The OHLCV-1m header is:
# ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol
USECOLS = ["ts_event", "open", "high", "low", "close", "volume", "symbol"]

# Outright NQ contracts look like NQZ5 / NQH6. Calendar spreads look like
# NQM5-NQU5 and MUST be dropped -- spread prices are small numbers near zero
# and manufacture impossible gaps (lookahead-taxonomy #8).
OUTRIGHT_RE = re.compile(r"^NQ[FGHJKMNQUVXZ]\d$")

FILENAME_RE = re.compile(r"glbx-mdp3-(\d{8})-(\d{8})\.ohlcv-1m\.csv\.zst$")

# ET windows we probe, expressed as the UTC hours that can contain them.
# ET 08:00-10:00 -> UTC 12,13,14 ; ET 16:55-18:05 -> UTC 20,21,22,23.
# (Every probe window sits on the same UTC calendar day as its ET date, so a
# cheap same-day string filter is safe here. This would NOT hold past ~19:00 ET.)
HOURS_MORNING = {"12", "13", "14"}
HOURS_BREAK = {"20", "21", "22", "23"}


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------

def available_files() -> list[tuple[str, str, Path]]:
    """Return (start_yyyymmdd, end_yyyymmdd, path) for each OHLCV-1m archive."""
    out = []
    for p in sorted(REPO.glob("glbx-mdp3-*.ohlcv-1m.csv.zst")):
        m = FILENAME_RE.search(p.name)
        if m:
            out.append((m.group(1), m.group(2), p))
    return out


def files_covering(dates: set[str] | None) -> list[Path]:
    """Pick the archives whose filename range covers the requested ET dates."""
    files = available_files()
    if not files:
        sys.exit("No glbx-mdp3-*.ohlcv-1m.csv.zst files found in the repo root.")
    if dates is None:
        return [p for _, _, p in files]
    keys = {d.replace("-", "") for d in dates}
    hits = [p for s, e, p in files if any(s <= k <= e for k in keys)]
    return hits or [files[-1][2]]


def read_window(
    paths: list[Path],
    hours: set[str],
    dates: set[str] | None = None,
    chunksize: int = 500_000,
) -> pd.DataFrame:
    """Stream the .zst archives, keeping only rows in the UTC hours of interest.

    Filtering happens on the raw timestamp string before parsing -- these files
    hold ~1400 bars/day/contract and we want a handful of minutes.
    """
    date_keys = {d for d in dates} if dates else None
    frames: list[pd.DataFrame] = []

    for path in paths:
        dctx = zstd.ZstdDecompressor()
        with open(path, "rb") as fh, dctx.stream_reader(fh) as reader:
            text = io.TextIOWrapper(reader, encoding="utf-8")
            for chunk in pd.read_csv(
                text,
                usecols=USECOLS,
                dtype={"ts_event": "string", "symbol": "string"},
                chunksize=chunksize,
            ):
                ts = chunk["ts_event"]
                mask = ts.str.slice(11, 13).isin(hours)
                if date_keys is not None:
                    mask &= ts.str.slice(0, 10).isin(date_keys)
                if mask.any():
                    frames.append(chunk.loc[mask])

    if not frames:
        return pd.DataFrame(columns=USECOLS)

    df = pd.concat(frames, ignore_index=True)

    # Drop calendar spreads BEFORE anything else touches price.
    df = df[df["symbol"].str.match(OUTRIGHT_RE, na=False)].copy()

    # ts_event is UTC ("...Z"). Convert once, here, and never do offset math.
    df["ts_utc"] = pd.to_datetime(df["ts_event"], format="ISO8601", utc=True)
    df["ts_ny"] = df["ts_utc"].dt.tz_convert(NY)
    df["date_ny"] = df["ts_ny"].dt.date.astype("string")
    df["hhmm"] = df["ts_ny"].dt.strftime("%H:%M")
    df["range_pts"] = df["high"] - df["low"]

    # The archives overlap (2023-2025-03 and 2025-01-2025-05 share dates).
    df = df.drop_duplicates(subset=["ts_utc", "symbol"], keep="first")

    return df.sort_values("ts_utc").reset_index(drop=True)


def front_month(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the highest-volume outright contract per ET date."""
    if df.empty:
        return df
    ranked = df.groupby(["date_ny", "symbol"], observed=True)["volume"].sum()
    winners = ranked.reset_index().sort_values("volume").groupby("date_ny").tail(1)
    keep = set(zip(winners["date_ny"], winners["symbol"]))
    return df[[(d, s) in keep for d, s in zip(df["date_ny"], df["symbol"])]].copy()


# --------------------------------------------------------------------------
# probe A/B -- locate the spike
# --------------------------------------------------------------------------

def scan_for_releases(df: pd.DataFrame, top: int) -> pd.DataFrame:
    """Rank ET dates by how violently volume spikes around 08:30.

    baseline = median 1m volume 07:00-08:20 ET (quiet pre-release drift)
    spike    = max 1m volume on the 08:29..08:32 stamps (brackets both
               conventions, so the ranking itself is convention-agnostic)
    """
    rows = []
    for date, day in df.groupby("date_ny", observed=True):
        base = day[(day["hhmm"] >= "07:00") & (day["hhmm"] <= "08:20")]["volume"]
        win = day[day["hhmm"].isin(["08:29", "08:30", "08:31", "08:32"])]
        if base.empty or win.empty:
            continue
        baseline = float(base.median())
        if baseline <= 0:
            continue
        peak = win.loc[win["volume"].idxmax()]
        rows.append(
            {
                "date": date,
                "baseline_vol": baseline,
                "peak_vol": int(peak["volume"]),
                "peak_stamp": peak["hhmm"],
                "ratio": float(peak["volume"]) / baseline,
            }
        )
    if not rows:
        return pd.DataFrame()
    return (
        pd.DataFrame(rows)
        .sort_values("ratio", ascending=False)
        .head(top)
        .reset_index(drop=True)
    )


def probe_spike(df: pd.DataFrame, date: str, anchor: str, label: str) -> str | None:
    """Print the minute bars bracketing `anchor` and return the verdict.

    anchor is the ET wall-clock instant of the event ("08:30" / "09:30").
    Spike on the anchor stamp  -> open-labeled.
    Spike on anchor+1 stamp    -> close-labeled.
    """
    day = df[df["date_ny"] == date]
    if day.empty:
        print(f"  {label}: no data for {date}")
        return None

    hh, mm = (int(x) for x in anchor.split(":"))
    anchor_min = hh * 60 + mm
    stamps = [f"{(anchor_min + d) // 60:02d}:{(anchor_min + d) % 60:02d}" for d in range(-5, 6)]
    win = day[day["hhmm"].isin(stamps)].sort_values("hhmm")
    if win.empty:
        print(f"  {label}: no bars in window on {date}")
        return None

    sym = win["symbol"].iloc[0]
    peak_stamp = win.loc[win["volume"].idxmax(), "hhmm"]
    prev_stamp = f"{(anchor_min - 1) // 60:02d}:{(anchor_min - 1) % 60:02d}"
    next_stamp = f"{(anchor_min + 1) // 60:02d}:{(anchor_min + 1) % 60:02d}"

    print(f"  {label} — {date}  ({sym})")
    print(f"    {'stamp':>7} {'volume':>9} {'range':>8}   {'high':>10} {'low':>10}")
    for _, r in win.iterrows():
        mark = "  <== PEAK" if r["hhmm"] == peak_stamp else ""
        note = ""
        if r["hhmm"] == prev_stamp:
            note = "  (quiet if open-labeled)"
        elif r["hhmm"] == anchor:
            note = "  (event minute if open-labeled)"
        elif r["hhmm"] == next_stamp:
            note = "  (event minute if close-labeled)"
        print(
            f"    {r['hhmm']:>7} {int(r['volume']):>9} {r['range_pts']:>8.2f}"
            f"   {r['high']:>10.2f} {r['low']:>10.2f}{mark}{note}"
        )

    if peak_stamp == anchor:
        verdict = "open"
    elif peak_stamp == next_stamp:
        verdict = "close"
    else:
        verdict = None
    print(f"    -> peak volume on the {peak_stamp} stamp => "
          f"{verdict + '-labeled' if verdict else 'INCONCLUSIVE (peak outside both candidate stamps)'}\n")
    return verdict


# --------------------------------------------------------------------------
# probe C -- session boundary (deterministic)
# --------------------------------------------------------------------------

def probe_session_break(df: pd.DataFrame, dates: list[str]) -> str | None:
    """CME NQ halts 17:00 ET, reopens 18:00 ET.

    Under open-labeling the halted hour means no bar can START at 17:00..17:59,
    so 16:59 is present, 17:00 is absent, and the reopen bar is stamped 18:00.
    Under close-labeling no bar can END in (17:00, 18:00], so 17:00 is present,
    18:00 is absent, and the reopen bar is stamped 18:01.
    """
    print("PROBE C — CME maintenance break (17:00-18:00 ET). Deterministic.\n")
    print(f"    {'date':>12} {'16:59':>7} {'17:00':>7} {'17:01':>7} "
          f"{'17:59':>7} {'18:00':>7} {'18:01':>7}   verdict")

    votes: list[str] = []
    for date in dates:
        day = df[df["date_ny"] == date]
        if day.empty:
            continue
        present = set(day["hhmm"])
        cells = {s: ("yes" if s in present else "-")
                 for s in ["16:59", "17:00", "17:01", "17:59", "18:00", "18:01"]}

        has_1700, has_1800, has_1801 = ("17:00" in present, "18:00" in present, "18:01" in present)
        # Friday 17:00 ET is the weekly close -- the market does not reopen until
        # Sunday 18:00, so neither 18:00 nor 18:01 exists and the probe cannot
        # discriminate. Skip rather than counting it as evidence.
        if pd.Timestamp(date).dayofweek == 4 and not (has_1800 or has_1801):
            v = "n/a (Friday weekly close)"
        elif not has_1700 and has_1800:
            v = "open-labeled"
        elif has_1700 and not has_1800 and has_1801:
            v = "close-labeled"
        else:
            v = "inconclusive"
        if not v.startswith("n/a"):
            votes.append(v)
        print(f"    {date:>12} " + " ".join(f"{cells[s]:>7}" for s in
              ["16:59", "17:00", "17:01", "17:59", "18:00", "18:01"]) + f"   {v}")

    if not votes:
        print("\n    no evening data loaded")
        return None
    tally = pd.Series(votes).value_counts()
    print(f"\n    tally: {tally.to_dict()}")
    top = tally.index[0]
    if top == "inconclusive" or tally.iloc[0] < len(votes):
        print("    -> mixed or inconclusive; do not rely on probe C alone\n")
    return {"open-labeled": "open", "close-labeled": "close"}.get(top)


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dates", nargs="*", default=None,
                    help="explicit ET dates (YYYY-MM-DD) to probe")
    ap.add_argument("--top", type=int, default=8,
                    help="how many scanned release-day candidates to list")
    ap.add_argument("--probe", type=int, default=3,
                    help="how many top candidates to probe in detail")
    ap.add_argument("--scan-only", action="store_true")
    args = ap.parse_args()

    print("=" * 78)
    print("STEP 0 — Databento OHLCV-1m bar-label convention")
    print("=" * 78)
    for s, e, p in available_files():
        print(f"  {p.name}   [{s} .. {e}]")
    print()

    # ---- locate candidate release days -----------------------------------
    if args.dates:
        target_dates = list(args.dates)
        paths = files_covering(set(target_dates))
        print(f"Using caller-supplied dates: {', '.join(target_dates)}\n")
        morning = front_month(read_window(paths, HOURS_MORNING, set(target_dates)))
    else:
        paths = [available_files()[-1][2]]  # most recent archive
        print(f"PROBE A0 — scanning {paths[0].name} for 08:30 ET release signatures")
        print("(empirical, so the result does not depend on recalling the BLS calendar)\n")
        morning = front_month(read_window(paths, HOURS_MORNING))
        cand = scan_for_releases(morning, args.top)
        if cand.empty:
            print("No candidate release days found.")
            return 1
        print(f"    {'date':>12} {'baseline':>9} {'peak vol':>9} {'stamp':>7} {'ratio':>7}")
        for _, r in cand.iterrows():
            print(f"    {r['date']:>12} {r['baseline_vol']:>9.0f} {r['peak_vol']:>9} "
                  f"{r['peak_stamp']:>7} {r['ratio']:>7.1f}x")
        print()
        target_dates = list(cand["date"].head(args.probe))

    if args.scan_only:
        return 0

    # ---- probe A: econ release -------------------------------------------
    print("=" * 78)
    print("PROBE A — 08:30 ET release: which minute stamp carries the spike?\n")
    votes_a = [v for d in target_dates
               if (v := probe_spike(morning, d, "08:30", "release")) is not None]

    # ---- probe B: cash open ----------------------------------------------
    print("=" * 78)
    print("PROBE B — 09:30 ET NY cash open: same question, independent event.\n")
    votes_b = [v for d in target_dates
               if (v := probe_spike(morning, d, "09:30", "cash open")) is not None]

    # ---- probe C: session break ------------------------------------------
    print("=" * 78)
    evening = front_month(read_window(paths, HOURS_BREAK, set(target_dates)))
    vote_c = probe_session_break(evening, target_dates)

    # ---- verdict ----------------------------------------------------------
    print("=" * 78)
    print("VERDICT\n")
    a = pd.Series(votes_a).mode()
    b = pd.Series(votes_b).mode()
    def fmt(s: pd.Series) -> str:
        return (s.iloc[0] + "-labeled") if len(s) else "inconclusive"

    print(f"  Probe A (08:30 release)   : {fmt(a)}   {votes_a}")
    print(f"  Probe B (09:30 cash open) : {fmt(b)}   {votes_b}")
    print(f"  Probe C (session break)   : "
          f"{vote_c + '-labeled' if vote_c else 'inconclusive'}")

    final = {v for v in [a.iloc[0] if len(a) else None,
                         b.iloc[0] if len(b) else None, vote_c] if v}
    print()
    if len(final) == 1:
        conv = final.pop()
        print(f"  ==> All probes agree: ts_event is {conv.upper()}-LABELED.")
        if conv == "open":
            print("      A bar stamped 09:31:00 covers [09:31:00, 09:32:00) and is")
            print("      NOT fully known until 09:32:00.")
            print("      => ingestion must shift +1 minute to reach the repo-wide")
            print("         invariant 'at timestamp T, bar T is fully known'.")
        else:
            print("      A bar stamped 09:31:00 covers (09:30:00, 09:31:00] and is")
            print("      fully known at 09:31:00 -- already the target invariant.")
    else:
        print(f"  ==> PROBES DISAGREE: {sorted(final)}. Do not proceed.")
        print("      Resolve against Databento documentation before writing any")
        print("      indicator or detector code.")
    print()
    print("  Confirm against Databento's published schema before locking this in;")
    print("  these probes are empirical evidence, not the vendor's own statement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
