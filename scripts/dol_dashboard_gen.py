#!/usr/bin/env python3
"""Rolling-bias -> DOL reach dashboard -> Artifact HTML (no wrapper tags)."""
import json
import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
D = json.load(open(f"{S}/dol_eval.json"))
CSS = open(f"{S}/_css_block.txt").read().replace('CSS = """', "").rstrip('"')
DATA = json.dumps(D, separators=(",", ":"))

BODY = """
<h1>Does a rolling bias help price reach the DOL? — 09:40–10:15 entries</h1>
<div class="sub"><b>Question:</b> with a bias re-evaluated every bar up to the entry moment (≤-now), when a breakout initiates inside 09:40–10:15, does price reach the bias-side draw-on-liquidity <b>before</b> invalidation — resolution allowed after 10:15? Full 2023→Jul 2026 1-min NQ, same feature frame / DST / holiday / Wilson-CI / walk-forward discipline as the prior runs. <b>The headline reach-% looked like a win; it isn't — and this page shows exactly why.</b></div>

<div class="tiles" id="tiles"></div>

<section><h2>1 · The rolling bias genuinely rolls (not a frozen 08:00 snapshot)</h2>
<div class="card"><table id="flips"></table>
<div class="note2">The bias flips on ~half of days between 08:00 and the entry — it tracks premarket evidence and updates, exactly as required. Coverage: <b id="cov"></b> of eligible days produce an in-window breakout with a defined DOL. Median time-to-resolution <b id="ttr"></b> min; <b id="after"></b> of trades resolve <b>after</b> 10:15 (the no-timeout rule matters).</div></div></section>

<section><h2>2 · The breakout→DOL reaction itself has no <i>directional</i> edge</h2>
<div class="grid3">
<div class="card"><h3>Reach vs its own mirror</h3><table id="mirror"></table>
<div class="note2">From the breakout point, the breakout-direction pool is reached <b>no more often</b> than an equidistant pool the opposite way. Post-breakout momentum ≈ 0 — the reaction doesn't predict its own direction.</div></div>
<div class="card"><h3>Reach across stop definitions</h3><svg id="stops" width="100%" height="180" viewBox="0 0 380 180"></svg>
<div class="note2">Monotone with stop size, no special peak — not curve-fit to one stop. Structural (15–70) reach ≈ <b id="rte"></b>%.</div></div>
<div class="card"><h3>Why reach looks "profitable"</h3><p class="p">Draws sit ~2.9R away, so even a 36% reach beats the 26% breakeven — <b>but this is symmetric</b> (works either side). It's "volatility eventually tags a far pool," not a tradeable direction. You still need something to tell you <i>which</i> side.</p></div>
</div></section>

<section><h2>3 · The trap: "aligned reaches +20pp more" is <span class="neg">nearer draws, not direction</span></h2>
<div class="grid3">
<div class="card"><h2>What it looks like</h2><table id="ctrlb"></table>
<div class="note2">Breakouts <b>aligned</b> with the rolling bias reach their DOL 43.9% vs 23.9% for <b>counter</b> — a +20pp raw lift, CI clears zero. Looks decisive.</div></div>
<div class="card"><h2>What's actually going on</h2><svg id="geo" width="100%" height="210" viewBox="0 0 380 210"></svg>
<div class="note2">Aligned draws sit at <b>48pt</b>; counter draws at <b>122pt</b> — same ~40pt stop. The nearer target is reached more often <i>by construction</i>, and pays less.</div></div>
<div class="card"><h2>R-adjusted: both breakeven</h2><table id="radj"></table>
<div class="note2">Once you credit each win its actual R, aligned E[R] <b>+0.017</b> and counter <b>−0.025</b> — both straddle zero. R-matched within buckets the gap flips sign (+24 / −5 / +7pp). <b>No directional edge survives.</b></div></div>
</div></section>

<section><h2>4 · Real Campion money confirms it — the bias adds nothing to P&L</h2>
<div class="card"><table id="m2"></table>
<div class="note2">Under the real rules (pad-20 stop, &gt;40→5-micro derisk, nearest-draw target capped 4R, slip+commission): <b>aligned is breakeven (PF 1.00, E[R] +0.02)</b> and <i>no better than</i> counter (PF 1.07). Max drawdown dwarfs net P&L on both. The reach advantage evaporates because aligned setups carry unfavourable R.</div></div></section>

<section class="grid3">
<div class="card" style="grid-column:span 2"><h2>Walk-forward — the raw-reach lift is the geometry artifact repeating</h2>
<div style="overflow:auto"><table id="folds"></table></div>
<div class="note2">Aligned raw-reach is higher in all 5 folds (2 clear zero) — but that's the same "aligned = nearer draw" selection recurring, not an out-of-sample directional edge, as the R-adjusted and money views show.</div></div>
<div class="card"><h2>By VIX regime</h2><table id="vix"></table>
<div class="note2">The raw-reach lift persists across VIX because nearer draws are reached more in every regime — again geometry, not direction.</div></div>
</section>

<section><h2>Verdict</h2><div class="card"><div id="verdict"></div></div></section>
<div class="tt" id="tt"></div>
"""

SCRIPT = r"""<script>
const D=__DATA__;const $=s=>document.querySelector(s);const g=D.geometry;
const A=g.rows.find(r=>r.who==='aligned'),C=g.rows.find(r=>r.who==='counter');
$("#tiles").innerHTML=[
 ["Breakouts w/ DOL",D.breakouts,D.coverage_pct+"% of eligible days"],
 ["Reaction reach",D.reach_te.pct+"%","test; but symmetric (no direction)"],
 ["Aligned raw lift","+"+(D.ctrlB.aligned_te.pct-D.ctrlB.counter_te.pct).toFixed(1)+"pp","looks like edge…"],
 ["…is nearer draws","48 vs 122pt","aligned vs counter DOL distance"],
 ["R-adjusted edge","≈ 0 R","both sides breakeven"],
 ["Verdict",D.proven?"PROVEN":"NOT PROVEN","bias adds no tradeable direction"],
].map(t=>`<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div><div class="s">${t[2]}</div></div>`).join("");

$("#cov").textContent=D.coverage_pct+"%";$("#ttr").textContent=D.ttr_median;
$("#after").textContent=Math.round(100*D.res_after_1015/D.breakouts)+"%";$("#rte").textContent=D.reach_te.pct;
const fl=D.flips;
$("#flips").innerHTML="<tr><th class='l'>bias change</th><th>days</th><th>share</th></tr>"+
 [["08:00 → 09:30",fl.chg_8_930,fl.n_all],["09:30 → breakout",fl.chg_930i,fl.n_init],["any 08:00 → breakout",fl.chg_any,fl.n_init]]
 .map(r=>`<tr><td class="l">${r[0]}</td><td>${r[1]}/${r[2]}</td><td>${Math.round(100*r[1]/r[2])}%</td></tr>`).join("");

$("#mirror").innerHTML="<tr><th class='l'>from the breakout point</th><th>reach</th></tr>"+
 `<tr><td class="l">breakout-direction pool</td><td>${D.reach_te.pct}%</td></tr>`+
 `<tr><td class="l">equidistant opposite pool</td><td>${D.mirror_te.pct}%</td></tr>`+
 `<tr><td class="l" style="color:var(--text-muted)">momentum gap</td><td style="color:var(--text-muted)">${(D.reach_te.pct-D.mirror_te.pct>0?'+':'')}${(D.reach_te.pct-D.mirror_te.pct).toFixed(1)}pp</td></tr>`;

(function(){const F=D.fixed,W=380,H=180,P={l:34,r:12,t:12,b:40};
 const mx=Math.max(...F.map(f=>f.pct));const bw=(W-P.l-P.r)/F.length*0.6;
 let s='';F.forEach((f,i)=>{const x=P.l+(W-P.l-P.r)*(i+0.5)/F.length;const h=(H-P.t-P.b)*f.pct/mx;
  s+=`<rect x="${x-bw/2}" y="${H-P.b-h}" width="${bw}" height="${h}" rx="3" fill="var(--series-1)" data-t="${f.lbl}: ${f.pct}% (n${f.n})"/>`;
  s+=`<text x="${x}" y="${H-P.b-h-4}" text-anchor="middle" style="font-size:10px">${f.pct}%</text>`;
  s+=`<text x="${x}" y="${H-P.b+14}" text-anchor="middle" style="font-size:9px;fill:var(--text-muted)">${f.lbl.replace('structural','struct')}</text>`;});
 $("#stops").innerHTML=s;bindtt("#stops");})();

$("#ctrlb").innerHTML="<tr><th class='l'>breakout</th><th>reach</th><th>95% CI</th><th>n</th></tr>"+
 [["aligned",D.ctrlB.aligned_te],["counter",D.ctrlB.counter_te],["no-bias",D.ctrlB.nobias_te]]
 .map(([l,r])=>`<tr><td class="l">${l}</td><td>${r.pct}%</td><td>[${r.ci[0]},${r.ci[1]}]</td><td>${r.n}</td></tr>`).join("")+
 `<tr><td class="l" style="color:var(--pos)">raw lift</td><td colspan="3" style="color:var(--pos)">+${(D.ctrlB.aligned_te.pct-D.ctrlB.counter_te.pct).toFixed(1)}pp (CI clears 0)</td></tr>`;

// geometry bars: DOL distance aligned vs counter
(function(){const rows=[["aligned DOL",A.dol_med,'var(--series-1)'],["counter DOL",C.dol_med,'var(--neg)'],["stop (both)",A.stop_med,'var(--text-muted)']];
 const W=380,H=210,P={l:96,r:40,t:16,b:20};const mx=Math.max(...rows.map(r=>r[1]));
 let s='';rows.forEach((r,i)=>{const y=P.t+i*52;const w=(W-P.l-P.r)*r[1]/mx;
  s+=`<text x="${P.l-8}" y="${y+18}" text-anchor="end" style="font-size:11px">${r[0]}</text>`;
  s+=`<rect x="${P.l}" y="${y+4}" width="${w}" height="26" rx="4" fill="${r[2]}"/>`;
  s+=`<text x="${P.l+w+6}" y="${y+22}" style="font-size:12px;font-weight:600">${r[1]}pt</text>`;});
 s+=`<text x="${P.l}" y="${H-2}" style="font-size:10px;fill:var(--text-muted)">nearer target → reached more often, pays less</text>`;
 $("#geo").innerHTML=s;})();

$("#radj").innerHTML="<tr><th class='l'>breakout</th><th>reach</th><th>meanR</th><th>E[R]/trade</th></tr>"+
 g.rows.map(r=>`<tr><td class="l">${r.who}</td><td>${r.reach}%</td><td>${r.meanR}</td><td style="color:${r.expR>0.05?'var(--pos)':Math.abs(r.expR)<0.05?'var(--text-muted)':'var(--neg)'}">${r.expR>0?'+':''}${r.expR}</td></tr>`).join("");

$("#m2").innerHTML="<tr><th class='l'>alignment</th><th>trades</th><th>E[R]</th><th>win%</th><th>win R</th><th>net $</th><th>maxDD $</th><th>PF</th></tr>"+
 [["aligned",D.m2.aligned],["counter",D.m2.counter],["no-bias",D.m2.nobias],["ALL",D.m2.all]].filter(x=>x[1]).map(([l,m])=>
 `<tr><td class="l">${l}</td><td>${m.n}</td><td style="color:${m.expR>0.1?'var(--pos)':'var(--text-muted)'}">${m.expR>0?'+':''}${m.expR}</td><td>${m.wr}%</td><td>${m.winR}</td><td>${m.usd}</td><td style="color:var(--neg)">${m.dd}</td><td>${m.pf}</td></tr>`).join("");

$("#folds").innerHTML="<tr><th class='l'>test block</th><th>aligned</th><th>counter</th><th>raw lift</th><th>95% CI</th></tr>"+
 D.folds.map(f=>`<tr><td class="l">${f.test}</td><td>${f.a}% <span style="font-size:9px;color:var(--text-muted)">n${f.n_al}</span></td><td>${f.c}% <span style="font-size:9px;color:var(--text-muted)">n${f.n_co}</span></td><td style="color:${f.lift>0?'var(--pos)':'var(--neg)'}">${f.lift>0?'+':''}${f.lift}pp</td><td style="color:${f.lo>0?'var(--pos)':'var(--text-muted)'}">[${f.lo},${f.hi}]</td></tr>`).join("");

$("#vix").innerHTML="<tr><th class='l'>VIX</th><th>n</th><th>aligned</th><th>counter</th></tr>"+
 D.vix.filter(v=>v.n>3).map(v=>`<tr><td class="l">${v.vix}</td><td>${v.n}</td><td>${v.aligned}%</td><td>${v.counter}%</td></tr>`).join("");

$("#verdict").innerHTML=`<div class="verdict-no">NOT PROVEN — the rolling bias adds no tradeable directional edge to DOL reach.</div>
<ul class="vlist">
<li>The bias <b>does roll</b> (flips on ~half of days) and the harness is clean — no lookahead, resolution allowed past 10:15, holidays/DST handled.</li>
<li>The breakout→DOL reaction reaches the pool ~36%, but <b>symmetric</b> (opposite pool 37%) — the reaction has <b>no direction</b> of its own.</li>
<li>The eye-catching <b>+20pp "aligned reaches more"</b> is a <b>geometry artifact</b>: aligned draws sit at 48pt vs counter's 122pt. Nearer targets are hit more often and pay less.</li>
<li>R-adjusted, <b>both sides are breakeven</b> (aligned +0.017R, counter −0.025R, CIs straddle zero); R-matched, the gap flips sign; and under <b>real Campion money the bias is no better than counter</b> (PF 1.00 vs 1.07, drawdown ≫ profit).</li>
</ul>
<div class="note2" style="margin-top:8px"><b>Actionable read:</b> the draw gets tagged often enough <i>both ways</i> that the DOL is best played <b>reactively from confirmation</b>, not predicted. The rolling bias is at most a mild <b>size/skip tilt</b> (lean lighter on counter-bias breakouts, whose draws are far) — it is <b>not</b> a P&L engine. This is the same conclusion the direction and window tests reached, now shown for the DOL-reach framing too.</div>`;

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
open(f"{S}/dol_reach_artifact.html", "w").write(out)
print("written dol_reach_artifact.html", len(out))
