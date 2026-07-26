#!/usr/bin/env python3
"""THE NEWS SENTINEL — daily forecast subagent (ANGUS 2026-07-26).

  "we want to build a subagent that looks at news forecasting so it knows when to not
   trade premarket before 8:30... its a simple look at news, okay theres red folder, we
   arent trading until after 8:30."

OBSERVE-ONLY, per docs/RULING-mechanical-only.md and the §8 design split: this agent looks
at TODAY'S board, writes a frozen dated snapshot, and reports changes. It never touches a
trade decision — the adopted mechanical gate (src/canon/news_gate.py) does the acting, by
table lookup on the snapshot this writes.

Runs PRE-SESSION on a machine Forex Factory allows (Cloudflare blocks datacenter IPs — this
container cannot run it; Angus/Brake's machine via cron, or test once from the VPS):

    python scripts/news_daily_agent.py            # fetch this week's board
    python scripts/news_daily_agent.py --html saved_page.html   # Cloudflare fallback

Then transport = git: commit data/reference/news_daily/news_YYYY-MM-DD.csv, push; the box
pulls before the session. Exit code 0 = fresh snapshot written; anything else = the box has
NO SNAPSHOT for today and the gate FAILS CLOSED (block all pre-09:30 entries — a missing
board is a red-folder day, never "no news").
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.scrape_ff_calendar import parse_html_table, parse_json_blob   # noqa: E402

NY = ZoneInfo("America/New_York")
OUT = Path("data/reference/news_daily")
URL = "https://www.forexfactory.com/calendar?week=this"


def fetch_html() -> str:
    import cloudscraper
    s = cloudscraper.create_scraper()
    s.cookies.set("fftimezone", "America%2FNew_York", domain=".forexfactory.com")
    r = s.get(URL, timeout=30)
    r.raise_for_status()
    return r.text


def main() -> int:
    today = datetime.now(NY).date()
    html = (Path(sys.argv[sys.argv.index("--html") + 1]).read_text()
            if "--html" in sys.argv else fetch_html())
    rows = parse_json_blob(html) or parse_html_table(html, today.year)
    if not rows:
        print("SENTINEL FAIL: page parsed to zero events — board unknown, gate must fail closed")
        return 2
    d = pd.DataFrame(rows)
    d["datetime_ET"] = pd.to_datetime(d["datetime_ET"])
    d = d.sort_values("datetime_ET")

    OUT.mkdir(parents=True, exist_ok=True)
    snap = OUT / f"news_{today}.csv"
    prev = sorted(OUT.glob("news_*.csv"))
    prev_path = prev[-1] if prev and prev[-1] != snap else None
    d.to_csv(snap, index=False)

    # today's pre-open red folders — the one-line answer the desk cares about
    t = d[(d["datetime_ET"].dt.date == today) & (d["impact"] == "high")
          & (d["datetime_ET"].dt.time < datetime.strptime("09:30", "%H:%M").time())]
    if len(t):
        first = t["datetime_ET"].min()
        print(f"SENTINEL: RED FOLDER PRE-OPEN today — no premarket entries before "
              f"{first.strftime('%H:%M')} ET ({', '.join(t.event.head(4))})")
    else:
        print("SENTINEL: no pre-open red folder today — premarket clear")

    # diff vs the previous snapshot: moved times / new events / impact changes
    if prev_path is not None:
        p = pd.read_csv(prev_path, parse_dates=["datetime_ET"])
        span = d[d["datetime_ET"].dt.date >= today]
        pspan = p[p["datetime_ET"].dt.date >= today]
        key = lambda x: x["event"].str.strip() + "|" + x["datetime_ET"].dt.date.astype(str)
        new = span[~key(span).isin(key(pspan))]
        for _, e in new.iterrows():
            print(f"SENTINEL CHANGE: NEW event {e['event']} @ {e['datetime_ET']} [{e['impact']}]")
        merged = span.merge(pspan, on="event", suffixes=("", "_prev"))
        moved = merged[merged["datetime_ET"] != merged["datetime_ET_prev"]]
        for _, e in moved.drop_duplicates("event").iterrows():
            print(f"SENTINEL CHANGE: {e['event']} moved {e['datetime_ET_prev']} -> {e['datetime_ET']}")
    print(f"wrote {snap} ({len(d)} events)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
