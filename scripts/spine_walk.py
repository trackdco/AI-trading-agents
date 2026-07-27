#!/usr/bin/env python3
"""Walk a canon book through the SAFETY SPINE — what the account actually does, live.

ANGUS (29-Jul): *"look at our risk spine as well, because the canon that we shipped to the
agents is built off of that. the maximum r loss in a day, the if we lose one trade we need
lots of conviction for the second, all of the out of fit testing should be done exactly as
so, or its invalid to what we are actually bringing live every night now."*

He is right, and the out-of-fit runs so far did none of it. They reported the canon's own
`pl`, which is a per-trade number with no account behind it. Live, three things sit between
that number and the broker, and every one of them is path-dependent:

  SIZING       risk_$ = base_dollar(available_dd) x min(2.0, conviction), micros = round(
               risk_$ / (stop_pts x $2)) clamped to 40. base_dollar is $200 at the floor,
               +$75 per $1k of available DD past $3k, and — the part that matters on a bad
               run — RAMPS LINEARLY TO ZERO between $1,500 and $100 of available DD. A trade
               that sizes to 0 micros is simply not taken. The account de-risks itself.

  DAY HALT     realized day P&L <= -4R of the day's own base_dollar stops the day. At the
               eval floor that is -$800 ACCOUNT-WIDE, beneath (not instead of) the canon's
               own -$400 per-book Layer 2c stop.

  DD HALT      available_dd <= $100 stops the day outright.

DEFAULT IS --account flat, AND THAT IS DELIBERATE. Angus (29-Jul): *"do not optimise the out
of fit test for a funded account that makes no sense, but you get what i was trying to say."*
Letting base_dollar compound turns the out-of-fit number into a function of the equity curve:
one strong early month inflates every trade after it, and fit-vs-holdout stops measuring the
strategy at all. The first run of this script did exactly that — $285,091 on a $50k account,
clamped at 40 micros on 231 of 422 trades. So `flat` pins base_dollar to the $200 floor
schedule for every trade while keeping the RULES fully active: the -4R day halt, the DD halt,
the 40-micro clamp, and the canon's own Layer 2b/2c escalation upstream. `funded` restores
the DD-scaled sizing for when the question really is "what would the account have done".

DRAWDOWN IS END-OF-DAY, not trailing: `line = min(start_balance, max(prior_line, EOD_balance
- DD))`. It trails EOD gains up and locks at the starting balance once clear; it does NOT
ratchet against an intraday spike. available_dd = equity - line, fixed at each day's start
and growing as the day profits.

None of this can be applied to a book after the fact as a multiplier, because size depends on
the equity curve, which depends on size. Hence a walk, trade by trade, in time order.

    python -m scripts.spine_walk --book output/ny_canon_fit.parquet --london output/london_canon_book.parquet
    python -m scripts.spine_walk --book output/ny_canon_holdout_daycap.parquet --london output/london_canon_book_holdout.parquet
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.canon.gate_evidence import (  # noqa: E402
    CONVICTION_CAP,
    MICRO_CLAMP,
    MNQ_DOLLARS_PER_PT,
    base_dollar,
)
from src.canon.spine import SpineConfig  # noqa: E402

NY = "America/New_York"
START_BALANCE = 50_000.0        # Lucid 50k
ACCOUNT_DD = 2_000.0            # tier DD; line starts at START_BALANCE - ACCOUNT_DD


def load_book(ny_path: str, lon_path: str | None) -> pd.DataFrame:
    """The taken trades of both sessions, chronological, with what the spine needs."""
    parts = []
    for path, sess in ((ny_path, "NY"), (lon_path, "LONDON")):
        if not path:
            continue
        p = ROOT / path
        if not p.exists():
            print(f"  (missing {path} — {sess} excluded)")
            continue
        d = pd.read_parquet(p)
        d = d[d["size"] > 0].copy()
        d["session"] = sess
        parts.append(d[["session", "day", "fill", "direction", "size", "risk", "dollars"]])
    if not parts:
        raise SystemExit("no books found")
    B = pd.concat(parts, ignore_index=True)
    B["fill"] = pd.to_datetime(B.fill, utc=True, format="mixed").dt.tz_convert(NY)
    B["day"] = B.day.astype(str).str[:10]
    return B.sort_values("fill").reset_index(drop=True)


def walk(B: pd.DataFrame, cfg: SpineConfig, account: str = "flat") -> pd.DataFrame:
    """Trade by trade, in time order, with the account state carried forward.

    `account="flat"` sizes every trade off the floor schedule regardless of equity, so the
    result measures the strategy rather than the compounding. The halts still watch the real
    equity curve — a day can still be stopped out, and the DD floor can still be reached.
    """
    flat = account == "flat"
    equity = START_BALANCE
    line = START_BALANCE - ACCOUNT_DD
    rows = []
    for day, g in B.groupby("day", sort=True):
        day_open_equity = equity
        avail_at_open = equity - line
        halt_at = cfg.daily_loss_halt_r * base_dollar(None if flat else avail_at_open)
        day_pl, halted = 0.0, None
        for t in g.itertuples():
            avail = equity - line
            if avail <= cfg.dd_halt_buffer:
                halted = halted or "dd_halt"
            if day_pl <= halt_at:
                halted = halted or "day_loss_halt"
            if halted:
                rows.append(_row(t, day, 0, 0.0, avail, halt_at, halted, equity))
                continue
            base = base_dollar(None if flat else avail)
            risk_d = base * min(CONVICTION_CAP, float(t.size))
            micros = min(MICRO_CLAMP,
                         int(round(risk_d / (float(t.risk) * MNQ_DOLLARS_PER_PT))))
            if micros <= 0:
                # the DD ramp sized this to nothing: not a halt, just a trade not taken
                rows.append(_row(t, day, 0, 0.0, avail, halt_at, "ramped_to_zero", equity))
                continue
            pl = micros * float(t.dollars) / 10.0        # micro = 1/10 of the NQ mini
            equity += pl
            day_pl += pl
            rows.append(_row(t, day, micros, pl, avail, halt_at, None, equity))
        # END-OF-DAY drawdown line: trails EOD gains up, locks at the starting balance
        line = min(START_BALANCE, max(line, equity - ACCOUNT_DD))
        rows[-1] = rows[-1] | {"eod_line": line, "eod_equity": equity,
                               "day_pl": equity - day_open_equity}
    return pd.DataFrame(rows)


def _row(t, day, micros, pl, avail, halt_at, blocked, equity) -> dict:
    return {"day": day, "session": t.session, "fill": t.fill, "conviction": float(t.size),
            "risk_pts": float(t.risk), "dollars_1lot": float(t.dollars),
            "micros": micros, "pl": pl, "available_dd_at_entry": round(avail, 2),
            "day_halt_threshold": round(halt_at, 2), "blocked": blocked,
            "equity_after": round(equity, 2)}


def report(W: pd.DataFrame, tag: str) -> None:
    took = W[W.micros > 0]
    blocked = W[W.blocked.notna()]
    eod = W[W.eod_equity.notna()] if "eod_equity" in W else W.iloc[0:0]
    print("\n" + "=" * 78)
    print(f"SPINE WALK — {tag}")
    print("=" * 78)
    print(f"  candidates {len(W)} | taken {len(took)} | blocked {len(blocked)}"
          + (f" ({blocked.blocked.value_counts().to_dict()})" if len(blocked) else ""))
    print(f"  final equity ${W.equity_after.iloc[-1]:,.0f}  "
          f"(P&L ${W.equity_after.iloc[-1] - START_BALANCE:+,.0f} on ${START_BALANCE:,.0f})")
    if len(eod):
        curve = eod.set_index("day").eod_equity
        dd = (curve.cummax() - curve).max()
        busted = (eod.eod_equity <= eod.eod_line.shift(1).fillna(START_BALANCE - ACCOUNT_DD)).sum()
        print(f"  worst peak-to-trough on the EOD curve ${dd:,.0f}   "
              f"days the line was breached: {busted}")
        print(f"  min available DD reached ${(eod.eod_equity - eod.eod_line).min():,.0f}")
    mo = W.assign(mo=W.day.str[:7]).groupby("mo").pl.sum()
    print(f"  months green {int((mo > 0).sum())}/{len(mo)}")
    print(mo.round(0).to_string())
    if len(took):
        print(f"\n  micros: median {int(took.micros.median())}, "
              f"max {int(took.micros.max())}, clamped at 40 on "
              f"{int((took.micros == MICRO_CLAMP).sum())} trades")
        for s, d in took.groupby("session"):
            print(f"  {s:<7} ${d.pl.sum():+9,.0f}  {len(d):>3} trades  "
                  f"WR {(d.dollars_1lot > 0).mean()*100:.0f}%")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", required=True, help="NY canon book parquet")
    ap.add_argument("--london", default=None, help="London canon book parquet")
    ap.add_argument("--account", choices=["flat", "funded"], default="flat",
                    help="flat pins base risk to the $200 floor (measures the strategy); "
                         "funded lets it scale with available drawdown (measures the account)")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    cfg = SpineConfig()
    print(f"account basis: {a.account}"
          + ("  (base risk pinned to the $200 floor — no compounding)" if a.account == "flat"
             else "  (base risk scales with available drawdown)"))
    print(f"spine: day halt {cfg.daily_loss_halt_r:g}R of base_dollar "
          f"(${cfg.daily_loss_halt_r * base_dollar(START_BALANCE - (START_BALANCE - ACCOUNT_DD)):,.0f} "
          f"at the ${ACCOUNT_DD:,.0f} opening buffer) | dd halt <= ${cfg.dd_halt_buffer:,.0f} "
          f"| clamp {MICRO_CLAMP} micros")
    B = load_book(a.book, a.london)
    print(f"book: {len(B)} taken trades, {B.day.nunique()} days, "
          f"{B.session.value_counts().to_dict()}")
    W = walk(B, cfg, a.account)
    out = ROOT / (a.out or f"output/spine_walk_{Path(a.book).stem}.parquet")
    W.to_parquet(out, index=False)
    report(W, a.tag or Path(a.book).stem)
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
