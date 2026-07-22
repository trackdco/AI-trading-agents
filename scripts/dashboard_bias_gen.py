#!/usr/bin/env python3
"""Bias-accuracy dashboard (Jul 2025 -> Jul 2026): reads bias_accuracy_days.csv +
bias_learning_log.csv -> self-contained HTML (light+dark, validated palette)."""
import json

import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
J = pd.read_csv(f"{S}/bias_accuracy_days.csv", dtype={"day": str})
L = pd.read_csv(f"{S}/bias_learning_log.csv") if pd.io.common.file_exists(f"{S}/bias_learning_log.csv") else pd.DataFrame()
J["mo"] = J.day.str.slice(0, 7)

def acc(x, col="verdict"):
    return round(100 * (x[col] == "CORRECT").mean(), 1) if len(x) else 0.0

D = J[J.bias != "NEUTRAL"]
head = dict(days=len(J), b=int((J.bias == "BULLISH").sum()), s=int((J.bias == "BEARISH").sum()),
            n=int((J.bias == "NEUTRAL").sum()),
            acc8=acc(J, "verdict8"), acc9=acc(J), accA=acc(J, "verdict_adapted"),
            accDir=acc(D), accDirA=acc(D, "verdict_adapted"),
            h1r=acc(J.iloc[:len(J)//2]), h1a=acc(J.iloc[:len(J)//2], "verdict_adapted"),
            h2r=acc(J.iloc[len(J)//2:]), h2a=acc(J.iloc[len(J)//2:], "verdict_adapted"))

monthly = [dict(mo=mo, raw=acc(g), ad=acc(g, "verdict_adapted"), n=len(g))
           for mo, g in J.groupby("mo")]

per_bias = []
for b in ["BULLISH", "BEARISH", "NEUTRAL"]:
    x = J[J.bias == b]
    if not len(x):
        continue
    per_bias.append(dict(b=b, n=len(x), correct=int((x.verdict == "CORRECT").sum()),
                         wrong=int((x.verdict == "WRONG").sum()), flat=int((x.verdict == "FLAT").sum()),
                         acc=acc(x)))

J["out3"] = J.apply(lambda r: "up" if r.net > 0 else "down", axis=1)
# strict flat via verdict logic: recompute using pct band ~0.1% -> use abs(net_pct)<=0.1
J.loc[J.net_pct.abs() <= 0.1, "out3"] = "flat"
conf = [{"bias": b, "up": int(((J.bias == b) & (J.out3 == "up")).sum()),
         "flat": int(((J.bias == b) & (J.out3 == "flat")).sum()),
         "down": int(((J.bias == b) & (J.out3 == "down")).sum())}
        for b in ["BULLISH", "BEARISH", "NEUTRAL"]]

conv = [dict(t=t, n=len(g), acc=acc(g)) for t, g in D.groupby("tier")]
learn = L.to_dict("records") if len(L) else []
log_cols = ["day", "weekday", "bias8", "bias", "tier", "adapted", "policy", "net", "net_pct",
            "verdict", "verdict_adapted", "news", "note"]
log = J[log_cols].fillna("").to_dict("records")

DATA = json.dumps(dict(head=head, monthly=monthly, per_bias=per_bias, conf=conf,
                       conv=conv, learn=learn, log=log), separators=(",", ":"))

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HTF Bias Accuracy — Jul 2025 → Jul 2026</title>
<style>
.viz-root{color-scheme:light;
 --surface-1:#fcfcfb;--surface-2:#f1f0ee;--border:#dedcd7;
 --text-primary:#0b0b0b;--text-secondary:#52514e;--text-muted:#8a887f;
 --series-1:#2a78d6;--series-2:#eb6834;--pos:#008300;--neg:#e34948;
 --warn-bg:#fdf3d8;--warn-tx:#7a5b00;
 font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--surface-1);
 color:var(--text-primary);margin:0;padding:24px;line-height:1.45}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;
 --surface-1:#1a1a19;--surface-2:#242423;--border:#3a3936;
 --text-primary:#ffffff;--text-secondary:#c3c2b7;--text-muted:#8a887f;
 --series-1:#3987e5;--series-2:#d95926;--pos:#4caf50;--neg:#e66767;
 --warn-bg:#3a2f10;--warn-tx:#e8c96a}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;
 --surface-1:#1a1a19;--surface-2:#242423;--border:#3a3936;
 --text-primary:#ffffff;--text-secondary:#c3c2b7;--text-muted:#8a887f;
 --series-1:#3987e5;--series-2:#d95926;--pos:#4caf50;--neg:#e66767;
 --warn-bg:#3a2f10;--warn-tx:#e8c96a}
h1{font-size:20px;margin:0 0 4px}.sub{color:var(--text-secondary);font-size:13px;margin-bottom:18px;max-width:1050px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:24px}
.tile{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:10px 12px}
.tile .k{font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.04em}
.tile .v{font-size:20px;font-weight:650;margin-top:2px}
section{margin-bottom:26px}h2{font-size:14px;color:var(--text-secondary);font-weight:600;margin:0 0 8px}
.card{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:14px;overflow-x:auto}
svg text{fill:var(--text-secondary);font-size:11px}.grid line{stroke:var(--border)}
.tt{position:fixed;pointer-events:none;background:var(--surface-1);border:1px solid var(--border);
 border-radius:6px;padding:6px 9px;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,.18);display:none;z-index:9}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{padding:5px 8px;text-align:right;border-bottom:1px solid var(--border);white-space:nowrap;vertical-align:top}
th:first-child,td:first-child,th.l,td.l{text-align:left}
th{cursor:pointer;color:var(--text-secondary);position:sticky;top:0;background:var(--surface-2)}
tr:hover td{background:color-mix(in srgb,var(--series-1) 7%,transparent)}
td.note{white-space:normal;min-width:320px;max-width:560px;text-align:left;color:var(--text-secondary)}
.chip{display:inline-block;border-radius:5px;padding:1px 7px;font-size:11px;font-weight:600}
.ok{background:color-mix(in srgb,var(--pos) 16%,transparent);color:var(--pos)}
.bad{background:color-mix(in srgb,var(--neg) 15%,transparent);color:var(--neg)}
.fl{background:var(--surface-1);color:var(--text-muted);border:1px solid var(--border)}
.pol{background:var(--warn-bg);color:var(--warn-tx)}
.legend{font-size:12px;color:var(--text-secondary);margin-bottom:6px}
.legend .sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin:0 4px 0 12px;vertical-align:-1px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.note2{font-size:12px;color:var(--text-muted);margin-top:6px}
.bar{height:10px;border-radius:4px;display:inline-block;min-width:2px;vertical-align:middle}
</style></head><body class="viz-root">
<h1>HTF Bias Accuracy Study — NQ, Jul 2025 → Jul 2026 (no trading, grading the read)</h1>
<div class="sub">Primary read = the <b>09:30 open checkpoint</b> (the bias in force when the NY session trades). Grade: <b>CORRECT only if the NY session (09:30→16:00) follows the bias</b> — net move beyond ±0.10% of the open; BULLISH needs an up session, BEARISH a down session; NEUTRAL is correct only if the session truly closed flat (±0.10%). A NEUTRAL read on a trending day is graded as a missed day. The <b>adapted</b> column is the walk-forward learner: each bias×conviction cell is kept, faded, or dropped based on its own trailing 60-day record — decided only from days already seen (no lookahead).</div>
<div class="tiles" id="tiles"></div>
<section><h2>Monthly accuracy — raw 09:30 read vs adapted (learned) read</h2>
<div class="card"><div class="legend">series:<span class="sw" style="background:var(--series-1)"></span>raw<span class="sw" style="background:var(--series-2)"></span>adapted</div>
<svg id="mo" width="100%" height="240" viewBox="0 0 960 240"></svg>
<div class="note2">50% line marked. Hover for values. The learner's edge grows as history accumulates — compare halves in the tiles.</div></div></section>
<section><h2>Per-bias outcomes (09:30 read)</h2><div class="grid3" id="pb"></div></section>
<section class="grid3" style="display:grid;gap:14px">
<div class="card"><h2>Confusion — read vs what the NY session did</h2><table id="cf"></table>
<div class="note2">"flat" = |net| ≤ 0.10%. NQ closes flat only ~8% of days — which is why NEUTRAL's strict accuracy is low; in trading terms NEUTRAL = stand-aside, its cost is missed days, not losses.</div></div>
<div class="card"><h2>Accuracy by conviction (directional reads)</h2><table id="cv"></table></div>
<div class="card"><h2>What the learner decided (walk-forward)</h2><table id="ln"></table>
<div class="note2">keep = trust the cell · flip = fade it (its trailing record favored the opposite) · drop = ignore to NEUTRAL. Decisions use only prior days.</div></div>
</section>
<section><h2>Every day — read, outcome, and what happened (sortable)</h2>
<div class="card" style="max-height:560px;overflow:auto"><table id="log"><thead></thead><tbody></tbody></table></div></section>
<div class="tt" id="tt"></div>
<script>
const DATA=__DATA__;const $=s=>document.querySelector(s);const H=DATA.head;
$("#tiles").innerHTML=[["Days graded",H.days],["Mix B / S / N",H.b+" / "+H.s+" / "+H.n],
 ["08:00 read acc",H.acc8+"%"],["09:30 read acc",H.acc9+"%"],["Adapted acc",H.accA+"%"],
 ["Directional-only",H.accDir+"% → "+H.accDirA+"%"],
 ["1st half raw→adapted",H.h1r+"% → "+H.h1a+"%"],["2nd half raw→adapted",H.h2r+"% → "+H.h2a+"%"]]
 .map(t=>`<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div></div>`).join("");
// monthly 2-series line
(function(){const M=DATA.monthly,W=960,Hh=240,P={l:44,r:10,t:12,b:26};
 const xs=i=>P.l+(W-P.l-P.r)*i/Math.max(1,M.length-1);const ys=v=>P.t+(Hh-P.t-P.b)*(1-v/100);
 let g='<g class="grid">';for(const v of [0,25,50,75,100]){g+=`<line x1="${P.l}" x2="${W-P.r}" y1="${ys(v)}" y2="${ys(v)}"${v===50?' stroke-dasharray="4,3"':''}/><text x="${P.l-6}" y="${ys(v)+4}" text-anchor="end">${v}</text>`;}g+='</g>';
 const path=(k,c)=>`<path fill="none" stroke="var(${c})" stroke-width="2" d="${M.map((m,i)=>(i?'L':'M')+xs(i)+','+ys(m[k])).join('')}"/>`;
 const dots=(k,c)=>M.map((m,i)=>`<circle cx="${xs(i)}" cy="${ys(m[k])}" r="4" fill="var(${c})" data-i="${i}"/>`).join('');
 const lbls=M.map((m,i)=>`<text x="${xs(i)}" y="${Hh-8}" text-anchor="middle">${m.mo.slice(2)}</text>`).join('');
 $("#mo").innerHTML=g+path("raw","--series-1")+path("ad","--series-2")+dots("raw","--series-1")+dots("ad","--series-2")+lbls;
 const tt=$("#tt");$("#mo").addEventListener("mousemove",ev=>{const t=ev.target;
  if(t.tagName!=="circle"){tt.style.display="none";return;}const m=DATA.monthly[+t.dataset.i];
  tt.style.display="block";tt.style.left=(ev.clientX+14)+"px";tt.style.top=(ev.clientY-10)+"px";
  tt.innerHTML=`<b>${m.mo}</b> (${m.n}d)<br>raw ${m.raw}% · adapted ${m.ad}%`;});
 $("#mo").addEventListener("mouseleave",()=>tt.style.display="none");})();
// per-bias cards
(function(){const w=$("#pb");for(const p of DATA.per_bias){
 const mx=Math.max(p.correct,p.wrong,p.flat)||1;
 const row=(lab,v,color)=>`<tr><td class="l">${lab}</td><td>${v}</td>
  <td class="l" style="width:120px"><span class="bar" style="width:${Math.round(90*v/mx)}%;background:${color}"></span></td></tr>`;
 w.innerHTML+=`<div class="card"><h2>${p.b} — ${p.n} days · ${p.acc}% correct</h2><table>
  ${row("correct",p.correct,"var(--series-1)")}${row("wrong",p.wrong,"var(--neg)")}${row("flat day",p.flat,"var(--text-muted)")}</table></div>`;}})();
// confusion
(function(){const C=DATA.conf;
 $("#cf").innerHTML="<tr><th class='l'>read ↓ / session →</th><th>up</th><th>flat</th><th>down</th></tr>"+
 C.map(r=>`<tr><td class="l">${r.bias}</td><td>${r.up}</td><td>${r.flat}</td><td>${r.down}</td></tr>`).join("");})();
// conviction
(function(){$("#cv").innerHTML="<tr><th class='l'>conviction</th><th>days</th><th>correct</th></tr>"+
 DATA.conv.map(c=>`<tr><td class="l">${c.t}</td><td>${c.n}</td><td>${c.acc}%</td></tr>`).join("");})();
// learning log
(function(){const L=DATA.learn;$("#ln").innerHTML="<tr><th class='l'>from day</th><th class='l'>cell</th><th class='l'>decision</th><th>keep acc</th><th>flip acc</th><th>n</th></tr>"+
 (L.length?L.map(l=>`<tr><td class="l">${l.day}</td><td class="l">${l.cell}</td><td class="l"><span class="chip pol">${l.policy}</span></td><td>${l.keep_acc}%</td><td>${l.flip_acc}%</td><td>${l.n}</td></tr>`).join(""):"<tr><td class='l'>no decisions yet</td></tr>");})();
// day log
(function(){const cols=[["day","date"],["weekday","day"],["bias8","08:00"],["bias","09:30"],["tier","conv."],
 ["adapted","adapted"],["net","NY net"],["verdict","verdict"],["verdict_adapted","adapted verdict"],["note","what happened"]];
 const th=$("#log thead"),tb=$("#log tbody");
 th.innerHTML="<tr>"+cols.map(c=>`<th class="${['day','weekday','bias8','bias','tier','adapted','note'].includes(c[0])?'l':''}" data-k="${c[0]}">${c[1]}</th>`).join("")+"</tr>";
 const chip=v=>v==="CORRECT"?'<span class="chip ok">CORRECT</span>':v==="WRONG"?'<span class="chip bad">WRONG</span>':'<span class="chip fl">FLAT</span>';
 let rows=DATA.log.slice(),asc=false,key="day";
 function render(){tb.innerHTML=rows.map(r=>`<tr><td class="l">${r.day}</td><td class="l">${r.weekday.slice(0,3)}</td>
  <td class="l">${r.bias8}</td><td class="l"><b>${r.bias}</b></td><td class="l">${r.tier}</td>
  <td class="l">${r.adapted}${r.policy&&r.policy!=="keep"?' <span class="chip pol">'+r.policy+'</span>':''}</td>
  <td class="${r.net>=0?'':' '}" style="color:${r.net>=0?'var(--pos)':'var(--neg)'}">${r.net>0?'+':''}${r.net}</td>
  <td>${chip(r.verdict)}</td><td>${chip(r.verdict_adapted)}</td><td class="note">${r.note}${r.news?' 📰':''}</td></tr>`).join("");}
 th.addEventListener("click",ev=>{const k=ev.target.dataset.k;if(!k)return;asc=(key===k)?!asc:false;key=k;
  rows.sort((a,b)=>{const x=a[k],y=b[k];return (x>y?1:x<y?-1:0)*(asc?1:-1);});render();});
 render();})();
</script></body></html>"""

out = f"{S}/bias_accuracy_dashboard.html"
open(out, "w").write(HTML.replace("__DATA__", DATA))
print("written", out)
