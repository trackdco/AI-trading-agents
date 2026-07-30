#!/usr/bin/env python3
"""CLOSE-AND-REVERSE — the canon's execution semantics. ANGUS ruling 2026-07-30.

  "when we're in a valid long, and a short position fires, close it right then and there"

At a netting broker one account holds one net position. Every trade keeps its own full
bracket; an OPPOSING canon fill is an ADDITIONAL exit: the moment trade B fills against an
open trade A, the same limit fill flattens A (at B's entry price — maker fill, no slip) and
opens B as its own trade. An opposing signal that never fills changes nothing. Same-direction
overlaps (sibling/scale-in fills) are untouched — they stack, they do not contradict.

Priced before ruling (holdout ledger look #3, declared): shipped $90,015/$56,409 ->
close-and-reverse $97,327/$59,407 (lucid), holdout maxDD $1,503 -> $1,429. The opposing fill
is the book's strongest exit signal; this harvests it and eliminates simultaneous
opposite-direction positions entirely.

Truncation math per flipped trade A (engine cost conventions): the V8 partial leg stands if
its price traded before the flip minute (recovered by inverting the book's own dollars,
never re-resolved); the remaining fraction closes at B's entry; commission charged once as
always; no slip on the flip close (it IS B's limit fill).

Writes output/aikido_cr_{span}.parquet — the overlay funded_book.load_book applies as LAW.
Sequential: a flipped trade is closed and cannot flip anything later; the flipping trade
lives with its ORIGINAL exit until (possibly) flipped itself.

    python -m scripts.apply_close_reverse
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import funded_book as fb  # noqa: E402
from scripts.capture_replay import (  # noqa: E402
    COMMISSION, PARTIAL_PCT, day_path, implied_partial, load_bars_ny, load_trades, sgn)


def build_span(span: str, bars) -> pd.DataFrame:
    T = load_trades(span)               # canon book rows with parsed NY stamps
    keys = [(t["ts"], t["direction"]) for t in T]
    assert len(keys) == len(set(keys)), f"{span}: (ts, direction) not unique in the book"

    rows = []
    by_day: dict[str, list[dict]] = {}
    for t in T:
        by_day.setdefault(t["day"], []).append(t)
    for day in sorted(by_day):
        todays = sorted(by_day[day], key=lambda x: x["fill"])
        open_list: list[dict] = []
        for b in todays:
            open_list = [a for a in open_list if a["exit"] > b["fill"]]
            for a in [x for x in open_list if x["direction"] != b["direction"]]:
                s = sgn(a["direction"])
                pp = implied_partial(a)
                legs = []
                if pp is not None:
                    seg = day_path(a, bars).loc[:b["fill"]]
                    if len(seg) and bool(((seg.low - 1e-9 <= pp)
                                          & (pp <= seg.high + 1e-9)).any()):
                        legs.append((PARTIAL_PCT, pp))
                legs.append((1.0 - sum(f for f, _ in legs), b["entry"]))
                pts = sum(f * s * (px - a["entry"]) for f, px in legs)
                rows.append({
                    "ts": a["ts"], "direction": a["direction"],
                    "cr_exit_ts": _fill_ts_str(b),
                    "cr_exit_price": float(b["entry"]),
                    "cr_dollars_1lot": round(pts * 20.0 * a["size"] - COMMISSION, 2),
                    "flipped_by_ts": b["ts"]})
            open_list = [a for a in open_list if a["direction"] == b["direction"]]
            open_list.append(b)
    return pd.DataFrame(rows)


def _fill_ts_str(t: dict) -> str:
    return t["fill"].isoformat()


def main() -> None:
    bars = load_bars_ny()
    for span in ("fit", "holdout"):
        O = build_span(span, bars)
        out = ROOT / f"output/aikido_cr_{span}.parquet"
        O.to_parquet(out, index=False)
        print(f"{span}: {len(O)} trades flipped -> {out.relative_to(ROOT)}")
        for profile in ("lucid", "scaled600"):
            V = fb.load_book(span)          # overlay applied if load_book already patched
            B = fb.run(V, profile)
            D = B.groupby("day").pl.sum()
            mo = B.groupby("month").pl.sum()
            cum = D.cumsum()
            bal, line, mb = fb.START, fb.START - fb.TRAIL, 1e9
            for p in D:
                bal += p
                mb = min(mb, bal - line)
                line = min(fb.START, max(line, bal - fb.TRAIL))
            print(f"  {profile}: net ${B.pl.sum():+,.0f} | worst day ${D.min():+,.0f} | "
                  f"maxDD ${(cum.cummax() - cum).max():,.0f} | months green "
                  f"{(mo > 0).sum()}/{len(mo)} | min buffer ${mb:,.0f}")


if __name__ == "__main__":
    main()
