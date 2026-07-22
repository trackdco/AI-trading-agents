#!/usr/bin/env python3
"""Prep the CVD-enriched fresh-eyes run (Angus 22 Jul). For each 2025 H2 day: build the
standard fresh-eyes briefing, inject a pre-market-flow (CVD) block (decision at ~09:30, so the
08:00-09:30 flow is honestly knowable), render the prompt, and write it. Also writes a labels
CSV (oracle action, both books, the ORIGINAL blind agent's action, pre-market CVD) for grading.

    python -m scripts.prep_fresheyes_cvd
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.desk.regime_agent import build_briefing, render_prompt                # noqa: E402
from src.backtest.engine import load_news_calendar                             # noqa: E402
from src.desk.v04 import load_analog_block, attach_analog_block, as_fresh_eyes  # noqa: E402

NY = "America/New_York"
OUT = Path("output/fe_cvd"); OUT.mkdir(parents=True, exist_ok=True)

CVD_GUIDE = """
## Extra field this run — `premarket_flow` (READ THIS)

The briefing now carries `premarket_flow`: cumulative CVD (aggressor buy-minus-sell volume)
over 08:00-09:30, plus how it ranks against the trailing 20 sessions. This is the ONE order-flow
signal that predicted tradeable-vs-stand-down days ACROSS regimes in testing.

How to weigh it (WITH the regime/auction evidence, never alone):
- Pre-market flow that is FLAT / no-conviction / mid-pack vs recent days -> lean STAND-DOWN
  (no one is committing before the open; chop/both-books-lose risk is elevated).
- Strong one-sided conviction (top/bottom of the trailing range) -> supports TRADING the
  aligned book (heavy buying -> momentum/long lean; heavy selling -> momentum/short lean).
- If pre-market flow contradicts the regime read, lower confidence / size.
You may cite it as `premarket_flow.net_delta` or `premarket_flow.vs_recent`.
"""


def load_premkt_cvd():
    fr = []
    for f in ("footprint_q3_2025", "footprint_q4_2025"):
        p = Path(f"data/reference/cvd/{f}.parquet")
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["ts_minute", "side", "volume"])
        d["s"] = np.where(d.side == "B", d.volume, -d.volume)
        fr.append(d.groupby("ts_minute")["s"].sum())
    g = pd.concat(fr).groupby(level=0).sum()
    g.index = g.index.tz_convert(NY)
    g = g.sort_index()
    hm = g.index.hour * 60 + g.index.minute
    pre = g[(hm >= 480) & (hm < 570)]
    day = pre.groupby(pre.index.strftime("%Y-%m-%d")).sum().rename("premkt_cvd")
    drive = g[(hm >= 570) & (hm < 580)].groupby(lambda t: t.strftime("%Y-%m-%d")).sum()
    return day, drive


def rank_label(x, hist):
    if len(hist) < 8:
        return "insufficient history"
    p = (np.asarray(hist) < x).mean()
    return ("top-decile BUYING" if p >= .9 else "heavy buying" if p >= .7 else
            "flat / neutral (mid-pack)" if p >= .3 else "heavy selling" if p >= .1 else "bottom-decile SELLING")


def main():
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    rv = pd.read_csv("output/regime_vector.csv")
    try:
        cal = load_news_calendar()
    except Exception:
        cal = None
    led = pd.read_csv("output/v07/walk_v07/ledger.csv")
    led["act3"] = led.act.map({"MOMENTUM": "E4", "ROTATION": "E3", "FLAT": "FLAT"}).fillna("FLAT")
    premkt, drive = load_premkt_cvd()
    days = [d for d in premkt.index if "2025-07" <= d <= "2025-12"]
    hist = premkt.sort_index()

    labels = []
    for day in days:
        lrow = led[led.day == day]
        if lrow.empty:
            continue
        b = build_briefing(day, df, rv, cal, analogs=None, news=None, playbook_notes=None)
        b = as_fresh_eyes(b)
        ab = load_analog_block(day)
        if ab:
            b = attach_analog_block(b, ab)
        prior = hist[hist.index < day].tail(20).values
        net = int(premkt[day])
        b["premarket_flow"] = {"window": "08:00-09:30 ET", "net_delta": net,
                               "vs_recent": rank_label(net, prior),
                               "open_drive_0930_0940": int(drive.get(day, 0))}
        prompt = render_prompt(b) + CVD_GUIDE
        (OUT / f"{day}.prompt.txt").write_text(prompt)
        r = lrow.iloc[0]
        oracle_act = "E3" if r.e3 > max(r.e4, 0) else "E4" if r.e4 > max(r.e3, 0) else "FLAT"
        labels.append(dict(day=day, e3=r.e3, e4=r.e4, oracle_act=oracle_act,
                           orig_act=r.act3, orig_hit=int(r.act3 == oracle_act),
                           premkt_cvd=net, vs_recent=b["premarket_flow"]["vs_recent"]))
    pd.DataFrame(labels).to_csv(OUT / "labels.csv", index=False)
    print(f"wrote {len(labels)} enriched prompts + labels -> {OUT}/")
    print(f"  orig blind agent book-hit on these days: {np.mean([l['orig_hit'] for l in labels])*100:.0f}%")


if __name__ == "__main__":
    main()
