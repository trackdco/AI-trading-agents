#!/usr/bin/env python3
"""Extract config/news_calendar.csv rows from Forex Factory calendar PDF exports.

WHAT / WHY
----------
Angus's Forex Factory calendar exports come as PDFs whose timestamps are in his
local zone (Australia/Melbourne, GMT+10) and whose impact rating lives only in the
colour of a folder icon (not in the text layer). This script turns those PDFs into
the repo's `datetime_ET,event,impact` schema:

  * event names + times + Melbourne dates: read from the PDF text layer
    (`pdftotext -layout` for date blocks, `pdftotext -bbox` for per-row geometry);
  * impact colour: read from the rendered page pixels (`pdftoppm`), red -> "high",
    orange -> "medium", grey -> "holiday";
  * every timestamp is converted Melbourne -> America/New_York with a DST-aware tz
    library (zoneinfo). Never fixed offsets — the exports span the Apr 5 AU DST change.

Date-block boundaries are the one genuinely hard part (Forex Factory centres each
date label inside its block). Two independent estimates are computed — a text-block
pass and a geometry "largest-gap" pass — and reconciled; recurring releases with
fixed weekdays (NFP=Fri, Claims=Thu, ...) are weekday-validated to break ties, then
two domain-fact corrections are applied (known US market holidays; AHE / Unemployment
Rate travel with the payrolls print). See context/progress-tracker.md for the flags
that still want an Angus spot-check.

REQUIREMENTS (dev-only; NOT engine runtime deps)
------------------------------------------------
  * poppler-utils on PATH (`pdftotext`, `pdftoppm`)
  * numpy (approved), Pillow (dev-only, for reading icon pixel colours)

USAGE
-----
  python scripts/extract_news_calendar.py OUT.csv PDF1 [PDF2 ...]

Then splice the printed rows into config/news_calendar.csv (Feb seed is kept as-is).
Re-run whenever Angus provides fresh/extended exports.
"""
import colorsys
import html
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
import numpy as np
from PIL import Image

MEL = ZoneInfo("Australia/Melbourne")
NY = ZoneInfo("America/New_York")
MON = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
MONALT = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
WD = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
DPI = 200
SCALE = DPI / 72.0
WORD_RE = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')
TIME_RE = re.compile(r'(\d{1,2}:\d{2}(?:am|pm))')
TIME_ONLY = re.compile(r'^\d{1,2}:\d{2}(am|pm)$')
DATE_RE = re.compile(rf'\b({MONALT})\s+(\d{{1,2}})\b')
DROP = re.compile(r'forex factory|changes|please|disclaimer|fair economy', re.I)
VALTOK = re.compile(r'\s+[-<>]?\d[\d.,]*[KMB%]?$')  # trailing Actual-value leaked into name
# Recurring releases whose ET weekday is fixed — used to break text/geom date ties.
FIXED = {"Non-Farm Employment Change": "Fri", "Unemployment Claims": "Thu",
         "Unemployment Rate": "Fri", "Average Hourly Earnings m/m": "Fri"}
# US equity/bank market holidays are known facts; drop any spurious "Bank Holiday".
US_HOLIDAYS = {"2026-05-25", "2026-06-19", "2026-07-03"}


def clean_name(n: str) -> str:
    while True:
        n2 = VALTOK.sub("", n).strip()
        if n2 == n:
            return n
        n = n2


def classify(img, yc, x0=150, x1=212) -> str:
    """Median hue of the impact folder icon on this row -> impact bucket."""
    py = int(yc * SCALE)
    px0, px1 = int(x0 * SCALE), int(x1 * SCALE)
    strip = img[max(0, py - 6):min(img.shape[0], py + 7), px0:px1, :].reshape(-1, 3).astype(float) / 255.0
    hues = []
    for r, g, b in strip:
        hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
        if ss > 0.35 and vv > 0.4:
            hues.append(hh * 360)
    if not hues:
        return "holiday"  # grey / no saturated colour
    hue = float(np.median(hues))
    return "high" if (hue <= 18 or hue >= 345) else "medium" if hue <= 42 else "medium"


def _words(pdf, page):
    out = subprocess.run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page), str(pdf), "-"],
                         capture_output=True, text=True).stdout
    return [dict(x0=float(a), y0=float(b), x1=float(c), y1=float(d), t=html.unescape(t))
            for a, b, c, d, t in WORD_RE.findall(out)]


def _render(pdf, page):
    base = f"/tmp/_nc_{Path(pdf).stem}_{page}"
    subprocess.run(["pdftoppm", "-png", "-r", str(DPI), "-f", str(page), "-l", str(page), str(pdf), base], check=True)
    png = list(Path("/tmp").glob(f"_nc_{Path(pdf).stem}_{page}-*.png"))[0]
    return np.asarray(Image.open(png).convert("RGB"))


def geom_rows(pdf, npages):
    """Per-row (event, colour, time) + a geometry date estimate (largest-gap blocks)."""
    seq = []
    last = None
    for page in range(1, npages + 1):
        ws = _words(pdf, page)
        img = _render(pdf, page)
        # date labels start with a weekday token in the left column
        left = sorted([w for w in ws if w["x1"] < 62], key=lambda w: w["y0"])
        labels = []
        for w in left:
            if w["t"] in WD:
                labels.append([w])
            elif labels:
                labels[-1].append(w)
        anch = []
        for lb in labels:
            mo = dy = None
            for w in lb:
                if w["t"] in MON:
                    mo = MON[w["t"]]
                elif w["t"].isdigit():
                    dy = int(w["t"])
            if mo and dy:
                ys = [w["y0"] for w in lb] + [w["y1"] for w in lb]
                anch.append(dict(y=sum(ys) / len(ys), mon=mo, day=dy))
        anch.sort(key=lambda a: a["y"])
        ws.sort(key=lambda w: (round(w["y0"], 0), w["x0"]))
        rws = []
        for w in ws:
            if rws and abs(w["y0"] - rws[-1][0]) <= 3:
                rws[-1][1].append(w)
            else:
                rws.append([w["y0"], [w]])
        ev = []
        for _, rw in rws:
            e = [w for w in rw if 200 <= w["x0"] < 425]
            if not e or not any(w["t"] in ("USD", "All") for w in rw):
                continue
            nm = clean_name(" ".join(w["t"] for w in sorted(e, key=lambda z: z["x0"])).strip())
            if DROP.search(nm):
                continue
            yc = (min(w["y0"] for w in rw) + max(w["y1"] for w in rw)) / 2
            tc = " ".join(w["t"] for w in rw if 64 <= w["x0"] < 120).strip()
            ev.append(dict(yc=yc, name=nm, tc=tc, imp=classify(img, yc)))
        ev.sort(key=lambda r: r["yc"])
        # block boundary between two date labels = the largest event-row gap between them
        bounds = []
        for k in range(len(anch) - 1):
            lo, hi = anch[k]["y"], anch[k + 1]["y"]
            pts = [lo] + [r["yc"] for r in ev if lo < r["yc"] < hi] + [hi]
            gaps = [(pts[i + 1] - pts[i], (pts[i + 1] + pts[i]) / 2) for i in range(len(pts) - 1)]
            bounds.append(max(gaps)[1])
        for r in ev:
            kk = sum(1 for b in bounds if r["yc"] > b)
            a = anch[min(kk, len(anch) - 1)]
            key = r["tc"].replace(" ", "")
            if TIME_ONLY.match(key):
                last = key
                tv = key
            elif r["tc"] in ("All Day", "Tentative") or "Data" in r["tc"]:
                tv = None
            else:
                tv = last
            seq.append(dict(mon=a["mon"], day=a["day"], tval=tv, event=r["name"], impact=r["imp"]))
    return seq


def text_rows(pdf):
    """Independent date estimate from the reflowed text (blank-line time-group blocks)."""
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    out = []
    last = None
    mon = day = None
    for blk in re.split(r'\n\s*\n', txt):
        lines = [ln for ln in blk.split("\n") if ln.strip()]
        for line in lines:
            m = DATE_RE.search(line.split("USD")[0])
            if m:
                mon, day = MON[m.group(1)], int(m.group(2))
                break
        for line in lines:
            ln = line.replace("All Day", "AllDay")
            c = ln.find("USD")
            if c < 0:
                ma = re.search(r'\bAll\b', ln)
                if not ma:
                    continue
                c = ma.start()
            pre, post = ln[:c], ln[c + 3:]
            tm = TIME_RE.search(pre)
            tv = tm.group(1) if tm else (None if ("AllDay" in pre or "Tentative" in pre) else last)
            if tm:
                last = tm.group(1)
            nm = clean_name(re.split(r"\s{2,}", post.strip())[0].strip())
            if not nm or DROP.search(nm):
                continue
            out.append(dict(mon=mon, day=day, tval=tv, event=nm))
    return out


def wd(mon, day):
    return datetime(2026, mon, day).strftime("%a")


def extract(pdfs):
    records = []
    for pdf, npages in pdfs:
        G, T = geom_rows(pdf, npages), text_rows(pdf)
        if len(G) != len(T):
            print(f"warn {Path(pdf).name}: geom {len(G)} text {len(T)} (aligning to min)", file=sys.stderr)
        for i in range(min(len(G), len(T))):
            g, t = G[i], T[i]
            if (g["mon"], g["day"]) == (t["mon"], t["day"]):
                mon, day = g["mon"], g["day"]
            else:  # disagreement: weekday-validate if it's a fixed-weekday release, else geom
                exp = FIXED.get(g["event"])
                if exp and wd(t["mon"], t["day"]) == exp and wd(g["mon"], g["day"]) != exp:
                    mon, day = t["mon"], t["day"]
                else:
                    mon, day = g["mon"], g["day"]
            records.append(dict(mon=mon, day=day, tval=g["tval"] or t["tval"],
                                event=g["event"], impact=g["impact"]))

    rows = []
    for r in records:
        if r["tval"]:
            hh, mm, ap = re.match(r'(\d{1,2}):(\d{2})(am|pm)', r["tval"]).groups()
            h = int(hh) % 12 + (12 if ap == "pm" else 0)
            dt = datetime(2026, r["mon"], r["day"], h, int(mm), tzinfo=MEL).astimezone(NY)
        else:
            dt = datetime(2026, r["mon"], r["day"], 0, 0, tzinfo=NY)
        rows.append((dt, r["event"], r["impact"]))
    rows.sort(key=lambda x: x[0])

    # dedup exact (datetime, event) — merges the shared boundary day between two exports
    seen, kept = set(), []
    for dt, ev, imp in rows:
        k = (dt.strftime("%Y-%m-%d %H:%M"), ev)
        if k in seen:
            continue
        seen.add(k)
        kept.append((dt, ev, imp))
    # domain-fact corrections
    kept = [(dt, ev, imp) for dt, ev, imp in kept
            if not (ev == "Bank Holiday" and dt.strftime("%Y-%m-%d") not in US_HOLIDAYS)]
    nfp = [dt for dt, ev, _ in kept if ev == "Non-Farm Employment Change"]
    out = []
    for dt, ev, imp in kept:
        if ev in ("Average Hourly Earnings m/m", "Unemployment Rate"):
            near = [n for n in nfp if abs((n - dt).total_seconds()) <= 2 * 86400]
            if near:
                n = min(near, key=lambda x: abs((x - dt).total_seconds()))
                dt = dt.replace(year=n.year, month=n.month, day=n.day)
        out.append((dt, ev, imp))
    out.sort(key=lambda x: x[0])
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: extract_news_calendar.py OUT.csv PDF1 [PDF2 ...]")
    out_csv, pdf_paths = sys.argv[1], sys.argv[2:]
    # page counts via pdfinfo
    pdfs = []
    for p in pdf_paths:
        info = subprocess.run(["pdfinfo", p], capture_output=True, text=True).stdout
        n = int(re.search(r'Pages:\s+(\d+)', info).group(1))
        pdfs.append((p, n))
    rows = extract(pdfs)
    with open(out_csv, "w") as f:
        f.write("datetime_ET,event,impact\n")
        for dt, ev, imp in rows:
            f.write(f"{dt:%Y-%m-%d %H:%M},{ev},{imp}\n")
    print(f"wrote {out_csv}: {len(rows)} rows  impacts={dict(Counter(r[2] for r in rows))}")


if __name__ == "__main__":
    main()
