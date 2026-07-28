#!/usr/bin/env python3
"""STEPS 1-4 of Brake's order-flow brief (2026-07-28): prove the data, coverage vs trades,
clock alignment, fresh-session check. NO features, NO outcomes, NO tests.

Research lane. Writes only research/sweep_2026_07/orderflow/. Reads repo artefacts read-only.
"""
import glob
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = "/home/user/AI-trading-agents"
OUT = os.path.join(REPO, "research/sweep_2026_07/orderflow")
os.makedirs(OUT, exist_ok=True)
R = {}

# ---------------------------------------------------------------- STEP 1: prove the data
print("=" * 90)
print("STEP 1 — WHAT ORDER-FLOW DATA EXISTS")
print("=" * 90)
scid = glob.glob(f"{REPO}/**/*.scid", recursive=True)
mbo = [p for p in glob.glob(f"{REPO}/**/*mbo*", recursive=True) if os.path.isfile(p)]
print(f"live Sierra .scid files: {len(scid)}   mbo-named files: {len(mbo)}")

files = sorted(glob.glob(f"{REPO}/data/reference/cvd/footprint_*.parquet"))
spans, tot = [], 0
frames = []
for f in files:
    t = pq.read_table(f, columns=["ts_minute", "side", "volume"]).to_pandas()
    t["ts_minute"] = pd.to_datetime(t.ts_minute, utc=True)
    frames.append(t)
    d = t.ts_minute
    spans.append((os.path.basename(f), len(t), str(d.min()), str(d.max()),
                  d.dt.strftime("%Y-%m-%d").nunique()))
    tot += len(t)
    print(f"  {os.path.basename(f):34s} {len(t):>10,} rows  {d.min().date()} -> {d.max().date()}"
          f"  ({d.dt.strftime('%Y-%m-%d').nunique()} days)")
T = pd.concat(frames, ignore_index=True)
del frames
print(f"  TOTAL {tot:,} rows   SPAN {T.ts_minute.min()} -> {T.ts_minute.max()}")
mo = sorted(T.ts_minute.dt.strftime("%Y-%m").unique())
print(f"  months: {mo}")
dup_min_files = 0  # contiguity: any minute in >1 file would double-count
R["step1_files"] = spans

# THE GATE: fraction of records/minutes carrying usable two-sided aggressor volume.
# A tape record is one (minute, price, side); 'usable bid and ask volume' at the minute level
# means the minute has BOTH buyer-aggressor (B) and seller-aggressor (A) volume > 0.
side_vol = T.groupby([T.ts_minute, "side"], observed=True).volume.sum().unstack(fill_value=0)
n_min = len(side_vol)
both = ((side_vol.get("B", 0) > 0) & (side_vol.get("A", 0) > 0)).mean()
volB, volA = int(side_vol.get("B", 0).sum()), int(side_vol.get("A", 0).sum())
print(f"\nGATE — two-sided usability:")
print(f"  distinct minutes on tape: {n_min:,}")
print(f"  minutes with BOTH bid- and ask-side volume > 0: {both*100:.2f}%")
print(f"  total buyer-aggressor volume {volB:,}  seller-aggressor {volA:,}  "
      f"(B share {volB/(volB+volA)*100:.1f}%)")
rec_nonzero = (T.volume > 0).mean()
print(f"  records with volume > 0: {rec_nonzero*100:.3f}%")
R["step1_gate"] = dict(minutes=n_min, both_sides_pct=float(both * 100),
                       volB=volB, volA=volA, records_nonzero_pct=float(rec_nonzero * 100))

# depth gate: snapshots with full 10x2 ladder
dep_files = sorted(glob.glob(f"{REPO}/data/reference/depth_2025/*.csv") +
                   glob.glob(f"{REPO}/data/reference/depth_2026/*.csv"))
ok_days = full = tot_snap = 0
for f in dep_files[::25] + [dep_files[-1]]:          # sample every 25th + last (fast, stated)
    d = pd.read_csv(f)
    g = d.groupby(["ts", "side"]).size().unstack(fill_value=0)
    tot_snap += len(g)
    full += int(((g.get("bid", 0) == 10) & (g.get("ask", 0) == 10)).sum())
    ok_days += 1
print(f"\n  depth (MBP-10), sampled {ok_days} of {len(dep_files)} days: "
      f"{full}/{tot_snap} snapshots with a full 10x2 ladder ({full/tot_snap*100:.1f}%)")
R["step1_depth"] = dict(days_total=len(dep_files), sampled=ok_days,
                        full_ladder_pct=float(full / tot_snap * 100))

# ---------------------------------------------------------------- STEP 2: coverage vs trades
print("\n" + "=" * 90)
print("STEP 2 — COVERAGE AGAINST THE 216 PRE-MARKET TRADES (not against calendar)")
print("=" * 90)
F = pd.read_csv(f"{REPO}/research/sweep_2026_07/phase2/phase2_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
F["et"] = F.ft.dt.tz_convert("America/New_York")
F["hm"] = F.et.dt.hour * 60 + F.et.dt.minute
assert len(F) == 216
tape_minutes = pd.DatetimeIndex(side_vol.index)
two_sided = set(side_vol.index[(side_vol.get("B", 0) > 0) & (side_vol.get("A", 0) > 0)])

PRE_WIN = 30  # defined pre-fill window (minutes), fixed here before anything is tested
rows = []
for r in F.itertuples(index=False):
    fill_min = r.ft.floor("min")
    need = pd.date_range(fill_min - pd.Timedelta(minutes=PRE_WIN), fill_min - pd.Timedelta(minutes=1),
                         freq="1min", tz="UTC")
    have = sum(1 for m in need if m in two_sided)
    at_fill_prev = (fill_min - pd.Timedelta(minutes=1)) in two_sided
    rows.append(dict(hm=r.hm, day=r.day, have=have, prev_ok=at_fill_prev))
C = pd.DataFrame(rows)
C["bucket"] = pd.cut(C.hm, [479, 510, 540, 570], labels=["08:00-08:29", "08:30-08:59", "09:00-09:29"])
C["full"] = C.have == PRE_WIN
C["partial"] = (C.have > 0) & (C.have < PRE_WIN)
C["absent"] = C.have == 0
print(f"pre-fill window: {PRE_WIN} completed minutes strictly before the fill minute, two-sided")
print(f"  FULL {int(C.full.sum())}/216   PARTIAL {int(C.partial.sum())}   ABSENT {int(C.absent.sum())}")
print(f"  prior-minute (fill-1) present: {int(C.prev_ok.sum())}/216")
print(f"\n  {'bucket':14s} {'n':>4} {'full':>5} {'partial':>8} {'absent':>7} {'min have (of 30)':>17}")
for b, s in C.groupby("bucket", observed=True):
    print(f"  {b:14s} {len(s):>4} {int(s.full.sum()):>5} {int(s.partial.sum()):>8} "
          f"{int(s.absent.sum()):>7} {int(s.have.min()):>17}")
part = C[C.partial | C.absent]
if len(part):
    print(f"  partial/absent trades by day: {part.day.value_counts().to_dict()}")
R["step2"] = dict(window_min=PRE_WIN, full=int(C.full.sum()), partial=int(C.partial.sum()),
                  absent=int(C.absent.sum()), prev_ok=int(C.prev_ok.sum()),
                  by_bucket={str(b): dict(n=len(s), full=int(s.full.sum()))
                             for b, s in C.groupby("bucket", observed=True)})

# ---------------------------------------------------------------- STEP 3: clock alignment
print("\n" + "=" * 90)
print("STEP 3 — CLOCK ALIGNMENT (arithmetic shown)")
print("=" * 90)
print(f"tape ts_minute dtype : {T.ts_minute.dtype}   (tz-aware UTC)")
print(f"book fill dtype      : {F.ft.dtype}   (tz-aware UTC)")
bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet", columns=["ts_event"])
bts = pd.to_datetime(bars.ts_event)
print(f"bars ts_event dtype  : {bts.dtype}   (tz-aware America/New_York)")
# 3a: tape minutes vs bar minutes, one EST day and one EDT day — exact-match rate
for day, regime in [("2025-12-10", "EST (UTC-5)"), ("2026-06-10", "EDT (UTC-4)")]:
    bm = set(bts[bts.dt.strftime("%Y-%m-%d") == day].dt.tz_convert("UTC").dt.floor("min"))
    tm = set(tape_minutes[(tape_minutes >= pd.Timestamp(day, tz="UTC") - pd.Timedelta(hours=6))
                          & (tape_minutes < pd.Timestamp(day, tz="UTC") + pd.Timedelta(hours=30))])
    inter = len(bm & tm)
    print(f"  {day} ({regime}): bar minutes {len(bm):,}, tape∩bars exact-UTC matches {inter:,} "
          f"({inter/len(bm)*100:.1f}% of bar minutes)")
# 3b: DST arithmetic on real trades either side of each US transition
print("\n  DST arithmetic — same 08:xx ET wallclock, UTC instant must move by exactly 3600 s:")
for d1, d2, name in [("2025-10-31", "2025-11-03", "US fall-back 2025-11-02"),
                     ("2026-03-06", "2026-03-09", "US spring-fwd 2026-03-08")]:
    a = F[F.day == d1].head(1)
    b_ = F[F.day == d2].head(1)
    if len(a) and len(b_):
        ta, tb = a.ft.iloc[0], b_.ft.iloc[0]
        ea, eb = a.et.iloc[0], b_.et.iloc[0]
        # normalise both to the same ET wallclock minute for the arithmetic
        base_a = ta - pd.Timedelta(minutes=ea.minute + 60 * (ea.hour - 8))
        base_b = tb - pd.Timedelta(minutes=eb.minute + 60 * (eb.hour - 8))
        diff = (base_b - base_a).total_seconds() % 86400
        print(f"    {name}: 08:00 ET = {base_a.strftime('%H:%M')} UTC before, "
              f"{base_b.strftime('%H:%M')} UTC after -> wallclock-anchored UTC shift "
              f"{diff:.0f}s mod day ({'PASS: 3600' if abs(diff-3600) < 1 or abs(diff-82800) < 1 else 'CHECK'})")
        pa = (ta.floor('min') - pd.Timedelta(minutes=1)) in two_sided
        pb = (tb.floor('min') - pd.Timedelta(minutes=1)) in two_sided
        print(f"      tape present at fill-1 on both sides of the change: {pa} / {pb}")
    else:
        print(f"    {name}: no pre-market trade on {d1} or {d2} — using bar-minute join above as the proof")
print("  conclusion basis: every coverage count in STEP 2 is an exact UTC-minute join between the")
print("  book's fill (UTC) and the tape (UTC); a 1-hour slip would make those joins miss ~100%.")
R["step3"] = "exact UTC-minute joins; DST arithmetic printed above"

# ---------------------------------------------------------------- STEP 4: fresh sessions?
print("\n" + "=" * 90)
print("STEP 4 — DOES ANYTHING EXTEND PAST 2026-07-10 (book end)?")
print("=" * 90)
book_max = F.day.max()
tape_max = T.ts_minute.max().date()
bars_max = bts.max().date()
print(f"  book last trade day : {book_max}")
print(f"  bars last session   : {bars_max}")
print(f"  tape last day       : {tape_max}")
extra_bar_days = sorted({d for d in bts.dt.strftime("%Y-%m-%d").unique() if d > book_max})
print(f"  bar sessions AFTER the book ends: {extra_bar_days}")
print(f"  tape days after bars end (unusable without bars): "
      f"{sorted({str(d.date()) for d in tape_minutes if str(d.date()) > str(bars_max)})}")
R["step4"] = dict(book_max=str(book_max), bars_max=str(bars_max), tape_max=str(tape_max),
                  extra_bar_days=extra_bar_days)

json.dump(R, open(f"{OUT}/step1_4_report.json", "w"), indent=1, default=str)
side_vol.reset_index().to_parquet(f"{OUT}/tape_minute_sides.parquet", index=False)
print(f"\nwrote {OUT}/step1_4_report.json and tape_minute_sides.parquet")
