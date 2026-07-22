#!/usr/bin/env python3
"""Generate docs/canon-dashboard.html — the full breakdown of the shipped canon book.
    python -m scripts.canon_dashboard
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

C = pd.read_parquet("output/canon_book.parquet")
T = C[C["size"] > 0].sort_values("fill").copy()
T["mo"] = T.day.str[:7]
T["win"] = T.dollars > 0
T["dow"] = pd.to_datetime(T.day).dt.day_name()

def stats(d):
    if len(d) == 0:
        return dict(n=0, w=0, l=0, wr=0, pl=0)
    return dict(n=len(d), w=int(d.win.sum()), l=int((~d.win).sum()),
                wr=d.win.mean() * 100, pl=d.pl.sum())

# monthly x window
mrows = []
for mo, g in T.groupby("mo"):
    r = {"mo": mo, "all": stats(g), "pre": stats(g[g.win_ == "pre"]), "gold": stats(g[g.win_ == "gold"])}
    mrows.append(r)
# dow x window
drows = []
for dw in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
    g = T[T.dow == dw]
    drows.append({"dow": dw, "all": stats(g), "pre": stats(g[g.win_ == "pre"]), "gold": stats(g[g.win_ == "gold"])})
# JS focus
JS = T[(T.mo >= "2025-07") & (T.mo <= "2025-09")]
js_win = {w: stats(JS[JS.win_ == w]) for w in ("pre", "gold")}
js_setup = {p: stats(JS[JS.pattern == p]) for p in ("A", "B", "B2")}
good = T[~((T.mo >= "2025-07") & (T.mo <= "2025-09"))]
gd_win = {w: stats(good[good.win_ == w]) for w in ("pre", "gold")}
# setup x window x year
sw = {}
for yr in (2025, 2026):
    for w in ("pre", "gold"):
        for p in ("A", "B", "B2"):
            sw[(yr, w, p)] = stats(T[(T.yr == yr) & (T.win_ == w) & (T.pattern == p)])
# score ladder
sc = {int(k): stats(g) for k, g in T.groupby("score")}
# checks on/off
chk = {}
for c, nm in [("W", "W heatmap"), ("F", "F fill-delta"), ("Tp", "T tape"), ("G", "G geometry"), ("C", "C window-CVD")]:
    on, off = T[T[c] == 1], T[T[c] == 0]
    chk[nm] = (stats(on), stats(off))
# layers activity
full = C
l2b = int(((full.nth >= 2) & (full.score < 4)).sum())
gov_days = full[full.governor < 1].day.nunique()
lad = int((full["size"].eq(0) & (full.score >= 3) & ~((full.nth >= 2) & (full.score < 4))).sum())
# days + curve
daypl = T.groupby("day").pl.sum()
best5 = daypl.nlargest(5); worst5 = daypl.nsmallest(5)
cum = daypl.cumsum()
dd = (cum.cummax() - cum)
eq_pts = list(zip(range(len(cum)), cum.values))
green_days = (daypl > 0).mean() * 100
y25, y26 = T[T.yr == 2025].pl.sum(), T[T.yr == 2026].pl.sum()
mm = T.groupby("mo").pl.sum()

def fm(v): return f"{v:+,.0f}"
def frac(s): return f"{s['w']}W-{s['l']}L"

def qmetrics(d):
    wins = d[d.pl > 0].pl; losses = d[d.pl < 0].pl
    pf = wins.sum() / abs(losses.sum()) if len(losses) else float("inf")
    rr = (d.dollars / (d.risk * 20)).replace([np.inf, -np.inf], np.nan)
    aw = wins.mean() if len(wins) else 0; al = losses.mean() if len(losses) else 0
    return pf, aw, al, (abs(aw / al) if al else 0), rr.mean(), d.pl.mean()

qm_slices = [("ALL", T), ("2025", T[T.yr == 2025]), ("2026", T[T.yr == 2026]),
             ("pre-market", T[T.win_ == "pre"]), ("golden", T[T.win_ == "gold"]),
             ("Jul-Sep 25", JS), ("good months", good),
             ("setup A", T[T.pattern == "A"]), ("setup B", T[T.pattern == "B"]),
             ("setup B2", T[T.pattern == "B2"])]
rows_qm = "\n".join(
    (lambda pf, aw, al, po, r, ex:
     f"<tr><td>{nm}</td><td class='mono'>{pf:.2f}</td><td class='mono gwin'>{aw:+.0f}</td>"
     f"<td class='mono gloss'>{al:+.0f}</td><td class='mono'>{po:.2f}</td>"
     f"<td class='mono'>{r:+.2f}</td><td class='mono {'gwin' if ex>=0 else 'gloss'}'>{ex:+.0f}</td></tr>")(*qmetrics(d))
    for nm, d in qm_slices if len(d))

jsd = JS.groupby("day").pl.sum().nsmallest(8)
rows_jsd = "\n".join(
    f"<tr><td class='mono'>{day}</td><td class='mono gloss'>{v:+,.0f}</td>"
    f"<td>{'; '.join(f'{r.win_}/{r.pattern} s{int(r.score)} {r.direction} ${r.pl:+.0f}' for r in JS[JS.day==day].itertuples())}</td></tr>"
    for day, v in jsd.items())

BAR_MAX = max(abs(mm.min()), mm.max())
def bar(v):
    pct = abs(v) / BAR_MAX * 100
    cls = "bw" if v >= 0 else "bl"
    return f'<div class="barwrap"><div class="{cls}" style="width:{pct:.0f}%"></div></div>'

rows_month = "\n".join(
    f"<tr><td class='mono'>{r['mo']}</td><td>{bar(r['all']['pl'])}</td>"
    f"<td class='mono {'gwin' if r['all']['pl']>=0 else 'gloss'}'>{fm(r['all']['pl'])}</td>"
    f"<td class='mono'>{r['all']['n']} ({r['all']['wr']:.0f}%)</td>"
    f"<td class='mono {'gwin' if r['pre']['pl']>=0 else 'gloss'}'>{fm(r['pre']['pl'])}</td>"
    f"<td class='mono'>{frac(r['pre'])} ({r['pre']['wr']:.0f}%)</td>"
    f"<td class='mono {'gwin' if r['gold']['pl']>=0 else 'gloss'}'>{fm(r['gold']['pl'])}</td>"
    f"<td class='mono'>{frac(r['gold'])} ({r['gold']['wr']:.0f}%)</td></tr>"
    for r in mrows)

rows_dow = "\n".join(
    f"<tr><td>{r['dow']}</td>"
    f"<td class='mono {'gwin' if r['all']['pl']>=0 else 'gloss'}'>{fm(r['all']['pl'])}</td>"
    f"<td class='mono'>{frac(r['all'])} ({r['all']['wr']:.0f}%)</td>"
    f"<td class='mono {'gwin' if r['pre']['pl']>=0 else 'gloss'}'>{fm(r['pre']['pl'])}</td>"
    f"<td class='mono'>{frac(r['pre'])} ({r['pre']['wr']:.0f}%)</td>"
    f"<td class='mono {'gwin' if r['gold']['pl']>=0 else 'gloss'}'>{fm(r['gold']['pl'])}</td>"
    f"<td class='mono'>{frac(r['gold'])} ({r['gold']['wr']:.0f}%)</td></tr>"
    for r in drows)

rows_sw = "\n".join(
    f"<tr><td class='mono'>{yr}</td><td>{w}</td><td class='mono'>{p}</td>"
    f"<td class='mono {'gwin' if s['pl']>=0 else 'gloss'}'>{fm(s['pl'])}</td>"
    f"<td class='mono'>{frac(s)} ({s['wr']:.0f}%)</td></tr>"
    for (yr, w, p), s in sw.items() if s["n"] > 0)

rows_sc = "\n".join(
    f"<tr><td class='mono'>{k}</td><td class='mono'>{s['n']}</td>"
    f"<td class='mono'>{s['wr']:.0f}%</td>"
    f"<td class='mono {'gwin' if s['pl']>=0 else 'gloss'}'>{fm(s['pl'])}</td></tr>"
    for k, s in sorted(sc.items()))

rows_chk = "\n".join(
    f"<tr><td>{nm}</td><td class='mono'>{on['n']} @ {on['wr']:.0f}%</td>"
    f"<td class='mono'>{off['n']} @ {off['wr']:.0f}%</td>"
    f"<td class='mono'>{on['wr']-off['wr']:+.0f}pp</td></tr>"
    for nm, (on, off) in chk.items())

# equity svg
W_, H_ = 940, 180
mn, mx = min(v for _, v in eq_pts), max(v for _, v in eq_pts)
span = mx - mn or 1
pts = " ".join(f"{i/(len(eq_pts)-1)*W_:.1f},{H_-(v-mn)/span*H_:.1f}" for i, v in eq_pts)

html = f"""<title>Canon Book — Full Breakdown</title>
<style>
:root{{--bg:#0b1216;--panel:#111c22;--line:#1d2c35;--ink:#d9e2e8;--dim:#8ba0ac;--faint:#5d7280;
--accent:#5ba8c4;--win:#3fb68b;--loss:#e0596b;}}
@media (prefers-color-scheme: light){{:root{{--bg:#f2f4f5;--panel:#fff;--line:#dde4e8;--ink:#1c2b33;
--dim:#54676f;--faint:#7e909a;--accent:#2e7d9c;--win:#178563;--loss:#c03a4e;}}}}
:root[data-theme="dark"]{{--bg:#0b1216;--panel:#111c22;--line:#1d2c35;--ink:#d9e2e8;--dim:#8ba0ac;--faint:#5d7280;--accent:#5ba8c4;--win:#3fb68b;--loss:#e0596b;}}
:root[data-theme="light"]{{--bg:#f2f4f5;--panel:#fff;--line:#dde4e8;--ink:#1c2b33;--dim:#54676f;--faint:#7e909a;--accent:#2e7d9c;--win:#178563;--loss:#c03a4e;}}
*{{box-sizing:border-box}}body{{background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif;margin:0}}
.wrap{{max-width:1080px;margin:0 auto;padding:34px 22px 80px}}
.mono{{font-family:ui-monospace,Menlo,Consolas,monospace;font-variant-numeric:tabular-nums}}
.eyebrow{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600}}
h1{{font-size:28px;margin:6px 0 4px}}h2{{font-size:18px;margin:38px 0 8px}}
.sub{{color:var(--dim);max-width:70ch}}
.band{{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0}}
.stat{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 16px;min-width:120px}}
.stat .v{{font-size:21px;font-weight:700}}.stat .k{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--faint);text-align:left;padding:7px 9px;border-bottom:1px solid var(--line)}}
td{{padding:6px 9px;border-bottom:1px solid var(--line)}}
.tw{{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:4px 8px 10px;margin-top:10px}}
.gwin{{color:var(--win)}}.gloss{{color:var(--loss)}}
.barwrap{{width:120px;height:10px;background:var(--bg);border-radius:3px;overflow:hidden}}
.bw{{height:100%;background:var(--win);border-radius:3px}}.bl{{height:100%;background:var(--loss);border-radius:3px}}
.note{{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:13px 17px;margin-top:14px;font-size:14px;color:var(--dim)}}
.note b{{color:var(--ink)}}
svg{{width:100%;height:auto;display:block}}
.eq{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;margin-top:10px}}
footer{{margin-top:50px;color:var(--faint);font-size:12.5px;border-top:1px solid var(--line);padding-top:14px}}
</style>
<div class="wrap">
<div class="eyebrow">Canon mechanical book · shipped 25 Jul 2026 · Jun 2025 – Jul 2026</div>
<h1>Full Breakdown</h1>
<p class="sub">Stop floor → 5-check validation → conviction ladder → trade #2+ needs score ≥ 4 →
within-day escalation (day red → structure required, A exempt; −$400 → done) → scoreboard governor.
No forecasting, no book choosing.</p>
<div class="band mono">
<div class="stat"><div class="v gwin">{fm(y25 + y26)}</div><div class="k">total P&amp;L</div></div>
<div class="stat"><div class="v">{fm(y25)}</div><div class="k">2025</div></div>
<div class="stat"><div class="v">{fm(y26)}</div><div class="k">2026</div></div>
<div class="stat"><div class="v">{(T.win.mean()*100):.0f}%</div><div class="k">win rate</div></div>
<div class="stat"><div class="v">{len(T)}</div><div class="k">trades</div></div>
<div class="stat"><div class="v">{green_days:.0f}%</div><div class="k">green days</div></div>
<div class="stat"><div class="v gloss">{fm(mm.min())}</div><div class="k">worst month</div></div>
<div class="stat"><div class="v gloss">-{dd.max():,.0f}</div><div class="k">max drawdown</div></div>
</div>

<h2>Equity curve (cumulative, by traded day)</h2>
<div class="eq"><svg viewBox="0 0 {W_} {H_}" preserveAspectRatio="none">
<polyline points="{pts}" fill="none" stroke="var(--accent)" stroke-width="2"/>
</svg><div class="mono" style="color:var(--faint);font-size:11px;margin-top:6px">Jun 2025 → Jul 2026 · low {fm(mn)} · final {fm(cum.iloc[-1])}</div></div>

<h2>Month by month — total, pre-market, golden</h2>
<div class="tw"><table>
<tr><th>month</th><th></th><th class="mono">total $</th><th>n (WR)</th><th class="mono">pre $</th><th>pre W-L (WR)</th><th class="mono">gold $</th><th>gold W-L (WR)</th></tr>
{rows_month}
</table></div>

<h2>The Jul–Sep question: where did it bleed?</h2>
<div class="note"><b>Answer (under the shipped canon): pre-market is now FLAT in Jul–Sep — the escalation
ladder cleaned it. The remaining bleed sits in the golden window's loss sizes.</b>
Jul–Sep pre-market: {frac(js_win['pre'])} ({js_win['pre']['wr']:.0f}% WR), {fm(js_win['pre']['pl'])} —
low win rate but the ladder cut it to break-even. Golden: {frac(js_win['gold'])}
({js_win['gold']['wr']:.0f}% WR!), {fm(js_win['gold']['pl'])} — it WINS more than it loses in
Jul–Sep golden, but the losers are bigger than the winners. Compare good months — pre:
{fm(gd_win['pre']['pl'])} ({gd_win['pre']['wr']:.0f}%) · gold: {fm(gd_win['gold']['pl'])}
({gd_win['gold']['wr']:.0f}%). By setup in Jul–Sep: A {fm(js_setup['A']['pl'])}
({js_setup['A']['wr']:.0f}%) · B {fm(js_setup['B']['pl'])} ({js_setup['B']['wr']:.0f}%) ·
B2 {fm(js_setup['B2']['pl'])} ({js_setup['B2']['wr']:.0f}%). The residual is a payoff-shape
problem (win small / lose big in dead tape), not a win-rate or window-selection problem.</div>

<h2>Day of week — total, pre-market, golden</h2>
<div class="tw"><table>
<tr><th>day</th><th class="mono">total $</th><th>W-L (WR)</th><th class="mono">pre $</th><th>pre W-L (WR)</th><th class="mono">gold $</th><th>gold W-L (WR)</th></tr>
{rows_dow}
</table></div>

<h2>Setup × window × year</h2>
<div class="tw"><table>
<tr><th>year</th><th>window</th><th>setup</th><th class="mono">$</th><th>W-L (WR)</th></tr>
{rows_sw}
</table></div>

<h2>Conviction ladder (score → outcome)</h2>
<div class="tw"><table>
<tr><th>score</th><th class="mono">n</th><th class="mono">WR</th><th class="mono">$</th></tr>
{rows_sc}
</table></div>

<h2>The five checks (on vs off, canon trades)</h2>
<div class="tw"><table>
<tr><th>check</th><th class="mono">on: n @ WR</th><th class="mono">off: n @ WR</th><th class="mono">gap</th></tr>
{rows_chk}
</table></div>

<h2>Quality metrics — profit factor, R, payoff</h2>
<div class="tw"><table>
<tr><th>slice</th><th class="mono">PF</th><th class="mono">avg win</th><th class="mono">avg loss</th><th class="mono">payoff</th><th class="mono">avg R</th><th class="mono">expectancy/t</th></tr>
{rows_qm}
</table></div>
<div class="note">Golden's profit factor (1.73) trails pre-market (2.12) because golden losers are
half again as big (−$459 vs −$241) — the payoff-shape issue localized above. Jul–Sep is the only
slice with PF &lt; 1 (0.85). Setup B is the workhorse (PF 2.39, payoff 2.86); A has positive
expectancy but inverted payoff (0.66) — small winners, occasional big losers, n=15.</div>

<h2>Jul–Sep: the most unprofitable days (canon)</h2>
<div class="tw"><table>
<tr><th>day</th><th class="mono">$</th><th>trades</th></tr>
{rows_jsd}
</table></div>
<div class="note"><b>The old nightmare is now a string of small cuts.</b> Worst Jul–Sep day under
canon: −$915 (a single score-5 golden B short on Aug 6 — highest conviction, still lost; chop
doesn't care). Second worst −$445. Nothing else reaches −$350. The bleed is no longer
concentrated or rule-breaking — it's the residual cost of participating in dead tape.</div>

<h2>Layer activity &amp; extremes</h2>
<div class="note">Layer 2b (trade #2+ needs ≥4) skipped <b>{l2b}</b> trades ·
Layer 2c ladder skipped <b>{lad}</b> · governor active on <b>{gov_days}</b> days ·
avg {len(T)/T.day.nunique():.1f} trades/day over {T.day.nunique()} traded days.<br>
Best days: {" · ".join(f"{k} <b>{fm(v)}</b>" for k, v in best5.items())}<br>
Worst days: {" · ".join(f"{k} <b>{fm(v)}</b>" for k, v in worst5.items())}</div>

<footer>Generated from output/canon_book.parquet · scripts/canon_dashboard.py · both books, every
footprint-covered day, 1-lot base sizing · 25 Jul 2026</footer>
</div>"""
Path("docs/canon-dashboard.html").write_text(html)
print("wrote docs/canon-dashboard.html")
print(f"JS pre {js_win['pre']}\nJS gold {js_win['gold']}")
