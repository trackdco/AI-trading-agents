#!/usr/bin/env python3
"""MONTE CARLO — pass + payout, standard 50k Lucid (Angus 21 Jul).
Two independent phases, each a fresh account with a $2k trailing DD that locks at breakeven
once peak >= +$2k:
  * EVAL   : 0 -> +$3,000 target. Bust = fail.
  * FUNDED : (after pass, balance resets to 0) 0 -> +$4,000 = MAX PAYOUT. Bust = lose it.
Overall payout requires clearing BOTH. Sizing: HIGH 8 micros, MID/LOW 4 micros.
Builds a localhost artifact: funnel, both equity fans, pass-by-trade curves, drawdown.

    python -m scripts.montecarlo_payout
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
DD = 2000.0
EVAL_T, FUND_T, PAYOUT = 3000.0, 4000.0, 4000.0
MICROS = {"HIGH": 8, "MID": 4, "LOW": 4}
SIMS, FAN, HORIZON = 40000, 6000, 70
SEED = 21


def sim_to(seq, target):
    eq = peak = 0.0
    for i, p in enumerate(seq, 1):
        eq += p; peak = max(peak, eq); floor = min(peak - DD, 0.0)
        if eq >= target:
            return "hit", i
        if eq <= floor:
            return "bust", i
    return "inc", len(seq)


def load():
    W = pd.read_csv("output/conviction_trades.csv")
    W["micros"] = W.tier.map(MICROS)
    W["mpnl"] = W.dollars * W.micros / 10.0
    W["fillkey"] = W.date + " " + W.fill_t
    return W.sort_values("fillkey").reset_index(drop=True)


def _sc(lo, hi, a, b):
    return lambda v: a + (v - lo) / (hi - lo) * (b - a)


def fan_svg(P, target, ymax):
    W_, H_ = 470, 300
    L, R, T, B = 52, 14, 14, 30
    ymin = -2500
    x = _sc(0, HORIZON, L, W_ - R); y = _sc(ymin, ymax, H_ - B, T)
    def poly(hi, lo):
        return " ".join([f"{x(t):.1f},{y(hi[t]):.1f}" for t in range(HORIZON + 1)] +
                        [f"{x(t):.1f},{y(lo[t]):.1f}" for t in range(HORIZON, -1, -1)])
    def line(a):
        return " ".join(f"{x(t):.1f},{y(a[t]):.1f}" for t in range(HORIZON + 1))
    grid = "".join(f'<line class="grid" x1="{L}" y1="{y(v):.1f}" x2="{W_-R}" y2="{y(v):.1f}"/>'
                   f'<text class="ax" x="{L-6}" y="{y(v)+4:.1f}" text-anchor="end">${v/1000:.0f}k</text>'
                   for v in range(-2000, int(ymax) + 1, 1000))
    xt = "".join(f'<text class="ax" x="{x(t):.1f}" y="{H_-B+16:.1f}" text-anchor="middle">{t}</text>'
                 for t in range(0, HORIZON + 1, 20))
    return f'''<svg viewBox="0 0 {W_} {H_}" class="chart" role="img">
      {grid}
      <line class="floor" x1="{L}" y1="{y(-2000):.1f}" x2="{W_-R}" y2="{y(-2000):.1f}"/>
      <line class="target" x1="{L}" y1="{y(target):.1f}" x2="{W_-R}" y2="{y(target):.1f}"/>
      <text class="tlab" x="{W_-R}" y="{y(target)-5:.1f}" text-anchor="end">${target/1000:.0f}k</text>
      <polygon class="b90" points="{poly(P[95],P[5])}"/>
      <polygon class="b50" points="{poly(P[75],P[25])}"/>
      <polyline class="med" points="{line(P[50])}"/>{xt}
      <text class="ax" x="{(L+W_-R)/2:.0f}" y="{H_-1}" text-anchor="middle">trade #</text></svg>'''


def fan_data(pool, rng, target):
    idx = rng.integers(0, len(pool), size=(FAN, HORIZON))
    eq = np.concatenate([np.zeros((FAN, 1)), np.cumsum(pool[idx], axis=1)], axis=1)
    P = {q: np.percentile(eq, q, axis=0) for q in (5, 25, 50, 75, 95)}
    passed = (eq >= target)
    first = np.where(passed.any(1), passed.argmax(1), HORIZON + 1)
    passN = [float((first <= t).mean() * 100) for t in range(HORIZON + 1)]
    run_peak = np.maximum.accumulate(eq, 1)
    dd95 = np.percentile((run_peak - eq).max(1), 95)
    return P, passN, dd95


def main():
    W = load()
    rng = np.random.default_rng(SEED)
    pool = W.mpnl.to_numpy()
    days = [g.sort_values("fillkey").mpnl.to_numpy() for _, g in W.groupby("date")]
    exp = pool.mean()

    def phase(target, cap):
        r = {"hit": 0, "bust": 0, "inc": 0}; steps = []
        for _ in range(SIMS):
            o, n = sim_to(pool[rng.integers(0, len(pool), cap)], target)
            r[o] += 1
            if o == "hit": steps.append(n)
        return r["hit"] / SIMS, r["bust"] / SIMS, (int(np.median(steps)) if steps else 0)
    p_eval, b_eval, med_eval = phase(EVAL_T, 200)
    p_fund, b_fund, med_fund = phase(FUND_T, 200)
    p_both = p_eval * p_fund
    exp_payout = PAYOUT * p_both

    Pe, passNe, dd_e = fan_data(pool, rng, EVAL_T)
    Pf, passNf, dd_f = fan_data(pool, rng, FUND_T)

    html = render(exp, W, p_eval, b_eval, med_eval, p_fund, b_fund, med_fund, p_both, exp_payout,
                  fan_svg(Pe, EVAL_T, 4200), fan_svg(Pf, FUND_T, 5200), dd_e, dd_f,
                  passNe, passNf, med_eval + med_fund)
    Path("docs/payout-dashboard.html").write_text(html)
    print(f"sizing 8/4/4 | expectancy ${exp:+.0f}/trade")
    print(f"EVAL  -> +$3k: pass {p_eval*100:.1f}%  bust {b_eval*100:.1f}%  med {med_eval} trades  (95% DD ${dd_e:,.0f})")
    print(f"FUND  -> +$4k: pass {p_fund*100:.1f}%  bust {b_fund*100:.1f}%  med {med_fund} trades  (95% DD ${dd_f:,.0f})")
    print(f"BOTH (eval then payout): {p_both*100:.1f}%   expected payout ${exp_payout:,.0f}")
    print("-> docs/payout-dashboard.html")


def render(exp, W, p_eval, b_eval, med_eval, p_fund, b_fund, med_fund, p_both, exp_payout,
           fan_e, fan_f, dd_e, dd_f, passNe, passNf, med_total):
    tiers = {t: dict(n=int((W.tier == t).sum()), mic=MICROS[t]) for t in ("HIGH", "MID", "LOW")}
    def w(v): return f"{v*100:.1f}%"
    fbust = lambda b: "grn" if b < .02 else ("amb" if b < .06 else "red")
    return f"""<title>Monte Carlo — Lucid 50k Pass + Payout</title>
<style>
:root{{--bg:#0f1115;--panel:#171a21;--p2:#1e222b;--ink:#e8ecf3;--mut:#93a0b4;--line:#2a2f3a;
--grn:#39d98a;--red:#ff6b6b;--amb:#ffb454;--acc:#5b9dff;--band:#5b9dff;}}
@media(prefers-color-scheme:light){{:root{{--bg:#f5f7fa;--panel:#fff;--p2:#eef1f5;--ink:#141922;
--mut:#5a6675;--line:#e0e5ec;--grn:#0f9d58;--red:#d64545;--amb:#b8730c;--acc:#2f6fed;--band:#2f6fed;}}}}
:root[data-theme=dark]{{--bg:#0f1115;--panel:#171a21;--p2:#1e222b;--ink:#e8ecf3;--mut:#93a0b4;--line:#2a2f3a;--grn:#39d98a;--red:#ff6b6b;--amb:#ffb454;--acc:#5b9dff;--band:#5b9dff;}}
:root[data-theme=light]{{--bg:#f5f7fa;--panel:#fff;--p2:#eef1f5;--ink:#141922;--mut:#5a6675;--line:#e0e5ec;--grn:#0f9d58;--red:#d64545;--amb:#b8730c;--acc:#2f6fed;--band:#2f6fed;}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14.5px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
.wrap{{max-width:1000px;margin:0 auto;padding:30px 20px 80px}}
h1{{font-size:25px;margin:0 0 3px;letter-spacing:-.02em}}h2{{font-size:17px;margin:28px 0 10px}}
.sub{{color:var(--mut);margin:0 0 20px}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}}
.row{{display:flex;gap:12px;flex-wrap:wrap}}.card{{flex:1 1 150px;background:var(--p2);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
.card .k{{color:var(--mut);font-size:11.5px;text-transform:uppercase;letter-spacing:.04em}}.card .v{{font-size:22px;font-weight:650;margin-top:2px}}
.grn{{color:var(--grn)}}.red{{color:var(--red)}}.amb{{color:var(--amb)}}.acc{{color:var(--acc)}}.mut{{color:var(--mut)}}
.chart{{width:100%;height:auto;display:block}}.grid{{stroke:var(--line);stroke-width:1}}.ax{{fill:var(--mut);font-size:10.5px}}
.b90{{fill:var(--band);opacity:.14}}.b50{{fill:var(--band);opacity:.27}}.med{{fill:none;stroke:var(--band);stroke-width:2.3}}
.target{{stroke:var(--grn);stroke-width:1.4;stroke-dasharray:6 4}}.tlab{{fill:var(--grn);font-size:11px;font-weight:600}}
.floor{{stroke:var(--red);stroke-width:1.4;stroke-dasharray:6 4}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}@media(max-width:720px){{.two{{grid-template-columns:1fr}}}}
.funnel{{display:flex;align-items:stretch;gap:0;margin:6px 0}}
.step{{flex:1;text-align:center;padding:14px 8px;border:1px solid var(--line);background:var(--p2);position:relative}}
.step:first-child{{border-radius:10px 0 0 10px}}.step:last-child{{border-radius:0 10px 10px 0}}
.step .p{{font-size:22px;font-weight:700}}.step .l{{font-size:12px;color:var(--mut);margin-top:2px}}
.step .n{{font-size:11px;color:var(--mut)}}
.note{{color:var(--mut);font-size:12.5px;margin-top:8px}}code{{background:var(--p2);border:1px solid var(--line);border-radius:5px;padding:1px 6px;font-size:12.5px}}
.foot{{color:var(--mut);font-size:12px;margin-top:24px;border-top:1px solid var(--line);padding-top:12px}}
ul{{margin:4px 0;padding-left:18px}}li{{margin:4px 0}}
</style>
<div class="wrap">
<h1>Monte Carlo — Lucid 50k: Pass + Payout</h1>
<p class="sub">Eval +$3k → reset → Funded +$4k max payout · $2k trailing DD (locks at breakeven) · sizing 8/4/4 micros · 40k sims/phase</p>

<div class="panel"><div class="row">
  <div class="card"><div class="k">Pass eval</div><div class="v grn">{w(p_eval)}</div><div class="mut" style="font-size:12px">→ +$3k, med {med_eval} trades</div></div>
  <div class="card"><div class="k">Reach max payout</div><div class="v {('grn' if p_both>.7 else 'amb')}">{w(p_both)}</div><div class="mut" style="font-size:12px">clear BOTH phases</div></div>
  <div class="card"><div class="k">Expected payout</div><div class="v acc">${exp_payout:,.0f}</div><div class="mut" style="font-size:12px">per eval attempt</div></div>
  <div class="card"><div class="k">Median to payout</div><div class="v">{med_total} <span style="font-size:13px" class="mut">trades</span></div><div class="mut" style="font-size:12px">both phases</div></div>
</div></div>

<h2>The funnel</h2>
<div class="panel">
<div class="funnel">
  <div class="step"><div class="p">100%</div><div class="l">Start eval</div><div class="n">$50k account</div></div>
  <div class="step"><div class="p grn">{w(p_eval)}</div><div class="l">Pass eval (+$3k)</div><div class="n">bust {w(b_eval)}</div></div>
  <div class="step"><div class="p {('grn' if p_both>.7 else 'amb')}">{w(p_both)}</div><div class="l">Max payout (+$4k)</div><div class="n">funded bust {w(b_fund)}</div></div>
</div>
<p class="note">Payout requires clearing both independent phases, so the overall number is eval × funded = {w(p_eval)} × {w(p_fund)} = <b>{w(p_both)}</b>.
Expected payout per attempt = $4,000 × {w(p_both)} = <b>${exp_payout:,.0f}</b> (full-or-nothing; real accounts allow interim withdrawals, so this is a floor).</p>
</div>

<h2>Equity fans — {FAN:,} paths each</h2>
<div class="two">
  <div class="panel"><h2 style="margin-top:2px;font-size:14px">Eval → +$3k · pass {w(p_eval)} · bust <span class="{fbust(b_eval)}">{w(b_eval)}</span></h2>
  {fan_e}<p class="note">95th-pct drawdown ${dd_e:,.0f} vs $2k buffer.</p></div>
  <div class="panel"><h2 style="margin-top:2px;font-size:14px">Funded → +$4k · pass {w(p_fund)} · bust <span class="{fbust(b_fund)}">{w(b_fund)}</span></h2>
  {fan_f}<p class="note">95th-pct drawdown ${dd_f:,.0f}. Higher target → longer exposure → a touch more bust risk.</p></div>
</div>

<h2>Read this honestly</h2>
<div class="panel"><ul>
<li><b>Resamples our own 82 winning 2026 trades.</b> The pass/payout %s prove the sizing clears the DD math under normal variance — <b>not</b> that the edge repeats on live fills. That's the real risk and no MC can price it.</li>
<li><b>Two phases multiply.</b> Even at ~{w(p_eval)} each, needing both drops the combined to {w(p_both)}. Sequential gates compound against you.</li>
<li><b>Expected ${exp_payout:,.0f}/attempt is a floor</b> — it counts only reaching the full $4k. In practice you withdraw along the way, so realized EV is higher; but it also ignores the eval fee and any consistency rule.</li>
<li><b>Sizing 8/4/4</b> (HIGH {tiers['HIGH']['n']} / MID {tiers['MID']['n']} / LOW {tiers['LOW']['n']} trades) sits between the safe 6/3/3 and the thin 10/5/5 — 95%-DD ~${dd_f:,.0f} still inside the $2k buffer.</li>
</ul></div>
<p class="foot">Reproduce: <code>python -m scripts.montecarlo_payout</code> · resamples <code>output/conviction_trades.csv</code>.</p>
</div>"""


if __name__ == "__main__":
    main()
