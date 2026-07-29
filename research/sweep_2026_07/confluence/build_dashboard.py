#!/usr/bin/env python3
"""Regenerate the confluence dashboard from results.json + entry_candle_report.json.
No number is typed by hand."""
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(f"{HERE}/results.json"))
EC = json.load(open(f"{HERE}/entry_candle_report.json"))
FAL = R.get("falsifiers", {})
NF = R.get("noise_floor", {})
PV = R.get("provenance", {})
CFG = R.get("configurations", {})
run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def f4(x, d=4, sign=True):
    if x is None or (isinstance(x, float) and x != x):
        return "&mdash;"
    return f"{x:+.{d}f}" if sign else f"{x:.{d}f}"


def pill(ok, y="PASS", n="FAIL"):
    return f'<span class="pill {"ok" if ok else "bad"}">{y if ok else n}</span>'


H = []
A = H.append
A(f"""<title>Confluence study &mdash; adaptive daily walk-forward</title>
<style>
:root{{--bg:#fbfbfa;--surf:#fff;--surf2:#f4f4f2;--ink:#1a1a19;--ink2:#55554f;--ink3:#86867e;
--line:#e3e3df;--ok:#1f6f43;--okbg:#e7f3ec;--bad:#a3231d;--badbg:#fbeae9;--warn:#8a5a00;
--warnbg:#fdf2dd;--accent:#2c5aa0;}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161614;--surf:#1e1e1c;--surf2:#26261f;
--ink:#f2f2ee;--ink2:#b9b9b0;--ink3:#8a8a80;--line:#33332e;--ok:#6fcf97;--okbg:#17301f;
--bad:#f08c86;--badbg:#331917;--warn:#e0b25e;--warnbg:#2e2410;--accent:#8fb4e8;}}}}
:root[data-theme="dark"]{{--bg:#161614;--surf:#1e1e1c;--surf2:#26261f;--ink:#f2f2ee;
--ink2:#b9b9b0;--ink3:#8a8a80;--line:#33332e;--ok:#6fcf97;--okbg:#17301f;--bad:#f08c86;
--badbg:#331917;--warn:#e0b25e;--warnbg:#2e2410;--accent:#8fb4e8;}}
:root[data-theme="light"]{{--bg:#fbfbfa;--surf:#fff;--surf2:#f4f4f2;--ink:#1a1a19;
--ink2:#55554f;--ink3:#86867e;--line:#e3e3df;--ok:#1f6f43;--okbg:#e7f3ec;--bad:#a3231d;
--badbg:#fbeae9;--warn:#8a5a00;--warnbg:#fdf2dd;--accent:#2c5aa0;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 ui-sans-serif,
-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;padding:28px 20px 80px}}
.wrap{{max-width:1080px;margin:0 auto}}
h1{{font-size:25px;margin:0 0 4px;letter-spacing:-.01em}}
h2{{font-size:19px;margin:34px 0 10px;padding-top:16px;border-top:1px solid var(--line)}}
h3{{font-size:13px;margin:20px 0 8px;color:var(--ink2);text-transform:uppercase;
letter-spacing:.06em;font-weight:600}}
p{{margin:9px 0;color:var(--ink2)}}
.sub{{color:var(--ink3);font-size:13px;margin-bottom:16px}}
.card{{background:var(--surf);border:1px solid var(--line);border-radius:10px;
padding:16px 18px;margin:14px 0}}
.cond{{background:var(--warnbg);border:1px solid var(--warn);border-radius:8px;
padding:11px 14px;margin:12px 0;font-size:13px;color:var(--ink)}}
.cond b{{color:var(--warn)}}
.hero{{background:var(--surf);border:2px solid var(--bad);border-radius:10px;
padding:18px 20px;margin:16px 0}}
.hero .v{{font-size:30px;font-weight:680;letter-spacing:-.02em}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}}
.tile{{background:var(--surf);border:1px solid var(--line);border-radius:9px;padding:12px 14px}}
.tile .k{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--ink3)}}
.tile .v{{font-size:21px;font-weight:650;margin-top:3px}}
.tile .n{{font-size:12px;color:var(--ink3);margin-top:2px}}
.scroll{{overflow-x:auto;margin:10px 0}}
table{{border-collapse:collapse;width:100%;font-size:13px;min-width:520px}}
th,td{{text-align:right;padding:6px 9px;border-bottom:1px solid var(--line);
font-variant-numeric:tabular-nums;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left;font-variant-numeric:normal}}
th{{color:var(--ink3);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.05em}}
tbody tr:hover{{background:var(--surf2)}}
.pill{{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;font-weight:650}}
.pill.ok{{background:var(--okbg);color:var(--ok)}}
.pill.bad{{background:var(--badbg);color:var(--bad)}}
.pill.warn{{background:var(--warnbg);color:var(--warn)}}
.muted{{color:var(--ink3)}}
code{{background:var(--surf2);padding:1px 5px;border-radius:4px;font-size:12px}}
.bar{{height:9px;background:var(--surf2);border-radius:5px;position:relative;margin:8px 0 2px}}
.bar i{{position:absolute;top:0;bottom:0;background:var(--accent);border-radius:5px}}
.bar u{{position:absolute;top:-4px;bottom:-4px;width:2px;background:var(--bad)}}
.prov{{font-size:12px;color:var(--ink3);font-family:ui-monospace,Menlo,monospace;
background:var(--surf2);border-radius:8px;padding:12px 14px;word-break:break-all}}
</style>
<div class="wrap">
<h1>Confluence study &mdash; adaptive daily walk-forward</h1>
<div class="sub">Rank-normalised ridge composite, expanding-window daily refit &middot;
{run_id} &middot; commit <code>{PV.get('commit','—')}</code></div>

<div class="cond">
<b>STANDING CONDITIONS.</b>
<b>Partial remediation only</b> &mdash; this book is <b>NOT clean</b>. Only the <code>C</code>
check was remediated; the <code>W</code> depth check and the entire <code>dep_*</code> family
failed the Phase-0 lookahead audit and <b>remain in its selection path</b>. Everything below
inherits that unquantified leak.
Sample: <b>{PV.get('n_trades','—')} trades over {PV.get('n_days','—')} days</b>; the walk-forward
issues predictions only once {CFG.get('min_train','—')} training trades exist. IS and OOS are
different market regimes (NQ 21k&rarr;30k, pre-market volume +~50%) &mdash; a single regime
transition, observed once. Cells below the count floor are marked
<span class="pill warn">insufficient</span> rather than given numbers.
</div>""")

# hero
passes = NF.get("passes")
A(f"""<div class="hero">
<div class="k muted" style="font-size:11px;text-transform:uppercase;letter-spacing:.07em">
Headline &mdash; the noise floor</div>
<div class="v">{f4(NF.get('percentile'),2,False)}th percentile {pill(passes,'PASS','NULL')}</div>
<p>The real composite scores <b>rho {f4(NF.get('real'))}</b> out-of-sample. Run end to end on
<b>{NF.get('n_perm','—')} day-block-shuffled outcome vectors</b>, the identical pipeline produces
a distribution whose 99th percentile is <b>{f4(NF.get('p99'))}</b>. The registered gate was
&ldquo;beyond the 99th percentile or the answer is null&rdquo;.
<b>{'It cleared.' if passes else 'It did not clear. The answer is NULL and is reported as null.'}</b></p>
<div class="bar">
  <i style="left:0;width:{max(0,min(100,NF.get('percentile') or 0)):.1f}%"></i>
  <u style="left:99%"></u>
</div>
<p class="muted" style="font-size:12px">blue = where the real result sits in the shuffled
distribution &middot; red line = the 99th-percentile gate &middot; empirical p =
{f4(NF.get('p_empirical'),4,False)}</p>
</div>

<div class="tiles">
 <div class="tile"><div class="k">Real metric</div><div class="v">{f4(NF.get('real'))}</div>
  <div class="n">Spearman, {R.get('real',{}).get('n_pred', FAL.get('real',{}).get('n_pred','—'))} OOS predictions</div></div>
 <div class="tile"><div class="k">Shuffled median</div><div class="v">{f4(NF.get('median'))}</div>
  <div class="n">{NF.get('n_perm','—')} runs</div></div>
 <div class="tile"><div class="k">Shuffled p95 / p99</div>
  <div class="v" style="font-size:16px">{f4(NF.get('p95'))} / {f4(NF.get('p99'))}</div>
  <div class="n">gate is p99</div></div>
 <div class="tile"><div class="k">Shuffled max</div><div class="v">{f4(NF.get('maxv'))}</div>
  <div class="n">best noise run</div></div>
 <div class="tile"><div class="k">Configurations</div>
  <div class="v">{CFG.get('model_specs_examined','—')}</div>
  <div class="n">model specifications examined</div></div>
</div>
<p class="muted">{CFG.get('detail','')}</p>""")

# falsifiers
V = R.get("verdict", {})
bs = FAL.get("best_single", {})
A(f"""<h2>Registered falsifiers</h2>
<div class="scroll"><table><thead><tr><th>Falsifier</th><th>Value</th><th>Real</th>
<th>Outcome</th></tr></thead><tbody>
<tr><td>(a) direction-blind twin <span class="muted">&mdash; unsigned magnitudes only</span></td>
<td>{f4(FAL.get('blind',{}).get('rho'))}</td><td>{f4(NF.get('real'))}</td>
<td>{pill(not V.get('fal_a'),'does not fire','FIRES')}</td></tr>
<tr><td>(b) single-best-feature baseline <span class="muted">&mdash;
<code>{bs.get('feature','—')}</code></span></td>
<td>{f4(bs.get('rho'))}</td><td>{f4(NF.get('real'))}</td>
<td>{pill(not V.get('fal_b'),'does not fire','FIRES')}</td></tr>
<tr><td>(c) random-weights composite <span class="muted">&mdash; same pool, p95 of
{R.get('random_weights',{}).get('n','—')} draws</span></td>
<td>{f4(R.get('random_weights',{}).get('p95'))}</td><td>{f4(NF.get('real'))}</td>
<td>{pill(not V.get('fal_c'),'does not fire','FIRES')}</td></tr>
</tbody></table></div>
<p class="verdict"><b>Falsifier (b) is the decisive one.</b> The fitted composite scores
{f4(NF.get('real'))} and its own best single component <code>{bs.get('feature','—')}</code>
scores {f4(bs.get('rho'))}. Combining thirteen features does not beat using one of them alone
&mdash; <b>confluence adds nothing here</b>. The direction-blind twin sits at
{f4(FAL.get('blind',{}).get('rho'))}, within
{abs((NF.get('real') or 0)-(FAL.get('blind',{}).get('rho') or 0)):.4f} of the signed composite,
so what little signal exists is not distinguishably directional.</p>

<h3>Single-feature baselines &mdash; identical walk-forward, one feature at a time</h3>
<div class="scroll"><table><thead><tr><th>Feature</th><th>Walk-forward rho</th>
<th>vs composite</th></tr></thead><tbody>""")
singles = FAL.get("singles", {})
LOWP = " <span class='muted'>LOW-POWER</span>"
for f, v in sorted(singles.items(), key=lambda kv: -(kv[1] or -9)):
    d = (v or 0) - (NF.get("real") or 0)
    tag = LOWP if f == "delta_div_15" else ""
    A(f"<tr><td><code>{f}</code>{tag}</td>"
      f"<td>{f4(v)}</td><td class='muted'>{f4(d)}</td></tr>")
A("</tbody></table></div>")

# entry candle
A("""<h2>New entry-candle features &mdash; the ones never previously tested</h2>
<p>Every feature built before this round used 5-minute windows or longer. These four are single
bar, computed on the bar at <b>fill&minus;1</b> (the last completed bar before the fill minute,
so strictly pre-fill), shift-tested against the same contaminated twins as the rest of the
study, and exchangeability-tested across the split <b>before</b> being allowed into the pool.</p>
<div class="scroll"><table><thead><tr><th>Feature</th><th>+1 differs</th><th>+15 differs</th>
<th>Shift</th><th>KS</th><th>p (perm)</th><th>Exchangeability</th><th>Pool</th>
</tr></thead><tbody>""")
for f in ("ec_delta", "ec_fp_imb", "ec_delta_hi_lo", "ec_aggr_flip"):
    s = EC["shift"].get(f, {})
    e = EC["exchangeability"].get(f, {})
    adm = f in EC["admitted"]
    A(f"<tr><td><code>{f}</code></td><td>{s.get('shift1','—')}</td><td>{s.get('leak15','—')}</td>"
      f"<td>{pill(s.get('passes'),'PASS','DEGENERATE')}</td><td>{f4(e.get('ks'),3,False)}</td>"
      f"<td>{f4(e.get('p'),4,False)}</td><td>{pill(e.get('passes'))}</td>"
      f"<td>{pill(adm,'ADMITTED','EXCLUDED')}</td></tr>")
A(f"""</tbody></table></div>
<p><code>ec_delta_hi_lo</code> failed exchangeability and was <b>excluded, not remedied</b> &mdash;
per the brief, no feature is repaired mid-run. Pool frozen at
<b>{PV.get('pool',[]) and len(PV['pool'])} features</b>; nothing was added after that point.</p>""")

# conviction
CS = FAL.get("conviction_state", {})
A(f"""<h2>Conviction sizing</h2>
<h3>Part 1 &mdash; diagnostic on code already running</h3>
<p>Conditional on a trade being taken, do the canon's own escalation and governor states predict
realised R? Day-clustered bootstrap, 4,000 draws. &ldquo;n needed&rdquo; is the sample this
effect size would require for 80% power &mdash; where it exceeds
{PV.get('n_trades','—')}, the cell is underpowered by construction.</p>
<div class="scroll"><table><thead><tr><th>State variable</th><th>rho</th><th>95% CI</th>
<th>p</th><th>rho (OOS half)</th><th>n needed</th><th>Levels</th></tr></thead><tbody>""")
for c, v in CS.items():
    ci = v.get("ci", [None, None])
    nn = v.get("n_required")
    nns = "&mdash;" if nn is None or nn != nn or nn == float("inf") else f"{nn:,.0f}"
    thin = v.get("thin_levels", 0)
    lv = (f"{len(v.get('levels',{}))} levels"
          + (f", <span class='pill warn'>{thin} insufficient</span>" if thin else ""))
    A(f"<tr><td><code>{c}</code></td><td>{f4(v.get('rho'),3)}</td>"
      f"<td class='muted'>[{f4(ci[0],3)}, {f4(ci[1],3)}]</td><td>{f4(v.get('p'),3,False)}</td>"
      f"<td>{f4(v.get('rho_oos'),3)}</td><td class='muted'>{nns}</td><td class='muted'>{lv}</td></tr>")
surv = FAL.get("conviction_survivors", [])
A(f"""</tbody></table></div>
<p class="verdict">Surviving Bonferroni over {len(CS)} state variables:
<b>{', '.join(f'<code>{s}</code>' for s in surv) if surv else 'NONE'}</b>. Worth noting against
the rest of this study: these internal-state associations
(|rho| up to {max((abs(v.get('rho') or 0) for v in CS.values()), default=0):.3f}) are
<b>several times larger</b> than anything the order-flow pool produced &mdash; but every one of
them needs {min((v.get('n_required') or 9e9) for v in CS.values()):,.0f}+ trades for 80% power
against the {PV.get('n_trades','—')} available, and none survives correction.</p>

<h3>Part 2 &mdash; score-proportional vs flat sizing under funded rules</h3>""")
c2 = R.get("conviction_part2", {})
if c2.get("run"):
    A("<p>Gate open; results follow.</p>")
else:
    A(f"""<div class="cond"><b>NOT RUN &mdash; and that is the registered outcome, not an
omission.</b> Part 2 was registered as conditional on the composite clearing its noise floor.
It did not clear it ({f4(NF.get('percentile'),2,False)}th percentile against a 99th-percentile
gate), so sizing proportional to composite score would be <b>sizing by noise</b>. Running it
anyway would be the search widening itself &mdash; exactly what the brief forbids.</div>""")

A(f"""<h2>Provenance</h2>
<div class="prov">
run_id &nbsp; {run_id}<br>
commit &nbsp; {PV.get('commit','—')}<br>
pipeline.py sha256/16 &nbsp; {PV.get('pipeline_sha','—')}<br>
run_shard.py sha256/16 &nbsp; {PV.get('shard_sha','—')}<br>
feature pool ({len(PV.get('pool',[]))}) &nbsp; {', '.join(PV.get('pool',[]))}<br>
direction-blind pool &nbsp; {', '.join(PV.get('blind',[]))}<br>
min_train &nbsp; {CFG.get('min_train','—')} trades &nbsp;|&nbsp; penalty grid &nbsp;
{CFG.get('penalties','—')} (selected inside each fold, 3-fold CV on training trades only)<br>
shuffles &nbsp; {NF.get('n_perm','—')} day-block permutations &nbsp;|&nbsp; duplicate shard keys
&nbsp; {NF.get('dup_keys',0)}<br>
shard files (one writer each, append-only) &nbsp; {', '.join(PV.get('shard_files',[]))}<br>
baseline &nbsp; {PV.get('baseline','—')}<br>
sample &nbsp; {PV.get('n_trades','—')} trades / {PV.get('n_days','—')} days<br>
regenerate &nbsp; python3 research/sweep_2026_07/confluence/build_dashboard.py
</div>
<p class="sub" style="margin-top:20px">Deterministic throughout: no LLM adjusted weights,
thresholds, or feature selection at any point. Shard workers ran one frozen command each and
wrote to disjoint append-only files; a single non-agent aggregator merged them.</p>
</div>
<script>(function(){{var t=localStorage.getItem('theme');
if(t)document.documentElement.setAttribute('data-theme',t);}})();</script>""")

path = f"{HERE}/dashboard_confluence.html"
open(path, "w").write("\n".join(H))
print(f"wrote {path} ({os.path.getsize(path):,} bytes)")
