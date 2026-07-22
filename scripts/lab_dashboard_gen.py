#!/usr/bin/env python3
"""Bias-Lab dashboard: concept screen + walk-forward ensemble result -> Artifact HTML."""
import json
import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
R = pd.read_csv(f"{S}/bias_lab_concepts.csv")
lab = json.load(open(f"{S}/_lab.json")); OUT = np.array(lab["out"]); is_train = np.array(lab["is_train"])
jr = json.load(open(f"{S}/ensemble_journal.json"))
ED = pd.read_csv(f"{S}/ensemble_days.csv")

base_tr = round(100 * (OUT[is_train] == 1).mean(), 1)
base_te = round(100 * (OUT[~is_train] == 1).mean(), 1)
def ens_acc(mask):
    p = ED.ens.values; fire = (p != 0) & mask
    return round(100 * ((p == OUT) & fire).sum() / fire.sum(), 1) if fire.sum() else 0
ens_all = ens_acc(np.ones(len(OUT), bool)); ens_te = ens_acc(~is_train)
best_te = R.sort_values("test_acc", ascending=False).iloc[0]

concepts = R.sort_values("test_edge", ascending=False).to_dict("records")
scatter = R[["concept", "train_acc", "test_acc"]].to_dict("records")
journal = jr[-10:]
DATA = json.dumps(dict(
    base_tr=base_tr, base_te=base_te, ens_all=ens_all, ens_te=ens_te,
    best=dict(c=best_te.concept, a=best_te.test_acc), n_concepts=len(R),
    concepts=concepts, scatter=scatter, journal=journal), separators=(",", ":"))

CSS = open(f"{S}/_css_block.txt").read().replace('CSS = """', "").rstrip('"')
BODY = """
<h1>Bias Lab — can any concept predict NQ daily direction? (2023 → 2026)</h1>
<div class="sub"><b>The honest screen.</b> {N} daily-bias concepts — ICT (session profiles, sweeps, judas, weekly bias), indicators (RSI, MACD, Bollinger, VWAP), momentum, seasonality, VIX regime, order-flow proxy — each a no-lookahead signal graded on whether the <b>NY session (09:30→16:00)</b> followed it. Split <b>TRAIN 2023–24</b> vs <b>TEST 2025–26</b>; edge = accuracy − base rate (P(up)). Plus a <b>walk-forward learning ensemble</b> that trusts/fades each concept by its own trailing record. Everything reproducible; the lookahead bug that made VIX look 70% (it collapsed to −7% once lagged) is the reason this is done as a strict screen, not a highlight reel.</div>
<div class="tiles" id="tiles"></div>
<section><h2>Every concept, ranked by out-of-sample edge over base rate</h2>
<div class="card"><svg id="rank" width="100%" height="520" viewBox="0 0 960 520"></svg>
<div class="note2">Zero line = base rate (predict-up). <b>Not one concept clears it by a meaningful margin out-of-sample.</b> The best (momentum_5d) is +0.5 — statistical zero.</div></div></section>
<section class="grid3">
<div class="card" style="grid-column:span 2"><h2>Train vs test accuracy — does any edge persist?</h2>
<svg id="sc" width="100%" height="300" viewBox="0 0 620 300"></svg>
<div class="note2">If concepts had real edge, points would sit top-right and hug the diagonal. They scatter around the base rate with no train→test persistence — the definition of noise.</div></div>
<div class="card"><h2>Verdict</h2><table id="vd"></table><div class="note2">The learning ensemble did WORSE than a coin flip — it chases recent winners that then reverse.</div></div>
</section>
<section><h2>Why the learner fails — trusted/faded concepts flip month to month</h2>
<div class="card" style="max-height:420px;overflow:auto"><table id="jr"></table>
<div class="note2">A concept trusted (≥55%) one month is faded (≤45%) a few months later, repeatedly. The "edge" is non-stationary — so reusing what recently worked is whipsaw, not learning.</div></div></section>
<section><h2>Full concept table (sortable)</h2>
<div class="card" style="max-height:480px;overflow:auto"><table id="tbl"><thead></thead><tbody></tbody></table></div></section>
<div class="tt" id="tt"></div>
"""
SCRIPT = """<script>
const DATA=__DATA__;const $=s=>document.querySelector(s);
$("#tiles").innerHTML=[
 ["Concepts screened",DATA.n_concepts,"no-lookahead"],
 ["Base rate (test)",DATA.base_te+"%","P(NY up) 2025-26"],
 ["Best concept OOS",DATA.best.a+"%",DATA.best.c],
 ["Best OOS edge","+0.5 pts","over base rate"],
 ["Learning ensemble",DATA.ens_te+"%","test — below coin flip"],
 ["Verdict","NO EDGE","daily direction ~unpredictable"],
].map(t=>`<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div><div class="s">${t[2]}</div></div>`).join("");
// ranked horizontal bars of test_edge
(function(){const C=DATA.concepts,W=960,rowH=19,P={l:150,r:30,t:6},H=C.length*rowH+P.t+10;
 const mx=Math.max(5,...C.map(c=>Math.abs(c.test_edge)));const x0=P.l+(W-P.l-P.r)*0.5;
 const sx=v=>x0+(W-P.l-P.r)*0.5*v/mx;
 let s=`<line x1="${x0}" x2="${x0}" y1="${P.t}" y2="${H-10}" stroke="var(--text-muted)" stroke-dasharray="3,3"/>`;
 C.forEach((c,i)=>{const y=P.t+i*rowH+rowH/2;const pos=c.test_edge>=0;const xe=sx(c.test_edge);
  s+=`<text x="${P.l-8}" y="${y+3}" text-anchor="end" style="font-size:10.5px">${c.concept}</text>`;
  s+=`<rect x="${pos?x0:xe}" y="${y-6}" width="${Math.abs(xe-x0)}" height="12" rx="3" fill="${pos?'var(--series-1)':'var(--neg)'}" data-t="${c.concept}: test ${c.test_acc}% (edge ${c.test_edge>0?'+':''}${c.test_edge}), train ${c.train_acc}%"/>`;
  s+=`<text x="${(pos?xe:xe)+(pos?4:-4)}" y="${y+3}" text-anchor="${pos?'start':'end'}" style="font-size:10px;fill:var(--text-muted)">${c.test_edge>0?'+':''}${c.test_edge}</text>`;});
 const svg=$("#rank");svg.setAttribute("viewBox",`0 0 ${W} ${H}`);svg.innerHTML=s;bindtt("#rank");})();
// train vs test scatter
(function(){const D=DATA.scatter,W=620,H=300,P={l:44,r:12,t:12,b:34};
 const sc=v=>[P.l+(W-P.l-P.r)*(v-35)/30, P.t+(H-P.t-P.b)*(1-(v-35)/30)];
 let g='';for(const v of[40,45,50,55,60]){const[x,]=sc(v);const[,y]=sc(v);
  g+=`<line x1="${x}" x2="${x}" y1="${P.t}" y2="${H-P.b}" stroke="var(--border)"/><text x="${x}" y="${H-P.b+14}" text-anchor="middle">${v}</text>`;
  g+=`<line x1="${P.l}" x2="${W-P.r}" y1="${y}" y2="${y}" stroke="var(--border)"/><text x="${P.l-6}" y="${y+3}" text-anchor="end">${v}</text>`;}
 const[dx0,dy0]=sc(35),[dx1,dy1]=sc(65);
 g+=`<line x1="${sc(38)[0]}" y1="${sc(38)[1]}" x2="${sc(62)[0]}" y2="${sc(62)[1]}" stroke="var(--text-muted)" stroke-dasharray="4,3"/>`;
 let pts='';D.forEach(d=>{const[x,y]=sc(Math.max(35,Math.min(65,d.train_acc)));const[,ty]=sc(Math.max(35,Math.min(65,d.test_acc)));
  pts+=`<circle cx="${x}" cy="${ty}" r="4" fill="var(--series-1)" opacity="0.75" data-t="${d.concept}: train ${d.train_acc}% test ${d.test_acc}%"/>`;});
 $("#sc").innerHTML=g+`<text x="${W/2}" y="${H-4}" text-anchor="middle" style="fill:var(--text-muted)">train accuracy %</text>`+pts;bindtt("#sc");})();
$("#vd").innerHTML="<tr><th class='l'>read</th><th>test acc</th></tr>"+
 `<tr><td class="l">base rate (up)</td><td>${DATA.base_te}%</td></tr>`+
 `<tr><td class="l">best single concept</td><td>${DATA.best.a}%</td></tr>`+
 `<tr><td class="l">learning ensemble</td><td class="bear">${DATA.ens_te}%</td></tr>`;
$("#jr").innerHTML="<tr><th class='l'>month</th><th class='l'>trusted (≥55%)</th><th class='l'>faded (≤45%)</th></tr>"+
 DATA.journal.map(j=>`<tr><td class="l">${j.mo}</td><td class="l" style="color:var(--pos)">${j.trusted.join(', ')||'—'}</td><td class="l" style="color:var(--neg)">${j.faded.join(', ')||'—'}</td></tr>`).join("");
(function(){const cols=[["concept","concept"],["n","fires"],["acc","all%"],["train_acc","train%"],["test_acc","test%"],["test_edge","OOS edge"]];
 const th=$("#tbl thead"),tb=$("#tbl tbody");
 th.innerHTML="<tr>"+cols.map(c=>`<th class="${c[0]==='concept'?'l':''}" data-k="${c[0]}">${c[1]}</th>`).join("")+"</tr>";
 let rows=DATA.concepts.slice(),asc=false,key="test_edge";
 function r(){tb.innerHTML=rows.map(x=>`<tr><td class="l">${x.concept}</td><td>${x.n}</td><td>${x.acc}</td><td>${x.train_acc}</td><td>${x.test_acc}</td><td style="color:${x.test_edge>0?'var(--pos)':'var(--neg)'}">${x.test_edge>0?'+':''}${x.test_edge}</td></tr>`).join("");}
 th.addEventListener("click",e=>{const k=e.target.dataset.k;if(!k)return;asc=(key===k)?!asc:false;key=k;rows.sort((a,b)=>{const p=a[k],q=b[k];return(p>q?1:p<q?-1:0)*(asc?1:-1);});r();});r();})();
function bindtt(sel){const el=$(sel),tt=$("#tt");el.addEventListener("mousemove",e=>{const t=e.target.dataset.t;
 if(!t){tt.style.display="none";return;}tt.style.display="block";tt.style.left=(e.clientX+14)+"px";tt.style.top=(e.clientY-10)+"px";tt.textContent=t;});
 el.addEventListener("mouseleave",()=>tt.style.display="none");}
</script>"""
out = CSS + BODY.replace("{N}", str(len(R))) + SCRIPT.replace("__DATA__", DATA)
for bad in ["<!doctype", "<html", "<head", "<body", "</html"]:
    assert bad not in out.lower(), bad
open(f"{S}/bias_lab_artifact.html", "w").write(out)
print("written bias_lab_artifact.html", len(out))
