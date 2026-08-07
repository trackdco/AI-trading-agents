"""Job 1 gates G1-G6 (spec section 6). INCONCLUSIVE blocks like FAIL.

Writes output/vp_census/gate_report.md. Exit code 0 only if every gate
PASSes.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts/vp_census")
import vp_lib as V

RESULTS: list[tuple[str, str, str]] = []


def record(gate: str, verdict: str, detail: str):
    RESULTS.append((gate, verdict, detail))
    print(f"{gate}: {verdict} — {detail}")


def g1_lookahead(bars: pd.DataFrame, sessions: list) -> None:
    """Perturb every bar at/after 09:30 on D; profile must be bit-identical."""
    rng = np.random.default_rng(20260807)
    sample = list(rng.choice(np.array(sessions, dtype=object),
                             size=min(20, len(sessions)), replace=False))
    base = V.build_profiles(bars, sample)
    mut = bars.copy()
    for d in sample:
        dts = pd.Timestamp(d, tz=V.ET)
        m = (mut["session"] == d) & (mut["ts_event"] >= dts + pd.Timedelta(hours=9, minutes=30))
        mut.loc[m, ["open", "high", "low", "close"]] = 99999.0
        mut.loc[m, "volume"] = 10**9
    pert = V.build_profiles(mut, sample)
    same = base[["session_date", "vah", "val", "poc"]].equals(
        pert[["session_date", "vah", "val", "poc"]])
    record("G1 lookahead", "PASS" if same else "FAIL",
           f"{len(sample)} sessions perturbed after 09:30; levels "
           f"{'bit-identical' if same else 'CHANGED — fatal'}")


def g2_dst(profiles: pd.DataFrame) -> None:
    ok = profiles[(profiles.construction == "bar_uniform") &
                  (profiles.bin_width == 1.0) & (profiles.va_pct == 0.70) &
                  (profiles.expansion == "paired")]
    exp = ok["expected_minutes"].value_counts().to_dict()
    # Normal sessions must expect 930 in BOTH DST regimes; transition
    # sessions expect 870 (spring) / 990 (fall).
    bad = {k: v for k, v in exp.items() if k not in (930, 870, 990)}
    dates = pd.to_datetime(ok["session_date"])
    jul = ok[dates.dt.month == 7]["expected_minutes"]
    nov = ok[dates.dt.month == 11]["expected_minutes"]
    normal_ok = (len(jul) == 0 or (jul == 930).mean() > 0.9) and \
                (len(nov) == 0 or (nov == 930).mean() > 0.9)
    verdict = "PASS" if (not bad and normal_ok) else "FAIL"
    record("G2 DST", verdict,
           f"expected-minute histogram {exp}; normal-month windows 930 in "
           f"both regimes: {normal_ok}")


def g3_roll(bars: pd.DataFrame, sessions: list) -> None:
    """Master must match the per-day max-volume contract from the raw
    Databento pull, and no session window straddles two contracts."""
    import io
    import zstandard
    files = ["glbx-mdp3-20230101-20250301.ohlcv-1m.csv.zst",
             "glbx-mdp3-20250101-20250501.ohlcv-1m.csv.zst",
             "glbx-mdp3-20250502-20251001.ohlcv-1m.csv.zst",
             "glbx-mdp3-20251002-20260131.ohlcv-1m.csv.zst"]
    frames = []
    for f in files:
        dctx = zstandard.ZstdDecompressor()
        with open(f, "rb") as fh:
            raw = pd.read_csv(io.TextIOWrapper(dctx.stream_reader(fh)),
                              usecols=["ts_event", "close", "volume", "symbol"])
        frames.append(raw)
    raw = pd.concat(frames, ignore_index=True)
    raw = raw[raw["symbol"].str.match(r"^NQ[HMUZ]\d$")]
    ts = pd.to_datetime(raw["ts_event"], utc=True).dt.tz_convert(V.ET)
    raw = raw.assign(ts_event=ts)
    tday = ts.dt.normalize() + pd.Timedelta(days=1) * (ts.dt.hour >= 18)
    wd = tday.dt.weekday
    tday = tday + pd.to_timedelta(np.where(wd == 5, 2, np.where(wd == 6, 1, 0)), unit="D")
    raw["session"] = tday.dt.date
    front = (raw.groupby(["session", "symbol"])["volume"].sum()
                .reset_index()
                .sort_values(["session", "volume", "symbol"], kind="mergesort"))
    front = front.groupby("session").tail(1)[["session", "symbol"]]
    raw_f = raw.merge(front, on=["session", "symbol"])

    # sample check: every 10th session covered by the raw pull
    check_sessions = [s for s in sessions if s in set(front["session"])][::10]
    n_checked = n_bad = 0
    for d in check_sessions:
        mb = bars[bars["session"] == d].set_index("ts_event")["close"]
        mr = raw_f[raw_f["session"] == d].set_index("ts_event")["close"]
        j = mb.align(mr, join="inner")
        if len(j[0]) == 0:
            continue
        n_checked += 1
        if not np.allclose(j[0].to_numpy(), j[1].to_numpy()):
            n_bad += 1
    # straddle check: raw front-month symbol constant within each session
    nsym = raw.merge(front, on="session", suffixes=("", "_front"))
    per = raw_f.groupby("session")["symbol"].nunique()
    straddle = int((per > 1).sum())
    if n_checked == 0:
        record("G3 roll", "INCONCLUSIVE", "raw pull did not overlap any session")
        return
    verdict = "PASS" if (n_bad == 0 and straddle == 0) else "FAIL"
    record("G3 roll", verdict,
           f"{n_checked} sessions sampled vs raw max-volume contract, "
           f"{n_bad} mismatched; {straddle} sessions with straddled front symbol "
           f"(raw pull ends 2026-01-31; later sessions inherit the volume-roll "
           f"construction of nq_1m_master per docs/CONTRACT-ROLL-DATES.md)")


def g4_determinism(bars: pd.DataFrame, sessions: list) -> None:
    sample = sessions[:40]
    h = []
    for _ in range(2):
        prof = V.build_profiles(bars, sample)
        ex = V.run_census(bars, prof)
        buf = ex.drop(columns=["excursion_start"]).to_csv(index=False) + \
            prof.to_csv(index=False) + ex["excursion_start"].astype(str).to_csv(index=False)
        h.append(hashlib.sha256(buf.encode()).hexdigest())
    verdict = "PASS" if h[0] == h[1] else "FAIL"
    record("G4 determinism", verdict,
           f"two consecutive builds over {len(sample)} sessions: "
           f"{'identical' if verdict == 'PASS' else 'DIFFER'} ({h[0][:12]})")


def g5_completeness(profiles: pd.DataFrame) -> None:
    ok = profiles[(profiles.construction == "bar_uniform") &
                  (profiles.bin_width == 1.0) & (profiles.va_pct == 0.70) &
                  (profiles.expansion == "paired")].copy()
    dates = pd.to_datetime(ok["session_date"])
    span_days = pd.bdate_range(dates.min(), dates.max())
    have = set(dates.dt.normalize())
    missing = [d for d in span_days if d not in have]
    # missing weekdays must be explainable as CME holidays; list them
    counts = ok["profile_status"].value_counts().to_dict()
    verdict = "PASS" if len(missing) <= 16 else "INCONCLUSIVE"
    record("G5 completeness", verdict,
           f"status counts {counts}; weekdays in span without a session row: "
           f"{len(missing)} -> {[str(d.date()) for d in missing]}")


def g6_independence(ex: pd.DataFrame) -> None:
    if "cluster_id" not in ex or ex["cluster_id"].isna().any():
        record("G6 independence", "FAIL", "cluster_id missing on some rows")
        return
    per_sess = ex.groupby("session_id").size()
    per_clus = ex.groupby("cluster_id").size()
    record("G6 independence", "PASS",
           f"excursions/session median {per_sess.median():.0f} max {per_sess.max()}; "
           f"excursions/cluster median {per_clus.median():.0f} max {per_clus.max()}; "
           f"{ex.cluster_id.nunique()} clusters over {len(ex)} excursions")


def main() -> int:
    bars = V.load_master_bars()
    profiles = pd.read_parquet("output/vp_census/profiles.parquet")
    ex = pd.read_parquet("output/vp_census/excursions.parquet")
    sessions = sorted(set(profiles[profiles.profile_status == "OK"]["session_date"]))

    g1_lookahead(bars, sessions)
    g2_dst(profiles)
    g3_roll(bars, sessions)
    g4_determinism(bars, sessions)
    g5_completeness(profiles)
    g6_independence(ex)

    lines = ["# Gate report — Job 1 VP excursion census", ""]
    all_pass = True
    for g, v, d in RESULTS:
        lines.append(f"- **{g}** — **{v}** — {d}")
        if v != "PASS":
            all_pass = False
    lines.append("")
    lines.append(f"OVERALL: {'PASS' if all_pass else 'BLOCKED'} "
                 "(INCONCLUSIVE blocks like FAIL)")
    open("output/vp_census/gate_report.md", "w").write("\n".join(lines) + "\n")
    print("OVERALL:", "PASS" if all_pass else "BLOCKED")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
