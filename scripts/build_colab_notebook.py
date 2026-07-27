#!/usr/bin/env python3
"""Generate notebooks/colab_holdout_pull.ipynb with the sealed holdout day list baked in.

The notebook is the artifact Angus opens in Colab. It carries the pre-registered day list
inline so there is no upload step and no chance of pulling a different set of days than the
one committed in docs/HOLDOUT-2023-24-PREREGISTRATION.md.

Re-run this after any (justified) redraw of the sample:

    python -m scripts.sample_holdout_days --mode days --n 100 --seed ... --force
    python -m scripts.build_colab_notebook
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DAYS_CSV = ROOT / "data/reference/holdout_2023_24_days.csv"
OUT = ROOT / "notebooks/colab_holdout_pull.ipynb"
OUT_SINGLE = ROOT / "notebooks/colab_holdout_pull_single.ipynb"


def md(*lines: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}


def code(*lines: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": list(lines)}


def _src(text: str) -> list[str]:
    """Split a block into notebook `source` form (each line keeps its newline)."""
    lines = text.strip("\n").split("\n")
    return [ln + "\n" for ln in lines[:-1]] + [lines[-1]]


def build() -> dict:
    d = pd.read_csv(DAYS_CSV, dtype=str)
    days = d["day"].tolist()
    digest = hashlib.sha256("\n".join(days).encode()).hexdigest()
    blocks = sorted(d["block"].unique())
    n23 = int((d["year"] == "2023").sum())
    n24 = int((d["year"] == "2024").sum())

    day_lit = "\n".join(
        "    " + " ".join(f'"{x}",' for x in days[i:i + 6]) for i in range(0, len(days), 6))

    cells = [
        md(*_src(f"""
# NQ holdout pull — 2023/2024 out-of-regime canon validation

Pulls MBP-10 depth + trades for the **pre-registered** holdout days and **condenses each day
in the same loop**, so only the small committable artifacts ever touch disk. The raw frames are
freed immediately and never written — that is the fix versus saving raw parquet and condensing
in a second pass.

Output per day is roughly **150 KB** instead of ~1 GB, so the final zip is small enough to hand
straight back to Claude.

| | |
|---|---|
| sealed days | **{len(days)}** ({n23} in 2023, {n24} in 2024) |
| blocks | {', '.join(blocks)} |
| SHA-256 of day list | `{digest[:32]}…` |

Fitted span of the canon is 2025-06-02 → 2026-07-15. Nothing below overlaps it.

**Three artifacts, three different consumers — the formats are not interchangeable:**

| output | window (native tz) | format | read by |
|---|---|---|---|
| `nq_depth_<day>_ny.csv` | 08:00–11:00 **America/New_York** | long `ts,side,price,size` | `scripts/trade_matrix.py`, `depth_features.py` |
| `glbx-mdp3-<yyyymmdd>.mbp-10_condensed.csv` | 08:00–10:00 **Europe/London** | wide, raw Databento columns | `scripts/london_depth.py` |
| `footprint_holdout_<yyyy-mm>.parquet` | 18:00 (D−1) → 11:00 (D) **ET** | `ts_minute,price,side,volume,trades` | `scripts/champion_journal_cvd.py` |

Windows are defined in their **native timezone** and localized per-day, so US and UK DST
transitions land correctly — including the March/November weeks where the two calendars disagree.
""")),

        md(*_src("""
## 1 — Install and authenticate

Your key is entered at runtime and never stored in the notebook.
""")),

        code(*_src("""
!pip install -q databento pandas pyarrow

import os, time, zipfile, getpass, gc
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import databento as db
import pandas as pd
import numpy as np

API_KEY = getpass.getpass("Databento API key: ").strip()
client = db.Historical(API_KEY)
print("authenticated")
""")),

        md(*_src("""
## 2 — Configuration

Three toggles for which artifacts to build, and `LIMIT_DAYS` for a smoke test. Edit anything
here and **re-run this cell** before continuing — editing alone changes nothing.
""")),

        code(*_src(f"""
DATASET = "GLBX.MDP3"
SYMBOL  = "NQ.v.0"          # front month, rolled by volume
STYPE   = "continuous"

# Which artifacts to build. Depth is the expensive one; trades is roughly 5-10% the size.
PULL_NY_DEPTH     = True    # canon pre + golden books
PULL_LONDON_DEPTH = True    # london canon book
PULL_TRADES       = True    # CVD / footprint - feeds checks F, C, Tc, BIGFD, LONSLOPE

# Smoke-test knob: set to 3 to pull only the first 3 days and check the plumbing,
# then set back to 0 and re-run - already-downloaded days are skipped, not re-fetched.
LIMIT_DAYS = 0              # 0 = all {len(days)} sealed days

OUTDIR = "/content/holdout_out"
ZIPOUT = "/content/nq_holdout_2023_24_condensed.zip"

# Optional: survive a Colab disconnect by writing to Drive instead.
USE_DRIVE = False
if USE_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
    OUTDIR = "/content/drive/MyDrive/holdout_out"
    ZIPOUT = "/content/drive/MyDrive/nq_holdout_2023_24_condensed.zip"

NY  = ZoneInfo("America/New_York")
LON = ZoneInfo("Europe/London")
UTC = ZoneInfo("UTC")

# (name, tz, start, end) - localized per day, so DST is handled by the calendar not by hand.
# NY ends 10:30, not 11:00 (ANGUS 2026-07-27): golden window is 09:40-10:15 and depth is only
# ever read AT the fill minute. Verified against output/canon_book.parquet - pre fills run
# 08:01-09:23, gold 09:41-10:12, and ZERO fills land at or after 10:15 anywhere in the
# universe including rejected candidates. 10:30 leaves 18 min of headroom and cuts ~17% off
# the MBP-10 bill. Trades below still run to 11:00 - the in-trade layer reads forward flow
# (fw_3) up to 10 minutes AFTER the fill, so the tape must outlast the book.
DEPTH_WINDOWS = {{
    "ny":     (NY,  (8, 0), (10, 30)),   # pre-market + golden (09:40-10:15) + headroom
    "london": (LON, (8, 0), (10, 0)),    # first 2h London
}}

for sub in ("depth_ny", "depth_london", "cvd"):
    os.makedirs(f"{{OUTDIR}}/{{sub}}", exist_ok=True)

# ---- the sealed, pre-registered day list -------------------------------------
# Generated by scripts/sample_holdout_days.py. Do not edit by hand: the SHA-256 in
# docs/HOLDOUT-2023-24-PREREGISTRATION.md is the commitment that these are the days.
DAYS = [
{day_lit}
]
SEALED_SHA256 = "{digest}"

import hashlib
_check = hashlib.sha256("\\n".join(DAYS).encode()).hexdigest()
assert _check == SEALED_SHA256, f"day list altered! {{_check}} != {{SEALED_SHA256}}"
print(f"{{len(DAYS)}} sealed days verified against pre-registration")
print(f"  {{DAYS[0]}} .. {{DAYS[-1]}}")
""")),

        md(*_src("""
## 3 — Window helpers

Every request is built by localizing the wall-clock window into its own timezone and then
converting to UTC. `fold=0` pins the ambiguous hour on autumn fall-back days.
""")),

        code(*_src('''
def utc_window(day: str, tz, start_hm, end_hm):
    """Localize a wall-clock window in `tz` for `day` and return UTC ISO strings."""
    y, m, dd = (int(x) for x in day.split("-"))
    s = datetime(y, m, dd, *start_hm, tzinfo=tz)
    e = datetime(y, m, dd, *end_hm, tzinfo=tz)
    return (s.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S"),
            e.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S"))


def trades_window(day: str):
    """18:00 ET the PREVIOUS calendar day -> 11:00 ET on `day`.

    CVD features reach back through the overnight: cvd_ON, cvd_ASIA (18:00-03:00 ET),
    cvd_LON (03:00-09:30) and cvd_PM all sit inside this span. Consecutive sampled days
    never overlap (each window ends 11:00 and the next starts 18:00), so concatenating
    the per-day frames cannot double-count a minute.
    """
    y, m, dd = (int(x) for x in day.split("-"))
    end = datetime(y, m, dd, 11, 0, tzinfo=NY)
    start = datetime(y, m, dd, 18, 0, tzinfo=NY) - timedelta(days=1)
    return (start.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S"),
            end.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S"))


def _decode_px(s):
    """Databento prices are 1e-9 fixed-point ints; to_df() usually decodes them already."""
    s = pd.to_numeric(s, errors="coerce")
    return np.where(s.abs() > 1e7, s / 1e9, s)


def _front_only(df):
    """Keep the modal instrument_id - a continuous pull can straddle a roll."""
    if "instrument_id" in df.columns and df["instrument_id"].nunique() > 1:
        return df[df["instrument_id"] == df["instrument_id"].value_counts().idxmax()]
    return df


for _d in ("2023-01-11", "2023-03-15", "2023-07-12"):
    _ny = utc_window(_d, *DEPTH_WINDOWS["ny"])
    _lo = utc_window(_d, *DEPTH_WINDOWS["london"])
    print(f"{_d}  ny {_ny[0][11:16]}-{_ny[1][11:16]}Z   london {_lo[0][11:16]}-{_lo[1][11:16]}Z   "
          f"trades {trades_window(_d)[0][5:16]} -> {trades_window(_d)[1][5:16]}Z")
print("\\n2023-03-15 is the DST gap week: US already on EDT, UK still on GMT, so the two")
print("windows sit 4h apart instead of 5h. Declaring them in native tz handles that.")
''')),

        md(*_src("""
## 4 — The three condensers

Definitions only, nothing runs. Each turns one raw Databento frame into the exact shape its
consumer in the repo expects — the formats are pinned by `tests/test_colab_holdout_notebook.py`.
""")),

        code(*_src('''
def fetch(schema, start, end, tries=4):
    """get_range with backoff. Streaming API - no batch job, nothing in the download centre."""
    for i in range(tries):
        try:
            return client.timeseries.get_range(dataset=DATASET, symbols=[SYMBOL],
                                               stype_in=STYPE, schema=schema,
                                               start=start, end=end)
        except Exception as ex:
            if i == tries - 1:
                raise
            wait = 2 ** i
            print(f"    retry in {wait}s ({type(ex).__name__}: {ex})")
            time.sleep(wait)


def condense_ny(df, day):
    """Long format: ts (ET, minute), side, price, size - one row per level per minute."""
    df = _front_only(df.reset_index())
    tcol = "ts_event" if "ts_event" in df.columns else "ts_recv"
    ts = pd.to_datetime(df[tcol], utc=True, format="mixed")
    df = df.assign(_m=ts.dt.floor("1min"), _t=ts).sort_values("_t")
    last = df.groupby("_m", as_index=False).tail(1)

    frames = []
    for i in range(10):
        for side in ("bid", "ask"):
            pxc, szc = f"{side}_px_{i:02d}", f"{side}_sz_{i:02d}"
            if pxc in last.columns and szc in last.columns:
                sub = last[["_m", pxc, szc]].rename(columns={pxc: "price", szc: "size"})
                sub["side"] = side
                frames.append(sub)
    if not frames:
        return None
    out = pd.concat(frames, ignore_index=True).dropna(subset=["price", "size"])
    out["price"] = np.round(_decode_px(out["price"]), 2)
    out = out[(out["size"] > 0) & (out["price"] > 0)]
    if out.empty:
        return None
    out["size"] = out["size"].astype("int64")
    out = out.rename(columns={"_m": "ts"})
    # ET, matching data/reference/depth_2025|2026 exactly
    out["ts"] = out["ts"].dt.tz_convert(NY)
    return out[["ts", "side", "price", "size"]].sort_values(["ts", "side", "price"]).reset_index(drop=True)


def condense_london(df, day):
    """Wide format: raw Databento columns, one row per minute, ts_event floored to the minute.

    scripts/london_depth.py reads ts_event as the minute label and bid_px_NN/ask_px_NN
    directly, so prices must already be decoded floats here.
    """
    df = _front_only(df.reset_index())
    tcol = "ts_event" if "ts_event" in df.columns else "ts_recv"
    ts = pd.to_datetime(df[tcol], utc=True, format="mixed")
    df = df.assign(_m=ts.dt.floor("1min"), _t=ts).sort_values("_t")
    last = df.groupby("_m", as_index=False).tail(1).copy()
    if last.empty:
        return None
    for c in [c for c in last.columns if "_px_" in c or c == "price"]:
        last[c] = np.round(_decode_px(last[c]), 2)
    last["ts_event"] = last["_m"]                       # minute label, UTC
    last = last.drop(columns=["_m", "_t"]).reset_index(drop=True)

    # Match the committed depth_london/ column order exactly. london_depth.py reads by
    # name so this is cosmetic to it, but keeping the artifacts identical in shape means
    # a new file can be concatenated with an old one without a reindex.
    head = ["ts_event", "ts_recv", "rtype", "publisher_id", "instrument_id", "action",
            "side", "depth", "price", "size", "flags", "ts_in_delta", "sequence"]
    lvls = [f"{s}_{f}_{i:02d}" for i in range(10) for f in ("px", "sz", "ct") for s in ("bid", "ask")]
    order = [c for c in head + lvls + ["symbol"] if c in last.columns]
    return last[order + [c for c in last.columns if c not in order]]


def condense_trades(df, day):
    """Footprint: per (minute, price, aggressor side) volume + tick count.

    side 'B' = buy aggressor, 'A' = sell aggressor (verified empirically in
    scripts/champion_journal_cvd.py: CVD = B - A). volume/trades are cast to int64 -
    the DBN export delivers uint32, which silently wraps on the B-A subtraction.
    """
    df = _front_only(df.reset_index())
    tcol = "ts_event" if "ts_event" in df.columns else "ts_recv"
    df = df[df["side"].isin(["B", "A"])].copy()
    if df.empty:
        return None, 0.0
    df["price"] = np.round(_decode_px(df["price"]), 2)
    df["size"] = pd.to_numeric(df["size"], errors="coerce").fillna(0).astype("int64")

    # Front-month band clean: drop calendar-spread / back-month prints that survive the
    # continuous pull. Volume-weighted median +/- 700pt, the documented fallback in
    # data/reference/cvd/README.md.
    tot = int(df["size"].sum())
    vwm = np.average(df["price"], weights=df["size"]) if tot else 0.0
    keep = df["price"].between(vwm - 700, vwm + 700)
    dropped = 1.0 - (df.loc[keep, "size"].sum() / tot if tot else 1.0)
    df = df[keep]
    if df.empty:
        return None, dropped

    # Nanosecond resolution to match the committed footprint_*.parquet files exactly
    # (pandas 3 defaults new datetimes to microseconds; concat across resolutions is
    # legal but the stored dtype should not silently drift between pulls).
    df["ts_minute"] = (pd.to_datetime(df[tcol], utc=True, format="mixed")
                         .dt.floor("1min").astype("datetime64[ns, UTC]"))
    g = (df.groupby(["ts_minute", "price", "side"], as_index=False)
           .agg(volume=("size", "sum"), trades=("size", "size")))
    g["volume"] = g["volume"].astype("int64")
    g["trades"] = g["trades"].astype("int64")
    return g, dropped
''')),

        md(*_src("""
## 5 — Pull and condense

The long cell. Each day is fetched, condensed immediately, and the raw frame freed before the
next request — so ~150 KB/day lands on disk instead of ~1 GB. Days already written are skipped,
so a disconnect costs only the day in flight: just re-run this cell.

Budget roughly 2-4 hours for the full sample. Set `LIMIT_DAYS = 3` in step 2 first if you want
to check the plumbing before committing to the whole run.
""")),

        code(*_src('''
todo = DAYS[:LIMIT_DAYS] if LIMIT_DAYS else DAYS
manifest, fp_by_month, t0 = [], {}, time.time()
print(f"pulling {len(todo)} of {len(DAYS)} sealed days\\n")

for n, day in enumerate(todo, 1):
    ny_path  = f"{OUTDIR}/depth_ny/nq_depth_{day}_ny.csv"
    lon_path = f"{OUTDIR}/depth_london/glbx-mdp3-{day.replace('-', '')}.mbp-10_condensed.csv"
    rec = {"day": day, "ny_rows": 0, "london_rows": 0, "fp_rows": 0, "dropped_pct": np.nan}
    el = time.time() - t0
    print(f"[{n:>3}/{len(DAYS)}] {day}  ({el/60:.1f}m elapsed)", flush=True)

    # ---- NY depth ----
    if PULL_NY_DEPTH and not os.path.exists(ny_path):
        try:
            s, e = utc_window(day, *DEPTH_WINDOWS["ny"])
            df = fetch("mbp-10", s, e).to_df()
            out = condense_ny(df, day) if len(df) else None
            del df; gc.collect()
            if out is not None:
                out.to_csv(ny_path, index=False)
                rec["ny_rows"] = len(out)
                print(f"    ny      {len(out):>7,} rows -> {os.path.basename(ny_path)}")
            else:
                print("    ny      no data (holiday?)")
            del out; gc.collect()
        except Exception as ex:
            print(f"    ny      FAILED: {type(ex).__name__}: {ex}")
    elif os.path.exists(ny_path):
        rec["ny_rows"] = -1
        print("    ny      skip (exists)")

    # ---- London depth ----
    if PULL_LONDON_DEPTH and not os.path.exists(lon_path):
        try:
            s, e = utc_window(day, *DEPTH_WINDOWS["london"])
            df = fetch("mbp-10", s, e).to_df()
            out = condense_london(df, day) if len(df) else None
            del df; gc.collect()
            if out is not None:
                out.to_csv(lon_path, index=False)
                rec["london_rows"] = len(out)
                print(f"    london  {len(out):>7,} rows -> {os.path.basename(lon_path)}")
            else:
                print("    london  no data (holiday?)")
            del out; gc.collect()
        except Exception as ex:
            print(f"    london  FAILED: {type(ex).__name__}: {ex}")
    elif os.path.exists(lon_path):
        rec["london_rows"] = -1
        print("    london  skip (exists)")

    # ---- trades / footprint ----
    if PULL_TRADES:
        mo = day[:7]
        mo_path = f"{OUTDIR}/cvd/footprint_holdout_{mo}.parquet"
        done = os.path.exists(mo_path) and mo not in fp_by_month
        if done:
            print("    trades  skip (month file exists)")
        else:
            try:
                s, e = trades_window(day)
                df = fetch("trades", s, e).to_df()
                out, dropped = condense_trades(df, day) if len(df) else (None, 0.0)
                del df; gc.collect()
                if out is not None:
                    fp_by_month.setdefault(mo, []).append(out)
                    rec["fp_rows"] = len(out)
                    rec["dropped_pct"] = round(dropped * 100, 3)
                    print(f"    trades  {len(out):>7,} minute-rows "
                          f"(band-dropped {dropped*100:.2f}%)")
                else:
                    print("    trades  no data")
                del out; gc.collect()
            except Exception as ex:
                print(f"    trades  FAILED: {type(ex).__name__}: {ex}")

    manifest.append(rec)
    time.sleep(0.5)   # be polite to the rate limiter

# ---- flush monthly footprint files ----
for mo, parts in fp_by_month.items():
    p = f"{OUTDIR}/cvd/footprint_holdout_{mo}.parquet"
    allp = pd.concat(parts, ignore_index=True)
    if os.path.exists(p):
        allp = pd.concat([pd.read_parquet(p), allp], ignore_index=True)
    allp = (allp.groupby(["ts_minute", "price", "side"], as_index=False)
                .agg(volume=("volume", "sum"), trades=("trades", "sum")))
    allp["volume"] = allp["volume"].astype("int64")
    allp["trades"] = allp["trades"].astype("int64")
    allp.to_parquet(p, index=False)
    print(f"wrote {os.path.basename(p)}: {len(allp):,} rows")

pd.DataFrame(manifest).to_csv(f"{OUTDIR}/MANIFEST.csv", index=False)
print(f"\\ndone in {(time.time()-t0)/60:.1f} min")
''')),

        md(*_src("""
## 6 — Verify, zip, download

Coverage check first — a silently missing day is worse than a loud failure — then zip and
download. Send the zip back to Claude.
""")),

        code(*_src('''
import glob

ny_have  = {os.path.basename(f).split("_")[2] for f in glob.glob(f"{OUTDIR}/depth_ny/nq_depth_*_ny.csv")}
lon_have = {os.path.basename(f).split(".")[0].split("-")[-1] for f in glob.glob(f"{OUTDIR}/depth_london/*.csv")}
lon_have = {f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in lon_have if len(d) == 8}

want = set(DAYS)
print(f"sealed days      : {len(want)}")
print(f"ny depth files   : {len(ny_have)}   missing {len(want - ny_have)}")
print(f"london files     : {len(lon_have)}   missing {len(want - lon_have)}")
for label, have in (("ny", ny_have), ("london", lon_have)):
    miss = sorted(want - have)
    if miss:
        print(f"  {label} missing: {miss[:12]}{' ...' if len(miss) > 12 else ''}")

fps = sorted(glob.glob(f"{OUTDIR}/cvd/*.parquet"))
print(f"\\nfootprint files  : {len(fps)}")
for f in fps:
    x = pd.read_parquet(f)
    ts = pd.to_datetime(x.ts_minute, utc=True)
    print(f"  {os.path.basename(f):<34}{len(x):>9,} rows  "
          f"{ts.min():%Y-%m-%d} -> {ts.max():%Y-%m-%d}  "
          f"vol={int(x.volume.sum()):,}  dtypes={x.volume.dtype}/{x.trades.dtype}")

size_mb = sum(os.path.getsize(f) for f in glob.glob(f"{OUTDIR}/**/*", recursive=True)
              if os.path.isfile(f)) / 1e6
print(f"\\ntotal condensed on disk: {size_mb:.1f} MB")

with zipfile.ZipFile(ZIPOUT, "w", zipfile.ZIP_DEFLATED) as z:
    for f in glob.glob(f"{OUTDIR}/**/*", recursive=True):
        if os.path.isfile(f):
            z.write(f, os.path.relpath(f, OUTDIR))

print(f"{ZIPOUT}  ->  {os.path.getsize(ZIPOUT)/1e6:.1f} MB")
print("\\nDownload it from the Colab file browser on the left, then hand it back to Claude.")
print("Unpacks into: depth_ny/  depth_london/  cvd/  MANIFEST.csv")

try:
    from google.colab import files
    files.download(ZIPOUT)
except Exception as ex:
    print(f"(auto-download unavailable: {ex} - grab it from the file browser)")
''')),

        md(*_src("""
## What happens to it back in the repo

```
depth_ny/*.csv       -> data/reference/depth_2023_24/
depth_london/*.csv   -> data/reference/depth_london/
cvd/*.parquet        -> data/reference/cvd/
```

Then the canon is scored **unchanged** — same frozen 2025 thresholds, no refits, no new knobs.
Any threshold that moves turns this from a holdout into a fit.

Raw data never enters the repo; only these condensed artifacts do.
""")),
    ]

    return {
        "cells": cells,
        "metadata": {
            "colab": {"provenance": [], "toc_visible": True},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }


def build_single(nb: dict) -> dict:
    """One-cell edition, concatenated FROM the multi-cell notebook.

    Derived rather than re-authored on purpose: the two versions cannot drift, because
    this is literally the same source text joined together. `tests/` asserts both define
    byte-identical functions.
    """
    blocks = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    banner = [
        "# =============================================================================",
        "# NQ HOLDOUT PULL — 2023/2024 out-of-regime canon validation.  ONE CELL, RUN IT.",
        "#",
        "# Edit only the CONFIG block below. Everything after it is machinery.",
        "# Resumable: re-running skips days already on disk, so a Colab disconnect costs",
        "# only the day in flight.",
        "# =============================================================================",
        "",
    ]
    src = "\n".join(banner) + "\n\n".join(blocks)
    return {
        "cells": [{"cell_type": "code", "execution_count": None, "metadata": {},
                   "outputs": [], "source": _src(src)}],
        "metadata": {"colab": {"provenance": []},
                     "kernelspec": {"display_name": "Python 3", "name": "python3"},
                     "language_info": {"name": "python"}},
        "nbformat": 4, "nbformat_minor": 0,
    }


def main() -> None:
    if not DAYS_CSV.exists():
        raise SystemExit(f"missing {DAYS_CSV.relative_to(ROOT)} — run scripts/sample_holdout_days.py first")
    nb = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(nb, indent=1) + "\n")
    n_code = sum(1 for c in nb["cells"] if c["cell_type"] == "code")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(nb['cells'])} cells, {n_code} code)")

    single = build_single(nb)
    OUT_SINGLE.write_text(json.dumps(single, indent=1) + "\n")
    n_lines = len("".join(single["cells"][0]["source"]).split("\n"))
    print(f"wrote {OUT_SINGLE.relative_to(ROOT)} (1 cell, {n_lines} lines)")


if __name__ == "__main__":
    main()
