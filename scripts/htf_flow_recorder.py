#!/usr/bin/env python3
"""HTF LIVE FLOW RECORDER — log-only, acts on NOTHING (C1; E-item 5).

Stage-3 shadow artifact. Logs every trigger of BOTH mechanisms at ALL SEVEN
declared loci (bbma15, poc, val, vah, vwap, vwap_m1, vwap_p1) — taken or
not, nothing is ever taken — with all twelve flow features, computed by THE
SAME CODE the census uses (scripts.htf_ma_level_census.day_rows import —
parity by construction, no reimplementation).

UPGRADED 2026-08-07 from the single-locus (bbma15) grammar. E1 found the
edge lives at break-of-VAL and break-of-VWAP-1, not at the incumbent, so a
single-locus recorder would have accrued a year of forward data on the
wrong grammar. Coverage is now ~5x per session (122-141 triggers vs 18-26).

Forward-recorded flow is the only validation route for any SELECTION layer
(the flow holdout cannot resolve a +4pp effect, D3), so every session
without this recorder is uncontaminated data lost permanently.

Modes:
  --replay SESS_DAY     certification: recompute one historical session from
                        the research files and assert row/feature identity
                        against the M-TABLE fit parquet (the parity gate —
                        run this ON THE VPS before leaving it unattended)
  --live                tail the live per-minute state files and append new
                        triggers to the JSONL journal each 15m close

Live inputs (config: config/flow_recorder.json):
  bars_path   1m OHLCV (parquet/csv, ts_event or NY-tz index; the existing
              intraday reader's bar output)
  fp_path     per-minute footprint state with columns b/a/vol/delta/vwp —
              fp_minutes schema; delta MUST be buys−sells (side 'B' − side
              'A' of the footprint capture; empirically verified 2026-08-07:
              corr(delta, 1m vwp change) = +0.46)
  journal     output JSONL path

Startup self-gates (refuse to log rather than log garbage):
  G-DELTA     corr(delta, dvwp) over the trailing tape must exceed +0.2 —
              catches a sign-inverted or dead delta feed
  G-DEPTH     >= 30h of bars and >= 20 completed 15m bars before first log
  G-CLOCK     newest bar within 3 minutes of wall clock (live mode)

No order path, no DTC, no position logic anywhere in this file.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.htf_ma_level_census import LOCI, day_rows              # noqa: E402
from scripts.htf_ma_mtable import FLOW_NAMES                        # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

CFG = ROOT / "config/flow_recorder.json"


def load_frames(bars_path: str, fp_path: str):
    bars = pd.read_parquet(bars_path) if bars_path.endswith("parquet") \
        else pd.read_csv(bars_path)
    if "ts_event" in bars.columns:
        bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
        bars = bars.set_index("mi")
    bars = bars.sort_index()[["open", "high", "low", "close", "volume"]]
    fp = pd.read_parquet(fp_path) if fp_path.endswith("parquet") \
        else pd.read_csv(fp_path, index_col=0, parse_dates=True)
    return bars, fp


def gate_delta(fp: pd.DataFrame) -> float:
    d = fp.tail(20000)
    c = float(np.corrcoef(d.delta.iloc[1:], d.vwp.diff().iloc[1:])[0, 1])
    return c


def sess_day_of(ts: pd.Timestamp) -> str:
    t = ts.tz_convert(NY)
    d = t.normalize()
    return str((d if t.hour >= 18 else d - pd.Timedelta(days=1)).date())


def row_key(r: dict) -> str:
    return (f"{r['sess_day']}|{r['t']}|{r.get('locus','bbma15')}|{r['arm']}"
            f"|{r['side']}|{r['n_attempts']}")


def emit(journal: Path, rows: list[dict], seen: set) -> int:
    n = 0
    with open(journal, "a") as f:
        for r in rows:
            k = row_key(r)
            if k in seen:
                continue
            seen.add(k)
            out = {k2: (str(v) if isinstance(v, pd.Timestamp) else
                        (None if isinstance(v, float) and np.isnan(v) else v))
                   for k2, v in r.items()}
            out["s1_keep"] = (r.get("flowconf") not in (0, 0.0))
            out["logged_at"] = pd.Timestamp.now(tz=NY).isoformat()
            f.write(json.dumps(out, default=str) + "\n")
            n += 1
    return n


def replay(sess_day: str) -> None:
    bars, fp = load_frames("data/reference/nq_1m_master.parquet"
                           if sess_day < "2026-02-01"
                           else "data/reference/nq_1m_feb_jul2026.parquet",
                           "output/fp_minutes_full.parquet")
    rows = day_rows(bars, sess_day, LOCI, fp=fp)
    F = pd.read_parquet(ROOT / "output/htf_ma_census/mtable_fit.parquet")
    ref = F[F.sess_day == sess_day]
    ok, checked = True, 0
    for r in rows:
        if r.get("locus") != "bbma15":
            continue                    # the M-TABLE indexes bbma15 only
        m = ref[(ref.t == r["t"]) & (ref.arm == r["arm"])
                & (ref.side == r["side"])
                & (ref.n_attempts == r["n_attempts"])]
        if len(m) != 1:
            # rows dropped by named exclusions exist in recorder output only
            continue
        for k in FLOW_NAMES + ["entry", "stop", "risk"]:
            a, b = r[k], m.iloc[0][k]
            same = (pd.isna(a) and pd.isna(b)) or a == b or \
                (np.isfinite(a) and np.isfinite(b) and abs(a - b) < 1e-9)
            if not same:
                ok = False
                print(f"PARITY FAIL {r['t']} {k}: recorder={a} table={b}")
        checked += 1
    per = {}
    for r in rows:
        per[r.get("locus", "?")] = per.get(r.get("locus", "?"), 0) + 1
    miss = [l for l in LOCI if per.get(l, 0) == 0]
    flow_cov = np.mean([np.isfinite(r.get("flowconf", np.nan)) for r in rows]) \
        if rows else 0.0
    print(f"REPLAY {sess_day}: {len(rows)} triggers across {len(per)} loci")
    print(f"  per-locus: {per}")
    print(f"  flow coverage: {flow_cov*100:.1f}% | bbma15 rows checked vs "
          f"M-TABLE: {checked} | PARITY {'PASS' if ok else 'FAIL'}")
    if miss:
        print(f"  NOTE: no triggers today at {miss} (not a failure)")
    ok = ok and checked > 0 and flow_cov > 0.9
    sys.exit(0 if ok else 1)


def live() -> None:
    cfg = json.loads(CFG.read_text())
    journal = Path(cfg["journal"])
    journal.parent.mkdir(parents=True, exist_ok=True)
    seen: set = set()
    if journal.exists():
        for line in journal.read_text().splitlines():
            try:
                seen.add(row_key(json.loads(line)))
            except Exception:
                pass
    last_q = None
    print(f"flow recorder up — journal {journal} — ACTS ON NOTHING")
    while True:
        now = pd.Timestamp.now(tz=NY)
        q = now.floor("15min")
        # compute ~40s after each 15m close so the minute files are flushed
        if q != last_q and (now - q).total_seconds() >= 40:
            last_q = q
            try:
                bars, fp = load_frames(cfg["bars_path"], cfg["fp_path"])
                g = gate_delta(fp)
                if not (g > 0.2):
                    print(f"{now} G-DELTA FAIL corr={g:+.2f} — NOT logging")
                    time.sleep(30)
                    continue
                if (now - bars.index[-1]).total_seconds() > 180:
                    print(f"{now} G-CLOCK stale bars ({bars.index[-1]}) — "
                          f"NOT logging")
                    time.sleep(30)
                    continue
                sd = sess_day_of(now)
                rows = day_rows(bars, sd, LOCI, fp=fp)
                n = emit(journal, rows, seen)
                if n:
                    print(f"{now} +{n} triggers logged (session {sd})")
            except Exception as e:                        # log-only: never die
                print(f"{now} recorder error: {e}")
        time.sleep(10)


def main() -> None:
    if "--replay" in sys.argv:
        replay(sys.argv[sys.argv.index("--replay") + 1])
    elif "--live" in sys.argv:
        live()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
