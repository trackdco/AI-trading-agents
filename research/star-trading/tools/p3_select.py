#!/usr/bin/env python3
"""P3 INSTANT SELECTION — Amendment 03 §7, under the blindness control.

Finds instants inside the workbench where a trigger survives PAST the confluence
gate and all the way through admission, so that the code paths P2 never reached —
trigger predicates, invalidation, order geometry, the RR-floor ladder, the A7
tie-break and the session cap — are all exercised by the parity reading.

Restricted to January 2025 (the reference platform can render 2m/3m/5m there) and
to entry timeframes 2m/3m/5m (1m is unreadable for this window, A11).

OUTPUT DISCIPLINE. This script writes the full expected state to a SEALED file.
Only the date and the time may be released. Everything else — timeframe,
direction, levels, the reason the instant was chosen — stays sealed until the
reading is submitted, or the blind is broken and P3 measures nothing.

No outcome is computed. The sealed workbench parquet is never opened.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import json
from pathlib import Path

from vwapbb_signals import (build_sessions, minute_of_day, cluster_levels, htf_flag,
                            RunningVWAP, TFS, BB_N, RTH_OPEN, FIRST_SIG, RTH_CLOSE,
                            NY_VWAP_ANCHOR, POC_BIN, CLUSTER_TOL)
from vwapbb_opportunity import trig, assert_workbench, WORKBENCH_END
from vwapbb_a7_selector import (ladder, tie_break, MIN_STOP, RR_FLOOR, FRONT_RUN_F,
                                MAX_TRADES_DAY, LOC_BAND, TICK)
from stage2_smoke import contract_key, EOD_FLATTEN, READING, signal_candidates

SEALED = Path(__file__).resolve().parents[2] / "vwap-bb" / "P3-SELECTION-SEALED.md"
FIRST = "2025-01-02"
NY_MIN_OBS = 30              # A8: NY sigma bands eligible from 10:00
A8_OK_MINUTE = NY_VWAP_ANCHOR + NY_MIN_OBS          # 600 = 10:00


def state_at(bars, prev_hl, target_cm, target_tf):
    """Full indicator state at one (cm, tf), replaying the sealed engine's
    construction. Used only to describe the chosen instant in the sealed file."""
    idxs = sorted(bars)
    dv, nv = RunningVWAP(), RunningVWAP()
    poc = collections.defaultdict(float)
    bb = {tf: collections.deque(maxlen=BB_N) for tf in TFS}
    tfacc = {tf: [] for tf in TFS}
    b15, acc15 = [], []
    h4, acc4 = collections.deque(maxlen=6), []
    sess_hi, sess_lo = -1e18, 1e18
    pre_hi, pre_lo = -1e18, 1e18
    snap = {}
    for i in idxs:
        o, h, l, c, v = bars[i]
        mm = minute_of_day(i)
        if mm + 1 > target_cm and not (mm >= 1080 or mm < RTH_OPEN):
            break
        dv.add(h, l, c, v)
        if NY_VWAP_ANCHOR <= mm < RTH_CLOSE + 1:
            nv.add(h, l, c, v)
        nb = max(1, int((h - l) / POC_BIN) + 1)
        for k in range(nb):
            poc[int((l + k * POC_BIN) / POC_BIN)] += v / nb
        sess_hi, sess_lo = max(sess_hi, h), min(sess_lo, l)
        if mm >= 1080 or mm < NY_VWAP_ANCHOR:
            pre_hi, pre_lo = max(pre_hi, h), min(pre_lo, l)
        acc15.append((o, h, l, c))
        if (mm + 1) % 15 == 0:
            b15.append((acc15[0][0], max(x[1] for x in acc15),
                        min(x[2] for x in acc15), acc15[-1][3]))
            acc15 = []
        acc4.append((h, l))
        if (mm + 1) % 240 == 0:
            h4.append((max(x[0] for x in acc4), min(x[1] for x in acc4)))
            acc4 = []
        for tf in TFS:
            tfacc[tf].append((o, h, l, c))
            if (mm + 1) % tf:
                continue
            g = tfacc[tf]
            tfacc[tf] = []
            to_, th_, tl_, tc_ = (g[0][0], max(x[1] for x in g),
                                  min(x[2] for x in g), g[-1][3])
            bb[tf].append(tc_)
            cm = mm + 1
            if len(bb[tf]) < BB_N or cm < FIRST_SIG:
                continue
            if cm > target_cm:
                continue
            dmid, dsig = dv.value()
            nmid, nsig = nv.value()
            if dmid is None:
                continue
            p = max(poc.items(), key=lambda kv: kv[1])[0] * POC_BIN
            basis = sum(bb[tf]) / BB_N
            sd = (sum((x - basis) ** 2 for x in bb[tf]) / BB_N) ** 0.5
            lv = [(basis, "bb"), (p, "poc")]
            for k in (0, 1, 2, 3):
                lv.append((dmid + k * dsig, "vwap"))
                if k:
                    lv.append((dmid - k * dsig, "vwap"))
            if nmid:
                lv += [(nmid, "vwap"), (nmid + nsig, "vwap"), (nmid - nsig, "vwap")]
            snap[tf] = {
                "cm": cm, "bar": {"o": to_, "h": th_, "l": tl_, "c": tc_},
                "bb": {"basis": basis, "up2": basis + 2 * sd, "lo2": basis - 2 * sd},
                "dv": {"mid": dmid, "sig": dsig}, "nv": {"mid": nmid, "sig": nsig},
                "ny_bars": int(nv.vol > 0) and (cm - NY_VWAP_ANCHOR),
                "poc": p, "sess_hi": sess_hi, "sess_lo": sess_lo,
                "pre_hi": pre_hi, "pre_lo": pre_lo,
                "prev_hl": list(prev_hl) if prev_hl else None,
                "h4": [max(x[0] for x in h4), min(x[1] for x in h4)] if h4 else None,
                "htf": htf_flag(b15),
                "levels": sorted((round(pp, 4), tt) for pp, tt in lv),
                "clusters": [{"lo": a, "hi": b_, "types": sorted(t), "n": n_}
                             for a, b_, t, n_ in cluster_levels(lv)],
            }
    return snap.get(target_tf), snap


def admit_full(bars, cands):
    """Streaming admission, counting and recording WHICH candidate won. No outcome."""
    idxs = sorted(bars)
    pending, pos, n_adm = None, None, 0
    out = []
    for j in idxs:
        o, h, l, c, v = bars[j]
        mj = minute_of_day(j)
        if pending is not None and pos is None:
            if mj >= EOD_FLATTEN:
                pending = None
            else:
                w, pending = pending, None
                bad = (w["direction"] == "long" and o <= w["stop_px"]) or \
                      (w["direction"] == "short" and o >= w["stop_px"])
                if not bad:
                    pos = w
                    n_adm += 1
                    out.append({**w, "fill_px": o, "fill_min": mj})
        if pos is not None:
            if mj >= EOD_FLATTEN:
                pos = None
            else:
                if pos["direction"] == "long":
                    done = (l <= pos["stop_px"]) or (h >= pos["tgt_px"])
                else:
                    done = (h >= pos["stop_px"]) or (l <= pos["tgt_px"])
                if done:
                    pos = None
        if pos is None and pending is None and n_adm < MAX_TRADES_DAY:
            g = cands.get(mj + 1)
            if g:
                win, lvl = tie_break(g)
                if win is not None:
                    pending = {**win, "lvl": lvl, "n_at_minute": len(g)}
    return out


def score(t, snap):
    """Test-design score: how many of the untested code paths and open ambiguities
    this instant exercises. Nothing about profitability enters."""
    s, why = 0, []
    if t["tf"] in (3, 5):
        s += 1; why.append("higher entry TF, easier to read off a chart (+1)")
    if t["cm"] >= A8_OK_MINUTE:
        s += 3; why.append(f"signal at/after 10:00 — NY VWAP has >={NY_MIN_OBS} bars, "
                           f"so A8's sigma-band eligibility rule is satisfied AND 1m-vs-2m "
                           f"VWAP aggregation has largely converged, widening the "
                           f"comparable surface (+3)")
    if t["nlev"] >= 3:
        s += 3; why.append(f"cluster carries {t['nlev']} levels (+3)")
    if t["types"] >= 3:
        s += 2; why.append(f"{t['types']} distinct types — exercises the counter-trend "
                           f"confluence path (+2)")
    if t["lvl"] >= 1:
        s += 2; why.append(f"A7 tie-break fired at level {t['lvl']} among "
                           f"{t['n_at_minute']} candidates (+2)")
    st = snap
    cl_hi = 2 * t["cl_mid"] - t["cl_lo"]
    if st:
        struct = [x for x in (st["sess_hi"], st["sess_lo"], st["pre_hi"], st["pre_lo"],
                              *(st["prev_hl"] or []))]
        near = [x for x in struct if t["cl_lo"] - CLUSTER_TOL <= x <= cl_hi + CLUSTER_TOL]
        if near:
            s += 3; why.append(f"{len(near)} structural level(s) within tolerance of the "
                               f"cluster — exercises ambiguity (a), structural "
                               f"cluster-eligibility (+3)")
        ps = sorted(p for p, _ in st["levels"])
        gaps = [round(b - a, 2) for a, b in zip(ps, ps[1:])
                if t["cl_lo"] - 25 <= a <= cl_hi + 25]
        bnd = [g for g in gaps if 7.0 <= g <= 10.0]
        if bnd:
            s += 3; why.append(f"adjacent gap(s) {bnd} in the local ladder sit in the "
                               f"7-10 pt band — exercises ambiguity (b), chaining vs "
                               f"span (+3)")
        nmid, nsig = st["nv"]["mid"], st["nv"]["sig"]
        dmid, dsig = st["dv"]["mid"], st["dv"]["sig"]
        b = st["bar"]
        if nmid:
            ny = (b["h"] >= nmid + nsig) if t["direction"] == "long" \
                else (b["l"] <= nmid - nsig)
            dl = (b["h"] >= dmid + dsig) if t["direction"] == "long" \
                else (b["l"] <= dmid - dsig)
            if ny != dl:
                s += 4; why.append("the NY and the daily reading of \"the opposing +/-1sigma\" "
                                   "DISAGREE here — exercises ambiguity (c) as a live "
                                   "decision, not a coincidence (+4)")
        if st["h4"]:
            rh, rl = st["h4"]
            if rh > rl:
                pos = (b["c"] - rl) / (rh - rl)
                if 0.55 <= pos <= 0.95 or -0.05 <= pos <= 0.45:
                    s += 1; why.append(f"range position {pos:.3f} sits near the retired "
                                       f"0.20/0.80 threshold — exercises ambiguity (d) "
                                       f"as a covariate (+1)")
    return s, why


def main():
    sess, sym_of = build_sessions()
    days = [d for d in sorted(sess) if d <= WORKBENCH_END]
    for d in days:
        assert_workbench(d)
    rolls, prev_sym = set(), None
    for d in days:
        s = sorted(sym_of[d], key=contract_key)[-1]
        if prev_sym and contract_key(s) > contract_key(prev_sym):
            rolls.add(d)
        prev_sym = s
    after_roll = {days[i + 1] for i, d in enumerate(days) if d in rolls and i + 1 < len(days)}

    prev_hl = None
    pool = []
    for d in days:
        assert_workbench(d)
        bars = sess[d]
        this_hl = (max(x[1] for x in bars.values()), min(x[2] for x in bars.values()))
        if FIRST <= d <= WORKBENCH_END and d not in rolls and d not in after_roll \
                and len(sym_of[d]) == 1:
            audit = collections.Counter()
            cands = signal_candidates(bars, prev_hl, audit)
            if cands:
                for t in admit_full(bars, cands):
                    if t["tf"] == 1:
                        continue
                    pool.append((d, t, prev_hl))
        if d not in rolls:
            prev_hl = this_hl

    print(f"January-2025 admitted trades on 2m/3m/5m: {len(pool)}")
    ranked = []
    for d, t, phl in pool:
        st, _all = state_at(sess[d], phl, t["cm"], t["tf"])
        sc, why = score(t, st)
        ranked.append((sc, d, t, phl, st, why))
    ranked.sort(key=lambda r: (-r[0], r[1], r[2]["cm"]))
    print("\ntop 8 by test-design score:")
    for sc, d, t, phl, st, why in ranked[:8]:
        print(f"   {sc:3d}  {d} {t['cm']//60:02d}:{t['cm']%60:02d}  tf={t['tf']}m")
    sc, d, t, phl, st, why = ranked[0]
    _, allsnap = state_at(sess[d], phl, t["cm"], t["tf"])

    L = []
    def w(s=""):
        L.append(s)
    hhmm = f"{t['cm']//60:02d}:{t['cm']%60:02d}"
    w("# P3 SELECTION — SEALED UNTIL ANGUS SUBMITS HIS READING")
    w()
    w("> ## DO NOT OPEN THIS FILE BEFORE SUBMITTING THE P3 SHEET.")
    w("> It contains the detector's expected values for the P3 instant, the timeframe the")
    w("> trigger fires on, its direction, and the reason the instant was chosen. Reading any")
    w("> of it before the reading is recorded destroys the blind and P3 measures nothing.")
    w()
    w("**Released to Angus: the date and the time. Nothing else.** Amendment 03 §7.")
    w()
    w("---")
    w()
    w("## 1. The selection, and why it is not evidence about agreement rates")
    w()
    w("**The instant was chosen FROM detector output.** That is legitimate test design — P3")
    w("exists to exercise code paths P2 never reached, and selecting inputs that reach deep")
    w("paths is what a unit test does. It is **not** legitimate as evidence about how often")
    w("the detector and the chart agree, because the instants were not randomly drawn.")
    w()
    w("> **The P3 result may be cited as evidence that the code paths behave as specified.**")
    w("> **It may NOT be cited as an agreement rate.**")
    w()
    w(f"**Chosen instant: {d} {hhmm} ET.** Test-design score {sc}.")
    w()
    w("Why this one:")
    for x in why:
        w(f"- {x}")
    w()
    w("What P2 could not test, and this instant does — the trade survives the confluence gate,")
    w("the §7 invalidation, the location gate, the entry-beyond-wick check and the RR-floor")
    w("ladder, wins its minute under the A7 tie-break, is admitted under the session cap and")
    w("fills at the next bar's open. **Every code path listed as unexercised in**")
    w("**`PARITY-P2-RESULT.md` §7 runs at this instant.**")
    w()
    w("## 2. Expected detector values")
    w()
    w(f"Session {d}, contract {sorted(sym_of[d], key=contract_key)}. Signal close-minute")
    w(f"`cm = {t['cm']}` = **{hhmm}**, i.e. the bar covering "
      f"**{(t['cm']-t['tf'])//60:02d}:{(t['cm']-t['tf'])%60:02d}:00 – "
      f"{(t['cm']-1)//60:02d}:{(t['cm']-1)%60:02d}:59** has just closed.")
    w()
    w("### The trade")
    w()
    w("| | |")
    w("|---|---|")
    for k, lab in (("tf", "entry timeframe"), ("direction", "direction"),
                   ("kind", "trigger kind"), ("htf", "HTF flag"),
                   ("counter", "counter-trend"), ("types", "distinct cluster types"),
                   ("nlev", "levels in cluster"), ("lvl", "tie-break level that decided"),
                   ("n_at_minute", "candidates sharing the minute")):
        w(f"| {lab} | **{t.get(k)}** |")
    for k, lab in (("entry", "intended entry (E1, BB MA)"), ("stop_px", "stop price"),
                   ("tgt_px", "target price"), ("R_int", "intended R, points"),
                   ("cl_lo", "cluster low"), ("cl_mid", "cluster mid"),
                   ("fill_px", "fill price (next bar open)")):
        v = t.get(k)
        w(f"| {lab} | **{v:.4f}** |" if isinstance(v, float) else f"| {lab} | {v} |")
    w(f"| fill minute | {t['fill_min']//60:02d}:{t['fill_min']%60:02d} |")
    w()
    w("### Levels at the instant, per entry timeframe")
    w()
    for tf in sorted(allsnap):
        s2 = allsnap[tf]
        w(f"**{tf}m** — last close cm={s2['cm']} "
          f"({s2['cm']//60:02d}:{s2['cm']%60:02d})")
        w()
        w("| | |")
        w("|---|---|")
        w(f"| bar O/H/L/C | {s2['bar']['o']} / {s2['bar']['h']} / "
          f"{s2['bar']['l']} / {s2['bar']['c']} |")
        w(f"| BB basis / +2σ / −2σ | {s2['bb']['basis']:.4f} / {s2['bb']['up2']:.4f} / "
          f"{s2['bb']['lo2']:.4f} |")
        w(f"| daily VWAP mid / σ | {s2['dv']['mid']:.4f} / {s2['dv']['sig']:.4f} |")
        w(f"| NY VWAP mid / σ | {s2['nv']['mid']:.4f} / {s2['nv']['sig']:.4f} |")
        w(f"| NY bars since anchor | {s2['ny_bars']} |")
        w(f"| POC | {s2['poc']} |")
        w(f"| session hi / lo | {s2['sess_hi']} / {s2['sess_lo']} |")
        w(f"| pre-market hi / lo | {s2['pre_hi']} / {s2['pre_lo']} |")
        w(f"| prior-day hi / lo (Globex) | {s2['prev_hl']} |")
        w(f"| 4h range hi / lo (clock blocks) | {s2['h4']} |")
        w(f"| HTF flag | {s2['htf']} |")
        w(f"| clusters | {[(round(cc['lo'],2), round(cc['hi'],2), cc['types']) for cc in s2['clusters']]} |")
        w()
    w("## 3. Known-unverifiable fields at this instant")
    w()
    w("Recorded in advance so they are not later read as passes:")
    w()
    w("- **NY VWAP σ bands.** A8 fixes the feed at 1-minute and Angus cannot render a 1m VWAP")
    w("  for January 2025. Any agreement here is coincidence; any disagreement is expected.")
    w("- **1m row.** Unreadable (A11).")
    w("- **The daily POC.** At P2 the 1m-vs-2m profile construction diverged by 44.50 points.")
    w("  Whether it converges later in a session is unknown and is not being controlled for.")
    w()
    w("## 4. Provenance")
    w()
    w("| | |")
    w("|---|---|")
    w("| selector | `research/star-trading/tools/p3_select.py` |")
    w("| detector | `stage2_smoke.signal_candidates` + the A7 admission loop, unmodified |")
    w(f"| pool | January-2025 admitted trades on 2m/3m/5m: **{len(pool)}** |")
    w("| sealed workbench parquet | **NOT opened** |")
    w("| holdout | **SEALED**; every date read ≤ 2025-01-31 |")
    w("| N_trials | **0** — no outcome was computed and nothing was ranked by profitability |")
    SEALED.write_text("\n".join(L) + "\n")
    print(f"\nsealed reasoning written to {SEALED}")
    print("\n" + "=" * 60)
    print("RELEASE TO ANGUS — date and time only:")
    print(f"    {d}   {hhmm} ET")
    print("=" * 60)


if __name__ == "__main__":
    main()
