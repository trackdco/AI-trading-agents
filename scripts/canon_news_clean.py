#!/usr/bin/env python3
"""THE NEW CANON STANDARD — leakage-clean C **plus** the pre-open news blackout.

ANGUS RULING 2026-07-26: *"do push the new canon standard of not trading before those high
impact news days like i said to you."*

Two corrections stacked, in the order they were ruled:

  1. `conf_PM` -> `pm_sofar_conf` in the pre-window C check (the look-ahead fix, already
     adopted as the arming reference: +$52,522.81 / 404).
  2. **No NY entry that would be open going into a pre-open high-impact release**, where
     "high-impact" is any event NAME the calendar tags high anywhere (`src/canon/news_gate.py`).

The veto is applied INSIDE `build_canon` as `size -> 0`, after the score ladder and before
the Layer-2b nth escalation. That ordering is the live-faithful one, and it is not cosmetic:

  * the signal still fires, so the Layer-3 governor's rolling win-rate state is untouched —
    a vetoed candidate is a candidate the detector saw, exactly as it will live;
  * the order is never placed, so the vetoed trade does NOT consume the day's first-trade
    slot. The next trade that day is genuinely the 1st taken, not the 2nd.

Writes `output/baseline_book_news.parquet` and `output/canon_news_report.md`.

    python -m scripts.canon_news_clean
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.baseline_dollar_risk import size_book          # noqa: E402
from scripts.canon_mechanical import build_canon            # noqa: E402
from src.canon.news_gate import NewsGate                    # noqa: E402

CLEAN_ANCHOR = 52_522.81        # the leakage-clean arming reference this builds on


def _sized(ny, lon) -> pd.DataFrame:
    b = pd.concat([size_book(ny, "NY"), size_book(lon, "LONDON")], ignore_index=True)
    return b.sort_values("fill").reset_index(drop=True)


def main() -> None:
    T = pd.read_parquet("output/trade_matrix.parquet")
    lon = pd.read_parquet("output/london_canon_book.parquet")
    gate = NewsGate.load()

    # trade_matrix is NY-only by construction (win_ in {pre, gold}); London carries no
    # pre-09:30 US release inside 03:00-08:00 ET, and the calendar has no UK/EU coverage
    # at all — see docs/FINDING-canon-has-no-news-blackout.md §6.
    T_clean = T.copy()
    T_clean["conf_PM"] = T_clean["pm_sofar_conf"]           # correction 1: the look-ahead fix
    clean = _sized(build_canon(T_clean), lon)               # arming reference today
    news = _sized(build_canon(T_clean, news_gate=gate), lon)   # + correction 2

    def stats(b):
        d = b.groupby("day").pl.sum()
        mo = b.groupby(pd.to_datetime(b.day).dt.to_period("M")).pl.sum()
        c = d.cumsum()
        return dict(pl=b.pl.sum(), n=len(b),
                    ny=b[b.session == "NY"].pl.sum(), n_ny=int((b.session == "NY").sum()),
                    lo=b[b.session == "LONDON"].pl.sum(), n_lo=int((b.session == "LONDON").sum()),
                    win=(b.pl > 0).mean() * 100, mo_grn=int((mo > 0).sum()), mo_n=len(mo),
                    worst_mo=mo.min(), worst_day=d.min(),
                    mdd=float((c.cummax() - c).max()))

    a, z = stats(clean), stats(news)
    lines = [
        "# The new canon standard — leakage-clean C + pre-open news blackout", "",
        "ANGUS RULING 2026-07-26. Correction 1 (`conf_PM` -> `pm_sofar_conf`) was already the",
        f"arming reference at +${CLEAN_ANCHOR:,.2f}. Correction 2 is the news blackout.", "",
        "| metric | clean only (today's reference) | **+ news blackout** | delta |",
        "|---|---|---|---|",
        f"| **total P&L** | ${a['pl']:+,.2f} | **${z['pl']:+,.2f}** | ${z['pl']-a['pl']:+,.2f} |",
        f"| trades | {a['n']} | **{z['n']}** | {z['n']-a['n']:+d} |",
        f"| win rate | {a['win']:.1f}% | {z['win']:.1f}% | {z['win']-a['win']:+.1f}pp |",
        f"| NY | ${a['ny']:+,.0f} / {a['n_ny']} | ${z['ny']:+,.0f} / {z['n_ny']} | "
        f"${z['ny']-a['ny']:+,.0f} / {z['n_ny']-a['n_ny']:+d} |",
        f"| London | ${a['lo']:+,.0f} / {a['n_lo']} | ${z['lo']:+,.0f} / {z['n_lo']} | "
        f"${z['lo']-a['lo']:+,.0f} / {z['n_lo']-a['n_lo']:+d} |",
        f"| months green | {a['mo_grn']}/{a['mo_n']} | {z['mo_grn']}/{z['mo_n']} | — |",
        f"| worst month | ${a['worst_mo']:+,.0f} | ${z['worst_mo']:+,.0f} | — |",
        f"| worst day | ${a['worst_day']:+,.0f} | ${z['worst_day']:+,.0f} | — |",
        f"| max drawdown | ${a['mdd']:,.0f} | ${z['mdd']:,.0f} | — |", "",
        f"Blackout days on the calendar: **{len(gate.releases)}**. "
        f"Promoted-high event names: **{len(gate.promoted)}**. "
        f"Calendar runs to **{gate.stale_after.date()}** — stale past that, and a stale "
        "calendar must FAIL CLOSED (`NewsGate.is_stale`).", "",
        "London is unchanged by construction: the calendar carries no release inside "
        "03:00-08:00 ET (and no UK/EU coverage at all — a known gap).",
    ]
    Path("output/canon_news_report.md").write_text("\n".join(lines) + "\n")
    news.to_parquet("output/baseline_book_news.parquet")
    print("\n".join(lines))

    ck = set(zip(clean.day.astype(str), clean.fill.astype(str)))
    zk = set(zip(news.day.astype(str), news.fill.astype(str)))
    print(f"\ndropped {len(ck-zk)} trades, {len(zk-ck)} newly appear "
          f"(the nth-escalation slot freed by a vetoed trade)")
    print("wrote output/canon_news_report.md and output/baseline_book_news.parquet")


if __name__ == "__main__":
    main()
