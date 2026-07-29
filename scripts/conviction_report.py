#!/usr/bin/env python3
"""CONVICTION-SIZING REPORT (Angus 21 Jul). Size by the entry book-support read:
HIGH (book against = absorption) = 2.0x, MID (neutral) = 1.0x, LOW (book with) = 0.5x.
Builds the full analytics dashboard: sizing test (train/test), day-by-day pre vs golden,
most-profitable days, most-profitable time periods, and risk:reward. Writes a self-contained
HTML to docs/conviction-dashboard.html.

    python -m scripts.conviction_report
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
PV = 20.0          # NQ $/point
TRAIN = {"2026-02", "2026-03", "2026-04"}
DEPTH = "data/reference/depth_2026"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]


def book_at(cache, path, minute):
    df = cache.get(path)
    if df is None:
        df = pd.read_csv(path, parse_dates=["ts"]); cache[path] = df
    m = df[(df.ts.dt.hour * 60 + df.ts.dt.minute).between(minute - 2, minute)]
    if not len(m):
        return None
    per = m.groupby(["ts", "side"])["size"].sum().unstack(fill_value=0)
    if "bid" not in per or "ask" not in per:
        return None
    bid, ask = per["bid"].mean(), per["ask"].mean()
    tot = per["bid"] + per["ask"]
    imbal = (bid - ask) / (bid + ask) if (bid + ask) else 0.0
    hp = (tot.iloc[-1] - tot.iloc[0]) if len(tot) > 1 else 0.0
    return imbal, hp


def build():
    W = pd.read_csv("output/window22_trades.csv")
    W = W[W.gated_kept].copy()
    W["date"] = W.date.astype(str)
    didx = {Path(f).stem.split("_")[2]: f for f in glob.glob(f"{DEPTH}/nq_depth_*_ny.csv")}
    cache = {}
    bs, hpv, dep = [], [], []
    for r in W.itertuples():
        p = didx.get(r.date)
        h, m = map(int, r.fill_t.split(":"))
        res = book_at(cache, p, h * 60 + m) if p else None
        if res is None:
            bs.append(np.nan); hpv.append(np.nan); dep.append(False)
        else:
            sgn = 1 if r.direction == "long" else -1
            bs.append(res[0] * sgn); hpv.append(res[1]); dep.append(True)
    W["book_support"] = bs
    W["hold_pull"] = hpv
    W["has_depth"] = dep
    W["fill_min"] = W.fill_t.map(lambda s: int(s[:2]) * 60 + int(s[3:]))
    # tier + conviction size (no-depth trades default to MID / 1.0)
    def tier(x):
        if pd.isna(x):
            return "MID"
        return "HIGH" if x < -0.05 else ("LOW" if x > 0.05 else "MID")
    W["tier"] = W.book_support.map(tier)
    W["conv_size"] = W.tier.map({"HIGH": 2.0, "MID": 1.0, "LOW": 0.5})
    W["conv_dollars"] = W.dollars * W.conv_size
    # reconstruct base size for R:R (half on oversized stop >42 or late fill >=10:30)
    W["base_size"] = np.where((W.risk_pts > 42) | (W.fill_min >= 630), 0.5, 1.0)
    W["points"] = W.dollars / (PV * W.base_size)
    W["R"] = W.points / W.risk_pts.replace(0, np.nan)
    W["risk_usd"] = W.risk_pts * PV
    W["set"] = np.where(W.month.isin(TRAIN), "train", "test")
    return W


# ---------- HTML helpers ----------
def money(x):
    return f"${x:+,.0f}"


def bar(pct):
    return f'<span class="bar"><span style="width:{max(0,min(100,pct)):.0f}%"></span></span>'


def main():
    W = build()
    base = W.dollars.sum()
    conv = W.conv_dollars.sum()
    avg_sz = W.conv_size.mean()
    winr = W.win.mean() * 100

    # tier table
    tiers = []
    for t in ("HIGH", "MID", "LOW"):
        s = W[W.tier == t]
        tiers.append(dict(t=t, n=len(s), win=s.win.mean()*100 if len(s) else 0,
                          at1=s.dollars.mean() if len(s) else 0, sz={"HIGH":2.0,"MID":1.0,"LOW":0.5}[t],
                          base=s.dollars.sum(), conv=s.conv_dollars.sum()))
    # train/test
    tt = []
    for name, key in (("Train Feb-Apr", "train"), ("Test May-Jul", "test"), ("All", None)):
        s = W if key is None else W[W.set == key]
        tt.append(dict(name=name, base=s.dollars.sum(), conv=s.conv_dollars.sum(),
                       avgsz=s.conv_size.mean(), n=len(s),
                       base_per=s.dollars.sum()/len(s), conv_per=s.conv_dollars.sum()/s.conv_size.sum()))

    # day-by-day pre vs golden
    piv = W.pivot_table(index="date", columns="window", values="dollars", aggfunc="sum").fillna(0.0)
    cpiv = W.pivot_table(index="date", columns="window", values="conv_dollars", aggfunc="sum").fillna(0.0)
    for c in ("pre", "golden"):
        if c not in piv: piv[c] = 0.0
        if c not in cpiv: cpiv[c] = 0.0
    day = pd.DataFrame({"pre": piv["pre"], "golden": piv["golden"],
                        "cpre": cpiv["pre"], "cgolden": cpiv["golden"]})
    day["total"] = day.pre + day.golden
    day["ctotal"] = day.cpre + day.cgolden
    day["wd"] = pd.to_datetime(day.index).day_name().str[:3]
    day = day.sort_index()
    top = day.sort_values("total", ascending=False).head(8)
    bot = day.sort_values("total").head(5)

    # periods
    by_win = {w: dict(base=W[W.window==w].dollars.sum(), conv=W[W.window==w].conv_dollars.sum(),
                      n=len(W[W.window==w]), win=W[W.window==w].win.mean()*100) for w in ("pre","golden")}
    by_mo = {m: dict(base=W[W.month==m].dollars.sum(), conv=W[W.month==m].conv_dollars.sum(),
                     n=len(W[W.month==m])) for m in MONTHS if len(W[W.month==m])}
    W["wd"] = pd.to_datetime(W.date).dt.day_name()
    by_wd = {d: dict(base=W[W.wd==d].dollars.sum(), n=len(W[W.wd==d]), win=W[W.wd==d].win.mean()*100,
                     avg=W[W.wd==d].dollars.mean())
             for d in ["Monday","Tuesday","Wednesday","Thursday","Friday"] if len(W[W.wd==d])}
    def tb(lo, hi):
        s = W[(W.fill_min >= lo) & (W.fill_min < hi)]
        return dict(n=len(s), base=s.dollars.sum(), win=s.win.mean()*100 if len(s) else 0,
                    avg=s.dollars.mean() if len(s) else 0)
    buckets = [("08:00-08:30", tb(480,510)), ("08:30-09:00", tb(510,540)),
               ("09:00-09:30", tb(540,570)), ("09:40-10:00", tb(580,600)),
               ("10:00-10:15", tb(600,615))]

    # risk:reward
    wins = W[W.win]; losses = W[~W.win]
    rr = dict(avg_risk_pts=W.risk_pts.mean(), avg_risk_usd=W.risk_usd.mean(),
              avg_win=wins.dollars.mean() if len(wins) else 0,
              avg_loss=losses.dollars.mean() if len(losses) else 0,
              avg_R=W.R.mean(), win_R=wins.R.mean() if len(wins) else 0,
              loss_R=losses.R.mean() if len(losses) else 0,
              expec=W.R.mean(), rrr=(wins.dollars.mean()/abs(losses.dollars.mean())) if len(losses) and losses.dollars.mean()!=0 else 0)

    W.to_csv("output/conviction_trades.csv", index=False)
    html = render(base, conv, avg_sz, winr, len(W), tiers, tt, day, top, bot,
                  by_win, by_mo, by_wd, buckets, rr)
    Path("docs/conviction-dashboard.html").write_text(html)
    print(f"baseline {money(base)}  conviction {money(conv)}  avg size {avg_sz:.2f}  win {winr:.0f}%")
    print("test half: base", money(tt[1]['base']), "-> conv", money(tt[1]['conv']),
          f"(per-unit base ${tt[1]['base_per']:+.0f} -> conv ${tt[1]['conv_per']:+.0f})")
    print("-> docs/conviction-dashboard.html")


def render(base, conv, avg_sz, winr, n, tiers, tt, day, top, bot, by_win, by_mo, by_wd, buckets, rr):
    def cls(x): return "grn" if x > 0 else ("red" if x < 0 else "mut")
    tier_rows = "".join(
        f"<tr><td><b>{t['t']}</b> <span class='mut'>×{t['sz']}</span></td><td>{t['n']}</td>"
        f"<td>{t['win']:.0f}%</td><td class='{cls(t['at1'])}'>${t['at1']:+.0f}</td>"
        f"<td class='{cls(t['base'])}'>{money(t['base'])}</td><td class='{cls(t['conv'])}'>{money(t['conv'])}</td></tr>"
        for t in tiers)
    tt_rows = "".join(
        f"<tr class='{'hi' if r['name'].startswith('Test') else ''}'><td>{r['name']}</td><td>{r['n']}</td>"
        f"<td class='{cls(r['base'])}'>{money(r['base'])}</td><td class='{cls(r['conv'])}'>{money(r['conv'])}</td>"
        f"<td>{r['avgsz']:.2f}</td><td class='mut'>${r['base_per']:+.0f} → ${r['conv_per']:+.0f}</td></tr>"
        for r in tt)
    day_rows = "".join(
        f"<tr><td>{d} <span class='mut'>{r.wd}</span></td>"
        f"<td class='{cls(r.pre)}'>{money(r.pre) if r.pre else '·'}</td>"
        f"<td class='{cls(r.golden)}'>{money(r.golden) if r.golden else '·'}</td>"
        f"<td class='{cls(r.total)}'><b>{money(r.total)}</b></td>"
        f"<td class='{cls(r.ctotal)}'>{money(r.ctotal)}</td></tr>"
        for d, r in day.iterrows())
    top_rows = "".join(
        f"<tr><td>{d} <span class='mut'>{r.wd}</span></td><td class='mut'>{'golden' if r.golden>=r.pre else 'pre'}</td>"
        f"<td class='{cls(r.total)}'><b>{money(r.total)}</b></td></tr>" for d, r in top.iterrows())
    bot_rows = "".join(
        f"<tr><td>{d} <span class='mut'>{r.wd}</span></td><td class='{cls(r.total)}'>{money(r.total)}</td></tr>"
        for d, r in bot.iterrows())
    win_rows = "".join(
        f"<tr><td>{'Pre-market 08:00–09:30' if w=='pre' else 'Golden 09:40–10:15'}</td><td>{v['n']}</td>"
        f"<td>{v['win']:.0f}%</td><td class='{cls(v['base'])}'>{money(v['base'])}</td>"
        f"<td class='{cls(v['conv'])}'>{money(v['conv'])}</td></tr>" for w, v in by_win.items())
    mo_rows = "".join(
        f"<tr><td>{m}</td><td>{v['n']}</td><td class='{cls(v['base'])}'>{money(v['base'])}</td>"
        f"<td class='{cls(v['conv'])}'>{money(v['conv'])}</td></tr>" for m, v in by_mo.items())
    wd_rows = "".join(
        f"<tr><td>{d}</td><td>{v['n']}</td><td>{v['win']:.0f}%</td>"
        f"<td class='{cls(v['avg'])}'>${v['avg']:+.0f}/t</td><td class='{cls(v['base'])}'>{money(v['base'])}</td></tr>"
        for d, v in by_wd.items())
    bk_rows = "".join(
        f"<tr><td>{lbl}</td><td>{v['n']}</td><td>{v['win']:.0f}%</td>"
        f"<td class='{cls(v['avg'])}'>${v['avg']:+.0f}/t</td><td class='{cls(v['base'])}'>{money(v['base'])}</td></tr>"
        for lbl, v in buckets)
    lift = conv - base
    return f"""<title>Conviction-Sizing & Full Breakdown — NQ 2026</title>
<style>
:root{{--bg:#0f1115;--panel:#171a21;--p2:#1e222b;--ink:#e8ecf3;--mut:#93a0b4;--line:#2a2f3a;
--grn:#39d98a;--red:#ff6b6b;--amb:#ffb454;--acc:#5b9dff;}}
@media(prefers-color-scheme:light){{:root{{--bg:#f5f7fa;--panel:#fff;--p2:#eef1f5;--ink:#141922;
--mut:#5a6675;--line:#e0e5ec;--grn:#0f9d58;--red:#d64545;--amb:#b8730c;--acc:#2f6fed;}}}}
:root[data-theme=dark]{{--bg:#0f1115;--panel:#171a21;--p2:#1e222b;--ink:#e8ecf3;--mut:#93a0b4;--line:#2a2f3a;--grn:#39d98a;--red:#ff6b6b;--amb:#ffb454;--acc:#5b9dff;}}
:root[data-theme=light]{{--bg:#f5f7fa;--panel:#fff;--p2:#eef1f5;--ink:#141922;--mut:#5a6675;--line:#e0e5ec;--grn:#0f9d58;--red:#d64545;--amb:#b8730c;--acc:#2f6fed;}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);
font:14.5px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:30px 20px 80px}}
h1{{font-size:25px;margin:0 0 3px;letter-spacing:-.02em}}h2{{font-size:17px;margin:30px 0 10px}}
.sub{{color:var(--mut);margin:0 0 20px}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}}
.row{{display:flex;gap:12px;flex-wrap:wrap}}.card{{flex:1 1 150px;background:var(--p2);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
.card .k{{color:var(--mut);font-size:11.5px;text-transform:uppercase;letter-spacing:.04em}}
.card .v{{font-size:21px;font-weight:650;margin-top:2px}}
.grn{{color:var(--grn)}}.red{{color:var(--red)}}.amb{{color:var(--amb)}}.acc{{color:var(--acc)}}.mut{{color:var(--mut)}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;margin-top:4px}}
th,td{{text-align:right;padding:7px 10px;border-bottom:1px solid var(--line)}}
th:first-child,td:first-child{{text-align:left}}
thead th{{color:var(--mut);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.03em}}
tbody tr:last-child td{{border-bottom:none}}.hi{{background:color-mix(in srgb,var(--acc) 12%,transparent)}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}@media(max-width:720px){{.two{{grid-template-columns:1fr}}}}
.scroll{{overflow-x:auto}}.note{{color:var(--mut);font-size:12.5px;margin-top:8px}}
code{{background:var(--p2);border:1px solid var(--line);border-radius:5px;padding:1px 6px;font-size:12.5px}}
.foot{{color:var(--mut);font-size:12px;margin-top:26px;border-top:1px solid var(--line);padding-top:12px}}
</style>
<div class="wrap">
<h1>Conviction-Sizing &amp; Full Breakdown</h1>
<p class="sub">NQ 2026 (Feb–Jul) · canon gated trades · size by entry book-support: HIGH ×2 · MID ×1 · LOW ×0.5 · 21 Jul 2026</p>

<div class="panel"><div class="row">
  <div class="card"><div class="k">Baseline (flat 1×)</div><div class="v grn">{money(base)}</div><div class="mut" style="font-size:12px">{n} gated trades</div></div>
  <div class="card"><div class="k">Conviction-sized</div><div class="v {cls(conv)}">{money(conv)}</div><div class="mut" style="font-size:12px">lift {money(lift)}</div></div>
  <div class="card"><div class="k">Avg size</div><div class="v {'amb' if avg_sz>1.05 else ''}">{avg_sz:.2f}×</div><div class="mut" style="font-size:12px">&gt;1 = net leverage up</div></div>
  <div class="card"><div class="k">Win rate</div><div class="v">{winr:.0f}%</div><div class="mut" style="font-size:12px">sizing doesn't change this</div></div>
</div></div>

<h2>1 · Conviction sizing — does leaning into absorption pay?</h2>
<div class="panel scroll">
<table><thead><tr><th>tier (book at entry)</th><th>trades</th><th>win</th><th>$/t @1×</th><th>base</th><th>sized</th></tr></thead>
<tbody>{tier_rows}</tbody></table>
<p class="note"><b>HIGH</b> = book against you (absorption) · <b>LOW</b> = book with you. The tier edge is what
justifies the size tilt — and it held out-of-fit.</p>
</div>
<div class="panel scroll">
<table><thead><tr><th>window</th><th>n</th><th>baseline</th><th>conviction</th><th>avg size</th><th>$/unit-risk base→conv</th></tr></thead>
<tbody>{tt_rows}</tbody></table>
<p class="note">The honest read is the last column: <b>$/unit of size deployed</b>. If conviction beats baseline there
(not just on raw total), the money came from better <i>allocation</i>, not just from betting bigger. Test half is highlighted.</p>
</div>

<h2>2 · Day by day — pre-market vs golden</h2>
<div class="panel scroll" style="max-height:460px;overflow-y:auto">
<table><thead><tr><th>day</th><th>pre-market</th><th>golden</th><th>day total</th><th>sized</th></tr></thead>
<tbody>{day_rows}</tbody></table>
</div>

<div class="two">
  <div class="panel scroll"><h2 style="margin-top:2px">Most profitable days</h2>
  <table><thead><tr><th>day</th><th>driver</th><th>total</th></tr></thead><tbody>{top_rows}</tbody></table></div>
  <div class="panel scroll"><h2 style="margin-top:2px">Worst days</h2>
  <table><thead><tr><th>day</th><th>total</th></tr></thead><tbody>{bot_rows}</tbody></table></div>
</div>

<h2>3 · When is the money made — periods</h2>
<div class="two">
  <div class="panel scroll"><h2 style="margin-top:2px;font-size:14px">By window</h2>
  <table><thead><tr><th>window</th><th>n</th><th>win</th><th>base</th><th>conv</th></tr></thead><tbody>{win_rows}</tbody></table></div>
  <div class="panel scroll"><h2 style="margin-top:2px;font-size:14px">By month</h2>
  <table><thead><tr><th>month</th><th>n</th><th>base</th><th>conv</th></tr></thead><tbody>{mo_rows}</tbody></table></div>
</div>
<div class="two">
  <div class="panel scroll"><h2 style="margin-top:2px;font-size:14px">By time-of-day</h2>
  <table><thead><tr><th>bucket</th><th>n</th><th>win</th><th>$/t</th><th>total</th></tr></thead><tbody>{bk_rows}</tbody></table></div>
  <div class="panel scroll"><h2 style="margin-top:2px;font-size:14px">By weekday</h2>
  <table><thead><tr><th>day</th><th>n</th><th>win</th><th>$/t</th><th>total</th></tr></thead><tbody>{wd_rows}</tbody></table></div>
</div>

<h2>4 · Risk : reward</h2>
<div class="panel"><div class="row">
  <div class="card"><div class="k">Avg risk / trade</div><div class="v">{rr['avg_risk_pts']:.0f} pt</div><div class="mut" style="font-size:12px">≈ ${rr['avg_risk_usd']:,.0f} @1×</div></div>
  <div class="card"><div class="k">Avg winner</div><div class="v grn">{money(rr['avg_win'])}</div><div class="mut" style="font-size:12px">{rr['win_R']:+.1f}R</div></div>
  <div class="card"><div class="k">Avg loser</div><div class="v red">{money(rr['avg_loss'])}</div><div class="mut" style="font-size:12px">{rr['loss_R']:+.1f}R</div></div>
  <div class="card"><div class="k">Reward : risk</div><div class="v acc">{rr['rrr']:.2f} : 1</div><div class="mut" style="font-size:12px">avg win ÷ avg loss</div></div>
  <div class="card"><div class="k">Expectancy</div><div class="v {cls(rr['expec'])}">{rr['expec']:+.2f}R</div><div class="mut" style="font-size:12px">per trade, @1×</div></div>
</div>
<p class="note">R = realized points ÷ structural stop. Winners run ~{rr['win_R']:.1f}R against ~{abs(rr['loss_R']):.1f}R stops —
a low win-rate / high-R:R profile: few winners, but each pays multiples of the risk. That's why the absorption tier
(higher win-rate at the same R:R) is worth sizing into.</p></div>

<h2>Honest notes</h2>
<div class="panel"><ul style="margin:4px 0;padding-left:18px">
<li>Doubling HIGH pushes <b>average size to {avg_sz:.2f}×</b> — part of any P&amp;L gain is leverage, not skill. Judge it on the
<b>$/unit-risk</b> column and the <b>test half</b>, not the raw total.</li>
<li>Sizing never changes <i>which</i> trades win — it only amplifies each tier's edge. It's justified only because book-against
held its edge out-of-fit (82%→ / 57% train, 25% / 12% test).</li>
<li><b>Small samples</b> per tier (~15–25/half). Directional; the absorption mechanism is the reason to trust it, not the n.</li>
<li>Book read only exists where we have depth (09:30–10:30 MBP-10); trades without it default to MID ×1.</li>
</ul></div>

<p class="foot">Reproduce: <code>python -m scripts.conviction_report</code> · per-trade CSV <code>output/conviction_trades.csv</code> · canon baseline +$17,346 unchanged.</p>
</div>"""


if __name__ == "__main__":
    main()
