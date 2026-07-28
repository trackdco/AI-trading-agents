#!/usr/bin/env python3
"""Rebuild research/sweep_2026_07/dashboard.html — v2, with Phase 2 results.

Self-contained, offline, section order per the brief (validity leads). Phase-0/1 headline tables
are recomputed from the frame; the fuller Phase-1 lane detail lives in the v1 dashboard already
delivered to Brake (the lane artefacts died with the container and are summarised, not faked).
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
R2 = json.load(open(f"{HERE}/phase2_results.json"))
F = pd.read_csv(f"{HERE}/phase2_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
F["et"] = F.ft.dt.tz_convert("America/New_York")
F["hm"] = F.et.dt.hour * 60 + F.et.dt.minute
rng = np.random.default_rng(5)

def wilson(k, n):
    if n == 0:
        return [0, 1]
    p, z = k / n, 1.96
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - h, c + h]

def boot_ci(v, n=4000):
    m = [np.mean(rng.choice(v, size=len(v), replace=True)) for _ in range(n)]
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]

# time-of-day cells (recomputed: n, P&L, mean R + CI, hit + Wilson)
cells = []
for lo, hi, lab in [(480, 510, "08:00-08:29"), (510, 540, "08:30-08:59"), (540, 570, "09:00-09:29")]:
    s = F[(F.hm >= lo) & (F.hm < hi)]
    cells.append(dict(bucket=lab, n=len(s), pl=float(s.pl.sum()), meanR=float(s.R.mean()),
                      ci=boot_ci(s.R.values), hit=float((s.pl > 0).mean()),
                      wil=wilson(int((s.pl > 0).sum()), len(s)),
                      oos_n=int(s.oos.sum())))

# survival + give-back from mfe_R (inclusive convention)
surv = []
prev = len(F)
for X in (1, 2, 3, 4):
    nX = int((F.mfe_R >= X).sum())
    surv.append(dict(X=X, p=nX / prev, n=nX, nprev=prev))
    prev = nX
give = []
for L in (1, 2, 3, 4):
    t = F[F.mfe_R >= L]
    red = t[t.pl < 0]
    give.append(dict(L=L, n=len(t), share=len(t) / len(F), held=int((t.R >= L).sum()),
                     red=len(red), red_pl=float(red.pl.sum()),
                     med_gb=float((t.mfe_R - t.R).median())))

ES = R2["effective_sample"]
chip = (f"effective sample: +4R cohort n={ES['plus4R_cohort_n']} carries "
        f"{ES['plus4R_share_of_window_pl']*100:.1f}% of window P&L; "
        f"{ES['plus4R_in_OOS_half']} of them are OOS; top-5 = "
        f"{ES['top5_pl_share_of_OOS']*100:.1f}% of OOS P&L")

H1, H2, H4, H5, H6 = R2["H1"], R2["H2"], R2["H4"], R2["H5"], R2["H6"]

def usd(v):
    return ("+$" if v >= 0 else "-$") + format(abs(round(v)), ",")

# ---- verdicts against the pre-committed criteria
verd = []
inc, wf = H1["incumbent_oos"], H1["walkforward_oos"]
h1_pass = wf["terminal"] > inc["terminal"]
verd.append(("H1 bigger fixed target beats canon (OOS, walk-forward)",
             f"FAIL — walk-forward {usd(wf['terminal'])} vs incumbent {usd(inc['terminal'])}; "
             f"selection also flips targets mid-stream ({', '.join(m+'→'+str(t)+'R' for m,t in H1['picks'][:3])}…), "
             f"and bust-prob {H1['bust_oos_walkforward']:.1f}% vs {H1['bust_oos_incumbent']:.1f}%",
             "fail" if not h1_pass else "pass"))
ng, sw = H2["cells"]["no_gate"], H2["cells"]["skip_with_bias"]
by = sw["by_half"]
h2_2025 = by.get("2025", {})
h2_2026 = by.get("2026", {})
ng25, ng26 = ng["by_half"].get("2025", {}), ng["by_half"].get("2026", {})
verd.append(("H2 skip-with-bias beats no-gate (IN-SAMPLE; needs both halves)",
             f"NOT ESTABLISHED — pooled {usd(sw['funded']['terminal'])} vs {usd(ng['funded']['terminal'])}, "
             f"but 2025 half: gate {usd(h2_2025.get('pl',0))} vs no-gate {usd(ng25.get('pl',0))}; "
             f"2026 half: {usd(h2_2026.get('pl',0))} vs {usd(ng26.get('pl',0))} — the criterion "
             "required reproduction in BOTH halves",
             "inc"))
best_th = max(H4["cells"], key=lambda k: H4["cells"][k]["funded_all"]["terminal"])
bt = H4["cells"][best_th]
h4_beats = bt["funded_all"]["terminal"] > H4["incumbent_all"]["terminal"]
verd.append((f"H4 MAE-cut beats canon (IN-SAMPLE; θ grid best = {best_th.replace('theta_','θ=')})",
             f"{'IN-SAMPLE PASS' if h4_beats else 'FAIL'} — best cell {usd(bt['funded_all']['terminal'])} vs incumbent "
             f"{usd(H4['incumbent_all']['terminal'])}; cut {bt['n_cut']} trades incl. {bt['winners_cut']} winners; "
             f"drop-5 {usd(bt['drop5'])} vs incumbent drop-5 {usd(H4['incumbent_drop5'])}. "
             f"Winner close-MAE max: IS {H4['winner_close_MAE_max_IS']:.2f}R / OOS {H4['winner_close_MAE_max_OOS']:.2f}R "
             "— confirmation requires fresh sessions (A1)",
             "wn" if h4_beats else "fail"))
ci5 = H5["diff_clean_minus_exposed_ci"]
h5_diff = ci5 and (ci5[0] > 0 or ci5[1] < 0)
verd.append(("H5 contract stratum indistinguishable (integrity)",
             f"{'FAIL — strata differ' if h5_diff else 'PASS (weak) — no detectable difference'}: "
             f"clean mean R {H5['mean_R_clean']:+.3f} vs exposed {H5['mean_R_exposed']:+.3f}, "
             f"day-block CI on diff [{ci5[0]:+.2f}, {ci5[1]:+.2f}], n_exposed={H5['n_exposed']} "
             f"carrying {H5['exposed_share_of_pl']*100:.1f}% of window P&L — thin n makes a null weak evidence",
             "fail" if h5_diff else "inc"))
verd.append(("H6 pre-market cannot carry itself (constraint)",
             f"CONFIRMED naked / OVERTURNED with spine — bust%: floor/no-halt {H6['floor_nohalt']:.1f}%, "
             f"floor/halt {H6['floor_halt']:.1f}%, DD-scaled/no-halt {H6['ddscale_nohalt']:.1f}%, "
             f"DD-scaled/halt {H6['ddscale_halt']:.1f}%. Both answers are true and describe different systems",
             "wn"))

DATA = dict(R2=R2, cells=cells, surv=surv, give=give, chip=chip, verd=verd)

css = """
:root{color-scheme:light;--s0:#f6f6f4;--s1:#fcfcfb;--bd:#e3e2dd;--tp:#0b0b0b;--ts:#52514e;--tm:#82817c;
--c1:#2a78d6;--c2:#eb6834;--ok:#1baf7a;--bad:#d64545;--warn:#eda100;--gr:#eceae5}
@media(prefers-color-scheme:dark){:root:where(:not([data-theme=light])){color-scheme:dark;--s0:#121211;--s1:#1a1a19;
--bd:#33322e;--tp:#fff;--ts:#c3c2b7;--tm:#8d8c84;--c1:#3987e5;--c2:#d95926;--ok:#199e70;--bad:#e06666;--warn:#c98500;--gr:#2a2926}}
:root[data-theme=dark]{color-scheme:dark;--s0:#121211;--s1:#1a1a19;--bd:#33322e;--tp:#fff;--ts:#c3c2b7;--tm:#8d8c84;
--c1:#3987e5;--c2:#d95926;--ok:#199e70;--bad:#e06666;--warn:#c98500;--gr:#2a2926}
*{box-sizing:border-box}body{margin:0;background:var(--s0);color:var(--tp);
font:14px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.w{max-width:1150px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:20px;font-weight:650;margin:0 0 4px}h2{font-size:15px;font-weight:640;margin:36px 0 6px}
.sub,.note{color:var(--ts);font-size:12.5px}.note{margin:0 0 12px;max-width:80ch}
.card{background:var(--s1);border:1px solid var(--bd);border-radius:10px;padding:15px 18px;margin-bottom:12px}
table{border-collapse:collapse;width:100%;font-size:12.3px;font-variant-numeric:tabular-nums}
th{text-align:right;font-weight:600;color:var(--ts);padding:6px 9px;border-bottom:1px solid var(--bd);
font-size:11px;text-transform:uppercase;letter-spacing:.04em;white-space:nowrap}
th:first-child,td:first-child{text-align:left}
td{padding:6px 9px;border-bottom:1px solid var(--gr);text-align:right;white-space:nowrap}
.scroll{overflow-x:auto}.pos{color:var(--ok)}.neg{color:var(--bad)}
.alert{border-left:3px solid var(--bad);padding:12px 16px;margin:12px 0;background:var(--s1);border-radius:0 10px 10px 0}
.alert.w{border-left-color:var(--warn)}.alert.g{border-left-color:var(--ok)}
.badge{display:inline-block;padding:1px 8px;border-radius:20px;font-size:10.5px;font-weight:650;text-transform:uppercase}
.b-fail{background:color-mix(in srgb,var(--bad) 16%,transparent);color:var(--bad)}
.b-pass{background:color-mix(in srgb,var(--ok) 16%,transparent);color:var(--ok)}
.b-inc{background:color-mix(in srgb,var(--tm) 18%,transparent);color:var(--ts)}
.b-wn{background:color-mix(in srgb,var(--warn) 18%,transparent);color:var(--warn)}
.chip{display:inline-block;background:color-mix(in srgb,var(--warn) 14%,transparent);color:var(--warn);
border-radius:7px;padding:3px 9px;font-size:11.5px;margin:4px 0}
code{font:11.5px ui-monospace,Menlo,monospace;background:var(--s0);padding:1px 5px;border-radius:4px;border:1px solid var(--bd)}
.btn{background:var(--s1);border:1px solid var(--bd);color:var(--ts);border-radius:7px;padding:6px 12px;cursor:pointer;font-size:12px}
"""

def h1_rows():
    out = []
    for name, c in H1["cells"].items():
        o = c["oos_funded"]
        out.append(f"<tr><td>fixed {name}</td><td>{usd(o['terminal'])}</td>"
                   f"<td>{usd(c['oos_drop5'])}</td><td>{o['halted_days']}</td>"
                   f"<td>{'yes' if o['busted'] else 'no'}</td></tr>")
    inc = H1["incumbent_oos"]
    out.append(f"<tr><td><b>incumbent (canon)</b></td><td><b>{usd(inc['terminal'])}</b></td>"
               f"<td><b>{usd(H1['incumbent_oos_drop5'])}</b></td><td>{inc['halted_days']}</td>"
               f"<td>{'yes' if inc['busted'] else 'no'}</td></tr>")
    wf = H1["walkforward_oos"]
    out.append(f"<tr><td><b>walk-forward selected</b></td><td><b>{usd(wf['terminal'])}</b></td>"
               f"<td><b>{usd(H1['walkforward_oos_drop5'])}</b></td><td>{wf['halted_days']}</td>"
               f"<td>{'yes' if wf['busted'] else 'no'}</td></tr>")
    return "".join(out)

def h2_rows():
    out = []
    for name, c in H2["cells"].items():
        if name == "alignment_counts":
            continue
        b25, b26 = c["by_half"].get("2025", {}), c["by_half"].get("2026", {})
        out.append(f"<tr><td>{name}</td><td>{c['n']}</td><td>{usd(c['funded']['terminal'])}</td>"
                   f"<td>{c['mean_R']:+.3f} [{c['mean_R_ci'][0]:+.2f},{c['mean_R_ci'][1]:+.2f}]</td>"
                   f"<td>{usd(b25.get('pl',0))} (n={b25.get('n',0)})</td>"
                   f"<td>{usd(b26.get('pl',0))} (n={b26.get('n',0)})</td></tr>")
    return "".join(out)

def h4_rows():
    out = []
    for name, c in H4["cells"].items():
        fa = c["funded_all"]
        out.append(f"<tr><td>{name.replace('theta_','θ=')}</td><td>{usd(fa['terminal'])}</td>"
                   f"<td>{c['n_cut']}</td><td class='neg'>{c['winners_cut']}</td>"
                   f"<td>{usd(c['drop5'])}</td></tr>")
    out.append(f"<tr><td><b>incumbent</b></td><td><b>{usd(H4['incumbent_all']['terminal'])}</b></td>"
               f"<td>—</td><td>—</td><td><b>{usd(H4['incumbent_drop5'])}</b></td></tr>")
    return "".join(out)

verd_rows = "".join(
    f"<tr><td style='text-align:left'>{q}</td><td style='text-align:left'>{a}</td>"
    f"<td><span class='badge b-{k}'>{dict(fail='fail',pass_='pass',inc='inconclusive',wn='mixed').get(k,k)}</span></td></tr>"
    for q, a, k in verd)

tod_rows = "".join(
    f"<tr><td>{c['bucket']}</td><td>{c['n']}</td><td>{c['oos_n']}</td><td>{usd(c['pl'])}</td>"
    f"<td>{c['meanR']:+.3f} [{c['ci'][0]:+.2f},{c['ci'][1]:+.2f}]</td>"
    f"<td>{c['hit']*100:.1f}% [{c['wil'][0]*100:.1f},{c['wil'][1]*100:.1f}]</td></tr>"
    for c in cells)
surv_rows = "".join(f"<tr><td>+{s['X']}R</td><td>{s['n']}/{s['nprev']}</td><td>{s['p']:.3f}</td></tr>" for s in surv)
give_rows = "".join(
    f"<tr><td>+{g['L']}R</td><td>{g['n']}</td><td>{g['share']*100:.1f}%</td><td>{g['held']}</td>"
    f"<td class='neg'>{g['red']} ({usd(g['red_pl'])})</td><td>{g['med_gb']:+.2f}R</td></tr>" for g in give)
picks = ", ".join(f"{m}→{t}R" for m, t in H1["picks"])

html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NY pre-market sweep — Phase 2 results</title><style>{css}</style></head><body><div class="w">
<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap">
<div><h1>NY pre-market sweep — Phase 0 gate · Phase 1 · Phase 2 results</h1>
<div class="sub">08:00–09:29 ET · n=216 · +$18,376.00 · clean book (404 / +$52,522.81) · commit 14ac690 ·
17 pre-registered comparisons (A5)</div></div>
<button class="btn" onclick="const r=document.documentElement,c=r.getAttribute('data-theme');
r.setAttribute('data-theme',(c?c==='dark':matchMedia('(prefers-color-scheme: dark)').matches)?'light':'dark')">◐ theme</button></div>

<div class="alert"><b>H0 CONDITIONALITY (Amendment 2).</b> The 40 leaky columns didn't only score
features — they <b>selected these 216 trades</b>. Every result on this page is conditional on a
trade population that may not survive re-derivation with clean inputs. H0 (re-derive the book
without the leaky columns) is a rulebook call for Brake/Pat and is not answered here.</div>
<div class="chip">{chip} — every funded-P&L figure below is effectively a ~15-observation OOS test (A3)</div>

<h2>1 · Validity gate (unchanged from Phase 0 report)</h2>
<div class="card scroll"><table><thead><tr><th>item</th><th>status</th><th>evidence</th></tr></thead><tbody>
<tr><td>0a order-flow source</td><td><span class="badge b-wn">no data</span></td><td>0 .scid files; Databento substitute awaiting ruling</td></tr>
<tr><td>0c lookahead</td><td><span class="badge b-fail">fail</span></td><td>40/161 columns; W flips 41.6% re-read pre-fill</td></tr>
<tr><td>0d clock</td><td><span class="badge b-pass">pass</span></td><td>1-hour slip arithmetically excluded</td></tr>
<tr><td>0d contract</td><td><span class="badge b-fail">fail</span></td><td>23/216 trades = 46.5% of window P&L on wrong-contract days</td></tr>
<tr><td>0e census</td><td><span class="badge b-inc">binding</span></td><td>OOS 69/24/16; floor 30 (sourced to the brief, A6)</td></tr>
</tbody></table></div>

<h2>2 · Phase 1 headlines (detail in the v1 dashboard already delivered)</h2>
<div class="card scroll"><h3 style="font-size:13px;color:var(--ts);margin:0 0 6px">Time-of-day (fixed 30-min grid)</h3>
<table><thead><tr><th>bucket</th><th>n</th><th>OOS n</th><th>P&L</th><th>mean R [boot 95]</th><th>hit [Wilson 95]</th></tr></thead>
<tbody>{tod_rows}</tbody></table>
<div class="note" style="margin-top:8px">All pairwise difference-of-means CIs include zero (Phase 1).
09:00 sign-flips by year. Only 08:00–08:29 clears the 30-OOS floor (A4: 69/24/16 correct; 138 was total n).</div></div>
<div class="card scroll" style="display:flex;gap:24px;flex-wrap:wrap">
<div style="flex:1;min-width:260px"><h3 style="font-size:13px;color:var(--ts);margin:0 0 6px">Continuation hazard</h3>
<table><thead><tr><th>rung</th><th>n</th><th>P(X | X−1)</th></tr></thead><tbody>{surv_rows}</tbody></table></div>
<div style="flex:2;min-width:340px"><h3 style="font-size:13px;color:var(--ts);margin:0 0 6px">Give-back (inclusive MFE)</h3>
<table><thead><tr><th>touched</th><th>n</th><th>% book</th><th>held</th><th>finished red</th><th>med give-back</th></tr></thead>
<tbody>{give_rows}</tbody></table></div></div>

<h2>3 · H1 — fixed targets vs canon <span class="badge b-pass">OOS-legitimate</span></h2>
<p class="note">Walk-forward, expanding monthly, selection on train terminal funded P&L only.
OOS = {R2['oos_n']} trades from {R2['split_day']}. Costs: $1.24 RT/micro + 1-tick slip on marketable exits
(incumbent uses recorded pl — cost models differ at the margin). Monthly picks: {picks}.</p>
<div class="card scroll"><table><thead><tr><th>variant</th><th>OOS funded P&L</th><th>OOS drop-5</th>
<th>halted days</th><th>busted</th></tr></thead><tbody>{h1_rows()}</tbody></table>
<div class="note" style="margin-top:8px">Bust probability (day-block bootstrap over the OOS window):
incumbent {H1['bust_oos_incumbent']:.2f}% vs walk-forward {H1['bust_oos_walkforward']:.2f}%.</div></div>

<h2>4 · H2 — bias-of-day gate <span class="badge b-wn">IN-SAMPLE (A1)</span></h2>
<p class="note">Bias from the committed artefact <code>output/amt_daytypes.csv</code> (the frozen
build_daytypes definition; Phase 1 verified it re-derives 912/912 from raw bars). Alignment counts:
{H2['cells']['alignment_counts']}. Selected FROM Phase-1 results on these same trades — the year columns
are a descriptive split, NOT confirmation; confirmation needs sessions after 2026-07-10.</p>
<div class="card scroll"><table><thead><tr><th>cell</th><th>n</th><th>funded P&L</th><th>mean R [day-clust 95]</th>
<th>2025 half</th><th>2026 half</th></tr></thead><tbody>{h2_rows()}</tbody></table></div>

<h2>5 · H4 — MAE cut at bar close <span class="badge b-wn">IN-SAMPLE (A1)</span></h2>
<p class="note">θ range descends from the 0.98R global max winner heat, which INCLUDES the OOS half —
the "no winner ever dug past θ" falsifier is partly pre-answered (A1). Winner close-MAE max:
IS {H4['winner_close_MAE_max_IS']:.2f}R · OOS {H4['winner_close_MAE_max_OOS']:.2f}R.</p>
<div class="card scroll"><table><thead><tr><th>cell</th><th>funded P&L (all 216)</th><th>trades cut</th>
<th>winners cut</th><th>drop-5</th></tr></thead><tbody>{h4_rows()}</tbody></table></div>

<h2>6 · H5 — contract stratum <span class="badge b-inc">integrity</span></h2>
<div class="card"><p class="note" style="margin:0">
Exposed days found: {H5['exposed_days_found']} · exposed trades n={H5['n_exposed']} carrying
{usd(H5['exposed_pl'])} = {H5['exposed_share_of_pl']*100:.1f}% of window P&L. Mean R clean
{H5['mean_R_clean']:+.3f} vs exposed {H5['mean_R_exposed']:+.3f}; day-block CI on the difference
[{ci5[0]:+.2f}, {ci5[1]:+.2f}] — includes zero, but n={H5['n_exposed']} makes this null <b>weak
evidence of safety</b>, stated per registration.</p></div>

<h2>7 · H6 — standalone viability <span class="badge b-wn">constraint</span></h2>
<div class="card scroll"><table><thead><tr><th>sizing × halts</th><th>bust % (day-block bootstrap, {R2['comparisons']['H6']} cells)</th></tr></thead>
<tbody><tr><td>floor · no halts</td><td class="neg">{H6['floor_nohalt']:.2f}%</td></tr>
<tr><td>floor · Tier-1 halts</td><td class="neg">{H6['floor_halt']:.2f}%</td></tr>
<tr><td>DD-scaled · no halts</td><td>{H6['ddscale_nohalt']:.2f}%</td></tr>
<tr><td>DD-scaled · Tier-1 halts</td><td class="pos">{H6['ddscale_halt']:.2f}%</td></tr></tbody></table></div>

<h2>8 · Verdicts against pre-committed criteria</h2>
<div class="card scroll"><table><thead><tr><th>hypothesis</th><th>result</th><th>verdict</th></tr></thead>
<tbody>{verd_rows}</tbody></table>
<div class="note" style="margin-top:8px">17 comparisons run (A5). Under a global null the expected minimum
p ≈ 0.06, so no single unadjusted p near 0.05 in this study means anything. Not tested: H3 (structurally
INCONCLUSIVE, A5), fast-loser filters, order-flow conviction, depth rules, 09:00-specific rules,
spread/VWAP filters — reasons in <code>01_hypotheses.md</code>.</div></div>

<h2>9 · Open questions</h2>
<div class="card"><ul style="margin:4px 0 0;padding-left:20px;color:var(--ts);font-size:12.5px">
<li><b>H0</b> — re-derive the book without the 40 leaky columns (rulebook call; everything above is conditional on it).</li>
<li>The 23 contract-exposed trades (46.5% of window P&L) — H5 could not distinguish the strata at n=23.</li>
<li>Order-flow source ruling (Databento tape vs absent .scid).</li>
<li>Baseline ruling — the clean book is marked superseded by <code>baseline_book_news.parquet</code> (+$55,989.81/383).</li>
<li>H2/H4 confirmation requires sessions after 2026-07-10 (fresh data), per A1.</li>
</ul></div>
</div></body></html>"""

out = os.path.join(os.path.dirname(HERE), "dashboard.html")
open(out, "w").write(html)
print(f"wrote {out} ({len(html)/1024:.0f} KB)")
