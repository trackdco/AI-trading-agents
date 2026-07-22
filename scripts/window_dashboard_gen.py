#!/usr/bin/env python3
"""Window-bias evaluation dashboard -> Artifact HTML (no wrapper tags)."""
import json
S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
D = json.load(open(f"{S}/window_eval.json"))
CSS = open(f"{S}/_css_block.txt").read().replace('CSS = """', "").rstrip('"')

# Fix-6 timestamp evidence (verified from the parquet; UTC offset flips with DST)
TS = [
    ["2023-01-17", "EST −05:00", "13:00", "14:30", "15:15"],
    ["2023-07-11", "EDT −04:00", "12:00", "13:30", "14:15"],
    ["2024-03-15", "EDT −04:00", "12:00", "13:30", "14:15"],
    ["2024-11-06", "EST −05:00", "13:00", "14:30", "15:15"],
    ["2025-06-10", "EDT −04:00", "12:00", "13:30", "14:15"],
]
DATA = json.dumps(dict(D, ts=TS), separators=(",", ":"))

BODY = """
<h1>Predicting the 08:00 → 10:15 ET window direction — the honest test</h1>
<div class="sub"><b>Question:</b> standing at 08:00 with only what is known by then, how accurately can the direction of your trading window (08:00→10:15 ET) be called? Not the daily close — the window you actually trade. 24 no-lookahead concepts + a walk-forward learning ensemble, graded on the window, <b>TRAIN 2023–24</b> frozen before <b>TEST 2025–26</b>. Every number carries its base rate, 95% CI and sample size; the ±15-pt three-way grade (bull / bear / neutral) makes raw accuracy look low by design — <b>skill = accuracy − base rate is the real metric.</b></div>

<div class="tiles" id="tiles"></div>

<section><h2>Data integrity first — DST, endpoints, exclusions (Fix 6)</h2>
<div class="grid3">
<div class="card"><h3>Timezone / DST alignment</h3><table id="ts"></table>
<div class="note2">08:00/09:30/10:15 <b>ET</b> map to the correct UTC rows year-round — the offset flips −05:00↔−04:00 across DST automatically. Verified on 5 days spanning both regimes.</div></div>
<div class="card"><h3>Exclusions &amp; endpoints</h3><table id="ex"></table>
<div class="note2">A day is graded only if both the 08:00 and 10:15 bars exist. VIX uses the last value <b>strictly before</b> 08:00 (prior close). Half-days keep the window if 08:00→10:15 is intact.</div></div>
<div class="card"><h3>What "skill" means</h3>
<p class="p">Outcome is 3-way: <b>bull</b> (net &gt; +15pt), <b>bear</b> (&lt; −15pt), <b>neutral</b> (chop). A directional call on a neutral day is graded wrong, so raw accuracy sits near 45%. The honest measure is <b>accuracy − base rate</b>: does the call beat guessing? A 95% CI that includes 0 skill = indistinguishable from chance.</p></div>
</div></section>

<section><h2>Every concept, ranked by out-of-sample skill (accuracy − base rate), with 95% CI</h2>
<div class="card"><svg id="rank" width="100%" height="560" viewBox="0 0 960 560"></svg>
<div class="note2">Point = test skill; whisker = 95% Wilson CI on accuracy re-centred to skill. <b>Every whisker crosses the zero line</b> — not one concept's edge is distinguishable from chance out-of-sample. With 24 concepts, ~1.2 are expected to look significant by luck alone; after Benjamini-Hochberg FDR correction, <b>zero</b> survive.</div></div></section>

<section class="grid3">
<div class="card"><h2>Ensemble directional calls are a coin flip</h2>
<svg id="conf" width="100%" height="260" viewBox="0 0 380 260"></svg>
<div class="note2">3×3 confusion (test). When the learner commits to <b>bull</b> it's right 27 / wrong 26; committing <b>bear</b>, right 38 / wrong 36. No side skill — it mostly abstains (neutral), and when it doesn't, it's ~50/50.</div></div>
<div class="card" style="grid-column:span 2"><h2>Best honest single strategy — the walk-forward ensemble</h2>
<table id="ens"></table>
<div class="note2">The ensemble is the only legitimate "strategy" (past-only weights, never sees the test block). Its test skill is <b>+1.4 pts</b> with a CI from −6 to +10 and p≈0.40 — a statistical zero. Grade B (a ±15 first-touch race from the 08:00 open) and the 09:30→10:15 "gold" sub-window are the same story.</div></div>
</section>

<section class="grid3">
<div class="card" style="grid-column:span 2"><h2>Walk-forward folds — the "5/5 positive" mirage (Fix 4a)</h2>
<div style="overflow:auto"><table id="folds"></table></div>
<div class="note2">Selecting the best-of-24 on each train block is positive on 5/5 test blocks — but that is <b>selection luck</b>: the winning concept <b>changes every fold</b> and fires on only 12–47 days. The honest single strategy (the ensemble) is positive on just 3/5, and every fold's sample is far too small to trust.</div></div>
<div class="card"><h2>By VIX regime (Fix 4b)</h2><table id="vix"></table>
<div class="note2">No clean regime story survives sample size: the low-VIX bucket has 2 days (noise); mid/high skills are within CI of zero. A blended number isn't hiding a great low-vol sub-regime — there isn't one.</div></div>
</section>

<section class="grid3">
<div class="card"><h2>Deadband curve — curve-fit check (Fix 7)</h2>
<svg id="db" width="100%" height="240" viewBox="0 0 420 240"></svg>
<div class="note2">Skill wobbles +0.7 → +3.5 across thresholds with no stable peak, and the volatility-normalized band (~35pt) gives +0.7. Edge that only appears at one fixed number would be curve-fit; here there's no edge at any.</div></div>
<div class="card" style="grid-column:span 2"><h2>Verdict — is there real, regime-robust, sample-sufficient signal?</h2>
<div id="verdict"></div></div>
</section>

<section><h2>Full concept table (test set, sortable) — no highlight reel</h2>
<div class="card" style="max-height:520px;overflow:auto"><table id="tbl"><thead></thead><tbody></tbody></table></div>
<div class="note2">te_n = test directional calls (gate N≥30). skill = acc − base. CI = 95% Wilson on accuracy. p = one-sided binomial vs base. BH = passes multiple-comparisons FDR≤0.10 (none do).</div></section>
<div class="tt" id="tt"></div>
"""

SCRIPT = r"""<script>
const D=__DATA__;const $=s=>document.querySelector(s);
const ens=D.ens;
$("#tiles").innerHTML=[
 ["Graded days",D.n_days,"2023 → Jul 2026, "+D.excl_endpoint.length+" excluded"],
 ["Window base P(up)",D.base_te+"%","test; window is down-skewed"],
 ["Best honest strategy",ens.te.acc+"%","ensemble — skill "+(ens.te.skill>=0?"+":"")+ens.te.skill],
 ["Its 95% CI on skill","−6 … +10","includes zero → chance"],
 ["Pass multiple-comp.","0 / 24","BH FDR≤0.10 on test"],
 ["Survivors","0","→ Fix 5 expectancy N/A"],
].map(t=>`<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div><div class="s">${t[2]}</div></div>`).join("");

$("#ts").innerHTML="<tr><th class='l'>date</th><th>DST</th><th>08:00</th><th>09:30</th><th>10:15</th></tr>"+
 D.ts.map(r=>`<tr><td class="l">${r[0]}</td><td style="color:var(--text-muted)">${r[1]}</td><td>${r[2]}Z</td><td>${r[3]}Z</td><td>${r[4]}Z</td></tr>`).join("");
$("#ex").innerHTML=`<tr><td class="l">graded days</td><td>${D.n_days}</td></tr>`+
 `<tr><td class="l">endpoint-excluded</td><td>${D.excl_endpoint.join(', ')||'—'}</td></tr>`+
 `<tr><td class="l">half-days kept</td><td>${D.half_days.length}</td></tr>`+
 `<tr><td class="l">VIX source</td><td>prior close (≤08:00)</td></tr>`;

// ranked skill with CI whiskers
(function(){const C=D.concepts.slice().sort((a,b)=>b.te_skill-a.te_skill);
 const W=960,rowH=21,P={l:150,r:60,t:8},H=C.length*rowH+P.t+14;
 const skl=c=>c.te_skill,lo=c=>c.te_ci_lo-c.te_base,hi=c=>c.te_ci_hi-c.te_base;
 const mn=Math.min(-14,...C.map(lo)),mx=Math.max(14,...C.map(hi));
 const sx=v=>P.l+(W-P.l-P.r)*(v-mn)/(mx-mn);const x0=sx(0);
 let s=`<line x1="${x0}" x2="${x0}" y1="${P.t}" y2="${H-14}" stroke="var(--text-muted)" stroke-dasharray="3,3"/>`;
 s+=`<text x="${x0}" y="${H-2}" text-anchor="middle" style="fill:var(--text-muted)">0 skill (= base rate)</text>`;
 C.forEach((c,i)=>{const y=P.t+i*rowH+rowH/2;const good=c.gate!=='OK';
  s+=`<text x="${P.l-8}" y="${y+3}" text-anchor="end" style="font-size:10.5px;${good?'fill:var(--text-muted)':''}">${c.concept}${good?' ⚠':''}</text>`;
  s+=`<line x1="${sx(lo(c))}" x2="${sx(hi(c))}" y1="${y}" y2="${y}" stroke="var(--border-strong,#999)" stroke-width="1.5"/>`;
  s+=`<line x1="${sx(lo(c))}" x2="${sx(lo(c))}" y1="${y-3}" y2="${y+3}" stroke="var(--border-strong,#999)"/>`;
  s+=`<line x1="${sx(hi(c))}" x2="${sx(hi(c))}" y1="${y-3}" y2="${y+3}" stroke="var(--border-strong,#999)"/>`;
  const col=skl(c)>=0?'var(--series-1)':'var(--neg)';
  s+=`<circle cx="${sx(skl(c))}" cy="${y}" r="4.5" fill="${col}" data-t="${c.concept}: test acc ${c.te_acc}% vs base ${c.te_base}% → skill ${skl(c)>0?'+':''}${skl(c)} | 95% CI acc [${c.te_ci_lo},${c.te_ci_hi}] | n=${c.te_n} | p=${c.te_p}"/>`;
  s+=`<text x="${sx(hi(c))+6}" y="${y+3}" style="font-size:9.5px;fill:var(--text-muted)">n=${c.te_n}</text>`;});
 const svg=$("#rank");svg.setAttribute("viewBox",`0 0 ${W} ${H}`);svg.innerHTML=s;bindtt("#rank");})();

// confusion heat
(function(){const M=D.confusion,W=380,H=260,cell=78,ox=150,oy=44;
 const rl=["pred bear","pred neut","pred bull"],cl=["bear","neut","bull"];
 const mx=Math.max(...M.flat());let s='';
 cl.forEach((c,j)=>s+=`<text x="${ox+j*cell+cell/2}" y="${oy-10}" text-anchor="middle" style="fill:var(--text-muted)">${c}</text>`);
 M.forEach((row,i)=>{s+=`<text x="${ox-8}" y="${oy+i*cell+cell/2+4}" text-anchor="end" style="fill:var(--text-muted)">${rl[i]}</text>`;
  row.forEach((v,j)=>{const a=0.12+0.6*v/mx;s+=`<rect x="${ox+j*cell}" y="${oy+i*cell}" width="${cell-3}" height="${cell-3}" rx="4" fill="var(--series-1)" opacity="${a}"/>`;
   s+=`<text x="${ox+j*cell+cell/2-1}" y="${oy+i*cell+cell/2+5}" text-anchor="middle" style="font-weight:600;fill:var(--text)">${v}</text>`;});});
 s+=`<text x="${ox+1.5*cell}" y="${H-6}" text-anchor="middle" style="fill:var(--text-muted)">realized window direction</text>`;
 $("#conf").innerHTML=s;})();

$("#ens").innerHTML="<tr><th class='l'>read</th><th>fires</th><th>acc</th><th>base</th><th>skill</th><th>95% CI (acc)</th><th>p</th></tr>"+
 [["TRAIN 23-24",ens.tr],["TEST 25-26",ens.te],["TEST Grade-B",ens.teB],["gold 09:30→10:15",ens.gold]].map(([l,g])=>
 `<tr><td class="l">${l}</td><td>${g.n}</td><td>${g.acc}%</td><td>${g.base_up}%</td><td style="color:${g.skill>0?'var(--pos)':'var(--neg)'}">${g.skill>0?'+':''}${g.skill}</td><td>[${g.ci[0]}, ${g.ci[1]}]</td><td>${g.p}</td></tr>`).join("");

$("#folds").innerHTML="<tr><th class='l'>test block</th><th class='l'>train-picked</th><th>pick acc</th><th>pick skill</th><th>pick n</th><th>ens acc</th><th>ens skill</th><th>ens n</th></tr>"+
 D.folds.map(f=>`<tr><td class="l">${f.test}</td><td class="l" style="color:var(--text-muted)">${f.sel}</td><td>${f.sel_acc}%</td><td style="color:${f.sel_skill>0?'var(--pos)':'var(--neg)'}">${f.sel_skill>0?'+':''}${f.sel_skill}</td><td>${f.sel_n}</td><td>${f.ens_acc}%</td><td style="color:${f.ens_skill>0?'var(--pos)':'var(--neg)'}">${f.ens_skill>0?'+':''}${f.ens_skill}</td><td>${f.ens_n}</td></tr>`).join("");

$("#vix").innerHTML="<tr><th class='l'>VIX</th><th>days</th><th>base</th><th>ens acc</th><th>ens skill</th><th>ens n</th></tr>"+
 D.vix.map(v=>`<tr><td class="l">${v.vix}</td><td>${v.n_days}</td><td>${v.base}%</td><td>${v.ens_acc}%</td><td style="color:${v.ens_skill>0?'var(--pos)':'var(--neg)'}">${v.ens_skill>0?'+':''}${v.ens_skill}</td><td>${v.ens_n}${v.ens_n<30?' ⚠':''}</td></tr>`).join("");

// deadband curve
(function(){const keys=["0","10","15","20","vol"],lbl=["0","10","15","20","vol~35"];
 const V=keys.map(k=>D.deadband_curve[k]);const W=420,H=240,P={l:40,r:14,t:16,b:38};
 const mx=Math.max(5,...V.map(v=>v.skill)),mn=Math.min(-1,...V.map(v=>v.skill));
 const sx=i=>P.l+(W-P.l-P.r)*i/(keys.length-1),sy=v=>P.t+(H-P.t-P.b)*(1-(v-mn)/(mx-mn));
 let g='';for(let v=0;v<=Math.ceil(mx);v++){const y=sy(v);g+=`<line x1="${P.l}" x2="${W-P.r}" y1="${y}" y2="${y}" stroke="var(--border)"/><text x="${P.l-6}" y="${y+3}" text-anchor="end">${v}</text>`;}
 const zy=sy(0);g+=`<line x1="${P.l}" x2="${W-P.r}" y1="${zy}" y2="${zy}" stroke="var(--text-muted)"/>`;
 let pth=V.map((v,i)=>`${i?'L':'M'}${sx(i)},${sy(v.skill)}`).join(" ");
 g+=`<path d="${pth}" fill="none" stroke="var(--series-1)" stroke-width="2"/>`;
 V.forEach((v,i)=>{g+=`<circle cx="${sx(i)}" cy="${sy(v.skill)}" r="4" fill="var(--series-1)" data-t="deadband ${lbl[i]}: skill ${v.skill>0?'+':''}${v.skill}, acc ${v.acc}%, n=${v.n}"/>`;
  g+=`<text x="${sx(i)}" y="${H-P.b+16}" text-anchor="middle" style="fill:var(--text-muted)">${lbl[i]}</text>`;});
 g+=`<text x="${W/2}" y="${H-6}" text-anchor="middle" style="fill:var(--text-muted)">deadband (pts)</text>`;
 $("#db").innerHTML=g;bindtt("#db");})();

$("#verdict").innerHTML=`<div class="verdict-no">NO reliable, regime-robust, sample-sufficient signal above base rate.</div>
<ul class="vlist">
<li><b>0 of 24</b> concepts clear their base rate after multiple-comparisons correction; every 95% CI crosses zero skill.</li>
<li>The honest learning ensemble scores <b>+1.4 skill</b> (p≈0.40) — a coin flip; its directional calls are 50/50 in the confusion matrix.</li>
<li>The "5/5 positive" walk-forward folds are selection luck — the winner changes each fold and fires on 12–47 days.</li>
<li>The 09:30→10:15 "gold" sub-window, with more information and a shorter horizon, is <b>+0.0 skill</b>.</li>
<li><b>Fix 5 (real Campion v1.1 expectancy) is N/A</b> — nothing survived the direction screen to grade, and grading an unproven bias by expectancy would just relabel noise.</li>
</ul>
<div class="note2" style="margin-top:8px"><b>What this does <i>not</i> say:</b> it doesn't say the strategy can't make money. It says <i>you cannot predict the window's direction at 08:00</i>. The durable edge lives in <b>reaction, not prediction</b> — trade the level/liquidity as it confirms in-window, and use "bias" only to size and to avoid fighting a clean trend, never as a pre-08:00 directional bet.</div>`;

(function(){const cols=[["concept","concept"],["te_n","n"],["te_acc","acc%"],["te_base","base%"],["te_skill","skill"],["te_ci_lo","CI lo"],["te_ci_hi","CI hi"],["te_p","p"],["teB_acc","B acc%"],["tr_skill","train skl"]];
 const th=$("#tbl thead"),tb=$("#tbl tbody");
 th.innerHTML="<tr>"+cols.map(c=>`<th class="${c[0]==='concept'?'l':''}" data-k="${c[0]}">${c[1]}</th>`).join("")+"</tr>";
 let rows=D.concepts.slice(),asc=false,key="te_skill";
 function fmt(x,k){return(k==='te_skill'||k==='tr_skill')?(x>0?'+':'')+x:x;}
 function r(){tb.innerHTML=rows.map(x=>`<tr>${cols.map(c=>{const k=c[0];const col=(k==='te_skill'||k==='tr_skill')?(x[k]>0?'var(--pos)':'var(--neg)'):'';return `<td class="${k==='concept'?'l':''}" style="${col?'color:'+col:''}">${fmt(x[k],k)}${k==='concept'&&x.gate!=='OK'?' ⚠':''}</td>`;}).join("")}</tr>`).join("");}
 th.addEventListener("click",e=>{const k=e.target.dataset.k;if(!k)return;asc=(key===k)?!asc:false;key=k;rows.sort((a,b)=>{const p=a[k],q=b[k];return(p>q?1:p<q?-1:0)*(asc?1:-1);});r();});r();})();

function bindtt(sel){const el=$(sel),tt=$("#tt");el.addEventListener("mousemove",e=>{const t=e.target.dataset.t;
 if(!t){tt.style.display="none";return;}tt.style.display="block";tt.style.left=(e.clientX+14)+"px";tt.style.top=(e.clientY-10)+"px";tt.textContent=t;});
 el.addEventListener("mouseleave",()=>tt.style.display="none");}
</script>"""

EXTRA = """<style>
.p{font-size:13px;line-height:1.5;color:var(--text)}
h3{font-size:13px;margin:0 0 8px;color:var(--text)}
.verdict-no{font-size:16px;font-weight:700;color:var(--neg);margin-bottom:8px}
.vlist{margin:0;padding-left:18px;font-size:13px;line-height:1.6;color:var(--text)}
.vlist li{margin-bottom:4px}
</style>"""
out = CSS + EXTRA + BODY + SCRIPT.replace("__DATA__", DATA)
for bad in ["<!doctype", "<html", "<head", "<body", "</html"]:
    assert bad not in out.lower(), bad
open(f"{S}/window_bias_artifact.html", "w").write(out)
print("written window_bias_artifact.html", len(out))
