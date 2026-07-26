#!/usr/bin/env python3
"""Stage-1 component edge gate dashboard -> Artifact HTML (no wrapper tags)."""
import json
import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
D = json.load(open(f"{S}/stage1_battery.json"))
CSS = open(f"{S}/_css_block.txt").read().replace('CSS = """', "").rstrip('"')
DATA = json.dumps(D, separators=(",", ":"))

BODY = """
<h1>Multi-agent trading sim — Stage 1 gate: component edge battery</h1>
<div class="sub"><b>The build order was: prove a component edge FIRST, then orchestrate.</b> 34 candidate components (rolling/frozen bias gates, all 24 daily concepts, direction, timing, geometry, VIX regime) were graded on 756 point-in-time in-window breakout events under <b>real Campion v1.1 money rules</b> (outcome = R/trade incl. slip &amp; commission). Pass required: test N≥30, (component − counter-baseline) bootstrap 95% CI entirely above zero, and positive in ≥60% of anchored walk-forward folds — then Benjamini-Hochberg across the whole battery and a shuffle/placebo audit. <b>The survivor list is empty, so per the spec's own non-negotiable directive, Stages 2–5 (agents, meta-learner) were NOT built.</b> Orchestration amplifies edge; it never creates it.</div>

<div class="tiles" id="tiles"></div>

<section><h2>Every component vs its counter-baseline — expectancy difference (R/trade, test 2025–26)</h2>
<div class="card"><svg id="rank" width="100%" height="700" viewBox="0 0 960 700"></svg>
<div class="note2">Point = test expectancy diff (component − counter-baseline); whisker = bootstrap 95% CI. <b>Every whisker crosses zero.</b> BH-corrected significant: <b>none</b>. The top entries are what the best-of-34 looks like by luck — e.g. momentum_5d's diff was +0.03R in train and +0.27R in test: no persistence, just a lucky draw.</div></div></section>

<section class="grid3">
<div class="card"><h2>Why the gate stops the build</h2>
<p class="p">Directive 3: the swarm and meta-learner may only weight components that already passed this battery. With zero survivors there is nothing legitimate to orchestrate — a learning layer on top would only learn noise faster (the earlier walk-forward ensemble scored <b>below</b> a coin flip doing exactly that). Stopping here is the spec working as designed, not a failure of the build.</p></div>
<div class="card"><h2>Guards in place for this stage</h2>
<table id="guards"></table>
<div class="note2">The §4 runtime time-guard and §5 learner date-filter belong to Stages 2/4, which were gated off. Every input here was built under the audited ≤-now harness.</div></div>
<div class="card"><h2>Run manifest</h2><table id="mani"></table>
<div class="note2">Deterministic: fixed seed, no wall-clock/random in decision paths; re-run reproduces every number.</div></div>
</section>

<section><h2>Full battery table (test set, sorted by diff)</h2>
<div class="card" style="max-height:520px;overflow:auto"><table id="tbl"><thead></thead><tbody></tbody></table></div>
<div class="note2">E[R] = component's own expectancy (R/trade, real money). ctr = counter-baseline expectancy. diff CI = bootstrap 95% CI on the difference. folds = positive/valid anchored walk-forward folds. Nothing passes N≥30 + CI&gt;0 + ≥60% folds; nothing survives BH FDR≤0.10.</div></section>

<section><h2>Verdict</h2><div class="card"><div id="verdict"></div></div></section>
<div class="tt" id="tt"></div>
"""

SCRIPT = r"""<script>
const D=__DATA__;const $=s=>document.querySelector(s);
$("#tiles").innerHTML=[
 ["Components tested",D.n_components,"one battery, BH applied once"],
 ["Events (real money)",D.n_events,D.n_train+" train / "+D.n_test+" test"],
 ["Baseline E[R] (all)","+0.058 R","CI [−0.10, +0.22] — breakeven"],
 ["Pass BH FDR≤0.10","0 / "+D.n_components,"expected by chance: ~1.7"],
 ["Pass full gate","0","N≥30 & CI>0 & folds"],
 ["Stages 2–5","NOT BUILT","empty survivor list → stop"],
].map(t=>`<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div><div class="s">${t[2]}</div></div>`).join("");

(function(){const C=D.battery.slice().sort((a,b)=>b.te_diff-a.te_diff);
 const W=960,rowH=19,P={l:170,r:66,t:8},H=C.length*rowH+P.t+16;
 const lo=c=>c.te_diff_ci[0],hi=c=>c.te_diff_ci[1];
 const mn=Math.min(-0.6,...C.map(lo)),mx=Math.max(0.6,...C.map(hi));
 const sx=v=>P.l+(W-P.l-P.r)*(v-mn)/(mx-mn);const x0=sx(0);
 let s=`<line x1="${x0}" x2="${x0}" y1="${P.t}" y2="${H-16}" stroke="var(--text-muted)" stroke-dasharray="3,3"/>`;
 s+=`<text x="${x0}" y="${H-4}" text-anchor="middle" style="fill:var(--text-muted)">0 (no edge over counter-baseline)</text>`;
 C.forEach((c,i)=>{const y=P.t+i*rowH+rowH/2;const low=c.gate_n!=='OK';
  s+=`<text x="${P.l-8}" y="${y+3}" text-anchor="end" style="font-size:10px;${low?'fill:var(--text-muted)':''}">${c.component.replace(/^c_/,'')}${low?' ⚠':''}</text>`;
  s+=`<line x1="${sx(lo(c))}" x2="${sx(hi(c))}" y1="${y}" y2="${y}" stroke="var(--border-strong,#999)" stroke-width="1.4"/>`;
  const col=c.te_diff>=0?'var(--series-1)':'var(--neg)';
  s+=`<circle cx="${sx(c.te_diff)}" cy="${y}" r="4" fill="${col}" data-t="${c.component}: diff ${c.te_diff>0?'+':''}${c.te_diff}R CI[${c.te_diff_ci}] p=${c.te_p} | own E[R] ${c.te_expR} | folds ${c.folds_pos}/${c.folds_valid} | train diff ${c.tr_diff}"/>`;
  s+=`<text x="${sx(hi(c))+5}" y="${y+3}" style="font-size:9px;fill:var(--text-muted)">n=${c.n_te}</text>`;});
 const svg=$("#rank");svg.setAttribute("viewBox",`0 0 ${W} ${H}`);svg.innerHTML=s;bindtt("#rank");})();

$("#guards").innerHTML=[
 ["Point-in-time inputs","events + signals from the audited ≤-now harness (bias_lab shift-1, rolling bias ≤ entry bar)"],
 ["Train/test split","frozen 2023–24 / 2025–26; test touched once"],
 ["Multiple comparisons","BH FDR≤0.10 across all 34 hypotheses, applied once"],
 ["Sample gate","N≥30 enforced; LOW-N flagged untrusted"],
 ["Walk-forward","5 anchored folds; ≥60% positive required"],
 ["Placebo/shuffle","armed for any pass — none reached it"],
].map(r=>`<tr><td class="l" style="white-space:nowrap">${r[0]}</td><td class="l" style="color:var(--text-muted)">${r[1]}</td></tr>`).join("");

$("#mani").innerHTML=[["data md5",D.manifest.data_md5.slice(0,16)+"…"],["git",D.manifest.git.slice(0,12)],
 ["seed",D.manifest.seed],["bootstrap",D.manifest.bootstrap],["outcome",D.manifest.outcome]]
 .map(r=>`<tr><td class="l">${r[0]}</td><td class="l" style="font-family:monospace">${r[1]}</td></tr>`).join("");

(function(){const cols=[["component","component"],["n_te","n"],["te_expR","E[R]"],["te_ctr_expR","ctr"],["te_diff","diff"],["te_p","p"],["folds_pos","folds+"],["folds_valid","valid"],["tr_diff","train diff"]];
 const th=$("#tbl thead"),tb=$("#tbl tbody");
 th.innerHTML="<tr>"+cols.map(c=>`<th class="${c[0]==='component'?'l':''}" data-k="${c[0]}">${c[1]}</th>`).join("")+"</tr>";
 let rows=D.battery.slice(),asc=false,key="te_diff";
 function r(){tb.innerHTML=rows.map(x=>`<tr><td class="l">${x.component}${x.gate_n!=='OK'?' ⚠':''}</td><td>${x.n_te}</td><td>${x.te_expR}</td><td>${x.te_ctr_expR===null?'0':x.te_ctr_expR}</td><td style="color:${x.te_diff>0?'var(--pos)':'var(--neg)'}">${x.te_diff>0?'+':''}${x.te_diff}</td><td>${x.te_p}</td><td>${x.folds_pos}</td><td>${x.folds_valid}</td><td>${x.tr_diff>0?'+':''}${x.tr_diff}</td></tr>`).join("");}
 th.addEventListener("click",e=>{const k=e.target.dataset.k;if(!k)return;asc=(key===k)?!asc:false;key=k;
  rows.sort((a,b)=>{const p=a[k]??-9,q=b[k]??-9;return(p>q?1:p<q?-1:0)*(asc?1:-1);});r();});r();})();

$("#verdict").innerHTML=`<div class="verdict-no">NO real, regime-robust, sample-sufficient, leakage-free component edge — Stage 1 gate closed, system not built.</div>
<ul class="vlist">
<li><b>0 of 34</b> components beat their counter-baseline with a CI above zero; <b>0</b> survive BH correction (~1.7 would look significant by luck).</li>
<li>The base reaction trade is <b>breakeven under real money</b> (+0.058 R/trade, CI [−0.10, +0.22]) — there is no edge for orchestration to amplify.</li>
<li>Top-of-table entries (momentum_5d +0.27R p=0.056, early_entry +0.38R p=0.11) show <b>no train→test persistence</b> — best-of-34 luck, and the placebo audit was never reached because the primary gate already failed.</li>
<li>The multi-agent swarm + meta-learner would add nothing: this session's earlier walk-forward learner scored <b>below a coin flip</b> learning from exactly this kind of noise.</li>
</ul>
<div class="note2" style="margin-top:8px"><b>What survives all of this session's testing:</b> the proven money edge remains the <b>mechanical Champion v1.1 / canonical baseline execution</b> (selective entries, structural stops, caps) — not any predictive bias layer. Honest null delivered per directive 5: no edge, no system.</div>`;

function bindtt(sel){const el=$(sel),tt=$("#tt");el.addEventListener("mousemove",e=>{const t=e.target.dataset.t;
 if(!t){tt.style.display="none";return;}tt.style.display="block";tt.style.left=(e.clientX+14)+"px";tt.style.top=(e.clientY-10)+"px";tt.textContent=t;});
 el.addEventListener("mouseleave",()=>tt.style.display="none");}
</script>"""

EXTRA = """<style>
.p{font-size:13px;line-height:1.5;color:var(--text)}
.verdict-no{font-size:16px;font-weight:700;color:var(--neg);margin-bottom:8px}
.vlist{margin:0;padding-left:18px;font-size:13px;line-height:1.6;color:var(--text)}
.vlist li{margin-bottom:4px}
</style>"""
out = CSS + EXTRA + BODY + SCRIPT.replace("__DATA__", DATA)
for bad in ["<!doctype", "<html", "<head", "<body", "</html"]:
    assert bad not in out.lower(), bad
open(f"{S}/stage1_artifact.html", "w").write(out)
print("written stage1_artifact.html", len(out))
