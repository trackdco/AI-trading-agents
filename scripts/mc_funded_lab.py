"""Monte Carlo lab for the funded eval + payout cycle, on the SHIPPED agent book.

House pattern (CANON-QA-LOG Phase 5, entries 42-46): day-level bootstrap that resamples
WHOLE days with intraday order preserved, seeded RNG, modes for eval / funded year /
full cycle, controls above charts, same palette and tile grammar as the desk dashboard.

The day-P&L pool is the desk-run-2 agent book (763 trades, 230 days) pushed through the
REAL funded sim (`funded_book.run`) once per base size — so micro rounding, the daily
budget, soft de-risk and the ramp are all in the vectors, not approximated client-side.
Account mechanics (trailing EOD DD, lock, eval target, payout trigger/amount/cap) run
in the browser so every knob is live.

    python -m scripts.mc_funded_lab            # writes mc_funded_lab.html
"""
from __future__ import annotations

import json
import sys

import pandas as pd

import scripts.funded_book as fb
from scripts.capture_desk_run import ROOT, RUNS
from scripts.capture_replay import load_trades

BASES = [100, 120, 140, 150, 160, 180, 200, 220, 240]


def day_vectors() -> dict:
    T = load_trades("fit")
    O = pd.read_parquet(ROOT / "output/aikido_cr_fit.parquet").set_index(["ts", "direction"])
    sup = set(O[O.cr_suppressed].index)
    T = [t for t in T if (t["ts"], t["direction"]) not in sup]
    O = O[~O.cr_suppressed]
    rows = [json.loads(l) for l in open(RUNS / "journal.jsonl")]
    jmap = {r["trade_id"]: r for r in rows}
    V = pd.DataFrame([{"trade_id": t["trade_id"], "day": t["day"], "ts": t["ts"],
                       "fill": t["fill"], "month": t["day"][:7],
                       "exit": pd.to_datetime(jmap[t["trade_id"]]["exit_ts"], utc=True),
                       "risk": t["risk"], "tier": t["tier"], "elite": t["elite"],
                       "dollars_1lot": jmap[t["trade_id"]]["agent_dollars"],
                       "sess": t["sess"]} for t in T]).sort_values("fill", kind="mergesort")
    alldays = sorted(V.day.unique())
    # Per base: full-size vector plus HALF and QUARTER vectors through the REAL sim —
    # the live de-risk ramp (half below $1,000 of buffer, quarter below $500, ANGUS
    # 2026-07-30) is applied by the browser engine by picking the vector that matches
    # the path's own buffer each day. Re-simulating at the ramped base keeps micro
    # rounding exact where linear scaling would lie (small rd rounds to whole micros).
    out = {"days": alldays, "base": {}, "grid": {}}

    def vec(eff: float) -> list:
        key = f"_mc{eff:g}"
        fb.PROFILES[key] = dict(base=eff, per=0.0, step=2000.0, after=3000.0, cap=eff)
        B = fb.run(V, key)
        return [round(x, 2)
                for x in B.groupby("day").pl.sum().reindex(alldays).fillna(0.0).tolist()]

    for b in BASES:
        out["base"][str(b)] = {"f": vec(float(b)), "h": vec(b / 2.0), "q": vec(b / 4.0)}
    # $40 grid for SCALED plans: the browser walks base_for(buffer) x ramp along the
    # ladder and snaps to the nearest grid vector — every step re-simulated for real.
    for g in range(40, 641, 40):
        out["grid"][str(g)] = vec(float(g))
    return out


HTML = r"""<title>MC lab — funded eval + payouts (agent book)</title>
<style>
:root{--bg:#F6F5F2;--panel:#FFF;--ink:#23282E;--ink2:#6A7178;--line:#E3E1DB;--line2:#EFEDE8;
--agent:#2a78d6;--v8:#eb6834;--pos:#2C7A57;--neg:#B04A38;--grid:#ECEAE4;--band:#2a78d622}
@media(prefers-color-scheme:dark){:root{--bg:#12151A;--panel:#191D24;--ink:#E4E6E9;--ink2:#8B929B;
--line:#2A3039;--line2:#232830;--agent:#3987e5;--v8:#d95926;--pos:#5BB98C;--neg:#D97B66;--grid:#232830;--band:#3987e522}}
:root[data-theme=dark]{--bg:#12151A;--panel:#191D24;--ink:#E4E6E9;--ink2:#8B929B;--line:#2A3039;
--line2:#232830;--agent:#3987e5;--v8:#d95926;--pos:#5BB98C;--neg:#D97B66;--grid:#232830;--band:#3987e522}
:root[data-theme=light]{--bg:#F6F5F2;--panel:#FFF;--ink:#23282E;--ink2:#6A7178;--line:#E3E1DB;
--line2:#EFEDE8;--agent:#2a78d6;--v8:#eb6834;--pos:#2C7A57;--neg:#B04A38;--grid:#ECEAE4;--band:#2a78d622}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.45 system-ui,sans-serif;padding:32px 16px 56px}
.wrap{max-width:960px;margin:0 auto;display:flex;flex-direction:column;gap:18px}
h1{font-size:19px;font-weight:650;margin:0}.sub{color:var(--ink2);font-size:13px;margin:0}
section{background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:hidden}
.cap{padding:11px 16px 9px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:baseline}
.cap h2{font-size:11.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;margin:0}
.cap span{color:var(--ink2);font-size:11.5px}
.controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:10px;padding:14px 16px}
.ctl label{display:block;font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);font-weight:600;margin-bottom:3px}
.ctl input,.ctl select{width:100%;background:var(--bg);color:var(--ink);border:1px solid var(--line);
border-radius:6px;padding:6px 8px;font:13px system-ui;font-variant-numeric:tabular-nums}
.runrow{display:flex;gap:10px;align-items:center;padding:0 16px 14px}
button{background:var(--agent);color:#fff;border:none;border-radius:6px;padding:8px 22px;
font:600 13px system-ui;cursor:pointer}button:hover{filter:brightness(1.08)}
.note{color:var(--ink2);font-size:12px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.tile .k{font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);font-weight:600}
.tile .v{font-size:19px;font-weight:650;font-variant-numeric:tabular-nums}
.tile .d{font-size:11.5px;color:var(--ink2)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:760px){.grid2{grid-template-columns:1fr}}
.chart{position:relative;padding:8px 8px 4px}
svg{display:block;width:100%}svg text{font:10px system-ui;fill:var(--ink2)}
.tip{position:absolute;pointer-events:none;background:var(--panel);border:1px solid var(--line);
border-radius:6px;padding:6px 9px;font:12px system-ui;color:var(--ink);box-shadow:0 2px 8px #0002;
display:none;white-space:nowrap;z-index:5}
</style>
<div class="wrap">
<header><h1>Monte Carlo — funded eval + payout cycle</h1>
<p class="sub">pool: the SHIPPED agent book (763 trades, 230 days, three-rule canon) through the
real funded sim per base · whole-day bootstrap, intraday order preserved · seeded</p></header>

<section><div class="cap"><h2>Controls</h2><span>day P&amp;L vectors are exact per base — sizing is never linearly scaled</span></div>
<div class="controls">
<div class="ctl"><label>mode</label><select id="mode">
<option value="funded">funded year</option><option value="eval">eval only</option>
<option value="cycle">full cycle (eval → funded)</option></select></div>
<div class="ctl"><label>sizing plan</label><select id="plan">
<option value="fixed">fixed base</option>
<option value="scaled" selected>scaled ladder</option></select></div>
<div class="ctl"><label>base sizing $</label><select id="base"></select></div>
<div class="ctl"><label>scale +$ / step</label><input id="sper" type="number" value="80" step="10"></div>
<div class="ctl"><label>scale step $</label><input id="sstep" type="number" value="2000" step="500"></div>
<div class="ctl"><label>scale after +$</label><input id="safter" type="number" value="3000" step="500"></div>
<div class="ctl"><label>base cap $</label><input id="scap" type="number" value="640" step="40"></div>
<div class="ctl"><label>trailing EOD DD $</label><input id="dd" type="number" value="2000" step="100"></div>
<div class="ctl"><label>line locks at $</label><input id="lock" type="number" value="50000" step="100"></div>
<div class="ctl"><label>start balance $</label><input id="start" type="number" value="50000" step="1000"></div>
<div class="ctl"><label>eval target +$</label><input id="target" type="number" value="3000" step="500"></div>
<div class="ctl"><label>payout trigger +$</label><input id="ptrig" type="number" value="4000" step="500"></div>
<div class="ctl"><label>payout amount $</label><input id="pamt" type="number" value="2000" step="500"></div>
<div class="ctl"><label>payout cap (0=∞)</label><input id="pcap" type="number" value="0" step="1"></div>
<div class="ctl"><label>win days / cycle</label><input id="wreq" type="number" value="5" step="1"></div>
<div class="ctl"><label>win day min $</label><input id="wmin" type="number" value="150" step="50"></div>
<div class="ctl"><label>horizon days</label><input id="hor" type="number" value="252" step="21"></div>
<div class="ctl"><label>sims</label><input id="sims" type="number" value="2000" step="500"></div>
<div class="ctl"><label>seed</label><input id="seed" type="number" value="42" step="1"></div>
</div>
<div class="runrow"><button id="run">Run</button><span class="note" id="status"></span></div>
</section>

<div class="tiles" id="tiles"></div>

<section><div class="cap"><h2>Equity fan</h2><span id="fansub"></span></div>
<div class="chart" id="fanwrap"><svg id="fan" height="300"></svg><div class="tip" id="fantip"></div></div></section>

<div class="grid2">
<section><div class="cap"><h2 id="h1t">Payouts per year</h2><span>distribution over sims</span></div>
<div class="chart" id="h1wrap"><svg id="hist1" height="230"></svg><div class="tip" id="h1tip"></div></div></section>
<section><div class="cap"><h2 id="h2t">Final balance + withdrawn</h2><span>total value at horizon</span></div>
<div class="chart" id="h2wrap"><svg id="hist2" height="230"></svg><div class="tip" id="h2tip"></div></div></section>
</div>
<p class="sub">Whole-day bootstrap from the fit-span agent book — regime mix is the fit span's.
The vectors carry the real sim's budget gates, soft de-risk and micro rounding at each base,
and the LIVE DE-RISK RAMP is enforced path-by-path: below $1,000 of buffer the day runs the
half-size vector, below $500 the quarter-size vector — each re-simulated through the real
funded sim, not linearly scaled. Trailing line ratchets on EOD balance, never down, and
freezes at the lock. Payout:
whenever EOD balance ≥ start+trigger (and funded), AND the winning-day clock has ≥ the required count since the last
payout (a winning day = day P&amp;L above the min $; the clock resets on each payout and runs in
the funded stage only), withdraw the amount. Bust: EOD balance ≤ line.</p>
</div>
<script>
const DATA = __DATA__;
const $=id=>document.getElementById(id);
const bsel=$("base");
for(const b of Object.keys(DATA.base).map(Number).sort((a,b)=>a-b)){
  const o=document.createElement("option");o.value=b;o.textContent="$"+b;if(b===160)o.selected=true;bsel.appendChild(o);}
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);
t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;}}
const fmt$=x=>(x<0?"-$":"$")+Math.abs(Math.round(x)).toLocaleString();

function simulate(){
  const P={mode:$("mode").value,plan:$("plan").value,base:+bsel.value,dd:+$("dd").value,
    lock:+$("lock").value,start:+$("start").value,target:+$("target").value,
    ptrig:+$("ptrig").value,pamt:+$("pamt").value,pcap:+$("pcap").value,
    sper:+$("sper").value,sstep:+$("sstep").value,safter:+$("safter").value,scap:+$("scap").value,
    wreq:+$("wreq").value,wmin:+$("wmin").value,
    H:+$("hor").value,S:+$("sims").value,seed:+$("seed").value};
  const V=DATA.base[String(P.base)];
  const plF=Float64Array.from(V.f),plH=Float64Array.from(V.h),plQ=Float64Array.from(V.q);
  const N=plF.length;
  const gkeys=Object.keys(DATA.grid).map(Number).sort((a,b)=>a-b);
  const gvec={};for(const k of gkeys)gvec[k]=Float64Array.from(DATA.grid[String(k)]);
  const snap=e=>{let best=gkeys[0];for(const k of gkeys)if(Math.abs(k-e)<Math.abs(best-e))best=k;return best;};
  // day P&L for a given buffer: scaled ladder (base_for x ramp, snapped to the $40 grid)
  // or the fixed base's exact full/half/quarter vectors.
  const dayPl=(buf,i)=>{
    if(P.plan==="scaled"){
      let b=P.base;
      if(buf>P.safter)b=Math.min(P.scap,P.base+Math.floor((buf-P.safter)/P.sstep)*P.sper);
      const m=buf<500?0.25:buf<1000?0.5:1;
      return gvec[snap(b*m)][i];
    }
    return buf<500?plQ[i]:buf<1000?plH[i]:plF[i];
  };
  const rng=mulberry32(P.seed);
  const paths=new Float32Array(P.S*P.H);
  const payouts=new Int32Array(P.S), withdrawn=new Float64Array(P.S);
  const busted=new Uint8Array(P.S), passDay=new Int32Array(P.S).fill(-1), fundDay=new Int32Array(P.S).fill(-1);
  const firstPay=new Int32Array(P.S).fill(-1), gaps=[];
  for(let s=0;s<P.S;s++){
    let bal=P.start, line=P.start-P.dd, funded=(P.mode==="funded"), dead=false, passed=(P.mode==="funded"), wins=0, lastPay=-1;
    for(let t=0;t<P.H;t++){
      if(!dead){
        const i=(rng()*N)|0;
        const p=dayPl(bal-line,i);               // sizing plan + de-risk ramp, per path
        bal+=p;
        if(bal<=line){dead=true;busted[s]=1;bal=line;}
        else{
          if(!passed && bal>=P.start+P.target){passed=true;passDay[s]=t+1;
            if(P.mode==="eval"){dead=true;}                    // eval account done
            else{funded=true;fundDay[s]=t+1;bal=P.start;line=P.start-P.dd;wins=0;} // fresh funded acct
          }
          else if(funded){
            if(p>P.wmin)wins++;                                // winning-day clock (funded only)
            if(bal>=P.start+P.ptrig && wins>=P.wreq && (P.pcap===0||payouts[s]<P.pcap)){
              bal-=P.pamt;payouts[s]++;withdrawn[s]+=P.pamt;wins=0;
              if(firstPay[s]<0)firstPay[s]=t+1;else gaps.push(t+1-lastPay);
              lastPay=t+1;}
          }
          line=Math.min(P.lock,Math.max(line,bal-P.dd));
        }
      }
      paths[s*P.H+t]=bal+withdrawn[s];   // total value incl. withdrawals
    }
  }
  return {P,paths,payouts,withdrawn,busted,passDay,fundDay,firstPay,gaps};
}

function pct(sorted,q){const i=(sorted.length-1)*q;const lo=Math.floor(i);
return sorted[lo]+(sorted[Math.min(lo+1,sorted.length-1)]-sorted[lo])*(i-lo);}

function tiles(R){
  const{P}=R;const el=$("tiles");el.innerHTML="";
  const add=(k,v,d)=>{el.insertAdjacentHTML("beforeend",
    `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div>`)};
  const pb=Array.from(R.busted).reduce((a,b)=>a+b,0)/P.S;
  if(P.mode!=="funded"){
    const pd=Array.from(R.passDay).filter(d=>d>0);
    add("P(pass eval)",(pd.length/P.S*100).toFixed(1)+"%","target +"+fmt$(P.target).slice(1));
    if(pd.length){pd.sort((a,b)=>a-b);
      add("days to pass",Math.round(pct(pd,.5)),"median · p95 "+Math.round(pct(pd,.95)));}
  }
  if(P.mode!=="eval"){
    const po=Array.from(R.payouts).sort((a,b)=>a-b);
    const wd=Array.from(R.withdrawn).sort((a,b)=>a-b);
    add("P(bust)",(pb*100).toFixed(1)+"%",P.mode==="cycle"?"across the whole cycle":"funded year");
    add("payouts",Math.round(pct(po,.5)),"median · p5 "+Math.round(pct(po,.05))+" · p95 "+Math.round(pct(po,.95)));
    const fp=Array.from(R.firstPay).filter(d=>d>0).sort((a,b)=>a-b);
    if(fp.length)add("1st payout",Math.round(pct(fp,.5))+"d",
      (P.mode==="cycle"?"from eval start":"from day 1")+" · p95 "+Math.round(pct(fp,.95))+"d");
    if(R.gaps.length){const g=R.gaps.slice().sort((a,b)=>a-b);
      add("days / cycle",Math.round(pct(g,.5)),"median between payouts · p95 "+Math.round(pct(g,.95)));}
    add("withdrawn",fmt$(pct(wd,.5)),"median over sims");
    if(P.pcap>0){const hit=po.filter(x=>x>=P.pcap).length;
      add("P(max payout)",(hit/P.S*100).toFixed(1)+"%","hit the "+P.pcap+"-payout cap");}
    else{add("p95 payouts",Math.round(pct(po,.95)),"best-case tail");}
  } else {add("P(bust in eval)",(pb*100).toFixed(1)+"%","before hitting target");}
  const fin=Array.from({length:R.P.S},(_,s)=>R.paths[s*P.H+P.H-1]).sort((a,b)=>a-b);
  add("value at horizon",fmt$(pct(fin,.5)),"median · p5 "+fmt$(pct(fin,.05)));
}

function axis(svg,x0,x1,y0,y1,W,H,pad){ // returns transforms
  const sx=v=>pad.l+(v-x0)/(x1-x0)*(W-pad.l-pad.r);
  const sy=v=>H-pad.b-(v-y0)/(y1-y0)*(H-pad.t-pad.b);
  return{sx,sy};
}
function gridlines(parts,sy,ticks,W,pad,f){for(const t of ticks){
  parts.push(`<line x1="${pad.l}" x2="${W-pad.r}" y1="${sy(t)}" y2="${sy(t)}" stroke="var(--grid)"/>`,
    `<text x="${pad.l-6}" y="${sy(t)+3}" text-anchor="end">${f(t)}</text>`);}}

function drawFan(R){
  const{P}=R;const svg=$("fan"),W=svg.clientWidth,H=300;svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
  const pad={l:58,r:14,t:12,b:22};
  const med=new Float64Array(P.H),lo=new Float64Array(P.H),hi=new Float64Array(P.H);
  const col=new Float64Array(P.S);
  for(let t=0;t<P.H;t++){for(let s=0;s<P.S;s++)col[s]=R.paths[s*P.H+t];
    const c=Float64Array.from(col).sort();med[t]=pct(c,.5);lo[t]=pct(c,.05);hi[t]=pct(c,.95);}
  let ymin=Math.min(...lo,P.start-P.dd),ymax=Math.max(...hi);
  const yr=ymax-ymin;ymin-=yr*.04;ymax+=yr*.04;
  const{sx,sy}=axis(svg,0,P.H-1,ymin,ymax,W,H,pad);
  const parts=[];
  const step=Math.pow(10,Math.floor(Math.log10(yr)));const ticks=[];
  for(let v=Math.ceil(ymin/step)*step;v<=ymax;v+=step)ticks.push(v);
  gridlines(parts,sy,ticks.length>=3?ticks:[ymin+yr*.25,ymin+yr*.55,ymin+yr*.85],W,pad,v=>fmt$(v));
  const line=(ys,cls,w,dash)=>{let d="M";for(let t=0;t<P.H;t++)d+=(t?"L":"")+sx(t).toFixed(1)+" "+sy(ys[t]).toFixed(1);
    parts.push(`<path d="${d}" fill="none" stroke="${cls}" stroke-width="${w}"${dash?` stroke-dasharray="${dash}"`:""}/>`)};
  let area="M";for(let t=0;t<P.H;t++)area+=(t?"L":"")+sx(t).toFixed(1)+" "+sy(hi[t]).toFixed(1);
  for(let t=P.H-1;t>=0;t--)area+="L"+sx(t).toFixed(1)+" "+sy(lo[t]).toFixed(1);
  parts.push(`<path d="${area}Z" fill="var(--band)"/>`);
  const nspag=Math.min(60,P.S);
  for(let s=0;s<nspag;s++){let d="M";for(let t=0;t<P.H;t++)d+=(t?"L":"")+sx(t).toFixed(1)+" "+sy(R.paths[s*P.H+t]).toFixed(1);
    parts.push(`<path d="${d}" fill="none" stroke="var(--agent)" stroke-opacity=".07" stroke-width="1"/>`);}
  line(med,"var(--agent)",2);
  parts.push(`<line x1="${pad.l}" x2="${W-pad.r}" y1="${sy(P.start)}" y2="${sy(P.start)}" stroke="var(--ink2)" stroke-dasharray="3 4" stroke-width="1"/>`,
    `<text x="${W-pad.r-2}" y="${sy(P.start)-4}" text-anchor="end">start ${fmt$(P.start)}</text>`,
    `<text x="${pad.l+4}" y="${sy(med[P.H-1])-6}" fill="var(--agent)" font-weight="600">median ${fmt$(med[P.H-1])}</text>`,
    `<text x="${(W)/2}" y="${H-6}" text-anchor="middle">trading day</text>`);
  svg.innerHTML=parts.join("");
  $("fansub").textContent=`${nspag} sample paths · 5–95% band · total value (balance + withdrawn)`;
  const tip=$("fantip"),wrap=$("fanwrap");
  wrap.onmousemove=e=>{const r=svg.getBoundingClientRect();const mx=(e.clientX-r.left)*(W/r.width);
    const t=Math.max(0,Math.min(P.H-1,Math.round((mx-pad.l)/(W-pad.l-pad.r)*(P.H-1))));
    if(mx<pad.l-6||mx>W-pad.r+6){tip.style.display="none";return;}
    tip.style.display="block";tip.style.left=(e.clientX-r.left+14)+"px";tip.style.top=(e.clientY-r.top-10)+"px";
    tip.innerHTML=`day ${t+1}<br>median <b>${fmt$(med[t])}</b><br>band ${fmt$(lo[t])} – ${fmt$(hi[t])}`;};
  wrap.onmouseleave=()=>tip.style.display="none";
}

function drawHist(svgId,wrapId,tipId,values,binf,titleF){
  const svg=$(svgId),W=svg.clientWidth,H=230;svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
  const pad={l:46,r:10,t:14,b:26};
  const{bins,x0,bw,label}=binf(values);
  const ymax=Math.max(...bins)||1;
  const sx=i=>pad.l+i/bins.length*(W-pad.l-pad.r);
  const sy=v=>H-pad.b-v/ymax*(H-pad.t-pad.b);
  const parts=[];
  gridlines(parts,sy,[ymax*.33,ymax*.66,ymax].map(Math.round),W,pad,v=>v);
  const bwpx=(W-pad.l-pad.r)/bins.length;
  for(let i=0;i<bins.length;i++){if(!bins[i])continue;
    parts.push(`<rect x="${(sx(i)+1).toFixed(1)}" y="${sy(bins[i]).toFixed(1)}" width="${Math.max(1,bwpx-2).toFixed(1)}" height="${(sy(0)-sy(bins[i])).toFixed(1)}" rx="3" fill="var(--agent)" data-i="${i}"/>`);}
  const nlab=Math.min(6,bins.length);
  for(let k=0;k<nlab;k++){const i=Math.round(k*(bins.length-1)/(nlab-1));
    const anch=k===0?"start":k===nlab-1?"end":"middle";
    const xl=k===0?pad.l:k===nlab-1?W-pad.r:sx(i)+bwpx/2;
    parts.push(`<text x="${xl.toFixed(1)}" y="${H-8}" text-anchor="${anch}">${label(i)}</text>`);}
  svg.innerHTML=parts.join("");
  const tip=$(tipId),wrap=$(wrapId);
  wrap.onmousemove=e=>{const r=svg.getBoundingClientRect();const mx=(e.clientX-r.left)*(W/r.width);
    const i=Math.floor((mx-pad.l)/bwpx);
    if(i<0||i>=bins.length||!bins[i]){tip.style.display="none";return;}
    tip.style.display="block";tip.style.left=(e.clientX-r.left+14)+"px";tip.style.top=(e.clientY-r.top-10)+"px";
    tip.innerHTML=titleF(i,bins[i]);};
  wrap.onmouseleave=()=>tip.style.display="none";
}

function run(){
  const t0=performance.now();
  const R=simulate();
  tiles(R);drawFan(R);
  const po=Array.from(R.payouts);
  drawHist("hist1","h1wrap","h1tip",po,vals=>{
    const mx=Math.max(...vals,1);const bins=new Array(mx+1).fill(0);
    for(const v of vals)bins[v]++;
    return{bins,x0:0,bw:1,label:i=>i};},(i,c)=>`${i} payouts<br><b>${c}</b> sims (${(c/R.P.S*100).toFixed(1)}%)`);
  const fin=Array.from({length:R.P.S},(_,s)=>R.paths[s*R.P.H+R.P.H-1]);
  drawHist("hist2","h2wrap","h2tip",fin,vals=>{
    const lo=Math.min(...vals),hi=Math.max(...vals),nb=28,bw=(hi-lo)/nb||1;
    const bins=new Array(nb).fill(0);
    for(const v of vals)bins[Math.min(nb-1,Math.floor((v-lo)/bw))]++;
    return{bins,x0:lo,bw,label:i=>fmt$(lo+bw*(i+.5))};},
    (i,c)=>{const lo2=Math.min(...fin),bw2=(Math.max(...fin)-lo2)/28||1;
      return`${fmt$(lo2+bw2*i)} – ${fmt$(lo2+bw2*(i+1))}<br><b>${c}</b> sims`;});
  $("h1t").textContent=R.P.mode==="eval"?"Days to pass":"Payouts in horizon";
  if(R.P.mode==="eval"){
    const pd=Array.from(R.passDay);
    drawHist("hist1","h1wrap","h1tip",pd,vals=>{
      const ok=vals.filter(d=>d>0);const mx=Math.max(...ok,1);
      const bins=new Array(mx+1).fill(0);for(const v of ok)bins[v]++;
      return{bins,x0:0,bw:1,label:i=>i};},(i,c)=>`pass on day ${i}<br><b>${c}</b> sims`);}
  $("status").textContent=`${R.P.S} sims × ${R.P.H} days in ${(performance.now()-t0).toFixed(0)}ms — pool: 230 days @ $${R.P.base} `+
    (R.P.plan==="scaled"?`+$${R.P.sper}/$${R.P.sstep} past +$${R.P.safter}, cap $${R.P.scap} (elite max risk $${2*R.P.scap})`:"fixed");
}
$("run").onclick=run;
for(const el of document.querySelectorAll("input,select"))el.addEventListener("keydown",e=>{if(e.key==="Enter")run()});
run();
</script>
"""


def main(out: str = "mc_funded_lab.html") -> None:
    data = day_vectors()
    html = HTML.replace("__DATA__", json.dumps(data))
    with open(out, "w") as f:
        f.write(html)
    print(f"mc lab: {len(data['days'])} days x {len(data['base'])} bases -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mc_funded_lab.html")
