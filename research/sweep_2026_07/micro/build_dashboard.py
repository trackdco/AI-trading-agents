#!/usr/bin/env python3
"""Regenerate the pre-market microstructure dashboard from the results artefacts."""
import json
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(f"{HERE}/micro_report.json"))
SW = json.load(open(f"{HERE}/exit_sweep_real.json"))
NU = json.load(open(f"{HERE}/exit_sweep_null.json"))
run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                        text=True, cwd="/home/user/AI-trading-agents").stdout.strip()


def money(x, d=0):
    return "&mdash;" if x is None else f"${x:+,.{d}f}"


def pct(x, d=0):
    return "&mdash;" if x is None else f"{x*100:.{d}f}%"


def num(x, d=2):
    return "&mdash;" if x is None else f"{x:.{d}f}"


def pill(ok, y, n):
    return f'<span class="pill {"ok" if ok else "bad"}">{y if ok else n}</span>'


H = []
A = H.append
A(f"""<title>Pre-market microstructure &mdash; ceilings, walls, chop, exits</title>
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
.wrap{{max-width:1100px;margin:0 auto}}
h1{{font-size:25px;margin:0 0 4px}}
h2{{font-size:19px;margin:34px 0 10px;padding-top:16px;border-top:1px solid var(--line)}}
h3{{font-size:13px;margin:20px 0 8px;color:var(--ink2);text-transform:uppercase;
letter-spacing:.06em;font-weight:600}}
p{{margin:9px 0;color:var(--ink2)}}
.sub{{color:var(--ink3);font-size:13px;margin-bottom:16px}}
.card{{background:var(--surf);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}}
.cond{{background:var(--warnbg);border:1px solid var(--warn);border-radius:8px;padding:11px 14px;
margin:12px 0;font-size:13px;color:var(--ink)}}
.cond b{{color:var(--warn)}}
.ans{{background:var(--surf);border-left:4px solid var(--accent);border-radius:0 8px 8px 0;
padding:12px 16px;margin:12px 0}}
.ans .q{{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink3)}}
.ans .a{{font-size:16px;font-weight:640;margin-top:3px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}}
.tile{{background:var(--surf);border:1px solid var(--line);border-radius:9px;padding:12px 14px}}
.tile .k{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--ink3)}}
.tile .v{{font-size:21px;font-weight:650;margin-top:3px}}
.tile .n{{font-size:12px;color:var(--ink3);margin-top:2px}}
.scroll{{overflow-x:auto;margin:10px 0}}
table{{border-collapse:collapse;width:100%;font-size:13px;min-width:540px}}
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
.prov{{font-size:12px;color:var(--ink3);font-family:ui-monospace,Menlo,monospace;
background:var(--surf2);border-radius:8px;padding:12px 14px;word-break:break-all}}
</style>
<div class="wrap">
<h1>Pre-market microstructure &mdash; ceilings, walls, chop and exits</h1>
<div class="sub">182 pre-market trades &middot; {run_id} &middot; commit <code>{commit}</code></div>

<div class="cond"><b>STANDING CONDITIONS.</b> Book is <b>partially remediated (C only)</b> &mdash;
the <code>W</code> check and the whole <code>dep_*</code> family failed the Phase-0 lookahead
audit and <b>remain in the book's selection path</b>. The wall features on this page were
<b>rebuilt clean</b> from the raw MBP-10 archive at the <b>fill&minus;1</b> snapshot, so the
ANALYSIS here is pre-fill; that does not repair the book's own selection. Cells under 10 trades
are marked <span class="pill warn">insufficient</span> and must not be read as edge. IS and OOS
are different regimes &mdash; one transition, observed once.</div>

<h2>Answers, up front</h2>
<div class="ans"><div class="q">Do trades at particular times only reach +1&ndash;2R then come back?</div>
<div class="a">No time-of-day pattern. The stall rate is flat: 14% / 13% / 14% across
early / mid / late.</div></div>
<div class="ans"><div class="q">Is early pre-market thin, with no liquidity wall to target?</div>
<div class="a">Not testable as asked &mdash; and what is testable says no. The 10-level book spans
~2 points, so a &ldquo;magnet&rdquo; 20&ndash;50 points out is invisible in this data.
Book thickness is <b>not</b> lower early (79 vs 64 vs 78).</div></div>
<div class="ans"><div class="q">Do late trades get chopped or swept, so only the stop fills?</div>
<div class="a">The opposite. Late trades are the <b>cleanest</b> (efficiency 0.222 vs 0.166) with
the <b>highest</b> 30-minute MFE (5.93R vs 1.63R) and the same stop-out rate.</div></div>
<div class="ans"><div class="q">Can a management rule remove losses while keeping winners?</div>
<div class="a">No. The best of 68 rules gained {money(SW['best']['d_is'])} in-sample and lost
<b>{money(SW['best']['d_oos'])}</b> out-of-sample.</div></div>""")

# Q-A
seg = M["qa_seg"]
A("""<h2>1 &mdash; The +1&ndash;2R ceiling question</h2>
<p>&ldquo;Stall&rdquo; = reached +1R but never +2R. &ldquo;Gave back&rdquo; = reached +1R or
better and still finished a loss. &ldquo;SL, no 1R&rdquo; = stopped out having never reached
+1R.</p>
<div class="scroll"><table><thead><tr><th>Segment</th><th>n</th><th>Median MFE</th>
<th>Stalled 1&ndash;2R</th><th>Gave back</th><th>SL, no 1R</th><th>Mean R</th><th>Net</th>
</tr></thead><tbody>""")
for s in ("early 08:00-08:29", "mid 08:30-08:59", "late 09:00-09:29"):
    v = seg[s]
    A(f"<tr><td>{s}</td><td>{v['n']}</td><td>{num(v['med_mfe'])}R</td>"
      f"<td>{pct(v['stall'])}</td><td>{pct(v['gave_back'])}</td><td>{pct(v['sl_no_1r'])}</td>"
      f"<td>{v['meanR']:+.3f}</td><td>{money(v['net'])}</td></tr>")
A("""</tbody></table></div>
<p><b>The pattern you suspected is not in the data by time of day.</b> The stall rate is
essentially identical across the window, and median MFE is flat (1.82 / 2.08 / 1.98R). What
does vary is give-back &mdash; 20% early vs <b>7% late</b> &mdash; i.e. early trades are more
likely to reach +1R and then lose it. That is a give-back difference, not a ceiling
difference.</p>
<div class="scroll"><table><thead><tr><th>Bucket</th><th>n</th><th>Median MFE</th>
<th>&lt;1R</th><th>1&ndash;2R</th><th>2&ndash;4R</th><th>4R+</th><th>Gave back</th>
<th>Net</th></tr></thead><tbody>""")
for b, v in M["qa_buckets"].items():
    ins = ' <span class="pill warn">insufficient</span>' if v["insufficient"] else ""
    A(f"<tr><td>{b}{ins}</td><td>{v['n']}</td><td>{num(v['med_mfe'])}R</td>"
      f"<td>{pct(v['bins'][0])}</td><td>{pct(v['bins'][1])}</td><td>{pct(v['bins'][2])}</td>"
      f"<td>{pct(v['bins'][3])}</td><td>{pct(v['gave_back'])}</td>"
      f"<td>{money(v['net'])}</td></tr>")
A("</tbody></table></div>")

# Q-B
qb = M["qb"]
A(f"""<h2>2 &mdash; Liquidity walls (heatmap magnet)</h2>
<div class="cond"><b>The honest limitation, before the numbers.</b> The archive is
<b>MBP-10</b> &mdash; ten price levels per side. In practice that spans about <b>2 points</b>
of price. The median &ldquo;wall ahead&rdquo; sits <b>1.8 points away, i.e. 0.12R</b>. A
liquidity magnet in the sense you mean &mdash; a large resting block 20&ndash;50 points out that
price travels toward &mdash; <b>is not visible in this data at all</b>. What is measured below is
top-of-book shape, not a heatmap. Answering the question you actually asked needs full-depth or
volume-profile data that this archive does not contain.</div>
<p class="muted">Walls rebuilt at the fill&minus;1 snapshot (strictly pre-fill). Measured
side-effect: the at-fill convention the canon used differs from the pre-fill one on
<b>{num(M.get('leak_pct'),1)}%</b> of trades &mdash; a direct measurement of the
<code>dep_*</code> leak, previously only asserted. Depth coverage
{M['depth_coverage']}/{M['n']} trades.</p>
<div class="scroll"><table><thead><tr><th>Group</th><th>n</th><th>Median MFE</th>
<th>Gave back</th><th>SL, no 1R</th><th>Mean R</th><th>Net</th></tr></thead><tbody>""")
for k, v in qb.items():
    if k in ("stall", "by_seg"):
        continue
    if v.get("insufficient"):
        A(f"<tr><td>{k}</td><td>{v['n']}</td><td colspan='5' class='muted'>"
          f"<span class='pill warn'>insufficient</span></td></tr>")
        continue
    A(f"<tr><td>{k}</td><td>{v['n']}</td><td>{num(v['med_mfe'])}R</td>"
      f"<td>{pct(v['gave_back'])}</td><td>{pct(v['sl_no_1r'])}</td>"
      f"<td>{v['meanR']:+.3f}</td><td>{money(v['net'])}</td></tr>")
st = qb["stall"]
A(f"""</tbody></table></div>
<p><b>Walls do not cap moves and do not sort outcomes.</b> Correlation between wall distance and
MFE is <b>{st['rho']:+.3f}</b> (n={st['n']}), and <b>{pct(st['reach_rate'])}</b> of trades push
at least as far as the wall &mdash; if the wall were a barrier that number would be low. Big
walls vs small walls give +0.422R vs +0.307R on 85 and 81 trades, a difference well inside
noise at this sample.</p>
<p><b>And early pre-market is not thinner.</b> Median book thickness by segment:
{" &middot; ".join(f"{k.split()[0]} <b>{v['thick']:.0f}</b>" for k, v in qb.get("by_seg", {}).items())}
&mdash; the early window is if anything the deepest. The &ldquo;lack of volume&rdquo; premise
does not hold at the order-book level.</p>""")

# Q-C
qc = M["qc"]
A("""<h2>3 &mdash; Chop and sweeps near the open</h2>
<p><code>eff30</code> = |net move| &divide; total distance travelled over 30 minutes. 1.0 is a
clean one-way move; near 0 is chop. &ldquo;Adverse first&rdquo; = the worst excursion happened
before the best one, i.e. price swept against the trade before working.</p>
<div class="scroll"><table><thead><tr><th>Segment</th><th>n</th><th>Efficiency (30m)</th>
<th>Mean crossings</th><th>Adverse first</th><th>SL, no 1R</th><th>Median MFE (30m)</th>
</tr></thead><tbody>""")
for s, v in qc.items():
    A(f"<tr><td>{s}</td><td>{v['n']}</td><td>{num(v['eff30'],3)}</td>"
      f"<td>{num(v['crosses'],1)}</td><td>{pct(v['adverse_first'])}</td>"
      f"<td>{pct(v['sl_no_1r'])}</td><td>{num(v['mfe30'])}R</td></tr>")
A("""</tbody></table></div>
<p><b>This overturns the premise.</b> The late window is the <i>least</i> choppy by efficiency
(0.222 vs 0.166 early), carries by far the largest 30-minute excursion (5.93R vs 1.63R), and
stops out without reaching +1R at the <i>same</i> rate as everywhere else (34% vs 37%). It also
has the best mean R in the book (+0.999).</p>
<p>The one thing that does support your read: <b>adverse-first rises to 17% late</b> against 6%
early &mdash; late entries are nearly three times more likely to be swept against before they
work. But that is 5 trades out of 29, and the same window still produces the best returns, so
the sweep is not costing money. The single ugly cell is <b>09:20&ndash;09:24</b> (71% stopped
without reaching 1R, &minus;$578) &mdash; <b>7 trades</b>, insufficient.</p>""")

# sweep
A(f"""<h2>4 &mdash; The variables test: can a rule cut losses and keep winners?</h2>
<p>{SW['n_configs']} configurations &mdash; 17 management rules (fixed targets 1&ndash;4R,
breakeven at 1/1.5/2R, trail-from-peak, time stops at 15/30/45/60 min) &times; 4 scopes (all
trades, or applied only to early / mid / late). The rule is chosen on the <b>in-sample half
only</b> and judged out-of-sample. Costs: $1.24/micro round trip, +$0.50/micro on marketable
exits.</p>
<div class="tiles">
 <div class="tile"><div class="k">IS-selected rule</div>
  <div class="v" style="font-size:16px">{SW['best']['rule']}</div>
  <div class="n">scope: {SW['best']['scope']}</div></div>
 <div class="tile"><div class="k">In-sample gain</div>
  <div class="v" style="color:var(--ok)">{money(SW['best']['d_is'])}</div>
  <div class="n">the number that is NOT evidence</div></div>
 <div class="tile"><div class="k">Out-of-sample</div>
  <div class="v" style="color:var(--bad)">{money(SW['best']['d_oos'])}</div>
  <div class="n">the number that matters</div></div>
 <div class="tile"><div class="k">Beat canon OOS</div>
  <div class="v">{SW['n_beat_oos']}/{SW['n_configs']}</div>
  <div class="n">fewer than half &mdash; worse than a coin</div></div>
</div>
<h3>Best-of-68 selection null &mdash; {NU['n']} day-block-permuted splits</h3>
<p>Running the same select-then-evaluate procedure on random half-splits shows what the
procedure produces from noise alone.</p>
<div class="scroll"><table><thead><tr><th></th><th>In-sample gain</th><th>Out-of-sample</th>
</tr></thead><tbody>
<tr><td><b>Real split</b></td><td>{money(NU['real_is'])}</td>
<td><b>{money(NU['real_oos'])}</b></td></tr>
<tr><td>Null median</td><td>{money(NU['null_is_med'])}</td><td>{money(NU['null_oos_med'])}</td></tr>
<tr><td>Null p5 / p95 (OOS)</td><td class="muted">p90 {money(NU['null_is_p90'])}</td>
<td>{money(NU['null_oos_p5'])} / {money(NU['null_oos_p95'])}</td></tr>
<tr><td>Real percentile</td><td>{NU['real_is_pct']:.0f}th</td>
<td>{NU['real_oos_pct']:.0f}th &nbsp;{pill(NU['passes'],'PASS','FAIL &mdash; gate was &gt;95th')}</td></tr>
</tbody></table></div>
<p class="verdict"><b>The selection is worth nothing, and the null proves it.</b> Picking the
best of 68 rules on <i>any</i> random half yields a median in-sample gain of
{money(NU['null_is_med'])} <i>by construction</i> &mdash; the real split's
{money(NU['real_is'])} is actually <b>below</b> that, at the {NU['real_is_pct']:.0f}th
percentile. Out-of-sample the same procedure shrinks to a median of
{money(NU['null_oos_med'])}, and only {NU['pct_null_positive_oos']:.0f}% of null splits make
money. The real out-of-sample result, {money(NU['real_oos'])}, sits at the
{NU['real_oos_pct']:.0f}th percentile &mdash; ordinary noise. <b>Median shrinkage from
in-sample to out-of-sample is {money(NU['null_oos_med'] - NU['null_is_med'])}.</b> That number
is the price of sweeping.</p>
<p>This is the third independent confirmation on this book: H1 (flat targets 1.5&ndash;4R) and
H4 (bar-close MAE cuts) already failed under walk-forward, and Job 1 showed breakeven-at-+1R is
a wash (+$1,140 across 27 affected trades). The reason is structural &mdash; the winners that
carry the book retrace a median <b>5.97R</b> after first touching +1R, so any rule tight enough
to cut losers also amputates them.</p>""")

A(f"""<h2>Provenance</h2>
<div class="prov">
run_id &nbsp; {run_id}<br>
commit &nbsp; {commit}<br>
book &nbsp; job2_books/sized_C_news &mdash; PARTIALLY REMEDIATED (C only); W and dep_* leaky<br>
trades &nbsp; {M['n']} pre-market, 08:00&ndash;09:29 ET half-open bins<br>
walls &nbsp; rebuilt from raw MBP-10 at the fill&minus;1 snapshot; coverage
{M['depth_coverage']}/{M['n']}; at-fill vs pre-fill disagreement {num(M.get('leak_pct'),1)}%<br>
sweep &nbsp; {SW['n_configs']} configurations; selection on IS half only; null =
{NU['n']} day-block-permuted splits<br>
costs &nbsp; $1.24/micro round trip; $0.50/micro slippage on marketable exits; resting-limit
target fills unslipped; canon baseline carries its own cost convention (stated, not merged)<br>
regenerate &nbsp; python3 research/sweep_2026_07/micro/build_dashboard.py
</div>
</div>
<script>(function(){{var t=localStorage.getItem('theme');
if(t)document.documentElement.setAttribute('data-theme',t);}})();</script>""")

path = f"{HERE}/dashboard_micro.html"
open(path, "w").write("\n".join(H))
print(f"wrote {path} ({os.path.getsize(path):,} bytes)")
