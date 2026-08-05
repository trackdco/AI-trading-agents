#!/usr/bin/env python3
"""Generate the live-sim desk dashboard (Angus's monitor artifact).

Reads runs/live_desk1/journal.jsonl + state.json and writes a self-contained
HTML page. Republished to the same artifact URL every cycle; the page also
meta-refreshes itself every 5 minutes so an open tab stays current.

    python -m scripts.live_desk_dashboard <out.html>
"""
from __future__ import annotations

import html
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs/live_desk1"
TOTAL_DAYS = 254
NY_OFF = -4  # ET offset for display only


def rows() -> list[dict]:
    f = RUNS / "journal.jsonl"
    if not f.exists():
        return []
    out = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    return sorted(out, key=lambda r: r["day"])


def usd(v: float, sign: bool = True) -> str:
    s = f"{abs(v):,.0f}"
    if sign:
        return ("+$" if v >= 0 else "−$") + s
    return "$" + s


def pl_class(v: float) -> str:
    return "up" if v >= 0 else "dn"


def spark(R: list[dict]) -> str:
    """Cumulative agent / B0 / B1 lines as inline SVG."""
    if len(R) < 2:
        return '<div class="empty">chart appears after the first few days land</div>'
    W, H, PAD = 860, 190, 10
    series = {}
    for key in ("agent_dollars", "b0_dollars", "b1_dollars"):
        acc, cum = 0.0, []
        for r in R:
            acc += r[key]
            cum.append(acc)
        series[key] = cum
    allv = [v for s in series.values() for v in s] + [0.0]
    lo, hi = min(allv), max(allv)
    rng = (hi - lo) or 1.0
    n = len(R)

    def pts(cum):
        return " ".join(
            f"{PAD + i * (W - 2 * PAD) / (n - 1):.1f},"
            f"{H - PAD - (v - lo) * (H - 2 * PAD) / rng:.1f}"
            for i, v in enumerate(cum))

    zero_y = H - PAD - (0 - lo) * (H - 2 * PAD) / rng
    end = {k: series[k][-1] for k in series}
    return f'''<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" role="img"
  aria-label="Cumulative P&amp;L: agent vs baselines">
  <line x1="{PAD}" y1="{zero_y:.1f}" x2="{W - PAD}" y2="{zero_y:.1f}" class="zero"/>
  <polyline points="{pts(series['b1_dollars'])}" class="ln b1"/>
  <polyline points="{pts(series['b0_dollars'])}" class="ln b0"/>
  <polyline points="{pts(series['agent_dollars'])}" class="ln ag"/>
  <circle cx="{W - PAD}" cy="{H - PAD - (end['agent_dollars'] - lo) * (H - 2 * PAD) / rng:.1f}" r="3.5" class="dot"/>
</svg>'''


def month_table(R: list[dict]) -> str:
    by = {}
    for r in R:
        m = by.setdefault(r["day"][:7], {"d": 0, "a": 0.0, "b0": 0.0, "b1": 0.0, "p": 0})
        m["d"] += 1
        m["a"] += r["agent_dollars"]
        m["b0"] += r["b0_dollars"]
        m["b1"] += r["b1_dollars"]
        m["p"] += len(r["passes"])
    tr = ""
    for mo in sorted(by):
        m = by[mo]
        d = m["a"] - m["b0"]
        tr += (f'<tr><td>{mo}</td><td>{m["d"]}</td>'
               f'<td class="{pl_class(m["a"])}">{usd(m["a"])}</td>'
               f'<td class="mut">{usd(m["b0"])}</td><td class="mut">{usd(m["b1"])}</td>'
               f'<td class="{pl_class(d)}">{usd(d)}</td><td>{m["p"]}</td></tr>')
    return tr


def build() -> str:
    R = rows()
    done = len(R)
    a = sum(r["agent_dollars"] for r in R)
    b0 = sum(r["b0_dollars"] for r in R)
    b1 = sum(r["b1_dollars"] for r in R)
    edge0, edge1 = a - b0, a - b1
    trades = [t for r in R for t in r["trades"]]
    passes = [p for r in R for p in r["passes"]]
    confl = [c for r in R for c in r.get("conflicts", [])]
    touched = [t for t in trades if t.get("touched")]
    forf = sum(p["mech_dollars"] for p in passes)
    turns = sum(r["turns"] for r in R)

    eng = ""
    for name in ("CANON", "SHELF"):
        g = [t for t in trades if t["engine"] == name]
        if not g:
            continue
        da = sum(t["agent_dollars"] for t in g)
        dm = sum(t["mech_dollars"] for t in g)
        dd = da - dm
        eng += (f'<div class="card"><div class="eyebrow">{name} · {len(g)} taken</div>'
                f'<div class="big {pl_class(da)}">{usd(da)}</div>'
                f'<div class="sub">mech would have {usd(dm)} '
                f'<span class="{pl_class(dd)}">({usd(dd)} management)</span></div></div>')

    # notable deviations: biggest agent-vs-mech deltas among touched trades
    notable = sorted(touched, key=lambda t: abs(t["agent_dollars"] - t["mech_dollars"]),
                     reverse=True)[:5]
    nt = ""
    for t in notable:
        d = t["agent_dollars"] - t["mech_dollars"]
        note = html.escape((t.get("last_note") or "")[:90])
        nt += (f'<tr><td>{t["day"]}</td><td>{t["engine"]} {t["direction"]}</td>'
               f'<td class="{pl_class(d)}">{usd(d)}</td>'
               f'<td class="note">{note}</td></tr>')
    if not nt:
        nt = '<tr><td colspan="4" class="empty">no agent deviations yet</td></tr>'

    cf = ""
    for c in confl[-6:]:
        cf += f'<span class="chip">{c["day"]} · {c["choice"]}</span>'
    if not cf:
        cf = '<span class="empty">none faced yet</span>'

    feed = ""
    for r in R[-8:][::-1]:
        d = r["agent_dollars"] - r["b0_dollars"]
        th = html.escape((r.get("thesis") or "").replace('"', "")[:110])
        feed += (f'<div class="feedrow"><div class="fday">{r["day"]}</div>'
                 f'<div class="fnum {pl_class(r["agent_dollars"])}">{usd(r["agent_dollars"])}</div>'
                 f'<div class="fvs {pl_class(d)}">{usd(d)} vs B0</div>'
                 f'<div class="fmeta">{r["n_signals"]} sigs · {len(r["passes"])} passes · '
                 f'{r["turns"]} turns</div>'
                 f'<div class="fth">{th}</div></div>')
    if not feed:
        feed = '<div class="empty">first day lands shortly</div>'

    # run health / ETA from transcript mtimes over the trailing hour
    eta = "—"
    tdir = RUNS / "transcripts"
    if tdir.exists() and done:
        now = time.time()
        recent = [f for f in tdir.glob("*.json") if now - f.stat().st_mtime < 3600]
        if recent and done < TOTAL_DAYS:
            rate = len(recent)  # days per hour
            if rate:
                hrs = (TOTAL_DAYS - done) / rate
                eta = f"~{hrs:.0f}h at current pace ({rate} days/h)"
        elif done >= TOTAL_DAYS:
            eta = "COMPLETE"
    upd = (datetime.now(timezone.utc) + timedelta(hours=NY_OFF)).strftime("%H:%M ET")
    pct = 100.0 * done / TOTAL_DAYS
    stale = ""
    jf = RUNS / "journal.jsonl"
    if jf.exists() and time.time() - jf.stat().st_mtime > 2400 and done < TOTAL_DAYS:
        stale = '<span class="warn">⚠ no new days in 40+ min — run may be stalled</span>'

    edge_pill = (f'<span class="pill {pl_class(edge0)}">{usd(edge0)} vs machine</span>'
                 if done else '<span class="pill mut">warming up</span>')

    return f'''<meta charset="utf-8">
<meta http-equiv="refresh" content="300">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Live-Sim Desk — IB Complex × Canon</title>
<style>
:root {{
  --bg:#0e1420; --panel:#161e2e; --panel2:#1b2436; --line:#26324a;
  --tx:#d7dfeb; --mut:#7c93ae; --gold:#d9a441; --up:#3fb68b; --dn:#e0554d;
  --chip:#22304a;
}}
@media (prefers-color-scheme: light) {{
  :root {{ --bg:#f3f5f8; --panel:#ffffff; --panel2:#eef1f6; --line:#d8dfe9;
  --tx:#1d2939; --mut:#5c718a; --gold:#a87716; --up:#177a58; --dn:#c03d36;
  --chip:#e6ebf3; }}
}}
:root[data-theme="dark"] {{ --bg:#0e1420; --panel:#161e2e; --panel2:#1b2436;
  --line:#26324a; --tx:#d7dfeb; --mut:#7c93ae; --gold:#d9a441; --up:#3fb68b;
  --dn:#e0554d; --chip:#22304a; }}
:root[data-theme="light"] {{ --bg:#f3f5f8; --panel:#ffffff; --panel2:#eef1f6;
  --line:#d8dfe9; --tx:#1d2939; --mut:#5c718a; --gold:#a87716; --up:#177a58;
  --dn:#c03d36; --chip:#e6ebf3; }}
* {{ box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--tx); margin:0; padding:20px;
  font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif; }}
.mono, td, .big, .fnum, .fvs, .pill {{ font-family:ui-monospace,"SF Mono",
  "Cascadia Mono",Consolas,monospace; font-variant-numeric:tabular-nums; }}
.wrap {{ max-width:920px; margin:0 auto; display:flex; flex-direction:column; gap:14px; }}
header {{ display:flex; justify-content:space-between; align-items:baseline; gap:12px;
  flex-wrap:wrap; }}
h1 {{ font-size:16px; margin:0; letter-spacing:.02em; }}
h1 .amber {{ color:var(--gold); }}
.upd {{ color:var(--mut); font-size:12px; }}
.score {{ display:grid; grid-template-columns:1.4fr 1fr 1fr; gap:10px; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:6px;
  padding:14px 16px; }}
.eyebrow {{ font-size:11px; text-transform:uppercase; letter-spacing:.08em;
  color:var(--mut); margin-bottom:4px; }}
.big {{ font-size:26px; font-weight:600; }}
.hero .big {{ font-size:34px; color:var(--gold); }}
.sub {{ color:var(--mut); font-size:12px; margin-top:4px; }}
.up {{ color:var(--up); }} .dn {{ color:var(--dn); }} .mut {{ color:var(--mut); }}
.pill {{ display:inline-block; border-radius:99px; padding:2px 10px; font-size:12px;
  background:var(--chip); margin-top:6px; }}
.prog {{ height:6px; background:var(--panel2); border-radius:3px; overflow:hidden; }}
.prog i {{ display:block; height:100%; width:{pct:.1f}%; background:var(--gold); }}
.progrow {{ display:flex; justify-content:space-between; color:var(--mut);
  font-size:12px; margin-top:6px; }}
svg {{ width:100%; height:190px; display:block; }}
.ln {{ fill:none; stroke-width:2; }} .ag {{ stroke:var(--gold); }}
.b0 {{ stroke:var(--mut); stroke-width:1.4; }}
.b1 {{ stroke:var(--mut); stroke-width:1; stroke-dasharray:4 4; }}
.zero {{ stroke:var(--line); stroke-width:1; }} .dot {{ fill:var(--gold); }}
.legend {{ display:flex; gap:16px; color:var(--mut); font-size:12px; margin-top:6px; }}
.legend b {{ font-weight:500; }}
.sw {{ display:inline-block; width:14px; height:3px; vertical-align:middle;
  margin-right:5px; border-radius:2px; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
table {{ border-collapse:collapse; width:100%; font-size:13px; }}
th {{ text-align:left; color:var(--mut); font-weight:500; font-size:11px;
  text-transform:uppercase; letter-spacing:.06em; padding:4px 8px;
  border-bottom:1px solid var(--line); }}
td {{ padding:5px 8px; border-bottom:1px solid var(--line); }}
tr:last-child td {{ border-bottom:none; }}
.note {{ font-family:system-ui,sans-serif; color:var(--mut); font-size:12px; }}
.chip {{ display:inline-block; background:var(--chip); border-radius:4px;
  padding:2px 8px; font-size:12px; margin:2px 3px 2px 0;
  font-family:ui-monospace,monospace; }}
.feedrow {{ display:grid; grid-template-columns:92px 92px 110px 1fr; gap:4px 12px;
  padding:7px 0; border-bottom:1px solid var(--line); align-items:baseline; }}
.feedrow:last-child {{ border-bottom:none; }}
.fday {{ color:var(--mut); font-size:12px; font-family:ui-monospace,monospace; }}
.fnum {{ font-weight:600; }} .fvs {{ font-size:12px; }}
.fmeta {{ color:var(--mut); font-size:12px; }}
.fth {{ grid-column:1/-1; color:var(--mut); font-size:12px; font-style:italic; }}
.empty {{ color:var(--mut); font-size:13px; padding:14px 0; text-align:center; }}
.warn {{ color:var(--dn); font-size:12px; }}
footer {{ color:var(--mut); font-size:12px; display:flex; gap:18px; flex-wrap:wrap; }}
.scroll {{ overflow-x:auto; }}
@media (max-width:720px) {{ .score,.grid2 {{ grid-template-columns:1fr; }} }}
</style>
<div class="wrap">
<header>
  <h1>LIVE-SIM DESK <span class="amber">·</span> IB Complex × Canon
    <span class="amber">·</span> no hindsight</h1>
  <span class="upd">updated {upd} · auto-refreshes</span>
</header>

<div class="score">
  <div class="card hero"><div class="eyebrow">The desk (agent, Sonnet)</div>
    <div class="big">{usd(a) if done else "—"}</div>{edge_pill}</div>
  <div class="card"><div class="eyebrow">B0 · pure machine</div>
    <div class="big mut">{usd(b0) if done else "—"}</div>
    <div class="sub">takes everything, nets conflicts</div></div>
  <div class="card"><div class="eyebrow">B1 · canon precedence</div>
    <div class="big mut">{usd(b1) if done else "—"}</div>
    <div class="sub {pl_class(edge1)}">desk {usd(edge1)} vs B1</div></div>
</div>

<div class="card">
  <div class="prog"><i></i></div>
  <div class="progrow"><span>{done} / {TOTAL_DAYS} days simulated ({pct:.0f}%)</span>
  <span>{eta}</span>{f"<span>{stale}</span>" if stale else ""}</div>
</div>

<div class="card">
  <div class="eyebrow">Cumulative P&amp;L</div>
  {spark(R)}
  <div class="legend">
    <span><i class="sw" style="background:var(--gold)"></i><b>desk</b></span>
    <span><i class="sw" style="background:var(--mut)"></i>B0 machine</span>
    <span><i class="sw" style="background:var(--mut);height:1px"></i>B1 canon-precedence</span>
  </div>
</div>

<div class="grid2">
  <div class="card scroll">
    <div class="eyebrow">By month</div>
    <table><tr><th>month</th><th>days</th><th>desk</th><th>B0</th><th>B1</th>
    <th>edge</th><th>passes</th></tr>{month_table(R)}</table>
  </div>
  <div style="display:flex;flex-direction:column;gap:10px;">
    {eng if eng else '<div class="card"><div class="empty">engine split appears with first trades</div></div>'}
    <div class="card"><div class="eyebrow">Discipline</div>
      <div class="sub" style="font-size:13px;">
      {len(passes)} passes · forfeited <span class="{pl_class(-forf)}">{usd(forf)}</span>
      of machine P&amp;L{" — passes are saving money" if forf < 0 else
      (" — passes are costing money" if passes else "")}<br>
      {len(touched)} of {len(trades)} taken trades touched by hand ·
      {turns:,} desk calls</div>
      <div style="margin-top:8px;">{cf}</div>
    </div>
  </div>
</div>

<div class="card scroll">
  <div class="eyebrow">Biggest interventions (desk vs its own machine outcome)</div>
  <table><tr><th>day</th><th>trade</th><th>delta</th><th>desk note</th></tr>{nt}</table>
</div>

<div class="card">
  <div class="eyebrow">Recent days</div>
  {feed}
</div>

<footer>
  <span>fit span 2025-06 → 2026-07 · 875 signals · month-parallel, journal chains monthly</span>
  <span>knowledge: both rulebooks + holdout only · passive desk == B0 verified</span>
</footer>
</div>'''


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("live_desk_dashboard.html")
    out.write_text(build())
    print(f"wrote {out} ({len(rows())} days)")
