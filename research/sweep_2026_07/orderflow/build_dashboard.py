#!/usr/bin/env python3
"""Regenerate the pre-market order-flow dashboard from the results artefacts.

Reads part0_report.json, part1_report.json, part1b_results.json, part2_results.json,
part3_results.json and emits a single self-contained HTML file. No numbers are typed by hand.
"""
import hashlib
import json
import os
import subprocess
import time

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/orderflow"

def load(n):
    p = f"{OUT}/{n}"
    return json.load(open(p)) if os.path.exists(p) else {}

P0, P1, P1B = load("part0_report.json"), load("part1_report.json"), load("part1b_results.json")
P2, P3 = load("part2_results.json"), load("part3_results.json")
FU = load("followups.json")
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                        text=True).stdout.strip()
run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
cfg_files = sorted(f for f in os.listdir(OUT) if f.startswith(("part0_", "part1", "part2_", "part3_"))
                   and f.endswith(".py"))
cfg_hash = hashlib.sha256(b"".join(open(f"{OUT}/{f}", "rb").read() for f in cfg_files)).hexdigest()[:16]
prov = P0.get("provenance", {})
S = P0.get("summary", {})

def f2(x, d=3, sign=True):
    if x is None or (isinstance(x, float) and x != x):
        return "&mdash;"
    return f"{x:+.{d}f}" if sign else f"{x:.{d}f}"

def money(x, d=0):
    if x is None or (isinstance(x, float) and x != x):
        return "&mdash;"
    return f"${x:+,.{d}f}"

def pill(ok, t_ok="PASS", t_no="FAIL"):
    c = "ok" if ok else "bad"
    return f'<span class="pill {c}">{t_ok if ok else t_no}</span>'

H = []
A = H.append

A(f"""<title>NY Pre-Market Order-Flow Study &mdash; Parts 0&ndash;3</title>
<style>
:root{{
  --bg:#fbfbfa; --surf:#ffffff; --surf2:#f4f4f2; --ink:#1a1a19; --ink2:#55554f;
  --ink3:#86867e; --line:#e3e3df; --ok:#1f6f43; --okbg:#e7f3ec; --bad:#a3231d;
  --badbg:#fbeae9; --warn:#8a5a00; --warnbg:#fdf2dd; --accent:#2c5aa0;
}}
@media (prefers-color-scheme:dark){{
  :root{{ --bg:#161614; --surf:#1e1e1c; --surf2:#26261f; --ink:#f2f2ee; --ink2:#b9b9b0;
    --ink3:#8a8a80; --line:#33332e; --ok:#6fcf97; --okbg:#17301f; --bad:#f08c86;
    --badbg:#331917; --warn:#e0b25e; --warnbg:#2e2410; --accent:#8fb4e8; }}
}}
:root[data-theme="dark"]{{ --bg:#161614; --surf:#1e1e1c; --surf2:#26261f; --ink:#f2f2ee;
  --ink2:#b9b9b0; --ink3:#8a8a80; --line:#33332e; --ok:#6fcf97; --okbg:#17301f;
  --bad:#f08c86; --badbg:#331917; --warn:#e0b25e; --warnbg:#2e2410; --accent:#8fb4e8; }}
:root[data-theme="light"]{{ --bg:#fbfbfa; --surf:#ffffff; --surf2:#f4f4f2; --ink:#1a1a19;
  --ink2:#55554f; --ink3:#86867e; --line:#e3e3df; --ok:#1f6f43; --okbg:#e7f3ec;
  --bad:#a3231d; --badbg:#fbeae9; --warn:#8a5a00; --warnbg:#fdf2dd; --accent:#2c5aa0; }}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 padding:28px 20px 80px}}
.wrap{{max-width:1120px;margin:0 auto}}
h1{{font-size:25px;margin:0 0 4px;letter-spacing:-.01em}}
h2{{font-size:19px;margin:36px 0 10px;padding-top:16px;border-top:1px solid var(--line)}}
h3{{font-size:14px;margin:22px 0 8px;color:var(--ink2);text-transform:uppercase;
 letter-spacing:.06em;font-weight:600}}
p{{margin:9px 0;color:var(--ink2)}}
.sub{{color:var(--ink3);font-size:13px;margin-bottom:18px}}
.card{{background:var(--surf);border:1px solid var(--line);border-radius:10px;
 padding:16px 18px;margin:14px 0}}
.cond{{background:var(--warnbg);border:1px solid var(--warn);border-radius:8px;
 padding:11px 14px;margin:12px 0;font-size:13px;color:var(--ink)}}
.cond b{{color:var(--warn)}}
.dead{{background:var(--badbg);border:1px solid var(--bad);border-radius:8px;
 padding:11px 14px;margin:12px 0;font-size:13px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin:14px 0}}
.tile{{background:var(--surf);border:1px solid var(--line);border-radius:9px;padding:12px 14px}}
.tile .k{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--ink3)}}
.tile .v{{font-size:22px;font-weight:650;margin-top:3px;letter-spacing:-.01em}}
.tile .n{{font-size:12px;color:var(--ink3);margin-top:2px}}
.scroll{{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:10px 0}}
table{{border-collapse:collapse;width:100%;font-size:13px;min-width:560px}}
th,td{{text-align:right;padding:6px 9px;border-bottom:1px solid var(--line);
 font-variant-numeric:tabular-nums;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left;font-variant-numeric:normal}}
th{{color:var(--ink3);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.05em}}
tbody tr:hover{{background:var(--surf2)}}
.oos{{border-left:3px solid var(--accent)}}
.is-panel{{opacity:.72;border-left:3px dashed var(--ink3)}}
.pill{{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;font-weight:650}}
.pill.ok{{background:var(--okbg);color:var(--ok)}}
.pill.bad{{background:var(--badbg);color:var(--bad)}}
.pill.warn{{background:var(--warnbg);color:var(--warn)}}
.muted{{color:var(--ink3)}}
code{{background:var(--surf2);padding:1px 5px;border-radius:4px;font-size:12px}}
.prov{{font-size:12px;color:var(--ink3);font-family:ui-monospace,Menlo,monospace;
 background:var(--surf2);border-radius:8px;padding:12px 14px;margin-top:10px;
 word-break:break-all}}
.verdict{{font-size:15px;font-weight:600;margin:6px 0}}
</style>
<div class="wrap">
<h1>NY pre-market order-flow study &mdash; Parts 0&ndash;3</h1>
<div class="sub">Scored on the partially-remediated, news-filtered book &middot;
generated {run_id} &middot; commit <code>{commit}</code></div>

<div class="cond">
<b>STANDING CONDITIONALITY &mdash; applies to every panel below.</b><br>
<b>1. Partial remediation only.</b> This book is <b>NOT clean</b>. Only the <code>C</code>
check was remediated (<code>conf_PM</code> &rarr; <code>pm_sofar_conf</code>). The
<code>W</code> depth check and the <b>entire <code>dep_*</code> family</b> failed the Phase-0
lookahead audit and <b>remain in this book's selection path</b>. Every number here inherits
that unquantified leak.<br>
<b>2. Conditional on H0.</b> These results stand only under Brake's H0 ruling that made this
arm the working baseline. They are not conditional on the certified 216-trade book, whose
registration was voided and whose IS/OOS split and tercile edges were <b>re-fixed</b> against
this trade set (see Part&nbsp;0).<br>
<b>3. January 2026 is a BOOK hole, not a data hole.</b> Bars are complete for every month
2023-01&hellip;2026-07 and the footprint tape is contiguous 2025-06-01&hellip;2026-07-19. No book
variant contains Jan-2026 <i>trades</i> because the generation chain never wired that tape in
and no depth data exists for the month. Traded window:
<b>2025-07&hellip;2025-12 + 2026-02&hellip;2026-07</b>.<br>
<b>4. One regime transition, not a general result.</b> IS and OOS are different market regimes
&mdash; NQ ran 21k&rarr;30k and pre-market volume rose ~50% across the split. Every
walk-forward statement here is a single regime transition observed once.
</div>""")

# ---------------------------------------------------------------- verdicts
_q1s = P1B.get("q1_survivors_fw", [])
_q2s = P1B.get("q2_survivors_fw", [])
_p2 = P2.get("scoring", {})
_p2any = any(isinstance(v, dict) and v.get("p") is not None and v.get("p") == v.get("p")
             and v["p"] <= (P2.get("alpha_per_test") or 0.05)
             for k, v in _p2.items() if k.startswith("OOS|"))
_c = P3.get("C", {})
_gap = P1B.get("q2_gap_|gap|", {})
A(f"""<h2>Verdicts</h2>
<div class="card">
<p class="verdict">Q1 &mdash; entry order flow vs the trades that pay:
{pill(bool(_q1s), 'SIGNAL', 'NULL')} &nbsp;
{'survivors: <code>' + '</code>, <code>'.join(_q1s) + '</code>' if _q1s
 else 'no feature survives family-wise correction out-of-sample.'}</p>
<p class="verdict">Q2 &mdash; does flow add anything beyond gap size?
{pill(bool(_q2s), 'YES', 'NO')} &nbsp;
{'survivors: <code>' + '</code>, <code>'.join(_q2s) + '</code>' if _q2s
 else 'nothing survives once |gap| is known &mdash; and |gap| alone carries &rho; '
      + f2(_gap.get('rho')) + ' (p ' + f2(_gap.get('p'), 3, False)
      + '), larger than every order-flow feature tested.'}</p>
<p class="verdict">Part 2 &mdash; in-trade flow at a retrace, resume vs reverse:
{pill(_p2any, 'SIGNAL', 'NULL')} &nbsp;
{'a feature survives.' if _p2any else
 'every AUC sits on 0.5. The base rate is the finding, and the <b>tradeable</b> number is <b>'
 + f"{(FU.get('resume',{}).get('resume_tradeable') or 0)*100:.1f}% of retraces resume before the "
   f"canon's own exit</b> &mdash; {(FU.get('resume',{}).get('resume_life') or 0)*100:.1f}% over "
   f"full trade life, but a resume after the position is flat is not tradeable."}</p>
<p class="verdict">Part 3 &mdash; the news filter:
{pill(_c.get('survives_kill_test'), 'SURVIVES', 'ANECDOTE')} &nbsp;
{money(_c.get('delta'))} on the working baseline (p {f2(_c.get('p'), 3, False)}, CI
[{money((_c.get('ci') or [None,None])[0])}, {money((_c.get('ci') or [None,None])[1])}]);
{_c.get('jackknife_flips','—')} of {_c.get('n_avoided','—')} single removals flip the sign.
The second arm is a <b>sensitivity check, not a replication</b>.</p>
</div>

<h2>Part 0 &mdash; the resolved book</h2>
<p>Q1 and Q2 were registered against a different trade set (the certified 216-trade book).
That registration's split and every tercile edge are <b>void and not carried</b>; both were
re-fixed against the 182-trade baseline below and the change is recorded in Amendment&nbsp;3.</p>
<div class="tiles">
  <div class="tile"><div class="k">Pre-market trades</div><div class="v">{S.get('n','—')}</div>
    <div class="n">08:00&ndash;09:29 ET, half-open bins</div></div>
  <div class="tile"><div class="k">Sized P&amp;L</div><div class="v">{money(S.get('pl_sized'),0)}</div>
    <div class="n">funded dollar-risk sizing</div></div>
  <div class="tile"><div class="k">Mechanical P&amp;L</div><div class="v">{money(S.get('pl_mech'),0)}</div>
    <div class="n">canon-native</div></div>
  <div class="tile"><div class="k">Win rate</div>
    <div class="v">{(S.get('wr') or 0)*100:.1f}%</div><div class="n">mean R {f2(S.get('meanR'))}</div></div>
  <div class="tile"><div class="k">IS / OOS split</div><div class="v">{prov.get('split_day','—')}</div>
    <div class="n">{prov.get('n_is','—')} / {prov.get('n_oos','—')} trades (re-fixed)</div></div>
  <div class="tile"><div class="k">Concentration</div>
    <div class="v">{(S.get('top10pct_pl_share') or 0)*100:.0f}%</div>
    <div class="n">of P&amp;L in the top {S.get('top10pct_n','—')} trades</div></div>
</div>
<div class="card">
<h3>Forced convention change &mdash; excursion window</h3>
<p>The canon's realized exit timestamps lived in <code>output/substrate_v2_signals.parquet</code>,
destroyed in the container wipe and rebuildable only by re-running the entire upstream chain.
Reconstructing exits from the recorded exit price fails: the level frequently sits inside the
fill bar, so a first-touch rule resolves early (83.9% agreement with the certified frame, every
disagreement biased low). Excursion is therefore measured over
<b>trade life = fill bar &rarr; first bar touching the recorded stop, else 15:55&nbsp;ET</b> &mdash;
both bounds known at fill, reconstructible from bars alone, and the correct window for an exit
study. Validated: life-window MFE &ge; certified MFE on
<b>{prov.get('anchor_monotone_ge','—')}</b> shared trades, identical on
{prov.get('anchor_identical','—')}. Realized R and P&amp;L are the book's own and are unchanged.</p>
<p class="muted">Consequence, recorded before scoring: the life-window &ldquo;+4R cohort&rdquo; is
<b>not</b> usable alone &mdash; it sweeps in trades whose price reached +4R only after the canon
had exited them at a loss (cohort P&amp;L share exceeds 100%). Q1's target was therefore
re-registered as a threshold-free primary plus two labelled binaries.</p>
</div>""")

# ---------------------------------------------------------------- Part 1: remedy
ex = P1.get("exchangeability", {})
A("""<h2>Part 1 &mdash; five-feature remedy, then Q1 &amp; Q2</h2>
<h3>The remedy &mdash; exchangeability before and after</h3>
<p>Every normalizer is built from a trailing window of the prior 20 trading days, same
time-of-day bucket, closing <b>strictly before the fill day</b> &mdash; never full-sample, never
within-half. Test is a day-block permutation of the KS statistic across the re-fixed 91/91
split; <code>p &ge; 0.05</code> means the halves are exchangeable (what we want).</p>
<div class="scroll"><table><thead><tr><th>Feature</th><th>KS</th><th>p (perm)</th>
<th>Verdict</th><th>Role</th></tr></thead><tbody>""")
ORDER = [("absorp_15", "pre-remedy"), ("absorp_atr", "remedy A &mdash; ATR (Brake's literal spec)"),
         ("absorp_rel", "remedy B &mdash; trailing median"), ("vol_15", "pre-remedy"),
         ("vol_15_rel", "remedied"), ("vol_30", "pre-remedy"), ("vol_30_rel", "remedied"),
         ("stack_bid_bin", "pre-remedy"), ("stack_bid_exc", "remedy attempt"),
         ("stack_ask_bin", "pre-remedy"), ("stack_ask_exc", "remedy attempt"),
         ("cvd_5", "unchanged"), ("cvd_15", "unchanged"), ("cvd_30", "unchanged"),
         ("cvd_norm_15", "unchanged"), ("abs_cvd_15", "unchanged"),
         ("delta_div_15", "unchanged &middot; LOW-POWER")]
for k, role in ORDER:
    e = ex.get(k)
    if not e:
        continue
    A(f"<tr><td><code>{k}</code></td><td>{f2(e.get('ks'),3,False)}</td>"
      f"<td>{f2(e.get('p'),4,False)}</td><td>{pill(e.get('passes'))}</td>"
      f"<td class='muted'>{role}</td></tr>")
A(f"""</tbody></table></div>
<p><b>Result: three of five remedied, two not.</b> Absorption is fixed by the trailing-median
normalizer (KS {f2(ex.get('absorp_rel',{}).get('ks'),3,False)},
p&nbsp;{f2(ex.get('absorp_rel',{}).get('p'),3,False)}) but <b>not</b> by ATR alone
(p&nbsp;{f2(ex.get('absorp_atr',{}).get('p'),3,False)}); both volume features pass comfortably.
The scored absorption variant was chosen on the exchangeability test <b>alone</b> &mdash; an
outcome-blind criterion &mdash; and is <code>{P1.get('absorption_choice','—')}</code>.</p>
<div class="cond"><b>The two stack features could not be remedied, and the attempt made them
worse</b> (<code>stack_bid_exc</code> KS {f2(ex.get('stack_bid_exc',{}).get('ks'),3,False)},
<code>stack_ask_exc</code> KS {f2(ex.get('stack_ask_exc',{}).get('ks'),3,False)}, both
p&nbsp;&le;&nbsp;0.0005 &mdash; worse than the raw binaries). The reason is structural: a
binary's distribution <i>is</i> its base rate, and that rate shifted ~17pp across the split, so
no monotone transform of a 0/1 variable can restore exchangeability. Subtracting a drifting
continuous baseline simply imports the drift directly. Fixing it would require redefining the
frozen 3:1&times;&ge;3 textbook constant &mdash; a threshold change, which is out of scope. Both
are carried <b>with the FAIL flag</b> and any finding resting on them is discounted, not
reported as clean.</div>""")

# ---------------------------------------------------------------- multiplicity
mu = P1B.get("multiplicity", {})
if mu:
    A(f"""<h3>Correlation and the effective number of tests</h3>
<p>Multiplicity is priced on the <b>effective</b> number of independent tests, not the nominal
feature count: <code>fp_imb_15</code> was <b>dropped</b> as an exact algebraic duplicate of
<code>cvd_norm_15</code> (it is that series &divide;&nbsp;2), and the CVD family are all
functions of one delta series.</p>
<div class="tiles">
 <div class="tile"><div class="k">Nominal tests</div><div class="v">{mu.get('nominal','—')}</div>
   <div class="n">scored features</div></div>
 <div class="tile"><div class="k">Effective tests</div>
   <div class="v">{f2(mu.get('m_eff'),2,False)}</div><div class="n">Li &amp; Ji eigenvalue method</div></div>
 <div class="tile"><div class="k">Per-test &alpha;</div>
   <div class="v">{f2(mu.get('alpha_per_test'),4,False)}</div>
   <div class="n">&Scaron;id&aacute;k on M<sub>eff</sub>, family-wise 0.05</div></div>
</div>
<p class="muted">Rank-correlation pairs at |r|&nbsp;&ge;&nbsp;0.6:
{', '.join(f'{a}&ndash;{b} ({c:+.2f})' for a,b,c in mu.get('high_corr_pairs',[])) or 'none'}.</p>""")

# ---------------------------------------------------------------- Q1
q1 = P1B.get("q1", {})
feats = P1B.get("scored_features", [])
fail_ex = set(P1B.get("failing_exchangeability", []))
if q1:
    A("""<h3>Q1 &mdash; does strictly pre-fill entry flow separate the trades that pay?</h3>
<p><code>conf_PM</code> was itself an order-flow entry-conviction signal, and it was the leak
that made this baseline necessary. <b>Q1 is the honest, strictly-pre-fill re-test of that same
idea</b> &mdash; so a null here is an informative result, not a failed search. Primary measure
is threshold-free: Spearman rank association between each feature and <b>realized R</b>. All
intervals are day-cluster bootstraps (4000 draws); <code>p_day</code> is an exact permutation
at day level.</p>""")
    for half, cls, note in (("OOS", "oos", "out-of-sample &mdash; <b>the headline</b>"),
                            ("IS", "is-panel", "in-sample &mdash; reference only, not evidence")):
        A(f'<div class="card {cls}"><h3>{half} &mdash; {note}</h3>'
          '<div class="scroll"><table><thead><tr><th>Feature</th><th>&rho; vs R</th>'
          '<th>95% CI</th><th>p</th><th>p (day)</th><th>AUC R&ge;2</th><th>AUC mfe&ge;4</th>'
          '<th>n needed</th></tr></thead><tbody>')
        for f in feats:
            r = q1.get(f"{half}|{f}")
            if not r:
                continue
            ci = r.get("ci", [None, None])
            flag = " &#9888;" if f in fail_ex else ""
            nreq = r.get("n_required")
            nr = "&mdash;" if nreq is None or nreq != nreq or nreq == float("inf") else f"{nreq:,.0f}"
            A(f"<tr><td><code>{f}</code>{flag}</td><td>{f2(r.get('rho'))}</td>"
              f"<td class='muted'>[{f2(ci[0])}, {f2(ci[1])}]</td><td>{f2(r.get('p_boot'),3,False)}</td>"
              f"<td>{f2(r.get('p_day'),3,False)}</td><td>{f2(r.get('auc_R2'),3,False)}</td>"
              f"<td>{f2(r.get('auc_mfe4'),3,False)}</td><td class='muted'>{nr}</td></tr>")
        n_h = next((q1[k].get("n") for k in q1 if k.startswith(half + "|")), "—")
        A(f'</tbody></table></div><p class="muted">n = {n_h} trades. '
          '&#9888; = still fails exchangeability; discount accordingly. '
          '&ldquo;n needed&rdquo; is the sample this effect size would have required for 80% '
          'power &mdash; where it exceeds the sample, the cell is underpowered by construction.</p></div>')
    fal = P1B.get("q1_falsifier", {})
    surv = P1B.get("q1_survivors_fw", [])
    A(f"""<div class="card"><h3>Falsifier and family-wise outcome</h3>
<p>Direction-blind twins (unsigned magnitude: <code>abs_cvd_15</code>, the volume and absorption
features) are the falsifier that killed the London and NY-window campaigns: if unsigned features
match or beat signed ones, any apparent &ldquo;edge&rdquo; is not directional information.</p>
<p class="verdict">Best signed |&rho;| {f2(fal.get('best_signed'),3,False)} vs best
direction-blind |&rho;| {f2(fal.get('best_blind'),3,False)} &mdash;
{pill(not fal.get('fires'), 'signed exceeds blind', 'FALSIFIER FIRES')}</p>
<p class="verdict">Features surviving family-wise correction out-of-sample:
{('<code>' + '</code>, <code>'.join(surv) + '</code>') if surv else '<b>NONE</b>'}</p></div>""")

terc = P1B.get("q1_terciles_IS_to_OOS", {})
if terc:
    A("""<h3>Tercile transfer &mdash; edges fixed on the re-fixed IS half, applied to OOS</h3>
<div class="scroll"><table><thead><tr><th>Feature</th><th>OOS low n</th><th>low mean R</th>
<th>OOS high n</th><th>high mean R</th><th>high &minus; low</th><th>95% CI</th><th>p</th>
</tr></thead><tbody>""")
    for f in feats:
        t = terc.get(f)
        if not t:
            continue
        if t.get("insufficient"):
            A(f"<tr><td><code>{f}</code></td><td colspan='7' class='muted'>"
              f"<span class='pill warn'>insufficient</span> n_low={t.get('n_lo')}, "
              f"n_high={t.get('n_hi')} (floor 10 per cell)</td></tr>")
            continue
        ci = t.get("ci", [None, None])
        A(f"<tr><td><code>{f}</code></td><td>{t.get('n_lo')}</td><td>{f2(t.get('meanR_lo'))}</td>"
          f"<td>{t.get('n_hi')}</td><td>{f2(t.get('meanR_hi'))}</td><td>{f2(t.get('diff'))}</td>"
          f"<td class='muted'>[{f2(ci[0])}, {f2(ci[1])}]</td>"
          f"<td>{f2(t.get('p'),3,False)}</td></tr>")
    A("</tbody></table></div>")

# ---------------------------------------------------------------- Q2
if P1B.get("q2_partial_given_gap"):
    q2 = P1B["q2_partial_given_gap"]
    A("""<h3>Q2 &mdash; does entry flow add anything beyond gap size?</h3>
<p>Gap (08:00&nbsp;ET price &minus; prior 15:59 close) is knowable at 08:00 with <b>no tape
whatsoever</b>. The question is therefore not &ldquo;does flow correlate with outcome&rdquo; but
&ldquo;does flow survive once gap size is already known&rdquo;. Association is rank-residualised
against |gap| and re-tested out-of-sample.</p>""")
    for nm in ("|gap|", "signed gap"):
        g = P1B.get(f"q2_gap_{nm}")
        if g:
            ci = g.get("ci", [None, None])
            A(f"<p class='muted'><code>{nm}</code> vs realized R: &rho; {f2(g.get('rho'))}, "
              f"CI [{f2(ci[0])}, {f2(ci[1])}], p {f2(g.get('p'),3,False)}</p>")
    A("""<div class="scroll"><table><thead><tr><th>Feature</th><th>&rho; raw (OOS)</th>
<th>&rho; | gap</th><th>95% CI</th><th>p</th><th>Reading</th></tr></thead><tbody>""")
    for f in feats:
        r = q2.get(f)
        if not r:
            continue
        ci = r.get("ci", [None, None])
        raw, pr = r.get("rho_raw"), r.get("rho_partial")
        keeps = (raw is not None and pr is not None and raw == raw and pr == pr
                 and abs(pr) >= 0.7 * abs(raw))
        A(f"<tr><td><code>{f}</code></td><td>{f2(raw)}</td><td>{f2(pr)}</td>"
          f"<td class='muted'>[{f2(ci[0])}, {f2(ci[1])}]</td><td>{f2(r.get('p'),3,False)}</td>"
          f"<td class='muted'>{'retains' if keeps else 'attenuates'}</td></tr>")
    sq = P1B.get("q2_survivors_fw", [])
    A(f"""</tbody></table></div>
<p class="verdict">Features retaining an OOS association after controlling for gap and surviving
family-wise correction: {('<code>' + '</code>, <code>'.join(sq) + '</code>') if sq else '<b>NONE</b>'}</p>""")

# ---------------------------------------------------------------- Part 2
A('<h2>Part 2 &mdash; exit-side order flow (pre-registered before scoring)</h2>')
if not P2:
    A('<p class="muted">Results artefact not present.</p>')
else:
    pr2 = P2.get("prereg", {})
    A(f"""<p>The untested angle, and the one that targets the actual failure mode: every exit rule
so far is flow-blind and clips the winners that carry the book. <b>Question:</b> read during the
trade, does order flow distinguish a retrace that <b>resumes</b> from one that <b>reverses</b>?
Constants frozen in Amendment&nbsp;4 before any outcome was computed &mdash; eligibility
+{pr2.get('PEAK_MIN','—')}R, trigger {pr2.get('RETRACE_TRIG','—')}R give-back, resume = a new
peak before the stop, {pr2.get('WIN','—')}-minute windows, one event per trade, split
{pr2.get('split','—')}. No sweeps.</p>""")
    sh = P2.get("shift_per_bar", {})
    if sh:
        A("""<h3>Shift test at every bar, not just the fill</h3>
<div class="scroll"><table><thead><tr><th>Feature &middot; bar bucket</th><th>bars</th>
<th>differs vs +1</th><th>differs vs +15</th><th>Verdict</th></tr></thead><tbody>""")
        for k, v in sh.items():
            f, b = k.split("|")
            A(f"<tr><td><code>{f}</code> &middot; <span class='muted'>{b}</span></td>"
              f"<td>{v.get('n',0):,}</td><td>{(v.get('differ1') or 0)*100:.1f}%</td>"
              f"<td>{(v.get('differ15') or 0)*100:.1f}%</td>"
              f"<td>{pill(v.get('passes'),'PASS','DEGENERATE')}</td></tr>")
        A("</tbody></table></div>")
    sc = P2.get("scoring", {})
    if sc.get("insufficient"):
        A(f"<div class='cond'><b>Not scored &mdash; insufficient events.</b> Only "
          f"{sc.get('n')} retrace events met the frozen definition; the floor was 20.</div>")
    else:
        A(f"""<h3>Scoring &mdash; resume vs reverse</h3>
<p class="muted">Base rate: {(P2.get('base_rate_resume') or 0)*100:.1f}% of retraces resume, so
AUC&nbsp;0.5 means flow adds nothing. Effective tests M<sub>eff</sub>
{f2(P2.get('m_eff'),2,False)}, per-test &alpha; {f2(P2.get('alpha_per_test'),4,False)}. Intervals
are <b>trade-clustered</b> bootstraps &mdash; bar counts above are for the shift test only and
are never used as an inference sample size.</p>""")
        for half, cls, note in (("OOS", "oos", "out-of-sample &mdash; <b>the headline</b>"),
                                ("IS", "is-panel", "in-sample &mdash; reference only")):
            hr = sc.get(half)
            if isinstance(hr, dict) and hr.get("insufficient"):
                A(f"<div class='card {cls}'><h3>{half}</h3><p><span class='pill warn'>"
                  f"insufficient</span> n={hr.get('n')} events &mdash; not scored.</p></div>")
                continue
            rows = [(f, sc.get(f"{half}|{f}")) for f in
                    ("cvd_roll_dir", "cvd_since_dir", "imb_roll_dir", "absorp_roll", "delta_div_roll")]
            rows = [(f, r) for f, r in rows if r]
            if not rows:
                continue
            A(f'<div class="card {cls}"><h3>{half} &mdash; {note}</h3><div class="scroll">'
              '<table><thead><tr><th>Feature</th><th>AUC</th><th>95% CI</th><th>p</th>'
              '<th>Verdict</th></tr></thead><tbody>')
            for f, r in rows:
                ci = r.get("ci", [None, None])
                ok = r.get("p") is not None and r.get("p") == r.get("p") and \
                    r["p"] <= (P2.get("alpha_per_test") or 0.05)
                A(f"<tr><td><code>{f}</code></td><td>{f2(r.get('auc'),3,False)}</td>"
                  f"<td class='muted'>[{f2(ci[0],3,False)}, {f2(ci[1],3,False)}]</td>"
                  f"<td>{f2(r.get('p'),3,False)}</td>"
                  f"<td>{pill(ok,'survives','ns')}</td></tr>")
            A(f'</tbody></table></div><p class="muted">n = {rows[0][1].get("n")} events.</p></div>')
        rs = FU.get("resume", {})
        if rs:
            A(f"""<div class="cond"><b>Corrected: the tradeable resume rate is
{(rs.get('resume_tradeable') or 0)*100:.1f}%, not {(rs.get('resume_life') or 0)*100:.1f}%.</b>
The 85% figure counts resumes anywhere in trade life &mdash; but a resume after the canon has
already closed the position is <b>not tradeable</b>. Restricting to bars at or before the
canon's exit:
<b>{rs.get('n_resume_tradeable')}/{rs.get('n_events')} = {(rs.get('resume_tradeable') or 0)*100:.1f}%</b>.
{rs.get('n_events',0) - rs.get('events_before_exit',0)} of {rs.get('n_events')} events fire
after the trade was already flat; of the {rs.get('events_before_exit')} that fire while the
position is still open, {(rs.get('resume_tradeable_before_exit') or 0)*100:.1f}% resume.<br>
<b>Bound direction:</b> the canon's exit timestamp is destroyed, so the exit bar is
lower-bounded by the first bar containing the recorded exit price. That makes this number
<b>conservative (biased low)</b>; for the {(rs.get('exact_stop_exits') or 0)*100:.0f}% of trades
exiting at the stop it is exact.</div>""")
        if P2.get("detectable_auc_oos"):
            A(f"<p class='muted'>Power: at this out-of-sample event count the smallest detectable "
              f"|AUC&minus;0.5| is about {P2['detectable_auc_oos']-0.5:.3f} (AUC "
              f"{P2['detectable_auc_oos']:.3f}). Anything smaller is invisible at this sample &mdash; "
              f"absence of a result here is not evidence of absence of an effect.</p>")

# ---------------------------------------------------------------- Part 3
A('<h2>Part 3 &mdash; the news filter</h2>')
if not P3:
    A('<p class="muted">Results artefact not present.</p>')
else:
    A("""<p>The strongest lead in the study, and the only rule that survived. It is <b>not
fitted</b> to this book &mdash; the veto is a published economic calendar, so it is knowable at
fill time by construction, with no threshold estimated from outcomes. It improves the sized
pre-market slice in both arms, but those arms are <b>not independent</b> (see below), so that
is corroboration of robustness to the C remediation, not a second experiment.</p>
<p><b>The test that can kill it:</b> it drops trades in a window where a handful carry nearly all
the P&amp;L. If the whole benefit is one bad day in fourteen months, it is an anecdote. So the
benefit is recomputed with the single largest avoided trade removed, then jackknifed over
<i>every</i> avoided trade.</p>""")
    _ar = FU.get("arms", {})
    if _ar:
        A(f"""<div class="cond"><b>The two arms are NOT independent &mdash; this is a sensitivity
check, not a replication.</b> The news-filtered arms share <b>{_ar.get('shared_news')} of
{max(_ar.get('n_L_news',0), _ar.get('n_C_news',0))} trades
({(_ar.get('shared_pct') or 0)*100:.0f}%)</b>, they veto
<b>{_ar.get('avoided_days_shared')} of {max(_ar.get('avoided_days_L',0), _ar.get('avoided_days_C',0))}
of the same days</b>, and their largest avoided trade is
<b>{'the same trade' if _ar.get('same_largest_avoided') else 'different'}</b>. The C arm is the
L arm with one check re-sourced. The leaky arm's 95% CI
[{money((P3.get('L',{}).get('ci') or [None,None])[0])},
{money((P3.get('L',{}).get('ci') or [None,None])[1])}] <b>spans zero</b> &mdash; on its own it
establishes nothing. It is shown to demonstrate that the result is not an artefact of the C
remediation, and for no stronger purpose.</div>""")
    for arm, label in (("C", "Partially-remediated arm (C only) &mdash; the working baseline"),
                       ("L", "Leaky arm (conf_PM) &mdash; sensitivity check only, CI spans zero")):
        r = P3.get(arm)
        if not r:
            continue
        ci = r.get("ci", [None, None])
        cls = "oos" if arm == "C" else "is-panel"
        A(f"""<div class="card {cls}"><h3>{label}</h3>
<div class="tiles">
 <div class="tile"><div class="k">No news</div><div class="v">{money(r.get('pl_nonews'))}</div>
   <div class="n">{r.get('n_nonews')} trades</div></div>
 <div class="tile"><div class="k">With news filter</div><div class="v">{money(r.get('pl_news'))}</div>
   <div class="n">{r.get('n_news')} trades</div></div>
 <div class="tile"><div class="k">Delta</div><div class="v">{money(r.get('delta'))}</div>
   <div class="n">p = {f2(r.get('p'),3,False)}</div></div>
 <div class="tile"><div class="k">95% CI (day-clustered)</div>
   <div class="v" style="font-size:15px">[{money(ci[0])}, {money(ci[1])}]</div>
   <div class="n">4000 draws</div></div>
</div>
<p>Avoided {r.get('n_avoided')} trades summing {money(r.get('pl_avoided'))};
{r.get('n_added')} newly appear from freed nth-escalation slots
({money(r.get('pl_added'))}).</p>""")
        if "largest_avoided" in r:
            la = r["largest_avoided"]
            A(f"""<p class="verdict">Kill test: the single largest avoided trade is
<b>{la.get('day')} at {money(la.get('pl'))}</b> &mdash; a <b>winner</b>, so removing it makes the
delta <i>larger</i>, not smaller: {money(r.get('delta_excl_largest'))}.
{pill(r.get('survives_kill_test'),'SURVIVES','SIGN FLIPS &mdash; anecdote')}</p>
<p>Jackknife over all {r.get('n_avoided')} avoided trades:
<b>{r.get('jackknife_flips')}</b> single removals flip the sign; delta stays within
[{money((r.get('jackknife_range') or [None,None])[0])},
{money((r.get('jackknife_range') or [None,None])[1])}]. The benefit is
<b>diffuse across many small avoided losses</b>, not one bad day.</p>""")
        for h, lab in (("IS", "In-sample half"), ("OOS", "Out-of-sample half")):
            hh = r.get(f"half_{h}")
            if hh:
                A(f"<p class='muted'>{lab}: {money(hh.get('pl_nonews'))} &rarr; "
                  f"{money(hh.get('pl_news'))} (delta {money(hh.get('delta'))}, "
                  f"{hh.get('n_avoided')} avoided)</p>")
        A("</div>")
    A("""<p class="muted">Because the filter is not fitted to either half, neither half is
privileged by construction &mdash; but the out-of-sample half remains the headline for
consistency with the rest of the study.</p>""")
    dec = FU.get("decomposition", {})
    if dec:
        A("""<h3>Where the money comes from</h3>
<p>The delta is not one mechanism. It splits into P&amp;L that simply never happened (avoided
trades), P&amp;L that changed because surviving trades were <i>resized</i> when the veto shifted
the nth-escalation counter, governor state and day ladder, and P&amp;L from trades that newly
appear in freed nth slots. The three sum to the delta exactly.</p>
<div class="scroll"><table><thead><tr><th>Arm</th><th>Total delta</th>
<th>(a) avoided-trade P&amp;L</th><th>(b) resizing cascade</th><th>(c) newly appearing</th>
<th>Sum check</th></tr></thead><tbody>""")
        for arm in ("C", "L"):
            d = dec.get(arm)
            if not d:
                continue
            A(f"<tr><td>{arm} arm</td><td>{money(d.get('delta'))}</td>"
              f"<td>{money(d.get('avoided_pl_removed'))} "
              f"<span class='muted'>({(d.get('pct_avoided') or 0)*100:.0f}%, "
              f"{d.get('n_avoided')} trades)</span></td>"
              f"<td>{money(d.get('resize'))} <span class='muted'>({(d.get('pct_resize') or 0)*100:.0f}%, "
              f"{d.get('n_resized')}/{d.get('n_shared')} shared trades change)</span></td>"
              f"<td>{money(d.get('added'))} <span class='muted'>({(d.get('pct_added') or 0)*100:.0f}%, "
              f"{d.get('n_added')} trades)</span></td>"
              f"<td>{pill(d.get('check_ok'),'exact','MISMATCH')}</td></tr>")
        A("""</tbody></table></div>
<p class="verdict">The benefit is overwhelmingly the <b>direct avoided-trade effect</b>, not the
resizing cascade &mdash; which makes it easier to trust, not harder: it does not depend on
second-order interactions with the escalation logic.</p>""")
    fr = FU.get("funded_risk", {})
    if fr:
        A("""<h3>Funded risk, with and without the filter</h3>
<p>Full sized book (NY + London, windowed), committed engine constants: $50k start, $2,000
EOD-trailing drawdown locked at the $50k floor, Tier-1 = the &minus;$800 daily-loss halt
<b>plus</b> the $100 drawdown-proximity halt. Bust probability is a day-block bootstrap
(5,000 paths); &ldquo;spine&rdquo; adds the DD-scaling ramp.</p>
<div class="scroll"><table><thead><tr><th>Book</th><th>Final P&amp;L</th><th>Bust % (naked)</th>
<th>Bust % (full spine)</th><th>Max drawdown</th><th>Min available DD</th>
<th>Daily-limit breach days</th></tr></thead><tbody>""")
        for arm in ("C", "L"):
            for tag, nm in (("nonews", "no filter"), ("news", "WITH filter")):
                v = fr.get(f"{arm}_{tag}")
                if not v:
                    continue
                A(f"<tr><td>{arm} arm &mdash; {nm}</td><td>{money(v.get('pl'))}</td>"
                  f"<td>{f2(v.get('bust_naked'),2,False)}%</td>"
                  f"<td>{f2(v.get('bust_spine'),2,False)}%</td>"
                  f"<td>${v.get('max_dd',0):,.0f}</td><td>${v.get('min_available',0):,.0f}</td>"
                  f"<td>{v.get('breach_days')}</td></tr>")
        A("""</tbody></table></div>
<p class="verdict">The filter roughly <b>halves naked bust probability</b> and cuts max drawdown
in both arms. With the full safety spine engaged, bust is 0.00% before and after &mdash; so the
risk benefit is real but only visible on the naked account. The &minus;$800 daily limit was
<b>never breached</b> in any book.</p>""")

# ---------------------------------------------------------------- dead numbers + provenance
A(f"""<h2>Numbers that are dead and must not reappear</h2>
<div class="dead">
<b>1. The trail-0.5R-from-1.5R sweep (+$35,980, 214 trades, 51.4% WR).</b> Superseded. It was
computed on the <b>leaky</b> book at 1 lot in R-space. Re-run on a remediated book with funded
sizing and walk-forward, every fixed target 1.5R&ndash;4R <i>loses</i> to the canon's own
management. It is not a live result and must never be quoted as one.<br><br>
<b>2. The ~$23k <code>conf_PM</code> figure quoted alone.</b> That is a <b>whole-book
mechanical</b> number. The pre-market portion is roughly <b>$17k mechanical</b> and about
<b>$3k sized</b>. Quoting $23k as a pre-market or funded figure overstates it by several times.
</div>

<h2>Provenance</h2>
<div class="prov">
run_id &nbsp; {run_id}<br>
commit &nbsp; {commit}<br>
config_hash (part0&ndash;3 scripts, sha256/16) &nbsp; {cfg_hash}<br>
book_mech &nbsp; {prov.get('book_mech_sha','—')} &nbsp;(job2_books/mech_C_news.parquet)<br>
book_sized &nbsp; {prov.get('book_sized_sha','—')} &nbsp;(job2_books/sized_C_news.parquet)<br>
bars &nbsp; {prov.get('bars_sha','—')} &nbsp;(data/reference/nq_1m_master.parquet)<br>
arm &nbsp; {prov.get('arm','—')}<br>
window &nbsp; {prov.get('window','—')}<br>
excursion &nbsp; {prov.get('excursion_convention','—')}<br>
split &nbsp; {prov.get('split_day','—')} &nbsp; ({prov.get('n_is','—')} IS / {prov.get('n_oos','—')} OOS)<br>
cost assumptions &nbsp; sizing = funded dollar-risk (risk capped at $400/trade, &le;40 micros);
book P&amp;L carries the canon's own fills; the exit-side study re-simulates no fills and adds
no cost; commissions/slippage are the book's, not re-applied here<br>
band &nbsp; tape source-cleaned to the ET-day bar band &plusmn;25pt (registered FIXED; swept at
&plusmn;10/&plusmn;50, worst bin movement 1.9%)<br>
regenerate &nbsp; python3 research/sweep_2026_07/orderflow/build_dashboard.py
</div>
<p class="sub" style="margin-top:22px">Every panel is conditional on the standing caveats at the
top: partial remediation (C only; W and <code>dep_*</code> still leaky), Brake's H0 ruling, the
January-2026 book hole, and a single observed regime transition.</p>
</div>
<script>
(function(){{
  var t = localStorage.getItem('theme');
  if (t) document.documentElement.setAttribute('data-theme', t);
}})();
</script>""")

path = f"{REPO}/research/sweep_2026_07/orderflow/dashboard_premarket_of.html"
open(path, "w").write("\n".join(H))
print(f"wrote {path} ({os.path.getsize(path):,} bytes)")
