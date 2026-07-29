#!/usr/bin/env python3
"""Historical Forex Factory calendar scraper — RUN LOCALLY (FF's Cloudflare blocks
cloud/datacenter IPs, so this cannot run in the agent container; same doctrine as the
depth condensers: raw fetching happens on your machine, the small CSV travels).

Fills the 2023-01 .. 2026-01 gap in config/news_calendar.csv so red_folder_today
stops printing 0 for every pre-2026 day. Output matches the existing schema exactly:
    datetime_ET,event,impact

USAGE (from repo root, on Angus/Brake's machine):
    pip install cloudscraper beautifulsoup4 pandas
    python scripts/scrape_ff_calendar.py
    # -> config/news_calendar_hist.csv  (~37 month pages, ~3s apart, a few minutes)
    # then: git add config/news_calendar_hist.csv, commit, push — it's a few hundred KB.

If Cloudflare still fights the scrape: open each month in your browser
(https://www.forexfactory.com/calendar?month=jan.2023 ... dec.2025), save the pages
as HTML into one folder, then:
    python scripts/scrape_ff_calendar.py --html-dir path/to/saved_pages

Parsing strategy: prefer the JSON state blob FF embeds in the page (event `dateline`
is a UTC epoch, which sidesteps rendered-timezone ambiguity entirely); fall back to
parsing the HTML table with the `fftimezone` cookie pinned to America/New_York.
"""
import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

NY = "America/New_York"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]
IMPACT = {"red": "high", "ora": "medium", "yel": "low"}   # gra = holiday -> skipped


def month_range(start: str, end: str):
    cur = pd.Period(start, "M")
    while cur <= pd.Period(end, "M"):
        yield f"{MONTHS[cur.month - 1]}.{cur.year}", str(cur)
        cur += 1


def _impact_of(s: str) -> str | None:
    s = (s or "").lower()
    for k, v in IMPACT.items():
        if f"impact-{k}" in s or v in s:                  # impactClass or impactTitle
            return v
    return None


def parse_json_blob(html: str) -> list[dict]:
    """FF embeds window.calendarComponentStates[N] = {..."days":[{"events":[...]}]}."""
    rows = []
    for m in re.finditer(r"calendarComponentStates\[\d+\]\s*=\s*", html):
        i = html.find("{", m.end())
        if i < 0:
            continue
        depth, j = 0, i
        in_str, esc = False, False
        while j < len(html):                              # brace-match the JS object
            c = html[j]
            if in_str:
                esc = (c == "\\" and not esc)
                if c == '"' and not esc:
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        try:
            state = json.loads(html[i:j + 1])
        except json.JSONDecodeError:
            continue
        for day in state.get("days", []):
            for ev in day.get("events", []):
                if str(ev.get("currency", "")).upper() != "USD":
                    continue
                imp = _impact_of(str(ev.get("impactClass", ""))
                                 + " " + str(ev.get("impactTitle", "")))
                dl = ev.get("dateline")
                if not imp or not dl:
                    continue
                ts = pd.Timestamp(int(dl), unit="s", tz="UTC").tz_convert(NY)
                rows.append(dict(datetime_ET=ts.strftime("%Y-%m-%d %H:%M"),
                                 event=str(ev.get("name", "")).strip(), impact=imp))
    return rows


def parse_html_table(html: str, year_hint: int) -> list[dict]:
    """Fallback: the rendered calendar table (requires fftimezone=America/New_York)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    rows, cur_date, cur_time = [], None, None
    for tr in soup.select("tr.calendar__row"):
        dcell = tr.select_one("td.calendar__date")
        if dcell and dcell.get_text(strip=True):
            txt = re.sub(r"^[A-Za-z]{3}", "", dcell.get_text(" ", strip=True)).strip()
            try:                                          # e.g. "Jan 3"
                cur_date = datetime.strptime(f"{txt} {year_hint}", "%b %d %Y").date()
            except ValueError:
                pass
        tcell = tr.select_one("td.calendar__time")
        ttxt = tcell.get_text(strip=True) if tcell else ""
        if ttxt:
            cur_time = ttxt
        cur = tr.select_one("td.calendar__currency")
        if not cur or cur.get_text(strip=True).upper() != "USD" or cur_date is None:
            continue
        icell = tr.select_one("td.calendar__impact span")
        imp = _impact_of(" ".join(icell.get("class", [])) if icell else "")
        name = tr.select_one("span.calendar__event-title")
        if not imp or not name:
            continue
        tm = "00:00"
        m = re.match(r"(\d{1,2}):(\d{2})(am|pm)", (cur_time or "").lower())
        if m:
            h = int(m.group(1)) % 12 + (12 if m.group(3) == "pm" else 0)
            tm = f"{h:02d}:{m.group(2)}"
        rows.append(dict(datetime_ET=f"{cur_date} {tm}",
                         event=name.get_text(strip=True), impact=imp))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2023-01")
    ap.add_argument("--end", default="2026-01")
    ap.add_argument("--out", default="config/news_calendar_hist.csv")
    ap.add_argument("--sleep", type=float, default=3.0)
    ap.add_argument("--html-dir", default=None,
                    help="parse browser-saved month pages instead of fetching")
    a = ap.parse_args()

    pages = []
    if a.html_dir:
        for p in sorted(Path(a.html_dir).glob("*.htm*")):
            m = re.search(r"(19|20)\d{2}", p.name)
            pages.append((p.read_text(errors="ignore"), int(m.group()) if m else 2024))
        print(f"parsing {len(pages)} saved pages from {a.html_dir}")
    else:
        import cloudscraper
        sc = cloudscraper.create_scraper()
        sc.cookies.set("fftimezone", "America%2FNew_York", domain=".forexfactory.com")
        for slug, ym in month_range(a.start, a.end):
            url = f"https://www.forexfactory.com/calendar?month={slug}"
            r = sc.get(url, timeout=30)
            r.raise_for_status()
            pages.append((r.text, int(ym[:4])))
            print(f"  fetched {ym} ({len(r.text) // 1024} KB)")
            time.sleep(a.sleep)

    rows = []
    for html, yr in pages:
        got = parse_json_blob(html)
        if not got:
            got = parse_html_table(html, yr)
        rows.extend(got)
    if not rows:
        raise SystemExit("no events parsed — send me one saved month page and I'll "
                         "adapt the parser to whatever FF is serving you")
    df = pd.DataFrame(rows).drop_duplicates(["datetime_ET", "event"]) \
        .sort_values("datetime_ET").reset_index(drop=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as f:
        f.write("# Historical FF calendar (scripts/scrape_ff_calendar.py) — "
                "schema matches config/news_calendar.csv\n")
        df.to_csv(f, index=False)
    print(f"\nwrote {a.out}: {len(df)} events")
    df["y"] = df.datetime_ET.str[:4]
    print(df.groupby(["y", "impact"]).size().unstack(fill_value=0).to_string())
    hi = df[df.impact == "high"]
    print(f"\nsanity: high-impact days/year ≈ "
          f"{hi.datetime_ET.str[:10].nunique() / max(df.y.nunique(), 1):.0f} "
          f"(expect roughly 60-100)")


if __name__ == "__main__":
    main()
