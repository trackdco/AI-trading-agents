#!/usr/bin/env python3
"""ORDER-FLOW FEATURE SUBSTRATE for the London 10:00-13:00 engine book — entries AND exits.

Builds the joined table every downstream check reads: 992 engine fills (2025-06-02 -> 2026-07-15,
the span where order-flow data exists) x order-flow state from three sources:

  CVD / footprint   data/reference/cvd/footprint_*.parquet    23,278,419 rows, per-minute
                    per-price per-aggressor-side tape (B = lifted offer, A = hit bid)
  DEPTH / heatmap   data/reference/depth_london_10_13/*.parquet  1,069,240 rows, per-minute
                    top-10 book snapshots, 10:00-13:00 London (matches the book's window)
  BARS              the substrate's own fill/exit prices and timestamps

WHAT IS HONEST ABOUT THE SAMPLE, stated here so no downstream reader has to rediscover it:
  * 992 fills, NOT the substrate's 3,005 — only fills on/after 2025-06-02 have order flow.
  * JANUARY 2026 IS MISSING from the footprint files on this branch (q4_2025 ends 2026-01-01,
    feb_mar2026 starts 2026-02-01). Rows in that gap get NaN CVD features, never zero, and are
    excluded per-check rather than silently imputed. The gap is not random: an earlier pass
    found the Jan-2026 signals it removes were all losers and all in H2.
  * raw book: 22.9% WR, -$53,462 over 992 fills. Any edge must come FROM the checks.
  * ~3,300 order-flow variables were already mined over this same data with ZERO survivors,
    and two falsifiers fired (direction-BLIND activity read as well as direction-aware; plain
    30-min bar volume beat all 18 footprint checks). Entry-side results here are therefore
    re-tests on an exhausted space; the EXIT side is the genuinely unexplored half.

THREE CORRECTNESS TRAPS, each one previously shipped as a live bug in this project:
  1 UNSIGNED OVERFLOW. depth `size`/`ct` and footprint `volume`/`trades` arrive as unsigned
    ints; `support - resist` or `buys - sells` WRAPS to a huge positive and inverts every
    imbalance feature. Everything is cast to float64/int64 on load. Non-negotiable.
  2 LOOKAHEAD. Entry features read the tape/book STRICTLY BEFORE the fill minute
    (`< fill_minute`, not `<=`). In-trade features at bar k read strictly `<= k`. A prior
    version of a sibling script used `i+1` here and manufactured a 65%-vs-31% win-rate gap
    that evaporated at `i`.
  3 CONTRACT MISMATCH. The depth export is its own series; when it rolls out of step with the
    bars, book prices sit hundreds of points from the trade. Rows where |mid - entry| > 10pt
    are flagged `px_mismatch` and dropped from book features (normal agreement is ~0.5pt).

    python3 scripts/london_of_substrate.py [--out <path>]
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = os.environ.get(
    "LONDON_SCRATCH",
    "/tmp/claude-0/-home-user-AI-trading-agents/c2c5ecfb-26be-555c-a4e7-e400e2cf3ead/scratchpad")
SUBSTRATE = os.path.join(SCRATCH, "london_engine_substrate.parquet")
FP_GLOB = os.path.join(HERE, "data/reference/cvd/footprint_*.parquet")
DEPTH_GLOB = os.path.join(SCRATCH, "canon/data/reference/depth_london_10_13/*.parquet")
PX_MISMATCH_PT = 10.0
LOOKBACKS = (5, 15, 30)          # minutes, for pre-fill tape windows
DEPTH_LEVELS = (3, 5, 10)        # top-N book aggregations
#: a tape window must END within this many minutes of the fill (else the tape is stale)
STALE_TOL_MIN = 5
#: ...and must not SPAN more than this multiple of its own length (else it crosses a data gap).
#: Generous, because thin minutes are legitimately absent inside an active session; the failure
#: this catches is a window reaching back WEEKS, not one reaching back a few quiet minutes.
GAP_TOL_MULT = 3


def _utc(s):
    t = pd.to_datetime(s, utc=True)
    return t


# --------------------------------------------------------------------------- tape
def build_minute_tape() -> pd.DataFrame:
    """Per-minute aggregate of the aggressor-tagged tape.

    delta = buy-aggressor volume - sell-aggressor volume, computed in int64 (see trap 1).
    Also keeps the per-minute price dispersion needed for absorption: volume concentrated at
    one price with a narrow range is absorption; the same volume spread over a wide range is
    displacement. Those are opposite signals and collapse into one number if you only keep
    total volume."""
    files = sorted(glob.glob(FP_GLOB))
    if not files:
        raise SystemExit(f"no footprint files at {FP_GLOB}")
    out = []
    for f in files:
        d = pd.read_parquet(f, columns=["ts_minute", "price", "side", "volume", "trades"])
        d["volume"] = d["volume"].astype("int64")        # trap 1
        d["trades"] = d["trades"].astype("int64")
        d["ts_minute"] = _utc(d.ts_minute)
        sign = np.where(d.side.values == "B", 1, -1)
        d["signed"] = d.volume.values * sign
        g = d.groupby("ts_minute", sort=False)
        agg = g.agg(vol=("volume", "sum"), trd=("trades", "sum"),
                    delta=("signed", "sum"),
                    px_lo=("price", "min"), px_hi=("price", "max"))
        # volume-weighted price + concentration (share of the minute's volume at its busiest price)
        vw = (d.assign(pv=d.price * d.volume).groupby("ts_minute", sort=False)
              .agg(pv=("pv", "sum"), v=("volume", "sum")))
        agg["vwp"] = vw.pv / vw.v.replace(0, np.nan)
        top = (d.groupby(["ts_minute", "price"], sort=False).volume.sum()
               .groupby("ts_minute").max())
        agg["poc_share"] = top / agg.vol.replace(0, np.nan)
        out.append(agg.reset_index())
        print(f"  tape {os.path.basename(f):34s} -> {len(agg):>7,} minutes", flush=True)
    t = pd.concat(out, ignore_index=True).sort_values("ts_minute").reset_index(drop=True)
    t["cvd"] = t.delta.cumsum()
    t["avg_trade"] = t.vol / t.trd.replace(0, np.nan)
    t["rng"] = t.px_hi - t.px_lo
    return t


# --------------------------------------------------------------------------- book
def build_minute_book() -> pd.DataFrame:
    """Per-minute book state from the top-10 ladder.

    Emits, for each of DEPTH_LEVELS: resting size each side, the imbalance, and the biggest
    single resting level ("wall") with its distance from mid. Wall PERSISTENCE is computed
    afterwards on the minute series — a wall one minute old is not a wall, and telling those
    apart is the whole difference between reading liquidity and reading a spoof."""
    files = sorted(glob.glob(DEPTH_GLOB))
    if not files:
        raise SystemExit(f"no depth files at {DEPTH_GLOB}")
    rows = []
    for f in files:
        d = pd.read_parquet(f)
        d["size"] = d["size"].astype("float64")          # trap 1
        d["ts"] = _utc(d.ts)
        d = d[d.level < max(DEPTH_LEVELS)]
        bid = d[d.side == "bid"]
        ask = d[d.side == "ask"]
        best = pd.DataFrame({
            "bb": bid[bid.level == 0].set_index("ts").price,
            "ba": ask[ask.level == 0].set_index("ts").price,
        })
        rec = {"ts": best.index, "bb": best.bb.values, "ba": best.ba.values}
        frame = pd.DataFrame(rec).set_index("ts")
        for n in DEPTH_LEVELS:
            bn = bid[bid.level < n].groupby("ts")["size"].sum()
            an = ask[ask.level < n].groupby("ts")["size"].sum()
            frame[f"bid_sz_{n}"] = bn
            frame[f"ask_sz_{n}"] = an
        # biggest resting level each side + its distance from mid
        bw = bid.loc[bid.groupby("ts")["size"].idxmax(), ["ts", "price", "size"]].set_index("ts")
        aw = ask.loc[ask.groupby("ts")["size"].idxmax(), ["ts", "price", "size"]].set_index("ts")
        frame["wall_bid_px"], frame["wall_bid_sz"] = bw.price, bw["size"]
        frame["wall_ask_px"], frame["wall_ask_sz"] = aw.price, aw["size"]
        rows.append(frame.reset_index())
        print(f"  book {os.path.basename(f):34s} -> {len(frame):>7,} minutes", flush=True)
    b = pd.concat(rows, ignore_index=True).sort_values("ts").reset_index(drop=True)
    b["mid"] = (b.bb + b.ba) / 2.0
    for n in DEPTH_LEVELS:
        tot = b[f"bid_sz_{n}"] + b[f"ask_sz_{n}"]
        b[f"imb_{n}"] = (b[f"bid_sz_{n}"] - b[f"ask_sz_{n}"]) / tot.replace(0, np.nan)
    b["wall_bid_d"] = b.mid - b.wall_bid_px
    b["wall_ask_d"] = b.wall_ask_px - b.mid
    # persistence: consecutive minutes the same wall price has held (per session day)
    day = b.ts.dt.strftime("%Y-%m-%d")
    for s in ("bid", "ask"):
        same = (b[f"wall_{s}_px"] == b[f"wall_{s}_px"].shift(1)) & (day == day.shift(1))
        grp = (~same).cumsum()
        b[f"wall_{s}_age"] = b.groupby(grp).cumcount()
    return b


def main(out_path: str, use_cache: bool = True) -> None:
    tp = os.path.join(SCRATCH, "of_minute_tape.parquet")
    bp = os.path.join(SCRATCH, "of_minute_book.parquet")
    if use_cache and os.path.exists(tp) and os.path.exists(bp):
        tape, book = pd.read_parquet(tp), pd.read_parquet(bp)
        print(f"cached tape {len(tape):,} minutes / book {len(book):,} minutes", flush=True)
    else:
        print("build minute tape ...", flush=True)
        tape = build_minute_tape()
        print(f"  tape: {len(tape):,} minutes  {tape.ts_minute.min()} -> {tape.ts_minute.max()}")
        print("build minute book ...", flush=True)
        book = build_minute_book()
        print(f"  book: {len(book):,} minutes  {book.ts.min()} -> {book.ts.max()}")
        tape.to_parquet(tp, index=False)
        book.to_parquet(bp, index=False)
        print("  cached -> of_minute_tape.parquet / of_minute_book.parquet")

    fills = pd.read_parquet(SUBSTRATE)
    fills = fills[fills.cvd == 1].reset_index(drop=True)
    fills["fill_ts"] = _utc(fills.fill)
    fills["exit_ts"] = _utc(fills["exit"])
    fills["fill_min"] = fills.fill_ts.dt.floor("min")
    print(f"\nfills: {len(fills)}  {fills.day.min()} -> {fills.day.max()}  "
          f"WR {100*(fills.dollars>0).mean():.1f}%  net ${fills.dollars.sum():,.0f}")

    t = tape.set_index("ts_minute").sort_index()
    bk = book.set_index("ts").sort_index()
    feats = []
    for r in fills.itertuples(index=False):
        fm = r.fill_min
        f = {"day": r.day, "book": r.book, "fill": r.fill_ts, "dir": r.direction,
             "entry": r.entry, "risk": r.risk, "dollars": r.dollars,
             "exit_reason": r.exit_reason, "win": r.dollars > 0}
        # ---- TAPE, strictly BEFORE the fill minute (trap 2)
        pre = t.loc[:fm - pd.Timedelta(minutes=1)]
        d = 1 if r.direction == "long" else -1
        for n in LOOKBACKS:
            w = pre.tail(n)
            # CONTIGUITY (bug found 2026-07-27, on the first build of this file). `tail(n)` returns
            # the last n minutes THAT EXIST, not the last n minutes before the fill. Across the
            # January-2026 footprint gap it happily returned DECEMBER minutes for JANUARY fills:
            # all 69 January fills scored as having valid tape features while the month held only
            # 60 tape minutes. `len(w) == n` cannot catch that — it counts rows, not adjacency.
            # Two conditions now: the window must END next to the fill, and it must not SPAN a
            # gap. A window that fails either is NaN, never a stale number.
            if len(w) == n:
                ends_near = w.index[-1] >= fm - pd.Timedelta(minutes=STALE_TOL_MIN)
                spans_gap = w.index[0] < fm - pd.Timedelta(minutes=GAP_TOL_MULT * n)
                if not ends_near or spans_gap:
                    continue
            if len(w) == n and w.vol.sum() > 0:
                f[f"delta_{n}"] = float(w.delta.sum())
                f[f"delta_norm_{n}"] = float(w.delta.sum() / w.vol.sum())
                f[f"delta_dir_{n}"] = float(d * w.delta.sum() / w.vol.sum())
                f[f"vol_{n}"] = float(w.vol.sum())
                f[f"avgtrade_{n}"] = float(w.vol.sum() / max(w.trd.sum(), 1))
                f[f"pocshare_{n}"] = float(w.poc_share.mean())
                # absorption: volume high, range low -> contracts traded without price moving
                rng = float(w.px_hi.max() - w.px_lo.min())
                f[f"absorp_{n}"] = float(w.vol.sum() / rng) if rng > 0 else np.nan
                # delta divergence: price direction vs delta direction disagree
                dp = float(w.vwp.iloc[-1] - w.vwp.iloc[0])
                f[f"divg_{n}"] = float(np.sign(dp) != np.sign(w.delta.sum())) if dp != 0 else 0.0
        # ---- BOOK, the last snapshot strictly before the fill minute (trap 2)
        pb = bk.loc[:fm - pd.Timedelta(minutes=1)]
        if len(pb):
            b0 = pb.iloc[-1]
            if np.isfinite(b0.mid) and abs(b0.mid - r.entry) <= PX_MISMATCH_PT:   # trap 3
                f["px_mismatch"] = 0
                for n in DEPTH_LEVELS:
                    f[f"imb_{n}"] = float(b0[f"imb_{n}"])
                    f[f"imb_dir_{n}"] = float(d * b0[f"imb_{n}"])
                    f[f"depth_{n}"] = float(b0[f"bid_sz_{n}"] + b0[f"ask_sz_{n}"])
                # wall ahead of / behind the trade, in the trade's own frame
                f["wall_ahead_sz"] = float(b0.wall_ask_sz if d > 0 else b0.wall_bid_sz)
                f["wall_ahead_d"] = float(b0.wall_ask_d if d > 0 else b0.wall_bid_d)
                f["wall_ahead_age"] = float(b0.wall_ask_age if d > 0 else b0.wall_bid_age)
                f["wall_behind_sz"] = float(b0.wall_bid_sz if d > 0 else b0.wall_ask_sz)
                f["wall_behind_d"] = float(b0.wall_bid_d if d > 0 else b0.wall_ask_d)
                f["wall_behind_age"] = float(b0.wall_bid_age if d > 0 else b0.wall_ask_age)
                f["spread"] = float(b0.ba - b0.bb)
            else:
                f["px_mismatch"] = 1
        feats.append(f)
    F = pd.DataFrame(feats)
    F.to_parquet(out_path, index=False)
    n_tape = F.filter(like="delta_norm_").notna().all(axis=1).sum()
    n_book = (F.get("px_mismatch", pd.Series(1, index=F.index)) == 0).sum()
    print(f"\nfeature table -> {out_path}")
    print(f"  {len(F)} rows x {F.shape[1]} cols")
    print(f"  tape features present : {n_tape} / {len(F)}")
    print(f"  book features present : {n_book} / {len(F)}  "
          f"(px_mismatch dropped {int((F.get('px_mismatch',0)==1).sum())})")
    miss = F[F.filter(like="delta_norm_").isna().any(axis=1)]
    if len(miss):
        mm = pd.to_datetime(miss.fill).dt.strftime("%Y-%m").value_counts().sort_index()
        print(f"  months with missing tape: {mm.to_dict()}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(SCRATCH, "london_of_features.parquet"))
    ap.add_argument("--rebuild", action="store_true",
                    help="re-aggregate the 23M-row tape / 1M-row book instead of using the cache")
    a = ap.parse_args()
    main(a.out, use_cache=not a.rebuild)
