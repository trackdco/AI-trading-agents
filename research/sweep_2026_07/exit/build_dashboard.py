#!/usr/bin/env python3
"""Regenerate the exit-timing dashboard, verdict table first, from the results artefacts."""
import json
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V = json.load(open(f"{HERE}/verdicts.json"))
P1 = json.load(open(f"{HERE}/part1_report.json"))
P2 = json.load(open(f"{HERE}/part2_report.json"))
P3 = json.load(open(f"{HERE}/part3_report.json"))
EP = json.load(open(f"{HERE}/placebo_extended.json"))
run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                        text=True, cwd="/home/user/AI-trading-agents").stdout.strip()
TAGC = {"WORKS": "ok", "NEEDS MORE WORK": "warn", "DEAD": "bad"}


def money(x, d=0):
    return "&mdash;" if x is None else f"${x:+,.{d}f}"


def num(x, d=3):
    return "&mdash;" if x is None else f"{x:+.{d}f}"


H = []
A = H.append
A(f"""<title>Exit-timing study &mdash; verdict table</title>
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
.wrap{{max-width:1150px;margin:0 auto}}
h1{{font-size:26px;margin:0 0 4px}}
h2{{font-size:19px;margin:34px 0 10px;padding-top:16px;border-top:1px solid var(--line)}}
h3{{font-size:13px;margin:20px 0 8px;color:var(--ink2);text-transform:uppercase;
letter-spacing:.06em;font-weight:600}}
p{{margin:9px 0;color:var(--ink2)}}
.sub{{color:var(--ink3);font-size:13px;margin-bottom:16px}}
.cond{{background:var(--warnbg);border:1px solid var(--warn);border-radius:8px;padding:11px 14px;
margin:12px 0;font-size:13px;color:var(--ink)}}
.cond b{{color:var(--warn)}}
.dead{{background:var(--badbg);border:1px solid var(--bad);border-radius:8px;padding:12px 15px;
margin:12px 0;font-size:13px}}
.vrow{{background:var(--surf);border:1px solid var(--line);border-left-width:5px;
border-radius:0 10px 10px 0;padding:14px 16px;margin:10px 0}}
.vrow.ok{{border-left-color:var(--ok)}}
.vrow.warn{{border-left-color:var(--warn)}}
.vrow.bad{{border-left-color:var(--bad)}}
.vhead{{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}}
.vname{{font-size:16px;font-weight:660}}
.vbody{{font-size:13px;color:var(--ink2);margin-top:7px}}
.vbody b{{color:var(--ink)}}
.kv{{margin-top:5px}}
.kv span.k{{display:inline-block;min-width:96px;color:var(--ink3);font-size:11px;
text-transform:uppercase;letter-spacing:.05em;vertical-align:top}}
.scroll{{overflow-x:auto;margin:10px 0}}
table{{border-collapse:collapse;width:100%;font-size:13px;min-width:520px}}
th,td{{text-align:right;padding:6px 9px;border-bottom:1px solid var(--line);
font-variant-numeric:tabular-nums;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left;font-variant-numeric:normal}}
th{{color:var(--ink3);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.05em}}
tbody tr:hover{{background:var(--surf2)}}
.pill{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;
letter-spacing:.03em}}
.pill.ok{{background:var(--okbg);color:var(--ok)}}
.pill.bad{{background:var(--badbg);color:var(--bad)}}
.pill.warn{{background:var(--warnbg);color:var(--warn)}}
.muted{{color:var(--ink3)}}
code{{background:var(--surf2);padding:1px 5px;border-radius:4px;font-size:12px}}
.prov{{font-size:12px;color:var(--ink3);font-family:ui-monospace,Menlo,monospace;
background:var(--surf2);border-radius:8px;padding:12px 14px;word-break:break-all}}
.counts{{display:flex;gap:10px;margin:14px 0;flex-wrap:wrap}}
.cbox{{flex:1;min-width:150px;background:var(--surf);border:1px solid var(--line);
border-radius:9px;padding:12px 14px}}
.cbox .v{{font-size:24px;font-weight:680}}
</style>
<div class="wrap">
<h1>Exit-timing study &mdash; verdict table</h1>
<div class="sub">Every hypothesis this project has tested &middot; {run_id} &middot; commit
<code>{commit}</code></div>

<div class="cond"><b>STANDING CONDITIONS.</b> Book is <b>partially remediated (C only)</b> &mdash;
the <code>W</code> check and the whole <code>dep_*</code> family failed the Phase-0 lookahead
audit and <b>remain in the selection path</b>. 182 pre-market trades over 145 days,
2025-07-01&ndash;2026-07-10, Jan-2026 absent from the book (not from the data). IS and OOS are
different market regimes (NQ 21k&rarr;30k, pre-market volume +~50%) &mdash; a single transition,
observed once. Cells under 10 trades are marked insufficient. Research only: canon and the live
path are untouched.</div>""")

rows = V["rows"]
nw = sum(1 for r in rows if r["tag"] == "WORKS")
nm = sum(1 for r in rows if r["tag"] == "NEEDS MORE WORK")
nd = sum(1 for r in rows if r["tag"] == "DEAD")
A(f"""<div class="counts">
<div class="cbox"><div class="muted" style="font-size:11px;text-transform:uppercase">Works</div>
<div class="v" style="color:var(--ok)">{nw}</div>
<div class="muted" style="font-size:12px">survived OOS + noise floor + funded risk</div></div>
<div class="cbox"><div class="muted" style="font-size:11px;text-transform:uppercase">Needs more work</div>
<div class="v" style="color:var(--warn)">{nm}</div>
<div class="muted" style="font-size:12px">under-evidenced; settling condition stated</div></div>
<div class="cbox"><div class="muted" style="font-size:11px;text-transform:uppercase">Dead</div>
<div class="v" style="color:var(--bad)">{nd}</div>
<div class="muted" style="font-size:12px">tested and failed; do not retest</div></div>
</div>
<p class="muted"><b>Definitions applied strictly.</b> WORKS = {V['definitions']['WORKS']}.
NEEDS MORE WORK = {V['definitions']['NEEDS MORE WORK']}. DEAD = {V['definitions']['DEAD']}.</p>""")

order = {"WORKS": 0, "NEEDS MORE WORK": 1, "DEAD": 2}
for r in sorted(rows, key=lambda x: order[x["tag"]]):
    c = TAGC[r["tag"]]
    A(f"""<div class="vrow {c}">
<div class="vhead"><span class="vname">{r['name']}</span>
<span class="pill {c}">{r['tag']}</span></div>
<div class="vbody">
<div class="kv"><span class="k">Tested</span> {r['tested']}</div>
<div class="kv"><span class="k">Numbers</span> {r['numbers']}</div>
<div class="kv"><span class="k">Noise floor</span> {r['noise_floor']}</div>
<div class="kv"><span class="k">Funded risk</span> {r['funded']}</div>""")
    if r.get("caveats"):
        A(f'<div class="kv"><span class="k">Caveats</span> {r["caveats"]}</div>')
    if r.get("settle"):
        A(f'<div class="kv"><span class="k">To settle</span> <b>{r["settle"]}</b></div>')
    A("</div></div>")

# ---------------------------------------------------------------- Part 1
A("""<h2>Part 1 &mdash; is the canon exiting winners too early?</h2>
<p>Descriptive only; no rule chosen, no threshold fitted. MFE is measured <b>ALIVE</b> &mdash;
clipped at the stop bar, because excursion after you have been stopped out cannot be banked.
Gap = MFE minus realised R.</p>
<div class="scroll"><table><thead><tr><th>Horizon</th><th>Mean MFE</th><th>Median MFE</th>
<th>Mean gap</th><th>Median gap</th><th>Gap &gt; 1R</th><th>Gap &gt; 2R</th></tr></thead><tbody>""")
for k, v in P1["horizons"].items():
    A(f"<tr><td>{k}</td><td>{v['mean_mfe']:.3f}</td><td>{v['med_mfe']:.3f}</td>"
      f"<td>{v['mean_gap']:+.3f}</td><td>{v['med_gap']:+.3f}</td>"
      f"<td>{v['pct_gap_gt1']*100:.0f}%</td><td>{v['pct_gap_gt2']*100:.0f}%</td></tr>")
A("</tbody></table></div><h3>Capture ratio &mdash; realised R divided by MFE at that horizon</h3>"
  '<div class="scroll"><table><thead><tr><th>Horizon</th><th>n</th><th>Median capture</th>'
  "<th>Captured &ge;80%</th><th>Captured &le;25%</th></tr></thead><tbody>")
for k, v in P1["capture"].items():
    A(f"<tr><td>{k}</td><td>{v['n']}</td><td>{v['median']:.2f}</td>"
      f"<td>{v['ge80']*100:.0f}%</td><td>{v['le25']*100:.0f}%</td></tr>")
A(f"""</tbody></table></div>
<p><b>The premise is true and the effect is large.</b> The canon banks a median of
<b>23%</b> of what was available within 15 minutes, falling to <b>7%</b> over full trade life,
and captures 80% or more on only 4&ndash;28% of trades. Trades that reach +1R (n=115) realise
+1.449 against a 60-minute alive-MFE of +4.837. Give-back rises monotonically with horizon and
is largest in the late segment.</p>
<div class="scroll"><table><thead><tr><th>Segment</th><th>n</th><th>Realised R</th>
<th>gap@15</th><th>gap@30</th><th>gap@45</th><th>gap@60</th><th>gap@life</th></tr></thead><tbody>""")
for k, v in P1["by_segment"].items():
    A(f"<tr><td>{k}</td><td>{v['n']}</td><td>{v['realised']:+.3f}</td>"
      + "".join(f"<td>{v['gap'+str(h)]:+.3f}</td>" for h in (15, 30, 45, 60))
      + f"<td>{v['gap_life']:+.3f}</td></tr>")
A("</tbody></table></div>")

# ---------------------------------------------------------------- Part 2
A(f"""<h2>Part 2 &mdash; the timer, measured completely</h2>
<div class="dead"><b>THIS RULE CANNOT BE CONFIRMED ON THIS BOOK.</b> It was found
<b>post-hoc</b>, after the pre-registered select-on-in-sample procedure had already rejected it.
It <b>lost in-sample (&minus;$575)</b> and gained everything <b>out-of-sample (+$9,075)</b> —
a sign flip across the single regime boundary this book contains. <b>15 of 68</b> configurations
in that sweep flip negative-to-positive by chance. Measuring it completely is not the same as
validating it; only the Part-4 forward shadow log can do that.</div>
<div class="scroll"><table><thead><tr><th>Variant</th><th>PM P&amp;L</th><th>Book P&amp;L</th>
<th>Max DD</th><th>Min avail DD</th><th>Breach days</th><th>Bust (naked)</th>
<th>Bust (spine)</th><th>Stop share</th></tr></thead><tbody>""")
for k in ("canon", "timer30", "timer45", "timer60", "timer90"):
    v = P2[k]
    nm_ = "canon (reference)" if k == "canon" else k.replace("timer", "timer ") + "m"
    ss = "&mdash;" if v.get("stop_share") is None else f"{v['stop_share']*100:.0f}%"
    A(f"<tr><td>{nm_}</td><td>{money(v['pm_pl'])}</td><td>{money(v['book_pl'])}</td>"
      f"<td>${v['max_dd']:,.0f}</td><td>${v['min_available']:,.0f}</td>"
      f"<td>{v['breach_days']:.0f}</td><td>{v['bust_naked']:.2f}%</td>"
      f"<td>{v['bust_spine']:.2f}%</td><td>{ss}</td></tr>")
sh = P2["shape"]
A(f"""</tbody></table></div>
<p><b>The variance cost is real and it is the answer to the question you asked.</b> Naked bust
probability goes 0.40% &rarr; 2.02% at 45 minutes (<b>5&times;</b>) and 10.66% at 90 minutes
(<b>27&times;</b>); max drawdown rises to $2,441 and daily-limit breach days from 0 to 2. The
rule takes a full 1R on 55% of trades with no trailing. With the full safety spine every variant
is 0.00%, so the cost is visible only on the naked account &mdash; but a variant that raises
expectancy <i>and</i> raises bust probability is worse, and this one does.</p>
<p><b>Shape: a hump, not a plateau.</b> PM P&amp;L across 30/45/60/90 runs
{" &rarr; ".join(money(v) for v in sh['values'])}, a spread of {money(sh['spread'])} on a mean of
{money(sh['mean'])} &mdash; <b>{sh['spread']/abs(sh['mean'])*100:.0f}% of the level</b> &mdash;
and it falls <b>below canon</b> at 90 minutes. Two adjacent horizons work and both neighbours
fail. That is closer to fitting than to structure.</p>
<h3>Where the money is (timer 45m vs canon, PM slice)</h3>
<div class="scroll"><table><thead><tr><th>Cut</th><th>n</th><th>Canon</th><th>Timer 45m</th>
<th>Delta</th></tr></thead><tbody>""")
for k, v in P2["where"].items():
    ins = ' <span class="pill warn">insufficient</span>' if v["insufficient"] else ""
    A(f"<tr><td>{k}{ins}</td><td>{v['n']}</td><td>{money(v['canon'])}</td>"
      f"<td>{money(v['timer'])}</td><td>{money(v['delta'])}</td></tr>")
A("""</tbody></table></div>
<p>The benefit is concentrated in <b>2026</b>, <b>out-of-sample</b>, and the <b>late segment on
29 trades</b>. That is a regime-specific, small-sample concentration, not a broad effect.</p>""")

# ---------------------------------------------------------------- Part 3
A(f"""<h2>Part 3 &mdash; the give-back gap, pre-registered</h2>
<p>Registration committed <b>before</b> any statistic was computed
(<code>PART3_PREREG.md</code>). Primary = conditional give-back, P(finished red | reached +1R);
statistic = early minus late; noise floor = 2,000-draw day-block permutation; rule = p&lt;0.05
<b>and</b> a CI excluding zero.</p>
<div class="scroll"><table><thead><tr><th>Segment</th><th>n</th><th>n reached +1R</th>
<th>Conditional give-back</th><th>Unconditional</th></tr></thead><tbody>""")
for k, v in P3["observed"].items():
    ins = ' <span class="pill warn">insufficient</span>' if v["insufficient"] else ""
    A(f"<tr><td>{k}{ins}</td><td>{v['n']}</td><td>{v['n_reached']}</td>"
      f"<td>{v['cond']*100:.1f}%</td><td>{v['uncond']*100:.1f}%</td></tr>")
A(f"""</tbody></table></div>
<div class="cond"><b>VERDICT: {P3['verdict']}</b> — reported exactly as registered, not
reinterpreted. Effect size <b>{P3['stat_primary']*100:+.1f} percentage points</b>; day-clustered
95% CI <b>[{P3['ci'][0]*100:+.1f}pp, {P3['ci'][1]*100:+.1f}pp]</b> and bootstrap p =
{P3['p_boot']:.3f} would both pass &mdash; but the day-block permutation gives
<b>p = {P3['p_primary']:.4f}</b>, and the registered rule required both. One of two is not
established.<br><br>
<b>What would settle it:</b> the late segment is binding. It needs
~{P3['n_required_per_group']:.0f} +1R-reaching trades and has
{P3['observed']['late 09:00-09:29']['n_reached']} &mdash; a shortfall of
{P3['shortfall_late']:.0f}. At the observed rate that is <b>~{P3['days_needed']:.0f} further
trading days (about 4 months)</b> of live or shadow data. The early segment is already
sufficient at {P3['observed']['early 08:00-08:29']['n_reached']}.</div>""")

# ---------------------------------------------------------------- Part 4
A("""<h2>Part 4 &mdash; shadow-tracking harness</h2>
<p>Pure parallel logging: no orders, no canon change, nothing on the live path. For every
pre-market trade it records side by side what the canon did and what the timer would have done,
at 30/45/60/90 minutes, append-only, idempotent (a re-run adds zero records).</p>
<pre style="background:var(--surf2);padding:12px 14px;border-radius:8px;font-size:12px;
overflow-x:auto"><code>python3 research/sweep_2026_07/exit/shadow_timer.py --backfill
python3 research/sweep_2026_07/exit/shadow_timer.py --day 2026-07-13   # the daily call
python3 research/sweep_2026_07/exit/shadow_timer.py --report</code></pre>
<p>Backfilled: <b>182 trades &times; 4 horizons = 728 records</b>. The report separates a
<b>forward-only slice</b> (sessions after 2026-07-10) from the backfill, and currently states
plainly that the forward slice is <b>empty</b> &mdash; every record so far is over the book the
hypothesis was formed on and therefore proves nothing about it. This is the only mechanism that
can ever validate the timer.</p>""")

# ---------------------------------------------------------------- dead numbers
A(f"""<h2>Independent audit of this table</h2>
<p>Before publishing, four independent readers extracted each hypothesis's evidence straight
from the committed artefacts and two adversarial auditors were asked to REFUTE the tags. They
challenged two, and both challenges were upheld:</p>
<div class="cond"><b>1. The news filter was initially graded WORKS on a floor-limited noise
floor.</b> The original calendar-shift placebo used 10 shifts, so its smallest achievable p was
1/11 = 0.091 &mdash; it could not clear 0.05 <i>by construction</i>. The placebo was re-run at
{EP['n_shifts']} shifts (&plusmn;1..{EP['maxshift']} trading days): the real calendar still beats
<b>all {EP['n_shifts']}</b>, giving <b>p = {EP['p']:.4f}</b>, which clears the gate. Only the
number of placebos changed &mdash; the statistic, the real value and the gate are identical. The
tag now holds on its own evidence.</div>
<div class="cond"><b>2. In-trade order flow at a retrace was re-tagged DEAD &rarr; NEEDS MORE
WORK.</b> It was never given a fair test: with 17 reversals in the whole sample the design
cannot detect anything below |AUC&minus;0.5| = 0.147, so its null is uninformative rather than a
refutation. DEAD is reserved for hypotheses that were tested and failed.</div>
<div class="dead"><b>3. The 45-minute timer was re-tagged NEEDS MORE WORK &rarr; DEAD.</b>
An auditor surfaced a fact I had not reported: <code>time45/all</code> ranks <b>1 of 68 by
out-of-sample</b> P&amp;L and <b>54 of 68 by in-sample</b>, and <b>all eight</b> top-OOS
configurations are negative in-sample. Its +$9,075 is a max-of-68 pick on the test half &mdash;
the same selection error that killed the sweep, run in the opposite direction. The selection-free
part of the finding (Part 1: the canon captures 7&ndash;23% of available excursion) is now carried
as its own separate row.</div>
<div class="dead"><b>4. The gap correlation was NOT out-of-sample, and I reported it as if it
were.</b> Verified from <code>part1_features.csv</code>: the &rho;&nbsp;+0.153 figure is
<b>pooled across both halves</b> (n=175). Out-of-sample alone it is <b>+0.123</b> (n=86);
in-sample +0.081. The ordering claim survives &mdash; +0.123 still exceeds the best order-flow
|&rho;| of 0.093 &mdash; but the basis I gave was wrong and the effect is weaker than stated.</div>
<div class="cond"><b>5. In-trade flow at a retrace went DEAD &rarr; NEEDS MORE WORK &rarr; DEAD.</b>
The two auditors split. My own definition settles it: NEEDS MORE WORK requires something
<i>promising</i>, and all five out-of-sample AUCs straddle 0.5. It is a null <b>with a stated
blind spot</b> (nothing below |AUC&minus;0.5| = 0.147 is detectable at 17 reversals), not a
strong refutation.</div>
<p class="muted">Further audit corrections applied: give-back's post-hoc status (the confirmatory
test re-used the same 182 trades that generated the observation); the confluence pool contains one
non-flow feature (gap_abs) and struct runs at n=176; the headline-print clause of the news
decomposition is definitively DEAD (34 blackout days, zero avoided trades). Notes were added
wherever a control other than a permutation was used (H2, H4, breakeven: direct funded-dollar
failure; Q2: family-wise correction on the effective test count). <b>No number in this table was
produced or altered by an LLM</b> &mdash; auditors could only challenge tags and demand evidence,
and every challenge above was independently re-verified against the artefacts before being
accepted.</p>""")
A('<h2>Dead numbers &mdash; must not reappear as live results</h2>')
for d in V["dead_numbers"]:
    A(f'<div class="dead"><b>{d["n"]}</b><br>{d["why"]}</div>')

A(f"""<h2>Provenance</h2>
<div class="prov">
run_id &nbsp; {run_id}<br>
commit &nbsp; {commit}<br>
anchors &nbsp; certified book 216 / $+18,376.00 &middot; working baseline 182 / $+21,097.875
&middot; both reproduced to the cent before any new number<br>
book &nbsp; job2_books/sized_C_news &mdash; PARTIALLY REMEDIATED (C only); W and dep_* leaky<br>
engine &nbsp; $50k start, $2,000 EOD-trailing DD locked at the floor, Tier-1 daily halt &minus;$800
plus $100 proximity halt; spine adds the DD-scaling ramp; {P2['provenance']['nboot']:,} bootstrap paths<br>
costs &nbsp; $1.24/micro round trip, $0.50/micro slippage on marketable exits; the canon
reference carries its own cost convention, stated not merged<br>
part 3 &nbsp; 2,000-draw day-block permutation, 4,000-draw day-clustered bootstrap<br>
regenerate &nbsp; python3 research/sweep_2026_07/exit/build_dashboard.py
</div>
<p class="sub" style="margin-top:20px">Deterministic throughout: no sweep, no configuration
search, no best-of selection &mdash; that procedure has failed three times and its cost is
measured at &minus;$7,050 median in-sample-to-out-of-sample shrinkage. No LLM adjusted a
threshold or selected a variant at any point.</p>
</div>
<script>(function(){{var t=localStorage.getItem('theme');
if(t)document.documentElement.setAttribute('data-theme',t);}})();</script>""")

path = f"{HERE}/dashboard_exit.html"
open(path, "w").write("\n".join(H))
print(f"wrote {path} ({os.path.getsize(path):,} bytes)")
