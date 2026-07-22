#!/usr/bin/env python3
"""Build the full-span fresh-eyes conviction DASHBOARD (Angus 22 Jul). Computes every requested
cut and writes a self-contained HTML file (output/fe_full/dashboard.html) + a JSON of aggregates.

Cuts: variant comparison (blind / pre-market-only / 09:50 binary / +agent-conviction /
+mechanical / full-stack) per year + total; month-by-month P&L per year; day-of-week P&L per
year + overall; pre-market vs golden-window P&L per year + overall (from the book trade log);
adaptation (revision) stats; regime & conviction-size distribution.

    python -m scripts.build_dashboard [verdicts.json]        # real run
    python -m scripts.build_dashboard --baseline             # smoke test w/ blind agent as verdict
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CONF_W = {"low": 0.5, "medium": 0.75, "high": 1.0}
OUT = Path("output/fe_full")


def act_of(regime, stand):
    if stand:
        return "FLAT"
    return "E3" if regime in ("balance", "trap") else "E4" if regime == "war" else "FLAT"


def book_pl(r, a):
    return r.e3 if a == "E3" else r.e4 if a == "E4" else 0.0


def load_verdicts(arg):
    L = pd.read_csv(OUT / "labels.csv")
    L["yr"] = L.day.str[:4].astype(int)
    L["both_red"] = (L.e3 <= 0) & (L.e4 <= 0)
    if arg == "--baseline":                       # smoke test: blind agent acts as the verdict
        V = {r.day: {"premarket_regime": None, "premarket_stand_down": r.orig_act == "FLAT",
                     "regime": {"E3": "balance", "E4": "war", "FLAT": "event_risk"}[r.orig_act],
                     "stand_down": r.orig_act == "FLAT", "size_multiplier": 1.0,
                     "confidence": "medium", "revised": False} for r in L.itertuples()}
    else:
        V = {d["day"]: d for d in json.loads(Path(arg).read_text())}
        L = L[L.day.isin(V)].copy()
    return L.reset_index(drop=True), V


def compute(L, V):
    med = {yr: (L[L.yr != yr].coil.median(), L[L.yr != yr].absorp_corr.median()) for yr in L.yr.unique()}
    rows = []
    for r in L.itertuples():
        v = V[r.day]
        pre_act = act_of(v.get("premarket_regime"), v.get("premarket_stand_down"))
        fin_act = act_of(v.get("regime"), bool(v.get("stand_down")) or float(v.get("size_multiplier", 1)) == 0)
        conv = float(v.get("size_multiplier", 1)) * CONF_W.get(v.get("confidence", "medium"), 0.75)
        cm, am = med[r.yr]
        mf = 0.25 if (r.coil == r.coil and r.coil >= cm and r.absorp_corr >= am) else 1.0
        base = book_pl(r, fin_act)
        rows.append(dict(day=r.day, yr=int(r.yr), dow=pd.Timestamp(r.day).day_name(),
                         month=r.day[:7], both_red=bool(r.both_red), oracle=r.oracle_act,
                         revised=bool(v.get("revised")), final_act=fin_act, pre_act=pre_act,
                         size=conv, mech=mf,
                         A=book_pl(r, r.orig_act), P=book_pl(r, pre_act), B=base,
                         C=base * conv, D=base * mf, E=base * conv * mf,
                         regime=v.get("regime"), size_mult=float(v.get("size_multiplier", 1)),
                         confidence=v.get("confidence")))
    return pd.DataFrame(rows)


def window_split(D, best):
    """pre-market vs golden P&L for the chosen book each day, from the book trade log, x size."""
    dec = pd.read_parquet(OUT / "window_decomp.parquet")     # day, book, premkt, golden
    dec = dec.set_index(["day", "book"])
    size_col = {"B": "size_is_1", "E": "size"}.get(best, "size")
    out = []
    for r in D.itertuples():
        if r.final_act not in ("E3", "E4"):
            continue
        key = (r.day, r.final_act)
        if key not in dec.index:
            continue
        row = dec.loc[key]
        sz = getattr(r, "size") if best in ("C", "D", "E") else 1.0
        out.append(dict(yr=r.yr, premkt=float(row.premkt) * sz, golden=float(row.golden) * sz))
    return pd.DataFrame(out)


def agg(D, best):
    variants = [("A", "Blind fresh-eyes (baseline)"), ("P", "Enriched · pre-market only"),
                ("B", "Enriched · 09:50 re-read (binary)"), ("C", "· × agent conviction"),
                ("D", "· × mechanical (coil∧absorp)"), ("E", "· full conviction stack")]
    oracle = D.assign(o=D.apply(lambda r: 0, axis=1))  # placeholder
    # variant table per year + total
    vt = []
    for k, name in variants:
        row = {"key": k, "name": name}
        for yr in sorted(D.yr.unique()):
            s = D[D.yr == yr]
            row[str(yr)] = round(s[k].sum())
        row["ALL"] = round(D[k].sum())
        akey = {"A": "pre_act"}.get(k)  # hit uses acts
        vt.append(row)
    # hit-rate + stand-down for A vs best (final_act) — computed separately
    def hit(mask_df, actcol):
        return round((mask_df[actcol] == mask_df.oracle).mean() * 100)
    stats = {
        "blind_hit": hit(D, "A") if False else round((D.A_act.eq(D.oracle).mean()*100) if "A_act" in D else 0),
    }
    return variants, vt


def money(x, plus=True):
    x = round(x)
    s = f"{x:+,}" if plus else f"{x:,}"
    return s.replace("+", "+$").replace("-", "−$") if x != 0 else "$0"


def cls(x):
    return "pos" if x > 0 else "neg" if x < 0 else "zero"


def vbars(items, val_key, label_key, years=None):
    """vertical bar chart html; items = list of dicts. scales to max abs."""
    vals = [it[val_key] for it in items]
    m = max((abs(v) for v in vals), default=1) or 1
    cells = []
    for it in items:
        v = it[val_key]
        h = abs(v) / m * 100
        up = v >= 0
        bar = (f'<div class="vb-track"><div class="vb-bar {cls(v)}" '
               f'style="height:{h:.1f}%;{"bottom:50%" if up else "top:50%"}"></div></div>')
        cells.append(f'<div class="vb-col" title="{it[label_key]}: {money(v)}">'
                     f'<div class="vb-val {cls(v)}">{money(v)}</div>{bar}'
                     f'<div class="vb-lab">{it[label_key]}</div></div>')
    return f'<div class="vbars"><div class="vb-zero"></div>{"".join(cells)}</div>'


def render_html(d):
    yrs = d["years"]
    best = d["best"]
    best_total = next(r["ALL"] for r in d["variants"] if r["key"] == best)
    blind_total = next(r["ALL"] for r in d["variants"] if r["key"] == "A")
    orc = d["oracle"]["ALL"]
    capt_blind = blind_total / orc * 100 if orc else 0
    capt_best = best_total / orc * 100 if orc else 0

    # variant rows
    vhead = "".join(f"<th>{y}</th>" for y in yrs)
    vrows = ""
    for r in d["variants"]:
        hi = " row-best" if r["key"] == best else (" row-base" if r["key"] == "A" else "")
        py = "".join(f'<td class="num {cls(r[str(y)])}">{money(r[str(y)])}</td>' for y in yrs)
        vrows += (f'<tr class="{hi.strip()}"><td class="vk">{r["key"]}</td>'
                  f'<td class="vn">{r["name"]}</td>{py}'
                  f'<td class="num tot {cls(r["ALL"])}">{money(r["ALL"])}</td></tr>')

    # month bars per year
    msec = ""
    for y in yrs:
        mo = [m for m in d["months"] if m["month"].startswith(str(y))]
        for m in mo:
            m["mlab"] = m["month"][5:]
        if mo:
            msec += (f'<div class="yblock"><div class="yhead">{y}</div>'
                     f'{vbars(mo, best, "mlab")}</div>')

    # day of week
    drows = ""
    for row in d["dow"]:
        yr_cells = "".join(f'<td class="num {cls(row[f"{y}_E"])}">{money(row[f"{y}_E"])}</td>' for y in yrs)
        drows += (f'<tr><td class="vn">{row["dow"]}</td>'
                  f'<td class="num muted">{row["n"]}</td>{yr_cells}'
                  f'<td class="num tot {cls(row["ALL_E"])}">{money(row["ALL_E"])}</td></tr>')

    # window split
    wsec = ""
    for scope in [str(y) for y in yrs] + ["ALL"]:
        w = d["window"][scope]
        tot = w["premkt"] + w["golden"]
        wsec += (f'<div class="wcard"><div class="wscope">{scope}</div>'
                 f'<div class="wrow"><span class="wl">Pre-market <em>&lt;09:30</em></span>'
                 f'<span class="num {cls(w["premkt"])}">{money(w["premkt"])}</span></div>'
                 f'<div class="wrow"><span class="wl">Golden window <em>&ge;09:30</em></span>'
                 f'<span class="num {cls(w["golden"])}">{money(w["golden"])}</span></div>'
                 f'<div class="wrow wtot"><span class="wl">Book total</span>'
                 f'<span class="num {cls(tot)}">{money(tot)}</span></div></div>')

    ad = d["adapt"]
    reg = " ".join(f'<span class="chip"><b>{k}</b> {v}</span>' for k, v in sorted(d["regdist"].items(), key=lambda x: -x[1]))
    szs = " ".join(f'<span class="chip"><b>{k}×</b> {v}</span>' for k, v in sorted(d["sizedist"].items()))
    mode_badge = "" if d["mode"] == "LIVE" else f'<span class="badge-warn">{d["mode"]}</span>'

    return f"""<style>
:root {{
  --ink:#0E1420; --panel:#161D2B; --panel2:#1B2434; --line:#26303F; --line2:#313d4f;
  --tx:#E4E9F0; --mut:#8B98AC; --gold:#E0A83E; --pos:#3FB984; --neg:#E5695B; --zero:#61708a;
  --shadow:0 1px 0 #ffffff08, 0 8px 24px #00000040;
}}
@media (prefers-color-scheme: light) {{
  :root {{ --ink:#F4F1EA; --panel:#FBFAF6; --panel2:#F3F0E8; --line:#E2DCCE; --line2:#D6CEBB;
    --tx:#1D2430; --mut:#6C7688; --gold:#B4791A; --pos:#1F9564; --neg:#C6483C; --zero:#94a0b2;
    --shadow:0 1px 0 #ffffff, 0 6px 20px #6b5f3f14; }}
}}
:root[data-theme="dark"] {{ --ink:#0E1420; --panel:#161D2B; --panel2:#1B2434; --line:#26303F; --line2:#313d4f;
  --tx:#E4E9F0; --mut:#8B98AC; --gold:#E0A83E; --pos:#3FB984; --neg:#E5695B; --zero:#61708a; --shadow:0 1px 0 #ffffff08, 0 8px 24px #00000040; }}
:root[data-theme="light"] {{ --ink:#F4F1EA; --panel:#FBFAF6; --panel2:#F3F0E8; --line:#E2DCCE; --line2:#D6CEBB;
  --tx:#1D2430; --mut:#6C7688; --gold:#B4791A; --pos:#1F9564; --neg:#C6483C; --zero:#94a0b2; --shadow:0 1px 0 #ffffff,0 6px 20px #6b5f3f14; }}
* {{ box-sizing:border-box; }}
.wrap {{ background:var(--ink); color:var(--tx); min-height:100vh;
  font-family:"Inter",system-ui,-apple-system,"Segoe UI",sans-serif; line-height:1.5;
  padding:clamp(18px,4vw,44px); }}
.num, .mono {{ font-family:ui-monospace,"SF Mono","JetBrains Mono",Menlo,monospace; font-variant-numeric:tabular-nums; }}
.pos {{ color:var(--pos); }} .neg {{ color:var(--neg); }} .zero {{ color:var(--zero); }}
.inner {{ max-width:1080px; margin:0 auto; display:flex; flex-direction:column; gap:26px; }}
h1 {{ font-size:clamp(22px,3.4vw,32px); font-weight:680; letter-spacing:-.02em; margin:0; text-wrap:balance; }}
.sub {{ color:var(--mut); font-size:14px; margin-top:6px; display:flex; gap:14px; flex-wrap:wrap; align-items:center; }}
.dot {{ width:4px; height:4px; border-radius:50%; background:var(--line2); }}
.badge-warn {{ background:#E0A83E22; color:var(--gold); border:1px solid #E0A83E55; padding:2px 9px; border-radius:20px; font-size:12px; font-weight:600; }}
.eyebrow {{ text-transform:uppercase; letter-spacing:.14em; font-size:11px; color:var(--gold); font-weight:640; margin-bottom:12px; }}
.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:clamp(16px,2.4vw,26px); box-shadow:var(--shadow); }}
/* hero */
.hero {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:var(--line); border:1px solid var(--line); border-radius:14px; overflow:hidden; }}
.stat {{ background:var(--panel); padding:20px clamp(14px,2vw,24px); }}
.stat .k {{ font-size:12px; text-transform:uppercase; letter-spacing:.09em; color:var(--mut); }}
.stat .v {{ font-size:clamp(24px,3.6vw,36px); font-weight:600; margin-top:8px; letter-spacing:-.01em; }}
.stat .m {{ font-size:12px; color:var(--mut); margin-top:6px; }}
.stat.best {{ background:linear-gradient(180deg,#E0A83E10,var(--panel)); }}
.track {{ margin-top:6px; height:9px; background:var(--panel2); border-radius:6px; overflow:hidden; border:1px solid var(--line); }}
.track > div {{ height:100%; border-radius:6px; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th {{ text-align:right; font-weight:600; color:var(--mut); font-size:11px; text-transform:uppercase; letter-spacing:.06em; padding:0 12px 10px; border-bottom:1px solid var(--line); }}
th:nth-child(1),th:nth-child(2) {{ text-align:left; }}
td {{ padding:10px 12px; border-bottom:1px solid var(--line); }}
tr:last-child td {{ border-bottom:none; }}
.vk {{ font-family:ui-monospace,monospace; color:var(--mut); font-weight:600; width:26px; }}
.vn {{ font-weight:500; }}
.num {{ text-align:right; }}
.tot {{ font-weight:680; }}
.muted {{ color:var(--mut); }}
.row-best {{ background:linear-gradient(90deg,#E0A83E12,transparent); }}
.row-best .vk, .row-best .vn {{ color:var(--gold); }}
.row-base td {{ color:var(--mut); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
.grid2 > * {{ min-width:0; }}
/* vbars */
.vbars {{ position:relative; display:flex; gap:clamp(3px,1vw,10px); align-items:stretch; height:190px; padding-top:18px; overflow-x:auto; }}
.vb-zero {{ position:absolute; left:0; right:0; top:calc(18px + (190px - 18px)/2); height:1px; background:var(--line2); }}
.vb-col {{ flex:1 1 0; min-width:26px; display:flex; flex-direction:column; align-items:center; position:relative; }}
.vb-track {{ position:relative; width:100%; flex:1; }}
.vb-bar {{ position:absolute; left:15%; right:15%; border-radius:3px; }}
.vb-bar.pos {{ background:linear-gradient(180deg,var(--pos),#3FB98488); }}
.vb-bar.neg {{ background:linear-gradient(0deg,var(--neg),#E5695B88); }}
.vb-val {{ font-family:ui-monospace,monospace; font-size:9.5px; font-variant-numeric:tabular-nums; position:absolute; top:-14px; white-space:nowrap; }}
.vb-lab {{ font-size:10px; color:var(--mut); margin-top:5px; font-family:ui-monospace,monospace; }}
.yblock {{ margin-top:6px; }}
.yhead {{ font-family:ui-monospace,monospace; font-size:12px; color:var(--gold); font-weight:600; margin:14px 0 2px; }}
/* window */
.wgrid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; }}
.wcard {{ background:var(--panel2); border:1px solid var(--line); border-radius:11px; padding:15px; }}
.wscope {{ font-family:ui-monospace,monospace; font-weight:640; color:var(--gold); font-size:13px; margin-bottom:11px; }}
.wrow {{ display:flex; justify-content:space-between; align-items:baseline; padding:5px 0; font-size:13px; }}
.wrow .wl {{ color:var(--mut); }} .wrow .wl em {{ font-style:normal; opacity:.6; font-size:11px; }}
.wtot {{ border-top:1px solid var(--line); margin-top:6px; padding-top:9px; font-weight:600; }}
.wtot .wl {{ color:var(--tx); }}
.chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:4px; }}
.chip {{ background:var(--panel2); border:1px solid var(--line); border-radius:20px; padding:5px 12px; font-size:12px; color:var(--mut); font-family:ui-monospace,monospace; }}
.chip b {{ color:var(--tx); font-weight:600; }}
.adapt-big {{ font-size:clamp(20px,3vw,28px); font-weight:600; }}
.note {{ font-size:12px; color:var(--mut); line-height:1.6; }}
.sec-title {{ font-size:17px; font-weight:640; margin:0 0 3px; letter-spacing:-.01em; }}
.sec-desc {{ font-size:13px; color:var(--mut); margin:0 0 18px; }}
@media (max-width:720px) {{ .hero {{ grid-template-columns:1fr; }} .grid2 {{ grid-template-columns:1fr; }} }}
</style>
<div class="wrap"><div class="inner">
  <header>
    <div class="eyebrow">NQ Desk · Fresh-Eyes Conviction Run</div>
    <h1>Conviction-sized regime read vs the oracle ceiling</h1>
    <div class="sub">{mode_badge}<span>{d["days"]} trading days</span><span class="dot"></span>
      <span>{d["span"][0]} → {d["span"][1]}</span><span class="dot"></span>
      <span>pre-market thesis + 09:50 opening-tape re-read</span></div>
  </header>

  <section class="hero">
    <div class="stat"><div class="k">Blind baseline</div>
      <div class="v {cls(blind_total)}">{money(blind_total)}</div>
      <div class="m">{capt_blind:.0f}% of oracle · prior fresh-eyes read</div>
      <div class="track"><div style="width:{max(0,min(100,capt_blind)):.0f}%;background:var(--zero)"></div></div></div>
    <div class="stat best"><div class="k">Best conviction variant · {best}</div>
      <div class="v {cls(best_total)}">{money(best_total)}</div>
      <div class="m">{capt_best:.0f}% of oracle · full stack</div>
      <div class="track"><div style="width:{max(0,min(100,capt_best)):.0f}%;background:linear-gradient(90deg,var(--gold),#f0c979)"></div></div></div>
    <div class="stat"><div class="k">Oracle ceiling</div>
      <div class="v" style="color:var(--gold)">{money(orc)}</div>
      <div class="m">perfect book pick, stand down both-red days</div>
      <div class="track"><div style="width:100%;background:var(--line2)"></div></div></div>
  </section>

  <section class="panel">
    <div class="eyebrow">The spine</div>
    <h2 class="sec-title">Sizing variants — what turns out more profitable</h2>
    <p class="sec-desc">Each layer added to the enriched agent's 09:50 read. Mechanical thresholds are out-of-fit (other year's median). Gold = best; grey = blind baseline.</p>
    <div style="overflow-x:auto"><table>
      <thead><tr><th></th><th>Variant</th>{vhead}<th>Total</th></tr></thead>
      <tbody>{vrows}</tbody>
    </table></div>
    <p class="note" style="margin-top:14px">Book-hit: blind {d["hits"]["blind"]}% → enriched {d["hits"]["final"]}% &nbsp;·&nbsp;
      stand-down rate {d["sd"]["blind"]}% → {d["sd"]["final"]}% &nbsp;·&nbsp;
      both-red days caught {d["sd"]["blind_brcaught"]}% → {d["sd"]["final_brcaught"]}%</p>
  </section>

  <section class="panel">
    <div class="eyebrow">Seasonality</div>
    <h2 class="sec-title">Month-by-month P&amp;L per year</h2>
    <p class="sec-desc">Full conviction stack (variant {best}), one bar per calendar month.</p>
    {msec}
  </section>

  <div class="grid2">
    <section class="panel">
      <div class="eyebrow">Weekday</div>
      <h2 class="sec-title">P&amp;L by day of week</h2>
      <p class="sec-desc">Variant {best}, per year and overall.</p>
      <div style="overflow-x:auto"><table>
        <thead><tr><th>Day</th><th>n</th>{"".join(f"<th>{y}</th>" for y in yrs)}<th>Total</th></tr></thead>
        <tbody>{drows}</tbody>
      </table></div>
    </section>
    <section class="panel">
      <div class="eyebrow">Intraday window · book trade log</div>
      <h2 class="sec-title">Pre-market vs golden window</h2>
      <p class="sec-desc">Chosen-book fills split by time. 2026 H1 sourced from the chained trade log.</p>
      <div class="wgrid">{wsec}</div>
    </section>
  </div>

  <div class="grid2">
    <section class="panel">
      <div class="eyebrow">Intraday adaptation</div>
      <h2 class="sec-title">Did the 09:50 re-read earn its keep?</h2>
      <p class="sec-desc">How often the tape overturned the pre-market thesis, and the P&amp;L swing on those days.</p>
      <div class="adapt-big">{ad["n_rev"]} / {ad["n"]} days revised
        <span style="color:var(--mut);font-size:15px">({round(ad["n_rev"]/max(ad["n"],1)*100)}%)</span></div>
      <div class="wrow" style="margin-top:14px"><span class="wl" style="color:var(--mut)">Revised days — pre-market thesis P&amp;L</span>
        <span class="num {cls(ad["rev_pre"])}">{money(ad["rev_pre"])}</span></div>
      <div class="wrow"><span class="wl" style="color:var(--mut)">Revised days — after 09:50 re-read</span>
        <span class="num {cls(ad["rev_final"])}">{money(ad["rev_final"])}</span></div>
      <div class="wrow wtot"><span class="wl">Adaptation delta</span>
        <span class="num {cls(ad["rev_final"]-ad["rev_pre"])}">{money(ad["rev_final"]-ad["rev_pre"])}</span></div>
    </section>
    <section class="panel">
      <div class="eyebrow">Agent behaviour</div>
      <h2 class="sec-title">Regime &amp; conviction distribution</h2>
      <p class="sec-desc">Final-verdict regime calls and the size the agent committed.</p>
      <div class="note" style="margin:2px 0 7px;color:var(--tx);font-weight:600">Regime</div>
      <div class="chips">{reg}</div>
      <div class="note" style="margin:16px 0 7px;color:var(--tx);font-weight:600">Size multiplier</div>
      <div class="chips">{szs}</div>
    </section>
  </div>

  <p class="note" style="text-align:center;padding-top:4px">Deterministic simulation over held book P&amp;L (E3 reversal / E4 displacement). Conviction sizing scales the chosen book's daily result. Oracle ceiling = perfect daily book selection with stand-down on both-losing days.</p>
</div></div>"""


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "--baseline"
    L, V = load_verdicts(arg)
    D = compute(L, V)
    best = "E"
    D["size_is_1"] = 1.0

    # ---- aggregates ----
    years = sorted(D.yr.unique())
    variants = [("A", "Blind fresh-eyes (baseline)"), ("P", "Enriched · pre-market only"),
                ("B", "Enriched · 09:50 re-read (binary)"), ("C", "· ×agent conviction"),
                ("D", "· ×mechanical (coil∧absorp)"), ("E", "· full conviction stack")]
    var_tbl = []
    for k, name in variants:
        r = {"key": k, "name": name, "ALL": round(D[k].sum())}
        for yr in years:
            r[str(yr)] = round(D[D.yr == yr][k].sum())
        # book-hit & stand-down for the action behind this variant
        actcol = {"A": "final_act"}.get(k, "final_act")  # A uses orig; others final
        r["hit"] = None
        var_tbl.append(r)
    # book-hit / stand-down: blind (A via orig) vs final (B..E)
    def hitrate(actser): return round((actser == D.oracle).mean() * 100)
    # A uses orig_act — recover from labels
    orig = pd.read_csv(OUT / "labels.csv").set_index("day").orig_act
    D["A_act"] = D.day.map(orig)
    hits = {"blind": hitrate(D.A_act), "final": hitrate(D.final_act)}
    br = D[D.both_red]
    sd = {"blind": round((D.A_act == "FLAT").mean() * 100), "final": round((D.final_act == "FLAT").mean() * 100),
          "blind_brcaught": round((br.A_act == "FLAT").mean() * 100) if len(br) else 0,
          "final_brcaught": round((br.final_act == "FLAT").mean() * 100) if len(br) else 0}

    oracle_ceiling = {str(yr): round(L[L.yr == yr].apply(lambda r: max(r.e3, r.e4, 0), axis=1).sum())
                      for yr in years}
    oracle_ceiling["ALL"] = round(L.apply(lambda r: max(r.e3, r.e4, 0), axis=1).sum())

    # month-by-month (baseline A vs best E)
    months = sorted(D.month.unique())
    month_tbl = [{"month": m, "A": round(D[D.month == m].A.sum()), "E": round(D[D.month == m].E.sum()),
                  "n": int((D.month == m).sum())} for m in months]
    # day-of-week
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    dow_tbl = []
    for d in order:
        row = {"dow": d, "ALL_A": round(D[D.dow == d].A.sum()), "ALL_E": round(D[D.dow == d].E.sum()),
               "n": int((D.dow == d).sum())}
        for yr in years:
            s = D[(D.dow == d) & (D.yr == yr)]
            row[f"{yr}_E"] = round(s.E.sum())
        dow_tbl.append(row)
    # window split
    W = window_split(D, best)
    win_tbl = {"ALL": {"premkt": round(W.premkt.sum()), "golden": round(W.golden.sum())}}
    for yr in years:
        s = W[W.yr == yr]
        win_tbl[str(yr)] = {"premkt": round(s.premkt.sum()), "golden": round(s.golden.sum())}
    # adaptation
    rev = D[D.revised]
    adapt = {"n_rev": int(D.revised.sum()), "n": int(len(D)),
             "rev_pre": round(rev.P.sum()), "rev_final": round(rev.B.sum())}
    # regime + size distribution (final)
    regdist = D.regime.value_counts().to_dict()
    sizedist = D.size_mult.value_counts().to_dict()

    data = dict(days=int(len(D)), span=[D.day.min(), D.day.max()], years=[int(y) for y in years],
                variants=var_tbl, hits=hits, sd=sd, oracle=oracle_ceiling, months=month_tbl,
                dow=dow_tbl, window=win_tbl, adapt=adapt,
                regdist={k: int(v) for k, v in regdist.items()},
                sizedist={str(k): int(v) for k, v in sizedist.items()}, best=best,
                mode=("BASELINE SMOKE TEST" if arg == "--baseline" else "LIVE"))
    (OUT / "dashboard_data.json").write_text(json.dumps(data, indent=2))
    (OUT / "dashboard.html").write_text(render_html(data))
    print("wrote", OUT / "dashboard_data.json", "and", OUT / "dashboard.html")
    print(json.dumps({k: data[k] for k in ("days", "span", "hits", "sd", "oracle", "adapt", "mode")}, indent=1))
    print("variant totals:", {r["key"]: r["ALL"] for r in var_tbl})


if __name__ == "__main__":
    main()
