#!/usr/bin/env python3
"""Render the run-2 live dashboard HTML from runs/desk2/journal.jsonl.

Republished to the same artifact URL on every check-in — snapshot-live, not streaming.

    python -m scripts.desk_dashboard <out.html>
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import funded_book as fb  # noqa: E402

NY = "America/New_York"
TOTAL = 763


def funded_month_table(rows: list[dict]) -> str:
    """Completed-month funded comparison under the static lucid sizing: the canon book's
    rows with agent exits/dollars substituted, run through the REAL funded sim, vs the
    mechanical (two-rule) book on the same months. Fills up as months complete."""
    V = fb.load_book("fit")             # CR law applied — the mechanical baseline
    V = V.reset_index(drop=True)
    V["trade_id"] = [f"{r.day}_{r.fill.tz_convert(NY).strftime('%H%M')}_{r.direction[0]}_{i}"
                     for i, r in enumerate(V.itertuples())]
    jmap = {r["trade_id"]: r for r in rows}
    canon_n = V.groupby("month").size()
    done_n = pd.Series([r["day"][:7] for r in rows]).value_counts()
    complete = [m for m in canon_n.index
                if done_n.get(m, 0) >= canon_n[m]]
    if not complete:
        return "<div style='padding:12px 16px;color:var(--ink2);font-size:13px'>fills up as months complete…</div>"
    W = V[V.month.isin(complete)].copy()
    Wa = W.copy()
    Wa["dollars_1lot"] = [jmap[t]["agent_dollars"] for t in Wa.trade_id]
    Wa["exit"] = pd.to_datetime([jmap[t]["exit_ts"] for t in Wa.trade_id], utc=True)
    out_rows = []
    Bm = fb.run(W.sort_values("fill", kind="mergesort"), "lucid")
    Ba = fb.run(Wa.sort_values("fill", kind="mergesort"), "lucid")
    pm = Bm.groupby("month").pl.sum()
    pa = Ba.groupby("month").pl.sum()
    for m in complete:
        g = [jmap[t] for t in W[W.month == m].trade_id]
        aR = pd.Series([r["agent_R"] for r in g])
        vR = pd.Series([r["v8_R"] for r in g])
        d = pa.get(m, 0) - pm.get(m, 0)
        cls = "pos" if d > 0 else "neg" if d < 0 else ""
        out_rows.append(
            f"<tr><td>{m}</td><td>{len(g)}</td>"
            f"<td class='a'>${pa.get(m, 0):+,.0f}</td><td class='v8'>${pm.get(m, 0):+,.0f}</td>"
            f"<td class='{cls}'>${d:+,.0f}</td>"
            f"<td class='a'>{(aR > 0).mean() * 100:.0f}%</td><td class='v8'>{(vR > 0).mean() * 100:.0f}%</td>"
            f"<td class='a'>{aR.mean():+.2f}</td><td class='v8'>{vR.mean():+.2f}</td>"
            f"<td class='a'>{aR[aR > 0].mean():+.2f}</td><td class='v8'>{vR[vR > 0].mean():+.2f}</td>"
            f"<td class='a'>{aR[aR <= 0].mean():+.2f}</td><td class='v8'>{vR[vR <= 0].mean():+.2f}</td></tr>")
    tot_d = pa.sum() - pm.sum()
    out_rows.append(
        f"<tr style='font-weight:650;border-top:1px solid var(--line)'><td>TOTAL</td>"
        f"<td>{int(canon_n[complete].sum())}</td>"
        f"<td class='a'>${pa.sum():+,.0f}</td><td class='v8'>${pm.sum():+,.0f}</td>"
        f"<td class='{'pos' if tot_d > 0 else 'neg'}'>${tot_d:+,.0f}</td>"
        f"<td colspan='8'></td></tr>")
    return ("<div class='scroll'><table><thead>"
            "<tr><th>month</th><th>n</th><th>funded agent</th><th>funded mech</th><th>Δ $</th>"
            "<th>WR a</th><th>WR m</th><th>avg R a</th><th>avg R m</th>"
            "<th>win x̄ a</th><th>win x̄ m</th><th>loss x̄ a</th><th>loss x̄ m</th></tr>"
            "</thead><tbody>" + "".join(out_rows) + "</tbody></table></div>")


def main(out: str) -> None:
    rows = [json.loads(x) for x in (ROOT / "runs/desk2/journal.jsonl").read_text().splitlines()
            if x.strip()]
    D = pd.DataFrame(rows)
    D["month"] = D.day.str[:7]
    D["delta"] = D.agent_R - D.v8_R
    da, dv = D.agent_R.sum(), D.v8_R.sum()
    cum_a = D.agent_R.cumsum().round(2)
    cum_v = D.v8_R.cumsum().round(2)
    dying = D[D.v8_R < -0.1]
    winning = D[D.v8_R > 0.1]
    caps = D.capture.dropna() if "capture" in D else pd.Series(dtype=float)
    cuts = D[(D.exit_reason == "agent_exit")] if len(D) else D
    cw = cuts[cuts.get("cvd5_at_exit", pd.Series(dtype=float)) > 0] if len(cuts) else cuts
    ca = cuts[cuts.get("cvd5_at_exit", pd.Series(dtype=float)) <= 0] if len(cuts) else cuts

    def month_rows():
        s = ""
        for mo, g in D.groupby("month"):
            s += (f"<tr><td>{mo}</td><td>{len(g)}</td>"
                  f"<td class='a'>{g.agent_R.sum():+.1f}</td>"
                  f"<td class='v8'>{g.v8_R.sum():+.1f}</td>"
                  f"<td>{g.delta.sum():+.1f}</td>"
                  f"<td class='a'>{(g.agent_R > 0).mean() * 100:.0f}%</td>"
                  f"<td class='v8'>{(g.v8_R > 0).mean() * 100:.0f}%</td></tr>")
        return s

    def feed():
        s = ""
        for r in rows[-12:][::-1]:
            d = r["agent_R"] - r["v8_R"]
            cls = "pos" if d > 0.05 else "neg" if d < -0.05 else ""
            s += (f"<tr><td>{r['day'][5:]} {r['sess']} {r['direction'][0].upper()}</td>"
                  f"<td class='a'>{r['agent_R']:+.2f}</td><td class='v8'>{r['v8_R']:+.2f}</td>"
                  f"<td class='{cls}'>{d:+.2f}</td><td>{r['exit_reason']}</td>"
                  f"<td class='note'>{(r.get('last_note') or '')[:70]}</td></tr>")
        return s

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stat = lambda c: (f"{c.agent_R.sum() - c.v8_R.sum():+.1f}R" if len(c) else "—")
    cutline = lambda c: (f"n{len(c)} · {int(c.would_have_stopped.sum())} saved stops · "
                         f"median left {c.left_peak_R.median():+.1f}R" if len(c) else "—")
    xs = list(range(1, len(D) + 1))
    html = f"""<title>Run 2 — live desk chain</title>
<style>
:root{{--bg:#F6F5F2;--panel:#FFF;--ink:#23282E;--ink2:#6A7178;--line:#E3E1DB;--line2:#EFEDE8;
--agent:#2a78d6;--v8:#eb6834;--pos:#2C7A57;--neg:#B04A38;--grid:#ECEAE4}}
@media(prefers-color-scheme:dark){{:root{{--bg:#12151A;--panel:#191D24;--ink:#E4E6E9;--ink2:#8B929B;
--line:#2A3039;--line2:#232830;--agent:#3987e5;--v8:#d95926;--pos:#5BB98C;--neg:#D97B66;--grid:#232830}}}}
:root[data-theme=dark]{{--bg:#12151A;--panel:#191D24;--ink:#E4E6E9;--ink2:#8B929B;--line:#2A3039;
--line2:#232830;--agent:#3987e5;--v8:#d95926;--pos:#5BB98C;--neg:#D97B66;--grid:#232830}}
:root[data-theme=light]{{--bg:#F6F5F2;--panel:#FFF;--ink:#23282E;--ink2:#6A7178;--line:#E3E1DB;
--line2:#EFEDE8;--agent:#2a78d6;--v8:#eb6834;--pos:#2C7A57;--neg:#B04A38;--grid:#ECEAE4}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.45 system-ui,sans-serif;padding:32px 16px 56px}}
.wrap{{max-width:900px;margin:0 auto;display:flex;flex-direction:column;gap:18px}}
h1{{font-size:19px;font-weight:650;margin:0}}
.sub{{color:var(--ink2);font-size:13px;margin:0}}
.bar{{height:6px;background:var(--line2);border-radius:3px;overflow:hidden}}
.bar i{{display:block;height:100%;background:var(--agent);border-radius:3px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}
.tile{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 12px}}
.tile .k{{font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);font-weight:600}}
.tile .v{{font-size:19px;font-weight:650;font-variant-numeric:tabular-nums}}
.tile .d{{font-size:11.5px;color:var(--ink2)}}
section{{background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:hidden}}
.cap{{padding:11px 16px 9px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between}}
.cap h2{{font-size:11.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;margin:0}}
.cap span{{color:var(--ink2);font-size:11.5px}}
.legend i{{display:inline-block;width:12px;height:3px;border-radius:2px;vertical-align:3px;margin:0 5px 0 12px}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%}}
th,td{{padding:7px 9px;text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums;font-size:13px}}
thead th{{font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);font-weight:600;
border-bottom:1px solid var(--line)}}
th:first-child,td:first-child{{text-align:left;padding-left:16px}}
tbody tr{{border-bottom:1px solid var(--line2)}}tbody tr:last-child{{border-bottom:none}}
td.a{{color:var(--agent);font-weight:600}}td.v8{{color:var(--v8);font-weight:600}}
td.pos{{color:var(--pos)}}td.neg{{color:var(--neg)}}
td.note{{color:var(--ink2);font-size:12px;max-width:340px;overflow:hidden;text-overflow:ellipsis;text-align:left}}
svg text{{font:10px system-ui;fill:var(--ink2)}}
</style>
<div class="wrap">
<header><h1>Run 2 — desk-live chain, phase 1 (fit span)</h1>
<p class="sub">v3 spec · three-rule canon baseline · updated {now} · refreshes hourly at this URL</p></header>
<div class="bar"><i style="width:{len(D) / TOTAL * 100:.1f}%"></i></div>
<p class="sub">{len(D)} of ~{TOTAL} trades · {D.day.nunique()} days · through {D.day.max()}</p>
<div class="tiles">
<div class="tile"><div class="k">Total R</div><div class="v"><span style="color:var(--agent)">{da:+.1f}</span>
 <span style="color:var(--ink2);font-size:13px">vs</span> <span style="color:var(--v8)">{dv:+.1f}</span></div>
<div class="d">delta {da - dv:+.1f}R ({(da - dv) / max(len(D), 1):+.3f}/trade)</div></div>
<div class="tile"><div class="k">Win rate</div><div class="v"><span style="color:var(--agent)">{(D.agent_R > 0).mean() * 100:.0f}%</span>
 <span style="color:var(--ink2);font-size:13px">vs</span> <span style="color:var(--v8)">{(D.v8_R > 0).mean() * 100:.0f}%</span></div>
<div class="d">agent vs mechanical</div></div>
<div class="tile"><div class="k">Defense</div><div class="v">{stat(dying)}</div>
<div class="d">on mech losers (n{len(dying)})</div></div>
<div class="tile"><div class="k">Offense</div><div class="v">{stat(winning)}</div>
<div class="d">on mech winners (n{len(winning)})</div></div>
<div class="tile"><div class="k">Capture</div><div class="v">{caps.median():.2f}</div>
<div class="d">median realized/peak</div></div>
</div>
<section><div class="cap"><h2>Cumulative R</h2><span class="legend">
<i style="background:var(--agent)"></i>agent<i style="background:var(--v8)"></i>mechanical</span></div>
<div style="padding:8px 10px 4px"><svg width="100%" height="200" viewBox="0 0 860 200" preserveAspectRatio="none">{_chart(xs, list(cum_a), list(cum_v))}</svg></div></section>
<section><div class="cap"><h2>Completed months — static funded sizing (lucid)</h2>
<span>a = agent · m = mechanical</span></div>{funded_month_table(rows)}</section>
<section><div class="cap"><h2>All months, running R</h2><span>incl. in-progress</span></div><div class="scroll"><table>
<thead><tr><th>month</th><th>n</th><th>agent R</th><th>mech R</th><th>Δ</th><th>agent WR</th><th>mech WR</th></tr></thead>
<tbody>{month_rows()}</tbody></table></div></section>
<section><div class="cap"><h2>Cut scorecard</h2><span>early exits, by flow at exit</span></div>
<div style="padding:10px 16px;font-size:13px">
flow WITH at exit: {cutline(cw)}<br>flow AGAINST at exit: {cutline(ca)}</div></section>
<section><div class="cap"><h2>Latest trades</h2><span>newest first</span></div>
<div class="scroll"><table>
<thead><tr><th>trade</th><th>agent</th><th>mech</th><th>Δ</th><th>exit</th><th>agent's note</th></tr></thead>
<tbody>{feed()}</tbody></table></div></section>
</div>"""
    Path(out).write_text(html)
    print(f"dashboard: {len(D)} trades -> {out}")


def _chart(xs, a, v):
    if len(xs) < 2:
        return "<text x='430' y='100' text-anchor='middle'>waiting for trades…</text>"
    W, H, P = 860, 200, 30
    ymax = max(max(a), max(v), 1)
    ymin = min(min(a), min(v), 0)
    X = lambda i: P + (W - 2 * P) * i / (len(xs) - 1)
    Y = lambda y: 12 + (H - 34) * (1 - (y - ymin) / (ymax - ymin))
    line = lambda d, c: ("<path d='" + "".join(f"{'L' if i else 'M'}{X(i):.1f},{Y(y):.1f}"
                         for i, y in enumerate(d)) + f"' fill='none' stroke='{c}' stroke-width='2'/>")
    grid = "".join(f"<line x1='{P}' x2='{W-P}' y1='{Y(g):.0f}' y2='{Y(g):.0f}' stroke='var(--grid)'/>"
                   f"<text x='{P-4}' y='{Y(g)+3:.0f}' text-anchor='end'>{g:+.0f}</text>"
                   for g in _ticks(ymin, ymax))
    return (grid + line(v, "var(--v8)") + line(a, "var(--agent)")
            + f"<text x='{X(len(xs)-1)-4}' y='{Y(a[-1])-6:.0f}' text-anchor='end' "
              f"fill='var(--agent)' style='font-weight:600'>{a[-1]:+.1f}</text>"
            + f"<text x='{X(len(xs)-1)-4}' y='{Y(v[-1])+12:.0f}' text-anchor='end' "
              f"fill='var(--v8)' style='font-weight:600'>{v[-1]:+.1f}</text>")


def _ticks(lo, hi):
    span = hi - lo
    step = 10 if span > 30 else 5 if span > 12 else 2
    t, out = int(lo // step) * step, []
    while t <= hi:
        if t >= lo:
            out.append(t)
        t += step
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "desk_dashboard.html")
