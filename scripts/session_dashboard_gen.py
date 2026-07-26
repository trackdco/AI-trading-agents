#!/usr/bin/env python3
"""Session-profile (London method) accuracy dashboard -> Artifact HTML."""
import json
import pandas as pd

import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
J = pd.read_csv(f"{S}/session_profile_days.csv", dtype={"day": str})
J["mo"] = J.day.str.slice(0, 7)
D = J[J.bias != "NEUTRAL"].copy()
acc = lambda x: round(100 * (x.verdict == "CORRECT").mean(), 1) if len(x) else 0.0
expf = lambda x: round(100 * x.expansion_ok.mean(), 1) if len(x) else 0.0

head = dict(days=len(J), dirn=len(D), aside=len(J) - len(D),
            strict=acc(D), expn=expf(D),
            mix=J.profile.value_counts().to_dict(),
            bull=acc(D[D.bias == "BULLISH"]), bear=acc(D[D.bias == "BEARISH"]))

# profile x direction (the key chart)
pxd = []
for p in ["A", "B", "C"]:
    for b in ["BULLISH", "BEARISH"]:
        x = D[(D.profile == p) & (D.bias == b)]
        if len(x):
            pxd.append(dict(k=f"{p} {b[:4].lower()}", p=p, b=b, n=len(x), acc=acc(x), exp=expf(x)))
prof = [dict(p=p, n=int((D.profile == p).sum()), acc=acc(D[D.profile == p]), exp=expf(D[D.profile == p]))
        for p in ["A", "B", "C"] if (D.profile == p).any()]
# cross-check + news
both = J[(J.bias != "NEUTRAL") & (J.ict_weekly.isin(["BULLISH", "BEARISH"]))]
cross = dict(agree_n=int(both.agree.sum()), agree_acc=acc(both[both.agree]),
             dis_n=int((~both.agree).sum()), dis_acc=acc(both[~both.agree]))
monthly = [dict(mo=mo, n=len(g), acc=acc(g), exp=expf(g)) for mo, g in D.groupby("mo")]
log = J[["day", "weekday", "profile", "raw_bias", "bias", "conviction", "net", "verdict",
         "expansion_ok", "newsday", "ict_weekly", "agree", "note"]].to_dict("records")
DATA = json.dumps(dict(head=head, pxd=pxd, prof=prof, cross=cross, monthly=monthly, log=log),
                  separators=(",", ":"))

CSS = open(f"{S}/_css_block.txt").read().replace('CSS = """', "").rstrip('"')

BODY = """
<h1>Session-Profile Daily Bias (London method) — NQ, Jul 2025 → Jul 2026</h1>
<div class="sub"><b>Read the previous session, don't predict.</b> At 08:00 ET (London complete) the engine reads what London (03:00–08:00) did around HTF draws (PDH/PDL, Asia H/L, 1H swings) and maps to one profile: <b>A</b> London consolidated → expect NY to sweep then reverse · <b>B</b> London swept but hasn't reversed → NY delivers the reversal away from the swept side · <b>C</b> London swept + already reversed → NY continues (after an LTF sweep). Direction: low-sweep+reversal → bullish/target highs; high-sweep+reversal → bearish/target lows. News-gated to stand-aside; ambiguity → NEUTRAL. Graded on the <b>NY session (09:30→16:00)</b>: strict = closed with the bias; expansion = swept-against-then-expanded.</div>
<div class="tiles" id="tiles"></div>
<section><h2>The decisive cut: profile × direction — bullish reads work, bearish reads fail</h2>
<div class="card"><div class="legend">series:<span class="sw" style="background:var(--series-1)"></span>strict<span class="sw" style="background:var(--series-2)"></span>expansion</div>
<svg id="pxd" width="100%" height="240" viewBox="0 0 960 240"></svg>
<div class="note2">Every bearish sub-profile is a coin-flip-or-worse; Profile C bearish (continuation-down) is the worst at 21%. Profile C <b>bullish</b> — London swept lows + reversed up, NY continues up — is the one clean edge (50% / 52%). The window was a bull market: counter-trend shorts get punished regardless of method.</div></div></section>
<section class="grid3">
<div class="card"><h2>By profile (both directions)</h2><table id="pf"></table></div>
<div class="card"><h2>Cross-check vs the weekly-ICT engine</h2><table id="cx"></table><div class="note2">When both engines agree on direction, accuracy did NOT improve — the two reads aren't complementary here.</div></div>
<div class="card"><h2>Bull vs bear (all profiles)</h2><table id="bb"></table><div class="note2">The single repeatable result across all three bias frameworks tested: long-side ~50%, short-side well below.</div></div>
</section>
<section><h2>Monthly — strict vs expansion (directional days)</h2><div class="card"><svg id="mo" width="100%" height="210" viewBox="0 0 960 210"></svg></div></section>
<section><h2>Every day — London profile, the call, and what NY did (sortable)</h2>
<div class="card" style="max-height:560px;overflow:auto"><table id="log"><thead></thead><tbody></tbody></table></div>
<div class="note2">raw = the profile's bias before the news gate; bias = after gating (NEUTRAL on red-folder days). ⚡ = NY swept-then-expanded. 🤝 = agreed with the weekly engine.</div></section>
<div class="tt" id="tt"></div>
"""

SCRIPT = """<script>
const DATA=__DATA__;const $=s=>document.querySelector(s);const H=DATA.head;
$("#tiles").innerHTML=[
 ["Days examined",H.days,"trading days"],["Directional calls",H.dirn,"stood aside "+H.aside],
 ["Strict accuracy",H.strict+"%","NY closed with bias"],["Expansion accuracy",H.expn+"%","swept then expanded"],
 ["Bullish reads",H.bull+"%","long side"],["Bearish reads",H.bear+"%","short side"],
 ["Profile mix",(H.mix.A||0)+" / "+(H.mix.B||0)+" / "+(H.mix.C||0),"A / B / C (raw)"],
].map(t=>`<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div><div class="s">${t[2]}</div></div>`).join("");
(function(){const W=DATA.pxd,Wd=960,Hh=240,P={l:40,r:10,t:14,b:34},n=W.length;
 const gw=(Wd-P.l-P.r)/n,bw=Math.min(30,gw/2-5);const ys=v=>P.t+(Hh-P.t-P.b)*(1-v/100);
 let g='<g class="grid">';for(const v of[0,25,50,75,100]){g+=`<line x1="${P.l}" x2="${Wd-P.r}" y1="${ys(v)}" y2="${ys(v)}"${v===50?' stroke-dasharray="4,3"':''}/><text x="${P.l-6}" y="${ys(v)+4}" text-anchor="end">${v}</text>`;}g+='</g>';
 let s='';W.forEach((d,i)=>{const cx=P.l+i*gw+gw/2;
  s+=`<rect x="${cx-bw-1}" y="${ys(d.acc)}" width="${bw}" height="${(Hh-P.t-P.b)-(ys(d.acc)-P.t)}" rx="4" fill="var(--series-1)" data-t="${d.k}: strict ${d.acc}% (n=${d.n})"/>`;
  s+=`<rect x="${cx+1}" y="${ys(d.exp)}" width="${bw}" height="${(Hh-P.t-P.b)-(ys(d.exp)-P.t)}" rx="4" fill="var(--series-2)" data-t="${d.k}: expansion ${d.exp}%"/>`;
  s+=`<text x="${cx}" y="${Hh-15}" text-anchor="middle">${d.k}</text><text x="${cx}" y="${Hh-3}" text-anchor="middle" style="fill:var(--text-muted)">n=${d.n}</text>`;});
 $("#pxd").innerHTML=g+s;bindtt("#pxd");})();
$("#pf").innerHTML="<tr><th class='l'>profile</th><th>days</th><th>strict</th><th>exp</th></tr>"+DATA.prof.map(p=>`<tr><td class="l">${p.p}</td><td>${p.n}</td><td>${p.acc}%</td><td>${p.exp}%</td></tr>`).join("");
$("#cx").innerHTML="<tr><th class='l'>vs weekly</th><th>days</th><th>strict</th></tr>"+`<tr><td class="l">agree</td><td>${DATA.cross.agree_n}</td><td>${DATA.cross.agree_acc}%</td></tr><tr><td class="l">disagree</td><td>${DATA.cross.dis_n}</td><td>${DATA.cross.dis_acc}%</td></tr>`;
$("#bb").innerHTML="<tr><th class='l'>side</th><th>strict</th></tr>"+`<tr><td class="l bull">BULLISH</td><td>${H.bull}%</td></tr><tr><td class="l bear">BEARISH</td><td>${H.bear}%</td></tr>`;
(function(){const M=DATA.monthly,Wd=960,Hh=210,P={l:40,r:10,t:12,b:26};
 const xs=i=>P.l+(Wd-P.l-P.r)*i/Math.max(1,M.length-1);const ys=v=>P.t+(Hh-P.t-P.b)*(1-v/100);
 let g='<g class="grid">';for(const v of[0,25,50,75,100]){g+=`<line x1="${P.l}" x2="${Wd-P.r}" y1="${ys(v)}" y2="${ys(v)}"${v===50?' stroke-dasharray="4,3"':''}/><text x="${P.l-6}" y="${ys(v)+4}" text-anchor="end">${v}</text>`;}g+='</g>';
 const line=(k,c)=>`<path fill="none" stroke="var(${c})" stroke-width="2" d="${M.map((m,i)=>(i?'L':'M')+xs(i)+','+ys(m[k])).join('')}"/>`;
 const dots=(k,c)=>M.map((m,i)=>`<circle cx="${xs(i)}" cy="${ys(m[k])}" r="3.5" fill="var(${c})" data-t="${m.mo}: strict ${m.acc}% / exp ${m.exp}% (n=${m.n})"/>`).join('');
 $("#mo").innerHTML=g+line("acc","--series-1")+line("exp","--series-2")+dots("acc","--series-1")+dots("exp","--series-2")+M.map((m,i)=>`<text x="${xs(i)}" y="${Hh-8}" text-anchor="middle">${m.mo.slice(2)}</text>`).join('');
 bindtt("#mo");})();
(function(){const cols=[["day","date"],["weekday","dow"],["profile","prof"],["raw_bias","raw"],["bias","bias(gated)"],["net","NY net"],["verdict","verdict"],["ict_weekly","weekly"],["note","what happened"]];
 const th=$("#log thead"),tb=$("#log tbody");
 th.innerHTML="<tr>"+cols.map(c=>`<th class="${['day','weekday','profile','raw_bias','bias','ict_weekly','note'].includes(c[0])?'l':''}" data-k="${c[0]}">${c[1]}</th>`).join("")+"</tr>";
 const bcls=b=>b==='BULLISH'?'bull':b==='BEARISH'?'bear':'neu';
 const vchip=(v,e)=>v==='CORRECT'?'<span class="chip ok">CORRECT'+(e?' ⚡':'')+'</span>':v==='WRONG'?'<span class="chip bad">WRONG</span>':v==='FLAT'?'<span class="chip fl">FLAT</span>':'<span class="chip na">ASIDE</span>';
 let rows=DATA.log.slice(),asc=false,key="day";
 function r(){tb.innerHTML=rows.map(x=>`<tr><td class="l">${x.day}</td><td class="l">${x.weekday}</td><td class="l">${x.profile}</td>
  <td class="l ${bcls(x.raw_bias)}">${x.raw_bias}</td><td class="l ${bcls(x.bias)}">${x.bias}</td>
  <td style="color:${x.net>=0?'var(--pos)':'var(--neg)'}">${x.net>0?'+':''}${x.net}</td>
  <td>${vchip(x.verdict,x.expansion_ok)}</td><td class="l ${bcls(x.ict_weekly)}">${(x.ict_weekly||'')[0]||''}${x.agree?' 🤝':''}</td>
  <td class="note">${x.note}</td></tr>`).join("");}
 th.addEventListener("click",e=>{const k=e.target.dataset.k;if(!k)return;asc=(key===k)?!asc:false;key=k;rows.sort((a,b)=>{const p=a[k],q=b[k];return(p>q?1:p<q?-1:0)*(asc?1:-1);});r();});r();})();
function bindtt(sel){const el=$(sel),tt=$("#tt");el.addEventListener("mousemove",e=>{const t=e.target.dataset.t;
 if(!t){tt.style.display="none";return;}tt.style.display="block";tt.style.left=(e.clientX+14)+"px";tt.style.top=(e.clientY-10)+"px";tt.textContent=t;});
 el.addEventListener("mouseleave",()=>tt.style.display="none");}
</script>"""

out = CSS + BODY + SCRIPT.replace("__DATA__", DATA)
for bad in ["<!doctype", "<html", "<head", "<body", "</html"]:
    assert bad not in out.lower(), bad
open(f"{S}/session_profile_artifact.html", "w").write(out)
print("written session_profile_artifact.html", len(out))
