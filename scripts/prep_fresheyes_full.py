#!/usr/bin/env python3
"""Prep the FULL-SPAN fresh-eyes conviction run (Angus 22 Jul). Every day with CVD+depth+ledger
coverage (2025-06-02 .. 2026-07-08, ~238 days). Each prompt carries:
  1. the standard fresh-eyes pre-open briefing (memoryless),
  2. premarket_flow  -- 08:00-09:30 CVD conviction + rank vs trailing 20 sessions,
  3. opening_tape    -- the 09:30-09:50 re-read: open drive, book coil, flow/price absorption,
                        developing profile (POC/VA @09:45), opening range; raw values + trailing
                        percentiles, NO fixed-threshold labels (agent judges),
plus instructions to form a PRE-MARKET thesis first, then RE-READ it against the opening tape
(decision time 09:50). Labels carry both books' P&L, the blind agent's action, and the mechanical
overlay features (coil, absorp_corr) for out-of-fit conviction sizing in the grader.

    python -m scripts.prep_fresheyes_full
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.desk.regime_agent import build_briefing, render_prompt                 # noqa: E402
from src.backtest.engine import load_news_calendar                              # noqa: E402
from src.desk.v04 import load_analog_block, attach_analog_block, as_fresh_eyes  # noqa: E402
from src.engine.indicators import volume_profile                                # noqa: E402

NY = "America/New_York"
OUT = Path("output/fe_full"); OUT.mkdir(parents=True, exist_ok=True)

GUIDE = """
## HOW TO READ THIS BRIEFING (two-phase, READ CAREFULLY)

Your decision time is 09:50 ET. Work in TWO PHASES and report both:

PHASE 1 -- PRE-MARKET THESIS (everything except `opening_tape`): form the regime read you would
have committed to at 09:30. Record it in `premarket_regime` / `premarket_stand_down`.

PHASE 2 -- RE-READ AT 09:50 (`opening_tape`): the first 20 minutes of tape are evidence about
whether your pre-market thesis is PLAYING OUT or FAILING. Do not carry a pre-market thesis into
the day unchanged if the tape contradicts it. Set `revised=true` whenever the tape changed your
regime, bias, stand-down, or size.

How to weigh the signals (validated on out-of-fit data):
- `premarket_flow` flat / mid-pack vs recent -> no one committed pre-open -> chop risk, lean
  stand-down or reduced size. Strong one-sided flow -> supports trading the aligned book.
- `opening_tape.book_coil` HIGH percentile (balanced bid/ask depth) AND
  `opening_tape.flow_price_absorption` HIGH percentile (aggressive flow NOT moving price) is the
  single most reliable no-trade/chop signature we have measured. Both high -> stand down or 0.25.
- `open_drive` CONFIRMING strong pre-market flow -> initiative continuation, supports the
  momentum book. Open drive CONTRADICTING pre-market flow -> exhaustion/trap risk, cut size.
- Developing value (`dev_profile`): price accepting inside a narrow developing value -> rotation
  lean; price driving and holding outside developing value -> imbalance/momentum lean.
- Conflicting evidence -> lower size_multiplier / confidence, do not average to a coin flip.

Final fields (`regime`, `directional_bias`, `stand_down`, `size_multiplier`, `confidence`) are
your 09:50 verdict, sized by conviction: 1.0 only when evidence stacks one way; 0.5 mixed but
tradeable; 0.25 thin; stand_down/0 when the day has no edge.
"""


def load_cvd_minutes():
    fr = []
    for f in ("footprint_q3_2025", "footprint_q4_2025", "footprint_feb_mar2026",
              "footprint_apr2026", "footprint_may_jul2026"):
        p = Path(f"data/reference/cvd/{f}.parquet")
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["ts_minute", "side", "volume"])
        d["s"] = np.where(d.side == "B", d.volume, -d.volume)
        fr.append(d.groupby("ts_minute")["s"].sum())
    g = pd.concat(fr).groupby(level=0).sum()
    g.index = g.index.tz_convert(NY)
    return g.sort_index()


def pct_rank(x, hist):
    h = np.asarray([v for v in hist if v == v])
    if len(h) < 8 or x != x:
        return None
    return round(float((h < x).mean()) * 100)


def rank_label(x, hist):
    p = pct_rank(x, hist)
    if p is None:
        return "insufficient history"
    return ("top-decile BUYING" if p >= 90 else "heavy buying" if p >= 70 else
            "flat / neutral (mid-pack)" if p >= 30 else "heavy selling" if p >= 10
            else "bottom-decile SELLING")


def main():
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    df = df.assign(ny=df.ts_event.dt.tz_convert(NY))
    df["d"] = df.ny.dt.strftime("%Y-%m-%d")
    df["hm"] = df.ny.dt.hour * 60 + df.ny.dt.minute
    rv = pd.read_csv("output/regime_vector.csv")
    try:
        cal = load_news_calendar()
    except Exception:
        cal = None
    L = pd.read_csv("output/v07/walk_v07/ledger.csv")
    L["act3"] = L.act.map({"MOMENTUM": "E4", "ROTATION": "E3", "FLAT": "FLAT"}).fillna("FLAT")
    cvd = load_cvd_minutes()
    cvd_days = set(pd.Series(cvd.index.strftime("%Y-%m-%d")).unique())
    depth_days = {Path(f).stem.split("_")[2]: f for f in
                  glob.glob("data/reference/depth_2025/*.csv") + glob.glob("data/reference/depth_2026/*.csv")}
    SF = pd.read_parquet("output/standdown_features.parquet")[["day", "coil"]].set_index("day")

    days = sorted(cvd_days & set(depth_days) & set(L.day))
    print(f"covered days: {len(days)}  span {days[0]} -> {days[-1]}")

    hm_c = cvd.index.hour * 60 + cvd.index.minute
    pre_by_day = cvd[(hm_c >= 480) & (hm_c < 570)].groupby(lambda t: t.strftime("%Y-%m-%d")).sum()
    drv_by_day = cvd[(hm_c >= 570) & (hm_c < 580)].groupby(lambda t: t.strftime("%Y-%m-%d")).sum()

    # rolling histories (trailing 20 covered days, prior only -> causal)
    hist = {k: [] for k in ("premkt", "coil", "absorp", "orange")}
    labels = []
    for day in days:
        lrow = L[L.day == day]
        g = df[(df.d == day) & (df.hm >= 570) & (df.hm < 590)].sort_values("hm")   # 09:30-09:50 bars
        if lrow.empty or len(g) < 15:
            continue
        # --- opening tape features ---
        c = cvd[(cvd.index >= pd.Timestamp(f"{day} 09:30", tz=NY)) &
                (cvd.index < pd.Timestamp(f"{day} 09:50", tz=NY))]
        cm = c.groupby(c.index.floor("min")).sum()
        ret = (g.close - g.open).values
        dlt = pd.Series(g.ny.dt.floor("min").values).map(cm).fillna(0).values
        absorp = (-np.corrcoef(ret, dlt)[0, 1]) if np.std(ret) > 0 and np.std(dlt) > 0 else 0.0
        coil = float(SF.coil.get(day, np.nan))
        orange = float(g[g.hm < 580].high.max() - g[g.hm < 580].low.min())
        premkt = float(pre_by_day.get(day, np.nan))
        drive = float(drv_by_day.get(day, 0.0))
        g45 = g[g.hm < 585]
        try:
            P = volume_profile(g45[["ts_event", "high", "low", "volume"]], 0.25, 70)
            px45 = float(g45.close.iloc[-1])
            dev = {"poc": round(P.poc, 2), "vah": round(P.vah, 2), "val": round(P.val, 2),
                   "va_width_pts": round(P.vah - P.val, 2),
                   "price_0945": px45, "price_vs_poc_pts": round(px45 - P.poc, 2),
                   "price_vs_value": ("above_value" if px45 > P.vah else
                                      "below_value" if px45 < P.val else "inside_value")}
        except Exception:
            dev = None

        # --- briefing ---
        b = build_briefing(day, df, rv, cal, analogs=None, news=None, playbook_notes=None)
        b = as_fresh_eyes(b)
        ab = load_analog_block(day)
        if ab:
            b = attach_analog_block(b, ab)
        b["premarket_flow"] = {"window": "08:00-09:30 ET", "net_delta": int(premkt),
                               "vs_recent": rank_label(premkt, hist["premkt"])}
        b["opening_tape"] = {
            "window": "09:30-09:50 ET (your re-read)",
            "open_drive_0930_0940_delta": int(drive),
            "book_coil": {"value": None if coil != coil else round(coil, 3),
                          "pctile_vs_recent": pct_rank(coil, hist["coil"]),
                          "note": "1.0 = perfectly balanced bid/ask depth at open"},
            "flow_price_absorption": {"value": round(float(absorp), 3),
                                      "pctile_vs_recent": pct_rank(absorp, hist["absorp"]),
                                      "note": "high = aggressive flow NOT moving price (absorbed)"},
            "opening_range_0930_0940_pts": round(orange, 2),
            "opening_range_pctile": pct_rank(orange, hist["orange"]),
            "dev_profile": dev,
        }
        prompt = render_prompt(b) + GUIDE
        (OUT / f"{day}.prompt.txt").write_text(prompt)

        r = lrow.iloc[0]
        oracle_act = "E3" if r.e3 > max(r.e4, 0) else "E4" if r.e4 > max(r.e3, 0) else "FLAT"
        labels.append(dict(day=day, e3=r.e3, e4=r.e4, pl_blind=r.pl, orig_act=r.act3,
                           oracle_act=oracle_act, premkt_cvd=premkt, coil=coil,
                           absorp_corr=float(absorp), open_range=orange))
        for k, v in (("premkt", premkt), ("coil", coil), ("absorp", absorp), ("orange", orange)):
            hist[k].append(v)
            hist[k] = hist[k][-20:]

    Lb = pd.DataFrame(labels)
    Lb.to_csv(OUT / "labels.csv", index=False)
    Lb[["day"]].to_csv(OUT / "days.csv", index=False)
    print(f"wrote {len(Lb)} prompts + labels -> {OUT}/")
    # sanity: does the 09:30-09:50 absorp variant still separate both-red days? (validated one was 09:30-10:00)
    Lb["both_red"] = ((Lb.e3 <= 0) & (Lb.e4 <= 0)).astype(int)
    Lb["yr"] = Lb.day.str[:4].astype(int)
    for yr in (2025, 2026):
        s = Lb[Lb.yr == yr]
        r = s.absorp_corr.rank()
        n1 = s.both_red.sum(); n0 = len(s) - n1
        a = (r[s.both_red == 1].sum() - n1 * (n1 + 1) / 2) / max(n1 * n0, 1)
        print(f"  absorp_corr(09:30-09:50) AUC vs both-red, {yr}: {a:.2f}   "
              f"blind agent book-hit {(s.orig_act == s.oracle_act).mean()*100:.0f}%")


if __name__ == "__main__":
    main()
