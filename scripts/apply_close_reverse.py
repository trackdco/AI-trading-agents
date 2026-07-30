#!/usr/bin/env python3
"""EXECUTION SEMANTICS — the canon's two rulings (ANGUS 2026-07-30), built as ONE overlay.

1. TWO SESSIONS — pre flat by the open: "i want all pre market trades to be flattened by
   market open. 2 different sessions basically." Every pre-session position is
   market-flattened on the first bar at/after 09:30 (engine knob `pre_flatten_at`, the
   REAL engine re-simulates every pre trigger — no re-implementation).
2. CLOSE-AND-REVERSE: "when we're in a valid long, and a short position fires, close it
   right then and there." An OPPOSING canon fill flattens the open trade at that fill
   (maker price, no slip) and reverses. An opposing signal that never fills changes
   nothing; same-direction adds stack untouched.

Order matters and is sequential per day: pre-flatten first reshapes exits, then the CR pass
runs over the spliced book (a pre trade flattened at 09:30 cannot flip a gold trade after
it). Priced before ruling (holdout ledger looks #3 and #4, both declared):
shipped $90,015/$56,409 -> CR $97,327/$59,407 -> CR+two-session $94,695/$56,756 (lucid).

Writes output/aikido_cr_{span}.parquet — every trade whose exit/dollars differ from the
engine's V8 walk, with final (post-both-rules) values. funded_book.load_book applies it as
LAW. Truncation math per flipped trade: the V8 partial leg stands if its price traded
before the flip minute (inverted from the book's own dollars); the rest closes at the
flipping trade's entry; commission once; no slip on the flip close (it IS the limit fill).

    python -m scripts.apply_close_reverse
"""
from __future__ import annotations

import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.build_l2_outcomes as m  # noqa: E402
from scripts import funded_book as fb  # noqa: E402
from scripts.capture_replay import (  # noqa: E402
    COMMISSION, PARTIAL_PCT, day_path, implied_partial, load_bars_ny, load_trades, sgn)

PRE_FLATTEN = dtime(9, 30)


def resim_pre(span: str) -> pd.DataFrame:
    """Every pre-session canon trigger through the REAL engine with the 09:30 flatten."""
    T = load_trades(span)
    pre_keys = {(t["ts"], t["direction"]) for t in T if t["sess"] == "pre"}
    C = pd.read_parquet(ROOT / f"output/l0_triggers_{span}.parquet")
    C = C[[(t, d) in pre_keys for t, d in zip(C.ts, C.direction)]].drop_duplicates(
        ["ts", "direction"])
    base_cfg = m.l2_cfg
    m.l2_cfg = lambda t_cancel=100000.0: base_cfg(t_cancel).model_copy(
        update={"pre_flatten_at": PRE_FLATTEN})
    out = m.run(C.copy(), procs=4)
    m.l2_cfg = base_cfg
    oc = out[out.status == "outcome"].drop_duplicates(["ts", "direction"])
    assert len(oc) == len(pre_keys), f"{span}: pre re-sim {len(oc)} != {len(pre_keys)}"
    return oc.set_index(["ts", "direction"])


def build_span(span: str, bars) -> pd.DataFrame:
    T = load_trades(span)               # V8-anchored book rows, parsed NY stamps
    keys = [(t["ts"], t["direction"]) for t in T]
    assert len(keys) == len(set(keys)), f"{span}: (ts, direction) not unique in the book"
    orig = {(t["ts"], t["direction"]): (t["dollars"], t["exit"]) for t in T}

    P = resim_pre(span)
    for t in T:                         # splice rule 1
        k = (t["ts"], t["direction"])
        if k in P.index:
            r = P.loc[k]
            t["dollars"] = float(r.dollars_1lot)
            t["exit_price"] = float(r.exit_price)
            t["exit_reason"] = str(r.exit_reason)
            t["exit"] = pd.to_datetime(r.exit_ts).tz_convert("America/New_York")

    by_day: dict[str, list[dict]] = {}
    for t in T:
        by_day.setdefault(t["day"], []).append(t)
    flips = 0
    for day in sorted(by_day):          # rule 2, sequential per day
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
                a["dollars"] = round(pts * 20.0 * a["size"] - COMMISSION, 2)
                a["exit_price"] = float(b["entry"])
                a["exit_reason"] = "flip"
                a["exit"] = b["fill"]
                flips += 1
            open_list = [a for a in open_list if a["direction"] == b["direction"]]
            open_list.append(b)

    rows = [{"ts": t["ts"], "direction": t["direction"],
             "cr_exit_ts": t["exit"].isoformat(),
             "cr_exit_price": float(t["exit_price"]),
             "cr_dollars_1lot": float(t["dollars"]),
             "cr_exit_reason": t["exit_reason"]}
            for t in T
            if (t["dollars"], t["exit"]) != orig[(t["ts"], t["direction"])]]
    print(f"{span}: {flips} flips | {len(rows)} trades differ from the V8 walk")
    return pd.DataFrame(rows)


def main() -> None:
    bars = load_bars_ny()
    for span in ("fit", "holdout"):
        O = build_span(span, bars)
        out = ROOT / f"output/aikido_cr_{span}.parquet"
        O.to_parquet(out, index=False)
        print(f"  wrote {out.relative_to(ROOT)}")
        for profile in ("lucid", "scaled600"):
            B = fb.run(fb.load_book(span), profile)
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
