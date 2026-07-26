#!/usr/bin/env python3
"""Build the self-contained HTML dashboard for the v1.1 x HTF-bias 3yr backtest.
Reads bt_v11_bias_3yr_trades.csv, writes campion_v11_bias_dashboard.html.
Dataviz method: form-first, reference palette (slots 1-2, validated both modes),
thin marks, hover layer, legend only where >=2 series, light+dark, table view built-in."""
import json

import numpy as np
import pandas as pd

import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
J = pd.read_csv(f"{S}/bt_v11_bias_3yr_trades.csv").sort_values(["day", "fill"]).reset_index(drop=True)

# ---------------- aggregates ----------------
def pf(x):
    w = x[x.dollars > 0].dollars.sum(); l = -x[x.dollars <= 0].dollars.sum()
    return (w / l) if l > 0 else float("inf")

def agg(x):
    return dict(n=int(len(x)), win=round(float((x.dollars > 0).mean() * 100), 1) if len(x) else 0,
                avgR=round(float(x.R.mean()), 3) if len(x) else 0,
                dollars=round(float(x.dollars.sum())), pf=round(pf(x), 2) if len(x) else 0)

eq = J.dollars.cumsum()
dd = float((eq - eq.cummax()).min())
wmax = lmax = w = l = 0
for v in (J.dollars > 0):
    w, l = (w + 1, 0) if v else (0, l + 1)
    wmax, lmax = max(wmax, w), max(lmax, l)

head = dict(trades=len(J), win=round(float((J.dollars > 0).mean() * 100), 1),
            avgR=round(float(J.R.mean()), 3), totR=round(float(J.R.sum()), 1),
            pts=round(float(J.pts.sum())), dollars=round(float(J.dollars.sum())),
            pf=round(pf(J), 2), dd=round(dd), ws=wmax, ls=lmax)

def bucket_R(r, reason):
    if reason == "stop":
        return "stopped"
    if r >= 3.95:
        return "4R cap"
    if r >= 3:
        return "3-4R"
    if r >= 2:
        return "2-3R"
    if r >= 1:
        return "1-2R"
    if r >= 0:
        return "0-1R"
    return "<0R"

J["rb"] = [bucket_R(r, re) for r, re in zip(J.R, J.reason.str.split(":").str[0].str.replace(" (no draw in dir)", "", regex=False))]
rb_order = ["stopped", "<0R", "0-1R", "1-2R", "2-3R", "3-4R", "4R cap"]
rr = [{"b": b, "n": int((J.rb == b).sum())} for b in rb_order]

def rows_for(col, order=None):
    ks = order or sorted(J[col].dropna().unique())
    return [{"k": str(k), **agg(J[J[col] == k])} for k in ks if (J[col] == k).any()]

J["yr"] = J.day.str.slice(0, 4)
J["bias_rel"] = np.where(J.counter, "counter-bias", "with-bias")
brk = {
    "Window": rows_for("window", ["premarket", "intime"]),
    "Bias relation": rows_for("bias_rel", ["with-bias", "counter-bias"]),
    "Conviction": rows_for("conviction", ["HIGH", "MEDIUM", "LOW"]),
    "Day of week": rows_for("weekday", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
    "Year": rows_for("yr"),
}

# equity series (per trade, with dates for tooltip)
eq_pts = [{"i": i, "d": d, "v": round(float(v))} for i, (d, v) in enumerate(zip(J.day, eq))]

log_cols = ["day", "fill", "window", "bias", "conviction", "dir", "entry", "stop_dist",
            "derisk", "counter", "padded", "target_kind", "reason", "R", "dollars"]
log = J[log_cols].to_dict("records")

DATA = json.dumps({"head": head, "rr": rr, "brk": brk, "eq": eq_pts, "log": log},
                  separators=(",", ":"))

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Campion v1.1 × HTF Bias — 3yr Backtest</title>
<style>
.viz-root{color-scheme:light;
 --surface-1:#fcfcfb;--surface-2:#f1f0ee;--border:#dedcd7;
 --text-primary:#0b0b0b;--text-secondary:#52514e;--text-muted:#8a887f;
 --series-1:#2a78d6;--series-2:#eb6834;
 --pos:#008300;--neg:#e34948;--warn-bg:#fdf3d8;--warn-tx:#7a5b00;
 font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--surface-1);
 color:var(--text-primary);margin:0;padding:24px;line-height:1.45}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;
 --surface-1:#1a1a19;--surface-2:#242423;--border:#3a3936;
 --text-primary:#ffffff;--text-secondary:#c3c2b7;--text-muted:#8a887f;
 --series-1:#3987e5;--series-2:#d95926;
 --pos:#4caf50;--neg:#e66767;--warn-bg:#3a2f10;--warn-tx:#e8c96a}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;
 --surface-1:#1a1a19;--surface-2:#242423;--border:#3a3936;
 --text-primary:#ffffff;--text-secondary:#c3c2b7;--text-muted:#8a887f;
 --series-1:#3987e5;--series-2:#d95926;
 --pos:#4caf50;--neg:#e66767;--warn-bg:#3a2f10;--warn-tx:#e8c96a}
h1{font-size:20px;margin:0 0 4px}
.sub{color:var(--text-secondary);font-size:13px;margin-bottom:20px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:24px}
.tile{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:10px 12px}
.tile .k{font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.04em}
.tile .v{font-size:20px;font-weight:650;margin-top:2px}
.tile .v.neg{color:var(--neg)}.tile .v.pos{color:var(--pos)}
section{margin-bottom:28px}
h2{font-size:14px;color:var(--text-secondary);font-weight:600;margin:0 0 8px}
.card{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:14px;overflow-x:auto}
svg text{fill:var(--text-secondary);font-size:11px}
.grid line{stroke:var(--border);stroke-width:1}
.axis{stroke:var(--border)}
.tt{position:fixed;pointer-events:none;background:var(--surface-1);border:1px solid var(--border);
 border-radius:6px;padding:6px 9px;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,.18);display:none;z-index:9}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{padding:5px 8px;text-align:right;border-bottom:1px solid var(--border);white-space:nowrap}
th:first-child,td:first-child,th.l,td.l{text-align:left}
th{cursor:pointer;color:var(--text-secondary);position:sticky;top:0;background:var(--surface-2);user-select:none}
tr:hover td{background:color-mix(in srgb,var(--series-1) 7%,transparent)}
.chip{display:inline-block;border-radius:5px;padding:1px 6px;font-size:11px;font-weight:600}
.chip.dr{background:var(--warn-bg);color:var(--warn-tx)}
.chip.cb{background:color-mix(in srgb,var(--series-2) 18%,transparent);color:var(--series-2)}
.pos{color:var(--pos)}.neg{color:var(--neg)}
.note{font-size:12px;color:var(--text-muted);margin-top:6px}
.brkgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.legend{font-size:12px;color:var(--text-secondary);margin-bottom:6px}
.legend span.swatch{display:inline-block;width:10px;height:10px;border-radius:3px;margin:0 4px 0 10px;vertical-align:-1px}
</style></head><body class="viz-root">
<h1>Campion (Champion) v1.1 × HTF-Bias Governance — NQ Backtest</h1>
<div class="sub" id="sub"></div>
<div class="tiles" id="tiles"></div>
<section><h2>Equity curve — cumulative $ (per-trade sequence)</h2>
<div class="card"><svg id="eqsvg" width="100%" height="260" viewBox="0 0 960 260" preserveAspectRatio="none"></svg>
<div class="note">Hover for date &amp; running P&amp;L. Sizing: normal = 1 NQ ($20/pt); de-risked (&gt;40pt stop) = 5 MNQ ($10/pt).</div></div></section>
<section><h2>R-outcome distribution</h2>
<div class="card"><svg id="rrsvg" width="100%" height="200" viewBox="0 0 960 200"></svg>
<div class="note">"stopped" = full stop-out; "4R cap" = target capped at 4R hit; draw exits land in their R bucket.</div></div></section>
<section><h2>Breakdowns — net $ by segment</h2><div class="brkgrid" id="brk"></div></section>
<section><h2>Trade log (click a header to sort)</h2>
<div class="card" style="max-height:520px;overflow:auto"><table id="log"><thead></thead><tbody></tbody></table></div>
<div class="note">Flags: <span class="chip dr">DE-RISK</span> stop &gt; 40pt → 5 MNQ · <span class="chip cb">COUNTER</span> counter-bias (high-execution bar only) · padded stops marked °(stop padded to 20pt from a tighter wick).</div></section>
<div class="tt" id="tt"></div>
<script>
const DATA = __DATA__;
const $ = s => document.querySelector(s);
const fmt$ = v => (v<0?"-$":"+$")+Math.abs(v).toLocaleString();
// tiles
const H = DATA.head;
const tiles = [["Trades",H.trades],["Win rate",H.win+"%"],["Avg R",H.avgR],["Total R",H.totR],
 ["P&L (pts)",H.pts.toLocaleString()],["P&L ($)",fmt$(H.dollars),H.dollars],["Profit factor",H.pf],
 ["Max drawdown",fmt$(H.dd),H.dd],["Best streak",H.ws+"W"],["Worst streak",H.ls+"L"]];
$("#tiles").innerHTML = tiles.map(t=>`<div class="tile"><div class="k">${t[0]}</div>
 <div class="v ${t.length>2?(t[2]>=0?"pos":"neg"):""}">${t[1]}</div></div>`).join("");
$("#sub").textContent = `${DATA.log[0].day} → ${DATA.log[DATA.log.length-1].day} · windows 08:00–09:30 & 09:40–10:15 ET (max 2+2/day) · every trade bias-governed · stops 15(pad20)/70, >40pt de-risked · targets: nearest HTF draw, 4R cap`;
// equity curve (single series -> no legend)
(function(){
 const E=DATA.eq, W=960, Hh=260, P={l:56,r:10,t:10,b:22};
 const xs=i=>P.l+(W-P.l-P.r)*i/Math.max(1,E.length-1);
 const vs=E.map(p=>p.v), mn=Math.min(0,...vs), mx=Math.max(0,...vs);
 const ys=v=>P.t+(Hh-P.t-P.b)*(1-(v-mn)/(mx-mn||1));
 let g='<g class="grid">';
 for(let k=0;k<=4;k++){const v=mn+(mx-mn)*k/4,y=ys(v);
  g+=`<line x1="${P.l}" x2="${W-P.r}" y1="${y}" y2="${y}"/><text x="${P.l-6}" y="${y+4}" text-anchor="end">${Math.round(v/1000)}k</text>`;}
 g+='</g>';
 const path=E.map((p,i)=>(i?'L':'M')+xs(i).toFixed(1)+','+ys(p.v).toFixed(1)).join('');
 const zero=`<line x1="${P.l}" x2="${W-P.r}" y1="${ys(0)}" y2="${ys(0)}" stroke="var(--text-muted)" stroke-width="1" stroke-dasharray="3,3"/>`;
 $("#eqsvg").innerHTML=g+zero+`<path d="${path}" fill="none" stroke="var(--series-1)" stroke-width="2"/>`+
  `<line id="ch" y1="${P.t}" y2="${Hh-P.b}" stroke="var(--text-muted)" stroke-width="1" style="display:none"/>`+
  `<circle id="cp" r="4" fill="var(--series-1)" style="display:none"/>`;
 const svg=$("#eqsvg"), tt=$("#tt");
 svg.addEventListener("mousemove",ev=>{
  const r=svg.getBoundingClientRect(), fx=(ev.clientX-r.left)/r.width*W;
  const i=Math.max(0,Math.min(E.length-1,Math.round((fx-P.l)/(W-P.l-P.r)*(E.length-1))));
  const p=E[i]; $("#ch").setAttribute("x1",xs(i));$("#ch").setAttribute("x2",xs(i));$("#ch").style.display="";
  const cp=$("#cp");cp.setAttribute("cx",xs(i));cp.setAttribute("cy",ys(p.v));cp.style.display="";
  tt.style.display="block";tt.style.left=(ev.clientX+14)+"px";tt.style.top=(ev.clientY-10)+"px";
  tt.innerHTML=`<b>${p.d}</b> · trade #${i+1}<br>cum ${fmt$(p.v)}`;});
 svg.addEventListener("mouseleave",()=>{tt.style.display="none";$("#ch").style.display="none";$("#cp").style.display="none";});
})();
// RR distribution (counts -> single hue, direct labels)
(function(){
 const R=DATA.rr,W=960,Hh=200,P={l:46,r:10,t:14,b:26},n=R.length;
 const mx=Math.max(...R.map(d=>d.n))||1, bw=(W-P.l-P.r)/n;
 let s='';
 R.forEach((d,i)=>{const h=(Hh-P.t-P.b)*d.n/mx, x=P.l+i*bw+3, y=Hh-P.b-h;
  s+=`<rect x="${x}" y="${y}" width="${bw-6}" height="${h}" rx="4" fill="var(--series-1)" data-i="${i}"/>`;
  s+=`<text x="${x+(bw-6)/2}" y="${y-4}" text-anchor="middle">${d.n}</text>`;
  s+=`<text x="${x+(bw-6)/2}" y="${Hh-8}" text-anchor="middle">${d.b}</text>`;});
 $("#rrsvg").innerHTML=`<line class="axis" x1="${P.l}" x2="${W-P.r}" y1="${Hh-P.b}" y2="${Hh-P.b}"/>`+s;
 const tt=$("#tt");
 $("#rrsvg").addEventListener("mousemove",ev=>{const t=ev.target;
  if(t.tagName!=="rect"){tt.style.display="none";return;}
  const d=R[+t.dataset.i];tt.style.display="block";tt.style.left=(ev.clientX+14)+"px";tt.style.top=(ev.clientY-10)+"px";
  tt.innerHTML=`<b>${d.b}</b><br>${d.n} trades (${(100*d.n/DATA.head.trades).toFixed(1)}%)`;});
 $("#rrsvg").addEventListener("mouseleave",()=>tt.style.display="none");
})();
// breakdowns: horizontal net-$ bars, single hue, labels carry identity
(function(){
 const B=DATA.brk, wrap=$("#brk");
 for(const [name,rows] of Object.entries(B)){
  const mx=Math.max(...rows.map(r=>Math.abs(r.dollars)))||1;
  let html=`<div class="card"><h2>${name}</h2><table><thead><tr>
   <th class="l">segment</th><th>n</th><th>win%</th><th>avg R</th><th>PF</th><th>net $</th><th class="l" style="width:130px"></th></tr></thead><tbody>`;
  rows.forEach(r=>{const w=Math.round(60*Math.abs(r.dollars)/mx);
   html+=`<tr><td class="l">${r.k}</td><td>${r.n}</td><td>${r.win}</td><td>${r.avgR}</td><td>${r.pf}</td>
   <td class="${r.dollars>=0?'pos':'neg'}">${fmt$(r.dollars)}</td>
   <td class="l"><span style="display:inline-block;height:10px;border-radius:4px;width:${w}%;min-width:2px;
    background:${r.dollars>=0?'var(--series-1)':'var(--neg)'}"></span></td></tr>`;});
  wrap.innerHTML+=html+"</tbody></table></div>";
 }
})();
// trade log
(function(){
 const cols=[["day","date"],["fill","fill"],["window","window"],["bias","bias"],["conviction","conv."],
  ["dir","dir"],["entry","entry"],["stop_dist","stop"],["target_kind","target"],["reason","exit"],
  ["R","R"],["dollars","$"],["flags","flags"]];
 const th=$("#log thead"), tb=$("#log tbody");
 th.innerHTML="<tr>"+cols.map(c=>`<th class="${['day','fill','window','bias','conviction','dir','target_kind','reason','flags'].includes(c[0])?'l':''}" data-k="${c[0]}">${c[1]}</th>`).join("")+"</tr>";
 let rows=DATA.log.slice(), asc=false, key="day";
 function render(){
  tb.innerHTML=rows.map(r=>{
   const flags=(r.derisk?'<span class="chip dr">DE-RISK</span> ':'')+(r.counter?'<span class="chip cb">COUNTER</span>':'');
   return `<tr><td class="l">${r.day}</td><td class="l">${r.fill}</td><td class="l">${r.window}</td>
   <td class="l">${r.bias}</td><td class="l">${r.conviction}</td><td class="l">${r.dir}</td>
   <td>${r.entry}</td><td>${r.stop_dist}${r.padded?"°":""}</td><td class="l">${r.target_kind}</td>
   <td class="l">${r.reason}</td><td class="${r.R>=0?'pos':'neg'}">${r.R.toFixed(2)}</td>
   <td class="${r.dollars>=0?'pos':'neg'}">${fmt$(Math.round(r.dollars))}</td><td class="l">${flags}</td></tr>`;}).join("");
 }
 th.addEventListener("click",ev=>{const k=ev.target.dataset.k;if(!k||k==="flags")return;
  asc=(key===k)?!asc:false;key=k;
  rows.sort((a,b)=>{const x=a[k],y=b[k];return (x>y?1:x<y?-1:0)*(asc?1:-1);});render();});
 render();
})();
</script></body></html>"""

out = f"{S}/campion_v11_bias_dashboard.html"
open(out, "w").write(HTML.replace("__DATA__", DATA))
print(f"dashboard written: {out}  trades={len(J)}")
