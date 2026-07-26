#!/usr/bin/env python3
"""ICT weekly-bias accuracy dashboard -> Artifact-format HTML (no wrapper tags)."""
import json
import pandas as pd

import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
J = pd.read_csv(f"{S}/ict_bias_v2_days.csv", dtype={"day": str})
J["mo"] = J.day.str.slice(0, 7)
D = J[J.bias != "NEUTRAL"].copy()

def acc(x, col="verdict"):
    return round(100 * (x[col] == "CORRECT").mean(), 1) if len(x) else 0.0
def exp(x):
    return round(100 * x.expansion_ok.mean(), 1) if len(x) else 0.0

head = dict(days=len(J), dirn=len(D), aside=len(J) - len(D),
            strict=acc(D), expn=exp(D),
            hi=acc(D[D.conviction == "HIGH"]), hiE=exp(D[D.conviction == "HIGH"]),
            med=acc(D[D.conviction == "MEDIUM"]),
            wk=J.weekly.value_counts().to_dict())

weekday = [dict(d=wd, n=int((D.weekday == wd).sum()), acc=acc(D[D.weekday == wd]),
                exp=exp(D[D.weekday == wd])) for wd in ["Mon", "Tue", "Wed", "Thu", "Fri"]]
conv = [dict(c=c, n=int((D.conviction == c).sum()), acc=acc(D[D.conviction == c]),
             exp=exp(D[D.conviction == c])) for c in ["HIGH", "MEDIUM"]]
monthly = [dict(mo=mo, n=len(g), acc=acc(g), exp=exp(g)) for mo, g in D.groupby("mo")]
per_bias = []
for b in ["BULLISH", "BEARISH"]:
    x = D[D.bias == b]
    if len(x):
        per_bias.append(dict(b=b, n=len(x), correct=int((x.verdict == "CORRECT").sum()),
                             wrong=int((x.verdict == "WRONG").sum()), flat=int((x.verdict == "FLAT").sum()),
                             acc=acc(x)))
newsq = [dict(k="red-folder days", n=int(D.newsday.sum()), acc=acc(D[D.newsday])),
         dict(k="quiet days", n=int((~D.newsday).sum()), acc=acc(D[~D.newsday]))]
log = J[["day", "weekday", "weekly", "bias", "conviction", "net", "verdict", "expansion_ok",
         "newsday", "reason", "note"]].to_dict("records")

DATA = json.dumps(dict(head=head, weekday=weekday, conv=conv, monthly=monthly,
                       per_bias=per_bias, newsq=newsq, log=log), separators=(",", ":"))

CSS = """<style>
:root{color-scheme:light;
 --bg:#f6f7f9;--surface-1:#ffffff;--surface-2:#fbfcfd;--border:#e5e8ee;
 --text-primary:#13161c;--text-secondary:#5b6472;--text-muted:#939aa8;
 --series-1:#2a78d6;--series-2:#eb6834;--pos:#0a7d33;--neg:#d63c3c;--warn-bg:#fdf3d8;--warn-tx:#7a5b00;
 --mono:ui-monospace,"SF Mono",Menlo,"Cascadia Code",Consolas,monospace;
 --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;
 --bg:#111318;--surface-1:#1a1d24;--surface-2:#20242c;--border:#333944;
 --text-primary:#eef1f6;--text-secondary:#a7b0be;--text-muted:#727b8a;
 --series-1:#3987e5;--series-2:#e0703c;--pos:#3fb862;--neg:#ec6a6a;--warn-bg:#3a2f10;--warn-tx:#e8c96a}}
:root[data-theme="dark"]{color-scheme:dark;
 --bg:#111318;--surface-1:#1a1d24;--surface-2:#20242c;--border:#333944;
 --text-primary:#eef1f6;--text-secondary:#a7b0be;--text-muted:#727b8a;
 --series-1:#3987e5;--series-2:#e0703c;--pos:#3fb862;--neg:#ec6a6a;--warn-bg:#3a2f10;--warn-tx:#e8c96a}
:root[data-theme="light"]{color-scheme:light;
 --bg:#f6f7f9;--surface-1:#ffffff;--surface-2:#fbfcfd;--border:#e5e8ee;
 --text-primary:#13161c;--text-secondary:#5b6472;--text-muted:#939aa8;
 --series-1:#2a78d6;--series-2:#eb6834;--pos:#0a7d33;--neg:#d63c3c;--warn-bg:#fdf3d8;--warn-tx:#7a5b00}
*{box-sizing:border-box}
body{font-family:var(--sans);background:var(--bg);color:var(--text-primary);margin:0;
 padding:clamp(16px,3vw,32px);line-height:1.5;font-variant-numeric:tabular-nums;max-width:1180px;margin-inline:auto}
h1{font-size:clamp(19px,3vw,23px);margin:0 0 4px;letter-spacing:-.01em;text-wrap:balance}
.sub{color:var(--text-secondary);font-size:13px;margin-bottom:20px;max-width:900px}
.sub b{color:var(--text-primary)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:26px}
.tile{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.tile .k{font-size:10.5px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em;font-weight:600}
.tile .v{font-size:22px;font-weight:650;margin-top:3px;font-family:var(--mono);letter-spacing:-.02em}
.tile .s{font-size:11px;color:var(--text-secondary);margin-top:1px}
.big{grid-column:span 2}
section{margin-bottom:26px}h2{font-size:14px;color:var(--text-secondary);font-weight:600;margin:0 0 8px}
.card{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:16px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}
svg text{fill:var(--text-secondary);font-size:11px;font-family:var(--mono)}
.grid line{stroke:var(--border)}
table{border-collapse:collapse;width:100%;font-size:12.5px;font-family:var(--mono)}
th,td{padding:6px 9px;text-align:right;border-bottom:1px solid var(--border);white-space:nowrap;vertical-align:top}
th:first-child,td:first-child,th.l,td.l{text-align:left}
th{cursor:pointer;color:var(--text-secondary);position:sticky;top:0;background:var(--surface-1);
 font-family:var(--sans);font-size:11px;letter-spacing:.03em;text-transform:uppercase}
tr:hover td{background:color-mix(in srgb,var(--series-1) 6%,transparent)}
td.note{white-space:normal;min-width:300px;max-width:540px;text-align:left;color:var(--text-secondary)}
.chip{display:inline-block;border-radius:5px;padding:1px 7px;font-size:11px;font-weight:600;font-family:var(--mono)}
.ok{background:color-mix(in srgb,var(--pos) 16%,transparent);color:var(--pos)}
.bad{background:color-mix(in srgb,var(--neg) 15%,transparent);color:var(--neg)}
.fl,.na{background:var(--surface-2);color:var(--text-muted);border:1px solid var(--border)}
.bull{color:var(--pos);font-weight:600}.bear{color:var(--neg);font-weight:600}.neu{color:var(--text-muted)}
.bar{height:11px;border-radius:4px;display:inline-block;min-width:2px;vertical-align:middle}
.note2{font-size:12px;color:var(--text-muted);margin-top:8px}
.legend{font-size:12px;color:var(--text-secondary);margin-bottom:8px}
.legend .sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin:0 4px 0 12px;vertical-align:-1px}
.tt{position:fixed;pointer-events:none;background:var(--surface-1);border:1px solid var(--border);
 border-radius:6px;padding:6px 9px;font-size:12px;box-shadow:0 3px 10px rgba(0,0,0,.2);display:none;z-index:9}
:focus-visible{outline:2px solid var(--series-1);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>"""

BODY = """
<h1>ICT Weekly-Bias Accuracy (v2) — NQ, Jul 2025 → Jul 2026</h1>
<div class="sub"><b>Top-down, calendar-driven, never counter-weekly.</b> Weekly bias set from completed weekly candles; the <b>red-folder economic calendar</b> picks which day places the week's low/high (the expansion days); daily bias is the weekly direction on expansion days and <b>NEUTRAL otherwise</b> — no shorts in a bullish week, and no read on quiet accumulation days. Graded on the <b>NY session (09:30→16:00)</b>: <b>strict</b> = session closed in the bias direction (±0.10%); <b>expansion</b> = NY swept against then expanded with the bias (the judas-swing shape you actually trade off a retracement + CISD). <b>v2 upgrades over v1:</b> trend-led weekly bias with a reversal-week veto, sweep-then-reclaim confirmation before calling expansion, and an HTF-array (4H/daily FVG) conviction factor — lifting HIGH-conviction from 50.9%→57.1% strict at the same ~123 directional days.</div>
<div class="tiles" id="tiles"></div>
<section><h2>Accuracy by day of week — testing the Tue/Wed/Thu expansion thesis</h2>
<div class="card"><div class="legend">series:<span class="sw" style="background:var(--series-1)"></span>strict net-close<span class="sw" style="background:var(--series-2)"></span>ICT expansion</div>
<svg id="wd" width="100%" height="230" viewBox="0 0 960 230"></svg>
<div class="note2">50% marked. Thursday & Friday carry the edge; Tuesday — the sweep/reversal day — is the weakest, exactly as ICT warns: the turtle-soup day is lower-probability than a clean expansion day.</div></div></section>
<section class="grid3">
<div class="card"><h2>By conviction</h2><table id="cv"></table><div class="note2">HIGH = expansion day Tue–Thu, low already in. The confidence tier is where the edge lives.</div></div>
<div class="card"><h2>By weekly bias</h2><table id="pb"></table><div class="note2">Weeks classified: bullish/bearish/neutral (neutral weeks → all days stand aside).</div></div>
<div class="card"><h2>News-day vs quiet-day</h2><table id="nq"></table><div class="note2">Directional reads only. The calendar concentrates the reads onto news days.</div></div>
</section>
<section><h2>Monthly — strict vs expansion accuracy (directional days)</h2>
<div class="card"><svg id="mo" width="100%" height="220" viewBox="0 0 960 220"></svg></div></section>
<section><h2>Every day — the read, the call, and what the session did (sortable)</h2>
<div class="card" style="max-height:560px;overflow:auto"><table id="log"><thead></thead><tbody></tbody></table></div>
<div class="note2">verdict is the strict NY-close grade; STAND ASIDE = we intentionally didn't trade (NEUTRAL). ⚡ = NY produced the sweep-then-expand shape. 📰 = red-folder day.</div></section>
<div class="tt" id="tt"></div>
"""

SCRIPT = """<script>
const DATA=__DATA__;const $=s=>document.querySelector(s);const H=DATA.head;
$("#tiles").innerHTML=[
 ["Days examined",H.days,"trading days"],
 ["Directional calls",H.dirn,"the rest stood aside ("+H.aside+")"],
 ["Strict accuracy",H.strict+"%","NY closed with the bias"],
 ["Expansion accuracy",H.expn+"%","swept then expanded"],
 ["HIGH-conviction",H.hi+"% / "+H.hiE+"%","strict / expansion"],
 ["MEDIUM-conviction",H.med+"%","strict"],
 ["Weeks B / S / N",(H.wk.BULLISH||0)+" / "+(H.wk.BEARISH||0)+" / "+(H.wk.NEUTRAL||0),"day-count by weekly bias"],
].map(t=>`<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div><div class="s">${t[2]}</div></div>`).join("");
// weekday grouped bars
(function(){const W=DATA.weekday,Wd=960,Hh=230,P={l:40,r:10,t:14,b:34},n=W.length;
 const gw=(Wd-P.l-P.r)/n, bw=Math.min(34,gw/2-6);const ys=v=>P.t+(Hh-P.t-P.b)*(1-v/100);
 let g='<g class="grid">';for(const v of[0,25,50,75,100]){g+=`<line x1="${P.l}" x2="${Wd-P.r}" y1="${ys(v)}" y2="${ys(v)}"${v===50?' stroke-dasharray="4,3"':''}/><text x="${P.l-6}" y="${ys(v)+4}" text-anchor="end">${v}</text>`;}g+='</g>';
 let s='';W.forEach((d,i)=>{const cx=P.l+i*gw+gw/2;
  const b1=cx-bw-2,b2=cx+2;
  s+=`<rect x="${b1}" y="${ys(d.acc)}" width="${bw}" height="${(Hh-P.t-P.b)-(ys(d.acc)-P.t)}" rx="4" fill="var(--series-1)" data-t="${d.d} strict ${d.acc}% (n=${d.n})"/>`;
  s+=`<rect x="${b2}" y="${ys(d.exp)}" width="${bw}" height="${(Hh-P.t-P.b)-(ys(d.exp)-P.t)}" rx="4" fill="var(--series-2)" data-t="${d.d} expansion ${d.exp}%"/>`;
  s+=`<text x="${cx}" y="${Hh-14}" text-anchor="middle">${d.d}</text><text x="${cx}" y="${Hh-2}" text-anchor="middle" style="fill:var(--text-muted)">n=${d.n}</text>`;});
 $("#wd").innerHTML=g+s;bindtt("#wd");})();
// tables
$("#cv").innerHTML="<tr><th class='l'>conviction</th><th>days</th><th>strict</th><th>expansion</th></tr>"+DATA.conv.map(c=>`<tr><td class="l">${c.c}</td><td>${c.n}</td><td>${c.acc}%</td><td>${c.exp}%</td></tr>`).join("");
$("#pb").innerHTML="<tr><th class='l'>bias</th><th>days</th><th>correct</th><th>wrong</th><th>flat</th></tr>"+DATA.per_bias.map(p=>`<tr><td class="l ${p.b==='BULLISH'?'bull':'bear'}">${p.b}</td><td>${p.n}</td><td>${p.correct}</td><td>${p.wrong}</td><td>${p.flat}</td></tr>`).join("");
$("#nq").innerHTML="<tr><th class='l'>day type</th><th>days</th><th>strict</th></tr>"+DATA.newsq.map(r=>`<tr><td class="l">${r.k}</td><td>${r.n}</td><td>${r.acc}%</td></tr>`).join("");
// monthly 2-line
(function(){const M=DATA.monthly,Wd=960,Hh=220,P={l:40,r:10,t:12,b:26};
 const xs=i=>P.l+(Wd-P.l-P.r)*i/Math.max(1,M.length-1);const ys=v=>P.t+(Hh-P.t-P.b)*(1-v/100);
 let g='<g class="grid">';for(const v of[0,25,50,75,100]){g+=`<line x1="${P.l}" x2="${Wd-P.r}" y1="${ys(v)}" y2="${ys(v)}"${v===50?' stroke-dasharray="4,3"':''}/><text x="${P.l-6}" y="${ys(v)+4}" text-anchor="end">${v}</text>`;}g+='</g>';
 const line=(k,c)=>`<path fill="none" stroke="var(${c})" stroke-width="2" d="${M.map((m,i)=>(i?'L':'M')+xs(i)+','+ys(m[k])).join('')}"/>`;
 const dots=(k,c)=>M.map((m,i)=>`<circle cx="${xs(i)}" cy="${ys(m[k])}" r="3.5" fill="var(${c})" data-t="${m.mo}: strict ${m.acc}% / exp ${m.exp}% (n=${m.n})"/>`).join('');
 const lbl=M.map((m,i)=>`<text x="${xs(i)}" y="${Hh-8}" text-anchor="middle">${m.mo.slice(2)}</text>`).join('');
 $("#mo").innerHTML='<div class="legend"></div>'+g+line("acc","--series-1")+line("exp","--series-2")+dots("acc","--series-1")+dots("exp","--series-2")+lbl;
 bindtt("#mo");})();
// day log
(function(){const cols=[["day","date"],["weekday","dow"],["weekly","weekly"],["bias","bias"],["conviction","conv."],["net","NY net"],["verdict","verdict"],["reason","reasoning"],["note","what happened"]];
 const th=$("#log thead"),tb=$("#log tbody");
 th.innerHTML="<tr>"+cols.map(c=>`<th class="${['day','weekday','weekly','bias','conviction','reason','note'].includes(c[0])?'l':''}" data-k="${c[0]}">${c[1]}</th>`).join("")+"</tr>";
 const bcls=b=>b==='BULLISH'?'bull':b==='BEARISH'?'bear':'neu';
 const vchip=(v,e)=>v==='CORRECT'?'<span class="chip ok">CORRECT'+(e?' ⚡':'')+'</span>':v==='WRONG'?'<span class="chip bad">WRONG</span>':v==='FLAT'?'<span class="chip fl">FLAT</span>':'<span class="chip na">STAND ASIDE</span>';
 let rows=DATA.log.slice(),asc=false,key="day";
 function r(){tb.innerHTML=rows.map(x=>`<tr><td class="l">${x.day}</td><td class="l">${x.weekday}</td>
  <td class="l ${bcls(x.weekly)}">${x.weekly[0]}</td><td class="l ${bcls(x.bias)}">${x.bias}</td><td class="l">${x.conviction}</td>
  <td style="color:${x.net>=0?'var(--pos)':'var(--neg)'}">${x.net>0?'+':''}${x.net}</td>
  <td>${vchip(x.verdict,x.expansion_ok)}</td><td class="l" style="color:var(--text-secondary)">${x.reason}</td>
  <td class="note">${x.note.replace('news:','📰')}</td></tr>`).join("");}
 th.addEventListener("click",e=>{const k=e.target.dataset.k;if(!k)return;asc=(key===k)?!asc:false;key=k;
  rows.sort((a,b)=>{const p=a[k],q=b[k];return(p>q?1:p<q?-1:0)*(asc?1:-1);});r();});
 r();})();
function bindtt(sel){const el=$(sel),tt=$("#tt");el.addEventListener("mousemove",e=>{const t=e.target.dataset.t;
 if(!t){tt.style.display="none";return;}tt.style.display="block";tt.style.left=(e.clientX+14)+"px";tt.style.top=(e.clientY-10)+"px";tt.textContent=t;});
 el.addEventListener("mouseleave",()=>tt.style.display="none");}
</script>"""

out = CSS + BODY + SCRIPT.replace("__DATA__", DATA)
open(f"{S}/ict_bias_artifact.html", "w").write(out)
for bad in ["<!doctype", "<html", "<head", "<body", "</html"]:
    assert bad not in out.lower(), bad
print("written ict_bias_artifact.html", len(out), "bytes")
