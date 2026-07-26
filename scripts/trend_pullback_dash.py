#!/usr/bin/env python3
"""Trend Pullback (stacked MA) dashboard: bare vs +confluence -> Artifact HTML."""
import json
import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
raw = open(f"{S}/trend_pullback.json").read().replace("Infinity", "999")
D = json.loads(raw)
CSS = open(f"{S}/_css_block.txt").read().replace('CSS = """', "").rstrip('"')
DATA = json.dumps(D, separators=(",", ":"))
p = D["params"]

BODY = """
<h1>Trend Pullback (stacked MA) — isolated setup: bare vs +confluence</h1>
<div class="sub"><b>New setup, tested alone</b> (not blended into any other book). M15 stacked-MA trend pullback: 20&gt;50&gt;200 stack, price pulls back to <b>touch the 50MA</b> with <b>fading volume</b> and resumes. Run two ways — <b>(a) bare</b> trigger only, <b>(b) +confluence</b> (delta/VWAP/Bollinger/POC). Parameters chosen on <b>train 2023–24</b> only; <b>test 2025→now touched once</b>. Point-in-time throughout — session VWAP/POC built cumulatively with a hard time-guard (0 violations).</div>

<div class="tiles" id="tiles"></div>

<section><h2>(a) bare vs (b) +confluence — side by side, train vs test</h2>
<div class="card"><table id="cmp"></table>
<div class="note2">Every figure with 95% CI and N. <b id="lown"></b> Counter-baseline = the same triggers taken in the mirror direction. Both variants' test expectancy CIs are enormous and <b>include the counter-baseline</b> — neither clears it.</div></div></section>

<section class="grid3">
<div class="card" style="grid-column:span 2"><h2>The decider: placebo / label-shuffle</h2>
<svg id="placebo" width="100%" height="200" viewBox="0 0 620 200"></svg>
<div class="note2">Real entries vs 300 shuffles that pick <b>random bars inside the same stacked-MA uptrend</b>. Both variants score <b>no better than random</b> (bare p=0.59, +confluence p=0.54). Translation: the money that shows up is <b>"we're in an uptrend,"</b> not the 50MA-touch/volume-fade trigger. The specific setup adds nothing over just being long in a trend.</div></div>
<div class="card"><h2>Parameters (logged, train-chosen)</h2><table id="params"></table></div>
</section>

<section><h2>Your three questions, answered</h2><div class="card"><div id="answers"></div></div></section>
<div class="tt" id="tt"></div>
"""

SCRIPT = r"""<script>
const D=__DATA__;const $=s=>document.querySelector(s);const p=D.params;
const bt=D.results.BARE.TEST.st,ct=D.results["+CONFLUENCE"].TEST.st;
const bc=D.results.BARE.TEST.ctr,cc=D.results["+CONFLUENCE"].TEST.ctr;
$("#tiles").innerHTML=[
 ["Setup","Trend Pullback","stacked-MA, isolated"],
 ["(a) bare — test E[R]",bt.expR+" R","PF "+bt.pf+", n="+bt.n],
 ["(b) +conf — test E[R]",ct.expR+" R","PF "+ct.pf+", n="+ct.n],
 ["Confluence adds","+"+(ct.expR-bt.expR).toFixed(3)+" R","within noise"],
 ["Clears counter?","NO","CI includes baseline"],
 ["Beats random trend?","NO","placebo p≈0.5-0.6"],
].map(t=>`<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div><div class="s">${t[2]}</div></div>`).join("");

const rows=[["BARE","TRAIN"],["BARE","TEST"],["+CONFLUENCE","TRAIN"],["+CONFLUENCE","TEST"]];
$("#cmp").innerHTML="<tr><th class='l'>variant</th><th class='l'>split</th><th>N</th><th>E[R]</th><th>95% CI</th><th>win%</th><th>PF</th><th>maxDD</th><th>counter E[R]</th><th>folds+</th></tr>"+
 rows.map(([v,s])=>{const o=D.results[v][s];const st=o.st,c=o.ctr;const low=st.n<30;
  return `<tr><td class="l">${v}</td><td class="l">${s}</td><td>${st.n}${low?' ⚠':''}</td>`+
   `<td style="color:${st.expR>0?'var(--pos)':'var(--neg)'}">${st.expR>0?'+':''}${st.expR}</td>`+
   `<td>[${st.exp_ci[0]}, ${st.exp_ci[1]}]</td><td>${st.wr}%</td><td>${st.pf}</td><td style="color:var(--neg)">${st.mddR}R</td>`+
   `<td style="color:var(--text-muted)">${c.expR!==undefined?(c.expR>0?'+':'')+c.expR:'—'} (n${c.n||0})</td>`+
   `<td>${s==='TEST'?o.folds[0]+'/'+o.folds[1]:'—'}</td></tr>`;}).join("");
$("#lown").textContent = (bt.n<30||ct.n<30)?"⚠ = N<30, untrusted.":"All test N≥30.";

(function(){const items=[["(a) bare",bt.expR,D.placebo.BARE,0.052],["(b) +confluence",ct.expR,D.placebo["+CONFLUENCE"],0.058]];
 const W=620,H=200,P={l:110,r:20,t:20,b:34};const mn=-0.2,mx=0.35;
 const sx=v=>P.l+(W-P.l-P.r)*(v-mn)/(mx-mn);
 let s=`<line x1="${sx(0)}" x2="${sx(0)}" y1="${P.t}" y2="${H-P.b}" stroke="var(--text-muted)" stroke-dasharray="3,3"/>`;
 items.forEach((it,i)=>{const y=P.t+i*66+20;
  s+=`<text x="${P.l-10}" y="${y+4}" text-anchor="end" style="font-size:12px">${it[0]}</text>`;
  s+=`<rect x="${sx(Math.min(0,it[3]))}" y="${y-14}" width="${Math.abs(sx(it[3])-sx(0))}" height="10" fill="var(--text-muted)" opacity="0.5"/>`;
  s+=`<text x="${sx(it[3])+4}" y="${y-6}" style="font-size:9px;fill:var(--text-muted)">random ${it[3].toFixed(2)}</text>`;
  const col=it[1]>0?'var(--series-1)':'var(--neg)';
  s+=`<rect x="${sx(Math.min(0,it[1]))}" y="${y}" width="${Math.abs(sx(it[1])-sx(0))}" height="14" rx="2" fill="${col}"/>`;
  s+=`<text x="${sx(it[1])+(it[1]>=0?4:-4)}" y="${y+11}" text-anchor="${it[1]>=0?'start':'end'}" style="font-size:10px">real ${it[1]>0?'+':''}${it[1]}  (shuffle p=${it[2]})</text>`;});
 s+=`<text x="${W/2}" y="${H-6}" text-anchor="middle" style="fill:var(--text-muted)">E[R] per trade — real entry vs random bars in the same uptrend</text>`;
 $("#placebo").innerHTML=s;})();

$("#params").innerHTML=[["touch",p.touch],["fade","vol < "+p.thr+" × mean(prior "+p.n+")"],["target",p.tgtR+"R"],["confluence","≥ "+p.conf_k+" of 4"]]
 .map(r=>`<tr><td class="l">${r[0]}</td><td class="l" style="font-family:monospace">${r[1]}</td></tr>`).join("");

$("#answers").innerHTML=`<ul class="vlist">
<li><b>1 · Does confluence beat bare OOS?</b> Marginally and within noise. Bare test E[R] <b>${bt.expR}R</b> (losing, PF ${bt.pf}); +confluence <b>${ct.expR}R</b> (breakeven, PF ${ct.pf}) — a +${(ct.expR-bt.expR).toFixed(3)}R nudge from losing to flat, but both CIs span roughly [−0.35, +0.4], so the difference is not significant. Confluence tidies, it doesn't rescue.</li>
<li><b>2 · Does either clear the counter-baseline OOS at N≥30 with CI excluding it?</b> <b>No.</b> Bare CI [${bt.exp_ci[0]}, ${bt.exp_ci[1]}] and +confluence CI [${ct.exp_ci[0]}, ${ct.exp_ci[1]}] both include their counter-baselines. Neither is distinguishable from the mirror.</li>
<li><b>3 · Train-vs-test gap (overfit alarm)?</b> Small — bare +0.021R, +confluence +0.064R. No overfitting alarm, but only because <b>there is no edge to overfit</b>: the setup is breakeven in both blocks.</li>
</ul>
<div class="verdict-no">Verdict: the Trend Pullback setup does not hold up in isolation.</div>
<div class="note2">The placebo is the tell — real 50MA-touch entries score no better than random bars in the same stacked-MA uptrend (p≈0.5–0.6). What little positive expectancy appears is the <b>trend regime itself</b>, not the pullback trigger or the confluence. Isolated and honestly graded, it is not a standalone edge. (Other setups untouched; delta = tick-rule proxy, true delta-divergence needs 2026-only bid/ask.)</div>`;

function bindtt(sel){}
</script>"""
EXTRA = """<style>
.verdict-no{font-size:15px;font-weight:700;color:var(--neg);margin:10px 0 6px}
.vlist{margin:0;padding-left:18px;font-size:13px;line-height:1.65;color:var(--text)}
.vlist li{margin-bottom:8px}
</style>"""
out = CSS + EXTRA + BODY + SCRIPT.replace("__DATA__", DATA)
for bad in ["<!doctype", "<html", "<head", "<body", "</html"]:
    assert bad not in out.lower(), bad
open(f"{S}/trend_pullback_artifact.html", "w").write(out)
print("written trend_pullback_artifact.html", len(out))
